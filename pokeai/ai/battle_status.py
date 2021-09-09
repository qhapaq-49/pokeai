"""
バトルの状態を表すオブジェクト
あるプレイヤーから見た状態を管理する
"""
import json
import re
from typing import Any, Dict, List, Set, Optional, Tuple, ClassVar
import dataclasses

from pokeai.sim.party_generator import Party


def parse_hp_condition(hp_condition: str, is_friend:bool=True) -> Tuple[int, int, str]:
    """
    HPと状態異常を表す文字列のパース
    :param hp_condition: '50/200' (現在HP=50, 最大HP=200, 状態異常なし) or '50/200 psn' (状態異常の時)
    :is_friend: 自軍の状態であるか。相手側の場合、最大HPの情報は隠す
    :return: 現在HP, 最大HP, 状態異常('', 'psn'(毒), 'tox'(猛毒), 'par', 'brn', 'slp', 'frz', 'fnt'(瀕死))
    """
    if hp_condition == '0 fnt':
        # 瀕死の時は0という表示になっている
        # 便宜上最大HP100として返している
        return 0, 100, 'fnt'
    m = re.match('^(\\d+)/(\\d+)(?: (psn|tox|par|brn|slp|frz|fnt)|)?$', hp_condition)
    assert m is not None, f"HP_CONDITION '{hp_condition}' cannot be parsed."
    # m[3]は状態異常がないときNoneとなる
    if not is_friend:
        curr_ratio = (100 * int(m[1])) // int(m[2])
        return curr_ratio, 100, m[3] or ''
    return int(m[1]), int(m[2]), m[3] or ''


def _parse_details(details: str) -> Tuple[str, int, str]:
    """
    ポケモンの情報をパース
    :param details: 種族名・レベル・性別情報　例:'Ninetales, L50, M'
    :return:
    """
    # 例外的な種族名 'Nidoran-F', 'Porygon2', 'Mr. Mime', "Farfetch'd"
    m = re.match('^([A-Za-z-]+|Porygon2|Mr\\. Mime|Farfetch\'d), L(\\d+)(?:, (M|F|N))?$', details)
    assert m is not None, f"DETAILS '{details}' cannot be parsed."
    # 性別不明だとm[3]はNone
    return m[1], int(m[2]), m[3] or 'N'

@dataclasses.dataclass
class ActivePokeStatus:
    """
    場に出ているポケモンの状態
    """
    RANK_INITIAL :ClassVar[Dict[str, int]] = {'atk': 0, 'def': 0, 'spa': 0, 'spd': 0, 'spe': 0, 'accuracy': 0, 'evasion': 0}
    RANK_MAX :ClassVar[int] = 6
    RANK_MIN : ClassVar[int] = -6
    RANK_ZERO: ClassVar[int] = 0
    pokemon: str  # |switch|POKEMON|DETAILS|HP STATUSにおけるPOKEMON部分。例：'p1a: Ninetales'
    species: str  # 種族　例：'Ninetales'
    level: int
    gender: str
    hp_current: int
    hp_max: int
    status: str  # 状態異常 (異常がない時は'')
    ranks: Dict[str, int]
    volatile_statuses: Set[str]  # 状態変化

    def __init__(self, pokemon: str, species: str, level: int, gender: str, hp_current: int, hp_max: int, status: str, ranks:Optional[Dict[str, int]]=None, volatile_statuses: Optional[Set[str]]=None):
        """
        場に出た直後のポケモンを生成する
        :param pokemon:
        :param species:
        :param hp_current:
        :param hp_max:
        :param status:
        """
        self.pokemon = pokemon
        self.species = species
        self.level = level
        self.gender = gender
        self.hp_current = hp_current
        self.hp_max = hp_max
        self.status = status
        if ranks is not None:
            self.ranks = ranks
        else:
            self.ranks = ActivePokeStatus.RANK_INITIAL.copy()
        if volatile_statuses is not None:
            self.volatile_statuses = set(volatile_statuses)
        else:
            self.volatile_statuses = set()

    def rank_boost(self, stat: str, amount: int):
        self._rank_set_clip(stat, self.ranks[stat] + amount)

    def rank_unboost(self, stat: str, amount: int):
        self._rank_set_clip(stat, self.ranks[stat] - amount)

    def rank_setboost(self, stat: str, amount: int):
        self._rank_set_clip(stat, amount)

    def _rank_set_clip(self, stat: str, value: int):
        assert stat in self.ranks
        self.ranks[stat] = min(max(value, ActivePokeStatus.RANK_MIN), ActivePokeStatus.RANK_MAX)

    def rank_clearallboost(self):
        for stat in self.ranks.keys():
            self.ranks[stat] = ActivePokeStatus.RANK_ZERO

    @property
    def hp_ratio(self) -> float:
        return self.hp_current / self.hp_max


@dataclasses.dataclass
class SideStatus:
    """
    一方のプレイヤーの状態
    """
    active: Optional[ActivePokeStatus]
    reserve_pokes: Dict[str, ActivePokeStatus]  # 控えのポケモンの交代直前の状態(瀕死状態のポケモンも含む)
    side_statuses: Set[str]  # プレイヤーの場の状態
    total_pokes: int  # 全手持ちポケモン数
    remaining_pokes: int  # 残っているポケモン数

    def __init__(self, active: Optional[Dict[str, Any]]=None, reserve_pokes: Optional[Dict[str, Any]]=None,
        side_statuses : Optional[List[str]]=None, total_pokes:int=0, remaining_pokes:int=0
    ):
        """
        バトル開始時の状態を生成する
        """
        if active is not None:
            self.active = ActivePokeStatus(**active)
        else:
            self.active = None
        
        self.reserve_pokes = {}
        if reserve_pokes is not None:
            for key in reserve_pokes:
                self.reserve_pokes[key] = ActivePokeStatus(**reserve_pokes[key])
        if side_statuses is not None:
            self.side_statuses = set(side_statuses)
        else:
            self.side_statuses = set()

        self.total_pokes = total_pokes
        self.remaining_pokes = remaining_pokes

    def switch(self, active: ActivePokeStatus):
        """
        ポケモンを交換、またはゲームの最初に繰り出す
        :param active:
        :return:
        """
        if self.active is not None:
            self.reserve_pokes[self.active.species] = self.active
        self.active = active
        if active.species in self.reserve_pokes:
            del self.reserve_pokes[active.species]

    def get_mean_hp_ratio(self) -> float:
        """
        控えを含めたポケモンごとの現在HP/最大HPを計算し、全ポケモンの平均を返す
        :return:
        """
        assert self.total_pokes > 0
        assert self.active is not None
        # まだ登場していないポケモンはhp_ratio==1.0とみなす
        ratio_sum = self.active.hp_ratio + sum(p.hp_ratio for p in self.reserve_pokes.values()) + (
                self.total_pokes - 1 - len(self.reserve_pokes))
        return ratio_sum / self.total_pokes

    def get_alive_ratio(self) -> float:
        """
        生きているポケモン数/全ポケモン数を計算する
        :return:
        """
        assert self.total_pokes > 0
        return self.remaining_pokes / self.total_pokes

@dataclasses.dataclass
class BattleStatus:
    WEATHER_NONE :ClassVar[str] = 'none'
    turn: int  # ターン番号(最初が0)
    side_friend: str  # 自分側のside ('p1' or 'p2')
    side_opponent: str  # 相手側のside ('p1' or 'p2')
    side_party: Party  # 自分側のパーティ
    weather: str  # 天候（なしの時はWEATHER_NONE='none'）
    side_statuses: Dict[str, SideStatus]  # key: 'p1' or 'p2'

    def __init__(self, side_friend: str, side_party: Party, 
        side_opponent: str="", turn: int=0, weather:str="none",
        side_statuses: Optional[Dict[str, Any]]=None
    ):
        assert side_friend in ['p1', 'p2']
        self.side_friend = side_friend
        self.side_opponent = {'p1': 'p2', 'p2': 'p1'}[side_friend]
        self.side_party = side_party
        self.turn = turn
        self.weather = BattleStatus.WEATHER_NONE
        if side_statuses is not None:
            self.side_statuses = {'p1': SideStatus(**side_statuses["p1"]), 'p2': SideStatus(**side_statuses["p2"])}
        else:
            self.side_statuses = {'p1': SideStatus(), 'p2': SideStatus()}

    def switch(self, pokemon: str, details: str, hp_condition: str):
        side = pokemon[:2]
        is_friend = (side == self.side_friend)
        species, level, gender = _parse_details(details)
        hp_current, hp_max, status = parse_hp_condition(hp_condition, is_friend)
        poke = ActivePokeStatus(pokemon, species, level, gender, hp_current, hp_max, status)
        self.side_statuses[side].switch(poke)

    def get_side(self, pokemon: str) -> SideStatus:
        return self.side_statuses[pokemon[:2]]

    def json_dumps(self) -> str:
        def default(obj):
            if isinstance(obj, set):
                return list(obj)
            else:
                return obj.__dict__

        return json.dumps(self, default=default)

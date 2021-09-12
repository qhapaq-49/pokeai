"""
行動選択AIのベースクラス
"""
from pokeai.ai.battle_status import BattleStatus


class ActionPolicy:
    train: bool

    def __init__(self):
        self.train = False

    def game_start(self):
        """
        内部状態のリセット
        :return:
        """
        pass

    def choice_turn_start(self, battle_status: BattleStatus, request: dict) -> str:
        """
        ターン開始時の行動選択
        :param battle_status:
        :param request:
        :return: 行動。"move [1-4]|switch [1-6]"
        """
        raise NotImplementedError

    def choice_force_switch(self, battle_status: BattleStatus, request: dict) -> str:
        """
        強制交換時の行動選択
        :param battle_status:
        :param request:
        :return: 行動。"switch [1-6]"
        """
        raise NotImplementedError

    def game_end(self, reward: float):
        """
        ゲーム終了時に呼び出される
        :param reward: 勝ち:1 負け:-1 引き分け:0
        :return:
        """
        pass

    def send_raw_chunk(self, chunk_type, chunk):
        """
        showdownからの情報を転送する
        """
        pass

    def ask_party(self, info_str:str) -> str:
        """
        どのポケモンを選ぶかを尋ねる

        :param info_str : json形式テキストで相手パーティーに関する情報を送る。
        相手パーティーに関する情報は"opponent"で、選ぶポケモンの数については"to_select"で与えられる
        :return: 選択するポケモン idxは1〜6であることに注意。例 "choice 1 2 3"
        
        """
        raise NotImplementedError
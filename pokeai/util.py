import json
import pickle
import base64
import yaml
from pathlib import Path
from typing import Union

ROOT_DIR = Path(__file__).resolve().parents[1]  # type: Path
DATASET_DIR = ROOT_DIR.joinpath('data', 'dataset')  # type:Path


def json_load(path: Union[str, Path]):
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def json_dump(obj, path: Union[str, Path]):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)


def pickle_load(path: Union[str, Path]):
    with open(path, 'rb') as f:
        return pickle.load(f)


def pickle_dump(obj, path: Union[str, Path]):
    with open(path, 'wb') as f:
        pickle.dump(obj, f)


def yaml_load(path: Union[str, Path]):
    with open(path, encoding='utf-8') as f:
        return yaml.safe_load(f)


def yaml_dump(obj, path: Union[str, Path]):
    with open(path, 'w', encoding='utf-8') as f:
        yaml.safe_dump(obj, f)


def pickle_base64_dumps(obj) -> str:
    """
    オブジェクトをダンプし、json等に格納可能なbase64文字列に変換する
    :param obj:
    :return:
    """
    return base64.b64encode(pickle.dumps(obj)).decode("ascii")


def pickle_base64_loads(s: str):
    return pickle.loads(base64.b64decode(s))


def side2idx(side: str) -> int:
    return {'p1': 0, 'p2': 1}[side]


def idx2side(idx: int) -> str:
    return ['p1', 'p2'][idx]

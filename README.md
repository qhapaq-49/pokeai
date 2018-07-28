# PokéAI ～人工知能の考えた最強のポケモン対戦戦略～
PokéAI(ポケエーアイ)は、ポケモンバトルの戦略を人工知能に考えさせ、
究極的には人が思いつかなかったような戦略を編み出すことを目標とするプロジェクトです。

初代バージョンの全ポケモン・技実装用ブランチ。2017年時点のコードをいったん消して再構築中。

# setup
Python 3.6が必要。

```
python setup.py develop
```

# test
```
python -m unittest
```

# AI機能
## ランダムなパーティ・方策での対戦
ランダムなパーティ構成と対戦結果を保存
```
python -m pokeai.agent.all_random_party_rank OUTPUT_FILE_NAME N_PARTIES
```

# ライセンス
コードはMITライセンスとしております。本については、ファイル内のライセンス表記をご参照ください。

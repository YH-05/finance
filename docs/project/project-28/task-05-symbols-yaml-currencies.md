# Task 05: symbols.yaml に currencies セクション追加

**Phase**: 2 - 為替データ
**依存**: なし
**ファイル**: `src/analyze/config/symbols.yaml`

## 概要

`symbols.yaml` に為替通貨ペアの定義を追加し、他のシンボルグループと同様に `get_symbols()` で取得できるようにする。

## 追加内容

```yaml
# 既存の indices, mag7, sectors, commodities の後に追加

currencies:
  jpy_crosses:
    - symbol: "USDJPY=X"
      name: "米ドル/円"
    - symbol: "EURJPY=X"
      name: "ユーロ/円"
    - symbol: "GBPJPY=X"
      name: "英ポンド/円"
    - symbol: "AUDJPY=X"
      name: "豪ドル/円"
    - symbol: "CADJPY=X"
      name: "カナダドル/円"
    - symbol: "CHFJPY=X"
      name: "スイスフラン/円"
```

## 使用方法

```python
from analyze.config import get_symbols

# 円クロス通貨を取得
symbols = get_symbols("currencies", "jpy_crosses")
# ['USDJPY=X', 'EURJPY=X', 'GBPJPY=X', 'AUDJPY=X', 'CADJPY=X', 'CHFJPY=X']
```

## 検証方法

```python
# Python REPL で確認
from analyze.config import get_symbols, get_symbol_group

# シンボルリスト取得
symbols = get_symbols("currencies", "jpy_crosses")
print(symbols)

# グループ詳細取得
group = get_symbol_group("currencies", "jpy_crosses")
print(group)
```

## 受け入れ条件

- [ ] 6通貨ペアが正しく定義されている
- [ ] `get_symbols("currencies", "jpy_crosses")` でシンボルリストを取得できる
- [ ] 既存のシンボルグループに影響がない
- [ ] YAML の構文が正しい

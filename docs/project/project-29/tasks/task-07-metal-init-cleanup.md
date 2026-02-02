# Task 07: metal.py - __init__メソッドのクリーンアップ

## 概要

`DollarsIndexAndMetalsAnalyzer.__init__` メソッドから `db_path` 関連のコードを削除する。

## 詳細

### 変更箇所

25-39行目の`__init__`メソッド:

**変更前**:
```python
def __init__(self):
    load_project_env()
    fred_dir = os.environ.get("FRED_DIR")
    if fred_dir is None:
        raise ValueError("FRED_DIR environment variable not set")
    self.db_path = Path(fred_dir) / "FRED.db"
    self.fred_cache = HistoricalCache()
    self.analyzer = MarketPerformanceAnalyzer()
    self.price_metal = self._load_metal_price()
    self.price = self.load_price()
    self.cum_return = self.calc_return()
```

**変更後**:
```python
def __init__(self):
    load_project_env()
    self.fred_cache = HistoricalCache()
    self.analyzer = MarketPerformanceAnalyzer()
    self.price_metal = self._load_metal_price()
    self.price = self.load_price()
    self.cum_return = self.calc_return()
```

### 削除項目

- `fred_dir = os.environ.get("FRED_DIR")` (31行目)
- `if fred_dir is None:` (32行目)
- `raise ValueError("FRED_DIR environment variable not set")` (33行目)
- `self.db_path = Path(fred_dir) / "FRED.db"` (34行目)

## 受け入れ条件

- [ ] `self.db_path` への参照が削除されている
- [ ] `FRED_DIR` 環境変数のチェックが削除されている
- [ ] 型チェック (`make typecheck`) が通る
- [ ] リント (`make lint`) が通る

## 依存関係

- Task 06 (インポート削除) に依存

## 見積もり時間

15分

# 実装計画: FREDデータソースをSQLiteからHistoricalCache(JSON)に移行

## 概要

`src/analyze/reporting/` 配下のモジュールで、SQLiteデータベースからのデータ読み込みを `HistoricalCache` のJSONキャッシュからの読み込みに変更する。

## 変更対象ファイル

| ファイル | 状況 | 対応 |
|----------|------|------|
| `us_treasury.py` | SQLite使用中 | **変更必要** |
| `metal.py` | SQLite使用中 | **変更必要** |
| `vix.py` | HistoricalCache使用済み | 変更不要 |

---

## 1. us_treasury.py の変更

### 1.1 インポートの変更

```python
# 追加
from market.fred.historical_cache import HistoricalCache

# 削除
import sqlite3
```

### 1.2 `load_fred_db_path()` 関数 (36-41行目)

**削除** - 不要になる

### 1.3 `plot_us_interest_rates_and_spread` 関数 (60-288行目)

**変更箇所** (106-123行目):

```python
# 変更前
db_path = db_path if db_path else load_fred_db_path()
conn = sqlite3.connect(db_path)
dfs = []
for series_id in series_id_interest_rates + series_id_spread:
    try:
        df_temp = (
            pd.read_sql(sql=f"SELECT * FROM '{series_id}'", con=conn)
            .rename(columns={series_id: "value"})
            .assign(variable=series_id)
        )
        dfs.append(df_temp)
    except pd.io.sql.DatabaseError:
        print(f"Warning: シリーズ '{series_id}' がデータベースに見つかりません。スキップします。")
conn.close()

# 変更後
cache = HistoricalCache()
dfs = []
for series_id in series_id_interest_rates + series_id_spread:
    df_temp = cache.get_series_df(series_id)
    if df_temp is not None:
        df_temp = df_temp.reset_index().rename(columns={"index": "date"})
        df_temp["variable"] = series_id
        dfs.append(df_temp)
    else:
        print(f"Warning: シリーズ '{series_id}' がキャッシュに見つかりません。スキップします。")
```

**シグネチャ変更**: `db_path` パラメータを削除

### 1.4 `load_yield_data_from_database` 関数 (292-347行目)

**関数名変更**: `load_yield_data_from_database` → `load_yield_data_from_cache`

**変更箇所** (323-334行目):

```python
# 変更前
dfs_yield = []
for table in table_list:
    df = (
        pd.read_sql(
            f"SELECT * FROM {table} ORDER BY date",
            sqlite3.connect(db_path),
            parse_dates=["date"],
        )
        .assign(tenor=table)
        .rename(columns={table: "value"})
    )
    dfs_yield.append(df)

# 変更後
cache = HistoricalCache()
dfs_yield = []
for series_id in table_list:
    df = cache.get_series_df(series_id)
    if df is not None:
        df = df.reset_index().rename(columns={"index": "date"})
        df["tenor"] = series_id
        dfs_yield.append(df)
```

**シグネチャ変更**: `db_path` パラメータを削除

### 1.5 `plot_us_corporate_bond_spreads` 関数 (576-650行目)

**変更箇所** (599-613行目):

```python
# 変更前
db_path = db_path if db_path else load_fred_db_path()
conn = sqlite3.connect(db_path)
spread_dict = {k: v["name_en"] for k, v in fred_series_id.items()}
dfs = [
    pd.read_sql(f"SELECT * FROM '{series_id}'", con=conn, parse_dates=["date"])
    .rename(columns={series_id: "value"})
    .assign(variable=series_id)
    for series_id in spread_dict
]
conn.close()

# 変更後
cache = HistoricalCache()
spread_dict = {k: v["name_en"] for k, v in fred_series_id.items()}
dfs = []
for series_id in spread_dict:
    df = cache.get_series_df(series_id)
    if df is not None:
        df = df.reset_index().rename(columns={"index": "date"})
        df["variable"] = series_id
        dfs.append(df)
```

**シグネチャ変更**: `db_path` パラメータを削除

---

## 2. metal.py の変更

### 2.1 インポートの削除

```python
# 削除
import os
import sqlite3
```

※ `HistoricalCache` は既にインポート済み

### 2.2 `__init__` メソッド (25-39行目)

```python
# 変更前
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

# 変更後
def __init__(self):
    load_project_env()
    self.fred_cache = HistoricalCache()
    self.analyzer = MarketPerformanceAnalyzer()
    self.price_metal = self._load_metal_price()
    self.price = self.load_price()
    self.cum_return = self.calc_return()
```

### 2.3 ヘルパーメソッドの追加

```python
def _load_dollars_index(self) -> pd.DataFrame:
    """ドル指数データをキャッシュから読み込む。

    Returns
    -------
    pd.DataFrame
        DTWEXAFEGS（ドル指数）データ

    Raises
    ------
    ValueError
        キャッシュにデータがない場合
    """
    df = self.fred_cache.get_series_df("DTWEXAFEGS")
    if df is None:
        raise ValueError(
            "DTWEXAFEGS not found in cache. "
            "Run: HistoricalCache().sync_series('DTWEXAFEGS')"
        )
    return df.rename_axis("Date")
```

### 2.4 `load_price` メソッド (61-92行目)

```python
# 変更前
def load_price(self):
    conn = sqlite3.connect(self.db_path)
    df_dollars = (
        pd.read_sql("SELECT * from DTWEXAFEGS", con=conn, parse_dates="date")
        .rename(columns={"date": "Date"})
        .set_index("Date")
    )
    # ...

# 変更後
def load_price(self):
    df_dollars = self._load_dollars_index()
    # ...
```

### 2.5 `calc_return` メソッド (95-122行目)

```python
# 変更前
def calc_return(self, start_date: str = "2020-01-01"):
    conn = sqlite3.connect(self.db_path)
    df_dollars = (
        pd.read_sql("SELECT * from DTWEXAFEGS", con=conn, parse_dates="date")
        .rename(columns={"date": "Date"})
        .set_index("Date")
    )
    # ...

# 変更後
def calc_return(self, start_date: str = "2020-01-01"):
    df_dollars = self._load_dollars_index()
    # ...
```

---

## 削除するコード一覧

### us_treasury.py

| 行 | 内容 |
|----|------|
| 7行目 | `import sqlite3` |
| 36-41行目 | `load_fred_db_path()` 関数全体 |

### metal.py

| 行 | 内容 |
|----|------|
| 7行目 | `import os` |
| 8行目 | `import sqlite3` |
| 31-34行目 | `fred_dir` 取得と `self.db_path` 設定 |

---

## 検証方法

### us_treasury.py

```python
from analyze.reporting.us_treasury import (
    plot_us_interest_rates_and_spread,
    load_yield_data_from_cache,
    plot_us_corporate_bond_spreads,
)

# 1. 金利チャートの表示確認
plot_us_interest_rates_and_spread(start_date="2020-01-01")

# 2. イールドデータのロード確認
df = load_yield_data_from_cache()
print(df.head())

# 3. 社債スプレッドチャートの表示確認
plot_us_corporate_bond_spreads()
```

### metal.py

```python
from analyze.reporting.metal import DollarsIndexAndMetalsAnalyzer

# 1. インスタンス化（データロード確認）
analyzer = DollarsIndexAndMetalsAnalyzer()

# 2. 各プロパティの確認
print(analyzer.price.head())
print(analyzer.cum_return.head())

# 3. プロット確認
fig = analyzer.plot_us_dollar_index_and_metal_price()
fig.show()
```

---

## 前提条件

以下のシリーズがキャッシュされている必要がある：

| シリーズID | 用途 |
|------------|------|
| `DFF`, `DGS1MO`〜`DGS30` | 金利・イールドカーブ |
| `T10Y3M`, `T10Y2Y` | イールドスプレッド |
| `BAMLC0A*`, `BAMLH0A*` | 社債スプレッド |
| `DTWEXAFEGS` | ドル指数 |

キャッシュ同期コマンド：
```bash
uv run python -m market.fred.scripts.sync_historical --all
```

---

## 実装順序

1. **us_treasury.py**
   1. `import sqlite3` を削除、`HistoricalCache` インポート追加
   2. `load_fred_db_path()` 関数を削除
   3. `load_yield_data_from_database` → `load_yield_data_from_cache` に変更
   4. `plot_us_interest_rates_and_spread` のデータ読み込み部分を変更
   5. `plot_us_corporate_bond_spreads` のデータ読み込み部分を変更

2. **metal.py**
   1. `import os` と `import sqlite3` を削除
   2. `__init__` から `db_path` 関連のコードを削除
   3. `_load_dollars_index()` ヘルパーメソッドを追加
   4. `load_price()` を修正
   5. `calc_return()` を修正

3. **動作確認**

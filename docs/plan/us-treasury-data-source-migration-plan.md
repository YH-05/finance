# プラン: us_treasury.py のデータソースをSQLiteからHistoricalCache(JSON)に変更

## 概要

`src/analyze/reporting/us_treasury.py` の3つの関数で、SQLiteデータベースからのデータ読み込みを `HistoricalCache` のJSONキャッシュからの読み込みに変更する。

## 変更対象ファイル

- `src/analyze/reporting/us_treasury.py`

## 変更内容

### 1. インポートの追加

```python
# 追加
from market.fred.historical_cache import HistoricalCache

# 削除（不要になる）
import sqlite3
# load_fred_db_path 関数も不要になる
```

### 2. `plot_us_interest_rates_and_spread` 関数 (60-288行目)

**変更前** (106-123行目):
```python
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
```

**変更後**:
```python
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

**シグネチャ変更**:
- `db_path` パラメータを `cache_path` に変更（または削除）

### 3. `load_yield_data_from_database` 関数 (292-347行目)

**関数名変更**: `load_yield_data_from_database` → `load_yield_data_from_cache`

**変更前** (323-334行目):
```python
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
```

**変更後**:
```python
cache = HistoricalCache()
dfs_yield = []
for series_id in table_list:
    df = cache.get_series_df(series_id)
    if df is not None:
        df = df.reset_index().rename(columns={"index": "date"})
        df["tenor"] = series_id
        dfs_yield.append(df)
```

**シグネチャ変更**:
- `db_path` パラメータを削除（または `cache_path` に変更）

### 4. `plot_us_corporate_bond_spreads` 関数 (576-650行目)

**変更前** (599-613行目):
```python
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
```

**変更後**:
```python
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

**シグネチャ変更**:
- `db_path` パラメータを削除（または `cache_path` に変更）

### 5. 削除する関数・コード

- `load_fred_db_path()` 関数 (36-41行目) - 不要になる
- `import sqlite3` - 不要になる

## 後方互換性の考慮

- `db_path` パラメータを持つ関数は、パラメータを `cache_path: Path | None = None` に変更し、`HistoricalCache(base_path=cache_path)` として使用することで互換性を維持可能
- または、パラメータを完全に削除してシンプルにする（推奨）

## 検証方法

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
print(df.columns)

# 3. 社債スプレッドチャートの表示確認
plot_us_corporate_bond_spreads()
```

## 実装順序

1. インポート文の変更
2. `load_fred_db_path()` 関数の削除
3. `load_yield_data_from_database` → `load_yield_data_from_cache` に変更
4. `plot_us_interest_rates_and_spread` のデータ読み込み部分を変更
5. `plot_us_corporate_bond_spreads` のデータ読み込み部分を変更
6. 動作確認

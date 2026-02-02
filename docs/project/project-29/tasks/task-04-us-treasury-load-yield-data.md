# Task 04: us_treasury.py - load_yield_data_from_database関数の変更

## 概要

`load_yield_data_from_database` 関数を `load_yield_data_from_cache` にリネームし、`HistoricalCache`を使用するように変更する。

## 詳細

### 関数名変更

- `load_yield_data_from_database` → `load_yield_data_from_cache`

### 変更箇所

323-334行目のデータ読み込み部分:

**変更前**:
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

### シグネチャ変更

- `db_path: Path | None = None` パラメータを削除
- 関数名を `load_yield_data_from_cache` に変更

### Docstring更新

関数のDocstringを更新し、キャッシュからデータを読み込むことを明記する。

## 受け入れ条件

- [ ] 関数名が `load_yield_data_from_cache` に変更されている
- [ ] `db_path` パラメータが削除されている
- [ ] `HistoricalCache` を使用してデータを取得している
- [ ] 戻り値のDataFrameの構造が変更前と同等
- [ ] Docstringが更新されている
- [ ] 型チェック (`make typecheck`) が通る

## 依存関係

- Task 01 (インポート変更) に依存
- Task 02 (load_fred_db_path削除) に依存

## 見積もり時間

30分

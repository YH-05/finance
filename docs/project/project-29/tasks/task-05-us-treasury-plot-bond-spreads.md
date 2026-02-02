# Task 05: us_treasury.py - plot_us_corporate_bond_spreads関数の変更

## 概要

`plot_us_corporate_bond_spreads` 関数のデータ読み込み部分をSQLiteから`HistoricalCache`に変更する。

## 詳細

### 変更箇所

599-613行目のデータ読み込み部分:

**変更前**:
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

### シグネチャ変更

- `db_path: Path | None = None` パラメータを削除

## 受け入れ条件

- [ ] `db_path` パラメータが関数シグネチャから削除されている
- [ ] `HistoricalCache` を使用してデータを取得している
- [ ] `sqlite3.connect` の呼び出しが削除されている
- [ ] データフレームのカラム構造が変更前と同等
- [ ] 型チェック (`make typecheck`) が通る
- [ ] 関数が正常に動作する（プロット表示確認）

## 依存関係

- Task 01 (インポート変更) に依存
- Task 02 (load_fred_db_path削除) に依存

## 見積もり時間

30分

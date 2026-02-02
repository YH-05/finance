# Task 03: us_treasury.py - plot_us_interest_rates_and_spread関数の変更

## 概要

`plot_us_interest_rates_and_spread` 関数のデータ読み込み部分をSQLiteから`HistoricalCache`に変更する。

## 詳細

### 変更箇所

106-123行目のデータ読み込み部分:

**変更前**:
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

### シグネチャ変更

- `db_path: Path | None = None` パラメータを削除

## 受け入れ条件

- [ ] `db_path` パラメータが関数シグネチャから削除されている
- [ ] `HistoricalCache` を使用してデータを取得している
- [ ] `sqlite3.connect` の呼び出しが削除されている
- [ ] データフレームのカラム構造が変更前と同等（date, value, variable）
- [ ] 型チェック (`make typecheck`) が通る
- [ ] 関数が正常に動作する（プロット表示確認）

## 依存関係

- Task 01 (インポート変更) に依存
- Task 02 (load_fred_db_path削除) に依存

## 見積もり時間

30分

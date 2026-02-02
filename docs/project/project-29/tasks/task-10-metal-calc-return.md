# Task 10: metal.py - calc_returnメソッドの変更

## 概要

`DollarsIndexAndMetalsAnalyzer.calc_return` メソッドをSQLiteから`HistoricalCache`を使用するように変更する。

## 詳細

### 変更箇所

95-122行目の`calc_return`メソッド:

**変更前**:
```python
def calc_return(self, start_date: str = "2020-01-01"):
    conn = sqlite3.connect(self.db_path)
    df_dollars = (
        pd.read_sql("SELECT * from DTWEXAFEGS", con=conn, parse_dates="date")
        .rename(columns={"date": "Date"})
        .set_index("Date")
    )
    # ...
```

**変更後**:
```python
def calc_return(self, start_date: str = "2020-01-01"):
    df_dollars = self._load_dollars_index()
    # ...（残りのコードは変更なし）
```

### 削除対象

- `conn = sqlite3.connect(self.db_path)` 行
- `pd.read_sql(...)` を使ったドル指数の読み込み処理

## 受け入れ条件

- [ ] `sqlite3.connect` の呼び出しが削除されている
- [ ] `_load_dollars_index()` を使用してドル指数を取得している
- [ ] 戻り値のDataFrameの構造が変更前と同等
- [ ] 型チェック (`make typecheck`) が通る
- [ ] メソッドが正常に動作する

## 依存関係

- Task 08 (_load_dollars_indexヘルパー追加) に依存

## 見積もり時間

20分

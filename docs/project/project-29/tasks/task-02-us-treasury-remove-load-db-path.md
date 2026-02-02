# Task 02: us_treasury.py - load_fred_db_path関数の削除

## 概要

`src/analyze/reporting/us_treasury.py` から不要になる `load_fred_db_path()` 関数を削除する。

## 詳細

### 削除対象

36-41行目の関数全体:

```python
def load_fred_db_path() -> Path:
    """FREDのSQLiteデータベースファイルのパスを取得する"""
    fred_dir = os.environ.get("FRED_DIR")
    if fred_dir is None:
        raise ValueError("FRED_DIR environment variable not set")
    return Path(fred_dir) / "FRED.db"
```

## 受け入れ条件

- [ ] `load_fred_db_path()` 関数が削除されている
- [ ] 関数への参照が残っていない
- [ ] 型チェック (`make typecheck`) が通る
- [ ] リント (`make lint`) が通る

## 依存関係

- Task 01 (インポート変更) に依存

## 見積もり時間

10分

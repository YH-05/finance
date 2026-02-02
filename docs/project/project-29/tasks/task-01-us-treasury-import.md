# Task 01: us_treasury.py - インポート文の変更

## 概要

`src/analyze/reporting/us_treasury.py` のインポート文を変更し、SQLiteから`HistoricalCache`へ移行する準備をする。

## 詳細

### 変更内容

1. **追加するインポート**:
   ```python
   from market.fred.historical_cache import HistoricalCache
   ```

2. **削除するインポート**:
   ```python
   import sqlite3
   ```

### 対象行

- 7行目: `import sqlite3` → 削除
- 24行目付近: `HistoricalCache` インポートを追加

## 受け入れ条件

- [ ] `import sqlite3` が削除されている
- [ ] `from market.fred.historical_cache import HistoricalCache` が追加されている
- [ ] 型チェック (`make typecheck`) が通る
- [ ] リント (`make lint`) が通る

## 依存関係

- 依存なし（最初に実施可能）

## 見積もり時間

15分

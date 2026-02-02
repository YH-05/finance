# Task 06: metal.py - 不要なインポートの削除

## 概要

`src/analyze/reporting/metal.py` から不要になる `os` と `sqlite3` のインポートを削除する。

## 詳細

### 削除対象

- 7行目: `import os`
- 8行目: `import sqlite3`

### 注意事項

- `HistoricalCache` は既にインポート済み（16行目）なので追加不要

## 受け入れ条件

- [ ] `import os` が削除されている
- [ ] `import sqlite3` が削除されている
- [ ] 型チェック (`make typecheck`) が通る
- [ ] リント (`make lint`) が通る

## 依存関係

- 依存なし（最初に実施可能、us_treasury.pyの変更と並行可能）

## 見積もり時間

10分

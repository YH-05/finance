# 議論メモ: launchd 定期実行スクリプトのメンテナンス

**日付**: 2026-04-12
**議論ID**: disc-2026-04-12-launchd-maintenance
**参加**: ユーザー + AI

## 背景・コンテキスト

quants プロジェクトの Mac mini 上で launchd による定期実行スクリプトの現状を棚卸し。
前回の議論（2026-04-04）で EarningsPipeline の4つの plist を設定済み。
今回は未インストールの plist 登録、エラー修正、不要ファイル削除、キャッシュ安定性改善を実施。

## 議論のサマリー

### 1. 未インストール plist の登録

scripts/ に存在するが ~/Library/LaunchAgents/ にインストールされていなかった4つの plist を登録:

| plist | スケジュール | 用途 |
|-------|------------|------|
| `com.quants.etfcom-daily` | 毎日 03:00 | ETF.com 日次データ収集 |
| `com.quants.etfcom-weekly` | 日曜 04:00 | ETF.com 週次データ収集 |
| `com.quants.etfcom-monthly` | 毎月1日 05:00 | ETF.com 月次データ収集 |
| `com.quants.fred-sync` | 毎日 06:00 | FRED 経済指標同期 |

全て `plutil -lint` OK → `cp` → `launchctl load` で登録完了。

### 2. polymarket-collect エラー修正

**症状**: exit code 1、ログに 201,641件の SQLite I/O エラー

**原因**:
- キャッシュ DB（`/Volumes/personal_folder/Projects/quants/data/cache/market_data.db`、106MB）が NAS 上にあり、ネットワーク不安定時に `disk I/O error` / `database disk image is malformed` が発生
- plist に `--env-file .env` がなかった（他の pipeline plist との設計不統一）

**対処**:
- キャッシュ DB を削除（一時データのため問題なし）
- plist に `--env-file /Users/yuki/Desktop/quants/.env` を追加
- `launchctl unload` → `load` で再登録
- ログクリア
- 修正済み plist を `scripts/com.quants.polymarket-collect.plist` に保存

### 3. 旧ファイル削除

| 削除ファイル | 理由 |
|------------|------|
| `scripts/com.finance.news-collector.plist` | 旧プロジェクト（/Users/yukihata/Desktop/finance）のパスのまま。Claude Agent SDK 依存で現在不使用 |
| `scripts/collect-news.sh` | 上記 plist から参照されるシェルスクリプト。同じく不使用 |

### 4. キャッシュ DB のローカル分離

NAS 上の SQLite キャッシュが不安定なため、キャッシュのみローカルに配置する変更を実施:

- `src/market/cache/cache.py` の `_resolve_cache_db_path()` に `CACHE_DIR` 環境変数の優先チェックを追加
- `.env` に `CACHE_DIR=/Users/yuki/Desktop/quants/data` を追加
- テスト追加（`CACHE_DIR` 優先テスト + 既存テストの `CACHE_DIR=""` パッチ）
- 208 passed, 0 failed

## 決定事項

| ID | 内容 | コンテキスト |
|----|------|------------|
| dec-2026-04-12-001 | etfcom-daily/weekly/monthly + fred-sync の4つの plist をインストール | scripts/ にあったが未インストールだった |
| dec-2026-04-12-002 | polymarket-collect の plist に --env-file .env を追加 | 他の pipeline plist との設計統一 |
| dec-2026-04-12-003 | NAS 上のキャッシュ DB（106MB）を削除、ログクリア | 201,641件の I/O エラーが発生していた |
| dec-2026-04-12-004 | キャッシュ DB をローカルに分離（CACHE_DIR 環境変数導入） | NAS 上の SQLite はファイルロックが不安定 |
| dec-2026-04-12-005 | com.finance.news-collector.plist と collect-news.sh を削除 | 旧プロジェクトの遺物、現在不使用 |

## アクションアイテム

| ID | 内容 | 優先度 | 状態 |
|----|------|--------|------|
| act-2026-04-12-001 | polymarket-collect の修正済み plist を scripts/ に保存 | 低 | 完了 |
| act-2026-04-12-002 | CACHE_DIR 変更（cache.py + .env + テスト）のコミット・PR | 中 | pending |
| act-2026-04-12-003 | polymarket-collect の次回実行（0:30）でエラー解消を確認 | 中 | pending |

## 現在の launchd スケジュール全体像

| 時刻 | ジョブ | 状態 |
|------|--------|------|
| 0:30, 6:30, 12:30, 18:30 | `com.quants.polymarket-collect` | 修正済み |
| 01:00 | `com.quants.pipeline-nasdaq` | 稼働中 |
| 02:00 | `com.quants.pipeline-alphavantage` | 稼働中 |
| 02:00 | `com.quants.pipeline-sec-edgar` | 稼働中 |
| 02:00 | `com.quants.pipeline-yfinance` | 稼働中 |
| 03:00 | `com.quants.etfcom-daily` | 新規登録 |
| 日曜 04:00 | `com.quants.etfcom-weekly` | 新規登録 |
| 毎月1日 05:00 | `com.quants.etfcom-monthly` | 新規登録 |
| 06:00 | `com.quants.fred-sync` | 新規登録 |
| 08:00 | `com.quants.edinet-sync` | 稼働中 |
| 常時 | `com.quants.neo4j` | 稼働中 |

## 次回の議論トピック

- NAS 定期同期の自動化（act-2026-04-08-013）
- AV free tier 25コール/日 → Pro プラン検討
- edinet-sync / polymarket-collect の plist がリポジトリの scripts/ と ~/Library/LaunchAgents/ で二重管理になっている問題 → 同期の仕組み検討

## 変更ファイル

| ファイル | 変更内容 |
|---------|---------|
| `src/market/cache/cache.py` | `_resolve_cache_db_path()` に CACHE_DIR 優先チェック追加 |
| `.env` | `CACHE_DIR=/Users/yuki/Desktop/quants/data` 追加 |
| `tests/market/unit/cache/test_cache.py` | CACHE_DIR テスト追加、既存テスト修正 |
| `scripts/com.quants.polymarket-collect.plist` | 新規（修正済み plist をリポジトリに保存） |
| `scripts/com.finance.news-collector.plist` | 削除 |
| `scripts/collect-news.sh` | 削除 |

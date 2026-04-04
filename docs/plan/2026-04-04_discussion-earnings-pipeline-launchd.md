# 議論メモ: EarningsPipeline launchd 定期実行設定

**日付**: 2026-04-04
**議論ID**: disc-2026-04-04-earnings-pipeline-launchd
**参加**: ユーザー + AI

## 背景・コンテキスト

PR #3887 で EarningsPipeline（market.pipeline）パッケージが main にマージ済み。
4フェーズのパイプライン（NASDAQ → AV → SEC EDGAR → yfinance）を launchd で定期実行するための設定を行った。

## 議論のサマリー

### 1. パイプラインの実装状況確認

4つのデータソースの実装状況を確認：
- **NASDAQ**: NasdaqClient + ScreenerCollector 完成、617+ テスト
- **AlphaVantage**: Client + Storage(8テーブル) + Collector 完成
- **SEC EDGAR**: EdgarFetcher + TextExtractor + BatchProcessor 完成
- **yfinance**: YFinanceFetcher（軽量ラッパー）

EarningsPipeline が4フェーズを統合（`python -m market.pipeline`）。

### 2. データ保存先の設定

- `DATA_DIR=/Volumes/personal_folder/Projects/quants/data`（.env）
- 各 DB: `DATA_DIR/sqlite/{name}.db`（`get_db_path()` で解決）
- 環境変数 `PIPELINE_*_DB_PATH` で個別上書き可能

### 3. launchd 設計の議論

**初期案**: 1つの統合 plist（4フェーズ直列実行）
→ テスト実行で問題発覚：
  - `uv run` の子プロセスでログが出ない（完了まで 0 バイト）
  - AV レートリミット（5req/min, 20req/hr）で長時間ブロック
  - `/bin/bash` ラッパーは macOS TCC 制限で Desktop アクセス不可

**最終設計**: 4つの独立した plist に分離
- `uv run --env-file .env` で `.env` を直接読み込み（TCC 回避）
- Phase 2/3/4 は並列実行（互いに依存しない）

### 4. priority 計算の導入

NASDAQ Calendar から enqueue 時に決算日の近さを priority に設定：
```
priority = max(0, 30 - abs(days_until_earnings))
```
AV の `get_pending()` が `ORDER BY priority DESC` で返すため、直近の決算銘柄が優先処理される。

### 5. SEC EDGAR Identity 修正

- `.env` に `SEC_EDGAR_IDENTITY` が未設定だった → 追加
- `collector_sec.py` で edgartools の `set_identity()` を呼ぶ処理を追加
  - PathFinder パターンで src/edgar との名前空間衝突を回避

### 6. SEC EDGAR データ抽出バグ修正

- 旧コード: `financials.to_dataframe()` を呼んでいたが、edgartools API が変更されていた
- 修正: `financials.get_revenue()` 等の `get_*` ヘルパーベースに書き換え
- 結果: 179行/92銘柄のデータ蓄積に成功

### 7. MCP Neo4j 設定の不一致を発見

- `.mcp.json` は `bolt://localhost:7690` を指定
- Docker は `7687` でマッピング
- `.mcp.json` を 7687 + 正しいパスワードに修正

## 決定事項

| ID | 内容 | コンテキスト |
|----|------|------------|
| dec-2026-04-04-001 | 4つの独立した launchd plist に分離（NASDAQ 01:00、AV/SEC/yfinance 02:00 並列） | 統合版は AV レートリミットで全体がブロックされるため |
| dec-2026-04-04-002 | priority = 決算日の近さ（max 30）で enqueue | note記事作成のために直近決算銘柄を優先処理 |
| dec-2026-04-04-003 | SEC/yfinance は AV 完了を待たない（独立実行） | 3フェーズ並列で効率化 |
| dec-2026-04-04-004 | `uv run --env-file .env` で環境変数を読み込む（plist に秘密情報を埋め込まない） | macOS TCC 制限回避 + セキュリティ |
| dec-2026-04-04-005 | SEC EDGAR collector を get_* ヘルパーベースに書き換え | edgartools の Financials.to_dataframe() が廃止されていた |
| dec-2026-04-04-006 | .mcp.json の Neo4j 接続先を bolt://localhost:7687 に修正 | Docker は 7687、MCP 設定が 7690 で不一致だった |

## アクションアイテム

| ID | 内容 | 優先度 | 状態 |
|----|------|--------|------|
| act-2026-04-04-001 | collector_sec.py の get_operating_cash_flow() が None を返す問題の調査 | 中 | pending |
| act-2026-04-04-002 | 既存キューの priority=0 エントリを決算日ベースで再計算（UPDATE文） | 低 | pending |
| act-2026-04-04-003 | SEC EDGAR の残り pending 280件を処理（次回 02:00 に自動実行） | 低 | 自動 |
| act-2026-04-04-004 | Claude Code 再起動後に Neo4j MCP 接続確認（7687） | 高 | pending |

## テスト結果

| Phase | 結果 | データ蓄積 |
|-------|------|-----------|
| Phase 1 (NASDAQ) | ✅ 381件、153秒 | `nc_earnings_calendar`: 381行 |
| Phase 2 (AV) | ✅ 17件（25コール上限） | `av_earnings`: 1,180行 |
| Phase 3 (SEC) | ✅ 100件、0エラー、517秒 | `se_financial_statements`: 179行 |
| Phase 4 (yfinance) | ✅ 100件、161秒 | `yf_daily_prices`: 24,843行 |

## 変更ファイル

| ファイル | 変更内容 |
|---------|---------|
| `src/market/pipeline/collector_nasdaq.py` | `_compute_priority()` 追加、enqueue 時に priority 設定 |
| `src/market/pipeline/collector_sec.py` | `_configure_identity()` 追加、`collect_symbol()` を get_* ベースに書き換え |
| `scripts/com.quants.pipeline-nasdaq.plist` | 新規（01:00） |
| `scripts/com.quants.pipeline-alphavantage.plist` | 新規（02:00） |
| `scripts/com.quants.pipeline-sec-edgar.plist` | 新規（02:00） |
| `scripts/com.quants.pipeline-yfinance.plist` | 新規（02:00） |
| `.env` | `ALPHA_VANTAGE_API_KEY`, `SEC_EDGAR_IDENTITY` 追加 |
| `.mcp.json` | Neo4j URI を 7690→7687、パスワード修正 |

## launchd スケジュール一覧（現在）

| 時刻 | ジョブ |
|------|--------|
| 01:00 | `com.quants.pipeline-nasdaq` |
| 02:00 | `com.quants.pipeline-alphavantage` |
| 02:00 | `com.quants.pipeline-sec-edgar` |
| 02:00 | `com.quants.pipeline-yfinance` |
| 08:00 | `com.quants.edinet-sync` |

## 次回の議論トピック

- SEC EDGAR の `operating_cashflow` が None になる問題の調査・修正
- AV free tier 25コール/日で全銘柄処理に約23日 → Pro プラン検討
- note 記事作成パイプラインとの連携設計

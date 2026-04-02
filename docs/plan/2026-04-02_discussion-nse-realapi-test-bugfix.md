# 議論メモ: NSE モジュール実機テスト + バグ修正

**日付**: 2026-04-02
**議論ID**: disc-2026-04-02-nse-realapi-test-bugfix
**参加**: ユーザー + AI

## 背景・コンテキスト

PR #3878 マージ後、NSE モジュールの実機テストとして RELIANCE Industries の全企業データ取得を実施。日本 IP からの NSE API アクセスにおける3つのバグを発見・修正した。

## 実機テスト結果

### テスト対象: RELIANCE Industries (NSE: RELIANCE)

| データ種別 | API エンドポイント | 結果 | CSV 出力 |
|-----------|-------------------|------|----------|
| Quote（株価） | `/api/quote-equity` | Last: ₹1,350.9, Change: -1.34% | `RELIANCE_quote_*.csv` |
| Financial Results（5Q） | `/api/results-comparision` | Q3 FY25: PAT ₹8,721Cr, EPS ₹6.44 | `RELIANCE_financials_*.csv` |
| Search（17件） | `/api/search/autocomplete` | RELIANCE 含む17関連銘柄 | `RELIANCE_search_*.csv` |
| Event Calendar（101件） | `/api/event-calendar` | 全101件（RELIANCE 直近予定なし） | `event_calendar_*.csv` |
| Market Status | `/api/marketStatus` | Capital Market: Closed, Commodity: Open | `market_status_*.csv` |

CSV 出力先: `data/cache/nse/`

## 発見・修正したバグ (3件)

### Bug 1: brotli 依存未宣言 (dec-2026-04-02-007)

- **現象**: `response.json()` で `UnicodeDecodeError: 'utf-8' codec can't decode byte 0xce`
- **原因**: NSE API が `Content-Encoding: br`（Brotli）を Accept-Encoding に関わらず強制返却。httpx は `brotli` パッケージがないとデコードできない。
- **修正**: `pyproject.toml` に `brotli>=1.2.0` を追加

### Bug 2: Cookie 取得タイムアウト (dec-2026-04-02-008)

- **現象**: `httpx.ReadTimeout: The read operation timed out`（`_ensure_cookies` 内）
- **原因**: `www.nseindia.com` ホームページが日本 IP から **HTTP 403** を返す（Akamai WAF）。httpx はリダイレクト等で30秒タイムアウトまでハング。
- **発見**: NSE API エンドポイント自体は **Cookie なしで直接アクセス可能**
- **修正**: `_ensure_cookies()` に `httpx.TimeoutException` キャッチ追加。タイムアウト/非2xx 時も `_cookie_acquired_at` を設定して繰り返し失敗を防止。
- **テスト追加**: `test_正常系_Cookie取得タイムアウトでフォールバック`, `test_正常系_Cookie取得403でフォールバック`

### Bug 3: Financial Results の symbol が空 (dec-2026-04-02-009)

- **現象**: `FinancialResult.symbol` が空文字列（統合テスト失敗）
- **原因**: NSE API の `resCmpData` 内に `symbol` フィールドが含まれない仕様
- **修正**: `parse_financial_results()` に `symbol` キーワード引数を追加。`CorporateCollector.get_financial_results()` からリクエスト時のシンボルを渡す。レスポンスに symbol があればそちらを優先。
- **テスト追加**: `test_正常系_symbol引数でレスポンスにsymbolがない場合に補完`, `test_正常系_レスポンスのsymbolが引数より優先`

## 決定事項

| ID | 内容 | コンテキスト |
|----|------|------------|
| dec-2026-04-02-007 | pyproject.toml に brotli>=1.2.0 を追加 | NSE API が Brotli 圧縮を強制返却 |
| dec-2026-04-02-008 | _ensure_cookies に TimeoutException キャッチ追加、タイムアウト/403 でフォールバック | 日本 IP から NSE ホームページが 403 |
| dec-2026-04-02-009 | parse_financial_results に symbol キーワード引数追加 | NSE API が resCmpData に symbol を含まない |

## アクションアイテム

| ID | 内容 | 優先度 | ステータス |
|----|------|--------|-----------|
| act-2026-04-02-009 | NSE 統合テスト実機実行 | 高 | in_progress（日本IPから実施済み、残: コミット・PR） |
| act-2026-04-02-012 | NSE バグ修正3件 + テスト4件をコミット・PR | 高 | pending |

## 変更ファイル

| ファイル | 変更内容 |
|---------|---------|
| `pyproject.toml` | `brotli>=1.2.0` 追加 |
| `src/market/nse/session.py` | `_ensure_cookies` に TimeoutException キャッチ追加 |
| `src/market/nse/parsers.py` | `parse_financial_results` に `symbol` 引数追加 |
| `src/market/nse/collectors/corporate.py` | `get_financial_results` から `symbol` を渡す |
| `tests/market/nse/unit/test_session.py` | +2 テスト（タイムアウト・403 フォールバック） |
| `tests/market/nse/unit/test_parsers.py` | +2 テスト（symbol 補完・優先順位） |

## テスト結果

- セッションテスト: 40 passed (38 → 40, +2)
- パーサーテスト含む全 NSE unit+property: 381 passed (+4)

## 次のステップ

1. バグ修正をコミット・PR（act-2026-04-02-012）
2. インド市場開場時間（IST 9:15-15:30）に統合テスト全項目実行
3. BSE BhavcopyCollector CSV 対応（act-2026-04-02-010）

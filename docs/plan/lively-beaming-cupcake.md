# Earnings Data Pipeline 実装計画

## Context

米国株の財務データをヒストリカルで取得し、DBに毎日蓄積するパイプラインを構築する。
NASDAQ決算カレンダーで決算発表銘柄を特定し、Alpha Vantage（EPS・サプライズ + Company Overview）、
SEC EDGAR（edgartools経由の財務諸表）、yfinance（株価）からデータを収集する。

ユニバースの限定はしない。NASDAQカレンダーにリストされた全銘柄を対象とする。

### 制約
- Alpha Vantage Free プラン: **25リクエスト/日**
- SEC EDGAR: 10リクエスト/秒（edgartools経由、XBRL対応は2009年〜）
- yfinance: 実質無制限（curl_cffi）
- DBファイルはソース別に分離、全テーブルに `fetched_at` タイムスタンプ

---

## アーキテクチャ

```
Phase 1: NASDAQ Earnings Calendar ──→ nasdaq_calendar.db
    │  (決算銘柄の特定 + 収集キュー投入)
    ▼
Phase 2: Alpha Vantage ──→ alphavantage.db (既存)
    │  EARNINGS (決算発表後のみ) + OVERVIEW (日次ローテーション)
    │
Phase 3: SEC EDGAR (edgartools) ──→ sec_edgar.db
    │  10-K/10-Q の IS/BS/CF (初回: 全ヒストリカル、以後: 新規filing のみ)
    │
Phase 4: yfinance ──→ yfinance.db
       日次株価 OHLCV
```

---

## パッケージ構成

`src/market/pipeline/` に新規作成:

```
src/market/pipeline/
├── __init__.py              # Public API exports
├── __main__.py              # python -m market.pipeline エントリポイント
├── constants.py             # DB名、テーブル名、環境変数名
├── errors.py                # PipelineError 階層
├── models.py                # 全 frozen dataclass レコード
├── ticker_normalizer.py     # normalize_ticker(symbol, target)
├── queue.py                 # CollectionQueue (収集状態管理)
├── storage_nasdaq.py        # NasdaqCalendarStorage
├── storage_sec.py           # SecEdgarStorage
├── storage_yfinance.py      # YFinanceStorage
├── collector_nasdaq.py      # Phase 1: NasdaqCalendarCollector
├── collector_sec.py         # Phase 3: SecEdgarCollector (edgartools)
├── collector_yfinance.py    # Phase 4: YFinanceCollector
├── pipeline.py              # EarningsPipeline オーケストレーター
└── cli.py                   # CLI (argparse)
```

既存パッケージ（alphavantage, nasdaq, yfinance, edgar）は変更しない。

---

## DB ファイル分離

| DB ファイル | テーブル | プレフィックス |
|---|---|---|
| `data/sqlite/nasdaq_calendar.db` | `nc_earnings_calendar`, `nc_collection_queue` | `nc_` |
| `data/sqlite/alphavantage.db` (既存) | `av_earnings`, `av_company_overview` (既存) | `av_` |
| `data/sqlite/sec_edgar.db` | `se_financial_statements` | `se_` |
| `data/sqlite/yfinance.db` | `yf_daily_prices` | `yf_` |

---

## テーブルスキーマ

### nc_earnings_calendar (nasdaq_calendar.db)

```sql
CREATE TABLE IF NOT EXISTS nc_earnings_calendar (
    symbol TEXT NOT NULL,
    earnings_date TEXT NOT NULL,             -- ISO 8601
    name TEXT,
    eps_estimate TEXT,
    eps_actual TEXT,
    surprise TEXT,
    fiscal_quarter_ending TEXT,
    market_cap TEXT,
    time TEXT,                               -- time-pre-market / time-after-hours
    no_of_ests TEXT,
    last_year_rpt_dt TEXT,
    last_year_eps TEXT,
    fetched_at TEXT NOT NULL,
    PRIMARY KEY (symbol, earnings_date)
);
```

### nc_collection_queue (nasdaq_calendar.db)

```sql
CREATE TABLE IF NOT EXISTS nc_collection_queue (
    symbol TEXT NOT NULL,
    earnings_date TEXT NOT NULL,
    source TEXT NOT NULL,                    -- 'av_earnings', 'av_overview', 'sec_edgar', 'yfinance'
    status TEXT NOT NULL DEFAULT 'pending',  -- pending / completed / failed / skipped
    priority INTEGER NOT NULL DEFAULT 0,
    error_message TEXT,
    attempts INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    completed_at TEXT,
    PRIMARY KEY (symbol, earnings_date, source)
);
```

### se_financial_statements (sec_edgar.db)

edgartools の `to_dataframe()` 出力を正規化して格納する。

```sql
CREATE TABLE IF NOT EXISTS se_financial_statements (
    symbol TEXT NOT NULL,
    cik TEXT NOT NULL,
    statement_type TEXT NOT NULL,            -- 'income', 'balance_sheet', 'cash_flow'
    filing_type TEXT NOT NULL,               -- '10-K', '10-Q'
    period_end TEXT NOT NULL,                -- 期末日 (ISO 8601)
    concept TEXT NOT NULL,                   -- XBRL concept (例: us-gaap_NetIncomeLoss)
    label TEXT,                              -- 人間可読ラベル
    standard_concept TEXT,                   -- edgartools 標準化概念名
    value REAL,
    unit TEXT,                               -- 'USD', 'shares', 'USD/shares'
    filing_date TEXT,                        -- SEC filing 日
    fiscal_year TEXT,
    fiscal_period TEXT,                      -- 'FY', 'Q1', 'Q2', 'Q3', 'Q4'
    fetched_at TEXT NOT NULL,
    PRIMARY KEY (symbol, statement_type, filing_type, period_end, concept)
);
```

設計方針: edgartools の DataFrame を**行単位で格納**する（concept ごとに1行）。
これにより `standard_concept` でのクロス企業クエリ、任意期間の抽出が容易になる。

### yf_daily_prices (yfinance.db)

```sql
CREATE TABLE IF NOT EXISTS yf_daily_prices (
    symbol TEXT NOT NULL,
    date TEXT NOT NULL,
    open REAL NOT NULL,
    high REAL NOT NULL,
    low REAL NOT NULL,
    close REAL NOT NULL,
    volume INTEGER NOT NULL,
    fetched_at TEXT NOT NULL,
    PRIMARY KEY (symbol, date)
);
```

---

## ティッカー正規化

NASDAQ カレンダーのシンボルを各ソース向けに変換する関数。

```python
# ticker_normalizer.py
def normalize_ticker(nasdaq_symbol: str, target: Literal["nasdaq", "alphavantage", "sec_edgar", "yfinance"]) -> str:
    if target == "alphavantage":
        return nasdaq_symbol.split(".")[0]    # GEF.B → GEF
    elif target == "yfinance":
        return nasdaq_symbol.replace(".", "-")  # GEF.B → GEF-B
    return nasdaq_symbol                        # nasdaq, sec_edgar はそのまま
```

テスト済みの互換性:

| Symbol | NASDAQ | Alpha Vantage | SEC EDGAR | yfinance |
|---|---|---|---|---|
| DAL | DAL | DAL | DAL | DAL |
| GEF.B | GEF.B | GEF (親のみ) | GEF.B | GEF-B |

---

## 主要クラス設計

### CollectionQueue (queue.py)

`nc_collection_queue` テーブルの CRUD を担当。

- `enqueue(symbol, earnings_date, sources, priority)` — pending エントリ追加（冪等）
- `get_pending(source, limit)` — 未処理エントリ取得（priority DESC, created_at ASC）
- `mark_completed(symbol, earnings_date, source)`
- `mark_failed(symbol, earnings_date, source, error)`
- `mark_skipped(symbol, earnings_date, source)`
- `reset_failed(max_attempts=3)` — リトライ対象を pending に戻す
- `get_stats()` — source × status の集計

### NasdaqCalendarCollector (collector_nasdaq.py)

Phase 1: NASDAQ カレンダー取得 + キュー投入。

- 依存: `NasdaqClient` (既存), `NasdaqCalendarStorage`, `CollectionQueue`
- `collect_date_range(start, end)` — 日付範囲のカレンダーを取得し DB + キューに書き込み
- `collect_recent(days_back=7, days_forward=7)` — today 基準の前後N日

### Phase 2: AlphaVantageCollector (既存を利用)

`market.alphavantage.collector.AlphaVantageCollector` の
`collect_earnings(symbol)` と `collect_company_overview(symbol)` をそのまま呼び出す。
パイプラインのオーケストレーターがキューから銘柄を取り出し、AV collector に委譲する。

### SecEdgarCollector (collector_sec.py)

Phase 3: edgartools 経由の財務データ取得。

- 依存: edgartools `Company`, `SecEdgarStorage`
- `collect_symbol(symbol, filing_types=['10-K', '10-Q'])` — 1銘柄の全 filing を取得
  1. `Company(symbol).get_filings(form=form)` で filing 一覧取得
  2. 各 filing を `.obj()` で TenK/TenQ に変換
  3. `.financials` から IS/BS/CF の `to_dataframe()` を取得
  4. `dimension==False & abstract==False` でフィルタ
  5. 行単位で `se_financial_statements` に upsert
- XBRL なし filing は skip（`financials is None`）
- CIK は edgartools が自動解決（ティッカーで直接アクセス可能）
- レート制限: `time.sleep(0.1)` で SEC の 10req/sec を遵守

**CF の standard_concept 欠落への対処:**
`label` 列をフォールバックキーとして使用。主要な CF 項目のラベルマッピング辞書を持つ:
```python
CF_LABEL_FALLBACK = {
    "Cash generated by operating activities": "OperatingCashFlow",
    "Cash used in financing activities": "FinancingCashFlow",
    "Cash generated by investing activities": "InvestingCashFlow",
    "Payments for dividends and dividend equivalents": "DividendsPaid",
    ...
}
```

### YFinanceCollector (collector_yfinance.py)

Phase 4: yfinance 日次株価取得。

- 依存: `YFinanceFetcher` (既存), `YFinanceStorage`
- `collect_daily(symbol, period='1y')` — 1銘柄の日次データ取得
- `collect_batch(symbols, period='1y')` — `yf.download()` バルク取得
- インクリメンタル: DB の最新日付から差分取得

### EarningsPipeline (pipeline.py)

4 Phase のオーケストレーター。

```python
class EarningsPipeline:
    def __init__(self, av_daily_budget: int = 25): ...

    def run(self, *, days_back=7, days_forward=7, skip_phases=None) -> PipelineResult:
        """Phase 1→2→3→4 を順次実行"""

    def run_phase1(self, days_back, days_forward) -> PhaseResult:
        """NASDAQ カレンダー取得 + キュー投入"""

    def run_phase2(self, budget=None) -> PhaseResult:
        """AV EARNINGS + OVERVIEW (キューから budget/2 銘柄)"""

    def run_phase3(self) -> PhaseResult:
        """SEC EDGAR 全 pending 処理"""

    def run_phase4(self) -> PhaseResult:
        """yfinance 全 pending 処理"""

    def get_status(self) -> dict:
        """キュー統計 + 各DB統計"""
```

---

## レート制限予算配分

### Alpha Vantage (25回/日)

| 用途 | リクエスト/銘柄 | 最大銘柄数/日 |
|---|---|---|
| EARNINGS | 1 | — |
| OVERVIEW | 1 | — |
| **合計** | **2** | **12銘柄/日** (24 req + 1余裕) |

キューにより未処理銘柄は翌日以降に自動繰り越し。

### SEC EDGAR (10req/sec)

| 処理 | リクエスト/銘柄 | 400銘柄の所要時間 |
|---|---|---|
| Filing 一覧取得 | 2 (10-K + 10-Q) | — |
| 各 filing の obj() + financials | ~70 | — |
| **合計** | **~72** | **~48分** |

初回一括取得後は新規 filing のみ差分取得。

---

## CLI インターフェース

```bash
# フルパイプライン実行（デフォルト: 前後7日）
uv run python -m market.pipeline

# カスタム日付範囲
uv run python -m market.pipeline --days-back 14 --days-forward 3

# 特定 Phase のみ
uv run python -m market.pipeline --phase 1

# Phase スキップ
uv run python -m market.pipeline --skip-phases 3 4

# AV 予算調整
uv run python -m market.pipeline --av-budget 20

# ステータス確認
uv run python -m market.pipeline --status

# 失敗エントリのリセット
uv run python -m market.pipeline --reset-failed

# Dry run
uv run python -m market.pipeline --dry-run
```

---

## 実装順序

### Wave 1: 基盤 (4ファイル)
1. `constants.py` — DB名、テーブル名定数、環境変数名
2. `errors.py` — `PipelineError` 階層
3. `models.py` — EarningsCalendarRecord, QueueEntry, FinancialStatementRecord, YFDailyPriceRecord
4. `ticker_normalizer.py` — `normalize_ticker()` + テスト

### Wave 2: ストレージ (3ファイル)
5. `storage_nasdaq.py` — NasdaqCalendarStorage (ensure_tables, upsert, query)
6. `storage_sec.py` — SecEdgarStorage (ensure_tables, upsert, query)
7. `storage_yfinance.py` — YFinanceStorage (ensure_tables, upsert, query)

### Wave 3: キュー (1ファイル)
8. `queue.py` — CollectionQueue (enqueue, get_pending, mark_*, reset_failed, get_stats)

### Wave 4: コレクター (3ファイル)
9. `collector_nasdaq.py` — NasdaqCalendarCollector
10. `collector_sec.py` — SecEdgarCollector (edgartools)
11. `collector_yfinance.py` — YFinanceCollector

### Wave 5: オーケストレーター + CLI (4ファイル)
12. `pipeline.py` — EarningsPipeline
13. `cli.py` — argparse CLI
14. `__init__.py` — public exports
15. `__main__.py` — エントリポイント

### Wave 6: テスト
16. `tests/market/pipeline/unit/` — 各モジュールのユニットテスト
17. `tests/market/pipeline/integration/` — Phase 間連携テスト

---

## 再利用する既存コード

| コンポーネント | ファイル | 用途 |
|---|---|---|
| `NasdaqClient` | `src/market/nasdaq/client.py` | `get_earnings_calendar(date)` (Phase 1) |
| `AlphaVantageCollector` | `src/market/alphavantage/collector.py` | `collect_earnings()`, `collect_company_overview()` (Phase 2) |
| `AlphaVantageStorage` | `src/market/alphavantage/storage.py` | 既存テーブル `av_earnings`, `av_company_overview` |
| `CollectionResult` / `CollectionSummary` | `src/market/alphavantage/collector.py` | 結果型を import して再利用 |
| `YFinanceFetcher` | `src/market/yfinance/fetcher.py` | OHLCV 取得 (Phase 4) |
| `SQLiteClient` | `src/database/db/sqlite_client.py` | 全 Storage の DB 基盤 |
| `get_db_path()` | `src/database/db/connection.py` | DB パス解決 |
| `get_logger()` | `src/utils_core/logging.py` | ロギング |
| edgartools `Company` | site-packages (既存 import パターン: `src/edgar/fetcher.py`) | SEC EDGAR データ取得 (Phase 3) |

---

## 検証方法

### 1. ユニットテスト
```bash
uv run pytest tests/market/pipeline/unit/ -v
```

### 2. 統合テスト（Phase 1 のみ、外部API）
```bash
uv run pytest tests/market/pipeline/integration/test_nasdaq_calendar.py -v
```

### 3. CLI での手動検証
```bash
# Phase 1 のみ実行して NASDAQ カレンダーを確認
uv run python -m market.pipeline --phase 1 --days-forward 7

# ステータス確認
uv run python -m market.pipeline --status

# Phase 2 を AV 予算4（テスト用、2銘柄分）で実行
uv run python -m market.pipeline --phase 2 --av-budget 4

# SEC EDGAR テスト（Phase 3 のみ）
uv run python -m market.pipeline --phase 3

# DB内容の直接確認
sqlite3 data/sqlite/nasdaq_calendar.db "SELECT * FROM nc_earnings_calendar LIMIT 5;"
sqlite3 data/sqlite/nasdaq_calendar.db "SELECT source, status, COUNT(*) FROM nc_collection_queue GROUP BY source, status;"
sqlite3 data/sqlite/sec_edgar.db "SELECT symbol, statement_type, COUNT(*) FROM se_financial_statements GROUP BY symbol, statement_type;"
```

### 4. 品質チェック
```bash
make check-all
```

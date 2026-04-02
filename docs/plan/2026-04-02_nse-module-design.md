# NSE（国立証券取引所）データ取得モジュール設計

## Context

インド株式市場の NSE（National Stock Exchange of India）データを `src/market/nse/` として新規実装する。BSE モジュール（`src/market/bse/`）の API は日本 IP から Akamai WAF にブロックされている一方、NSE API は日本からアクセス可能であることが検証済み。NSE は BSE よりも取引量が多く、NIFTY 50/500 等の主要インデックスを提供するインド最大の証券取引所であり、企業データ・決算情報も API 経由で取得可能。

## 検証済み NSE データソース

### API エンドポイント（`https://www.nseindia.com/api/`）

| エンドポイント | データ | レスポンス |
|---------------|--------|-----------|
| `quote-equity?symbol=X` | リアルタイム株価・PE・セクター・ISIN | StockQuote |
| `equity-stockIndices?index=X` | インデックス構成銘柄 OHLCV | list[IndexConstituent] |
| `allIndices` | 全135インデックス | DataFrame |
| `results-comparision?symbol=X` | 四半期決算 5期分 | list[FinancialResult] |
| `event-calendar` | コーポレートイベント | list[CorporateEvent] |
| `market-data-pre-open?key=ALL` | プレオープン全銘柄（2,023） | DataFrame |
| `search/autocomplete?q=X` | 銘柄検索 | list[dict] |
| `marketStatus` | 市場ステータス | MarketStatus |
| `chart-databyindex?index=X` | チャートデータ | dict |
| `corporate-filing-summary?symbol=X` | 開示サマリー | dict |
| `last-quarter-details?upto=N` | 利用可能四半期 | list[dict] |
| `market-turnover` | 市場売買代金 | dict |

### CSV ダウンロード（`https://nsearchives.nseindia.com/`）

| URL | データ | 件数 |
|-----|--------|------|
| `content/equities/EQUITY_L.csv` | 全上場銘柄リスト（SYMBOL, NAME, ISIN, 上場日, 額面） | 2,265 |

### NSE API の特性

- **Cookie 必須**: 最初に `https://www.nseindia.com/` を GET し Cookie を取得 → 同一クライアントで API コール
- **Cookie 有効期限**: 約5分。定期的にリフレッシュが必要
- **Referer 必須**: `Referer: https://www.nseindia.com/`
- **レート**: ポライトディレイ 0.5s 以上推奨
- **日本からのアクセス**: ジオブロックなし（BSE API とは異なる）

## モジュール構成

```
src/market/nse/
├── __init__.py              # パブリック API エクスポート
├── constants.py             # URL, ヘッダー, ALLOWED_HOSTS, カラムマップ
├── errors.py                # NseError 階層
├── types.py                 # NseConfig, データクラス, enum
├── session.py               # NseSession（httpx + Cookie 管理 + リトライ）
├── parsers.py               # JSON/CSV パーサー
└── collectors/
    ├── __init__.py           # コレクター再エクスポート
    ├── _base.py              # NseCollectorMixin
    ├── quote.py              # QuoteCollector
    ├── indices.py            # IndicesCollector
    ├── corporate.py          # CorporateCollector
    └── stock_list.py         # StockListCollector
```

## クラス設計

### NseSession (`session.py`)

BSE の `BseSession` をベースに、**Cookie ライフサイクル管理** を追加。

```python
class NseSession:
    def __init__(self, config: NseConfig | None, retry_config: RetryConfig | None) -> None
    def get(self, url: str, params: dict | None) -> httpx.Response
    def get_with_retry(self, url: str, params: dict | None) -> httpx.Response
    def download(self, url: str) -> bytes
    def close(self) -> None
    # Cookie 管理（BSE との差分）
    def _ensure_cookies(self) -> None      # Cookie 取得/リフレッシュ
    # BseSession と同一パターン
    def _validate_url(self, url: str) -> None
    def _polite_delay(self) -> None
    def _rotate_user_agent(self) -> str
    def _handle_response(self, response, url) -> None
    def _calculate_backoff_delay(self, attempt: int) -> float
```

**BSE との主な差分:**
- `_ensure_cookies()`: API コール前に Cookie の有無・有効期限を確認し、必要なら `www.nseindia.com` を GET
- `follow_redirects=True`: NSE はリダイレクトする場合がある
- 403 受信時に Cookie リフレッシュ → リトライのロジック追加

### NseConfig (`types.py`)

```python
@dataclass(frozen=True)
class NseConfig:
    polite_delay: float = 0.5              # BSE(0.15) より長め
    delay_jitter: float = 0.15
    user_agents: tuple[str, ...] = ()
    timeout: float = 30.0
    cookie_refresh_interval: float = 300.0  # 5分
```

### RetryConfig

`market.bse.types.RetryConfig` を再利用（同一インターフェース）。NSE 固有のロジックがないため複製ではなくインポート。

### エラー階層 (`errors.py`)

```
NseError (base)
├── NseAPIError(message, url, status_code, response_body)
├── NseRateLimitError(message, url, retry_after)
├── NseParseError(message, raw_data, field)
├── NseValidationError(message, field, value)
└── NseCookieError(message, url, status_code)    ← NSE 固有
```

### データクラス (`types.py`)

| クラス | フィールド | 用途 |
|--------|-----------|------|
| `StockQuote` | symbol, company_name, isin, series, open/high/low/close, prev_close, change, pct_change, volume, pe_ratio, sector, industry | 個別銘柄気配値 |
| `IndexConstituent` | symbol, open/high/low/close, prev_close, change, pct_change, volume, year_high, year_low | インデックス構成銘柄 |
| `FinancialResult` | symbol, period_from, period_to, net_sales, total_income, total_expenditure, net_profit, eps_basic, eps_diluted, face_value | 四半期決算 |
| `CorporateEvent` | symbol, company, purpose, date, description | コーポレートイベント |
| `StockInfo` | symbol, name, series, date_of_listing, isin, face_value | 銘柄マスタ |
| `MarketStatus` | market, status, trade_date, index, last, variation, pct_change | 市場ステータス |

### enum (`types.py`)

```python
class NseIndex(str, Enum):
    NIFTY_50 = "NIFTY 50"
    NIFTY_NEXT_50 = "NIFTY NEXT 50"
    NIFTY_100 = "NIFTY 100"
    NIFTY_200 = "NIFTY 200"
    NIFTY_500 = "NIFTY 500"
    NIFTY_BANK = "NIFTY BANK"
    NIFTY_IT = "NIFTY IT"
    NIFTY_PHARMA = "NIFTY PHARMA"
    NIFTY_AUTO = "NIFTY AUTO"
    NIFTY_FINANCIAL_SERVICES = "NIFTY FINANCIAL SERVICES"
    NIFTY_MIDCAP_50 = "NIFTY MIDCAP 50"
    NIFTY_SMALLCAP_50 = "NIFTY SMLCAP 50"
    SECURITIES_IN_FO = "SECURITIES IN F&O"
```

### コレクター

すべて `NseCollectorMixin` から `_get_session() -> (NseSession, bool)` を継承。

#### QuoteCollector (`collectors/quote.py`)

`NseCollectorMixin` + `DataCollector` ABC。

| メソッド | エンドポイント | 戻り値 |
|---------|---------------|--------|
| `fetch_quote(symbol)` | `quote-equity?symbol=X` | `StockQuote` |
| `fetch_batch(index_name)` | `equity-stockIndices?index=X` | `list[IndexConstituent]` |
| `fetch(**kwargs)` | ABC 実装 | `pd.DataFrame` |
| `validate(df)` | 必須カラム確認 | `bool` |

#### IndicesCollector (`collectors/indices.py`)

`NseCollectorMixin` + `DataCollector` ABC。

| メソッド | エンドポイント | 戻り値 |
|---------|---------------|--------|
| `fetch_index(index_name)` | `equity-stockIndices?index=X` | `pd.DataFrame` |
| `fetch_all_indices()` | `allIndices` | `pd.DataFrame` |
| `fetch_market_status()` | `marketStatus` | `list[MarketStatus]` |
| `list_indices()` | 静的 | `list[str]` |

#### CorporateCollector (`collectors/corporate.py`)

`NseCollectorMixin` のみ（ABC なし、異種型を返すため）。

| メソッド | エンドポイント | 戻り値 |
|---------|---------------|--------|
| `get_financial_results(symbol)` | `results-comparision?symbol=X` | `list[FinancialResult]` |
| `get_event_calendar()` | `event-calendar` | `list[CorporateEvent]` |
| `get_filing_summary(symbol)` | `corporate-filing-summary?symbol=X` | `dict` |
| `get_available_quarters(upto)` | `last-quarter-details?upto=N` | `list[dict]` |
| `search(query)` | `search/autocomplete?q=X` | `list[dict]` |

#### StockListCollector (`collectors/stock_list.py`)

`NseCollectorMixin` + `DataCollector` ABC。

| メソッド | エンドポイント | 戻り値 |
|---------|---------------|--------|
| `fetch_stock_list()` | `nsearchives:EQUITY_L.csv` | `pd.DataFrame`（2,265銘柄） |
| `fetch_preopen()` | `market-data-pre-open?key=ALL` | `pd.DataFrame`（2,023銘柄） |
| `fetch_market_turnover()` | `market-turnover` | `dict` |

### パーサー (`parsers.py`)

| 関数 | 入力 | 出力 |
|------|------|------|
| `parse_quote_response(raw)` | dict | `StockQuote` |
| `parse_index_constituents(raw)` | dict | `list[IndexConstituent]` |
| `parse_financial_results(raw)` | dict | `list[FinancialResult]` |
| `parse_event_calendar(raw)` | list[dict] | `list[CorporateEvent]` |
| `parse_stock_list_csv(content)` | str/bytes | `pd.DataFrame` |
| `parse_preopen_data(raw)` | dict | `pd.DataFrame` |
| `parse_all_indices(raw)` | dict | `pd.DataFrame` |
| `parse_market_status(raw)` | dict | `list[MarketStatus]` |
| `parse_search_results(raw)` | dict | `list[dict]` |
| `clean_price(value)` | str | `float | None` |
| `clean_volume(value)` | str | `int | None` |

`FINANCIAL_FIELD_MAP` で `re_net_sale` → `net_sales` 等の省略フィールド名をマッピング。

### 定数 (`constants.py`)

```python
BASE_URL: Final[str] = "https://www.nseindia.com/api"
MAIN_URL: Final[str] = "https://www.nseindia.com"
ARCHIVES_BASE_URL: Final[str] = "https://nsearchives.nseindia.com"

ALLOWED_HOSTS: Final[frozenset[str]] = frozenset({
    "www.nseindia.com",
    "nsearchives.nseindia.com",
})

DEFAULT_POLITE_DELAY: Final[float] = 0.5
DEFAULT_DELAY_JITTER: Final[float] = 0.15
DEFAULT_TIMEOUT: Final[float] = 30.0
COOKIE_REFRESH_INTERVAL: Final[float] = 300.0

FINANCIAL_FIELD_MAP: Final[dict[str, str]] = {
    "re_net_sale": "net_sales",
    "re_con_pro_loss": "consolidated_profit_loss",
    "re_net_profit": "net_profit",
    "re_tot_inc": "total_income",
    "re_oth_exp": "other_expenditure",
    "re_staff_cost": "staff_cost",
    "re_face_val": "face_value",
    "re_basic_eps_for_cont_dic_opr": "eps_basic",
    "re_dilut_eps_for_cont_dic_opr": "eps_diluted",
    "re_pro_loss_bef_tax": "profit_before_tax",
    "re_tax": "tax",
    "re_from_dt": "period_from",
    "re_to_dt": "period_to",
    ...
}
```

## 追加変更

### `src/market/types.py`

`DataSource` enum に `NSE = "nse"` を追加。

### `src/market/__init__.py`

NSE モジュールのエクスポートを追加。

## テスト構成

```
tests/market/nse/
├── __init__.py
├── conftest.py                     # NseConfig, mock レスポンス fixtures
├── unit/
│   ├── test_constants.py           # ALLOWED_HOSTS, URL, カラムマップ
│   ├── test_errors.py              # エラー階層・属性・継承
│   ├── test_types.py               # enum 値, dataclass frozen, バリデーション
│   ├── test_session.py             # Cookie 管理, ポライトディレイ, SSRF, リトライ
│   ├── test_parsers.py             # 全パーサー（モック JSON/CSV）
│   ├── test_init.py                # __all__ 完全性
│   ├── test_quote.py               # QuoteCollector（モックセッション）
│   ├── test_indices.py             # IndicesCollector
│   ├── test_corporate.py           # CorporateCollector
│   └── test_stock_list.py          # StockListCollector
├── property/
│   └── test_parsers_property.py    # Hypothesis テスト
└── integration/
    └── test_nse_integration.py     # ライブ API テスト（pytest.mark.integration）
```

## 実装順序

| Phase | ファイル | 依存関係 |
|-------|---------|---------|
| 1 | `errors.py`, `constants.py`, `types.py` + テスト | なし |
| 2 | `session.py` + テスト | Phase 1 |
| 3 | `parsers.py` + テスト | Phase 1 |
| 4 | `collectors/` 全ファイル + テスト | Phase 2, 3 |
| 5 | `__init__.py`, `market/types.py`, `market/__init__.py` + テスト | Phase 4 |
| 6 | 統合テスト | Phase 5 |

## 検証方法

```bash
# 1. 全テスト実行
make test

# 2. NSE モジュールのみ
uv run pytest tests/market/nse/ -v

# 3. 統合テスト（ライブ API）
uv run pytest tests/market/nse/integration/ -m integration -v

# 4. 品質チェック
make check-all

# 5. 動作確認スクリプト
uv run python -c "
from market.nse import QuoteCollector, IndicesCollector, CorporateCollector, StockListCollector

# 銘柄一覧
sl = StockListCollector()
df = sl.fetch_stock_list()
print(f'Total stocks: {len(df)}')

# 株価
qc = QuoteCollector()
quote = qc.fetch_quote('INFY')
print(f'{quote.symbol}: {quote.close}')

# 決算
cc = CorporateCollector()
results = cc.get_financial_results('INFY')
for r in results:
    print(f'{r.period_to}: Revenue={r.net_sales}')

# インデックス
ic = IndicesCollector()
df = ic.fetch_all_indices()
print(f'Indices: {len(df)}')
"
```

## 参照ファイル

| 参照元 | パス |
|--------|------|
| BSE session（ベースパターン） | `src/market/bse/session.py` |
| BSE parsers（パーサーパターン） | `src/market/bse/parsers.py` |
| BSE types（RetryConfig 再利用） | `src/market/bse/types.py` |
| BSE collector mixin | `src/market/bse/collectors/_base.py` |
| DataCollector ABC | `src/market/base_collector.py` |
| DataSource enum | `src/market/types.py` |
| Market exports | `src/market/__init__.py` |
| BSE テスト構成 | `tests/market/bse/` |
| BSE 設計書（参考） | `docs/plan/2026-03-06_bse-module-design.md` |

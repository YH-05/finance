# ETF.com ヒストリカルファンドフロー API 実装計画

## Context

現在の `market.etfcom.FundFlowsCollector` は HTML スクレイピングで日次ファンドフローを取得しているが、**3フィールド（date, ticker, net_flows）のみ**で、**ヒストリカル範囲指定も不可**。

調査の結果、ETF.com の内部 REST API（`api-prod.etf.com`）を発見。curl_cffi の TLS fingerprint impersonation で直接アクセス可能であることを28銘柄（大型/セクター/債券/国際/コモディティ/テーマ）で検証済み（成功率100%）。

この API を活用し、**約5,000 ETF の設定日〜直近の日次データ（8フィールド）**を取得する `HistoricalFundFlowsCollector` を追加する。

---

## API 仕様（検証済み）

### 1. ティッカー API
```
GET https://api-prod.etf.com/v2/fund/tickers
→ 5,013 records: {fundId, fund, ticker, inceptionDate, assetClass, issuer}
```

### 2. ファンドフロー API
```
POST https://api-prod.etf.com/v2/fund/fund-details
Body: {"query": "fundFlowsData", "variables": {"fund_id": "521", "ticker": "SPY", "fund_isin": ""}}
→ 8フィールド: navDate, nav, navChange, navChangePercent, premiumDiscount, fundFlows, sharesOutstanding, aum
→ SPY: 8,616 records (1993〜2026)
```

### 3. アクセス要件
- curl_cffi + TLS impersonation（Playwright不要）
- 必須ヘッダー: `Origin: https://www.etf.com`, `Referer: https://www.etf.com/`, `Content-Type: application/json`

---

## 変更ファイル一覧

| ファイル | 変更内容 |
|---------|---------|
| `src/market/etfcom/constants.py` | API URL・ヘッダー定数追加 |
| `src/market/etfcom/types.py` | `HistoricalFundFlowRecord`, `TickerInfo` 追加 |
| `src/market/etfcom/errors.py` | `ETFComAPIError` 追加 |
| `src/market/etfcom/session.py` | `_request()`, `post()`, `post_with_retry()` 追加（GET/POST DRY化） |
| `src/market/etfcom/collectors.py` | `HistoricalFundFlowsCollector` 追加 |
| `src/market/etfcom/__init__.py` | 新クラスのエクスポート追加 |
| `tests/market/etfcom/unit/test_session.py` | POST メソッドのテスト追加 |
| `tests/market/etfcom/unit/test_historical_fund_flows.py` | 新規：コレクターテスト |
| `tests/market/etfcom/unit/test_types.py` | 新型定義のテスト追加 |
| `tests/market/etfcom/unit/test_errors.py` | `ETFComAPIError` テスト追加 |
| `tests/market/etfcom/conftest.py` | API レスポンスフィクスチャ追加 |

---

## 実装詳細

### Wave 1: 基盤（定数・型・エラー）

#### 1-1. constants.py — API定数追加

```python
ETFCOM_API_BASE_URL: Final[str] = "https://api-prod.etf.com"
TICKERS_API_URL: Final[str] = f"{ETFCOM_API_BASE_URL}/v2/fund/tickers"
FUND_DETAILS_API_URL: Final[str] = f"{ETFCOM_API_BASE_URL}/v2/fund/fund-details"
FUND_FLOWS_QUERY: Final[str] = "fundFlowsData"

API_HEADERS: Final[dict[str, str]] = {
    "Origin": "https://www.etf.com",
    "Referer": "https://www.etf.com/",
    "Content-Type": "application/json",
    "Accept": "application/json",
}
```

#### 1-2. types.py — 新データ型追加

```python
@dataclass(frozen=True)
class HistoricalFundFlowRecord:
    """ETF.com REST API からのヒストリカルファンドフローレコード。"""
    nav_date: date
    ticker: str
    nav: float | None
    nav_change: float | None
    nav_change_percent: float | None
    premium_discount: float | None
    fund_flows: float | None
    shares_outstanding: float | None
    aum: float | None

@dataclass(frozen=True)
class TickerInfo:
    """ティッカーAPI から取得した ETF 基本情報。"""
    fund_id: str
    fund: str
    ticker: str
    inception_date: str | None
    asset_class: str | None
    issuer: str | None
```

#### 1-3. errors.py — API固有エラー追加

```python
class ETFComAPIError(ETFComError):
    """REST API 固有のエラー。"""
    def __init__(self, message: str, ticker: str | None = None, fund_id: str | None = None) -> None:
        super().__init__(message)
        self.ticker = ticker
        self.fund_id = fund_id
```

### Wave 2: セッション拡張（POST対応）

#### 2-1. session.py — `_request()` 共通メソッド導入

既存 `get()` のロジック（polite delay, UA rotation, block detection）を `_request()` に抽出し、`get()` / `post()` がそれに委譲。

```python
def _request(self, method: str, url: str, **kwargs: Any) -> curl_requests.Response:
    """GET/POST 共通処理: delay → headers → request → block detection"""

def get(self, url: str, **kwargs: Any) -> curl_requests.Response:
    return self._request("GET", url, **kwargs)

def post(self, url: str, **kwargs: Any) -> curl_requests.Response:
    return self._request("POST", url, **kwargs)

def _request_with_retry(self, method: str, url: str, **kwargs: Any) -> curl_requests.Response:
    """GET/POST 共通リトライ: exponential backoff + session rotation"""

def get_with_retry(self, url: str, **kwargs: Any) -> curl_requests.Response:
    return self._request_with_retry("GET", url, **kwargs)

def post_with_retry(self, url: str, **kwargs: Any) -> curl_requests.Response:
    return self._request_with_retry("POST", url, **kwargs)
```

**後方互換性**: `get()` / `get_with_retry()` のシグネチャ・動作は完全維持。

### Wave 3: コレクター実装

#### 3-1. collectors.py — `HistoricalFundFlowsCollector`

```python
class HistoricalFundFlowsCollector(DataCollector):
    """ETF.com REST API からヒストリカルファンドフローデータを取得。"""

    def __init__(self, session: ETFComSession | None = None, ...) -> None:
        self._ticker_cache: dict[str, TickerInfo] = {}
        self._cache_loaded: bool = False

    def fetch(self, **kwargs) -> pd.DataFrame:
        """ticker, start_date, end_date を受け取り DataFrame を返す"""

    def fetch_multiple(self, tickers: list[str], ...) -> pd.DataFrame:
        """複数ティッカーを逐次取得して結合"""

    def fetch_tickers(self) -> pd.DataFrame:
        """GET /v2/fund/tickers → DataFrame"""

    def _resolve_fund_id(self, ticker: str) -> str:
        """メモリキャッシュ → API呼び出し → fund_id"""

    def _fetch_fund_flows(self, fund_id: str, ticker: str) -> list[dict]:
        """POST /v2/fund/fund-details → raw records"""

    def _parse_response(self, raw_records, ticker, start_date, end_date) -> pd.DataFrame:
        """camelCase→snake_case変換、日付フィルタリング、ソート"""

    def validate(self, df: pd.DataFrame) -> bool:
        """必須カラム(nav_date, ticker, fund_flows)の存在確認"""
```

**API 呼び出しフロー:**
```
fetch(ticker="SPY", start_date=..., end_date=...)
  → _resolve_fund_id("SPY")  →  メモリキャッシュ or GET /v2/fund/tickers
  → _fetch_fund_flows("521", "SPY")  →  POST /v2/fund/fund-details
  → _parse_response(records, "SPY", start_date, end_date)
  → DataFrame
```

**ティッカーキャッシュ**: インメモリ dict。初回呼び出し時に全5,013件を一括取得（1 GET）。

**日付フィルタリング**: APIにサーバーサイドフィルタなし → 全期間取得後にクライアントサイドフィルタ。

### Wave 4: 公開API・テスト

#### 4-1. `__init__.py` エクスポート追加

`HistoricalFundFlowsCollector`, `HistoricalFundFlowRecord`, `TickerInfo`, `ETFComAPIError`

#### 4-2. テスト概要

| テストファイル | ケース数 | 内容 |
|---------------|---------|------|
| `test_session.py`（追加） | ~12 | post(), post_with_retry(), _request() 共通化、既存 get() 後方互換 |
| `test_historical_fund_flows.py`（新規） | ~35 | 初期化、fetch_tickers、_resolve_fund_id、_fetch_fund_flows、_parse_response、fetch、fetch_multiple、validate |
| `test_types.py`（追加） | ~4 | HistoricalFundFlowRecord、TickerInfo の初期化・frozen |
| `test_errors.py`（追加） | ~2 | ETFComAPIError 初期化・継承 |

---

## 既存コードとの整合性

| 項目 | 方針 |
|------|------|
| 既存 `FundFlowsCollector` | 変更なし（HTMLスクレイピング版として維持） |
| `DataCollector` ABC | `fetch(**kwargs)`, `validate(df)` を実装 |
| `ETFComSession` | `get()` の動作は完全維持。内部を `_request()` にリファクタ |
| テスト命名 | 日本語: `test_正常系_条件で結果` |
| ロギング | `utils_core.logging.get_logger(__name__)` |
| 型ヒント | PEP 695、`date | None` 等 |

---

## 検証方法

### 1. 単体テスト
```bash
uv run pytest tests/market/etfcom/unit/ -v
```

### 2. 既存テスト回帰確認
```bash
uv run pytest tests/market/etfcom/ -v  # 既存106テストが全てパスすること
```

### 3. 品質チェック
```bash
make check-all  # format, lint, typecheck, test
```

### 4. 手動動作確認（実API）
```python
from market.etfcom import HistoricalFundFlowsCollector
from datetime import date

collector = HistoricalFundFlowsCollector()

# 単一ティッカー
df = collector.fetch(ticker="SPY")
print(df.shape, df.columns.tolist())

# 日付範囲指定
df = collector.fetch(ticker="SPY", start_date=date(2025, 1, 1), end_date=date(2025, 12, 31))
print(df.shape)

# 複数ティッカー
df = collector.fetch_multiple(["SPY", "QQQ", "GLD"])
print(df.groupby("ticker").size())

# ティッカー一覧
tickers_df = collector.fetch_tickers()
print(f"Total: {len(tickers_df)} tickers")
```

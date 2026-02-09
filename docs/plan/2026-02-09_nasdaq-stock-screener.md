# NASDAQ Stock Screener モジュール設計

## 概要

NASDAQ Stock Screener（https://www.nasdaq.com/market-activity/stocks/screener）のREST APIを使用し、フィルターカテゴリごとに銘柄データをCSV形式で取得・保存するPythonモジュール。

## 調査結果

### API エンドポイント

- **URL**: `https://api.nasdaq.com/api/screener/stocks`
- **メソッド**: GET
- **認証**: 不要（User-Agentヘッダーのみ必要）
- **レスポンス形式**: JSON（`data.table.headers` + `data.table.rows`）
- **ブラウザ自動化**: 不要（REST APIで完結）

### 利用可能なフィルター

| フィルター | パラメータ名 | 値 |
|-----------|------------|-----|
| 取引所 | `exchange` | `nasdaq`, `nyse`, `amex` |
| 時価総額 | `marketcap` | `mega`, `large`, `mid`, `small`, `micro`, `nano` |
| セクター | `sector` | `technology`, `telecommunications`, `health_care`, `finance`, `real_estate`, `consumer_discretionary`, `consumer_staples`, `industrials`, `basic_materials`, `energy`, `utilities` |
| レコメンド | `recommendation` | `strong_buy`, `buy`, `hold`, `sell`, `strong_sell` |
| 地域 | `region` | `africa`, `asia`, `australia_and_south_pacific`, `caribbean`, `europe`, `middle_east`, `north_america`, `south_america` |
| 国 | `country` | `usa`, `canada`, `japan`, `germany`, `uk` 等40+国 |

### リクエスト例

```
GET https://api.nasdaq.com/api/screener/stocks?exchange=nasdaq&sector=technology&limit=0
Headers:
  User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) ...
  Accept: application/json
```

### レスポンス構造

```json
{
  "data": {
    "table": {
      "headers": {
        "symbol": "Symbol",
        "name": "Name",
        "lastsale": "Last Sale",
        "netchange": "Net Change",
        "pctchange": "% Change",
        "marketCap": "Market Cap",
        "country": "Country",
        "ipoyear": "IPO Year",
        "volume": "Volume",
        "sector": "Sector",
        "industry": "Industry",
        "url": "Url"
      },
      "rows": [
        {
          "symbol": "AAPL",
          "name": "Apple Inc. Common Stock",
          "lastsale": "$227.63",
          "netchange": "-1.95",
          "pctchange": "-0.849%",
          "marketCap": "3,435,123,456,789",
          "country": "United States",
          "ipoyear": "1980",
          "volume": "48,123,456",
          "sector": "Technology",
          "industry": "Computer Manufacturing",
          "url": "/market-activity/stocks/aapl"
        }
      ]
    },
    "totalrecords": 4234
  },
  "message": null,
  "status": {
    "rCode": 200,
    "bCodeMessage": null,
    "developerMessage": null
  }
}
```

### 注意事項

- `limit=0` で全件取得可能
- 価格・時価総額は `$` や `,` 付き文字列 → 数値変換が必要
- `pctchange` は `%` 付き文字列
- レートリミット: 明示的な文書なし。リクエスト間に `sleep(0.2)` 程度推奨

## パッケージ配置

### 追加先: `src/market/nasdaq/`

既存の `src/market/` サブパッケージ群と同列に配置する。

**理由**:
- `yfinance/`, `fred/`, `bloomberg/`, `etfcom/` と同じパターン
- `DataCollector` 基底クラスを継承可能（ETF.comの `TickerCollector` と同型）
- 既存のキャッシュ（`cache/`）、エラーハンドリング（`errors.py`）、エクスポート（`export/`）機構を活用可能
- `types.py` の `DataSource` Enum に `NASDAQ = "nasdaq"` を追加

## ディレクトリ構造

```
src/market/nasdaq/
├── __init__.py              # 公開API（ScreenerCollector, ScreenerFilter等）
├── constants.py             # API URL、フィルター値、ヘッダー定義
├── types.py                 # 型定義（Enum群、ScreenerFilter、ScreenerResult）
├── session.py               # curl_cffi セッション管理（NasdaqSession）
├── collector.py             # ScreenerCollector（DataCollector継承）
├── parser.py                # JSON レスポンスのパース・数値変換
├── errors.py                # NasdaqError 例外クラス群
└── cli.py                   # CLI エントリーポイント

tests/market/nasdaq/
├── unit/
│   ├── test_types.py
│   ├── test_parser.py
│   └── test_collector.py
├── property/
│   └── test_parser_property.py
└── integration/
    └── test_screener_integration.py
```

## 主要クラス設計

### 1. types.py - 型定義

```python
from enum import Enum
from dataclasses import dataclass

class Exchange(str, Enum):
    """取引所"""
    NASDAQ = "nasdaq"
    NYSE = "nyse"
    AMEX = "amex"

class MarketCap(str, Enum):
    """時価総額区分"""
    MEGA = "mega"        # $200B+
    LARGE = "large"      # $10B-$200B
    MID = "mid"          # $2B-$10B
    SMALL = "small"      # $300M-$2B
    MICRO = "micro"      # $50M-$300M
    NANO = "nano"        # <$50M

class Sector(str, Enum):
    """セクター"""
    TECHNOLOGY = "technology"
    TELECOMMUNICATIONS = "telecommunications"
    HEALTH_CARE = "health_care"
    FINANCE = "finance"
    REAL_ESTATE = "real_estate"
    CONSUMER_DISCRETIONARY = "consumer_discretionary"
    CONSUMER_STAPLES = "consumer_staples"
    INDUSTRIALS = "industrials"
    BASIC_MATERIALS = "basic_materials"
    ENERGY = "energy"
    UTILITIES = "utilities"

class Recommendation(str, Enum):
    """アナリスト推奨"""
    STRONG_BUY = "strong_buy"
    BUY = "buy"
    HOLD = "hold"
    SELL = "sell"
    STRONG_SELL = "strong_sell"

class Region(str, Enum):
    """地域"""
    AFRICA = "africa"
    ASIA = "asia"
    AUSTRALIA_AND_SOUTH_PACIFIC = "australia_and_south_pacific"
    CARIBBEAN = "caribbean"
    EUROPE = "europe"
    MIDDLE_EAST = "middle_east"
    NORTH_AMERICA = "north_america"
    SOUTH_AMERICA = "south_america"

class Country(str, Enum):
    """国（主要国のみ抜粋、全40+国対応）"""
    USA = "united_states"
    CANADA = "canada"
    JAPAN = "japan"
    # ... 全国リストは constants.py で定義

@dataclass(frozen=True)
class ScreenerFilter:
    """スクリーナーのフィルター条件"""
    exchange: Exchange | None = None
    marketcap: MarketCap | None = None
    sector: Sector | None = None
    recommendation: Recommendation | None = None
    region: Region | None = None
    country: str | None = None  # 国数が多いため str 許容
    limit: int = 0  # 0 = 全件取得

    def to_params(self) -> dict[str, str]:
        """APIクエリパラメータに変換"""
        params: dict[str, str] = {"limit": str(self.limit)}
        if self.exchange:
            params["exchange"] = self.exchange.value
        if self.marketcap:
            params["marketcap"] = self.marketcap.value
        if self.sector:
            params["sector"] = self.sector.value
        if self.recommendation:
            params["recommendation"] = self.recommendation.value
        if self.region:
            params["region"] = self.region.value
        if self.country:
            params["country"] = self.country
        return params

# フィルターカテゴリの型エイリアス
type FilterCategory = type[Exchange] | type[MarketCap] | type[Sector] | type[Recommendation] | type[Region]
```

### 2. constants.py - 定数

```python
BASE_URL = "https://api.nasdaq.com/api"
SCREENER_ENDPOINT = f"{BASE_URL}/screener/stocks"

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
}

REQUEST_DELAY_SECONDS = 0.3  # リクエスト間の待機時間

# カテゴリ名 → フィルター属性名のマッピング
CATEGORY_PARAM_MAP: dict[str, str] = {
    "Exchange": "exchange",
    "MarketCap": "marketcap",
    "Sector": "sector",
    "Recommendation": "recommendation",
    "Region": "region",
}
```

### 3. session.py - セッション管理

```python
from curl_cffi.requests import Session

class NasdaqSession:
    """NASDAQ API へのHTTPセッション"""

    def __init__(
        self,
        retry_config: RetryConfig | None = None,
        impersonate: str = "chrome120",
    ) -> None: ...

    def get(self, url: str, params: dict[str, str] | None = None) -> dict: ...

    def __enter__(self) -> "NasdaqSession": ...
    def __exit__(self, ...) -> None: ...
```

### 4. parser.py - レスポンスパーサー

```python
def parse_screener_response(response: dict) -> pd.DataFrame:
    """JSON レスポンスを DataFrame に変換

    - "$1,234.56" → 1234.56 (float)
    - "1.23%" → 1.23 (float)
    - "1,234,567" → 1234567 (int)
    - 空文字・N/A → None
    """

def clean_price(value: str) -> float | None:
    """価格文字列を数値に変換（"$1,234.56" → 1234.56）"""

def clean_percentage(value: str) -> float | None:
    """パーセント文字列を数値に変換（"-0.849%" → -0.849）"""

def clean_market_cap(value: str) -> int | None:
    """時価総額文字列を数値に変換（"3,435,123,456,789" → 3435123456789）"""
```

### 5. collector.py - メインコレクター

```python
class ScreenerCollector(DataCollector):
    """NASDAQ Stock Screener データコレクター"""

    def __init__(
        self,
        session: NasdaqSession | None = None,
        cache_config: CacheConfig | None = None,
    ) -> None: ...

    # --- DataCollector 必須メソッド ---

    def fetch(self, *, filter: ScreenerFilter | None = None, **kwargs) -> pd.DataFrame:
        """フィルター条件でスクリーニング結果を取得"""

    def validate(self, df: pd.DataFrame) -> bool:
        """DataFrame の基本的な妥当性を検証"""

    # --- 拡張メソッド ---

    def fetch_by_category(
        self,
        category: FilterCategory,
        *,
        base_filter: ScreenerFilter | None = None,
    ) -> dict[str, pd.DataFrame]:
        """カテゴリの全値で一括取得

        Parameters
        ----------
        category
            取得対象のカテゴリ（Exchange, Sector, MarketCap 等）
        base_filter
            ベースとなるフィルター（他条件を組み合わせたい場合）

        Returns
        -------
        dict[str, pd.DataFrame]
            カテゴリ値名 → DataFrame のマッピング
            例: {"technology": df_tech, "finance": df_finance, ...}
        """

    def download_csv(
        self,
        filter: ScreenerFilter | None = None,
        *,
        output_dir: Path = Path("data/raw/nasdaq"),
        filename: str | None = None,
    ) -> Path:
        """フィルター結果をCSVでダウンロード

        Returns
        -------
        Path
            保存されたCSVファイルのパス
        """

    def download_by_category(
        self,
        category: FilterCategory,
        *,
        output_dir: Path = Path("data/raw/nasdaq"),
        base_filter: ScreenerFilter | None = None,
    ) -> list[Path]:
        """カテゴリの全値で一括CSV保存

        ファイル名: {category}_{value}_{YYYY-MM-DD}.csv
        例: sector_technology_2026-02-09.csv
        """
```

### 6. errors.py - エラー定義

```python
from market.errors import MarketError, ErrorCode

class NasdaqError(MarketError):
    """NASDAQ API エラーの基底クラス"""

class NasdaqAPIError(NasdaqError):
    """API レスポンスエラー（4xx, 5xx）"""

class NasdaqRateLimitError(NasdaqError):
    """レートリミットエラー"""

class NasdaqParseError(NasdaqError):
    """レスポンスパースエラー"""
```

### 7. cli.py - CLI

```python
"""NASDAQ Stock Screener CLI

Usage:
    uv run python -m market.nasdaq
    uv run python -m market.nasdaq --category sector
    uv run python -m market.nasdaq --category sector --output data/raw/nasdaq/
    uv run python -m market.nasdaq --filter exchange=nasdaq sector=technology
"""
```

## 利用例

```python
from market.nasdaq import ScreenerCollector, ScreenerFilter, Sector, Exchange, MarketCap

# 初期化
collector = ScreenerCollector()

# 1. 単一フィルターで取得
df = collector.fetch(filter=ScreenerFilter(sector=Sector.TECHNOLOGY))

# 2. 複数フィルター組み合わせ
df = collector.fetch(filter=ScreenerFilter(
    exchange=Exchange.NASDAQ,
    sector=Sector.TECHNOLOGY,
    marketcap=MarketCap.LARGE,
))

# 3. 全セクター一括取得
all_sectors = collector.fetch_by_category(Sector)
# → {"technology": df_tech, "finance": df_fin, ...}

# 4. 全セクター一括CSV保存
paths = collector.download_by_category(Sector, output_dir=Path("data/raw/nasdaq"))
# → [Path("data/raw/nasdaq/sector_technology_2026-02-09.csv"), ...]

# 5. カテゴリ × 条件の組み合わせ
# NASDAQの全セクターをダウンロード
paths = collector.download_by_category(
    Sector,
    base_filter=ScreenerFilter(exchange=Exchange.NASDAQ),
)

# 6. フィルターなし全件取得
df_all = collector.fetch()

# 7. CSV直接ダウンロード
path = collector.download_csv(
    filter=ScreenerFilter(exchange=Exchange.NASDAQ),
    filename="nasdaq_all_stocks.csv",
)
```

## 既存コードへの変更

### 1. `src/market/types.py` - DataSource に追加

```python
class DataSource(str, Enum):
    YFINANCE = "yfinance"
    FRED = "fred"
    LOCAL = "local"
    BLOOMBERG = "bloomberg"
    FACTSET = "factset"
    ETF_COM = "etfcom"
    NASDAQ = "nasdaq"  # 追加
```

### 2. `src/market/errors.py` - エラー再エクスポート

```python
from market.nasdaq.errors import NasdaqError  # 追加
```

### 3. `src/market/__init__.py` - 公開API追加

```python
from market.nasdaq import ScreenerCollector, ScreenerFilter  # 追加
```

## 実装タスク（Issue分解案）

| # | タスク | 依存 | 見積り |
|---|--------|------|--------|
| 1 | `types.py` - Enum群 + ScreenerFilter 定義 | - | S |
| 2 | `constants.py` - API URL・ヘッダー・Country全リスト | - | S |
| 3 | `errors.py` - NasdaqError 例外クラス群 | - | S |
| 4 | `parser.py` - JSON→DataFrame変換 + 数値クリーニング | 1 | M |
| 5 | `session.py` - curl_cffi セッション管理 | 2, 3 | M |
| 6 | `collector.py` - ScreenerCollector 本体 | 1-5 | L |
| 7 | `cli.py` - CLI エントリーポイント | 6 | S |
| 8 | テスト一式 | 1-7 | M |
| 9 | 既存コード変更（types.py, errors.py, __init__.py） | 6 | S |

## 技術的判断

### curl_cffi vs requests

**curl_cffi を採用**（既存 `etfcom/`, `yfinance/` と同じ）

- ブラウザ偽装（TLS fingerprint）でブロック回避
- ETF.com の `ETFComSession` パターンを踏襲
- `impersonate="chrome120"` 等でUser-Agent以外のfingerprint も偽装

### キャッシュ戦略

- 既存の `cache/SQLiteCache` をオプション利用
- スクリーナーデータは日次で変わるため `ttl_seconds=86400`（24時間）
- カテゴリ一括取得時はキャッシュキーに日付+フィルター条件を含める

### CSV 出力フォーマット

```
data/raw/nasdaq/
├── sector_technology_2026-02-09.csv
├── sector_finance_2026-02-09.csv
├── exchange_nasdaq_2026-02-09.csv
├── marketcap_mega_2026-02-09.csv
└── all_stocks_2026-02-09.csv
```

- エンコーディング: `utf-8-sig`（Excel互換）
- 数値はクリーニング済み（`$`, `,`, `%` 除去後の数値）

## 参考情報

- [NASDAQ Stock Screener](https://www.nasdaq.com/market-activity/stocks/screener)
- [NASDAQ API Notebook](https://github.com/evgenyzorin/Financials/blob/main/nasdaq-api-v3.0.2.ipynb)
- [How to Scrape NASDAQ Data (Bright Data)](https://brightdata.com/blog/web-data/how-to-scrape-nasdaq)
- [Scrape Nasdaq Guide (Decodo)](https://decodo.com/blog/scrape-nasdaq)

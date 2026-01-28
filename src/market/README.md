# market - 金融データ取得パッケージ

複数のデータソース（Yahoo Finance、FRED、Bloomberg）から金融市場データを統合的に取得・エクスポートするパッケージ。株価、経済指標、指数データなどを効率的に扱えます。

## インストール

```bash
# uv を使用（このリポジトリ内）
uv sync --all-extras
```

<!-- AUTO-GENERATED: QUICKSTART -->

## クイックスタート

### 最初の5分で試す

**Yahoo Finance から株価データを取得する**（最も基本的な使い方）

```python
from market.yfinance import YFinanceFetcher, FetchOptions

# 1. フェッチャーを初期化（初期化不要なので簡単）
fetcher = YFinanceFetcher()

# 2. 取得するシンボルと期間を指定
options = FetchOptions(
    symbols=["AAPL"],  # Apple の株価を取得
    start_date="2024-01-01",
    end_date="2024-12-31",
)

# 3. データを取得
results = fetcher.fetch(options)
result = results[0]  # 最初の結果を取得

# 4. データを確認
print(f"シンボル: {result.symbol}")
print(f"データ点数: {result.row_count}")
print(result.data.head())  # 最初の5行を表示
```

### よくある使い方

#### 1. 複数銘柄の一括取得

```python
from market.yfinance import YFinanceFetcher, FetchOptions

fetcher = YFinanceFetcher()

# MAG7 銘柄を一括取得（2024年の日次データ）
options = FetchOptions(
    symbols=["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA"],
    start_date="2024-01-01",
    end_date="2024-12-31",
)

results = fetcher.fetch(options)

# 各銘柄の統計情報を表示
for result in results:
    df = result.data
    print(f"{result.symbol}: 終値の範囲 ${df['close'].min():.2f} - ${df['close'].max():.2f}")
```

#### 2. 経済指標データの取得（FRED）

```python
from market.fred import FREDFetcher
from market.fred.types import FetchOptions as FREDFetchOptions

fetcher = FREDFetcher()

# 米国のマクロ経済指標を取得
options = FREDFetchOptions(
    symbols=["GDP", "CPIAUCSL", "UNRATE"],  # GDP, CPI, 失業率
    start_date="2020-01-01",
)

results = fetcher.fetch(options)

for result in results:
    if not result.is_empty:
        latest = result.data['close'].iloc[-1]
        print(f"{result.symbol}: 最新値 {latest:.2f}")
```

#### 3. Bloomberg から株価データを取得

```python
from market.bloomberg import BloombergFetcher, BloombergFetchOptions

fetcher = BloombergFetcher()

options = BloombergFetchOptions(
    securities=["AAPL US Equity"],
    fields=["PX_LAST", "PX_VOLUME"],  # 終値と出来高
    start_date="2024-01-01",
    end_date="2024-12-31",
)

results = fetcher.get_historical_data(options)
```

<!-- END: QUICKSTART -->

<!-- AUTO-GENERATED: IMPLEMENTATION -->

## 実装状況

| モジュール | 状態 | ファイル数 | 行数 |
|-----------|------|----------|------|
| `yfinance/` | ✅ 実装済み | 4 | 700+ |
| `fred/` | ✅ 実装済み | 7 | 1,000+ |
| `bloomberg/` | ✅ 実装済み | 5 | 900+ |
| `cache/` | ✅ 実装済み | 3 | 350+ |
| `export/` | ✅ 実装済み | 2 | 400+ |
| `schema.py` | ✅ 実装済み | 1 | 400+ |
| `types.py` | ✅ 実装済み | 1 | 200+ |
| `factset/` | 🚧 開発中 | 1 | 30 |
| `alternative/` | 🚧 開発中 | 1 | 30 |

<!-- END: IMPLEMENTATION -->

## サブモジュール

| モジュール | 説明 |
|-----------|------|
| `market.yfinance` | Yahoo Finance データ取得（OHLCV、財務指標） |
| `market.fred` | FRED 経済指標データ取得（金利、CPI、失業率など） |
| `market.bloomberg` | Bloomberg API 連携（計画済み実装） |
| `market.export` | データエクスポート（JSON、CSV、SQLite、Agent JSON） |
| `market.cache` | キャッシュ機能（SQLite キャッシュ対応） |
| `market.schema` | JSON スキーマ定義 (Pydantic V2) |
| `market.factset` | FactSet データ取得（計画中） |
| `market.alternative` | オルタナティブデータ（計画中） |

<!-- AUTO-GENERATED: API -->

## 公開 API

このパッケージは、複数のデータソースから市場データを効率的に取得するための統合インターフェースを提供します。

### 主要クラス

#### YFinanceFetcher

Yahoo Finance から株価データを取得するメインクラス。複数銘柄の一括取得とキャッシュ機能をサポートします。

**説明**: Yahoo Finance API を使用して、日本株・米国株・指数・為替の OHLCV（始値・高値・安値・終値・出来高）データを取得します。

**基本的な使い方**:

```python
from market.yfinance import YFinanceFetcher, FetchOptions

fetcher = YFinanceFetcher()

# 1つの銘柄を取得
options = FetchOptions(
    symbols=["AAPL"],
    start_date="2024-01-01",
    end_date="2024-12-31",
)
results = fetcher.fetch(options)

# 結果にアクセス
result = results[0]
print(f"シンボル: {result.symbol}")
print(f"行数: {result.row_count}")
print(result.data.head())  # DataFrame で確認
```

**主なメソッド**:

| メソッド | 説明 | 戻り値 |
|----------|------|--------|
| `fetch(options)` | FetchOptions に基づいてデータを取得 | `list[MarketDataResult]` |
| `__enter__()` / `__exit__()` | コンテキストマネージャー（リソース自動解放） | `YFinanceFetcher` |

---

#### FREDFetcher

FRED（連邦準備制度の経済データベース）から経済指標を取得します。

**説明**: 米国の経済指標（GDP、失業率、インフレーション など）を FRED API から取得します。事前に FRED API キーの取得が必要です。

**基本的な使い方**:

```python
from market.fred import FREDFetcher
from market.fred.types import FetchOptions

# 環境変数 FRED_API_KEY を設定済みであることが前提
fetcher = FREDFetcher()

# 経済指標を取得
options = FetchOptions(
    symbols=["GDP", "UNRATE"],  # GDP と失業率
    start_date="2020-01-01",
)
results = fetcher.fetch(options)

for result in results:
    print(f"{result.symbol}: {result.row_count} data points")
```

**主なメソッド**:

| メソッド | 説明 | 戻り値 |
|----------|------|--------|
| `fetch(options)` | FetchOptions に基づいてデータを取得 | `list[MarketDataResult]` |
| `get_series_info(series_id)` | シリーズのメタデータを取得 | `dict` |

---

#### BloombergFetcher

Bloomberg Terminal API 連携でプロフェッショナル向けデータを取得します。

**説明**: Bloomberg 端末が利用可能な環境で、高度な金融データ（リアルタイム価格、ファンダメンタルズ、ニュースなど）を取得します。

**基本的な使い方**:

```python
from market.bloomberg import BloombergFetcher, BloombergFetchOptions

fetcher = BloombergFetcher()

options = BloombergFetchOptions(
    securities=["AAPL US Equity"],
    fields=["PX_LAST", "PX_VOLUME"],  # 終値と出来高
    start_date="2024-01-01",
    end_date="2024-12-31",
)

results = fetcher.get_historical_data(options)
```

---

#### DataExporter

取得したデータを複数のフォーマットでエクスポートします。

**説明**: DataFrame や MarketDataResult オブジェクトを JSON、CSV、SQLite などの形式で保存します。

**基本的な使い方**:

```python
from market import DataExporter

exporter = DataExporter()

# JSON エクスポート
exporter.to_json(result.data, "output.json")

# CSV エクスポート
exporter.to_csv(result.data, "output.csv")

# SQLite に保存
exporter.to_sqlite(result.data, "database.db", "market_data")

# AI エージェント向け JSON
agent_output = exporter.to_agent_json(result.data)
```

---

### データ型

#### MarketDataResult

データ取得操作の結果を表します。シンボル、データフレーム、メタデータなどを含みます。

```python
from market import MarketDataResult

# 例：YFinanceFetcher の結果
result: MarketDataResult
print(result.symbol)      # シンボル（例: "AAPL"）
print(result.source)      # データソース（例: DataSource.YFINANCE）
print(result.data)        # pandas DataFrame
print(result.row_count)   # データ行数
print(result.is_empty)    # データが空かどうか
```

#### DataSource 列挙型

データの出所を示します。

```python
from market import DataSource

# 利用可能なデータソース
DataSource.YFINANCE   # Yahoo Finance
DataSource.FRED       # Federal Reserve Economic Data
DataSource.BLOOMBERG  # Bloomberg Terminal
DataSource.LOCAL      # ローカルファイル
DataSource.FACTSET    # FactSet（計画中）
```

---

### 設定クラス（Pydantic V2 モデル）

#### MarketConfig

パッケージ全体の設定をまとめたクラス。複数のデータソースとキャッシュの設定を一元管理します。

```python
from market import MarketConfig, CacheConfig, DataSourceConfig

config = MarketConfig(
    cache=CacheConfig(
        enabled=True,
        ttl_seconds=3600,  # 1時間
    ),
    sources={
        "yfinance": DataSourceConfig(
            enabled=True,
            timeout=30,
        ),
        "fred": DataSourceConfig(
            enabled=True,
            api_key="your_api_key",
        ),
    },
)
```

#### DateRange

日付範囲を表します。

```python
from market import DateRange
from datetime import date

date_range = DateRange(
    start=date(2024, 1, 1),
    end=date(2024, 12, 31),
)
```

---

### バリデーション関数

設定のバリデーション機能を提供します。

```python
from market import (
    validate_config,
    validate_stock_metadata,
    validate_economic_metadata,
)

# 設定のバリデーション
try:
    validate_config(config)
    print("設定は有効です")
except ValueError as e:
    print(f"バリデーションエラー: {e}")
```

---

### エラークラス

#### MarketError

基本的なエラークラス。すべてのパッケージ固有エラーの基底クラスです。

#### ExportError

エクスポート処理中のエラー。ファイル書き込みやフォーマット変換の失敗時に発生します。

#### CacheError

キャッシュ処理中のエラー。キャッシュの読み書き失敗時に発生します。

```python
from market import ExportError, CacheError

try:
    exporter.to_json(data, "output.json")
except ExportError as e:
    print(f"エクスポート失敗: {e}")

try:
    cache.get(key)
except CacheError as e:
    print(f"キャッシュエラー: {e}")
```

<!-- END: API -->

## yfinance モジュール

Yahoo Finance から OHLCV データを取得します。curl_cffi によるブラウザ偽装でレート制限を回避します。

### 基本的な使い方

```python
from market.yfinance import (
    YFinanceFetcher,
    FetchOptions,
    Interval,
    DataSource,
)

fetcher = YFinanceFetcher()

# 日次データを取得
options = FetchOptions(
    symbols=["AAPL"],
    start_date="2024-01-01",
    end_date="2024-12-31",
    interval=Interval.DAILY,
)
results = fetcher.fetch(options)

# 結果を確認
result = results[0]
print(f"Symbol: {result.symbol}")
print(f"Source: {result.source}")  # DataSource.YFINANCE
print(f"Rows: {len(result.data)}")
print(result.data.head())
```

### 複数シンボルの一括取得

yf.download() を使用した効率的な一括取得をサポートしています。

```python
from market.yfinance import YFinanceFetcher, FetchOptions, Interval

fetcher = YFinanceFetcher()

# MAG7 銘柄を一括取得
options = FetchOptions(
    symbols=["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA"],
    start_date="2024-01-01",
    end_date="2024-12-31",
    interval=Interval.DAILY,
)

results = fetcher.fetch(options)

# 各銘柄の結果を処理
for result in results:
    if not result.is_empty:
        df = result.data
        print(f"{result.symbol}: {result.row_count} rows")
        print(f"  期間: {df.index.min()} 〜 {df.index.max()}")
        print(f"  終値範囲: ${df['close'].min():.2f} - ${df['close'].max():.2f}")
```

### 株価指数・為替レートの取得

```python
from market.yfinance import YFinanceFetcher, FetchOptions

fetcher = YFinanceFetcher()

# 株価指数を取得
index_options = FetchOptions(
    symbols=["^GSPC", "^DJI", "^IXIC", "^N225"],  # S&P500, ダウ, ナスダック, 日経225
    start_date="2024-01-01",
)
index_results = fetcher.fetch(index_options)

for result in index_results:
    print(f"{result.symbol}: {result.row_count} data points")

# 為替レートを取得
forex_options = FetchOptions(
    symbols=["USDJPY=X", "EURUSD=X", "GBPUSD=X"],
    start_date="2024-01-01",
)
forex_results = fetcher.fetch(forex_options)

for result in forex_results:
    if not result.is_empty:
        latest = result.data['close'].iloc[-1]
        print(f"{result.symbol}: {latest:.4f}")
```

### 時間足データの取得

```python
from market.yfinance import YFinanceFetcher, FetchOptions, Interval

fetcher = YFinanceFetcher()

# 週次データ
weekly_options = FetchOptions(
    symbols=["AAPL"],
    start_date="2020-01-01",
    interval=Interval.WEEKLY,
)

# 月次データ
monthly_options = FetchOptions(
    symbols=["AAPL"],
    start_date="2015-01-01",
    interval=Interval.MONTHLY,
)

# 時間足（直近60日間のみ取得可能）
hourly_options = FetchOptions(
    symbols=["AAPL"],
    interval=Interval.HOURLY,  # 過去60日間の制限あり
)
```

### コンテキストマネージャーの使用

```python
from market.yfinance import YFinanceFetcher, FetchOptions

# with 文でリソースを自動解放
with YFinanceFetcher() as fetcher:
    options = FetchOptions(
        symbols=["AAPL", "GOOGL"],
        start_date="2024-01-01",
    )
    results = fetcher.fetch(options)

    for result in results:
        print(f"{result.symbol}: {result.row_count} rows")
# セッションが自動的にクローズされる
```

### データの操作例

```python
from market.yfinance import YFinanceFetcher, FetchOptions
import pandas as pd

fetcher = YFinanceFetcher()

options = FetchOptions(
    symbols=["AAPL"],
    start_date="2024-01-01",
    end_date="2024-12-31",
)
results = fetcher.fetch(options)
result = results[0]

# DataFrame の構造
# columns: ['open', 'high', 'low', 'close', 'volume']
# index: DatetimeIndex
df = result.data

# 日次リターンの計算
df['daily_return'] = df['close'].pct_change()

# 移動平均の追加
df['sma_20'] = df['close'].rolling(window=20).mean()
df['sma_50'] = df['close'].rolling(window=50).mean()

# 統計情報
print(f"平均終値: ${df['close'].mean():.2f}")
print(f"最高値: ${df['high'].max():.2f}")
print(f"最安値: ${df['low'].min():.2f}")
print(f"平均出来高: {df['volume'].mean():,.0f}")
print(f"日次リターン標準偏差: {df['daily_return'].std():.4f}")
```

### FetchOptions パラメータ

| パラメータ | 型 | デフォルト | 説明 |
|-----------|-----|-----------|------|
| `symbols` | `list[str]` | 必須 | 取得するシンボルのリスト |
| `start_date` | `datetime \| str \| None` | None | 開始日 |
| `end_date` | `datetime \| str \| None` | None | 終了日 |
| `interval` | `Interval` | `Interval.DAILY` | データ間隔 |
| `use_cache` | `bool` | True | キャッシュを使用するか |

### Interval 列挙型

| 値 | 文字列 | 説明 |
|----|--------|------|
| `Interval.DAILY` | "1d" | 日次 |
| `Interval.WEEKLY` | "1wk" | 週次 |
| `Interval.MONTHLY` | "1mo" | 月次 |
| `Interval.HOURLY` | "1h" | 時間足 |

### エラーハンドリング

```python
from market.yfinance import (
    YFinanceFetcher,
    FetchOptions,
    DataFetchError,
    ValidationError,
)

fetcher = YFinanceFetcher()

try:
    options = FetchOptions(symbols=["INVALID_SYMBOL"])
    results = fetcher.fetch(options)
except ValidationError as e:
    print(f"バリデーションエラー: {e}")
    print(f"フィールド: {e.field}")
    print(f"値: {e.value}")
except DataFetchError as e:
    print(f"データ取得エラー: {e}")
    print(f"シンボル: {e.symbol}")
    print(f"ソース: {e.source}")
    print(f"エラーコード: {e.code}")
```

### 時価総額・財務指標の取得

`yf.Ticker` を直接使用して、時価総額や PER などの財務指標を取得できます。

```python
import yfinance as yf

# 単一銘柄の財務指標
ticker = yf.Ticker("AAPL")
info = ticker.info

# 主要な財務指標
print(f"時価総額: ${info.get('marketCap', 0):,.0f}")
print(f"PER（TTM）: {info.get('trailingPE', 'N/A')}")
print(f"PBR: {info.get('priceToBook', 'N/A')}")
print(f"配当利回り: {info.get('dividendYield', 0) * 100:.2f}%")
print(f"52週高値: ${info.get('fiftyTwoWeekHigh', 0):.2f}")
print(f"52週安値: ${info.get('fiftyTwoWeekLow', 0):.2f}")
```

### 複数銘柄の財務データ一括取得

```python
import yfinance as yf
import pandas as pd

# MAG7 銘柄の財務データを一括取得
symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA"]

# 取得したい指標
metrics = [
    "marketCap",      # 時価総額
    "trailingPE",     # PER（TTM）
    "forwardPE",      # 予想PER
    "priceToBook",    # PBR
    "dividendYield",  # 配当利回り
    "beta",           # ベータ値
    "fiftyTwoWeekHigh",
    "fiftyTwoWeekLow",
]

# 各銘柄のデータを収集
data = []
for symbol in symbols:
    ticker = yf.Ticker(symbol)
    info = ticker.info
    row = {"symbol": symbol}
    for metric in metrics:
        row[metric] = info.get(metric)
    data.append(row)

# DataFrame に変換
df = pd.DataFrame(data)
df.set_index("symbol", inplace=True)

# 時価総額を兆ドル単位に変換
df["marketCap_T"] = df["marketCap"] / 1e12

# 配当利回りをパーセント表示
df["dividendYield_pct"] = df["dividendYield"].fillna(0) * 100

print(df[["marketCap_T", "trailingPE", "priceToBook", "dividendYield_pct"]])
```

出力例:
```
        marketCap_T  trailingPE  priceToBook  dividendYield_pct
symbol
AAPL          3.45       28.50        45.20               0.44
MSFT          3.12       35.80        12.30               0.72
GOOGL         2.15       24.20         6.80               0.00
AMZN          2.05       42.50         8.90               0.00
NVDA          3.20       55.30        48.50               0.02
META          1.45       27.80         8.20               0.35
TSLA          0.85      120.50        15.60               0.00
```

### 財務諸表データの取得

損益計算書、貸借対照表、キャッシュフロー計算書を取得できます。

```python
import yfinance as yf

ticker = yf.Ticker("AAPL")

# 損益計算書（年次）
income_stmt = ticker.financials
print("=== 損益計算書（直近4年）===")
print(income_stmt.loc[["Total Revenue", "Gross Profit", "Net Income"]])

# 貸借対照表（年次）
balance_sheet = ticker.balance_sheet
print("\n=== 貸借対照表 ===")
print(balance_sheet.loc[["Total Assets", "Total Liabilities Net Minority Interest", "Stockholders Equity"]])

# キャッシュフロー計算書（年次）
cashflow = ticker.cashflow
print("\n=== キャッシュフロー ===")
print(cashflow.loc[["Operating Cash Flow", "Capital Expenditure", "Free Cash Flow"]])

# 四半期データも取得可能
quarterly_income = ticker.quarterly_financials
quarterly_balance = ticker.quarterly_balance_sheet
quarterly_cashflow = ticker.quarterly_cashflow
```

### 複数銘柄の財務比較

```python
import yfinance as yf
import pandas as pd

def get_financial_summary(symbol: str) -> dict:
    """銘柄の財務サマリーを取得"""
    ticker = yf.Ticker(symbol)
    info = ticker.info

    # 最新の財務データ
    try:
        income = ticker.financials
        balance = ticker.balance_sheet

        # 最新年度のデータ（最初の列）
        latest_income = income.iloc[:, 0] if not income.empty else pd.Series()
        latest_balance = balance.iloc[:, 0] if not balance.empty else pd.Series()

        return {
            "symbol": symbol,
            "name": info.get("shortName", symbol),
            "marketCap": info.get("marketCap", 0),
            "trailingPE": info.get("trailingPE"),
            "priceToBook": info.get("priceToBook"),
            "revenue": latest_income.get("Total Revenue", 0),
            "netIncome": latest_income.get("Net Income", 0),
            "totalAssets": latest_balance.get("Total Assets", 0),
            "totalDebt": latest_balance.get("Total Debt", 0),
            "roe": info.get("returnOnEquity"),
            "roa": info.get("returnOnAssets"),
        }
    except Exception as e:
        print(f"Warning: {symbol} の財務データ取得に失敗: {e}")
        return {"symbol": symbol, "error": str(e)}

# 比較対象銘柄
symbols = ["AAPL", "MSFT", "GOOGL"]

# 財務データを収集
summaries = [get_financial_summary(s) for s in symbols]
df = pd.DataFrame(summaries)

# 単位変換（十億ドル）
for col in ["marketCap", "revenue", "netIncome", "totalAssets", "totalDebt"]:
    if col in df.columns:
        df[f"{col}_B"] = df[col] / 1e9

# 利益率の計算
df["profitMargin"] = df["netIncome"] / df["revenue"] * 100

print(df[["symbol", "name", "marketCap_B", "revenue_B", "profitMargin", "trailingPE"]])
```

### 主要な info フィールド一覧

| フィールド | 説明 |
|-----------|------|
| `marketCap` | 時価総額 |
| `trailingPE` | PER（過去12ヶ月） |
| `forwardPE` | 予想PER |
| `priceToBook` | PBR |
| `priceToSales` | PSR |
| `enterpriseValue` | 企業価値（EV） |
| `dividendYield` | 配当利回り |
| `dividendRate` | 年間配当額 |
| `payoutRatio` | 配当性向 |
| `beta` | ベータ値 |
| `fiftyTwoWeekHigh` | 52週高値 |
| `fiftyTwoWeekLow` | 52週安値 |
| `averageVolume` | 平均出来高 |
| `returnOnEquity` | ROE |
| `returnOnAssets` | ROA |
| `profitMargins` | 利益率 |
| `grossMargins` | 粗利率 |
| `operatingMargins` | 営業利益率 |
| `revenueGrowth` | 売上成長率 |
| `earningsGrowth` | 利益成長率 |
| `currentRatio` | 流動比率 |
| `quickRatio` | 当座比率 |
| `debtToEquity` | 負債資本比率 |

### キャッシュとリトライ設定

```python
from market.yfinance import (
    YFinanceFetcher,
    CacheConfig,
    RetryConfig,
)

# キャッシュ設定
cache_config = CacheConfig(
    ttl_seconds=3600,  # 1時間
    max_entries=1000,
)

# リトライ設定
retry_config = RetryConfig(
    max_attempts=3,
    initial_delay=1.0,
    max_delay=60.0,
    exponential_base=2.0,
)

# 設定を適用
fetcher = YFinanceFetcher(
    cache_config=cache_config,
    retry_config=retry_config,
)
```

## fred モジュール

FRED (Federal Reserve Economic Data) から経済指標データを取得します。

### 前提条件

FRED API キーが必要です。[FRED](https://fred.stlouisfed.org/) でアカウントを作成し、API キーを取得してください。

```bash
# 環境変数に設定
export FRED_API_KEY="your_api_key_here"
```

### 基本的な使い方

```python
from market.fred import FREDFetcher, FRED_API_KEY_ENV
from market.fred.types import FetchOptions

# 環境変数 FRED_API_KEY を設定するか、コンストラクタで渡す
fetcher = FREDFetcher()

# 経済指標を取得
options = FetchOptions(symbols=["GDP", "CPIAUCSL", "UNRATE"])
results = fetcher.fetch(options)

for result in results:
    print(f"{result.symbol}: {len(result.data)} data points")
```

### 代表的な経済指標の取得

```python
from market.fred import FREDFetcher
from market.fred.types import FetchOptions

fetcher = FREDFetcher()

# 主要経済指標
options = FetchOptions(
    symbols=[
        "GDP",       # 国内総生産（四半期）
        "CPIAUCSL",  # 消費者物価指数（月次）
        "UNRATE",    # 失業率（月次）
        "FEDFUNDS",  # フェデラルファンド金利（日次）
        "DGS10",     # 10年国債利回り（日次）
        "DGS2",      # 2年国債利回り（日次）
    ],
    start_date="2020-01-01",
    end_date="2024-12-31",
)

results = fetcher.fetch(options)

for result in results:
    if not result.is_empty:
        df = result.data
        # FRED データは close カラムに値が格納される
        print(f"{result.symbol}:")
        print(f"  期間: {df.index.min()} 〜 {df.index.max()}")
        print(f"  最新値: {df['close'].iloc[-1]:.2f}")
        print(f"  データ点数: {result.row_count}")
```

### FRED シリーズ ID 一覧（よく使う指標）

| シリーズ ID | 説明 | 頻度 |
|-------------|------|------|
| `GDP` | 国内総生産 | 四半期 |
| `GDPC1` | 実質 GDP | 四半期 |
| `CPIAUCSL` | 消費者物価指数（全項目） | 月次 |
| `CPILFESL` | コア CPI（食料・エネルギー除く） | 月次 |
| `UNRATE` | 失業率 | 月次 |
| `PAYEMS` | 非農業部門雇用者数 | 月次 |
| `FEDFUNDS` | フェデラルファンド金利 | 日次/月次 |
| `DGS10` | 10年国債利回り | 日次 |
| `DGS2` | 2年国債利回り | 日次 |
| `DGS30` | 30年国債利回り | 日次 |
| `T10Y2Y` | 10年-2年スプレッド（イールドカーブ） | 日次 |
| `VIXCLS` | VIX 恐怖指数 | 日次 |
| `DEXJPUS` | ドル円為替レート | 日次 |
| `M2SL` | M2 マネーサプライ | 月次 |
| `UMCSENT` | ミシガン大学消費者信頼感指数 | 月次 |

### シリーズ情報の取得

```python
from market.fred import FREDFetcher

fetcher = FREDFetcher()

# シリーズのメタデータを取得
info = fetcher.get_series_info("GDP")
print(f"タイトル: {info.get('title')}")
print(f"単位: {info.get('units')}")
print(f"頻度: {info.get('frequency')}")
print(f"季節調整: {info.get('seasonal_adjustment')}")
```

### イールドカーブ分析の例

```python
from market.fred import FREDFetcher
from market.fred.types import FetchOptions
import pandas as pd

fetcher = FREDFetcher()

# 各年限の国債利回りを取得
options = FetchOptions(
    symbols=[
        "DGS1MO",  # 1ヶ月
        "DGS3MO",  # 3ヶ月
        "DGS6MO",  # 6ヶ月
        "DGS1",    # 1年
        "DGS2",    # 2年
        "DGS5",    # 5年
        "DGS10",   # 10年
        "DGS30",   # 30年
    ],
    start_date="2024-01-01",
)

results = fetcher.fetch(options)

# 最新のイールドカーブを構築
yield_curve = {}
for result in results:
    if not result.is_empty:
        yield_curve[result.symbol] = result.data['close'].iloc[-1]

print("最新イールドカーブ:")
for series_id, value in yield_curve.items():
    print(f"  {series_id}: {value:.2f}%")

# 10年-2年スプレッド（景気後退の先行指標）
if "DGS10" in yield_curve and "DGS2" in yield_curve:
    spread = yield_curve["DGS10"] - yield_curve["DGS2"]
    print(f"\n10年-2年スプレッド: {spread:.2f}%")
    if spread < 0:
        print("⚠️ 逆イールド発生中（景気後退の可能性）")
```

### キャッシュとリトライの設定

```python
from market.fred import FREDFetcher
from market.fred.types import FetchOptions, CacheConfig, RetryConfig
from market.fred.cache import SQLiteCache

# キャッシュ設定
cache_config = CacheConfig(
    enabled=True,
    ttl_seconds=86400,  # 24時間
    db_path="./cache/fred_cache.db",
)

# リトライ設定
retry_config = RetryConfig(
    max_attempts=5,
    initial_delay=1.0,
    max_delay=30.0,
    exponential_base=2.0,
)

# キャッシュを初期化
cache = SQLiteCache(db_path="./cache/fred_cache.db")

# フェッチャーを初期化
fetcher = FREDFetcher(
    cache=cache,
    cache_config=cache_config,
    retry_config=retry_config,
)

options = FetchOptions(
    symbols=["GDP", "CPIAUCSL"],
    start_date="2020-01-01",
    use_cache=True,  # キャッシュを使用
)

results = fetcher.fetch(options)

for result in results:
    cache_status = "キャッシュから取得" if result.from_cache else "API から取得"
    print(f"{result.symbol}: {cache_status}")
```

### エラーハンドリング

```python
from market.fred import FREDFetcher
from market.fred.types import FetchOptions
from market.fred.errors import FREDFetchError, FREDValidationError

try:
    fetcher = FREDFetcher()
    options = FetchOptions(symbols=["INVALID_SERIES_ID"])
    results = fetcher.fetch(options)
except FREDValidationError as e:
    print(f"バリデーションエラー: {e}")
    # API キーが設定されていない場合など
except FREDFetchError as e:
    print(f"データ取得エラー: {e}")
    # 存在しないシリーズ ID、ネットワークエラーなど
```

### 利用可能な定数

```python
from market.fred import FRED_API_KEY_ENV, FRED_SERIES_PATTERN

print(FRED_API_KEY_ENV)      # "FRED_API_KEY"
print(FRED_SERIES_PATTERN)   # FRED シリーズ ID の正規表現パターン
```

## export モジュール

データを各種フォーマットでエクスポートします。

### DataExporter

```python
from market import DataExporter

exporter = DataExporter()

# JSON エクスポート
exporter.to_json(data, "output.json")

# CSV エクスポート
exporter.to_csv(data, "output.csv")

# SQLite に保存 (UPSERT サポート)
exporter.to_sqlite(data, "database.db", "table_name")

# AI エージェント向け JSON 出力
agent_output = exporter.to_agent_json(data)
```

<!-- AUTO-GENERATED: STATS -->

## モジュール統計

| 項目 | 値 |
|------|-----|
| Python ファイル数 | 29 |
| 総行数（実装コード） | 7,499 |
| モジュール数 | 9 |
| テストファイル数 | 12 |
| テストカバレッジ | 多くのモジュールで実装済み |

<!-- END: STATS -->

<!-- AUTO-GENERATED: STRUCTURE -->

## ディレクトリ構造

```
src/market/
├── __init__.py          # 公開 API
├── README.md
├── types.py             # 共通型定義
├── errors.py            # 共通エラー定義
├── schema.py            # Pydantic V2 スキーマ
├── yfinance/            # Yahoo Finance データ取得
│   ├── __init__.py
│   ├── fetcher.py       # YFinanceFetcher
│   ├── types.py         # FetchOptions, Interval 等
│   └── errors.py        # DataFetchError, ValidationError
├── fred/                # FRED 経済指標データ取得
│   ├── __init__.py
│   ├── fetcher.py       # FREDFetcher
│   ├── base_fetcher.py
│   ├── cache.py
│   ├── constants.py
│   ├── types.py
│   └── errors.py
├── cache/               # キャッシュ機能
│   ├── __init__.py
│   ├── cache.py
│   └── types.py
├── export/              # データエクスポート
│   ├── __init__.py
│   └── exporter.py      # DataExporter
├── bloomberg/           # Bloomberg 連携
│   ├── __init__.py
│   ├── constants.py
│   ├── errors.py
│   ├── fetcher.py
│   └── types.py
├── factset/             # FactSet 連携 (計画中)
│   └── __init__.py
├── alternative/         # オルタナティブデータ (計画中)
│   └── __init__.py
└── utils/               # ユーティリティ
    ├── __init__.py
    └── logging_config.py
```

<!-- END: STRUCTURE -->

## 開発

### テスト実行

```bash
# 全テスト
uv run pytest tests/market/

# カバレッジ付き
uv run pytest tests/market/ --cov=src/market --cov-report=term-missing
```

### 品質チェック

```bash
# フォーマット
uv run ruff format src/market/ tests/market/

# リント
uv run ruff check src/market/ tests/market/

# 型チェック
uv run pyright src/market/ tests/market/
```

## 関連ドキュメント

- [パッケージリファクタリング計画](../../docs/project/package-refactoring.md)
- [コーディング規約](../../docs/coding-standards.md)
- [テスト戦略](../../docs/testing-strategy.md)

## ライセンス

MIT License

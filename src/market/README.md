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

# 1. フェッチャーを初期化（設定不要で即座に使える）
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
print(result.data.head())  # 最初の5行を表示（pandas DataFrame）
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
    if not result.is_empty:
        df = result.data
        print(f"{result.symbol}: 終値の範囲 ${df['close'].min():.2f} - ${df['close'].max():.2f}")
```

#### 2. 経済指標データの取得（FRED）

```python
from market.fred import FREDFetcher
from market.fred.types import FetchOptions as FREDFetchOptions

# 事前に環境変数 FRED_API_KEY を設定してください
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

# Bloomberg Terminal がインストールされている環境が必要
fetcher = BloombergFetcher()

options = BloombergFetchOptions(
    securities=["AAPL US Equity"],
    fields=["PX_LAST", "PX_VOLUME"],  # 終値と出来高
    start_date="2024-01-01",
    end_date="2024-12-31",
)

results = fetcher.get_historical_data(options)

for result in results:
    print(f"{result.security}: {result.row_count} data points")
```

#### 4. ETF.com から ETF データを取得

```python
from market.etfcom import TickerCollector, FundamentalsCollector

# ETF ティッカーリストを取得
ticker_collector = TickerCollector()
ticker_df = ticker_collector.fetch()
print(f"全 ETF 数: {len(ticker_df)}")

# 上位10 ETF のティッカーを取得
top_tickers = ticker_df.nlargest(10, "aum")["ticker"].tolist()

# ファンダメンタルズ情報を取得
fundamentals_collector = FundamentalsCollector()
fundamentals_df = fundamentals_collector.fetch(tickers=top_tickers)
print(fundamentals_df[["ticker", "expense_ratio", "aum", "dividend_yield"]])
```

#### 5. データのエクスポート

```python
from market import DataExporter

exporter = DataExporter()

# 取得したデータを複数のフォーマットで保存
result = results[0]  # YFinanceFetcher の結果

# JSON エクスポート
exporter.to_json(result.data, "aapl_2024.json")

# CSV エクスポート
exporter.to_csv(result.data, "aapl_2024.csv")

# SQLite に保存（UPSERT サポート）
exporter.to_sqlite(result.data, "market_data.db", "stock_prices")

# AI エージェント向け JSON（統計情報付き）
agent_output = exporter.to_agent_json(result.data)
print(agent_output)
```

<!-- END: QUICKSTART -->

<!-- AUTO-GENERATED: IMPLEMENTATION -->

## 実装状況

| モジュール | 状態 | ファイル数 | 実装行数 |
|-----------|------|----------|---------|
| `yfinance/` | ✅ 実装済み | 4 | 1,443 |
| `fred/` | ✅ 実装済み | 9 | 2,724 |
| `bloomberg/` | ✅ 実装済み | 6 | 2,937 |
| `etfcom/` | ✅ 実装済み | 7 | 2,541 |
| `factset/` | 🚧 開発中 | 4 | 2,179 |
| `cache/` | ✅ 実装済み | 3 | 648 |
| `export/` | ✅ 実装済み | 2 | 586 |
| `alternative/` | 🚧 開発中 | 2 | 252 |
| `schema.py` | ✅ 実装済み | 1 | 211 |
| `types.py` | ✅ 実装済み | 1 | 120 |
| `errors.py` | ✅ 実装済み | 1 | 248 |
| `utils/` | ✅ 実装済み | 1 | 0 |

<!-- END: IMPLEMENTATION -->

## サブモジュール

| モジュール | 説明 | 状態 |
|-----------|------|------|
| `market.yfinance` | Yahoo Finance データ取得（OHLCV、財務指標、指数、為替） | ✅ 実装済み |
| `market.fred` | FRED 経済指標データ取得（GDP、金利、CPI、失業率など）、履歴キャッシュ機能 | ✅ 実装済み |
| `market.bloomberg` | Bloomberg Terminal API 連携（履歴データ、リファレンスデータ、ニュース） | ✅ 実装済み |
| `market.etfcom` | ETF.com スクレイピング（ティッカーリスト、ファンダメンタルズ、資金フロー） | ✅ 実装済み |
| `market.factset` | FactSet データ取得・処理ユーティリティ | 🚧 開発中 |
| `market.alternative` | オルタナティブデータソース、時系列分析 | 🚧 開発中 |
| `market.export` | データエクスポート（JSON、CSV、SQLite、AI エージェント向け JSON） | ✅ 実装済み |
| `market.cache` | SQLite ベースのキャッシュ機能（TTL 対応、UPSERT サポート） | ✅ 実装済み |
| `market.schema` | Pydantic V2 スキーマ定義（MarketConfig、DateRange、メタデータ検証） | ✅ 実装済み |
| `market.types` | 共通型定義（MarketDataResult、DataSource、AnalysisResult） | ✅ 実装済み |
| `market.errors` | 共通エラークラス（MarketError、ExportError、CacheError、各データソース固有エラー） | ✅ 実装済み |
| `market.utils` | 共通ユーティリティ | ✅ 実装済み |

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

#### TickerCollector

ETF.com のスクリーナーページから ETF ティッカーリストを取得します。

**説明**: ETF.com のスクリーナーをスクレイピングし、全 ETF のティッカーシンボルと基本情報を取得します。curl_cffi を使用したブラウザ偽装でボット検出を回避します。

**基本的な使い方**:

```python
from market.etfcom import TickerCollector

# ティッカーリストを取得
collector = TickerCollector()
df = collector.fetch()

# 結果を確認（pandas DataFrame）
print(f"取得した ETF 数: {len(df)}")
print(df[["ticker", "name", "aum"]].head())
```

**主なメソッド**:

| メソッド | 説明 | 戻り値 |
|----------|------|--------|
| `fetch()` | ETF.com スクリーナーから全 ETF データを取得 | `pd.DataFrame` |

---

#### FundamentalsCollector

ETF.com の個別 ETF プロファイルページからファンダメンタルズデータを取得します。

**説明**: 指定した ETF のプロファイルページをスクレイピングし、経費率、資産規模、配当利回りなどのファンダメンタルズ情報を取得します。

**基本的な使い方**:

```python
from market.etfcom import FundamentalsCollector

# 特定の ETF のファンダメンタルズを取得
collector = FundamentalsCollector()
df = collector.fetch(tickers=["SPY", "VOO", "IVV"])

# 結果を確認
print(df[["ticker", "expense_ratio", "aum", "dividend_yield"]].head())
```

**主なメソッド**:

| メソッド | 説明 | 戻り値 |
|----------|------|--------|
| `fetch(tickers)` | 指定した ETF のファンダメンタルズを取得 | `pd.DataFrame` |

---

#### FundFlowsCollector

ETF.com のファンドフローページから日次資金フローデータを取得します。

**説明**: ETF への資金流入・流出の日次データを取得します。マーケットセンチメントや ETF の人気動向を分析できます。

**基本的な使い方**:

```python
from market.etfcom import FundFlowsCollector

# ファンドフローデータを取得
collector = FundFlowsCollector()
df = collector.fetch()

# 結果を確認
print(f"取得した ETF 数: {len(df['ticker'].unique())}")
print(df[["ticker", "date", "flow_amount"]].head())
```

**主なメソッド**:

| メソッド | 説明 | 戻り値 |
|----------|------|--------|
| `fetch()` | 全 ETF の日次ファンドフローを取得 | `pd.DataFrame` |

---

#### HistoricalFundFlowsCollector

ETF.com の REST API からヒストリカルファンドフローデータを取得します。

**説明**: ETF.com の JSON REST API（`api-prod.etf.com`）を使用して、個別 ETF の日次ファンドフロー履歴データ（NAV、NAV変動、プレミアム/ディスカウント、資金フロー、発行済株式数、AUM）を取得します。HTML スクレイピングではなく REST API を直接呼び出すため、ブラウザは不要です。

**基本的な使い方**:

```python
from market.etfcom import HistoricalFundFlowsCollector

# 単一 ETF のファンドフロー履歴を取得
collector = HistoricalFundFlowsCollector()
df = collector.fetch(ticker="SPY")

# 結果を確認
# columns: ticker, nav_date, nav, nav_change, nav_change_percent,
#          premium_discount, fund_flows, shares_outstanding, aum
print(f"データ件数: {len(df)}")
print(df[["ticker", "nav_date", "fund_flows", "aum"]].head())

# 日付範囲を指定して取得
df = collector.fetch(ticker="SPY", start_date="2024-01-01", end_date="2024-12-31")

# 複数 ETF の一括取得（並列実行）
df = collector.fetch_multiple(tickers=["SPY", "VOO", "QQQ"], max_concurrency=3)
```

**主なメソッド**:

| メソッド | 説明 | 戻り値 |
|----------|------|--------|
| `fetch(ticker, start_date, end_date)` | 単一 ETF のファンドフロー履歴を取得 | `pd.DataFrame` |
| `fetch_multiple(tickers, max_concurrency)` | 複数 ETF のファンドフローを並列取得 | `pd.DataFrame` |
| `fetch_tickers()` | 全 ETF のティッカーリストと fund ID を取得 | `pd.DataFrame` |

**API 仕様**:

| 項目 | 詳細 |
|------|------|
| ベース URL | `https://api-prod.etf.com` |
| ティッカー一覧 | `GET /private/apps/fundflows/tickers` |
| ファンドフロー取得 | `POST /private/apps/fundflows/fund-flows-query` |
| リクエスト形式 | JSON (`{"fundId": <int>}`) |
| レスポンス形式 | JSON (`{"results": [<record>, ...]}`) |

**レスポンスフィールド**:

| フィールド（API） | フィールド（DataFrame） | 型 | 説明 |
|-------------------|------------------------|-----|------|
| `navDate` | `nav_date` | `date` | 観測日 |
| `nav` | `nav` | `float \| None` | 基準価額 |
| `navChange` | `nav_change` | `float \| None` | NAV 変動額 |
| `navChangePercent` | `nav_change_percent` | `float \| None` | NAV 変動率（%） |
| `premiumDiscount` | `premium_discount` | `float \| None` | プレミアム/ディスカウント |
| `fundFlows` | `fund_flows` | `float \| None` | 純資金フロー（USD） |
| `sharesOutstanding` | `shares_outstanding` | `float \| None` | 発行済株式数 |
| `aum` | `aum` | `float \| None` | 運用資産総額（USD） |

**FundFlowsCollector との比較**:

| 項目 | FundFlowsCollector | HistoricalFundFlowsCollector |
|------|-------------------|------------------------------|
| データソース | HTML スクレイピング | REST API（JSON） |
| ブラウザ要否 | 不要（curl_cffi） | 不要（curl_cffi） |
| 取得単位 | 全 ETF 一括 | 個別 ETF 指定 |
| 並列取得 | 非対応 | 対応（`fetch_multiple`） |
| 日付フィルタ | 非対応 | 対応（`start_date` / `end_date`） |
| データフィールド | ticker, date, flow_amount, aum | ticker, nav_date, nav, nav_change, nav_change_percent, premium_discount, fund_flows, shares_outstanding, aum |
| ティッカーキャッシュ | なし | 3層キャッシュ（メモリ/ファイル/API） |
| 主な用途 | 市場全体の資金フロー概況 | 個別 ETF の詳細なファンドフロー履歴分析 |

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

#### ETFComError

ETF.com スクレイピング処理中のエラー。基底エラークラスです。

#### ETFComAPIError

ETF.com REST API がエラーレスポンスを返した際に発生します。`url`、`status_code`、`response_body`、`ticker`、`fund_id` 属性を持ちます。

#### ETFComBlockedError

ボット検出によりアクセスがブロックされた際に発生します。

#### ETFComScrapingError

HTML パース・データ抽出に失敗した際に発生します。

#### ETFComTimeoutError

ページロードやナビゲーションがタイムアウトした際に発生します。

```python
from market import ExportError, CacheError
from market.etfcom import ETFComError, ETFComBlockedError

try:
    exporter.to_json(data, "output.json")
except ExportError as e:
    print(f"エクスポート失敗: {e}")

try:
    cache.get(key)
except CacheError as e:
    print(f"キャッシュエラー: {e}")

try:
    collector.fetch()
except ETFComBlockedError as e:
    print(f"ETF.com からブロックされました: {e}")
except ETFComError as e:
    print(f"ETF.com スクレイピングエラー: {e}")
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
from market.errors import FREDFetchError, FREDValidationError

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

## etfcom モジュール

ETF.com から ETF データをスクレイピングで取得します。curl_cffi によるブラウザ偽装でボット検出を回避します。

### 主要機能

| 機能 | クラス | 説明 |
|------|--------|------|
| ティッカーリスト取得 | `TickerCollector` | スクリーナーから全 ETF のティッカーと基本情報を取得 |
| ファンダメンタルズ取得 | `FundamentalsCollector` | 個別 ETF の詳細情報（経費率、資産規模、配当など）を取得 |
| ファンドフロー取得 | `FundFlowsCollector` | 日次の資金流入・流出データを取得（HTML スクレイピング） |
| ヒストリカルファンドフロー取得 | `HistoricalFundFlowsCollector` | 個別 ETF の日次ファンドフロー履歴を取得（REST API） |
| セッション管理 | `ETFComSession` | リトライ・タイムアウト・ボット検出回避を統合 |

### 基本的な使い方

#### ティッカーリストの取得

```python
from market.etfcom import TickerCollector

# 全 ETF のティッカーリストを取得
collector = TickerCollector()
df = collector.fetch()

# DataFrame の構造
# columns: ['ticker', 'name', 'aum', 'expense_ratio', 'category', ...]
print(f"取得した ETF 数: {len(df)}")
print(df.head())

# 資産規模でソート
top_etfs = df.nlargest(10, "aum")
print(top_etfs[["ticker", "name", "aum"]])
```

#### ファンダメンタルズの取得

```python
from market.etfcom import FundamentalsCollector

# 特定の ETF の詳細情報を取得
collector = FundamentalsCollector()
tickers = ["SPY", "VOO", "IVV", "QQQ", "VTI"]
df = collector.fetch(tickers=tickers)

# 取得できる情報
# - expense_ratio: 経費率
# - aum: 資産規模
# - dividend_yield: 配当利回り
# - inception_date: 設定日
# - avg_volume: 平均出来高
# - holdings_count: 保有銘柄数
# など

print(df[["ticker", "expense_ratio", "aum", "dividend_yield"]])
```

#### ファンドフローの取得

```python
from market.etfcom import FundFlowsCollector

# 日次のファンドフローデータを取得
collector = FundFlowsCollector()
df = collector.fetch()

# DataFrame の構造
# columns: ['ticker', 'date', 'flow_amount', 'aum', ...]
print(f"取得した ETF 数: {len(df['ticker'].unique())}")
print(f"データ期間: {df['date'].min()} 〜 {df['date'].max()}")

# 直近の大口流入を確認
recent_flows = df.sort_values("flow_amount", ascending=False).head(10)
print(recent_flows[["ticker", "date", "flow_amount"]])
```

#### ヒストリカルファンドフローの取得

```python
from market.etfcom import HistoricalFundFlowsCollector

# 単一 ETF のファンドフロー履歴を取得
collector = HistoricalFundFlowsCollector()
df = collector.fetch(ticker="SPY")

# DataFrame の構造
# columns: ['ticker', 'nav_date', 'nav', 'nav_change', 'nav_change_percent',
#           'premium_discount', 'fund_flows', 'shares_outstanding', 'aum']
print(f"データ件数: {len(df)}")
print(df.head())

# 日付範囲を指定
df = collector.fetch(ticker="SPY", start_date="2024-01-01", end_date="2024-12-31")
print(f"2024年のデータ件数: {len(df)}")

# 複数 ETF を並列取得
df = collector.fetch_multiple(tickers=["SPY", "VOO", "QQQ"], max_concurrency=3)
print(f"取得した ETF 数: {len(df['ticker'].unique())}")

# 全 ETF のティッカーリストと fund ID を取得
tickers_df = collector.fetch_tickers()
print(f"全 ETF 数: {len(tickers_df)}")
print(tickers_df[["ticker", "fund_id", "name"]].head())
```

#### ヒストリカルファンドフローのエラーハンドリング

```python
from market.etfcom import (
    HistoricalFundFlowsCollector,
    ETFComAPIError,
    ETFComError,
)

collector = HistoricalFundFlowsCollector()

try:
    df = collector.fetch(ticker="INVALID_TICKER")
except ETFComAPIError as e:
    print(f"REST API エラー: {e}")
    print(f"URL: {e.url}")
    print(f"ステータスコード: {e.status_code}")
    print(f"ティッカー: {e.ticker}")
except ETFComError as e:
    print(f"ETF.com エラー: {e}")
```

### リトライとタイムアウト設定

```python
from market.etfcom import TickerCollector, RetryConfig, ScrapingConfig

# リトライ設定
retry_config = RetryConfig(
    max_attempts=5,         # 最大リトライ回数
    initial_delay=1.0,      # 初回リトライ待機時間（秒）
    max_delay=60.0,         # 最大待機時間（秒）
    exponential_base=2.0,   # 指数バックオフの基数
)

# スクレイピング設定
scraping_config = ScrapingConfig(
    timeout=30.0,           # ページロードタイムアウト（秒）
    user_agent="...",       # カスタム User-Agent
)

# 設定を適用
collector = TickerCollector(
    retry_config=retry_config,
    scraping_config=scraping_config,
)
```

### エラーハンドリング

```python
from market.etfcom import (
    TickerCollector,
    ETFComError,
    ETFComAPIError,
    ETFComBlockedError,
    ETFComScrapingError,
    ETFComTimeoutError,
)

collector = TickerCollector()

try:
    df = collector.fetch()
except ETFComBlockedError as e:
    print(f"ボット検出でブロックされました: {e}")
    # User-Agent を変更するか、待機時間を延ばす
except ETFComTimeoutError as e:
    print(f"ページロードがタイムアウトしました: {e}")
    # タイムアウト設定を延長
except ETFComScrapingError as e:
    print(f"HTML パース・データ抽出に失敗: {e}")
    # ETF.com のページ構造が変更された可能性
except ETFComAPIError as e:
    print(f"REST API エラー: {e}")
    # API のステータスコードやレスポンスを確認
except ETFComError as e:
    print(f"ETF.com エラー: {e}")
```

### セッション管理

複数のコレクターで同じセッションを共有できます。

```python
from market.etfcom import ETFComSession, TickerCollector, FundamentalsCollector

# セッションを共有
with ETFComSession() as session:
    # ティッカーリスト取得
    ticker_collector = TickerCollector(session=session)
    ticker_df = ticker_collector.fetch()

    # 上位10 ETF のファンダメンタルズ取得
    top_tickers = ticker_df.nlargest(10, "aum")["ticker"].tolist()
    fundamentals_collector = FundamentalsCollector(session=session)
    fundamentals_df = fundamentals_collector.fetch(tickers=top_tickers)
# セッションが自動的にクローズされる
```

### 利用上の注意

1. **レート制限**: ETF.com への過剰なリクエストは避けてください。リトライ間隔を適切に設定してください。
2. **ボット検出**: curl_cffi によるブラウザ偽装を使用していますが、短時間に大量のリクエストを送るとブロックされる可能性があります。
3. **HTML 構造変更**: ETF.com のページ構造が変更されると、スクレイピングが失敗する可能性があります。

### データ型

```python
from market.etfcom import (
    ETFRecord,
    FundamentalsRecord,
    FundFlowRecord,
    HistoricalFundFlowRecord,
    TickerInfo,
)
from datetime import date

# ETFRecord: TickerCollector の結果
etf_record = ETFRecord(
    ticker="SPY",
    name="SPDR S&P 500 ETF Trust",
    aum=450000000000.0,  # 4500億ドル
    expense_ratio=0.0945,
)

# FundamentalsRecord: FundamentalsCollector の結果
fundamentals = FundamentalsRecord(
    ticker="SPY",
    expense_ratio=0.0945,
    aum=450000000000.0,
    dividend_yield=1.35,
    inception_date="1993-01-22",
)

# FundFlowRecord: FundFlowsCollector の結果
flow = FundFlowRecord(
    ticker="SPY",
    date="2024-12-31",
    flow_amount=1500000000.0,  # 15億ドルの流入
    aum=450000000000.0,
)

# HistoricalFundFlowRecord: HistoricalFundFlowsCollector の結果
historical_flow = HistoricalFundFlowRecord(
    ticker="SPY",
    nav_date=date(2025, 9, 10),
    nav=450.25,
    nav_change=2.15,
    nav_change_percent=0.48,
    premium_discount=-0.02,
    fund_flows=2787590000.0,  # 約28億ドルの流入
    shares_outstanding=920000000.0,
    aum=414230000000.0,
)

# TickerInfo: HistoricalFundFlowsCollector.fetch_tickers() の結果
ticker_info = TickerInfo(
    ticker="SPY",
    fund_id=1,
    name="SPDR S&P 500 ETF Trust",
    issuer="State Street",
    asset_class="Equity",
    inception_date="1993-01-22",
)
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
| Python ファイル数 | 45 |
| 総行数（実装コード） | 15,278 |
| サブモジュール数 | 9 |
| テストファイル数 | 28 |
| テストカバレッジ | 主要モジュール（yfinance, fred, bloomberg, etfcom, export, cache）で実装済み |

<!-- END: STATS -->

<!-- AUTO-GENERATED: STRUCTURE -->

## ディレクトリ構造

```
market/
├── __init__.py              # 公開 API エクスポート
├── README.md                # パッケージドキュメント
├── types.py                 # 共通型定義（MarketDataResult, DataSource 等）
├── errors.py                # 共通エラークラス（MarketError, ExportError 等）
├── schema.py                # Pydantic V2 スキーマ（MarketConfig, DateRange 等）
├── base_collector.py        # 基底データコレクタークラス
├── bloomberg_processor.py   # Bloomberg データ処理ユーティリティ
├── tsa.py                   # 時系列分析ユーティリティ
│
├── yfinance/                # Yahoo Finance データ取得
│   ├── __init__.py
│   ├── fetcher.py           # YFinanceFetcher（主要実装: 528行）
│   ├── session.py           # セッション管理
│   └── types.py             # FetchOptions, Interval
│
├── fred/                    # FRED 経済指標データ取得
│   ├── __init__.py
│   ├── fetcher.py           # FREDFetcher（主要実装: 303行）
│   ├── base_fetcher.py      # 基底フェッチャークラス
│   ├── cache.py             # SQLite キャッシュ実装（248行）
│   ├── historical_cache.py  # 履歴データキャッシュ（337行）
│   ├── constants.py         # FRED 定数（API キー環境変数名等）
│   ├── types.py             # FetchOptions, CacheConfig, RetryConfig
│   └── scripts/             # ユーティリティスクリプト
│       ├── __init__.py
│       └── sync_historical.py  # 履歴データ同期スクリプト
│
├── bloomberg/               # Bloomberg Terminal API 連携
│   ├── __init__.py
│   ├── fetcher.py           # BloombergFetcher（主要実装: 390行）
│   ├── types.py             # BloombergFetchOptions, Periodicity, IDType
│   ├── constants.py         # Bloomberg 定数
│   └── sample/              # サンプルデータ・実装
│       ├── data_blpapi.py   # blpapi サンプル実装（146行）
│       └── data_local.py    # ローカルデータアクセス（227行）
│
├── etfcom/                  # ETF.com スクレイピング
│   ├── __init__.py
│   ├── collectors.py        # TickerCollector, FundamentalsCollector, FundFlowsCollector
│   ├── session.py           # ETFComSession（curl_cffi ベースのセッション管理）
│   ├── browser.py           # ブラウザ偽装・ボット検出回避
│   ├── types.py             # ETFRecord, FundamentalsRecord, FundFlowRecord
│   ├── errors.py            # ETFComError, ETFComBlockedError 等
│   └── constants.py         # ETF.com URL・設定定数
│
├── factset/                 # FactSet データ取得（開発中）
│   ├── __init__.py
│   ├── factset_utils.py     # FactSet ユーティリティ（1,111行）
│   ├── factset_downloaded_data_utils.py  # ダウンロードデータ処理（74行）
│   └── price.py             # 価格データ処理（32行）
│
├── cache/                   # キャッシュ機能
│   ├── __init__.py
│   ├── cache.py             # SQLite キャッシュ実装（289行）
│   └── types.py             # CacheEntry, CacheConfig
│
├── export/                  # データエクスポート
│   ├── __init__.py
│   └── exporter.py          # DataExporter（JSON/CSV/SQLite/AgentJSON: 214行）
│
├── alternative/             # オルタナティブデータ（開発中）
│   ├── __init__.py
│   └── tsa.py               # 時系列分析（170行）
│
└── utils/                   # ユーティリティ
    └── __init__.py
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

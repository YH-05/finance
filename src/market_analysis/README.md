# market_analysis

金融市場分析パッケージ

## 概要

このパッケージは市場データの取得・分析・可視化機能を提供します。

**現在のバージョン:** 0.1.0

<!-- AUTO-GENERATED: QUICKSTART -->

## クイックスタート

### インストール

```bash
# このリポジトリのパッケージとして利用
uv sync --all-extras
```

### 基本的な使い方

```python
from market_analysis import MarketData, Analysis, Chart

# 1. 市場データを取得
data = MarketData()
stock_df = data.fetch_stock("AAPL", start="2024-01-01")

# 2. テクニカル分析を実行（メソッドチェーン）
analysis = Analysis(stock_df)
result = analysis.add_sma(20).add_ema(50).add_returns().result()

# 3. チャートを生成
chart = Chart(result.data, title="AAPL 株価チャート")
chart.price_chart(overlays=["SMA_20", "EMA_50"])
chart.save("chart.png")
```

### よくある使い方

#### ユースケース1: 複数銘柄の相関分析

```python
from market_analysis import MarketData, Analysis, Chart

# データ取得
data = MarketData()
aapl_df = data.fetch_stock("AAPL", start="2024-01-01")
msft_df = data.fetch_stock("MSFT", start="2024-01-01")

# 相関分析
corr_matrix = Analysis.correlation([aapl_df, msft_df])

# ヒートマップ生成
fig = Chart.correlation_heatmap(corr_matrix, title="株価相関マップ")
```

#### ユースケース2: 経済指標の取得と分析

```python
from market_analysis import MarketData

# FRED から経済指標を取得
data = MarketData(fred_api_key="your_api_key")
gdp_df = data.fetch_fred("GDP", start="2020-01-01")
unemployment_df = data.fetch_fred("UNRATE", start="2020-01-01")
```

#### ユースケース3: テクニカル指標の計算

```python
from market_analysis import Analysis

# 単一指標の計算
analysis = Analysis(stock_df)
result = analysis.add_sma(20).result()

# 複数指標の組み合わせ
result = (
    analysis
    .add_sma(20)
    .add_ema(12)
    .add_returns()
    .add_volatility(window=20)
    .result()
)
```

#### ユースケース4: セクター分析（2026年新機能）

```python
from market_analysis.analysis.sector import (
    calculate_sector_returns,
    get_top_bottom_sectors,
)

# 11セクターの騰落率を取得
sector_returns = calculate_sector_returns(period="1M")
print(sector_returns)
# {'technology': 0.085, 'energy': -0.032, ...}

# トップ3とボトム3セクターを取得
top_sectors, bottom_sectors = get_top_bottom_sectors(sector_returns, n=3)
```

#### ユースケース5: 決算カレンダー（2026年新機能）

```python
from market_analysis.analysis.earnings import fetch_earnings_calendar
from datetime import datetime, timedelta

# 今後2週間の決算予定を取得
end_date = datetime.now() + timedelta(days=14)
earnings_list = fetch_earnings_calendar(
    tickers=["AAPL", "MSFT", "NVDA"],
    end_date=end_date
)

for earning in earnings_list:
    print(f"{earning.ticker}: {earning.earnings_date}, EPS予想: {earning.eps_estimate}")
```

#### ユースケース6: 多期間騰落率計算（2026年新機能）

```python
from market_analysis.analysis.returns import (
    calculate_return,
    calculate_returns_for_symbols,
)

# 単一銘柄の1日騰落率
daily_return = calculate_return("AAPL", period="1D")
print(f"AAPL 1日騰落率: {daily_return:.2%}")

# 複数銘柄の複数期間騰落率
symbols = ["^GSPC", "^N225", "AAPL"]
periods = ["1D", "1W", "MTD", "YTD"]
returns_df = calculate_returns_for_symbols(symbols, periods)
print(returns_df)
```

<!-- END: QUICKSTART -->

## ディレクトリ構成

<!-- AUTO-GENERATED: STRUCTURE -->

```
market_analysis/
├── __init__.py                  # 公開API定義（129行）
├── py.typed                     # PEP 561マーカー
├── types.py                     # 型定義13種（592行）
├── errors.py                    # 例外クラス8種（521行）
├── api/                         # パブリックAPI（推奨エントリポイント）
│   ├── __init__.py
│   ├── analysis.py              # Analysis - テクニカル分析（1,177行）
│   ├── chart.py                 # Chart - チャート生成（488行）
│   └── market_data.py           # MarketData - データ取得統合（887行）
├── analysis/                    # 分析ロジック
│   ├── __init__.py
│   ├── analyzer.py              # Analyzer（428行）
│   ├── correlation.py           # CorrelationAnalyzer（511行）
│   ├── indicators.py            # IndicatorCalculator（477行）
│   ├── earnings.py              # EarningsCalendar - 決算日程取得（414行）
│   ├── returns.py               # MultiPeriodReturns - 多期間騰落率（505行）
│   └── sector.py                # SectorAnalysis - セクター分析（639行）
├── core/                        # データフェッチャー
│   ├── __init__.py
│   ├── base_fetcher.py          # BaseDataFetcher（382行）
│   ├── data_fetcher_factory.py  # DataFetcherFactory（174行）
│   ├── yfinance_fetcher.py      # YFinanceFetcher（516行）
│   ├── fred_fetcher.py          # FREDFetcher（605行）
│   ├── bloomberg_fetcher.py     # BloombergFetcher（640行）
│   ├── factset_fetcher.py       # FactSetFetcher（723行）
│   └── mock_fetchers.py         # MockFetchers（665行）
├── export/                      # データエクスポート
│   ├── __init__.py
│   └── exporter.py              # DataExporter（678行）
├── utils/                       # ユーティリティ関数
│   ├── __init__.py
│   ├── cache.py                 # SQLiteキャッシュ（637行）
│   ├── logger_factory.py        # ロガー生成（52行）
│   ├── logging_config.py        # 構造化ロギング（377行）
│   ├── retry.py                 # リトライ（410行）
│   ├── ticker_registry.py       # ティッカーレジストリ（696行）
│   └── validators.py            # バリデーション（581行）
├── visualization/               # チャート生成
│   ├── __init__.py
│   ├── charts.py                # ChartBuilder（687行）
│   ├── heatmap.py               # HeatmapChart（267行）
│   └── price_charts.py          # CandlestickChart, LineChart（782行）
└── docs/                        # ライブラリドキュメント（8ファイル）
    ├── project.md
    ├── architecture.md
    ├── development-guidelines.md
    ├── functional-design.md
    ├── glossary.md
    ├── library-requirements.md
    ├── repository-structure.md
    └── tasks.md
```

<!-- END: STRUCTURE -->

## 実装状況

<!-- AUTO-GENERATED: IMPLEMENTATION -->

| モジュール | 状態 | ファイル数 | 行数 | テスト | 備考 |
|-----------|------|-----------|------|-------|------|
| `types.py` | ✅ 実装済み | 1 | 592 | ✅ | 型定義13種（TypedDict, Enum等） |
| `errors.py` | ✅ 実装済み | 1 | 521 | ✅ | 例外クラス8種（MarketAnalysisError等） |
| `api/` | ✅ 実装済み | 4 | 2,552 | ✅ (3) | MarketData, Analysis, Chart, MarketPerformanceAnalyzer |
| `analysis/` | ✅ 実装済み | 7 | 2,974 | ✅ (6) | Analyzer, Indicators, Correlation, Earnings, Returns, Sector |
| `core/` | ✅ 実装済み | 8 | 3,705 | ✅ (7) | 5種データフェッチャー + Factory + Mock |
| `export/` | ✅ 実装済み | 2 | 678 | ✅ (1) | DataExporter（CSV/JSON/Parquet） |
| `utils/` | ✅ 実装済み | 7 | 2,753 | ✅ (1) | cache, retry, validators, ticker_registry等 |
| `visualization/` | ✅ 実装済み | 4 | 1,736 | ✅ (3) | ChartBuilder, HeatmapChart, LineChart等 |

**テスト構成**: 単体テスト 21ファイル + 統合テスト 1ファイル = 計22テスト

**分析機能の拡張**:
- ✅ セクター分析（sector.py）- 11セクターのETFパフォーマンス分析、トップ/ボトムセクター検出
- ✅ 決算カレンダー（earnings.py）- 決算予定日の取得、EPS/売上予想の抽出
- ✅ 多期間騰落率（returns.py）- 1D/1W/MTD/YTD等の複数期間リターン計算

**データソース対応状況**:
- ✅ Yahoo Finance (yfinance) - 株価・為替・指数データ
- ✅ FRED (Federal Reserve Economic Data) - 米国経済指標
- ✅ Bloomberg Terminal (BLPAPI) - プロフェッショナル市場データ（要ライセンス）
- ✅ FactSet - ファイルベースデータローダー（要契約）
- ✅ Mock Fetchers - テスト・開発用モック実装

<!-- END: IMPLEMENTATION -->

## 公開 API

<!-- AUTO-GENERATED: API -->

### クイックスタート

パッケージの基本的な使い方を最初に示します。

```python
from market_analysis import MarketData, Analysis, Chart

# 最も基本的な使い方（3ステップ）
data = MarketData()
stock_df = data.fetch_stock("AAPL", start="2024-01-01")

analysis = Analysis(stock_df)
result = analysis.add_sma(20).result()

chart = Chart(result.data)
chart.save("chart.png")
```

### 主要クラス

#### `MarketData`

**説明**: 市場データ取得の統合インターフェース。Yahoo Finance（yfinance）とFRED（米国経済指標）からデータを取得します。

**基本的な使い方**:

```python
from market_analysis import MarketData

# 初期化（キャッシュ有効）
data = MarketData(cache_path="data/cache.db")

# 株価データの取得
stock_df = data.fetch_stock("AAPL", start="2024-01-01", end="2024-12-31")

# 為替レートの取得
forex_df = data.fetch_forex("USDJPY", start="2024-01-01")

# 経済指標の取得（FRED APIキーが必要）
data_with_fred = MarketData(fred_api_key="your_api_key")
gdp_df = data_with_fred.fetch_fred("GDP", start="2020-01-01")
```

**主なメソッド**:

| メソッド | 説明 | 戻り値 |
|---------|------|--------|
| `fetch_stock(symbol, start, end)` | 株価データを取得 | `pd.DataFrame` |
| `fetch_forex(pair, start, end)` | 為替データを取得 | `pd.DataFrame` |
| `fetch_fred(series_id, start, end)` | FRED経済指標を取得 | `pd.DataFrame` |
| `fetch_index(symbol, start, end)` | 指数データを取得 | `pd.DataFrame` |

---

#### `Analysis`

**説明**: テクニカル分析を行うクラス。メソッドチェーンで複数の指標を順次追加できます。

**基本的な使い方**:

```python
from market_analysis import Analysis

# 初期化
analysis = Analysis(stock_df)

# 単一指標の追加
result = analysis.add_sma(20).result()

# 複数指標の組み合わせ（メソッドチェーン）
result = (
    analysis
    .add_sma(20)           # 単純移動平均
    .add_ema(12)           # 指数移動平均
    .add_returns()         # リターン計算
    .add_volatility(20)    # ボラティリティ
    .result()
)

# 相関分析（クラスメソッド）
corr_matrix = Analysis.correlation([aapl_df, msft_df])
```

**主なメソッド**:

| メソッド | 説明 | 戻り値 |
|---------|------|--------|
| `add_sma(window)` | 単純移動平均を追加 | `Self` |
| `add_ema(span)` | 指数移動平均を追加 | `Self` |
| `add_returns()` | リターンを計算 | `Self` |
| `add_volatility(window)` | ボラティリティを計算 | `Self` |
| `result()` | 分析結果を取得 | `AnalysisResult` |
| `correlation(dataframes)` | 相関分析（クラスメソッド） | `pd.DataFrame` |

---

#### `Chart`

**説明**: チャート生成インターフェース。価格チャート、ヒートマップを作成できます。

**基本的な使い方**:

```python
from market_analysis import Chart

# 初期化
chart = Chart(stock_df, title="AAPL 株価チャート")

# 価格チャートの生成（指標オーバーレイ付き）
fig = chart.price_chart(overlays=["SMA_20", "EMA_50"])

# ファイル保存
chart.save("chart.png")

# 相関ヒートマップ（クラスメソッド）
corr_matrix = Analysis.correlation([aapl_df, msft_df])
fig = Chart.correlation_heatmap(corr_matrix, title="株価相関マップ")
```

**主なメソッド**:

| メソッド | 説明 | 戻り値 |
|---------|------|--------|
| `price_chart(overlays)` | 価格チャートを生成 | `go.Figure` |
| `save(filepath)` | チャートをファイル保存 | `None` |
| `correlation_heatmap(matrix, title)` | 相関ヒートマップ（クラスメソッド） | `go.Figure` |

---

#### `MarketPerformanceAnalyzer`

**説明**: 主要インデックス、セクター、個別株のパフォーマンスを一元的に分析・可視化するクラス。株価データ取得、リターン計算、累積リターンプロットを提供します。

**基本的な使い方**:

```python
from market_analysis import MarketPerformanceAnalyzer

# 初期化（自動的にデータを取得・計算）
analyzer = MarketPerformanceAnalyzer()

# 累積リターンの取得
cum_returns = analyzer.cum_return_plot

# パフォーマンステーブルの取得
perf_table = analyzer.performance_table
```

**主なメソッド**:

| メソッド | 説明 | 戻り値 |
|---------|------|--------|
| `yf_download_with_curl(tickers)` | yfinanceでデータ取得 | `pd.DataFrame` |
| `plot_cumulative_returns(...)` | 累積リターンをプロット | `go.Figure` |

**対象資産**:
- 米国主要指数: S&P 500, ダウ, ナスダック等
- MAG7 + 半導体: AAPL, MSFT, NVDA, GOOGL, AMZN, TSLA, META, ^SOX
- セクター: 11セクター（XLK, XLF, XLV等）
- 商品: 金属（GLD, SLV等）、原油（CL=F）
- センチメント: VIX, ドル指数

---

### 内部分析クラス（上級ユーザー向け）

より細かい制御が必要な場合は、内部クラスを直接使用できます。

```python
from market_analysis import Analyzer, CorrelationAnalyzer, IndicatorCalculator

# Analyzer: 低レベル分析インターフェース
analyzer = Analyzer(stock_df, symbol="AAPL")

# CorrelationAnalyzer: 相関分析専用クラス
corr_analyzer = CorrelationAnalyzer()
corr_matrix = corr_analyzer.calculate([df1, df2])

# IndicatorCalculator: 指標計算専用クラス
calc = IndicatorCalculator(stock_df)
sma = calc.sma(window=20)
```

---

### データエクスポート

#### `DataExporter`

**説明**: 分析結果をCSV、JSON、Parquet形式でエクスポートします。

**使用例**:

```python
from market_analysis import DataExporter

exporter = DataExporter()
exporter.to_csv(result.data, "output.csv")
exporter.to_json(result.data, "output.json")
exporter.to_parquet(result.data, "output.parquet")
```

---

### 型定義

データ構造の定義。型ヒントやバリデーションに使用します。

```python
from market_analysis import (
    # Enum型（定数定義）
    AssetType,       # 資産タイプ（STOCK, FOREX, CRYPTO等）
    DataSource,      # データソース（YFINANCE, FRED）
    Interval,        # 時間間隔（1d, 1wk, 1mo等）

    # TypedDict（データ構造）
    AgentOutput,           # エージェント出力形式
    AgentOutputMetadata,   # メタデータ
    AnalysisOptions,       # 分析オプション
    AnalysisResult,        # 分析結果
    CacheConfig,           # キャッシュ設定
    ChartOptions,          # チャートオプション
    CorrelationResult,     # 相関分析結果
    ExportOptions,         # エクスポートオプション
    FetchOptions,          # データ取得オプション
    MarketDataResult,      # 市場データ結果
    RetryConfig,           # リトライ設定
)
```

---

### エラーハンドリング

例外処理に使用するエラークラスです。

```python
from market_analysis import (
    MarketAnalysisError,  # 基底例外クラス
    AnalysisError,        # 分析処理のエラー
    CacheError,           # キャッシュ操作のエラー
    DataFetchError,       # データ取得のエラー
    ErrorCode,            # エラーコード定数
    ExportError,          # エクスポート処理のエラー
    RateLimitError,       # APIレート制限エラー
    TimeoutError,         # タイムアウトエラー
    ValidationError,      # バリデーションエラー
)

# 使用例
try:
    data = MarketData()
    stock_df = data.fetch_stock("INVALID_SYMBOL")
except DataFetchError as e:
    print(f"データ取得失敗: {e}")
```

---

### ユーティリティ

便利な補助機能を提供します。

```python
from market_analysis import (
    PRESET_GROUPS,         # プリセットティッカーグループ
    TickerInfo,            # ティッカー情報（TypedDict）
    TickerRegistry,        # ティッカーレジストリクラス
    get_logger,            # ロガー取得関数
    get_ticker_registry,   # レジストリ取得関数
)

# ティッカーレジストリの使用
registry = get_ticker_registry()
ticker_info = registry.get("AAPL")
print(ticker_info["name"])  # "Apple Inc."

# ロガーの使用
logger = get_logger(__name__)
logger.info("処理開始")
```

<!-- END: API -->

## 統計

<!-- AUTO-GENERATED: STATS -->

| 項目 | 値 |
|-----|-----|
| Pythonファイル数 | 35 |
| 総行数（実装コード） | 12,818 |
| モジュール数 | 8 |
| テストファイル数 | 22 |
| テストカバレッジ | N/A |

**モジュール構成**:
- コアモジュール: `types.py` (型定義13種, 592行), `errors.py` (例外クラス8種, 521行)
- 機能モジュール: `api/` (4クラス, 2,552行), `analysis/` (6クラス, 2,974行), `core/` (8フェッチャー, 3,705行), `export/` (1クラス, 678行), `utils/` (7モジュール, 2,753行), `visualization/` (4クラス, 1,736行)

**実装進捗**:
- 完全実装: 8/8 モジュール (100%)
- テスト整備: 8/8 モジュール (100%) - 全モジュールに単体テスト整備完了
- テスト数: 単体テスト 21ファイル、統合テスト 1ファイル

**最新追加機能（2026-01）**:
- セクター分析（sector.py）: 11セクターのETFパフォーマンス、トップ/ボトムセクター検出、寄与銘柄分析
- 決算カレンダー（earnings.py）: 決算予定日取得、EPS/売上予想の抽出、期間フィルタリング
- 多期間騰落率（returns.py）: 1D/1W/MTD/1M/3M/6M/YTD/1Y/3Y/5Y のリターン計算、米国/グローバル指数対応

**データソース**:
- Yahoo Finance (yfinance) - 株価・為替・指数データ
- FRED (Federal Reserve Economic Data) - 米国経済指標
- Bloomberg Terminal (BLPAPI) - プロフェッショナル市場データ（要ライセンス）
- FactSet - ファイルベースデータローダー（要契約）
- Mock Fetchers - テスト・開発用モック実装

<!-- END: STATS -->

## 拡張ガイド

1. **コアモジュール追加**: `/issue` → `feature-implementer` で TDD 実装
2. **ユーティリティ追加**: `/issue` → `feature-implementer` で TDD 実装
3. **型定義追加**: `types.py` に追加
4. **例外追加**: `errors.py` に追加

## 関連ドキュメント

-   `docs/project.md` - プロジェクトファイル
-   `docs/library-requirements.md` - ライブラリ要求定義書
-   `docs/functional-design.md` - 機能設計書
-   `docs/architecture.md` - アーキテクチャ設計書
-   `docs/development-guidelines.md` - 開発ガイドライン

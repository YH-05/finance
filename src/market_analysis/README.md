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

<!-- END: QUICKSTART -->

## ディレクトリ構成

<!-- AUTO-GENERATED: STRUCTURE -->
```
market_analysis/
├── __init__.py                  # 公開API定義（__version__, __all__）
├── py.typed                     # PEP 561マーカー
├── types.py                     # 型定義（TypedDict, Enum等）
├── errors.py                    # 例外クラス定義
├── api/                         # パブリックAPI（推奨エントリポイント）
│   ├── __init__.py
│   ├── analysis.py              # Analysis - テクニカル分析（メソッドチェーン対応）
│   ├── chart.py                 # Chart - チャート生成インターフェース
│   └── market_data.py           # MarketData - データ取得統合インターフェース
├── analysis/                    # 分析ロジック
│   ├── __init__.py
│   ├── analyzer.py              # Analyzer（メイン分析クラス）
│   ├── correlation.py           # CorrelationAnalyzer（相関分析）
│   └── indicators.py            # IndicatorCalculator（テクニカル指標）
├── core/                        # データフェッチャー
│   ├── __init__.py
│   ├── base_fetcher.py          # BaseDataFetcher（抽象基底クラス）
│   ├── data_fetcher_factory.py  # DataFetcherFactory（ファクトリパターン）
│   ├── yfinance_fetcher.py      # YFinanceFetcher（Yahoo Finance株価）
│   ├── fred_fetcher.py          # FREDFetcher（FRED API経済指標）
│   ├── bloomberg_fetcher.py     # BloombergFetcher（Bloomberg Terminal）
│   ├── factset_fetcher.py       # FactSetFetcher（FactSetファイルローダー）
│   └── mock_fetchers.py         # MockFetchers（テスト用モック実装）
├── export/                      # データエクスポート
│   ├── __init__.py
│   └── exporter.py              # DataExporter（CSV/JSON/Parquet）
├── utils/                       # ユーティリティ関数
│   ├── __init__.py
│   ├── cache.py                 # SQLiteキャッシュ（TTL付き）
│   ├── logger_factory.py        # ロガー生成ファクトリ
│   ├── logging_config.py        # 構造化ロギング設定
│   ├── retry.py                 # リトライデコレータ（指数バックオフ）
│   ├── ticker_registry.py       # ティッカーレジストリ（シンボル管理）
│   └── validators.py            # バリデーション関数（日付・ティッカー等）
├── visualization/               # チャート生成
│   ├── __init__.py
│   ├── charts.py                # ChartBuilder, ChartConfig, ChartTheme
│   ├── heatmap.py               # HeatmapChart（相関マトリクス可視化）
│   └── price_charts.py          # CandlestickChart, LineChart（価格チャート）
└── docs/                        # ライブラリドキュメント
    ├── project.md               # プロジェクトファイル
    ├── architecture.md          # アーキテクチャ設計書
    ├── development-guidelines.md # 開発ガイドライン
    ├── functional-design.md     # 機能設計書
    ├── glossary.md              # 用語集
    ├── library-requirements.md  # LRD（ライブラリ要求定義書）
    ├── repository-structure.md  # リポジトリ構造定義書
    └── tasks.md                 # タスク管理
```
<!-- END: STRUCTURE -->

## 実装状況

<!-- AUTO-GENERATED: IMPLEMENTATION -->

| モジュール | 状態 | ファイル数 | 行数 | テスト | 備考 |
|-----------|------|-----------|------|-------|------|
| `types.py` | ✅ 実装済み | 1 | 555 | ✅ | TypedDict, Enum等の型定義（18型） |
| `errors.py` | ✅ 実装済み | 1 | 515 | ✅ | MarketAnalysisError等の例外クラス（8エラー） |
| `api/` | ✅ 実装済み | 3 | 1,475 | ✅ (3) | MarketData, Analysis, Chart（メソッドチェーン対応） |
| `analysis/` | ✅ 実装済み | 3 | 1,158 | ✅ (3) | Analyzer, IndicatorCalculator, CorrelationAnalyzer |
| `core/` | ✅ 実装済み | 7 | 3,746 | ✅ (7) | BaseDataFetcher, YFinanceFetcher, FREDFetcher, BloombergFetcher, FactSetFetcher, MockFetchers |
| `export/` | ✅ 実装済み | 1 | 582 | ✅ | DataExporter（CSV/JSON/Parquet対応） |
| `utils/` | ✅ 実装済み | 6 | 2,244 | ✅ (2) | logging, validators, cache, retry, ticker_registry |
| `visualization/` | ✅ 実装済み | 3 | 1,392 | ✅ (3) | ChartBuilder, CandlestickChart, HeatmapChart |

**テスト構成**: 単体テスト (18) + 統合テスト (0) = 計18テスト

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
| Pythonファイル数 | 32 |
| 総行数（実装コード） | 13,429 |
| モジュール数 | 8 |
| テストファイル数 | 18 |
| テストカバレッジ | N/A |

**モジュール構成**:
- コアモジュール: `types.py` (型定義18種), `errors.py` (例外クラス8種)
- 機能モジュール: `api/` (3クラス), `analysis/` (3クラス), `core/` (7フェッチャー), `export/` (1クラス), `utils/` (6モジュール), `visualization/` (3クラス)

**実装進捗**:
- 完全実装: 8/8 モジュール (100%)
- テスト整備: 8/8 モジュール (100%) - 全モジュールに単体テスト整備完了
- テスト数: 単体テスト 18ファイル、統合テスト 0ファイル

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

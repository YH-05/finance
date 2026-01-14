# market_analysis

金融市場分析パッケージ

## 概要

このパッケージは市場データの取得・分析・可視化機能を提供します。

**現在のバージョン:** 0.1.0

## ディレクトリ構成

<!-- AUTO-GENERATED: STRUCTURE -->
```
market_analysis/
├── __init__.py              # 公開API定義（__version__含む）
├── py.typed                 # PEP 561マーカー
├── types.py                 # 型定義（TypedDict, Enum等）
├── errors.py                # 例外クラス定義
├── api/                     # パブリックAPI（推奨エントリポイント）
│   ├── __init__.py
│   ├── analysis.py          # Analysis - テクニカル分析（メソッドチェーン対応）
│   └── market_data.py       # MarketData - データ取得統合インターフェース
├── analysis/                # 分析ロジック
│   ├── __init__.py
│   ├── analyzer.py          # Analyzer（メイン分析クラス）
│   ├── correlation.py       # CorrelationAnalyzer（相関分析）
│   └── indicators.py        # IndicatorCalculator（テクニカル指標）
├── core/                    # データフェッチャー
│   ├── __init__.py
│   ├── base_fetcher.py      # BaseDataFetcher（抽象基底クラス）
│   ├── data_fetcher_factory.py  # DataFetcherFactory
│   ├── fred_fetcher.py      # FREDFetcher（FRED API）
│   └── yfinance_fetcher.py  # YFinanceFetcher（Yahoo Finance）
├── export/                  # データエクスポート
│   ├── __init__.py
│   └── exporter.py          # DataExporter
├── utils/                   # ユーティリティ関数
│   ├── __init__.py
│   ├── cache.py             # SQLiteキャッシュ
│   ├── logger_factory.py    # ロガー生成
│   ├── logging_config.py    # 構造化ロギング設定
│   ├── retry.py             # リトライ機能
│   ├── ticker_registry.py   # ティッカーレジストリ
│   └── validators.py        # バリデーション
├── visualization/           # チャート生成
│   ├── __init__.py
│   ├── charts.py            # ChartBuilder, ChartConfig, ChartTheme
│   ├── heatmap.py           # HeatmapChart
│   └── price_charts.py      # CandlestickChart, LineChart
└── docs/                    # ライブラリドキュメント
    ├── project.md               # プロジェクトファイル
    ├── architecture.md          # アーキテクチャ設計書
    ├── development-guidelines.md # 開発ガイドライン
    ├── functional-design.md     # 機能設計書
    ├── glossary.md              # 用語集
    ├── library-requirements.md  # LRD
    ├── repository-structure.md  # リポジトリ構造定義書
    └── tasks.md                 # タスク管理
```
<!-- END: STRUCTURE -->

## 実装状況

<!-- AUTO-GENERATED: IMPLEMENTATION -->

| モジュール | 状態 | ファイル数 | 行数 | テスト | 備考 |
|-----------|------|-----------|-----|-------|------|
| `types.py` | ✅ 実装済み | 1 | 555 | - | TypedDict, Enum等の型定義 |
| `errors.py` | ✅ 実装済み | 1 | 515 | - | MarketAnalysisError等の例外クラス |
| `api/` | ✅ 実装済み | 3 | 1,326 | 2 | MarketData, Analysis（メソッドチェーン対応） |
| `analysis/` | ✅ 実装済み | 4 | 1,427 | 3 | Analyzer, IndicatorCalculator, CorrelationAnalyzer |
| `core/` | ✅ 実装済み | 5 | 1,650 | 4 | BaseDataFetcher, YFinanceFetcher, FREDFetcher |
| `export/` | ✅ 実装済み | 2 | 692 | 1 | DataExporter |
| `utils/` | ✅ 実装済み | 7 | 2,746 | 1 | logging, validators, cache, retry, ticker_registry |
| `visualization/` | ✅ 実装済み | 4 | 1,747 | 3 | ChartBuilder, CandlestickChart, HeatmapChart |

<!-- END: IMPLEMENTATION -->

## 公開 API

<!-- AUTO-GENERATED: API -->

### 主要インターフェース（推奨）

```python
from market_analysis import MarketData, Analysis

# データ取得
data = MarketData()
stock_df = data.fetch_stock("AAPL", start="2024-01-01")

# テクニカル分析（メソッドチェーン）
analysis = Analysis(stock_df)
result = analysis.add_sma(20).add_returns().result()
```

### 内部分析クラス（上級ユーザー向け）

```python
from market_analysis import Analyzer, CorrelationAnalyzer, IndicatorCalculator
```

### チャート生成

```python
from market_analysis.visualization import CandlestickChart, HeatmapChart, PriceChartData

# ローソク足チャート
data = PriceChartData(df=ohlcv_df, symbol="AAPL")
chart = CandlestickChart(data).add_sma(20).build()
chart.save("chart.png")

# ヒートマップ
chart = HeatmapChart(correlation_matrix).build().save("heatmap.png")
```

### データエクスポート

```python
from market_analysis import DataExporter
```

### 型定義

```python
from market_analysis import (
    # Enum
    AssetType,
    DataSource,
    Interval,
    # TypedDict / Options
    AgentOutput,
    AgentOutputMetadata,
    AnalysisOptions,
    AnalysisResult,
    CacheConfig,
    ChartOptions,
    CorrelationResult,
    ExportOptions,
    FetchOptions,
    MarketDataResult,
    RetryConfig,
)
```

### エラーハンドリング

```python
from market_analysis import (
    MarketAnalysisError,  # 基底例外
    AnalysisError,        # 分析エラー
    CacheError,           # キャッシュエラー
    DataFetchError,       # データ取得エラー
    ErrorCode,            # エラーコード定数
    ExportError,          # エクスポートエラー
    RateLimitError,       # レート制限エラー
    TimeoutError,         # タイムアウトエラー
    ValidationError,      # バリデーションエラー
)
```

### ユーティリティ

```python
from market_analysis import (
    PRESET_GROUPS,
    TickerInfo,
    TickerRegistry,
    get_logger,
    get_ticker_registry,
)
```
<!-- END: API -->

## 統計

<!-- AUTO-GENERATED: STATS -->

| 項目 | 値 |
|-----|---|
| Pythonファイル数 | 28 |
| 総行数（実装コード） | 9,784 |
| モジュール数 | 6 |
| テストファイル数 | 14 |
| テストカバレッジ | N/A |

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

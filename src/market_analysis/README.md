# market_analysis

金融市場分析パッケージ

## 概要

このパッケージは市場データの取得・分析・可視化機能を提供します。

**現在のバージョン:** 0.1.0

## ディレクトリ構成

```
market_analysis/
├── __init__.py              # 公開 API 定義（__version__含む）
├── py.typed                 # PEP 561 マーカー
├── types.py                 # 型定義（TypedDict, Enum等）
├── errors.py                # 例外クラス定義
├── api/                     # パブリック API（推奨エントリポイント）
│   ├── __init__.py
│   ├── market_data.py       # MarketData - データ取得統合インターフェース
│   └── analysis.py          # Analysis - テクニカル分析（メソッドチェーン対応）
├── core/                    # データフェッチャー
│   ├── __init__.py
│   ├── base_fetcher.py      # BaseDataFetcher（抽象基底クラス）
│   ├── yfinance_fetcher.py  # YFinanceFetcher（Yahoo Finance）
│   ├── fred_fetcher.py      # FREDFetcher（FRED API）
│   └── data_fetcher_factory.py  # DataFetcherFactory
├── analysis/                # 分析ロジック
│   ├── __init__.py
│   ├── analyzer.py          # Analyzer（メイン分析クラス）
│   ├── indicators.py        # IndicatorCalculator（テクニカル指標）
│   └── correlation.py       # CorrelationAnalyzer（相関分析）
├── visualization/           # チャート生成
│   ├── __init__.py
│   ├── charts.py            # ChartBuilder, ChartConfig, ChartTheme
│   ├── price_charts.py      # CandlestickChart, LineChart
│   └── heatmap.py           # HeatmapChart
├── export/                  # データエクスポート
│   ├── __init__.py
│   └── exporter.py          # DataExporter
├── utils/                   # ユーティリティ関数
│   ├── __init__.py
│   ├── logging_config.py    # 構造化ロギング設定
│   ├── logger_factory.py    # ロガー生成
│   ├── validators.py        # バリデーション
│   ├── cache.py             # SQLiteキャッシュ
│   ├── retry.py             # リトライ機能
│   └── ticker_registry.py   # ティッカーレジストリ
└── docs/                    # ライブラリドキュメント
    ├── project.md           # プロジェクトファイル
    ├── library-requirements.md  # LRD
    ├── functional-design.md     # 機能設計書
    ├── architecture.md          # アーキテクチャ設計書
    ├── repository-structure.md  # リポジトリ構造定義書
    ├── development-guidelines.md # 開発ガイドライン
    ├── glossary.md              # 用語集
    └── tasks.md                 # タスク管理
```

## 実装状況

| モジュール                | 状態        | 備考                                      |
| ------------------------- | ----------- | ----------------------------------------- |
| `types.py`                | ✅ 実装済み | TypedDict, Enum等の型定義                 |
| `errors.py`               | ✅ 実装済み | MarketAnalysisError等の例外クラス         |
| `api/market_data.py`      | ✅ 実装済み | MarketData - データ取得統合API            |
| `api/analysis.py`         | ✅ 実装済み | Analysis - メソッドチェーン対応分析API    |
| `core/base_fetcher.py`    | ✅ 実装済み | BaseDataFetcher抽象基底クラス             |
| `core/yfinance_fetcher.py`| ✅ 実装済み | YFinanceFetcher（株価・為替・指標）       |
| `core/fred_fetcher.py`    | ✅ 実装済み | FREDFetcher（経済指標）                   |
| `core/data_fetcher_factory.py` | ✅ 実装済み | DataFetcherFactory                   |
| `analysis/analyzer.py`    | ✅ 実装済み | Analyzer（メイン分析クラス）              |
| `analysis/indicators.py`  | ✅ 実装済み | IndicatorCalculator（SMA, EMA, RSI等）    |
| `analysis/correlation.py` | ✅ 実装済み | CorrelationAnalyzer                       |
| `visualization/charts.py` | ✅ 実装済み | ChartBuilder, ChartConfig, ChartTheme     |
| `visualization/price_charts.py` | ✅ 実装済み | CandlestickChart, LineChart         |
| `visualization/heatmap.py`| ✅ 実装済み | HeatmapChart                              |
| `export/exporter.py`      | ✅ 実装済み | DataExporter                              |
| `utils/logging_config.py` | ✅ 実装済み | 構造化ロギング                            |
| `utils/validators.py`     | ✅ 実装済み | バリデーション                            |
| `utils/cache.py`          | ✅ 実装済み | SQLiteキャッシュ                          |
| `utils/retry.py`          | ✅ 実装済み | リトライ機能                              |
| `utils/ticker_registry.py`| ✅ 実装済み | ティッカーレジストリ                      |

## 公開 API

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
    AssetType, DataSource, Interval,
    FetchOptions, AnalysisOptions, ChartOptions, ExportOptions,
    MarketDataResult, AnalysisResult, CorrelationResult,
)
```

### エラーハンドリング

```python
from market_analysis import (
    MarketAnalysisError,  # 基底例外
    DataFetchError,       # データ取得エラー
    ValidationError,      # バリデーションエラー
    AnalysisError,        # 分析エラー
    CacheError,           # キャッシュエラー
    ExportError,          # エクスポートエラー
    RateLimitError,       # レート制限エラー
    TimeoutError,         # タイムアウトエラー
)
```

### ユーティリティ

```python
from market_analysis import get_logger, TickerRegistry, get_ticker_registry, PRESET_GROUPS
```

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

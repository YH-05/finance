# market_analysis

金融市場分析パッケージ

## 概要

このパッケージは市場データの取得・分析・可視化機能を提供します。

**現在のバージョン:** 0.1.0

## ディレクトリ構成

<!-- AUTO-GENERATED: STRUCTURE -->
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
<!-- END: STRUCTURE -->

## 実装状況

<!-- AUTO-GENERATED: IMPLEMENTATION -->

| モジュール | 状態 | ファイル数 | 行数 | 備考 |
|-----------|------|-----------|-----|------|
| `types.py` | ✅ 実装済み | 1 | 555 | TypedDict, Enum等の型定義 |
| `errors.py` | ✅ 実装済み | 1 | 515 | MarketAnalysisError等の例外クラス |
| `api/` | ✅ 実装済み | 3 | 1,326 | MarketData, Analysis（メソッドチェーン対応） |
| `core/` | ✅ 実装済み | 5 | 1,650 | BaseDataFetcher, YFinanceFetcher, FREDFetcher |
| `analysis/` | ✅ 実装済み | 4 | 1,427 | Analyzer, IndicatorCalculator, CorrelationAnalyzer |
| `visualization/` | ✅ 実装済み | 4 | 1,747 | ChartBuilder, CandlestickChart, HeatmapChart |
| `export/` | ✅ 実装済み | 2 | 692 | DataExporter |
| `utils/` | ✅ 実装済み | 7 | 2,746 | logging, validators, cache, retry, ticker_registry |

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
<!-- END: API -->

## 統計

<!-- AUTO-GENERATED: STATS -->

| 項目 | 値 |
|-----|---|
| Pythonファイル数 | 28 |
| 総行数（実装コード） | 10,785 |
| モジュール数 | 8 |
| テストファイル数 | 24 |
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

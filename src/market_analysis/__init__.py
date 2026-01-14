"""market_analysis package.

金融市場データの取得・分析・可視化を行う Python ライブラリ。

Public API
----------
MarketData
    市場データ取得の統合インターフェース
Analysis
    テクニカル分析（メソッドチェーン対応）
Chart
    チャート生成（価格チャート、ヒートマップ）
__version__
    パッケージバージョン

Examples
--------
>>> from market_analysis import MarketData, Analysis, Chart
>>> data = MarketData()
>>> stock_df = data.fetch_stock("AAPL", start="2024-01-01")
>>> analysis = Analysis(stock_df)
>>> result = analysis.add_sma(20).add_returns().result()
>>>
>>> chart = Chart(stock_df, title="AAPL Price Chart")
>>> chart.price_chart(overlays=["SMA_20", "EMA_50"])
>>> chart.save("chart.png")
"""

# =============================================================================
# Public API - メインの公開インターフェース
# Analysis Classes - 内部分析クラス（上級ユーザー向け）
# =============================================================================
from .analysis import Analyzer, CorrelationAnalyzer, IndicatorCalculator
from .api import Analysis, Chart, MarketData

# =============================================================================
# Errors - 例外クラス
# =============================================================================
from .errors import (
    AnalysisError,
    CacheError,
    DataFetchError,
    ErrorCode,
    ExportError,
    MarketAnalysisError,
    RateLimitError,
    TimeoutError,
    ValidationError,
)

# =============================================================================
# Export - データエクスポート
# =============================================================================
from .export import DataExporter

# =============================================================================
# Types - 型定義
# =============================================================================
from .types import (
    AgentOutput,
    AgentOutputMetadata,
    AnalysisOptions,
    AnalysisResult,
    AssetType,
    CacheConfig,
    ChartOptions,
    CorrelationResult,
    DataSource,
    ExportOptions,
    FetchOptions,
    Interval,
    MarketDataResult,
    RetryConfig,
)

# =============================================================================
# Utilities - ユーティリティ
# =============================================================================
from .utils import (
    PRESET_GROUPS,
    TickerInfo,
    TickerRegistry,
    get_logger,
    get_ticker_registry,
)

# =============================================================================
# __all__ - 公開シンボル定義
# =============================================================================
__all__ = [
    "PRESET_GROUPS",
    "AgentOutput",
    "AgentOutputMetadata",
    "Analysis",
    "AnalysisError",
    "AnalysisOptions",
    "AnalysisResult",
    "Analyzer",
    "AssetType",
    "CacheConfig",
    "CacheError",
    "Chart",
    "ChartOptions",
    "CorrelationAnalyzer",
    "CorrelationResult",
    "DataExporter",
    "DataFetchError",
    "DataSource",
    "ErrorCode",
    "ExportError",
    "ExportOptions",
    "FetchOptions",
    "IndicatorCalculator",
    "Interval",
    "MarketAnalysisError",
    "MarketData",
    "MarketDataResult",
    "RateLimitError",
    "RetryConfig",
    "TickerInfo",
    "TickerRegistry",
    "TimeoutError",
    "ValidationError",
    "get_logger",
    "get_ticker_registry",
]

__version__ = "0.1.0"

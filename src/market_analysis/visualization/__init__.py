"""Visualization module for creating financial charts and graphs.

This module provides tools for creating consistent, themed visualizations
of financial data using Plotly.

Examples
--------
>>> from market_analysis.visualization import ChartBuilder, ChartConfig, ChartTheme
>>> config = ChartConfig(theme=ChartTheme.DARK, title="Price Chart")

>>> from market_analysis.visualization import CandlestickChart, PriceChartData
>>> data = PriceChartData(df=ohlcv_df, symbol="AAPL")
>>> chart = CandlestickChart(data).add_sma(20).build()
>>> chart.save("chart.png")

>>> from market_analysis.visualization import HeatmapChart
>>> chart = HeatmapChart(correlation_matrix).build().save("heatmap.png")
"""

from .charts import (
    DARK_THEME_COLORS,
    DEFAULT_HEIGHT,
    DEFAULT_WIDTH,
    JAPANESE_FONT_STACK,
    LIGHT_THEME_COLORS,
    ChartBuilder,
    ChartConfig,
    ChartTheme,
    ExportFormat,
    ThemeColors,
    get_theme_colors,
)
from .heatmap import HeatmapChart
from .price_charts import (
    CandlestickChart,
    IndicatorOverlay,
    LineChart,
    PriceChartBuilder,
    PriceChartData,
)

__all__ = [
    "DARK_THEME_COLORS",
    "DEFAULT_HEIGHT",
    "DEFAULT_WIDTH",
    "JAPANESE_FONT_STACK",
    "LIGHT_THEME_COLORS",
    "CandlestickChart",
    "ChartBuilder",
    "ChartConfig",
    "ChartTheme",
    "ExportFormat",
    "HeatmapChart",
    "IndicatorOverlay",
    "LineChart",
    "PriceChartBuilder",
    "PriceChartData",
    "ThemeColors",
    "get_theme_colors",
]

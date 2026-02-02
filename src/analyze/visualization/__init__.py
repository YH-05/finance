"""Visualization module for creating financial charts and graphs.

This module provides tools for creating consistent, themed visualizations
of financial data using Plotly.

Examples
--------
>>> from analyze.visualization import ChartBuilder, ChartConfig, ChartTheme
>>> config = ChartConfig(theme=ChartTheme.DARK, title="Price Chart")

>>> from analyze.visualization import CandlestickChart, PriceChartData
>>> data = PriceChartData(df=ohlcv_df, symbol="AAPL")
>>> chart = CandlestickChart(data).add_sma(20).build()
>>> chart.save("chart.png")

>>> from analyze.visualization import HeatmapChart
>>> chart = HeatmapChart(correlation_matrix).build().save("heatmap.png")

>>> from analyze.visualization import apply_df_style, plot_cumulative_returns
>>> styled = apply_df_style(returns_df)
>>> fig = plot_cumulative_returns(price_df, ["AAPL", "MSFT"], "Performance")

>>> from analyze.visualization import plot_vix_and_high_yield_spread
>>> fig = plot_vix_and_high_yield_spread(volatility_df)

>>> from analyze.visualization import plot_rolling_correlation
>>> fig = plot_rolling_correlation(df_corr, ticker="AAPL", target_index="S&P 500")

>>> from analyze.visualization import plot_rolling_beta
>>> fig = plot_rolling_beta(df_beta, tickers=["AAPL", "MSFT"], target_index="S&P 500")

>>> from analyze.visualization import plot_dollar_index_and_metals
>>> fig = plot_dollar_index_and_metals(df_cum_return)
"""

from .beta import plot_rolling_beta
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
from .correlation import plot_rolling_correlation
from .currency import plot_dollar_index_and_metals
from .heatmap import HeatmapChart
from .performance import apply_df_style, plot_cumulative_returns
from .price_charts import (
    CandlestickChart,
    IndicatorOverlay,
    LineChart,
    PriceChartBuilder,
    PriceChartData,
)
from .volatility import plot_vix_and_high_yield_spread, plot_vix_and_uncertainty_index

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
    "apply_df_style",
    "get_theme_colors",
    "plot_cumulative_returns",
    "plot_dollar_index_and_metals",
    "plot_rolling_beta",
    "plot_rolling_correlation",
    "plot_vix_and_high_yield_spread",
    "plot_vix_and_uncertainty_index",
]

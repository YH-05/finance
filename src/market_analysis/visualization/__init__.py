"""Visualization module for creating financial charts and graphs.

This module provides tools for creating consistent, themed visualizations
of financial data using Plotly.

Examples
--------
>>> from market_analysis.visualization import ChartBuilder, ChartConfig, ChartTheme
>>> config = ChartConfig(theme=ChartTheme.DARK, title="Price Chart")
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

__all__ = [
    "DARK_THEME_COLORS",
    "DEFAULT_HEIGHT",
    "DEFAULT_WIDTH",
    "JAPANESE_FONT_STACK",
    "LIGHT_THEME_COLORS",
    "ChartBuilder",
    "ChartConfig",
    "ChartTheme",
    "ExportFormat",
    "ThemeColors",
    "get_theme_colors",
]

"""Correlation visualization module for financial data.

This module provides tools for visualizing correlation-related data,
including rolling correlation coefficients between securities and indices
using Plotly charts.

Examples
--------
>>> from analyze.visualization.correlation import plot_rolling_correlation
>>> import pandas as pd

>>> # Plot rolling correlation between a stock and an index
>>> df_corr = pd.DataFrame({
...     "AAPL": [0.5, 0.6, 0.55, 0.7, 0.65],
...     "MSFT": [0.4, 0.5, 0.45, 0.6, 0.55],
... }, index=pd.date_range("2024-01-01", periods=5))
>>> fig = plot_rolling_correlation(df_corr, ticker="AAPL", target_index="S&P 500")
>>> fig.show()
"""

import plotly.graph_objects as go
from pandas import DataFrame

from utils_core.logging import get_logger

from .charts import JAPANESE_FONT_STACK, ChartTheme, get_theme_colors

logger = get_logger(__name__)


def plot_rolling_correlation(
    df_corr: DataFrame,
    ticker: str,
    target_index: str,
) -> go.Figure:
    """Plot rolling correlation coefficient over time.

    Creates an interactive Plotly chart showing the rolling correlation
    coefficient between a ticker and a target index over time.

    Parameters
    ----------
    df_corr : DataFrame
        DataFrame with DatetimeIndex containing rolling correlation values.
        Each column represents a ticker's correlation with the target index.
    ticker : str
        Ticker symbol to plot (must be a column in df_corr).
    target_index : str
        Name of the target index for chart labeling (e.g., "S&P 500").

    Returns
    -------
    go.Figure
        Plotly Figure object with the rolling correlation chart.

    Examples
    --------
    >>> import pandas as pd
    >>> import numpy as np
    >>> dates = pd.date_range("2024-01-01", periods=100, freq="D")
    >>> df_corr = pd.DataFrame({
    ...     "AAPL": np.random.uniform(0.3, 0.9, 100),
    ...     "MSFT": np.random.uniform(0.4, 0.8, 100),
    ... }, index=dates)
    >>> fig = plot_rolling_correlation(df_corr, ticker="AAPL", target_index="S&P 500")
    >>> fig.show()

    Notes
    -----
    The correlation coefficient ranges from -1 to 1, where:
    - 1 indicates perfect positive correlation
    - 0 indicates no correlation
    - -1 indicates perfect negative correlation

    A horizontal line at y=0 is displayed as a reference.
    """
    logger.debug(
        "Creating rolling correlation plot",
        ticker=ticker,
        target_index=target_index,
        data_points=len(df_corr),
        columns=list(df_corr.columns) if not df_corr.empty else [],
    )

    # Create figure
    fig = go.Figure()

    if df_corr.empty:
        logger.warning("Empty DataFrame provided for rolling correlation plot")
        _apply_layout(
            fig,
            title=f"{ticker} vs {target_index} ローリング相関係数",
            yaxis_title="相関係数",
        )
        return fig

    # Get theme colors
    colors = get_theme_colors(ChartTheme.LIGHT)

    # Check if ticker exists in DataFrame
    if ticker not in df_corr.columns:
        logger.warning(
            "Ticker not found in DataFrame",
            ticker=ticker,
            available_columns=list(df_corr.columns),
        )
        _apply_layout(
            fig,
            title=f"{ticker} vs {target_index} ローリング相関係数",
            yaxis_title="相関係数",
        )
        return fig

    # Extract correlation data for the specified ticker
    corr_data = df_corr[ticker].dropna()

    if corr_data.empty:
        logger.warning("No valid correlation data for ticker", ticker=ticker)
        _apply_layout(
            fig,
            title=f"{ticker} vs {target_index} ローリング相関係数",
            yaxis_title="相関係数",
        )
        return fig

    # Add correlation line trace
    fig.add_trace(
        go.Scatter(
            x=corr_data.index,
            y=corr_data.values,
            mode="lines",
            name=f"{ticker} 相関係数",
            line={"color": colors.series_colors[0], "width": 2},
            hovertemplate=(
                f"{ticker} vs {target_index}<br>"
                "%{x|%Y-%m-%d}<br>"
                "相関係数: %{y:.3f}<extra></extra>"
            ),
        )
    )

    logger.debug("Correlation trace added", ticker=ticker, data_points=len(corr_data))

    # Apply layout with zero reference line
    _apply_layout(
        fig,
        title=f"{ticker} vs {target_index} ローリング相関係数",
        yaxis_title="相関係数",
    )

    # Add horizontal line at y=0 for reference
    fig.add_shape(
        type="line",
        x0=corr_data.index.min(),
        x1=corr_data.index.max(),
        y0=0,
        y1=0,
        line={
            "color": colors.grid,
            "width": 1,
            "dash": "dash",
        },
    )

    logger.info(
        "Rolling correlation plot created",
        ticker=ticker,
        target_index=target_index,
        traces=len(list(fig.data)),
    )

    return fig


def _apply_layout(
    fig: go.Figure,
    title: str,
    yaxis_title: str,
) -> None:
    """Apply common layout settings for correlation charts.

    Parameters
    ----------
    fig : go.Figure
        Plotly figure to update.
    title : str
        Chart title.
    yaxis_title : str
        Title for the y-axis.
    """
    colors = get_theme_colors(ChartTheme.LIGHT)

    fig.update_layout(
        title={
            "text": title,
            "font": {
                "family": JAPANESE_FONT_STACK,
                "size": 18,
                "color": colors.text,
            },
            "x": 0.5,
            "xanchor": "center",
        },
        font={
            "family": JAPANESE_FONT_STACK,
            "size": 12,
            "color": colors.text,
        },
        paper_bgcolor=colors.paper,
        plot_bgcolor=colors.background,
        xaxis={
            "title": "Date",
            "gridcolor": colors.grid,
            "linecolor": colors.axis,
            "showgrid": True,
        },
        yaxis={
            "title": {
                "text": yaxis_title,
                "font": {
                    "family": JAPANESE_FONT_STACK,
                    "color": colors.text,
                },
            },
            "gridcolor": colors.grid,
            "linecolor": colors.axis,
            "showgrid": True,
            "zeroline": True,
            "zerolinecolor": colors.grid,
            "zerolinewidth": 1,
            "tickfont": {
                "family": JAPANESE_FONT_STACK,
                "color": colors.text,
            },
        },
        showlegend=True,
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "xanchor": "center",
            "x": 0.5,
            "font": {
                "family": JAPANESE_FONT_STACK,
                "size": 11,
                "color": colors.text,
            },
        },
        margin={"l": 60, "r": 40, "t": 80, "b": 60},
        hovermode="x unified",
    )


# =============================================================================
# __all__ Export
# =============================================================================

__all__ = [
    "plot_rolling_correlation",
]

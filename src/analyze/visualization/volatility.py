"""Volatility visualization module for financial data.

This module provides tools for visualizing volatility-related data,
including VIX, high yield spreads, and economic policy uncertainty indices
using dual-axis Plotly charts.

Examples
--------
>>> from analyze.visualization.volatility import (
...     plot_vix_and_high_yield_spread,
...     plot_vix_and_uncertainty_index,
... )
>>> import pandas as pd

>>> # Plot VIX and High Yield Spread
>>> df = pd.DataFrame({
...     "VIX": [15.0, 16.0, 17.0],
...     "High_Yield_Spread": [4.0, 4.2, 4.3],
... }, index=pd.date_range("2024-01-01", periods=3))
>>> fig = plot_vix_and_high_yield_spread(df)
>>> fig.show()

>>> # Plot VIX and Uncertainty Index with EMA
>>> df = pd.DataFrame({
...     "VIX": [15.0, 16.0, 17.0],
...     "Uncertainty_Index": [100.0, 110.0, 105.0],
... }, index=pd.date_range("2024-01-01", periods=3))
>>> fig = plot_vix_and_uncertainty_index(df, ema_span=10)
>>> fig.show()
"""

import plotly.graph_objects as go
from pandas import DataFrame

from utils_core.logging import get_logger

from .charts import JAPANESE_FONT_STACK, ChartTheme, get_theme_colors

logger = get_logger(__name__)


def plot_vix_and_high_yield_spread(df: DataFrame) -> go.Figure:
    """Plot VIX and High Yield Spread on a dual-axis chart.

    Creates an interactive Plotly chart with VIX on the left y-axis
    and High Yield Spread on the right y-axis, allowing comparison
    of volatility and credit risk indicators.

    Parameters
    ----------
    df : DataFrame
        DataFrame with DatetimeIndex and columns:
        - "VIX": VIX volatility index values
        - "High_Yield_Spread": High yield spread values (in percentage points)

    Returns
    -------
    go.Figure
        Plotly Figure object with dual-axis chart

    Examples
    --------
    >>> import pandas as pd
    >>> dates = pd.date_range("2024-01-01", periods=5, freq="D")
    >>> df = pd.DataFrame({
    ...     "VIX": [15.0, 16.0, 17.0, 18.0, 19.0],
    ...     "High_Yield_Spread": [4.0, 4.2, 4.3, 4.5, 4.6],
    ... }, index=dates)
    >>> fig = plot_vix_and_high_yield_spread(df)
    >>> fig.show()

    Notes
    -----
    VIX (CBOE Volatility Index) measures market expectations of
    near-term volatility. High Yield Spread (also known as junk bond
    spread) measures the difference between high yield and investment
    grade bond yields, indicating credit risk appetite.
    """
    logger.debug(
        "Creating VIX and High Yield Spread plot",
        data_points=len(df),
        columns=list(df.columns) if not df.empty else [],
    )

    # Create figure
    fig = go.Figure()

    if df.empty:
        logger.warning("Empty DataFrame provided for VIX and High Yield Spread plot")
        _apply_layout(
            fig,
            title="VIX vs ハイイールドスプレッド",
            yaxis1_title="VIX",
            yaxis2_title="ハイイールドスプレッド (%)",
        )
        return fig

    # Get theme colors
    colors = get_theme_colors(ChartTheme.LIGHT)

    # Extract data (handle missing columns gracefully)
    vix_col = "VIX" if "VIX" in df.columns else None
    spread_col = "High_Yield_Spread" if "High_Yield_Spread" in df.columns else None

    # Add VIX trace (left y-axis)
    if vix_col:
        vix_data = df[vix_col].dropna()
        fig.add_trace(
            go.Scatter(
                x=vix_data.index,
                y=vix_data.values,
                mode="lines",
                name="VIX",
                line={"color": colors.series_colors[0], "width": 2},
                hovertemplate="VIX<br>%{x}<br>%{y:.2f}<extra></extra>",
                yaxis="y",
            )
        )
        logger.debug("VIX trace added", data_points=len(vix_data))

    # Add High Yield Spread trace (right y-axis)
    if spread_col:
        spread_data = df[spread_col].dropna()
        fig.add_trace(
            go.Scatter(
                x=spread_data.index,
                y=spread_data.values,
                mode="lines",
                name="ハイイールドスプレッド",
                line={"color": colors.series_colors[1], "width": 2},
                hovertemplate="ハイイールドスプレッド<br>%{x}<br>%{y:.2f}%<extra></extra>",
                yaxis="y2",
            )
        )
        logger.debug("High Yield Spread trace added", data_points=len(spread_data))

    # Apply layout with dual axes
    _apply_layout(
        fig,
        title="VIX vs ハイイールドスプレッド",
        yaxis1_title="VIX",
        yaxis2_title="ハイイールドスプレッド (%)",
    )

    logger.info(
        "VIX and High Yield Spread plot created",
        traces=len(list(fig.data)),
    )

    return fig


def plot_vix_and_uncertainty_index(
    df: DataFrame,
    ema_span: int = 30,
) -> go.Figure:
    """Plot VIX and Economic Policy Uncertainty Index on a dual-axis chart.

    Creates an interactive Plotly chart with VIX on the left y-axis
    and Economic Policy Uncertainty Index (with EMA smoothing) on
    the right y-axis.

    Parameters
    ----------
    df : DataFrame
        DataFrame with DatetimeIndex and columns:
        - "VIX": VIX volatility index values
        - "Uncertainty_Index": Economic Policy Uncertainty Index values
    ema_span : int, optional
        Span for Exponential Moving Average smoothing of the
        Uncertainty Index (default: 30)

    Returns
    -------
    go.Figure
        Plotly Figure object with dual-axis chart

    Raises
    ------
    ValueError
        If ema_span is not positive

    Examples
    --------
    >>> import pandas as pd
    >>> dates = pd.date_range("2024-01-01", periods=60, freq="D")
    >>> import numpy as np
    >>> df = pd.DataFrame({
    ...     "VIX": np.random.uniform(15, 25, 60),
    ...     "Uncertainty_Index": np.random.uniform(80, 150, 60),
    ... }, index=dates)
    >>> fig = plot_vix_and_uncertainty_index(df, ema_span=10)
    >>> fig.show()

    Notes
    -----
    The Economic Policy Uncertainty (EPU) Index measures uncertainty
    related to economic policy. The EMA smoothing helps reduce noise
    and highlight trends in the uncertainty data.
    """
    logger.debug(
        "Creating VIX and Uncertainty Index plot",
        data_points=len(df),
        ema_span=ema_span,
        columns=list(df.columns) if not df.empty else [],
    )

    # Validate ema_span
    if ema_span <= 0:
        logger.error("Invalid ema_span value", ema_span=ema_span)
        raise ValueError(f"ema_span must be positive, got {ema_span}")

    # Create figure
    fig = go.Figure()

    if df.empty:
        logger.warning("Empty DataFrame provided for VIX and Uncertainty Index plot")
        _apply_layout(
            fig,
            title="VIX vs 経済政策不確実性指数",
            yaxis1_title="VIX",
            yaxis2_title="不確実性指数 (EMA)",
        )
        return fig

    # Get theme colors
    colors = get_theme_colors(ChartTheme.LIGHT)

    # Extract data (handle missing columns gracefully)
    vix_col = "VIX" if "VIX" in df.columns else None
    uncertainty_col = "Uncertainty_Index" if "Uncertainty_Index" in df.columns else None

    # Add VIX trace (left y-axis)
    if vix_col:
        vix_data = df[vix_col].dropna()
        fig.add_trace(
            go.Scatter(
                x=vix_data.index,
                y=vix_data.values,
                mode="lines",
                name="VIX",
                line={"color": colors.series_colors[0], "width": 2},
                hovertemplate="VIX<br>%{x}<br>%{y:.2f}<extra></extra>",
                yaxis="y",
            )
        )
        logger.debug("VIX trace added", data_points=len(vix_data))

    # Add Uncertainty Index trace with EMA (right y-axis)
    if uncertainty_col:
        uncertainty_data = df[uncertainty_col].dropna()
        # Apply EMA smoothing
        uncertainty_ema = uncertainty_data.ewm(span=ema_span, adjust=False).mean()
        fig.add_trace(
            go.Scatter(
                x=uncertainty_ema.index,
                y=uncertainty_ema.values,
                mode="lines",
                name=f"不確実性指数 (EMA{ema_span})",
                line={"color": colors.series_colors[1], "width": 2},
                hovertemplate=f"不確実性指数 (EMA{ema_span})<br>%{{x}}<br>%{{y:.2f}}<extra></extra>",
                yaxis="y2",
            )
        )
        logger.debug(
            "Uncertainty Index trace added",
            data_points=len(uncertainty_ema),
            ema_span=ema_span,
        )

    # Apply layout with dual axes
    _apply_layout(
        fig,
        title="VIX vs 経済政策不確実性指数",
        yaxis1_title="VIX",
        yaxis2_title="不確実性指数 (EMA)",
    )

    logger.info(
        "VIX and Uncertainty Index plot created",
        traces=len(list(fig.data)),
        ema_span=ema_span,
    )

    return fig


def _apply_layout(
    fig: go.Figure,
    title: str,
    yaxis1_title: str,
    yaxis2_title: str,
) -> None:
    """Apply common layout settings for dual-axis volatility charts.

    Parameters
    ----------
    fig : go.Figure
        Plotly figure to update
    title : str
        Chart title
    yaxis1_title : str
        Title for the left y-axis
    yaxis2_title : str
        Title for the right y-axis
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
                "text": yaxis1_title,
                "font": {
                    "family": JAPANESE_FONT_STACK,
                    "color": colors.series_colors[0],
                },
            },
            "gridcolor": colors.grid,
            "linecolor": colors.axis,
            "showgrid": True,
            "tickfont": {
                "family": JAPANESE_FONT_STACK,
                "color": colors.series_colors[0],
            },
        },
        yaxis2={
            "title": {
                "text": yaxis2_title,
                "font": {
                    "family": JAPANESE_FONT_STACK,
                    "color": colors.series_colors[1],
                },
            },
            "gridcolor": colors.grid,
            "linecolor": colors.axis,
            "showgrid": False,
            "overlaying": "y",
            "side": "right",
            "tickfont": {
                "family": JAPANESE_FONT_STACK,
                "color": colors.series_colors[1],
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
        margin={"l": 60, "r": 60, "t": 80, "b": 60},
        hovermode="x unified",
    )


# =============================================================================
# __all__ Export
# =============================================================================

__all__ = [
    "plot_vix_and_high_yield_spread",
    "plot_vix_and_uncertainty_index",
]

"""Currency and metals visualization module for financial data.

This module provides tools for visualizing currency and precious metals data,
including Dollar Index vs metals cumulative returns on dual-axis Plotly charts.

Examples
--------
>>> from analyze.visualization.currency import plot_dollar_index_and_metals
>>> import pandas as pd

>>> # Plot Dollar Index and metals cumulative returns
>>> df = pd.DataFrame({
...     "DX-Y.NYB": [1.0, 1.5, 2.0],
...     "GC=F": [3.0, 3.5, 4.0],
...     "SI=F": [5.0, 6.0, 7.0],
... }, index=pd.date_range("2024-01-01", periods=3))
>>> fig = plot_dollar_index_and_metals(df)
>>> fig.show()
"""

import plotly.graph_objects as go
from pandas import DataFrame

from utils_core.logging import get_logger

from .charts import JAPANESE_FONT_STACK, ChartTheme, get_theme_colors

logger = get_logger(__name__)

# Column name to display name mapping
COLUMN_DISPLAY_NAMES: dict[str, str] = {
    "DX-Y.NYB": "ドル指数",
    "GC=F": "金",
    "SI=F": "銀",
}


def plot_dollar_index_and_metals(df_cum_return: DataFrame) -> go.Figure:
    """Plot Dollar Index and metals cumulative returns on a dual-axis chart.

    Creates an interactive Plotly chart with Dollar Index cumulative returns
    on the left y-axis and precious metals (Gold, Silver) cumulative returns
    on the right y-axis, allowing comparison of currency strength and
    commodity price movements.

    Parameters
    ----------
    df_cum_return : DataFrame
        DataFrame with DatetimeIndex and cumulative return columns:
        - "DX-Y.NYB": Dollar Index cumulative return (percentage)
        - "GC=F": Gold cumulative return (percentage)
        - "SI=F": Silver cumulative return (percentage)

        Any of these columns may be absent; the function handles
        partial data gracefully.

    Returns
    -------
    go.Figure
        Plotly Figure object with dual-axis chart

    Examples
    --------
    >>> import pandas as pd
    >>> import numpy as np
    >>> dates = pd.date_range("2024-01-01", periods=30, freq="D")
    >>> df = pd.DataFrame({
    ...     "DX-Y.NYB": np.cumsum(np.random.randn(30) * 0.3),
    ...     "GC=F": np.cumsum(np.random.randn(30) * 0.5),
    ...     "SI=F": np.cumsum(np.random.randn(30) * 0.8),
    ... }, index=dates)
    >>> fig = plot_dollar_index_and_metals(df)
    >>> fig.show()

    Notes
    -----
    The Dollar Index (DXY) is often inversely correlated with precious metals.
    This chart helps visualize this relationship by plotting them together
    on separate axes.

    Gold and Silver typically move in the same direction but with different
    volatilities. Silver tends to be more volatile than gold.
    """
    logger.debug(
        "Creating Dollar Index and metals plot",
        data_points=len(df_cum_return),
        columns=list(df_cum_return.columns) if not df_cum_return.empty else [],
    )

    # Create figure
    fig = go.Figure()

    if df_cum_return.empty:
        logger.warning("Empty DataFrame provided for Dollar Index and metals plot")
        _apply_layout(
            fig,
            title="ドル指数 vs 金属価格（累積リターン）",
            yaxis1_title="ドル指数 (%)",
            yaxis2_title="金属価格 (%)",
        )
        return fig

    # Get theme colors
    colors = get_theme_colors(ChartTheme.LIGHT)

    # Define which columns go to which axis
    dollar_col = "DX-Y.NYB"
    metals_cols = ["GC=F", "SI=F"]

    # Track which axes have data
    has_dollar_data = False
    has_metals_data = False

    # Add Dollar Index trace (left y-axis)
    if dollar_col in df_cum_return.columns:
        dollar_data = df_cum_return[dollar_col].dropna()
        if not dollar_data.empty:
            fig.add_trace(
                go.Scatter(
                    x=dollar_data.index,
                    y=dollar_data.values,
                    mode="lines",
                    name=COLUMN_DISPLAY_NAMES[dollar_col],
                    line={"color": colors.series_colors[0], "width": 2},
                    hovertemplate=(
                        f"{COLUMN_DISPLAY_NAMES[dollar_col]}<br>"
                        "%{x}<br>%{y:+.2f}%<extra></extra>"
                    ),
                    yaxis="y",
                )
            )
            has_dollar_data = True
            logger.debug("Dollar Index trace added", data_points=len(dollar_data))

    # Add metals traces (right y-axis)
    metals_color_index = 1  # Start after the dollar color
    for col in metals_cols:
        if col in df_cum_return.columns:
            metal_data = df_cum_return[col].dropna()
            if not metal_data.empty:
                fig.add_trace(
                    go.Scatter(
                        x=metal_data.index,
                        y=metal_data.values,
                        mode="lines",
                        name=COLUMN_DISPLAY_NAMES[col],
                        line={
                            "color": colors.series_colors[metals_color_index],
                            "width": 2,
                        },
                        hovertemplate=(
                            f"{COLUMN_DISPLAY_NAMES[col]}<br>"
                            "%{x}<br>%{y:+.2f}%<extra></extra>"
                        ),
                        yaxis="y2",
                    )
                )
                has_metals_data = True
                logger.debug(
                    f"{COLUMN_DISPLAY_NAMES[col]} trace added",
                    data_points=len(metal_data),
                )
                metals_color_index += 1

    # Apply layout with dual axes
    _apply_layout(
        fig,
        title="ドル指数 vs 金属価格（累積リターン）",
        yaxis1_title="ドル指数 (%)",
        yaxis2_title="金属価格 (%)",
    )

    logger.info(
        "Dollar Index and metals plot created",
        traces=len(list(fig.data)),
        has_dollar_data=has_dollar_data,
        has_metals_data=has_metals_data,
    )

    return fig


def _apply_layout(
    fig: go.Figure,
    title: str,
    yaxis1_title: str,
    yaxis2_title: str,
) -> None:
    """Apply common layout settings for dual-axis currency charts.

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
            "tickformat": "+.1f",
            "ticksuffix": "%",
            "zeroline": True,
            "zerolinecolor": colors.axis,
            "zerolinewidth": 1,
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
            "tickformat": "+.1f",
            "ticksuffix": "%",
            "zeroline": True,
            "zerolinecolor": colors.axis,
            "zerolinewidth": 1,
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
    "plot_dollar_index_and_metals",
]

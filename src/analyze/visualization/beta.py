"""Beta visualization module for financial data.

This module provides tools for visualizing rolling beta coefficients,
showing how individual securities' sensitivity to market movements
changes over time using Plotly charts.

Examples
--------
>>> from analyze.visualization.beta import plot_rolling_beta
>>> import pandas as pd
>>> import numpy as np

>>> # Plot rolling beta for multiple tickers against an index
>>> dates = pd.date_range("2024-01-01", periods=100, freq="D")
>>> df_beta = pd.DataFrame({
...     "AAPL": np.random.uniform(0.8, 1.5, 100),
...     "MSFT": np.random.uniform(0.7, 1.3, 100),
... }, index=dates)
>>> fig = plot_rolling_beta(df_beta, tickers=["AAPL", "MSFT"], target_index="S&P 500")
>>> fig.show()
"""

import pandas as pd
import plotly.graph_objects as go
from pandas import DataFrame

from utils_core.logging import get_logger

from .charts import JAPANESE_FONT_STACK, ChartTheme, get_theme_colors

logger = get_logger(__name__)


def plot_rolling_beta(
    df_beta: DataFrame,
    tickers: list[str],
    target_index: str,
    *,
    window: int | None = None,
    title: str | None = None,
) -> go.Figure:
    """Plot rolling beta coefficient over time for multiple tickers.

    Creates an interactive Plotly chart showing the rolling beta
    coefficients for specified tickers against a target index over time.
    A horizontal reference line at beta=1 is included for comparison.

    Parameters
    ----------
    df_beta : DataFrame
        DataFrame with DatetimeIndex containing rolling beta values.
        Each column represents a ticker's beta with the target index.
    tickers : list[str]
        List of ticker symbols to plot. Only tickers present in df_beta
        will be plotted; invalid tickers are silently ignored.
    target_index : str
        Name of the target index for chart labeling (e.g., "S&P 500").
    window : int | None, optional
        Rolling window size used to calculate beta. If provided, it will
        be included in the chart title for reference. Default: None.
    title : str | None, optional
        Custom chart title. If None, a default title will be generated
        based on the target_index parameter. Default: None.

    Returns
    -------
    go.Figure
        Plotly Figure object with the rolling beta chart.

    Examples
    --------
    >>> import pandas as pd
    >>> import numpy as np
    >>> dates = pd.date_range("2024-01-01", periods=100, freq="D")
    >>> df_beta = pd.DataFrame({
    ...     "AAPL": np.random.uniform(0.8, 1.5, 100),
    ...     "MSFT": np.random.uniform(0.7, 1.3, 100),
    ... }, index=dates)
    >>> fig = plot_rolling_beta(df_beta, tickers=["AAPL"], target_index="S&P 500")
    >>> fig.show()

    >>> # Plot multiple tickers with custom title
    >>> fig = plot_rolling_beta(
    ...     df_beta,
    ...     tickers=["AAPL", "MSFT"],
    ...     target_index="S&P 500",
    ...     window=60,
    ...     title="MAG7 Rolling Beta",
    ... )
    >>> fig.show()

    Notes
    -----
    Beta measures the sensitivity of an asset's returns to benchmark returns:
    - Beta > 1: Higher volatility than the benchmark
    - Beta = 1: Same volatility as the benchmark
    - Beta < 1: Lower volatility than the benchmark
    - Beta < 0: Negative correlation with the benchmark (rare)

    A horizontal line at y=1 is displayed as a reference.
    """
    logger.debug(
        "Creating rolling beta plot",
        tickers=tickers,
        target_index=target_index,
        window=window,
        data_points=len(df_beta),
        columns=list(df_beta.columns) if not df_beta.empty else [],
    )

    # Create figure
    fig = go.Figure()

    # Generate title
    chart_title = title
    if chart_title is None:
        if window is not None:
            chart_title = f"ローリングベータ vs {target_index} ({window}日)"
        else:
            chart_title = f"ローリングベータ vs {target_index}"

    if df_beta.empty:
        logger.warning("Empty DataFrame provided for rolling beta plot")
        _apply_layout(
            fig,
            title=chart_title,
            yaxis_title="ベータ",
        )
        return fig

    if not tickers:
        logger.warning("Empty tickers list provided for rolling beta plot")
        _apply_layout(
            fig,
            title=chart_title,
            yaxis_title="ベータ",
        )
        return fig

    # Get theme colors
    colors = get_theme_colors(ChartTheme.LIGHT)

    # Filter valid tickers (those present in the DataFrame)
    valid_tickers = [t for t in tickers if t in df_beta.columns]

    if not valid_tickers:
        logger.warning(
            "No valid tickers found in DataFrame",
            requested_tickers=tickers,
            available_columns=list(df_beta.columns),
        )
        _apply_layout(
            fig,
            title=chart_title,
            yaxis_title="ベータ",
        )
        return fig

    # Add trace for each valid ticker
    all_indices: list[pd.DatetimeIndex] = []
    for i, ticker in enumerate(valid_tickers):
        beta_data = df_beta[ticker].dropna()

        if beta_data.empty:
            logger.warning("No valid beta data for ticker", ticker=ticker)
            continue

        # Collect index for min/max calculation
        all_indices.append(beta_data.index)  # type: ignore[arg-type]

        # Get color from theme series colors (cycle if more tickers than colors)
        color = colors.series_colors[i % len(colors.series_colors)]

        fig.add_trace(
            go.Scatter(
                x=beta_data.index,
                y=beta_data.values,
                mode="lines",
                name=f"{ticker} ベータ",
                line={"color": color, "width": 2},
                hovertemplate=(
                    f"{ticker}<br>%{{x|%Y-%m-%d}}<br>ベータ: %{{y:.3f}}<extra></extra>"
                ),
            )
        )

        logger.debug(
            "Beta trace added",
            ticker=ticker,
            data_points=len(beta_data),
            color=color,
        )

    # Apply layout
    _apply_layout(
        fig,
        title=chart_title,
        yaxis_title="ベータ",
    )

    # Add horizontal line at beta=1 for reference (if we have data)
    if all_indices:
        combined_index = all_indices[0]
        for idx in all_indices[1:]:
            combined_index = combined_index.union(idx)
        min_date = combined_index.min()
        max_date = combined_index.max()
        fig.add_shape(
            type="line",
            x0=min_date,
            x1=max_date,
            y0=1,
            y1=1,
            line={
                "color": colors.grid,
                "width": 1,
                "dash": "dash",
            },
        )
        logger.debug("Beta=1 reference line added")

    logger.info(
        "Rolling beta plot created",
        tickers=valid_tickers,
        target_index=target_index,
        traces=len(list(fig.data)),
        window=window,
    )

    return fig


def _apply_layout(
    fig: go.Figure,
    title: str,
    yaxis_title: str,
) -> None:
    """Apply common layout settings for beta charts.

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
    "plot_rolling_beta",
]

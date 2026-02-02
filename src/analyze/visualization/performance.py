"""Performance visualization module for financial data.

This module provides tools for visualizing financial performance data,
including DataFrame styling with color-coded returns and cumulative
return plots using Plotly.

Examples
--------
>>> from analyze.visualization.performance import apply_df_style, plot_cumulative_returns
>>> import pandas as pd

>>> # Style a returns DataFrame
>>> returns_df = pd.DataFrame({"1D": [1.5, -0.8], "1W": [3.2, -1.5]}, index=["AAPL", "MSFT"])
>>> styled = apply_df_style(returns_df)

>>> # Plot cumulative returns
>>> price_df = pd.DataFrame({"AAPL": [150, 152, 154], "MSFT": [350, 352, 355]})
>>> fig = plot_cumulative_returns(price_df, ["AAPL", "MSFT"], "Cumulative Returns")
>>> fig.show()
"""

import pandas as pd
import plotly.graph_objects as go
from pandas import DataFrame
from pandas.io.formats.style import Styler

from utils_core.logging import get_logger

from .charts import JAPANESE_FONT_STACK, ChartTheme, get_theme_colors

logger = get_logger(__name__)


def apply_df_style(df: DataFrame) -> Styler:
    """Apply styling to a DataFrame with color-coded values and bars.

    Applies visual styling to a numeric DataFrame for better readability:
    - Positive values are colored green
    - Negative values are colored red
    - Background gradient bars show magnitude
    - Numbers are formatted with sign and percentage

    Parameters
    ----------
    df : DataFrame
        DataFrame with numeric values to style. Typically contains
        return percentages with period columns (1D, 1W, 1M, YTD, etc.)

    Returns
    -------
    Styler
        Styled DataFrame object that can be displayed in Jupyter
        or exported to HTML

    Examples
    --------
    >>> returns_df = pd.DataFrame({
    ...     "1D": [1.5, -0.8, 2.3],
    ...     "1W": [3.2, -1.5, 4.8],
    ... }, index=["AAPL", "MSFT", "GOOGL"])
    >>> styled = apply_df_style(returns_df)
    >>> styled.to_html()  # Export to HTML
    """
    logger.debug(
        "Applying DataFrame style",
        shape=df.shape,
        columns=list(df.columns) if not df.empty else [],
    )

    if df.empty:
        logger.warning("Empty DataFrame provided for styling")
        return df.style

    # Get theme colors for consistent styling
    colors = get_theme_colors(ChartTheme.LIGHT)

    def _color_values(val: float | int) -> str:
        """Apply text color based on value sign.

        Parameters
        ----------
        val : float | int
            Numeric value to color

        Returns
        -------
        str
            CSS color style string
        """
        if pd.isna(val):
            return ""
        if val > 0:
            return f"color: {colors.positive}"
        elif val < 0:
            return f"color: {colors.negative}"
        return ""

    def _background_gradient(
        series: pd.Series,
        cmap_positive: str = "Greens",
        cmap_negative: str = "Reds",
    ) -> list[str]:
        """Apply background gradient based on value magnitude.

        Parameters
        ----------
        series : pd.Series
            Series of values to style
        cmap_positive : str
            Colormap name for positive values
        cmap_negative : str
            Colormap name for negative values

        Returns
        -------
        list[str]
            List of CSS background-color styles
        """
        styles = []
        for val in series:
            if pd.isna(val):
                styles.append("")
                continue

            # Calculate intensity (0-100 scale, capped at 50%)
            intensity = min(abs(float(val)) * 2, 100)
            alpha = intensity / 100 * 0.3  # Max 30% opacity

            if val > 0:
                # Green with alpha
                styles.append(f"background-color: rgba(76, 175, 80, {alpha})")
            elif val < 0:
                # Red with alpha
                styles.append(f"background-color: rgba(244, 67, 54, {alpha})")
            else:
                styles.append("")

        return styles

    # Select only numeric columns
    numeric_df = df.select_dtypes(include=["number"])

    if numeric_df.empty:
        logger.warning("No numeric columns found for styling")
        return df.style

    # Apply styling
    styler: Styler = (
        numeric_df.style.map(_color_values)
        .apply(_background_gradient, axis=0)
        .format("{:+.2f}%")
    )  # type: ignore[assignment]

    logger.info(
        "DataFrame style applied",
        rows=len(df),
        columns=len(numeric_df.columns),
    )

    return styler


def plot_cumulative_returns(
    price_df: DataFrame,
    symbols: list[str],
    title: str,
) -> go.Figure:
    """Plot cumulative returns for multiple symbols.

    Creates an interactive Plotly line chart showing the cumulative
    percentage returns for the specified symbols, starting from 0%.

    Parameters
    ----------
    price_df : DataFrame
        DataFrame with price data. Index should be DatetimeIndex,
        columns should be symbol names containing price values.
    symbols : list[str]
        List of symbol names to plot. Must be present as columns
        in price_df. Invalid symbols are silently ignored.
    title : str
        Chart title to display

    Returns
    -------
    go.Figure
        Plotly Figure object with cumulative return traces

    Examples
    --------
    >>> import pandas as pd
    >>> dates = pd.date_range("2024-01-01", periods=5, freq="D")
    >>> price_df = pd.DataFrame({
    ...     "AAPL": [150, 152, 151, 154, 156],
    ...     "MSFT": [350, 348, 352, 355, 354],
    ... }, index=dates)
    >>> fig = plot_cumulative_returns(price_df, ["AAPL", "MSFT"], "Performance")
    >>> fig.show()

    Notes
    -----
    Cumulative returns are calculated as:
        (current_price / first_price - 1) * 100

    The first data point is always 0% (the baseline).
    """
    logger.debug(
        "Creating cumulative returns plot",
        symbols=symbols,
        title=title,
        data_points=len(price_df),
    )

    # Create figure
    fig = go.Figure()

    if price_df.empty or not symbols:
        logger.warning("Empty price data or no symbols provided")
        fig.update_layout(
            title=title,
            font={"family": JAPANESE_FONT_STACK},
        )
        return fig

    # Get theme colors
    colors = get_theme_colors(ChartTheme.LIGHT)
    series_colors = colors.series_colors

    # Add trace for each valid symbol
    valid_symbols_count = 0
    for i, symbol in enumerate(symbols):
        if symbol not in price_df.columns:
            logger.warning(
                "Symbol not found in price data",
                symbol=symbol,
                available_columns=list(price_df.columns),
            )
            continue

        # Get price series
        prices = price_df[symbol].dropna()

        if prices.empty:
            logger.warning("No valid prices for symbol", symbol=symbol)
            continue

        # Calculate cumulative returns (percentage)
        first_price = prices.iloc[0]
        if first_price == 0:
            logger.warning("First price is zero, skipping symbol", symbol=symbol)
            continue

        cumulative_returns = (prices / first_price - 1) * 100

        # Add trace
        color = series_colors[i % len(series_colors)]
        fig.add_trace(
            go.Scatter(
                x=cumulative_returns.index,
                y=cumulative_returns.values,
                mode="lines",
                name=symbol,
                line={"color": color, "width": 2},
                hovertemplate=f"{symbol}<br>%{{x}}<br>%{{y:.2f}}%<extra></extra>",
            )
        )
        valid_symbols_count += 1

    # Configure layout
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
            "title": "Cumulative Return (%)",
            "gridcolor": colors.grid,
            "linecolor": colors.axis,
            "showgrid": True,
            "tickformat": "+.1f",
            "ticksuffix": "%",
            "zeroline": True,
            "zerolinecolor": colors.axis,
            "zerolinewidth": 1,
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

    logger.info(
        "Cumulative returns plot created",
        title=title,
        symbols_plotted=valid_symbols_count,
        total_symbols=len(symbols),
    )

    return fig


# =============================================================================
# __all__ Export
# =============================================================================

__all__ = [
    "apply_df_style",
    "plot_cumulative_returns",
]

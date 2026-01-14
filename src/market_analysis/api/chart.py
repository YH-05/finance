"""Chart API for market data visualization.

This module provides a simplified interface for creating financial charts,
wrapping the lower-level visualization components.

Examples
--------
>>> from market_analysis import Chart
>>> chart = Chart(stock_df, title="AAPL Price Chart")
>>> fig = chart.price_chart(overlays=["SMA_20", "EMA_50"])
>>> chart.save("chart.png")

>>> corr_matrix = Analysis.correlation([stock1_df, stock2_df])
>>> fig = Chart.correlation_heatmap(corr_matrix, title="Correlation Matrix")
"""

from logging import Logger
from pathlib import Path
from typing import Literal

import pandas as pd
import plotly.graph_objects as go

from ..utils.logger_factory import create_logger
from ..visualization.charts import ChartConfig, ChartTheme
from ..visualization.heatmap import HeatmapChart
from ..visualization.price_charts import LineChart, PriceChartData

logger: Logger = create_logger(__name__, module="api")


class Chart:
    """Chart generation class for market data visualization.

    This class provides a simplified interface for creating financial charts
    including price charts with indicator overlays and correlation heatmaps.
    Uses plotly for interactive charts with marimo notebook support.

    Parameters
    ----------
    data : pd.DataFrame
        Market data DataFrame with OHLCV columns (Open, High, Low, Close, Volume).
        Index should be DatetimeIndex.
    title : str | None, default=None
        Chart title to display

    Attributes
    ----------
    data : pd.DataFrame
        The market data used for charting
    title : str | None
        The chart title

    Examples
    --------
    >>> import pandas as pd
    >>> from market_analysis import Chart
    >>>
    >>> # Create price chart
    >>> chart = Chart(stock_df, title="AAPL Price Chart")
    >>> fig = chart.price_chart(overlays=["SMA_20", "EMA_50"])
    >>> chart.save("chart.png")
    >>>
    >>> # Create correlation heatmap (static method)
    >>> corr_matrix = stock_df[["AAPL", "GOOGL", "MSFT"]].corr()
    >>> fig = Chart.correlation_heatmap(corr_matrix)
    """

    def __init__(
        self,
        data: pd.DataFrame,
        title: str | None = None,
    ) -> None:
        """Initialize Chart with data and optional title.

        Parameters
        ----------
        data : pd.DataFrame
            Market data DataFrame with OHLCV columns.
            Required columns: Open, High, Low, Close
            Optional columns: Volume
            Index should be DatetimeIndex.
        title : str | None, default=None
            Chart title to display

        Raises
        ------
        ValueError
            If required columns (Open, High, Low, Close) are missing
        """
        self._data = data
        self._title = title
        self._figure: go.Figure | None = None

        # Validate required columns for price charts
        required_cols = {"Open", "High", "Low", "Close"}
        missing = required_cols - set(data.columns)
        if missing:
            logger.warning(
                "Missing OHLC columns for full price chart support",
                missing_columns=list(missing),
            )

        logger.debug(
            "Chart initialized",
            title=title,
            data_points=len(data),
            columns=list(data.columns),
        )

    @property
    def data(self) -> pd.DataFrame:
        """Get the chart data.

        Returns
        -------
        pd.DataFrame
            The market data DataFrame
        """
        return self._data

    @property
    def title(self) -> str | None:
        """Get the chart title.

        Returns
        -------
        str | None
            The chart title
        """
        return self._title

    def price_chart(
        self,
        column: str = "Close",
        overlays: list[str] | None = None,
        width: int = 1200,
        height: int = 600,
    ) -> go.Figure:
        """Generate a price chart with optional indicator overlays.

        Creates a line chart of the specified price column with optional
        technical indicator overlays (e.g., moving averages).

        Parameters
        ----------
        column : str, default="Close"
            Column to use for the price line
        overlays : list[str] | None, default=None
            List of indicator columns to overlay on the chart.
            Supports patterns like "SMA_20", "EMA_50" which will be
            calculated if not present in the data.
        width : int, default=1200
            Chart width in pixels
        height : int, default=600
            Chart height in pixels

        Returns
        -------
        go.Figure
            Plotly Figure object for interactive display

        Raises
        ------
        ValueError
            If the specified column does not exist in the data

        Examples
        --------
        >>> chart = Chart(stock_df, title="AAPL")
        >>> fig = chart.price_chart()  # Simple close price chart
        >>> fig = chart.price_chart(overlays=["SMA_20", "EMA_50"])  # With overlays
        >>> chart.save("chart.png")
        """
        if column not in self._data.columns:
            raise ValueError(
                f"Column '{column}' not found in data. "
                f"Available columns: {list(self._data.columns)}"
            )

        logger.info(
            "Creating price chart",
            column=column,
            overlays=overlays,
            width=width,
            height=height,
        )

        # Create config
        config = ChartConfig(
            width=width,
            height=height,
            title=self._title,
            theme=ChartTheme.LIGHT,
        )

        # Create price chart data
        price_data = PriceChartData(
            df=self._data,
            symbol=self._title or "",
        )

        # Build chart
        chart_builder = LineChart(
            data=price_data,
            config=config,
            show_volume="Volume" in self._data.columns,
            price_column=column,
        )

        # Add overlay indicators
        if overlays:
            for overlay in overlays:
                self._add_overlay(chart_builder, overlay)

        chart_builder.build()
        self._figure = chart_builder.figure

        logger.info(
            "Price chart created",
            title=self._title,
            data_points=len(self._data),
        )

        return self._figure  # type: ignore[return-value]

    def _add_overlay(self, chart_builder: LineChart, overlay: str) -> None:
        """Add an indicator overlay to the chart builder.

        Parameters
        ----------
        chart_builder : LineChart
            The chart builder to add the overlay to
        overlay : str
            Overlay specification (e.g., "SMA_20", "EMA_50")
        """
        parts = overlay.upper().split("_")
        if len(parts) != 2:
            logger.warning(
                "Invalid overlay format, expected 'INDICATOR_PERIOD'",
                overlay=overlay,
            )
            return

        indicator_type = parts[0]
        try:
            period = int(parts[1])
        except ValueError:
            logger.warning(
                "Invalid period in overlay specification",
                overlay=overlay,
            )
            return

        if indicator_type == "SMA":
            chart_builder.add_sma(window=period, name=overlay)
        elif indicator_type == "EMA":
            chart_builder.add_ema(window=period, name=overlay)
        elif indicator_type == "BB":
            chart_builder.add_bollinger_bands(window=period, name=overlay)
        else:
            logger.warning(
                "Unsupported indicator type",
                indicator_type=indicator_type,
                overlay=overlay,
            )

    @staticmethod
    def correlation_heatmap(
        correlation_matrix: pd.DataFrame,
        title: str = "Correlation Matrix",
        width: int = 800,
        height: int = 800,
    ) -> go.Figure:
        """Generate a correlation heatmap.

        Creates a heatmap visualization of a correlation matrix with
        values annotated in each cell.

        Parameters
        ----------
        correlation_matrix : pd.DataFrame
            Correlation matrix (typically from pd.DataFrame.corr())
        title : str, default="Correlation Matrix"
            Chart title
        width : int, default=800
            Chart width in pixels
        height : int, default=800
            Chart height in pixels

        Returns
        -------
        go.Figure
            Plotly Figure object for interactive display

        Raises
        ------
        ValueError
            If the correlation matrix is empty

        Examples
        --------
        >>> corr_matrix = prices_df.corr()
        >>> fig = Chart.correlation_heatmap(corr_matrix, title="Asset Correlations")
        >>> fig.write_html("heatmap.html")
        """
        if correlation_matrix.empty:
            raise ValueError("Correlation matrix is empty")

        logger.info(
            "Creating correlation heatmap",
            title=title,
            symbols=list(correlation_matrix.columns),
            width=width,
            height=height,
        )

        # Create config
        config = ChartConfig(
            width=width,
            height=height,
            title=title,
            theme=ChartTheme.LIGHT,
        )

        # Build heatmap
        heatmap_builder = HeatmapChart(
            correlation_matrix=correlation_matrix,
            config=config,
            show_values=True,
        )
        heatmap_builder.build()

        logger.info(
            "Correlation heatmap created",
            title=title,
            symbols_count=len(correlation_matrix.columns),
        )

        return heatmap_builder.figure  # type: ignore[return-value]

    def save(
        self,
        path: str | Path,
        format: Literal["png", "svg", "html"] | None = None,
        scale: int = 2,
    ) -> None:
        """Save the chart to a file.

        Parameters
        ----------
        path : str | Path
            Output file path
        format : {"png", "svg", "html"} | None, default=None
            Export format. If None, inferred from file extension.
        scale : int, default=2
            Resolution scale for PNG format (higher = better quality)

        Raises
        ------
        RuntimeError
            If no chart has been generated yet (call price_chart first)
        ValueError
            If the format is not supported

        Examples
        --------
        >>> chart = Chart(stock_df, title="AAPL")
        >>> chart.price_chart()
        >>> chart.save("chart.png")  # PNG format
        >>> chart.save("chart.svg", format="svg")  # SVG format
        >>> chart.save("chart.html")  # Interactive HTML
        """
        if self._figure is None:
            raise RuntimeError(
                "No chart to save. Call price_chart() first to generate a chart."
            )

        path = Path(path)

        # Infer format from extension if not specified
        if format is None:
            ext = path.suffix.lower().lstrip(".")
            if ext not in ("png", "svg", "html"):
                raise ValueError(
                    f"Cannot infer format from extension '{ext}'. "
                    f"Supported formats: png, svg, html"
                )
            # ext is guaranteed to be one of the valid formats at this point
            format = ext if ext in ("png", "svg", "html") else "png"

        # Ensure parent directory exists
        path.parent.mkdir(parents=True, exist_ok=True)

        logger.info(
            "Saving chart",
            path=str(path),
            format=format,
            scale=scale if format == "png" else None,
        )

        if format == "html":
            self._figure.write_html(str(path), include_plotlyjs=True)
        elif format == "png":
            import plotly.io as pio

            pio.write_image(self._figure, str(path), format="png", scale=scale)
        elif format == "svg":
            import plotly.io as pio

            pio.write_image(self._figure, str(path), format="svg")
        else:
            raise ValueError(f"Unsupported format: {format}")

        logger.info("Chart saved successfully", path=str(path))

    def show(self) -> None:
        """Display the chart in an interactive viewer.

        Shows the chart in a browser window or Jupyter/marimo notebook.
        This method is designed to work seamlessly with marimo notebooks
        for interactive data exploration.

        Raises
        ------
        RuntimeError
            If no chart has been generated yet (call price_chart first)

        Examples
        --------
        >>> chart = Chart(stock_df, title="AAPL")
        >>> chart.price_chart(overlays=["SMA_20"])
        >>> chart.show()  # Opens in browser or notebook
        """
        if self._figure is None:
            raise RuntimeError(
                "No chart to show. Call price_chart() first to generate a chart."
            )

        logger.info("Displaying chart")
        self._figure.show()


__all__ = [
    "Chart",
]

"""Price chart implementations for financial data visualization.

This module provides chart builders for creating price charts including:
- CandlestickChart: OHLC candlestick charts with volume
- LineChart: Simple line charts for price trends

Both support technical indicator overlays and date range filtering.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from analyze.technical import TechnicalIndicators as IndicatorCalculator
from database.utils.logging_config import get_logger

from .charts import ChartBuilder, ChartConfig

logger = get_logger(__name__)


# =============================================================================
# Data Configuration
# =============================================================================


@dataclass
class PriceChartData:
    """Data configuration for price charts.

    Parameters
    ----------
    df : pd.DataFrame
        OHLCV DataFrame with columns: Open, High, Low, Close, Volume
        (case-insensitive matching supported for YFinance compatibility)
        Index should be DatetimeIndex
    symbol : str
        Symbol name for display
    start_date : datetime | str | None
        Start date for filtering (default: None, no filter)
    end_date : datetime | str | None
        End date for filtering (default: None, no filter)

    Raises
    ------
    ValueError
        If required OHLC columns are missing or date range is invalid
    """

    df: pd.DataFrame
    symbol: str = ""
    start_date: datetime | str | None = None
    end_date: datetime | str | None = None

    def __post_init__(self) -> None:
        """Validate data after initialization."""
        # Required OHLC columns (Volume is optional)
        # Support case-insensitive column matching (Issue #316: YFinance lowercase columns)
        required_cols = {"Open", "High", "Low", "Close"}
        column_mapping = self._create_column_mapping(required_cols)

        missing = required_cols - set(column_mapping.keys())
        if missing:
            raise ValueError(f"Missing required columns: {missing}")

        # Rename columns to standard format if needed
        if column_mapping:
            reverse_mapping = {v: k for k, v in column_mapping.items()}
            self.df = self.df.rename(columns=reverse_mapping)

        # Also normalize Volume column if present
        volume_mapping = self._create_column_mapping({"Volume"})
        if volume_mapping:
            reverse_volume = {v: k for k, v in volume_mapping.items()}
            self.df = self.df.rename(columns=reverse_volume)

        # Validate date range
        if self.start_date is not None and self.end_date is not None:
            start = pd.to_datetime(self.start_date)
            end = pd.to_datetime(self.end_date)
            if start > end:
                raise ValueError(
                    f"start_date ({start}) must be before end_date ({end})"
                )

        logger.debug(
            "PriceChartData validated",
            symbol=self.symbol,
            rows=len(self.df),
            columns=list(self.df.columns),
        )

    def _create_column_mapping(self, required_cols: set[str]) -> dict[str, str]:
        """Create mapping from standard column names to actual column names.

        Performs case-insensitive matching to support YFinance lowercase columns.

        Parameters
        ----------
        required_cols : set[str]
            Set of required column names (standard format)

        Returns
        -------
        dict[str, str]
            Mapping from standard name to actual column name in DataFrame
        """
        mapping: dict[str, str] = {}
        actual_cols_lower = {col.lower(): col for col in self.df.columns}

        for required_col in required_cols:
            # Exact match first
            if required_col in self.df.columns:
                mapping[required_col] = required_col
            # Case-insensitive match
            elif required_col.lower() in actual_cols_lower:
                actual_col = actual_cols_lower[required_col.lower()]
                mapping[required_col] = actual_col
                logger.debug(
                    "Column name resolved case-insensitively",
                    requested=required_col,
                    resolved=actual_col,
                )

        return mapping

    def get_filtered_data(self) -> pd.DataFrame:
        """Get data filtered by date range.

        Returns
        -------
        pd.DataFrame
            Filtered DataFrame
        """
        data = self.df.copy()

        if self.start_date is not None:
            start = pd.to_datetime(self.start_date)
            data = data.loc[data.index >= start]

        if self.end_date is not None:
            end = pd.to_datetime(self.end_date)
            data = data.loc[data.index <= end]

        return data


@dataclass
class IndicatorOverlay:
    """Configuration for a single indicator overlay.

    Parameters
    ----------
    indicator_type : str
        Type of indicator: "sma", "ema", "bollinger"
    params : dict[str, Any]
        Parameters for the indicator (e.g., {"window": 20})
    color : str | None
        Custom color for the indicator (default: auto)
    name : str | None
        Custom name for legend (default: auto-generated)
    """

    indicator_type: str
    params: dict[str, Any] = field(default_factory=dict)
    color: str | None = None
    name: str | None = None


# =============================================================================
# Base Price Chart Builder
# =============================================================================


class PriceChartBuilder(ChartBuilder):
    """Base class for price chart builders.

    Provides common functionality for price charts including:
    - Technical indicator overlays
    - Volume subplot
    - Date range filtering
    """

    def __init__(
        self,
        data: PriceChartData,
        config: ChartConfig | None = None,
        *,
        show_volume: bool = True,
    ) -> None:
        """Initialize PriceChartBuilder.

        Parameters
        ----------
        data : PriceChartData
            Price data configuration
        config : ChartConfig | None
            Chart configuration
        show_volume : bool, default=True
            Whether to show volume subplot
        """
        super().__init__(config)
        self._data = data
        self._show_volume = show_volume
        self._indicators: list[IndicatorOverlay] = []
        self._indicator_color_idx = 0

        logger.debug(
            "PriceChartBuilder initialized",
            symbol=data.symbol,
            show_volume=show_volume,
            data_points=len(data.df),
        )

    def add_sma(
        self,
        window: int = 20,
        color: str | None = None,
        name: str | None = None,
    ) -> "PriceChartBuilder":
        """Add Simple Moving Average overlay.

        Parameters
        ----------
        window : int, default=20
            SMA window period
        color : str | None
            Custom color (default: auto from theme)
        name : str | None
            Custom legend name (default: "SMA {window}")

        Returns
        -------
        PriceChartBuilder
            Self for method chaining

        Examples
        --------
        >>> chart = CandlestickChart(data)
        >>> chart.add_sma(20).add_sma(50, color="#FF0000").build()
        """
        self._indicators.append(
            IndicatorOverlay(
                indicator_type="sma",
                params={"window": window},
                color=color,
                name=name or f"SMA {window}",
            )
        )
        logger.debug("Added SMA overlay", window=window)
        return self

    def add_ema(
        self,
        window: int = 12,
        color: str | None = None,
        name: str | None = None,
    ) -> "PriceChartBuilder":
        """Add Exponential Moving Average overlay.

        Parameters
        ----------
        window : int, default=12
            EMA window period
        color : str | None
            Custom color (default: auto from theme)
        name : str | None
            Custom legend name (default: "EMA {window}")

        Returns
        -------
        PriceChartBuilder
            Self for method chaining

        Examples
        --------
        >>> chart = CandlestickChart(data)
        >>> chart.add_ema(12).add_ema(26).build()
        """
        self._indicators.append(
            IndicatorOverlay(
                indicator_type="ema",
                params={"window": window},
                color=color,
                name=name or f"EMA {window}",
            )
        )
        logger.debug("Added EMA overlay", window=window)
        return self

    def add_bollinger_bands(
        self,
        window: int = 20,
        num_std: float = 2.0,
        color: str | None = None,
        name: str | None = None,
    ) -> "PriceChartBuilder":
        """Add Bollinger Bands overlay.

        Parameters
        ----------
        window : int, default=20
            Window period for the moving average
        num_std : float, default=2.0
            Number of standard deviations
        color : str | None
            Custom color for bands (default: auto from theme)
        name : str | None
            Custom legend name prefix (default: "BB")

        Returns
        -------
        PriceChartBuilder
            Self for method chaining

        Examples
        --------
        >>> chart = CandlestickChart(data)
        >>> chart.add_bollinger_bands(20, 2.0).build()
        """
        self._indicators.append(
            IndicatorOverlay(
                indicator_type="bollinger",
                params={"window": window, "num_std": num_std},
                color=color,
                name=name or "BB",
            )
        )
        logger.debug("Added Bollinger Bands overlay", window=window, num_std=num_std)
        return self

    def _get_next_indicator_color(self) -> str:
        """Get next color from theme series colors.

        Returns
        -------
        str
            Color hex code
        """
        colors = self._colors.series_colors
        color = colors[self._indicator_color_idx % len(colors)]
        self._indicator_color_idx += 1
        return color

    def _add_indicator_traces(self, df: pd.DataFrame) -> None:
        """Add indicator traces to the figure.

        Parameters
        ----------
        df : pd.DataFrame
            Price data with DatetimeIndex
        """
        if self._figure is None:
            return

        close_prices: pd.Series = df["Close"]  # type: ignore[assignment]

        for overlay in self._indicators:
            color = overlay.color or self._get_next_indicator_color()

            if overlay.indicator_type == "sma":
                self._add_sma_trace(df.index, close_prices, overlay, color)
            elif overlay.indicator_type == "ema":
                self._add_ema_trace(df.index, close_prices, overlay, color)
            elif overlay.indicator_type == "bollinger":
                self._add_bollinger_traces(df.index, close_prices, overlay, color)

        logger.debug(
            "Indicator traces added",
            count=len(self._indicators),
        )

    def _add_sma_trace(
        self,
        index: pd.Index,
        close_prices: pd.Series,
        overlay: IndicatorOverlay,
        color: str,
    ) -> None:
        """Add SMA indicator trace.

        Parameters
        ----------
        index : pd.Index
            DataFrame index (dates)
        close_prices : pd.Series
            Close price series
        overlay : IndicatorOverlay
            Indicator configuration
        color : str
            Line color
        """
        if self._figure is None:
            return

        window = overlay.params.get("window", 20)
        values = IndicatorCalculator.calculate_sma(close_prices, window)
        self._figure.add_trace(
            go.Scatter(
                x=index,
                y=values,
                mode="lines",
                name=overlay.name,
                line={"color": color, "width": 1},
            ),
            row=1,
            col=1,
        )

    def _add_ema_trace(
        self,
        index: pd.Index,
        close_prices: pd.Series,
        overlay: IndicatorOverlay,
        color: str,
    ) -> None:
        """Add EMA indicator trace.

        Parameters
        ----------
        index : pd.Index
            DataFrame index (dates)
        close_prices : pd.Series
            Close price series
        overlay : IndicatorOverlay
            Indicator configuration
        color : str
            Line color
        """
        if self._figure is None:
            return

        window = overlay.params.get("window", 12)
        values = IndicatorCalculator.calculate_ema(close_prices, window)
        self._figure.add_trace(
            go.Scatter(
                x=index,
                y=values,
                mode="lines",
                name=overlay.name,
                line={"color": color, "width": 1},
            ),
            row=1,
            col=1,
        )

    def _add_bollinger_traces(
        self,
        index: pd.Index,
        close_prices: pd.Series,
        overlay: IndicatorOverlay,
        color: str,
    ) -> None:
        """Add Bollinger Bands traces (upper, middle, lower).

        Parameters
        ----------
        index : pd.Index
            DataFrame index (dates)
        close_prices : pd.Series
            Close price series
        overlay : IndicatorOverlay
            Indicator configuration
        color : str
            Line color
        """
        if self._figure is None:
            return

        window = overlay.params.get("window", 20)
        num_std = overlay.params.get("num_std", 2.0)
        bands = IndicatorCalculator.calculate_bollinger_bands(
            close_prices, window, num_std
        )

        # Upper band
        self._figure.add_trace(
            go.Scatter(
                x=index,
                y=bands["upper"],
                mode="lines",
                name=f"{overlay.name} Upper",
                line={"color": color, "width": 1, "dash": "dash"},
            ),
            row=1,
            col=1,
        )

        # Middle band (SMA)
        self._figure.add_trace(
            go.Scatter(
                x=index,
                y=bands["middle"],
                mode="lines",
                name=f"{overlay.name} Middle",
                line={"color": color, "width": 1},
            ),
            row=1,
            col=1,
        )

        # Lower band
        self._figure.add_trace(
            go.Scatter(
                x=index,
                y=bands["lower"],
                mode="lines",
                name=f"{overlay.name} Lower",
                line={"color": color, "width": 1, "dash": "dash"},
            ),
            row=1,
            col=1,
        )

    def _add_volume_trace(self, df: pd.DataFrame) -> None:
        """Add volume bar trace to subplot.

        Parameters
        ----------
        df : pd.DataFrame
            Price data with Volume column
        """
        if self._figure is None or not self._show_volume:
            return

        if "Volume" not in df.columns:
            logger.warning("Volume column not found in data")
            return

        # Color bars based on price change
        colors = [
            self._colors.positive if close >= open_ else self._colors.negative
            for close, open_ in zip(df["Close"], df["Open"], strict=True)
        ]

        self._figure.add_trace(
            go.Bar(
                x=df.index,
                y=df["Volume"],
                marker_color=colors,
                name="Volume",
                showlegend=False,
            ),
            row=2,
            col=1,
        )

        logger.debug("Volume trace added")

    def _create_subplots(self) -> go.Figure:
        """Create figure with subplots if volume is enabled.

        Returns
        -------
        go.Figure
            Figure with or without subplots
        """
        if self._show_volume:
            fig = make_subplots(
                rows=2,
                cols=1,
                shared_xaxes=True,
                vertical_spacing=0.03,
                row_heights=[0.7, 0.3],
            )
        else:
            fig = make_subplots(rows=1, cols=1)

        return fig


# =============================================================================
# CandlestickChart
# =============================================================================


class CandlestickChart(PriceChartBuilder):
    """Candlestick chart builder for OHLC data.

    Creates candlestick charts with optional volume subplot and
    technical indicator overlays.

    Examples
    --------
    >>> data = PriceChartData(df=ohlcv_df, symbol="AAPL")
    >>> config = ChartConfig(title="AAPL Price Chart", theme=ChartTheme.DARK)
    >>> chart = CandlestickChart(data, config)
    >>> chart.add_sma(20).add_bollinger_bands().build().save("chart.png")
    """

    def build(self) -> "CandlestickChart":
        """Build the candlestick chart.

        Returns
        -------
        CandlestickChart
            Self for method chaining
        """
        logger.info(
            "Building candlestick chart",
            symbol=self._data.symbol,
            show_volume=self._show_volume,
            indicators=len(self._indicators),
        )

        # Get filtered data
        df = self._data.get_filtered_data()

        if df.empty:
            logger.warning("No data to display after filtering")
            self._figure = go.Figure()
            self._apply_theme()
            return self

        # Create subplots
        self._figure = self._create_subplots()

        # Add candlestick trace
        self._figure.add_trace(
            go.Candlestick(
                x=df.index,
                open=df["Open"],
                high=df["High"],
                low=df["Low"],
                close=df["Close"],
                name=self._data.symbol or "Price",
                increasing_line_color=self._colors.positive,
                decreasing_line_color=self._colors.negative,
                increasing_fillcolor=self._colors.positive,
                decreasing_fillcolor=self._colors.negative,
            ),
            row=1,
            col=1,
        )

        # Add volume
        self._add_volume_trace(df)

        # Add indicator overlays
        self._add_indicator_traces(df)

        # Apply theme
        self._apply_theme()

        # Remove rangeslider for cleaner look
        self._figure.update_layout(xaxis_rangeslider_visible=False)

        # Update y-axis titles
        self._figure.update_yaxes(title_text="Price", row=1, col=1)
        if self._show_volume:
            self._figure.update_yaxes(title_text="Volume", row=2, col=1)

        logger.info(
            "Candlestick chart built",
            symbol=self._data.symbol,
            data_points=len(df),
        )

        return self


# =============================================================================
# LineChart
# =============================================================================


class LineChart(PriceChartBuilder):
    """Line chart builder for price data.

    Creates line charts with optional volume subplot and
    technical indicator overlays.

    Examples
    --------
    >>> data = PriceChartData(df=ohlcv_df, symbol="AAPL")
    >>> chart = LineChart(data)
    >>> chart.add_sma(50).add_ema(20).build().save("chart.png")
    """

    def __init__(
        self,
        data: PriceChartData,
        config: ChartConfig | None = None,
        *,
        show_volume: bool = True,
        price_column: str = "Close",
    ) -> None:
        """Initialize LineChart.

        Parameters
        ----------
        data : PriceChartData
            Price data configuration
        config : ChartConfig | None
            Chart configuration
        show_volume : bool, default=True
            Whether to show volume subplot
        price_column : str, default="Close"
            Column to use for the line chart
        """
        super().__init__(data, config, show_volume=show_volume)
        self._price_column = price_column

    def build(self) -> "LineChart":
        """Build the line chart.

        Returns
        -------
        LineChart
            Self for method chaining
        """
        logger.info(
            "Building line chart",
            symbol=self._data.symbol,
            show_volume=self._show_volume,
            indicators=len(self._indicators),
            price_column=self._price_column,
        )

        # Get filtered data
        df = self._data.get_filtered_data()

        if df.empty:
            logger.warning("No data to display after filtering")
            self._figure = go.Figure()
            self._apply_theme()
            return self

        # Create subplots
        self._figure = self._create_subplots()

        # Add line trace
        self._figure.add_trace(
            go.Scatter(
                x=df.index,
                y=df[self._price_column],
                mode="lines",
                name=self._data.symbol or "Price",
                line={"color": self._colors.accent, "width": 2},
            ),
            row=1,
            col=1,
        )

        # Add volume
        self._add_volume_trace(df)

        # Add indicator overlays
        self._add_indicator_traces(df)

        # Apply theme
        self._apply_theme()

        # Update y-axis titles
        self._figure.update_yaxes(title_text="Price", row=1, col=1)
        if self._show_volume:
            self._figure.update_yaxes(title_text="Volume", row=2, col=1)

        logger.info(
            "Line chart built",
            symbol=self._data.symbol,
            data_points=len(df),
        )

        return self


# =============================================================================
# __all__ Export
# =============================================================================

__all__ = [
    "CandlestickChart",
    "IndicatorOverlay",
    "LineChart",
    "PriceChartBuilder",
    "PriceChartData",
]

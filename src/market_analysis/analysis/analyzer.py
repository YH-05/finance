"""Analyzer class for market data analysis with method chaining.

This module provides the Analyzer class that enables fluent method chaining
for adding technical indicators to market data.
"""

from __future__ import annotations

from datetime import datetime
from typing import Self, cast

import pandas as pd

from ..types import AnalysisResult
from ..utils.logging_config import get_logger
from .indicators import IndicatorCalculator

logger = get_logger(__name__, module="analyzer")


class Analyzer:
    """Analyzer for market data with method chaining support.

    Provides a fluent interface for adding technical indicators to price data.
    All operations are performed on a copy of the original data.

    Parameters
    ----------
    data : pd.DataFrame
        OHLCV DataFrame with at least a 'close' column
    symbol : str
        Symbol identifier for the data

    Attributes
    ----------
    data : pd.DataFrame
        DataFrame with original data and added indicators
    indicators : dict[str, pd.Series]
        Dictionary of calculated indicators
    symbol : str
        Symbol identifier

    Examples
    --------
    >>> df = pd.DataFrame({"close": [100, 102, 101, 103, 105]})
    >>> analyzer = Analyzer(df, "AAPL")
    >>> result = (
    ...     analyzer
    ...     .add_sma(20)
    ...     .add_ema(12)
    ...     .add_returns()
    ...     .add_volatility(20)
    ...     .result()
    ... )
    """

    def __init__(
        self,
        data: pd.DataFrame,
        symbol: str = "",
    ) -> None:
        """Initialize the Analyzer.

        Parameters
        ----------
        data : pd.DataFrame
            OHLCV DataFrame with at least a 'close' column
        symbol : str, default=""
            Symbol identifier for the data
        """
        logger.debug(
            "Initializing Analyzer",
            symbol=symbol,
            rows=len(data),
            columns=list(data.columns),
        )

        # Store a copy to avoid modifying the original
        self._data = data.copy()
        self._symbol = symbol
        self._indicators: dict[str, pd.Series] = {}
        self._price_column = "close"

        # Validate that close column exists
        if self._price_column not in self._data.columns:
            logger.warning(
                "Close column not found, trying alternatives",
                available_columns=list(self._data.columns),
            )
            # Try common alternatives
            for alt in ["Close", "adj_close", "Adj Close", "price"]:
                if alt in self._data.columns:
                    self._price_column = alt
                    break

        logger.info(
            "Analyzer initialized",
            symbol=symbol,
            price_column=self._price_column,
        )

    @property
    def data(self) -> pd.DataFrame:
        """Get the DataFrame with all added indicators.

        Returns
        -------
        pd.DataFrame
            Copy of the data with indicators added as columns
        """
        return self._data.copy()

    @property
    def indicators(self) -> dict[str, pd.Series]:
        """Get dictionary of calculated indicators.

        Returns
        -------
        dict[str, pd.Series]
            Dictionary mapping indicator names to their Series
        """
        return self._indicators.copy()

    @property
    def symbol(self) -> str:
        """Get the symbol identifier."""
        return self._symbol

    def _get_prices(self) -> pd.Series:
        """Get the price series for calculations."""
        return cast("pd.Series", self._data[self._price_column])

    def add_sma(self, window: int, column_name: str | None = None) -> Self:
        """Add Simple Moving Average indicator.

        Parameters
        ----------
        window : int
            Window size for SMA calculation
        column_name : str | None, default=None
            Custom column name. If None, uses f"sma_{window}"

        Returns
        -------
        Self
            Returns self for method chaining

        Examples
        --------
        >>> analyzer.add_sma(20).add_sma(50).add_sma(200)
        """
        name = column_name or f"sma_{window}"

        logger.debug("Adding SMA", window=window, column_name=name)

        sma = IndicatorCalculator.calculate_sma(self._get_prices(), window)
        self._data[name] = sma
        self._indicators[name] = sma

        logger.debug("SMA added", column_name=name)

        return self

    def add_ema(
        self,
        window: int,
        column_name: str | None = None,
        adjust: bool = True,
    ) -> Self:
        """Add Exponential Moving Average indicator.

        Parameters
        ----------
        window : int
            Span for EMA calculation
        column_name : str | None, default=None
            Custom column name. If None, uses f"ema_{window}"
        adjust : bool, default=True
            Whether to use adjusted calculation

        Returns
        -------
        Self
            Returns self for method chaining

        Examples
        --------
        >>> analyzer.add_ema(12).add_ema(26)
        """
        name = column_name or f"ema_{window}"

        logger.debug("Adding EMA", window=window, column_name=name)

        ema = IndicatorCalculator.calculate_ema(self._get_prices(), window, adjust)
        self._data[name] = ema
        self._indicators[name] = ema

        logger.debug("EMA added", column_name=name)

        return self

    def add_returns(
        self,
        periods: int = 1,
        log_returns: bool = False,
        column_name: str | None = None,
    ) -> Self:
        """Add returns indicator.

        Parameters
        ----------
        periods : int, default=1
            Number of periods for return calculation
        log_returns : bool, default=False
            If True, calculate logarithmic returns
        column_name : str | None, default=None
            Custom column name. If None, uses "returns" or "log_returns"

        Returns
        -------
        Self
            Returns self for method chaining

        Examples
        --------
        >>> analyzer.add_returns().add_returns(periods=5, column_name="returns_5d")
        """
        if column_name is None:
            if log_returns:
                name = "log_returns" if periods == 1 else f"log_returns_{periods}"
            else:
                name = "returns" if periods == 1 else f"returns_{periods}"
        else:
            name = column_name

        logger.debug(
            "Adding returns",
            periods=periods,
            log_returns=log_returns,
            column_name=name,
        )

        returns = IndicatorCalculator.calculate_returns(
            self._get_prices(), periods, log_returns
        )
        self._data[name] = returns
        self._indicators[name] = returns

        logger.debug("Returns added", column_name=name)

        return self

    def add_volatility(
        self,
        window: int = 20,
        annualize: bool = True,
        annualization_factor: int = 252,
        column_name: str | None = None,
    ) -> Self:
        """Add volatility indicator.

        Note: This method requires returns to be calculated first.
        If returns are not present, they will be calculated automatically.

        Parameters
        ----------
        window : int, default=20
            Rolling window size
        annualize : bool, default=True
            Whether to annualize volatility
        annualization_factor : int, default=252
            Factor for annualization
        column_name : str | None, default=None
            Custom column name. If None, uses "volatility" or "volatility_{window}"

        Returns
        -------
        Self
            Returns self for method chaining

        Examples
        --------
        >>> analyzer.add_volatility(20).add_volatility(60, column_name="vol_60d")
        """
        name = column_name or (f"volatility_{window}" if window != 20 else "volatility")

        logger.debug(
            "Adding volatility",
            window=window,
            annualize=annualize,
            column_name=name,
        )

        # Get or calculate returns
        if "returns" in self._indicators:
            returns = self._indicators["returns"]
        else:
            returns = IndicatorCalculator.calculate_returns(self._get_prices())

        volatility = IndicatorCalculator.calculate_volatility(
            returns,
            window=window,
            annualize=annualize,
            annualization_factor=annualization_factor,
        )
        self._data[name] = volatility
        self._indicators[name] = volatility

        logger.debug("Volatility added", column_name=name)

        return self

    def add_all_indicators(
        self,
        sma_windows: list[int] | None = None,
        ema_windows: list[int] | None = None,
        volatility_window: int = 20,
    ) -> Self:
        """Add multiple common indicators at once.

        Parameters
        ----------
        sma_windows : list[int] | None, default=None
            Windows for SMA (default: [20, 50, 200])
        ema_windows : list[int] | None, default=None
            Windows for EMA (default: [12, 26])
        volatility_window : int, default=20
            Window for volatility

        Returns
        -------
        Self
            Returns self for method chaining

        Examples
        --------
        >>> analyzer.add_all_indicators()
        """
        if sma_windows is None:
            sma_windows = [20, 50, 200]
        if ema_windows is None:
            ema_windows = [12, 26]

        logger.info(
            "Adding all indicators",
            sma_windows=sma_windows,
            ema_windows=ema_windows,
            volatility_window=volatility_window,
        )

        # Add returns first (needed for volatility)
        self.add_returns()

        # Add SMAs
        for window in sma_windows:
            self.add_sma(window)

        # Add EMAs
        for window in ema_windows:
            self.add_ema(window)

        # Add volatility
        self.add_volatility(volatility_window)

        logger.info(
            "All indicators added",
            indicator_count=len(self._indicators),
        )

        return self

    def result(self) -> AnalysisResult:
        """Get the analysis result.

        Returns
        -------
        AnalysisResult
            Result object containing data, indicators, and statistics

        Examples
        --------
        >>> result = analyzer.add_sma(20).add_returns().result()
        >>> result.symbol
        'AAPL'
        """
        logger.info(
            "Creating analysis result",
            symbol=self._symbol,
            indicator_count=len(self._indicators),
        )

        # Calculate basic statistics
        statistics: dict[str, float] = {}
        if "returns" in self._indicators:
            returns = self._indicators["returns"].dropna()
            if len(returns) > 0:
                statistics["mean_return"] = float(returns.mean())
                statistics["std_return"] = float(returns.std())
                statistics["min_return"] = float(returns.min())
                statistics["max_return"] = float(returns.max())

        if "volatility" in self._indicators:
            vol = self._indicators["volatility"].dropna()
            if len(vol) > 0:
                statistics["avg_volatility"] = float(vol.mean())
                statistics["current_volatility"] = float(vol.iloc[-1])

        return AnalysisResult(
            symbol=self._symbol,
            data=self._data.copy(),
            indicators=self._indicators.copy(),
            statistics=statistics,
            analyzed_at=datetime.now(),
        )

    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"Analyzer(symbol={self._symbol!r}, "
            f"rows={len(self._data)}, "
            f"indicators={list(self._indicators.keys())})"
        )


__all__ = [
    "Analyzer",
]

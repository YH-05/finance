"""Technical indicator calculations for market data analysis.

This module provides static methods for calculating common technical
indicators used in financial analysis.
"""

from typing import Any, cast

import numpy as np
import pandas as pd

from ..utils.logging_config import get_logger

logger = get_logger(__name__, module="indicators")


class IndicatorCalculator:
    """Calculator for technical indicators.

    Provides static methods for calculating common technical indicators
    such as moving averages, returns, and volatility.

    All methods are designed to handle edge cases gracefully,
    returning NaN values when there are insufficient data points.

    Examples
    --------
    >>> prices = pd.Series([100, 102, 101, 103, 105])
    >>> sma = IndicatorCalculator.calculate_sma(prices, window=3)
    >>> returns = IndicatorCalculator.calculate_returns(prices)
    """

    @staticmethod
    def calculate_sma(
        prices: pd.Series,
        window: int,
    ) -> pd.Series:
        """Calculate Simple Moving Average (SMA).

        The SMA is calculated as the arithmetic mean of prices
        over the specified window period.

        Parameters
        ----------
        prices : pd.Series
            Price series (typically closing prices)
        window : int
            Number of periods for the moving average

        Returns
        -------
        pd.Series
            SMA values. First (window-1) values will be NaN.

        Raises
        ------
        ValueError
            If window is less than 1

        Examples
        --------
        >>> prices = pd.Series([10, 11, 12, 13, 14])
        >>> sma = IndicatorCalculator.calculate_sma(prices, window=3)
        >>> sma.iloc[-1]
        13.0
        """
        logger.debug(
            "Calculating SMA",
            window=window,
            data_points=len(prices),
        )

        if window < 1:
            logger.error("Invalid window size", window=window)
            raise ValueError(f"Window must be at least 1, got {window}")

        if prices.empty:
            logger.warning("Empty price series provided")
            return pd.Series(dtype=np.float64)

        result = cast(
            pd.Series, prices.rolling(window=window, min_periods=window).mean()
        )

        logger.debug(
            "SMA calculation completed",
            window=window,
            valid_values=result.notna().sum(),
            nan_values=result.isna().sum(),
        )

        return result

    @staticmethod
    def calculate_ema(
        prices: pd.Series,
        window: int,
        adjust: bool = True,
    ) -> pd.Series:
        """Calculate Exponential Moving Average (EMA).

        The EMA gives more weight to recent prices, making it more
        responsive to new information than the SMA.

        Parameters
        ----------
        prices : pd.Series
            Price series (typically closing prices)
        window : int
            Span for the exponential moving average
        adjust : bool, default=True
            Whether to use adjusted calculation (recommended for accuracy)

        Returns
        -------
        pd.Series
            EMA values. Earlier values may be NaN depending on min_periods.

        Raises
        ------
        ValueError
            If window is less than 1

        Examples
        --------
        >>> prices = pd.Series([10, 11, 12, 13, 14])
        >>> ema = IndicatorCalculator.calculate_ema(prices, window=3)
        >>> ema.iloc[-1]  # Will be close to 13.5 due to weighting
        13.5
        """
        logger.debug(
            "Calculating EMA",
            window=window,
            adjust=adjust,
            data_points=len(prices),
        )

        if window < 1:
            logger.error("Invalid window size", window=window)
            raise ValueError(f"Window must be at least 1, got {window}")

        if prices.empty:
            logger.warning("Empty price series provided")
            return pd.Series(dtype=np.float64)

        result = cast(
            pd.Series, prices.ewm(span=window, adjust=adjust, min_periods=window).mean()
        )

        logger.debug(
            "EMA calculation completed",
            window=window,
            valid_values=result.notna().sum(),
            nan_values=result.isna().sum(),
        )

        return result

    @staticmethod
    def calculate_returns(
        prices: pd.Series,
        periods: int = 1,
        log_returns: bool = False,
    ) -> pd.Series:
        """Calculate price returns.

        Parameters
        ----------
        prices : pd.Series
            Price series
        periods : int, default=1
            Number of periods for return calculation
        log_returns : bool, default=False
            If True, calculate logarithmic returns instead of simple returns

        Returns
        -------
        pd.Series
            Return values. First `periods` values will be NaN.

        Raises
        ------
        ValueError
            If periods is less than 1

        Examples
        --------
        >>> prices = pd.Series([100, 102, 101, 105])
        >>> returns = IndicatorCalculator.calculate_returns(prices)
        >>> returns.iloc[1]  # (102-100)/100 = 0.02
        0.02
        """
        logger.debug(
            "Calculating returns",
            periods=periods,
            log_returns=log_returns,
            data_points=len(prices),
        )

        if periods < 1:
            logger.error("Invalid periods value", periods=periods)
            raise ValueError(f"Periods must be at least 1, got {periods}")

        if prices.empty:
            logger.warning("Empty price series provided")
            return pd.Series(dtype=np.float64)

        if log_returns:
            result = np.log(prices / prices.shift(periods))
        else:
            result = prices.pct_change(periods=periods, fill_method=None)

        logger.debug(
            "Returns calculation completed",
            periods=periods,
            log_returns=log_returns,
            valid_values=result.notna().sum(),
            nan_values=result.isna().sum(),
        )

        return result

    @staticmethod
    def calculate_volatility(
        returns: pd.Series,
        window: int,
        annualize: bool = True,
        annualization_factor: int = 252,
    ) -> pd.Series:
        """Calculate rolling volatility (standard deviation of returns).

        Parameters
        ----------
        returns : pd.Series
            Return series (use calculate_returns first)
        window : int
            Rolling window size for volatility calculation
        annualize : bool, default=True
            If True, annualize the volatility
        annualization_factor : int, default=252
            Factor for annualization (252 for daily, 52 for weekly, 12 for monthly)

        Returns
        -------
        pd.Series
            Volatility values. First (window-1) values will be NaN.

        Raises
        ------
        ValueError
            If window is less than 2 or annualization_factor is less than 1

        Examples
        --------
        >>> prices = pd.Series([100, 102, 101, 103, 105, 104, 106])
        >>> returns = IndicatorCalculator.calculate_returns(prices)
        >>> vol = IndicatorCalculator.calculate_volatility(returns, window=5)
        """
        logger.debug(
            "Calculating volatility",
            window=window,
            annualize=annualize,
            annualization_factor=annualization_factor,
            data_points=len(returns),
        )

        if window < 2:
            logger.error("Invalid window size for volatility", window=window)
            raise ValueError(
                f"Window must be at least 2 for volatility calculation, got {window}"
            )

        if annualization_factor < 1:
            logger.error(
                "Invalid annualization factor",
                annualization_factor=annualization_factor,
            )
            raise ValueError(
                f"Annualization factor must be at least 1, got {annualization_factor}"
            )

        if returns.empty:
            logger.warning("Empty returns series provided")
            return pd.Series(dtype=np.float64)

        # Calculate rolling standard deviation
        result = cast(
            pd.Series, returns.rolling(window=window, min_periods=window).std()
        )

        # Annualize if requested
        if annualize:
            result = cast(pd.Series, result * np.sqrt(annualization_factor))

        logger.debug(
            "Volatility calculation completed",
            window=window,
            annualized=annualize,
            valid_values=result.notna().sum(),
            nan_values=result.isna().sum(),
        )

        return result

    @staticmethod
    def calculate_all(
        prices: pd.Series,
        sma_windows: list[int] | None = None,
        ema_windows: list[int] | None = None,
        volatility_window: int = 20,
        annualize_volatility: bool = True,
        annualization_factor: int = 252,
    ) -> dict[str, pd.Series]:
        """Calculate multiple indicators at once.

        Convenience method to calculate SMA, EMA, returns, and volatility
        in a single call.

        Parameters
        ----------
        prices : pd.Series
            Price series (typically closing prices)
        sma_windows : list[int] | None, default=None
            Windows for SMA calculation (default: [20, 50, 200])
        ema_windows : list[int] | None, default=None
            Windows for EMA calculation (default: [12, 26])
        volatility_window : int, default=20
            Window for volatility calculation
        annualize_volatility : bool, default=True
            Whether to annualize volatility
        annualization_factor : int, default=252
            Factor for annualization

        Returns
        -------
        dict[str, pd.Series]
            Dictionary with indicator names as keys and Series as values

        Examples
        --------
        >>> prices = pd.Series([100, 102, 101, 103, 105])
        >>> indicators = IndicatorCalculator.calculate_all(prices)
        >>> "returns" in indicators
        True
        """
        logger.info(
            "Calculating all indicators",
            data_points=len(prices),
            sma_windows=sma_windows,
            ema_windows=ema_windows,
            volatility_window=volatility_window,
        )

        if sma_windows is None:
            sma_windows = [20, 50, 200]

        if ema_windows is None:
            ema_windows = [12, 26]

        result: dict[str, Any] = {}

        # Calculate returns first (needed for volatility)
        returns = IndicatorCalculator.calculate_returns(prices)
        result["returns"] = returns

        # Calculate SMAs
        for window in sma_windows:
            result[f"sma_{window}"] = IndicatorCalculator.calculate_sma(prices, window)

        # Calculate EMAs
        for window in ema_windows:
            result[f"ema_{window}"] = IndicatorCalculator.calculate_ema(prices, window)

        # Calculate volatility
        result["volatility"] = IndicatorCalculator.calculate_volatility(
            returns,
            window=volatility_window,
            annualize=annualize_volatility,
            annualization_factor=annualization_factor,
        )

        logger.info(
            "All indicators calculated",
            indicator_count=len(result),
            indicators=list(result.keys()),
        )

        return result


__all__ = [
    "IndicatorCalculator",
]

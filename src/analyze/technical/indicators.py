"""Technical indicator calculations for financial data analysis.

This module provides the TechnicalIndicators class with static methods for
calculating common technical indicators used in financial analysis.

Classes
-------
TechnicalIndicators
    Calculator for technical indicators (SMA, EMA, RSI, MACD, etc.)

Examples
--------
>>> import pandas as pd
>>> from analyze.technical.indicators import TechnicalIndicators
>>> prices = pd.Series([100.0, 102.0, 101.0, 103.0, 105.0])
>>> sma = TechnicalIndicators.calculate_sma(prices, window=3)
>>> returns = TechnicalIndicators.calculate_returns(prices)
"""

from typing import Any, cast

import numpy as np
import pandas as pd

from database.utils.logging_config import get_logger

from .types import BollingerBandsResult, MACDResult

logger = get_logger(__name__)


class TechnicalIndicators:
    """Calculator for technical indicators.

    Provides static methods for calculating common technical indicators
    such as moving averages, returns, volatility, RSI, MACD, and
    Bollinger Bands.

    All methods are designed to handle edge cases gracefully,
    returning NaN values when there are insufficient data points.

    Methods
    -------
    calculate_sma(prices, window)
        Calculate Simple Moving Average
    calculate_ema(prices, window, adjust=True)
        Calculate Exponential Moving Average
    calculate_returns(prices, periods=1, log_returns=False)
        Calculate price returns
    calculate_volatility(returns, window, annualize=True, annualization_factor=252)
        Calculate rolling volatility
    calculate_bollinger_bands(prices, window=20, num_std=2.0)
        Calculate Bollinger Bands
    calculate_rsi(prices, period=14)
        Calculate Relative Strength Index
    calculate_macd(prices, fast_period=12, slow_period=26, signal_period=9)
        Calculate MACD
    calculate_all(prices, ...)
        Calculate multiple indicators at once

    Examples
    --------
    >>> prices = pd.Series([100, 102, 101, 103, 105])
    >>> sma = TechnicalIndicators.calculate_sma(prices, window=3)
    >>> returns = TechnicalIndicators.calculate_returns(prices)
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
            Number of periods for the moving average. Must be at least 1.

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
        >>> prices = pd.Series([10.0, 11.0, 12.0, 13.0, 14.0])
        >>> sma = TechnicalIndicators.calculate_sma(prices, window=3)
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
            raise ValueError("window must be at least 1")

        if prices.empty:
            logger.warning("Empty price series provided")
            return pd.Series(dtype=np.float64)

        result = cast(
            "pd.Series", prices.rolling(window=window, min_periods=window).mean()
        )

        logger.debug(
            "SMA calculation completed",
            window=window,
            valid_values=int(result.notna().sum()),
            nan_values=int(result.isna().sum()),
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
            Span for the exponential moving average. Must be at least 1.
        adjust : bool, default=True
            Whether to use adjusted calculation (recommended for accuracy)

        Returns
        -------
        pd.Series
            EMA values. First (window-1) values will be NaN.

        Raises
        ------
        ValueError
            If window is less than 1

        Examples
        --------
        >>> prices = pd.Series([10.0, 11.0, 12.0, 13.0, 14.0])
        >>> ema = TechnicalIndicators.calculate_ema(prices, window=3)
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
            raise ValueError("window must be at least 1")

        if prices.empty:
            logger.warning("Empty price series provided")
            return pd.Series(dtype=np.float64)

        result = cast(
            "pd.Series",
            prices.ewm(span=window, adjust=adjust, min_periods=window).mean(),
        )

        logger.debug(
            "EMA calculation completed",
            window=window,
            valid_values=int(result.notna().sum()),
            nan_values=int(result.isna().sum()),
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
            Number of periods for return calculation. Must be at least 1.
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
        >>> prices = pd.Series([100.0, 102.0, 101.0, 105.0])
        >>> returns = TechnicalIndicators.calculate_returns(prices)
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
            raise ValueError("periods must be at least 1")

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
            valid_values=int(result.notna().sum()),
            nan_values=int(result.isna().sum()),
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
            Rolling window size for volatility calculation. Must be at least 2.
        annualize : bool, default=True
            If True, annualize the volatility
        annualization_factor : int, default=252
            Factor for annualization (252 for daily, 52 for weekly, 12 for monthly).
            Must be at least 1.

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
        >>> prices = pd.Series([100.0, 102.0, 101.0, 103.0, 105.0, 104.0, 106.0])
        >>> returns = TechnicalIndicators.calculate_returns(prices)
        >>> vol = TechnicalIndicators.calculate_volatility(returns, window=5)
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
            raise ValueError("window must be at least 2")

        if annualization_factor < 1:
            logger.error(
                "Invalid annualization factor",
                annualization_factor=annualization_factor,
            )
            raise ValueError("annualization_factor must be at least 1")

        if returns.empty:
            logger.warning("Empty returns series provided")
            return pd.Series(dtype=np.float64)

        # Calculate rolling standard deviation
        result = cast(
            "pd.Series", returns.rolling(window=window, min_periods=window).std()
        )

        # Annualize if requested
        if annualize:
            result = cast("pd.Series", result * np.sqrt(annualization_factor))

        logger.debug(
            "Volatility calculation completed",
            window=window,
            annualized=annualize,
            valid_values=int(result.notna().sum()),
            nan_values=int(result.isna().sum()),
        )

        return result

    @staticmethod
    def calculate_bollinger_bands(
        prices: pd.Series,
        window: int = 20,
        num_std: float = 2.0,
    ) -> BollingerBandsResult:
        """Calculate Bollinger Bands.

        Bollinger Bands consist of a middle band (SMA) and upper/lower bands
        that are standard deviations away from the middle band.

        Parameters
        ----------
        prices : pd.Series
            Price series (typically closing prices)
        window : int, default=20
            Number of periods for the moving average. Must be at least 2.
        num_std : float, default=2.0
            Number of standard deviations for the bands. Must be positive.

        Returns
        -------
        BollingerBandsResult
            Dictionary with keys 'middle', 'upper', 'lower'

        Raises
        ------
        ValueError
            If window is less than 2 or num_std is not positive

        Examples
        --------
        >>> prices = pd.Series([100.0, 102.0, 101.0, 103.0, 105.0, 104.0, 106.0, 108.0])
        >>> bands = TechnicalIndicators.calculate_bollinger_bands(prices, window=5)
        >>> 'upper' in bands and 'middle' in bands and 'lower' in bands
        True
        """
        logger.debug(
            "Calculating Bollinger Bands",
            window=window,
            num_std=num_std,
            data_points=len(prices),
        )

        if window < 2:
            logger.error("Invalid window size", window=window)
            raise ValueError("window must be at least 2")

        if num_std <= 0:
            logger.error("Invalid num_std", num_std=num_std)
            raise ValueError("num_std must be positive")

        if prices.empty:
            logger.warning("Empty price series provided")
            return BollingerBandsResult(
                middle=pd.Series(dtype=np.float64),
                upper=pd.Series(dtype=np.float64),
                lower=pd.Series(dtype=np.float64),
            )

        # Calculate middle band (SMA)
        middle = cast(
            "pd.Series", prices.rolling(window=window, min_periods=window).mean()
        )

        # Calculate standard deviation
        rolling_std = cast(
            "pd.Series", prices.rolling(window=window, min_periods=window).std()
        )

        # Calculate upper and lower bands
        upper = cast("pd.Series", middle + (rolling_std * num_std))
        lower = cast("pd.Series", middle - (rolling_std * num_std))

        logger.debug(
            "Bollinger Bands calculation completed",
            window=window,
            num_std=num_std,
            valid_values=int(middle.notna().sum()),
        )

        return BollingerBandsResult(middle=middle, upper=upper, lower=lower)

    @staticmethod
    def calculate_rsi(
        prices: pd.Series,
        period: int = 14,
    ) -> pd.Series:
        """Calculate Relative Strength Index (RSI).

        RSI is a momentum indicator that measures the speed and magnitude of
        recent price changes to evaluate overbought or oversold conditions.

        The calculation uses EMA (Exponential Moving Average) for averaging
        gains and losses.

        Parameters
        ----------
        prices : pd.Series
            Price series (typically closing prices)
        period : int, default=14
            Number of periods for RSI calculation. Must be at least 1.

        Returns
        -------
        pd.Series
            RSI values in the range [0, 100]. First `period` values will be NaN.

        Raises
        ------
        ValueError
            If period is less than 1

        Notes
        -----
        RSI = 100 - (100 / (1 + RS))
        where RS = Average Gain / Average Loss

        RSI > 70 is typically considered overbought
        RSI < 30 is typically considered oversold

        Examples
        --------
        >>> prices = pd.Series([44.0, 44.34, 44.09, 43.61, 44.33, 44.83, 45.10, 45.42])
        >>> rsi = TechnicalIndicators.calculate_rsi(prices, period=6)
        """
        logger.debug(
            "Calculating RSI",
            period=period,
            data_points=len(prices),
        )

        if period < 1:
            logger.error("Invalid period value", period=period)
            raise ValueError("period must be at least 1")

        if prices.empty:
            logger.warning("Empty price series provided")
            return pd.Series(dtype=np.float64)

        # Calculate price changes
        delta = prices.diff()

        # Separate gains and losses
        gains = delta.clip(lower=0)
        losses = (-delta).clip(lower=0)

        # Calculate EMA of gains and losses
        avg_gain = gains.ewm(span=period, adjust=False, min_periods=period).mean()
        avg_loss = losses.ewm(span=period, adjust=False, min_periods=period).mean()

        # Calculate RS
        rs = avg_gain / avg_loss

        # Calculate RSI
        rsi = 100 - (100 / (1 + rs))

        # Handle case where avg_loss is 0 (all gains, RSI should be 100)
        rsi = rsi.fillna(100.0)

        # Ensure first `period` values are NaN
        rsi.iloc[:period] = np.nan

        logger.debug(
            "RSI calculation completed",
            period=period,
            valid_values=int(rsi.notna().sum()),
            nan_values=int(rsi.isna().sum()),
        )

        return rsi

    @staticmethod
    def calculate_macd(
        prices: pd.Series,
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9,
    ) -> MACDResult:
        """Calculate Moving Average Convergence Divergence (MACD).

        MACD is a trend-following momentum indicator that shows the relationship
        between two exponential moving averages of prices.

        Parameters
        ----------
        prices : pd.Series
            Price series (typically closing prices)
        fast_period : int, default=12
            Period for the fast EMA. Must be less than slow_period.
        slow_period : int, default=26
            Period for the slow EMA
        signal_period : int, default=9
            Period for the signal line EMA

        Returns
        -------
        MACDResult
            Dictionary with keys 'macd', 'signal', 'histogram'

        Raises
        ------
        ValueError
            If fast_period is greater than or equal to slow_period

        Notes
        -----
        MACD Line = Fast EMA - Slow EMA
        Signal Line = EMA of MACD Line
        Histogram = MACD Line - Signal Line

        Common trading signals:
        - MACD crosses above signal line: bullish
        - MACD crosses below signal line: bearish
        - MACD crosses above zero: bullish
        - MACD crosses below zero: bearish

        Examples
        --------
        >>> prices = pd.Series([100.0 + i * 0.5 for i in range(40)])
        >>> macd = TechnicalIndicators.calculate_macd(prices)
        """
        logger.debug(
            "Calculating MACD",
            fast_period=fast_period,
            slow_period=slow_period,
            signal_period=signal_period,
            data_points=len(prices),
        )

        if fast_period >= slow_period:
            logger.error(
                "Invalid MACD periods",
                fast_period=fast_period,
                slow_period=slow_period,
            )
            raise ValueError("fast_period must be less than slow_period")

        if prices.empty:
            logger.warning("Empty price series provided")
            return MACDResult(
                macd=pd.Series(dtype=np.float64),
                signal=pd.Series(dtype=np.float64),
                histogram=pd.Series(dtype=np.float64),
            )

        # Calculate fast and slow EMA
        fast_ema = prices.ewm(
            span=fast_period, adjust=False, min_periods=fast_period
        ).mean()
        slow_ema = prices.ewm(
            span=slow_period, adjust=False, min_periods=slow_period
        ).mean()

        # MACD line
        macd_line = fast_ema - slow_ema

        # Signal line (EMA of MACD)
        signal_line = macd_line.ewm(
            span=signal_period, adjust=False, min_periods=signal_period
        ).mean()

        # Histogram
        histogram = macd_line - signal_line

        logger.debug(
            "MACD calculation completed",
            fast_period=fast_period,
            slow_period=slow_period,
            signal_period=signal_period,
            valid_macd_values=int(macd_line.notna().sum()),
        )

        return MACDResult(macd=macd_line, signal=signal_line, histogram=histogram)

    @staticmethod
    def calculate_all(
        prices: pd.Series,
        sma_windows: list[int] | None = None,
        ema_windows: list[int] | None = None,
        volatility_window: int = 20,
        annualize_volatility: bool = True,
        annualization_factor: int = 252,
        rsi_period: int = 14,
        macd_fast: int = 12,
        macd_slow: int = 26,
        macd_signal: int = 9,
    ) -> dict[str, Any]:
        """Calculate multiple indicators at once.

        Convenience method to calculate SMA, EMA, returns, volatility,
        RSI, MACD, and Bollinger Bands in a single call.

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
        rsi_period : int, default=14
            Period for RSI calculation
        macd_fast : int, default=12
            Fast period for MACD
        macd_slow : int, default=26
            Slow period for MACD
        macd_signal : int, default=9
            Signal period for MACD

        Returns
        -------
        dict[str, Any]
            Dictionary with indicator names as keys and Series as values.
            Keys include: 'returns', 'sma_{window}', 'ema_{window}',
            'volatility', 'rsi', 'macd', 'macd_signal', 'macd_histogram'

        Examples
        --------
        >>> prices = pd.Series([100.0 + i for i in range(250)])
        >>> indicators = TechnicalIndicators.calculate_all(prices)
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
        returns = TechnicalIndicators.calculate_returns(prices)
        result["returns"] = returns

        # Calculate SMAs
        for window in sma_windows:
            result[f"sma_{window}"] = TechnicalIndicators.calculate_sma(prices, window)

        # Calculate EMAs
        for window in ema_windows:
            result[f"ema_{window}"] = TechnicalIndicators.calculate_ema(prices, window)

        # Calculate volatility
        result["volatility"] = TechnicalIndicators.calculate_volatility(
            returns,
            window=volatility_window,
            annualize=annualize_volatility,
            annualization_factor=annualization_factor,
        )

        # Calculate RSI
        result["rsi"] = TechnicalIndicators.calculate_rsi(prices, period=rsi_period)

        # Calculate MACD
        macd_result = TechnicalIndicators.calculate_macd(
            prices,
            fast_period=macd_fast,
            slow_period=macd_slow,
            signal_period=macd_signal,
        )
        result["macd"] = macd_result["macd"]
        result["macd_signal"] = macd_result["signal"]
        result["macd_histogram"] = macd_result["histogram"]

        logger.info(
            "All indicators calculated",
            indicator_count=len(result),
            indicators=list(result.keys()),
        )

        return result


__all__ = [
    "TechnicalIndicators",
]

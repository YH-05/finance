"""Analyze package integration for strategy package.

This module provides integration between the analyze package's technical
analysis functions and the strategy package's signal generation.

Classes
-------
TechnicalSignalProvider
    Provides trading signals based on technical indicators

Functions
---------
create_signal_provider
    Factory function to create a TechnicalSignalProvider

Examples
--------
>>> from strategy.integration import create_signal_provider
>>> provider = create_signal_provider()
>>> signals = provider.compute_signals(price_series)
"""

from typing import Any

import pandas as pd

from strategy.utils.logging_config import get_logger

logger = get_logger(__name__)


class TechnicalSignalProvider:
    """Provider for technical trading signals using analyze package.

    This class uses the analyze package's TechnicalIndicators to compute
    various technical signals that can be used in strategy construction.

    Examples
    --------
    >>> provider = TechnicalSignalProvider()
    >>> signals = provider.compute_signals(close_prices)
    >>> "rsi" in signals
    True
    """

    def __init__(self) -> None:
        """Initialize TechnicalSignalProvider."""
        logger.debug("Initializing TechnicalSignalProvider")
        logger.info("TechnicalSignalProvider initialized")

    def compute_signals(
        self,
        prices: pd.Series,
        sma_windows: list[int] | None = None,
        ema_windows: list[int] | None = None,
        rsi_period: int = 14,
    ) -> dict[str, Any]:
        """Compute technical signals from price data.

        Parameters
        ----------
        prices : pd.Series
            Price series (typically close prices)
        sma_windows : list[int] | None
            Windows for SMA calculation (default: [20, 50])
        ema_windows : list[int] | None
            Windows for EMA calculation (default: [12, 26])
        rsi_period : int
            Period for RSI calculation (default: 14)

        Returns
        -------
        dict[str, Any]
            Dictionary of signal name to pd.Series

        Examples
        --------
        >>> provider = TechnicalSignalProvider()
        >>> signals = provider.compute_signals(close_prices)
        >>> "returns" in signals
        True
        """
        logger.debug(
            "Computing technical signals",
            data_points=len(prices),
            rsi_period=rsi_period,
        )

        if prices.empty:
            logger.warning("Empty price series provided")
            return {}

        if sma_windows is None:
            sma_windows = [20, 50]

        if ema_windows is None:
            ema_windows = [12, 26]

        # Import here to avoid circular dependencies
        from analyze.technical.indicators import TechnicalIndicators

        result: dict[str, Any] = {}

        # Calculate returns
        result["returns"] = TechnicalIndicators.calculate_returns(prices)

        # Calculate SMAs
        for window in sma_windows:
            if len(prices) >= window:
                result[f"sma_{window}"] = TechnicalIndicators.calculate_sma(
                    prices, window
                )

        # Calculate EMAs
        for window in ema_windows:
            if len(prices) >= window:
                result[f"ema_{window}"] = TechnicalIndicators.calculate_ema(
                    prices, window
                )

        # Calculate RSI
        if len(prices) >= rsi_period:
            result["rsi"] = TechnicalIndicators.calculate_rsi(prices, period=rsi_period)

        # Calculate volatility
        if len(prices) >= 20:
            returns = result.get("returns")
            if returns is not None and isinstance(returns, pd.Series):
                result["volatility"] = TechnicalIndicators.calculate_volatility(
                    returns, window=20
                )

        logger.info(
            "Technical signals computed",
            signal_count=len(result),
            signals=list(result.keys()),
        )

        return result

    def compute_momentum_signal(
        self,
        prices: pd.Series,
        lookback: int = 20,
    ) -> pd.Series:
        """Compute momentum signal.

        Parameters
        ----------
        prices : pd.Series
            Price series
        lookback : int
            Lookback period for momentum (default: 20)

        Returns
        -------
        pd.Series
            Momentum signal values
        """
        logger.debug("Computing momentum signal", lookback=lookback)

        if len(prices) < lookback:
            logger.warning(
                "Insufficient data for momentum calculation",
                required=lookback,
                available=len(prices),
            )
            return pd.Series(dtype=float)

        momentum = prices.pct_change(periods=lookback)

        logger.debug(
            "Momentum signal computed", valid_values=int(momentum.notna().sum())
        )

        return momentum

    def compute_trend_signal(
        self,
        prices: pd.Series,
        short_window: int = 20,
        long_window: int = 50,
    ) -> pd.Series:
        """Compute trend signal based on moving average crossover.

        Parameters
        ----------
        prices : pd.Series
            Price series
        short_window : int
            Short moving average window (default: 20)
        long_window : int
            Long moving average window (default: 50)

        Returns
        -------
        pd.Series
            Trend signal: 1 for bullish, -1 for bearish, 0 for neutral
        """
        logger.debug(
            "Computing trend signal",
            short_window=short_window,
            long_window=long_window,
        )

        if len(prices) < long_window:
            logger.warning(
                "Insufficient data for trend calculation",
                required=long_window,
                available=len(prices),
            )
            return pd.Series(dtype=float)

        # Import here to avoid circular dependencies
        from analyze.technical.indicators import TechnicalIndicators

        short_ma = TechnicalIndicators.calculate_sma(prices, short_window)
        long_ma = TechnicalIndicators.calculate_sma(prices, long_window)

        # Generate trend signal
        signal = pd.Series(0, index=prices.index, dtype=float)
        signal[short_ma > long_ma] = 1.0
        signal[short_ma < long_ma] = -1.0

        logger.debug("Trend signal computed")

        return signal

    def compute_rsi_signal(
        self,
        prices: pd.Series,
        period: int = 14,
        overbought: float = 70.0,
        oversold: float = 30.0,
    ) -> pd.Series:
        """Compute RSI-based signal.

        Parameters
        ----------
        prices : pd.Series
            Price series
        period : int
            RSI period (default: 14)
        overbought : float
            Overbought threshold (default: 70)
        oversold : float
            Oversold threshold (default: 30)

        Returns
        -------
        pd.Series
            RSI signal: 1 for oversold (buy), -1 for overbought (sell), 0 for neutral
        """
        logger.debug(
            "Computing RSI signal",
            period=period,
            overbought=overbought,
            oversold=oversold,
        )

        if len(prices) < period:
            logger.warning(
                "Insufficient data for RSI calculation",
                required=period,
                available=len(prices),
            )
            return pd.Series(dtype=float)

        # Import here to avoid circular dependencies
        from analyze.technical.indicators import TechnicalIndicators

        rsi = TechnicalIndicators.calculate_rsi(prices, period=period)

        # Generate signal
        signal = pd.Series(0.0, index=prices.index, dtype=float)
        signal[rsi < oversold] = 1.0  # Buy signal
        signal[rsi > overbought] = -1.0  # Sell signal

        logger.debug("RSI signal computed")

        return signal


def create_signal_provider() -> TechnicalSignalProvider:
    """Factory function to create a TechnicalSignalProvider.

    Returns
    -------
    TechnicalSignalProvider
        A new TechnicalSignalProvider instance

    Examples
    --------
    >>> provider = create_signal_provider()
    >>> isinstance(provider, TechnicalSignalProvider)
    True
    """
    logger.debug("Creating TechnicalSignalProvider via factory function")
    return TechnicalSignalProvider()


__all__ = [
    "TechnicalSignalProvider",
    "create_signal_provider",
]

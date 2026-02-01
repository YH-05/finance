"""Analyze package integration for factor analysis.

This module provides integration between the analyze package's technical
analysis functions and the factor package's factor calculations.

Classes
-------
EnhancedFactorAnalyzer
    Factor analyzer enhanced with analyze package capabilities

Functions
---------
calculate_factor_with_indicators
    Calculate factor values alongside technical indicators
create_enhanced_analyzer
    Factory function to create an EnhancedFactorAnalyzer

Examples
--------
>>> from factor.integration.analyze_integration import create_enhanced_analyzer
>>> analyzer = create_enhanced_analyzer()
>>> indicators = analyzer.compute_indicators(price_data)
"""

from typing import TYPE_CHECKING, Any, cast

import pandas as pd
from analyze.statistics.correlation import calculate_correlation
from analyze.technical.indicators import TechnicalIndicators
from utils_core.logging import get_logger

if TYPE_CHECKING:
    from analyze.statistics.types import CorrelationMethod

logger = get_logger(__name__)


class EnhancedFactorAnalyzer:
    """Factor analyzer enhanced with analyze package capabilities.

    This class combines factor analysis with technical indicators from
    the analyze package, providing a unified interface for factor
    research and validation.

    Examples
    --------
    >>> analyzer = EnhancedFactorAnalyzer()
    >>> indicators = analyzer.compute_indicators(price_data)
    >>> rsi = analyzer.compute_rsi(close_prices)
    """

    def __init__(self) -> None:
        """Initialize EnhancedFactorAnalyzer."""
        logger.debug("Initializing EnhancedFactorAnalyzer")
        logger.info("EnhancedFactorAnalyzer initialized")

    def compute_indicators(
        self,
        data: pd.DataFrame,
        sma_windows: list[int] | None = None,
        ema_windows: list[int] | None = None,
        volatility_window: int = 20,
    ) -> dict[str, Any]:
        """Compute technical indicators for price data.

        Parameters
        ----------
        data : pd.DataFrame
            Price data with OHLCV columns
        sma_windows : list[int] | None
            Windows for SMA calculation (default: [20, 50])
        ema_windows : list[int] | None
            Windows for EMA calculation (default: [12, 26])
        volatility_window : int
            Window for volatility calculation (default: 20)

        Returns
        -------
        dict[str, Any]
            Dictionary of indicator name to pd.Series

        Examples
        --------
        >>> analyzer = EnhancedFactorAnalyzer()
        >>> indicators = analyzer.compute_indicators(price_data)
        >>> "returns" in indicators
        True
        """
        logger.debug(
            "Computing indicators",
            columns=list(data.columns) if not data.empty else [],
            rows=len(data),
        )

        if data.empty:
            logger.warning("Empty DataFrame provided")
            return {}

        if sma_windows is None:
            sma_windows = [20, 50]

        if ema_windows is None:
            ema_windows = [12, 26]

        # Get close prices
        if "close" in data.columns:
            close_prices_raw = data["close"]
        elif "Close" in data.columns:
            close_prices_raw = data["Close"]
        else:
            logger.warning("No close column found in data")
            return {}

        # Ensure we have a Series
        close_prices: pd.Series = (
            close_prices_raw
            if isinstance(close_prices_raw, pd.Series)
            else close_prices_raw.iloc[:, 0]
            if hasattr(close_prices_raw, "iloc")
            else pd.Series(close_prices_raw)
        )

        # Use analyze package's TechnicalIndicators
        result: dict[str, Any] = {}

        # Returns
        result["returns"] = TechnicalIndicators.calculate_returns(close_prices)

        # SMAs
        for window in sma_windows:
            if len(close_prices) >= window:
                result[f"sma_{window}"] = TechnicalIndicators.calculate_sma(
                    close_prices, window
                )

        # EMAs
        for window in ema_windows:
            if len(close_prices) >= window:
                result[f"ema_{window}"] = TechnicalIndicators.calculate_ema(
                    close_prices, window
                )

        # Volatility
        if len(close_prices) >= volatility_window:
            returns = result.get("returns")
            if returns is not None and isinstance(returns, pd.Series):
                result["volatility"] = TechnicalIndicators.calculate_volatility(
                    returns, window=volatility_window
                )

        logger.info(
            "Indicators computed",
            indicator_count=len(result),
            indicators=list(result.keys()),
        )

        return result

    def compute_rsi(
        self,
        prices: pd.Series,
        period: int = 14,
    ) -> pd.Series:
        """Compute RSI (Relative Strength Index) for price series.

        Parameters
        ----------
        prices : pd.Series
            Price series (typically close prices)
        period : int
            RSI period (default: 14)

        Returns
        -------
        pd.Series
            RSI values in range [0, 100]

        Examples
        --------
        >>> analyzer = EnhancedFactorAnalyzer()
        >>> rsi = analyzer.compute_rsi(close_prices)
        >>> rsi.iloc[-1]
        55.5
        """
        logger.debug(
            "Computing RSI",
            period=period,
            data_points=len(prices),
        )

        if prices.empty:
            logger.warning("Empty price series provided")
            return pd.Series(dtype=float)

        result = TechnicalIndicators.calculate_rsi(prices, period=period)

        logger.debug(
            "RSI computed",
            valid_values=int(result.notna().sum()),
        )

        return result

    def compute_correlation(
        self,
        series_a: pd.Series,
        series_b: pd.Series,
        method: str = "pearson",
    ) -> float:
        """Compute correlation between two series.

        Parameters
        ----------
        series_a : pd.Series
            First data series
        series_b : pd.Series
            Second data series
        method : str
            Correlation method ("pearson", "spearman", "kendall")

        Returns
        -------
        float
            Correlation coefficient in range [-1, 1]

        Examples
        --------
        >>> analyzer = EnhancedFactorAnalyzer()
        >>> corr = analyzer.compute_correlation(factor_a, factor_b)
        >>> -1 <= corr <= 1
        True
        """
        logger.debug(
            "Computing correlation",
            method=method,
            series_a_len=len(series_a),
            series_b_len=len(series_b),
        )

        if series_a.empty or series_b.empty:
            logger.warning("Empty series provided for correlation")
            return float("nan")

        # Align series lengths
        min_len = min(len(series_a), len(series_b))
        series_a_aligned = series_a.iloc[:min_len].reset_index(drop=True)
        series_b_aligned = series_b.iloc[:min_len].reset_index(drop=True)

        # Use analyze package's correlation function
        # The type is a Literal, but we cast for flexibility
        method_typed = cast("CorrelationMethod", method)
        result = calculate_correlation(series_a_aligned, series_b_aligned, method_typed)

        logger.debug(
            "Correlation computed",
            correlation=result,
            method=method,
        )

        return result

    def compute_volatility(
        self,
        prices: pd.Series,
        window: int = 20,
        annualize: bool = True,
    ) -> pd.Series:
        """Compute rolling volatility for price series.

        Parameters
        ----------
        prices : pd.Series
            Price series
        window : int
            Rolling window (default: 20)
        annualize : bool
            Whether to annualize (default: True)

        Returns
        -------
        pd.Series
            Volatility values

        Examples
        --------
        >>> analyzer = EnhancedFactorAnalyzer()
        >>> vol = analyzer.compute_volatility(close_prices)
        """
        logger.debug(
            "Computing volatility",
            window=window,
            annualize=annualize,
            data_points=len(prices),
        )

        if prices.empty:
            logger.warning("Empty price series provided")
            return pd.Series(dtype=float)

        # First calculate returns
        returns = TechnicalIndicators.calculate_returns(prices)

        # Then calculate volatility
        result = TechnicalIndicators.calculate_volatility(
            returns, window=window, annualize=annualize
        )

        logger.debug(
            "Volatility computed",
            valid_values=int(result.notna().sum()),
        )

        return result


def calculate_factor_with_indicators(
    prices: pd.Series,
    factor_window: int = 20,
    include_rsi: bool = True,
    include_volatility: bool = True,
) -> dict[str, Any]:
    """Calculate factor values alongside technical indicators.

    This function provides a convenient way to compute both factor
    values (momentum, etc.) and supporting technical indicators in
    a single call.

    Parameters
    ----------
    prices : pd.Series
        Price series
    factor_window : int
        Window for factor calculation (default: 20)
    include_rsi : bool
        Whether to include RSI (default: True)
    include_volatility : bool
        Whether to include volatility (default: True)

    Returns
    -------
    dict[str, Any]
        Dictionary containing factor values and indicators

    Examples
    --------
    >>> result = calculate_factor_with_indicators(close_prices)
    >>> "momentum" in result or "factor_value" in result
    True
    """
    logger.debug(
        "Calculating factor with indicators",
        factor_window=factor_window,
        include_rsi=include_rsi,
        include_volatility=include_volatility,
    )

    if prices.empty:
        logger.warning("Empty price series provided")
        return {}

    result: dict[str, Any] = {}

    # Compute momentum (returns over window)
    if len(prices) >= factor_window:
        result["momentum"] = prices.pct_change(periods=factor_window)
        result["factor_value"] = result["momentum"]

    # Compute returns
    result["returns"] = TechnicalIndicators.calculate_returns(prices)

    # Optionally include RSI
    if include_rsi and len(prices) >= 14:
        result["rsi"] = TechnicalIndicators.calculate_rsi(prices)

    # Optionally include volatility
    if include_volatility and len(prices) >= factor_window:
        returns = result.get("returns")
        if returns is not None and isinstance(returns, pd.Series):
            result["volatility"] = TechnicalIndicators.calculate_volatility(
                returns, window=factor_window
            )

    logger.info(
        "Factor with indicators calculated",
        result_keys=list(result.keys()),
    )

    return result


def create_enhanced_analyzer() -> EnhancedFactorAnalyzer:
    """Factory function to create an EnhancedFactorAnalyzer.

    Returns
    -------
    EnhancedFactorAnalyzer
        A new EnhancedFactorAnalyzer instance

    Examples
    --------
    >>> analyzer = create_enhanced_analyzer()
    >>> isinstance(analyzer, EnhancedFactorAnalyzer)
    True
    """
    logger.debug("Creating EnhancedFactorAnalyzer via factory function")
    return EnhancedFactorAnalyzer()


__all__ = [
    "EnhancedFactorAnalyzer",
    "calculate_factor_with_indicators",
    "create_enhanced_analyzer",
]

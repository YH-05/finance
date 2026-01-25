"""Correlation analysis functions for statistical analysis.

This module provides functions and classes for calculating correlations
and beta values between data series.

Classes
-------
CorrelationAnalyzer : Comprehensive correlation analysis class

Functions
---------
calculate_correlation : Calculate pairwise correlation coefficient
calculate_correlation_matrix : Calculate correlation matrix for multiple series
calculate_rolling_correlation : Calculate rolling correlation
calculate_beta : Calculate beta coefficient against benchmark
calculate_rolling_beta : Calculate rolling beta coefficient

Examples
--------
>>> import pandas as pd
>>> a = pd.Series([1, 2, 3, 4, 5])
>>> b = pd.Series([2, 4, 6, 8, 10])
>>> calculate_correlation(a, b)
1.0
"""

from typing import cast

import numpy as np
import pandas as pd

from database.utils.logging_config import get_logger

from .types import CorrelationMethod, CorrelationResult

logger = get_logger(__name__)


def calculate_correlation(
    series_a: pd.Series,
    series_b: pd.Series,
    method: CorrelationMethod = "pearson",
) -> float:
    """Calculate correlation coefficient between two series.

    Parameters
    ----------
    series_a : pd.Series
        First data series.
    series_b : pd.Series
        Second data series.
    method : {"pearson", "spearman", "kendall"}, default="pearson"
        Correlation method to use.

    Returns
    -------
    float
        Correlation coefficient between -1 and 1.
        Returns NaN if insufficient data.

    Raises
    ------
    ValueError
        If series have different lengths or method is invalid.

    Examples
    --------
    >>> import pandas as pd
    >>> a = pd.Series([1, 2, 3, 4, 5])
    >>> b = pd.Series([2, 4, 6, 8, 10])
    >>> calculate_correlation(a, b)
    1.0
    """
    logger.debug(
        "Calculating correlation",
        method=method,
        series_a_len=len(series_a),
        series_b_len=len(series_b),
    )

    if len(series_a) != len(series_b):
        logger.error(
            "Series length mismatch",
            series_a_len=len(series_a),
            series_b_len=len(series_b),
        )
        raise ValueError(
            f"Series must have equal length: {len(series_a)} != {len(series_b)}"
        )

    valid_methods: list[CorrelationMethod] = ["pearson", "spearman", "kendall"]
    if method not in valid_methods:
        logger.error("Invalid correlation method", method=method)
        raise ValueError(f"Invalid method '{method}'. Must be one of: {valid_methods}")

    if series_a.empty or series_b.empty:
        logger.warning("Empty series provided")
        return float("nan")

    # Drop NaN values for correlation calculation
    combined = pd.DataFrame({"a": series_a, "b": series_b}).dropna()

    if len(combined) < 2:
        logger.warning(
            "Insufficient data points for correlation",
            valid_points=len(combined),
        )
        return float("nan")

    series_a_clean = cast("pd.Series", combined["a"])
    series_b_clean = cast("pd.Series", combined["b"])
    correlation = series_a_clean.corr(series_b_clean, method=method)

    logger.debug(
        "Correlation calculated",
        method=method,
        correlation=correlation,
        data_points=len(combined),
    )

    return float(correlation)


def calculate_correlation_matrix(
    data: pd.DataFrame,
    method: CorrelationMethod = "pearson",
) -> pd.DataFrame:
    """Calculate correlation matrix for multiple series.

    Parameters
    ----------
    data : pd.DataFrame
        DataFrame with each column representing a different series.
    method : {"pearson", "spearman", "kendall"}, default="pearson"
        Correlation method to use.

    Returns
    -------
    pd.DataFrame
        Symmetric correlation matrix with diagonal elements equal to 1.0.

    Raises
    ------
    ValueError
        If data has fewer than 2 columns or method is invalid.

    Examples
    --------
    >>> import pandas as pd
    >>> data = pd.DataFrame({
    ...     "A": [1, 2, 3, 4],
    ...     "B": [2, 4, 6, 8],
    ...     "C": [4, 3, 2, 1],
    ... })
    >>> matrix = calculate_correlation_matrix(data)
    >>> matrix.loc["A", "B"]
    1.0
    """
    logger.debug(
        "Calculating correlation matrix",
        method=method,
        columns=list(data.columns),
        rows=len(data),
    )

    if data.shape[1] < 2:
        logger.error("Insufficient columns for matrix", columns=data.shape[1])
        raise ValueError(f"Data must have at least 2 columns, got {data.shape[1]}")

    valid_methods: list[CorrelationMethod] = ["pearson", "spearman", "kendall"]
    if method not in valid_methods:
        logger.error("Invalid correlation method", method=method)
        raise ValueError(f"Invalid method '{method}'. Must be one of: {valid_methods}")

    correlation_matrix = data.corr(method=method)

    logger.info(
        "Correlation matrix calculated",
        method=method,
        shape=correlation_matrix.shape,
    )

    return correlation_matrix


def calculate_rolling_correlation(
    series_a: pd.Series,
    series_b: pd.Series,
    window: int,
    min_periods: int | None = None,
) -> pd.Series:
    """Calculate rolling correlation between two series.

    Parameters
    ----------
    series_a : pd.Series
        First data series.
    series_b : pd.Series
        Second data series.
    window : int
        Rolling window size.
    min_periods : int | None, default=None
        Minimum observations required. Defaults to window size.

    Returns
    -------
    pd.Series
        Rolling correlation values. Earlier values will be NaN.

    Raises
    ------
    ValueError
        If series have different lengths or window/min_periods is invalid.

    Examples
    --------
    >>> import pandas as pd
    >>> a = pd.Series([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
    >>> b = pd.Series([2, 4, 6, 8, 10, 12, 14, 16, 18, 20])
    >>> rolling = calculate_rolling_correlation(a, b, window=5)
    >>> rolling.iloc[-1]
    1.0
    """
    logger.debug(
        "Calculating rolling correlation",
        window=window,
        min_periods=min_periods,
        series_a_len=len(series_a),
        series_b_len=len(series_b),
    )

    if len(series_a) != len(series_b):
        logger.error(
            "Series length mismatch",
            series_a_len=len(series_a),
            series_b_len=len(series_b),
        )
        raise ValueError(
            f"Series must have equal length: {len(series_a)} != {len(series_b)}"
        )

    if window < 2:
        logger.error("Invalid window size", window=window)
        raise ValueError(f"Window must be at least 2, got {window}")

    if min_periods is None:
        min_periods = window

    if min_periods < 2:
        logger.error("Invalid min_periods", min_periods=min_periods)
        raise ValueError(f"min_periods must be at least 2, got {min_periods}")

    result = cast(
        "pd.Series",
        series_a.rolling(window=window, min_periods=min_periods).corr(series_b),
    )

    logger.debug(
        "Rolling correlation calculated",
        window=window,
        valid_values=result.notna().sum(),
        nan_values=result.isna().sum(),
    )

    return result


def calculate_beta(
    returns: pd.Series,
    benchmark_returns: pd.Series,
) -> float:
    """Calculate beta coefficient against a benchmark.

    Beta measures the sensitivity of an asset's returns to benchmark returns.
    Beta > 1 indicates higher volatility than the benchmark.
    Beta < 1 indicates lower volatility than the benchmark.

    Parameters
    ----------
    returns : pd.Series
        Asset return series.
    benchmark_returns : pd.Series
        Benchmark return series (e.g., SPY returns).

    Returns
    -------
    float
        Beta coefficient. Returns NaN if insufficient data.

    Raises
    ------
    ValueError
        If series have different lengths.

    Examples
    --------
    >>> import pandas as pd
    >>> asset = pd.Series([0.01, 0.02, -0.01, 0.03, 0.01])
    >>> benchmark = pd.Series([0.005, 0.01, -0.005, 0.015, 0.005])
    >>> beta = calculate_beta(asset, benchmark)
    >>> beta  # Asset moves 2x the benchmark
    2.0
    """
    logger.debug(
        "Calculating beta",
        returns_len=len(returns),
        benchmark_len=len(benchmark_returns),
    )

    if len(returns) != len(benchmark_returns):
        logger.error(
            "Series length mismatch",
            returns_len=len(returns),
            benchmark_len=len(benchmark_returns),
        )
        raise ValueError(
            f"Series must have equal length: {len(returns)} != {len(benchmark_returns)}"
        )

    # Drop NaN values
    combined = pd.DataFrame({"asset": returns, "benchmark": benchmark_returns}).dropna()

    if len(combined) < 2:
        logger.warning(
            "Insufficient data points for beta calculation",
            valid_points=len(combined),
        )
        return float("nan")

    # Beta = Cov(asset, benchmark) / Var(benchmark)
    asset_returns = cast("pd.Series", combined["asset"])
    benchmark_returns_clean = cast("pd.Series", combined["benchmark"])
    covariance = asset_returns.cov(benchmark_returns_clean)
    variance = benchmark_returns_clean.var()

    if variance == 0:
        logger.warning("Benchmark variance is zero, cannot calculate beta")
        return float("nan")

    beta = covariance / variance

    logger.debug(
        "Beta calculated",
        beta=beta,
        covariance=covariance,
        variance=variance,
        data_points=len(combined),
    )

    return cast("float", beta)


def calculate_rolling_beta(
    returns: pd.Series,
    benchmark_returns: pd.Series,
    window: int,
    min_periods: int | None = None,
) -> pd.Series:
    """Calculate rolling beta coefficient against a benchmark.

    Parameters
    ----------
    returns : pd.Series
        Asset return series.
    benchmark_returns : pd.Series
        Benchmark return series.
    window : int
        Rolling window size.
    min_periods : int | None, default=None
        Minimum observations required. Defaults to window size.

    Returns
    -------
    pd.Series
        Rolling beta values. Earlier values will be NaN.

    Raises
    ------
    ValueError
        If series have different lengths or window is invalid.

    Examples
    --------
    >>> import pandas as pd
    >>> asset = pd.Series([0.01, 0.02, -0.01, 0.03, 0.01] * 10)
    >>> benchmark = pd.Series([0.005, 0.01, -0.005, 0.015, 0.005] * 10)
    >>> rolling_beta = calculate_rolling_beta(asset, benchmark, window=20)
    """
    logger.debug(
        "Calculating rolling beta",
        window=window,
        min_periods=min_periods,
        returns_len=len(returns),
        benchmark_len=len(benchmark_returns),
    )

    if len(returns) != len(benchmark_returns):
        logger.error(
            "Series length mismatch",
            returns_len=len(returns),
            benchmark_len=len(benchmark_returns),
        )
        raise ValueError(
            f"Series must have equal length: {len(returns)} != {len(benchmark_returns)}"
        )

    if window < 2:
        logger.error("Invalid window size", window=window)
        raise ValueError(f"Window must be at least 2, got {window}")

    if min_periods is None:
        min_periods = window

    if min_periods < 2:
        logger.error("Invalid min_periods", min_periods=min_periods)
        raise ValueError(f"min_periods must be at least 2, got {min_periods}")

    # Calculate rolling covariance and variance
    rolling_cov = cast(
        "pd.Series",
        returns.rolling(window=window, min_periods=min_periods).cov(benchmark_returns),
    )
    rolling_var = cast(
        "pd.Series",
        benchmark_returns.rolling(window=window, min_periods=min_periods).var(),
    )

    # Handle zero variance
    rolling_var = rolling_var.replace(0, np.nan)

    result = cast("pd.Series", rolling_cov / rolling_var)

    logger.debug(
        "Rolling beta calculated",
        window=window,
        valid_values=result.notna().sum(),
        nan_values=result.isna().sum(),
    )

    return result


class CorrelationAnalyzer:
    """Analyzer for correlation and beta calculations.

    Provides both static methods for individual calculations and
    an analyze method for comprehensive correlation analysis.

    Examples
    --------
    >>> import pandas as pd
    >>> data = pd.DataFrame({
    ...     "AAPL": [0.01, 0.02, -0.01, 0.03],
    ...     "GOOGL": [0.015, 0.018, -0.008, 0.025],
    ... })
    >>> analyzer = CorrelationAnalyzer()
    >>> result = analyzer.analyze(data, period="1Y")
    >>> result.symbols
    ['AAPL', 'GOOGL']
    """

    @staticmethod
    def calculate_correlation(
        series_a: pd.Series,
        series_b: pd.Series,
        method: CorrelationMethod = "pearson",
    ) -> float:
        """Calculate correlation coefficient between two series.

        Parameters
        ----------
        series_a : pd.Series
            First data series.
        series_b : pd.Series
            Second data series.
        method : {"pearson", "spearman", "kendall"}, default="pearson"
            Correlation method to use.

        Returns
        -------
        float
            Correlation coefficient between -1 and 1.

        See Also
        --------
        calculate_correlation : Module-level function with same behavior.
        """
        return calculate_correlation(series_a, series_b, method)

    @staticmethod
    def calculate_correlation_matrix(
        data: pd.DataFrame,
        method: CorrelationMethod = "pearson",
    ) -> pd.DataFrame:
        """Calculate correlation matrix for multiple series.

        Parameters
        ----------
        data : pd.DataFrame
            DataFrame with each column representing a different series.
        method : {"pearson", "spearman", "kendall"}, default="pearson"
            Correlation method to use.

        Returns
        -------
        pd.DataFrame
            Symmetric correlation matrix.

        See Also
        --------
        calculate_correlation_matrix : Module-level function with same behavior.
        """
        return calculate_correlation_matrix(data, method)

    @staticmethod
    def calculate_rolling_correlation(
        series_a: pd.Series,
        series_b: pd.Series,
        window: int,
        min_periods: int | None = None,
    ) -> pd.Series:
        """Calculate rolling correlation between two series.

        Parameters
        ----------
        series_a : pd.Series
            First data series.
        series_b : pd.Series
            Second data series.
        window : int
            Rolling window size.
        min_periods : int | None, default=None
            Minimum observations required.

        Returns
        -------
        pd.Series
            Rolling correlation values.

        See Also
        --------
        calculate_rolling_correlation : Module-level function with same behavior.
        """
        return calculate_rolling_correlation(series_a, series_b, window, min_periods)

    @staticmethod
    def calculate_beta(
        returns: pd.Series,
        benchmark_returns: pd.Series,
    ) -> float:
        """Calculate beta coefficient against a benchmark.

        Parameters
        ----------
        returns : pd.Series
            Asset return series.
        benchmark_returns : pd.Series
            Benchmark return series.

        Returns
        -------
        float
            Beta coefficient.

        See Also
        --------
        calculate_beta : Module-level function with same behavior.
        """
        return calculate_beta(returns, benchmark_returns)

    @staticmethod
    def calculate_rolling_beta(
        returns: pd.Series,
        benchmark_returns: pd.Series,
        window: int,
        min_periods: int | None = None,
    ) -> pd.Series:
        """Calculate rolling beta coefficient against a benchmark.

        Parameters
        ----------
        returns : pd.Series
            Asset return series.
        benchmark_returns : pd.Series
            Benchmark return series.
        window : int
            Rolling window size.
        min_periods : int | None, default=None
            Minimum observations required.

        Returns
        -------
        pd.Series
            Rolling beta values.

        See Also
        --------
        calculate_rolling_beta : Module-level function with same behavior.
        """
        return calculate_rolling_beta(returns, benchmark_returns, window, min_periods)

    def analyze(
        self,
        data: pd.DataFrame,
        method: CorrelationMethod = "pearson",
        period: str = "",
    ) -> CorrelationResult:
        """Perform correlation analysis and return structured result.

        Parameters
        ----------
        data : pd.DataFrame
            DataFrame with columns for each symbol's data.
        method : {"pearson", "spearman", "kendall"}, default="pearson"
            Correlation method to use.
        period : str, default=""
            Description of the analysis period
            (e.g., "1Y", "2024-01-01 to 2024-12-31").

        Returns
        -------
        CorrelationResult
            Structured result containing correlation matrix and metadata.

        Examples
        --------
        >>> import pandas as pd
        >>> data = pd.DataFrame({
        ...     "AAPL": [0.01, 0.02, -0.01, 0.03],
        ...     "GOOGL": [0.015, 0.018, -0.008, 0.025],
        ... })
        >>> analyzer = CorrelationAnalyzer()
        >>> result = analyzer.analyze(data, period="1Y")
        >>> result.symbols
        ['AAPL', 'GOOGL']
        """
        logger.info(
            "Starting correlation analysis",
            symbols=list(data.columns),
            method=method,
            period=period,
            data_points=len(data),
        )

        correlation_matrix = self.calculate_correlation_matrix(data, method=method)

        result = CorrelationResult(
            symbols=list(data.columns),
            correlation_matrix=correlation_matrix,
            period=period,
            method=method,
        )

        logger.info(
            "Correlation analysis completed",
            symbols=result.symbols,
            method=result.method,
        )

        return result


__all__ = [
    "CorrelationAnalyzer",
    "CorrelationResult",
    "calculate_beta",
    "calculate_correlation",
    "calculate_correlation_matrix",
    "calculate_rolling_beta",
    "calculate_rolling_correlation",
]

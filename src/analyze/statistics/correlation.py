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

from typing import Any, cast

import numpy as np
import pandas as pd

from utils_core.logging import get_logger

from .base import StatisticalAnalyzer
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


class RollingCorrelationAnalyzer(StatisticalAnalyzer):
    """Analyzer for calculating rolling correlation between columns.

    This class inherits from StatisticalAnalyzer and provides functionality
    to calculate rolling correlation coefficients between a target column
    and other columns in a DataFrame.

    Rolling correlation is useful for analyzing how the relationship between
    assets changes over time, which is important for portfolio management
    and risk assessment.

    Parameters
    ----------
    window : int, default=252
        Rolling window size in observations. Default is 252, representing
        approximately one trading year.
    min_periods : int, default=30
        Minimum number of observations required to calculate correlation.
        Default is 30 observations.

    Attributes
    ----------
    window : int
        The rolling window size.
    min_periods : int
        The minimum number of observations required.

    Examples
    --------
    >>> import pandas as pd
    >>> df = pd.DataFrame({
    ...     "AAPL": [100, 101, 102, 103, 104, 105],
    ...     "MSFT": [200, 202, 204, 206, 208, 210],
    ...     "SPY": [400, 402, 404, 406, 408, 410],
    ... })
    >>> analyzer = RollingCorrelationAnalyzer(window=5, min_periods=3)
    >>> result = analyzer.analyze(df, target_column="SPY")
    >>> result.columns.tolist()
    ['AAPL', 'MSFT']
    """

    def __init__(self, window: int = 252, min_periods: int = 30) -> None:
        """Initialize RollingCorrelationAnalyzer.

        Parameters
        ----------
        window : int, default=252
            Rolling window size in observations.
        min_periods : int, default=30
            Minimum number of observations required to calculate correlation.

        Examples
        --------
        >>> analyzer = RollingCorrelationAnalyzer()
        >>> analyzer.window
        252
        >>> analyzer.min_periods
        30
        >>> analyzer = RollingCorrelationAnalyzer(window=60, min_periods=10)
        >>> analyzer.window
        60
        """
        self._window = window
        self._min_periods = min_periods
        logger.debug(
            "RollingCorrelationAnalyzer initialized",
            window=window,
            min_periods=min_periods,
        )

    @property
    def window(self) -> int:
        """Return the rolling window size.

        Returns
        -------
        int
            The rolling window size in observations.
        """
        return self._window

    @property
    def min_periods(self) -> int:
        """Return the minimum number of periods.

        Returns
        -------
        int
            The minimum number of observations required.
        """
        return self._min_periods

    def validate_input(self, df: pd.DataFrame) -> bool:
        """Validate the input DataFrame for rolling correlation calculation.

        This method checks that the DataFrame meets the requirements for
        rolling correlation calculation:
        - DataFrame is not empty
        - Has at least 2 numeric columns
        - Has enough rows for min_periods

        Parameters
        ----------
        df : pd.DataFrame
            The DataFrame to validate.

        Returns
        -------
        bool
            True if the data is valid for calculation, False otherwise.

        Examples
        --------
        >>> analyzer = RollingCorrelationAnalyzer(window=5, min_periods=3)
        >>> df = pd.DataFrame({"A": [1, 2, 3, 4, 5], "B": [2, 4, 6, 8, 10]})
        >>> analyzer.validate_input(df)
        True
        >>> analyzer.validate_input(pd.DataFrame())
        False
        """
        logger.debug(
            "Validating input for rolling correlation",
            rows=len(df) if not df.empty else 0,
            columns=list(df.columns) if not df.empty else [],
        )

        # Check if DataFrame is empty
        if df.empty:
            logger.warning("Empty DataFrame provided")
            return False

        # Check for at least 2 numeric columns
        numeric_cols = df.select_dtypes(include=["number"]).columns
        if len(numeric_cols) < 2:
            logger.warning(
                "Insufficient numeric columns for correlation",
                numeric_columns=len(numeric_cols),
            )
            return False

        # Check for sufficient rows
        if len(df) < self._min_periods:
            logger.warning(
                "Insufficient rows for min_periods",
                rows=len(df),
                min_periods=self._min_periods,
            )
            return False

        logger.debug("Input validation passed")
        return True

    def calculate(self, df: pd.DataFrame, **kwargs: Any) -> pd.DataFrame:
        """Calculate rolling correlation with a target column.

        This method calculates the rolling correlation coefficient between
        each numeric column in the DataFrame and the specified target column.

        Parameters
        ----------
        df : pd.DataFrame
            The input DataFrame with time series data. Each column represents
            a different asset or series.
        **kwargs : Any
            Additional keyword arguments. Required:
            - target_column (str): The column name to calculate correlations against.

        Returns
        -------
        pd.DataFrame
            DataFrame containing rolling correlation values for each column
            against the target column. The target column is excluded from results.
            Earlier values will be NaN until min_periods is reached.

        Raises
        ------
        ValueError
            If target_column is not provided or not found in the DataFrame.

        Examples
        --------
        >>> import pandas as pd
        >>> df = pd.DataFrame({
        ...     "AAPL": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        ...     "SPY": [2, 4, 6, 8, 10, 12, 14, 16, 18, 20],
        ... })
        >>> analyzer = RollingCorrelationAnalyzer(window=5, min_periods=3)
        >>> result = analyzer.calculate(df, target_column="SPY")
        >>> result["AAPL"].iloc[-1]  # Perfect correlation
        1.0
        """
        target_column = kwargs.get("target_column")

        if target_column is None:
            msg = "target_column is required"
            logger.error(msg)
            raise ValueError(msg)

        if target_column not in df.columns:
            msg = f"target_column '{target_column}' not found in DataFrame"
            logger.error(msg, available_columns=list(df.columns))
            raise ValueError(msg)

        logger.info(
            "Calculating rolling correlation",
            target_column=target_column,
            window=self._window,
            min_periods=self._min_periods,
            input_rows=len(df),
            input_columns=len(df.columns),
        )

        # Get target series
        target = df[target_column]

        # Get numeric columns excluding target
        numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
        other_cols = [col for col in numeric_cols if col != target_column]

        # Calculate rolling correlation for each column
        result_data: dict[str, pd.Series] = {}
        for col in other_cols:
            rolling_corr = cast(
                "pd.Series",
                df[col]
                .rolling(window=self._window, min_periods=self._min_periods)
                .corr(target),
            )
            result_data[col] = rolling_corr
            logger.debug(
                "Rolling correlation calculated",
                column=col,
                target_column=target_column,
                valid_values=rolling_corr.notna().sum(),
            )

        result = pd.DataFrame(result_data, index=df.index)

        logger.info(
            "Rolling correlation calculation completed",
            output_columns=list(result.columns),
            output_rows=len(result),
        )

        return result


__all__ = [
    "CorrelationAnalyzer",
    "CorrelationResult",
    "RollingCorrelationAnalyzer",
    "calculate_beta",
    "calculate_correlation",
    "calculate_correlation_matrix",
    "calculate_rolling_beta",
    "calculate_rolling_correlation",
]

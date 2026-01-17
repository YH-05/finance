"""IC/IR analysis module for factor validation.

This module provides the ICAnalyzer class for computing Information Coefficient (IC)
and Information Ratio (IR) to evaluate factor predictive power.
"""

from dataclasses import dataclass
from typing import Any, Literal

import numpy as np
import pandas as pd
from scipy import stats

from factor.errors import InsufficientDataError, ValidationError

# Minimum number of symbols required for IC calculation
MIN_SYMBOLS_FOR_IC = 5


def _get_logger() -> Any:
    """Get logger with lazy initialization to avoid circular imports.

    Returns
    -------
    Any
        Logger instance
    """
    try:
        from factor.utils.logging_config import get_logger

        return get_logger(__name__, module="ic_analyzer")
    except ImportError:
        import logging

        return logging.getLogger(__name__)


logger: Any = _get_logger()


@dataclass
class ICResult:
    """Result of IC/IR analysis.

    Parameters
    ----------
    ic_series : pd.Series
        Time series of IC values (index: date)
    mean_ic : float
        Mean IC across all periods
    std_ic : float
        Standard deviation of IC
    ir : float
        Information Ratio (mean_ic / std_ic)
    t_stat : float
        t-statistic for testing IC != 0
    p_value : float
        p-value for t-test
    method : str
        Correlation method used ("spearman" or "pearson")
    n_periods : int
        Number of valid periods used in analysis

    Examples
    --------
    >>> result = ICResult(
    ...     ic_series=pd.Series([0.1, 0.2, 0.15]),
    ...     mean_ic=0.15,
    ...     std_ic=0.05,
    ...     ir=3.0,
    ...     t_stat=5.2,
    ...     p_value=0.001,
    ...     method="spearman",
    ...     n_periods=3,
    ... )
    >>> result.ir
    3.0
    """

    ic_series: pd.Series
    mean_ic: float
    std_ic: float
    ir: float
    t_stat: float
    p_value: float
    method: str
    n_periods: int


class ICAnalyzer:
    """IC/IR analyzer for evaluating factor predictive power.

    The Information Coefficient (IC) measures the correlation between
    factor values and forward returns. The Information Ratio (IR) is
    the mean IC divided by its standard deviation, measuring consistency.

    Parameters
    ----------
    method : Literal["spearman", "pearson"], default="spearman"
        Correlation method to use:
        - "spearman": Rank correlation (more robust to outliers)
        - "pearson": Linear correlation

    Attributes
    ----------
    method : str
        The correlation method used

    Examples
    --------
    >>> analyzer = ICAnalyzer(method="spearman")
    >>> result = analyzer.analyze(factor_values, forward_returns)
    >>> print(f"Mean IC: {result.mean_ic:.4f}, IR: {result.ir:.4f}")
    Mean IC: 0.0523, IR: 1.245
    """

    def __init__(
        self,
        method: Literal["spearman", "pearson"] = "spearman",
    ) -> None:
        """Initialize ICAnalyzer with correlation method.

        Parameters
        ----------
        method : Literal["spearman", "pearson"], default="spearman"
            Correlation method to use

        Raises
        ------
        ValidationError
            If an invalid method is specified
        """
        valid_methods = ("spearman", "pearson")
        if method not in valid_methods:
            logger.error(
                "Invalid correlation method",
                method=method,
                valid_methods=valid_methods,
            )
            raise ValidationError(
                f"method must be one of {valid_methods}, got {method!r}",
                field="method",
                value=method,
            )

        self.method = method
        logger.debug(
            "ICAnalyzer initialized",
            method=method,
        )

    def analyze(
        self,
        factor_values: pd.DataFrame,
        forward_returns: pd.DataFrame,
    ) -> ICResult:
        """Analyze IC/IR for factor values and forward returns.

        Parameters
        ----------
        factor_values : pd.DataFrame
            Factor values (index: date, columns: symbols)
        forward_returns : pd.DataFrame
            Forward returns (index: date, columns: symbols)

        Returns
        -------
        ICResult
            Analysis result containing IC series, mean IC, IR, t-stat, p-value

        Raises
        ------
        ValidationError
            If factor_values and forward_returns have no common index or columns
        InsufficientDataError
            If there is insufficient data for IC calculation

        Examples
        --------
        >>> analyzer = ICAnalyzer(method="spearman")
        >>> result = analyzer.analyze(momentum_values, forward_returns)
        >>> print(f"Mean IC: {result.mean_ic:.4f}")
        Mean IC: 0.0523
        """
        logger.debug(
            "Starting IC analysis",
            factor_shape=factor_values.shape,
            return_shape=forward_returns.shape,
            method=self.method,
        )

        # Validate inputs
        self._validate_inputs(factor_values, forward_returns)

        # Compute IC series
        ic_series = self.compute_ic_series(factor_values, forward_returns)

        # Remove NaN values for statistics
        valid_ic = ic_series.dropna()

        if len(valid_ic) == 0:
            logger.error(
                "No valid IC values computed",
                total_periods=len(ic_series),
            )
            raise InsufficientDataError(
                "No valid IC values could be computed",
                required=1,
                available=0,
            )

        # Compute statistics
        mean_ic = float(valid_ic.mean())
        std_ic = float(valid_ic.std())

        # Compute IR (handle zero std case)
        if std_ic == 0 or np.isnan(std_ic):
            ir = float("inf") if mean_ic != 0 else float("nan")
        else:
            ir = mean_ic / std_ic

        # Compute t-statistic and p-value
        n_periods = len(valid_ic)
        if n_periods > 1 and std_ic > 0:
            t_stat = mean_ic / (std_ic / np.sqrt(n_periods))
            # Two-tailed t-test
            p_value = float(2 * (1 - stats.t.cdf(abs(t_stat), df=n_periods - 1)))
        else:
            t_stat = float("nan")
            p_value = float("nan")

        logger.info(
            "IC analysis completed",
            mean_ic=mean_ic,
            std_ic=std_ic,
            ir=ir,
            t_stat=t_stat,
            p_value=p_value,
            n_periods=n_periods,
        )

        return ICResult(
            ic_series=ic_series,
            mean_ic=mean_ic,
            std_ic=std_ic,
            ir=ir,
            t_stat=t_stat,
            p_value=p_value,
            method=self.method,
            n_periods=n_periods,
        )

    def compute_ic_series(
        self,
        factor_values: pd.DataFrame,
        forward_returns: pd.DataFrame,
    ) -> pd.Series:
        """Compute time series of IC values.

        Parameters
        ----------
        factor_values : pd.DataFrame
            Factor values (index: date, columns: symbols)
        forward_returns : pd.DataFrame
            Forward returns (index: date, columns: symbols)

        Returns
        -------
        pd.Series
            IC value for each date (index: date)

        Examples
        --------
        >>> analyzer = ICAnalyzer(method="spearman")
        >>> ic_series = analyzer.compute_ic_series(factor_values, forward_returns)
        >>> ic_series.head()
        2024-01-01    0.052
        2024-01-02    0.078
        ...
        """
        logger.debug(
            "Computing IC series",
            factor_dates=len(factor_values),
            return_dates=len(forward_returns),
        )

        # Find common dates
        common_dates = factor_values.index.intersection(forward_returns.index)
        ic_series = pd.Series(index=common_dates, dtype=float)

        for date in common_dates:
            factors = factor_values.loc[date].dropna()
            returns = forward_returns.loc[date].dropna()

            # Find common symbols
            common_symbols = factors.index.intersection(returns.index)

            if len(common_symbols) < MIN_SYMBOLS_FOR_IC:
                ic_series.loc[date] = float("nan")
                continue

            f = factors.loc[common_symbols]
            r = returns.loc[common_symbols]

            # Check for constant values (would result in undefined correlation)
            if f.std() == 0 or r.std() == 0:
                ic_series.loc[date] = float("nan")
                continue

            # Compute correlation
            if self.method == "spearman":
                result = stats.spearmanr(f, r)
                ic = float(result.statistic)
            else:
                result = stats.pearsonr(f, r)
                ic = float(result.statistic)

            ic_series.loc[date] = ic

        logger.debug(
            "IC series computed",
            total_dates=len(common_dates),
            valid_dates=ic_series.notna().sum(),
        )

        return ic_series

    @staticmethod
    def compute_forward_returns(
        prices: pd.DataFrame,
        periods: int = 1,
    ) -> pd.DataFrame:
        """Compute forward returns from price data.

        Parameters
        ----------
        prices : pd.DataFrame
            Price data (index: date, columns: symbols)
        periods : int, default=1
            Number of periods for forward return calculation

        Returns
        -------
        pd.DataFrame
            Forward returns (index: date, columns: symbols)
            The last `periods` rows will be NaN.

        Examples
        --------
        >>> forward_returns = ICAnalyzer.compute_forward_returns(prices, periods=5)
        >>> forward_returns.head()
        """
        logger.debug(
            "Computing forward returns",
            price_shape=prices.shape,
            periods=periods,
        )

        # Forward return: (P_{t+n} / P_t) - 1
        forward_returns = prices.shift(-periods) / prices - 1

        logger.debug(
            "Forward returns computed",
            shape=forward_returns.shape,
            nan_rows=forward_returns.isna().all(axis=1).sum(),
        )

        return forward_returns

    def _validate_inputs(
        self,
        factor_values: pd.DataFrame,
        forward_returns: pd.DataFrame,
    ) -> None:
        """Validate input DataFrames.

        Parameters
        ----------
        factor_values : pd.DataFrame
            Factor values
        forward_returns : pd.DataFrame
            Forward returns

        Raises
        ------
        InsufficientDataError
            If DataFrames are empty or have insufficient data
        ValidationError
            If DataFrames have no common index or columns
        """
        # Check for empty DataFrames
        if factor_values.empty or forward_returns.empty:
            logger.error(
                "Empty DataFrame provided",
                factor_empty=factor_values.empty,
                return_empty=forward_returns.empty,
            )
            raise InsufficientDataError(
                "factor_values and forward_returns cannot be empty",
                required=1,
                available=0,
            )

        # Check for common index
        common_index = factor_values.index.intersection(forward_returns.index)
        if len(common_index) == 0:
            logger.error(
                "No common dates between factor_values and forward_returns",
                factor_dates=list(factor_values.index[:5]),
                return_dates=list(forward_returns.index[:5]),
            )
            raise ValidationError(
                "factor_values and forward_returns have no common dates",
                field="index",
            )

        # Check for common columns
        common_columns = factor_values.columns.intersection(forward_returns.columns)
        if len(common_columns) == 0:
            logger.error(
                "No common symbols between factor_values and forward_returns",
                factor_symbols=list(factor_values.columns[:5]),
                return_symbols=list(forward_returns.columns[:5]),
            )
            raise ValidationError(
                "factor_values and forward_returns have no common symbols",
                field="columns",
            )

        # Check for minimum symbols
        if len(common_columns) < MIN_SYMBOLS_FOR_IC:
            logger.error(
                "Insufficient symbols for IC calculation",
                available=len(common_columns),
                required=MIN_SYMBOLS_FOR_IC,
            )
            raise InsufficientDataError(
                f"At least {MIN_SYMBOLS_FOR_IC} common symbols required, "
                f"got {len(common_columns)}",
                required=MIN_SYMBOLS_FOR_IC,
                available=len(common_columns),
            )

        logger.debug(
            "Input validation passed",
            common_dates=len(common_index),
            common_symbols=len(common_columns),
        )


__all__ = ["ICAnalyzer", "ICResult"]

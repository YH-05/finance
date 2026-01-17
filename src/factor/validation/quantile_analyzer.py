"""Quantile analysis for factor validation.

This module provides QuantileAnalyzer class for analyzing factor effectiveness
through quantile portfolio construction and return analysis.
"""

from typing import Any, cast

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from scipy import stats

from ..errors import InsufficientDataError, ValidationError
from ..types import QuantileResult


def _get_logger() -> Any:
    """Get logger with lazy initialization to avoid circular imports."""
    try:
        from ..utils.logging_config import get_logger

        return get_logger(__name__, module="quantile_analyzer")
    except ImportError:
        import logging

        return logging.getLogger(__name__)


logger: Any = _get_logger()


class QuantileAnalyzer:
    """Quantile portfolio analyzer for factor validation.

    Analyzes factor effectiveness by constructing quantile portfolios
    and comparing their returns. Supports customizable quantile counts
    and provides visualization capabilities.

    Parameters
    ----------
    n_quantiles : int, default=5
        Number of quantiles to divide the universe into.
        Must be at least 2.

    Attributes
    ----------
    n_quantiles : int
        Number of quantiles for analysis

    Examples
    --------
    >>> analyzer = QuantileAnalyzer(n_quantiles=5)
    >>> result = analyzer.analyze(factor_values, forward_returns)
    >>> print(f"Long-Short Return: {result.long_short_return:.4f}")
    >>> fig = analyzer.plot(result)
    >>> fig.show()
    """

    def __init__(self, n_quantiles: int = 5) -> None:
        """Initialize QuantileAnalyzer.

        Parameters
        ----------
        n_quantiles : int, default=5
            Number of quantiles. Must be >= 2.

        Raises
        ------
        ValidationError
            If n_quantiles is less than 2.
        """
        logger.debug(
            "Initializing QuantileAnalyzer",
            n_quantiles=n_quantiles,
        )

        if n_quantiles < 2:
            logger.error(
                "Invalid n_quantiles value",
                n_quantiles=n_quantiles,
                error="n_quantiles must be at least 2",
            )
            raise ValidationError(
                f"n_quantiles must be at least 2, got {n_quantiles}",
                field="n_quantiles",
                value=n_quantiles,
            )

        self.n_quantiles = n_quantiles
        logger.info(
            "QuantileAnalyzer initialized",
            n_quantiles=n_quantiles,
        )

    def assign_quantiles(self, factor_values: pd.DataFrame) -> pd.DataFrame:
        """Assign quantile numbers to factor values.

        For each row (date), assigns quantile numbers 1 to n_quantiles
        based on factor values. Quantile 1 contains the lowest factor values,
        and quantile n_quantiles contains the highest.

        Parameters
        ----------
        factor_values : pd.DataFrame
            Factor values with datetime index and symbol columns.

        Returns
        -------
        pd.DataFrame
            Quantile assignments (1 to n_quantiles) with same shape
            as input. NaN values in input remain NaN in output.

        Raises
        ------
        ValidationError
            If factor_values is empty.
        InsufficientDataError
            If there are not enough symbols for quantile assignment.

        Examples
        --------
        >>> analyzer = QuantileAnalyzer(n_quantiles=5)
        >>> quantiles = analyzer.assign_quantiles(factor_values)
        >>> # Each row contains values 1-5 indicating quantile membership
        """
        logger.debug(
            "Assigning quantiles",
            shape=factor_values.shape,
            n_quantiles=self.n_quantiles,
        )

        if factor_values.empty:
            logger.error("Empty factor_values provided")
            raise ValidationError(
                "factor_values cannot be empty",
                field="factor_values",
            )

        # For assign_quantiles, we allow fewer symbols than n_quantiles
        # The actual number of quantiles per row is determined by valid data
        n_symbols = len(factor_values.columns)
        logger.debug(
            "Processing quantile assignment",
            n_symbols=n_symbols,
            n_quantiles=self.n_quantiles,
        )

        def _assign_quantile_row(row: pd.Series) -> pd.Series:
            """Assign quantiles for a single row."""
            valid = row.dropna()
            if len(valid) < 2:
                # Need at least 2 valid values to create quantiles
                return pd.Series(np.nan, index=row.index)

            # Use the minimum of n_quantiles and number of valid values
            effective_n_quantiles = min(self.n_quantiles, len(valid))

            try:
                # Use qcut for equal-frequency binning
                quantiles = pd.qcut(
                    valid,
                    q=effective_n_quantiles,
                    labels=list(range(1, effective_n_quantiles + 1)),
                    duplicates="drop",
                )
                result = pd.Series(np.nan, index=row.index)
                result.loc[valid.index] = quantiles.astype(float)
                return result
            except ValueError:
                # Handle edge cases where qcut fails
                return pd.Series(np.nan, index=row.index)

        result_df = cast(
            "pd.DataFrame", factor_values.apply(_assign_quantile_row, axis=1)
        )

        logger.debug(
            "Quantile assignment completed",
            result_shape=result_df.shape,
            non_nan_count=result_df.notna().sum().sum(),
        )

        return result_df

    def compute_quantile_returns(
        self,
        quantile_assignments: pd.DataFrame,
        forward_returns: pd.DataFrame,
    ) -> pd.DataFrame:
        """Compute returns for each quantile.

        For each date and quantile, computes the mean return of all
        symbols assigned to that quantile.

        Parameters
        ----------
        quantile_assignments : pd.DataFrame
            Quantile assignments from assign_quantiles().
        forward_returns : pd.DataFrame
            Forward returns with same index and columns as
            quantile_assignments.

        Returns
        -------
        pd.DataFrame
            Returns by quantile. Index is dates, columns are quantile
            numbers (1 to n_quantiles).

        Raises
        ------
        ValidationError
            If shapes or indices don't match between inputs.

        Examples
        --------
        >>> quantiles = analyzer.assign_quantiles(factor_values)
        >>> returns = analyzer.compute_quantile_returns(quantiles, forward_returns)
        >>> # returns has columns [1, 2, 3, 4, 5] for 5-quantile analysis
        """
        logger.debug(
            "Computing quantile returns",
            quantile_shape=quantile_assignments.shape,
            returns_shape=forward_returns.shape,
        )

        # Validate inputs
        if not quantile_assignments.index.equals(forward_returns.index):
            logger.error(
                "Index mismatch",
                quantile_index_len=len(quantile_assignments.index),
                returns_index_len=len(forward_returns.index),
            )
            raise ValidationError(
                "quantile_assignments and forward_returns must have the same index",
                field="index",
            )

        if set(quantile_assignments.columns) != set(forward_returns.columns):
            logger.error(
                "Columns mismatch",
                quantile_cols=list(quantile_assignments.columns),
                returns_cols=list(forward_returns.columns),
            )
            raise ValidationError(
                "quantile_assignments and forward_returns must have the same columns",
                field="columns",
            )

        # Initialize result DataFrame
        column_labels = pd.Index(list(range(1, self.n_quantiles + 1)))
        result = pd.DataFrame(
            index=forward_returns.index,
            columns=column_labels,
            dtype=float,
        )

        # Compute mean return for each quantile at each date
        for date in forward_returns.index:
            assignments = quantile_assignments.loc[date]
            returns = forward_returns.loc[date]

            for q in range(1, self.n_quantiles + 1):
                stocks_in_quantile = assignments[assignments == q].index
                common = stocks_in_quantile.intersection(returns.dropna().index)

                if len(common) > 0:
                    result.loc[date, q] = returns.loc[common].mean()

        logger.debug(
            "Quantile returns computed",
            result_shape=result.shape,
            non_nan_counts={q: result[q].notna().sum() for q in result.columns},
        )

        return result

    def analyze(
        self,
        factor_values: pd.DataFrame,
        forward_returns: pd.DataFrame,
    ) -> QuantileResult:
        """Perform full quantile analysis.

        Assigns quantiles, computes quantile returns, calculates
        long-short return and monotonicity score.

        Parameters
        ----------
        factor_values : pd.DataFrame
            Factor values with datetime index and symbol columns.
        forward_returns : pd.DataFrame
            Forward returns with same structure as factor_values.

        Returns
        -------
        QuantileResult
            Complete analysis results including quantile returns,
            mean returns, long-short return, and monotonicity score.

        Raises
        ------
        ValidationError
            If inputs are invalid.
        InsufficientDataError
            If there is not enough data for analysis.

        Examples
        --------
        >>> analyzer = QuantileAnalyzer(n_quantiles=5)
        >>> result = analyzer.analyze(factor_values, forward_returns)
        >>> print(f"Mean IC: {result.long_short_return:.4f}")
        >>> print(f"Monotonicity: {result.monotonicity_score:.2f}")
        """
        logger.debug(
            "Starting quantile analysis",
            factor_shape=factor_values.shape,
            returns_shape=forward_returns.shape,
            n_quantiles=self.n_quantiles,
        )

        # Validate inputs
        if factor_values.empty or forward_returns.empty:
            logger.error("Empty input data")
            raise ValidationError(
                "factor_values and forward_returns cannot be empty",
            )

        # Check minimum data requirements
        # Need at least enough rows and symbols for meaningful analysis
        min_periods = 5
        if len(factor_values) < min_periods:
            logger.error(
                "Insufficient data periods",
                available=len(factor_values),
                required=min_periods,
            )
            raise InsufficientDataError(
                f"Need at least {min_periods} periods for analysis, "
                f"got {len(factor_values)}",
                required=min_periods,
                available=len(factor_values),
            )

        n_symbols = len(factor_values.columns)
        if n_symbols < self.n_quantiles:
            logger.error(
                "Insufficient symbols",
                n_symbols=n_symbols,
                n_quantiles=self.n_quantiles,
            )
            raise InsufficientDataError(
                f"Need at least {self.n_quantiles} symbols for {self.n_quantiles}-quantile "
                f"analysis, got {n_symbols}",
                required=self.n_quantiles,
                available=n_symbols,
            )

        # Align indices
        common_index = factor_values.index.intersection(forward_returns.index)
        common_columns = factor_values.columns.intersection(forward_returns.columns)

        if len(common_index) < min_periods:
            logger.error(
                "Insufficient common dates",
                common_dates=len(common_index),
                required=min_periods,
            )
            raise InsufficientDataError(
                f"Need at least {min_periods} common dates, got {len(common_index)}",
                required=min_periods,
                available=len(common_index),
            )

        factor_aligned = factor_values.loc[common_index, common_columns]
        returns_aligned = forward_returns.loc[common_index, common_columns]

        # Assign quantiles and compute returns
        quantile_assignments = self.assign_quantiles(factor_aligned)
        quantile_returns = self.compute_quantile_returns(
            quantile_assignments, returns_aligned
        )

        # Calculate mean returns by quantile
        mean_returns_series = cast("pd.Series", quantile_returns.mean())

        # Calculate long-short return (top - bottom)
        top_return = float(mean_returns_series.iloc[-1])  # Highest quantile
        bottom_return = float(mean_returns_series.iloc[0])  # Lowest quantile
        long_short_return = top_return - bottom_return

        # Calculate monotonicity score using Spearman correlation
        monotonicity_score = self._compute_monotonicity_score(mean_returns_series)

        result = QuantileResult(
            quantile_returns=quantile_returns,
            mean_returns=mean_returns_series,
            long_short_return=long_short_return,
            monotonicity_score=monotonicity_score,
            n_quantiles=self.n_quantiles,
            turnover=None,  # Optional, not computed by default
        )

        logger.info(
            "Quantile analysis completed",
            long_short_return=long_short_return,
            monotonicity_score=monotonicity_score,
            n_quantiles=self.n_quantiles,
        )

        return result

    def _compute_monotonicity_score(self, mean_returns: pd.Series) -> float:
        """Compute monotonicity score from mean returns.

        Uses Spearman correlation between quantile numbers and mean
        returns. A score of 1.0 indicates perfect monotonicity
        (higher quantile = higher return).

        Parameters
        ----------
        mean_returns : pd.Series
            Mean returns by quantile, indexed by quantile number.

        Returns
        -------
        float
            Monotonicity score between 0 and 1.
        """
        # Get non-NaN values
        valid_returns = mean_returns.dropna()
        if len(valid_returns) < 2:
            return 0.0

        # Spearman correlation between quantile number and return
        quantile_numbers = np.array(valid_returns.index, dtype=np.float64)
        returns = np.array(valid_returns.values, dtype=np.float64)

        result = stats.spearmanr(quantile_numbers, returns)
        correlation = float(result.statistic)

        # Convert to 0-1 scale (correlation is -1 to 1)
        # We want positive monotonicity (higher quantile = higher return)
        # to score high, so we use (correlation + 1) / 2
        if np.isnan(correlation):
            return 0.0

        score = (correlation + 1.0) / 2.0
        return score

    def plot(
        self,
        result: QuantileResult,
        title: str | None = None,
    ) -> go.Figure:
        """Plot quantile returns as a bar chart.

        Creates a bar chart showing mean returns for each quantile,
        making it easy to visualize factor effectiveness.

        Parameters
        ----------
        result : QuantileResult
            Analysis result from analyze().
        title : str | None, default=None
            Chart title. If None, a default title is used.

        Returns
        -------
        go.Figure
            Plotly Figure object for the bar chart.

        Examples
        --------
        >>> result = analyzer.analyze(factor_values, forward_returns)
        >>> fig = analyzer.plot(result, title="Momentum Factor Analysis")
        >>> fig.show()
        """
        logger.debug(
            "Creating quantile plot",
            n_quantiles=result.n_quantiles,
            title=title,
        )

        if title is None:
            title = f"Quantile Analysis (n={result.n_quantiles})"

        # Prepare data for plotting
        quantiles = list(result.mean_returns.index)
        returns = list(result.mean_returns.values)

        # Create color scale (red for low, green for high)
        colors = [
            f"rgb({int(255 * (1 - i / (len(quantiles) - 1)))}, "
            f"{int(255 * (i / (len(quantiles) - 1)))}, 100)"
            for i in range(len(quantiles))
        ]

        fig = go.Figure(
            data=[
                go.Bar(
                    x=[f"Q{q}" for q in quantiles],
                    y=returns,
                    marker_color=colors,
                    text=[f"{r:.4f}" if not np.isnan(r) else "N/A" for r in returns],
                    textposition="outside",
                )
            ]
        )

        fig.update_layout(
            title=title,
            xaxis_title="Quantile",
            yaxis_title="Mean Return",
            showlegend=False,
            template="plotly_white",
        )

        # Add annotation for long-short return
        fig.add_annotation(
            x=0.5,
            y=1.05,
            xref="paper",
            yref="paper",
            text=f"Long-Short: {result.long_short_return:.4f} | "
            f"Monotonicity: {result.monotonicity_score:.2f}",
            showarrow=False,
            font={"size": 12},
        )

        logger.debug("Quantile plot created")

        return fig

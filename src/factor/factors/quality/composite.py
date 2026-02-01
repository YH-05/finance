"""CompositeQualityFactor module for computing composite quality-based factor values.

This module provides CompositeQualityFactor class that computes composite quality metrics
by combining multiple quality indicators (ROE, ROA, earnings stability, debt ratio)
with optional custom weights.

Classes
-------
CompositeQualityFactor
    Factor implementation for composite quality-based metrics.

Examples
--------
>>> from factor.factors.quality.composite import CompositeQualityFactor
>>> from factor.providers import YFinanceProvider
>>>
>>> provider = YFinanceProvider()
>>> factor = CompositeQualityFactor(
...     metrics=["roe", "roa", "earnings_stability"],
...     weights=[0.4, 0.4, 0.2],
... )
>>> result = factor.compute(
...     provider=provider,
...     universe=["AAPL", "GOOGL", "MSFT"],
...     start_date="2024-01-01",
...     end_date="2024-12-31",
... )
>>> result.columns.tolist()
['AAPL', 'GOOGL', 'MSFT']
"""

from datetime import datetime

import pandas as pd
from utils_core.logging import get_logger

from factor.core.base import Factor
from factor.core.normalizer import Normalizer
from factor.enums import FactorCategory
from factor.errors import ValidationError
from factor.providers.base import DataProvider

logger = get_logger(__name__)

# Metrics that should be inverted (lower is better)
# For quality factors, only debt_ratio needs inversion
_INVERTED_METRICS: frozenset[str] = frozenset({"debt_ratio"})


class CompositeQualityFactor(Factor):
    """Composite quality factor for computing combined quality metrics.

    Computes a composite quality factor by combining multiple quality indicators.
    Each indicator is normalized (z-score) and then combined using specified weights.
    ROE, ROA, and earnings_stability are kept as-is (higher is better), while
    debt_ratio is inverted (lower is better).

    Parameters
    ----------
    metrics : list[str]
        List of quality metrics to combine. Must be a non-empty list of valid
        metric names from VALID_METRICS ("roe", "roa", "earnings_stability", "debt_ratio").
    weights : list[float] | None, default=None
        Weights for each metric. If None, equal weights are used.
        Must have the same length as metrics if provided.

    Attributes
    ----------
    name : str
        Factor name, always "composite_quality".
    description : str
        Human-readable description of the factor.
    category : FactorCategory
        Factor category, always FactorCategory.QUALITY.
    metrics : list[str]
        The list of quality metrics being combined.
    weights : list[float] | None
        The weights for each metric.
    VALID_METRICS : tuple[str, ...]
        Class attribute containing valid metric names.

    Raises
    ------
    ValidationError
        If metrics is empty or contains invalid metric names.
        If weights length does not match metrics length.

    Examples
    --------
    >>> factor = CompositeQualityFactor(metrics=["roe", "roa"])
    >>> factor.metrics
    ['roe', 'roa']

    >>> # With custom weights
    >>> factor = CompositeQualityFactor(
    ...     metrics=["roe", "roa", "earnings_stability"],
    ...     weights=[0.5, 0.3, 0.2],
    ... )

    Notes
    -----
    The normalization uses z-score with robust estimators (median and MAD).
    For metrics where lower is better (debt_ratio), the normalized
    values are inverted so that better values result in higher factor scores.
    ROE, ROA, and earnings_stability are kept as-is since higher is better.

    References
    ----------
    Novy-Marx, R. (2013). The other side of value: The gross profitability
    premium. Journal of Financial Economics, 108(1), 1-28.
    """

    # Class attributes required by Factor base class
    name: str = "composite_quality"
    description: str = (
        "Composite quality factor combining multiple quality metrics "
        "(ROE, ROA, earnings stability, debt ratio)"
    )
    category: FactorCategory = FactorCategory.QUALITY

    # Class constant for valid metrics (same as QualityFactor)
    VALID_METRICS: tuple[str, ...] = ("roe", "roa", "earnings_stability", "debt_ratio")

    # Optional class attributes for metadata customization
    _required_data: list[str] = ["fundamentals"]
    _frequency: str = "daily"
    _lookback_period: int | None = None
    _higher_is_better: bool = True
    _default_parameters: dict[str, int | float] = {}

    def __init__(
        self,
        metrics: list[str],
        weights: list[float] | None = None,
    ) -> None:
        """Initialize CompositeQualityFactor with the specified metrics and weights.

        Parameters
        ----------
        metrics : list[str]
            List of quality metrics to combine.
        weights : list[float] | None, default=None
            Weights for each metric. If None, equal weights are used.

        Raises
        ------
        ValidationError
            If metrics is empty, contains invalid metric names,
            or if weights length does not match metrics length.
        """
        logger.debug(
            "Initializing CompositeQualityFactor",
            metrics=metrics,
            weights=weights,
        )

        # Validate metrics is not empty
        if not metrics:
            logger.error("Empty metrics list provided")
            raise ValidationError(
                "metrics cannot be empty",
                field="metrics",
                value=metrics,
            )

        # Validate all metrics are valid
        invalid_metrics = [m for m in metrics if m not in self.VALID_METRICS]
        if invalid_metrics:
            logger.error(
                "Invalid metrics specified",
                invalid_metrics=invalid_metrics,
                valid_metrics=self.VALID_METRICS,
            )
            raise ValidationError(
                f"Invalid metrics: {invalid_metrics}. "
                f"Must be one of {self.VALID_METRICS}",
                field="metrics",
                value=invalid_metrics,
            )

        # Validate weights length matches metrics length if provided
        if weights is not None and len(weights) != len(metrics):
            logger.error(
                "Weights length mismatch",
                weights_len=len(weights),
                metrics_len=len(metrics),
            )
            raise ValidationError(
                f"weights length ({len(weights)}) must match "
                f"metrics length ({len(metrics)})",
                field="weights",
                value=weights,
            )

        self.metrics = metrics
        self.weights = weights

        # Create normalizer for z-score normalization
        # Use min_samples=1 to handle small universes
        self._normalizer = Normalizer(min_samples=1)

        logger.info(
            "CompositeQualityFactor initialized",
            metrics=metrics,
            weights=weights,
        )

    def compute(
        self,
        provider: DataProvider,
        universe: list[str],
        start_date: datetime | str,
        end_date: datetime | str,
    ) -> pd.DataFrame:
        """Compute composite quality factor values for the specified universe and date range.

        Fetches fundamental data from the provider, normalizes each metric using
        z-score, inverts metrics where lower is better, and combines them using
        the specified weights.

        Parameters
        ----------
        provider : DataProvider
            Data provider implementing the DataProvider protocol.
        universe : list[str]
            List of ticker symbols to compute factors for.
        start_date : datetime | str
            Start date for the computation period.
            Accepts datetime object or ISO format string (e.g., "2024-01-01").
        end_date : datetime | str
            End date for the computation period.
            Accepts datetime object or ISO format string (e.g., "2024-12-31").

        Returns
        -------
        pd.DataFrame
            DataFrame with factor values:
            - Index: DatetimeIndex named "Date"
            - Columns: symbol names from universe
            - Values: float64 factor values

        Raises
        ------
        ValidationError
            If universe is empty or date range is invalid.

        Examples
        --------
        >>> provider = SomeDataProvider()
        >>> factor = CompositeQualityFactor(metrics=["roe", "roa"])
        >>> result = factor.compute(
        ...     provider=provider,
        ...     universe=["AAPL", "GOOGL"],
        ...     start_date="2024-01-01",
        ...     end_date="2024-12-31",
        ... )
        >>> result.index.name
        'Date'
        >>> list(result.columns)
        ['AAPL', 'GOOGL']
        """
        logger.debug(
            "Computing CompositeQualityFactor",
            metrics=self.metrics,
            weights=self.weights,
            universe_size=len(universe),
            start_date=str(start_date),
            end_date=str(end_date),
        )

        # Validate inputs using base class method
        self.validate_inputs(universe, start_date, end_date)

        # Fetch fundamental data from provider
        logger.debug(
            "Fetching fundamentals data",
            symbols=universe,
            metrics=self.metrics,
        )
        fundamentals = provider.get_fundamentals(
            symbols=universe,
            metrics=self.metrics,
            start_date=start_date,
            end_date=end_date,
        )

        # Calculate weights (equal if not specified)
        effective_weights = self.weights
        if effective_weights is None:
            effective_weights = [1.0 / len(self.metrics)] * len(self.metrics)

        # Process each metric: extract, normalize, invert if needed
        normalized_components: list[pd.DataFrame] = []

        for metric, weight in zip(self.metrics, effective_weights, strict=True):
            # Extract metric data for all symbols
            metric_data = self._extract_metric_data(fundamentals, universe, metric)

            # Normalize using z-score (cross-sectional)
            # Apply row-wise normalization for each date
            normalized = self._normalize_cross_sectional(metric_data)

            # Invert if metric is one where lower is better
            if metric in _INVERTED_METRICS:
                logger.debug(f"Inverting metric: {metric}")
                normalized = -normalized

            # Apply weight
            weighted = normalized * weight
            normalized_components.append(weighted)

        # Combine all weighted components
        result = sum(normalized_components)

        # Ensure result is a DataFrame (not Series)
        if isinstance(result, pd.Series):
            result = result.to_frame()

        # Ensure index is named "Date"
        result.index.name = "Date"

        # Ensure column order matches universe
        result = result.loc[:, universe]

        logger.info(
            "CompositeQualityFactor computation completed",
            metrics=self.metrics,
            rows=len(result),
            columns=len(result.columns),
        )

        return result

    def _extract_metric_data(
        self,
        fundamentals: pd.DataFrame,
        universe: list[str],
        metric: str,
    ) -> pd.DataFrame:
        """Extract a single metric's data for all symbols.

        Parameters
        ----------
        fundamentals : pd.DataFrame
            DataFrame with MultiIndex columns (symbol, metric).
        universe : list[str]
            List of symbols.
        metric : str
            The metric to extract.

        Returns
        -------
        pd.DataFrame
            DataFrame with symbols as columns and dates as index.
        """
        result_data: dict[str, pd.Series] = {}

        for symbol in universe:
            try:
                symbol_data = fundamentals[(symbol, metric)]
                if isinstance(symbol_data, pd.Series):
                    result_data[symbol] = symbol_data
                else:
                    result_data[symbol] = pd.Series(
                        index=fundamentals.index,
                        dtype=float,
                    )
            except KeyError:
                logger.warning(
                    "Symbol data not found in fundamentals",
                    symbol=symbol,
                    metric=metric,
                )
                result_data[symbol] = pd.Series(
                    index=fundamentals.index,
                    dtype=float,
                )

        return pd.DataFrame(result_data)

    def _normalize_cross_sectional(
        self,
        data: pd.DataFrame,
    ) -> pd.DataFrame:
        """Normalize data cross-sectionally (row by row).

        Parameters
        ----------
        data : pd.DataFrame
            DataFrame with symbols as columns and dates as index.

        Returns
        -------
        pd.DataFrame
            Normalized DataFrame with same structure.
        """
        # Apply z-score normalization row by row (cross-sectional)
        # Each row is normalized independently
        normalized_rows = []
        for idx in data.index:
            row = data.loc[idx]
            zscore_row = self._normalizer.zscore(row, robust=True)
            normalized_rows.append(zscore_row)

        return pd.DataFrame(normalized_rows, index=data.index)


__all__ = ["CompositeQualityFactor"]

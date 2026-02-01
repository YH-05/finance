"""QualityFactor module for computing quality-based factor values.

This module provides QualityFactor class that computes various quality metrics
including ROE, ROA, earnings stability, and debt ratio.

Classes
-------
QualityFactor
    Factor implementation for quality-based metrics.

Examples
--------
>>> from factor.factors.quality import QualityFactor
>>> from factor.providers import YFinanceProvider
>>>
>>> provider = YFinanceProvider()
>>> factor = QualityFactor(metric="roe")
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
from typing import Literal

import pandas as pd

from factor.core.base import Factor
from factor.enums import FactorCategory
from factor.errors import ValidationError
from factor.providers.base import DataProvider
from utils_core.logging import get_logger

logger = get_logger(__name__)

# Valid metrics for QualityFactor
QualityMetric = Literal["roe", "roa", "earnings_stability", "debt_ratio"]


class QualityFactor(Factor):
    """Quality factor for computing quality metrics.

    Computes quality-based factor values such as ROE (Return on Equity),
    ROA (Return on Assets), earnings stability, and debt ratio.
    Higher values typically indicate better quality (except for debt ratio
    where lower is better).

    Parameters
    ----------
    metric : str, default="roe"
        The quality metric to compute. Must be one of:
        - "roe": Return on Equity
        - "roa": Return on Assets
        - "earnings_stability": Earnings stability (inverse of volatility)
        - "debt_ratio": Debt to assets ratio (inverted so lower debt = higher score)

    Attributes
    ----------
    name : str
        Factor name, always "quality".
    description : str
        Human-readable description of the factor.
    category : FactorCategory
        Factor category, always FactorCategory.QUALITY.
    metric : str
        The quality metric being computed.
    VALID_METRICS : tuple[str, ...]
        Class attribute containing valid metric names.

    Raises
    ------
    ValidationError
        If metric is not one of VALID_METRICS.

    Examples
    --------
    >>> factor = QualityFactor(metric="roe")
    >>> factor.metric
    'roe'

    >>> # For debt ratio, values are inverted (low debt = high score)
    >>> debt_factor = QualityFactor(metric="debt_ratio")

    Notes
    -----
    The factor values are computed as follows:
    - For ROE/ROA/earnings_stability: higher values = higher scores (no inversion)
    - For debt_ratio: values are inverted (lower debt = higher score)

    References
    ----------
    Novy-Marx, R. (2013). The other side of value: The gross profitability
    premium. Journal of Financial Economics, 108(1), 1-28.
    """

    # Class attributes required by Factor base class
    name: str = "quality"
    description: str = "Quality factor computing quality metrics (ROE, ROA, etc.)"
    category: FactorCategory = FactorCategory.QUALITY

    # Class constant for valid metrics
    VALID_METRICS: tuple[str, ...] = ("roe", "roa", "earnings_stability", "debt_ratio")

    # Optional class attributes for metadata customization
    _required_data: list[str] = ["fundamentals"]
    _frequency: str = "daily"
    _lookback_period: int | None = None
    _higher_is_better: bool = True
    _default_parameters: dict[str, int | float] = {}

    def __init__(
        self,
        metric: str = "roe",
    ) -> None:
        """Initialize QualityFactor with the specified metric.

        Parameters
        ----------
        metric : str, default="roe"
            The quality metric to compute.

        Raises
        ------
        ValidationError
            If metric is not a valid metric name.
        """
        logger.debug(
            "Initializing QualityFactor",
            metric=metric,
        )

        if metric not in self.VALID_METRICS:
            logger.error(
                "Invalid metric specified",
                metric=metric,
                valid_metrics=self.VALID_METRICS,
            )
            raise ValidationError(
                f"metric must be one of {self.VALID_METRICS}, got '{metric}'",
                field="metric",
                value=metric,
            )

        self.metric = metric

        logger.info(
            "QualityFactor initialized",
            metric=metric,
        )

    def compute(
        self,
        provider: DataProvider,
        universe: list[str],
        start_date: datetime | str,
        end_date: datetime | str,
    ) -> pd.DataFrame:
        """Compute quality factor values for the specified universe and date range.

        Fetches fundamental data from the provider and computes factor values
        based on the configured metric. For debt_ratio, values are negated
        so that lower debt results in higher factor scores.

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
        >>> factor = QualityFactor(metric="roe")
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
            "Computing QualityFactor",
            metric=self.metric,
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
            metrics=[self.metric],
        )
        fundamentals = provider.get_fundamentals(
            symbols=universe,
            metrics=[self.metric],
            start_date=start_date,
            end_date=end_date,
        )

        # Extract the metric values for each symbol
        # fundamentals has MultiIndex columns: (symbol, metric)
        result_data: dict[str, pd.Series] = {}

        for symbol in universe:
            try:
                # Access the specific symbol and metric from MultiIndex
                # Cast to Series since we're accessing a single column
                symbol_data = fundamentals[(symbol, self.metric)]
                if isinstance(symbol_data, pd.Series):
                    result_data[symbol] = symbol_data
                else:
                    # Handle edge case where it might be DataFrame
                    result_data[symbol] = pd.Series(
                        index=fundamentals.index,
                        dtype=float,
                    )
            except KeyError:
                logger.warning(
                    "Symbol data not found in fundamentals",
                    symbol=symbol,
                    metric=self.metric,
                )
                # Create a series of NaN values
                result_data[symbol] = pd.Series(
                    index=fundamentals.index,
                    dtype=float,
                )

        # Create result DataFrame
        result = pd.DataFrame(result_data)

        # Ensure index is named "Date"
        result.index.name = "Date"

        # For debt_ratio, invert values (lower debt = higher score)
        if self.metric == "debt_ratio":
            logger.debug("Inverting debt_ratio values (lower debt = higher score)")
            result = -result

        # Ensure column order matches universe and return as DataFrame
        # Use .loc for proper DataFrame return type
        ordered_result = result.loc[:, universe]

        logger.info(
            "QualityFactor computation completed",
            metric=self.metric,
            rows=len(ordered_result),
            columns=len(ordered_result.columns),
        )

        return ordered_result


__all__ = ["QualityFactor"]

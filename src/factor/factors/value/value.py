"""ValueFactor module for computing value-based factor values.

This module provides ValueFactor class that computes various value metrics
including PER, PBR, dividend yield, and EV/EBITDA.

Classes
-------
ValueFactor
    Factor implementation for value-based metrics.

Examples
--------
>>> from factor.factors.value import ValueFactor
>>> from factor.providers import YFinanceProvider
>>>
>>> provider = YFinanceProvider()
>>> factor = ValueFactor(metric="per", invert=True)
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

# Valid metrics for ValueFactor
ValueMetric = Literal["per", "pbr", "dividend_yield", "ev_ebitda"]


class ValueFactor(Factor):
    """Value factor for computing valuation metrics.

    Computes value-based factor values such as PER, PBR, dividend yield,
    and EV/EBITDA. Lower values typically indicate undervaluation (except
    for dividend yield where higher is better).

    Parameters
    ----------
    metric : str, default="per"
        The valuation metric to compute. Must be one of:
        - "per": Price-to-Earnings Ratio
        - "pbr": Price-to-Book Ratio
        - "dividend_yield": Dividend Yield
        - "ev_ebitda": Enterprise Value to EBITDA
    invert : bool, default=True
        Whether to invert the factor values. When True, lower raw values
        result in higher factor scores (e.g., low PER = high value score).
        Set to False for metrics where higher is better (like dividend yield).

    Attributes
    ----------
    name : str
        Factor name, always "value".
    description : str
        Human-readable description of the factor.
    category : FactorCategory
        Factor category, always FactorCategory.VALUE.
    metric : str
        The valuation metric being computed.
    invert : bool
        Whether factor values are inverted.
    VALID_METRICS : tuple[str, ...]
        Class attribute containing valid metric names.

    Raises
    ------
    ValidationError
        If metric is not one of VALID_METRICS.

    Examples
    --------
    >>> factor = ValueFactor(metric="per", invert=True)
    >>> factor.metric
    'per'
    >>> factor.invert
    True

    >>> # For dividend yield, higher is better
    >>> div_factor = ValueFactor(metric="dividend_yield", invert=False)

    Notes
    -----
    The invert parameter controls the direction of factor scores:
    - For PER/PBR/EV-EBITDA: invert=True (low values = good)
    - For dividend yield: invert=False (high values = good)

    References
    ----------
    Fama, E. F., & French, K. R. (1993). Common risk factors in the returns
    on stocks and bonds. Journal of Financial Economics, 33(1), 3-56.
    """

    # Class attributes required by Factor base class
    name: str = "value"
    description: str = "Value factor computing valuation metrics (PER, PBR, etc.)"
    category: FactorCategory = FactorCategory.VALUE

    # Class constant for valid metrics
    VALID_METRICS: tuple[str, ...] = ("per", "pbr", "dividend_yield", "ev_ebitda")

    # Optional class attributes for metadata customization
    _required_data: list[str] = ["fundamentals"]
    _frequency: str = "daily"
    _lookback_period: int | None = None
    _higher_is_better: bool = True  # After inversion, higher is better
    _default_parameters: dict[str, int | float] = {}

    def __init__(
        self,
        metric: str = "per",
        invert: bool = True,
    ) -> None:
        """Initialize ValueFactor with the specified metric.

        Parameters
        ----------
        metric : str, default="per"
            The valuation metric to compute.
        invert : bool, default=True
            Whether to invert factor values.

        Raises
        ------
        ValidationError
            If metric is not a valid metric name.
        """
        logger.debug(
            "Initializing ValueFactor",
            metric=metric,
            invert=invert,
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
        self.invert = invert

        logger.info(
            "ValueFactor initialized",
            metric=metric,
            invert=invert,
        )

    def compute(
        self,
        provider: DataProvider,
        universe: list[str],
        start_date: datetime | str,
        end_date: datetime | str,
    ) -> pd.DataFrame:
        """Compute value factor values for the specified universe and date range.

        Fetches fundamental data from the provider and computes factor values
        based on the configured metric. If invert is True, the values are
        negated so that lower raw values result in higher factor scores.

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
        >>> factor = ValueFactor(metric="per", invert=True)
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
            "Computing ValueFactor",
            metric=self.metric,
            invert=self.invert,
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

        # Apply inversion if configured
        if self.invert:
            logger.debug("Applying factor inversion")
            result = -result

        # Ensure column order matches universe and return as DataFrame
        # Use .loc for proper DataFrame return type
        ordered_result = result.loc[:, universe]

        logger.info(
            "ValueFactor computation completed",
            metric=self.metric,
            rows=len(ordered_result),
            columns=len(ordered_result.columns),
        )

        return ordered_result


__all__ = ["ValueFactor"]

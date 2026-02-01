"""SizeFactor module for computing size-based factor values.

This module provides SizeFactor class that computes various size metrics
including market capitalization, revenue, and total assets.

Classes
-------
SizeFactor
    Factor implementation for size-based metrics.

Examples
--------
>>> from factor.factors.size import SizeFactor
>>> from factor.providers import YFinanceProvider
>>>
>>> provider = YFinanceProvider()
>>> factor = SizeFactor(metric="market_cap", invert=True)
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

import numpy as np
import pandas as pd
from utils_core.logging import get_logger

from factor.core.base import Factor
from factor.enums import FactorCategory
from factor.errors import ValidationError
from factor.providers.base import DataProvider

logger = get_logger(__name__)


class SizeFactor(Factor):
    """Size factor for computing size metrics.

    Computes size-based factor values such as market capitalization, revenue,
    and total assets. Higher values typically indicate larger companies.
    Use invert=True to capture the small-cap premium effect.

    Parameters
    ----------
    metric : str, default="market_cap"
        The size metric to compute. Must be one of:
        - "market_cap": Market capitalization
        - "revenue": Total revenue
        - "total_assets": Total assets
    invert : bool, default=False
        Whether to invert the factor values. When True, smaller companies
        receive higher factor scores (small-cap premium strategy).
    log_transform : bool, default=True
        Whether to apply log transformation (np.log1p) to reduce skewness
        in size distributions.

    Attributes
    ----------
    name : str
        Factor name, always "size".
    description : str
        Human-readable description of the factor.
    category : FactorCategory
        Factor category, always FactorCategory.SIZE.
    metric : str
        The size metric being computed.
    invert : bool
        Whether factor values are inverted.
    log_transform : bool
        Whether log transformation is applied.
    VALID_METRICS : tuple[str, ...]
        Class attribute containing valid metric names.

    Raises
    ------
    ValidationError
        If metric is not one of VALID_METRICS.

    Examples
    --------
    >>> factor = SizeFactor(metric="market_cap", invert=False)
    >>> factor.metric
    'market_cap'
    >>> factor.invert
    False

    >>> # For small-cap premium strategy
    >>> smb_factor = SizeFactor(metric="market_cap", invert=True)

    Notes
    -----
    The invert parameter controls the direction of factor scores:
    - invert=False: Large companies get high scores
    - invert=True: Small companies get high scores (small-cap premium)

    The log_transform parameter helps normalize highly skewed size distributions:
    - log_transform=True: Applies np.log1p for more normal distribution
    - log_transform=False: Uses raw values

    References
    ----------
    Fama, E. F., & French, K. R. (1993). Common risk factors in the returns
    on stocks and bonds. Journal of Financial Economics, 33(1), 3-56.
    """

    # Class attributes required by Factor base class
    name: str = "size"
    description: str = "Size factor computing size metrics (market cap, revenue, etc.)"
    category: FactorCategory = FactorCategory.SIZE

    # Class constant for valid metrics
    VALID_METRICS: tuple[str, ...] = ("market_cap", "revenue", "total_assets")

    # Optional class attributes for metadata customization
    _required_data: list[str] = ["market_cap", "fundamentals"]
    _frequency: str = "daily"
    _lookback_period: int | None = None
    _higher_is_better: bool = True  # After inversion, higher is better
    _default_parameters: dict[str, int | float] = {}

    def __init__(
        self,
        metric: str = "market_cap",
        invert: bool = False,
        log_transform: bool = True,
    ) -> None:
        """Initialize SizeFactor with the specified metric.

        Parameters
        ----------
        metric : str, default="market_cap"
            The size metric to compute.
        invert : bool, default=False
            Whether to invert factor values for small-cap premium.
        log_transform : bool, default=True
            Whether to apply log transformation.

        Raises
        ------
        ValidationError
            If metric is not a valid metric name.
        """
        logger.debug(
            "Initializing SizeFactor",
            metric=metric,
            invert=invert,
            log_transform=log_transform,
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
        self.log_transform = log_transform

        logger.info(
            "SizeFactor initialized",
            metric=metric,
            invert=invert,
            log_transform=log_transform,
        )

    def compute(
        self,
        provider: DataProvider,
        universe: list[str],
        start_date: datetime | str,
        end_date: datetime | str,
    ) -> pd.DataFrame:
        """Compute size factor values for the specified universe and date range.

        Fetches size data from the provider and computes factor values based on
        the configured metric. Applies log transformation if configured, and
        inverts values if configured for small-cap premium strategy.

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
        >>> factor = SizeFactor(metric="market_cap", invert=True)
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
            "Computing SizeFactor",
            metric=self.metric,
            invert=self.invert,
            log_transform=self.log_transform,
            universe_size=len(universe),
            start_date=str(start_date),
            end_date=str(end_date),
        )

        # Validate inputs using base class method
        self.validate_inputs(universe, start_date, end_date)

        # Fetch data based on metric type
        if self.metric == "market_cap":
            result = self._compute_market_cap(provider, universe, start_date, end_date)
        else:
            # revenue or total_assets use fundamentals
            result = self._compute_fundamentals(
                provider, universe, start_date, end_date
            )

        # Apply log transformation if configured
        if self.log_transform:
            logger.debug("Applying log transformation")
            result = np.log1p(result)

        # Apply inversion if configured (for small-cap premium)
        if self.invert:
            logger.debug("Applying factor inversion for small-cap premium")
            result = -result

        # Ensure column order matches universe and return as DataFrame
        ordered_result = result.loc[:, universe]

        logger.info(
            "SizeFactor computation completed",
            metric=self.metric,
            rows=len(ordered_result),
            columns=len(ordered_result.columns),
        )

        return ordered_result

    def _compute_market_cap(
        self,
        provider: DataProvider,
        universe: list[str],
        start_date: datetime | str,
        end_date: datetime | str,
    ) -> pd.DataFrame:
        """Compute market capitalization factor values.

        Parameters
        ----------
        provider : DataProvider
            Data provider implementing the DataProvider protocol.
        universe : list[str]
            List of ticker symbols.
        start_date : datetime | str
            Start date for the computation period.
        end_date : datetime | str
            End date for the computation period.

        Returns
        -------
        pd.DataFrame
            DataFrame with market capitalization values.
        """
        logger.debug(
            "Fetching market cap data",
            symbols=universe,
        )

        market_cap = provider.get_market_cap(
            symbols=universe,
            start_date=start_date,
            end_date=end_date,
        )

        # Ensure index is named "Date"
        market_cap.index.name = "Date"

        return market_cap

    def _compute_fundamentals(
        self,
        provider: DataProvider,
        universe: list[str],
        start_date: datetime | str,
        end_date: datetime | str,
    ) -> pd.DataFrame:
        """Compute fundamentals-based factor values (revenue, total_assets).

        Parameters
        ----------
        provider : DataProvider
            Data provider implementing the DataProvider protocol.
        universe : list[str]
            List of ticker symbols.
        start_date : datetime | str
            Start date for the computation period.
        end_date : datetime | str
            End date for the computation period.

        Returns
        -------
        pd.DataFrame
            DataFrame with fundamental metric values.
        """
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

        return result


__all__ = ["SizeFactor"]

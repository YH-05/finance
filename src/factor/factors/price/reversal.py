"""Reversal factor implementation.

This module provides the ReversalFactor class for calculating short-term
price reversal signals, which capture the tendency of recent price movements
to reverse.

Classes
-------
ReversalFactor
    Short-term reversal factor implementation.

Examples
--------
>>> from factor.factors.price import ReversalFactor
>>> from factor.providers import YFinanceProvider
>>>
>>> provider = YFinanceProvider()
>>> factor = ReversalFactor(lookback=5)
>>> result = factor.compute(
...     provider=provider,
...     universe=["AAPL", "GOOGL", "MSFT"],
...     start_date="2024-01-01",
...     end_date="2024-12-31",
... )
>>> result.head()
               AAPL     GOOGL      MSFT
Date
2024-01-08 -0.0234  0.0189  -0.0156
2024-01-09 -0.0312  0.0145  -0.0178
...
"""

from datetime import datetime

import pandas as pd
from utils_core.logging import get_logger

from factor.core.base import Factor
from factor.enums import FactorCategory
from factor.errors import ValidationError
from factor.providers.base import DataProvider

logger = get_logger(__name__)


class ReversalFactor(Factor):
    """Short-term reversal factor.

    Calculates the short-term reversal factor, which is the negation of
    short-term returns. Stocks that have declined are expected to recover
    (mean reversion), so they receive positive factor scores.

    The reversal is calculated as:
        reversal = -(P_t / P_{t-lookback} - 1)

    Where P_t is the current price and P_{t-lookback} is the price
    `lookback` periods ago.

    Parameters
    ----------
    lookback : int, default=5
        Number of trading days to look back for return calculation.
        Must be a positive integer.

    Attributes
    ----------
    name : str
        Factor name: "reversal"
    description : str
        Factor description
    category : FactorCategory
        Factor category: PRICE
    lookback : int
        Lookback period in trading days

    Examples
    --------
    >>> from factor.factors.price import ReversalFactor
    >>> from factor.providers import YFinanceProvider
    >>>
    >>> # Create reversal factor with 5-day lookback
    >>> factor = ReversalFactor(lookback=5)
    >>> provider = YFinanceProvider()
    >>>
    >>> # Calculate reversal scores
    >>> result = factor.compute(
    ...     provider=provider,
    ...     universe=["AAPL", "GOOGL"],
    ...     start_date="2024-01-01",
    ...     end_date="2024-03-31",
    ... )
    >>>
    >>> # Stocks with negative recent returns have positive reversal scores
    >>> result.tail()
               AAPL     GOOGL
    Date
    2024-03-25 -0.0234  0.0189
    2024-03-26 -0.0312  0.0145
    2024-03-27 -0.0178  0.0298
    2024-03-28 -0.0089  0.0234
    2024-03-29 -0.0156  0.0312

    Notes
    -----
    - The reversal factor is commonly used in short-term trading strategies
    - Higher reversal scores indicate stocks that have recently declined
    - The first `lookback` rows will contain NaN values
    """

    name: str = "reversal"
    description: str = "Short-term reversal factor (negated short-term returns)"
    category: FactorCategory = FactorCategory.PRICE

    # Optional metadata
    _required_data: list[str] = ["price"]
    _frequency: str = "daily"
    _lookback_period: int | None = None
    _higher_is_better: bool = True  # Higher reversal = expected to go up
    _default_parameters: dict[str, int | float] = {"lookback": 5}

    def __init__(self, lookback: int = 5) -> None:
        """Initialize ReversalFactor with the specified lookback period.

        Parameters
        ----------
        lookback : int, default=5
            Number of trading days to look back for return calculation.
            Must be a positive integer.

        Raises
        ------
        ValidationError
            If lookback is not a positive integer.

        Examples
        --------
        >>> factor = ReversalFactor()  # Default 5-day lookback
        >>> factor.lookback
        5

        >>> factor = ReversalFactor(lookback=10)  # Custom 10-day lookback
        >>> factor.lookback
        10
        """
        if lookback <= 0:
            logger.error(
                "Invalid lookback period",
                lookback=lookback,
            )
            raise ValidationError(
                f"lookback must be a positive integer, got {lookback}",
                field="lookback",
                value=lookback,
            )

        self.lookback = lookback
        self._lookback_period = lookback

        logger.debug(
            "ReversalFactor initialized",
            lookback=lookback,
        )

    def compute(
        self,
        provider: DataProvider,
        universe: list[str],
        start_date: datetime | str,
        end_date: datetime | str,
    ) -> pd.DataFrame:
        """Compute reversal factor values for the specified universe.

        The reversal is calculated as the negation of the lookback-period
        return:
            reversal = -(P_t / P_{t-lookback} - 1)

        Parameters
        ----------
        provider : DataProvider
            Data provider implementing the DataProvider protocol.
        universe : list[str]
            List of ticker symbols to compute factors for.
        start_date : datetime | str
            Start date for the computation period.
        end_date : datetime | str
            End date for the computation period.

        Returns
        -------
        pd.DataFrame
            DataFrame with reversal factor values:
            - Index: DatetimeIndex named "Date"
            - Columns: symbol names from universe
            - Values: reversal factor scores (negative returns negated)

        Raises
        ------
        ValidationError
            If input validation fails.

        Examples
        --------
        >>> factor = ReversalFactor(lookback=5)
        >>> provider = MockDataProvider()
        >>> result = factor.compute(
        ...     provider=provider,
        ...     universe=["AAPL", "GOOGL"],
        ...     start_date="2024-01-01",
        ...     end_date="2024-03-31",
        ... )
        >>> result.columns.tolist()
        ['AAPL', 'GOOGL']
        """
        # Validate inputs
        self.validate_inputs(universe, start_date, end_date)

        logger.info(
            "Computing reversal factor",
            lookback=self.lookback,
            universe_size=len(universe),
            start_date=str(start_date),
            end_date=str(end_date),
        )

        # Get price data from provider
        prices = provider.get_prices(universe, start_date, end_date)

        # Calculate returns over the lookback period
        returns = prices.pct_change(periods=self.lookback)

        # Reversal is the negation of returns
        reversal = -returns

        logger.debug(
            "Reversal factor computed",
            result_shape=reversal.shape,
            non_nan_count=reversal.notna().sum().sum(),
        )

        return reversal


__all__ = [
    "ReversalFactor",
]

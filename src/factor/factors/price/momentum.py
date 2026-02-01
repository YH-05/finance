"""Momentum factor implementation.

This module provides the MomentumFactor class for calculating price momentum,
which measures past returns over a specified lookback period.

Classes
-------
MomentumFactor
    Price momentum factor with configurable lookback and skip periods.

Examples
--------
>>> from factor.factors.price.momentum import MomentumFactor
>>> from datetime import datetime
>>>
>>> factor = MomentumFactor(lookback=252, skip_recent=21)
>>> # Compute 12-month momentum excluding recent 1-month
>>> result = factor.compute(
...     provider=data_provider,
...     universe=["AAPL", "GOOGL", "MSFT"],
...     start_date="2023-01-01",
...     end_date="2024-01-01",
... )
"""

from datetime import datetime

import pandas as pd
from utils_core.logging import get_logger

from factor.core.base import Factor
from factor.enums import FactorCategory
from factor.providers.base import DataProvider

logger = get_logger(__name__)


class MomentumFactor(Factor):
    """Price momentum factor.

    Calculates price momentum as the return over a lookback period,
    optionally excluding recent returns to avoid reversal effects.

    The momentum is calculated as:
        momentum = (P_{t-skip} / P_{t-lookback}) - 1

    where:
        - P_{t-skip} is the price at (lookback - skip_recent) days ago
        - P_{t-lookback} is the price at lookback days ago

    Parameters
    ----------
    lookback : int, default=252
        Lookback period in trading days (252 = 12 months).
    skip_recent : int, default=21
        Number of recent days to skip (21 = 1 month).
        This helps avoid short-term reversal effects.

    Attributes
    ----------
    name : str
        Factor name ("momentum")
    description : str
        Factor description
    category : FactorCategory
        Factor category (PRICE)
    lookback : int
        Lookback period in trading days
    skip_recent : int
        Recent days to skip

    Raises
    ------
    ValueError
        If lookback is not positive.
    ValueError
        If skip_recent is negative.
    ValueError
        If skip_recent >= lookback.

    Examples
    --------
    >>> # 12-month momentum excluding recent 1-month (standard)
    >>> factor = MomentumFactor(lookback=252, skip_recent=21)
    >>>
    >>> # 3-month momentum without exclusion
    >>> factor = MomentumFactor(lookback=63, skip_recent=0)
    >>>
    >>> # 1-month momentum
    >>> factor = MomentumFactor(lookback=21, skip_recent=0)
    """

    name: str = "momentum"
    description: str = "価格モメンタム（過去リターン）"
    category: FactorCategory = FactorCategory.PRICE

    # Optional class attributes for metadata
    _required_data: list[str] = ["price"]
    _frequency: str = "daily"
    _higher_is_better: bool = True

    def __init__(
        self,
        lookback: int = 252,
        skip_recent: int = 21,
    ) -> None:
        """Initialize MomentumFactor.

        Parameters
        ----------
        lookback : int, default=252
            Lookback period in trading days.
            Common values: 21 (1 month), 63 (3 months), 252 (12 months).
        skip_recent : int, default=21
            Number of recent days to skip.
            Set to 0 to include all recent returns.

        Raises
        ------
        ValueError
            If lookback is not positive.
        ValueError
            If skip_recent is negative.
        ValueError
            If skip_recent >= lookback.
        """
        logger.debug(
            "Initializing MomentumFactor",
            lookback=lookback,
            skip_recent=skip_recent,
        )

        if lookback <= 0:
            logger.error(
                "Invalid lookback parameter",
                lookback=lookback,
                error="lookback must be positive",
            )
            raise ValueError(f"lookback must be positive, got {lookback}")

        if skip_recent < 0:
            logger.error(
                "Invalid skip_recent parameter",
                skip_recent=skip_recent,
                error="skip_recent must be non-negative",
            )
            raise ValueError(f"skip_recent must be non-negative, got {skip_recent}")

        if skip_recent >= lookback:
            logger.error(
                "Invalid skip_recent parameter",
                skip_recent=skip_recent,
                lookback=lookback,
                error="skip_recent must be less than lookback",
            )
            raise ValueError(
                f"skip_recent ({skip_recent}) must be less than lookback ({lookback})"
            )

        self.lookback = lookback
        self.skip_recent = skip_recent

        # Update metadata with actual parameters
        self._lookback_period = lookback
        self._default_parameters = {
            "lookback": lookback,
            "skip_recent": skip_recent,
        }

        logger.info(
            "MomentumFactor initialized",
            lookback=lookback,
            skip_recent=skip_recent,
        )

    def compute(
        self,
        provider: DataProvider,
        universe: list[str],
        start_date: datetime | str,
        end_date: datetime | str,
    ) -> pd.DataFrame:
        """Compute momentum factor values.

        Calculates momentum as: (P_{t-skip} / P_{t-lookback}) - 1

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
            DataFrame with momentum values:
            - Index: DatetimeIndex named "Date"
            - Columns: symbol names from universe

        Raises
        ------
        ValidationError
            If input validation fails (empty universe, invalid date range).
        InsufficientDataError
            If there is not enough data for calculation.

        Examples
        --------
        >>> factor = MomentumFactor(lookback=252, skip_recent=21)
        >>> result = factor.compute(
        ...     provider=provider,
        ...     universe=["AAPL", "GOOGL"],
        ...     start_date="2023-01-01",
        ...     end_date="2024-01-01",
        ... )
        >>> result.columns.tolist()
        ['AAPL', 'GOOGL']
        """
        logger.debug(
            "Computing momentum factor",
            universe_size=len(universe),
            start_date=str(start_date),
            end_date=str(end_date),
            lookback=self.lookback,
            skip_recent=self.skip_recent,
        )

        # Validate inputs using base class method
        self.validate_inputs(universe, start_date, end_date)

        # Fetch price data from provider
        logger.debug("Fetching price data from provider")
        prices_df = provider.get_prices(universe, start_date, end_date)

        # Extract close prices for each symbol
        close_prices = self._extract_close_prices(prices_df, universe)

        # Calculate momentum
        momentum_df = self._calculate_momentum(close_prices)

        logger.info(
            "Momentum factor computation completed",
            result_shape=momentum_df.shape,
            valid_values=momentum_df.notna().sum().sum(),
        )

        return momentum_df

    def _extract_close_prices(
        self,
        prices_df: pd.DataFrame,
        universe: list[str],
    ) -> pd.DataFrame:
        """Extract close prices from MultiIndex price DataFrame.

        Parameters
        ----------
        prices_df : pd.DataFrame
            Price DataFrame with MultiIndex columns (symbol, price_type).
        universe : list[str]
            List of symbols to extract.

        Returns
        -------
        pd.DataFrame
            DataFrame with close prices (columns: symbols).
        """
        logger.debug(
            "Extracting close prices",
            price_df_shape=prices_df.shape,
            universe_size=len(universe),
        )

        close_prices: dict[str, pd.Series] = {}

        for symbol in universe:
            try:
                if isinstance(prices_df.columns, pd.MultiIndex):
                    # MultiIndex: (symbol, price_type)
                    series = prices_df[(symbol, "Close")]
                # Single symbol case or flat columns
                elif "Close" in prices_df.columns:
                    series = prices_df["Close"]
                else:
                    series = prices_df[symbol]

                # Ensure we have a Series (not DataFrame)
                if isinstance(series, pd.DataFrame):
                    series = series.iloc[:, 0]
                close_prices[symbol] = pd.Series(series, dtype=float)
            except KeyError:
                logger.warning(
                    "Close price not found for symbol",
                    symbol=symbol,
                )
                # Create NaN series
                close_prices[symbol] = pd.Series(
                    index=prices_df.index,
                    dtype=float,
                )

        result = pd.DataFrame(close_prices)
        result.index.name = "Date"

        logger.debug(
            "Close prices extracted",
            result_shape=result.shape,
        )

        return result

    def _calculate_momentum(
        self,
        close_prices: pd.DataFrame,
    ) -> pd.DataFrame:
        """Calculate momentum values.

        Momentum = (P_{t-skip} / P_{t-lookback}) - 1

        Parameters
        ----------
        close_prices : pd.DataFrame
            DataFrame with close prices (columns: symbols).

        Returns
        -------
        pd.DataFrame
            DataFrame with momentum values.
        """
        logger.debug(
            "Calculating momentum",
            input_shape=close_prices.shape,
            lookback=self.lookback,
            skip_recent=self.skip_recent,
        )

        # Price at t-skip (numerator)
        # If skip_recent=0, this is current price
        price_recent = close_prices.shift(self.skip_recent)

        # Price at t-lookback (denominator)
        price_past = close_prices.shift(self.lookback)

        # Calculate momentum: (P_{t-skip} / P_{t-lookback}) - 1
        # Handle division by zero by replacing 0 with NaN
        price_past_safe = price_past.replace(0, float("nan"))
        momentum = (price_recent / price_past_safe) - 1

        # Ensure index name is "Date"
        momentum.index.name = "Date"

        logger.debug(
            "Momentum calculation completed",
            output_shape=momentum.shape,
            nan_count=momentum.isna().sum().sum(),
        )

        return momentum


__all__ = ["MomentumFactor"]

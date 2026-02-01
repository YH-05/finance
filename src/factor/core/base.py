"""Base module for Factor class hierarchy.

This module provides the abstract base class for all factor implementations,
along with supporting dataclasses for factor metadata and compute options.

Classes
-------
FactorMetadata
    Immutable dataclass holding factor metadata.
FactorComputeOptions
    Immutable dataclass for factor computation options.
Factor
    Abstract base class for factor implementations.

Examples
--------
>>> from factor.core.base import Factor, FactorMetadata
>>> from factor.enums import FactorCategory
>>>
>>> class MomentumFactor(Factor):
...     name = "momentum"
...     description = "Price momentum factor"
...     category = FactorCategory.MOMENTUM
...
...     def compute(self, provider, universe, start_date, end_date):
...         prices = provider.get_prices(universe, start_date, end_date)
...         return prices.pct_change(periods=252)
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal

import pandas as pd

from factor.enums import FactorCategory
from factor.errors import ValidationError
from factor.providers.base import DataProvider
from utils_core.logging import get_logger

logger = get_logger(__name__)


# Type aliases for better readability
CategoryLiteral = Literal["price", "value", "quality", "size", "macro", "alternative"]
FrequencyLiteral = Literal["daily", "weekly", "monthly", "quarterly"]
MissingHandleLiteral = Literal["drop", "fill_zero", "fill_mean"]


@dataclass(frozen=True)
class FactorMetadata:
    """Immutable metadata for a factor.

    This dataclass holds descriptive information about a factor including
    its name, category, data requirements, and default parameters.

    Parameters
    ----------
    name : str
        Unique identifier for the factor.
    description : str
        Human-readable description of the factor.
    category : {"price", "value", "quality", "size", "macro", "alternative"}
        Category classification for the factor.
    required_data : list[str]
        List of data types required for factor calculation
        (e.g., ["price", "volume"]).
    frequency : {"daily", "weekly", "monthly", "quarterly"}
        Data frequency for the factor.
    lookback_period : int | None, default=None
        Number of periods to look back for calculation.
    higher_is_better : bool, default=True
        Whether higher factor values indicate better quality.
    default_parameters : dict[str, int | float], default={}
        Default parameter values for factor calculation.

    Attributes
    ----------
    name : str
    description : str
    category : str
    required_data : list[str]
    frequency : str
    lookback_period : int | None
    higher_is_better : bool
    default_parameters : dict[str, int | float]

    Examples
    --------
    >>> metadata = FactorMetadata(
    ...     name="momentum_12m",
    ...     description="12-month price momentum",
    ...     category="price",
    ...     required_data=["price"],
    ...     frequency="daily",
    ...     lookback_period=252,
    ...     higher_is_better=True,
    ...     default_parameters={"lookback": 252, "skip_recent": 21},
    ... )
    >>> metadata.name
    'momentum_12m'
    >>> metadata.category
    'price'
    """

    name: str
    description: str
    category: CategoryLiteral
    required_data: list[str]
    frequency: FrequencyLiteral
    lookback_period: int | None = None
    higher_is_better: bool = True
    default_parameters: dict[str, int | float] = field(default_factory=dict)


@dataclass(frozen=True)
class FactorComputeOptions:
    """Immutable options for factor computation.

    This dataclass holds configuration options that control how factor
    values are computed, including missing data handling and filtering.

    Parameters
    ----------
    handle_missing : {"drop", "fill_zero", "fill_mean"}, default="drop"
        Strategy for handling missing values:
        - "drop": Remove rows with missing values
        - "fill_zero": Replace missing values with zero
        - "fill_mean": Replace missing values with cross-sectional mean
    min_periods : int, default=20
        Minimum number of valid observations required for calculation.
    universe_filter : str | None, default=None
        Optional filter expression for universe selection
        (e.g., "market_cap > 1e9").

    Attributes
    ----------
    handle_missing : str
    min_periods : int
    universe_filter : str | None

    Examples
    --------
    >>> options = FactorComputeOptions(
    ...     handle_missing="fill_mean",
    ...     min_periods=30,
    ...     universe_filter="market_cap > 1e9",
    ... )
    >>> options.handle_missing
    'fill_mean'
    >>> options.min_periods
    30
    """

    handle_missing: MissingHandleLiteral = "drop"
    min_periods: int = 20
    universe_filter: str | None = None


class Factor(ABC):
    """Abstract base class for factor implementations.

    All factor implementations must inherit from this class and implement
    the `compute` method. The class provides common functionality for
    input validation and metadata access.

    Class Attributes
    ----------------
    name : str
        Unique identifier for the factor. Must be overridden in subclasses.
    description : str
        Human-readable description. Must be overridden in subclasses.
    category : FactorCategory
        Category classification. Must be overridden in subclasses.

    Notes
    -----
    Subclasses may optionally define these class attributes for metadata:
    - _required_data: list[str] - Data types required (default: ["price"])
    - _frequency: str - Data frequency (default: "daily")
    - _lookback_period: int | None - Lookback period (default: None)
    - _higher_is_better: bool - Direction interpretation (default: True)
    - _default_parameters: dict[str, int | float] - Default params (default: {})

    Examples
    --------
    >>> from factor.core.base import Factor
    >>> from factor.enums import FactorCategory
    >>>
    >>> class MyFactor(Factor):
    ...     name = "my_factor"
    ...     description = "My custom factor"
    ...     category = FactorCategory.VALUE
    ...
    ...     def compute(self, provider, universe, start_date, end_date):
    ...         prices = provider.get_prices(universe, start_date, end_date)
    ...         return prices.pct_change()
    """

    # Class attributes to be overridden by subclasses
    # These are placeholders that must be overridden in concrete subclasses
    name: str = ""
    description: str = ""
    category: FactorCategory = FactorCategory.PRICE  # Default, should be overridden

    # Optional class attributes for metadata customization
    _required_data: list[str] = ["price"]
    _frequency: str = "daily"
    _lookback_period: int | None = None
    _higher_is_better: bool = True
    _default_parameters: dict[str, int | float] = {}

    @property
    def metadata(self) -> FactorMetadata:
        """Return factor metadata as FactorMetadata instance.

        Constructs a FactorMetadata object from the factor's class attributes.
        The category is converted from FactorCategory enum to its string value
        to match the Literal type expected by FactorMetadata.

        Returns
        -------
        FactorMetadata
            Immutable metadata object containing factor information.

        Examples
        --------
        >>> class MyFactor(Factor):
        ...     name = "test"
        ...     description = "Test factor"
        ...     category = FactorCategory.VALUE
        ...     def compute(self, provider, universe, start_date, end_date):
        ...         ...
        >>> factor = MyFactor()
        >>> factor.metadata.name
        'test'
        >>> factor.metadata.category
        'value'
        """
        # Get optional attributes with defaults from class hierarchy
        required_data = getattr(self, "_required_data", ["price"])
        frequency = getattr(self, "_frequency", "daily")
        lookback_period = getattr(self, "_lookback_period", None)
        higher_is_better = getattr(self, "_higher_is_better", True)
        default_parameters = getattr(self, "_default_parameters", {})

        # Convert FactorCategory enum to string value for Literal type
        category_value = (
            self.category.value
            if hasattr(self.category, "value")
            else str(self.category)
        )

        # Map enum values to valid Literal values
        # FactorCategory has: macro, quality, value, momentum, size, price
        # FactorMetadata accepts: price, value, quality, size, macro, alternative
        category_mapping: dict[str, CategoryLiteral] = {
            "macro": "macro",
            "quality": "quality",
            "value": "value",
            "momentum": "price",  # Map momentum to price category
            "size": "size",
            "price": "price",
        }
        mapped_category: CategoryLiteral = category_mapping.get(category_value, "price")

        logger.debug(
            "Creating FactorMetadata",
            factor_name=self.name,
            category=mapped_category,
            frequency=frequency,
        )

        return FactorMetadata(
            name=self.name,
            description=self.description,
            category=mapped_category,
            required_data=list(required_data),  # Ensure it's a list copy
            frequency=frequency,  # type: ignore[arg-type]
            lookback_period=lookback_period,
            higher_is_better=higher_is_better,
            default_parameters=dict(default_parameters),  # Ensure it's a dict copy
        )

    @abstractmethod
    def compute(
        self,
        provider: DataProvider,
        universe: list[str],
        start_date: datetime | str,
        end_date: datetime | str,
    ) -> pd.DataFrame:
        """Compute factor values for the specified universe and date range.

        This method must be implemented by all subclasses. It should fetch
        the required data from the provider and compute factor values.

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

        Raises
        ------
        ValidationError
            If input validation fails.
        InsufficientDataError
            If there is not enough data for calculation.

        Examples
        --------
        >>> factor = MomentumFactor()
        >>> provider = YFinanceProvider()
        >>> result = factor.compute(
        ...     provider=provider,
        ...     universe=["AAPL", "GOOGL", "MSFT"],
        ...     start_date="2024-01-01",
        ...     end_date="2024-12-31",
        ... )
        >>> result.columns.tolist()
        ['AAPL', 'GOOGL', 'MSFT']
        """
        ...

    def validate_inputs(
        self,
        universe: list[str],
        start_date: datetime | str,
        end_date: datetime | str,
    ) -> None:
        """Validate input parameters for factor computation.

        Performs validation checks on the input parameters before
        factor computation begins.

        Parameters
        ----------
        universe : list[str]
            List of ticker symbols to validate.
        start_date : datetime | str
            Start date for the computation period.
        end_date : datetime | str
            End date for the computation period.

        Raises
        ------
        ValidationError
            If universe is empty.
        ValidationError
            If start_date >= end_date.

        Examples
        --------
        >>> factor = MomentumFactor()
        >>> factor.validate_inputs(
        ...     universe=["AAPL", "GOOGL"],
        ...     start_date=datetime(2024, 1, 1),
        ...     end_date=datetime(2024, 12, 31),
        ... )  # No exception raised

        >>> factor.validate_inputs(
        ...     universe=[],
        ...     start_date=datetime(2024, 1, 1),
        ...     end_date=datetime(2024, 12, 31),
        ... )
        Traceback (most recent call last):
            ...
        ValidationError: Universe cannot be empty
        """
        logger.debug(
            "Validating inputs",
            factor_name=self.name,
            universe_size=len(universe),
            start_date=str(start_date),
            end_date=str(end_date),
        )

        # Validate universe is not empty
        if not universe:
            logger.error(
                "Validation failed: empty universe",
                factor_name=self.name,
            )
            raise ValidationError(
                "Universe cannot be empty",
                field="universe",
                value=universe,
            )

        # Convert string dates to datetime for comparison
        start_dt = self._parse_date(start_date)
        end_dt = self._parse_date(end_date)

        # Validate date range: start_date must be strictly before end_date
        if start_dt >= end_dt:
            logger.error(
                "Validation failed: invalid date range",
                factor_name=self.name,
                start_date=str(start_date),
                end_date=str(end_date),
            )
            raise ValidationError(
                f"start_date ({start_date}) must be before end_date ({end_date})",
                field="date_range",
                value={"start_date": str(start_date), "end_date": str(end_date)},
            )

        logger.debug(
            "Input validation passed",
            factor_name=self.name,
        )

    def _parse_date(self, date: datetime | str) -> datetime:
        """Parse a date string or return datetime as-is.

        Parameters
        ----------
        date : datetime | str
            Date as datetime object or ISO format string.

        Returns
        -------
        datetime
            Parsed datetime object.
        """
        if isinstance(date, datetime):
            return date
        return datetime.fromisoformat(date)


__all__ = [
    "Factor",
    "FactorComputeOptions",
    "FactorMetadata",
]

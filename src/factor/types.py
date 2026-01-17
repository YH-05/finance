"""Common type definitions for the factor package.

This module provides type definitions for factor analysis including:
- Configuration dataclasses
- Result dataclasses
- TypedDicts for data structures
"""

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal, TypedDict, cast

import pandas as pd

from .enums import FactorCategory, NormalizationMethod

# Status types
type ProcessorStatus = Literal["success", "error", "pending"]
type ValidationStatus = Literal["valid", "invalid", "skipped"]


# Common data structures
class ItemDict(TypedDict):
    """Typed dictionary for item data."""

    id: int
    name: str
    value: int


class ItemDictWithStatus(ItemDict):
    """Extended item dictionary with status."""

    status: ProcessorStatus
    processed: bool


class ConfigDict(TypedDict, total=False):
    """Typed dictionary for configuration data."""

    name: str
    max_items: int
    enable_validation: bool
    debug: bool
    timeout: float


class ErrorInfo(TypedDict):
    """Typed dictionary for error information."""

    code: str
    message: str
    details: Mapping[str, str | int | None]


# Result types
class ProcessingResult(TypedDict):
    """Result of a processing operation."""

    status: ProcessorStatus
    data: list[ItemDict]
    errors: list[ErrorInfo]
    processed_count: int
    skipped_count: int


class ValidationResult(TypedDict):
    """Result of a validation operation."""

    is_valid: bool
    errors: list[str]
    warnings: list[str]


# JSON types
type JSONPrimitive = str | int | float | bool | None
type JSONValue = JSONPrimitive | Mapping[str, "JSONValue"] | list["JSONValue"]
type JSONObject = Mapping[str, JSONValue]

# File operation types
type FileOperation = Literal["read", "write", "append", "delete"]
type FileFormat = Literal["json", "yaml", "csv", "txt"]

# Sorting and filtering
type SortOrder = Literal["asc", "desc"]
type FilterOperator = Literal["eq", "ne", "gt", "lt", "gte", "lte", "in", "contains"]


# Structured logging types
class LogContext(TypedDict, total=False):
    """Context information for structured logging."""

    user_id: str | int | None
    request_id: str | None
    session_id: str | None
    trace_id: str | None
    module: str | None
    function: str | None
    line_number: int | None
    extra: Mapping[str, JSONValue]


class LogEvent(TypedDict):
    """Structured log event."""

    event: str
    level: Literal["debug", "info", "warning", "error", "critical"]
    timestamp: str
    logger: str
    context: LogContext | None
    exception: str | None
    duration_ms: float | None


# Log formatting types
type LogFormat = Literal["json", "console", "plain"]
type LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


# =============================================================================
# Configuration Dataclasses
# =============================================================================


@dataclass
class FactorConfig:
    """Configuration for factor analysis.

    Parameters
    ----------
    name : str
        Factor name identifier
    category : FactorCategory
        Factor category classification
    normalization : NormalizationMethod
        Method for normalizing factor values (default: ZSCORE)
    window : int
        Rolling window size for calculations (default: 252)
    min_periods : int
        Minimum periods required for calculation (default: 20)
    winsorize_limits : tuple[float, float] | None
        Lower and upper percentile limits for winsorization (default: None)
    lag : int
        Number of periods to lag the factor (default: 0)

    Examples
    --------
    >>> config = FactorConfig(
    ...     name="momentum_12m",
    ...     category=FactorCategory.MOMENTUM,
    ...     window=252,
    ... )
    >>> config.name
    'momentum_12m'
    """

    name: str
    category: FactorCategory
    normalization: NormalizationMethod = NormalizationMethod.ZSCORE
    window: int = 252
    min_periods: int = 20
    winsorize_limits: tuple[float, float] | None = None
    lag: int = 0


@dataclass
class FactorResult:
    """Result of a factor calculation.

    Parameters
    ----------
    name : str
        Factor name
    data : pd.DataFrame
        Factor values with datetime index and symbol columns
    config : FactorConfig
        Configuration used for calculation
    calculated_at : datetime
        Timestamp when factor was calculated
    coverage : dict[str, float]
        Data coverage ratio per symbol (0-1)
    statistics : dict[str, Any]
        Summary statistics (mean, std, min, max, etc.)

    Examples
    --------
    >>> result = FactorResult(
    ...     name="value_factor",
    ...     data=factor_df,
    ...     config=config,
    ...     calculated_at=datetime.now(),
    ... )
    >>> result.is_empty
    False
    """

    name: str
    data: pd.DataFrame
    config: FactorConfig
    calculated_at: datetime = field(default_factory=datetime.now)
    coverage: dict[str, float] = field(default_factory=dict)
    statistics: dict[str, Any] = field(default_factory=dict)

    @property
    def is_empty(self) -> bool:
        """Check if the result contains no data."""
        return self.data.empty

    @property
    def symbols(self) -> list[str]:
        """Get list of symbols in the result."""
        return list(self.data.columns)

    @property
    def date_range(self) -> tuple[datetime, datetime] | None:
        """Get the date range of the factor data."""
        if self.is_empty:
            return None
        min_ts = self.data.index.min()
        max_ts = self.data.index.max()
        # Convert pandas Timestamp to datetime, casting to satisfy type checker
        start = cast("datetime", min_ts.to_pydatetime())
        end = cast("datetime", max_ts.to_pydatetime())
        return (start, end)


@dataclass
class OrthogonalizationResult:
    """Result of factor orthogonalization.

    Parameters
    ----------
    original_factor : str
        Name of the original factor
    orthogonalized_data : pd.DataFrame
        Orthogonalized factor values
    control_factors : list[str]
        List of control factors used for orthogonalization
    method : str
        Method used for orthogonalization (default: "gram_schmidt")
    r_squared : float
        R-squared from regression (variance explained by control factors)
    residual_std : float
        Standard deviation of residuals
    orthogonalized_at : datetime
        Timestamp of orthogonalization

    Examples
    --------
    >>> result = OrthogonalizationResult(
    ...     original_factor="raw_momentum",
    ...     orthogonalized_data=ortho_df,
    ...     control_factors=["size", "value"],
    ...     r_squared=0.25,
    ...     residual_std=0.8,
    ... )
    >>> result.variance_removed
    0.25
    """

    original_factor: str
    orthogonalized_data: pd.DataFrame
    control_factors: list[str]
    method: str = "gram_schmidt"
    r_squared: float = 0.0
    residual_std: float = 0.0
    orthogonalized_at: datetime = field(default_factory=datetime.now)

    @property
    def variance_removed(self) -> float:
        """Get the proportion of variance removed by orthogonalization."""
        return self.r_squared

    @property
    def is_empty(self) -> bool:
        """Check if the result contains no data."""
        return self.orthogonalized_data.empty


# =============================================================================
# __all__ Export
# =============================================================================

__all__ = [
    "ConfigDict",
    "ErrorInfo",
    "FactorCategory",
    "FactorConfig",
    "FactorResult",
    "FileFormat",
    "FileOperation",
    "FilterOperator",
    "ItemDict",
    "ItemDictWithStatus",
    "JSONObject",
    "JSONPrimitive",
    "JSONValue",
    "LogContext",
    "LogEvent",
    "LogFormat",
    "LogLevel",
    "NormalizationMethod",
    "OrthogonalizationResult",
    "ProcessingResult",
    "ProcessorStatus",
    "SortOrder",
    "ValidationResult",
    "ValidationStatus",
]

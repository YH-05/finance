"""Type definitions for the analyze.statistics module.

This module provides Pydantic models for statistical analysis results:
- DescriptiveStats: Descriptive statistics results
- CorrelationResult: Correlation analysis results

Examples
--------
>>> from analyze.statistics.types import DescriptiveStats
>>> stats = DescriptiveStats(
...     count=10,
...     mean=5.5,
...     median=5.5,
...     std=3.03,
...     var=9.17,
...     min=1.0,
...     max=10.0,
...     q25=3.25,
...     q50=5.5,
...     q75=7.75,
... )
>>> stats.count
10
"""

from typing import Annotated, Literal

import pandas as pd
from pydantic import BaseModel, ConfigDict, Field, field_validator

# =============================================================================
# Type Aliases
# =============================================================================

type CorrelationMethod = Literal["pearson", "spearman", "kendall"]


# =============================================================================
# Descriptive Statistics Model
# =============================================================================


class DescriptiveStats(BaseModel):
    """Descriptive statistics result model.

    Stores the results of descriptive statistical analysis including
    measures of central tendency, dispersion, and distribution shape.

    Parameters
    ----------
    count : int
        Number of non-null observations.
    mean : float
        Arithmetic mean of the data.
    median : float
        Median (50th percentile) of the data.
    std : float
        Sample standard deviation (ddof=1).
    var : float
        Sample variance (ddof=1).
    min : float
        Minimum value in the data.
    max : float
        Maximum value in the data.
    q25 : float
        25th percentile (first quartile).
    q50 : float
        50th percentile (median, same as median field).
    q75 : float
        75th percentile (third quartile).
    skewness : float | None, default=None
        Skewness of the distribution. None if insufficient data.
    kurtosis : float | None, default=None
        Excess kurtosis of the distribution. None if insufficient data.

    Examples
    --------
    >>> stats = DescriptiveStats(
    ...     count=10,
    ...     mean=5.5,
    ...     median=5.5,
    ...     std=3.03,
    ...     var=9.17,
    ...     min=1.0,
    ...     max=10.0,
    ...     q25=3.25,
    ...     q50=5.5,
    ...     q75=7.75,
    ...     skewness=0.0,
    ...     kurtosis=-1.2,
    ... )
    >>> stats.mean
    5.5

    Notes
    -----
    NaN values are allowed for all float fields to handle edge cases
    such as empty datasets or insufficient data for certain calculations.
    """

    model_config = ConfigDict(
        frozen=True,
        str_strip_whitespace=True,
        validate_default=True,
    )

    count: Annotated[
        int,
        Field(
            ...,
            ge=0,
            description="Number of non-null observations",
        ),
    ]

    mean: Annotated[
        float,
        Field(
            ...,
            description="Arithmetic mean of the data",
            allow_inf_nan=True,
        ),
    ]

    median: Annotated[
        float,
        Field(
            ...,
            description="Median (50th percentile) of the data",
            allow_inf_nan=True,
        ),
    ]

    std: Annotated[
        float,
        Field(
            ...,
            description="Sample standard deviation (ddof=1)",
            allow_inf_nan=True,
        ),
    ]

    var: Annotated[
        float,
        Field(
            ...,
            description="Sample variance (ddof=1)",
            allow_inf_nan=True,
        ),
    ]

    min: Annotated[
        float,
        Field(
            ...,
            description="Minimum value in the data",
            allow_inf_nan=True,
        ),
    ]

    max: Annotated[
        float,
        Field(
            ...,
            description="Maximum value in the data",
            allow_inf_nan=True,
        ),
    ]

    q25: Annotated[
        float,
        Field(
            ...,
            description="25th percentile (first quartile)",
            allow_inf_nan=True,
        ),
    ]

    q50: Annotated[
        float,
        Field(
            ...,
            description="50th percentile (median)",
            allow_inf_nan=True,
        ),
    ]

    q75: Annotated[
        float,
        Field(
            ...,
            description="75th percentile (third quartile)",
            allow_inf_nan=True,
        ),
    ]

    skewness: Annotated[
        float | None,
        Field(
            default=None,
            description="Skewness of the distribution",
            allow_inf_nan=True,
        ),
    ] = None

    kurtosis: Annotated[
        float | None,
        Field(
            default=None,
            description="Excess kurtosis of the distribution",
            allow_inf_nan=True,
        ),
    ] = None


# =============================================================================
# Correlation Analysis Model
# =============================================================================


class CorrelationResult(BaseModel):
    """Correlation analysis result model.

    Stores the results of correlation analysis including the correlation
    matrix, symbols analyzed, time period, and correlation method used.

    Parameters
    ----------
    symbols : list[str]
        List of symbols/column names included in the analysis.
    correlation_matrix : pd.DataFrame
        Correlation matrix as a pandas DataFrame.
        Rows and columns are indexed by symbols.
    period : str, default=""
        Description of the analysis period (e.g., "1Y", "2024-01-01 to 2024-12-31").
    method : CorrelationMethod, default="pearson"
        Correlation method used: "pearson", "spearman", or "kendall".

    Examples
    --------
    >>> import pandas as pd
    >>> matrix = pd.DataFrame(
    ...     [[1.0, 0.8], [0.8, 1.0]],
    ...     index=["AAPL", "GOOGL"],
    ...     columns=["AAPL", "GOOGL"],
    ... )
    >>> result = CorrelationResult(
    ...     symbols=["AAPL", "GOOGL"],
    ...     correlation_matrix=matrix,
    ...     period="1Y",
    ...     method="pearson",
    ... )
    >>> result.symbols
    ['AAPL', 'GOOGL']
    >>> result.correlation_matrix.loc["AAPL", "GOOGL"]
    0.8

    Notes
    -----
    The correlation_matrix field uses arbitrary_types_allowed=True
    to support pandas DataFrame objects directly.
    """

    model_config = ConfigDict(
        frozen=True,
        arbitrary_types_allowed=True,
        str_strip_whitespace=True,
        validate_default=True,
    )

    symbols: Annotated[
        list[str],
        Field(
            ...,
            min_length=1,
            description="List of symbols/column names included in the analysis",
        ),
    ]

    correlation_matrix: Annotated[
        pd.DataFrame,
        Field(
            ...,
            description="Correlation matrix as a pandas DataFrame",
        ),
    ]

    period: Annotated[
        str,
        Field(
            default="",
            description="Description of the analysis period",
        ),
    ] = ""

    method: Annotated[
        CorrelationMethod,
        Field(
            default="pearson",
            description="Correlation method used",
        ),
    ] = "pearson"

    @field_validator("symbols")
    @classmethod
    def validate_symbols_not_empty(cls, v: list[str]) -> list[str]:
        """Validate that symbol names are not empty strings."""
        for symbol in v:
            if not symbol or not symbol.strip():
                raise ValueError("Symbol names cannot be empty or whitespace only")
        return v

    @field_validator("correlation_matrix")
    @classmethod
    def validate_correlation_matrix(cls, v: pd.DataFrame) -> pd.DataFrame:
        """Validate that correlation matrix is properly formed."""
        if v.empty:
            raise ValueError("Correlation matrix cannot be empty")
        if v.shape[0] != v.shape[1]:
            raise ValueError("Correlation matrix must be square")
        return v


# =============================================================================
# __all__ Export
# =============================================================================

__all__ = [
    "CorrelationMethod",
    "CorrelationResult",
    "DescriptiveStats",
]

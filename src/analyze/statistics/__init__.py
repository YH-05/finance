"""Statistics module for statistical analysis functions.

This module provides:
- Descriptive statistics functions
- Correlation analysis functions
- Statistical data models

Examples
--------
>>> import pandas as pd
>>> from analyze.statistics import calculate_mean, describe
>>> series = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])
>>> calculate_mean(series)
3.0
>>> stats = describe(series)
>>> stats.count
5
"""

from analyze.statistics.correlation import (
    CorrelationAnalyzer,
    calculate_beta,
    calculate_correlation,
    calculate_correlation_matrix,
    calculate_rolling_beta,
    calculate_rolling_correlation,
)
from analyze.statistics.descriptive import (
    calculate_kurtosis,
    calculate_mean,
    calculate_median,
    calculate_percentile_rank,
    calculate_quantile,
    calculate_skewness,
    calculate_std,
    calculate_var,
    describe,
)
from analyze.statistics.types import (
    CorrelationMethod,
    CorrelationResult,
    DescriptiveStats,
)

__all__ = [
    "CorrelationAnalyzer",
    "CorrelationMethod",
    "CorrelationResult",
    "DescriptiveStats",
    "calculate_beta",
    "calculate_correlation",
    "calculate_correlation_matrix",
    "calculate_kurtosis",
    "calculate_mean",
    "calculate_median",
    "calculate_percentile_rank",
    "calculate_quantile",
    "calculate_rolling_beta",
    "calculate_rolling_correlation",
    "calculate_skewness",
    "calculate_std",
    "calculate_var",
    "describe",
]

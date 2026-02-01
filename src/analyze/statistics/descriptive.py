"""Descriptive statistics functions for data analysis.

This module provides functions for calculating descriptive statistics
including measures of central tendency, dispersion, and distribution shape.

Functions
---------
calculate_mean : Calculate arithmetic mean
calculate_median : Calculate median value
calculate_std : Calculate standard deviation
calculate_var : Calculate variance
calculate_skewness : Calculate skewness
calculate_kurtosis : Calculate excess kurtosis
describe : Generate comprehensive descriptive statistics
calculate_quantile : Calculate specific quantile
calculate_percentile_rank : Calculate percentile rank of a value

Examples
--------
>>> import pandas as pd
>>> series = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])
>>> calculate_mean(series)
3.0
>>> calculate_median(series)
3.0
"""

from typing import cast

import pandas as pd

from utils_core.logging import get_logger

from .types import DescriptiveStats

logger = get_logger(__name__)


def calculate_mean(series: pd.Series) -> float:
    """Calculate arithmetic mean of a series.

    Parameters
    ----------
    series : pd.Series
        Input data series. NaN values are excluded.

    Returns
    -------
    float
        Arithmetic mean of the series.
        Returns NaN if series is empty.

    Examples
    --------
    >>> import pandas as pd
    >>> series = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])
    >>> calculate_mean(series)
    3.0
    """
    logger.debug("Calculating mean", series_len=len(series))

    if series.empty:
        logger.warning("Empty series provided for mean calculation")
        return float("nan")

    result = float(series.mean())
    logger.debug("Mean calculated", mean=result)
    return result


def calculate_median(series: pd.Series) -> float:
    """Calculate median of a series.

    Parameters
    ----------
    series : pd.Series
        Input data series. NaN values are excluded.

    Returns
    -------
    float
        Median of the series.
        Returns NaN if series is empty.

    Examples
    --------
    >>> import pandas as pd
    >>> series = pd.Series([1.0, 3.0, 5.0])
    >>> calculate_median(series)
    3.0
    """
    logger.debug("Calculating median", series_len=len(series))

    if series.empty:
        logger.warning("Empty series provided for median calculation")
        return float("nan")

    result = float(series.median())
    logger.debug("Median calculated", median=result)
    return result


def calculate_std(series: pd.Series, ddof: int = 1) -> float:
    """Calculate standard deviation of a series.

    Parameters
    ----------
    series : pd.Series
        Input data series. NaN values are excluded.
    ddof : int, default=1
        Delta degrees of freedom.
        ddof=1 for sample std, ddof=0 for population std.

    Returns
    -------
    float
        Standard deviation of the series.
        Returns NaN if series is empty.

    Raises
    ------
    ValueError
        If ddof is negative.

    Examples
    --------
    >>> import pandas as pd
    >>> series = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])
    >>> calculate_std(series)  # Sample std
    1.5811388300841898
    >>> calculate_std(series, ddof=0)  # Population std
    1.4142135623730951
    """
    logger.debug("Calculating std", series_len=len(series), ddof=ddof)

    if ddof < 0:
        logger.error("Invalid ddof", ddof=ddof)
        raise ValueError(f"ddof must be non-negative, got {ddof}")

    if series.empty:
        logger.warning("Empty series provided for std calculation")
        return float("nan")

    result = float(series.std(ddof=ddof))
    logger.debug("Std calculated", std=result)
    return result


def calculate_var(series: pd.Series, ddof: int = 1) -> float:
    """Calculate variance of a series.

    Parameters
    ----------
    series : pd.Series
        Input data series. NaN values are excluded.
    ddof : int, default=1
        Delta degrees of freedom.
        ddof=1 for sample variance, ddof=0 for population variance.

    Returns
    -------
    float
        Variance of the series.
        Returns NaN if series is empty.

    Raises
    ------
    ValueError
        If ddof is negative.

    Examples
    --------
    >>> import pandas as pd
    >>> series = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])
    >>> calculate_var(series)  # Sample variance
    2.5
    """
    logger.debug("Calculating var", series_len=len(series), ddof=ddof)

    if ddof < 0:
        logger.error("Invalid ddof", ddof=ddof)
        raise ValueError(f"ddof must be non-negative, got {ddof}")

    if series.empty:
        logger.warning("Empty series provided for variance calculation")
        return float("nan")

    result = float(series.var(ddof=ddof))
    logger.debug("Variance calculated", var=result)
    return result


def calculate_skewness(series: pd.Series) -> float:
    """Calculate skewness of a series.

    Skewness measures the asymmetry of the distribution.
    - Positive skewness: right tail is longer (right-skewed)
    - Negative skewness: left tail is longer (left-skewed)
    - Zero skewness: symmetric distribution

    Parameters
    ----------
    series : pd.Series
        Input data series. NaN values are excluded.

    Returns
    -------
    float
        Skewness of the series.
        Returns NaN if series has fewer than 3 data points.

    Examples
    --------
    >>> import pandas as pd
    >>> series = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0, 5.0, 4.0, 3.0, 2.0, 1.0])
    >>> calculate_skewness(series)  # Approximately 0 (symmetric)
    0.0
    """
    logger.debug("Calculating skewness", series_len=len(series))

    if series.empty:
        logger.warning("Empty series provided for skewness calculation")
        return float("nan")

    clean_series = series.dropna()
    if len(clean_series) < 3:
        logger.warning(
            "Insufficient data for skewness calculation",
            valid_points=len(clean_series),
        )
        return float("nan")

    result = float(clean_series.skew())
    logger.debug("Skewness calculated", skewness=result)
    return result


def calculate_kurtosis(series: pd.Series) -> float:
    """Calculate excess kurtosis of a series.

    Excess kurtosis measures the tailedness relative to normal distribution.
    - Positive kurtosis: heavier tails than normal (leptokurtic)
    - Negative kurtosis: lighter tails than normal (platykurtic)
    - Zero kurtosis: normal distribution (mesokurtic)

    Parameters
    ----------
    series : pd.Series
        Input data series. NaN values are excluded.

    Returns
    -------
    float
        Excess kurtosis of the series.
        Returns NaN if series has fewer than 4 data points.

    Examples
    --------
    >>> import pandas as pd
    >>> import numpy as np
    >>> np.random.seed(42)
    >>> series = pd.Series(np.random.normal(0, 1, 1000))
    >>> calculate_kurtosis(series)  # Close to 0 for normal distribution
    -0.0196...
    """
    logger.debug("Calculating kurtosis", series_len=len(series))

    if series.empty:
        logger.warning("Empty series provided for kurtosis calculation")
        return float("nan")

    clean_series = series.dropna()
    if len(clean_series) < 4:
        logger.warning(
            "Insufficient data for kurtosis calculation",
            valid_points=len(clean_series),
        )
        return float("nan")

    result = float(clean_series.kurtosis())
    logger.debug("Kurtosis calculated", kurtosis=result)
    return result


def describe(series: pd.Series) -> DescriptiveStats:
    """Generate comprehensive descriptive statistics for a series.

    Parameters
    ----------
    series : pd.Series
        Input data series. NaN values are excluded for calculations.

    Returns
    -------
    DescriptiveStats
        Pydantic model containing all descriptive statistics.

    Examples
    --------
    >>> import pandas as pd
    >>> series = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])
    >>> stats = describe(series)
    >>> stats.mean
    3.0
    >>> stats.count
    5
    """
    logger.debug("Generating descriptive statistics", series_len=len(series))

    clean_series = series.dropna()
    count = len(clean_series)

    if count == 0:
        logger.warning("Empty series provided for describe")
        return DescriptiveStats(
            count=0,
            mean=float("nan"),
            median=float("nan"),
            std=float("nan"),
            var=float("nan"),
            min=float("nan"),
            max=float("nan"),
            q25=float("nan"),
            q50=float("nan"),
            q75=float("nan"),
            skewness=float("nan"),
            kurtosis=float("nan"),
        )

    mean = calculate_mean(series)
    median = calculate_median(series)
    std = calculate_std(series)
    var = calculate_var(series)
    min_val = float(clean_series.min())
    max_val = float(clean_series.max())
    q25 = float(clean_series.quantile(0.25))
    q50 = float(clean_series.quantile(0.50))
    q75 = float(clean_series.quantile(0.75))
    skewness = calculate_skewness(series)
    kurtosis = calculate_kurtosis(series)

    stats = DescriptiveStats(
        count=count,
        mean=mean,
        median=median,
        std=std,
        var=var,
        min=min_val,
        max=max_val,
        q25=q25,
        q50=q50,
        q75=q75,
        skewness=skewness,
        kurtosis=kurtosis,
    )

    logger.info("Descriptive statistics generated", count=count, mean=mean)
    return stats


def calculate_quantile(series: pd.Series, q: float) -> float:
    """Calculate a specific quantile of a series.

    Parameters
    ----------
    series : pd.Series
        Input data series. NaN values are excluded.
    q : float
        Quantile to compute, must be between 0 and 1 (inclusive).
        0 = minimum, 0.5 = median, 1 = maximum.

    Returns
    -------
    float
        The quantile value.
        Returns NaN if series is empty.

    Raises
    ------
    ValueError
        If q is not between 0 and 1.

    Examples
    --------
    >>> import pandas as pd
    >>> series = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])
    >>> calculate_quantile(series, 0.5)  # Median
    3.0
    >>> calculate_quantile(series, 0.25)  # First quartile
    2.0
    """
    logger.debug("Calculating quantile", series_len=len(series), q=q)

    if q < 0 or q > 1:
        logger.error("Invalid q value", q=q)
        raise ValueError(f"q must be between 0 and 1, got {q}")

    if series.empty:
        logger.warning("Empty series provided for quantile calculation")
        return float("nan")

    clean_series = series.dropna()
    if len(clean_series) == 0:
        return float("nan")

    result = float(clean_series.quantile(q))
    logger.debug("Quantile calculated", q=q, result=result)
    return result


def calculate_percentile_rank(series: pd.Series, value: float) -> float:
    """Calculate the percentile rank of a value within a series.

    Percentile rank indicates what percentage of data falls below the given value.

    Parameters
    ----------
    series : pd.Series
        Input data series. NaN values are excluded.
    value : float
        The value to calculate the percentile rank for.

    Returns
    -------
    float
        Percentile rank (0-100).
        Returns NaN if series is empty.

    Examples
    --------
    >>> import pandas as pd
    >>> series = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])
    >>> calculate_percentile_rank(series, 3.0)  # 50th percentile
    50.0
    >>> calculate_percentile_rank(series, 1.0)  # Minimum
    0.0
    """
    logger.debug(
        "Calculating percentile rank",
        series_len=len(series),
        value=value,
    )

    if series.empty:
        logger.warning("Empty series provided for percentile rank calculation")
        return float("nan")

    clean_series = series.dropna()
    if len(clean_series) == 0:
        return float("nan")

    # Count values less than the given value
    count_below = cast("int", (clean_series < value).sum())
    total = len(clean_series)

    # Percentile rank = (count below / total) * 100
    result = (count_below / total) * 100

    logger.debug(
        "Percentile rank calculated",
        value=value,
        percentile_rank=result,
    )
    return result


__all__ = [
    "DescriptiveStats",
    "calculate_kurtosis",
    "calculate_mean",
    "calculate_median",
    "calculate_percentile_rank",
    "calculate_quantile",
    "calculate_skewness",
    "calculate_std",
    "calculate_var",
    "describe",
]

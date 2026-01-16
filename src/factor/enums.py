"""Enum definitions for the factor package.

This module provides enum types for factor analysis configuration:
- Factor categorization
- Normalization methods
"""

from enum import Enum


class FactorCategory(str, Enum):
    """Category classification for factors.

    Attributes
    ----------
    MACRO : str
        Macroeconomic factors (GDP growth, inflation, interest rates)
    QUALITY : str
        Quality factors (ROE, earnings stability, debt ratios)
    VALUE : str
        Value factors (P/E, P/B, dividend yield)
    MOMENTUM : str
        Momentum factors (price momentum, earnings momentum)
    SIZE : str
        Size factors (market cap, asset size)

    Examples
    --------
    >>> category = FactorCategory.VALUE
    >>> category.value
    'value'
    """

    MACRO = "macro"
    QUALITY = "quality"
    VALUE = "value"
    MOMENTUM = "momentum"
    SIZE = "size"


class NormalizationMethod(str, Enum):
    """Normalization methods for factor values.

    Attributes
    ----------
    ZSCORE : str
        Z-score normalization (mean=0, std=1)
    RANK : str
        Cross-sectional rank transformation
    PERCENTILE : str
        Percentile transformation (0-100)
    QUINTILE : str
        Quintile grouping (1-5)

    Examples
    --------
    >>> method = NormalizationMethod.ZSCORE
    >>> method.value
    'zscore'
    """

    ZSCORE = "zscore"
    RANK = "rank"
    PERCENTILE = "percentile"
    QUINTILE = "quintile"


__all__ = [
    "FactorCategory",
    "NormalizationMethod",
]

"""Validation module for factor analysis.

This module provides tools for validating factor effectiveness:
- QuantileAnalyzer: Quantile portfolio analysis
"""

from .quantile_analyzer import QuantileAnalyzer

__all__ = [
    "QuantileAnalyzer",
]

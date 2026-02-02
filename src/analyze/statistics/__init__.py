"""Statistical analysis module for financial data.

This module provides abstract base classes and concrete implementations
for various statistical analyses including correlation, beta, and
Kalman filtering.

Examples
--------
>>> from analyze.statistics import StatisticalAnalyzer
>>> class MyAnalyzer(StatisticalAnalyzer):
...     def calculate(self, df: pd.DataFrame, **kwargs) -> pd.DataFrame:
...         return df.describe()
...     def validate_input(self, df: pd.DataFrame) -> bool:
...         return not df.empty
"""

from .base import StatisticalAnalyzer

__all__ = ["StatisticalAnalyzer"]

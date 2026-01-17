"""strategy package.

This package provides portfolio strategy analysis tools including:
- Risk calculation and metrics
- Portfolio optimization
"""

from .risk import RiskCalculator, RiskMetricsResult
from .utils.logging_config import get_logger

__all__ = [
    "RiskCalculator",
    "RiskMetricsResult",
    "get_logger",
]

__version__ = "0.1.0"

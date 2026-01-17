"""factor package."""

from .enums import FactorCategory, NormalizationMethod
from .errors import (
    FactorError,
    InsufficientDataError,
    NormalizationError,
    OrthogonalizationError,
    ValidationError,
)
from .types import FactorConfig, FactorResult, OrthogonalizationResult, QuantileResult
from .utils.logging_config import get_logger
from .validation import ICAnalyzer, ICResult, QuantileAnalyzer

__all__ = [
    "FactorCategory",
    "FactorConfig",
    "FactorError",
    "FactorResult",
    "ICAnalyzer",
    "ICResult",
    "InsufficientDataError",
    "NormalizationError",
    "NormalizationMethod",
    "OrthogonalizationError",
    "OrthogonalizationResult",
    "QuantileAnalyzer",
    "QuantileResult",
    "ValidationError",
    "get_logger",
]

__version__ = "0.1.0"

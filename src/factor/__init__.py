"""factor package."""

from .core.base import Factor, FactorComputeOptions, FactorMetadata
from .core.registry import (
    FactorNotFoundError,
    FactorRegistry,
    get_registry,
    register_factor,
)
from .enums import FactorCategory, NormalizationMethod
from .errors import (
    FactorError,
    InsufficientDataError,
    NormalizationError,
    OrthogonalizationError,
    ValidationError,
)
from .factors.value import CompositeValueFactor, ValueFactor
from .types import FactorConfig, FactorResult, OrthogonalizationResult, QuantileResult
from .utils.logging_config import get_logger
from .validation import ICAnalyzer, ICResult, QuantileAnalyzer

__all__ = [
    "CompositeValueFactor",
    "Factor",
    "FactorCategory",
    "FactorComputeOptions",
    "FactorConfig",
    "FactorError",
    "FactorMetadata",
    "FactorNotFoundError",
    "FactorRegistry",
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
    "ValueFactor",
    "get_logger",
    "get_registry",
    "register_factor",
]

__version__ = "0.1.0"

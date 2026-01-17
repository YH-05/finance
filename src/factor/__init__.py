"""factor package - カスタムファクター開発フレームワーク.

This package provides a comprehensive framework for factor analysis:

Core:
    - Factor: Abstract base class for factor implementations
    - Normalizer: Factor normalization algorithms (z-score, percentile, quintile)
    - Orthogonalizer: Factor orthogonalization using OLS residuals
    - YieldCurvePCA: PCA analysis for yield curves with sign alignment
    - ReturnCalculator: Return calculation utilities

Factors:
    - Price: MomentumFactor, ReversalFactor, VolatilityFactor
    - Value: ValueFactor, CompositeValueFactor
    - Quality: QualityFactor, CompositeQualityFactor, ROICFactor, ROICTransitionLabeler
    - Size: SizeFactor

Providers:
    - DataProvider: Abstract protocol for data sources
    - YFinanceProvider: Yahoo Finance data provider
    - Cache: Caching utility for providers

Validation:
    - ICAnalyzer: IC/IR analysis for factor evaluation
    - QuantileAnalyzer: Quantile-based factor analysis
"""

# Core
from .core.base import Factor, FactorComputeOptions, FactorMetadata
from .core.normalizer import Normalizer
from .core.orthogonalization import Orthogonalizer
from .core.pca import PCAResult, YieldCurvePCA
from .core.registry import (
    FactorNotFoundError,
    FactorRegistry,
    get_registry,
    register_factor,
)
from .core.return_calculator import ReturnCalculator, ReturnConfig

# Enums
from .enums import FactorCategory, NormalizationMethod

# Errors
from .errors import (
    DataFetchError,
    FactorError,
    InsufficientDataError,
    NormalizationError,
    OrthogonalizationError,
    ValidationError,
)

# Price Factors
from .factors.price import MomentumFactor, ReversalFactor, VolatilityFactor

# Quality Factors
from .factors.quality import (
    CompositeQualityFactor,
    QualityFactor,
    ROICFactor,
    ROICTransitionLabeler,
)

# Size Factors
from .factors.size import SizeFactor

# Value Factors
from .factors.value import CompositeValueFactor, ValueFactor

# Providers
from .providers import Cache, DataProvider, YFinanceProvider

# Types
from .types import FactorConfig, FactorResult, OrthogonalizationResult, QuantileResult

# Logging
from .utils.logging_config import get_logger

# Validation
from .validation import ICAnalyzer, ICResult, QuantileAnalyzer

__all__ = [
    # Providers
    "Cache",
    # Quality Factors
    "CompositeQualityFactor",
    # Value Factors
    "CompositeValueFactor",
    # Errors
    "DataFetchError",
    "DataProvider",
    # Core
    "Factor",
    # Enums
    "FactorCategory",
    "FactorComputeOptions",
    # Types
    "FactorConfig",
    "FactorError",
    "FactorMetadata",
    "FactorNotFoundError",
    "FactorRegistry",
    "FactorResult",
    # Validation
    "ICAnalyzer",
    "ICResult",
    "InsufficientDataError",
    # Price Factors
    "MomentumFactor",
    "NormalizationError",
    "NormalizationMethod",
    "Normalizer",
    "OrthogonalizationError",
    "OrthogonalizationResult",
    "Orthogonalizer",
    "PCAResult",
    "QualityFactor",
    "QuantileAnalyzer",
    "QuantileResult",
    "ROICFactor",
    "ROICTransitionLabeler",
    "ReturnCalculator",
    "ReturnConfig",
    "ReversalFactor",
    # Size Factors
    "SizeFactor",
    "ValidationError",
    "ValueFactor",
    "VolatilityFactor",
    "YFinanceProvider",
    "YieldCurvePCA",
    # Logging
    "get_logger",
    "get_registry",
    "register_factor",
]

__version__ = "0.1.0"

"""Core functionality of the factor package.

This module exports the main classes for factor analysis:
- Factor: Abstract base class for factor implementations
- FactorComputeOptions: Options for factor computation
- FactorMetadata: Metadata for factor definitions
- Normalizer: Factor normalization algorithms (z-score, percentile, quintile, winsorize)
- ReturnCalculator: Return calculation (multi-period, forward, active returns)
- Orthogonalizer: Factor orthogonalization using OLS residuals
- YieldCurvePCA: PCA analysis for yield curves with sign alignment
"""

from .base import Factor, FactorComputeOptions, FactorMetadata
from .normalizer import Normalizer
from .orthogonalization import Orthogonalizer
from .pca import PCAResult, YieldCurvePCA
from .return_calculator import ReturnCalculator, ReturnConfig

__all__ = [
    "Factor",
    "FactorComputeOptions",
    "FactorMetadata",
    "Normalizer",
    "Orthogonalizer",
    "PCAResult",
    "ReturnCalculator",
    "ReturnConfig",
    "YieldCurvePCA",
]

"""Core functionality of the factor package.

This module exports the main classes for factor analysis:
- Normalizer: Factor normalization algorithms (z-score, percentile, quintile, winsorize)
- ReturnCalculator: Return calculation (multi-period, forward, active returns)
- Orthogonalizer: Factor orthogonalization using OLS residuals
- YieldCurvePCA: PCA analysis for yield curves with sign alignment
"""

from .normalizer import Normalizer
from .orthogonalization import Orthogonalizer
from .pca import PCAResult, YieldCurvePCA
from .return_calculator import ReturnCalculator, ReturnConfig

__all__ = [
    "Normalizer",
    "Orthogonalizer",
    "PCAResult",
    "ReturnCalculator",
    "ReturnConfig",
    "YieldCurvePCA",
]

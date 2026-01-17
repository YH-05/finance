"""Quality factor implementations.

This module provides quality factor implementations including:
- QualityFactor: ROE, ROA, earnings stability, debt ratio
- CompositeQualityFactor: Multiple quality metrics combined
- ROIC (Return on Invested Capital) factor calculations
- Transition labeling for factor analysis.
"""

from .composite import CompositeQualityFactor
from .quality import QualityFactor
from .roic import ROICFactor
from .roic_label import ROICTransitionLabeler

__all__ = [
    "CompositeQualityFactor",
    "QualityFactor",
    "ROICFactor",
    "ROICTransitionLabeler",
]

"""Quality factor implementations.

This module provides ROIC (Return on Invested Capital) factor calculations
and transition labeling for factor analysis.
"""

from .roic import ROICFactor
from .roic_label import ROICTransitionLabeler

__all__ = [
    "ROICFactor",
    "ROICTransitionLabeler",
]

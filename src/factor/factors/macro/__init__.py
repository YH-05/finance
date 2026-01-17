"""macro package - Macroeconomic factor implementations.

This package provides implementations for macroeconomic factors:
- BaseMacroFactor: Abstract base class for all macro factors
- InterestRateFactor: Level, Slope, Curvature from yield curve PCA
- FlightToQualityFactor: HY-IG spread based flight-to-quality factor
- InflationFactor: Inflation expectations factor based on T10YIE
- MacroFactorBuilder: Orchestrates construction of all macro factors
"""

from .base import BaseMacroFactor
from .flight_to_quality import FlightToQualityFactor
from .inflation import InflationFactor
from .interest_rate import InterestRateFactor
from .macro_builder import MacroFactorBuilder

__all__ = [
    "BaseMacroFactor",
    "FlightToQualityFactor",
    "InflationFactor",
    "InterestRateFactor",
    "MacroFactorBuilder",
]

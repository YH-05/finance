"""Technical analysis module for financial data.

This module provides technical analysis tools including:
- Moving averages (SMA, EMA)
- Momentum indicators (RSI, MACD)
- Volatility indicators (Bollinger Bands, ATR)
- Return calculations

Public API
----------
Types (TypedDict)
~~~~~~~~~~~~~~~~~
SMAParams
    Parameters for Simple Moving Average calculation
EMAParams
    Parameters for Exponential Moving Average calculation
RSIParams
    Parameters for Relative Strength Index calculation
MACDParams
    Parameters for MACD calculation
BollingerBandsParams
    Parameters for Bollinger Bands calculation
VolatilityParams
    Parameters for volatility calculation
ReturnParams
    Parameters for return calculation
BollingerBandsResult
    Result of Bollinger Bands calculation
MACDResult
    Result of MACD calculation
"""

from .indicators import TechnicalIndicators
from .types import (
    BollingerBandsParams,
    BollingerBandsResult,
    EMAParams,
    MACDParams,
    MACDResult,
    ReturnParams,
    RSIParams,
    SMAParams,
    VolatilityParams,
)

__all__ = [
    "BollingerBandsParams",
    "BollingerBandsResult",
    "EMAParams",
    "MACDParams",
    "MACDResult",
    "RSIParams",
    "ReturnParams",
    "SMAParams",
    "TechnicalIndicators",
    "VolatilityParams",
]

__version__ = "0.1.0"

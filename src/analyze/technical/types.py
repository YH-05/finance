"""Type definitions for the technical analysis module.

This module provides type definitions for technical analysis operations including:
- Parameter types (TypedDict) for indicator functions
- Result types (TypedDict) for multi-value indicators
- Type aliases for common data structures

Type Aliases
------------
PriceSeries
    Type alias for pandas Series containing price data
ReturnSeries
    Type alias for pandas Series containing return data

Parameter Types
---------------
SMAParams
    Simple Moving Average parameters
EMAParams
    Exponential Moving Average parameters
RSIParams
    Relative Strength Index parameters
MACDParams
    Moving Average Convergence Divergence parameters
BollingerBandsParams
    Bollinger Bands parameters
VolatilityParams
    Volatility calculation parameters
ReturnParams
    Return calculation parameters

Result Types
------------
BollingerBandsResult
    Result of Bollinger Bands calculation (middle, upper, lower)
MACDResult
    Result of MACD calculation (macd, signal, histogram)

Examples
--------
>>> from analyze.technical.types import SMAParams, MACDParams
>>> params: SMAParams = {"window": 20}
>>> macd_params: MACDParams = {
...     "fast_period": 12,
...     "slow_period": 26,
...     "signal_period": 9,
... }
"""

from typing import Required, TypedDict

import pandas as pd

# =============================================================================
# Type Aliases (PEP 695 syntax for Python 3.12+)
# =============================================================================

type PriceSeries = pd.Series
"""Type alias for price data series.

A pandas Series containing price values (open, high, low, close, or adjusted close)
with a DatetimeIndex.
"""

type ReturnSeries = pd.Series
"""Type alias for return data series.

A pandas Series containing return values (simple or log returns)
with a DatetimeIndex.
"""

type IndicatorSeries = pd.Series
"""Type alias for indicator values series.

A pandas Series containing calculated indicator values
with a DatetimeIndex.
"""


# =============================================================================
# Parameter Types (TypedDict)
# =============================================================================


class SMAParams(TypedDict):
    """Parameters for Simple Moving Average (SMA) calculation.

    Parameters
    ----------
    window : int
        The number of periods to use for the moving average.
        Must be a positive integer (typically 5, 10, 20, 50, 100, or 200).

    Examples
    --------
    >>> params: SMAParams = {"window": 20}
    >>> params: SMAParams = {"window": 50}
    """

    window: Required[int]


class EMAParams(TypedDict, total=False):
    """Parameters for Exponential Moving Average (EMA) calculation.

    Parameters
    ----------
    window : int
        The number of periods to use for the EMA. Required.
        Must be a positive integer (typically 12, 26, 50, or 200).
    adjust : bool
        Whether to adjust the EMA calculation. Default is True.
        If True, uses weights (1-alpha)^i for i = 0, 1, ..., n-1.
        If False, uses recursively calculated weights.

    Examples
    --------
    >>> params: EMAParams = {"window": 12}
    >>> params: EMAParams = {"window": 26, "adjust": False}
    """

    window: Required[int]
    adjust: bool


class RSIParams(TypedDict):
    """Parameters for Relative Strength Index (RSI) calculation.

    Parameters
    ----------
    period : int
        The number of periods to use for RSI calculation.
        Standard value is 14, but 7, 21, and 28 are also common.

    Examples
    --------
    >>> params: RSIParams = {"period": 14}
    >>> params: RSIParams = {"period": 7}
    """

    period: Required[int]


class MACDParams(TypedDict, total=False):
    """Parameters for Moving Average Convergence Divergence (MACD) calculation.

    Parameters
    ----------
    fast_period : int
        The number of periods for the fast EMA. Default is 12.
    slow_period : int
        The number of periods for the slow EMA. Default is 26.
    signal_period : int
        The number of periods for the signal line EMA. Default is 9.

    Notes
    -----
    The standard MACD uses 12, 26, and 9 as periods.
    MACD line = Fast EMA - Slow EMA
    Signal line = EMA of MACD line
    Histogram = MACD line - Signal line

    Examples
    --------
    >>> params: MACDParams = {}  # Uses defaults (12, 26, 9)
    >>> params: MACDParams = {
    ...     "fast_period": 8,
    ...     "slow_period": 17,
    ...     "signal_period": 9,
    ... }
    """

    fast_period: int
    slow_period: int
    signal_period: int


class BollingerBandsParams(TypedDict, total=False):
    """Parameters for Bollinger Bands calculation.

    Parameters
    ----------
    window : int
        The number of periods for the moving average. Default is 20.
    num_std : float
        The number of standard deviations for the bands. Default is 2.0.
        Common values are 1.0, 2.0, and 3.0.

    Notes
    -----
    Bollinger Bands consist of:
    - Middle band: SMA of the price
    - Upper band: SMA + (num_std * standard deviation)
    - Lower band: SMA - (num_std * standard deviation)

    Examples
    --------
    >>> params: BollingerBandsParams = {}  # Uses defaults (20, 2.0)
    >>> params: BollingerBandsParams = {"window": 10, "num_std": 1.5}
    """

    window: int
    num_std: float


class VolatilityParams(TypedDict, total=False):
    """Parameters for volatility calculation.

    Parameters
    ----------
    window : int
        The rolling window size for volatility calculation. Default is 20.
    annualize : bool
        Whether to annualize the volatility. Default is True.
    annualization_factor : int
        The factor used for annualization. Default is 252 (trading days).
        Use 365 for calendar days, 52 for weekly data, 12 for monthly data.

    Notes
    -----
    Volatility is calculated as the standard deviation of returns.
    Annualized volatility = rolling std * sqrt(annualization_factor)

    Examples
    --------
    >>> params: VolatilityParams = {}  # Uses defaults
    >>> params: VolatilityParams = {
    ...     "window": 30,
    ...     "annualize": True,
    ...     "annualization_factor": 252,
    ... }
    """

    window: int
    annualize: bool
    annualization_factor: int


class ReturnParams(TypedDict, total=False):
    """Parameters for return calculation.

    Parameters
    ----------
    periods : int
        The number of periods for return calculation. Default is 1.
        Use 1 for daily returns, 5 for weekly, 21 for monthly, 252 for annual.
    log_return : bool
        Whether to calculate log returns instead of simple returns.
        Default is False (simple returns).

    Notes
    -----
    Simple return: (P_t - P_{t-n}) / P_{t-n}
    Log return: ln(P_t / P_{t-n})

    Examples
    --------
    >>> params: ReturnParams = {}  # Daily simple returns
    >>> params: ReturnParams = {"periods": 21, "log_return": True}  # Monthly log returns
    """

    periods: int
    log_return: bool


# =============================================================================
# Result Types (TypedDict)
# =============================================================================


class BollingerBandsResult(TypedDict):
    """Result of Bollinger Bands calculation.

    Parameters
    ----------
    middle : pd.Series
        The middle band (Simple Moving Average).
    upper : pd.Series
        The upper band (SMA + num_std * standard deviation).
    lower : pd.Series
        The lower band (SMA - num_std * standard deviation).

    Examples
    --------
    >>> result: BollingerBandsResult = {
    ...     "middle": sma_series,
    ...     "upper": upper_series,
    ...     "lower": lower_series,
    ... }
    >>> result["upper"]  # Access upper band
    """

    middle: pd.Series
    upper: pd.Series
    lower: pd.Series


class MACDResult(TypedDict):
    """Result of MACD calculation.

    Parameters
    ----------
    macd : pd.Series
        The MACD line (fast EMA - slow EMA).
    signal : pd.Series
        The signal line (EMA of MACD line).
    histogram : pd.Series
        The MACD histogram (MACD line - signal line).

    Notes
    -----
    Trading signals are often generated when:
    - MACD crosses above/below the signal line
    - MACD crosses above/below zero
    - Histogram changes from positive to negative or vice versa

    Examples
    --------
    >>> result: MACDResult = {
    ...     "macd": macd_series,
    ...     "signal": signal_series,
    ...     "histogram": histogram_series,
    ... }
    >>> result["histogram"]  # Access histogram
    """

    macd: pd.Series
    signal: pd.Series
    histogram: pd.Series


# =============================================================================
# __all__ Export
# =============================================================================

__all__ = [
    "BollingerBandsParams",
    "BollingerBandsResult",
    "EMAParams",
    "IndicatorSeries",
    "MACDParams",
    "MACDResult",
    "PriceSeries",
    "RSIParams",
    "ReturnParams",
    "ReturnSeries",
    "SMAParams",
    "VolatilityParams",
]

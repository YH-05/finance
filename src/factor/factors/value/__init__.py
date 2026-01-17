"""Value factors package.

This package provides value-based factor implementations including:
- ValueFactor: Computes valuation metrics (PER, PBR, dividend yield, EV/EBITDA)

Examples
--------
>>> from factor.factors.value import ValueFactor
>>>
>>> # Create a PER-based value factor
>>> per_factor = ValueFactor(metric="per", invert=True)
>>>
>>> # Create a dividend yield factor
>>> div_factor = ValueFactor(metric="dividend_yield", invert=False)
"""

from .value import ValueFactor

__all__ = ["ValueFactor"]

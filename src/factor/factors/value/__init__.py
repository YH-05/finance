"""Value factors package.

This package provides value-based factor implementations including:
- ValueFactor: Computes valuation metrics (PER, PBR, dividend yield, EV/EBITDA)
- CompositeValueFactor: Combines multiple valuation metrics with custom weights

Examples
--------
>>> from factor.factors.value import ValueFactor, CompositeValueFactor
>>>
>>> # Create a PER-based value factor
>>> per_factor = ValueFactor(metric="per", invert=True)
>>>
>>> # Create a dividend yield factor
>>> div_factor = ValueFactor(metric="dividend_yield", invert=False)
>>>
>>> # Create a composite value factor combining PER and PBR
>>> composite = CompositeValueFactor(
...     metrics=["per", "pbr"],
...     weights=[0.6, 0.4],
... )
"""

from .composite import CompositeValueFactor
from .value import ValueFactor

__all__ = ["CompositeValueFactor", "ValueFactor"]

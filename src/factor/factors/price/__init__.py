"""Price-based factor implementations.

このモジュールは価格ベースのファクター実装を提供します:
- VolatilityFactor: 価格ボラティリティ
"""

from factor.factors.price.volatility import VolatilityFactor

__all__ = [
    "VolatilityFactor",
]

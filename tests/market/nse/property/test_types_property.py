"""Property-based tests for market.nse.types module.

Uses Hypothesis to verify invariant properties of CorporateShareHolding's
``to_float_*()`` accessor methods: they must never raise an exception and
must return either ``None`` or a ``float``.

Test TODO List:
- [x] to_float_promoter_group_pct: arbitrary text never raises, result is None | float
- [x] to_float_public_pct: arbitrary text never raises, result is None | float
- [x] to_float_employee_trust_pct: arbitrary text never raises, result is None | float
"""

from __future__ import annotations

from hypothesis import given, settings
from hypothesis import strategies as st

from market.nse.types import CorporateShareHolding

# =============================================================================
# to_float_* properties
# =============================================================================


class TestCorporateShareHoldingToFloatProperty:
    """Hypothesis property tests for CorporateShareHolding.to_float_*()."""

    @given(value=st.text(max_size=200))
    @settings(max_examples=200)
    def test_プロパティ_to_float_promoter_group_pctは例外非送出(
        self, value: str
    ) -> None:
        """任意の文字列入力で to_float_promoter_group_pct() が例外を送出しないこと。"""
        holding = CorporateShareHolding(
            symbol="TESTCO",
            as_on_date="31-Dec-2025",
            promoter_group_pct=value,
            public_pct="0",
        )
        result = holding.to_float_promoter_group_pct()
        assert result is None or isinstance(result, float)

    @given(value=st.text(max_size=200))
    @settings(max_examples=200)
    def test_プロパティ_to_float_public_pctは例外非送出(self, value: str) -> None:
        """任意の文字列入力で to_float_public_pct() が例外を送出しないこと。"""
        holding = CorporateShareHolding(
            symbol="TESTCO",
            as_on_date="31-Dec-2025",
            promoter_group_pct="0",
            public_pct=value,
        )
        result = holding.to_float_public_pct()
        assert result is None or isinstance(result, float)

    @given(value=st.text(max_size=200))
    @settings(max_examples=200)
    def test_プロパティ_to_float_employee_trust_pctは例外非送出(
        self, value: str
    ) -> None:
        """任意の文字列入力で to_float_employee_trust_pct() が例外を送出しないこと。"""
        holding = CorporateShareHolding(
            symbol="TESTCO",
            as_on_date="31-Dec-2025",
            promoter_group_pct="0",
            public_pct="0",
            employee_trust_pct=value,
        )
        result = holding.to_float_employee_trust_pct()
        assert result is None or isinstance(result, float)

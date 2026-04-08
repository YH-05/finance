"""Property-based tests for market.pipeline.collector_sec module.

Uses Hypothesis to verify invariant properties of numeric extraction functions.

Test TODO List:
- [x] _extract_operating_cashflow_fallback: NaN/Inf/negative values never raise exception
- [x] _extract_operating_cashflow_fallback: valid float concept value returns float
- [x] _extract_operating_cashflow_fallback: result is always float | None
- [x] _safe_float: arbitrary input never raises exception, result is float | None
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pandas as pd
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from market.pipeline.collector_sec import (
    _extract_operating_cashflow_fallback,
    _safe_float,
)

# ---------------------------------------------------------------------------
# Strategy helpers
# ---------------------------------------------------------------------------

# A known operating cashflow concept key that _extract_operating_cashflow_fallback
# will match via _OPERATING_CF_CONCEPTS.
_KNOWN_CONCEPT = "NetCashProvidedByUsedInOperatingActivities"

_any_numeric = st.one_of(
    st.floats(),  # includes NaN, Inf, -Inf
    st.integers(),
    st.none(),
)


def _make_financials_mock(cf_df: pd.DataFrame | None) -> MagicMock:
    mock_financials = MagicMock()
    if cf_df is None:
        mock_financials.cashflow_statement.return_value = None
    else:
        mock_cf_stmt = MagicMock()
        mock_cf_stmt.to_dataframe.return_value = cf_df
        mock_financials.cashflow_statement.return_value = mock_cf_stmt
    return mock_financials


# =============================================================================
# _extract_operating_cashflow_fallback properties
# =============================================================================


class TestExtractOperatingCashflowFallbackProperty:
    """Hypothesis property tests for _extract_operating_cashflow_fallback."""

    @given(value=_any_numeric)
    @settings(max_examples=300)
    def test_プロパティ_任意数値セルで例外が発生しない(self, value: object) -> None:
        """概念列に任意の数値（NaN/Inf/負値/None）が入っても例外を送出しないこと。"""
        df = pd.DataFrame(
            [{"concept": _KNOWN_CONCEPT, "label": "Net Cash", "2024-12-31": value}]
        )
        mock_financials = _make_financials_mock(df)
        result = _extract_operating_cashflow_fallback(mock_financials)
        # 結果は float | None のいずれか
        assert result is None or isinstance(result, float)

    @given(
        value=st.floats(
            min_value=-1e15,
            max_value=1e15,
            allow_nan=False,
            allow_infinity=False,
        )
    )
    @settings(max_examples=200)
    def test_プロパティ_有限float値はfloatを返す(self, value: float) -> None:
        """有限 float 値が入ったセルでは float 型の結果を返すこと。"""
        df = pd.DataFrame(
            [{"concept": _KNOWN_CONCEPT, "label": "Net Cash", "2024-12-31": value}]
        )
        mock_financials = _make_financials_mock(df)
        result = _extract_operating_cashflow_fallback(mock_financials)
        assert isinstance(result, float)
        assert result == pytest.approx(value)

    @given(
        rows=st.lists(
            st.fixed_dictionaries(
                {
                    "concept": st.text(max_size=80),
                    "label": st.text(max_size=80),
                    "2024-12-31": _any_numeric,
                }
            ),
            max_size=10,
        )
    )
    @settings(max_examples=100)
    def test_プロパティ_任意行を持つDataFrameで例外が発生しない(
        self, rows: list[dict[str, object]]
    ) -> None:
        """任意の concept/label/値を持つ DataFrame でも例外を送出しないこと。"""
        df = pd.DataFrame(rows) if rows else pd.DataFrame()
        mock_financials = _make_financials_mock(df)
        result = _extract_operating_cashflow_fallback(mock_financials)
        assert result is None or isinstance(result, float)


# =============================================================================
# _safe_float properties
# =============================================================================


class TestSafeFloatProperty:
    """Hypothesis property tests for _safe_float."""

    @given(
        value=st.one_of(st.text(), st.integers(), st.floats(), st.none(), st.binary())
    )
    @settings(max_examples=300)
    def test_プロパティ_任意入力で例外が発生しない(self, value: object) -> None:
        """任意の型・値を渡しても例外を送出しないこと（クラッシュ安全性）。"""
        result = _safe_float(value)
        assert result is None or isinstance(result, float)

    @given(
        value=st.floats(
            min_value=-1e15,
            max_value=1e15,
            allow_nan=False,
            allow_infinity=False,
        )
    )
    @settings(max_examples=200)
    def test_プロパティ_有限floatは値を保持する(self, value: float) -> None:
        """有限 float 値はそのまま float として返すこと。"""
        result = _safe_float(value)
        assert result == pytest.approx(value)

    @given(value=st.integers(min_value=-(10**15), max_value=10**15))
    @settings(max_examples=200)
    def test_プロパティ_整数はfloatに変換される(self, value: int) -> None:
        """整数値は float に変換されること。"""
        result = _safe_float(value)
        assert isinstance(result, float)
        assert result == pytest.approx(float(value))

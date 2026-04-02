"""Property-based tests for market.nse.parsers module.

Uses Hypothesis to verify invariant properties of cleaning functions
and missing value handling.

Test TODO List:
- [x] clean_price: arbitrary string never raises exception, result is float|None
- [x] clean_volume: arbitrary string never raises exception, result is int|None
- [x] clean_indian_number: arbitrary string never raises exception, result is float|None
- [x] clean_price: finite floats produce float results (type preservation)
- [x] clean_volume: non-negative ints produce int results (type preservation)
- [x] clean_indian_number: float input round-trips correctly
- [x] _MISSING_VALUES: all sentinel values produce None across all cleaners
- [x] clean_price: NaN/inf safety (non-finite values return None)
- [x] clean_volume: NaN/inf safety (non-finite values return None)
- [x] clean_price: integer inputs always produce float results
- [x] clean_volume: integer inputs always produce int results
"""

import math

from hypothesis import given, settings
from hypothesis import strategies as st

from market.nse.parsers import (
    _MISSING_VALUES,
    clean_indian_number,
    clean_price,
    clean_volume,
)

# =============================================================================
# Strategies
# =============================================================================

finite_floats = st.floats(
    min_value=-1e12,
    max_value=1e12,
    allow_nan=False,
    allow_infinity=False,
)
"""Finite float strategy for generating valid numeric values."""

non_negative_ints = st.integers(min_value=0, max_value=10**9)
"""Non-negative integer strategy for volume-like values."""

non_finite_floats = st.sampled_from([float("nan"), float("inf"), float("-inf")])
"""Non-finite float strategy for testing NaN/inf safety."""


# =============================================================================
# clean_price properties
# =============================================================================


class TestCleanPriceProperty:
    """Hypothesis property tests for clean_price."""

    @given(value=st.text(max_size=200))
    @settings(max_examples=200)
    def test_プロパティ_任意文字列入力で例外が発生しない(self, value: str) -> None:
        """任意の文字列を入力しても例外が発生しないこと。"""
        result = clean_price(value)
        assert result is None or isinstance(result, float)

    @given(number=finite_floats)
    @settings(max_examples=100)
    def test_プロパティ_有効な数値文字列はfloat型を返す(self, number: float) -> None:
        """有効な数値文字列は float 型の結果を返すこと（型保持）。"""
        value = f"{number:,.2f}"
        result = clean_price(value)
        assert result is not None
        assert isinstance(result, float)

    @given(number=non_finite_floats)
    def test_プロパティ_非有限値文字列はNoneを返す(self, number: float) -> None:
        """NaN, inf, -inf の文字列表現は None を返すこと（NaN安全性）。"""
        result = clean_price(str(number))
        assert result is None

    @given(number=non_finite_floats)
    def test_プロパティ_非有限float直接入力はNoneを返す(self, number: float) -> None:
        """NaN, inf, -inf を直接入力すると None を返すこと。"""
        result = clean_price(number)
        assert result is None

    @given(value=st.sampled_from(list(_MISSING_VALUES)))
    def test_プロパティ_欠損値センチネルはNoneを返す(self, value: str) -> None:
        """_MISSING_VALUES の全センチネル値で None を返すこと。"""
        assert clean_price(value) is None

    @given(number=st.integers(min_value=-(10**9), max_value=10**9))
    @settings(max_examples=100)
    def test_プロパティ_整数入力はfloatを返す(self, number: int) -> None:
        """整数を直接入力すると float を返すこと。"""
        result = clean_price(number)
        assert result is not None
        assert isinstance(result, float)
        assert result == float(number)

    @given(number=finite_floats)
    @settings(max_examples=100)
    def test_プロパティ_float直接入力は同値を返す(self, number: float) -> None:
        """有限 float を直接入力すると同じ値を返すこと。"""
        result = clean_price(number)
        assert result is not None
        assert isinstance(result, float)
        assert math.isclose(result, number, rel_tol=1e-9)


# =============================================================================
# clean_volume properties
# =============================================================================


class TestCleanVolumeProperty:
    """Hypothesis property tests for clean_volume."""

    @given(value=st.text(max_size=200))
    @settings(max_examples=200)
    def test_プロパティ_任意文字列入力で例外が発生しない(self, value: str) -> None:
        """任意の文字列を入力しても例外が発生しないこと。"""
        result = clean_volume(value)
        assert result is None or isinstance(result, int)

    @given(number=non_negative_ints)
    @settings(max_examples=100)
    def test_プロパティ_非負整数はint型を返す(self, number: int) -> None:
        """非負整数を入力すると int 型の結果を返すこと（型保持）。"""
        result = clean_volume(number)
        assert result is not None
        assert isinstance(result, int)
        assert result == number

    @given(number=non_negative_ints)
    @settings(max_examples=100)
    def test_プロパティ_整数文字列はint型を返す(self, number: int) -> None:
        """整数の文字列表現を入力すると int 型の結果を返すこと。"""
        result = clean_volume(str(number))
        assert result is not None
        assert isinstance(result, int)
        assert result == number

    @given(number=non_finite_floats)
    def test_プロパティ_非有限float直接入力はNoneを返す(self, number: float) -> None:
        """NaN, inf, -inf を直接入力すると None を返すこと。"""
        result = clean_volume(number)
        assert result is None

    @given(value=st.sampled_from(list(_MISSING_VALUES)))
    def test_プロパティ_欠損値センチネルはNoneを返す(self, value: str) -> None:
        """_MISSING_VALUES の全センチネル値で None を返すこと。"""
        assert clean_volume(value) is None


# =============================================================================
# clean_indian_number properties
# =============================================================================


class TestCleanIndianNumberProperty:
    """Hypothesis property tests for clean_indian_number."""

    @given(value=st.text(max_size=200))
    @settings(max_examples=200)
    def test_プロパティ_任意文字列入力で例外が発生しない(self, value: str) -> None:
        """任意の文字列を入力しても例外が発生しないこと。"""
        result = clean_indian_number(value)
        assert result is None or isinstance(result, float)

    @given(number=finite_floats)
    @settings(max_examples=100)
    def test_プロパティ_有限floatはfloat型を返す(self, number: float) -> None:
        """有限 float を直接入力すると float 型の結果を返すこと。"""
        result = clean_indian_number(number)
        assert result is not None
        assert isinstance(result, float)
        assert math.isclose(result, number, rel_tol=1e-9)

    @given(number=st.integers(min_value=0, max_value=10**12))
    @settings(max_examples=100)
    def test_プロパティ_カンマなし数値文字列は同値を返す(self, number: int) -> None:
        """カンマなし数値文字列を入力すると同じ値を返すこと（ラウンドトリップ）。"""
        result = clean_indian_number(str(number))
        assert result is not None
        assert math.isclose(result, float(number), rel_tol=1e-9)

    @given(number=non_finite_floats)
    def test_プロパティ_非有限float直接入力はNoneを返す(self, number: float) -> None:
        """NaN, inf, -inf を直接入力すると None を返すこと。"""
        result = clean_indian_number(number)
        assert result is None

    @given(value=st.sampled_from(list(_MISSING_VALUES)))
    def test_プロパティ_欠損値センチネルはNoneを返す(self, value: str) -> None:
        """_MISSING_VALUES の全センチネル値で None を返すこと。"""
        assert clean_indian_number(value) is None

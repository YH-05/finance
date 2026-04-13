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
- [x] parse_financial_results: total_income fallback calculation is accurate
- [x] NseConfig: valid range values never raise ValueError
- [x] NseConfig: invalid timeout range raises ValueError
- [x] parse_shareholding_pattern: arbitrary list of dicts never raises exception
- [x] parse_shareholding_pattern: all result fields are str type
- [x] parse_shareholding_pattern: non-list input always raises NseParseError
- [x] parse_corporate_shareholding: arbitrary list[dict] never raises exception
- [x] parse_corporate_shareholding: all fields of every record are str type
"""

import dataclasses
import math

import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

from market.nse.errors import NseParseError
from market.nse.parsers import (
    _MISSING_VALUES,
    clean_indian_number,
    clean_price,
    clean_volume,
    parse_corporate_shareholding,
    parse_financial_results,
    parse_shareholding_pattern,
)
from market.nse.types import CorporateShareHolding, ShareholdingPattern

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


# =============================================================================
# parse_financial_results properties
# =============================================================================


class TestParseFinancialResultsTotalIncomeProperty:
    """Hypothesis property tests for parse_financial_results total_income fallback."""

    @given(
        net_sale=st.floats(
            min_value=0, max_value=1e12, allow_nan=False, allow_infinity=False
        ),
        other_income=st.floats(
            min_value=0, max_value=1e12, allow_nan=False, allow_infinity=False
        ),
    )
    @settings(max_examples=100)
    def test_プロパティ_total_income_フォールバック計算が正確(
        self, net_sale: float, other_income: float
    ) -> None:
        """re_total_inc がない場合 re_net_sale + re_oth_inc_new になること。

        3段階フォールバックの第3段階 (net_sale + other_income) を検証する。
        """
        item = {
            "re_net_sale": str(net_sale),
            "re_oth_inc_new": str(other_income),
        }
        raw = {"resCmpData": [item]}
        results = parse_financial_results(raw)

        assert len(results) == 1
        income_str = results[0].income
        if income_str:
            parsed = clean_price(income_str)
            expected = net_sale + other_income
            assert parsed is not None
            assert math.isclose(parsed, expected, rel_tol=1e-6)

    @given(
        total_inc=st.floats(
            min_value=0.01, max_value=1e12, allow_nan=False, allow_infinity=False
        ),
    )
    @settings(max_examples=100)
    def test_プロパティ_total_income_re_total_incが優先される(
        self, total_inc: float
    ) -> None:
        """re_total_inc が正値の場合はその値が優先されること（フォールバック第1段階）。

        Notes
        -----
        フォールバック計算は ``or`` 演算子を使用するため、0.0 は falsy として
        扱われ次のフォールバックに進む。このテストは非ゼロ正値のみを対象とする。
        """
        item = {
            "re_total_inc": str(total_inc),
            "re_net_sale": "999999.0",
            "re_oth_inc_new": "999999.0",
        }
        raw = {"resCmpData": [item]}
        results = parse_financial_results(raw)

        assert len(results) == 1
        income_str = results[0].income
        if income_str:
            parsed = clean_price(income_str)
            assert parsed is not None
            assert math.isclose(parsed, total_inc, rel_tol=1e-6)


# =============================================================================
# NseConfig boundary value properties
# =============================================================================


class TestNseConfigBoundaryProperty:
    """Hypothesis property tests for NseConfig validation boundaries."""

    @given(
        timeout=st.floats(
            min_value=1.0, max_value=300.0, allow_nan=False, allow_infinity=False
        ),
        polite_delay=st.floats(
            min_value=0.0, max_value=60.0, allow_nan=False, allow_infinity=False
        ),
        delay_jitter=st.floats(
            min_value=0.0, max_value=30.0, allow_nan=False, allow_infinity=False
        ),
        cookie_refresh_interval=st.floats(
            min_value=10.0, max_value=3600.0, allow_nan=False, allow_infinity=False
        ),
    )
    @settings(max_examples=100)
    def test_プロパティ_NseConfig有効範囲内ではValueError不送出(
        self,
        timeout: float,
        polite_delay: float,
        delay_jitter: float,
        cookie_refresh_interval: float,
    ) -> None:
        """有効範囲内の値で NseConfig が正常に作成されること。"""
        from market.nse.types import NseConfig

        config = NseConfig(
            timeout=timeout,
            polite_delay=polite_delay,
            delay_jitter=delay_jitter,
            cookie_refresh_interval=cookie_refresh_interval,
        )
        assert config.timeout == pytest.approx(timeout)
        assert config.polite_delay == pytest.approx(polite_delay)
        assert config.delay_jitter == pytest.approx(delay_jitter)
        assert config.cookie_refresh_interval == pytest.approx(cookie_refresh_interval)

    @given(
        timeout=st.one_of(
            st.floats(max_value=0.99, allow_nan=False, allow_infinity=False),
            st.floats(min_value=300.01, allow_nan=False, allow_infinity=False),
        ),
    )
    @settings(max_examples=100)
    def test_プロパティ_NseConfig無効timeout範囲でValueError(
        self, timeout: float
    ) -> None:
        """有効範囲外の timeout で ValueError が送出されること。"""
        assume(not math.isnan(timeout) and not math.isinf(timeout))
        from market.nse.types import NseConfig

        with pytest.raises(ValueError):
            NseConfig(timeout=timeout)

    @given(
        polite_delay=st.one_of(
            st.floats(max_value=-0.01, allow_nan=False, allow_infinity=False),
            st.floats(min_value=60.01, allow_nan=False, allow_infinity=False),
        ),
    )
    @settings(max_examples=100)
    def test_プロパティ_NseConfig無効polite_delay範囲でValueError(
        self, polite_delay: float
    ) -> None:
        """有効範囲外の polite_delay で ValueError が送出されること。"""
        assume(not math.isnan(polite_delay) and not math.isinf(polite_delay))
        from market.nse.types import NseConfig

        with pytest.raises(ValueError):
            NseConfig(polite_delay=polite_delay)

    @given(
        delay_jitter=st.one_of(
            st.floats(max_value=-0.01, allow_nan=False, allow_infinity=False),
            st.floats(min_value=30.01, allow_nan=False, allow_infinity=False),
        ),
    )
    @settings(max_examples=100)
    def test_プロパティ_NseConfig無効delay_jitter範囲でValueError(
        self, delay_jitter: float
    ) -> None:
        """有効範囲外の delay_jitter で ValueError が送出されること。"""
        assume(not math.isnan(delay_jitter) and not math.isinf(delay_jitter))
        from market.nse.types import NseConfig

        with pytest.raises(ValueError):
            NseConfig(delay_jitter=delay_jitter)

    @given(
        cookie_refresh_interval=st.one_of(
            st.floats(max_value=9.99, allow_nan=False, allow_infinity=False),
            st.floats(min_value=3600.01, allow_nan=False, allow_infinity=False),
        ),
    )
    @settings(max_examples=100)
    def test_プロパティ_NseConfig無効cookie_refresh_interval範囲でValueError(
        self, cookie_refresh_interval: float
    ) -> None:
        """有効範囲外の cookie_refresh_interval で ValueError が送出されること。"""
        assume(
            not math.isnan(cookie_refresh_interval)
            and not math.isinf(cookie_refresh_interval)
        )
        from market.nse.types import NseConfig

        with pytest.raises(ValueError):
            NseConfig(cookie_refresh_interval=cookie_refresh_interval)


# =============================================================================
# parse_shareholding_pattern properties
# =============================================================================

# Strategy: arbitrary nested dict mimicking NextApi getShareholdingPattern response
# Each value is a dict with arbitrary text keys/values (simulating record dicts)
_shareholding_record_strategy = st.dictionaries(
    keys=st.text(max_size=50),
    values=st.one_of(
        st.text(max_size=100),
        st.dictionaries(st.text(max_size=20), st.text(max_size=50), max_size=3),
        st.none(),
    ),
    max_size=10,
)
_shareholding_data_strategy = st.dictionaries(
    keys=st.text(max_size=30),
    values=_shareholding_record_strategy,
    max_size=10,
)


class TestParseShareholdingPatternProperty:
    """Hypothesis property tests for parse_shareholding_pattern."""

    @given(data=_shareholding_data_strategy)
    @settings(max_examples=200)
    def test_プロパティ_任意dictで例外が発生しない(
        self, data: dict[str, dict[str, object]]
    ) -> None:
        """任意の dict[str, dict] を渡しても例外を送出しないこと（クラッシュ安全性）。"""
        result = parse_shareholding_pattern(data)  # type: ignore[arg-type]
        assert isinstance(result, list)

    @given(data=_shareholding_data_strategy)
    @settings(max_examples=100)
    def test_プロパティ_結果の全フィールドがstr型(
        self, data: dict[str, dict[str, object]]
    ) -> None:
        """結果の ShareholdingPattern 各フィールドが常に str 型であること。"""
        results = parse_shareholding_pattern(data)  # type: ignore[arg-type]
        for item in results:
            assert isinstance(item, ShareholdingPattern)
            assert isinstance(item.symbol, str)
            assert isinstance(item.date, str)
            assert isinstance(item.ndsid, str)
            assert isinstance(item.series, str)
            assert isinstance(item.total, str)
            assert isinstance(item.promoter_group, str)
            assert isinstance(item.public, str)

    @given(
        non_dict=st.one_of(
            st.lists(st.dictionaries(st.text(), st.text()), max_size=5),
            st.integers(),
            st.text(),
            st.none(),
            st.floats(allow_nan=False, allow_infinity=False),
        )
    )
    @settings(max_examples=100)
    def test_プロパティ_非dict入力で常にNseParseError(self, non_dict: object) -> None:
        """dict 以外の入力は常に NseParseError を送出すること。"""
        with pytest.raises(NseParseError):
            parse_shareholding_pattern(non_dict)  # type: ignore[arg-type]


# =============================================================================
# parse_corporate_shareholding properties
# =============================================================================

# Strategy: arbitrary list of dicts with mixed value types. Each dict may
# contain keys matching NSE's corporate-share-holdings-master response
# (``symbol``, ``date``, ``pr_and_prgrp``, ``public_val`` など) as well as
# junk keys. Values are text or None.
_corporate_record_strategy = st.dictionaries(
    keys=st.text(max_size=30),
    values=st.one_of(st.text(max_size=100), st.none()),
    max_size=10,
)
_corporate_data_strategy = st.lists(_corporate_record_strategy, max_size=5)


class TestParseCorporateShareholdingProperty:
    """Hypothesis property tests for parse_corporate_shareholding."""

    @given(data=_corporate_data_strategy)
    @settings(max_examples=200)
    def test_プロパティ_任意list_dict入力で例外非送出(
        self, data: list[dict[str, object]]
    ) -> None:
        """任意の list[dict] を渡しても例外を送出しないこと。

        result は list であり、各要素は CorporateShareHolding、かつ全フィールドが str 型。
        """
        result = parse_corporate_shareholding(data)  # type: ignore[arg-type]
        assert isinstance(result, list)
        for item in result:
            assert isinstance(item, CorporateShareHolding)
            for field in dataclasses.fields(item):
                assert isinstance(getattr(item, field.name), str), (
                    f"field {field.name} is not str"
                )

    @given(
        data=st.lists(
            st.dictionaries(
                keys=st.sampled_from(
                    [
                        "symbol",
                        "date",
                        "pr_and_prgrp",
                        "public_val",
                        "employeeTrusts",
                        "submissionDate",
                        "broadcastDate",
                        "xbrl",
                    ]
                ),
                values=st.text(max_size=100),
                max_size=8,
            ),
            max_size=5,
        )
    )
    @settings(max_examples=100)
    def test_プロパティ_想定キーのみでも例外非送出(
        self, data: list[dict[str, str]]
    ) -> None:
        """NSE API の想定キーのみを持つ入力でも例外を送出しないこと。"""
        result = parse_corporate_shareholding(data)
        assert isinstance(result, list)
        assert len(result) == len(data)

    @given(
        non_list=st.one_of(
            st.dictionaries(st.text(), st.text(), max_size=3),
            st.integers(),
            st.text(),
            st.none(),
        )
    )
    @settings(max_examples=100)
    def test_プロパティ_非list入力で常にNseParseError(self, non_list: object) -> None:
        """list 以外の入力は常に NseParseError を送出すること。"""
        with pytest.raises(NseParseError):
            parse_corporate_shareholding(non_list)  # type: ignore[arg-type]

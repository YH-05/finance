"""Property-based tests for market.nasdaq.parser module.

Uses Hypothesis to verify that all cleaning functions handle arbitrary
string inputs without raising exceptions, and that parse_screener_response
produces consistent output shapes.

Test TODO List:
- [x] clean_price: arbitrary string never raises exception
- [x] clean_percentage: arbitrary string never raises exception
- [x] clean_market_cap: arbitrary string never raises exception
- [x] clean_volume: arbitrary string never raises exception
- [x] clean_ipo_year: arbitrary string never raises exception
- [x] clean_price: valid numeric strings produce float results
- [x] parse_screener_response: valid rows produce correct column count
"""

from typing import Any

import pandas as pd
from hypothesis import given, settings
from hypothesis import strategies as st

from market.nasdaq.parser import (
    clean_ipo_year,
    clean_market_cap,
    clean_percentage,
    clean_price,
    clean_volume,
    parse_screener_response,
)

# =============================================================================
# Cleaning function robustness properties
# =============================================================================


class TestCleanPriceProperty:
    """Hypothesis property tests for clean_price."""

    @given(value=st.text(max_size=200))
    @settings(max_examples=200)
    def test_プロパティ_任意文字列入力で例外が発生しない(self, value: str) -> None:
        """任意の文字列を入力しても例外が発生しないこと。"""
        result = clean_price(value)
        assert result is None or isinstance(result, float)

    @given(
        number=st.floats(
            min_value=-1e12,
            max_value=1e12,
            allow_nan=False,
            allow_infinity=False,
        )
    )
    @settings(max_examples=100)
    def test_プロパティ_有効な数値文字列はfloatを返す(self, number: float) -> None:
        """有効な数値文字列は float 型の結果を返すこと。"""
        # Format as a dollar-sign price
        value = f"${number:,.2f}"
        result = clean_price(value)
        assert result is not None
        assert isinstance(result, float)


class TestCleanPercentageProperty:
    """Hypothesis property tests for clean_percentage."""

    @given(value=st.text(max_size=200))
    @settings(max_examples=200)
    def test_プロパティ_任意文字列入力で例外が発生しない(self, value: str) -> None:
        """任意の文字列を入力しても例外が発生しないこと。"""
        result = clean_percentage(value)
        assert result is None or isinstance(result, float)


class TestCleanMarketCapProperty:
    """Hypothesis property tests for clean_market_cap."""

    @given(value=st.text(max_size=200))
    @settings(max_examples=200)
    def test_プロパティ_任意文字列入力で例外が発生しない(self, value: str) -> None:
        """任意の文字列を入力しても例外が発生しないこと。"""
        result = clean_market_cap(value)
        assert result is None or isinstance(result, int)


class TestCleanVolumeProperty:
    """Hypothesis property tests for clean_volume."""

    @given(value=st.text(max_size=200))
    @settings(max_examples=200)
    def test_プロパティ_任意文字列入力で例外が発生しない(self, value: str) -> None:
        """任意の文字列を入力しても例外が発生しないこと。"""
        result = clean_volume(value)
        assert result is None or isinstance(result, int)


class TestCleanIpoYearProperty:
    """Hypothesis property tests for clean_ipo_year."""

    @given(value=st.text(max_size=200))
    @settings(max_examples=200)
    def test_プロパティ_任意文字列入力で例外が発生しない(self, value: str) -> None:
        """任意の文字列を入力しても例外が発生しないこと。"""
        result = clean_ipo_year(value)
        assert result is None or isinstance(result, int)


# =============================================================================
# parse_screener_response properties
# =============================================================================


def _make_row(**overrides: str) -> dict[str, str]:
    """Create a valid API row dict with optional overrides."""
    row: dict[str, str] = {
        "symbol": "TEST",
        "name": "Test Corp.",
        "lastsale": "$100.00",
        "netchange": "1.50",
        "pctchange": "1.5%",
        "marketCap": "1,000,000",
        "country": "United States",
        "ipoyear": "2020",
        "volume": "10,000",
        "sector": "Technology",
        "industry": "Software",
        "url": "/market-activity/stocks/test",
    }
    row.update(overrides)
    return row


class TestParseScreenerResponseProperty:
    """Hypothesis property tests for parse_screener_response."""

    @given(
        num_rows=st.integers(min_value=1, max_value=50),
    )
    @settings(max_examples=50)
    def test_プロパティ_有効な行数で正しいDataFrame行数を返す(
        self, num_rows: int
    ) -> None:
        """N 行のレスポンスから N 行の DataFrame が生成されること。"""
        rows: list[dict[str, str]] = [
            _make_row(symbol=f"T{i}") for i in range(num_rows)
        ]
        response: dict[str, Any] = {"data": {"table": {"rows": rows}}}

        df = parse_screener_response(response)

        assert isinstance(df, pd.DataFrame)
        assert len(df) == num_rows
        # All expected columns must be present
        expected_columns = {
            "symbol",
            "name",
            "last_sale",
            "net_change",
            "pct_change",
            "market_cap",
            "country",
            "ipo_year",
            "volume",
            "sector",
            "industry",
            "url",
        }
        assert expected_columns.issubset(set(df.columns))

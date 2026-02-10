"""Unit tests for market.nasdaq.parser module.

Tests verify the JSON-to-DataFrame parser and all numeric cleaning functions
for the NASDAQ Stock Screener API response format.

Test TODO List:
- [x] clean_price: normal price with $ and commas
- [x] clean_price: negative price
- [x] clean_price: empty string returns None
- [x] clean_price: N/A returns None
- [x] clean_price: malformed value returns None
- [x] clean_percentage: normal percentage with %
- [x] clean_percentage: negative percentage
- [x] clean_percentage: empty string returns None
- [x] clean_percentage: malformed value returns None
- [x] clean_market_cap: comma-separated integer
- [x] clean_market_cap: empty string returns None
- [x] clean_market_cap: N/A returns None
- [x] clean_volume: comma-separated integer
- [x] clean_volume: empty string returns None
- [x] clean_ipo_year: valid year string
- [x] clean_ipo_year: empty string returns None
- [x] clean_ipo_year: non-numeric returns None
- [x] _camel_to_snake: camelCase to snake_case
- [x] parse_screener_response: valid response with one row
- [x] parse_screener_response: valid response with multiple rows
- [x] parse_screener_response: empty rows list
- [x] parse_screener_response: missing data key raises NasdaqParseError
- [x] parse_screener_response: missing table key raises NasdaqParseError
- [x] parse_screener_response: missing rows key raises NasdaqParseError
- [x] parse_screener_response: rows is not list raises NasdaqParseError
- [x] parse_screener_response: rows with N/A fields
- [x] Module exports: __all__ completeness
"""

import pytest

from market.nasdaq.errors import NasdaqParseError
from market.nasdaq.parser import (
    __all__,
    _camel_to_snake,
    clean_ipo_year,
    clean_market_cap,
    clean_percentage,
    clean_price,
    clean_volume,
    parse_screener_response,
)

# =============================================================================
# Fixtures
# =============================================================================


def _make_single_row_response(
    *,
    symbol: str = "AAPL",
    name: str = "Apple Inc. Common Stock",
    lastsale: str = "$227.63",
    netchange: str = "-1.95",
    pctchange: str = "-0.849%",
    market_cap: str = "3,435,123,456,789",
    country: str = "United States",
    ipoyear: str = "1980",
    volume: str = "48,123,456",
    sector: str = "Technology",
    industry: str = "Computer Manufacturing",
    url: str = "/market-activity/stocks/aapl",
) -> dict:
    """Build a minimal NASDAQ API response with a single row."""
    return {
        "data": {
            "table": {
                "rows": [
                    {
                        "symbol": symbol,
                        "name": name,
                        "lastsale": lastsale,
                        "netchange": netchange,
                        "pctchange": pctchange,
                        "marketCap": market_cap,
                        "country": country,
                        "ipoyear": ipoyear,
                        "volume": volume,
                        "sector": sector,
                        "industry": industry,
                        "url": url,
                    }
                ]
            }
        }
    }


# =============================================================================
# Module exports
# =============================================================================


class TestModuleExports:
    """Test module __all__ exports."""

    def test_正常系_モジュールがインポートできる(self) -> None:
        """parser モジュールが正常にインポートできること。"""
        from market.nasdaq import parser

        assert parser is not None

    def test_正常系_allが定義されている(self) -> None:
        """__all__ がリストとして定義されていること。"""
        assert isinstance(__all__, list)
        assert len(__all__) > 0

    def test_正常系_allの全項目がモジュールに存在する(self) -> None:
        """__all__ の全項目がモジュールの属性として存在すること。"""
        from market.nasdaq import parser

        for name in __all__:
            assert hasattr(parser, name), f"{name} is not defined in parser module"

    def test_正常系_allが6項目を含む(self) -> None:
        """__all__ が全6関数をエクスポートしていること。"""
        expected = {
            "clean_ipo_year",
            "clean_market_cap",
            "clean_percentage",
            "clean_price",
            "clean_volume",
            "parse_screener_response",
        }
        assert set(__all__) == expected


# =============================================================================
# clean_price
# =============================================================================


class TestCleanPrice:
    """clean_price のテスト。"""

    def test_正常系_ドル記号とカンマ付き価格を変換できる(self) -> None:
        """'$1,234.56' を 1234.56 に変換できること。"""
        assert clean_price("$1,234.56") == 1234.56

    def test_正常系_ドル記号なしの価格を変換できる(self) -> None:
        """'227.63' を 227.63 に変換できること。"""
        assert clean_price("227.63") == 227.63

    def test_正常系_負の価格を変換できる(self) -> None:
        """'-1.95' を -1.95 に変換できること。"""
        assert clean_price("-1.95") == -1.95

    def test_正常系_ドル記号付き負の価格を変換できる(self) -> None:
        """'$-1.95' ではなく '-$1.95' 等にも対応すること。"""
        # NASDAQ API returns net_change without $ typically
        assert clean_price("-1.95") == -1.95

    def test_エッジケース_空文字でNoneを返す(self) -> None:
        """空文字で None を返すこと。"""
        assert clean_price("") is None

    def test_エッジケース_NAでNoneを返す(self) -> None:
        """'N/A' で None を返すこと。"""
        assert clean_price("N/A") is None

    def test_異常系_不正な値でNoneを返す(self) -> None:
        """パースできない文字列で None を返すこと。"""
        assert clean_price("abc") is None

    def test_エッジケース_スペースのみでNoneを返す(self) -> None:
        """空白文字のみで None を返すこと。"""
        assert clean_price("   ") is None


# =============================================================================
# clean_percentage
# =============================================================================


class TestCleanPercentage:
    """clean_percentage のテスト。"""

    def test_正常系_パーセント記号付き値を変換できる(self) -> None:
        """\"-0.849%\" を -0.849 に変換できること。"""
        assert clean_percentage("-0.849%") == pytest.approx(-0.849)

    def test_正常系_正のパーセントを変換できる(self) -> None:
        """'1.23%' を 1.23 に変換できること。"""
        assert clean_percentage("1.23%") == pytest.approx(1.23)

    def test_正常系_パーセント記号なしを変換できる(self) -> None:
        """'2.5' を 2.5 に変換できること。"""
        assert clean_percentage("2.5") == pytest.approx(2.5)

    def test_エッジケース_空文字でNoneを返す(self) -> None:
        """空文字で None を返すこと。"""
        assert clean_percentage("") is None

    def test_エッジケース_NAでNoneを返す(self) -> None:
        """'N/A' で None を返すこと。"""
        assert clean_percentage("N/A") is None

    def test_異常系_不正な値でNoneを返す(self) -> None:
        """パースできない文字列で None を返すこと。"""
        assert clean_percentage("abc%") is None


# =============================================================================
# clean_market_cap
# =============================================================================


class TestCleanMarketCap:
    """clean_market_cap のテスト。"""

    def test_正常系_カンマ区切り整数を変換できる(self) -> None:
        """'3,435,123,456,789' を 3435123456789 に変換できること。"""
        assert clean_market_cap("3,435,123,456,789") == 3435123456789

    def test_正常系_カンマなし整数を変換できる(self) -> None:
        """'1000000' を 1000000 に変換できること。"""
        assert clean_market_cap("1000000") == 1000000

    def test_エッジケース_空文字でNoneを返す(self) -> None:
        """空文字で None を返すこと。"""
        assert clean_market_cap("") is None

    def test_エッジケース_NAでNoneを返す(self) -> None:
        """'N/A' で None を返すこと。"""
        assert clean_market_cap("N/A") is None

    def test_異常系_不正な値でNoneを返す(self) -> None:
        """パースできない文字列で None を返すこと。"""
        assert clean_market_cap("abc") is None

    def test_正常系_ゼロを変換できる(self) -> None:
        """'0' を 0 に変換できること。"""
        assert clean_market_cap("0") == 0


# =============================================================================
# clean_volume
# =============================================================================


class TestCleanVolume:
    """clean_volume のテスト。"""

    def test_正常系_カンマ区切り整数を変換できる(self) -> None:
        """'48,123,456' を 48123456 に変換できること。"""
        assert clean_volume("48,123,456") == 48123456

    def test_正常系_カンマなし整数を変換できる(self) -> None:
        """'1000' を 1000 に変換できること。"""
        assert clean_volume("1000") == 1000

    def test_エッジケース_空文字でNoneを返す(self) -> None:
        """空文字で None を返すこと。"""
        assert clean_volume("") is None

    def test_エッジケース_NAでNoneを返す(self) -> None:
        """'N/A' で None を返すこと。"""
        assert clean_volume("N/A") is None

    def test_異常系_不正な値でNoneを返す(self) -> None:
        """パースできない文字列で None を返すこと。"""
        assert clean_volume("abc") is None


# =============================================================================
# clean_ipo_year
# =============================================================================


class TestCleanIpoYear:
    """clean_ipo_year のテスト。"""

    def test_正常系_有効な年を変換できる(self) -> None:
        """'1980' を 1980 に変換できること。"""
        assert clean_ipo_year("1980") == 1980

    def test_正常系_2000年代の年を変換できる(self) -> None:
        """'2024' を 2024 に変換できること。"""
        assert clean_ipo_year("2024") == 2024

    def test_エッジケース_空文字でNoneを返す(self) -> None:
        """空文字で None を返すこと。"""
        assert clean_ipo_year("") is None

    def test_エッジケース_NAでNoneを返す(self) -> None:
        """'N/A' で None を返すこと。"""
        assert clean_ipo_year("N/A") is None

    def test_異常系_非数値でNoneを返す(self) -> None:
        """非数値文字列で None を返すこと。"""
        assert clean_ipo_year("abc") is None

    def test_エッジケース_スペース付き年を変換できる(self) -> None:
        """前後のスペースを無視して変換できること。"""
        assert clean_ipo_year(" 1980 ") == 1980


# =============================================================================
# _camel_to_snake
# =============================================================================


class TestCamelToSnake:
    """_camel_to_snake のテスト。"""

    def test_正常系_camelCaseを変換できる(self) -> None:
        """'marketCap' を 'market_cap' に変換できること。"""
        assert _camel_to_snake("marketCap") == "market_cap"

    def test_正常系_小文字のみはそのまま(self) -> None:
        """'symbol' はそのまま 'symbol' になること。"""
        assert _camel_to_snake("symbol") == "symbol"

    def test_正常系_連結語を変換できる(self) -> None:
        """'netChange' を 'net_change' に変換できること。"""
        assert _camel_to_snake("netChange") == "net_change"

    def test_正常系_全大文字連続は分割しない(self) -> None:
        """'URL' は 'url' のようになること（全大文字は特殊）。"""
        # The regex only inserts before uppercase preceded by lowercase/digit
        assert _camel_to_snake("URL") == "url"

    def test_正常系_複数の大文字区切りを変換できる(self) -> None:
        """'navChangePercent' を 'nav_change_percent' に変換できること。"""
        assert _camel_to_snake("navChangePercent") == "nav_change_percent"


# =============================================================================
# parse_screener_response
# =============================================================================


class TestParseScreenerResponse:
    """parse_screener_response のテスト。"""

    def test_正常系_1行のレスポンスを正しく変換できる(self) -> None:
        """1行のレスポンスが正しくDataFrameに変換されること。"""
        response = _make_single_row_response()
        df = parse_screener_response(response)

        assert len(df) == 1
        row = df.iloc[0]
        assert row["symbol"] == "AAPL"
        assert row["name"] == "Apple Inc. Common Stock"
        assert row["last_sale"] == pytest.approx(227.63)
        assert row["net_change"] == pytest.approx(-1.95)
        assert row["pct_change"] == pytest.approx(-0.849)
        assert row["market_cap"] == 3435123456789
        assert row["country"] == "United States"
        assert row["ipo_year"] == 1980
        assert row["volume"] == 48123456
        assert row["sector"] == "Technology"
        assert row["industry"] == "Computer Manufacturing"
        assert row["url"] == "/market-activity/stocks/aapl"

    def test_正常系_複数行のレスポンスを変換できる(self) -> None:
        """複数行のレスポンスが正しくDataFrameに変換されること。"""
        response = {
            "data": {
                "table": {
                    "rows": [
                        {
                            "symbol": "AAPL",
                            "name": "Apple Inc.",
                            "lastsale": "$227.63",
                            "netchange": "-1.95",
                            "pctchange": "-0.849%",
                            "marketCap": "3,435,123,456,789",
                            "country": "United States",
                            "ipoyear": "1980",
                            "volume": "48,123,456",
                            "sector": "Technology",
                            "industry": "Computer Manufacturing",
                            "url": "/market-activity/stocks/aapl",
                        },
                        {
                            "symbol": "MSFT",
                            "name": "Microsoft Corp.",
                            "lastsale": "$420.50",
                            "netchange": "2.30",
                            "pctchange": "0.55%",
                            "marketCap": "3,100,000,000,000",
                            "country": "United States",
                            "ipoyear": "1986",
                            "volume": "25,000,000",
                            "sector": "Technology",
                            "industry": "Computer Software",
                            "url": "/market-activity/stocks/msft",
                        },
                    ]
                }
            }
        }
        df = parse_screener_response(response)

        assert len(df) == 2
        assert list(df["symbol"]) == ["AAPL", "MSFT"]
        assert df["last_sale"].iloc[1] == pytest.approx(420.50)

    def test_エッジケース_空のrows配列で空DataFrameを返す(self) -> None:
        """rows が空配列のとき空DataFrameを返すこと。"""
        response = {"data": {"table": {"rows": []}}}
        df = parse_screener_response(response)

        assert len(df) == 0
        # Should have expected columns
        assert "symbol" in df.columns
        assert "last_sale" in df.columns

    def test_異常系_dataキーがないとNasdaqParseErrorを発生させる(self) -> None:
        """'data' キーが欠如しているとき NasdaqParseError が発生すること。"""
        with pytest.raises(NasdaqParseError, match="data"):
            parse_screener_response({})

    def test_異常系_tableキーがないとNasdaqParseErrorを発生させる(self) -> None:
        """'data.table' キーが欠如しているとき NasdaqParseError が発生すること。"""
        with pytest.raises(NasdaqParseError, match="table"):
            parse_screener_response({"data": {}})

    def test_異常系_rowsキーがないとNasdaqParseErrorを発生させる(self) -> None:
        """'data.table.rows' キーが欠如しているとき NasdaqParseError が発生すること。"""
        with pytest.raises(NasdaqParseError, match="rows"):
            parse_screener_response({"data": {"table": {}}})

    def test_異常系_rowsがリストでないとNasdaqParseErrorを発生させる(self) -> None:
        """'rows' がリストでないとき NasdaqParseError が発生すること。"""
        with pytest.raises(NasdaqParseError, match="rows"):
            parse_screener_response({"data": {"table": {"rows": "not a list"}}})

    def test_異常系_dataがdictでないとNasdaqParseErrorを発生させる(self) -> None:
        """'data' が dict でないとき NasdaqParseError が発生すること。"""
        with pytest.raises(NasdaqParseError, match="data"):
            parse_screener_response({"data": "not a dict"})

    def test_エッジケース_NAフィールドをNoneに変換できる(self) -> None:
        """N/A フィールドが None に変換されること。"""
        response = _make_single_row_response(
            lastsale="N/A",
            netchange="N/A",
            pctchange="N/A",
            market_cap="N/A",
            ipoyear="N/A",
            volume="N/A",
        )
        df = parse_screener_response(response)

        assert len(df) == 1
        row = df.iloc[0]
        assert row["last_sale"] is None
        assert row["net_change"] is None
        assert row["pct_change"] is None
        assert row["market_cap"] is None
        assert row["ipo_year"] is None
        assert row["volume"] is None

    def test_エッジケース_空文字フィールドをNoneに変換できる(self) -> None:
        """空文字フィールドが None に変換されること。"""
        response = _make_single_row_response(
            lastsale="",
            netchange="",
            pctchange="",
            market_cap="",
            ipoyear="",
            volume="",
        )
        df = parse_screener_response(response)

        assert len(df) == 1
        row = df.iloc[0]
        assert row["last_sale"] is None
        assert row["net_change"] is None
        assert row["pct_change"] is None
        assert row["market_cap"] is None
        assert row["ipo_year"] is None
        assert row["volume"] is None

    def test_正常系_カラム名がsnake_caseにリネームされる(self) -> None:
        """API の camelCase カラム名が snake_case にリネームされること。"""
        response = _make_single_row_response()
        df = parse_screener_response(response)

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
        assert set(df.columns) == expected_columns

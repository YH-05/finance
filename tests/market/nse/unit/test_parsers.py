"""Unit tests for market.nse.parsers module.

Tests verify all JSON/CSV parsers and numeric cleaning functions for
the NSE API response format.

Test TODO List:
- [x] clean_price: numeric float input
- [x] clean_price: string with commas
- [x] clean_price: negative string
- [x] clean_price: empty string returns None
- [x] clean_price: N/A returns None
- [x] clean_price: None returns None
- [x] clean_price: malformed value returns None
- [x] clean_price: infinity value returns None
- [x] clean_price: integer input
- [x] clean_volume: integer input
- [x] clean_volume: string with commas
- [x] clean_volume: float string rounds to int
- [x] clean_volume: empty string returns None
- [x] clean_volume: N/A returns None
- [x] clean_volume: None returns None
- [x] clean_volume: malformed value returns None
- [x] clean_indian_number: standard number
- [x] clean_indian_number: Indian format (lakhs/crores)
- [x] clean_indian_number: float input
- [x] clean_indian_number: empty string returns None
- [x] clean_indian_number: N/A returns None
- [x] clean_indian_number: None returns None
- [x] clean_indian_number: malformed value returns None
- [x] clean_indian_number: infinity returns None
- [x] parse_quote_response: valid response
- [x] parse_quote_response: missing required sub-objects raises NseParseError
- [x] parse_quote_response: empty dict raises NseParseError
- [x] parse_quote_response: non-dict raises NseParseError
- [x] parse_index_constituents: valid response filters index metadata row
- [x] parse_index_constituents: empty data list
- [x] parse_index_constituents: missing 'data' key raises NseParseError
- [x] parse_index_constituents: non-dict raises NseParseError
- [x] parse_financial_results: valid response with single result
- [x] parse_financial_results: missing 'resCmpData' raises NseParseError
- [x] parse_financial_results: empty resCmpData list returns empty list
- [x] parse_financial_results: non-dict raises NseParseError
- [x] parse_financial_results: symbol引数でレスポンスにsymbolがない場合に補完
- [x] parse_financial_results: レスポンスのsymbolが引数より優先
- [x] parse_event_calendar: valid array
- [x] parse_event_calendar: empty array returns empty list
- [x] parse_event_calendar: non-list raises NseParseError
- [x] parse_stock_list_csv: valid CSV content
- [x] parse_stock_list_csv: empty CSV raises NseParseError
- [x] parse_stock_list_csv: bytes input (utf-8)
- [x] parse_stock_list_csv: column renaming via STOCK_LIST_COLUMN_MAP
- [x] parse_preopen_data: valid response
- [x] parse_preopen_data: missing 'data' key raises NseParseError
- [x] parse_preopen_data: empty data returns empty DataFrame
- [x] parse_preopen_data: non-dict raises NseParseError
- [x] parse_all_indices: valid response
- [x] parse_all_indices: missing 'data' key raises NseParseError
- [x] parse_all_indices: empty data returns empty DataFrame
- [x] parse_all_indices: non-dict raises NseParseError
- [x] parse_market_status: valid response
- [x] parse_market_status: missing 'marketState' key raises NseParseError
- [x] parse_market_status: empty marketState returns empty list
- [x] parse_market_status: non-dict raises NseParseError
- [x] Module exports: __all__ completeness (includes parse_corporate_shareholding)
"""

import pandas as pd
import pytest

from market.nse.errors import NseParseError
from market.nse.parsers import (
    _MISSING_VALUES,
    __all__,
    clean_indian_number,
    clean_price,
    clean_volume,
    parse_all_indices,
    parse_event_calendar,
    parse_financial_results,
    parse_index_constituents,
    parse_market_status,
    parse_preopen_data,
    parse_quote_response,
    parse_stock_list_csv,
)
from market.nse.types import (
    CorporateEvent,
    FinancialResult,
    IndexConstituent,
    MarketStatus,
    StockQuote,
)

# =============================================================================
# Fixtures
# =============================================================================


def _make_quote_response(
    *,
    symbol: str = "INFY",
    company_name: str = "Infosys Limited",
    isin: str = "INE009A01021",
    series: str = "EQ",
    last_price: float = 1269.3,
    change: float = -6.4,
    pct_change: float = -0.50,
    prev_close: float = 1275.7,
    open_: float = 1260.0,
    vwap: float = 1268.09,
    lower_cp: str = "1148.20",
    upper_cp: str = "1403.20",
    base_price: float = 1275.7,
    day_low: float = 1259.8,
    day_high: float = 1276.7,
    year_low: float = 1215.1,
    year_low_date: str = "19-Mar-2026",
    year_high: float = 1728.0,
    year_high_date: str = "03-Feb-2026",
    sector_pe: float = 17.91,
    symbol_pe: float = 18.48,
    sector_ind: str = "NIFTY 50",
    sector_inds: list[str] | None = None,
    listing_date: str = "1995-02-08",
    face_value: float = 5.0,
    issued_size: int = 4055591723,
    macro_sector: str = "Information Technology",
    sector: str = "Information Technology",
    industry: str = "IT - Software",
    basic_industry: str = "Computers - Software & Consulting",
    is_fno: bool = True,
    is_slb: bool = True,
    is_suspended: bool = False,
) -> dict:
    """Build a minimal NSE quote-equity API response."""
    if sector_inds is None:
        sector_inds = ["NIFTY 50", "NIFTY IT"]
    return {
        "info": {
            "symbol": symbol,
            "companyName": company_name,
            "isin": isin,
            "isFNOSec": is_fno,
            "isSLBSec": is_slb,
            "isSuspended": is_suspended,
            "listingDate": listing_date,
            "segment": "EQUITY",
            "identifier": f"{symbol}EQN",
        },
        "metadata": {
            "series": series,
            "pdSectorPe": sector_pe,
            "pdSymbolPe": symbol_pe,
            "pdSectorInd": sector_ind,
            "pdSectorIndAll": sector_inds,
        },
        "priceInfo": {
            "lastPrice": last_price,
            "change": change,
            "pChange": pct_change,
            "previousClose": prev_close,
            "open": open_,
            "vwap": vwap,
            "lowerCP": lower_cp,
            "upperCP": upper_cp,
            "basePrice": base_price,
            "intraDayHighLow": {"min": day_low, "max": day_high},
            "weekHighLow": {
                "min": year_low,
                "minDate": year_low_date,
                "max": year_high,
                "maxDate": year_high_date,
            },
            "tickSize": 0.1,
        },
        "securityInfo": {
            "faceValue": face_value,
            "issuedSize": issued_size,
            "boardStatus": "Main",
            "tradingStatus": "Active",
        },
        "industryInfo": {
            "macro": macro_sector,
            "sector": sector,
            "industry": industry,
            "basicIndustry": basic_industry,
        },
    }


def _make_index_response(*, include_constituent: bool = True) -> dict:
    """Build a minimal NSE equity-stockIndices API response."""
    index_item = {
        "symbol": "Nifty 50",
        "open": 22383.4,
        "dayHigh": 22406.0,
        "dayLow": 22182.55,
        "lastPrice": 22371.8,
        "previousClose": 22679.4,
        "change": -307.6,
        "pChange": -1.36,
        "totalTradedVolume": 258513840,
        "totalTradedValue": 15000000000.0,
        "yearHigh": 26373.2,
        "yearLow": 21743.65,
        "priority": 1,
    }
    if not include_constituent:
        return {"name": "NIFTY 50", "data": [index_item]}

    constituent = {
        "symbol": "RELIANCE",
        "identifier": "RELIANCEEQN",
        "series": "EQ",
        "open": "2450.00",
        "dayHigh": "2480.50",
        "dayLow": "2440.00",
        "lastPrice": "2470.25",
        "previousClose": "2445.00",
        "change": "25.25",
        "pChange": "1.03",
        "totalTradedVolume": "5000000",
        "totalTradedValue": "12345678900.00",
        "yearHigh": "2900.00",
        "yearLow": "2100.00",
        "priority": 0,
    }
    return {"name": "NIFTY 50", "data": [index_item, constituent]}


def _make_financial_response() -> dict:
    """Build a minimal NSE results-comparision API response."""
    return {
        "bankNonBnking": "N",
        "resCmpData": [
            {
                "symbol": "INFY",
                "re_from_dt": "01-OCT-2024",
                "re_to_dt": "31-DEC-2024",
                "re_res_type": "A",
                "re_net_sale": "3491500",
                "re_oth_inc_new": "100100",
                "re_net_profit": "635800",
                "re_basic_eps_for_cont_dic_opr": "15.31",
                "re_dilut_eps_for_cont_dic_opr": "15.29",
                "re_face_val": "5",
                "re_pdup": "207500",
                "re_pro_loss_bef_tax": "884400",
                "re_tax": "248600",
                "re_create_dt": "16-JAN-2025",
                "re_seq_num": "1189815",
            }
        ],
    }


def _make_event_calendar_response() -> list:
    """Build a minimal NSE event-calendar API response array."""
    return [
        {
            "symbol": "EFCIL",
            "company": "EFC (I) Limited",
            "purpose": "Fund Raising",
            "bm_desc": "Intimation of Board Meeting.",
            "date": "03-Apr-2026",
        },
        {
            "symbol": "RELIANCE",
            "company": "Reliance Industries Limited",
            "purpose": "Dividend",
            "bm_desc": "Board Meeting to consider final dividend.",
            "date": "05-Apr-2026",
        },
    ]


def _make_stock_list_csv() -> str:
    """Build a minimal NSE EQUITY_L.csv content."""
    return (
        "SYMBOL,NAME OF COMPANY,SERIES,DATE OF LISTING,"
        "PAID UP VALUE,MARKET LOT,ISIN NUMBER,FACE VALUE\n"
        "RELIANCE,Reliance Industries Limited,EQ,29-NOV-1995,"
        "10,1,INE002A01018,10\n"
        "INFY,Infosys Limited,EQ,08-FEB-1995,"
        "5,1,INE009A01021,5\n"
    )


def _make_preopen_response() -> dict:
    """Build a minimal NSE market-data-pre-open API response."""
    return {
        "data": [
            {
                "symbol": "RELIANCE",
                "iep": 2450.0,
                "chn": 25.0,
                "perChn": 1.03,
                "pCls": 2425.0,
                "trdQnty": 50000,
                "iVal": 122500000.0,
            },
            {
                "symbol": "INFY",
                "iep": 1269.3,
                "chn": -6.4,
                "perChn": -0.50,
                "pCls": 1275.7,
                "trdQnty": 80000,
                "iVal": 101544000.0,
            },
        ]
    }


def _make_all_indices_response() -> dict:
    """Build a minimal NSE allIndices API response."""
    return {
        "data": [
            {
                "indexSymbol": "NIFTY 50",
                "current": 22371.8,
                "variation": -307.6,
                "percentChange": -1.36,
                "open": 22383.4,
                "high": 22406.0,
                "low": 22182.55,
                "previousClose": 22679.4,
                "yearHigh": 26373.2,
                "yearLow": 21743.65,
                "perChange30d": -10.03,
                "perChange365d": -4.12,
            },
            {
                "indexSymbol": "NIFTY BANK",
                "current": 49500.0,
                "variation": -300.0,
                "percentChange": -0.60,
                "open": 49800.0,
                "high": 49900.0,
                "low": 49300.0,
                "previousClose": 49800.0,
                "yearHigh": 54000.0,
                "yearLow": 44000.0,
                "perChange30d": -5.0,
                "perChange365d": -2.0,
            },
        ]
    }


def _make_market_status_response() -> dict:
    """Build a minimal NSE marketStatus API response."""
    return {
        "marketState": [
            {
                "market": "Capital Market",
                "marketStatus": "Open",
                "tradeDate": "02-Apr-2026",
                "index": "NIFTY 50",
                "last": "22371.80",
                "variation": "-307.60",
                "percentChange": "-1.36",
            },
            {
                "market": "Derivatives",
                "marketStatus": "Open",
                "tradeDate": "02-Apr-2026",
                "index": "NIFTY 50",
                "last": "22365.00",
                "variation": "-300.00",
                "percentChange": "-1.32",
            },
        ]
    }


# =============================================================================
# clean_price tests
# =============================================================================


class TestCleanPrice:
    """Unit tests for clean_price."""

    def test_正常系_数値floatを変換できる(self) -> None:
        """float 型の数値を正しく変換できること。"""
        result = clean_price(2450.0)
        assert result == pytest.approx(2450.0, rel=1e-9)
        assert isinstance(result, float)

    def test_正常系_整数入力をfloatに変換できる(self) -> None:
        """int 型の数値を float に変換できること。"""
        result = clean_price(2450)
        assert result == pytest.approx(2450.0, rel=1e-9)
        assert isinstance(result, float)

    def test_正常系_カンマ付き文字列を変換できる(self) -> None:
        """カンマ区切りの価格文字列を変換できること。"""
        result = clean_price("2,450.00")
        assert result == pytest.approx(2450.0, rel=1e-9)

    def test_正常系_負の価格を変換できる(self) -> None:
        """負の価格文字列を変換できること。"""
        result = clean_price("-1.95")
        assert result == pytest.approx(-1.95, rel=1e-9)

    def test_異常系_空文字列はNoneを返す(self) -> None:
        """空文字列は None を返すこと。"""
        assert clean_price("") is None

    def test_異常系_NAはNoneを返す(self) -> None:
        """'N/A' は None を返すこと。"""
        assert clean_price("N/A") is None

    def test_異常系_Noneはそのまま返す(self) -> None:
        """None は None を返すこと。"""
        assert clean_price(None) is None

    def test_異常系_不正な文字列はNoneを返す(self) -> None:
        """パース不能な文字列は None を返すこと。"""
        assert clean_price("abc") is None

    def test_異常系_無限大はNoneを返す(self) -> None:
        """無限大の値は None を返すこと。"""
        assert clean_price(float("inf")) is None
        assert clean_price(float("-inf")) is None

    def test_異常系_NaNはNoneを返す(self) -> None:
        """NaN は None を返すこと。"""
        assert clean_price(float("nan")) is None

    def test_エッジケース_ハイフンはNoneを返す(self) -> None:
        """'-' は欠損値として None を返すこと。"""
        assert clean_price("-") is None

    def test_エッジケース_スペースのみはNoneを返す(self) -> None:
        """スペースのみの文字列は None を返すこと。"""
        assert clean_price("   ") is None


# =============================================================================
# clean_volume tests
# =============================================================================


class TestCleanVolume:
    """Unit tests for clean_volume."""

    def test_正常系_整数を変換できる(self) -> None:
        """整数型の出来高を変換できること。"""
        result = clean_volume(5000000)
        assert result == 5000000
        assert isinstance(result, int)

    def test_正常系_カンマ付き文字列を変換できる(self) -> None:
        """カンマ区切りの出来高文字列を変換できること。"""
        result = clean_volume("48,123,456")
        assert result == 48123456

    def test_正常系_小数点付き数値を整数に変換できる(self) -> None:
        """小数点付きの数値文字列を整数に変換できること。"""
        result = clean_volume("5000000.0")
        assert result == 5000000
        assert isinstance(result, int)

    def test_異常系_空文字列はNoneを返す(self) -> None:
        """空文字列は None を返すこと。"""
        assert clean_volume("") is None

    def test_異常系_NAはNoneを返す(self) -> None:
        """'N/A' は None を返すこと。"""
        assert clean_volume("N/A") is None

    def test_異常系_Noneは返す(self) -> None:
        """None は None を返すこと。"""
        assert clean_volume(None) is None

    def test_異常系_不正な文字列はNoneを返す(self) -> None:
        """パース不能な文字列は None を返すこと。"""
        assert clean_volume("abc") is None

    def test_異常系_無限大はNoneを返す(self) -> None:
        """無限大の値は None を返すこと。"""
        assert clean_volume(float("inf")) is None


# =============================================================================
# clean_indian_number tests
# =============================================================================


class TestCleanIndianNumber:
    """Unit tests for clean_indian_number."""

    def test_正常系_標準数値を変換できる(self) -> None:
        """標準的な数値文字列を変換できること。"""
        result = clean_indian_number("1234.56")
        assert result == pytest.approx(1234.56, rel=1e-9)

    def test_正常系_インドフォーマット_ラクで変換できる(self) -> None:
        """インド式のラクフォーマットを変換できること。"""
        result = clean_indian_number("1,23,456")
        assert result == pytest.approx(123456.0, rel=1e-9)

    def test_正常系_インドフォーマット_クローレで変換できる(self) -> None:
        """インド式のクローレフォーマットを変換できること。"""
        result = clean_indian_number("12,34,56,789")
        assert result == pytest.approx(123456789.0, rel=1e-9)

    def test_正常系_float入力を変換できる(self) -> None:
        """float 型の入力を変換できること。"""
        result = clean_indian_number(1234.56)
        assert result == pytest.approx(1234.56, rel=1e-9)

    def test_異常系_空文字列はNoneを返す(self) -> None:
        """空文字列は None を返すこと。"""
        assert clean_indian_number("") is None

    def test_異常系_NAはNoneを返す(self) -> None:
        """'N/A' は None を返すこと。"""
        assert clean_indian_number("N/A") is None

    def test_異常系_Noneを返す(self) -> None:
        """None は None を返すこと。"""
        assert clean_indian_number(None) is None

    def test_異常系_不正な文字列はNoneを返す(self) -> None:
        """パース不能な文字列は None を返すこと。"""
        assert clean_indian_number("abc") is None

    def test_異常系_無限大はNoneを返す(self) -> None:
        """無限大の値は None を返すこと。"""
        assert clean_indian_number(float("inf")) is None


# =============================================================================
# parse_quote_response tests
# =============================================================================


class TestParseQuoteResponse:
    """Unit tests for parse_quote_response."""

    def test_正常系_有効なレスポンスを変換できる(self) -> None:
        """有効な quote-equity レスポンスを StockQuote に変換できること。"""
        raw = _make_quote_response()
        quote = parse_quote_response(raw)

        assert isinstance(quote, StockQuote)
        assert quote.symbol == "INFY"
        assert quote.company_name == "Infosys Limited"
        assert quote.series == "EQ"
        assert quote.last_price == "1269.3"
        assert quote.prev_close == "1275.7"

    def test_正常系_全フィールドが返される(self) -> None:
        """StockQuote の全フィールドがレスポンスから取得されること。"""
        raw = _make_quote_response()
        quote = parse_quote_response(raw)

        assert quote.open == "1260.0"
        assert quote.high == "1276.7"
        assert quote.low == "1259.8"
        assert quote.change == "-6.4"
        assert quote.pct_change == "-0.5"

    def test_異常系_必須サブオブジェクトが欠損するとエラー(self) -> None:
        """必須サブオブジェクトが欠落している場合 NseParseError が発生すること。"""
        raw = _make_quote_response()
        del raw["priceInfo"]

        with pytest.raises(NseParseError) as exc_info:
            parse_quote_response(raw)
        assert "priceInfo" in str(exc_info.value)

    def test_異常系_空辞書はエラー(self) -> None:
        """空の辞書を渡すと NseParseError が発生すること。"""
        with pytest.raises(NseParseError):
            parse_quote_response({})

    def test_異常系_非辞書型はエラー(self) -> None:
        """辞書でない型を渡すと NseParseError が発生すること。"""
        with pytest.raises(NseParseError):
            parse_quote_response("not a dict")  # type: ignore[arg-type]

    def test_異常系_Noneはエラー(self) -> None:
        """None を渡すと NseParseError が発生すること。"""
        with pytest.raises(NseParseError):
            parse_quote_response(None)  # type: ignore[arg-type]


# =============================================================================
# parse_index_constituents tests
# =============================================================================


class TestParseIndexConstituents:
    """Unit tests for parse_index_constituents."""

    def test_正常系_構成銘柄を変換できる(self) -> None:
        """インデックスの構成銘柄が正しく変換されること。"""
        raw = _make_index_response()
        result = parse_index_constituents(raw)

        assert isinstance(result, list)
        assert len(result) == 1
        constituent = result[0]
        assert isinstance(constituent, IndexConstituent)
        assert constituent.symbol == "RELIANCE"
        assert constituent.series == "EQ"

    def test_正常系_インデックスメタデータ行が除外される(self) -> None:
        """data[0] のインデックスメタデータ行（priority=1）が除外されること。"""
        raw = _make_index_response()
        result = parse_index_constituents(raw)

        symbols = [c.symbol for c in result]
        assert "Nifty 50" not in symbols
        assert "RELIANCE" in symbols

    def test_正常系_空のデータリストは空リストを返す(self) -> None:
        """data が空の場合、空リストを返すこと。"""
        raw = {"name": "NIFTY 50", "data": []}
        result = parse_index_constituents(raw)
        assert result == []

    def test_異常系_dataキーがない場合はエラー(self) -> None:
        """'data' キーが欠落している場合 NseParseError が発生すること。"""
        with pytest.raises(NseParseError) as exc_info:
            parse_index_constituents({"name": "NIFTY 50"})
        assert "data" in str(exc_info.value)

    def test_異常系_非辞書型はエラー(self) -> None:
        """辞書でない型を渡すと NseParseError が発生すること。"""
        with pytest.raises(NseParseError):
            parse_index_constituents("not a dict")  # type: ignore[arg-type]

    def test_正常系_構成銘柄なしはインデックス行のみを除外(self) -> None:
        """構成銘柄がない場合（インデックス行のみ）、空リストを返すこと。"""
        raw = _make_index_response(include_constituent=False)
        result = parse_index_constituents(raw)
        assert result == []


# =============================================================================
# parse_financial_results tests
# =============================================================================


class TestParseFinancialResults:
    """Unit tests for parse_financial_results."""

    def test_正常系_有効なレスポンスを変換できる(self) -> None:
        """有効な results-comparision レスポンスを FinancialResult に変換できること。"""
        raw = _make_financial_response()
        results = parse_financial_results(raw)

        assert isinstance(results, list)
        assert len(results) == 1
        result = results[0]
        assert isinstance(result, FinancialResult)
        assert result.symbol == "INFY"

    def test_正常系_財務フィールドが正しく設定される(self) -> None:
        """財務フィールドが正しく設定されること。"""
        raw = _make_financial_response()
        results = parse_financial_results(raw)
        result = results[0]

        assert result.from_date == "01-OCT-2024"
        assert result.to_date == "31-DEC-2024"
        assert result.result_type == "A"

    def test_正常系_空のresCmpDataは空リストを返す(self) -> None:
        """resCmpData が空の場合、空リストを返すこと。"""
        raw = {"bankNonBnking": "N", "resCmpData": []}
        results = parse_financial_results(raw)
        assert results == []

    def test_異常系_resCmpDataキーがないとエラー(self) -> None:
        """'resCmpData' キーが欠落している場合 NseParseError が発生すること。"""
        with pytest.raises(NseParseError) as exc_info:
            parse_financial_results({"bankNonBnking": "N"})
        assert "resCmpData" in str(exc_info.value)

    def test_異常系_非辞書型はエラー(self) -> None:
        """辞書でない型を渡すと NseParseError が発生すること。"""
        with pytest.raises(NseParseError):
            parse_financial_results([])  # type: ignore[arg-type]

    def test_正常系_total_income_フォールバック(self) -> None:
        """total_income が null の場合、net_sale + other_income で計算されること。"""
        raw = {
            "bankNonBnking": "N",
            "resCmpData": [
                {
                    "symbol": "INFY",
                    "re_from_dt": "01-OCT-2024",
                    "re_to_dt": "31-DEC-2024",
                    "re_res_type": "A",
                    "re_net_sale": "3491500",
                    "re_oth_inc_new": "100100",
                    "re_total_inc": None,
                    "re_net_profit": "635800",
                    "re_basic_eps_for_cont_dic_opr": "15.31",
                }
            ],
        }
        results = parse_financial_results(raw)
        assert len(results) == 1
        # income should fall back to net_sale + other_income = 3591600
        assert results[0].income == "3591600.0"

    def test_正常系_symbol引数でレスポンスにsymbolがない場合に補完(self) -> None:
        """レスポンスにsymbolが無い場合、引数のsymbolが使われること。"""
        raw = {
            "bankNonBnking": "N",
            "resCmpData": [
                {
                    "re_from_dt": "01-OCT-2024",
                    "re_to_dt": "31-DEC-2024",
                    "re_res_type": "U",
                    "re_net_sale": "12826000",
                    "re_net_profit": "872100",
                    "re_basic_eps_for_cont_dic_opr": "6.44",
                }
            ],
        }
        results = parse_financial_results(raw, symbol="RELIANCE")
        assert results[0].symbol == "RELIANCE"

    def test_正常系_レスポンスのsymbolが引数より優先(self) -> None:
        """レスポンスにsymbolがある場合、引数よりレスポンスが優先されること。"""
        raw = _make_financial_response()
        results = parse_financial_results(raw, symbol="OVERRIDE")
        assert results[0].symbol == "INFY"


# =============================================================================
# parse_event_calendar tests
# =============================================================================


class TestParseEventCalendar:
    """Unit tests for parse_event_calendar."""

    def test_正常系_有効な配列を変換できる(self) -> None:
        """有効な event-calendar 配列を CorporateEvent のリストに変換できること。"""
        data = _make_event_calendar_response()
        events = parse_event_calendar(data)

        assert isinstance(events, list)
        assert len(events) == 2
        event = events[0]
        assert isinstance(event, CorporateEvent)
        assert event.symbol == "EFCIL"
        assert event.company_name == "EFC (I) Limited"
        assert event.purpose == "Fund Raising"
        assert event.date == "03-Apr-2026"

    def test_正常系_descriptionフィールドが設定される(self) -> None:
        """description フィールド (bm_desc) が正しく設定されること。"""
        data = _make_event_calendar_response()
        events = parse_event_calendar(data)
        assert events[0].description == "Intimation of Board Meeting."

    def test_正常系_空配列は空リストを返す(self) -> None:
        """空の配列を渡すと空リストを返すこと。"""
        assert parse_event_calendar([]) == []

    def test_異常系_非リスト型はエラー(self) -> None:
        """リストでない型を渡すと NseParseError が発生すること。"""
        with pytest.raises(NseParseError):
            parse_event_calendar({"key": "value"})  # type: ignore[arg-type]

    def test_正常系_複数イベントが全て変換される(self) -> None:
        """複数のイベントが全て変換されること。"""
        data = _make_event_calendar_response()
        events = parse_event_calendar(data)
        symbols = [e.symbol for e in events]
        assert "EFCIL" in symbols
        assert "RELIANCE" in symbols


# =============================================================================
# parse_stock_list_csv tests
# =============================================================================


class TestParseStockListCsv:
    """Unit tests for parse_stock_list_csv."""

    def test_正常系_有効なCSVを変換できる(self) -> None:
        """有効な EQUITY_L.csv を DataFrame に変換できること。"""
        content = _make_stock_list_csv()
        df = parse_stock_list_csv(content)

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert "symbol" in df.columns

    def test_正常系_列名がリネームされる(self) -> None:
        """STOCK_LIST_COLUMN_MAP に従って列名が変換されること。"""
        content = _make_stock_list_csv()
        df = parse_stock_list_csv(content)

        assert "symbol" in df.columns
        assert "company_name" in df.columns
        assert "isin" in df.columns
        # Original uppercase names should not remain
        assert "SYMBOL" not in df.columns
        assert "ISIN NUMBER" not in df.columns

    def test_正常系_最初の銘柄が正しく変換される(self) -> None:
        """最初の銘柄データが正しく変換されること。"""
        content = _make_stock_list_csv()
        df = parse_stock_list_csv(content)
        assert df["symbol"].iloc[0] == "RELIANCE"

    def test_正常系_bytes入力を処理できる(self) -> None:
        """bytes 型の CSV 入力を処理できること。"""
        content = _make_stock_list_csv().encode("utf-8")
        df = parse_stock_list_csv(content)
        assert len(df) == 2

    def test_異常系_空文字列はエラー(self) -> None:
        """空文字列を渡すと NseParseError が発生すること。"""
        with pytest.raises(NseParseError):
            parse_stock_list_csv("")

    def test_異常系_空bytes入力はエラー(self) -> None:
        """空のバイト列を渡すと NseParseError が発生すること。"""
        with pytest.raises(NseParseError):
            parse_stock_list_csv(b"")


# =============================================================================
# parse_preopen_data tests
# =============================================================================


class TestParsePreopenData:
    """Unit tests for parse_preopen_data."""

    def test_正常系_有効なレスポンスを変換できる(self) -> None:
        """有効なプレオープンデータを DataFrame に変換できること。"""
        raw = _make_preopen_response()
        df = parse_preopen_data(raw)

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2

    def test_正常系_列名がリネームされる(self) -> None:
        """PREOPEN_COLUMN_MAP に従って列名が変換されること。"""
        raw = _make_preopen_response()
        df = parse_preopen_data(raw)

        assert "symbol" in df.columns
        assert "iep" in df.columns
        assert "change" in df.columns
        assert "pct_change" in df.columns

    def test_正常系_空データは空DataFrameを返す(self) -> None:
        """data が空の場合、空 DataFrame を返すこと。"""
        raw = {"data": []}
        df = parse_preopen_data(raw)
        assert isinstance(df, pd.DataFrame)
        assert df.empty

    def test_異常系_dataキーがないとエラー(self) -> None:
        """'data' キーが欠落している場合 NseParseError が発生すること。"""
        with pytest.raises(NseParseError) as exc_info:
            parse_preopen_data({})
        assert "data" in str(exc_info.value)

    def test_異常系_非辞書型はエラー(self) -> None:
        """辞書でない型を渡すと NseParseError が発生すること。"""
        with pytest.raises(NseParseError):
            parse_preopen_data([])  # type: ignore[arg-type]


# =============================================================================
# parse_all_indices tests
# =============================================================================


class TestParseAllIndices:
    """Unit tests for parse_all_indices."""

    def test_正常系_有効なレスポンスを変換できる(self) -> None:
        """有効な allIndices レスポンスを DataFrame に変換できること。"""
        raw = _make_all_indices_response()
        df = parse_all_indices(raw)

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2

    def test_正常系_列名がリネームされる(self) -> None:
        """ALL_INDICES_COLUMN_MAP に従って列名が変換されること。"""
        raw = _make_all_indices_response()
        df = parse_all_indices(raw)

        assert "index_symbol" in df.columns
        assert "current" in df.columns
        assert "pct_change" in df.columns
        assert "prev_close" in df.columns

    def test_正常系_最初のインデックスが正しく変換される(self) -> None:
        """最初のインデックスデータが正しく変換されること。"""
        raw = _make_all_indices_response()
        df = parse_all_indices(raw)
        assert df["index_symbol"].iloc[0] == "NIFTY 50"

    def test_正常系_空データは空DataFrameを返す(self) -> None:
        """data が空の場合、空 DataFrame を返すこと。"""
        raw = {"data": []}
        df = parse_all_indices(raw)
        assert isinstance(df, pd.DataFrame)
        assert df.empty

    def test_異常系_dataキーがないとエラー(self) -> None:
        """'data' キーが欠落している場合 NseParseError が発生すること。"""
        with pytest.raises(NseParseError) as exc_info:
            parse_all_indices({})
        assert "data" in str(exc_info.value)

    def test_異常系_非辞書型はエラー(self) -> None:
        """辞書でない型を渡すと NseParseError が発生すること。"""
        with pytest.raises(NseParseError):
            parse_all_indices([])  # type: ignore[arg-type]


# =============================================================================
# parse_market_status tests
# =============================================================================


class TestParseMarketStatus:
    """Unit tests for parse_market_status."""

    def test_正常系_有効なレスポンスを変換できる(self) -> None:
        """有効な marketStatus レスポンスを MarketStatus のリストに変換できること。"""
        raw = _make_market_status_response()
        statuses = parse_market_status(raw)

        assert isinstance(statuses, list)
        assert len(statuses) == 2
        status = statuses[0]
        assert isinstance(status, MarketStatus)
        assert status.market == "Capital Market"
        assert status.market_status == "Open"

    def test_正常系_全フィールドが設定される(self) -> None:
        """MarketStatus の全フィールドが正しく設定されること。"""
        raw = _make_market_status_response()
        statuses = parse_market_status(raw)
        status = statuses[0]

        assert status.trade_date == "02-Apr-2026"
        assert status.index == "NIFTY 50"
        assert status.last == "22371.80"
        assert status.variation == "-307.60"
        assert status.pct_change == "-1.36"

    def test_正常系_空のmarketStateは空リストを返す(self) -> None:
        """marketState が空の場合、空リストを返すこと。"""
        raw = {"marketState": []}
        statuses = parse_market_status(raw)
        assert statuses == []

    def test_異常系_marketStateキーがないとエラー(self) -> None:
        """'marketState' キーが欠落している場合 NseParseError が発生すること。"""
        with pytest.raises(NseParseError) as exc_info:
            parse_market_status({})
        assert "marketState" in str(exc_info.value)

    def test_異常系_非辞書型はエラー(self) -> None:
        """辞書でない型を渡すと NseParseError が発生すること。"""
        with pytest.raises(NseParseError):
            parse_market_status([])  # type: ignore[arg-type]

    def test_正常系_複数市場セグメントが全て変換される(self) -> None:
        """複数の市場セグメントが全て変換されること。"""
        raw = _make_market_status_response()
        statuses = parse_market_status(raw)
        markets = [s.market for s in statuses]
        assert "Capital Market" in markets
        assert "Derivatives" in markets


# =============================================================================
# Module exports tests
# =============================================================================


class TestModuleExports:
    """Tests for module exports completeness."""

    def test_正常系_モジュールエクスポートが完全であること(self) -> None:
        """__all__ に全パブリックシンボルが含まれていること。"""
        expected = {
            "_MISSING_VALUES",
            "clean_indian_number",
            "clean_price",
            "clean_volume",
            "parse_all_indices",
            "parse_corporate_shareholding",
            "parse_event_calendar",
            "parse_financial_results",
            "parse_index_constituents",
            "parse_market_status",
            "parse_preopen_data",
            "parse_quote_response",
            "parse_shareholding_pattern",
            "parse_stock_list_csv",
        }
        assert expected == set(__all__)

    def test_正常系_欠損値センチネルセットが完全であること(self) -> None:
        """_MISSING_VALUES が期待されるセンチネル値を全て含むこと。"""
        assert "" in _MISSING_VALUES
        assert "N/A" in _MISSING_VALUES
        assert "NA" in _MISSING_VALUES
        assert "-" in _MISSING_VALUES

"""Unit tests for parse_corporate_shareholding function.

Tests verify JSON list parsing from the NSE corporate-share-holdings-master
endpoint into list[CorporateShareHolding].

Test TODO List:
- [x] 正常系: list[CorporateShareHolding] を返す
- [x] 正常系: 空 list で空 list を返す
- [x] 異常系: 非 list 入力で NseParseError が raise される
- [x] 正常系: 欠損フィールドはデフォルト値（空文字列）になる
- [x] 正常系: symbol keyword-only 引数が動作する
- [x] 正常系: xbrl_url フィールドが正しく抽出される
- [x] 正常系: 複数レコードを正しく変換できる
- [x] 正常系: list に dict でない要素が含まれる場合はスキップ
- [x] 正常系: promoter_group_pct / public_pct / employee_trust_pct が正しく抽出される
- [x] Module exports: __all__ に含まれる
"""

from dataclasses import FrozenInstanceError

import pytest

from market.nse.errors import NseParseError
from market.nse.parsers import parse_corporate_shareholding
from market.nse.types import CorporateShareHolding

# =============================================================================
# Helpers: sample API JSON
# =============================================================================


def _make_reliance_record() -> dict:
    """Create a single corporate share holding record (RELIANCE style)."""
    return {
        "symbol": "RELIANCE",
        "date": "31-Dec-2025",
        "pr_and_prgrp": "50.01",
        "public_val": "49.99",
        "employeeTrusts": "",
        "submissionDate": "15-Jan-2026",
        "broadcastDate": "16-Jan-2026",
        "xbrl": "https://archives.nseindia.com/corporate/xbrl/RELIANCE_2025_Q3.xml",
    }


def _make_hdfcbank_record() -> dict:
    """Create a record for HDFCBANK (no promoter_group)."""
    return {
        "symbol": "HDFCBANK",
        "date": "31-Dec-2025",
        "pr_and_prgrp": "",
        "public_val": "100.00",
        "employeeTrusts": "0.00",
        "submissionDate": "14-Jan-2026",
        "broadcastDate": "15-Jan-2026",
        "xbrl": "https://archives.nseindia.com/corporate/xbrl/HDFCBANK_2025_Q3.xml",
    }


def _make_reliance_list() -> list[dict]:
    """Create a two-record API response (2 quarters for RELIANCE)."""
    return [
        _make_reliance_record(),
        {
            "symbol": "RELIANCE",
            "date": "30-Sep-2025",
            "pr_and_prgrp": "50.02",
            "public_val": "49.98",
            "employeeTrusts": "0.00",
            "submissionDate": "16-Oct-2025",
            "broadcastDate": "17-Oct-2025",
            "xbrl": "https://archives.nseindia.com/corporate/xbrl/RELIANCE_2025_Q2.xml",
        },
    ]


# =============================================================================
# Tests: basic return type and structure
# =============================================================================


class TestParseCorporateShareHoldingReturn:
    def test_正常系_list_CorporateShareHoldingを返す(self) -> None:
        data = _make_reliance_list()
        result = parse_corporate_shareholding(data)
        assert isinstance(result, list)
        assert len(result) == 2
        assert all(isinstance(r, CorporateShareHolding) for r in result)

    def test_正常系_空listで空listを返す(self) -> None:
        result = parse_corporate_shareholding([])
        assert result == []

    def test_正常系_frozenDataclassで不変(self) -> None:
        data = [_make_reliance_record()]
        result = parse_corporate_shareholding(data)
        with pytest.raises(FrozenInstanceError):
            result[0].symbol = "OTHER"  # type: ignore[misc]


# =============================================================================
# Tests: error handling
# =============================================================================


class TestParseCorporateShareHoldingErrors:
    def test_異常系_dictでNseParseError(self) -> None:
        with pytest.raises(NseParseError):
            parse_corporate_shareholding({"not": "a list"})  # type: ignore[arg-type]

    def test_異常系_文字列でNseParseError(self) -> None:
        with pytest.raises(NseParseError):
            parse_corporate_shareholding("not a list")  # type: ignore[arg-type]

    def test_異常系_Noneでは呼び出せない(self) -> None:
        with pytest.raises((NseParseError, TypeError)):
            parse_corporate_shareholding(None)  # type: ignore[arg-type]


# =============================================================================
# Tests: field extraction
# =============================================================================


class TestParseCorporateShareHoldingFields:
    def test_正常系_全フィールドが正しく抽出される(self) -> None:
        data = [_make_reliance_record()]
        result = parse_corporate_shareholding(data)
        assert len(result) == 1
        r = result[0]

        assert r.symbol == "RELIANCE"
        assert r.as_on_date == "31-Dec-2025"
        assert r.promoter_group_pct == "50.01"
        assert r.public_pct == "49.99"
        assert r.employee_trust_pct == ""
        assert r.submission_date == "15-Jan-2026"
        assert r.broadcast_date == "16-Jan-2026"
        assert (
            r.xbrl_url
            == "https://archives.nseindia.com/corporate/xbrl/RELIANCE_2025_Q3.xml"
        )

    def test_正常系_xbrl_urlフィールドが正しく抽出される(self) -> None:
        """xbrl フィールドが xbrl_url に正しくマッピングされる。"""
        url = "https://archives.nseindia.com/corporate/xbrl/INFY_2025_Q3.xml"
        data = [
            {
                "symbol": "INFY",
                "date": "31-Dec-2025",
                "pr_and_prgrp": "15.11",
                "public_val": "84.89",
                "employeeTrusts": "",
                "submissionDate": "10-Jan-2026",
                "broadcastDate": "11-Jan-2026",
                "xbrl": url,
            }
        ]
        result = parse_corporate_shareholding(data)
        assert result[0].xbrl_url == url

    def test_正常系_欠損フィールドはデフォルト空文字列(self) -> None:
        """一部フィールドが欠損しているレコードでもデフォルト値が適用される。"""
        data: list[dict] = [
            {
                "symbol": "TCS",
                "date": "31-Dec-2025",
                "pr_and_prgrp": "72.30",
                "public_val": "27.70",
                # employeeTrusts, submissionDate, broadcastDate, xbrl が欠損
            }
        ]
        result = parse_corporate_shareholding(data)
        assert len(result) == 1
        r = result[0]
        assert r.employee_trust_pct == ""
        assert r.submission_date == ""
        assert r.broadcast_date == ""
        assert r.xbrl_url == ""

    def test_正常系_employee_trust_pctフィールドが正しく抽出される(self) -> None:
        data = [_make_hdfcbank_record()]
        result = parse_corporate_shareholding(data)
        assert result[0].employee_trust_pct == "0.00"

    def test_正常系_promoter_group_pct_公開株のみで空文字列(self) -> None:
        """promoter_group が空文字列のケース（HDFCBANK 型）。"""
        data = [_make_hdfcbank_record()]
        result = parse_corporate_shareholding(data)
        assert result[0].promoter_group_pct == ""
        assert result[0].public_pct == "100.00"


# =============================================================================
# Tests: symbol keyword argument
# =============================================================================


class TestParseCorporateShareHoldingSymbolArg:
    def test_正常系_symbolキーワード引数でシンボルを補完できる(self) -> None:
        """symbol が欠損しているレコードに keyword 引数で補完される。"""
        data: list[dict] = [
            {
                "date": "31-Dec-2025",
                "pr_and_prgrp": "50.01",
                "public_val": "49.99",
            }
        ]
        result = parse_corporate_shareholding(data, symbol="RELIANCE")
        assert result[0].symbol == "RELIANCE"

    def test_正常系_symbolキーワードデフォルトは空文字列(self) -> None:
        """symbol 引数を省略した場合はデフォルトの空文字列が使われる。"""
        data: list[dict] = [
            {
                "date": "31-Dec-2025",
                "pr_and_prgrp": "50.01",
                "public_val": "49.99",
            }
        ]
        result = parse_corporate_shareholding(data)
        assert result[0].symbol == ""

    def test_正常系_レコードのsymbolがキーワード引数より優先(self) -> None:
        """レコードに symbol が含まれる場合はそちらが使われる。"""
        data = [_make_reliance_record()]  # symbol="RELIANCE" が含まれる
        result = parse_corporate_shareholding(data, symbol="OVERRIDE")
        assert result[0].symbol == "RELIANCE"

    def test_正常系_symbolはkeyword_onlyで位置引数不可(self) -> None:
        """symbol が keyword-only 引数であることを確認。"""
        data: list[dict] = [
            {"date": "31-Dec-2025", "pr_and_prgrp": "50.01", "public_val": "49.99"}
        ]
        with pytest.raises(TypeError):
            parse_corporate_shareholding(data, "RELIANCE")  # type: ignore[call-arg]


# =============================================================================
# Tests: list iteration and skipping
# =============================================================================


class TestParseCorporateShareHoldingIteration:
    def test_正常系_複数レコードを正しく変換できる(self) -> None:
        data = _make_reliance_list()
        result = parse_corporate_shareholding(data)
        assert len(result) == 2
        assert result[0].as_on_date == "31-Dec-2025"
        assert result[1].as_on_date == "30-Sep-2025"
        assert result[1].promoter_group_pct == "50.02"

    def test_正常系_dict以外の要素はスキップされる(self) -> None:
        """list の中に dict でない要素がある場合はスキップする。"""
        data: list = [
            _make_reliance_record(),
            "not a dict",
            42,
            None,
        ]
        result = parse_corporate_shareholding(data)
        assert len(result) == 1
        assert result[0].symbol == "RELIANCE"


# =============================================================================
# Tests: __all__ exports
# =============================================================================


class TestModuleExports:
    def test_正常系_parse_corporate_shareholdingが__all__に含まれる(self) -> None:
        from market.nse.parsers import __all__

        assert "parse_corporate_shareholding" in __all__

    def test_正常系_initからimportできる(self) -> None:
        from market.nse import parse_corporate_shareholding as pcs

        assert pcs is parse_corporate_shareholding

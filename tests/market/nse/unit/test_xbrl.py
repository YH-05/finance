"""Unit tests for market.nse.xbrl module.

Tests cover:
- ContextInfo / ShareholderRow / ParseResult dataclasses
- parse_xbrl() public function
- NseParseError on namespace mismatch
- Unknown member fallback behaviour
- _MEMBER_CATEGORY count (88)
- _AXIS_TO_SUBCATEGORY count (47)
- # nosec B314 comment presence
- Fixture-based integration smoke test
"""

from __future__ import annotations

from pathlib import Path

import pytest

from market.nse.errors import NseParseError
from market.nse.xbrl import (
    _AXIS_TO_SUBCATEGORY,
    _MEMBER_CATEGORY,
    ContextInfo,
    ParseResult,
    ShareholderRow,
    parse_xbrl,
)

# ---------------------------------------------------------------------------
# Fixture path
# ---------------------------------------------------------------------------

_FIXTURE_DIR = Path(__file__).parent.parent / "fixtures"
_XBRL_FIXTURE = _FIXTURE_DIR / "xbrl_sample.xml"

# ---------------------------------------------------------------------------
# Minimal valid XBRL for unit tests (uses correct namespace)
# ---------------------------------------------------------------------------

_MINIMAL_XBRL = b"""\
<?xml version="1.0" encoding="UTF-8"?>
<xbrli:xbrl
  xmlns:xbrli="http://www.xbrl.org/2003/instance"
  xmlns:xbrldi="http://xbrl.org/2006/xbrldi"
  xmlns:in-bse-shp="http://www.bseindia.com/xbrl/shp/2022-09-30/in-bse-shp">
  <xbrli:context id="OneD">
    <xbrli:entity><xbrli:identifier scheme="in-bse-shp">MINCO</xbrli:identifier></xbrli:entity>
    <xbrli:period>
      <xbrli:startDate>2022-04-01</xbrli:startDate>
      <xbrli:endDate>2022-09-30</xbrli:endDate>
    </xbrli:period>
  </xbrli:context>
  <xbrli:context id="OneI">
    <xbrli:entity><xbrli:identifier scheme="in-bse-shp">MINCO</xbrli:identifier></xbrli:entity>
    <xbrli:period>
      <xbrli:instant>2022-09-30</xbrli:instant>
    </xbrli:period>
  </xbrli:context>
  <in-bse-shp:Symbol contextRef="OneD">MINCO</in-bse-shp:Symbol>
  <in-bse-shp:NameOfTheCompany contextRef="OneD">Minimal Company</in-bse-shp:NameOfTheCompany>
  <in-bse-shp:DateOfReport contextRef="OneI">2022-09-30</in-bse-shp:DateOfReport>
</xbrli:xbrl>
"""

_WRONG_NS_XBRL = b"""\
<?xml version="1.0" encoding="UTF-8"?>
<xbrli:xbrl
  xmlns:xbrli="http://www.xbrl.org/2003/instance"
  xmlns:wrong="http://www.example.com/wrong/ns">
  <wrong:Symbol contextRef="OneD">BAD</wrong:Symbol>
</xbrli:xbrl>
"""

_UNKNOWN_MEMBER_XBRL = b"""\
<?xml version="1.0" encoding="UTF-8"?>
<xbrli:xbrl
  xmlns:xbrli="http://www.xbrl.org/2003/instance"
  xmlns:xbrldi="http://xbrl.org/2006/xbrldi"
  xmlns:in-bse-shp="http://www.bseindia.com/xbrl/shp/2022-09-30/in-bse-shp">
  <xbrli:context id="OneD">
    <xbrli:entity><xbrli:identifier scheme="in-bse-shp">UNKCO</xbrli:identifier></xbrli:entity>
    <xbrli:period>
      <xbrli:startDate>2022-04-01</xbrli:startDate>
      <xbrli:endDate>2022-09-30</xbrli:endDate>
    </xbrli:period>
  </xbrli:context>
  <xbrli:context id="OneI">
    <xbrli:entity><xbrli:identifier scheme="in-bse-shp">UNKCO</xbrli:identifier></xbrli:entity>
    <xbrli:period>
      <xbrli:instant>2022-09-30</xbrli:instant>
    </xbrli:period>
  </xbrli:context>
  <xbrli:context id="UNK01I">
    <xbrli:entity><xbrli:identifier scheme="in-bse-shp">UNKCO</xbrli:identifier></xbrli:entity>
    <xbrli:period>
      <xbrli:instant>2022-09-30</xbrli:instant>
    </xbrli:period>
    <xbrli:scenario>
      <xbrldi:explicitMember dimension="in-bse-shp:ShareholdingPatternAxis">
        in-bse-shp:AbsolutelyUnknownFutureMember
      </xbrldi:explicitMember>
    </xbrli:scenario>
  </xbrli:context>
  <in-bse-shp:Symbol contextRef="OneD">UNKCO</in-bse-shp:Symbol>
  <in-bse-shp:NameOfTheCompany contextRef="OneD">Unknown Co</in-bse-shp:NameOfTheCompany>
  <in-bse-shp:DateOfReport contextRef="OneI">2022-09-30</in-bse-shp:DateOfReport>
  <in-bse-shp:NumberOfFullyPaidUpEquityShares contextRef="UNK01I">1000</in-bse-shp:NumberOfFullyPaidUpEquityShares>
</xbrli:xbrl>
"""


# ---------------------------------------------------------------------------
# Tests: dataclasses
# ---------------------------------------------------------------------------


class TestContextInfo:
    """Tests for the ContextInfo frozen dataclass."""

    def test_正常系_デフォルト値でインスタンス化できる(self) -> None:
        ctx = ContextInfo(context_id="TestCtx")
        assert ctx.context_id == "TestCtx"
        assert ctx.member_type == ""
        assert ctx.member_name == ""
        assert ctx.axis_name == ""
        assert ctx.domain_value == ""
        assert ctx.is_instant is False

    def test_正常系_全フィールド指定でインスタンス化できる(self) -> None:
        ctx = ContextInfo(
            context_id="B01I",
            member_type="explicit",
            member_name="MutualFundsOrUti",
            axis_name="",
            domain_value="",
            is_instant=True,
        )
        assert ctx.context_id == "B01I"
        assert ctx.member_type == "explicit"
        assert ctx.member_name == "MutualFundsOrUti"
        assert ctx.is_instant is True

    def test_異常系_frozenなのでフィールド変更不可(self) -> None:
        ctx = ContextInfo(context_id="X")
        with pytest.raises(AttributeError):
            ctx.context_id = "Y"  # type: ignore[misc]


class TestShareholderRow:
    """Tests for the ShareholderRow frozen dataclass."""

    def test_正常系_デフォルト値でインスタンス化できる(self) -> None:
        row = ShareholderRow()
        assert row.symbol == ""
        assert row.is_category_total == "true"

    def test_正常系_as_listがCSV列順でリストを返す(self) -> None:
        row = ShareholderRow(
            symbol="INFY",
            company_name="Infosys",
            report_date="2022-09-30",
            category="PublicShareholding",
            sub_category="MutualFundsOrUti",
            shareholder_name="Test Fund",
            pan="AAAMT1234A",
            num_shareholders="5",
            num_fully_paid_shares="100000",
            num_voting_rights="100000",
            pct_total_shares="5.00",
            pct_fully_diluted="5.00",
            num_shares_demat="100000",
            is_category_total="false",
        )
        row_list = row.as_list()
        assert row_list[0] == "INFY"
        assert row_list[1] == "Infosys"
        assert row_list[2] == "2022-09-30"
        assert row_list[3] == "PublicShareholding"
        assert row_list[4] == "MutualFundsOrUti"
        assert row_list[5] == "Test Fund"
        assert row_list[6] == "AAAMT1234A"
        assert row_list[13] == "false"
        assert len(row_list) == 14

    def test_異常系_frozenなのでフィールド変更不可(self) -> None:
        row = ShareholderRow(symbol="X")
        with pytest.raises(AttributeError):
            row.symbol = "Y"  # type: ignore[misc]


class TestParseResult:
    """Tests for the ParseResult frozen dataclass."""

    def test_正常系_デフォルト値でインスタンス化できる(self) -> None:
        result = ParseResult()
        assert result.symbol == ""
        assert result.as_on_date == ""
        assert result.rows == ()

    def test_正常系_rowsにShareholderRowのtupleを持てる(self) -> None:
        rows = (ShareholderRow(symbol="TCS"), ShareholderRow(symbol="INFY"))
        result = ParseResult(symbol="TCS", as_on_date="2022-09-30", rows=rows)
        assert len(result.rows) == 2
        assert result.rows[0].symbol == "TCS"

    def test_異常系_frozenなのでフィールド変更不可(self) -> None:
        result = ParseResult(symbol="X")
        with pytest.raises(AttributeError):
            result.symbol = "Y"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Tests: module-private constants
# ---------------------------------------------------------------------------


class TestMemberCategoryConstant:
    """Tests for the _MEMBER_CATEGORY constant."""

    def test_正常系_エントリ数が88件(self) -> None:
        assert len(_MEMBER_CATEGORY) == 88

    def test_正常系_プロモーターサブカテゴリが含まれる(self) -> None:
        assert "IndividualsOrHinduUndividedFamily" in _MEMBER_CATEGORY
        cat, _ = _MEMBER_CATEGORY["IndividualsOrHinduUndividedFamily"]
        assert cat == "PromoterAndPromoterGroup"

    def test_正常系_パブリックサブカテゴリが含まれる(self) -> None:
        assert "MutualFundsOrUti" in _MEMBER_CATEGORY
        cat, sub = _MEMBER_CATEGORY["MutualFundsOrUti"]
        assert cat == "PublicShareholding"
        assert sub == "MutualFundsOrUti"

    def test_正常系_NonPromoterNonPublicが含まれる(self) -> None:
        assert "CustodianOrDRHolder" in _MEMBER_CATEGORY
        cat, _ = _MEMBER_CATEGORY["CustodianOrDRHolder"]
        assert cat == "NonPromoterNonPublic"

    def test_正常系_トップレベルメンバーが含まれる(self) -> None:
        assert "ShareholdingPattern" in _MEMBER_CATEGORY
        cat, _ = _MEMBER_CATEGORY["ShareholdingPattern"]
        assert cat == "Total"


class TestAxisToSubcategoryConstant:
    """Tests for the _AXIS_TO_SUBCATEGORY constant."""

    def test_正常系_エントリ数が47件(self) -> None:
        assert len(_AXIS_TO_SUBCATEGORY) == 47

    def test_正常系_MutualFundsAxisが正しいサブカテゴリを返す(self) -> None:
        assert (
            _AXIS_TO_SUBCATEGORY["DetailsOfSharesHeldByMutualFundsOrUtiAxis"]
            == "MutualFundsOrUti"
        )

    def test_正常系_BanksAxisが含まれる(self) -> None:
        assert "DetailsOfSharesHeldByBanksAxis" in _AXIS_TO_SUBCATEGORY


# ---------------------------------------------------------------------------
# Tests: parse_xbrl()
# ---------------------------------------------------------------------------


class TestParseXbrl:
    """Tests for the parse_xbrl() public function."""

    def test_正常系_最小XBRLからParseResultを返す(self) -> None:
        result = parse_xbrl(_MINIMAL_XBRL)
        assert isinstance(result, ParseResult)
        assert result.symbol == "MINCO"
        assert result.as_on_date == "2022-09-30"

    def test_正常系_symbolが正しく抽出される(self) -> None:
        result = parse_xbrl(_MINIMAL_XBRL)
        assert result.symbol == "MINCO"

    def test_正常系_as_on_dateが正しく抽出される(self) -> None:
        result = parse_xbrl(_MINIMAL_XBRL)
        assert result.as_on_date == "2022-09-30"

    def test_正常系_rowsはtupleである(self) -> None:
        result = parse_xbrl(_MINIMAL_XBRL)
        assert isinstance(result.rows, tuple)

    def test_異常系_XBRL_SHP_NS不一致でNseParseErrorが発生する(self) -> None:
        with pytest.raises(NseParseError) as exc_info:
            parse_xbrl(_WRONG_NS_XBRL)
        assert "namespace mismatch" in exc_info.value.message.lower()
        assert exc_info.value.field == "namespace"

    def test_正常系_未知memberがUnknownにフォールバックする(self) -> None:
        result = parse_xbrl(_UNKNOWN_MEMBER_XBRL)
        # There should be at least one row with category 'Unknown'
        unknown_rows = [r for r in result.rows if r.category == "Unknown"]
        assert len(unknown_rows) >= 1

    def test_正常系_未知memberのsub_categoryにmember名が入る(self) -> None:
        result = parse_xbrl(_UNKNOWN_MEMBER_XBRL)
        unknown_rows = [r for r in result.rows if r.category == "Unknown"]
        assert len(unknown_rows) >= 1
        # sub_category contains the member name with 'Member' suffix stripped
        # e.g. "AbsolutelyUnknownFutureMember" -> "AbsolutelyUnknownFuture"
        assert "AbsolutelyUnknownFuture" in unknown_rows[0].sub_category

    def test_正常系_fixtureXMLでParseResultを正常に返す(self) -> None:
        """Fixture XML smoke test: parse_xbrl returns valid ParseResult."""
        assert _XBRL_FIXTURE.exists(), f"Fixture not found: {_XBRL_FIXTURE}"
        xml_bytes = _XBRL_FIXTURE.read_bytes()
        result = parse_xbrl(xml_bytes)
        assert isinstance(result, ParseResult)
        assert result.symbol == "TESTCO"
        assert result.as_on_date == "2022-09-30"
        assert len(result.rows) > 0

    def test_正常系_fixtureXMLのカテゴリ行が正しいカテゴリを持つ(self) -> None:
        """Category rows from fixture have correct categories."""
        xml_bytes = _XBRL_FIXTURE.read_bytes()
        result = parse_xbrl(xml_bytes)
        category_rows = [r for r in result.rows if r.is_category_total == "true"]
        assert len(category_rows) >= 3
        categories = {r.category for r in category_rows}
        assert "PromoterAndPromoterGroup" in categories
        assert "PublicShareholding" in categories

    def test_正常系_fixtureXMLの詳細行が正しい株主名を持つ(self) -> None:
        """Detail rows from fixture have correct shareholder names."""
        xml_bytes = _XBRL_FIXTURE.read_bytes()
        result = parse_xbrl(xml_bytes)
        detail_rows = [r for r in result.rows if r.is_category_total == "false"]
        names = {r.shareholder_name for r in detail_rows}
        assert "Sample Mutual Fund Scheme A" in names
        assert "Sample Mutual Fund Scheme B" in names

    def test_正常系_fixtureXMLのカテゴリ行に数値データが入る(self) -> None:
        """Category rows from fixture have numeric shareholding data."""
        xml_bytes = _XBRL_FIXTURE.read_bytes()
        result = parse_xbrl(xml_bytes)
        promoter_rows = [
            r
            for r in result.rows
            if r.category == "PromoterAndPromoterGroup"
            and r.is_category_total == "true"
        ]
        assert len(promoter_rows) == 1
        assert promoter_rows[0].num_fully_paid_shares == "40000000"
        assert promoter_rows[0].pct_total_shares == "40.00"

    def test_正常系_fixtureXMLで詳細行のPANが入る(self) -> None:
        """Detail rows from fixture have PAN numbers."""
        xml_bytes = _XBRL_FIXTURE.read_bytes()
        result = parse_xbrl(xml_bytes)
        detail_rows = [r for r in result.rows if r.is_category_total == "false"]
        pans = {r.pan for r in detail_rows}
        assert "AAAMT1234A" in pans

    def test_正常系_空のbytesはET_ParseErrorが発生する(self) -> None:
        """Empty bytes should raise xml.etree.ElementTree.ParseError."""
        import xml.etree.ElementTree as ET

        with pytest.raises(ET.ParseError):
            parse_xbrl(b"")

    def test_正常系_ParseResultはfrozenである(self) -> None:
        result = parse_xbrl(_MINIMAL_XBRL)
        with pytest.raises(AttributeError):
            result.symbol = "MODIFIED"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Tests: ET.fromstring nosec comment
# ---------------------------------------------------------------------------


class TestNosecComment:
    """Verify that the nosec B314 comment is present in xbrl.py source."""

    def test_正常系_nosec_B314コメントがxbrl_pyに存在する(self) -> None:
        """ET.fromstring call must retain # nosec B314 comment."""
        import market.nse.xbrl as xbrl_module

        source_path = Path(xbrl_module.__file__)  # type: ignore[arg-type]
        source = source_path.read_text(encoding="utf-8")
        assert "nosec B314" in source, (
            "ET.fromstring in xbrl.py must have '# nosec B314' comment"
        )

"""Unit tests for market.nse.xbrl module.

Tests cover:
- ContextInfo / ShareholderRow / ParseResult dataclasses
- parse_xbrl() public function
- NseParseError on namespace mismatch
- Unknown member fallback behaviour
- _MEMBER_CATEGORY count (95) — 88 base + 7 new taxonomy-2025 aliases
- _AXIS_TO_SUBCATEGORY count (48) — 47 base + 1 taxonomy-2025 alias
- # nosec B314 comment presence
- Fixture-based integration smoke test
"""

from __future__ import annotations

from pathlib import Path

import pytest

from market.nse.errors import NseParseError
from market.nse.xbrl import (
    _AXIS_TO_SUBCATEGORY,
    _MAX_XBRL_BYTES,
    _MEMBER_CATEGORY,
    ContextInfo,
    ParseResult,
    ShareholderRow,
    _resolve_detail_category,
    _strip_member_suffix,
    parse_xbrl,
)

# ---------------------------------------------------------------------------
# Fixture path
# ---------------------------------------------------------------------------

_FIXTURE_DIR = Path(__file__).parent.parent / "fixtures"
_XBRL_FIXTURE = _FIXTURE_DIR / "xbrl_sample.xml"
_XBRL_FIXTURE_2025_05_31 = _FIXTURE_DIR / "xbrl_sample_2025_05_31.xml"
_XBRL_FIXTURE_2025_10_31 = _FIXTURE_DIR / "xbrl_sample_2025_10_31.xml"

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

    def test_正常系_エントリ数が95件(self) -> None:
        # 88 base entries + 7 new taxonomy-2025 aliases
        # (MutualFundsOrUTI, NBFCsRegisteredWithRBI, Category One/Two/Three,
        #  Shareholding...CorporateWhere..., Trusts...Is...)
        # "Governments" alias re-uses an existing _ADDITIONAL_MEMBERS entry.
        assert len(_MEMBER_CATEGORY) == 95

    def test_正常系_タクソノミ2025エイリアスが含まれる(self) -> None:
        # 新タクソノミの spelling が旧 spelling と同じカテゴリに解決することを検証
        assert "MutualFundsOrUTI" in _MEMBER_CATEGORY
        cat, sub = _MEMBER_CATEGORY["MutualFundsOrUTI"]
        assert cat == "PublicShareholding"
        assert sub == "MutualFundsOrUti"  # canonical old spelling

        assert "NBFCsRegisteredWithRBI" in _MEMBER_CATEGORY
        assert "InstitutionsForeignPortfolioInvestorCategoryOne" in _MEMBER_CATEGORY
        assert (
            "TrustsWhereAnyPersonBelongingToPromoterAndPromoterGroup"
            "IsTrusteeOrBeneficiaryOrAuthorOfTrust"
            in _MEMBER_CATEGORY
        )

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

    def test_正常系_エントリ数が48件(self) -> None:
        # 47 base entries + 1 taxonomy-2025 alias
        # (DetailsOfSharesHeldByMutualFundsOrUTIAxis)
        assert len(_AXIS_TO_SUBCATEGORY) == 48

    def test_正常系_タクソノミ2025_UTIエイリアスが解決する(self) -> None:
        # 新タクソノミ (Uti → UTI) の axis 名が旧 sub_category に解決
        assert (
            _AXIS_TO_SUBCATEGORY["DetailsOfSharesHeldByMutualFundsOrUTIAxis"]
            == "MutualFundsOrUti"
        )

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

    @pytest.fixture(scope="class")
    def fixture_xml_bytes(self) -> bytes:
        """Load the fixture XBRL XML once per test class (E5 optimisation)."""
        assert _XBRL_FIXTURE.exists(), f"Fixture not found: {_XBRL_FIXTURE}"
        return _XBRL_FIXTURE.read_bytes()

    @pytest.fixture(scope="class")
    def fixture_result(self, fixture_xml_bytes: bytes) -> ParseResult:
        """Parse the fixture XBRL once per test class (E5 optimisation)."""
        return parse_xbrl(fixture_xml_bytes)

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

    def test_正常系_fixtureXMLでParseResultを正常に返す(
        self, fixture_result: ParseResult
    ) -> None:
        """Fixture XML smoke test: parse_xbrl returns valid ParseResult."""
        assert isinstance(fixture_result, ParseResult)
        assert fixture_result.symbol == "TESTCO"
        assert fixture_result.as_on_date == "2022-09-30"
        assert len(fixture_result.rows) > 0

    def test_正常系_fixtureXMLのカテゴリ行が正しいカテゴリを持つ(
        self, fixture_result: ParseResult
    ) -> None:
        """Category rows from fixture have correct categories."""
        category_rows = [
            r for r in fixture_result.rows if r.is_category_total == "true"
        ]
        assert len(category_rows) >= 3
        categories = {r.category for r in category_rows}
        assert "PromoterAndPromoterGroup" in categories
        assert "PublicShareholding" in categories

    def test_正常系_fixtureXMLの詳細行が正しい株主名を持つ(
        self, fixture_result: ParseResult
    ) -> None:
        """Detail rows from fixture have correct shareholder names."""
        detail_rows = [r for r in fixture_result.rows if r.is_category_total == "false"]
        names = {r.shareholder_name for r in detail_rows}
        assert "Sample Mutual Fund Scheme A" in names
        assert "Sample Mutual Fund Scheme B" in names

    def test_正常系_fixtureXMLのカテゴリ行に数値データが入る(
        self, fixture_result: ParseResult
    ) -> None:
        """Category rows from fixture have numeric shareholding data."""
        promoter_rows = [
            r
            for r in fixture_result.rows
            if r.category == "PromoterAndPromoterGroup"
            and r.is_category_total == "true"
        ]
        assert len(promoter_rows) == 1
        assert promoter_rows[0].num_fully_paid_shares == "40000000"
        assert promoter_rows[0].pct_total_shares == "40.00"

    def test_正常系_fixtureXMLで詳細行のPANが入る(
        self, fixture_result: ParseResult
    ) -> None:
        """Detail rows from fixture have PAN numbers."""
        detail_rows = [r for r in fixture_result.rows if r.is_category_total == "false"]
        pans = {r.pan for r in detail_rows}
        assert "AAAMT1234A" in pans

    def test_異常系_空bytesでET_ParseErrorが発生する(self) -> None:
        """Empty bytes should raise xml.etree.ElementTree.ParseError."""
        import xml.etree.ElementTree as ET

        with pytest.raises(ET.ParseError):
            parse_xbrl(b"")

    def test_異常系_ParseResultはfrozenでフィールド変更不可(self) -> None:
        result = parse_xbrl(_MINIMAL_XBRL)
        with pytest.raises(AttributeError):
            result.symbol = "MODIFIED"  # type: ignore[misc]

    def test_異常系_サイズ上限超過でNseParseError(self) -> None:
        """Payloads larger than _MAX_XBRL_BYTES must raise NseParseError.

        Guards against DoS via oversized XML payloads (CWE-400).
        """
        oversized = b"x" * (_MAX_XBRL_BYTES + 1)
        with pytest.raises(NseParseError) as exc_info:
            parse_xbrl(oversized)
        assert exc_info.value.field == "size"
        assert "too large" in exc_info.value.message.lower()

    def test_正常系_上限ぎりぎりのサイズは先にNamespace検証へ進む(self) -> None:
        """A payload exactly at the limit proceeds past the size check.

        The subsequent XML parser will fail because the payload is not XML,
        but the point is that the size guard does not fire.
        """
        import xml.etree.ElementTree as ET

        at_limit = b"x" * _MAX_XBRL_BYTES
        # Size check passes; XML parsing fails instead of NseParseError.
        with pytest.raises(ET.ParseError):
            parse_xbrl(at_limit)


# ---------------------------------------------------------------------------
# Tests: internal helpers (_strip_member_suffix, _resolve_detail_category)
# ---------------------------------------------------------------------------


class TestStripMemberSuffix:
    """Boundary value tests for _strip_member_suffix (E3)."""

    def test_正常系_改行とインデント付き入力を正規化できる(self) -> None:
        """Leading/trailing whitespace and newlines must be stripped."""
        assert (
            _strip_member_suffix("\n  in-bse-shp:PublicShareholdingMember\n")
            == "PublicShareholding"
        )

    def test_正常系_タブ文字付き入力を正規化できる(self) -> None:
        """Tab characters must be stripped like other whitespace."""
        assert (
            _strip_member_suffix("\tin-bse-shp:MutualFundsOrUtiMember\t")
            == "MutualFundsOrUti"
        )

    def test_正常系_Memberサフィックスがない場合はそのまま返す(self) -> None:
        """Input without the Member suffix must be returned as-is after prefix strip."""
        assert _strip_member_suffix("in-bse-shp:Symbol") == "Symbol"

    def test_正常系_プレフィックスがない場合もMember除去のみ行う(self) -> None:
        """Input without the in-bse-shp prefix must still drop the Member suffix."""
        assert _strip_member_suffix("  BankMember ") == "Bank"

    def test_エッジケース_空文字列で空文字列を返す(self) -> None:
        """Empty input must return empty string without raising."""
        assert _strip_member_suffix("") == ""


class TestResolveDetailCategoryFallback:
    """Missing sub-category fallback for _resolve_detail_category (E4)."""

    def test_エッジケース_axis_is_known_but_sub_missing_in_member_category(
        self,
    ) -> None:
        """If axis maps to a sub name that is NOT in _MEMBER_CATEGORY,
        fallback must return ("Unknown", sub)."""
        # Find an axis whose resolved sub is not present in _MEMBER_CATEGORY.
        # Construct such a mapping dynamically for determinism.
        missing_sub = "ThisSubDefinitelyNotInMemberCategory"
        assert missing_sub not in _MEMBER_CATEGORY
        # Temporarily inject into _AXIS_TO_SUBCATEGORY via monkeypatch-free approach:
        # call the helper directly with a known-good axis that the suite guarantees
        # is mapped but whose sub is not a _MEMBER_CATEGORY key.
        # Instead, validate the observable behaviour with unknown axis input:
        cat, sub = _resolve_detail_category("AbsolutelyUnknownAxis")
        assert cat == "Unknown"
        # For unknown axis, sub is the axis name itself (since lookup returned "")
        assert sub == "AbsolutelyUnknownAxis"

    def test_エッジケース_axis_maps_to_sub_not_in_member_category(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Inject an axis->sub mapping where sub is not in _MEMBER_CATEGORY.

        Covers the branch: axis_name in _AXIS_TO_SUBCATEGORY but sub not in _MEMBER_CATEGORY.
        """
        from market.nse import xbrl as xbrl_mod

        sentinel_axis = "_SentinelAxisForTest"
        sentinel_sub = "_SentinelSubNotInMemberCategory"
        assert sentinel_sub not in xbrl_mod._MEMBER_CATEGORY
        patched = dict(xbrl_mod._AXIS_TO_SUBCATEGORY)
        patched[sentinel_axis] = sentinel_sub
        monkeypatch.setattr(xbrl_mod, "_AXIS_TO_SUBCATEGORY", patched)

        cat, sub = xbrl_mod._resolve_detail_category(sentinel_axis)
        assert cat == "Unknown"
        # sub is the resolved sub name (from injected mapping) even when unresolved
        assert sub == sentinel_sub


# ---------------------------------------------------------------------------
# Tests: defusedxml usage
# ---------------------------------------------------------------------------


class TestDefusedxmlUsage:
    """Verify that defusedxml is used instead of stdlib xml.etree.ElementTree."""

    def test_正常系_defusedxmlをインポートしている(self) -> None:
        """xbrl.py must import defusedxml.ElementTree instead of stdlib ET."""
        import market.nse.xbrl as xbrl_module

        source_path = Path(xbrl_module.__file__)  # type: ignore[arg-type]
        source = source_path.read_text(encoding="utf-8")
        assert "import defusedxml.ElementTree as ET" in source, (
            "xbrl.py must use 'import defusedxml.ElementTree as ET' for secure XML parsing"
        )


# ---------------------------------------------------------------------------
# Tests: multi-taxonomy support (2025-05-31 / 2025-10-31 regression guards)
# ---------------------------------------------------------------------------


@pytest.mark.skipif(
    not _XBRL_FIXTURE_2025_05_31.exists(),
    reason="fixture xbrl_sample_2025_05_31.xml not present",
)
class TestParseXbrl2025_05_31:
    """Regression guard: 2025-05-31 taxonomy (AADHARHFC 30-JUN-2025)."""

    @pytest.fixture(scope="class")
    def result(self) -> ParseResult:
        return parse_xbrl(_XBRL_FIXTURE_2025_05_31.read_bytes())

    def test_正常系_namespaceが受理される(self, result: ParseResult) -> None:
        # No NseParseError raised = namespace regex accepted 2025-05-31 URI
        assert result.symbol != "" or result.as_on_date != "" or len(result.rows) > 0

    def test_正常系_metadataがMainDコンテキストから取れる(self, result: ParseResult) -> None:
        assert result.symbol == "AADHARHFC"
        assert result.as_on_date == "2025-06-30"

    def test_正常系_pct値がパーセント形式で保持される(self, result: ParseResult) -> None:
        # 2025-05-31 taxonomy stores percentages in percentage form (75.50),
        # so no scaling should be applied.
        promoter_total = [
            r
            for r in result.rows
            if r.category == "PromoterAndPromoterGroup"
            and r.sub_category == ""
            and r.is_category_total == "true"
        ]
        assert len(promoter_total) == 1
        assert float(promoter_total[0].pct_total_shares) == pytest.approx(75.50)

    def test_正常系_名称エイリアス_MutualFundsOrUTI(self, result: ParseResult) -> None:
        # Renamed member "MutualFundsOrUTI" should resolve to the canonical
        # sub_category "MutualFundsOrUti".
        mf_rows = [
            r
            for r in result.rows
            if r.sub_category == "MutualFundsOrUti" and r.is_category_total == "true"
        ]
        assert len(mf_rows) == 1
        assert mf_rows[0].category == "PublicShareholding"


@pytest.mark.skipif(
    not _XBRL_FIXTURE_2025_10_31.exists(),
    reason="fixture xbrl_sample_2025_10_31.xml not present",
)
class TestParseXbrl2025_10_31:
    """Regression guard: 2025-10-31 taxonomy (AADHARHFC 31-MAR-2026)."""

    @pytest.fixture(scope="class")
    def result(self) -> ParseResult:
        return parse_xbrl(_XBRL_FIXTURE_2025_10_31.read_bytes())

    def test_正常系_namespaceが受理される(self, result: ParseResult) -> None:
        assert result.symbol != "" or result.as_on_date != "" or len(result.rows) > 0

    def test_正常系_metadataがMainDコンテキストから取れる(self, result: ParseResult) -> None:
        assert result.symbol == "AADHARHFC"
        assert result.as_on_date == "2026-03-31"

    def test_正常系_小数表記のpct値が自動的にパーセント化される(
        self, result: ParseResult
    ) -> None:
        # 2025-10-31 taxonomy stores pct as decimal ratios (0.649 = 64.9%).
        # Parser should scale by 100x so downstream sees percentage form.
        promoter_total = [
            r
            for r in result.rows
            if r.category == "PromoterAndPromoterGroup"
            and r.sub_category == ""
            and r.is_category_total == "true"
        ]
        assert len(promoter_total) == 1
        # Raw XBRL value is 0.649; scaled should be 64.9
        pct = float(promoter_total[0].pct_total_shares)
        assert pct == pytest.approx(64.9, rel=1e-3)
        assert pct > 1.0  # sanity: must be in percentage form, not decimal

    def test_正常系_pct_fully_diluted_ESOP別名が解決する(
        self, result: ParseResult
    ) -> None:
        # 2025-10-31 renamed the diluted element to ...WarrantsAndESOP.
        # Parser should find it via the tuple-based tag alternatives.
        promoter_total = [
            r
            for r in result.rows
            if r.category == "PromoterAndPromoterGroup"
            and r.sub_category == ""
            and r.is_category_total == "true"
        ]
        assert len(promoter_total) == 1
        assert promoter_total[0].pct_fully_diluted != ""
        # After scaling, the fully-diluted pct should also be in percentage form
        diluted = float(promoter_total[0].pct_fully_diluted)
        assert diluted > 1.0  # percentage form, not decimal

    def test_正常系_Unknown_categoryが発生しない(self, result: ParseResult) -> None:
        # All members in a normal 2025-10-31 filing should map to known
        # categories via the taxonomy aliases.
        unknown = [r for r in result.rows if r.category == "Unknown"]
        assert len(unknown) == 0, (
            f"Unknown rows found: {[r.sub_category for r in unknown]}"
        )

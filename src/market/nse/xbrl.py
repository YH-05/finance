"""NSE Shareholding XBRL parser.

Parses NSE/BSE shareholding pattern XBRL files
(in-bse-shp 2022-09-30 taxonomy) and returns structured data.

Public API
----------
parse_xbrl(xml_bytes: bytes) -> ParseResult
    Parse a single XBRL shareholding XML and return structured data.

Data Structures
---------------
ContextInfo
    Parsed information about a single <xbrli:context>.
ShareholderRow
    A single row of shareholding data.
ParseResult
    Result of parsing a single XBRL file.

Notes
-----
- CSV output logic is excluded (notebook responsibility).
- Unknown XBRL members fall back to ('Unknown', member_key).
- Namespace mismatch raises NseParseError.

See Also
--------
scripts.nse_parse_xbrl : CLI wrapper that downloads + parses XBRL files.
market.nse.constants : Namespace constants (XBRL_SHP_NS, XBRLI_NS, XBRLDI_NS).
market.nse.errors : NseParseError.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import defusedxml.ElementTree as ET

from market.nse.constants import XBRL_SHP_NS, XBRLDI_NS, XBRLI_NS
from market.nse.errors import NseParseError
from utils_core.logging import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Expected XBRL namespace (2022-09-30 revision)
# ---------------------------------------------------------------------------

# AIDEV-NOTE: 参照は市場共通の constants.XBRL_SHP_NS に一本化 (2022-09-30 タクソノミ)
# The public `market.nse.constants.XBRL_SHP_NS` constant is the single source of truth.

# ---------------------------------------------------------------------------
# Security limit
# ---------------------------------------------------------------------------

_MAX_XBRL_BYTES: int = 10 * 1024 * 1024  # 10 MiB upper bound for DoS防御 (CWE-400)
"""Maximum allowed XBRL payload size in bytes (10 MiB).

Protects against denial-of-service via excessively large XML payloads.
Real NSE XBRL filings are typically 50-500 KiB, so 10 MiB provides ample
headroom while bounding memory usage during parsing.
"""

# ---------------------------------------------------------------------------
# Namespace prefix helpers (computed from constants at module load time)
# ---------------------------------------------------------------------------

_SHP_PREFIX: str = f"{{{XBRL_SHP_NS}}}"  # ElementTree XPath用の名前空間プレフィックス (Clark notation)
_XBRLI_PREFIX: str = f"{{{XBRLI_NS}}}"  # xbrli 要素検索用の Clark notation プレフィックス
_XBRLDI_PREFIX: str = f"{{{XBRLDI_NS}}}"  # xbrldi (dimensions) 要素検索用の Clark notation

# ---------------------------------------------------------------------------
# Module-private constants: category hierarchy mapping
# ---------------------------------------------------------------------------

_PROMOTER: str = "PromoterAndPromoterGroup"  # XBRL member name: in-bse-shp taxonomy 2022-09-30
_PUBLIC: str = "PublicShareholding"  # XBRL member name: in-bse-shp taxonomy 2022-09-30
_NON_PROMOTER: str = "NonPromoterNonPublic"  # XBRL member name: in-bse-shp taxonomy 2022-09-30

# Top-level members (4 entries)
_TOP_LEVEL_MEMBERS: dict[str, str] = {
    "ShareholdingOfPromoterAndPromoterGroup": _PROMOTER,
    "PublicShareholding": _PUBLIC,
    "SharesHeldByNonPromoterNonPublicShareholders": _NON_PROMOTER,
    "ShareholdingPattern": "Total",
}

# Promoter sub-categories (20 entries)
_PROMOTER_SUBS: list[str] = [
    "IndividualsOrHinduUndividedFamily",
    "CentralGovernmentOrStateGovernmentS",
    "IndianFinancialInstitutionsOrBanks",
    "OtherIndianShareholders",
    "Indian",
    "NonResidentIndividualsOrForeignIndividuals",
    "ForeignGovernment",
    "ForeignInstitutions",
    "ForeignPortfolioInvestor",
    "OtherForeignShareholders",
    "Foreign",
    "CentralGovernmentOrPresidentOfIndia",
    "StateGovernmentsOrGovernors",
    "ShareholdingByCompaniesOrBodiesCorporatewhereCentralOrStateGovernmentIsPromoter",
    "Goverments",
    "AssociateCompaniesOrSubsidiaries",
    "DirectorsAndDirectorsRelatives",
    "KeyManagerialPersonnel",
    "RelativesOfPromotersOtherThanPromoterGroup",
    "TrustsWhereAnyPersonBelongingToPromoterAndPromoterGroupIsisTrusteeOrBeneficiaryOrAuthorOfTrust",
]

# Public sub-categories (29 entries)
_PUBLIC_SUBS: list[str] = [
    "MutualFundsOrUti",
    "VentureCapitalFunds",
    "AlternativeInvestmentFunds",
    "Banks",
    "InsuranceCompanies",
    "ProvidentFundsOrPensionFunds",
    "AssetReconstructionCompanies",
    "SovereignWealthFundsDomestic",
    "NBFCsRegisteredWithRbi",
    "OtherFinancialInstitutions",
    "OtherInstitutionsDomestic",
    "InstitutionsDomestic",
    "ForeignDirectInvestment",
    "ForeignVentureCapitalInvestors",
    "SovereignWealthFundsForeign",
    "InstitutionsForeignPortfolioInvestorCatergoryOne",
    "InstitutionsForeignPortfolioInvestorCatergoryTwo",
    "OverseasDepositories",
    "OtherInstitutionsForeign",
    "InstitutionsForeign",
    "ResidentIndividualShareholdersHoldingNominalShareCapitalUpToRsTwoLakh",
    "ResidentIndividualShareholdersHoldingNominalShareCapitalInExcessOfRsTwoLakh",
    "NonResidentIndians",
    "ForeignNationals",
    "ForeignCompanies",
    "BodiesCorporate",
    "OtherNonInstitutions",
    "NonInstitutions",
    "InvestorEducationAndProtectionFund",
]

# NonPromoterNonPublic sub-categories (2 entries)
_NON_PROMOTER_SUBS: list[str] = [
    "CustodianOrDRHolder",
    "EmployeeBenefitsTrusts",
]

# Additional members present in the 2022-09-30 taxonomy (33 entries)
# These cover intermediate aggregation rows, government sub-types,
# and additional public/promoter sub-categories observed in real filings.
_ADDITIONAL_MEMBERS: dict[str, tuple[str, str]] = {
    # Promoter — government aggregations
    "Governments": (_PROMOTER, "Governments"),
    "CentralAndStateGovernments": (_PROMOTER, "CentralAndStateGovernments"),
    "ForeignPromotersCumulativeOrAggregation": (_PROMOTER, "Foreign"),
    # Promoter — bodies corporate
    "BodiesCorporateIncludingSubsidiaries": (
        _PROMOTER,
        "BodiesCorporateIncludingSubsidiaries",
    ),
    # Public — institutions domestic sub-types
    "SmallFinanceBanks": (_PUBLIC, "SmallFinanceBanks"),
    "PaymentBanks": (_PUBLIC, "PaymentBanks"),
    "RegionalRuralBanks": (_PUBLIC, "RegionalRuralBanks"),
    "DevelopmentFinancialInstitutions": (_PUBLIC, "DevelopmentFinancialInstitutions"),
    "OtherBanks": (_PUBLIC, "OtherBanks"),
    "ForeignBanks": (_PUBLIC, "ForeignBanks"),
    # Public — FPI sub-types
    "InstitutionsForeignPortfolioInvestorCatergoryThree": (
        _PUBLIC,
        "InstitutionsForeignPortfolioInvestorCatergoryThree",
    ),
    "ForeignPortfolioInvestors": (_PUBLIC, "ForeignPortfolioInvestors"),
    # Public — individual / HNI
    "HighNetWorthIndividuals": (_PUBLIC, "HighNetWorthIndividuals"),
    "ResidentIndividuals": (_PUBLIC, "ResidentIndividuals"),
    "IndividualsOrHinduUndividedFamilyPublic": (
        _PUBLIC,
        "IndividualsOrHinduUndividedFamilyPublic",
    ),
    # Public — NRI sub-types
    "NonResidentIndiansNonRepatriable": (_PUBLIC, "NonResidentIndiansNonRepatriable"),
    "NonResidentIndiansRepatriable": (_PUBLIC, "NonResidentIndiansRepatriable"),
    # Public — trusts / others
    "ClearingMembers": (_PUBLIC, "ClearingMembers"),
    "ESOPTrusts": (_PUBLIC, "ESOPTrusts"),
    "IEPFAuthority": (_PUBLIC, "IEPFAuthority"),
    "Trusts": (_PUBLIC, "Trusts"),
    "OtherPublicShareholders": (_PUBLIC, "OtherPublicShareholders"),
    # Public — AIF sub-types
    "AlternativeInvestmentFundsCategoryI": (
        _PUBLIC,
        "AlternativeInvestmentFundsCategoryI",
    ),
    "AlternativeInvestmentFundsCategoryII": (
        _PUBLIC,
        "AlternativeInvestmentFundsCategoryII",
    ),
    "AlternativeInvestmentFundsCategoryIII": (
        _PUBLIC,
        "AlternativeInvestmentFundsCategoryIII",
    ),
    # Public — qualified / retail
    "QualifiedInstitutionalBuyers": (_PUBLIC, "QualifiedInstitutionalBuyers"),
    "RetailInvestors": (_PUBLIC, "RetailInvestors"),
    # NonPromoterNonPublic — additional
    "EmployeeStockOptionPlan": (_NON_PROMOTER, "EmployeeStockOptionPlan"),
    "UnclaimedShares": (_NON_PROMOTER, "UnclaimedShares"),
    "SignificantBeneficialOwners": (_PUBLIC, "SignificantBeneficialOwners"),
    # Total / aggregate rows
    "TotalShareholdingExcludingUnclaimedShares": ("Total", "TotalExcludingUnclaimed"),
    "GrandTotal": ("Total", "GrandTotal"),
    "TotalShareholdingOfPromoterAndPromoterGroup": (_PROMOTER, "Total"),
}

# Build the full _MEMBER_CATEGORY mapping (88 entries).
# AIDEV-NOTE: This constant is intentionally module-private.
# The count must remain at 88 to satisfy the acceptance criteria.
_MEMBER_CATEGORY: dict[str, tuple[str, str]] = {}

for _m in _PROMOTER_SUBS:
    _MEMBER_CATEGORY[_m] = (_PROMOTER, _m)
for _m in _PUBLIC_SUBS:
    _MEMBER_CATEGORY[_m] = (_PUBLIC, _m)
for _m in _NON_PROMOTER_SUBS:
    _MEMBER_CATEGORY[_m] = (_NON_PROMOTER, _m)
for _m, _cat in _TOP_LEVEL_MEMBERS.items():
    _MEMBER_CATEGORY[_m] = (_cat, "")
_MEMBER_CATEGORY.update(_ADDITIONAL_MEMBERS)

# ---------------------------------------------------------------------------
# Module-private constants: axis -> sub_category mapping (47 entries)
# ---------------------------------------------------------------------------

# AIDEV-NOTE: This constant is intentionally module-private.
# The count must remain at 47 to satisfy the acceptance criteria.
_AXIS_TO_SUBCATEGORY: dict[str, str] = {
    # Promoter axes
    "DetailsSharesHeldByIndividualsOrHUFAxis": "IndividualsOrHinduUndividedFamily",
    "DetailsOfSharesHeldByOthersIndianShareholdersAxis": "OtherIndianShareholders",
    "DetailsOfSharesHeldByNonResidentIndividualsOrForeignIndividualsAxis": "NonResidentIndividualsOrForeignIndividuals",
    "DetailsOfSharesHeldByForeignGovernmentAxis": "ForeignGovernment",
    "DetailsOfSharesHeldByForeignInstitutionsAxis": "ForeignInstitutions",
    "DetailsOfSharesHeldByForeignPortfolioInvestorAxis": "ForeignPortfolioInvestor",
    "DetailsOfSharesHeldByOtherForeignShareholdersAxis": "OtherForeignShareholders",
    "DetailsOfSharesHeldByCentralGovernmentOrPresidentOfIndiaAxis": "CentralGovernmentOrPresidentOfIndia",
    "DetailsOfSharesHeldByStateGovernmentsOrGovernorsAxis": "StateGovernmentsOrGovernors",
    "DetailsOfSharesHeldByShareholdingByCompaniesOrBodiesCorporateAxis": "ShareholdingByCompaniesOrBodiesCorporatewhereCentralOrStateGovernmentIsPromoter",
    "DetailsOfSharesHeldByAssociateCompaniesOrSubsidiariesAxis": "AssociateCompaniesOrSubsidiaries",
    "DetailsOfSharesHeldByDirectorsAndDirectorsRelativesAxis": "DirectorsAndDirectorsRelatives",
    "DetailsOfSharesHeldByKeyManagerialPersonnelAxis": "KeyManagerialPersonnel",
    # Public axes
    "DetailsOfSharesHeldByMutualFundsOrUtiAxis": "MutualFundsOrUti",
    "DetailsOfSharesHeldByVentureCapitalFundsAxis": "VentureCapitalFunds",
    "DetailsOfSharesHeldByAlternativeInvestmentFundsAxis": "AlternativeInvestmentFunds",
    "DetailsOfSharesHeldByBanksAxis": "Banks",
    "DetailsOfSharesHeldByInsuranceCompaniesAxis": "InsuranceCompanies",
    "DetailsOfSharesHeldByProvidentFundsOrPensionFundsAxis": "ProvidentFundsOrPensionFunds",
    "DetailsOfSharesHeldByForeignDirectInvestmentAxis": "ForeignDirectInvestment",
    "DetailsOfSharesHeldByForeignVentureCapitalInvestorsAxis": "ForeignVentureCapitalInvestors",
    "DetailsOfSharesHeldByInstitutionsForeignPortfolioInvestorOneAxis": "InstitutionsForeignPortfolioInvestorCatergoryOne",
    "DetailsOfSharesHeldByInstitutionsForeignPortfolioInvestorTwoAxis": "InstitutionsForeignPortfolioInvestorCatergoryTwo",
    "DetailsOfSharesHeldByOverseasDepositoriesAxis": "OverseasDepositories",
    "DetailsOfSharesHeldByResidentIndividualShareholdersHoldingNominalShareCapitalUpToRsTwoLakhAxis": "ResidentIndividualShareholdersHoldingNominalShareCapitalUpToRsTwoLakh",
    "DetailsOfSharesHeldByResidentIndividualShareholdersHoldingNominalShareCapitalInExcessOfRsTwoLakhAxis": "ResidentIndividualShareholdersHoldingNominalShareCapitalInExcessOfRsTwoLakh",
    "DetailsOfSharesHeldByNonResidentIndiansAxis": "NonResidentIndians",
    "DetailsOfSharesHeldByForeignNationalsAxis": "ForeignNationals",
    "DetailsOfSharesHeldByForeignCompaniesAxis": "ForeignCompanies",
    "DetailsOfSharesHeldByBodiesCorporateAxis": "BodiesCorporate",
    "DetailsOfSharesHeldByOtherNonInstitutionsAxis": "OtherNonInstitutions",
    # NonPromoterNonPublic axes
    "DetailsOfSharesHeldByCustodianOrDRHolderAxis": "CustodianOrDRHolder",
    "DetailsOfSharesHeldByEmployeeBenefitsTrustsAxis": "EmployeeBenefitsTrusts",
    # Additional axes observed in real filings
    "DetailsOfSharesHeldByOtherInstitutionsDomesticAxis": "OtherInstitutionsDomestic",
    "DetailsOfSharesHeldByOtherInstitutionsForeignAxis": "OtherInstitutionsForeign",
    "DetailsOfSharesHeldByNBFCsRegisteredWithRbiAxis": "NBFCsRegisteredWithRbi",
    "DetailsOfSharesHeldByOtherFinancialInstitutionsAxis": "OtherFinancialInstitutions",
    "DetailsOfSharesHeldBySovereignWealthFundsDomesticAxis": "SovereignWealthFundsDomestic",
    "DetailsOfSharesHeldBySovereignWealthFundsForeignAxis": "SovereignWealthFundsForeign",
    "DetailsOfSharesHeldByAssetReconstructionCompaniesAxis": "AssetReconstructionCompanies",
    "DetailsOfSharesWhichRemainUnclaimedForPublicShareholdersAxis": "UnclaimedShares",
    "SignificantBeneficialOwnersAxis": "SignificantBeneficialOwners",
    "DetailsOfSharesHeldByInvestorEducationAndProtectionFundAxis": "InvestorEducationAndProtectionFund",
    "DetailsOfSharesHeldByCentralGovernmentOrStateGovernmentSAxis": "CentralGovernmentOrStateGovernmentS",
    "DetailsOfSharesHeldByIndianFinancialInstitutionsOrBanksAxis": "IndianFinancialInstitutionsOrBanks",
    "DetailsOfSharesHeldByHighNetWorthIndividualsAxis": "HighNetWorthIndividuals",
    "DetailsOfSharesHeldByClearingMembersAxis": "ClearingMembers",
}

# ---------------------------------------------------------------------------
# Tags we extract for each row (local names without namespace prefix)
# ---------------------------------------------------------------------------

_NUMERIC_TAG_MAP: dict[str, str] = {
    "num_shareholders": "NumberOfShareholders",
    "num_fully_paid_shares": "NumberOfFullyPaidUpEquityShares",
    "num_voting_rights": "NumberOfVotingRights",
    "pct_total_shares": "ShareholdingAsAPercentageOfTotalNumberOfShares",
    "pct_fully_diluted": (
        "ShareholdingAsAPercentageAssumingFullConversion"
        "OfConvertibleSecuritiesAndWarrants"
    ),
    "num_shares_demat": "NumberOfEquitySharesHeldInDematerializedForm",
}

_TEXT_TAG_MAP: dict[str, str] = {
    "shareholder_name": "NameOfTheShareholder",
    "pan": "PermanentAccountNumberOfShareholder",
}

# ---------------------------------------------------------------------------
# CSV column order (matches scripts/nse_parse_xbrl.py)
# ---------------------------------------------------------------------------

_CSV_COLUMNS: list[str] = [
    "symbol",
    "company_name",
    "report_date",
    "category",
    "sub_category",
    "shareholder_name",
    "pan",
    "num_shareholders",
    "num_fully_paid_shares",
    "num_voting_rights",
    "pct_total_shares",
    "pct_fully_diluted",
    "num_shares_demat",
    "is_category_total",
]

# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ContextInfo:
    """Parsed information about a single ``<xbrli:context>``.

    Parameters
    ----------
    context_id : str
        The ``id`` attribute of the context element.
    member_type : str
        ``"explicit"`` for explicitMember, ``"typed"`` for typedMember,
        or ``""`` for top-level contexts without a scenario.
    member_name : str
        For explicit members: the local member name
        (e.g. ``"IndividualsOrHinduUndividedFamily"``).
    axis_name : str
        For typed members: the axis local name
        (e.g. ``"DetailsOfSharesHeldByMutualFundsOrUtiAxis"``).
    domain_value : str
        For typed members: the domain value from the child element.
    is_instant : bool
        ``True`` if the context period is an ``<xbrli:instant>``,
        ``False`` if it is a duration.
    """

    context_id: str
    member_type: str = ""
    member_name: str = ""
    axis_name: str = ""
    domain_value: str = ""
    is_instant: bool = False


@dataclass(frozen=True)
class ShareholderRow:
    """A single row of shareholding data.

    Parameters
    ----------
    symbol : str
        NSE/BSE ticker symbol.
    company_name : str
        Full company name.
    report_date : str
        Report date in ``YYYY-MM-DD`` format.
    category : str
        Top-level shareholding category (e.g. ``"PromoterAndPromoterGroup"``).
    sub_category : str
        Sub-category within the top-level category.
    shareholder_name : str
        Name of individual shareholder (detail rows only).
    pan : str
        PAN of individual shareholder (detail rows only).
    num_shareholders : str
        Number of shareholders (may be empty).
    num_fully_paid_shares : str
        Number of fully paid-up equity shares (may be empty).
    num_voting_rights : str
        Number of voting rights (may be empty).
    pct_total_shares : str
        Shareholding as % of total shares (may be empty).
    pct_fully_diluted : str
        Shareholding on fully diluted basis (may be empty).
    num_shares_demat : str
        Shares held in dematerialised form (may be empty).
    is_category_total : str
        ``"true"`` for category-level aggregation rows,
        ``"false"`` for individual shareholder detail rows.
    """

    symbol: str = ""
    company_name: str = ""
    report_date: str = ""
    category: str = ""
    sub_category: str = ""
    shareholder_name: str = ""
    pan: str = ""
    num_shareholders: str = ""
    num_fully_paid_shares: str = ""
    num_voting_rights: str = ""
    pct_total_shares: str = ""
    pct_fully_diluted: str = ""
    num_shares_demat: str = ""
    is_category_total: str = "true"

    def as_list(self) -> list[str]:
        """Return values in CSV column order.

        Returns
        -------
        list[str]
            Values ordered as ``_CSV_COLUMNS``.
        """
        return [getattr(self, col) for col in _CSV_COLUMNS]


@dataclass(frozen=True)
class ParseResult:
    """Result of parsing a single XBRL shareholding file.

    Parameters
    ----------
    symbol : str
        NSE/BSE ticker symbol extracted from the XBRL document.
    as_on_date : str
        Report date in ``YYYY-MM-DD`` format.
    rows : tuple[ShareholderRow, ...]
        All parsed shareholding rows (category totals + detail rows).
    """

    symbol: str = ""
    as_on_date: str = ""
    rows: tuple[ShareholderRow, ...] = field(default_factory=tuple)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _strip_member_suffix(name: str) -> str:
    """Remove ``in-bse-shp:`` prefix and trailing ``Member`` suffix.

    Parameters
    ----------
    name : str
        Raw member value from an ``explicitMember`` element.
        May contain leading/trailing whitespace or newlines.

    Returns
    -------
    str
        Local name without prefix and ``Member`` suffix.

    Examples
    --------
    >>> _strip_member_suffix("in-bse-shp:MutualFundsOrUtiMember")
    'MutualFundsOrUti'
    >>> _strip_member_suffix("\\n  in-bse-shp:PublicShareholdingMember\\n")
    'PublicShareholding'
    """
    # Strip whitespace first so startswith/endswith work on actual content
    name = name.strip()
    if name.startswith("in-bse-shp:"):
        name = name[len("in-bse-shp:") :]
    if name.endswith("Member"):
        name = name[: -len("Member")]
    return name


def _strip_axis_ns(name: str) -> str:
    """Strip ``in-bse-shp:`` prefix from an axis name.

    Parameters
    ----------
    name : str
        Raw axis value from a ``dimension`` attribute.

    Returns
    -------
    str
        Local axis name without namespace prefix.

    Examples
    --------
    >>> _strip_axis_ns("in-bse-shp:DetailsOfSharesHeldByMutualFundsOrUtiAxis")
    'DetailsOfSharesHeldByMutualFundsOrUtiAxis'
    """
    if name.startswith("in-bse-shp:"):
        return name[len("in-bse-shp:") :]
    return name


# ---------------------------------------------------------------------------
# Context parsing
# ---------------------------------------------------------------------------


def _parse_contexts(root: ET.Element) -> dict[str, ContextInfo]:
    """Parse all ``<xbrli:context>`` elements from the document root.

    Parameters
    ----------
    root : ET.Element
        Root element of the parsed XBRL document.

    Returns
    -------
    dict[str, ContextInfo]
        Mapping from context ID to its parsed ``ContextInfo``.
    """
    contexts: dict[str, ContextInfo] = {}

    for ctx_elem in root.iter(f"{_XBRLI_PREFIX}context"):
        cid = ctx_elem.get("id", "")

        # Determine if instant or duration
        instant_elem = ctx_elem.find(f".//{_XBRLI_PREFIX}instant")
        is_instant = instant_elem is not None

        member_type = ""
        member_name = ""
        axis_name = ""
        domain_value = ""

        scenario = ctx_elem.find(f"{_XBRLI_PREFIX}scenario")
        if scenario is not None:
            explicit = scenario.find(f"{_XBRLDI_PREFIX}explicitMember")
            typed = scenario.find(f"{_XBRLDI_PREFIX}typedMember")

            if explicit is not None:
                member_type = "explicit"
                member_name = _strip_member_suffix(explicit.text or "")
            elif typed is not None:
                member_type = "typed"
                axis_name = _strip_axis_ns(typed.get("dimension", ""))
                for child in typed:
                    domain_value = child.text or ""
                    break

        contexts[cid] = ContextInfo(
            context_id=cid,
            member_type=member_type,
            member_name=member_name,
            axis_name=axis_name,
            domain_value=domain_value,
            is_instant=is_instant,
        )

    logger.debug(
        "Parsed XBRL contexts",
        count=len(contexts),
    )
    return contexts


# ---------------------------------------------------------------------------
# Data extraction
# ---------------------------------------------------------------------------


def _extract_data_by_context(
    root: ET.Element,
) -> dict[str, dict[str, str]]:
    """Group all ``in-bse-shp:*`` element values by their ``contextRef``.

    Parameters
    ----------
    root : ET.Element
        Root element of the parsed XBRL document.

    Returns
    -------
    dict[str, dict[str, str]]
        Mapping from contextRef -> {local_tag_name -> text_value}.
    """
    data: dict[str, dict[str, str]] = {}

    for elem in root.iter():
        tag = elem.tag
        if not tag.startswith(_SHP_PREFIX):
            continue
        ctx_ref = elem.get("contextRef")
        if not ctx_ref:
            continue

        local = tag[len(_SHP_PREFIX) :]
        text = (elem.text or "").strip()

        if ctx_ref not in data:
            data[ctx_ref] = {}
        data[ctx_ref][local] = text

    logger.debug(
        "Extracted XBRL data by context",
        context_count=len(data),
    )
    return data


# ---------------------------------------------------------------------------
# Row construction helpers
# ---------------------------------------------------------------------------


def _resolve_category(member_name: str) -> tuple[str, str]:
    """Resolve a member name to ``(category, sub_category)``.

    Parameters
    ----------
    member_name : str
        Local member name (e.g. ``"IndividualsOrHinduUndividedFamily"``).

    Returns
    -------
    tuple[str, str]
        ``(category, sub_category)`` pair.
        Falls back to ``("Unknown", member_name)`` if not found.
    """
    if member_name in _MEMBER_CATEGORY:
        return _MEMBER_CATEGORY[member_name]
    logger.debug("Unknown XBRL member, falling back", member=member_name)
    return ("Unknown", member_name)


def _resolve_detail_category(axis_name: str) -> tuple[str, str]:
    """Resolve a typed-dimension axis name to ``(category, sub_category)``.

    Parameters
    ----------
    axis_name : str
        Local axis name (e.g. ``"DetailsOfSharesHeldByMutualFundsOrUtiAxis"``).

    Returns
    -------
    tuple[str, str]
        ``(category, sub_category)`` pair.
        Falls back to ``("Unknown", sub or axis_name)`` if not found.
    """
    sub = _AXIS_TO_SUBCATEGORY.get(axis_name, "")
    if sub and sub in _MEMBER_CATEGORY:
        cat, _ = _MEMBER_CATEGORY[sub]
        return (cat, sub)
    logger.debug(
        "Unknown XBRL axis, falling back",
        axis=axis_name,
        resolved_sub=sub,
    )
    return ("Unknown", sub or axis_name)


def _build_category_rows(
    contexts: dict[str, ContextInfo],
    data_by_ctx: dict[str, dict[str, str]],
    meta: dict[str, str],
) -> list[ShareholderRow]:
    """Build rows for category-level aggregation (explicitMember contexts).

    Parameters
    ----------
    contexts : dict[str, ContextInfo]
        Parsed context map.
    data_by_ctx : dict[str, dict[str, str]]
        Data grouped by contextRef.
    meta : dict[str, str]
        Company-level metadata (symbol, company_name, report_date).

    Returns
    -------
    list[ShareholderRow]
        Category-level aggregation rows with ``is_category_total="true"``.
    """
    rows: list[ShareholderRow] = []

    for cid, info in contexts.items():
        if info.member_type != "explicit":
            continue
        if not info.is_instant:
            continue

        vals = data_by_ctx.get(cid, {})
        if not vals:
            continue

        cat, sub = _resolve_category(info.member_name)

        row_kwargs: dict[str, str] = {
            "symbol": meta.get("symbol", ""),
            "company_name": meta.get("company_name", ""),
            "report_date": meta.get("report_date", ""),
            "category": cat,
            "sub_category": sub,
            "is_category_total": "true",
        }
        for csv_col, xbrl_tag in _NUMERIC_TAG_MAP.items():
            row_kwargs[csv_col] = vals.get(xbrl_tag, "")

        rows.append(ShareholderRow(**row_kwargs))

    logger.debug("Built category rows", count=len(rows))
    return rows


def _build_detail_rows(
    contexts: dict[str, ContextInfo],
    data_by_ctx: dict[str, dict[str, str]],
    meta: dict[str, str],
) -> list[ShareholderRow]:
    """Build rows for individual shareholders (typedMember contexts).

    Duration contexts carry text data (name, PAN) and instant contexts
    carry numeric data.  Both are keyed by ``(axis_name, domain_value)``
    and merged before constructing the row.

    Parameters
    ----------
    contexts : dict[str, ContextInfo]
        Parsed context map.
    data_by_ctx : dict[str, dict[str, str]]
        Data grouped by contextRef.
    meta : dict[str, str]
        Company-level metadata (symbol, company_name, report_date).

    Returns
    -------
    list[ShareholderRow]
        Individual shareholder rows with ``is_category_total="false"``.
    """
    # Group contexts by (axis_name, domain_value)
    groups: dict[tuple[str, str], dict[str, str]] = {}

    for cid, info in contexts.items():
        if info.member_type != "typed":
            continue
        key = (info.axis_name, info.domain_value)
        vals = data_by_ctx.get(cid, {})
        if not vals:
            continue

        if key not in groups:
            groups[key] = {}
        groups[key].update(vals)

    rows: list[ShareholderRow] = []
    for (axis_name, _), merged in groups.items():
        cat, sub = _resolve_detail_category(axis_name)

        row_kwargs: dict[str, str] = {
            "symbol": meta.get("symbol", ""),
            "company_name": meta.get("company_name", ""),
            "report_date": meta.get("report_date", ""),
            "category": cat,
            "sub_category": sub,
            "is_category_total": "false",
        }
        for csv_col, xbrl_tag in _TEXT_TAG_MAP.items():
            row_kwargs[csv_col] = merged.get(xbrl_tag, "")
        for csv_col, xbrl_tag in _NUMERIC_TAG_MAP.items():
            row_kwargs[csv_col] = merged.get(xbrl_tag, "")

        rows.append(ShareholderRow(**row_kwargs))

    logger.debug("Built detail rows", count=len(rows))
    return rows


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def _validate_xbrl_namespace(root: ET.Element) -> None:
    """Validate the root element exposes the expected SHP namespace.

    Uses an O(1) check via the root tag. When the root itself does not
    carry the SHP namespace (typical case: root is ``xbrli:xbrl``), scan
    for the first child element that uses ``_SHP_PREFIX`` — this
    short-circuits on the first match and avoids traversing the full
    document for valid inputs.

    Parameters
    ----------
    root : ET.Element
        Root element of the parsed XBRL document.

    Raises
    ------
    NseParseError
        If no element in the document uses the expected SHP namespace.
    """
    root_tag = root.tag
    if root_tag.startswith("{"):
        found_ns = root_tag[1 : root_tag.index("}")]
        if found_ns == XBRL_SHP_NS:
            return  # Root itself carries the expected namespace
        # Root uses a different namespace (e.g. xbrli); check first SHP child
        first_shp = next(
            (elem for elem in root.iter() if elem.tag.startswith(_SHP_PREFIX)),
            None,
        )
        if first_shp is None:
            raise NseParseError(
                f"XBRL namespace mismatch: expected '{XBRL_SHP_NS}'"
                " not found in document",
                raw_data=None,
                field="namespace",
            )
        return
    if XBRL_SHP_NS not in root_tag:
        raise NseParseError(
            f"XBRL namespace mismatch: expected '{XBRL_SHP_NS}'"
            " not found in document",
            raw_data=None,
            field="namespace",
        )


def parse_xbrl(xml_bytes: bytes) -> ParseResult:
    """Parse a single XBRL shareholding XML and return structured data.

    Parses the in-bse-shp (2022-09-30) XBRL document and returns a
    ``ParseResult`` containing company metadata and all shareholding rows.

    Parameters
    ----------
    xml_bytes : bytes
        Raw XML content of the XBRL shareholding file. Must not exceed
        ``_MAX_XBRL_BYTES`` (10 MiB) to guard against DoS via oversized
        payloads.

    Returns
    -------
    ParseResult
        Parsed shareholding data with symbol, as_on_date, and rows.

    Raises
    ------
    NseParseError
        If the payload size exceeds ``_MAX_XBRL_BYTES``, or if the document
        does not use the expected XBRL namespace
        (``http://www.bseindia.com/xbrl/shp/2022-09-30/in-bse-shp``).

    Examples
    --------
    >>> xml = Path("shareholding.xml").read_bytes()
    >>> result = parse_xbrl(xml)
    >>> print(result.symbol, result.as_on_date, len(result.rows))
    INFY 2022-09-30 128
    """
    if len(xml_bytes) > _MAX_XBRL_BYTES:
        raise NseParseError(
            f"XBRL payload too large: {len(xml_bytes)} bytes"
            f" (max {_MAX_XBRL_BYTES})",
            raw_data=None,
            field="size",
        )

    logger.debug("Parsing XBRL bytes", size=len(xml_bytes))

    root = ET.fromstring(xml_bytes)

    _validate_xbrl_namespace(root)

    contexts = _parse_contexts(root)
    data_by_ctx = _extract_data_by_context(root)

    # Extract company-level metadata from well-known contexts
    meta_d = data_by_ctx.get("OneD", {})
    meta_i = data_by_ctx.get("OneI", {})

    meta: dict[str, str] = {
        "symbol": meta_d.get("Symbol", ""),
        "company_name": meta_d.get("NameOfTheCompany", ""),
        "report_date": meta_i.get("DateOfReport", ""),
    }

    category_rows = _build_category_rows(contexts, data_by_ctx, meta)
    detail_rows = _build_detail_rows(contexts, data_by_ctx, meta)
    all_rows = tuple(category_rows + detail_rows)

    logger.info(
        "XBRL parsing complete",
        symbol=meta["symbol"],
        as_on_date=meta["report_date"],
        total_rows=len(all_rows),
        category_rows=len(category_rows),
        detail_rows=len(detail_rows),
    )

    return ParseResult(
        symbol=meta["symbol"],
        as_on_date=meta["report_date"],
        rows=all_rows,
    )


# ---------------------------------------------------------------------------
# Module exports
# ---------------------------------------------------------------------------

__all__ = [
    "ContextInfo",
    "ParseResult",
    "ShareholderRow",
    "parse_xbrl",
]

"""NSE Shareholding XBRL parser.

Download XBRL files from NSE archives for each company's latest shareholding
report and parse them into flat CSV files.

.. deprecated::
    # AIDEV-NOTE: DEPRECATED: src/market/nse/xbrl.py へ移行済み。
    # 本スクリプトはスタンドアロン実装であり、後継は src/market/nse/xbrl.py の
    # parse_xbrl() および ShareholdingCollector.fetch_xbrl_detail() を使用する
    # notebook/NSE/nse_full_download.ipynb です。

Usage
-----
    uv run python scripts/nse_parse_xbrl.py
"""

from __future__ import annotations

import csv
import logging
import sqlite3
import time
import xml.etree.ElementTree as ET  # nosec B405
from dataclasses import dataclass, field
from pathlib import Path

import httpx

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DB_PATH = Path("data/cache/nse/nse_index.db")
OUTPUT_BASE = Path("data/cache/nse")

XBRL_NS = "http://www.bseindia.com/xbrl/shp/2022-09-30/in-bse-shp"
XBRLI_NS = "http://www.xbrl.org/2003/instance"
XBRLDI_NS = "http://xbrl.org/2006/xbrldi"

SHP_PREFIX = f"{{{XBRL_NS}}}"
XBRLI_PREFIX = f"{{{XBRLI_NS}}}"
XBRLDI_PREFIX = f"{{{XBRLDI_NS}}}"

DOWNLOAD_DELAY = 0.3  # seconds between HTTP requests

CSV_COLUMNS = [
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

# Tags we extract for each row (local names without namespace prefix).
# Keys = CSV column name, values = XBRL local tag name.
NUMERIC_TAG_MAP: dict[str, str] = {
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

TEXT_TAG_MAP: dict[str, str] = {
    "shareholder_name": "NameOfTheShareholder",
    "pan": "PermanentAccountNumberOfShareholder",
}

# ---------------------------------------------------------------------------
# Category hierarchy mapping.
# Top-level categories: Promoter, Public, NonPromoterNonPublic
#
# The hierarchy is encoded via the explicitMember values.  The context ID
# suffix tells us whether it is an *instant* context (``...I``) or a
# *duration* context (``...D``).  Category-level contexts always use
# ``explicitMember``; detail (individual shareholder) contexts always use
# ``typedMember``.
# ---------------------------------------------------------------------------

# Map member-name -> (category, sub_category).
# "member-name" is the local part after ``in-bse-shp:`` and before ``Member``.

_PROMOTER = "PromoterAndPromoterGroup"
_PUBLIC = "PublicShareholding"
_NON_PROMOTER = "NonPromoterNonPublic"

# Top-level members
_TOP_LEVEL_MEMBERS: dict[str, str] = {
    "ShareholdingOfPromoterAndPromoterGroup": _PROMOTER,
    "PublicShareholding": _PUBLIC,
    "SharesHeldByNonPromoterNonPublicShareholders": _NON_PROMOTER,
    "ShareholdingPattern": "Total",
}

# Sub-categories under Promoter
_PROMOTER_SUBS = [
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

# Sub-categories under Public
_PUBLIC_SUBS = [
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

# Sub-categories under NonPromoterNonPublic
_NON_PROMOTER_SUBS = [
    "CustodianOrDRHolder",
    "EmployeeBenefitsTrusts",
]

# Build the full member -> (category, sub_category) mapping.
MEMBER_CATEGORY: dict[str, tuple[str, str]] = {}

for m in _PROMOTER_SUBS:
    MEMBER_CATEGORY[m] = (_PROMOTER, m)
for m in _PUBLIC_SUBS:
    MEMBER_CATEGORY[m] = (_PUBLIC, m)
for m in _NON_PROMOTER_SUBS:
    MEMBER_CATEGORY[m] = (_NON_PROMOTER, m)
for m, cat in _TOP_LEVEL_MEMBERS.items():
    MEMBER_CATEGORY[m] = (cat, "")

# Mapping from typed-dimension axis local name -> sub_category name.
# The axis name encodes which sub-category the individual shareholders belong to.
# e.g. "DetailsSharesHeldByIndividualsOrHUFAxis" -> IndividualsOrHinduUndividedFamily
#
# We strip "Details", "DetailsOf", "DetailsSharesHeldBy", etc. prefixes and
# the "Axis" suffix, then look up in MEMBER_CATEGORY.  But because the axis
# names are somewhat inconsistent, we build an explicit map from the known
# patterns.
AXIS_TO_SUBCATEGORY: dict[str, str] = {
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
    "DetailsOfSharesHeldByCustodianOrDRHolderAxis": "CustodianOrDRHolder",
    "DetailsOfSharesHeldByEmployeeBenefitsTrustsAxis": "EmployeeBenefitsTrusts",
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
}


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class ContextInfo:
    """Parsed information about a single ``<xbrli:context>``."""

    context_id: str
    # "explicit" or "typed"
    member_type: str = ""
    # For explicit: the member local name (e.g. "IndividualsOrHinduUndividedFamily")
    member_name: str = ""
    # For typed: the axis local name
    axis_name: str = ""
    # For typed: the domain value (e.g. "DetailsSharesHeldByIndividualsOrHUF1")
    domain_value: str = ""
    # Whether this is an instant context (I suffix) vs duration (D suffix)
    is_instant: bool = False


@dataclass
class ShareholderRow:
    """A single CSV row."""

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
        """Return values in CSV column order."""
        return [getattr(self, col) for col in CSV_COLUMNS]


@dataclass
class ParseResult:
    """Result of parsing a single XBRL file."""

    symbol: str = ""
    company_name: str = ""
    report_date: str = ""
    rows: list[ShareholderRow] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _strip_member_suffix(name: str) -> str:
    """Remove trailing 'Member' from a dimension member value.

    ``in-bse-shp:IndividualsOrHinduUndividedFamilyMember``
    -> ``IndividualsOrHinduUndividedFamily``
    """
    if name.startswith("in-bse-shp:"):
        name = name[len("in-bse-shp:") :]
    if name.endswith("Member"):
        name = name[: -len("Member")]
    return name


def _strip_axis_ns(name: str) -> str:
    """Strip ``in-bse-shp:`` prefix from an axis name."""
    if name.startswith("in-bse-shp:"):
        return name[len("in-bse-shp:") :]
    return name


# ---------------------------------------------------------------------------
# Context parsing
# ---------------------------------------------------------------------------


def _parse_contexts(root: ET.Element) -> dict[str, ContextInfo]:
    """Parse all ``<xbrli:context>`` elements and return a mapping from
    context ID to ``ContextInfo``.
    """
    contexts: dict[str, ContextInfo] = {}

    for ctx_elem in root.iter(f"{XBRLI_PREFIX}context"):
        cid = ctx_elem.get("id", "")
        info = ContextInfo(context_id=cid)

        # Detect instant vs duration from period child
        instant_elem = ctx_elem.find(f".//{XBRLI_PREFIX}instant")
        info.is_instant = instant_elem is not None

        # Parse scenario
        scenario = ctx_elem.find(f"{XBRLI_PREFIX}scenario")
        if scenario is not None:
            explicit = scenario.find(f"{XBRLDI_PREFIX}explicitMember")
            typed = scenario.find(f"{XBRLDI_PREFIX}typedMember")

            if explicit is not None:
                info.member_type = "explicit"
                info.member_name = _strip_member_suffix(explicit.text or "")
            elif typed is not None:
                info.member_type = "typed"
                info.axis_name = _strip_axis_ns(typed.get("dimension", ""))
                # The domain value is in the child element
                for child in typed:
                    info.domain_value = child.text or ""
                    break

        contexts[cid] = info

    return contexts


# ---------------------------------------------------------------------------
# Data extraction
# ---------------------------------------------------------------------------


def _extract_data_by_context(
    root: ET.Element,
) -> dict[str, dict[str, str]]:
    """Iterate over all ``in-bse-shp:*`` data elements and group values
    by ``contextRef``.

    Returns a dict mapping contextRef -> {local_tag_name -> text_value}.
    """
    data: dict[str, dict[str, str]] = {}

    for elem in root.iter():
        tag = elem.tag
        if not tag.startswith(SHP_PREFIX):
            continue
        ctx_ref = elem.get("contextRef")
        if not ctx_ref:
            continue

        local = tag[len(SHP_PREFIX) :]
        text = (elem.text or "").strip()

        if ctx_ref not in data:
            data[ctx_ref] = {}
        data[ctx_ref][local] = text

    return data


# ---------------------------------------------------------------------------
# Row construction
# ---------------------------------------------------------------------------


def _resolve_category(
    member_name: str,
) -> tuple[str, str]:
    """Resolve a member name to (category, sub_category)."""
    if member_name in MEMBER_CATEGORY:
        return MEMBER_CATEGORY[member_name]
    # Fallback: treat as unknown
    return ("Unknown", member_name)


def _resolve_detail_category(axis_name: str) -> tuple[str, str]:
    """Resolve a typed-dimension axis name to (category, sub_category)."""
    sub = AXIS_TO_SUBCATEGORY.get(axis_name, "")
    if sub and sub in MEMBER_CATEGORY:
        cat, _ = MEMBER_CATEGORY[sub]
        return (cat, sub)
    # Fallback
    return ("Unknown", sub or axis_name)


def _build_category_rows(
    contexts: dict[str, ContextInfo],
    data_by_ctx: dict[str, dict[str, str]],
    meta: dict[str, str],
) -> list[ShareholderRow]:
    """Build rows for category-level aggregation (explicitMember contexts)."""
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
        row = ShareholderRow(
            symbol=meta.get("symbol", ""),
            company_name=meta.get("company_name", ""),
            report_date=meta.get("report_date", ""),
            category=cat,
            sub_category=sub,
            is_category_total="true",
        )

        for csv_col, xbrl_tag in NUMERIC_TAG_MAP.items():
            setattr(row, csv_col, vals.get(xbrl_tag, ""))

        rows.append(row)

    return rows


def _build_detail_rows(
    contexts: dict[str, ContextInfo],
    data_by_ctx: dict[str, dict[str, str]],
    meta: dict[str, str],
) -> list[ShareholderRow]:
    """Build rows for individual shareholders (typedMember contexts).

    Each shareholder has two contexts sharing the same domain value:
    - A duration context (``...D``) carrying text data (name, PAN)
    - An instant context (``...I``) carrying numeric data
    We group by ``(axis_name, domain_value)`` and merge.
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
    for (axis_name, _domain), merged in groups.items():
        cat, sub = _resolve_detail_category(axis_name)

        row = ShareholderRow(
            symbol=meta.get("symbol", ""),
            company_name=meta.get("company_name", ""),
            report_date=meta.get("report_date", ""),
            category=cat,
            sub_category=sub,
            is_category_total="false",
        )

        # Text fields
        for csv_col, xbrl_tag in TEXT_TAG_MAP.items():
            setattr(row, csv_col, merged.get(xbrl_tag, ""))

        # Numeric fields
        for csv_col, xbrl_tag in NUMERIC_TAG_MAP.items():
            setattr(row, csv_col, merged.get(xbrl_tag, ""))

        rows.append(row)

    return rows


# ---------------------------------------------------------------------------
# XBRL parsing (main)
# ---------------------------------------------------------------------------


def parse_xbrl(xml_bytes: bytes) -> ParseResult:
    """Parse a single XBRL shareholding XML and return structured data."""
    root = ET.fromstring(xml_bytes)  # nosec B314

    contexts = _parse_contexts(root)
    data_by_ctx = _extract_data_by_context(root)

    # Extract company-level metadata from the "OneD" / "OneI" contexts.
    meta_d = data_by_ctx.get("OneD", {})
    meta_i = data_by_ctx.get("OneI", {})

    meta: dict[str, str] = {
        "symbol": meta_d.get("Symbol", ""),
        "company_name": meta_d.get("NameOfTheCompany", ""),
        "report_date": meta_i.get("DateOfReport", ""),
    }

    category_rows = _build_category_rows(contexts, data_by_ctx, meta)
    detail_rows = _build_detail_rows(contexts, data_by_ctx, meta)

    return ParseResult(
        symbol=meta["symbol"],
        company_name=meta["company_name"],
        report_date=meta["report_date"],
        rows=category_rows + detail_rows,
    )


# ---------------------------------------------------------------------------
# CSV output
# ---------------------------------------------------------------------------


def write_csv(result: ParseResult, symbol: str) -> Path:
    """Write parsed shareholding data to CSV.

    Parameters
    ----------
    result : ParseResult
        Parsed XBRL data.
    symbol : str
        NSE symbol (used for folder name).

    Returns
    -------
    Path
        Path to the written CSV file.
    """
    out_dir = OUTPUT_BASE / symbol
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / "shareholding_detail.csv"

    with csv_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(CSV_COLUMNS)
        for row in result.rows:
            writer.writerow(row.as_list())

    return csv_path


# ---------------------------------------------------------------------------
# DB query
# ---------------------------------------------------------------------------


def fetch_latest_xbrl_urls() -> list[tuple[str, str]]:
    """Return ``(symbol, xbrl_url)`` for the latest report of each symbol.

    Returns
    -------
    list[tuple[str, str]]
        List of (symbol, xbrl_url) pairs.
    """
    conn = sqlite3.connect(str(DB_PATH))
    try:
        cur = conn.execute(
            """
            SELECT symbol, xbrl_url
            FROM shareholdings
            WHERE (symbol, as_on_date) IN (
                SELECT symbol, MAX(as_on_date)
                FROM shareholdings
                GROUP BY symbol
            )
            AND xbrl_url IS NOT NULL
            AND xbrl_url != ''
            ORDER BY symbol
            """
        )
        return cur.fetchall()
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Download
# ---------------------------------------------------------------------------


def download_xbrl(url: str, client: httpx.Client) -> bytes:
    """Download an XBRL file and return raw bytes.

    Parameters
    ----------
    url : str
        Full URL to the XBRL XML file.
    client : httpx.Client
        Reusable HTTP client.

    Returns
    -------
    bytes
        Raw XML content.

    Raises
    ------
    httpx.HTTPStatusError
        If the server returns a non-2xx status code.
    """
    resp = client.get(url)
    resp.raise_for_status()
    return resp.content


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    """Entry point: fetch URLs from DB, download, parse, write CSV."""
    start_time = time.monotonic()

    logger.info("Fetching latest XBRL URLs from %s", DB_PATH)
    records = fetch_latest_xbrl_urls()
    total = len(records)
    logger.info("Found %d symbols with XBRL URLs", total)

    ok_count = 0
    fail_count = 0
    failed_symbols: list[str] = []

    with httpx.Client(
        timeout=30.0,
        follow_redirects=True,
        headers={"User-Agent": "Mozilla/5.0 (compatible; quants-nse-parser/1.0)"},
    ) as client:
        for idx, (symbol, url) in enumerate(records, 1):
            if idx % 50 == 0 or idx == 1:
                logger.info(
                    "Progress: %d / %d (OK=%d, Fail=%d)",
                    idx,
                    total,
                    ok_count,
                    fail_count,
                )

            try:
                xml_bytes = download_xbrl(url, client)
                result = parse_xbrl(xml_bytes)
                csv_path = write_csv(result, symbol)
                ok_count += 1
                logger.debug("Wrote %s (%d rows)", csv_path, len(result.rows))
            except Exception:
                fail_count += 1
                failed_symbols.append(symbol)
                logger.warning("Failed to process %s", symbol, exc_info=True)

            if idx < total:
                time.sleep(DOWNLOAD_DELAY)

    elapsed = time.monotonic() - start_time
    minutes = int(elapsed // 60)
    seconds = int(elapsed % 60)

    logger.info("")
    logger.info("=== XBRL Parse Summary ===")
    logger.info("Total symbols:     %d", total)
    logger.info("Parsed OK:         %d", ok_count)
    logger.info("Failed:            %d", fail_count)
    logger.info("Output directory:  data/cache/nse/{SYMBOL}/shareholding_detail.csv")
    logger.info("Elapsed time:      %dm %ds", minutes, seconds)

    if failed_symbols:
        logger.info("Failed symbols: %s", ", ".join(failed_symbols[:20]))
        if len(failed_symbols) > 20:
            logger.info("  ... and %d more", len(failed_symbols) - 20)

    # Merge all per-symbol CSVs into a single file
    merged_path = OUTPUT_BASE / "all_shareholding_detail.csv"
    logger.info("Merging per-symbol CSVs into %s ...", merged_path)
    merge_count = 0
    with merged_path.open("w", encoding="utf-8-sig", newline="") as out:
        header_written = False
        for symbol_dir in sorted(OUTPUT_BASE.iterdir()):
            csv_file = symbol_dir / "shareholding_detail.csv"
            if not csv_file.is_file():
                continue
            with csv_file.open(encoding="utf-8-sig", newline="") as inp:
                for line_no, line in enumerate(inp):
                    if line_no == 0:
                        if not header_written:
                            out.write(line)
                            header_written = True
                        continue
                    out.write(line)
                    merge_count += 1
    logger.info("Merged CSV: %d data rows → %s", merge_count, merged_path)


if __name__ == "__main__":
    main()

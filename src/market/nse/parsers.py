"""NSE API response parsers and numeric cleaning utilities.

This module converts raw JSON responses from the NSE India API and
CSV content into typed dataclasses and pandas DataFrames.

It provides:

- **Cleaning functions**: ``clean_price``, ``clean_volume``,
  ``clean_indian_number`` for converting NSE-formatted string/numeric values
  to native Python numeric types.
- **Quote parser**: ``parse_quote_response`` for converting a NSE
  quote-equity JSON payload to a ``StockQuote`` dataclass.
- **Index parser**: ``parse_index_constituents`` for converting an
  equity-stockIndices JSON payload to a list of ``IndexConstituent`` dataclasses.
- **Financial parser**: ``parse_financial_results`` for converting a
  results-comparision JSON payload to a list of ``FinancialResult`` dataclasses.
- **Event parser**: ``parse_event_calendar`` for converting an event-calendar
  JSON array to a list of ``CorporateEvent`` dataclasses.
- **CSV parsers**: ``parse_stock_list_csv``, ``parse_preopen_data``,
  ``parse_all_indices`` for DataFrame-based parsing.
- **Status parser**: ``parse_market_status`` for converting a marketStatus
  JSON payload to a list of ``MarketStatus`` dataclasses.

All cleaning functions treat empty strings, ``"N/A"``, ``"-"``, and ``None``
as missing data, returning ``None``.  Unknown or malformed formats also return
``None`` with a warning log.

See Also
--------
market.bse.parsers : Similar parser pattern for the BSE module.
market.nse.constants : Field maps used for column renaming.
market.nse.errors : ``NseParseError`` raised on structural failures.
market.nse.types : Typed dataclasses for NSE data.
"""

from __future__ import annotations

import io
import math
from typing import Any

import pandas as pd

from market.nse.constants import (
    ALL_INDICES_COLUMN_MAP,
    EVENT_CALENDAR_FIELD_MAP,
    FINANCIAL_FIELD_MAP,
    PREOPEN_COLUMN_MAP,
    SHAREHOLDING_FIELD_MAP,
    STOCK_LIST_COLUMN_MAP,
)
from market.nse.errors import NseParseError
from market.nse.types import (
    CorporateEvent,
    FinancialResult,
    IndexConstituent,
    MarketStatus,
    ShareholdingPattern,
    StockQuote,
)
from utils_core.logging import get_logger

# ---------------------------------------------------------------------------
# Module-level pre-computed lookup constants (performance: avoid repeated
# linear scans of constant dicts inside per-record loops)
# ---------------------------------------------------------------------------

# FINANCIAL_FIELD_MAP reverse lookups for parse_financial_results()
# AIDEV-NOTE: Pre-computed once at module load to avoid O(n×m) per-record scans
_FINANCIAL_FROM_DATE_KEY: str = next(
    (k for k, v in FINANCIAL_FIELD_MAP.items() if v == "period_from"), "re_from_dt"
)
_FINANCIAL_TO_DATE_KEY: str = next(
    (k for k, v in FINANCIAL_FIELD_MAP.items() if v == "period_to"), "re_to_dt"
)

# EVENT_CALENDAR_FIELD_MAP reverse lookups for parse_event_calendar()
_EVT_SYM_KEY: str = next(
    (k for k, v in EVENT_CALENDAR_FIELD_MAP.items() if v == "symbol"), "symbol"
)
_EVT_CO_KEY: str = next(
    (k for k, v in EVENT_CALENDAR_FIELD_MAP.items() if v == "company_name"),
    "company_name",
)
_EVT_PUR_KEY: str = next(
    (k for k, v in EVENT_CALENDAR_FIELD_MAP.items() if v == "purpose"), "purpose"
)
_EVT_DESC_KEY: str = next(
    (k for k, v in EVENT_CALENDAR_FIELD_MAP.items() if v == "description"),
    "description",
)
_EVT_DATE_KEY: str = next(
    (k for k, v in EVENT_CALENDAR_FIELD_MAP.items() if v == "date"), "date"
)

# SHAREHOLDING_FIELD_MAP reverse lookups for parse_shareholding_pattern()
# AIDEV-NOTE: Pre-computed once at module load to avoid O(n×m) per-record scans
_SHP_SYM_KEY: str = next(
    (k for k, v in SHAREHOLDING_FIELD_MAP.items() if v == "symbol"), "symbol"
)
_SHP_DATE_KEY: str = next(
    (k for k, v in SHAREHOLDING_FIELD_MAP.items() if v == "date"), "date"
)
_SHP_PROMOTER_KEY: str = next(
    (k for k, v in SHAREHOLDING_FIELD_MAP.items() if v == "promoter_group"),
    "promoterGroup",
)
_SHP_FII_KEY: str = next(
    (k for k, v in SHAREHOLDING_FIELD_MAP.items() if v == "fii"), "fii"
)
_SHP_DII_KEY: str = next(
    (k for k, v in SHAREHOLDING_FIELD_MAP.items() if v == "dii"), "dii"
)
_SHP_PUBLIC_KEY: str = next(
    (k for k, v in SHAREHOLDING_FIELD_MAP.items() if v == "public"), "public"
)

logger = get_logger(__name__)

# Maximum length of raw data stored in NseParseError (CWE-209 mitigation)
_MAX_RAW_DATA_LOG: int = 500

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_MISSING_VALUES: frozenset[str] = frozenset(
    {"", "N/A", "NA", "n/a", "-", "null", "None"}
)
"""String values treated as missing data by all cleaning functions."""


def _is_missing(value: str) -> bool:
    """Return ``True`` if *value* should be treated as missing data.

    Parameters
    ----------
    value : str
        The raw string value to check.

    Returns
    -------
    bool
        ``True`` if *value* is in the set of known missing-data sentinels.
    """
    return value.strip() in _MISSING_VALUES


def _to_str(value: Any) -> str:
    """Convert any value to a string for cleaning.

    Parameters
    ----------
    value : Any
        The raw value from a JSON response.

    Returns
    -------
    str
        String representation of the value.
    """
    if value is None:
        return ""
    return str(value)


# ---------------------------------------------------------------------------
# Cleaning functions
# ---------------------------------------------------------------------------


def clean_price(value: Any) -> float | None:
    """Convert an NSE price value to a float.

    Strips commas before conversion. NSE prices may be returned as
    numeric types (``float`` / ``int``) or as strings.

    Parameters
    ----------
    value : Any
        Price value such as ``2450.00``, ``"2,450.00"``, or ``"-1.95"``.

    Returns
    -------
    float | None
        The numeric price, or ``None`` if the value is missing or
        cannot be parsed.

    Examples
    --------
    >>> clean_price(2450.0)
    2450.0
    >>> clean_price("2,450.00")
    2450.0
    >>> clean_price("-1.95")
    -1.95
    >>> clean_price("") is None
    True
    >>> clean_price("N/A") is None
    True
    """
    if value is None:
        return None

    # Numeric fast-path
    if isinstance(value, (int, float)):
        if not math.isfinite(value):
            logger.warning("Failed to parse price value", raw_value=value)
            return None
        return float(value)

    s = _to_str(value)
    if _is_missing(s):
        return None

    try:
        cleaned = s.replace(",", "").strip()
        if not cleaned:
            return None
        result = float(cleaned)
        if not math.isfinite(result):
            logger.warning("Failed to parse price value", raw_value=value)
            return None
        return result
    except (ValueError, TypeError, OverflowError):
        logger.warning("Failed to parse price value", raw_value=value)
        return None


def clean_volume(value: Any) -> int | None:
    """Convert a trading volume value to an integer.

    Strips commas from formatted number values. NSE volumes may be
    returned as numeric types or as strings.

    Parameters
    ----------
    value : Any
        Volume value such as ``5000000``, ``"48,123,456"``, or ``"5000000"``.

    Returns
    -------
    int | None
        The numeric volume, or ``None`` if the value is missing or
        cannot be parsed.

    Examples
    --------
    >>> clean_volume(5000000)
    5000000
    >>> clean_volume("48,123,456")
    48123456
    >>> clean_volume("") is None
    True
    >>> clean_volume("N/A") is None
    True
    """
    if value is None:
        return None

    # Numeric fast-path
    if isinstance(value, (int, float)):
        if not math.isfinite(value):
            logger.warning("Failed to parse volume value", raw_value=value)
            return None
        return int(float(value))

    s = _to_str(value)
    if _is_missing(s):
        return None

    try:
        cleaned = s.replace(",", "").strip()
        if not cleaned:
            return None
        result = float(cleaned)
        if not math.isfinite(result):
            logger.warning("Failed to parse volume value", raw_value=value)
            return None
        return int(result)
    except (ValueError, TypeError, OverflowError):
        logger.warning("Failed to parse volume value", raw_value=value)
        return None


def clean_indian_number(value: Any) -> float | None:
    """Convert an Indian-formatted number string (lakhs/crores) to a float.

    Indian numbering uses the format ``X,XX,XX,XXX`` where the last group
    is 3 digits and preceding groups are 2 digits.  For example:

    - ``"1,23,456"`` = 1,23,456 (1 lakh 23 thousand 456)
    - ``"12,34,56,789"`` = 12,34,56,789 (12 crore 34 lakh 56 thousand 789)

    Also handles standard comma-separated numbers, plain numbers,
    and numeric types directly.

    Parameters
    ----------
    value : Any
        Number value in Indian or standard format.

    Returns
    -------
    float | None
        The numeric value, or ``None`` if the value is missing or
        cannot be parsed.

    Examples
    --------
    >>> clean_indian_number("1,23,456")
    123456.0
    >>> clean_indian_number("12,34,56,789")
    123456789.0
    >>> clean_indian_number("1234.56")
    1234.56
    >>> clean_indian_number("") is None
    True
    >>> clean_indian_number("N/A") is None
    True
    """
    if value is None:
        return None

    if isinstance(value, (int, float)):
        if not math.isfinite(value):
            logger.warning("Failed to parse Indian number value", raw_value=value)
            return None
        return float(value)

    s = _to_str(value)
    if _is_missing(s):
        return None

    stripped = s.strip()
    if not stripped:
        return None

    try:
        # Remove all commas (works for both Indian and standard formats)
        cleaned = stripped.replace(",", "")
        result = float(cleaned)
        if not math.isfinite(result):
            logger.warning("Failed to parse Indian number value", raw_value=value)
            return None
        return result
    except (ValueError, TypeError, OverflowError):
        logger.warning("Failed to parse Indian number value", raw_value=value)
        return None


# ---------------------------------------------------------------------------
# Quote response parser
# ---------------------------------------------------------------------------


def parse_quote_response(raw: dict[str, Any]) -> StockQuote:
    """Parse an NSE quote-equity JSON response into a StockQuote.

    The NSE API returns quote data nested in ``info``, ``metadata``,
    ``priceInfo``, ``securityInfo``, and ``industryInfo`` sub-objects.
    This function extracts the relevant fields and maps them to a
    ``StockQuote`` dataclass.

    Parameters
    ----------
    raw : dict[str, Any]
        The raw JSON response from the NSE API's ``/api/quote-equity``
        endpoint.  Expected top-level keys include ``"info"``,
        ``"metadata"``, ``"priceInfo"``, ``"securityInfo"``,
        ``"industryInfo"``.

    Returns
    -------
    StockQuote
        A frozen dataclass containing the parsed quote data.

    Raises
    ------
    NseParseError
        If the response is empty, not a dict, or missing required sub-objects.

    Examples
    --------
    >>> raw = {
    ...     "info": {
    ...         "symbol": "INFY",
    ...         "companyName": "Infosys Limited",
    ...         "isin": "INE009A01021",
    ...         "isFNOSec": True,
    ...         "isSLBSec": True,
    ...         "isSuspended": False,
    ...         "listingDate": "1995-02-08",
    ...         "segment": "EQUITY",
    ...     },
    ...     "metadata": {
    ...         "series": "EQ",
    ...         "pdSectorPe": 17.91,
    ...         "pdSymbolPe": 18.48,
    ...         "pdSectorInd": "NIFTY 50",
    ...         "pdSectorIndAll": ["NIFTY 50"],
    ...     },
    ...     "priceInfo": {
    ...         "lastPrice": 1269.3,
    ...         "change": -6.4,
    ...         "pChange": -0.50,
    ...         "previousClose": 1275.7,
    ...         "open": 1260.0,
    ...         "vwap": 1268.09,
    ...         "lowerCP": "1148.20",
    ...         "upperCP": "1403.20",
    ...         "basePrice": 1275.7,
    ...         "intraDayHighLow": {"min": 1259.8, "max": 1276.7},
    ...         "weekHighLow": {"min": 1215.1, "minDate": "19-Mar-2026",
    ...                         "max": 1728.0, "maxDate": "03-Feb-2026"},
    ...     },
    ...     "securityInfo": {
    ...         "faceValue": 5,
    ...         "issuedSize": 4055591723,
    ...         "boardStatus": "Main",
    ...         "tradingStatus": "Active",
    ...     },
    ...     "industryInfo": {
    ...         "macro": "Information Technology",
    ...         "sector": "Information Technology",
    ...         "industry": "IT - Software",
    ...         "basicIndustry": "Computers - Software & Consulting",
    ...     },
    ... }
    >>> quote = parse_quote_response(raw)
    >>> quote.symbol
    'INFY'
    """
    logger.debug("Parsing NSE quote response")

    if not isinstance(raw, dict):
        raise NseParseError(
            f"Expected dict for quote response, got {type(raw).__name__}",
            raw_data=str(raw)[:_MAX_RAW_DATA_LOG],
            field=None,
        )

    if not raw:
        raise NseParseError(
            "Empty NSE quote response",
            raw_data=str(raw)[:_MAX_RAW_DATA_LOG],
            field=None,
        )

    _required_sub_objects = {
        "info",
        "metadata",
        "priceInfo",
        "securityInfo",
        "industryInfo",
    }
    missing = _required_sub_objects - set(raw.keys())
    if missing:
        raise NseParseError(
            f"Missing required sub-objects in quote response: {sorted(missing)}",
            raw_data=str(raw)[:_MAX_RAW_DATA_LOG],
            field=", ".join(sorted(missing)),
        )

    info = raw["info"]
    metadata = raw["metadata"]
    price_info = raw["priceInfo"]
    security_info = raw["securityInfo"]
    industry_info = raw["industryInfo"]

    intraday = price_info.get("intraDayHighLow", {}) or {}
    week_hl = price_info.get("weekHighLow", {}) or {}

    quote = StockQuote(
        symbol=str(info.get("symbol", "")),
        company_name=str(info.get("companyName", "")),
        series=str(metadata.get("series", "")),
        open=str(price_info.get("open", "")),
        high=str(intraday.get("max", "")),
        low=str(intraday.get("min", "")),
        last_price=str(price_info.get("lastPrice", "")),
        prev_close=str(price_info.get("previousClose", "")),
        change=str(price_info.get("change", "")),
        pct_change=str(price_info.get("pChange", "")),
        total_traded_volume=str(price_info.get("totalTradedVolume", "")),
        total_traded_value=str(price_info.get("totalTradedValue", "")),
    )

    logger.info(
        "NSE quote response parsed",
        symbol=quote.symbol,
        company_name=quote.company_name,
    )

    return quote


# ---------------------------------------------------------------------------
# Index constituents parser
# ---------------------------------------------------------------------------


def parse_index_constituents(raw: dict[str, Any]) -> list[IndexConstituent]:
    """Parse an NSE equity-stockIndices JSON response into IndexConstituents.

    The NSE equity-stockIndices API returns a dict with a ``"data"`` key
    containing a list where ``data[0]`` is the index metadata and
    ``data[1..]`` are the constituent stock entries.

    Parameters
    ----------
    raw : dict[str, Any]
        The raw JSON response from the NSE API's
        ``/api/equity-stockIndices?index=X`` endpoint.

    Returns
    -------
    list[IndexConstituent]
        A list of frozen dataclasses, one per constituent stock.

    Raises
    ------
    NseParseError
        If the response is not a dict, is empty, or missing the ``"data"`` key.

    Examples
    --------
    >>> raw = {
    ...     "name": "NIFTY 50",
    ...     "data": [
    ...         {"symbol": "Nifty 50", "open": 22383.4, "priority": 1},
    ...         {"symbol": "INFY", "series": "EQ", "open": "1260.0",
    ...          "dayHigh": "1276.7", "dayLow": "1259.8",
    ...          "lastPrice": "1269.3", "previousClose": "1275.7",
    ...          "change": "-6.4", "pChange": "-0.50",
    ...          "totalTradedVolume": "5000000",
    ...          "totalTradedValue": "6344500000",
    ...          "yearHigh": "1728.0", "yearLow": "1215.1",
    ...          "priority": 0},
    ...     ],
    ... }
    >>> constituents = parse_index_constituents(raw)
    >>> len(constituents)
    1
    >>> constituents[0].symbol
    'INFY'
    """
    logger.debug("Parsing NSE index constituents response")

    if not isinstance(raw, dict):
        raise NseParseError(
            f"Expected dict for index constituents response, got {type(raw).__name__}",
            raw_data=str(raw)[:_MAX_RAW_DATA_LOG],
            field=None,
        )

    if "data" not in raw:
        raise NseParseError(
            "Missing 'data' key in index constituents response",
            raw_data=str(raw)[:_MAX_RAW_DATA_LOG],
            field="data",
        )

    data_list = raw["data"]
    if not isinstance(data_list, list):
        raise NseParseError(
            f"Expected list for 'data', got {type(data_list).__name__}",
            raw_data=str(raw)[:_MAX_RAW_DATA_LOG],
            field="data",
        )

    # data[0] is the index itself (priority=1), data[1..] are constituents
    # Skip entries without 'series' field (the index row) or with priority != 0
    constituents: list[IndexConstituent] = []
    for item in data_list:
        if not isinstance(item, dict):
            continue
        # Skip the index metadata entry
        if item.get("priority", 0) == 1 or "series" not in item:
            continue

        constituent = IndexConstituent(
            symbol=str(item.get("symbol", "")),
            series=str(item.get("series", "")),
            open=str(item.get("open", "")),
            day_high=str(item.get("dayHigh", "")),
            day_low=str(item.get("dayLow", "")),
            last_price=str(item.get("lastPrice", "")),
            prev_close=str(item.get("previousClose", "")),
            change=str(item.get("change", "")),
            pct_change=str(item.get("pChange", "")),
            total_traded_volume=str(item.get("totalTradedVolume", "")),
            total_traded_value=str(item.get("totalTradedValue", "")),
            year_high=str(item.get("yearHigh", "")),
            year_low=str(item.get("yearLow", "")),
        )
        constituents.append(constituent)

    logger.info(
        "NSE index constituents parsed",
        constituent_count=len(constituents),
        index_name=raw.get("name", ""),
    )

    return constituents


# ---------------------------------------------------------------------------
# Financial results parser
# ---------------------------------------------------------------------------


def parse_financial_results(
    raw: dict[str, Any],
    *,
    symbol: str = "",
) -> list[FinancialResult]:
    """Parse an NSE results-comparision JSON response into FinancialResults.

    The NSE results-comparision API returns a dict with ``"resCmpData"``
    containing a list of quarterly result records, and a ``"bankNonBnking"``
    flag to distinguish banking companies.

    Parameters
    ----------
    raw : dict[str, Any]
        The raw JSON response from the NSE API's
        ``/api/results-comparision?symbol=X`` endpoint.
    symbol : str
        The stock symbol to populate in each result record.  The NSE API
        does not include the symbol in ``resCmpData`` items, so callers
        should pass it explicitly.

    Returns
    -------
    list[FinancialResult]
        A list of frozen dataclasses, one per quarterly result.

    Raises
    ------
    NseParseError
        If the response is not a dict, is empty, or missing ``"resCmpData"``.

    Examples
    --------
    >>> raw = {
    ...     "bankNonBnking": "N",
    ...     "resCmpData": [
    ...         {
    ...             "re_from_dt": "01-OCT-2024",
    ...             "re_to_dt": "31-DEC-2024",
    ...             "re_res_type": "A",
    ...             "re_net_sale": "3491500",
    ...             "re_net_profit": "635800",
    ...             "re_basic_eps_for_cont_dic_opr": "15.31",
    ...             "re_dilut_eps_for_cont_dic_opr": "15.29",
    ...         }
    ...     ],
    ... }
    >>> results = parse_financial_results(raw, symbol="INFY")
    >>> len(results)
    1
    >>> results[0].symbol
    'INFY'
    """
    logger.debug("Parsing NSE financial results response")

    if not isinstance(raw, dict):
        raise NseParseError(
            f"Expected dict for financial results response, got {type(raw).__name__}",
            raw_data=str(raw)[:_MAX_RAW_DATA_LOG],
            field=None,
        )

    if "resCmpData" not in raw:
        raise NseParseError(
            "Missing 'resCmpData' key in financial results response",
            raw_data=str(raw)[:_MAX_RAW_DATA_LOG],
            field="resCmpData",
        )

    data_list = raw["resCmpData"]
    if not isinstance(data_list, list):
        raise NseParseError(
            f"Expected list for 'resCmpData', got {type(data_list).__name__}",
            raw_data=str(raw)[:_MAX_RAW_DATA_LOG],
            field="resCmpData",
        )

    results: list[FinancialResult] = []
    for item in data_list:
        if not isinstance(item, dict):
            continue

        # total_income fallback: try re_total_inc → re_tot_inc → net_sale + other_income
        total_income = (
            clean_price(item.get("re_total_inc"))
            or clean_price(item.get("re_tot_inc"))
            or (
                (clean_price(item.get("re_net_sale")) or 0.0)
                + (clean_price(item.get("re_oth_inc_new")) or 0.0)
            )
            or None
        )

        result = FinancialResult(
            symbol=str(item.get("symbol", "")) or symbol,
            from_date=_to_str(item.get(_FINANCIAL_FROM_DATE_KEY, "")),
            to_date=_to_str(item.get(_FINANCIAL_TO_DATE_KEY, "")),
            income=_to_str(total_income) if total_income is not None else "",
            profit_after_tax=_to_str(item.get("re_net_profit", "")),
            eps=_to_str(item.get("re_basic_eps_for_cont_dic_opr", "")),
            result_type=_to_str(item.get("re_res_type", "")),
            broadcast_date=_to_str(item.get("re_create_dt", "")),
        )
        results.append(result)

    logger.info(
        "NSE financial results parsed",
        result_count=len(results),
    )

    return results


# ---------------------------------------------------------------------------
# Event calendar parser
# ---------------------------------------------------------------------------


def parse_event_calendar(data: list[dict[str, Any]]) -> list[CorporateEvent]:
    """Parse an NSE event-calendar JSON array into CorporateEvents.

    The NSE event-calendar API returns a flat JSON array where each item
    represents one corporate event with keys defined in
    ``EVENT_CALENDAR_FIELD_MAP``.

    Parameters
    ----------
    data : list[dict[str, Any]]
        The raw JSON array from the NSE API's ``/api/event-calendar``
        endpoint.

    Returns
    -------
    list[CorporateEvent]
        A list of frozen dataclasses, one per event.

    Raises
    ------
    NseParseError
        If the input is not a list.

    Examples
    --------
    >>> data = [
    ...     {
    ...         "symbol": "RELIANCE",
    ...         "company": "Reliance Industries Limited",
    ...         "purpose": "Dividend",
    ...         "bm_desc": "Board Meeting to consider dividend.",
    ...         "date": "03-Apr-2026",
    ...     }
    ... ]
    >>> events = parse_event_calendar(data)
    >>> len(events)
    1
    >>> events[0].symbol
    'RELIANCE'
    """
    logger.debug("Parsing NSE event calendar response")

    if not isinstance(data, list):
        raise NseParseError(
            f"Expected list for event calendar response, got {type(data).__name__}",
            raw_data=str(data)[:_MAX_RAW_DATA_LOG],
            field=None,
        )

    events: list[CorporateEvent] = []

    for item in data:
        if not isinstance(item, dict):
            continue

        event = CorporateEvent(
            symbol=str(item.get(_EVT_SYM_KEY, "")),
            company_name=str(item.get(_EVT_CO_KEY, "")),
            purpose=str(item.get(_EVT_PUR_KEY, "")),
            date=str(item.get(_EVT_DATE_KEY, "")),
            description=str(item.get(_EVT_DESC_KEY, "")),
        )
        events.append(event)

    logger.info("NSE event calendar parsed", event_count=len(events))

    return events


# ---------------------------------------------------------------------------
# CSV parsers
# ---------------------------------------------------------------------------


def _decode_csv_bytes(content: bytes) -> str:
    """Decode CSV bytes with multi-encoding fallback.

    Tries utf-8-sig first (BOM-aware), then utf-8, then latin-1.

    Parameters
    ----------
    content : bytes
        Raw bytes from an NSE CSV download.

    Returns
    -------
    str
        Decoded string content.
    """
    for encoding in ("utf-8-sig", "utf-8", "latin-1"):
        try:
            return content.decode(encoding)
        except UnicodeDecodeError:
            continue
    # latin-1 never raises UnicodeDecodeError, so this is unreachable
    return content.decode("latin-1")  # pragma: no cover


def parse_stock_list_csv(content: str | bytes) -> pd.DataFrame:
    """Parse the NSE EQUITY_L.csv stock list into a cleaned pandas DataFrame.

    Reads CSV content from
    ``https://nsearchives.nseindia.com/content/equities/EQUITY_L.csv``,
    renames columns from NSE CSV names to snake_case using
    ``STOCK_LIST_COLUMN_MAP``, and strips whitespace.

    Parameters
    ----------
    content : str | bytes
        The raw CSV content from the NSE stock list download.
        Can be a string or bytes (utf-8 decoded automatically).

    Returns
    -------
    pd.DataFrame
        A DataFrame with snake_case column names representing all
        NSE-listed stocks.

    Raises
    ------
    NseParseError
        If the CSV content cannot be parsed or is empty.

    Examples
    --------
    >>> csv_content = (
    ...     "SYMBOL,NAME OF COMPANY,SERIES,DATE OF LISTING,"
    ...     "PAID UP VALUE,MARKET LOT,ISIN NUMBER,FACE VALUE\\n"
    ...     "RELIANCE,Reliance Industries Limited,EQ,29-NOV-1995,"
    ...     "10,1,INE002A01018,10\\n"
    ... )
    >>> df = parse_stock_list_csv(csv_content)
    >>> df["symbol"].iloc[0]
    'RELIANCE'
    """
    logger.debug("Parsing NSE stock list CSV")

    if isinstance(content, bytes):
        content = _decode_csv_bytes(content)

    if not content.strip():
        raise NseParseError(
            "Empty NSE stock list CSV content",
            raw_data=None,
            field=None,
        )

    try:
        df = pd.read_csv(io.StringIO(content))
    except Exception as e:
        raise NseParseError(
            f"Failed to parse NSE stock list CSV: {e}",
            raw_data=content[:_MAX_RAW_DATA_LOG]
            if len(content) > _MAX_RAW_DATA_LOG
            else content,
            field=None,
        ) from e

    if df.empty:
        logger.info("NSE stock list CSV contains no rows")
        return df

    # Strip whitespace from column names
    df.columns = pd.Index([col.strip() for col in df.columns])

    # Rename columns
    rename_map: dict[str, str] = {}
    for col in df.columns:
        mapped = STOCK_LIST_COLUMN_MAP.get(col)
        if mapped is not None:
            rename_map[col] = mapped
        else:
            rename_map[col] = col.strip().lower().replace(" ", "_")

    df = df.rename(columns=rename_map)

    # Strip whitespace from string columns
    for col in df.columns:
        if df[col].dtype == object:
            df[col] = df[col].str.strip()

    logger.info(
        "NSE stock list CSV parsed",
        row_count=len(df),
        columns=list(df.columns),
    )

    return df


def parse_preopen_data(raw: dict[str, Any]) -> pd.DataFrame:
    """Parse an NSE market-data-pre-open JSON response into a DataFrame.

    The NSE pre-open market API returns a dict with a ``"data"`` key
    containing a list of pre-open session entries for all symbols.

    Parameters
    ----------
    raw : dict[str, Any]
        The raw JSON response from the NSE API's
        ``/api/market-data-pre-open?key=ALL`` endpoint.

    Returns
    -------
    pd.DataFrame
        A DataFrame with snake_case column names representing pre-open
        market data for all symbols.

    Raises
    ------
    NseParseError
        If the response is not a dict or is missing the ``"data"`` key.

    Examples
    --------
    >>> raw = {
    ...     "data": [
    ...         {
    ...             "symbol": "RELIANCE",
    ...             "iep": 2450.0,
    ...             "chn": 25.0,
    ...             "perChn": 1.03,
    ...             "pCls": 2425.0,
    ...             "trdQnty": 50000,
    ...         }
    ...     ]
    ... }
    >>> df = parse_preopen_data(raw)
    >>> df["symbol"].iloc[0]
    'RELIANCE'
    """
    logger.debug("Parsing NSE pre-open market data")

    if not isinstance(raw, dict):
        raise NseParseError(
            f"Expected dict for pre-open data, got {type(raw).__name__}",
            raw_data=str(raw)[:_MAX_RAW_DATA_LOG],
            field=None,
        )

    if "data" not in raw:
        raise NseParseError(
            "Missing 'data' key in pre-open market data response",
            raw_data=str(raw)[:_MAX_RAW_DATA_LOG],
            field="data",
        )

    data_list = raw["data"]
    if not isinstance(data_list, list):
        raise NseParseError(
            f"Expected list for 'data', got {type(data_list).__name__}",
            raw_data=str(raw)[:_MAX_RAW_DATA_LOG],
            field="data",
        )

    if not data_list:
        logger.info("NSE pre-open data contains no rows")
        return pd.DataFrame()

    df = pd.DataFrame(data_list)

    # Rename columns using PREOPEN_COLUMN_MAP
    rename_map: dict[str, str] = {}
    for col in df.columns:
        mapped = PREOPEN_COLUMN_MAP.get(col)
        if mapped is not None:
            rename_map[col] = mapped

    if rename_map:
        df = df.rename(columns=rename_map)

    logger.info(
        "NSE pre-open data parsed",
        row_count=len(df),
        columns=list(df.columns),
    )

    return df


def parse_all_indices(raw: dict[str, Any]) -> pd.DataFrame:
    """Parse an NSE allIndices JSON response into a DataFrame.

    The NSE allIndices API returns a dict with a ``"data"`` key
    containing a list of all index summary entries.

    Parameters
    ----------
    raw : dict[str, Any]
        The raw JSON response from the NSE API's ``/api/allIndices``
        endpoint.

    Returns
    -------
    pd.DataFrame
        A DataFrame with snake_case column names representing all
        NSE indices.

    Raises
    ------
    NseParseError
        If the response is not a dict or is missing the ``"data"`` key.

    Examples
    --------
    >>> raw = {
    ...     "data": [
    ...         {
    ...             "indexSymbol": "NIFTY 50",
    ...             "current": 22371.8,
    ...             "variation": -307.6,
    ...             "percentChange": -1.36,
    ...             "open": 22383.4,
    ...             "high": 22406.0,
    ...             "low": 22182.55,
    ...             "previousClose": 22679.4,
    ...             "yearHigh": 26373.2,
    ...             "yearLow": 21743.65,
    ...         }
    ...     ]
    ... }
    >>> df = parse_all_indices(raw)
    >>> df["index_symbol"].iloc[0]
    'NIFTY 50'
    """
    logger.debug("Parsing NSE all indices response")

    if not isinstance(raw, dict):
        raise NseParseError(
            f"Expected dict for all indices response, got {type(raw).__name__}",
            raw_data=str(raw)[:_MAX_RAW_DATA_LOG],
            field=None,
        )

    if "data" not in raw:
        raise NseParseError(
            "Missing 'data' key in all indices response",
            raw_data=str(raw)[:_MAX_RAW_DATA_LOG],
            field="data",
        )

    data_list = raw["data"]
    if not isinstance(data_list, list):
        raise NseParseError(
            f"Expected list for 'data', got {type(data_list).__name__}",
            raw_data=str(raw)[:_MAX_RAW_DATA_LOG],
            field="data",
        )

    if not data_list:
        logger.info("NSE all indices data contains no rows")
        return pd.DataFrame()

    df = pd.DataFrame(data_list)

    # Rename columns using ALL_INDICES_COLUMN_MAP
    rename_map: dict[str, str] = {}
    for col in df.columns:
        mapped = ALL_INDICES_COLUMN_MAP.get(col)
        if mapped is not None:
            rename_map[col] = mapped

    if rename_map:
        df = df.rename(columns=rename_map)

    logger.info(
        "NSE all indices parsed",
        row_count=len(df),
        columns=list(df.columns),
    )

    return df


# ---------------------------------------------------------------------------
# Market status parser
# ---------------------------------------------------------------------------


def parse_market_status(raw: dict[str, Any]) -> list[MarketStatus]:
    """Parse an NSE marketStatus JSON response into MarketStatus records.

    The NSE marketStatus API returns a dict with a ``"marketState"`` key
    containing a list of market segment status entries.

    Parameters
    ----------
    raw : dict[str, Any]
        The raw JSON response from the NSE API's ``/api/marketStatus``
        endpoint.

    Returns
    -------
    list[MarketStatus]
        A list of frozen dataclasses, one per market segment.

    Raises
    ------
    NseParseError
        If the response is not a dict or is missing the ``"marketState"`` key.

    Examples
    --------
    >>> raw = {
    ...     "marketState": [
    ...         {
    ...             "market": "Capital Market",
    ...             "marketStatus": "Open",
    ...             "tradeDate": "02-Apr-2026",
    ...             "index": "NIFTY 50",
    ...             "last": "22371.80",
    ...             "variation": "-307.60",
    ...             "percentChange": "-1.36",
    ...         }
    ...     ]
    ... }
    >>> statuses = parse_market_status(raw)
    >>> len(statuses)
    1
    >>> statuses[0].market
    'Capital Market'
    """
    logger.debug("Parsing NSE market status response")

    if not isinstance(raw, dict):
        raise NseParseError(
            f"Expected dict for market status response, got {type(raw).__name__}",
            raw_data=str(raw)[:_MAX_RAW_DATA_LOG],
            field=None,
        )

    if "marketState" not in raw:
        raise NseParseError(
            "Missing 'marketState' key in market status response",
            raw_data=str(raw)[:_MAX_RAW_DATA_LOG],
            field="marketState",
        )

    state_list = raw["marketState"]
    if not isinstance(state_list, list):
        raise NseParseError(
            f"Expected list for 'marketState', got {type(state_list).__name__}",
            raw_data=str(raw)[:_MAX_RAW_DATA_LOG],
            field="marketState",
        )

    statuses: list[MarketStatus] = []
    for item in state_list:
        if not isinstance(item, dict):
            continue

        status = MarketStatus(
            market=str(item.get("market", "")),
            market_status=str(item.get("marketStatus", "")),
            trade_date=str(item.get("tradeDate", "")),
            index=str(item.get("index", "")),
            last=str(item.get("last", "")),
            variation=str(item.get("variation", "")),
            pct_change=str(item.get("percentChange", "")),
        )
        statuses.append(status)

    logger.info("NSE market status parsed", segment_count=len(statuses))

    return statuses


# ---------------------------------------------------------------------------
# Shareholding pattern parser
# ---------------------------------------------------------------------------


def parse_shareholding_pattern(
    data: list[dict[str, Any]],
) -> list[ShareholdingPattern]:
    """Parse an NSE corporates-shareholding JSON array into ShareholdingPatterns.

    The NSE shareholding API (``/api/corporates-shareholding``) returns a flat
    JSON array where each item represents one quarterly shareholding record.
    Each entry contains the promoter, FII, DII, and public holding percentages.

    Parameters
    ----------
    data : list[dict[str, Any]]
        The raw JSON array from the NSE API's
        ``/api/corporates-shareholding?symbol=X`` endpoint.

    Returns
    -------
    list[ShareholdingPattern]
        A list of frozen dataclasses, one per quarterly record.

    Raises
    ------
    NseParseError
        If the input is not a list.

    Examples
    --------
    >>> data = [
    ...     {
    ...         "symbol": "RELIANCE",
    ...         "date": "31-Dec-2024",
    ...         "promoterGroup": "50.30",
    ...         "fii": "23.45",
    ...         "dii": "12.10",
    ...         "public": "14.15",
    ...     }
    ... ]
    >>> patterns = parse_shareholding_pattern(data)
    >>> len(patterns)
    1
    >>> patterns[0].symbol
    'RELIANCE'
    >>> patterns[0].promoter_group
    '50.30'
    """
    logger.debug("Parsing NSE shareholding pattern response")

    if not isinstance(data, list):
        raise NseParseError(
            f"Expected list for shareholding pattern response, got {type(data).__name__}",
            raw_data=str(data)[:_MAX_RAW_DATA_LOG],
            field=None,
        )

    patterns: list[ShareholdingPattern] = []

    for item in data:
        if not isinstance(item, dict):
            continue

        pattern = ShareholdingPattern(
            symbol=str(item.get(_SHP_SYM_KEY, "")),
            date=str(item.get(_SHP_DATE_KEY, "")),
            promoter_group=str(item.get(_SHP_PROMOTER_KEY, "")),
            fii=str(item.get(_SHP_FII_KEY, "")),
            dii=str(item.get(_SHP_DII_KEY, "")),
            public=str(item.get(_SHP_PUBLIC_KEY, "")),
        )
        patterns.append(pattern)

    logger.info(
        "NSE shareholding patterns parsed",
        pattern_count=len(patterns),
    )

    return patterns


# ---------------------------------------------------------------------------
# Module exports
# ---------------------------------------------------------------------------

__all__ = [
    "_MISSING_VALUES",
    "clean_indian_number",
    "clean_price",
    "clean_volume",
    "parse_all_indices",
    "parse_event_calendar",
    "parse_financial_results",
    "parse_index_constituents",
    "parse_market_status",
    "parse_preopen_data",
    "parse_quote_response",
    "parse_shareholding_pattern",
    "parse_stock_list_csv",
]

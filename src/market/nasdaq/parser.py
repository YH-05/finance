"""JSON response parser and numeric cleaning utilities for the NASDAQ Screener API.

This module converts raw JSON responses from the NASDAQ Stock Screener API
into pandas DataFrames with properly typed numeric columns.  It provides:

- **Cleaning functions**: ``clean_price``, ``clean_percentage``,
  ``clean_market_cap``, ``clean_volume``, ``clean_ipo_year`` for converting
  formatted string values (e.g. ``"$1,234.56"``, ``"-0.849%"``) to native
  Python numeric types.
- **Column name conversion**: ``_camel_to_snake`` for normalising API
  camelCase keys to snake_case.
- **Response parser**: ``parse_screener_response`` for end-to-end
  conversion of the screener JSON payload to a cleaned DataFrame.

All cleaning functions treat empty strings and ``"N/A"`` as missing data,
returning ``None``.  Unknown or malformed formats also return ``None``
with a warning log.

See Also
--------
market.nasdaq.constants : ``COLUMN_NAME_MAP`` used for column renaming.
market.nasdaq.errors : ``NasdaqParseError`` raised on structural failures.
market.nasdaq.types : ``StockRecord`` dataclass for raw row data.
market.etfcom.collectors : Reference ``_camel_to_snake`` / ``_parse_response``.
"""

from __future__ import annotations

import math
import re
from typing import Any

import pandas as pd

from market.nasdaq.constants import COLUMN_NAME_MAP
from market.nasdaq.errors import NasdaqParseError
from utils_core.logging import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_CAMEL_TO_SNAKE_RE: re.Pattern[str] = re.compile(r"(?<=[a-z0-9])(?=[A-Z])")
"""Regex that inserts an underscore before each uppercase letter preceded by
a lowercase letter or digit.  Used by ``_camel_to_snake``."""

_MISSING_VALUES: frozenset[str] = frozenset({"", "N/A", "NA", "n/a"})
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


# ---------------------------------------------------------------------------
# Column name conversion
# ---------------------------------------------------------------------------


def _camel_to_snake(name: str) -> str:
    """Convert a camelCase or concatenated string to snake_case.

    Inserts underscores before each uppercase letter that is preceded by a
    lowercase letter or digit, then lowercases the entire result.

    Parameters
    ----------
    name : str
        camelCase string to convert.

    Returns
    -------
    str
        The snake_case equivalent.

    Examples
    --------
    >>> _camel_to_snake("marketCap")
    'market_cap'
    >>> _camel_to_snake("pctchange")
    'pctchange'
    >>> _camel_to_snake("symbol")
    'symbol'
    """
    return _CAMEL_TO_SNAKE_RE.sub("_", name).lower()


# ---------------------------------------------------------------------------
# Cleaning functions
# ---------------------------------------------------------------------------


def clean_price(value: str) -> float | None:
    """Convert a price string to a float.

    Strips leading ``$`` signs and commas before conversion.

    Parameters
    ----------
    value : str
        Price string such as ``"$1,234.56"`` or ``"-1.95"``.

    Returns
    -------
    float | None
        The numeric price, or ``None`` if the value is missing or
        cannot be parsed.

    Examples
    --------
    >>> clean_price("$1,234.56")
    1234.56
    >>> clean_price("-1.95")
    -1.95
    >>> clean_price("")
    >>> clean_price("N/A")
    """
    if _is_missing(value):
        return None

    try:
        cleaned = value.replace("$", "").replace(",", "").strip()
        if not cleaned:
            return None
        result = float(cleaned)
        if not math.isfinite(result):
            logger.warning(
                "Failed to parse price value",
                raw_value=value,
            )
            return None
        return result
    except (ValueError, TypeError):
        logger.warning(
            "Failed to parse price value",
            raw_value=value,
        )
        return None


def clean_percentage(value: str) -> float | None:
    """Convert a percentage string to a float.

    Strips trailing ``%`` signs before conversion.  The returned value
    is the raw percentage number (e.g. ``-0.849``), **not** divided by 100.

    Parameters
    ----------
    value : str
        Percentage string such as ``"-0.849%"`` or ``"1.23%"``.

    Returns
    -------
    float | None
        The numeric percentage, or ``None`` if the value is missing or
        cannot be parsed.

    Examples
    --------
    >>> clean_percentage("-0.849%")
    -0.849
    >>> clean_percentage("1.23%")
    1.23
    >>> clean_percentage("")
    >>> clean_percentage("N/A")
    """
    if _is_missing(value):
        return None

    try:
        cleaned = value.replace("%", "").replace(",", "").strip()
        if not cleaned:
            return None
        result = float(cleaned)
        if not math.isfinite(result):
            logger.warning(
                "Failed to parse percentage value",
                raw_value=value,
            )
            return None
        return result
    except (ValueError, TypeError):
        logger.warning(
            "Failed to parse percentage value",
            raw_value=value,
        )
        return None


def clean_market_cap(value: str) -> int | None:
    """Convert a market capitalisation string to an integer.

    Strips commas and leading ``$`` signs.  The NASDAQ API typically
    returns market cap as a comma-separated integer string
    (e.g. ``"3,435,123,456,789"``).

    Parameters
    ----------
    value : str
        Market cap string such as ``"3,435,123,456,789"``.

    Returns
    -------
    int | None
        The numeric market cap, or ``None`` if the value is missing or
        cannot be parsed.

    Examples
    --------
    >>> clean_market_cap("3,435,123,456,789")
    3435123456789
    >>> clean_market_cap("")
    >>> clean_market_cap("N/A")
    """
    if _is_missing(value):
        return None

    try:
        cleaned = value.replace("$", "").replace(",", "").strip()
        if not cleaned:
            return None
        # Handle floating point market cap values (e.g. "3435123456789.0")
        result = float(cleaned)
        if not math.isfinite(result):
            logger.warning(
                "Failed to parse market cap value",
                raw_value=value,
            )
            return None
        return int(result)
    except (ValueError, TypeError, OverflowError):
        logger.warning(
            "Failed to parse market cap value",
            raw_value=value,
        )
        return None


def clean_volume(value: str) -> int | None:
    """Convert a trading volume string to an integer.

    Strips commas from the formatted number string.

    Parameters
    ----------
    value : str
        Volume string such as ``"48,123,456"``.

    Returns
    -------
    int | None
        The numeric volume, or ``None`` if the value is missing or
        cannot be parsed.

    Examples
    --------
    >>> clean_volume("48,123,456")
    48123456
    >>> clean_volume("")
    >>> clean_volume("N/A")
    """
    if _is_missing(value):
        return None

    try:
        cleaned = value.replace(",", "").strip()
        if not cleaned:
            return None
        result = float(cleaned)
        if not math.isfinite(result):
            logger.warning(
                "Failed to parse volume value",
                raw_value=value,
            )
            return None
        return int(result)
    except (ValueError, TypeError, OverflowError):
        logger.warning(
            "Failed to parse volume value",
            raw_value=value,
        )
        return None


def clean_ipo_year(value: str) -> int | None:
    """Convert an IPO year string to an integer.

    Parameters
    ----------
    value : str
        Year string such as ``"1980"``.

    Returns
    -------
    int | None
        The numeric year, or ``None`` if the value is missing or
        cannot be parsed.

    Examples
    --------
    >>> clean_ipo_year("1980")
    1980
    >>> clean_ipo_year("")
    >>> clean_ipo_year("N/A")
    """
    if _is_missing(value):
        return None

    try:
        cleaned = value.strip()
        if not cleaned:
            return None
        return int(cleaned)
    except (ValueError, TypeError):
        logger.warning(
            "Failed to parse IPO year value",
            raw_value=value,
        )
        return None


# ---------------------------------------------------------------------------
# Response parser
# ---------------------------------------------------------------------------


def parse_screener_response(response: dict[str, Any]) -> pd.DataFrame:
    """Parse a NASDAQ Screener API JSON response into a cleaned DataFrame.

    Extracts row data from ``response["data"]["table"]["rows"]``, renames
    columns from API keys to snake_case using ``COLUMN_NAME_MAP``, and
    applies numeric cleaning to price, percentage, market cap, volume,
    and IPO year columns.

    Parameters
    ----------
    response : dict[str, Any]
        The raw JSON response from the NASDAQ Screener API.  Expected
        structure::

            {
                "data": {
                    "table": {
                        "rows": [{"symbol": "AAPL", ...}, ...]
                    }
                }
            }

    Returns
    -------
    pd.DataFrame
        A DataFrame with snake_case column names and cleaned numeric
        values.  Columns: ``symbol``, ``name``, ``last_sale``,
        ``net_change``, ``pct_change``, ``market_cap``, ``country``,
        ``ipo_year``, ``volume``, ``sector``, ``industry``, ``url``.

    Raises
    ------
    NasdaqParseError
        If the JSON structure does not match the expected schema
        (missing ``data``, ``table``, or ``rows`` keys, or ``rows``
        is not a list).

    Examples
    --------
    >>> resp = {
    ...     "data": {
    ...         "table": {
    ...             "rows": [
    ...                 {
    ...                     "symbol": "AAPL",
    ...                     "name": "Apple Inc.",
    ...                     "lastsale": "$227.63",
    ...                     "netchange": "-1.95",
    ...                     "pctchange": "-0.849%",
    ...                     "marketCap": "3,435,123,456,789",
    ...                     "country": "United States",
    ...                     "ipoyear": "1980",
    ...                     "volume": "48,123,456",
    ...                     "sector": "Technology",
    ...                     "industry": "Computer Manufacturing",
    ...                     "url": "/market-activity/stocks/aapl",
    ...                 }
    ...             ]
    ...         }
    ...     }
    ... }
    >>> df = parse_screener_response(resp)
    >>> df["symbol"].iloc[0]
    'AAPL'
    >>> df["last_sale"].iloc[0]
    227.63
    """
    logger.debug("Parsing screener response")

    # --- Validate structure ---
    data = response.get("data")
    if not isinstance(data, dict):
        raise NasdaqParseError(
            "Missing or invalid 'data' key in response",
            raw_data=str(response)[:500],
            field="data",
        )

    table = data.get("table")
    if not isinstance(table, dict):
        raise NasdaqParseError(
            "Missing or invalid 'data.table' key in response",
            raw_data=str(data)[:500],
            field="data.table",
        )

    rows = table.get("rows")
    if not isinstance(rows, list):
        raise NasdaqParseError(
            "Missing or invalid 'data.table.rows' key in response",
            raw_data=str(table)[:500],
            field="data.table.rows",
        )

    if not rows:
        logger.info("Screener response contains no rows")
        return pd.DataFrame(
            columns=pd.Index(list(COLUMN_NAME_MAP.values())),
        )

    logger.debug("Parsing screener rows", row_count=len(rows))

    # --- Build DataFrame ---
    df = pd.DataFrame(rows)

    # Rename columns using COLUMN_NAME_MAP
    rename_map: dict[str, str] = {}
    for col in df.columns:
        mapped = COLUMN_NAME_MAP.get(col)
        if mapped is not None:
            rename_map[col] = mapped
        else:
            # Fallback: use _camel_to_snake for unknown columns
            rename_map[col] = _camel_to_snake(col)

    df = df.rename(columns=rename_map)

    # --- Apply numeric cleaning ---
    if "last_sale" in df.columns:
        df["last_sale"] = df["last_sale"].apply(
            lambda v: clean_price(str(v)) if pd.notna(v) else None,
        )

    if "net_change" in df.columns:
        df["net_change"] = df["net_change"].apply(
            lambda v: clean_price(str(v)) if pd.notna(v) else None,
        )

    if "pct_change" in df.columns:
        df["pct_change"] = df["pct_change"].apply(
            lambda v: clean_percentage(str(v)) if pd.notna(v) else None,
        )

    if "market_cap" in df.columns:
        df["market_cap"] = df["market_cap"].apply(
            lambda v: clean_market_cap(str(v)) if pd.notna(v) else None,
        )

    if "volume" in df.columns:
        df["volume"] = df["volume"].apply(
            lambda v: clean_volume(str(v)) if pd.notna(v) else None,
        )

    if "ipo_year" in df.columns:
        df["ipo_year"] = df["ipo_year"].apply(
            lambda v: clean_ipo_year(str(v)) if pd.notna(v) else None,
        )

    logger.info(
        "Screener response parsed",
        row_count=len(df),
        columns=list(df.columns),
    )

    return df


# ---------------------------------------------------------------------------
# Module exports
# ---------------------------------------------------------------------------

__all__ = [
    "clean_ipo_year",
    "clean_market_cap",
    "clean_percentage",
    "clean_price",
    "clean_volume",
    "parse_screener_response",
]

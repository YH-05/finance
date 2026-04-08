#!/usr/bin/env python3
"""NSE 全上場銘柄 + インデックス構成 + Shareholding Pattern → SQLite 格納スクリプト.

NSE（National Stock Exchange of India）の全上場銘柄情報、インデックス構成銘柄、
Shareholding Pattern を取得し、SQLite データベースに格納するスタンドアロンスクリプト。

Output:
    data/sqlite/nse_index.db

Tables:
    - stocks: 全上場銘柄の基本情報（EQUITY_L.csv + equity-stockIndices 詳細）
    - index_members: インデックス構成銘柄
    - shareholdings: 株主構成パターン（四半期ごと）

Processing Phases:
    Phase 1: EQUITY_L.csv から銘柄マスタを取得・INSERT
    Phase 2: allIndices → equity-stockIndices でインデックス構成と詳細情報を取得
    Phase 3: corporate-share-holdings-master で全銘柄の株主構成を取得

Examples
--------
Basic usage::

    $ uv run python scripts/nse_index_shareholding.py

Notes
-----
- スタンドアロンスクリプト: src/market/nse/ パッケージは使用しない
- httpx + sqlite3 + csv + logging のみ使用
- 冪等: INSERT OR REPLACE で上書き
- エラー耐性: 1銘柄の失敗で全体が止まらない
"""

from __future__ import annotations

import csv
import io
import logging
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DB_PATH = "data/cache/nse/nse_index.db"

HEADERS = {
    "user-agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "accept": "application/json",
    "accept-language": "en-US,en;q=0.9",
}

EQUITY_CSV_URL = "https://nsearchives.nseindia.com/content/equities/EQUITY_L.csv"
API_BASE = "https://www.nseindia.com/api"

# Bond / non-equity index prefixes to skip
SKIP_INDEX_PREFIXES = (
    "BHARATBOND",
    "NIFTY GS",
)

INDEX_DELAY_SEC = 0.3
SHAREHOLDING_DELAY_SEC = 0.5

HTTPX_TIMEOUT = 30.0

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
# SQL DDL
# ---------------------------------------------------------------------------

CREATE_STOCKS_TABLE = """\
CREATE TABLE IF NOT EXISTS stocks (
    symbol          TEXT PRIMARY KEY,
    company_name    TEXT NOT NULL,
    isin            TEXT,
    series          TEXT DEFAULT 'EQ',
    listing_date    TEXT,
    face_value      REAL,
    industry        TEXT,
    sector          TEXT,
    basic_industry  TEXT,
    macro           TEXT,
    is_fno          INTEGER,
    last_price      REAL,
    previous_close  REAL,
    year_high       REAL,
    year_low        REAL,
    ffmc            REAL,
    pct_change_30d  REAL,
    pct_change_365d REAL,
    fetched_at      TEXT NOT NULL
)
"""

CREATE_SHAREHOLDINGS_TABLE = """\
CREATE TABLE IF NOT EXISTS shareholdings (
    symbol              TEXT NOT NULL,
    as_on_date          TEXT NOT NULL,
    promoter_pct        REAL,
    public_pct          REAL,
    employee_trust_pct  REAL DEFAULT 0,
    submission_date     TEXT,
    broadcast_date      TEXT,
    xbrl_url            TEXT,
    fetched_at          TEXT NOT NULL,
    PRIMARY KEY (symbol, as_on_date),
    FOREIGN KEY (symbol) REFERENCES stocks(symbol)
)
"""

CREATE_INDEX_MEMBERS_TABLE = """\
CREATE TABLE IF NOT EXISTS index_members (
    index_name  TEXT NOT NULL,
    symbol      TEXT NOT NULL,
    priority    INTEGER,
    fetched_at  TEXT NOT NULL,
    PRIMARY KEY (index_name, symbol),
    FOREIGN KEY (symbol) REFERENCES stocks(symbol)
)
"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _now_iso() -> str:
    """Return current UTC timestamp in ISO 8601 format."""
    return datetime.now(timezone.utc).isoformat()


def _safe_float(value: Any) -> float | None:
    """Convert value to float, returning None on failure."""
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def _safe_int(value: Any) -> int | None:
    """Convert value to int, returning None on failure."""
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def _create_session() -> httpx.Client:
    """Create an httpx client with cookie persistence for NSE.

    NSE requires an initial page visit to set session cookies
    before API endpoints will respond.

    Returns
    -------
    httpx.Client
        Configured HTTP client with session cookies.
    """
    client = httpx.Client(
        headers=HEADERS,
        timeout=HTTPX_TIMEOUT,
        follow_redirects=True,
    )
    # Warm up session cookies by visiting the main page
    logger.info("Warming up NSE session cookies...")
    resp = client.get("https://www.nseindia.com")
    logger.info("Session cookie response: %d", resp.status_code)
    return client


# ---------------------------------------------------------------------------
# Database setup
# ---------------------------------------------------------------------------


def _init_db(db_path: str) -> sqlite3.Connection:
    """Initialise SQLite database and create tables.

    Parameters
    ----------
    db_path : str
        Path to the SQLite database file.

    Returns
    -------
    sqlite3.Connection
        Database connection.
    """
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path, timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=30000")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute(CREATE_STOCKS_TABLE)
    conn.execute(CREATE_SHAREHOLDINGS_TABLE)
    conn.execute(CREATE_INDEX_MEMBERS_TABLE)
    conn.commit()
    logger.info("Database initialised: %s", db_path)
    return conn


# ---------------------------------------------------------------------------
# Phase 1: Stock Master (EQUITY_L.csv)
# ---------------------------------------------------------------------------


def fetch_equity_csv(client: httpx.Client) -> list[dict[str, str]]:
    """Fetch and parse EQUITY_L.csv from NSE archives.

    Parameters
    ----------
    client : httpx.Client
        HTTP client with session cookies.

    Returns
    -------
    list[dict[str, str]]
        Parsed rows with stripped header keys.
    """
    logger.info("Phase 1: Fetching EQUITY_L.csv...")
    resp = client.get(EQUITY_CSV_URL)
    resp.raise_for_status()

    text = resp.text
    reader = csv.DictReader(io.StringIO(text))
    rows: list[dict[str, str]] = []
    for row in reader:
        # Strip whitespace from keys (CSV headers have leading spaces)
        stripped = {k.strip(): v.strip() if v else "" for k, v in row.items()}
        rows.append(stripped)
    logger.info("Phase 1: Parsed %d stocks from EQUITY_L.csv", len(rows))
    return rows


def insert_stocks_from_csv(
    conn: sqlite3.Connection,
    rows: list[dict[str, str]],
) -> int:
    """Insert stock master data from EQUITY_L.csv.

    Parameters
    ----------
    conn : sqlite3.Connection
        Database connection.
    rows : list[dict[str, str]]
        Parsed CSV rows.

    Returns
    -------
    int
        Number of rows inserted.
    """
    now = _now_iso()
    insert_sql = """\
    INSERT OR REPLACE INTO stocks
        (symbol, company_name, isin, series, listing_date, face_value, fetched_at)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """
    count = 0
    for row in rows:
        symbol = row.get("SYMBOL", "")
        if not symbol:
            continue
        conn.execute(
            insert_sql,
            (
                symbol,
                row.get("NAME OF COMPANY", ""),
                row.get("ISIN NUMBER", ""),
                row.get("SERIES", "EQ"),
                row.get("DATE OF LISTING", ""),
                _safe_float(row.get("FACE VALUE")),
                now,
            ),
        )
        count += 1
    conn.commit()
    logger.info("Phase 1: Inserted %d stocks into DB", count)
    return count


# ---------------------------------------------------------------------------
# Phase 2: Index Members (allIndices + equity-stockIndices)
# ---------------------------------------------------------------------------


def fetch_all_indices(client: httpx.Client) -> list[str]:
    """Fetch all index names from NSE /api/allIndices.

    Parameters
    ----------
    client : httpx.Client
        HTTP client with session cookies.

    Returns
    -------
    list[str]
        List of index symbol names.
    """
    logger.info("Phase 2: Fetching all indices...")
    url = f"{API_BASE}/allIndices"
    resp = client.get(url)
    resp.raise_for_status()
    data = resp.json()

    indices: list[str] = []
    for item in data.get("data", []):
        name = item.get("indexSymbol", "")
        if not name:
            continue
        # Skip bond / non-equity indices
        if any(name.startswith(prefix) for prefix in SKIP_INDEX_PREFIXES):
            continue
        indices.append(name)

    logger.info("Phase 2: Found %d equity indices (after filtering)", len(indices))
    return indices


def fetch_index_constituents(
    client: httpx.Client,
    index_name: str,
) -> list[dict[str, Any]]:
    """Fetch constituents for a single index.

    Parameters
    ----------
    client : httpx.Client
        HTTP client with session cookies.
    index_name : str
        Index symbol name (e.g., "NIFTY 50").

    Returns
    -------
    list[dict[str, Any]]
        Constituent data items.
    """
    url = f"{API_BASE}/equity-stockIndices"
    resp = client.get(url, params={"index": index_name})
    resp.raise_for_status()
    data = resp.json()
    return data.get("data", [])


def process_indices(
    client: httpx.Client,
    conn: sqlite3.Connection,
    indices: list[str],
) -> tuple[int, int, list[str]]:
    """Process all indices: insert members and update stock details.

    Parameters
    ----------
    client : httpx.Client
        HTTP client with session cookies.
    conn : sqlite3.Connection
        Database connection.
    indices : list[str]
        List of index names.

    Returns
    -------
    tuple[int, int, list[str]]
        (total_member_rows, total_stock_updates, failed_indices)
    """
    now = _now_iso()
    member_insert_sql = """\
    INSERT OR REPLACE INTO index_members
        (index_name, symbol, priority, fetched_at)
    VALUES (?, ?, ?, ?)
    """
    stock_update_sql = """\
    UPDATE stocks SET
        industry = COALESCE(?, industry),
        is_fno = COALESCE(?, is_fno),
        last_price = ?,
        previous_close = ?,
        year_high = ?,
        year_low = ?,
        ffmc = ?,
        pct_change_30d = ?,
        pct_change_365d = ?,
        fetched_at = ?
    WHERE symbol = ?
    """

    total_members = 0
    total_updates = 0
    failed: list[str] = []

    for i, idx_name in enumerate(indices, 1):
        try:
            constituents = fetch_index_constituents(client, idx_name)
            if not constituents:
                logger.debug(
                    "Phase 2: [%d/%d] %s — empty, skipped",
                    i,
                    len(indices),
                    idx_name,
                )
                time.sleep(INDEX_DELAY_SEC)
                continue

            for item in constituents:
                symbol = item.get("symbol", "")
                if not symbol:
                    continue
                # Skip the index-summary row (e.g. "NIFTY 50" itself)
                if symbol == idx_name:
                    continue
                meta = item.get("meta", {}) or {}

                # Ensure symbol exists in stocks (may be missing from CSV)
                conn.execute(
                    """INSERT OR IGNORE INTO stocks (symbol, company_name, fetched_at)
                    VALUES (?, ?, ?)""",
                    (symbol, meta.get("companyName", ""), now),
                )

                # Insert index member
                conn.execute(
                    member_insert_sql,
                    (
                        idx_name,
                        symbol,
                        _safe_int(item.get("priority")),
                        now,
                    ),
                )
                total_members += 1

                # Update stock details
                conn.execute(
                    stock_update_sql,
                    (
                        meta.get("industry"),
                        1 if meta.get("isFNOSec") else 0,
                        _safe_float(item.get("lastPrice")),
                        _safe_float(item.get("previousClose")),
                        _safe_float(item.get("yearHigh")),
                        _safe_float(item.get("yearLow")),
                        _safe_float(item.get("ffmc")),
                        _safe_float(item.get("perChange30d")),
                        _safe_float(item.get("perChange365d")),
                        now,
                        symbol,
                    ),
                )
                total_updates += 1

            conn.commit()

            if i % 10 == 0 or i == len(indices):
                logger.info(
                    "Phase 2: [%d/%d] indices processed, %d members, %d stock updates",
                    i,
                    len(indices),
                    total_members,
                    total_updates,
                )
        except Exception:
            logger.exception("Phase 2: Failed to process index '%s'", idx_name)
            failed.append(idx_name)

        time.sleep(INDEX_DELAY_SEC)

    logger.info(
        "Phase 2: Completed — %d members, %d stock updates, %d failed",
        total_members,
        total_updates,
        len(failed),
    )
    return total_members, total_updates, failed


# ---------------------------------------------------------------------------
# Phase 3: Shareholding Pattern
# ---------------------------------------------------------------------------


def fetch_shareholding(
    client: httpx.Client,
    symbol: str,
) -> list[dict[str, Any]]:
    """Fetch shareholding pattern for a single symbol.

    Parameters
    ----------
    client : httpx.Client
        HTTP client with session cookies.
    symbol : str
        Stock symbol.

    Returns
    -------
    list[dict[str, Any]]
        Shareholding records (may contain multiple quarters).
    """
    url = f"{API_BASE}/corporate-share-holdings-master"
    resp = client.get(
        url,
        params={"index": "equities", "symbol": symbol},
    )
    resp.raise_for_status()
    data = resp.json()
    if isinstance(data, list):
        return data
    return []


def process_shareholdings(
    client: httpx.Client,
    conn: sqlite3.Connection,
) -> tuple[int, list[str]]:
    """Fetch and insert shareholding data for all stocks.

    Parameters
    ----------
    client : httpx.Client
        HTTP client with session cookies.
    conn : sqlite3.Connection
        Database connection.

    Returns
    -------
    tuple[int, list[str]]
        (total_rows_inserted, failed_symbols)
    """
    cursor = conn.execute("SELECT symbol FROM stocks ORDER BY symbol")
    symbols = [row[0] for row in cursor.fetchall()]
    logger.info("Phase 3: Processing shareholdings for %d symbols...", len(symbols))

    insert_sql = """\
    INSERT OR REPLACE INTO shareholdings
        (symbol, as_on_date, promoter_pct, public_pct,
         employee_trust_pct, submission_date, broadcast_date,
         xbrl_url, fetched_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    now = _now_iso()
    total_rows = 0
    failed: list[str] = []

    for i, symbol in enumerate(symbols, 1):
        try:
            records = fetch_shareholding(client, symbol)
            for rec in records:
                if not rec.get("date"):
                    continue
                conn.execute(
                    insert_sql,
                    (
                        rec.get("symbol", symbol),
                        rec.get("date", ""),
                        _safe_float(rec.get("pr_and_prgrp")),
                        _safe_float(rec.get("public_val")),
                        _safe_float(rec.get("employeeTrusts")),
                        rec.get("submissionDate"),
                        rec.get("broadcastDate"),
                        rec.get("xbrl"),
                        now,
                    ),
                )
                total_rows += 1

            if i % 50 == 0:
                conn.commit()
                logger.info(
                    "Phase 3: Processing %d/%d shareholdings... "
                    "(%d rows inserted so far)",
                    i,
                    len(symbols),
                    total_rows,
                )
        except Exception:
            logger.exception("Phase 3: Failed to fetch shareholding for '%s'", symbol)
            failed.append(symbol)

        time.sleep(SHAREHOLDING_DELAY_SEC)

    conn.commit()
    logger.info(
        "Phase 3: Completed — %d rows inserted, %d failed",
        total_rows,
        len(failed),
    )
    return total_rows, failed


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    """Run the full NSE data collection pipeline."""
    start = time.monotonic()
    logger.info("=" * 60)
    logger.info("NSE Index + Shareholding Pipeline — Start")
    logger.info("=" * 60)

    conn = _init_db(DB_PATH)
    client = _create_session()

    try:
        # Phase 1: Stock master
        csv_rows = fetch_equity_csv(client)
        stock_count = insert_stocks_from_csv(conn, csv_rows)

        # Phase 2: Index members + stock detail updates
        indices = fetch_all_indices(client)
        member_count, update_count, failed_indices = process_indices(
            client, conn, indices
        )

        # Phase 3: Shareholding patterns
        sh_rows, failed_sh = process_shareholdings(client, conn)

    finally:
        client.close()
        conn.close()

    elapsed = time.monotonic() - start
    minutes = int(elapsed // 60)
    seconds = elapsed % 60

    # Final summary
    logger.info("=" * 60)
    logger.info("NSE Index + Shareholding Pipeline — Summary")
    logger.info("=" * 60)
    logger.info("Stocks inserted:         %d", stock_count)
    logger.info("Indices processed:       %d", len(indices))
    logger.info("Index member rows:       %d", member_count)
    logger.info("Stock detail updates:    %d", update_count)
    logger.info("Shareholding rows:       %d", sh_rows)
    logger.info("Failed indices:          %d", len(failed_indices))
    logger.info("Failed shareholdings:    %d", len(failed_sh))
    logger.info("Elapsed time:            %dm %.1fs", minutes, seconds)
    logger.info("Database:                %s", DB_PATH)

    if failed_indices:
        logger.warning("Failed indices: %s", failed_indices)
    if failed_sh:
        logger.warning(
            "Failed shareholding symbols (%d): %s",
            len(failed_sh),
            failed_sh[:20],
        )


if __name__ == "__main__":
    main()

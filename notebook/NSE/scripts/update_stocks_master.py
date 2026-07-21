"""EQUITY_L.csv から stocks テーブルの上場銘柄マスタを UPSERT 更新する.

`INSERT OR REPLACE` は指定しなかった列を NULL で上書きしてしまうため、
`ON CONFLICT(symbol) DO UPDATE SET` で symbol/company_name/isin/series/
listing_date/face_value/fetched_at のみを更新する。industry/sector/
last_price 等、EQUITY_L.csv 由来ではない列は既存値を保持する。

入力:
- NSE Archives の EQUITY_L.csv
  (``StockListCollector.fetch_stock_list()`` でライブ取得)

出力:
- --db-path で指定する SQLite DB の stocks テーブル（新規銘柄は INSERT、
  既存銘柄は対象列のみ UPDATE）
"""

from __future__ import annotations

import argparse
import logging
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from market.nse import NseSession, StockListCollector

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
log = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DB_PATH = ROOT / "notebook/NSE/data/cache/nse/nse_index.db"

UPSERT_SQL = """
INSERT INTO stocks (symbol, company_name, isin, series, listing_date, face_value, fetched_at)
VALUES (?, ?, ?, ?, ?, ?, ?)
ON CONFLICT(symbol) DO UPDATE SET
    company_name = excluded.company_name,
    isin         = excluded.isin,
    series       = excluded.series,
    listing_date = excluded.listing_date,
    face_value   = excluded.face_value,
    fetched_at   = excluded.fetched_at
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="EQUITY_L.csv から stocks テーブルを UPSERT 更新する"
        "（industry/sector/last_price 等の他列は保持）"
    )
    parser.add_argument(
        "--db-path",
        type=Path,
        default=DEFAULT_DB_PATH,
        help=f"更新対象 SQLite DB ファイルパス（デフォルト: {DEFAULT_DB_PATH}）",
    )
    return parser.parse_args()


def to_float(value: str | float | None) -> float | None:
    try:
        return float(value) if value not in (None, "") else None
    except (TypeError, ValueError):
        return None


def build_rows(stocks_df: pd.DataFrame) -> list[tuple[object, ...]]:
    fetched_at = datetime.now(UTC).isoformat()
    rows: list[tuple[object, ...]] = []
    for _, row in stocks_df.iterrows():
        symbol = row.get("symbol")
        if not symbol:
            continue
        rows.append(
            (
                symbol,
                row.get("company_name", ""),
                row.get("isin") or None,
                row.get("series") or "EQ",
                row.get("date_of_listing") or None,
                to_float(row.get("face_value")),
                fetched_at,
            )
        )
    return rows


def main() -> None:
    args = parse_args()

    log.info("Fetching NSE stock list (EQUITY_L.csv)")
    with NseSession() as session:
        collector = StockListCollector(session=session)
        stocks_df = collector.fetch_stock_list()
    log.info(f"Fetched {len(stocks_df)} stocks from EQUITY_L.csv")

    rows = build_rows(stocks_df)

    conn = sqlite3.connect(args.db_path)
    try:
        before = conn.execute("SELECT COUNT(*) FROM stocks").fetchone()[0]
        conn.executemany(UPSERT_SQL, rows)
        conn.commit()
        after = conn.execute("SELECT COUNT(*) FROM stocks").fetchone()[0]
    finally:
        conn.close()

    log.info(f"Upserted {len(rows)} rows into stocks table ({args.db_path})")
    log.info(f"stocks count: {before} -> {after} ({after - before:+d})")


if __name__ == "__main__":
    main()

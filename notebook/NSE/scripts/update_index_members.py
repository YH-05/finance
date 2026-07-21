"""index_members テーブルを NSE Archives 静的CSVから最新化する.

nse_full_download.ipynb Phase 2 は動的API (`fetch_index`) から全80+
インデックスをまとめて更新するが、動的APIはレートリミット・cookie失効で
不安定なため、増分更新では静的アーカイブCSV
(`IndicesCollector.fetch_index_constituents_archive`) から
NIFTY 50/100/200/500/TOTAL MKT の5インデックスのみを対象に更新する。

INSERT OR REPLACE ではなく index_name 単位の DELETE→INSERT を採用する理由:
    アーカイブCSVは「現在の構成銘柄」のスナップショットであり、除外された
    銘柄の行は含まれない。INSERT OR REPLACE では除外銘柄の古い行が残留する
    ため、対象 index_name の既存行を全削除してから再挿入する
    （nse_full_download.ipynb Phase2 の設計思想を踏襲）。

入力:
    NSE Archives 静的CSV（`fetch_index_constituents_archive` 経由）

出力:
    --db-path で指定する SQLite DB の index_members テーブル
    （対象5インデックスのみ全delete→re-insert、他インデックスは変更しない）
"""

from __future__ import annotations

import argparse
import logging
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from market.nse import IndicesCollector, NseSession

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
log = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DB_PATH = ROOT / "notebook/NSE/data/cache/nse/nse_index.db"

TARGET_INDICES: list[str] = [
    "NIFTY 50",
    "NIFTY 100",
    "NIFTY 200",
    "NIFTY 500",
    "NIFTY TOTAL MKT",
]

DELETE_SQL = "DELETE FROM index_members WHERE index_name = ?"
INSERT_SQL = """
INSERT INTO index_members (index_name, symbol, priority, fetched_at)
VALUES (?, ?, ?, ?)
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="NSE Archives 静的CSVから index_members テーブルを最新化する"
        f"（対象: {', '.join(TARGET_INDICES)}）"
    )
    parser.add_argument(
        "--db-path",
        type=Path,
        default=DEFAULT_DB_PATH,
        help=f"更新対象 SQLite DB ファイルパス（デフォルト: {DEFAULT_DB_PATH}）",
    )
    return parser.parse_args()


def build_rows(
    symbols: list[str], index_name: str, fetched_at: str
) -> list[tuple[object, ...]]:
    return [(index_name, symbol, None, fetched_at) for symbol in symbols]


def main() -> None:
    args = parse_args()

    conn = sqlite3.connect(args.db_path)
    try:
        with NseSession() as session:
            collector = IndicesCollector(session=session)

            for index_name in TARGET_INDICES:
                before = conn.execute(
                    "SELECT COUNT(*) FROM index_members WHERE index_name = ?",
                    (index_name,),
                ).fetchone()[0]

                log.info(f"Fetching index constituents archive: {index_name}")
                df = collector.fetch_index_constituents_archive(index_name)
                symbols = [s for s in df["symbol"].tolist() if s]
                fetched_at = datetime.now(UTC).isoformat()
                rows = build_rows(symbols, index_name, fetched_at)

                conn.execute(DELETE_SQL, (index_name,))
                conn.executemany(INSERT_SQL, rows)
                conn.commit()

                after = conn.execute(
                    "SELECT COUNT(*) FROM index_members WHERE index_name = ?",
                    (index_name,),
                ).fetchone()[0]

                log.info(
                    f"{index_name}: {before} -> {after} members ({after - before:+d})"
                )
    finally:
        conn.close()

    log.info(f"index_members updated: {args.db_path}")


if __name__ == "__main__":
    main()

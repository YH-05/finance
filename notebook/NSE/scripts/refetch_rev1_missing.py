"""rev1 にあるが nifty750_universe.csv に無い銘柄を NSE から再取得.

act-2026-05-12-001: rev1 (632 銘柄) と現 universe (800 銘柄) の差分 55 銘柄のうち、
NSE symbol が解決可能な 38 銘柄について Phase 3 (shareholdings) +
Phase 4 (XBRL detail) を再取得する。

入力:
    notebook/NSE/data/exports/nse/rev1_missing_from_universe.csv
        rev1 - universe の差分。symbol_resolved 列が空でない行のみ取得対象。

出力:
    notebook/NSE/data/exports/nse/refetch_rev1_log.json
        各銘柄の試行結果 (phase3 / phase4 の OK/FAIL とエラー詳細)
    SQLite: shareholdings / shareholding_detail テーブルに UPSERT
"""

from __future__ import annotations

import json
import logging
import sqlite3
import time
from pathlib import Path

import pandas as pd

from market.nse.collectors.share_holding import ShareholdingCollector
from market.nse.session import NseSession

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
log = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[3]
DB_PATH = ROOT / "notebook/NSE/data/cache/nse/nse_index.db"
EXPORT_DIR = ROOT / "notebook/NSE/data/exports/nse"
INPUT_CSV = EXPORT_DIR / "rev1_missing_from_universe.csv"
LOG_FILE = EXPORT_DIR / "refetch_rev1_log.json"

RATE_LIMIT_SEC = 0.5


def fetch_phase3(
    collector: ShareholdingCollector, symbol: str
) -> tuple[bool, str, list]:
    try:
        holdings = collector.fetch_shareholding(symbol)
        return True, f"fetched {len(holdings)} holdings", holdings
    except Exception as e:
        return False, f"{type(e).__name__}: {e}", []


def fetch_phase4(
    collector: ShareholdingCollector, xbrl_url: str
) -> tuple[bool, str, object]:
    try:
        result = collector.fetch_xbrl_detail(xbrl_url)
        return True, f"parsed {len(result.rows)} rows", result
    except Exception as e:
        return False, f"{type(e).__name__}: {e}", None


def main() -> None:
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)

    missing_df = pd.read_csv(INPUT_CSV)
    targets = missing_df[missing_df["resolution_status"] == "resolvable"].copy()
    log.info(f"Target symbols: {len(targets)} (resolvable from rev1_missing CSV)")

    log_entries: list[dict] = []

    with NseSession() as session:
        collector = ShareholdingCollector(session=session)

        for _, target in targets.iterrows():
            symbol = target["symbol_resolved"]
            isin = target["isin"]
            log.info(f"--- {symbol} ({isin}) ---")
            entry: dict = {
                "symbol": symbol,
                "isin": isin,
                "rev1_category": target["rev1_category"],
            }

            ok3, msg3, holdings = fetch_phase3(collector, symbol)
            entry["phase3"] = {"ok": ok3, "msg": msg3, "count": len(holdings)}
            log.info(f"  Phase 3: {'OK' if ok3 else 'FAIL'} — {msg3}")

            if not ok3 or not holdings:
                entry["phase4"] = {
                    "ok": False,
                    "msg": "skipped (Phase 3 failed or empty)",
                }
                log_entries.append(entry)
                time.sleep(RATE_LIMIT_SEC)
                continue

            # Phase 4: latest quarter only (saves rate limit)
            latest = holdings[0]
            xbrl_url = getattr(latest, "xbrl_url", "") or ""
            if not xbrl_url:
                entry["phase4"] = {"ok": False, "msg": "no xbrl_url in latest holding"}
                log_entries.append(entry)
                time.sleep(RATE_LIMIT_SEC)
                continue

            ok4, msg4, result = fetch_phase4(collector, xbrl_url)
            entry["phase4"] = {
                "ok": ok4,
                "msg": msg4,
                "row_count": len(result.rows) if ok4 and result else 0,
                "as_on_date": result.as_on_date if ok4 and result else None,
            }
            log.info(f"  Phase 4: {'OK' if ok4 else 'FAIL'} — {msg4}")

            log_entries.append(entry)
            time.sleep(RATE_LIMIT_SEC)

    LOG_FILE.write_text(
        json.dumps(log_entries, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    log.info(f"\nLog written: {LOG_FILE}")

    n_p3_ok = sum(1 for e in log_entries if e["phase3"]["ok"])
    n_p4_ok = sum(
        1
        for e in log_entries
        if isinstance(e.get("phase4"), dict) and e["phase4"].get("ok")
    )
    log.info(
        f"Summary: Phase 3 OK={n_p3_ok}/{len(log_entries)}, "
        f"Phase 4 OK={n_p4_ok}/{len(log_entries)}"
    )


if __name__ == "__main__":
    main()

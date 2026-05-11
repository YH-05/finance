"""rev1 圏内・Phase 3/4 圏外 銘柄の再取得.

⚠️ HISTORICAL SCRIPT (2026-05-07): act-2026-05-07-003 の一回限りの救済処理。
全 13 銘柄 (360ONE + B カテゴリ 12 銘柄) の再取得は完了済み (refetch_log.json 参照)。
再実行は不要。手順記録として保存。

対応カテゴリ:
- C カテゴリ (1件): 360ONE — Phase 3 取得済み、Phase 4 (XBRL) のみ再実行
- B カテゴリ (12件): SANOFI/GUJGASLTD 等 — Phase 3 + Phase 4 を試行

出力:
- notebook/NSE/data/exports/nse/refetch_log.json
    各銘柄の試行結果 (success/error/error_msg)
- shareholdings.csv / shareholding_detail.csv に追記 (成功分のみ)
"""

from __future__ import annotations

import json
import logging
import sqlite3
import time
import traceback
from dataclasses import asdict
from pathlib import Path

import pandas as pd

from market.nse.collectors.share_holding import ShareholdingCollector
from market.nse.session import NseSession

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[3]
DB_PATH = ROOT / "notebook/NSE/data/cache/nse/nse_index.db"
EXPORT_DIR = ROOT / "notebook/NSE/data/exports/nse"
LOG_FILE = EXPORT_DIR / "refetch_log.json"

# C カテゴリ: 360ONE は Phase 4 のみ
C_SYMBOLS = ["360ONE"]

# B カテゴリ: 12 銘柄、Phase 3 + Phase 4
B_SYMBOLS = [
    "MAHLIFE",     # MAHINDRA LIFESPACE DEVELOPER (Owner)
    "FINOPB",      # FINO PAYMENTS BANK (Professional)
    "SANOFI",      # SANOFI INDIA (MNC)
    "BALMLAWRIE",  # BALMER LAWRIE & CO (State)
    "PGHH",        # PROCTER & GAMBLE HYGIENE (MNC)
    "GUJALKALI",   # GUJARAT ALKALIES & CHEMICALS (State)
    "PGHL",        # PROCTER & GAMBLE HEALTH (MNC)
    "TICL",        # TWAMEV CONSTRUCTION AND INFRA (Professional)
    "PSB",         # PUNJAB & SIND BANK (State)
    "UTKARSHBNK",  # UTKARSH SMALL FINANCE BANK (typo: abb)
    "GUJGASLTD",   # GUJARAT GAS (State)
    "KIOCL",       # KIOCL (State)
]


def fetch_phase3(collector: ShareholdingCollector, symbol: str) -> tuple[bool, str, list]:
    """Phase 3: shareholding pattern 取得."""
    try:
        holdings = collector.fetch_shareholding(symbol)
        return True, f"fetched {len(holdings)} holdings", holdings
    except Exception as e:
        return False, f"{type(e).__name__}: {e}", []


def fetch_phase4(collector: ShareholdingCollector, xbrl_url: str) -> tuple[bool, str, object]:
    """Phase 4: XBRL parse."""
    try:
        result = collector.fetch_xbrl_detail(xbrl_url)
        return True, f"parsed {len(result.rows)} rows", result
    except Exception as e:
        return False, f"{type(e).__name__}: {e}", None


def main() -> None:
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)

    log_entries: list[dict] = []

    # NseSession を共有 (Cookie ライフサイクル管理)
    with NseSession() as session:
        collector = ShareholdingCollector(session=session)

        # === C: 360ONE — Phase 4 のみ ===
        log.info("=" * 60)
        log.info("Category C: Phase 4 のみ再実行")
        log.info("=" * 60)

        conn = sqlite3.connect(DB_PATH)
        for sym in C_SYMBOLS:
            log.info(f"--- {sym} (C) ---")
            existing = pd.read_sql_query(
                "SELECT as_on_date, xbrl_url FROM shareholdings "
                "WHERE symbol = ? ORDER BY as_on_date DESC LIMIT 8",
                conn,
                params=(sym,),
            )
            log.info(f"  {sym}: shareholdings 上の最新 {len(existing)} 期分を試行")

            phase4_results = []
            for _, row in existing.iterrows():
                if not row["xbrl_url"] or pd.isna(row["xbrl_url"]):
                    phase4_results.append(
                        {
                            "as_on_date": row["as_on_date"],
                            "ok": False,
                            "msg": "xbrl_url is empty",
                        }
                    )
                    continue
                ok, msg, result = fetch_phase4(collector, row["xbrl_url"])
                phase4_results.append(
                    {
                        "as_on_date": row["as_on_date"],
                        "ok": ok,
                        "msg": msg,
                        "row_count": len(result.rows) if ok and result else 0,
                    }
                )
                log.info(f"    {row['as_on_date']}: {'OK' if ok else 'FAIL'} — {msg}")
                time.sleep(0.5)  # rate limit

            log_entries.append(
                {
                    "symbol": sym,
                    "category": "C",
                    "phase3": "skipped (already exists)",
                    "phase4": phase4_results,
                }
            )

        # === B: 12 銘柄 — Phase 3 + Phase 4 ===
        log.info("=" * 60)
        log.info("Category B: Phase 3 + Phase 4 試行")
        log.info("=" * 60)

        for sym in B_SYMBOLS:
            log.info(f"--- {sym} (B) ---")
            entry = {"symbol": sym, "category": "B"}

            ok3, msg3, holdings = fetch_phase3(collector, sym)
            entry["phase3"] = {"ok": ok3, "msg": msg3, "count": len(holdings)}
            log.info(f"  {sym} Phase 3: {'OK' if ok3 else 'FAIL'} — {msg3}")

            if not ok3 or not holdings:
                entry["phase4"] = "skipped (Phase 3 failed)"
                log_entries.append(entry)
                time.sleep(0.5)
                continue

            # 最新 1 期分のみ Phase 4 試行 (リソース節約)
            holding = holdings[0]
            xbrl_url = getattr(holding, "xbrl_url", None) or ""
            if not xbrl_url:
                entry["phase4"] = {"ok": False, "msg": "no xbrl_url in latest holding"}
            else:
                ok4, msg4, result = fetch_phase4(collector, xbrl_url)
                entry["phase4"] = {
                    "ok": ok4,
                    "msg": msg4,
                    "row_count": len(result.rows) if ok4 and result else 0,
                }
                log.info(f"  {sym} Phase 4 (latest): {'OK' if ok4 else 'FAIL'} — {msg4}")

            log_entries.append(entry)
            time.sleep(0.5)

        conn.close()

    # ログを JSON 出力
    LOG_FILE.write_text(
        json.dumps(log_entries, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    log.info(f"\n結果: {LOG_FILE}")

    # サマリー
    log.info("=" * 60)
    log.info("サマリー")
    log.info("=" * 60)
    for e in log_entries:
        if e["category"] == "C":
            n_ok = sum(1 for r in e["phase4"] if r["ok"])
            log.info(f"  {e['symbol']} (C): Phase 4 {n_ok}/{len(e['phase4'])} 成功")
        else:
            p3 = e["phase3"]
            p4 = e.get("phase4", {})
            p3_str = "OK" if (isinstance(p3, dict) and p3.get("ok")) else "FAIL"
            p4_str = (
                "OK" if (isinstance(p4, dict) and p4.get("ok"))
                else ("OK" if p4 == "skipped (Phase 3 failed)" else "FAIL")
                if isinstance(p4, dict)
                else "SKIP"
            )
            log.info(f"  {e['symbol']} (B): Phase 3 {p3_str} / Phase 4 {p4_str}")


if __name__ == "__main__":
    main()

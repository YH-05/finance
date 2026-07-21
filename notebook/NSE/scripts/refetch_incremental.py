"""任意の対象銘柄リストに対して NSE Phase 3/4 データを再取得する汎用スクリプト.

refetch_rev1_missing.py（rev1 と universe の差分 55 銘柄専用にハードコードされた版）を
汎用化したもの。対象銘柄リストは実行のたびに変わりうるため、CLI 引数
``--symbols-file`` で外部 JSON から注入する。

入力:
    --symbols-file で指定する JSON ファイル
        ``target_symbols`` キーに NSE symbol のリストを含むこと。
        例: {"added": [...], "drift": [...], "target_symbols": [...], "removed": [...]}

出力:
    --output-log で指定する JSON ファイル（デフォルト:
    notebook/NSE/data/exports/nse/refetch_incremental_log.json）
        各銘柄の試行結果 (phase3 / phase4 の OK/FAIL とエラー詳細)。
        refetch_rev1_log.json と同一スキーマ。ただし isin / rev1_category は
        symbols-file から得られないため null。

注意:
    SQLite への永続化は行わない（persist_rev1_missing.py 相当の責務は別スクリプト）。
"""

from __future__ import annotations

import argparse
import json
import logging
import time
from pathlib import Path

from market.nse.collectors.share_holding import ShareholdingCollector
from market.nse.session import NseSession

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
log = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[3]
EXPORT_DIR = ROOT / "notebook/NSE/data/exports/nse"
DEFAULT_OUTPUT_LOG = EXPORT_DIR / "refetch_incremental_log.json"

RATE_LIMIT_SEC = 0.5


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="対象銘柄リスト（JSON）に対して NSE Phase 3/4 データを再取得する"
    )
    parser.add_argument(
        "--symbols-file",
        type=Path,
        required=True,
        help="対象銘柄リストを含む JSON ファイルパス（'target_symbols' キーを読む）",
    )
    parser.add_argument(
        "--output-log",
        type=Path,
        default=DEFAULT_OUTPUT_LOG,
        help=f"出力ログ JSON ファイルパス（デフォルト: {DEFAULT_OUTPUT_LOG}）",
    )
    parser.add_argument(
        "--rate-limit-sec",
        type=float,
        default=RATE_LIMIT_SEC,
        help=f"銘柄ごとのレート制限秒数（デフォルト: {RATE_LIMIT_SEC}）",
    )
    return parser.parse_args()


def load_target_symbols(symbols_file: Path) -> list[str]:
    data = json.loads(symbols_file.read_text(encoding="utf-8"))
    symbols = data.get("target_symbols", [])
    if not symbols:
        raise ValueError(f"'target_symbols' キーが見つからないか空です: {symbols_file}")
    return symbols


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
    args = parse_args()
    args.output_log.parent.mkdir(parents=True, exist_ok=True)

    targets = load_target_symbols(args.symbols_file)
    log.info(f"Target symbols: {len(targets)} (from {args.symbols_file})")

    log_entries: list[dict] = []

    with NseSession() as session:
        collector = ShareholdingCollector(session=session)

        for symbol in targets:
            log.info(f"--- {symbol} ---")
            entry: dict = {
                "symbol": symbol,
                "isin": None,
                "rev1_category": None,
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
                time.sleep(args.rate_limit_sec)
                continue

            # Phase 4: latest quarter only (saves rate limit)
            latest = holdings[0]
            xbrl_url = getattr(latest, "xbrl_url", "") or ""
            if not xbrl_url:
                entry["phase4"] = {"ok": False, "msg": "no xbrl_url in latest holding"}
                log_entries.append(entry)
                time.sleep(args.rate_limit_sec)
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
            time.sleep(args.rate_limit_sec)

    args.output_log.write_text(
        json.dumps(log_entries, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    log.info(f"\nLog written: {args.output_log}")

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

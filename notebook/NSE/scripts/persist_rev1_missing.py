"""rev1 圏内・現 universe 圏外 銘柄の永続化 + Phase 5 分類 + 解決不能銘柄の流用.

act-2026-05-12-002: refetch_rev1_missing.py の出力を SQLite に永続化し、
owner_candidates.csv に append する。

処理:
1. refetch_rev1_log.json を読み、成功銘柄 (Phase 3 + Phase 4 両方 OK) について
   Phase 3/4 を再実行して SQLite に INSERT OR REPLACE
2. shareholdings.csv / shareholding_detail.csv を再エクスポート
3. 取得結果から Tier 1-4 ロジックで owner_candidates 行を生成 (nse_fetch_status='ok')
4. Phase 4 失敗銘柄 (BSE 等) は rev1 ラベルから minimal 行を作成
   (nse_fetch_status='phase4_failed_xbrl')
5. unresolvable 17 銘柄も rev1 ラベルから minimal 行を作成
   (nse_fetch_status='unresolvable_isin')
6. owner_candidates.csv に append (既存 787 行は nse_fetch_status='ok' を付与)

入力:
- notebook/NSE/data/exports/nse/refetch_rev1_log.json
- notebook/NSE/data/exports/nse/rev1_missing_from_universe.csv
- notebook/NSE/data/cache/nse/owners_rev1.json
- notebook/NSE/data/cache/nse/nse_index.db (Phase 3/4 結果は upsert 済み)

出力:
- shareholdings.csv / shareholding_detail.csv (再エクスポート)
- owner_candidates.csv (838+ 行に拡張、nse_fetch_status 付き)
- persist_rev1_log.json
"""

from __future__ import annotations

import json
import logging
import sqlite3
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from market.nse.collectors.share_holding import ShareholdingCollector
from market.nse.session import NseSession

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
log = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

from market.nse.analysis.owner_classification import (  # noqa: E402
    FOREIGN_NON_GOVT_SUBS,
    GOVT_COMPONENT_SUBS,
    GOVT_ROLLUP_SUBS,
    classify_owner_flag,
    compute_govt_pct,
    derive_owner_flag_final,
)

DB_PATH = ROOT / "notebook/NSE/data/cache/nse/nse_index.db"
EXPORT_DIR = ROOT / "notebook/NSE/data/exports/nse"
CACHE_DIR = ROOT / "notebook/NSE/data/cache/nse"

REFETCH_LOG = EXPORT_DIR / "refetch_rev1_log.json"
MISSING_CSV = EXPORT_DIR / "rev1_missing_from_universe.csv"
OWNERS_JSON = CACHE_DIR / "owners_rev1.json"
PERSIST_LOG = EXPORT_DIR / "persist_rev1_log.json"

CANDIDATES_CSV = EXPORT_DIR / "owner_candidates.csv"
SH_CSV = EXPORT_DIR / "shareholdings.csv"
SD_CSV = EXPORT_DIR / "shareholding_detail.csv"

RATE_LIMIT_SEC = 0.5


def to_float(s: str) -> float:
    try:
        return float(s) if s and str(s).strip() else 0.0
    except (TypeError, ValueError):
        return 0.0


def to_int(s: str) -> int:
    try:
        return int(float(s)) if s and str(s).strip() else 0
    except (TypeError, ValueError):
        return 0


def upsert_phase3(conn: sqlite3.Connection, symbol: str, holdings: list) -> int:
    fetched_at = datetime.now(UTC).isoformat()
    rows = []
    for h in holdings:
        rows.append(
            (
                h.symbol,
                h.as_on_date,
                to_float(h.promoter_group_pct),
                to_float(h.public_pct),
                to_float(getattr(h, "employee_trust_pct", "")),
                getattr(h, "submission_date", ""),
                getattr(h, "broadcast_date", ""),
                getattr(h, "xbrl_url", ""),
                fetched_at,
            )
        )
    cur = conn.cursor()
    cur.execute("DELETE FROM shareholdings WHERE symbol = ?", (symbol,))
    cur.executemany(
        "INSERT OR IGNORE INTO shareholdings (symbol, as_on_date, promoter_pct, public_pct, "
        "employee_trust_pct, submission_date, broadcast_date, xbrl_url, fetched_at) "
        "VALUES (?,?,?,?,?,?,?,?,?)",
        rows,
    )
    conn.commit()
    return len(rows)


def upsert_phase4(conn: sqlite3.Connection, symbol: str, result) -> int:
    fetched_at = datetime.now(UTC).isoformat()
    report_date = result.as_on_date
    rows = []
    for r in result.rows:
        rows.append(
            (
                r.symbol,
                report_date,
                r.category,
                r.sub_category,
                r.shareholder_name,
                r.pan,
                to_int(r.num_shareholders),
                to_int(r.num_fully_paid_shares),
                to_int(r.num_voting_rights),
                to_float(r.pct_total_shares),
                to_float(r.pct_fully_diluted),
                to_int(r.num_shares_demat),
                1 if str(r.is_category_total).lower() in ("true", "1") else 0,
                fetched_at,
            )
        )
    cur = conn.cursor()
    cur.execute(
        "DELETE FROM shareholding_detail WHERE symbol = ? AND report_date = ?",
        (symbol, report_date),
    )
    cur.executemany(
        "INSERT OR IGNORE INTO shareholding_detail (symbol, report_date, category, sub_category, "
        "shareholder_name, pan, num_shareholders, num_fully_paid_shares, "
        "num_voting_rights, pct_total_shares, pct_fully_diluted, num_shares_demat, "
        "is_category_total, fetched_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        rows,
    )
    conn.commit()
    return len(rows)


def aggregate_owner_candidate(
    conn: sqlite3.Connection, symbol: str, isin: str
) -> dict | None:
    sd = pd.read_sql_query(
        "SELECT * FROM shareholding_detail WHERE symbol = ? ORDER BY report_date DESC",
        conn,
        params=(symbol,),
    )
    if sd.empty:
        return None

    latest_date = sd["report_date"].max()
    df = sd[sd["report_date"] == latest_date].copy()
    company_name = df["shareholder_name"].iloc[0] if not df.empty else symbol

    prom = df[df["category"] == "PromoterAndPromoterGroup"]
    cat_total = prom[prom["is_category_total"] == 1]

    def s(sub: str) -> dict:
        r = cat_total[cat_total["sub_category"] == sub]
        if r.empty:
            return {"num": 0, "pct": 0.0}
        return {
            "num": int(r["num_shareholders"].sum() or 0),
            "pct": float(r["pct_total_shares"].sum()),
        }

    hufi = s("IndividualsOrHinduUndividedFamily")
    nri = s("NonResidentIndividualsOrForeignIndividuals")
    dir_ = s("DirectorsAndDirectorsRelatives")
    kmp = s("KeyManagerialPersonnel")
    rel = s("RelativesOfPromotersOtherThanPromoterGroup")
    trust = s(
        "TrustsWhereAnyPersonBelongingToPromoterAndPromoterGroupIsisTrusteeOrBeneficiaryOrAuthorOfTrust"
    )

    natural_pct_sum = hufi["pct"] + nri["pct"] + dir_["pct"] + kmp["pct"] + rel["pct"]
    natural_num_sum = hufi["num"] + nri["num"] + dir_["num"] + kmp["num"] + rel["num"]

    cat_total_root = cat_total[
        cat_total["sub_category"].isna() | (cat_total["sub_category"] == "")
    ]
    promoter_total_pct = (
        float(cat_total_root["pct_total_shares"].sum())
        if not cat_total_root.empty
        else 0.0
    )
    if promoter_total_pct == 0.0:
        for k in ("Indian", "Foreign"):
            r = cat_total[cat_total["sub_category"] == k]
            promoter_total_pct += float(r["pct_total_shares"].sum())
    if promoter_total_pct == 0.0:
        # 一部XBRL開示（新規上場企業等）では「総合計」行自体が省略され、
        # DirectorsAndDirectorsRelatives等の内訳行のみ存在するケースがある。
        # その場合は内訳合計にフォールバックする（実例: INDGN, IXIGO, FIRSTCRY, PINELABS, SAMHI）。
        promoter_total_pct = natural_pct_sum

    other_indian_pct = float(
        cat_total[cat_total["sub_category"] == "OtherIndianShareholders"][
            "pct_total_shares"
        ].sum()
    )
    other_foreign_pct = float(
        cat_total[cat_total["sub_category"] == "OtherForeignShareholders"][
            "pct_total_shares"
        ].sum()
    )

    # Governments は内訳の合計行であり、内訳と同時に開示されると二重計上になる
    govt_pct = compute_govt_pct(
        float(
            cat_total[cat_total["sub_category"].isin(GOVT_COMPONENT_SUBS)][
                "pct_total_shares"
            ].sum()
        ),
        float(
            cat_total[cat_total["sub_category"].isin(GOVT_ROLLUP_SUBS)][
                "pct_total_shares"
            ].sum()
        ),
    )

    foreign_non_govt_pct = float(
        cat_total[cat_total["sub_category"].isin(FOREIGN_NON_GOVT_SUBS)][
            "pct_total_shares"
        ].sum()
    )

    detail_rows = prom[prom["is_category_total"] == 0]
    names = [n for n in detail_rows["shareholder_name"].dropna().unique() if n.strip()]
    promoter_names = "|".join(names)

    # 判定ルールは市場ロジックとして src/market/nse/analysis に一元化した。
    # 以前は本スクリプト群3本とノートブックに複製されており、同一データでも
    # 処理経路によって結果が変わっていた (実例: INOXGREEN)。
    owner_flag = classify_owner_flag(
        promoter_total_pct=promoter_total_pct,
        hufi_num=hufi["num"],
        hufi_pct=hufi["pct"],
        nri_num=nri["num"],
        dir_num=dir_["num"],
        kmp_num=kmp["num"],
        rel_num=rel["num"],
        trust_num=trust["num"],
        natural_num_sum=natural_num_sum,
        govt_pct=govt_pct,
        other_indian_pct=other_indian_pct,
        other_foreign_pct=other_foreign_pct,
        foreign_non_govt_pct=foreign_non_govt_pct,
    )
    owner_flag_final = derive_owner_flag_final(owner_flag)

    ai_review_needed = owner_flag.startswith("ambiguous") or owner_flag.startswith(
        "owner_probable"
    )

    return {
        "symbol": symbol,
        "company_name": company_name,
        "isin": isin,
        "report_date": latest_date,
        "promoter_total_pct": round(promoter_total_pct, 2),
        "hufi_num": hufi["num"],
        "hufi_pct": round(hufi["pct"], 2),
        "nri_num": nri["num"],
        "nri_pct": round(nri["pct"], 2),
        "dir_num": dir_["num"],
        "dir_pct": round(dir_["pct"], 2),
        "kmp_num": kmp["num"],
        "kmp_pct": round(kmp["pct"], 2),
        "rel_num": rel["num"],
        "rel_pct": round(rel["pct"], 2),
        "trust_num": trust["num"],
        "trust_pct": round(trust["pct"], 2),
        "natural_num_sum": natural_num_sum,
        "natural_pct_sum": round(natural_pct_sum, 2),
        "other_indian_pct": round(other_indian_pct, 2),
        "other_foreign_pct": round(other_foreign_pct, 2),
        "foreign_non_govt_pct": round(foreign_non_govt_pct, 2),
        "govt_pct": round(govt_pct, 2),
        "promoter_names_full_list": promoter_names,
        "owner_flag": owner_flag,
        "ai_review_needed": ai_review_needed,
        "owner_flag_ai": "",
        "ai_confidence": "",
        "ai_reasoning": "",
        "owner_flag_final": owner_flag_final,
    }


def make_rev1_only_row(
    symbol: str,
    isin: str,
    rev1_company: str,
    rev1_category: str,
    nse_fetch_status: str,
) -> dict:
    """NSE 取得不可銘柄について rev1 ラベルだけで minimal row を作成."""
    if rev1_category == "Owner":
        owner_flag_final = "OWNER"
        owner_flag = "rev1_label_only_owner"
    elif rev1_category in ("Professional", "MNC", "State"):
        owner_flag_final = "NOT_OWNER"
        owner_flag = f"rev1_label_only_{rev1_category.lower()}"
    else:
        owner_flag_final = "OWNER_WEAK"
        owner_flag = "rev1_label_only_unknown"

    return {
        "symbol": symbol or "",
        "company_name": rev1_company,
        "isin": isin,
        "report_date": "",
        "promoter_total_pct": 0.0,
        "hufi_num": 0,
        "hufi_pct": 0.0,
        "nri_num": 0,
        "nri_pct": 0.0,
        "dir_num": 0,
        "dir_pct": 0.0,
        "kmp_num": 0,
        "kmp_pct": 0.0,
        "rel_num": 0,
        "rel_pct": 0.0,
        "trust_num": 0,
        "trust_pct": 0.0,
        "natural_num_sum": 0,
        "natural_pct_sum": 0.0,
        "other_indian_pct": 0.0,
        "other_foreign_pct": 0.0,
        "foreign_non_govt_pct": 0.0,
        "govt_pct": 0.0,
        "promoter_names_full_list": "",
        "owner_flag": owner_flag,
        "ai_review_needed": False,
        "owner_flag_ai": "",
        "ai_confidence": "",
        "ai_reasoning": "",
        "owner_flag_final": owner_flag_final,
    }


def main() -> None:
    refetch_log = json.loads(REFETCH_LOG.read_text(encoding="utf-8"))
    missing_df = pd.read_csv(MISSING_CSV)
    rev1_data = json.loads(OWNERS_JSON.read_text(encoding="utf-8"))
    isin_to_rev1 = {e["isin"]: e for e in rev1_data}

    # Phase 4 OK 銘柄 (37 件): SQLite に永続化
    p4_ok_symbols = [
        e["symbol"]
        for e in refetch_log
        if isinstance(e.get("phase4"), dict) and e["phase4"].get("ok")
    ]
    log.info(f"Phase 4 OK symbols (will persist to DB): {len(p4_ok_symbols)}")

    persist_entries: list[dict] = []
    conn = sqlite3.connect(DB_PATH)
    with NseSession() as session:
        coll = ShareholdingCollector(session=session)

        for entry in refetch_log:
            symbol = entry["symbol"]
            if not (
                isinstance(entry.get("phase4"), dict) and entry["phase4"].get("ok")
            ):
                continue

            log.info(f"=== Persisting {symbol} ===")
            persist_entry: dict = {"symbol": symbol, "isin": entry["isin"]}
            try:
                holdings = coll.fetch_shareholding(symbol)
                n3 = upsert_phase3(conn, symbol, holdings)
                persist_entry["phase3_rows"] = n3
                log.info(f"  Phase 3: {n3} rows persisted")
            except Exception as e:
                persist_entry["phase3_error"] = f"{type(e).__name__}: {e}"
                log.error(f"  Phase 3 failed: {e}")
                persist_entries.append(persist_entry)
                time.sleep(RATE_LIMIT_SEC)
                continue

            if holdings and getattr(holdings[0], "xbrl_url", ""):
                try:
                    result = coll.fetch_xbrl_detail(holdings[0].xbrl_url)
                    n4 = upsert_phase4(conn, symbol, result)
                    persist_entry["phase4_rows"] = n4
                    log.info(
                        f"  Phase 4: {n4} rows persisted (report_date={result.as_on_date})"
                    )
                except Exception as e:
                    persist_entry["phase4_error"] = f"{type(e).__name__}: {e}"
                    log.error(f"  Phase 4 failed: {e}")

            persist_entries.append(persist_entry)
            time.sleep(RATE_LIMIT_SEC)

    # Re-export shareholdings.csv / shareholding_detail.csv
    log.info("=" * 60)
    log.info("Re-exporting CSVs")
    log.info("=" * 60)

    sh = pd.read_sql_query(
        "SELECT s.symbol, st.company_name, st.isin, s.as_on_date, s.promoter_pct, "
        "s.public_pct, s.employee_trust_pct, s.submission_date, s.broadcast_date, "
        "s.xbrl_url, s.fetched_at FROM shareholdings s "
        "LEFT JOIN stocks st ON s.symbol = st.symbol",
        conn,
    )
    sh.to_csv(SH_CSV, index=False)
    log.info(f"  shareholdings.csv: {len(sh)} rows")

    sd = pd.read_sql_query(
        "SELECT d.*, st.company_name AS _name, st.isin AS _isin "
        "FROM shareholding_detail d "
        "LEFT JOIN stocks st ON d.symbol = st.symbol",
        conn,
    )
    if "company_name" not in sd.columns:
        sd["company_name"] = sd["_name"]
    if "isin" not in sd.columns:
        sd["isin"] = sd["_isin"]
    sd = sd.drop(columns=[c for c in ["_name", "_isin"] if c in sd.columns])
    sd.to_csv(SD_CSV, index=False)
    log.info(f"  shareholding_detail.csv: {len(sd)} rows")

    # Update owner_candidates.csv
    cand = pd.read_csv(CANDIDATES_CSV)
    log.info(f"  owner_candidates.csv (before): {len(cand)} rows")

    # 既存行に nse_fetch_status='ok' を付与
    if "nse_fetch_status" not in cand.columns:
        cand["nse_fetch_status"] = "ok"

    new_rows: list[dict] = []

    # Phase 4 OK 銘柄: 集計
    for entry in refetch_log:
        if not (isinstance(entry.get("phase4"), dict) and entry["phase4"].get("ok")):
            continue
        row = aggregate_owner_candidate(conn, entry["symbol"], entry["isin"])
        if row:
            row["nse_fetch_status"] = "ok"
            new_rows.append(row)
            log.info(
                f"  Aggregated {entry['symbol']}: flag={row['owner_flag']} → "
                f"final={row['owner_flag_final']}"
            )

    # Phase 4 NG 銘柄 (BSE 等): rev1 ラベル流用
    for entry in refetch_log:
        if isinstance(entry.get("phase4"), dict) and entry["phase4"].get("ok"):
            continue
        # Phase 3 OK だが Phase 4 NG、または両方 NG
        isin = entry["isin"]
        rev1_entry = isin_to_rev1.get(isin)
        if not rev1_entry:
            log.warning(f"  {entry['symbol']}: rev1 not found, skipping")
            continue
        row = make_rev1_only_row(
            symbol=entry["symbol"],
            isin=isin,
            rev1_company=rev1_entry["company name"],
            rev1_category=rev1_entry["Category (Owner, MNC, State, Professional)"],
            nse_fetch_status="phase4_failed_xbrl",
        )
        row["nse_fetch_status"] = "phase4_failed_xbrl"
        new_rows.append(row)
        log.info(
            f"  rev1-only (P4 fail) {entry['symbol']}: flag={row['owner_flag']} → "
            f"final={row['owner_flag_final']}"
        )

    # Unresolvable 17 銘柄: rev1 ラベル流用
    for _, miss in missing_df.iterrows():
        if miss["resolution_status"] != "unresolvable":
            continue
        isin = miss["isin"]
        rev1_entry = isin_to_rev1.get(isin)
        if not rev1_entry:
            continue
        row = make_rev1_only_row(
            symbol="",
            isin=isin,
            rev1_company=rev1_entry["company name"],
            rev1_category=rev1_entry["Category (Owner, MNC, State, Professional)"],
            nse_fetch_status="unresolvable_isin",
        )
        row["nse_fetch_status"] = "unresolvable_isin"
        new_rows.append(row)

    log.info(f"  New rows total: {len(new_rows)}")

    new_df = pd.DataFrame(new_rows)
    # de-dupe by ISIN (新規優先)
    cand_filtered = cand[~cand["isin"].isin([r["isin"] for r in new_rows])]
    # カラム順を揃える
    for col in new_df.columns:
        if col not in cand_filtered.columns:
            cand_filtered = cand_filtered.assign(**{col: ""})
    merged = pd.concat([cand_filtered, new_df], ignore_index=True, sort=False)
    merged.to_csv(CANDIDATES_CSV, index=False)
    log.info(
        f"  owner_candidates.csv (after): {len(merged)} rows ({len(new_rows)} new)"
    )
    log.info(
        f"  nse_fetch_status distribution: "
        f"{merged['nse_fetch_status'].value_counts().to_dict()}"
    )

    conn.close()

    PERSIST_LOG.write_text(
        json.dumps(persist_entries, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    log.info(f"\nPersist log: {PERSIST_LOG}")


if __name__ == "__main__":
    main()

"""rev1 圏内・Phase 3/4 圏外 13 銘柄の永続化 + Phase 5 分類.

入力: refetch_log.json (Phase 3/4 試行成功確認済み)
処理:
1. Phase 3/4 を再実行して結果を SQLite に INSERT OR REPLACE
2. shareholdings.csv / shareholding_detail.csv を再エクスポート
3. shareholding_detail から Phase 5 (Tier 1-4) ロジックで owner_candidates 行を生成
4. owner_candidates.csv に append (de-dupe by symbol)

出力:
- DB: shareholdings, shareholding_detail テーブル更新
- CSV: shareholdings.csv, shareholding_detail.csv 再生成
- CSV: owner_candidates.csv に 13 銘柄追記
- log: persist_log.json
"""

from __future__ import annotations

import json
import logging
import sqlite3
import time
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from market.nse.collectors.share_holding import ShareholdingCollector
from market.nse.session import NseSession

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
log = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[3]
DB_PATH = ROOT / "notebook/NSE/data/cache/nse/nse_index.db"
EXPORT_DIR = ROOT / "notebook/NSE/data/exports/nse"
PERSIST_LOG = EXPORT_DIR / "persist_log.json"

C_SYMBOLS = ["360ONE"]
B_SYMBOLS = [
    "MAHLIFE", "FINOPB", "SANOFI", "BALMLAWRIE", "PGHH", "GUJALKALI",
    "PGHL", "TICL", "PSB", "UTKARSHBNK", "GUJGASLTD", "KIOCL",
]
ALL_SYMBOLS = C_SYMBOLS + B_SYMBOLS


def to_float(s: str) -> float:
    try:
        return float(s) if s and s.strip() else 0.0
    except (TypeError, ValueError):
        return 0.0


def to_int(s: str) -> int:
    try:
        return int(float(s)) if s and s.strip() else 0
    except (TypeError, ValueError):
        return 0


def upsert_phase3(conn: sqlite3.Connection, symbol: str, holdings: list) -> int:
    """Phase 3 結果を shareholdings テーブルに INSERT OR REPLACE."""
    fetched_at = datetime.now(UTC).isoformat()
    rows = []
    for h in holdings:
        rows.append((
            h.symbol, h.as_on_date,
            to_float(h.promoter_group_pct), to_float(h.public_pct),
            to_float(getattr(h, "employee_trust_pct", "")),
            getattr(h, "submission_date", ""), getattr(h, "broadcast_date", ""),
            getattr(h, "xbrl_url", ""), fetched_at,
        ))
    cur = conn.cursor()
    cur.execute("DELETE FROM shareholdings WHERE symbol = ?", (symbol,))
    # API レスポンス内の重複 (re-filing 等) を許容
    cur.executemany(
        "INSERT OR IGNORE INTO shareholdings (symbol, as_on_date, promoter_pct, public_pct, "
        "employee_trust_pct, submission_date, broadcast_date, xbrl_url, fetched_at) "
        "VALUES (?,?,?,?,?,?,?,?,?)",
        rows,
    )
    conn.commit()
    return cur.rowcount if cur.rowcount > 0 else len(rows)


def upsert_phase4(conn: sqlite3.Connection, symbol: str, result) -> int:
    """Phase 4 結果を shareholding_detail テーブルに INSERT OR REPLACE."""
    fetched_at = datetime.now(UTC).isoformat()
    report_date = result.as_on_date  # YYYY-MM-DD
    rows = []
    for r in result.rows:
        rows.append((
            r.symbol, report_date,
            r.category, r.sub_category, r.shareholder_name, r.pan,
            to_int(r.num_shareholders), to_int(r.num_fully_paid_shares),
            to_int(r.num_voting_rights), to_float(r.pct_total_shares),
            to_float(r.pct_fully_diluted), to_int(r.num_shares_demat),
            1 if str(r.is_category_total).lower() in ("true", "1") else 0,
            fetched_at,
        ))
    cur = conn.cursor()
    cur.execute(
        "DELETE FROM shareholding_detail WHERE symbol = ? AND report_date = ?",
        (symbol, report_date),
    )
    # XBRL 内に同名株主が複数 sub_category に出る場合があるため OR IGNORE
    cur.executemany(
        "INSERT OR IGNORE INTO shareholding_detail (symbol, report_date, category, sub_category, "
        "shareholder_name, pan, num_shareholders, num_fully_paid_shares, "
        "num_voting_rights, pct_total_shares, pct_fully_diluted, num_shares_demat, "
        "is_category_total, fetched_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        rows,
    )
    conn.commit()
    return cur.rowcount if cur.rowcount > 0 else len(rows)


def aggregate_owner_candidate(conn: sqlite3.Connection, symbol: str, isin: str) -> dict | None:
    """shareholding_detail から最新四半期の owner_candidates 行を集計."""
    sd = pd.read_sql_query(
        "SELECT * FROM shareholding_detail WHERE symbol = ? "
        "ORDER BY report_date DESC",
        conn, params=(symbol,),
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
    trust = s("TrustsWhereAnyPersonBelongingToPromoterAndPromoterGroupIsisTrusteeOrBeneficiaryOrAuthorOfTrust")

    # promoter total: row with sub_category empty/NaN (= the category rollup)
    cat_total_root = cat_total[cat_total["sub_category"].isna() | (cat_total["sub_category"] == "")]
    promoter_total_pct = float(cat_total_root["pct_total_shares"].sum()) if not cat_total_root.empty else 0.0
    if promoter_total_pct == 0.0:
        # フォールバック: 主要 sub_category の合計 (Indian + Foreign)
        for k in ("Indian", "Foreign"):
            r = cat_total[cat_total["sub_category"] == k]
            promoter_total_pct += float(r["pct_total_shares"].sum())

    other_indian_pct = float(cat_total[cat_total["sub_category"] == "OtherIndianShareholders"]["pct_total_shares"].sum())
    other_foreign_pct = float(cat_total[cat_total["sub_category"] == "OtherForeignShareholders"]["pct_total_shares"].sum())

    govt_subs = {
        "CentralGovernmentOrPresidentOfIndia",
        "StateGovernmentsOrGovernors",
        "ForeignGovernment",
        "ShareholdingByCompaniesOrBodiesCorporatewhereCentralOrStateGovernmentIsPromoter",
        "CentralGovernmentOrStateGovernmentS",
        "Governments", "Goverments",
    }
    govt_pct = float(cat_total[cat_total["sub_category"].isin(govt_subs)]["pct_total_shares"].sum())

    foreign_non_govt_subs = {"ForeignInstitutions", "ForeignPortfolioInvestor"}
    foreign_non_govt_pct = float(cat_total[cat_total["sub_category"].isin(foreign_non_govt_subs)]["pct_total_shares"].sum())

    natural_pct_sum = hufi["pct"] + nri["pct"] + dir_["pct"] + kmp["pct"] + rel["pct"]
    natural_num_sum = hufi["num"] + nri["num"] + dir_["num"] + kmp["num"] + rel["num"]

    # promoter_names_full_list: 個別行の shareholder_name
    detail_rows = prom[prom["is_category_total"] == 0]
    names = [n for n in detail_rows["shareholder_name"].dropna().unique() if n.strip()]
    promoter_names = "|".join(names)

    # Tier 1-4 ロジック (簡易版)
    has_natural = natural_pct_sum > 0
    if has_natural:
        if dir_["pct"] > 0 or kmp["pct"] > 0:
            if hufi["pct"] > 0:
                owner_flag = "owner_confirmed_individual_and_director"
            else:
                owner_flag = "owner_confirmed_director_only"
        elif hufi["pct"] > 0:
            if hufi["pct"] < 0.5 and dir_["pct"] == 0 and kmp["pct"] == 0:
                owner_flag = "owner_confirmed_individual_passive"
            else:
                owner_flag = "owner_confirmed_individual"
        elif nri["pct"] > 0:
            owner_flag = "owner_probable_nri_family"
        else:
            owner_flag = "owner_probable_relatives_trust"
    elif govt_pct >= 50:
        owner_flag = "excluded_state_dominant"
    elif other_indian_pct == 0 and other_foreign_pct == 0 and foreign_non_govt_pct == 0:
        owner_flag = "excluded_no_natural_no_holding"
    elif other_foreign_pct + foreign_non_govt_pct > other_indian_pct:
        owner_flag = "ambiguous_holding_foreign"
    elif other_indian_pct > 0:
        owner_flag = "ambiguous_holding_indian"
    else:
        owner_flag = "ambiguous_mnc_jv_candidate"

    # 簡易 owner_flag_final (AI レビュー未適用、ハイブリッド未適用)
    if owner_flag.startswith("owner_confirmed") or owner_flag.startswith("owner_probable"):
        owner_flag_final = "OWNER"
    elif owner_flag.startswith("excluded"):
        owner_flag_final = "NOT_OWNER"
    else:
        owner_flag_final = "OWNER_WEAK"  # ambiguous は AI レビュー要

    ai_review_needed = owner_flag.startswith("ambiguous") or owner_flag.startswith("owner_probable")

    return {
        "symbol": symbol,
        "company_name": company_name,
        "isin": isin,
        "report_date": latest_date,
        "promoter_total_pct": round(promoter_total_pct, 2),
        "hufi_num": hufi["num"], "hufi_pct": round(hufi["pct"], 2),
        "nri_num": nri["num"], "nri_pct": round(nri["pct"], 2),
        "dir_num": dir_["num"], "dir_pct": round(dir_["pct"], 2),
        "kmp_num": kmp["num"], "kmp_pct": round(kmp["pct"], 2),
        "rel_num": rel["num"], "rel_pct": round(rel["pct"], 2),
        "trust_num": trust["num"], "trust_pct": round(trust["pct"], 2),
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


def main() -> None:
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)

    # rev1 から ISIN を引く
    with open(ROOT / "notebook/NSE/data/cache/nse/owners.json", encoding="utf-8") as f:
        rev1 = json.load(f)
    name_to_isin = {x["company name"]: x["isin"] for x in rev1}

    sym_isin = {
        "360ONE": "INE466L01038",
        "MAHLIFE": "INE813A01018", "FINOPB": "INE02NC01014", "SANOFI": "INE058A01010",
        "BALMLAWRIE": "INE164A01016", "PGHH": "INE179A01014", "GUJALKALI": "INE186A01019",
        "PGHL": "INE199A01012", "TICL": "INE388G01026", "PSB": "INE608A01012",
        "UTKARSHBNK": "INE735W01017", "GUJGASLTD": "INE844O01030", "KIOCL": "INE880L01014",
    }

    persist_log: list[dict] = []
    conn = sqlite3.connect(DB_PATH)

    with NseSession() as session:
        coll = ShareholdingCollector(session=session)

        for symbol in ALL_SYMBOLS:
            log.info(f"=== {symbol} ===")
            entry = {"symbol": symbol}

            # Phase 3
            try:
                holdings = coll.fetch_shareholding(symbol)
                n3 = upsert_phase3(conn, symbol, holdings)
                entry["phase3_rows"] = n3
                log.info(f"  Phase 3: {n3} rows persisted")
            except Exception as e:
                entry["phase3_error"] = f"{type(e).__name__}: {e}"
                log.error(f"  Phase 3 failed: {e}")
                persist_log.append(entry)
                time.sleep(0.5)
                continue

            # Phase 4: 最新四半期のみ (owner_candidates 用)
            if holdings and getattr(holdings[0], "xbrl_url", ""):
                try:
                    result = coll.fetch_xbrl_detail(holdings[0].xbrl_url)
                    n4 = upsert_phase4(conn, symbol, result)
                    entry["phase4_rows"] = n4
                    log.info(f"  Phase 4: {n4} rows persisted (report_date={result.as_on_date})")
                except Exception as e:
                    entry["phase4_error"] = f"{type(e).__name__}: {e}"
                    log.error(f"  Phase 4 failed: {e}")

            persist_log.append(entry)
            time.sleep(0.5)

    # 再エクスポート
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
    sh.to_csv(EXPORT_DIR / "shareholdings.csv", index=False)
    log.info(f"  shareholdings.csv: {len(sh)} rows")

    sd = pd.read_sql_query(
        "SELECT d.*, st.company_name AS _name, st.isin AS _isin "
        "FROM shareholding_detail d "
        "LEFT JOIN stocks st ON d.symbol = st.symbol",
        conn,
    )
    # company_name / isin が detail 側にない場合のみ stocks から補完
    if "company_name" not in sd.columns:
        sd["company_name"] = sd["_name"]
    if "isin" not in sd.columns:
        sd["isin"] = sd["_isin"]
    sd = sd.drop(columns=[c for c in ["_name", "_isin"] if c in sd.columns])
    sd.to_csv(EXPORT_DIR / "shareholding_detail.csv", index=False)
    log.info(f"  shareholding_detail.csv: {len(sd)} rows")

    # owner_candidates.csv に 13 銘柄を追記
    cand = pd.read_csv(EXPORT_DIR / "owner_candidates.csv")
    log.info(f"  owner_candidates.csv (before): {len(cand)} rows")

    new_rows = []
    for symbol in ALL_SYMBOLS:
        row = aggregate_owner_candidate(conn, symbol, sym_isin[symbol])
        if row:
            new_rows.append(row)
            log.info(f"  Aggregated {symbol}: flag={row['owner_flag']} → final={row['owner_flag_final']}")

    if new_rows:
        new_df = pd.DataFrame(new_rows)
        # de-dupe
        cand_filtered = cand[~cand["symbol"].isin([r["symbol"] for r in new_rows])]
        merged = pd.concat([cand_filtered, new_df], ignore_index=True)
        merged.to_csv(EXPORT_DIR / "owner_candidates.csv", index=False)
        log.info(f"  owner_candidates.csv (after): {len(merged)} rows ({len(new_rows)} new)")

    conn.close()

    PERSIST_LOG.write_text(json.dumps(persist_log, ensure_ascii=False, indent=2), encoding="utf-8")
    log.info(f"\nPersist log: {PERSIST_LOG}")


if __name__ == "__main__":
    main()

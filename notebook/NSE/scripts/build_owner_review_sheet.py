"""
act-2026-04-30-009: 全 787 銘柄レビューシート生成

入力:
- notebook/NSE/data/exports/nse/owner_candidates.csv (787 銘柄)
- notebook/NSE/data/cache/nse/owners.json (rev1 GT, 632 銘柄, ISIN ベース)

出力:
- notebook/NSE/data/exports/nse/owner_review_sheet.csv
    787 銘柄全件、rev1 圏内/圏外フラグ付き、owner_flag 別ソート
- notebook/NSE/data/exports/nse/owner_review_summary.md
    owner_flag 別 / rev1 圏内圏外別の集計サマリー
- notebook/NSE/data/exports/nse/owner_review_rev1_outside.csv
    rev1 圏外 223 銘柄のみ抽出 (act-2026-05-07-001 用)
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[3]
EXPORT_DIR = ROOT / "notebook/NSE/data/exports/nse"
CACHE_DIR = ROOT / "notebook/NSE/data/cache/nse"
CONFIG_DIR = ROOT / "data/config"

CANDIDATES_CSV = EXPORT_DIR / "owner_candidates.csv"
OWNERS_JSON = CACHE_DIR / "owners.json"
CLASSIFIER_YAML = CONFIG_DIR / "nse_promoter_classifier.yaml"

OUT_SHEET = EXPORT_DIR / "owner_review_sheet.csv"
OUT_SUMMARY = EXPORT_DIR / "owner_review_summary.md"
OUT_REV1_OUT = EXPORT_DIR / "owner_review_rev1_outside.csv"


def classify_promoter_names(promoter_names: str, yaml_data: dict) -> tuple[str, str]:
    """yaml v0.3.0 の解決アルゴリズムを Python で実装.

    Returns
    -------
    (classification, matched_detail)
        classification: 'OWNER' | 'PROFESSIONAL' | 'STATE' | 'MNC' | 'UNKNOWN'
        matched_detail: マッチした keyword と family/parent (ログ用)
    """
    if not isinstance(promoter_names, str):
        return "UNKNOWN", ""
    text_lower = promoter_names.lower()

    matched = {"OWNER": [], "PROFESSIONAL": [], "STATE": [], "MNC": []}
    override_state = False

    for kw in yaml_data.get("owner_keywords", []):
        if kw["keyword"].lower() not in text_lower:
            continue
        # exclude_when_also_matches: いずれかが同時マッチしていれば OWNER 認定から除外
        # (信託 vehicle 経由保有のような OWNER+PROFESSIONAL/STATE/MNC 両マッチ問題への対処)
        excludes = kw.get("exclude_when_also_matches") or []
        if any(ex.lower() in text_lower for ex in excludes):
            continue
        matched["OWNER"].append(f"{kw['keyword']}({kw.get('family', '')})")
        if kw.get("override_state"):
            override_state = True

    for kw in yaml_data.get("professional_keywords", []):
        if kw["keyword"].lower() in text_lower:
            matched["PROFESSIONAL"].append(f"{kw['keyword']}({kw.get('parent', '')})")

    for kw in yaml_data.get("state_keywords", []):
        if kw["keyword"].lower() in text_lower:
            matched["STATE"].append(f"{kw['keyword']}({kw.get('parent', '')})")

    for kw in yaml_data.get("mnc_keywords", []):
        if kw["keyword"].lower() in text_lower:
            matched["MNC"].append(f"{kw['keyword']}({kw.get('parent', '')})")

    detail = "; ".join(f"{cat}=[{','.join(v)}]" for cat, v in matched.items() if v)

    has_owner = bool(matched["OWNER"])
    has_prof = bool(matched["PROFESSIONAL"])
    has_state = bool(matched["STATE"])
    has_mnc = bool(matched["MNC"])

    # Tata Communications 例外: Tata Sons + PRESIDENT OF INDIA → PROFESSIONAL
    if any("tata sons" in m.lower() for m in matched["PROFESSIONAL"]) and any(
        "president of india" in m.lower() for m in matched["STATE"]
    ):
        return "PROFESSIONAL", detail

    # state 優先 (override_state でなければ)
    if has_state and not override_state:
        return "STATE", detail
    if has_owner and not has_prof and not has_mnc:
        return "OWNER", detail
    if has_owner and override_state:
        return "OWNER", detail
    if has_prof and not has_owner:
        return "PROFESSIONAL", detail
    if has_mnc and not has_owner and not has_prof:
        return "MNC", detail
    if has_owner and has_prof:
        return "UNKNOWN", detail  # 矛盾
    return "UNKNOWN", detail


def load_rev1() -> pd.DataFrame:
    """owners.json (ISIN canonical) を DataFrame 化."""
    with OWNERS_JSON.open(encoding="utf-8") as f:
        data = json.load(f)
    rev1 = pd.DataFrame(data)
    rev1 = rev1.rename(
        columns={
            "company name": "rev1_company_name",
            "isin": "isin",
            "Category (Owner, MNC, State, Professional)": "rev1_category",
        }
    )
    return rev1[["isin", "rev1_company_name", "rev1_category"]]


def main() -> None:
    cand = pd.read_csv(CANDIDATES_CSV)
    rev1 = load_rev1()
    with CLASSIFIER_YAML.open(encoding="utf-8") as f:
        yaml_data = yaml.safe_load(f)

    # Merge on ISIN
    merged = cand.merge(rev1, on="isin", how="left")
    merged["in_rev1"] = merged["rev1_category"].notna()
    merged["is_owner_in_rev1"] = merged["rev1_category"] == "Owner"

    # ハイブリッドルール (yaml 分類器) を owner_confirmed_director_only に適用
    # CSV の owner_flag_final はハイブリッド未適用なので、ここで上書き
    yaml_results = merged["promoter_names_full_list"].apply(
        lambda x: classify_promoter_names(x, yaml_data)
    )
    merged["yaml_classification"] = yaml_results.apply(lambda x: x[0])
    merged["yaml_matched_detail"] = yaml_results.apply(lambda x: x[1])

    def apply_hybrid(row: pd.Series) -> str:
        flag = row["owner_flag"]
        cls = row["yaml_classification"]

        # Tier 2 ハイブリッド: director_only への yaml 適用
        if flag == "owner_confirmed_director_only":
            if cls == "OWNER":
                return "OWNER"
            if cls in ("PROFESSIONAL", "STATE", "MNC"):
                return "NOT_OWNER"
            return "OWNER_WEAK"

        # ambiguous_*: yaml 分類で確定情報があればそれに従う
        ambiguous_targets = {
            "ambiguous_holding_indian",
            "ambiguous_holding_foreign",
            "ambiguous_mnc_jv_candidate",
        }
        if flag in ambiguous_targets:
            if cls == "OWNER":
                return "OWNER"  # Tier 1.5 corporate-vehicle rescue
            if cls in ("PROFESSIONAL", "STATE", "MNC"):
                return "NOT_OWNER"  # yaml で非Owner確定
            return row["owner_flag_final"]  # UNKNOWN: AI レビュー結果に従う

        # excluded_*: 基本 NOT_OWNER だが owner_keywords マッチで救済
        excluded_targets = {
            "excluded_no_natural_no_holding",
            "excluded_state_dominant",
        }
        if flag in excluded_targets and cls == "OWNER":
            return "OWNER"

        # owner_probable_* / owner_via_individual_in_other (Tier 2 / 2.5):
        # yaml で既知一族と確定マッチした場合は OWNER に昇格 (act-2026-05-11-018)
        probable_targets = {
            "owner_probable_relatives_trust",
            "owner_probable_nri_family",
            "owner_via_individual_in_other",
        }
        if flag in probable_targets and cls == "OWNER":
            return "OWNER"

        return row["owner_flag_final"]

    merged["owner_flag_final_hybrid"] = merged.apply(apply_hybrid, axis=1)

    # 判定ステータス: TP/FP/FN/TN/(rev1 圏外) — ハイブリッド版で評価
    def judge(row: pd.Series) -> str:
        if not row["in_rev1"]:
            return "rev1_outside"
        is_owner_pred = row["owner_flag_final_hybrid"] in ("OWNER", "OWNER_WEAK")
        is_owner_gt = row["is_owner_in_rev1"]
        if is_owner_pred and is_owner_gt:
            return "TP"
        if is_owner_pred and not is_owner_gt:
            return "FP"
        if not is_owner_pred and is_owner_gt:
            return "FN"
        return "TN"

    merged["judge"] = merged.apply(judge, axis=1)

    # ソート: owner_flag → judge → symbol
    flag_order = [
        "owner_confirmed_individual_and_director",
        "owner_confirmed_individual",
        "owner_confirmed_individual_passive",
        "owner_confirmed_director_only",
        "owner_probable_relatives_trust",
        "owner_probable_nri_family",
        "owner_via_individual_in_other",
        "ambiguous_holding_indian",
        "ambiguous_holding_foreign",
        "ambiguous_mnc_jv_candidate",
        "excluded_no_natural_no_holding",
        "excluded_state_dominant",
    ]
    merged["__flag_order"] = (
        merged["owner_flag"].map({f: i for i, f in enumerate(flag_order)}).fillna(99)
    )
    merged = merged.sort_values(["__flag_order", "judge", "symbol"]).drop(
        columns=["__flag_order"]
    )

    # 出力カラム
    cols = [
        "symbol",
        "company_name",
        "isin",
        "owner_flag",
        "owner_flag_final",
        "owner_flag_final_hybrid",
        "yaml_classification",
        "yaml_matched_detail",
        "judge",
        "in_rev1",
        "rev1_category",
        "rev1_company_name",
        "promoter_total_pct",
        "natural_pct_sum",
        "hufi_pct",
        "dir_pct",
        "kmp_pct",
        "rel_pct",
        "trust_pct",
        "other_indian_pct",
        "other_foreign_pct",
        "foreign_non_govt_pct",
        "govt_pct",
        "ai_review_needed",
        "owner_flag_ai",
        "ai_confidence",
        "ai_reasoning",
        "promoter_names_full_list",
    ]
    merged[cols].to_csv(OUT_SHEET, index=False)
    print(f"Wrote: {OUT_SHEET} ({len(merged)} rows)")

    # rev1 圏外のみ抽出
    rev1_out = merged[merged["judge"] == "rev1_outside"].copy()
    rev1_out[cols].to_csv(OUT_REV1_OUT, index=False)
    print(f"Wrote: {OUT_REV1_OUT} ({len(rev1_out)} rows)")

    # サマリー Markdown
    lines = ["# Owner Review Sheet Summary", ""]
    lines.append("**生成元**: act-2026-04-30-009 / act-2026-05-07-001")
    lines.append(f"**対象**: 全 {len(merged)} 銘柄 (Phase 3/4 完了)")
    lines.append(f"**rev1 GT**: {len(rev1)} 銘柄")
    lines.append(f"**intersection (rev1 圏内)**: {merged['in_rev1'].sum()} 銘柄")
    lines.append(
        f"**rev1 圏外**: {(~merged['in_rev1']).sum()} 銘柄 (← 目視レビュー優先対象)"
    )
    lines.append("")

    # owner_flag_final 分布 (ハイブリッド適用後)
    lines.append("## owner_flag_final_hybrid 分布 (ハイブリッドルール適用後)")
    lines.append("")
    final_dist = merged["owner_flag_final_hybrid"].value_counts()
    lines.append("| owner_flag_final_hybrid | 銘柄数 |")
    lines.append("|---|---|")
    for flag, n in final_dist.items():
        lines.append(f"| {flag} | {n} |")
    lines.append("")
    lines.append("(参考) CSV 上の `owner_flag_final` (ハイブリッド未適用) との差異:")
    lines.append("")
    diff = merged[merged["owner_flag_final"] != merged["owner_flag_final_hybrid"]]
    lines.append(f"- ハイブリッドで再分類された銘柄: {len(diff)} 件")
    lines.append("")

    # judge 分布
    lines.append("## 判定状況")
    lines.append("")
    judge_dist = merged["judge"].value_counts()
    lines.append("| judge | 銘柄数 | 説明 |")
    lines.append("|---|---|---|")
    descriptions = {
        "TP": "rev1=Owner ∩ 予測=OWNER (true positive)",
        "TN": "rev1≠Owner ∩ 予測=NOT_OWNER (true negative)",
        "FP": "rev1≠Owner ∩ 予測=OWNER (false positive、要確認)",
        "FN": "rev1=Owner ∩ 予測=NOT_OWNER (false negative、要確認)",
        "rev1_outside": "rev1 GT 圏外、generated label のみ (act-05-07-001 対象)",
    }
    for j in ["TP", "TN", "FP", "FN", "rev1_outside"]:
        n = judge_dist.get(j, 0)
        lines.append(f"| {j} | {n} | {descriptions[j]} |")
    lines.append("")

    # owner_flag × judge クロス集計
    lines.append("## owner_flag × judge クロス集計")
    lines.append("")
    cross = pd.crosstab(merged["owner_flag"], merged["judge"]).reindex(
        columns=["TP", "TN", "FP", "FN", "rev1_outside"], fill_value=0
    )
    cross["total"] = cross.sum(axis=1)
    cross = cross.sort_values("total", ascending=False)
    header = "| owner_flag | " + " | ".join(cross.columns) + " |"
    sep = "|---" * (len(cross.columns) + 1) + "|"
    lines.append(header)
    lines.append(sep)
    for flag, row in cross.iterrows():
        cells = " | ".join(str(int(v)) for v in row)
        lines.append(f"| {flag} | {cells} |")
    lines.append("")

    # rev1 圏外 銘柄の owner_flag_final_hybrid 分布
    lines.append("## rev1 圏外 銘柄の owner_flag_final_hybrid 分布")
    lines.append("")
    out_dist = rev1_out["owner_flag_final_hybrid"].value_counts()
    lines.append("| owner_flag_final_hybrid | 銘柄数 |")
    lines.append("|---|---|")
    for flag, n in out_dist.items():
        lines.append(f"| {flag} | {n} |")
    lines.append("")

    # 要注意ケース: rev1 圏外で OWNER_WEAK (AI レビュー対象)
    weak_outside = rev1_out[rev1_out["owner_flag_final_hybrid"] == "OWNER_WEAK"]
    if not weak_outside.empty:
        lines.append("### rev1 圏外 OWNER_WEAK 銘柄 (AI レビューが必要)")
        lines.append("")
        lines.append("| symbol | company_name | owner_flag | promoter_pct |")
        lines.append("|---|---|---|---|")
        for _, r in weak_outside.iterrows():
            lines.append(
                f"| {r['symbol']} | {r['company_name']} | {r['owner_flag']} | "
                f"{r['promoter_total_pct']:.2f}% |"
            )
        lines.append("")

    # rev1 圏外で Tier 1.5 救済 (excluded/ambiguous → OWNER) の可能性高い銘柄
    rescued_outside = rev1_out[
        (rev1_out["owner_flag_final_hybrid"] == "OWNER")
        & (
            rev1_out["owner_flag"].isin(
                [
                    "excluded_no_natural_no_holding",
                    "excluded_state_dominant",
                    "ambiguous_holding_indian",
                    "ambiguous_holding_foreign",
                    "ambiguous_mnc_jv_candidate",
                ]
            )
        )
    ]
    if not rescued_outside.empty:
        lines.append(
            "### rev1 圏外で Tier 1.5 corporate-vehicle rescue / A-3 救済された銘柄"
        )
        lines.append("")
        lines.append(
            "| symbol | company_name | owner_flag (Tier 2) | owner_flag_final |"
        )
        lines.append("|---|---|---|---|")
        for _, r in rescued_outside.iterrows():
            lines.append(
                f"| {r['symbol']} | {r['company_name']} | {r['owner_flag']} | "
                f"{r['owner_flag_final']} |"
            )
        lines.append("")

    # rev1 圏外 / NOT_OWNER で promoter_pct >=10% かつ natural_pct_sum > 0 (要確認)
    suspect_not_owner = rev1_out[
        (rev1_out["owner_flag_final_hybrid"] == "NOT_OWNER")
        & (rev1_out["promoter_total_pct"] >= 10)
        & (rev1_out["natural_pct_sum"] > 0)
    ]
    if not suspect_not_owner.empty:
        lines.append(
            "### rev1 圏外 NOT_OWNER だが natural_pct>0 & promoter>=10% (見落とし候補)"
        )
        lines.append("")
        lines.append(
            "| symbol | company_name | owner_flag | promoter_pct | natural_pct |"
        )
        lines.append("|---|---|---|---|---|")
        for _, r in suspect_not_owner.iterrows():
            lines.append(
                f"| {r['symbol']} | {r['company_name']} | {r['owner_flag']} | "
                f"{r['promoter_total_pct']:.2f}% | {r['natural_pct_sum']:.2f}% |"
            )
        lines.append("")

    OUT_SUMMARY.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote: {OUT_SUMMARY}")


if __name__ == "__main__":
    main()

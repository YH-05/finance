"""rev1 圏外 223 銘柄の目視レビュー用パッケージ生成 (act-2026-05-07-001).

入力: notebook/NSE/data/exports/nse/owner_review_sheet.csv (800 銘柄)
出力:
1. notebook/NSE/data/exports/nse/rev1_outside_review.md
   優先度別 (P0-P4) のレビュー用 Markdown
2. notebook/NSE/data/exports/nse/rev1_outside_review.csv
   priority 列付きの整形済み CSV
3. notebook/NSE/data/exports/nse/yaml_extension_candidates.md
   223 銘柄の promoter_names から抽出した yaml 拡張候補
"""

from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
EXPORT_DIR = ROOT / "notebook/NSE/data/exports/nse"
SHEET = EXPORT_DIR / "owner_review_sheet.csv"
OUT_MD = EXPORT_DIR / "rev1_outside_review.md"
OUT_CSV = EXPORT_DIR / "rev1_outside_review.csv"
OUT_YAML_CAND = EXPORT_DIR / "yaml_extension_candidates.md"


def assign_priority(row: pd.Series) -> tuple[str, str]:
    """銘柄に優先度 P0-P4 と理由を割り当てる."""
    flag = row["owner_flag"]
    final = row["owner_flag_final_hybrid"]
    yaml_cls = row["yaml_classification"]
    promoter = row["promoter_total_pct"]
    natural = row["natural_pct_sum"]
    other_indian = row["other_indian_pct"]
    other_foreign = row["other_foreign_pct"]

    # P0: 確認必須 — OWNER_WEAK (yaml 未マッチ)
    if final == "OWNER_WEAK":
        return ("P0", "OWNER_WEAK: yaml 未マッチで AI/手動判定が必要")

    # P1: 高優先 — Tier 1.5 / A-3 救済 (excluded/ambiguous → OWNER に変換された)
    if final == "OWNER" and flag in (
        "excluded_no_natural_no_holding",
        "excluded_state_dominant",
        "ambiguous_holding_indian",
        "ambiguous_holding_foreign",
        "ambiguous_mnc_jv_candidate",
        "owner_via_individual_in_other",
    ):
        return ("P1", f"Tier 1.5 corporate-vehicle rescue: {flag} → OWNER (yaml owner_keyword match)")

    # P2: 中優先 — promoter 低いが OWNER 判定 (Tier 1 流入の可能性)
    if final == "OWNER" and promoter < 30 and flag.startswith("owner_confirmed"):
        return ("P2", f"低 promoter ({promoter:.1f}%) で OWNER 判定: 構造的限界 (Tier 1 流入)")

    # P3: 中優先 — Tier 2 director_only で yaml マッチ
    if flag == "owner_confirmed_director_only":
        if final == "OWNER" and yaml_cls == "OWNER":
            return ("P3", f"Tier 2 hybrid OK: director_only + yaml owner match")
        if final == "NOT_OWNER":
            return ("P3", f"Tier 2 hybrid NOT_OWNER: yaml {yaml_cls} match")
        if final == "OWNER_WEAK":
            return ("P0", "Tier 2 director_only + yaml UNKNOWN: 確認必須")

    # P4: 低優先 — Tier 1 高信頼 OWNER (個人 promoter 顕在)
    if final == "OWNER" and flag in (
        "owner_confirmed_individual_and_director",
        "owner_confirmed_individual",
        "owner_confirmed_individual_passive",
        "owner_probable_nri_family",
        "owner_probable_relatives_trust",
    ):
        return ("P4", f"高信頼 OWNER ({flag}): スポット確認のみ")

    # P4: 低優先 — 明確な NOT_OWNER (excluded_state_dominant)
    if final == "NOT_OWNER":
        return ("P4", f"明確 NOT_OWNER: {flag}")

    return ("P4", f"その他: {flag} → {final}")


def extract_yaml_candidates(df: pd.DataFrame) -> str:
    """223 銘柄の promoter_names から yaml 拡張候補を抽出."""
    text_lines = []
    text_lines.append("# yaml 拡張候補 (rev1 圏外 223 銘柄から抽出)\n")
    text_lines.append("OWNER_WEAK 銘柄の promoter_names_full_list を分析し、共通する企業グループを特定。")
    text_lines.append("ユーザー目視で「これは Owner/Professional/MNC/State」と判定したら、yaml v0.5.0 で keyword 追加。\n")

    weak = df[df["owner_flag_final_hybrid"] == "OWNER_WEAK"].copy()
    text_lines.append(f"## OWNER_WEAK {len(weak)} 銘柄の promoter (詳細)\n")
    text_lines.append("| symbol | company | promoter_% | promoter_names_full_list (先頭 300 char) |")
    text_lines.append("|---|---|---|---|")
    for _, r in weak.sort_values("promoter_total_pct", ascending=False).iterrows():
        names = str(r.get("promoter_names_full_list", ""))[:300]
        # | をエスケープ
        names = names.replace("|", "<br>")
        company = str(r.get("company_name", ""))[:40] if pd.notna(r.get("company_name")) else r["symbol"]
        text_lines.append(f"| {r['symbol']} | {company} | {r['promoter_total_pct']:.1f}% | {names} |")
    text_lines.append("")

    # promoter_names 全体から頻出企業グループ (P0+P1+P2 のみ)
    target = df[df["priority"].isin(["P0", "P1", "P2"])]
    word_counter = Counter()
    family_indicators = [
        "Tata", "Adani", "Birla", "Mahindra", "Bajaj", "Mittal", "Hinduja",
        "Goenka", "Lodha", "Patanjali", "Shriram", "Wadia", "Jindal",
        "Reliance", "Ambani", "Vedanta", "Agarwal", "L&T", "Larsen",
        "HDFC", "ICICI", "SBI", "Axis", "PNB",
        "Schneider", "Siemens", "Whirlpool", "P&G", "Procter", "Sanofi",
        "Government of", "President of", "PRESIDENT OF",
        "Carlyle", "Blackstone", "KKR", "TPG", "Bain", "Warburg",
    ]
    for _, r in target.iterrows():
        text = str(r.get("promoter_names_full_list", ""))
        for ind in family_indicators:
            if ind.lower() in text.lower():
                word_counter[ind] += 1

    text_lines.append("\n## P0/P1/P2 銘柄の promoter_names で頻出するグループ (Top 20)")
    text_lines.append("| 出現キーワード | 件数 | 推定カテゴリ |")
    text_lines.append("|---|---|---|")
    cat_hint = {
        "Tata": "Professional", "Adani": "Owner", "Birla": "Owner",
        "Mahindra": "Owner", "Bajaj": "Owner", "Mittal": "Owner",
        "Hinduja": "Owner", "Goenka": "Owner", "Lodha": "Owner",
        "Patanjali": "Owner", "Shriram": "Owner", "Wadia": "Owner",
        "Jindal": "Owner", "Reliance": "Owner", "Ambani": "Owner",
        "Vedanta": "Owner", "Agarwal": "Owner",
        "L&T": "Professional", "Larsen": "Professional",
        "HDFC": "Professional", "ICICI": "Professional", "SBI": "State",
        "Axis": "Professional", "PNB": "State",
        "Schneider": "MNC", "Siemens": "MNC", "Whirlpool": "MNC",
        "P&G": "MNC", "Procter": "MNC", "Sanofi": "MNC",
        "Government of": "State", "President of": "State", "PRESIDENT OF": "State",
        "Carlyle": "Professional", "Blackstone": "Professional",
        "KKR": "Professional", "TPG": "Professional",
        "Bain": "Professional", "Warburg": "Professional",
    }
    for kw, cnt in word_counter.most_common(20):
        text_lines.append(f"| {kw} | {cnt} | {cat_hint.get(kw, '?')} |")

    return "\n".join(text_lines)


def main() -> None:
    df = pd.read_csv(SHEET)
    out = df[df["judge"] == "rev1_outside"].copy()
    print(f"rev1 圏外: {len(out)} 銘柄")

    # 優先度割当
    out[["priority", "priority_reason"]] = out.apply(
        lambda r: pd.Series(assign_priority(r)), axis=1
    )
    print(f"\n優先度分布:")
    print(out["priority"].value_counts().sort_index())

    # CSV 出力
    cols_csv = [
        "priority", "priority_reason", "symbol", "company_name", "isin",
        "owner_flag", "owner_flag_final_hybrid", "yaml_classification",
        "yaml_matched_detail", "promoter_total_pct", "natural_pct_sum",
        "hufi_pct", "dir_pct", "kmp_pct", "other_indian_pct",
        "other_foreign_pct", "foreign_non_govt_pct", "govt_pct",
        "promoter_names_full_list",
    ]
    out_sorted = out.sort_values(["priority", "promoter_total_pct"], ascending=[True, False])
    out_sorted[cols_csv].to_csv(OUT_CSV, index=False)
    print(f"\n→ {OUT_CSV}")

    # Markdown 出力
    lines = []
    lines.append("# rev1 圏外 223 銘柄 — 目視レビュー用レポート")
    lines.append("")
    lines.append(f"**生成日**: 2026-05-07 / **act-2026-05-07-001**")
    lines.append(f"**対象**: 全 800 銘柄中、rev1 GT 圏外 {len(out)} 銘柄")
    lines.append(f"**目的**: ground truth 無しの generated label の妥当性をユーザー目視で確認")
    lines.append("")
    lines.append("## 優先度定義")
    lines.append("")
    lines.append("| 優先度 | 定義 | アクション |")
    lines.append("|--------|------|----------|")
    lines.append("| **P0** | OWNER_WEAK (yaml 未マッチ) | 目視で Owner/Professional/MNC/State を確定 → yaml 追補 |")
    lines.append("| **P1** | Tier 1.5 corporate-vehicle rescue で OWNER 化 | 救済が妥当か確認 (NOT_OWNER の可能性) |")
    lines.append("| **P2** | 低 promoter (<30%) で OWNER 判定 | 真の Owner か Tier 1 誤流入か判定 |")
    lines.append("| **P3** | Tier 2 director_only + yaml 確定 | スポット確認 (大半は正しい) |")
    lines.append("| **P4** | Tier 1 高信頼 OWNER または明確 NOT_OWNER | 大量、サンプルチェックのみ |")
    lines.append("")
    lines.append("## 優先度別件数")
    lines.append("")
    lines.append("| 優先度 | 件数 | 推奨レビュー時間 |")
    lines.append("|--------|------|-----------------|")
    for p in ["P0", "P1", "P2", "P3", "P4"]:
        n = (out["priority"] == p).sum()
        time_est = {"P0": "1-2 分/件", "P1": "1 分/件", "P2": "30 秒/件",
                     "P3": "10 秒/件", "P4": "サンプルのみ"}[p]
        lines.append(f"| {p} | {n} | {time_est} |")
    lines.append("")

    # 各優先度の詳細
    for priority in ["P0", "P1", "P2", "P3"]:
        sub = out_sorted[out_sorted["priority"] == priority]
        if sub.empty:
            continue
        lines.append(f"---")
        lines.append("")
        lines.append(f"## {priority} ({len(sub)} 銘柄)")
        lines.append("")
        if priority == "P0":
            lines.append(
                "**OWNER_WEAK** — yaml 既知一族リストにマッチせず、Tier 4 で AI レビュー対象だった銘柄。"
                "promoter_names を見て Owner/Professional/MNC/State を確定し、yaml v0.5.0 で keyword 追加してください。"
            )
        elif priority == "P1":
            lines.append(
                "**Tier 1.5 corporate-vehicle rescue** で `excluded_*` / `ambiguous_*` から OWNER に救済された銘柄。"
                "yaml owner_keyword がマッチしていますが、本当に Owner 一族支配かを確認してください。"
            )
        elif priority == "P2":
            lines.append(
                "**低 promoter (<30%) で OWNER 判定** — Tier 1 ロジックで個人 promoter が顕在化しているが、"
                "promoter 比率自体が低い銘柄。Murthy/Jhunjhunwala 系の Tier 1 流入と同じ構造的限界の可能性。"
            )
        elif priority == "P3":
            lines.append(
                "**Tier 2 director_only + yaml 確定** — yaml が OWNER/PROFESSIONAL/STATE/MNC のいずれかにマッチして確定済み。"
                "サンプルでスポット確認するのみで OK。"
            )
        lines.append("")

        cols_md = ["symbol", "company_name", "owner_flag", "owner_flag_final_hybrid",
                   "yaml_classification", "promoter_total_pct"]
        lines.append("| symbol | company | flag (Tier 2) | final | yaml_cls | promoter% | promoter_names (先頭150文字) |")
        lines.append("|---|---|---|---|---|---|---|")
        for _, r in sub.iterrows():
            company = str(r.get("company_name", "")) if pd.notna(r.get("company_name")) else ""
            company = company[:35]
            names = str(r.get("promoter_names_full_list", ""))[:150]
            names = names.replace("|", " / ").replace("\n", " ")
            yaml_cls = str(r.get("yaml_classification", ""))
            lines.append(
                f"| {r['symbol']} | {company} | {r['owner_flag']} | {r['owner_flag_final_hybrid']} | "
                f"{yaml_cls} | {r['promoter_total_pct']:.1f}% | {names} |"
            )
        lines.append("")

    # P4 サマリー
    p4 = out_sorted[out_sorted["priority"] == "P4"]
    lines.append(f"---")
    lines.append("")
    lines.append(f"## P4 ({len(p4)} 銘柄) — 低優先度")
    lines.append("")
    lines.append("Tier 1 高信頼 OWNER または明確 NOT_OWNER の銘柄群。サンプルのみ確認推奨。")
    lines.append("")
    lines.append("### owner_flag 分布")
    lines.append("")
    lines.append("| owner_flag | 件数 |")
    lines.append("|---|---|")
    for flag, cnt in p4["owner_flag"].value_counts().items():
        lines.append(f"| {flag} | {cnt} |")
    lines.append("")
    lines.append("### owner_flag_final_hybrid 分布")
    lines.append("")
    lines.append("| final | 件数 |")
    lines.append("|---|---|")
    for f, cnt in p4["owner_flag_final_hybrid"].value_counts().items():
        lines.append(f"| {f} | {cnt} |")
    lines.append("")
    lines.append(f"**詳細は `rev1_outside_review.csv` を Excel で開いて priority=P4 でフィルタ**")
    lines.append("")

    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(f"→ {OUT_MD}")

    # yaml 拡張候補
    yaml_md = extract_yaml_candidates(out)
    OUT_YAML_CAND.write_text(yaml_md, encoding="utf-8")
    print(f"→ {OUT_YAML_CAND}")


if __name__ == "__main__":
    main()

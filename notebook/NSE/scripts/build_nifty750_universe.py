"""
act-2026-05-07-002: NIFTY 750 universe メタデータ整備 + owner_companies.csv 確定版

目的:
    NSE オーナー企業抽出 (project-106 / yaml v0.5.1) の最終成果物として
    NIFTY 750 (800 銘柄) を investment universe として整備する。
    NSE owner extraction の universe は NIFTY 750 (analyst universe (US銘柄中心)
    とは別軸 — feedback memory: feedback_nse_universe_is_nifty750.md)。

入力:
    - notebook/NSE/data/exports/nse/owner_review_sheet.csv (800 行)
    - notebook/NSE/data/cache/nse/nse_index.db
        index_members テーブル (NIFTY 50 / 100 / 200 / 500 / TOTAL MKT)

出力:
    - notebook/NSE/data/exports/nse/owner_companies.csv
        確定版オーナー企業 (OWNER 600 件)
    - notebook/NSE/data/exports/nse/nifty750_universe.csv
        800 銘柄全件 + universe メタデータ (is_owner_company / owner_family /
        is_nifty50 / is_nifty100 / is_nifty200 / is_nifty500 / is_nifty_total_mkt)
    - notebook/NSE/data/exports/nse/nifty750_universe_summary.md
        Owner 比率・family 別分布・index level 別分布のサマリー
"""

from __future__ import annotations

import re
import sqlite3
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
EXPORT_DIR = ROOT / "notebook/NSE/data/exports/nse"
CACHE_DIR = ROOT / "notebook/NSE/data/cache/nse"

REVIEW_SHEET = EXPORT_DIR / "owner_review_sheet.csv"
INDEX_DB = CACHE_DIR / "nse_index.db"

OUT_OWNERS = EXPORT_DIR / "owner_companies.csv"
OUT_UNIVERSE = EXPORT_DIR / "nifty750_universe.csv"
OUT_SUMMARY = EXPORT_DIR / "nifty750_universe_summary.md"

INDEX_TARGETS = {
    "is_nifty50": "NIFTY 50",
    "is_nifty100": "NIFTY 100",
    "is_nifty200": "NIFTY 200",
    "is_nifty500": "NIFTY 500",
    "is_nifty_total_mkt": "NIFTY TOTAL MKT",
}


def extract_owner_family(yaml_matched_detail: str) -> str:
    """yaml_matched_detail の OWNER=[KEYWORD(family),...] から family を抽出.

    family 自体が括弧を含むケース (例: 'Goenka (RPSG)') にも対応するため、
    KEYWORD(...) のパースは単純 regex ではなく括弧深度を追跡する。
    複数 family がマッチした場合は重複を除いて | 区切りで結合.
    OWNER カテゴリのマッチがない場合は空文字を返す.
    """
    if not isinstance(yaml_matched_detail, str) or "OWNER=[" not in yaml_matched_detail:
        return ""
    # OWNER=[...] セクションのみを抽出 (PROFESSIONAL=[...] 等が後続する場合に備える)
    m = re.search(r"OWNER=\[(.+?)\](?:;|$)", yaml_matched_detail)
    if not m:
        return ""
    inner = m.group(1)

    # KEYWORD(family) パターンを括弧深度トラッキングで抽出
    families: list[str] = []
    depth = 0
    start = -1
    for i, ch in enumerate(inner):
        if ch == "(":
            if depth == 0:
                start = i + 1
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0 and start >= 0:
                families.append(inner[start:i])
                start = -1

    # 重複除去 (順序保持)
    seen: dict[str, None] = {}
    for f in families:
        if f and f not in seen:
            seen[f] = None
    return "|".join(seen.keys())


def load_index_membership() -> pd.DataFrame:
    """nse_index.db から NIFTY 50/100/200/500/TOTAL MKT の構成銘柄を取得.

    Returns
    -------
    pd.DataFrame
        symbol を index に、各 is_niftyXX フラグを bool で持つ DataFrame
    """
    with sqlite3.connect(INDEX_DB) as conn:
        df = pd.read_sql(
            "SELECT index_name, symbol FROM index_members "
            f"WHERE index_name IN ({','.join(['?'] * len(INDEX_TARGETS))})",
            conn,
            params=list(INDEX_TARGETS.values()),
        )
    pivot = pd.DataFrame({"symbol": df["symbol"].unique()})
    for flag, idx_name in INDEX_TARGETS.items():
        members = set(df[df["index_name"] == idx_name]["symbol"])
        pivot[flag] = pivot["symbol"].isin(members)
    return pivot.set_index("symbol")


def main() -> None:
    sheet = pd.read_csv(REVIEW_SHEET)
    print(f"Loaded review sheet: {len(sheet)} rows")

    # owner_family 抽出
    sheet["owner_family"] = sheet["yaml_matched_detail"].apply(extract_owner_family)
    sheet["is_owner_company"] = sheet["owner_flag_final_hybrid"] == "OWNER"

    # index 帰属フラグを付与
    membership = load_index_membership()
    sheet = sheet.merge(
        membership, left_on="symbol", right_index=True, how="left"
    )
    for flag in INDEX_TARGETS:
        sheet[flag] = sheet[flag].fillna(False).astype(bool)

    # ----- Step 1: owner_companies.csv 確定版 -----
    owner_cols = [
        "symbol",
        "isin",
        "company_name",
        "owner_flag",
        "owner_flag_final_hybrid",
        "yaml_classification",
        "owner_family",
        "promoter_total_pct",
        "natural_pct_sum",
        "in_rev1",
        "rev1_category",
        "is_nifty50",
        "is_nifty100",
        "is_nifty200",
        "is_nifty500",
        "is_nifty_total_mkt",
    ]
    owners = sheet[sheet["is_owner_company"]][owner_cols].copy()
    owners = owners.sort_values(["owner_family", "symbol"])
    owners.to_csv(OUT_OWNERS, index=False)
    print(f"Wrote: {OUT_OWNERS} ({len(owners)} owner companies)")

    # ----- Step 2: nifty750_universe.csv (800 銘柄全件 + メタデータ) -----
    universe_cols = [
        "symbol",
        "isin",
        "company_name",
        "is_owner_company",
        "owner_family",
        "owner_flag",
        "owner_flag_final_hybrid",
        "yaml_classification",
        "promoter_total_pct",
        "natural_pct_sum",
        "in_rev1",
        "rev1_category",
        "is_nifty50",
        "is_nifty100",
        "is_nifty200",
        "is_nifty500",
        "is_nifty_total_mkt",
    ]
    universe = sheet[universe_cols].copy()
    universe = universe.sort_values(["is_owner_company", "symbol"], ascending=[False, True])
    universe.to_csv(OUT_UNIVERSE, index=False)
    print(f"Wrote: {OUT_UNIVERSE} ({len(universe)} stocks)")

    # ----- Step 3: nifty750_universe_summary.md -----
    lines: list[str] = []
    lines.append("# NIFTY 750 Universe Summary (NSE Owner Extraction)")
    lines.append("")
    lines.append(f"**生成元**: act-2026-05-07-002 (build_nifty750_universe.py)")
    lines.append(f"**入力**: owner_review_sheet.csv (yaml v0.5.1)")
    lines.append(f"**対象**: 全 {len(universe)} 銘柄 (NIFTY 750 + rev1 補完 50 銘柄)")
    lines.append("")

    # 全体サマリー
    n_total = len(universe)
    n_owner = int(universe["is_owner_company"].sum())
    n_not_owner = n_total - n_owner
    lines.append("## 全体サマリー")
    lines.append("")
    lines.append("| 区分 | 銘柄数 | 比率 |")
    lines.append("|---|---|---|")
    lines.append(f"| OWNER | {n_owner} | {n_owner / n_total * 100:.1f}% |")
    lines.append(f"| NOT_OWNER | {n_not_owner} | {n_not_owner / n_total * 100:.1f}% |")
    lines.append(f"| 合計 | {n_total} | 100.0% |")
    lines.append("")

    # Index level 別 Owner 比率
    lines.append("## Index level 別 OWNER 比率")
    lines.append("")
    lines.append("| Index | 帰属銘柄数 | OWNER 数 | OWNER 比率 |")
    lines.append("|---|---|---|---|")
    for flag, idx_name in INDEX_TARGETS.items():
        members = universe[universe[flag]]
        n_members = len(members)
        n_member_owners = int(members["is_owner_company"].sum())
        ratio = n_member_owners / n_members * 100 if n_members > 0 else 0
        lines.append(f"| {idx_name} | {n_members} | {n_member_owners} | {ratio:.1f}% |")
    n_outside = (~universe[list(INDEX_TARGETS.keys())].any(axis=1)).sum()
    n_outside_owners = int(
        universe[~universe[list(INDEX_TARGETS.keys())].any(axis=1)]["is_owner_company"].sum()
    )
    outside_ratio = n_outside_owners / n_outside * 100 if n_outside > 0 else 0
    lines.append(
        f"| (上記 5 index 圏外、rev1 補完銘柄) | {n_outside} | {n_outside_owners} | {outside_ratio:.1f}% |"
    )
    lines.append("")

    # Owner family 別分布 (上位 20)
    lines.append("## OWNER family 別分布 (上位 20)")
    lines.append("")
    family_counts = (
        universe[universe["is_owner_company"] & (universe["owner_family"] != "")]
        .assign(family_first=lambda x: x["owner_family"].str.split("|").str[0])
        .groupby("family_first")
        .size()
        .sort_values(ascending=False)
        .head(20)
    )
    lines.append("| Family | 銘柄数 |")
    lines.append("|---|---|")
    for family, n in family_counts.items():
        lines.append(f"| {family} | {n} |")
    lines.append("")

    # family が空の OWNER (yaml 未マッチで OWNER 確定したもの)
    n_owner_no_family = int(
        ((universe["is_owner_company"]) & (universe["owner_family"] == "")).sum()
    )
    lines.append(
        f"**family 未取得 OWNER**: {n_owner_no_family} 件 "
        "(yaml owner_keywords 未マッチで Tier 1 自然人 promoter ベースで OWNER 判定された銘柄)"
    )
    lines.append("")

    # 利用例
    lines.append("## 利用例")
    lines.append("")
    lines.append("```python")
    lines.append("import pandas as pd")
    lines.append("")
    lines.append("# 全 universe (800 銘柄) を読み込み")
    lines.append('df = pd.read_csv("notebook/NSE/data/exports/nse/nifty750_universe.csv")')
    lines.append("")
    lines.append("# OWNER 企業のみフィルタ (= owner_companies.csv 相当)")
    lines.append('owners = df[df["is_owner_company"]]')
    lines.append("")
    lines.append("# NIFTY 100 圏内 OWNER 企業のみ")
    lines.append('large_owners = df[df["is_owner_company"] & df["is_nifty100"]]')
    lines.append("")
    lines.append("# 特定 family の銘柄を抽出 (Adani グループ)")
    lines.append('adani = df[df["owner_family"].fillna("").str.contains("Adani")]')
    lines.append("```")
    lines.append("")

    OUT_SUMMARY.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote: {OUT_SUMMARY}")


if __name__ == "__main__":
    main()

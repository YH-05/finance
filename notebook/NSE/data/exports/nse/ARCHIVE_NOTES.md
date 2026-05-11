# Archive Notes — 履歴ファイル一覧

このディレクトリには「現在の最新成果物」と「過去のスナップショット」が混在している。
混同を避けるため、本ファイルでマップする。最新メトリクスは `logic_system_review.md` または `nifty750_universe_summary.md` を参照。

**最終更新**: 2026-05-11 (yaml v0.5.1 / project-106 Phase 5 完了時点)

---

## 🟢 現役 (Current)

直近のロジック・設定・出力。

| ファイル | 説明 |
|---|---|
| `owner_review_sheet.csv` | 全 800 銘柄レビューシート (yaml v0.5.1 適用済) |
| `owner_review_summary.md` | 上記の集計サマリー |
| `owner_review_rev1_outside.csv` | rev1 圏外 223 銘柄抽出 |
| `nifty750_universe.csv` | **800 銘柄 + メタデータ (唯一の確定版)** (act-2026-05-07-002 + dec-2026-05-11-011)。`df[df["is_owner_company"]]` で OWNER 600 件をフィルタ |
| `nifty750_universe_summary.md` | universe 全体サマリー |
| `logic_system_review.md` | ロジック体系レビュー (v0.5.1 ベース) |
| `rev1_outside_review.csv` / `.md` | rev1 圏外 P0-P4 優先度分類 (人間レビュー用、現役) |
| `owner_candidates.csv` | 元データ (Phase 3/4 + 13 銘柄救済反映済) |
| `shareholdings.csv` / `shareholding_detail.csv` | XBRL 抽出データ (May 7 時点、現役) |
| `index_members.csv` / `stocks.csv` | NSE 銘柄マスタ (Apr 17、現役、低頻度更新) |
| `xbrl_category_reference.md` | XBRL カテゴリ参照 (Apr 17、ロジック設計仕様、現役) |

---

## 🟡 履歴スナップショット (Historical Snapshots)

過去の特定時点のレポート。**現状の数字とは異なる**ので注意。失敗パターン学習や経緯トレース用に保管。

| ファイル | 生成時点 | 当時の状態 | 現状との差異 |
|---|---|---|---|
| `owners_coverage_and_false_positives.md` | 2026-04-27 | FP=42 件 (director_only ハイブリッド導入前) | **現在 FP=4 件まで縮減** |
| `owners_reconciliation.csv` | 2026-04-30 | rev1 GT との照合表 (632 件、ハイブリッド前) | rev1 採用後の照合は `owner_review_sheet.csv` (judge 列) で代替 |
| `owners_rev1_false_positives.csv` | 2026-04-30 | rev1 評価時の FP リスト (3 件) | 現在の FP 4 件と内容差あり (`owner_review_sheet.csv` で `judge=FP` フィルタ) |
| `owners_rev1_false_negatives.csv` | 2026-04-30 | rev1 評価時の FN リスト (0 件) | 現在も FN=0 維持 |
| `rev1_diff_report.md` | 2026-04-30 | act-2026-04-30-007 自動 diff レポート (787 銘柄 / FP=3 / Precision 99.3%) | **800 銘柄 / FP=4 / Precision 99.04% に更新** |
| `refetch_log.json` | 2026-05-07 | act-2026-05-07-003 13 銘柄救済の試行ログ | 救済完了、再実行不要 |
| `persist_log.json` | 2026-05-07 | 同上の永続化ログ | 同上 |

---

## 🔵 関連スクリプト

| ファイル | 状態 | 説明 |
|---|---|---|
| `notebook/NSE/scripts/build_owner_review_sheet.py` | 🟢 現役 | レビューシート生成 (v0.5.1 ハイブリッド + exclude_when 評価対応) |
| `notebook/NSE/scripts/build_nifty750_universe.py` | 🟢 現役 | NIFTY 750 universe 整備 (Step 1-3 一括) |
| `notebook/NSE/scripts/build_rev1_outside_review.py` | 🟢 現役 | rev1 圏外 P0-P4 分類スクリプト |
| `notebook/NSE/scripts/refetch_missing.py` | 🟡 履歴 | 13 銘柄救済 (一回限り、完了済) |
| `notebook/NSE/scripts/persist_and_classify.py` | 🟡 履歴 | 13 銘柄永続化 (一回限り、完了済) |

---

## 🗑️ 廃止済 (Trash)

v0.5.1 リリースで陳腐化、`trash/2026-05-11_nse-owner-obsolete/` へ移動済:

- `yaml_v0.5.0_proposal.md`
- `yaml_v0.5.0_evidence.md`
- `yaml_extension_candidates.md`
- `_shareholding_detail.csv` (古い snapshot)
- `_shareholdings.csv` (古い snapshot)
- `owner_companies.csv` (nifty750_universe.csv に集約、dec-2026-05-11-011)

詳細 (廃止経緯): `docs/plan/2026-05-11_obsolete-nse-files.md` 参照
実体 (ローカルのみ、`trash/` は `.gitignore` 除外): `trash/2026-05-11_nse-owner-obsolete/`

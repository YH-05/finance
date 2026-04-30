# NSE Owner Candidates - rev1 GT Diff Report

**生成日時**: 2026-04-30T17:02:05
**対象**:
- owner_candidates.csv: 787 銘柄
- owners.json (rev1 GT): 632 銘柄
- intersection: 564 銘柄

## メトリクスサマリー

| 指標 | 値 |
|---|---|
| TP | 410 |
| FP | 3 |
| FN | 0 |
| TN | 151 |
| Precision | 99.3% |
| Recall | 100.0% |
| F1 | 99.6% |

**Confusion**: TP=410 FP=3 FN=0 TN=151

## 前回比較

前回レポートなし（初回実行）

## 残 FP 一覧

- [INFY] INFOSYS LTD - cat=Professional flag=owner_confirmed_individual_and_director ai=nan
- [STARHEALTH] STAR HEALTH & ALLIED INSURAN - cat=Professional flag=owner_confirmed_individual_and_director ai=nan
- [KSB] KSB LTD - cat=MNC flag=owner_confirmed_individual_passive ai=nan

## 残 FN 一覧

（なし）

## 関連ファイル

- `owners_reconciliation.csv` — ISIN 主キー照合表 (632 rows)
- `owners_rev1_false_positives.csv` — FP 3 件
- `owners_rev1_false_negatives.csv` — FN 0 件
- `rev1_diff_report_prev.md` — 前回レポート（差分比較用）

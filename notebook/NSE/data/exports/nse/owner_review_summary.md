# Owner Review Sheet Summary

**生成元**: act-2026-04-30-009 / act-2026-05-07-001
**対象**: 全 865 銘柄 (Phase 3/4 完了)
**rev1 GT**: 632 銘柄
**intersection (rev1 圏内)**: 632 銘柄
**rev1 圏外**: 233 銘柄 (← 目視レビュー優先対象)

## owner_flag_final_hybrid 分布 (ハイブリッドルール適用後)

| owner_flag_final_hybrid | 銘柄数 |
|---|---|
| OWNER | 608 |
| NOT_OWNER | 251 |
| OWNER_WEAK | 6 |

(参考) CSV 上の `owner_flag_final` (ハイブリッド未適用) との差異:

- ハイブリッドで再分類された銘柄: 75 件

## 判定状況

| judge | 銘柄数 | 説明 |
|---|---|---|
| TP | 419 | rev1=Owner ∩ 予測=OWNER (true positive) |
| TN | 203 | rev1≠Owner ∩ 予測=NOT_OWNER (true negative) |
| FP | 4 | rev1≠Owner ∩ 予測=OWNER (false positive、要確認) |
| FN | 6 | rev1=Owner ∩ 予測=NOT_OWNER (false negative、要確認) |
| rev1_outside | 233 | rev1 GT 圏外、generated label のみ (act-05-07-001 対象) |

## owner_flag × judge クロス集計

| owner_flag | TP | TN | FP | FN | rev1_outside | total |
|---|---|---|---|---|---|---|
| owner_confirmed_individual_and_director | 298 | 1 | 2 | 0 | 122 | 423 |
| owner_confirmed_individual | 64 | 0 | 2 | 0 | 50 | 116 |
| owner_confirmed_director_only | 23 | 43 | 0 | 0 | 20 | 86 |
| excluded_state_dominant | 1 | 69 | 0 | 0 | 2 | 72 |
| excluded_low_promoter | 0 | 33 | 0 | 6 | 4 | 43 |
| excluded_no_natural_no_holding | 3 | 25 | 0 | 0 | 15 | 43 |
| ambiguous_holding_foreign | 4 | 13 | 0 | 0 | 8 | 25 |
| ambiguous_holding_indian | 7 | 7 | 0 | 0 | 7 | 21 |
| ambiguous_mnc_jv_candidate | 4 | 2 | 0 | 0 | 3 | 9 |
| rev1_label_only_owner | 8 | 0 | 0 | 0 | 0 | 8 |
| rev1_label_only_professional | 0 | 8 | 0 | 0 | 0 | 8 |
| owner_probable_nri_family | 6 | 0 | 0 | 0 | 1 | 7 |
| nse_data_unavailable | 0 | 0 | 0 | 0 | 1 | 1 |
| owner_probable_relatives_trust | 1 | 0 | 0 | 0 | 0 | 1 |
| rev1_label_only_mnc | 0 | 1 | 0 | 0 | 0 | 1 |
| rev1_label_only_state | 0 | 1 | 0 | 0 | 0 | 1 |

## rev1 圏外 銘柄の owner_flag_final_hybrid 分布

| owner_flag_final_hybrid | 銘柄数 |
|---|---|
| OWNER | 185 |
| NOT_OWNER | 42 |
| OWNER_WEAK | 6 |

### rev1 圏外 OWNER_WEAK 銘柄 (AI レビューが必要)

| symbol | company_name | owner_flag | promoter_pct |
|---|---|---|---|
| INDGN | nan | owner_confirmed_director_only | 21.42% |
| IXIGO | nan | owner_confirmed_director_only | 13.35% |
| CIGNITITEC | nan | ambiguous_holding_indian | 54.00% |
| JSWDULUX | nan | ambiguous_holding_indian | 61.20% |
| SAGILITY | nan | ambiguous_holding_foreign | 50.95% |
| AKZOINDIA | Akzo Nobel India Limited | nse_data_unavailable | 0.00% |

### rev1 圏外で Tier 1.5 corporate-vehicle rescue / A-3 救済された銘柄

| symbol | company_name | owner_flag (Tier 2) | owner_flag_final |
|---|---|---|---|
| BHARTIHEXA | nan | ambiguous_holding_indian | OWNER_WEAK |
| KITEX | nan | ambiguous_holding_indian | OWNER |
| SMLMAH | nan | ambiguous_holding_indian | OWNER |
| TRAVELFOOD | nan | ambiguous_holding_indian | OWNER |
| PFOCUS | nan | ambiguous_mnc_jv_candidate | OWNER |

### rev1 圏外 NOT_OWNER だが natural_pct>0 & promoter>=10% (見落とし候補)

| symbol | company_name | owner_flag | promoter_pct | natural_pct |
|---|---|---|---|---|
| FEDFINA | nan | owner_confirmed_director_only | 60.81% | 0.28% |
| HDBFS | nan | owner_confirmed_director_only | 74.15% | 0.16% |
| ITCHOTELS | nan | owner_confirmed_director_only | 39.85% | 0.02% |
| JSFB | nan | owner_confirmed_director_only | 21.85% | 0.68% |
| TATACAP | nan | owner_confirmed_director_only | 85.41% | 0.18% |
| TATAINVEST | nan | owner_confirmed_director_only | 73.38% | 0.07% |
| THYROCARE | nan | owner_confirmed_director_only | 60.92% | 0.14% |
| TMCV | nan | owner_confirmed_director_only | 42.56% | 0.03% |
| GRINDWELL | nan | ambiguous_mnc_jv_candidate | 58.03% | 6.44% |
| HCG | nan | ambiguous_mnc_jv_candidate | 64.21% | 9.86% |
| AADHARHFC | nan | excluded_no_natural_no_holding | 64.90% | 0.41% |
| BBOX | nan | excluded_no_natural_no_holding | 70.49% | 1.60% |
| CRISIL | nan | excluded_no_natural_no_holding | 66.64% | 0.06% |
| HEXT | nan | excluded_no_natural_no_holding | 74.30% | 0.48% |
| NIVABUPA | nan | excluded_no_natural_no_holding | 55.36% | 0.92% |
| ORKLAINDIA | nan | excluded_no_natural_no_holding | 75.00% | 0.01% |
| THOMASCOOK | nan | excluded_no_natural_no_holding | 63.83% | 0.09% |
| VIYASH | nan | excluded_no_natural_no_holding | 61.41% | 3.20% |

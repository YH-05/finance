# Owner Review Sheet Summary

**生成元**: act-2026-04-30-009 / act-2026-05-07-001
**対象**: 全 864 銘柄 (Phase 3/4 完了)
**rev1 GT**: 632 銘柄
**intersection (rev1 圏内)**: 632 銘柄
**rev1 圏外**: 232 銘柄 (← 目視レビュー優先対象)

## owner_flag_final_hybrid 分布 (ハイブリッドルール適用後)

| owner_flag_final_hybrid | 銘柄数 |
|---|---|
| OWNER | 615 |
| NOT_OWNER | 214 |
| OWNER_WEAK | 35 |

(参考) CSV 上の `owner_flag_final` (ハイブリッド未適用) との差異:

- ハイブリッドで再分類された銘柄: 108 件

## 判定状況

| judge | 銘柄数 | 説明 |
|---|---|---|
| TP | 425 | rev1=Owner ∩ 予測=OWNER (true positive) |
| TN | 177 | rev1≠Owner ∩ 予測=NOT_OWNER (true negative) |
| FP | 30 | rev1≠Owner ∩ 予測=OWNER (false positive、要確認) |
| FN | 0 | rev1=Owner ∩ 予測=NOT_OWNER (false negative、要確認) |
| rev1_outside | 232 | rev1 GT 圏外、generated label のみ (act-05-07-001 対象) |

## owner_flag × judge クロス集計

| owner_flag | TP | TN | FP | FN | rev1_outside | total |
|---|---|---|---|---|---|---|
| owner_confirmed_individual_and_director | 299 | 0 | 4 | 0 | 120 | 423 |
| owner_confirmed_director_only | 25 | 45 | 24 | 0 | 24 | 118 |
| owner_confirmed_individual | 64 | 0 | 2 | 0 | 51 | 117 |
| excluded_state_dominant | 1 | 68 | 0 | 0 | 2 | 71 |
| excluded_no_natural_no_holding | 3 | 30 | 0 | 0 | 14 | 47 |
| ambiguous_holding_foreign | 4 | 14 | 0 | 0 | 8 | 26 |
| ambiguous_holding_indian | 7 | 8 | 0 | 0 | 8 | 23 |
| ambiguous_mnc_jv_candidate | 4 | 2 | 0 | 0 | 2 | 8 |
| rev1_label_only_owner | 8 | 0 | 0 | 0 | 0 | 8 |
| rev1_label_only_professional | 0 | 8 | 0 | 0 | 0 | 8 |
| owner_probable_nri_family | 6 | 0 | 0 | 0 | 1 | 7 |
| owner_confirmed_individual_passive | 2 | 0 | 0 | 0 | 1 | 3 |
| owner_probable_relatives_trust | 2 | 0 | 0 | 0 | 0 | 2 |
| nse_data_unavailable | 0 | 0 | 0 | 0 | 1 | 1 |
| rev1_label_only_mnc | 0 | 1 | 0 | 0 | 0 | 1 |
| rev1_label_only_state | 0 | 1 | 0 | 0 | 0 | 1 |

## rev1 圏外 銘柄の owner_flag_final_hybrid 分布

| owner_flag_final_hybrid | 銘柄数 |
|---|---|
| OWNER | 185 |
| NOT_OWNER | 37 |
| OWNER_WEAK | 10 |

### rev1 圏外 OWNER_WEAK 銘柄 (AI レビューが必要)

| symbol | company_name | owner_flag | promoter_pct |
|---|---|---|---|
| FIRSTCRY | nan | owner_confirmed_director_only | 5.31% |
| INDGN | nan | owner_confirmed_director_only | 21.42% |
| INOXGREEN | nan | owner_confirmed_director_only | 56.12% |
| IXIGO | nan | owner_confirmed_director_only | 13.35% |
| PINELABS | nan | owner_confirmed_director_only | 2.66% |
| SAMHI | nan | owner_confirmed_director_only | 2.14% |
| CIGNITITEC | nan | ambiguous_holding_indian | 54.00% |
| JSWDULUX | nan | ambiguous_holding_indian | 61.20% |
| SAGILITY | nan | ambiguous_holding_foreign | 50.95% |
| AKZOINDIA | Akzo Nobel India Limited | nse_data_unavailable | 0.00% |

### rev1 圏外で Tier 1.5 corporate-vehicle rescue / A-3 救済された銘柄

| symbol | company_name | owner_flag (Tier 2) | owner_flag_final |
|---|---|---|---|
| BAJAJHFL | nan | ambiguous_holding_indian | OWNER_WEAK |
| BHARTIHEXA | Bharti Hexacom Limited | ambiguous_holding_indian | OWNER_WEAK |
| KITEX | Kitex Garments Limited | ambiguous_holding_indian | OWNER |
| SMLMAH | SML Mahindra Limited | ambiguous_holding_indian | OWNER |
| TRAVELFOOD | Travel Food Services Limited | ambiguous_holding_indian | OWNER |
| PFOCUS | Prime Focus Limited | ambiguous_mnc_jv_candidate | OWNER |

### rev1 圏外 NOT_OWNER だが natural_pct>0 & promoter>=10% (見落とし候補)

| symbol | company_name | owner_flag | promoter_pct | natural_pct |
|---|---|---|---|---|
| AADHARHFC | nan | owner_confirmed_director_only | 64.90% | 0.41% |
| FEDFINA | Fedbank Financial Services Limited | owner_confirmed_director_only | 60.81% | 0.28% |
| HDBFS | HDB Financial Services Limited | owner_confirmed_director_only | 74.15% | 0.16% |
| ITCHOTELS | ITC Hotels Limited | owner_confirmed_director_only | 39.85% | 0.02% |
| JSFB | Jana Small Finance Bank Limited | owner_confirmed_director_only | 21.85% | 0.68% |
| TATACAP | Tata Capital Limited | owner_confirmed_director_only | 85.41% | 0.18% |
| TATAINVEST | Tata Investment Corporation Limited | owner_confirmed_director_only | 73.38% | 0.07% |
| THYROCARE | Thyrocare Technologies Limited | owner_confirmed_director_only | 60.92% | 0.14% |
| TMCV | Tata Motors Limited | owner_confirmed_director_only | 42.56% | 0.03% |
| HCG | Healthcare Global Enterprises Limited | ambiguous_mnc_jv_candidate | 64.21% | 9.86% |
| BBOX | Black Box Limited | excluded_no_natural_no_holding | 70.49% | 1.60% |
| CRISIL | CRISIL Limited | excluded_no_natural_no_holding | 66.64% | 0.06% |
| HEXT | Hexaware Technologies Limited | excluded_no_natural_no_holding | 74.30% | 0.48% |
| NIVABUPA | Niva Bupa Health Insurance Company Limited | excluded_no_natural_no_holding | 55.36% | 0.92% |
| ORKLAINDIA | Orkla India Limited | excluded_no_natural_no_holding | 75.00% | 0.01% |
| THOMASCOOK | Thomas Cook  (India)  Limited | excluded_no_natural_no_holding | 63.83% | 0.09% |
| VIYASH | Viyash Scientific Limited | excluded_no_natural_no_holding | 61.41% | 3.20% |

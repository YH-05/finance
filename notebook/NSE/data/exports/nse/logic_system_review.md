# NSE オーナー企業判定 ロジック体系レビュー

**生成日**: 2026-05-07
**対象**: act-2026-04-30-009 (現状ロジック検証)
**スコープ**: NIFTY 750 (Phase 3/4 完了 787 銘柄)
**現状メトリクス (rev1 GT intersection 564 銘柄)**: TP=410 / FP=4 / FN=0 / TN=150 → **Precision 99.0% / Recall 100% / F1 99.5%**

---

## 1. ロジック全体像

```
[NSE shareholding XBRL]
        |
        v
[Phase 3/4: 787銘柄に対する shareholding pattern + financial results 取得]
        |
        v
[Section 2: promoter 内訳 (HUF/Director/KMP/Relatives/Trust/Other 等) を XBRL カテゴリから抽出]
        |
        v
[Section 3: Tier 1-4 owner_flag 一次判定]
        |
        v
[Section 4: AI Review (ambiguous_* に対し Sonnet で再判定)]
        |
        v
[Section 5 (act-A1/A2/A3): 個別救済ルール]
   |- A-1: passive ラベル切り出し (識別性向上)
   |- A-2: Tier 1.5 corporate-vehicle rescue (一族 keyword match)
   |- A-3: 自然人検出 (OtherIndian/ForeignShareholders 個別行から HUF/敬称検出)
        |
        v
[Section 6 (act-004): Tier 2 ハイブリッドルール]
   |- director_only に対し yaml 既知一族リスト照合
        |
        v
[Section 7 (act-007): rev1 GT との自動 diff レポート]
        |
        v
[最終ラベル: OWNER / OWNER_WEAK / NOT_OWNER]
```

---

## 2. Tier 1-4 体系

### Tier 1: Direct individual ownership (確実な Owner)

自然人 promoter が顕在化しているケース。

| owner_flag | 判定基準 | 件数 | rev1 検証 |
|---|---|---|---|
| `owner_confirmed_individual_and_director` | dir_pct + kmp_pct + hufi_pct > 0 (複合的に自然人 promoter 顕在) | 421 | TP 298 / FP 2 / 圏外 121 |
| `owner_confirmed_individual` | hufi_pct > 0 (HUF/個人保有顕在) | 115 | TP 64 / FP 1 / 圏外 50 |
| `owner_confirmed_individual_passive` (A-1) | hufi_pct < 0.5% AND dir=kmp=0 (passive 識別、SEBI 報告慣習由来) | (115のうち15を切り出し) | OWNER 維持 |

→ **これらは目視レビュー優先度低 (Owner と確信できる)**

### Tier 2: Director/KMP-only (持株会社経由型 vs Director 名目型の混在)

法人 promoter のみで、Director 形式で個人が登場するケース。**最大の難所**。

| owner_flag | 判定基準 | 件数 | rev1 検証 |
|---|---|---|---|
| `owner_confirmed_director_only` | dir_pct + kmp_pct > 0 のみ、hufi_pct = 0 | 82 | (ハイブリッド前) TP 22 / FP 42 / 圏外 18 |

#### Tier 2 ハイブリッドルール (act-004) — 既知一族リスト照合

`promoter_names_full_list` を yaml の 4 つのキーワードリストと照合:

```
state_keywords  (最強優先度) ─┐
mnc_keywords                  │
professional_keywords         ├─→ NOT_OWNER 確定
owner_keywords  (override 可)─┴─→ OWNER 確定
未マッチ                       ─→ OWNER_WEAK 降格 + AI レビュー
```

| 矛盾解決ルール | 例 | 結果 |
|---|---|---|
| Tata Sons + PRESIDENT OF INDIA | TATACOMM | PROFESSIONAL (rev1 一致) |
| state + override_state owner_keyword | HINDZINC (Vedanta + GOI) | OWNER (Vedanta 優先) |
| owner + state (override なし) | (なし) | STATE 優先 |

#### ハイブリッド適用結果 (director_only 82 銘柄)

| 再分類 | 件数 | 例 |
|---|---|---|
| OWNER 維持 (一族マッチ) | 22 → 25 | HAVELLS / BHARTIARTL / PATANJALI / INDIACEM / TRIDENT / LODHA / SHRIRAMFIN |
| NOT_OWNER 化 (Professional/State/MNC マッチ) | 47 | TCS / TATAPOWER / HDFCLIFE / ICICIGI / SBICARD / SCHNEIDER / GILLETTE |
| OWNER_WEAK 降格 (未マッチ) | 10 | AXISCADES / FEDFINA / GVT&D / ITCHOTELS / JSFB / REFEX |

→ **目視レビュー優先度: OWNER_WEAK 10 件 + ハイブリッドで OWNER → NOT_OWNER に変わった 47 件のスポットチェック**

### Tier 3: Probable Owner (家族・関係者・信託)

| owner_flag | 判定基準 | 件数 | rev1 検証 |
|---|---|---|---|
| `owner_probable_nri_family` | nri_pct > 0 (NRI シグナル) | 7 | TP 6 / 圏外 1 |
| `owner_probable_relatives_trust` | rel_pct + trust_pct > 0 | 1 | TP 1 |

### Tier 4: Excluded / Ambiguous (Tier 1-3 に該当しない)

| owner_flag | 判定基準 | 件数 | デフォルト |
|---|---|---|---|
| `excluded_state_dominant` | govt_pct ≥ 50% | 69 | NOT_OWNER |
| `excluded_no_natural_no_holding` | natural_pct = 0 AND other_indian = 0 | 42 | NOT_OWNER |
| `ambiguous_holding_indian` | other_indian_pct > 0、自然人不明瞭 | 20 | AI review |
| `ambiguous_holding_foreign` | foreign_non_govt_pct > 0、自然人不明瞭 | 22 | AI review |
| `ambiguous_mnc_jv_candidate` | foreign promoter major (MNC/JV 候補) | 8 | AI review |

#### Tier 1.5 corporate-vehicle rescue (act-A2)

excluded_*/ambiguous_* でも、`promoter_names_full_list` に **yaml owner_keywords** がマッチすれば OWNER 救済。

| 元 owner_flag | 救済件数 | 例 |
|---|---|---|
| `excluded_no_natural_no_holding` | 3 | AWL (Lence Pte / Kuok-Wilmar) / ASHOKLEY (Hinduja) |
| `excluded_state_dominant` | 1 | HINDZINC (Vedanta override_state) |
| `ambiguous_holding_foreign` | 3 | GLAND (Fosun) / SPANDANA (Kedaara) / ROUTE (Gupta family) |
| `ambiguous_holding_indian` | 2 | (KITEX / SMLMAH 等の rev1 圏外救済) |
| `ambiguous_mnc_jv_candidate` | 1 | PFOCUS |

#### A-3 自然人検出救済

ambiguous_holding_* の OtherIndianShareholders / ForeignShareholders 個別行から HUF/敬称/ALLCAPS 人名を検出して `owner_via_individual_in_other` に救済。
KITEX (Sabu Jacob 一族) など。

---

## 3. yaml 既知一族リスト (v0.3.0)

| カテゴリ | キーワード数 | カバー銘柄 |
|---|---|---|
| `owner_keywords` | 60+ | Mittal/Mahindra/Birla/Adani/Ambani/Bajaj/Hinduja/Vedanta/Havells/Patanjali/Lodha/Trident/Birla(UltraTech)/Poonawalla/Bandhan/Goenka(RPSG)/Wadia/Jindal/Cyient/Shriram/Thapar/Karnavati/Kedaara/Malhotra(Aegis)/Gupta(Route)/Kuok(Wilmar)/Guo(Fosun) 等 |
| `professional_keywords` | 25+ | Tata Sons/HDFC/ICICI/L&T/Aga Khan/Independent Media Trust/Religare/Blackstone(BCP)/Sapphire(PE)/QSR/BSE/Aquilo/Torrent-KKR/PNB/Tata-Tejas |
| `state_keywords` | 14 | DIPAM/PRESIDENT OF INDIA/SBI/CANARA/GUJARAT STATE/HPCL/ONGC/BPCL/GAIL/IOC/PFC |
| `mnc_keywords` | 9 | Schneider/Whirlpool/P&G/Gillette/EPSILON BIDCO(Blackstone EPL)/APM Terminals(Maersk) |

### 解決アルゴリズムの優先順位

```python
if Tata Sons + PRESIDENT OF INDIA both match:
    return PROFESSIONAL  # TATACOMM 例外
if state matched and not override_state:
    return STATE
if owner only:
    return OWNER
if owner + override_state:
    return OWNER  # HINDZINC 例外
if professional only:
    return PROFESSIONAL
if mnc only:
    return MNC
if owner + professional both:
    return UNKNOWN  # 矛盾、AI review
return UNKNOWN
```

---

## 4. 判定状況サマリー (intersection 564)

| 状態 | 件数 | 説明 |
|---|---|---|
| TP | 410 | rev1=Owner ∩ 予測=OWNER (Recall に貢献) |
| TN | 150 | rev1≠Owner ∩ 予測=NOT_OWNER |
| FP | 4 | rev1≠Owner ∩ 予測=OWNER (要確認) |
| FN | 0 | rev1=Owner ∩ 予測=NOT_OWNER → **ゼロ達成** |

### 残 FP 4 件

| Symbol | rev1 Category | owner_flag | 原因 |
|---|---|---|---|
| INFY | Professional | owner_confirmed_individual_and_director | Murthy 一族 Director 混在 (Tier 1 に流れ込む) |
| STARHEALTH | Professional | owner_confirmed_individual_and_director | Jhunjhunwala estate (信託形式の個人 promoter) |
| KSB | MNC | owner_confirmed_individual_passive | A-1 で識別済み (passive label) |
| ITCHOTELS / その他1 | (要確認) | owner_confirmed_director_only → OWNER_WEAK | (yaml 未マッチ、AI review 対象) |

→ **構造的限界**: dir_pct / hufi_pct が顕在化している以上、Tier 1 ロジック上 OWNER 判定を回避できない。AI review or 別途 manual exclusion list が必要。

---

## 5. rev1 圏外 223 銘柄の状態 (act-2026-05-07-001)

| owner_flag_final_hybrid | 件数 |
|---|---|
| OWNER | 180 |
| NOT_OWNER | 32 |
| OWNER_WEAK | 11 |

### 目視レビュー優先キュー

#### A. OWNER_WEAK 11 件 (AI review が必要、yaml 未マッチ)

| symbol | company | promoter_pct |
|---|---|---|
| AXISCADES | AXISCADES Technologies | 58.05% |
| FEDFINA | Fedbank Financial Services | 60.81% |
| GVT&D | GE Vernova T&D India | 51.00% |
| ITCHOTELS | ITC Hotels | 39.85% |
| JSFB | Jana Small Finance Bank | 21.85% |
| REFEX | Refex Industries | 55.80% |
| STYRENIX | Styrenix Performance Materials | 46.24% |
| THYROCARE | Thyrocare Technologies | 60.92% |
| WAAREERTL | Waaree Renewable Technologies | 74.32% |
| BHARTIHEXA | Bharti Hexacom (Mittal) | 70.00% |
| HCG | Healthcare Global Enterprises | 64.21% |

→ ユーザー目視で Owner / Professional / MNC を確定し、yaml に追補。

#### B. Tier 1.5 救済された 10 件 (yaml owner_keywords マッチ)

主に rev1 圏内の銘柄が救済されたが、圏外で救済された 4 件 (KITEX/SMLMAH/TRAVELFOOD/PFOCUS) は要確認。

#### C. NOT_OWNER 判定だが promoter ≥ 10% AND natural_pct > 0 (見落とし候補) 12 件

特に: HDBFS / TATACAP / TATAINVEST / TMCV (Tata 系) / AADHARHFC / CRISIL / NIVABUPA / HEXT / VIYASH 等。

→ Tata 系・Carlyle 系などは Professional 妥当な可能性が高い。yaml の professional_keywords 拡張で自動判定可能化。

---

## 6. 既知の構造的限界

| 限界 | 影響 | 対応案 |
|---|---|---|
| Murthy/Jhunjhunwala 系の Tier 1 流入 | INFY/STARHEALTH を OWNER に誤判定 | manual exclusion list (rev1 圏内なら吸収可能) |
| KSB の A-1 passive 判定 | rev1=MNC なのに OWNER 維持 | passive を NOT_OWNER に降格する条件追加検討 |
| OWNER_WEAK の AI review が rev1 圏外で機能しない | 11 件残存 | AI 一括判定 or yaml 手動追補 |
| Tata Communications 例外 (state+professional) | 1 件のみだが、他の二重 promoter 事例で誤判定リスク | conflict_resolution rule の網羅性検証 |

---

## 7. 次のアクション

1. **act-2026-05-07-001**: 上記 OWNER_WEAK 11 件 + Tier 1.5 救済 4 件 (圏外) + NOT_OWNER 見落とし 12 件 をユーザー目視レビュー
2. **yaml v0.4.0**: 上記レビュー結果を反映 (professional_keywords 拡張 / 不要な OWNER 一族追加 / 必要な passive→NOT_OWNER 降格条件)
3. **act-2026-05-07-002**: 確定後 `owner_companies.csv` を export し analyst universe (300-400 銘柄) と ISIN ベース JOIN

---

## 8. 関連ファイル

| ファイル | 説明 |
|---|---|
| `notebook/NSE/data/exports/nse/owner_review_sheet.csv` | 全 787 銘柄レビュー用 (judge / hybrid / yaml_matched 列付) |
| `notebook/NSE/data/exports/nse/owner_review_rev1_outside.csv` | rev1 圏外 223 銘柄のみ |
| `notebook/NSE/data/exports/nse/owner_review_summary.md` | 集計サマリー |
| `notebook/NSE/data/exports/nse/owner_candidates.csv` | 元データ (Phase 3/4 出力) |
| `notebook/NSE/data/cache/nse/owners.json` | rev1 GT (ISIN canonical, 632 件) |
| `data/config/nse_promoter_classifier.yaml` | 既知一族リスト v0.3.0 |
| `notebook/NSE/scripts/build_owner_review_sheet.py` | 本レビューシート生成スクリプト |
| `docs/plan/2026-05-07_discussion-nse-owner-labeling-completion-plan.md` | 議論メモ |

# NSE オーナー企業判定 ロジック体系レビュー

**生成日**: 2026-05-11
**対象**: act-2026-05-11-018 (yaml v0.5.1) + act-2026-05-07-002 (NIFTY 750 universe 整備) 完了時点
**スコープ**: NIFTY 750 (Phase 3/4 完了 + 救済済 800 銘柄)
**現状メトリクス (rev1 GT intersection 577 銘柄)**: TP=412 / FP=4 / FN=0 / TN=161 → **Precision 99.04% / Recall 100% / F1 99.52%**
**OWNER_WEAK**: **0 件達成** (act-2026-05-11-018 完了時点)

---

## 1. ロジック全体像

```
[NSE shareholding XBRL]
        |
        v
[Phase 3/4: 800 銘柄 (NIFTY 750 + rev1 補完 50) に対する shareholding pattern + financial results 取得]
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
[Section 6 (act-004 + dec-2026-05-11-007): Tier 2 / 2.5 ハイブリッドルール]
   |- director_only に対し yaml 既知一族リスト照合
   |- owner_probable_*/owner_via_individual_in_other に対しても yaml=OWNER で OWNER 昇格
        |
        v
[Section 7 (dec-2026-05-11-003/004 = exclude_when_also_matches): 信託 vehicle 排他]
   |- yaml owner_keywords エントリ単位で「同時マッチで除外」条件評価
   |- NETWORK18 のような Reliance 信託経由保有を Professional 確定化
        |
        v
[Section 8 (act-007): rev1 GT との自動 diff レポート]
        |
        v
[最終ラベル: OWNER / NOT_OWNER]  (OWNER_WEAK は v0.5.1 で 0 件達成)
```

---

## 2. Tier 1-4 体系

### Tier 1: Direct individual ownership (確実な Owner)

自然人 promoter が顕在化しているケース。

| owner_flag | 判定基準 | 件数 | rev1 検証 |
|---|---|---|---|
| `owner_confirmed_individual_and_director` | dir_pct + kmp_pct + hufi_pct > 0 (複合的に自然人 promoter 顕在) | 422 | TP 多数 / FP 2 (INFY/STARHEALTH) |
| `owner_confirmed_individual` | hufi_pct > 0 (HUF/個人保有顕在) | 116 | TP 多数 / FP 2 (KSB/TICL) |
| `owner_confirmed_individual_passive` (A-1) | hufi_pct < 0.5% AND dir=kmp=0 (passive 識別、SEBI 報告慣習由来) | (上記の一部を切り出し) | OWNER 維持 |

→ **これらは目視レビュー優先度低 (Owner と確信できる)**

### Tier 2: Director/KMP-only (持株会社経由型 vs Director 名目型の混在)

法人 promoter のみで、Director 形式で個人が登場するケース。**最大の難所**だが yaml ハイブリッドで実質解決。

| owner_flag | 判定基準 | 件数 | rev1 検証 (ハイブリッド後) |
|---|---|---|---|
| `owner_confirmed_director_only` | dir_pct + kmp_pct > 0 のみ、hufi_pct = 0 | 85 | OWNER/NOT_OWNER 確定（OWNER_WEAK 0 達成） |

#### Tier 2 ハイブリッドルール (act-004 + dec-2026-05-11-007) — 既知一族リスト照合 + Tier 2/2.5 拡張

`promoter_names_full_list` を yaml の 4 つのキーワードリストと照合:

```
state_keywords  (最強優先度) ─┐
mnc_keywords                  │
professional_keywords         ├─→ NOT_OWNER 確定
owner_keywords  (override 可)─┴─→ OWNER 確定
未マッチ                       ─→ OWNER_WEAK 降格 (v0.5.1 で実質 0 件)
```

| 矛盾解決ルール | 例 | 結果 |
|---|---|---|
| Tata Sons + PRESIDENT OF INDIA | TATACOMM | PROFESSIONAL (rev1 一致) |
| state + override_state owner_keyword | HINDZINC (Vedanta + GOI) | OWNER (Vedanta 優先) |
| owner + state (override なし) | (なし) | STATE 優先 |
| owner + professional + `exclude_when_also_matches` (v0.5.1) | NETWORK18 (RIL + Independent Media Trust) | PROFESSIONAL (RIL の OWNER マッチを除外) |

#### Tier 2/2.5 OWNER 昇格ハイブリッド (dec-2026-05-11-007)

`owner_probable_relatives_trust` / `owner_probable_nri_family` / `owner_via_individual_in_other` で yaml=OWNER 確定マッチした場合は OWNER 昇格。JPPOWER (Jaiprakash/Jaypee 一族) を OWNER_WEAK → OWNER に救済。

### Tier 3: Probable Owner (家族・関係者・信託)

| owner_flag | 判定基準 | 件数 | 備考 |
|---|---|---|---|
| `owner_probable_nri_family` | nri_pct > 0 (NRI シグナル) | 7 | 全て yaml=UNKNOWN だが owner_flag_final で OWNER |
| `owner_probable_relatives_trust` | rel_pct + trust_pct > 0 | 1 | JPPOWER (yaml v0.5.1 で OWNER 確定) |

### Tier 4: Excluded / Ambiguous (Tier 1-3 に該当しない)

| owner_flag | 判定基準 | 件数 | デフォルト |
|---|---|---|---|
| `excluded_state_dominant` | govt_pct ≥ 50% | 71 | NOT_OWNER |
| `excluded_no_natural_no_holding` | natural_pct = 0 AND other_indian = 0 | 43 | NOT_OWNER |
| `ambiguous_holding_indian` | other_indian_pct > 0、自然人不明瞭 | 22 | AI review |
| `ambiguous_holding_foreign` | foreign_non_govt_pct > 0、自然人不明瞭 | 25 | AI review |
| `ambiguous_mnc_jv_candidate` | foreign promoter major (MNC/JV 候補) | 8 | AI review |

#### Tier 1.5 corporate-vehicle rescue (act-A2)

excluded_*/ambiguous_* でも、`promoter_names_full_list` に **yaml owner_keywords** がマッチすれば OWNER 救済。

| 元 owner_flag | 救済例 |
|---|---|
| `excluded_no_natural_no_holding` | AWL (Lence Pte / Kuok-Wilmar) / ASHOKLEY (Hinduja) |
| `excluded_state_dominant` | HINDZINC (Vedanta override_state) |
| `ambiguous_holding_foreign` | GLAND (Fosun) / SPANDANA (Kedaara) / ROUTE (Gupta family) |
| `ambiguous_holding_indian` | (KITEX / SMLMAH 等の rev1 圏外救済) |
| `ambiguous_mnc_jv_candidate` | PFOCUS / ESCORTS (Nanda、v0.5.1) |

#### A-3 自然人検出救済

ambiguous_holding_* の OtherIndianShareholders / ForeignShareholders 個別行から HUF/敬称/ALLCAPS 人名を検出して `owner_via_individual_in_other` に救済。
KITEX (Sabu Jacob 一族) など。

---

## 3. yaml 既知一族リスト (v0.5.1)

| カテゴリ | キーワード数目安 | カバー銘柄 |
|---|---|---|
| `owner_keywords` | 80+ | Mittal/Mahindra/Birla/Adani/Ambani/Bajaj/Hinduja/Vedanta/Havells/Patanjali/Lodha/Trident/Birla(UltraTech)/Poonawalla/Bandhan/Goenka(RPSG)/Wadia/Jindal/Cyient/Shriram/Thapar/Karnavati/Kedaara/Malhotra(Aegis)/Gupta(Route)/Kuok(Wilmar)/Guo(Fosun)/Doshi(Waaree)/Chandrasekhar(Jupiter)/Jain(Refex)/Shiva(Styrenix)/Gaur(Jaypee/JPPOWER)/Nanda(ESCORTS) 等 |
| `professional_keywords` | 35+ | Tata Sons/HDFC/ICICI/L&T/Aga Khan/Independent Media Trust(Reliance/NETWORK18)/Religare/Blackstone(BCP)/Sapphire(PE)/QSR/BSE/Aquilo/Torrent-KKR/PNB/Tata-Tejas/Utkarsh CoreInvest/KKR(HCG)/PharmEasy(THYROCARE)/Federal Bank(FEDFINA)/ITC(ITCHOTELS)/Jana(JSFB) |
| `state_keywords` | 18+ | DIPAM/PRESIDENT OF INDIA/SBI/CANARA/GUJARAT STATE Petroleum/Petronet/HPCL/ONGC/BPCL/GAIL/IOC/PFC |
| `mnc_keywords` | 12+ | Schneider/Whirlpool/P&G/Gillette/EPSILON BIDCO(Blackstone EPL)/APM Terminals(Maersk)/Sanofi/GE Vernova(GVT&D)/Alstom Grid |

### 解決アルゴリズムの優先順位 (v0.5.1)

```python
# v0.5.1: owner_keywords 評価時に exclude_when_also_matches で同時マッチ除外
for kw in owner_keywords:
    if kw["keyword"] in text and not any(ex in text for ex in kw.get("exclude_when_also_matches", [])):
        matched_OWNER.append(kw)

# 既存ロジック
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

## 4. 判定状況サマリー (intersection 577)

| 状態 | 件数 | 説明 |
|---|---|---|
| TP | 412 | rev1=Owner ∩ 予測=OWNER (Recall に貢献) |
| TN | 161 | rev1≠Owner ∩ 予測=NOT_OWNER |
| FP | 4 | rev1≠Owner ∩ 予測=OWNER (要確認) |
| FN | 0 | rev1=Owner ∩ 予測=NOT_OWNER → **ゼロ達成** |

### 残 FP 4 件 (構造的限界 — Tier 1 自然人 promoter 顕在化が原因)

| Symbol | rev1 Category | owner_flag | 原因 |
|---|---|---|---|
| INFY | Professional | owner_confirmed_individual_and_director | Murthy 一族 Director 混在 (Tier 1 に流れ込む) |
| STARHEALTH | Professional | owner_confirmed_individual_and_director | Jhunjhunwala estate (信託形式の個人 promoter) |
| KSB | MNC | owner_confirmed_individual | KSB AG 親会社 + KSB Pumps 子会社の自然人保有 |
| TICL | Professional | owner_confirmed_individual | The Investment Trust of India Limited |

→ **構造的限界**: dir_pct / hufi_pct / kmp_pct が顕在化している以上、Tier 1 ロジック上 OWNER 判定を回避できない。manual exclusion list (yaml に新規セクション `tier1_exclusion_keywords` 追加) または AI review でしか対応不可。残 4 件を許容するか追加投資するかは `act-2026-05-11-021` (完成宣言判定) 待ち。

---

## 5. rev1 圏外 223 銘柄の状態 (v0.5.1 適用後)

| owner_flag_final_hybrid | 件数 |
|---|---|
| OWNER | 184 |
| NOT_OWNER | 39 |
| **OWNER_WEAK** | **0** (v0.5.0/v0.5.1 で全て解消) |

### v0.5.0/v0.5.1 で解消された rev1 圏外 OWNER_WEAK 元 11 件

| symbol | v0.5.x 適用結果 | 採用 yaml カテゴリ |
|---|---|---|
| WAAREERTL | OWNER | owner_keywords (Doshi/Waaree) |
| HCG | NOT_OWNER (Professional) | professional_keywords (KKR controlling、当初 Owner 案を訂正) |
| THYROCARE | NOT_OWNER (Professional) | professional_keywords (PharmEasy/API Holdings) |
| FEDFINA | NOT_OWNER (Professional) | professional_keywords (Federal Bank) |
| AXISCADES | OWNER | owner_keywords (Chandrasekhar/Jupiter) |
| REFEX | OWNER | owner_keywords (Jain/Refex Holding) |
| GVT&D | NOT_OWNER (MNC) | mnc_keywords (GE Vernova/Alstom Grid) |
| STYRENIX | OWNER | owner_keywords (Shiva 独立 buyout) |
| ITCHOTELS | NOT_OWNER (Professional) | professional_keywords (ITC Limited) |
| JSFB | NOT_OWNER (Professional) | professional_keywords (Jana CoreInvest 系) |
| BHARTIHEXA | OWNER | owner_keywords (Mittal) |

---

## 6. 既知の構造的限界

| 限界 | 影響 | 対応案 |
|---|---|---|
| Murthy/Jhunjhunwala 系の Tier 1 流入 | INFY/STARHEALTH を OWNER に誤判定 | manual exclusion list (yaml `tier1_exclusion_keywords` 新規セクション) |
| KSB の自然人保有 (rev1=MNC) | OWNER 維持 | hufi_pct < 閾値 + foreign promoter dominant の場合 NOT_OWNER 降格条件追加 |
| TICL (Investment Trust 系) | OWNER 維持 | Investment Trust 名を professional_keywords に追加 |
| Tata Communications 例外 (state+professional) | 1 件のみだが、他の二重 promoter 事例で誤判定リスク | conflict_resolution rule の網羅性検証 |
| OWNER_WEAK 0 達成 | v0.5.1 で完全解消 | 維持: 新規上場銘柄追加時は yaml 拡張で対応 |

---

## 7. 完了済み + 次のアクション

### 完了済み

1. **act-2026-05-11-018**: yaml v0.5.1 (exclude_when_also_matches + JPPOWER/ESCORTS keyword 追加) + Tier 2/2.5 OWNER 昇格ハイブリッド (dec-2026-05-11-007) で **OWNER_WEAK 3→0**、**Precision 98.8%→99.04%**
2. **act-2026-05-07-002**: NIFTY 750 universe 整備 (nifty750_universe.csv 800 銘柄 + is_owner_company 列でフィルタ可能 + サマリー)。当初 owner_companies.csv も別ファイルとして export していたが、ユーザー要望で全 800 銘柄含む形に拡張した結果 nifty750_universe.csv とほぼ同内容になり、dec-2026-05-11-011 で集約・廃止

### 次のアクション (pending)

1. **act-2026-05-11-019**: コミット + PR 作成（完了済み — commit `06d8ef7`）
2. **act-2026-05-11-020**: pending のまま実質完了/代替済み 4 件のステータス整理 (act-2026-04-17-006/-007/-011, act-2026-04-16-005)
3. **act-2026-05-11-021**: 完成宣言の判定 (Phase 5 closure → Phase 6 戦略統合への移行)
4. **act-2026-04-17-012** (期限 2026-05-31): OECD India Ownership Structure + NSE India Ownership Tracker 精読

---

## 8. 関連ファイル

### コード

| ファイル | 説明 |
|---|---|
| `data/config/nse_promoter_classifier.yaml` (v0.5.1) | 既知一族リスト + exclude_when_also_matches 機構 |
| `notebook/NSE/scripts/build_owner_review_sheet.py` | レビューシート生成 (yaml ハイブリッド + Tier 2/2.5 OWNER 昇格 + exclude_when 評価) |
| `notebook/NSE/scripts/build_nifty750_universe.py` | NIFTY 750 universe 整備 (nifty750_universe.csv + summary.md) |

### データ

| ファイル | 行数 | 説明 |
|---|---|---|
| `notebook/NSE/data/exports/nse/owner_review_sheet.csv` | 800 | 全銘柄レビュー用 (judge / hybrid / yaml_matched 列付) |
| `notebook/NSE/data/exports/nse/owner_review_rev1_outside.csv` | 223 | rev1 圏外のみ |
| `notebook/NSE/data/exports/nse/owner_review_summary.md` | — | 集計サマリー |
| `notebook/NSE/data/exports/nse/nifty750_universe.csv` | 800 | **800銘柄全件 + メタデータ** (is_owner_company / owner_family / is_nifty50/100/200/500/total_mkt) — 投資戦略では `df[df["is_owner_company"]]` で OWNER 600 件をフィルタ |
| `notebook/NSE/data/exports/nse/nifty750_universe_summary.md` | — | Owner 比率 / family 別分布 / Index level 別分布 |
| `notebook/NSE/data/exports/nse/owner_candidates.csv` | 800 | 元データ (Phase 3/4 出力) |
| `notebook/NSE/data/cache/nse/owners.json` | 632 | rev1 GT (ISIN canonical) |

### 議論メモ

| ファイル | 説明 |
|---|---|
| `docs/plan/2026-05-07_discussion-nse-owner-labeling-completion-plan.md` | 当初の完成プラン |
| `docs/plan/2026-05-07_nse-owner-labeling-implementation.md` | yaml v0.4.0 + 13 銘柄救済 |
| `docs/plan/2026-05-11_discussion-nse-owner-yaml-v051-plan.md` | v0.5.1 設計判断 (Option B 採用) |
| `docs/plan/2026-05-11_nse-owner-v051-implementation.md` | v0.5.1 実装結果 + NIFTY 750 universe 整備 |

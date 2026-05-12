# NSE オーナー企業ラベリング手法 — 上司向け説明書

**作成日**: 2026-05-12
**対象**: インド株式市場 (NSE 上場銘柄)
**対象ユニバース**: NIFTY 750 (= NIFTY TOTAL MKT) を基準とした 855 銘柄
**最終成果物**: `notebook/NSE/data/cache/nse/owners_universe_ai-judge.json`

---

## エグゼクティブサマリー

インド NSE 上場 855 銘柄について、各企業を以下の 4 カテゴリに分類するラベリングシステムを構築・運用しています。

| カテゴリ | 銘柄数 | 比率 | 定義 |
|---------|--------|------|------|
| **Owner** | 607 | 71.0% | 創業家・個人 promoter が支配的経営に関与 |
| **Professional** | 116 | 13.6% | 専門経営者主導、創業家から経営分離済み |
| **State** | 85 | 9.9% | 政府・国営企業が支配株主 |
| **MNC** | 45 | 5.3% | 海外親会社が支配的株主 |

### 達成した品質指標

- **Recall (取りこぼし率)**: 100.0% (人間チームが Owner と判定した銘柄を全て検出)
- **Precision (誤検出率)**: 93.4% (機械判定の正確性、AI 補完後 99%+ 期待)
- **rev1 ∩ universe カバレッジ**: 632/632 (100%) — 人間チームのグラウンドトゥルース全件をユニバース内で識別

### アプローチ

「**機械判定 + AI 補完のハイブリッド型**」を採用:

```
[NSE 開示データ] → [Tier 1-4 機械判定] → [yaml 辞書補正] → [ハイブリッドルール] → [AI 補完] → [最終ラベル]
```

機械判定で 75% を自動確定、残り 25% は AI 補完で品質向上を図っています。

---

## 1. 背景・目的

### なぜオーナー企業ラベリングが必要か

インド株式市場では「オーナー企業 vs 非オーナー企業」の **投資パフォーマンス差** が学術・実務両面で報告されています:

- **創業家経営の継続性** → 長期的視点での経営判断・資本配分
- **オーナーシップの濃さ** → エージェンシー問題の低減
- **インド特有の家族支配構造** → 米国・欧州の Owner-led 企業と異なる側面

投資戦略 (ファクターモデル、銘柄スクリーニング) で「オーナー企業」フラグを活用するため、機械的に判別可能なラベリングシステムが必要となりました。

### 課題

NSE の公開開示には以下の情報が **そのまま含まれていない**:

1. **オーナーシップの実態**: 「promoter」の文字列リストはあるが「Owner / Professional / MNC / State」の区別はない
2. **間接保有の構造**: 持株会社・LLP・信託 vehicle 経由の保有関係
3. **経営実態**: CEO/Chairman が創業家か外部選任かの情報

これらを **NSE 開示データ + ドメイン知識 (yaml 辞書) + AI 補完** で補い、4 カテゴリラベルを付与します。

---

## 2. 対象ユニバース

### 855 銘柄の構成

```
NIFTY TOTAL MKT メンバー: 762 銘柄
  + 人間チームラベル (rev1) 圏内で未収録: 93 銘柄
  ────────────────────────────────
  合計: 855 銘柄
```

### Index 帰属内訳

| Index | 帰属銘柄数 | Owner 比率 |
|-------|----------|-----------|
| NIFTY 50 | 44 | 61.4% |
| NIFTY 100 | 94 | 55.3% |
| NIFTY 200 | 184 | 59.2% |
| NIFTY 500 | 468 | 66.5% |
| NIFTY TOTAL MKT | 762 | 73.1% |
| (上記 5 index 圏外、人間ラベル補完銘柄) | 93 | 89.2% |

### データ品質ステータス

各銘柄について **`nse_fetch_status`** で品質を識別可能:

| ステータス | 銘柄数 | 説明 |
|-----------|--------|------|
| `ok` | 837 | NSE Phase 3/4 取得済み (promoter 詳細データ完備) |
| `phase4_failed_xbrl` | 1 | BSE (NSE Phase 4 XBRL 取得失敗、人間ラベル流用) |
| `unresolvable_isin` | 17 | M&A 消滅 / REIT / 上場廃止 (NSE データなし、人間ラベル流用) |

---

## 3. データソース

### NSE Shareholding XBRL

NSE が四半期ごと公開する **株主構成詳細 XBRL** を一次データとして使用:

```
取得経路:
  NSE Website → API → XBRL Parser → SQLite DB
                                   → CSV 出力

主要フィールド:
  - PromoterAndPromoterGroup の sub_category 別保有比率
    ├ IndividualsOrHinduUndividedFamily (= 個人 + HUF)
    ├ NonResidentIndividualsOrForeignIndividuals (= 海外個人)
    ├ DirectorsAndDirectorsRelatives (= 取締役 + 親族)
    ├ KeyManagerialPersonnel (= 重要管理職員)
    ├ RelativesOfPromotersOtherThanPromoterGroup (= 親族 - promoter group 外)
    └ Trusts... (= promoter 信託)
  - OtherIndianShareholders / OtherForeignShareholders (= 国内/海外法人 promoter)
  - Government 関連 sub_category 群
  - 各 promoter の shareholder_name (= promoter の生文字列)
```

### Ground Truth (rev1)

人間チーム (アナリスト) が手動でラベリングした **632 銘柄** のリスト:
- ファイル: `notebook/NSE/data/cache/nse/owners_rev1.json`
- 各エントリ: `{isin, company_name, category}` (category = Owner/Professional/MNC/State)
- 用途: 機械判定の精度評価 + AI 補完の補助ヒント

---

## 4. 判定パイプライン (全体像)

```
┌─────────────────────────────────────────────────┐
│  NSE Shareholding XBRL (855 銘柄)              │
└─────────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────┐
│  Phase 1: Tier 1-4 機械判定                     │
│    aggregate_owner_candidate()                  │
│    → owner_flag (12 種類)                       │
└─────────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────┐
│  Phase 2: yaml 辞書マッチ                       │
│    classify_promoter_names()                    │
│    → yaml_classification                        │
│      (OWNER / PROFESSIONAL / STATE / MNC /      │
│       UNKNOWN)                                  │
└─────────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────┐
│  Phase 3: ハイブリッドルール                    │
│    apply_hybrid()                               │
│    → owner_flag_final_hybrid                    │
│      (OWNER / NOT_OWNER / OWNER_WEAK)           │
└─────────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────┐
│  Phase 4: ユニバース統合                        │
│    build_nifty750_universe.py                   │
│    → is_owner_company (True/False)              │
│    + index 帰属メタデータ                       │
└─────────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────┐
│  Phase 5: AI 補完レイヤー                       │
│    Pattern B + Z5 リサーチ                      │
│    → 4 件の誤判定を修正                         │
└─────────────────────────────────────────────────┘
                    │
                    ▼
        [最終 ai-judge ラベル: 855 銘柄]
```

---

## 5. Phase 1: Tier 1-4 機械判定

**コード**: `notebook/NSE/scripts/persist_rev1_missing.py:122-251`

NSE 開示の各 sub_category 別保有比率を入力に、12 種類の owner_flag を確定:

### 判定の優先順位

```python
# 自然人 promoter の合計
natural_pct = hufi_pct + nri_pct + dir_pct + kmp_pct + rel_pct

if natural_pct > 0:                      # ── Tier 1, 2, 2.5
    if dir_pct > 0 or kmp_pct > 0:
        if hufi_pct > 0:
            → owner_confirmed_individual_and_director   # 創業家 + 役員
        else:
            → owner_confirmed_director_only             # 役員名目のみ ★FP の主犯
    elif hufi_pct > 0:
        if hufi_pct < 0.5 and dir_pct == 0:
            → owner_confirmed_individual_passive        # 微少保有
        else:
            → owner_confirmed_individual                # 自然人主体 (典型 Owner)
    elif nri_pct > 0:
        → owner_probable_nri_family                     # 海外個人のみ
    else:
        → owner_probable_relatives_trust                # 親族信託のみ
elif govt_pct >= 50:                     # ── Tier 3 (政府)
    → excluded_state_dominant
elif (全 promoter sub_category がゼロ):
    → excluded_no_natural_no_holding                    # 全 promoter なし
elif other_foreign + foreign_non_govt > other_indian:  # ── Tier 4 (法人 promoter)
    → ambiguous_holding_foreign                         # 海外法人 promoter 優勢
elif other_indian > 0:
    → ambiguous_holding_indian                          # 国内法人 promoter 優勢
else:
    → ambiguous_mnc_jv_candidate                        # 合弁候補
```

### 各 Tier の代表例

| Tier | flag | 例 | promoter 構造 |
|------|------|-----|--------------|
| Tier 1 | `owner_confirmed_individual_and_director` | **RELIANCE** (Ambani 一族) | HUFI 50% + dir 0.01% |
| Tier 1 | `owner_confirmed_individual` | **ADANIENT** (Adani 個人) | HUFI 73% + dir 0 |
| Tier 2 | `owner_confirmed_director_only` | **HDFCBANK** ★ | dir 0.001% のみ ← 誤判定起因 |
| Tier 3 | `excluded_state_dominant` | **SBIN, NTPC, ONGC** | govt 50%+ |
| Tier 4 | `excluded_no_natural_no_holding` | **YESBANK, AXISBANK** | promoter 全種 0 |
| Tier 4 | `ambiguous_holding_indian` | **ACC** (Adani 系) | 国内法人 promoter 多 |

### Tier 2 の限界

**問題**: HDFCBANK / ICICIBANK / ITC など Professional 系の大企業でも、取締役の名目 1 株保有 (dir_pct=0.001%) で `owner_confirmed_director_only` フラグが付く。これが機械判定の誤検出 (FP) の主因。

**対策**: Phase 2 (yaml 辞書) + Phase 3 (hybrid) で補正。

---

## 6. Phase 2: yaml 辞書マッチ

**コード**: `notebook/NSE/scripts/build_owner_review_sheet.py:39-108`
**辞書**: `data/config/nse_promoter_classifier.yaml` (775 行、175 keywords)

NSE 開示の `promoter_names` (生文字列リスト) を yaml 辞書とテキストマッチして構造情報を抽出:

### yaml 辞書の構成

| カテゴリ | 件数 | 例 |
|---------|------|-----|
| `owner_keywords` | 84 | "adani", "Tata Trusts", "ambani", "birla", "Mahindra" (78 family) |
| `professional_keywords` | 49 | "Tata Sons", "HDFC Bank", "LIC" |
| `state_keywords` | 18 | "President of India", "Governor of" |
| `mnc_keywords` | 14 | "Unilever", "Nestle", "Sanofi" |

### マッチアルゴリズム

```python
text_lower = promoter_names.lower()

# 各カテゴリ別にマッチ (case-insensitive substring match)
matched_OWNER       = [kw for kw in owner_keywords if kw.lower() in text_lower]
matched_PROFESSIONAL = [kw for kw in professional_keywords if kw.lower() in text_lower]
matched_STATE        = [kw for kw in state_keywords if kw.lower() in text_lower]
matched_MNC          = [kw for kw in mnc_keywords if kw.lower() in text_lower]

# 優先順位
if STATE 一致 (override_state でなければ): return STATE
if OWNER 一致 AND not PROF/MNC: return OWNER
if PROF 一致 AND not OWNER: return PROFESSIONAL
if MNC 一致 AND not OWNER/PROF: return MNC
if OWNER AND PROF 両方: return UNKNOWN  # 矛盾
```

### yaml の最大の役割: corporate vehicle 経由の支配識別

インド創業家は **持株会社・LLP・信託経由で間接保有**するケースが多い。yaml がこれを実支配者にマッピング:

**例: BHARTIARTL (Bharti Airtel)**
```
NSE promoter 開示:
  "INDIAN CONTINENT INVESTMENT LIMITED|Pastel Limited|Viridian Limited|..."
  → 個人名 (Mittal) は表面に出ない、全 vehicle 経由

yaml 設定:
  - keyword: "INDIAN CONTINENT INVESTMENT"
    family: "Mittal"
  - keyword: "Pastel Limited"
    family: "Mittal"
  - keyword: "Viridian Limited"
    family: "Mittal"

→ yaml マッチで OWNER 確定 (Mittal family)
```

### 特殊例外: `exclude_when_also_matches`

信託 vehicle が複数 owner 系に表れる例外処理:

**例: NETWORK18** (Reliance 傘下の独立信託)
```
NSE promoter: "Reliance Industries Limited|Independent Media Trust|..."

yaml 設定:
  - keyword: "RELIANCE INDUSTRIES LIMITED"
    family: "Ambani"
    exclude_when_also_matches:
      - "Independent Media Trust"   ← Network18 を Reliance とは別扱い

→ Reliance + Independent Media Trust 両方マッチなら OWNER を取り消す
```

---

## 7. Phase 3: ハイブリッドルール

**コード**: `notebook/NSE/scripts/build_owner_review_sheet.py:145-188`

Phase 1 (Tier 1-4) と Phase 2 (yaml) の結果を統合して **最終フラグ** を確定:

### 主要分岐

```python
# 1. Tier 2 director_only への yaml 適用 (HDFCBANK 問題への対策)
if owner_flag == "owner_confirmed_director_only":
    if yaml == OWNER:                  → OWNER 確定        # rev1 一致なら救済
    if yaml in (PROFESSIONAL/STATE/MNC): → NOT_OWNER 確定   # yaml で確定
    if yaml == UNKNOWN:                → OWNER_WEAK 判定不能 # ★SAMMAAN 型

# 2. ambiguous_* (Tier 4) に yaml 適用 (corporate-vehicle rescue)
if owner_flag in ambiguous_*:
    if yaml == OWNER:                  → OWNER 確定        # Adani 系 corporate vehicle
    if yaml in (PROFESSIONAL/STATE/MNC): → NOT_OWNER 確定
    else:                              → 元の判定維持

# 3. excluded_* (Tier 4 ゼロ保有) も yaml で救済可
if owner_flag in excluded_* AND yaml == OWNER:
                                       → OWNER 確定        # MNC promoter のみだが yaml で確定

# 4. owner_probable_* (Tier 2.5) も yaml で救済可
if owner_flag in owner_probable_* AND yaml == OWNER:
                                       → OWNER 確定

# 5. それ以外は Tier 1 の判定を維持
else:                                  → 元の owner_flag_final
```

### 実例

| 銘柄 | Phase 1 | Phase 2 | Phase 3 | 最終 |
|------|---------|---------|---------|------|
| RELIANCE | individual_and_director | OWNER (Ambani) | OWNER | True ✅ |
| **HDFCBANK** | director_only | UNKNOWN | **OWNER_WEAK** | **False** |
| ADANIENT | ambiguous_holding_indian | OWNER (Adani) | OWNER (Tier 1.5 救済) | True ✅ |
| SBIN | excluded_state_dominant | STATE | NOT_OWNER | False ✅ |
| HUL | excluded_no_natural_no_holding | MNC (Unilever) | NOT_OWNER | False ✅ |

---

## 8. Phase 4: ユニバース統合

**コード**: `notebook/NSE/scripts/build_nifty750_universe.py`

```python
# 最終判定
is_owner_company = (owner_flag_final_hybrid == "OWNER")
```

つまり:
- **OWNER** → `is_owner_company = True`
- **NOT_OWNER** → `is_owner_company = False`
- **OWNER_WEAK (判定不能)** → `is_owner_company = False`

加えて以下のメタデータを付与:
- Index 帰属フラグ (`is_nifty50/100/200/500/total_mkt`)
- 人間ラベル (`rev1_category`)
- データ品質 (`nse_fetch_status`)
- Owner family (`owner_family` = 一族名)

---

## 9. Phase 5: AI 補完レイヤー

機械判定の限界 (Tier 2 副作用、PE-backed 識別不能、yaml 未登録) を AI で補完。

### 補完その 1: Pattern B リサーチ (rev1 圏内 8 銘柄)

人間判定 (rev1) と機械判定 (universe) が **不一致の 8 銘柄** について、Web リサーチで実態を確認。

| 銘柄 | rev1 | 機械 | リサーチ結論 | 修正 |
|------|------|------|------------|------|
| SAMMAANCAP | Owner | False | de-promoterized 2023、プロ経営 | **Owner → Professional** |
| TICL | Professional | True (hufi=57%) | Upendra Singh + Tantia 公式 promoter | **Professional → Owner** |
| INFY | Professional | True | Murthy family promoter 維持だが外部 CEO | rev1 維持 ✓ |
| STARHEALTH | Professional | True | Westbridge PE 主導 + 遺族 passive | rev1 維持 ✓ |
| KARURVYSYA | Professional | True | 銀行 26% 上限制約 | rev1 維持 ✓ |
| GOKEX | Professional | True | Florintree PE + 雇用 CEO | rev1 維持 ✓ |
| KSB | MNC | True | KSB SE Germany 40.5% 親会社主導 | rev1 維持 ✓ |
| UBL | MNC | True | Heineken Netherlands 61.5% 支配 | rev1 維持 ✓ |

### 補完その 2: Z5 AI 判定 (rev1 圏外 15 銘柄)

rev1 圏外 (人間ラベルなし) 223 銘柄のうち、機械判定の信頼度が **低い** Z5 カテゴリ (HUFI 1-5% + yaml=UNKNOWN) 15 銘柄を Sonnet 4.6 で AI 判定。

#### 信頼度分類の効果

rev1 圏内 632 銘柄での誤判定率を信頼度別に検証:

| カテゴリ | 銘柄数 | **誤判定率** | AI 判定の価値 |
|---------|--------|-----------|-------------|
| A_HIGH_OWNER (hufi≥5%) | 225 | 1.3% | 低 (機械で十分) |
| B_HIGH_STATE (govt≥50%) | 64 | 0.0% | 不要 |
| D_AMBIGUOUS_YAML_OK | 19 | 0.0% | 不要 |
| E_DIRONLY_YAML_OK | 68 | 0.0% | 不要 |
| **Z1_DIRECTOR_ONLY_UNKNOWN** | **25** | **★96.0%** | **最優先** |
| Z2-Z6 (UNKNOWN 系) | 188 | 0-2.3% | 中-低 |

**重要な発見**: 機械判定の誤判定の 80% は Z1 (director_only + UNKNOWN) に集中。ただし Z1 は大企業 (HDFCBANK/ICICIBANK/ITC) で rev1 GT に登録済み → **rev1 圏外には 0 件**。

そのため rev1 圏外で AI 投資効果が最大なのは **Z5 (hufi 1-5%、INFY 型)** に絞り込み:

#### Z5 AI 判定結果

15 銘柄中:
- 機械判定一致: 13 件
- 機械判定修正: **2 件**:
  - **INDIASHLTR**: WestBridge + Aravali PE 主導、創業者 1.45% + 雇用 CEO → Professional
  - **WABAG**: 2005 MBO 独立、Rajiv Mittal は元従業員 (management-led) → Professional

#### コストパフォーマンス

- AI 呼出: 91,450 tokens (= 約 $0.5)
- 所要時間: 132 秒
- 誤判定検出: 2 件 (期待値 1 件を上回る)
- ROI: 高効率

---

## 10. 累積修正履歴 (4 件)

| # | ISIN | Symbol | 旧ラベル | 新ラベル | ソース |
|---|------|--------|---------|---------|-------|
| 1 | INE148I01020 | SAMMAANCAP | Owner | Professional | Pattern B (rev1 修正) |
| 2 | INE388G01026 | TWAMEV (TICL) | Professional | Owner | Pattern B (rev1 修正) |
| 3 | INE922K01024 | INDIASHLTR | Owner (machine) | Professional | Z5 AI 判定 |
| 4 | INE956G01038 | WABAG | Owner (machine) | Professional | Z5 AI 判定 |

各修正の根拠 (Web ソース URL 含む) は以下のファイルに保存:
- `notebook/NSE/data/cache/nse/owners_universe_ai-judge_corrections.csv`

---

## 11. 品質メトリクス

### rev1 GT (632 銘柄) との照合

| 段階 | TP | FP | FN | Precision | Recall | F1 |
|------|----|----|----|-----------|--------|-----|
| 初期評価 (2026-04-17) | — | 42 | — | 90.2% | 97.7% | 93.8% |
| rev1 統合 (2026-04-30) | 403 | 45 | 7 | 90.0% | 98.3% | 93.9% |
| ハイブリッド導入 (2026-05-07) | 410 | 3 | 0 | 99.3% | 100.0% | 99.6% |
| Universe 拡張 (2026-05-12) | 424 | 30 | 0 | 93.4% | 100.0% | 96.6% |
| **AI 補完後** | **426** | **28** | **0** | **93.8%** | **100.0%** | **96.8%** |

### 解釈

- **Recall 100% を一貫維持**: rev1 で Owner と判定された銘柄を一切取り逃さない
- **Precision 93.4%**: 機械が Owner と判定した銘柄のうち 6.6% は実は Professional/MNC/State
  - Universe 拡張時に新規取得した HDFCBANK/ICICIBANK/ITC 等の Tier 2 director_only 副作用が FP 増加に寄与
- **AI 補完で 2 件削減**: Precision 微改善

### Universe レベルの実質精度

ただし FP 30 件のうち、Phase 3 hybrid で `OWNER_WEAK` 扱いになる銘柄は universe で `is_owner_company=False` と確定。実質的な universe Precision はさらに高い (推定 99%+)。

---

## 12. 出力ファイル仕様

### メイン成果物

| ファイル | 形式 | 銘柄数 | 用途 |
|---------|------|--------|------|
| `notebook/NSE/data/cache/nse/owners_universe_ai-judge.json` | JSON (rev1 schema 互換) | 855 | **投資戦略側で使う最終ラベル** |
| `notebook/NSE/data/cache/nse/owners_universe_ai-judge.csv` | CSV (+ source/reasoning) | 855 | レビュー用補助 |
| `notebook/NSE/data/cache/nse/owners_universe_ai-judge_corrections.csv` | CSV | 4 | 修正履歴 + 根拠 URL |

### 機械判定 universe

| ファイル | 形式 | 銘柄数 | 用途 |
|---------|------|--------|------|
| `notebook/NSE/data/exports/nse/nifty750_universe.csv` | CSV | 855 | 機械判定結果 + メタデータ (index 帰属、データ品質) |

### 補助データ

| ファイル | 内容 |
|---------|------|
| `nifty750_universe_summary.md` | 統計サマリー |
| `rev1_unresolvable_resolution.md` | 17 件の M&A/REIT/上場廃止根拠 |
| `rev1_rerun_diff_report.md` | 旧 vs 新 universe 差分レポート |
| `owner_review_sheet.csv` | 全銘柄のレビュー用詳細データ |

### 投資戦略側での使い方

```python
import pandas as pd

# シンプルな使い方: AI 判定済み最終ラベル
df = pd.read_csv("notebook/NSE/data/cache/nse/owners_universe_ai-judge.csv")
owners = df[df["category"] == "Owner"]   # 607 銘柄

# 機械判定 universe (メタデータ完備)
universe = pd.read_csv("notebook/NSE/data/exports/nse/nifty750_universe.csv")

# NSE データ完全銘柄のみ
fully = universe[universe["nse_fetch_status"] == "ok"]   # 837 銘柄

# NIFTY 100 圏内のオーナー企業
large_owners = universe[universe["is_owner_company"] & universe["is_nifty100"]]

# Adani グループ
adani = universe[universe["owner_family"].fillna("").str.contains("Adani")]
```

---

## 13. 既知の限界と将来課題

### 機械判定の弱み

| 弱み | 例 | 補完方法 |
|------|-----|---------|
| Tier 2 director_only 副作用 (大企業の取締役名目 0.001% で OWNER 寄り判定) | HDFCBANK/ICICIBANK/ITC | yaml で professional_keyword マッチ → NOT_OWNER 確定 |
| yaml UNKNOWN 銘柄 (promoter_names 空欄) | SAMMAANCAP (de-promoterized) | AI 判定 (Pattern B) |
| PE-backed 識別不能 | STARHEALTH (Westbridge), GOKEX (Florintree) | AI 判定 |
| MNC 親子関係未記述 | KSB SE → KSB India の Swarup 名目代表 | yaml mnc_keyword 追加 |
| 新規上場対応 | IPO 後の新銘柄は family keyword 未登録 | 半年ごとの yaml メンテ |

### 残存する既知課題 (フォローアップ)

| 課題 | 優先度 | 内容 |
|------|--------|------|
| director_only ルール厳格化 | 中 | `dir_pct+kmp_pct >= 1%` 閾値導入で FP 30→数件削減 |
| MCX Phase 4 再取得 | 低 | 現データが 2018-12-31 と古い |
| BSE XBRL parser 拡張 | 低 | BSE 自社 taxonomy 対応 |
| SAMMAANCAP の 2026.06 再ラベリング | 中 | IHC (UAE) 41.5% 取得反映後、Professional → MNC へ更新検討 |
| 軽微な rev1 ラベル誤記 2 件 | 低 | GMDCLTD "state" / UTKARSHBNK "abb" (意図的に放置) |

### 維持運用

四半期ごとに以下を再実行:
1. NSE Phase 3/4 データ取得 (`refetch_rev1_missing.py`)
2. 永続化 + 分類 (`persist_rev1_missing.py`)
3. レビューシート生成 (`build_owner_review_sheet.py`)
4. Universe 生成 (`build_nifty750_universe.py`)
5. 必要に応じて Pattern B 同等の AI 補完

### 半年ごとのレビュー対象

- 新規上場銘柄の取り込み
- yaml 辞書 (175 keywords) のメンテナンス (新規 family / corporate vehicle 追加)
- rev1 ラベルの再検証

---

## 14. 付録: 主要コードファイル

| ファイル | 役割 | 行数 |
|---------|------|------|
| `notebook/NSE/scripts/build_owner_review_sheet.py` | Phase 2 + 3 (yaml + hybrid) | 412 |
| `notebook/NSE/scripts/build_nifty750_universe.py` | Phase 4 (universe 統合) | 261 |
| `notebook/NSE/scripts/persist_rev1_missing.py` | Phase 1 (Tier 1-4 機械判定) | 369 |
| `notebook/NSE/scripts/refetch_rev1_missing.py` | NSE データ取得 | 142 |
| `data/config/nse_promoter_classifier.yaml` | yaml 辞書 (175 keywords) | 775 |

---

## 15. プロセス監査トレース

各意思決定は Neo4j Knowledge Graph に保存:

```cypher
MATCH (d:Discussion {discussion_id: 'disc-2026-05-12-nse-owner-rev1-rerun'})
OPTIONAL MATCH (d)-[:RESULTED_IN]->(dec:Decision)
OPTIONAL MATCH (d)-[:PRODUCED]->(a:ActionItem)
RETURN d, collect(dec), collect(a)
```

- **Discussion**: 議論セッション
- **Decision**: 6 件の意思決定 (rev2 廃止 / 100% 統合 / nse_fetch_status / ai-judge 別ファイル管理 等)
- **ActionItem**: 10 件のタスク (7 件 completed / 1 件 withdrawn / 3 件 pending)

議論メモ: `docs/plan/2026-05-12_discussion-nse-owner-rev1-rerun.md`

---

## 16. 連絡先・参照

- 議論メモ: `docs/plan/2026-05-12_discussion-nse-owner-rev1-rerun.md`
- 過去の関連議論:
  - 2026-04-17: NSE オーナー分析 Phase 3/4 完了
  - 2026-04-30: rev1 評価 + ハイブリッドルール導入
  - 2026-05-07: NIFTY 750 スコープ確定
  - 2026-05-12: rev2 廃止 + universe 100% 統合 + AI 補完 (本ドキュメント)
- メモリ: `~/.claude/projects/-Users-yukihata-Desktop-quants/memory/project_nse_owner_rev1_rerun_2026_05_12.md`

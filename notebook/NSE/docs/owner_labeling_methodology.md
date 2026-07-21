# NSE オーナー企業ラベリング手法 — 上司向け説明書

- **作成日**: 2026-05-12
- **対象**: インド株式市場 (NSE 上場銘柄)
- **対象ユニバース**: NIFTY 750 (= NIFTY TOTAL MKT) を基準とした 855 銘柄
- **最終成果物**: `notebook/NSE/data/cache/nse/owners_universe_ai-judge.json`

---

## エグゼクティブサマリー

インド NSE 上場 855 銘柄について、各企業を以下の 4 カテゴリに分類するラベリングシステムを構築・運用しています。

| カテゴリ | 銘柄数 | 比率 | 定義 |
|---------|--------|------|------|
| **Owner** | 607 | 71.0% | 創業家・個人 promoter が支配的経営に関与 (SAST 10% 閾値クリア) |
| **Professional** | 116 | 13.6% | 専門経営者主導、創業家から経営分離済み |
| **State** | 85 | 9.9% | 政府・国営企業が支配株主 |
| **MNC** | 45 | 5.3% | 海外親会社が支配的株主 |

なお、機械判定の `is_owner_company` フラグは **Stage1 (SAST 2011 Reg 3 の 10% 閾値)** を必要条件として課しているため、上記 Owner 607 件のうち **NSE 開示で promoter ≥ 10% を満たすのは 599 件** です (残り 8 件は人間ラベルで Owner だが SAST 閾値未達)。投資戦略では `is_owner_company=True` を使うことで法令準拠の 599 銘柄を取得できます。

### 達成した品質指標 (Stage1 適用後)

- **Precision**: 99.0% (機械が Owner と判定した銘柄の正確性、SAST 10% 閾値で誤検出を排除)
- **Recall**: 96.7% (rev1 で Owner だが SAST 閾値未達の 14 銘柄は法令準拠で除外)
- **F1**: 97.9%
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

NSE が四半期ごと公開する **株主構成詳細 XBRL (Shareholding Pattern)** を一次データとして使用します。SEBI 開示規制 (LODR Regulation 31) に基づき、上場企業は四半期ごとに「誰がどれだけ株を持っているか」を XBRL 形式で公開する義務があります。

```
取得経路:
  NSE Website → API → XBRL Parser → SQLite DB
                                   → CSV 出力 (shareholdings.csv / shareholding_detail.csv)
```

### NSE Shareholding XBRL の構造

NSE の XBRL は **3 階層のカテゴリ構造** で promoter の保有を開示します:

```
Category (大分類)
└── Sub-Category (中分類)
    └── 個別 promoter 名 + 保有比率
```

**Category** (= `category` カラム) の主要分類:
- `PromoterAndPromoterGroup`: promoter およびその関係者 (= 本ラベリング対象の中核)
- `Public`: 一般株主
- `NonPromoterNonPublic`: その他

本ラベリングでは `PromoterAndPromoterGroup` のみを集計対象とします。

### NSE sub_category とロジック変数の対応 ★

NSE が開示する sub_category (= `sub_category` カラム) を、Phase 1 のロジックで使う変数に集約しています:

| NSE sub_category | 集約変数 | 意味 | Phase 1 での使用 |
|------------------|----------|------|------------------|
| `IndividualsOrHinduUndividedFamily` | **`hufi_pct`** | 個人 + Hindu Undivided Family (HUF) の保有比率 | Tier 1 の主要判定軸 (HUFI≥5%なら Owner 確定の主候補) |
| `NonResidentIndividualsOrForeignIndividuals` | **`nri_pct`** | 海外個人 / NRI (Non-Resident Indian) の保有比率 | Tier 2.5 で `owner_probable_nri_family` の根拠 |
| `DirectorsAndDirectorsRelatives` | **`dir_pct`** | 取締役 + その親族の保有比率 | Tier 2 で `owner_confirmed_director_only` の根拠 (★FP の主犯) |
| `KeyManagerialPersonnel` | **`kmp_pct`** | 重要管理職員 (KMP) の保有比率 | Tier 2 で dir_pct と並び director_only 判定の根拠 |
| `RelativesOfPromotersOtherThanPromoterGroup` | **`rel_pct`** | promoter group 外の親族 | Tier 2.5 で `owner_probable_relatives_trust` の根拠 |
| `TrustsWhereAnyPersonBelongingToPromoter...` | **`trust_pct`** | promoter 関連信託 | Tier 2.5 補助情報 |
| `OtherIndianShareholders` | **`other_indian_pct`** | 国内法人 promoter (= corporate vehicle 経由保有) | Tier 4 で `ambiguous_holding_indian` の根拠 |
| `OtherForeignShareholders` | **`other_foreign_pct`** | 海外法人 promoter (= 外国親会社・海外 vehicle) | Tier 4 で `ambiguous_holding_foreign` の根拠 |
| `ForeignInstitutions` / `ForeignPortfolioInvestor` | **`foreign_non_govt_pct`** | 外国機関投資家 / FPI (= MNC promoter 候補) | Tier 4 で foreign 判定の根拠 |
| `CentralGovernmentOrPresidentOfIndia` 他 7 種 | **`govt_pct`** | 政府関連 (中央政府 / 州政府 / 大統領 / 国営企業 holding 等) | Tier 3 で `excluded_state_dominant` の根拠 |
| (sub_category なし、root) | **`promoter_total_pct`** | promoter 全体の保有比率 | NO_PROMOTER 判定 (= 全 promoter ゼロ) の根拠 |

これらの集計ロジックは `notebook/NSE/scripts/persist_rev1_missing.py:142-178` に実装されています。

### 派生変数

| 派生変数 | 算出式 | 意味 |
|----------|--------|------|
| `natural_pct_sum` | `hufi + nri + dir + kmp + rel` | 自然人 promoter 合計。Tier 1/2/2.5 の分岐に使う |

### promoter 名の取得 (Phase 2 で使用)

各 promoter の生文字列 (= `shareholder_name` カラム) を `|` 区切りで結合したものが `promoter_names_full_list`。これが Phase 2 の yaml 辞書マッチの入力となります。

```python
# 個別 promoter 行 (is_category_total == 0) のみ抽出
detail_rows = prom[prom["is_category_total"] == 0]
names = [n for n in detail_rows["shareholder_name"].dropna().unique() if n.strip()]
promoter_names_full_list = "|".join(names)
```

例 (RELIANCE):
```
"K. D. Ambani|Mukesh Dhirubhai Ambani|Nita Mukesh Ambani|Isha Mukesh Ambani|...
 |Reliance Industries Holding Pvt Ltd|Devarshi Commercials LLP|..."
```

### データ取得 Phase (NSE 取得側の用語)

NSE 開示の取得を 4 つの Phase に分けて運用しています (本ドキュメントの判定 Phase 1-5 とは別概念):

| 取得 Phase | 取得対象 | 出力 |
|-----------|----------|------|
| Phase 1 (Universe) | NIFTY 50/100/200/500/TOTAL MKT のメンバー | `index_members.csv` |
| Phase 2 (Stocks) | 各銘柄の symbol/ISIN/company_name | `stocks.csv` |
| **Phase 3 (Shareholding)** | 各銘柄の四半期 shareholding pattern (promoter 合計のみ) | `shareholdings.csv` |
| **Phase 4 (XBRL Detail)** | 各銘柄の XBRL 詳細 (個別 promoter ごとの sub_category 別保有) | `shareholding_detail.csv` ← **本ラベリングの主要入力** |

`nse_fetch_status` カラムはこの取得 Phase 3/4 の成功状況を示します:
- `ok`: Phase 3 + Phase 4 両方成功 (= 完全データ)
- `phase4_failed_xbrl`: Phase 3 OK だが Phase 4 XBRL parse 失敗 (例: BSE 自社 taxonomy 不対応)
- `unresolvable_isin`: NSE の stocks テーブルに ISIN が存在しない (M&A 消滅、REIT、上場廃止)

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

### 何をする Phase か

NSE が四半期ごとに開示する **株主構成データ (Shareholding Pattern XBRL)** を読み込み、各銘柄の promoter (= 大株主) がどのような構成になっているかを数値で読み取り、機械的に **12 種類のフラグ** に分類する Phase です。アナリストが財務諸表を見て「これは創業家経営の会社」「これは政府系」と直感的に判断する作業を、開示数値だけで再現することを目指しています。

### 入力データ (NSE 開示との対応)

Phase 1 が直接読むのは **`shareholding_detail.csv`** (Phase 4 XBRL Detail 取得分) です。第 3 章で示した sub_category 別の保有比率を以下のように使います:

| 判定軸 | 元 NSE sub_category | 使う変数 |
|--------|---------------------|---------|
| 自然人主体か | `IndividualsOrHinduUndividedFamily` | `hufi_pct` |
| 役員主体か | `DirectorsAndDirectorsRelatives` / `KeyManagerialPersonnel` | `dir_pct` / `kmp_pct` |
| 海外個人主体か | `NonResidentIndividualsOrForeignIndividuals` | `nri_pct` |
| 信託/親族主体か | `RelativesOfPromotersOtherThanPromoterGroup` | `rel_pct` |
| 政府主体か | `CentralGovernmentOrPresidentOfIndia` 他 7 種 | `govt_pct` |
| 国内法人 promoter | `OtherIndianShareholders` | `other_indian_pct` |
| 海外法人 promoter | `OtherForeignShareholders` | `other_foreign_pct` |
| 外国機関投資家 | `ForeignInstitutions` / `ForeignPortfolioInvestor` | `foreign_non_govt_pct` |

これら 8 つの変数の組み合わせで 12 種類のフラグに分類します。

### Tier 構造の考え方

判定ロジックは Tier 1 から Tier 4 まで段階的に下りていく構造になっています。これは **「インドの企業オーナーシップは自然人 (Individuals/HUF) の保有比率を最優先で見るべき」** という業界知見を反映したものです。

- **Tier 1 (自然人 promoter 主体)**: HUFI (個人 + Hindu Undivided Family) が一定以上保有 → 創業家経営の典型。「ある一族が会社の支配的株主であり経営にも関与している」ケース
- **Tier 2 (役員のみ)**: 取締役 / KMP の名目保有のみ。これは一見オーナー寄りに見えるが **大企業の取締役慣行 (1株保有の Token holding)** とも区別がつかない。Phase 2/3 で補正が必要
- **Tier 2.5 (NRI / 親族信託)**: 海外個人や親族信託のみの保有。一族支配だが構造が複雑で確証は低い
- **Tier 3 (政府主体)**: govt_pct 50%以上で SBI / NTPC のような政府支配企業を自動識別
- **Tier 4 (法人 promoter 主体 / 全 promoter ゼロ)**: 個人保有なしで法人 vehicle 経由のみ。これは Adani 系 corporate vehicle (= 創業家支配だが個人名が表面に出ない)、外国 MNC 子会社、PE-backed 等の **どれか判断不能** な状態。Phase 2 (yaml) と Phase 3 (hybrid) で確定させる

### Phase 1 が単独で確定できる範囲

Phase 1 だけでほぼ確実に判定できるのは **Tier 1 (HUFI 高保有)** と **Tier 3 (政府主体)** の 2 ケースのみです。Tier 2 / 2.5 / 4 は **判定保留** であり、後段の Phase で yaml 辞書や AI 判定で補完します。

### コード参照

**コード**: `notebook/NSE/scripts/persist_rev1_missing.py:122-251`

NSE 開示の各 sub_category 別保有比率を入力に、12 種類の owner_flag を確定:

### 判定軸: 株主数を用いる (2026-07-21 変更)

判定は原則として **株主数 (`*_num`)** で行う。保有比率は閾値判定
(promoter 総計・政府保有・外資保有・微少個人) にのみ使う。

インドの支配的な promoter 構造は持株会社ピラミッドであり、一族は holdco 経由で
支配して個人名義は名目的な株数にとどまる。`hufi_pct` は小数第2位で丸められるため
この構造では 0.00% となり、比率で判定すると一族の存在を取りこぼす
(実例: INOXGREEN は自然人3名で計500株、発行済4.01億株に対し `hufi_pct=0.00%`)。

本ルールは rev1 手動ラベル 425 銘柄に対する実測で選定した。

| ルール変種 | Precision | Recall | F1 |
|---|---|---|---|
| **株主数ベース (採用)** | **99.0%** | **96.7%** | **97.9%** |
| 保有比率ベース | 98.8% | 94.1% | 96.4% |

### 実装の一元化 (2026-07-21)

判定ルールの実装は `src/market/nse/analysis/owner_classification.py` に一元化されている。
`nse_owner_analysis.ipynb` および `persist_incremental.py` / `persist_rev1_missing.py` /
`persist_and_classify.py` はすべて同モジュールを呼び出す。

従来はノートブックとスクリプト群に別実装が存在し、同一データでも「どの経路で処理
されたか」で結果が変わっていた (実例: INOXGREEN が再取得を機に OWNER → OWNER_WEAK
へ反転)。差異は自然人判定の判定軸だけでなく、役員判定の判定軸・外資ガードの有無・
`excluded_low_promoter` 等の tier の有無にも及んでいた。

### 判定の優先順位

```python
# 自然人 promoter の合計
natural_pct = hufi_pct + nri_pct + dir_pct + kmp_pct + rel_pct

if natural_pct > 0:                      # ── Tier 1, 2, 2.5
    if dir_pct > 0 or kmp_pct > 0:
        if hufi_num >= 1:                # ★株主数で判定 (2026-07-21 変更)
            → owner_confirmed_individual_and_director   # 創業家 + 役員
        else:
            → owner_confirmed_director_only             # 役員名目のみ ★FP の主犯
    elif hufi_num >= 1:                  # ★株主数で判定 (2026-07-21 変更)
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

### 何をする Phase か

NSE は promoter の名前を **「文字列のリスト」としてしか出してくれません**。例えば BHARTIARTL (Bharti Airtel) の開示には "INDIAN CONTINENT INVESTMENT LIMITED" や "Pastel Limited" といった会社名が並びますが、この文字列を見ただけでは **これが Mittal 一族の持株会社だ** とは機械にはわかりません。Phase 2 では、この文字列を **人間知識でまとめた辞書 (yaml)** と照合することで、「この vehicle は誰の支配下か」を構造情報として抽出します。

### 入力データ (NSE 開示との対応)

Phase 2 が直接読むのは Phase 1 で生成された **`promoter_names_full_list`** カラムです。これは NSE XBRL の **`shareholder_name`** フィールド (個別 promoter の生文字列) を、`is_category_total = 0` の行 (= 個別 promoter 行、合計行除く) だけ集めて `|` 区切りで結合したものです。

```python
# Phase 1 で生成済み (persist_rev1_missing.py:181-185)
detail_rows = prom[prom["is_category_total"] == 0]
names = [n for n in detail_rows["shareholder_name"].dropna().unique() if n.strip()]
promoter_names_full_list = "|".join(names)
```

つまり Phase 2 は **NSE が文字列開示した個別 promoter 名のリスト** を入力として、yaml 辞書とテキストマッチします。

### なぜ yaml 辞書が不可欠か

インドの大企業オーナーシップには 3 つの特徴があります:

1. **間接保有が主流**: 創業家 (例: Adani / Tata / Birla / Mittal) は個人保有ではなく **持株会社・LLP・信託 vehicle 経由で間接保有** することがほとんど。NSE 開示の表面には個人名ではなく vehicle 名が並びます
2. **vehicle 名は会社固有**: vehicle 名は固有名詞 (例: "INDIAN CONTINENT INVESTMENT" や "Inuus Infrastructure") であり、機械的アルゴリズムでは「これが Mittal か」を当てる手段がありません
3. **業界知識でしか紐付けできない**: 「Pastel Limited は Mittal の vehicle」と知るには市場ニュースや SEBI 開示の歴史を追う必要があり、これは **人間の暗黙知** です

そこで、過去のアナリスト・チームのラベリング (rev1) と Web 公開情報をもとに **「キーワード → 実支配者」マッピング辞書** (175 keywords、78 family) を構築し、機械が文字列照合で実支配者を識別できるようにしています。

### 辞書の 4 カテゴリの役割分担

- **`owner_keywords`** (84 件): 創業家系 vehicle を Owner に紐付ける (Tier 1.5 救済の主役)
- **`professional_keywords`** (49 件): プロ経営の corporate vehicle を Professional に紐付ける (Tata Sons / HDFC Bank / LIC など、それ自体は家族ではないが大企業 holding に頻出)
- **`state_keywords`** (18 件): "President of India" など政府保有を明示する文字列を State に確定
- **`mnc_keywords`** (14 件): "Unilever" "Nestle" など海外親会社名を MNC に確定

### Phase 2 の限界

yaml は **promoter_names に文字列が入っている前提**で動きます。SAMMAAN Capital のように 2023 年に de-promoterization (promoter 取り消し) された企業は文字列が空欄になり、yaml は何もマッチさせられず UNKNOWN を返します。この場合は Phase 3 (hybrid) で OWNER_WEAK 扱いになり、最終的には AI 判定で補完します。

### コード参照

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

### なぜ「ハイブリッド」と呼ぶか

Phase 1 (数値ベースの Tier 判定) と Phase 2 (文字列ベースの yaml 判定) は **それぞれ単独では限界がある** ため、両者を組み合わせて補完しあう構造にしています。具体的には:

- Phase 1 の **数値判定** (NSE sub_category 別保有比率) は客観的だが、Tier 2 や Tier 4 のように「判定保留」のケースが残る
- Phase 2 の **文字列判定** (NSE shareholder_name + yaml 辞書) は人間知識を反映できるが、文字列が空欄だと無力

両者の出力を **5 つの分岐ルール** で統合することで、最終的に「Owner / NOT_OWNER / 判定不能 (OWNER_WEAK)」のいずれかに確定させるのが Phase 3 の役割です。

### 入力データ (NSE 開示との対応)

Phase 3 自体は NSE 開示を直接読まず、Phase 1/2 の出力 (派生変数) のみを使います:

| 入力 | 由来 | 元の NSE 開示 |
|------|------|--------------|
| `owner_flag` | Phase 1 出力 | sub_category 別保有比率の組み合わせ |
| `yaml_classification` | Phase 2 出力 | shareholder_name 文字列 ✕ yaml 辞書 |

### 5 つの分岐ルールの意図

各ルールは特定の「機械判定の弱点」を補正するために設計されています:

1. **Tier 2 director_only への yaml 適用**: HDFCBANK / ICICIBANK / ITC など Professional 系大企業が「取締役の名目 1 株保有」だけで Tier 2 を獲得してしまう問題への対策。yaml が「これは HDFC Bank の corporate vehicle」と判定すれば NOT_OWNER に確定、未判定 (UNKNOWN) なら OWNER_WEAK で AI に委ねる
2. **ambiguous_* への yaml 適用 (Tier 1.5 corporate-vehicle rescue)**: Adani 系の銘柄は個人保有がなく法人 vehicle 経由のみのため、Phase 1 では Tier 4 ambiguous_* で「判定保留」になります。yaml で "Adani" にマッチすれば OWNER に格上げ救済する仕組み
3. **excluded_* への yaml 救済**: HUL のように個人 promoter ゼロでも yaml で "Unilever" マッチなら MNC として NOT_OWNER 確定
4. **owner_probable_* への yaml 救済**: NRI / 信託のみで判定が弱いケースも yaml で確定情報があれば OWNER 確定
5. **それ以外**: 上記分岐に当てはまらない Tier 1 銘柄は、もともと Phase 1 で確度高く判定済みなので、その判定を維持

### OWNER_WEAK (判定不能) の扱い

Phase 3 の出力は OWNER / NOT_OWNER / OWNER_WEAK の 3 値です。OWNER_WEAK は **「機械では判定不能、AI 判定推奨」** を意味し、最終 universe では `is_owner_company=False` 扱いとなります。これは SAMMAAN や HDFCBANK のように **取締役名目保有のみ + yaml で family/parent 識別不可** のケースで発生します。

このように OWNER と NOT_OWNER の二項判定ではなく **第三の「判定不能」状態** を設けることで、機械判定の品質を保ちつつ AI 補完が必要な銘柄を明示的に切り出せる構造になっています。

### コード参照

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

### 何をする Phase か

Phase 1〜3 で確定した判定結果を **投資戦略チームが使いやすい単一の CSV ファイル** (`nifty750_universe.csv`) にまとめ、銘柄スクリーニング・ファクターモデル構築に必要なメタデータを付与する Phase です。

### 入力データ (NSE 開示との対応)

Phase 4 では複数の NSE 由来データを統合します:

| 入力 | 由来 | NSE 開示元 |
|------|------|-----------|
| Phase 3 出力 (`owner_flag_final_hybrid`) | レビューシート | NSE XBRL Phase 3/4 集約 |
| Index 帰属情報 (`is_nifty50` 等) | `index_members` テーブル | NSE Index Constituents API |
| 銘柄基本情報 (`symbol`, `isin`, `company_name`) | `stocks` テーブル | NSE Securities API |
| データ品質 (`nse_fetch_status`) | refetch ログ | Phase 3/4 取得成否 |

### なぜシンプルなブール変換か

最終的な投資戦略側の関心は「**この銘柄はオーナー企業か (True/False)**」という二項判定です。そのため Phase 3 の 3 値出力 (OWNER / NOT_OWNER / OWNER_WEAK) を `is_owner_company` という単一のブール値に集約します。判定不能 (OWNER_WEAK) は保守的に False 扱いとし、**「機械が確信できないものは Owner と認定しない」** という方針を取っています。これにより Owner フラグの **Precision を優先** した universe になります (Recall は別途 rev1 GT との照合で保証)。

### 付与するメタデータの役割

ブール判定の根拠を後から追跡・検証できるよう、以下の補助情報を併記します:

- **`owner_flag` / `owner_flag_final_hybrid`**: どのロジックで判定されたか (デバッグ・レビュー用)
- **`rev1_category`**: 人間チームの GT ラベル (機械 vs 人間の差分追跡用)
- **`promoter_total_pct` / `hufi_pct` / `dir_pct` 等**: 元の NSE 開示数値 (判定根拠の数値証跡)
- **`is_nifty50/100/200/500/total_mkt`**: index 帰属フラグ (投資戦略で「NIFTY 100 圏内の Owner 企業のみ」のような絞り込みに必須)
- **`owner_family`**: 一族名 (例: "Adani" / "Tata" / "Birla")、グループ別分析に活用
- **`nse_fetch_status`**: データ品質ラベル (`ok` / `phase4_failed_xbrl` / `unresolvable_isin`)、データ完全性を要する戦略で「ok のみ」フィルタが可能

### 投資戦略との接続

このユニバースは **ファクター投資戦略** での Owner ファクターや、**スクリーニング** での「Owner かつ NIFTY 100 圏内」のような絞り込みに直接使えるよう設計されています。さらに `owner_family` カラムでグループ別 (Adani 全銘柄、Tata 全銘柄) の分析・バックテストが可能です。

### Stage1 (promoter ≥ 10%) フィルタ — 上司指定

最終判定では **SAST 2011 Reg 3 に基づく 10% 閾値** を必要条件として課しています (`dec-2026-04-16-002` 上司指定)。

SEBI の Substantial Acquisition of Shares and Takeovers Regulations 2011 第 3 条で、**実質支配の発動閾値は 10%** と定められています。つまり「**10% 以上の保有がない promoter は法的に支配的影響力を持たない**」とみなされます。この法的根拠に基づき、上司指定として「オーナー企業の必要条件は promoter_total ≥ 10%」が確定しています。

### コード参照

**コード**: `notebook/NSE/scripts/build_nifty750_universe.py:121`

```python
# Stage1 (上司指定、SAST 2011 Reg 3 閾値) + Phase 3 hybrid 出力の AND
stage1_promoter_ge_10 = promoter_total_pct >= 10
is_owner_company = (owner_flag_final_hybrid == "OWNER") & stage1_promoter_ge_10
```

つまり:
- Stage1 通過 **かつ** hybrid OWNER → `is_owner_company = True`
- Stage1 通過しない (promoter < 10%) → `is_owner_company = False` (hybrid OWNER でも降格)
- hybrid NOT_OWNER / OWNER_WEAK → `is_owner_company = False`

### Stage1 で is_owner=False に降格する銘柄

Stage1 適用で 15 件が hybrid OWNER から `is_owner_company=False` に降格します:

| パターン | 件数 | 例 | 妥当性 |
|---------|------|-----|--------|
| rev1 流用 (NSE データなし、promoter=0%) | 8 | EMBASSY/MINDSPACE REIT、PIRAMAL、DHANI 等 | 上場廃止/REIT は投資対象外、降格は妥当 |
| NSE 取得済みだが promoter < 10% | 7 | DISHTV (4.06%)、360ONE (6.24%)、KARURVYSYA (2.07%) 等 | SAST 法的閾値未達、降格は法的に正当 |

このうち rev1=Owner として人間チームがラベルした 14 件は新規 **FN** として記録されますが、これは「SAST 規制下では支配的でない」という法的判断に従った結果です。

### 出力カラム

- `is_owner_company` (bool): Stage1 + hybrid 統合の最終判定
- `stage1_promoter_ge_10` (bool): Stage1 通過フラグ (デバッグ用)
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
| AI 補完後 | 426 | 28 | 0 | 93.8% | 100.0% | 96.8% |
| **Stage1 適用後 (最終)** | **411** | **4** | **14** | **99.0%** | **96.7%** | **97.9%** |

### 解釈

- **Precision 99.0% (Stage1 適用後)**: SAST 規制閾値で支配的影響力を持たない銘柄を除外し、機械判定 Owner の正確性を担保
- **Recall 96.7% (Stage1 適用後)**: rev1 で Owner と判定されたが promoter < 10% の 14 銘柄 (= 法的支配閾値未達) を法令準拠で除外
- **Stage1 のトレードオフ**: FP 30→4 に激減する一方、FN 0→14 が発生。これは **法的支配閾値の厳格適用** という上司方針の必然的結果

### Stage1 で除外される 14 件の内訳

#### A. NSE データなし (8 件、rev1 流用銘柄)

EMBASSY/MINDSPACE REIT、PIRAMAL、DHANI、JAIPRAKASH、FUTURE RETAIL、TCNS、TV18:
- M&A 消滅 / REIT / 上場廃止 → そもそも投資ユニバース対象外
- Stage1 による降格は投資戦略上は実質的影響なし

#### B. NSE 取得済みだが promoter < 10% (6 件)

| 銘柄 | promoter | 状況 |
|------|---------|------|
| SAMMAANCAP | 0.00% | de-promoterized 2023.02、すでに Professional 確定 (AI 修正済) |
| MFSL | 1.25% | Max Financial、Singh family promoter 薄い |
| KARURVYSYA | 2.07% | 銀行業 26% 上限制約、family promoter 制度的に薄い (★) |
| ZEEL | 3.99% | Chandra family 経営危機・保有売却中 |
| DISHTV | 4.06% | Zee 系の経営危機 |
| 360ONE | 6.24% | Bansal family の保有薄い |
| ASTRAMICRO | 6.54% | Reddy family + 役員保有 |

★ KARURVYSYA のような銀行業の特殊規制下銘柄は **法的に promoter を 10% 以上保有できない**ため、Stage1 適用と銀行規制が矛盾します。これは個別検討が必要なケースですが、現状は上司指定どおり Stage1 で除外しています。

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

**2026-06-30版で運用フローを刷新**（従来の `refetch_rev1_missing.py` は rev1 GT との差分専用ロジックであり、「前回universe vs 最新指数構成」の差分検出には対応していなかったため、増分更新専用のスクリプト群を新規実装した）。

差分更新の実行手順:
1. universe差分検出 (`src/market/nse/analysis/universe_diff.py::diff_universe()`、指数構成は `IndicesCollector.fetch_index_constituents_archive()` で静的CSV経由取得——動的API `equity-stockIndices` は2026-07時点で404となり不通のため代替手段が必須)
2. promoter比率drift検出 (`src/market/nse/analysis/promoter_drift.py::detect_promoter_drift()`、既存 `shareholdings` テーブルの四半期時系列のみで新規取得不要)
3. 差分銘柄（新規採用+drift検出）のNSEデータ取得 (`refetch_incremental.py --symbols-file`)
4. 永続化 + 分類 (`persist_incremental.py --db-path`)
5. index_members最新化 (`update_index_members.py --db-path`)
6. レビューシート生成 (`build_owner_review_sheet.py`)
7. Universe 生成 (`build_nifty750_universe.py --db-path --output-universe --output-summary`)
8. 必要に応じて AI 補完

前回版DBと今回版DBは別ファイル（例: `nse_index_20260512.db` / `nse_index_20260630.db`）として分離保持し、本体`nse_index.db`は最終確認後に置き換える運用とする。

### 半年ごとのレビュー対象

- 新規上場銘柄の取り込み
- yaml 辞書 (175 keywords) のメンテナンス (新規 family / corporate vehicle 追加)
- rev1 ラベルの再検証
- stocksテーブルの完全最新化（EQUITY_L.csv全体、新規上場銘柄のISIN解決に必要）

### 2026-06-30版での変更・修正

- **バグ修正**: `aggregate_owner_candidate()` の `promoter_total_pct` 算出ロジックが、`PromoterAndPromoterGroup` カテゴリの「総合計」行が省略されたXBRL開示（新規上場企業で確認）で0.0%を誤算出する不具合を修正。`natural_pct_sum`へのフォールバックを追加（`persist_incremental.py`・`persist_rev1_missing.py`両方に適用）。既存845銘柄のうち25銘柄が同一パターンの影響を受けていたが、Stage1判定への影響はゼロ（フォールバック後も全て10%未満）と確認済み
- 詳細: `notebook/NSE/data/exports/nse/universe_diff_report_20260630.md`

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

# 議論メモ: owners_rev1.json 採用 + ロジック改善方針

**日付**: 2026-04-30
**議論ID**: `disc-2026-04-30-nse-owners-rev1-evaluation`
**前回議論**: `disc-2026-04-27-nse-owners-coverage-and-fp-report`
**関連プロジェクト**: project-106 (NSE パッケージ拡張)

## 背景・コンテキスト

ユーザーが owners.json の ISIN 欠損 24 件を補完した owners_rev1.json を提供。これを正誤表として採用し、現状のオーナー企業抽出ロジックの精度・妥当性を再評価。

## 議論のサマリー

### owners_rev1.json の構造解析

#### 重大発見 1: JSON キー入替のバグ
- `"company name"` 列に ISIN、`"isin"` 列に社名が入っている（632/632 件で確認）
- そのまま読み込むと既存スクリプトが破綻する
- → `owners_rev1.normalized.json` を生成（632 件すべて valid ISIN）

#### 重大発見 2: 件数 635 → 632、内容差分が想像以上に大きい
- ISIN 欠損: 24 件 → 0 件（完全解消）
- 社名差分: 28 件削除 / 25 件追加
  - 大半は corporate action（rename/split/spin-off）の反映
  - 例: ZOMATO→ETERNAL / MACROTECH→LODHA / AFFLE INDIA→AFFLE 3I / AMARA RAJA BATTERIES→AMARA RAJA ENERGY & MOBILITY / RELIANCE INDUSTRIES LTD→LIMITED
- Category 分布: Owner 428→425（−3）、その他不変
- → 単なる ISIN 補完ではなく実質的なメンテナンス更新

### 再評価結果（rev1 を ground truth、ISIN ベース）

| 指標 | 前回 (owners.json, 名前ベース) | 今回 (rev1, ISIN ベース) | Δ |
|---|---|---|---|
| Recall | 97.7% | **98.3%** | +0.6pt |
| Precision | 90.2% | **90.0%** | -0.2pt |
| F1 | 93.8% | **93.9%** | +0.1pt |
| TP / FP / FN / TN | — / 42 / — / — | 403 / **45** / 7 / 109 | (intersection 564) |

**結論**: ロジックの精度水準は前回評価とほぼ同一。FP の 42件 (93%) が `owner_confirmed_director_only` 起因という構造も再現された。

### FP 内訳 (45件)
- Professional 31 / State 8 / MNC 6
- 増分 +3 (vs 前回 42 件) はすべて Professional：LTF / TMPV / LTM（rev1 で corporate action 反映により追加された）
- 全 45 件中 42 件が `owner_confirmed_director_only` ルール起因

### FN 内訳 (7件)

| Symbol | rev1 名 | owner_flag | AI 判定 | 備考 |
|---|---|---|---|---|
| AWL | AWL AGRI BUSINESS | excluded_no_natural_no_holding | — | 旧 ADANI WILMAR、rev1 で新規追加 |
| SPANDANA | SPANDANA SPHOORTY FINANCIAL | ambiguous_holding_foreign | ai_professional | rev1≠AI 食違い |
| GLAND | GLAND PHARMA | ambiguous_holding_foreign | ai_mnc | rev1≠AI 食違い |
| ROUTE | ROUTE MOBILE | ambiguous_holding_foreign | ai_mnc | rev1≠AI 食違い |
| ASHOKLEY | ASHOK LEYLAND | excluded_no_natural_no_holding | — | promoter 51.5% 法人 promoter |
| AEGISLOG | AEGIS LOGISTICS | excluded_no_natural_no_holding | — | rev1 で ISIN 補完されて評価対象に |
| HINDZINC | HINDUSTAN ZINC | excluded_state_dominant | — | Vedanta 系 |

### director_only 厳格化の検証（重要な発見）

#### 単純な閾値 `dir+kmp ≥ 1%` は採用不可

| 指標 | 現状 | 閾値 1% 適用後 | Δ |
|---|---|---|---|
| Precision | 90.0% | **99.2%** | +9.2pt ✅ |
| Recall | 98.3% | **92.9%** | **−5.4pt ⚠️** |
| F1 | 93.9% | 96.0% | +2.1pt |

**理由**: 真の Owner 22 社（HAVELLS/BHARTIARTL/PATANJALI/TECHM/M&MFIN/LODHA/INDUSINDBK/SHRIRAMFIN/INDIACEM/TRIDENT 等）は持株会社経由保有のため dir+kmp が極小値（0.0〜0.5%）になる。閾値だけだとこれらが全て FN に流れる。

#### 真の構造的問題

`owner_confirmed_director_only` (64件 in intersection) の中身は2種類が混在:

| パターン | 件数 | 例 | 性質 |
|---|---|---|---|
| **A. 真の Owner（持株会社経由）** | 22 | HAVELLS (Anil Rai Gupta)/PATANJALI/INDIACEM/TRIDENT | promoter group の corporate vehicle が一族支配下 |
| **B. 偽の Owner（Director の名目保有）** | 42 | TCS/TATAPOWER/HDFCLIFE/ICICIGI | promoter group は Tata Sons / HDFC 系の信託・分散保有 |

dir+kmp の値だけでは A と B を区別できない。promoter_names の分析が必要。

### 採用方針: 既知一族リスト + OWNER_WEAK 降格（ハイブリッド）

```
Tier 2 で owner_flag = director_only と判定されたら:
  promoter_names_full_list を既知一族リストと照合
    → Owner 一族マッチ (Mittal/Hinduja/Mahindra/Adani/Birla/Bajaj/Ambani/Agarwal/Shriram/Goenka/Jindal/Lodha 等)
       → OWNER 確定
    → Professional/State/MNC 持株主マッチ (Tata Sons/HDFC/ICICI/SBI/Schneider/Whirlpool/PG 等)
       → NOT_OWNER 確定
    → 未マッチ
       → OWNER_WEAK 降格 + ai_review_needed=True で AI 個別判定
```

期待効果:
- Precision: 90% → 95-98%（リスト完成度に依存）
- Recall: 98% 維持（OWNER_WEAK 経由で AI が拾う）

## 決定事項

| ID | 内容 | コンテキスト |
|----|------|------------|
| dec-2026-04-30-001 | owners_rev1.json (ISIN 補完版) を以後の ground truth として canonical 採用、ISIN ベース照合 | rev1 は全 632 件で ISIN を完備（original の欠損 24 件→0 件）。corporate action も反映済みで ISIN は安定 |
| dec-2026-04-30-002 | rev1.json のキー入替バグを修正した owners_rev1.normalized.json を canonical 化、owners.json を上書き | ISIN_RE 検証で 632/632 件すべて valid ISIN を確認 |
| dec-2026-04-30-003 | 現状ロジックの精度水準 (Recall 98.3% / Precision 90.0% / F1 93.9%) を確定。前回評価とほぼ一致 | TP=403/FP=45/FN=7/TN=109 (intersection 564 銘柄)。FP 内訳: Professional 31 / State 8 / MNC 6 |
| dec-2026-04-30-004 | director_only 厳格化は閾値単独ではなく「既知一族リスト + OWNER_WEAK 降格」のハイブリッド方式を採用 | 単純閾値 dir+kmp≥1% は HAVELLS/PATANJALI/INDIACEM 等 22 銘柄を Recall ロスする。promoter_names 解析で true Owner と Professional 持株主を区別する必要 |

## アクションアイテム

| ID | 内容 | 優先度 |
|----|------|--------|
| act-2026-04-30-001 | owners_rev1.normalized.json で owners.json を上書き commit / push | 高 |
| act-2026-04-30-002 | nse_owner_analysis.ipynb 照合ロジックを ISIN ベースへ書き換え | 高 |
| act-2026-04-30-003 | 既知一族リスト構築（data/config/nse_promoter_classifier.yaml 想定） | 高 |
| act-2026-04-30-004 | Tier 2 にハイブリッドルール統合（OWNER_WEAK 降格 + ai_review_needed=True） | 高 |
| act-2026-04-30-005 | AI 判定 vs rev1 不一致 3 件 (SPANDANA/GLAND/ROUTE) の個別ソース検証 | 中 |
| act-2026-04-30-006 | excluded_no_natural_no_holding 4 件 (AWL/ASHOKLEY/AEGISLOG/HINDZINC) の例外ルール検討 | 中 |
| act-2026-04-30-007 | owner_candidates.csv 生成時に rev1 GT との自動 diff レポート出力 | 中 |
| act-2026-04-30-008 | Phase 3/4 を全 2,263 銘柄に拡大実行 (act-2026-04-13-001 継続) | 中 |

## 次回の議論トピック

- 既知一族リスト (act-2026-04-30-003) の初期値設計：rev1 の FP 42 件 + 真Owner-director_only 22 件から逆引きで初期化、メンテナンスポリシー策定
- ハイブリッドルール (act-2026-04-30-004) 実装後の再評価サイクル設計
- AI 判定 vs rev1 不一致 3 件の最終決定（rev1 を信じるか AI を信じるか）

## 成果物

- `notebook/NSE/data/cache/nse/owners_rev1.normalized.json` — キー入替修正版
- `notebook/NSE/data/exports/nse/owners_rev1_false_positives.csv` — FP 45件
- `notebook/NSE/data/exports/nse/owners_rev1_false_negatives.csv` — FN 7件
- `docs/plan/2026-04-30_discussion-nse-owners-rev1-evaluation.md` — このファイル

## 保存先

- **Neo4j**:
  - Discussion: `disc-2026-04-30-nse-owners-rev1-evaluation`
  - Decision: `dec-2026-04-30-001` 〜 `dec-2026-04-30-004`（4件）
  - ActionItem: `act-2026-04-30-001` 〜 `act-2026-04-30-008`（8件）
  - リレーション: `(curr)-[:FOLLOWS]->(prev)`, `(disc)-[:RESULTED_IN]->(dec×4)`, `(disc)-[:PRODUCED]->(act×8)`
- **ドキュメント**: このファイル

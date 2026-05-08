# 議論メモ: yaml v0.5.0 検証 + 重要訂正 + コミット完了

**日付**: 2026-05-08
**議論ID**: `disc-2026-05-08-yaml-v050-validation-and-commit`
**前回**: `disc-2026-05-07-nse-owner-labeling-implementation`
**関連プロジェクト**: project-106

## 背景・コンテキスト

2026-05-07 セッションで完成した yaml v0.5.0 提案 (P0 10 件分の 10 keyword 追加案、`dec-2026-05-07-005` で `pending_approval`) を、ユーザーの方針 (AI による web 裏取り) に基づいて検証・適用・コミット完了。

ユーザーが Indian Owner 企業のドメイン知識を持たないため、web 裏取り (Tavily 並列検索) で各銘柄を確認するアプローチを採用。

## 議論のサマリー

### web 裏取りで判明した重要事実

10 銘柄を Tavily 並列検索で調査した結果、**2 件の重要訂正**が必要だった:

#### HCG (Healthcare Global Enterprises) — 訂正必要

- **元案**: Owner (`AJAIKUMAR` keyword、Dr. BS Ajaikumar 創業に着目)
- **裏取り発見**: 2025/02 に **KKR が CVC から $400M で controlling 54% 取得** (Hector Asia Holdings II Pte 経由)
- **訂正後**: Professional (`HECTOR ASIA HOLDINGS` を professional_keywords に追加)
- **示唆**: promoter_names だけでなく直近 M&A 情報の確認が必須

#### STYRENIX (Styrenix Performance Materials) — 訂正必要

- **元案**: 保留 (Shiva Performance Materials 1 社のみで親会社不明)
- **裏取り発見**: **2022 年に Shiva (Vadodara 独立 buyer) が INEOS Styrolution から 61.19% 取得**して新 promoter 化
- **訂正後**: Owner (`Shiva Performance Materials Private Limited` を owner_keywords に追加)
- **示唆**: 「親会社不明 = 保留」は早計、独立 buyout で新 owner family 化の可能性

### yaml v0.5.0 適用結果

#### 全 P0 10 件の最終判定 (確信度付き)

| Symbol | 確信度 | 判定 | yaml カテゴリ |
|--------|--------|------|--------------|
| WAAREERTL | 🟢 高 | Owner | owner (WAAREE ENERGIES) |
| HCG ⚠️ | 🟡 中 | **Professional** (KKR訂正) | professional (HECTOR ASIA HOLDINGS) |
| THYROCARE | 🟢 高 | Professional | professional (API Holdings) |
| FEDFINA | 🟢 高 | Professional | professional (Federal Bank) |
| AXISCADES | 🟡 中 | Owner | owner (JUPITER CAPITAL) |
| REFEX | 🟢 高 | Owner | owner (REFEX HOLDING) |
| GVT&D | 🟢 高 | MNC | mnc (GE Grid Solutions) |
| STYRENIX ⚠️ | 🟡 中 | **Owner** (独立 buyout) | owner (Shiva Performance Materials) |
| ITCHOTELS | 🟢 高 | Professional | professional (ITC Limited) |
| JSFB | 🟢 高 | Professional | professional (Jana Capital/Holdings/Foundation) |

#### メトリクス変化

| 指標 | v0.4.0 | **v0.5.0** | 差分 |
|------|--------|-----------|------|
| 全体 OWNER_WEAK | 13 | **3** | **-10 ✅** |
| 圏外 OWNER | 180 | 184 | +4 |
| 圏外 NOT_OWNER | 33 | 36 | +3 |
| Precision (intersection) | 98.8% | 98.8% | 維持 |
| Recall (intersection) | 100% | 100% | 維持 |

#### 残 OWNER_WEAK 3 件 (rev1 圏内)

| Symbol | rev1 | 状況 | v0.5.1 で対応 |
|--------|------|------|--------------|
| NETWORK18 | Professional | "Independent Media Trust" yaml にあるが括弧形式 matching 失敗 | yaml 文字列調整 |
| JPPOWER | Owner | Jaiprakash Associates / Jaypee 系 | owner_keywords に追加 |
| ESCORTS | Owner | Nanda 一族 + Kubota JV | owner_keywords (固有性高い keyword) |

### コミット完了

| コミット | 内容 | リモート |
|---------|------|---------|
| `903a35c` | feat(nse): yaml v0.5.0 — rev1 圏外 P0 10 件の web 裏取り判定を反映 | origin/main |
| `e962ed5` | docs(analyst): MTG メモと AI ファンドコンセプトのリサーチ集を追加 | origin/main |

## 決定事項

| ID | 内容 | コンテキスト |
|----|------|------------|
| dec-2026-05-08-001 | HCG の判定を Owner → Professional に訂正 (yaml v0.5.0 反映) | 2025/02 KKR controlling 54% 取得 ($400M) |
| dec-2026-05-08-002 | STYRENIX の判定を 保留 → Owner に確定 (yaml v0.5.0 反映) | 2022 年 Shiva Performance Materials 独立 buyout |

## アクションアイテム

### 完了 (2026-05-07/08)

| ID | 内容 | 状態 |
|----|------|------|
| act-2026-05-07-004 | yaml v0.5.0 適用 | ✅ completed |
| act-2026-05-07-005 | STYRENIX web 調査 | ✅ completed (act-004 内で実施) |

### Pending

| ID | 内容 | 優先度 | 依存 |
|----|------|--------|------|
| **act-2026-05-08-001** | yaml v0.5.1 で残 OWNER_WEAK 3 件 (NETWORK18/JPPOWER/ESCORTS) 解消 | 中 | 独立 |
| act-2026-05-07-002 | owner_companies.csv 確定 + analyst universe ISIN JOIN | 中 | 着手可 |

## 次回の議論トピック

- act-2026-05-08-001 (v0.5.1 残 3 件解消) の着手判断
- act-2026-05-07-002 (analyst universe 統合) との優先順位
- web 裏取り手法の標準化 (今後の P0 銘柄判定で「promoter_names + 直近 M&A 情報」の二重確認をデフォルトに)
- NIFTY 750 ラベリング完成宣言の判定基準 (現状 Recall 100%/Precision 98.8% で十分か)

## 参考: 学んだこと

### 1. ドメイン知識不足の代替アプローチ

ユーザーが Indian Owner 企業判定の専門知識を持たない場合、AI による web 裏取りが有効。Tavily 並列検索 (10 銘柄を 1 リクエストでカバー) で 5-10 分で完了。

### 2. promoter_names だけでは不十分

HCG の事例: promoter_names に "Ajaikumar" 一族と "HECTOR ASIA HOLDINGS II PTE. LTD." が混在。前者だけ見ると Owner、後者の正体 (KKR vehicle) を web で確認しないと正しく分類できない。

### 3. 「親会社不明 = 保留」は早計

STYRENIX の事例: Shiva Performance Materials が web で見つかりにくいが、INEOS からの独立 buyout 経緯を確認すれば Owner 確定可能。

## 保存先

- **Neo4j**:
  - Discussion: `disc-2026-05-08-yaml-v050-validation-and-commit`
  - Decision: `dec-2026-05-08-001` (HCG 訂正)、`dec-2026-05-08-002` (STYRENIX 訂正)
  - ActionItem: `act-2026-05-08-001` (v0.5.1 残 3 件)
  - リレーション: `(curr)-[:FOLLOWS]->(prev)`、`(disc)-[:RESULTED_IN]->(dec×2)`、`(disc)-[:PRODUCED]->(act-08-001)`、`(disc)-[:EXECUTED]->(act-07-004 / act-07-005)`、`(project-106)-[:HAS_DISCUSSION]->(disc)`
- **ドキュメント**: このファイル
- **コード**: `data/config/nse_promoter_classifier.yaml` v0.5.0 (commit `903a35c`)
- **生成物**: `notebook/NSE/data/exports/nse/yaml_v0.5.0_evidence.md` (web 裏取り根拠付きレポート)

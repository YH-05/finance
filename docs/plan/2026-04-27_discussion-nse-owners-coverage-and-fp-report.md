# 議論メモ: NSE owners.json 取得可否レポート + 偽陽性42件特定

**日付**: 2026-04-27
**議論ID**: `disc-2026-04-27-nse-owners-coverage-and-fp-report`
**前回議論**: `disc-2026-04-17-nse-owner-phase34-reconciliation`
**関連プロジェクト**: project-106 (NSE パッケージ拡張)
**関連 commit**: `4616332` docs(nse): owners.json取得可否+偽陽性レポートを追加

## 背景・コンテキスト

前回 (disc-2026-04-17-nse-owner-phase34-reconciliation) で nse_owner_analysis.ipynb を完成させ、owners.json 候補内 546 銘柄で Recall 97.7% / Precision 90.2% / F1 93.8% を達成。今回はユーザー要望により、改めて **owners.json 全 635 銘柄** に対する自前 NSE データ取得ロジックのカバレッジ全件確認と、自前ロジックが OWNER 判定したが owners.json では Owner 以外の偽陽性銘柄の特定を実施。

## 議論のサマリー

### 取得カバレッジ計測 (5分類指標)

owners.json (635 銘柄) を以下5ステータスに分類:

| ステータス | 件数 | 割合 | 説明 |
|---|---:|---:|---|
| **fully_covered** | **546** | **86.0%** | shareholdings + detail + owner_candidates すべて取得済 |
| **partially_covered** | 38 | 6.0% | shareholdings のみ取得（XBRL detail 未取得） |
| not_collected | 11 | 1.7% | stocks に存在するが Phase 3/4 対象外 |
| isin_unresolved | 16 | 2.5% | stocks.csv に ISIN 該当なし（上場廃止・REIT 等） |
| isin_missing | 24 | 3.8% | owners.json 側 ISIN 欄が空 |

**実質取得率 (fully + partially)**: 584 / 635 = **92.0%**

### Category 別カバレッジ

| Category | fully | partial | not_coll | isin_unres | isin_missing | 計 | 取得率 |
|---|---:|---:|---:|---:|---:|---:|---:|
| **Owner (428)** | **397** | 5 | 0 | 8 | 18 | 428 | **93.9%** |
| **MNC (44)** | 37 | 2 | 3 | 1 | 1 | 44 | **88.6%** |
| **State (84)** | 78 | 0 | 5 | 1 | 0 | 84 | **92.9%** |
| **Professional (78)** | 34 | 31 | 2 | 6 | 5 | 78 | **83.3%** |
| abb (1) | 0 | 0 | 1 | 0 | 0 | 1 | — |

### Owner カテゴリ部分取得 5 件（XBRL detail 未取得）

| Symbol | ISIN | 会社名 | 既知の理由 |
|---|---|---|---|
| `MFSL` | INE180A01020 | MAX FINANCIAL SERVICES LTD | promoter 1.25% 低値で Phase 4 対象外 |
| `ZEEL` | INE256A01028 | ZEE ENTERTAINMENT ENTERPRISE | promoter 3.99% 低値で Phase 4 対象外 |
| `DISHTV` | INE836F01026 | DISH TV INDIA LTD | promoter 4.04% 低値で Phase 4 対象外 |
| `ASTRAMICRO` | INE386C01029 | ASTRA MICROWAVE PRODUCTS LTD | promoter 6.54% 低値で Phase 4 対象外 |
| `360ONE` | INE466L01038 | 360 ONE WAM LTD | **promoter 14.2% (>10%) なのに detail_rows=0、別バグ (act-2026-04-17-011)** |

### Owner カテゴリ ISIN 由来取得不可 26 件

#### isin_unresolved 8 件（上場廃止・REIT — 取得不可）

| ISIN | 会社名 | 推定理由 |
|---|---|---|
| INE274G01010 | DHANI SERVICES LTD | 上場廃止 |
| INE752P01024 | FUTURE RETAIL LTD | 上場廃止 |
| INE140A01024 | PIRAMAL ENTERPRISES LTD | 上場廃止/組織再編 |
| INE886H01027 | TV18 BROADCAST LTD | 上場廃止 |
| INE0CCU25019 | MINDSPACE BUSINESS PARKS REIT | REIT |
| INE041025011 | EMBASSY OFFICE PARKS REIT | REIT |
| INE778U01029 | TCNS CLOTHING CO LTD | 上場廃止 |
| INE455F01025 | JAIPRAKASH ASSOCIATES LTD | 上場廃止 |

#### isin_missing 18 件（owners.json メンテ漏れ — 補完すれば取得可能）

JINDAL STEEL & POWER, CENTURY TEXTILES & INDS, INDIABULLS REAL ESTATE, INDIABULLS HOUSING FINANCE, GMR INFRASTRUCTURE, INFIBEAM AVENUES, AMARA RAJA BATTERIES, AEGIS LOGISTICS, ADANI TRANSMISSION, ADANI WILMAR, GLENMARK LIFE SCIENCES, AMI ORGANICS, WELSPUN INDIA, MAHINDRA LIFESPACE DEVELOPER, SWAN ENERGY, HBL POWER SYSTEMS, LT FOODS, D B REALTY

### 偽陽性 (FP) 42 件 — 自前=OWNER系 / owners.json≠Owner

| owners.json Category | 件数 | 主な性格 |
|---|---:|---|
| Professional | 28 | 金融機関・専門経営企業（HDFCBANK / RBLBANK / CUB / CROMPTON / LT 等） |
| State | 8 | 政府系企業の Director/KMP 名目保有による誤判定 |
| MNC | 6 | 多国籍企業の現地子会社で Director/KMP 名目保有 |

**全 42 件で `owner_confirmed_director_only` ルール起因と再確認**。dir_pct + kmp_pct が極めて低い（しばしば 0.001% 程度の名目 1 株保有）にもかかわらず、Tier 2 の director_only 判定で OWNER に流れ込む構造。

### 成果物

- `notebook/NSE/data/exports/nse/owners_coverage_and_false_positives.md` (279 行 / 17KB) — Category 別カバレッジ + 全 FP 銘柄テーブル + 取得不可銘柄一覧
- commit `4616332` で push 済み

## 決定事項

| ID | 内容 | コンテキスト |
|----|------|------------|
| dec-2026-04-27-001 | owners.json 取得カバレッジは 5 分類指標 (fully_covered / partially_covered / not_collected / isin_unresolved / isin_missing) で計測する | 単純な「取得 / 未取得」ではなく、ISIN 解決可否と Phase 4 detail 取得状況を分離して計測することで、改善余地を明確化（コード由来 vs データ由来） |
| dec-2026-04-27-002 | 偽陽性 42 件は Category 別に Professional 28 / State 8 / MNC 6 で確定。全件 owner_confirmed_director_only ルール起因 | act-2026-04-17-006 (director_only 厳格化) で改善対象。Professional の HDFCBANK/RBLBANK/CUB 系統は法人 promoter 配下の雇われ役員名目保有が典型 |
| dec-2026-04-27-003 | Owner 部分取得 5 件のうち 4 件 (MFSL/ZEEL/DISHTV/ASTRAMICRO) は低 promoter (1.25%-6.54%) による正当除外、1 件 (360ONE) のみ Phase 4 XBRL 取得失敗バグ | 部分取得=コード不具合ではなく、4/5 は仕様通り。360ONE のみ act-2026-04-17-011 で個別調査対象 |

## アクションアイテム

新規ActionItemなし。既存ActionItemの優先度を再確認:

| 既存 ID | 内容 | 優先度 | ステータス | 今回の根拠 |
|---|---|---|---|---|
| act-2026-04-17-006 | owner_confirmed_director_only ルール厳格化 (Precision 90.2→98%+) | **高** | pending | FP 42 件全件が起因と再確認、Professional 28 件への効果が最大 |
| act-2026-04-17-007 | Section 3/4 退避 CSV 自動マージロジック | 高 | pending | 変更なし |
| act-2026-04-17-010 | owners.json ISIN 欠損 18 件補完 | 中 | pending | カバレッジを 92.0% → 94.8% に押し上げる効果と確認 |
| act-2026-04-17-011 | 360ONE Phase 4 XBRL 取得失敗調査 | 低 | pending | 部分取得 5 件中 4 件は仕様通りで、唯一の真バグと判明 |

## 次回の議論トピック

- act-2026-04-17-006 の director_only ルール厳格化設計（dir_pct+kmp_pct≥1% 閾値 vs Tier 3 降格 の比較検証）
- act-2026-04-17-010 の ISIN 補完手段（stocks テーブル / NSE 公式 listing / SEBI listing から自動補完）
- 全 2,263 銘柄のフル実行タイミング（act-2026-04-13-001、現状 787 銘柄）

## 保存先

- **Neo4j**: 保存リトライ予定（docker volume マウント権限エラーで一時的に保存不可）
  - 予定 ID: Discussion `disc-2026-04-27-nse-owners-coverage-and-fp-report` + Decision ×3 (001/002/003)
  - リレーション: `(project-106)-[:HAS_DISCUSSION]->(disc)`, `(disc)-[:FOLLOWS]->(disc-2026-04-17-nse-owner-phase34-reconciliation)`, `(disc)-[:RESULTED_IN]->(dec ×3)`
- **ドキュメント**: `docs/plan/2026-04-27_discussion-nse-owners-coverage-and-fp-report.md` (このファイル)
- **レポート**: `notebook/NSE/data/exports/nse/owners_coverage_and_false_positives.md` (commit 4616332)

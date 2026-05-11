# 議論メモ: NSE オーナーラベリング yaml v0.5.1 実装 + NIFTY 750 universe 整備

**日付**: 2026-05-11
**議論ID**: `disc-2026-05-11-nse-owner-v051-implementation`
**前回 (計画フェーズ)**: `disc-2026-05-11-nse-owner-yaml-v051-plan`
**関連プロジェクト**: project-106 (NSE パッケージ拡張 + 全銘柄データ取得ノートブック)

## 背景・コンテキスト

計画フェーズ (`disc-2026-05-11-nse-owner-yaml-v051-plan`) で確定した方針に従い実装を実施。さらに `act-2026-05-07-002` (universe 整備) も同セッション内で完了。実装中にユーザーから「analyst universe (US銘柄中心) は今回の NSE オーナー企業抽出とは無関係。NIFTY 750 がユニバースである」という重要訂正を受けた。

## 実装したタスク

### 1. act-2026-05-11-018 完了 — yaml v0.5.1 + exclude_when 機構

**生成物**:
- `data/config/nse_promoter_classifier.yaml` v0.5.0 → **v0.5.1**
  - `exclude_when_also_matches: [keyword,...]` スキーマフィールド追加
  - RIL に `exclude_when_also_matches: ["Independent Media Trust"]` 追加 (NETWORK18)
  - JPPOWER 用 owner_keywords 2 件追加 (`JAIPRAKASH ASSOCIATES` / `JAYPEE INFRA VENTURES`)
  - ESCORTS 用 owner_keywords 3 件追加 (`NIKHIL NANDA` / `HAR PARSHAD AND COMPANY` / `NIKY TASHA`)
- `notebook/NSE/scripts/build_owner_review_sheet.py`:
  - `classify_promoter_names` に `exclude_when_also_matches` 評価追加 (10 行)
  - `apply_hybrid` に Tier 2/2.5 OWNER 昇格救済追加 (実装中追加判明、`dec-2026-05-11-007`)
- `notebook/NSE/data/exports/nse/owner_review_sheet.csv` 再生成 (800 行)
- `notebook/NSE/data/exports/nse/owner_review_summary.md` 再生成

**重要発見**: JPPOWER は `owner_flag=owner_probable_relatives_trust` (Tier 2)、yaml=OWNER だが、当初の hybrid ロジックは Tier 2 救済を実装していなかったため OWNER_WEAK に残った。Tier 2/2.5 用のハイブリッド救済 (yaml=OWNER → OWNER 昇格) を追加し解消。`owner_probable_nri_family` 7 件は yaml=UNKNOWN なので副作用なし。

**結果メトリクス**:
| 段階 | TP | FP | FN | TN | Precision | Recall | F1 | OWNER_WEAK |
|------|-----|-----|-----|-----|-----------|--------|-----|-----------|
| v0.5.0 (元) | 412 | 5 | 0 | 160 | 98.8% | 100% | 99.4% | 3 |
| **v0.5.1 (実測)** | **412** | **4** | **0** | **161** | **99.04%** | **100.00%** | **99.52%** | **0** |

8 監視銘柄全て期待通り (NETWORK18=NOT_OWNER/Professional 確定、JPPOWER/ESCORTS=OWNER 確定、HATHWAY/ALOKINDS/HINDZINC/TATACOMM/IDEA は副作用ゼロ)。

### 2. act-2026-05-07-002 完了 — NIFTY 750 universe 整備

**重要訂正** (`dec-2026-05-11-008`): NSE オーナー企業抽出の universe は **NIFTY 750 (800銘柄)**。analyst universe (US銘柄中心、investment_thesis や ca_strategy PoC 等) とは別軸。過去の議論で「analyst universe (300-400銘柄) と JOIN」と記述されていたが、それは誤りであり実体ファイルも存在しなかった。本訂正は `feedback_nse_universe_is_nifty750.md` にも保存。

**生成物**:
- `notebook/NSE/scripts/build_nifty750_universe.py` (新規 ~200 行) — Step 1-3 一括実装
- `notebook/NSE/data/exports/nse/owner_companies.csv` — 確定版 OWNER 企業 600 件
- `notebook/NSE/data/exports/nse/nifty750_universe.csv` — 800 銘柄 + メタデータ (is_owner_company / owner_family / is_nifty50/100/200/500/total_mkt)
- `notebook/NSE/data/exports/nse/nifty750_universe_summary.md` — Owner 比率 / family 別分布 / Index level 別分布

**全体サマリー**: OWNER 600 (75.0%) / NOT_OWNER 200 (25.0%)

**Index level 別 OWNER 比率** (中小型に行くほど Owner 比率が上がる):
| Index | 帰属銘柄数 | OWNER 数 | OWNER 比率 |
|-------|-----------|----------|-----------|
| NIFTY 50 | 44 | 27 | 61.4% |
| NIFTY 100 | 94 | 52 | 55.3% |
| NIFTY 200 | 184 | 109 | 59.2% |
| NIFTY 500 | 468 | 311 | 66.5% |
| NIFTY TOTAL MKT | 707 | 517 | **73.1%** |
| (5 index 圏外、rev1 補完銘柄) | 93 | 83 | 89.2% |

→ 2026-04-17 Web 調査仮説 (`dec-2026-04-17-013`: NIFTY 750 ≒ 70%) と整合。

**Owner family 上位**: Jindal 14 / Bajaj 13 / Adani 10 / Birla 9 / Mahindra 6 / Ambani 6 / Goenka (RPSG) 4 / Vedanta 3 / Rai Gupta (Havells) 3 / Mittal 3 / Wadia 3。family 未取得 OWNER 499 件 = Tier 1 自然人 promoter ベースで判定された銘柄。

## 決定事項 (本セッションで追加)

| ID | 内容 | ステータス |
|----|------|-----------|
| dec-2026-05-11-007 | build_owner_review_sheet.py で owner_probable_* / owner_via_individual_in_other (Tier 2/2.5) も yaml=OWNER 確定マッチで OWNER 昇格対象に追加。実装中 JPPOWER 残存問題から判明 | implemented |
| dec-2026-05-11-008 | NSE オーナー企業抽出の universe は NIFTY 750 (800銘柄)。analyst universe (US銘柄中心) とは別軸 | active |

(計画フェーズで確定済の dec-2026-05-11-003〜006 は全て status=implemented に更新済)

## アクションアイテム

### 完了

| ID | 内容 |
|----|------|
| act-2026-05-11-018 | yaml v0.5.1 リリース + exclude_when 機構実装 + 再実行で OWNER_WEAK 0 到達 |
| act-2026-05-07-002 | NIFTY 750 universe 整備 (owner_companies.csv 確定版 + nifty750_universe.csv + summary) |

### 次セッションへの pending

| ID | 内容 | 優先度 |
|----|------|--------|
| act-2026-05-11-019 | 9 ファイルを `/commit-and-pr` でコミット・PR 化。推奨タイトル: `feat(nse): owner classifier yaml v0.5.1 で OWNER_WEAK 0達成 + NIFTY 750 universe 整備 (Precision 99.04%/Recall 100%)` | 高 |
| act-2026-05-11-020 | pending のまま実質完了/代替済み 4 件のステータス整理 (act-2026-04-17-006/-007/-011, act-2026-04-16-005) | 中 |
| act-2026-05-11-021 | 完成宣言の判定。現状 Precision 99.04% / Recall 100% / F1 99.52% / OWNER_WEAK 0 で当面ゴール (NIFTY 750 ラベリング) は達成。Phase 6 (戦略統合) への移行可否 | 中 |

## 次回の議論トピック

- 完成宣言を出した後の Phase 6 (戦略統合) 設計
  - owner_companies.csv / nifty750_universe.csv を ca_strategy など他パッケージから利用する方法
  - data/processed/nse/ への配置等、消費側からの利便性
- act-2026-04-17-012 (期限 2026-05-31): OECD India Ownership Structure + NSE India Ownership Tracker (2025年6月) 精読
- 全 2,263 銘柄拡大 (act-2026-04-13-001 / dec-2026-05-07-001 で deferred) の再評価タイミング

## 保存先

- **Neo4j**:
  - Discussion: `disc-2026-05-11-nse-owner-v051-implementation`
  - Decision: `dec-2026-05-11-007`、`dec-2026-05-11-008` (本セッションで追加)
  - ActionItem: `act-2026-05-11-019/020/021` (pending)、`act-2026-05-11-018` (completed)、`act-2026-05-07-002` (completed)
  - リレーション: `(disc)-[:FOLLOWS]->(disc-2026-05-11-nse-owner-yaml-v051-plan)`、`(disc)-[:RESULTED_IN]->(dec-007/008)`、`(disc)-[:PRODUCED]->(act-019/020/021)`、`(disc)-[:EXECUTED]->(act-018, act-2026-05-07-002)`、`(project-106)-[:HAS_DISCUSSION]->(disc)`
- **ドキュメント**: このファイル
- **Memory**: `feedback_nse_universe_is_nifty750.md` (NSE universe = NIFTY 750 の訂正記録)
- **コード**:
  - `data/config/nse_promoter_classifier.yaml` v0.5.1
  - `notebook/NSE/scripts/build_owner_review_sheet.py` (Tier 2 拡張 + exclude_when)
  - `notebook/NSE/scripts/build_nifty750_universe.py` (新規)
- **データ**:
  - `notebook/NSE/data/exports/nse/owner_review_sheet.csv` (800 行、再生成)
  - `notebook/NSE/data/exports/nse/owner_review_summary.md`
  - `notebook/NSE/data/exports/nse/owner_companies.csv` (600 OWNER)
  - `notebook/NSE/data/exports/nse/nifty750_universe.csv` (800 銘柄 + メタデータ)
  - `notebook/NSE/data/exports/nse/nifty750_universe_summary.md`

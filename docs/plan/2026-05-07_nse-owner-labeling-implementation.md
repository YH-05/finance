# 議論メモ: NSE オーナー企業ラベリング 実装セッション

**日付**: 2026-05-07
**議論ID**: `disc-2026-05-07-nse-owner-labeling-implementation`
**前回**: `disc-2026-05-07-nse-owner-labeling-completion-plan` (計画フェーズ)
**関連プロジェクト**: project-106 (NSE パッケージ拡張 + 全銘柄データ取得ノートブック)

## 背景・コンテキスト

前セッションで立てた完成プラン (`disc-2026-05-07-nse-owner-labeling-completion-plan`) に従い、3 つの ActionItem を実装。さらに 13 銘柄の救済 + yaml v0.4.0 リリースを追加実施。

## 実装したタスク

### 1. act-2026-04-30-009 完了 — 787 銘柄レビューシート + ロジック体系ドキュメント

**生成物**:
- `notebook/NSE/data/exports/nse/owner_review_sheet.csv` — 全 787 (現在は 800) 銘柄、judge / hybrid / yaml_matched 列付き
- `notebook/NSE/data/exports/nse/owner_review_rev1_outside.csv` — rev1 圏外 223 銘柄抽出
- `notebook/NSE/data/exports/nse/owner_review_summary.md` — 集計サマリー
- `notebook/NSE/data/exports/nse/logic_system_review.md` — Tier 1-4 / yaml v0.3.0 / 限界事項を 8 章で整理
- `notebook/NSE/scripts/build_owner_review_sheet.py` — 生成スクリプト (yaml ハイブリッド + Tier 1.5 を Python 再実装)

**重要発見**: CSV の `owner_flag_final` 列はハイブリッドルール未適用。82 件の `owner_confirmed_director_only` がすべて OWNER のまま。Notebook Cell 13 で計算されるが export には反映されないため、Python 側で yaml v0.3.0 ロジックを再実装し `owner_flag_final_hybrid` 列を追加。

### 2. act-2026-05-07-003 完了 — rev1 圏内・Phase 3/4 圏外 13 銘柄救済

**対象**: 360ONE (C) + B 12 銘柄 (MAHLIFE/FINOPB/SANOFI/BALMLAWRIE/PGHH/GUJALKALI/PGHL/TICL/PSB/UTKARSHBNK/GUJGASLTD/KIOCL)

**実装**:
- `notebook/NSE/scripts/refetch_missing.py` — Phase 3+4 API 再取得検証
- `notebook/NSE/scripts/persist_and_classify.py` — DB 永続化 + Phase 5 分類
- 360ONE は Phase 3 取得済みだが Phase 4 (XBRL) のみ取得失敗 → API リトライで救済成功 (Phase 4: 66 行 + 過去四半期分も補完)
- B 12 銘柄は Phase 3 から取得失敗 → 全件再取得成功 (Phase 3+4 両方)
- yaml v0.4.0 で SANOFI/UTKARSHBNK/GUJGASLTD 用 keyword 追加
- ハイブリッドルールが ambiguous_holding_* に対して OWNER 救済しか扱っていなかったバグを修正 (Professional/STATE/MNC 確定処理を追加)

**結果**: 13 銘柄を owner_candidates に追加、12/13 が rev1 と一致 (TP/TN)

### 3. act-2026-05-07-001 完了 — rev1 圏外 223 銘柄レビュー

**生成物**:
- `notebook/NSE/data/exports/nse/rev1_outside_review.md` — P0-P4 別の表形式レビュードキュメント
- `notebook/NSE/data/exports/nse/rev1_outside_review.csv` — priority 列付き整形済み CSV
- `notebook/NSE/data/exports/nse/yaml_extension_candidates.md` — OWNER_WEAK 詳細 + 頻出グループ
- `notebook/NSE/data/exports/nse/yaml_v0.5.0_proposal.md` — yaml 拡張提案 (10 keyword 追加コード付き)
- `notebook/NSE/scripts/build_rev1_outside_review.py` — 生成スクリプト

**優先度分類**:
| 優先度 | 件数 | 内容 |
|--------|------|------|
| P0 | 10 | OWNER_WEAK (yaml 未マッチ、判定要) |
| P1 | 5 | Tier 1.5 救済済 (確認推奨) |
| P2 | 13 | 低 promoter (<30%) で OWNER 判定 (新興 IPO Owner-led) |
| P3 | 9 | yaml 確定済 director_only |
| P4 | 186 | Tier 1 高信頼 OWNER または明確 NOT_OWNER |

**P0 ドラフト判定** (要ユーザー承認):
- WAAREERTL → Owner (Doshi family、`WAAREE ENERGIES LIMITED`)
- HCG → Owner (Ajaikumar family、`AJAIKUMAR`)
- THYROCARE → Professional (PharmEasy 系、`API Holdings Limited`)
- FEDFINA → Professional (Federal Bank、`The Federal Bank Limited`)
- AXISCADES → Owner (Rajeev Chandrasekhar、`JUPITER CAPITAL`)
- REFEX → Owner (Jain family、`REFEX HOLDING`)
- GVT&D → MNC (GE Vernova、`GE Grid Solutions`)
- STYRENIX → 要 web 調査
- ITCHOTELS → Professional (ITC Limited、`ITC Limited`)
- JSFB → Professional (Jana Group、`JANA CAPITAL/HOLDINGS/URBAN FOUNDATION`)

## メトリクス推移

| 段階 | 銘柄数 | Intersection | TP | FP | FN | TN | Precision | Recall | F1 |
|------|--------|-------------|----|----|----|----|-----------|--------|-----|
| 元 (act-009 完了時) | 787 | 564 | 410 | 4 | 0 | 150 | 99.0% | 100% | 99.5% |
| +13 銘柄 (yaml v0.4.0) | **800** | **577** | **412** | **5** | **0** | **160** | **98.8%** | **100%** | **99.4%** |

## 決定事項

| ID | 内容 | ステータス |
|----|------|-----------|
| dec-2026-05-07-004 | yaml v0.4.0 リリース (SANOFI/UTKARSHBNK/GUJGASLTD 用 keyword 4 種追加) | implemented |
| dec-2026-05-07-005 | yaml v0.5.0 拡張案 (P0 10 件のうち 9 件分の 10 keyword 追加) | pending_approval |

## アクションアイテム

### 完了

| ID | 内容 | commit/成果物 |
|----|------|---------------|
| act-2026-04-30-009 | 787 銘柄レビューシート + ロジック体系ドキュメント | owner_review_sheet.csv / logic_system_review.md |
| act-2026-04-17-010 | owners.json ISIN 欠損 18 件補完 | rev1 採用 (act-2026-04-30-001) に吸収 |
| act-2026-05-07-001 | rev1 圏外 223 銘柄レビュー | rev1_outside_review.md / yaml_v0.5.0_proposal.md |
| act-2026-05-07-003 | rev1 圏内 Phase 3/4 圏外 13 銘柄救済 | yaml v0.4.0 / refetch_missing.py / persist_and_classify.py |

### Pending

| ID | 内容 | 優先度 | 依存 |
|----|------|--------|------|
| **act-2026-05-07-002** | owner_companies.csv 確定版 + analyst universe ISIN JOIN (act-2026-04-16-005 継続) | 中 | act-009 完了済 → 次着手可 |
| **act-2026-05-07-004** | yaml v0.5.0 適用 (10 keyword 追加 + 再実行) | 高 | dec-2026-05-07-005 承認後 |
| **act-2026-05-07-005** | STYRENIX web 調査 | 低 | 独立 |

## 次回の議論トピック

- yaml v0.5.0 (10 keyword 追加案) の承認可否
- WAAREERTL/HCG/AXISCADES/REFEX を Owner 認定する根拠の妥当性
- THYROCARE/FEDFINA/ITCHOTELS/JSFB を Professional 認定する根拠の妥当性
- act-2026-05-07-002 (analyst universe 統合) の着手判断
- 完成宣言の判定基準 (現状 Recall 100%/Precision 98.8% で十分か)

## 保存先

- **Neo4j**:
  - Discussion: `disc-2026-05-07-nse-owner-labeling-implementation`
  - Decision: `dec-2026-05-07-004` (yaml v0.4.0)、`dec-2026-05-07-005` (yaml v0.5.0 提案)
  - ActionItem: `act-2026-05-07-004` (yaml v0.5.0 適用)、`act-2026-05-07-005` (STYRENIX 調査)
  - リレーション: `(curr)-[:FOLLOWS]->(prev_plan)`、`(disc)-[:RESULTED_IN]->(dec×2)`、`(disc)-[:PRODUCED]->(act×2)`、`(disc)-[:EXECUTED]->(act-04-30-009 / act-05-07-001 / act-05-07-003)`、`(project-106)-[:HAS_DISCUSSION]->(disc)`、`(act-004)-[:BLOCKED_BY_APPROVAL]->(dec-005)`
- **ドキュメント**: このファイル (`docs/plan/2026-05-07_nse-owner-labeling-implementation.md`)
- **コード**: `notebook/NSE/scripts/{build_owner_review_sheet,refetch_missing,persist_and_classify,build_rev1_outside_review}.py`
- **データ**: `notebook/NSE/data/exports/nse/owner_review_sheet.csv` (800 銘柄)、`owner_candidates.csv` (800 銘柄、+13)、`shareholdings.csv` / `shareholding_detail.csv` (DB 再エクスポート)
- **設定**: `data/config/nse_promoter_classifier.yaml` v0.4.0

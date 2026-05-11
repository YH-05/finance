# 議論メモ: NSE オーナー成果物の整理 (廃止 trash + ロジックレビュー更新 + 履歴注釈)

**日付**: 2026-05-11
**議論ID**: `disc-2026-05-11-nse-owner-housekeeping`
**前回 (実装フェーズ)**: `disc-2026-05-11-nse-owner-v051-implementation`
**関連プロジェクト**: project-106 (NSE パッケージ拡張 + 全銘柄データ取得ノートブック)

## 背景・コンテキスト

project-106 Phase 5 完成 (yaml v0.5.1 + NIFTY 750 universe 整備) 後、`notebook/NSE/data/exports/nse/` および `notebook/NSE/scripts/` 配下に「最新成果物」と「過去のスナップショット」「廃止資料」が混在。今後の混同防止と将来の参照のため整理を実施。

## 議論のサマリー

ファイルを 4 区分に分類:

| 区分 | 件数 | 対応 |
|------|------|------|
| 🟢 現役 | 多数 | そのまま (`ARCHIVE_NOTES.md` で明示) |
| 🟡 履歴スナップショット | 9 | 注釈を追加 (混同防止) |
| 🔄 内容陳腐化したが構造的に必要 | 1 | 全面更新 (logic_system_review.md) |
| 🗑️ 廃止 (バージョン陳腐化) | 5 | trash 移動 + 復元手順記録 |

### A. 廃止ファイル trash 移動 (5 ファイル / 約 16 MB)

| ファイル | 廃止理由 |
|----------|----------|
| `yaml_v0.5.0_proposal.md` | dec-2026-05-07-005 で承認 → v0.5.0 リリース → さらに v0.5.1 へ更新済 |
| `yaml_v0.5.0_evidence.md` | v0.5.0 反映後、HCG/STYRENIX を v0.5.1 で訂正済 |
| `yaml_extension_candidates.md` | v0.5.0 提案の前段、v0.5.1 まで反映済 |
| `_shareholding_detail.csv` (Apr 17) | `shareholding_detail.csv` (May 7) で更新済 |
| `_shareholdings.csv` (Apr 17) | `shareholdings.csv` (May 7) で更新済 |

→ `trash/2026-05-11_nse-owner-obsolete/` へ `git mv` + `README.md` (関連 Neo4j ノード・復元手順を記録)

### B. logic_system_review.md の v0.5.1 化

主な更新:
- 生成日 2026-05-07 → **2026-05-11**
- 対象 787 → **800 銘柄**
- メトリクス TP=410/FP=4/Precision 99.0%/F1 99.5% → **TP=412/FP=4/Precision 99.04%/F1 99.52%**
- yaml v0.3.0 → **v0.5.1** (changelog 全反映)
- **新セクション**: Section 7 (`exclude_when_also_matches` 機構) + Tier 2/2.5 OWNER 昇格救済 (dec-2026-05-11-007)
- OWNER_WEAK 残 11 件 (rev1 圏外) → **0 件達成済**、解消経緯を表化
- 残 FP 4 件の最新内訳: INFY/STARHEALTH/KSB/**TICL** (旧版 "ITCHOTELS / その他1" → 実際は TICL に修正)
- 関連ファイル一覧を v0.5.1 ベースに刷新 (owner_companies.csv / nifty750_universe.csv 追加)

### C. 履歴ファイル 9 件の注釈追加

| ファイル種別 | 件数 | 注釈方式 |
|-------------|------|---------|
| `.md` | 2 | 冒頭に HISTORICAL SNAPSHOT ブロック (生成日・差分・最新参照先を明記) |
| `.py` | 2 | docstring に HISTORICAL SCRIPT 追記 (一回限り処理・再実行不要) |
| `.csv` / `.json` | 5 | 直接編集せず、共通 `ARCHIVE_NOTES.md` を新規作成 |

`ARCHIVE_NOTES.md`: 🟢 現役 / 🟡 履歴スナップショット / 🔵 関連スクリプト / 🗑️ 廃止済 の 4 区分で全 export ファイルを分類。最新メトリクス参照先と過去の差異も明示。

## 決定事項

| ID | 内容 | コンテキスト |
|----|------|-------------|
| dec-2026-05-11-009 | export 成果物の整理は 3 層アプローチ採用: (A) バージョン陳腐化は trash + README、(B) 内容陳腐化は最新版へ更新、(C) 履歴スナップショットは注釈で混同防止。データ系ファイル (csv/json) は直接編集せず ARCHIVE_NOTES.md で集約マップ | 本セッション、データファイル整合性 vs 混同防止の両立 |

## アクションアイテム

| ID | 内容 | 優先度 | 状態 |
|----|------|--------|------|
| **act-2026-05-11-022** | 本 housekeeping 変更 (合計 12 ファイル) を `/push` でコミット・プッシュ。推奨タイトル: `chore(nse): 廃止ファイル整理 + 履歴注釈追加 + logic_system_review v0.5.1 化` | 高 | pending |

## 次回の議論トピック

- act-2026-05-11-020 (pending のまま実質完了/代替済み 4 件のステータス整理) の実施
- act-2026-05-11-021 (完成宣言の判定 → Phase 6 戦略統合への移行) の実施
- 完成宣言後、`owner_companies.csv` / `nifty750_universe.csv` を ca_strategy など他パッケージから利用する設計

## 保存先

- **Neo4j**:
  - Discussion: `disc-2026-05-11-nse-owner-housekeeping`
  - Decision: `dec-2026-05-11-009` (3層クリーンアップ方式)
  - ActionItem: `act-2026-05-11-022` (housekeeping 変更のコミット・プッシュ)
  - リレーション: `(disc)-[:FOLLOWS]->(disc-2026-05-11-nse-owner-v051-implementation)`、`(project-106)-[:HAS_DISCUSSION]->(disc)`、`(disc)-[:RESULTED_IN]->(dec-009)`、`(disc)-[:PRODUCED]->(act-022)`
- **ドキュメント**: このファイル
- **新規ファイル**:
  - `trash/2026-05-11_nse-owner-obsolete/README.md`
  - `notebook/NSE/data/exports/nse/ARCHIVE_NOTES.md`
- **更新ファイル**:
  - `notebook/NSE/data/exports/nse/logic_system_review.md` (v0.5.1 ベースに全面更新)
  - `notebook/NSE/data/exports/nse/owners_coverage_and_false_positives.md` (HISTORICAL SNAPSHOT 注釈追加)
  - `notebook/NSE/data/exports/nse/rev1_diff_report.md` (HISTORICAL SNAPSHOT 注釈追加)
  - `notebook/NSE/scripts/refetch_missing.py` (HISTORICAL SCRIPT 注釈追加)
  - `notebook/NSE/scripts/persist_and_classify.py` (HISTORICAL SCRIPT 注釈追加)
- **trash 移動 (5 ファイル)**:
  - `trash/2026-05-11_nse-owner-obsolete/yaml_v0.5.0_proposal.md`
  - `trash/2026-05-11_nse-owner-obsolete/yaml_v0.5.0_evidence.md`
  - `trash/2026-05-11_nse-owner-obsolete/yaml_extension_candidates.md`
  - `trash/2026-05-11_nse-owner-obsolete/_shareholding_detail.csv`
  - `trash/2026-05-11_nse-owner-obsolete/_shareholdings.csv`

# 議論メモ: NSE オーナーラベリング 後続 Q&A から判明した知見

**日付**: 2026-05-11
**議論ID**: `disc-2026-05-11-nse-owner-clarifications-and-gaps`
**前回 (housekeeping)**: `disc-2026-05-11-nse-owner-housekeeping`
**関連プロジェクト**: project-106 (NSE パッケージ拡張 + 全銘柄データ取得ノートブック)

## 背景・コンテキスト

housekeeping 完了後 (commit `0e1ce89` push 済) のユーザー Q&A 3 件から得た追加知見を整理。完成成果物の確認、新 PC での再現性、運用パターンの 3 点。

## 議論サマリー

### Q1: オーナー企業フィルタリングロジックと結果のチェック先 (再掲)

整理後の状態 (housekeeping 適用後) では `ARCHIVE_NOTES.md` が全 export ファイルのインデックスとして機能。`logic_system_review.md` (v0.5.1 ベース) を最初の入り口として推奨。

### Q2: 他 PC での実行ノートブック特定

実行順序を文書化したところ、**Section 4 (AI レビュー) で手動介入が必要なボトルネック**が判明:

```
nse_full_download.ipynb (Phase 1-4: ~30-40 分)
    ↓
nse_owner_analysis.ipynb (Phase 5)
    ├─ Section 1-3: owner_candidates.csv 自動生成
    ├─ Section 4: AI レビュー結果統合 ← ⚠️ 手動 (現状ギャップ)
    └─ Section 5-6: 統計確認
    ↓
build_owner_review_sheet.py (yaml v0.5.1 ハイブリッド)
build_nifty750_universe.py (universe メタデータ)
```

現状は ambiguous_* 銘柄 (約 55 件) の `owner_flag_ai` 列が手動で `owner_candidates.csv` に埋まっている前提で動作。新 PC で再現するには (A) 既存 CSV を NAS/git 同期、(B) AI 自動化スクリプト実装、(C) 手動 AI 判定再実行、のいずれか。

### Q3: 完成成果物の存在確認

全成果物が yaml v0.5.1 ベースで完成済み・利用可能であることを確認:

| ファイル | データ行数 | 状態 |
|----------|-----------|------|
| owner_companies.csv | 600 | OWNER 確定企業 |
| nifty750_universe.csv | 800 | universe + メタデータ |
| nifty750_universe_summary.md | — | サマリー |
| owner_review_sheet.csv | 800 | レビュー用 |
| owner_review_summary.md | — | judge 集計 |
| owner_review_rev1_outside.csv | 223 | rev1 圏外抽出 |

**メトリクス**: Precision 99.04% / Recall 100% / F1 99.52% / OWNER_WEAK 0

### Q4 (運用): trash/ gitignore パターンの落とし穴

housekeeping 中に発生した実例:
- `trash/2026-05-11_nse-owner-obsolete/README.md` を作成 → `git add` で隠れた (gitignore 除外)
- `git mv` で tracked file を trash に移動した分は rename として履歴に残る (✅ commit 済)
- 新規 README は local-only (❌ commit 不可)
- 解決: `docs/plan/2026-05-11_obsolete-nse-files.md` に移動 + `ARCHIVE_NOTES.md` 内のリンク修正 (commit `d3e6730` / `298e287`)

→ **運用パターン化**: 廃止経緯は `docs/plan/{YYYY-MM-DD}_obsolete-{topic}.md` に置く

## 決定事項

| ID | 内容 | コンテキスト |
|----|------|-------------|
| dec-2026-05-11-010 | trash/ は .gitignore 除外のため、廃止ファイル経緯ドキュメントは docs/plan/{YYYY-MM-DD}_obsolete-{topic}.md として配置する。git mv で tracked file は trash に rename 移動できるが、trash 内の新規ファイルは local-only。経緯ドキュメントから trash 内ファイルへの参照を持たせ、将来 trash 削除されても廃止理由がトレース可能にする | 2026-05-11 housekeeping 中の実体験から確立 |

## アクションアイテム

| ID | 内容 | 優先度 | 状態 |
|----|------|--------|------|
| act-2026-05-11-023 | AI レビュー自動化スクリプト `notebook/NSE/scripts/run_ai_review.py` を新規実装し、新 PC でのフルパイプライン再現性を確保。スコープ: ambiguous_* 銘柄 (約 55 件) を抽出 → Anthropic API (Claude Sonnet) で promoter_names_full_list を入力に Owner/Professional/State/MNC を判定 → owner_flag_ai/ai_confidence/ai_reasoning 列を CSV に書き戻し | 中 | pending |

## 次回の議論トピック

- `act-2026-05-11-023` (AI レビュー自動化) の設計検討
  - 入力: owner_candidates.csv の ambiguous_* 行
  - 出力: owner_flag_ai 列を埋めた owner_candidates.csv
  - プロンプト設計: どの情報を Claude に渡すか (promoter_names のみ vs + ISIN + sub_category 内訳)
  - エラーハンドリング: API 失敗時の retry / fallback
- `act-2026-05-11-020` (pending 4 件のステータス整理) の実施
- `act-2026-05-11-021` (完成宣言の判定) の実施
- 新 PC 再現手順を `notebook/NSE/README.md` に明文化

## 参考情報

- Memory feedback 追加: `feedback_trash_gitignored_pattern.md`

## 保存先

- **Neo4j**:
  - Discussion: `disc-2026-05-11-nse-owner-clarifications-and-gaps`
  - Decision: `dec-2026-05-11-010` (trash/ gitignore 運用パターン)
  - ActionItem: `act-2026-05-11-023` (AI レビュー自動化)
  - リレーション: `(disc)-[:FOLLOWS]->(disc-2026-05-11-nse-owner-housekeeping)`、`(project-106)-[:HAS_DISCUSSION]->(disc)`、`(disc)-[:RESULTED_IN]->(dec-010)`、`(disc)-[:PRODUCED]->(act-023)`
- **ドキュメント**: このファイル
- **Memory**: `feedback_trash_gitignored_pattern.md` (新規)

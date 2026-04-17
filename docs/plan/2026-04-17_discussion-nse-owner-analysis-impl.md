# 議論メモ: NSE オーナー企業分析 notebook 実装 + AI 分類完了

**日付**: 2026-04-17
**議論ID**: `disc-2026-04-17-nse-owner-analysis-impl`
**関連プロジェクト**: `project-106: NSE パッケージ拡張 + 全銘柄データ取得ノートブック`
**前回議論**: `disc-2026-04-16-nse-owner-company-filter`

## 背景・コンテキスト

前回議論 (04-16) で確定した owner_flag ラベル体系 + 緩フィルタ + AI 判定の 2 段階パイプラインを実装に移した。上司条件「promoter>=10 AND 経営陣に Promoter group member」の XBRL データ上の解釈と、owners.json 手動ラベルとの照合検証を経て、最終的な分類を完了。

## 議論のサマリー

### owners.json ラベル逆解析 (370 件)

| フィルタ | Recall | Precision | F1 |
|---|---|---|---|
| hufi_num>=1 | 88.8% | 98.1% | 93.2 |
| natural_num>=1 | 96.6% | 82.6% | 89.1 |
| 複合 (hufi OR holding型+natural+not_MNC/State) | 94.6% | 93.0% | 93.8 |
| 100% recall (natural OR OtherIndian/Foreign>=10) | 100% | ~80% | — |

### 上司条件の XBRL マッピング

「経営陣に Promoter group member」= `DirectorsAndDirectorsRelatives >= 1 OR KeyManagerialPersonnel >= 1` の厳密解釈だと recall 82% (43件 Owner 漏れ)。XBRL filers が Individuals/HUF にのみ創業家を報告する慣習があるため、`hufi_num >= 1` も経営陣兼任の proxy として採用。

### 実装成果

- `nse_owner_analysis.ipynb` (19 セル): Section 1-5 で CSV 退避 + テーブル出力 + XBRL レポート + owner_flag 付与 + AI merge + 統計表示
- `nse_full_download.ipynb`: `PHASE3_EXTRA_OWNERS_JSON` パッチ適用 (owners.json Owner 銘柄を Phase 3 に自動追加 +75 銘柄)
- 49 銘柄 AI 分類: ai_owner 15 + ai_owner_weak 6 + ai_mnc 15 + ai_state 4 + ai_professional 9 → PENDING=0

### 最終分布

| owner_flag_final | 件数 |
|---|---|
| OWNER | 523 |
| OWNER_WEAK | 6 |
| NOT_OWNER | 72 |

## 決定事項

| ID | 内容 |
|----|------|
| dec-2026-04-17-001 | owner_flag: 4 Tier / 12 ラベル体系 (confirmed/probable/ambiguous/excluded) |
| dec-2026-04-17-002 | 緩フィルタ + AI アドホック判定 2 段階パイプライン。Claude Code subscription 使用 |
| dec-2026-04-17-003 | 単一 notebook 統合 (nse_owner_analysis.ipynb, 19 セル) |
| dec-2026-04-17-004 | CSV: symbol/company_name/isin 先頭、promoter_names は `|` 区切り、既存 CSV は `_` 退避 |
| dec-2026-04-17-005 | nse_full_download.ipynb に PHASE3_EXTRA_OWNERS_JSON 動的追加パッチ |
| dec-2026-04-17-006 | xbrl_category_reference.md を CSV と同フォルダに生成 (9 セクション、日本語+英語) |
| dec-2026-04-17-007 | Tier 2 (probable_*) も AI review 対象 |

## アクションアイテム

| ID | 内容 | 優先度 | ステータス |
|----|------|--------|----------|
| act-2026-04-17-001 | nse_full_download.ipynb で 75 追加銘柄 Phase 3/4 実行 | 高 | pending |
| act-2026-04-17-002 | NSE Board Composition API 調査 (Phase 5 用) | 中 | pending |
| act-2026-04-17-003 | nse_owner_analysis.ipynb を Jupyter で正式実行 + owners.json 照合 | 高 | pending |
| act-2026-04-17-004 | OWNER_WEAK 6 銘柄の最終判定を上司と確認 | 中 | pending |
| act-2026-04-17-005 | commit + push | 高 | pending |

## 前回 ActionItem の更新

| ID | 内容 | 新ステータス |
|----|------|------------|
| act-2026-04-16-001 | nse_owner_company_filter.ipynb 実行 | done (nse_owner_analysis.ipynb に統合・置換) |
| act-2026-04-16-002 | xbrl.py への関数化 Issue | done (notebook 層で先行実装完了) |

## 成果物

- `notebook/NSE/nse_owner_analysis.ipynb` — 統合分析 notebook (19 セル)
- `notebook/NSE/nse_full_download.ipynb` — PHASE3_EXTRA_OWNERS_JSON パッチ適用済み
- `notebook/NSE/_nse_owner_company_filter.ipynb` — 旧版退避
- `notebook/NSE/data/exports/nse/owner_candidates.csv` — 601 銘柄 × 30 列 (AI 判定完了)
- `notebook/NSE/data/exports/nse/shareholdings.csv` — 40,634 行
- `notebook/NSE/data/exports/nse/shareholding_detail.csv` — 46,103 行
- `notebook/NSE/data/exports/nse/xbrl_category_reference.md` — 12 KB

## 次回の議論トピック

- 75 追加銘柄のデータ取得後、owner_candidates.csv を更新して最終精度検証
- NSE Board Composition API 調査結果 → Phase 5 実装可否
- OWNER_WEAK 6 銘柄の上司判定結果
- owners.json との照合レポート (一致率、不一致分析)

## 保存先

- **Neo4j**: Discussion `disc-2026-04-17-nse-owner-analysis-impl` + Decision ×7 + ActionItem ×5
- **ドキュメント**: `docs/plan/2026-04-17_discussion-nse-owner-analysis-impl.md`

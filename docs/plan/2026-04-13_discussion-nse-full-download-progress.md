# 議論メモ: NSE 全銘柄データ取得ノートブック & market.nse パッケージ拡張 - 進捗

**日付**: 2026-04-13
**議論ID**: disc-2026-04-13-nse-full-download-progress
**参加**: ユーザー + AI

## 背景・コンテキスト

2026-04-13 に `/project-discuss` で NSE データ取得ロジックの実装状況を確認したところ、
`market.nse` パッケージに `corporate-share-holdings-master` エンドポイントと XBRL 解析機能が
未実装（スタンドアロン `scripts/` にのみ存在）であることが判明。詳細な株主構成データ
（Promoter / Public / FII / DII / Mutual Funds 等のカテゴリ別内訳）を取得するには、
この 2 機能のパッケージ統合が必要。

本議論では Option 2（パッケージ拡張 → ノートブック作成）を選択し、`/plan-project` で
GitHub Project #113（project-106）を立ち上げ、8 Issue に分解して**同日中に全実装完了・PR マージ**
まで進めた。本メモはその進捗サマリーと次回議論トピックを記録する。

## 議論のサマリー

### 設計議論（Option 選択）

1. **Option 1**（スクリプトロジックをノートブックにそのまま展開）
2. **Option 2**（パッケージ拡張 + 薄いノートブック）← **採用**
3. **Option 3**（スクリプトを subprocess 呼び出し + 可視化のみ）

Option 2 を選択した理由: テスト可能性、再利用性、パッケージ完成度向上。

### 実装方針 HF（Human Feedback）ゲート

Phase 1 で 4 つの情報ギャップを確認し、以下を決定:

1. `CorporateShareHolding` dataclass は **str 保持 + `to_float_*()` アクセサ**
2. XBRL マッピング定数（88 + 47 件）は **`xbrl.py` 内 module-private**
3. SQLite DB パスは **既存 `data/cache/nse/nse_index.db` と互換**
4. XBRL URL の SSRF 制限は **既存 `nsearchives.nseindia.com` のまま**

### タスク分解（8 タスク / 4 Wave）

- Wave 1: constants + types（#3925）
- Wave 2: xbrl.py + fixture（#3926）, parsers.py（#3927）
- Wave 3: Collector（#3928）+ テスト 3 本（#3929-3931）
- Wave 4: ノートブック + README + 実機検証（#3932）

### 実装完了（PR #3933）

- **マージ**: 2026-04-13T02:31:02Z（squash, `0efabc5`）
- **変更規模**: 28 ファイル / +5,056 / -128
- **新規**: `src/market/nse/xbrl.py` (+933 LOC), `collectors/share_holding.py`,
  `notebook/NSE/nse_full_download.ipynb`, `notebook/NSE/README.md`
- **テスト**: +1,200 LOC 以上（`test_xbrl.py` +505, `test_shareholding_collector.py` +402,
  `test_parse_corporate_shareholding.py` +280 等）
- **DEPRECATED**: `scripts/nse_parse_xbrl.py`, `scripts/nse_index_shareholding.py`

### クリーンアップ完了

- worktree `/Users/yukihata/Desktop/.worktrees/quants/feature-prj113` 削除
- ローカルブランチ `feature/issues-3925-3932` 削除
- ローカルブランチ `feature/prj113`（未使用オーファン）削除
- GitHub Project #113 の 8 Issue すべて `Done` に遷移（自動）

## 決定事項

| ID | 内容 | コンテキスト |
|----|------|------------|
| dec-2026-04-13-001 | `market.nse` パッケージに `corporate-share-holdings-master` + XBRL 解析を統合する（Option 2） | スクリプトの直接展開よりテスト可能性と再利用性を優先 |
| dec-2026-04-13-002 | `CorporateShareHolding` は str 保持 + `to_float_*()` アクセサで両対応 | 既存 `ShareholdingPattern` の str 保持方針と整合 |
| dec-2026-04-13-003 | XBRL マッピング定数（`_MEMBER_CATEGORY` 88件, `_AXIS_TO_SUBCATEGORY` 47件）は `xbrl.py` 内 module-private として配置 | 影響範囲を xbrl に限定、constants.py 肥大化回避 |
| dec-2026-04-13-004 | ノートブックの SQLite DB パスは `data/cache/nse/nse_index.db` で既存スクリプトと完全互換 | promoter_pct REAL 型互換を notebook 層で float 変換して実現 |
| dec-2026-04-13-005 | XBRL URL の SSRF 制限は既存 `ALLOWED_HOSTS`（nsearchives.nseindia.com 限定）のまま変更しない | 他ホストが来た場合は NseSession の既存 SSRF ガードで reject |
| dec-2026-04-13-006 | 既存スクリプト `scripts/nse_parse_xbrl.py` / `nse_index_shareholding.py` は削除せず DEPRECATED コメント追加 | 段階的移行、互換性維持 |

## アクションアイテム

| ID | 内容 | 優先度 | 状態 | 備考 |
|----|------|--------|------|------|
| act-2026-04-13-001 | ノートブック `notebook/NSE/nse_full_download.ipynb` を JupyterLab 等で実際に実行し、全 2,263 銘柄のデータを取得（所要 30-40 分） | 中 | pending | 実機検証は `LIMIT_SYMBOLS=10` で完了済み、フル実行は未実施 |
| act-2026-04-13-002 | 取得した SQLite DB (`data/cache/nse/nse_index.db`) を NAS `/Volumes/personal_folder/Projects/quants/data/sqlite/` へ手動コピー | 低 | pending | 既存決定 `dec-2026-04-08-014` の 2 段階方式に従う |
| act-2026-04-13-003 | `scripts/nse_parse_xbrl.py` / `nse_index_shareholding.py` の完全削除タイミングを検討 | 低 | pending | DEPRECATED 宣言中、次四半期で削除判断 |
| act-2026-04-13-004 | ASEAN/India 統合設計書（Issue #3900 Wave3）の作成着手 | 中 | pending | 前回 2026-04-08 議論から継続。`market_common` リネーム完了済み |
| act-2026-04-13-005 | Windows 環境での動作テスト（スクリプト + パッケージ版両方） | 低 | pending | 前回 2026-04-08 議論の継続項目 `act-2026-04-08-012` |

## 関連 GitHub リソース

- **GitHub Project**: [#113 Project-106: NSE パッケージ拡張 + 全銘柄データ取得ノートブック](https://github.com/users/YH-05/projects/113)
- **マージ済み PR**: [#3933 [Wave1-4] NSE: corporate-share-holdings 全実装](https://github.com/YH-05/quants/pull/3933)
- **Done 済み Issue**: #3925, #3926, #3927, #3928, #3929, #3930, #3931, #3932
- **計画書**: `docs/project/project-106/project.md`
- **元プラン**: `docs/project/project-106/original-plan.md`

## 次回の議論トピック

1. **フル実行結果の確認**: 全 2,263 銘柄取得後のデータ品質検証（期待行数との乖離、XBRL パース失敗率等）
2. **ASEAN/India 統合設計書**（Issue #3900 Wave3）: `market_common` リネーム完了後の次ステップ
3. **BSE モジュール再検討**: geo-block 問題の回避策（プロキシ経由 / 代替データソース）
4. **データ更新の自動化**: 四半期ごとに `corporate-share-holdings-master` を再取得する launchd / cron 設定

## 参考情報

- 既存議論: `docs/plan/2026-04-08_discussion-nse-scripts.md`（スクリプト整備経緯）
- 既存議論: `docs/plan/2026-04-08_discussion-asean-integration-design.md`（ASEAN 統合設計）
- Project #105: `docs/plan/2026-04-08_project-105-nse-pipeline-improvements.md`（前駆プロジェクト）

---

**最終更新**: 2026-04-13

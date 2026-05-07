# 議論メモ: NSE オーナー企業ラベリング完成プラン (NIFTY 750 スコープ確定)

**日付**: 2026-05-07
**議論ID**: `disc-2026-05-07-nse-owner-labeling-completion-plan`
**前回議論**: `disc-2026-04-30-nse-owners-rev1-evaluation`
**関連プロジェクト**: project-106 (NSE パッケージ拡張 + 全銘柄データ取得ノートブック)

## 背景・コンテキスト

`/project-discuss` でオーナー企業抽出スクリプトの進捗を一覧化。2026-04-30 の rev1 採用 + ハイブリッドルール導入で intersection 564 銘柄に対して Recall 100% / Precision 99.3% / F1 99.6% を達成済み。次に何をすべきかをユーザーと確認した。

## 議論のサマリー

### 現状診断 (NIFTY 750 ラベリング達成度)

| 観点 | 現状 | ギャップ |
|------|------|---------|
| 取得済銘柄数 | 787 銘柄 (Phase 3/4 完了) | NIFTY 750 ≒ 完了 |
| rev1 owners.json と intersection | 564 銘柄 | 64 銘柄が rev1 にあるが NSE 取得側で漏れ |
| intersection のラベリング精度 | Recall 100% / Precision 99.3% | 残 FP 3 件は構造的限界 (INFY/STARHEALTH/KSB) |
| rev1 圏外 223 銘柄 (787 − 564) | **未検証** (GT 無し、generated label のみ) | ラベル妥当性が未確認 |
| 最終アウトプット | `owner_companies.csv` 個別 export のみ | analyst universe (300-400 銘柄) との統合未着手 |

### ユーザー方針

> 「いまは NIFTY 750 の銘柄についてオーナー企業のラベリングができればそれで十分。次は何をすればいいか教えて。」

→ 全 2,263 銘柄拡大は当面スコープ外。NIFTY 750 (787 銘柄) のラベリング完成度向上とアウトプット整備に集中する。

### 推奨ステップ (順序付き)

1. **act-2026-04-30-009 (次着手)** — 全 787 銘柄目視レビューシート + ロジック体系ドキュメント作成
   - 特に rev1 圏外 223 銘柄を切り出してユーザー目視で誤判定をリストアップ
   - 必要なら `nse_promoter_classifier.yaml` を追補
2. **owner_companies.csv 確定版整備** — analyst universe (300-400 銘柄) と ISIN ベース JOIN
3. **deferred** — act-008 (2,263 銘柄拡大) / act-04-13-001 (フル実行) / act-04-17-002 (Board Composition API) / act-04-08-009 (NextApi 移行調査) は当面スコープ外

## 決定事項

| ID | 内容 | コンテキスト |
|----|------|------------|
| dec-2026-05-07-001 | NSE オーナー企業ラベリングの当面ゴールを NIFTY 750 (787 銘柄) のラベリング完成に限定。全 2,263 銘柄拡大は deferred | ユーザーが「NIFTY 750 で十分」と方針明示。Phase 5 拡大より現スコープの完成度向上を優先 |
| dec-2026-05-07-002 | 次の優先タスクは act-2026-04-30-009。rev1 圏外 223 銘柄のラベル妥当性をユーザー目視で確認することが NIFTY 750 完成判定の最終要件 | rev1 GT 圏外は generated label のみで未検証。完成宣言には目視レビューが必須 |
| dec-2026-05-07-003 | act-2026-04-30-009 完了後、owner_companies.csv を確定版アウトプットとして整備し analyst universe と ISIN ベース JOIN (act-2026-04-16-005 継続) | スクリプト構築の最終目的は投資ユニバース構築への活用。CSV export + universe 統合まで完了して「使える状態」になる |

## アクションアイテム

| ID | 内容 | 優先度 | 依存 | ステータス |
|----|------|--------|------|------------|
| act-2026-04-30-009 (既存) | 全 787 銘柄目視レビューシート + ロジック体系ドキュメント作成 | 高 | — | pending (次着手) |
| act-2026-05-07-001 | act-009 着手時に rev1 圏外 223 銘柄のラベル品質スポットチェックを優先実施 | 高 | act-04-30-009 | pending |
| act-2026-05-07-002 | owner_companies.csv 確定版 export + analyst universe (300-400 銘柄) と ISIN ベース JOIN | 中 | act-04-30-009 | pending |

## 次回の議論トピック

- act-2026-04-30-009 のレビューシート出力後、ユーザー目視で発見された誤判定の対応方針 (yaml 追補 / Tier 修正 / 諦めて FP/FN として記録)
- analyst universe との JOIN 結果における OWNER カバレッジ確認 (300-400 銘柄中で OWNER 比率はどの程度か)
- NIFTY 750 ラベリング完成宣言の判定基準 (Precision/Recall を維持できれば完成と見なすか、目視レビューで何件以上の確認が必要か)

## 参考: 既存進捗 (累計メトリクス推移)

| 段階 | TP | FP | FN | Precision | Recall | F1 |
|------|----|----|----|-----------|--------|-----|
| 初期評価 (4-17) | — | 42 | — | 90.2% | 97.7% | 93.8% |
| rev1 当初 (4-30) | 403 | 45 | 7 | 90.0% | 98.3% | 93.9% |
| act-004 ハイブリッド | 403 | 3 | 7 | 99.3% | 98.3% | 98.8% |
| act-A2 Tier 1.5 | 408 | 3 | 2 | 99.3% | 99.5% | 99.4% |
| act-005 yaml v0.3.0 (現状) | **410** | **3** | **0** | **99.3%** | **100.0%** | **99.6%** |

## 保存先

- **Neo4j**:
  - Discussion: `disc-2026-05-07-nse-owner-labeling-completion-plan`
  - Decision: `dec-2026-05-07-001` 〜 `dec-2026-05-07-003` (3 件)
  - ActionItem: `act-2026-05-07-001`, `act-2026-05-07-002` (2 件)
  - リレーション: `(curr)-[:FOLLOWS]->(prev)`, `(disc)-[:RESULTED_IN]->(dec×3)`, `(disc)-[:PRODUCED]->(act×2)`, `(project-106)-[:HAS_DISCUSSION]->(disc)`, `(act-05-07-*)-[:BLOCKED_BY]->(act-04-30-009)`
- **ドキュメント**: このファイル (`docs/plan/2026-05-07_discussion-nse-owner-labeling-completion-plan.md`)

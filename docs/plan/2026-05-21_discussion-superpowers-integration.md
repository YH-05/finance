# 議論メモ: superpowers の精密性を quants ワークフローに統合

**日付**: 2026-05-21
**議論ID**: disc-2026-05-21-superpowers-integration
**参加**: ユーザー + AI（Claude Opus 4.7）
**関連コミット**: `612f328` feat(.claude): superpowers の spec-reviewer 設計を /issue-implement と /plan-project に統合

## 背景・コンテキスト

quants では既存の `/plan-project` + `/issue-implement` ワークフローを使用しているが、superpowers プラグイン（`writing-plans` / `subagent-driven-development`）との差異が不明確だった。両者の本質的な違いを理解し、quants の既存ワークフローに足りない精密性を superpowers から補完する必要があった。

### セッション前の状態

- superpowers プラグイン (5.1.0) インストール済み（`~/.claude/plugins/cache/claude-plugins-official/superpowers/5.1.0/`）
- `/issue-implement-single` の Phase 5.5 は品質3観点のみ（pr-readability, pr-security-code, pr-test-coverage）
- 仕様準拠を独立検証するエージェントが存在しなかった
- feature-implementer に Self-Review 工程なし
- plan-project の HF3 はユーザー確認のみで、機械的な品質チェック（placeholder/coverage/命名）が無かった

## 議論のサマリー

### 論点1: superpowers と既存ワークフローの本質的差異

| 観点 | superpowers | quants 既存 |
|------|-------------|-------------|
| プラン粒度 | 2-5分のステップ（コード断片付き） | Issue 単位（≒ 機能ブロック） |
| プレースホルダ | **明示禁止**（"No Placeholders" ルール） | 制約なし |
| レビュー方式 | タスク毎に **spec → quality** の2段独立レビュー | PR 単位でまとめて品質レビュー |
| コンテキスト分離 | タスク毎に fresh subagent | Issue 毎に context: fork |
| モデル選択 | 複雑度で明示的に使い分け | 言及なし |
| 永続化 | プラン Markdown のみ | GitHub Project + Issue |

**結論**: 「精密実装力は superpowers が上、運用力は quants が上。両者は補完可能」。

### 論点2: spec-reviewer の本質

superpowers の spec-reviewer の特異な設計を確認:
- **実装者の自己申告を信用しない**前提
- コードを直接読んで Issue 要件と1行ずつ照合
- missing / extra / misunderstanding の3観点を `file:line` 付きで報告
- **過剰実装も違反**として叩く（普通の品質レビューには無い視点）
- code-quality-reviewer とは順序固定（spec 通過後に quality）

### 論点3: 6項目の補完案

| 案 | 内容 | 実装難度 | 効果 |
|----|------|---------|------|
| A | No Placeholders を project-decomposer に組込み | 低 | 中〜高 |
| B | plan-project に Self-Review ゲート追加 | 低 | 中 |
| C | pr-spec-compliance 追加 + Phase 5.5 を 3→4並列 | 中 | **最高** |
| D | Phase 5.5 ループ条件を観点別に分離 | 低 | 高 |
| E | feature-implementer Self-Review 追加 | 中 | 中 |
| F | モデル選択ガイドの注入 | 低 | 中 |

### 論点4: 実装範囲

ユーザー判断で **B, C, D, E** を採用、A と F は今回見送り。
理由（推測）: 最大効果の C を中心に、その効果を最大化する D と E、計画段階の品質を底上げする B を組み合わせた組み合わせがバランス良い。

## 決定事項

| ID | 内容 | コンテキスト |
|----|------|------------|
| dec-2026-05-21-001 | 仕様準拠（spec）と品質（quality）を独立観点として分離するレビューモデルを採用 | 過剰実装と仕様未達を品質観点と分けて検出するため。superpowers の spec/quality 2段レビュー思想を quants に移植 |
| dec-2026-05-21-002 | Phase 5.5 ループ条件を観点別に分離: 仕様準拠は最大3サイクルで BLOCKED、品質は最大2サイクルで警告続行 | 仕様外/未達のままコミットすると Issue の境界が破壊されるため、仕様準拠の "Accept 'close enough'" を禁止 |
| dec-2026-05-21-003 | plan-project に Phase 3.5 Self-Review ゲートを追加（placeholder/spec coverage/命名整合性） | HF3 でユーザーに「OK / 修正して再分解」を判断してもらう前に、機械的に検出可能な品質問題を先に潰す |
| dec-2026-05-21-004 | feature-implementer に Self-Review チェックリストを実装完了→コミット間に必須化 | 後段の pr-spec-compliance BLOCKED を未然に防ぐ。実装者自身に客観的な自己確認を強制 |
| dec-2026-05-21-005 | 補完案 A（No Placeholders）と F（モデル選択）は今回見送り、効果が最大の B, C, D, E を優先実装 | 段階的ロードマップとして、まず最大効果の組合せを先行投入 |

## アクションアイテム

| ID | 内容 | 優先度 | 期限 | 状態 |
|----|------|--------|------|------|
| act-2026-05-21-001 | 実装した補強を実 Issue で試運転（特に pr-spec-compliance の BLOCKED 発生頻度を観察） | 高 | 次回作業時 | pending |
| act-2026-05-21-002 | 補完案 A（No Placeholders を project-decomposer.md に組込み）の実装判断 | 中 | 試運転後 | pending |
| act-2026-05-21-003 | 補完案 F（モデル選択ガイドを issue-implement-single SKILL.md に注入）の実装判断 | 中 | 試運転後 | pending |
| act-2026-05-21-004 | plan-project と issue-implement のハイブリッド運用（Issue 本文に superpowers 流 bite-sized step を埋め込む）の試運転 | 低 | 試運転後 | pending |

**Neo4j 投入**: 2026-05-21 完了。Discussion 1件 + Decision 5件 + ActionItem 4件 + リレーション10件を MERGE 投入済み。`MATCH (d:Discussion {discussion_id: 'disc-2026-05-21-superpowers-integration'})` で参照可能。

## 実装成果物

### 新規作成

- `.claude/agents/pr-spec-compliance.md` (254行)
  - superpowers spec-reviewer の核心を反映
  - missing / extra / misunderstanding の3観点で `file:line` 付き報告
  - verdict: compliant / non_compliant の二値、extra_work 単独でも non_compliant
  - model: opus（判断密度の高いタスクに opus）

### 修正

- `.claude/skills/issue-implement-single/SKILL.md` (+189/-29)
  - Phase 5.5 を 3並列 → 4並列に拡張
  - 観点別ループ制御（仕様準拠 max 3 / BLOCKED、品質 max 2 / 警告続行）
  - blocked 時のサマリーフォーマット追加
- `.claude/agents/feature-implementer.md` (+100/-1)
  - Self-Review セクション新規追加（実装完了 → コミット前）
  - 受け入れ条件カバレッジ / 仕様外追加スキャン / 命名整合性の3チェック
  - 出力に `self_review` フィールド追加
- `.claude/skills/plan-project/SKILL.md` (+25/-2)
  - ワークフローに Phase 3.5 を挿入
  - HF3 の表示内容に Self-Review 結果を追加
  - データフローに `self-review.json` を追加
- `.claude/skills/plan-project/guide.md` (+172/-2)
  - Phase 3.5 詳細セクション追加（3チェックの実装手順 + JSON スキーマ）
  - HF3 表示フォーマットに警告セクション追加

合計: 5 files changed, +702 / -43 lines

## 次回の議論トピック

- **試運転結果のレビュー**: pr-spec-compliance が実際に missing/extra/misunderstanding を捕捉できるか、BLOCKED の発生頻度は妥当か
- **補完案 A の優先度判断**: project-decomposer に No Placeholders ルールを組み込むかどうか
- **補完案 F の優先度判断**: モデル選択（haiku/sonnet/opus）を Phase ごとに明示するかどうか
- **plan-project と issue-implement の併用パターン**: 例として「plan-project で Issue 作成 → 各 Issue 本文に superpowers writing-plans 流の bite-sized step を追記 → issue-implement で実行」というハイブリッド運用が成立するか

## 参考情報

### superpowers のリソース位置

- スキル本体: `~/.claude/plugins/cache/claude-plugins-official/superpowers/5.1.0/skills/`
- writing-plans SKILL.md
- subagent-driven-development SKILL.md
- spec-reviewer-prompt.md（pr-spec-compliance の設計ベース）
- code-quality-reviewer-prompt.md

### 関連ファイル（このセッションの変更対象）

- `.claude/agents/pr-spec-compliance.md` (新規)
- `.claude/skills/issue-implement-single/SKILL.md`
- `.claude/agents/feature-implementer.md`
- `.claude/skills/plan-project/SKILL.md`
- `.claude/skills/plan-project/guide.md`

### 関連コマンド

- `/plan-project` → Phase 3.5 Self-Review が組み込まれた
- `/issue-implement` → Phase 5.5 が 4並列化、ループ条件が観点別に
- `/commit-and-pr` → 後段の review-pr とは独立して機能

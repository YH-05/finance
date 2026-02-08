# /plan-project スキル実装計画

## Context

現在の `/new-project` は、軽量プロジェクトモード（10-12問インタビュー）とパッケージ開発モード（設計ドキュメント順次生成）の2パターンに限定されている。Python パッケージ以外の実装（エージェント、スキル、コマンド、ドキュメント等）に対応しておらず、リサーチフェーズが不在のため情報不足のまま計画が進む問題がある。

`/plan-project` は `/new-project` を完全に置き換え、Agent Teams を活用した「リサーチ→設計→タスク分解→GitHub Project 登録」のユニバーサルな計画ワークフローを提供する。

## ワークフロー概要

```
Phase 0: 初期化・方向確認 ─── [HF0] 方向確認
    ↓
Phase 1: リサーチ (project-researcher) ─── [HF1] リサーチ結果・ギャップ質問
    ↓
Phase 2: 計画策定 (project-planner) ─── [HF2] 計画承認
    ↓
Phase 3: タスク分解 (project-decomposer) ─── [HF3] タスク確認
    ↓
Phase 4: GitHub Project・Issue 登録 (plan-lead 直接) ─── 完了レポート
```

## Agent Team 構成

| メンバー | サブエージェントタイプ | 役割 |
|---------|---------------------|------|
| **plan-lead** | メイン会話（スキル読込） | HF ゲート管理、GitHub操作、全体オーケストレーション |
| **project-researcher** | 新規エージェント | コードベース探索、パターン識別、ギャップ分析 |
| **project-planner** | 新規エージェント | アーキテクチャ設計、ファイルマップ、リスク評価 |
| **project-decomposer** | 新規エージェント | タスク分解、依存関係、Wave グルーピング、Issue 準備 |

plan-lead はメイン会話エージェント自身が skill-preload で担当する（HF ゲートに AskUserQuestion が必要なため）。残り3体は Task ツールで起動し、`.tmp/plan-project-{session_id}/` ディレクトリ経由でデータを受け渡す。

## データフロー

```
.tmp/plan-project-{session_id}/
├── session-meta.json          ← Phase 0 出力
├── research-findings.json     ← Phase 1 出力 (project-researcher)
├── user-answers.json          ← HF1 出力 (ユーザー回答)
├── implementation-plan.json   ← Phase 2 出力 (project-planner)
├── task-breakdown.json        ← Phase 3 出力 (project-decomposer)
└── workflow-status.json       ← 進捗管理
```

## 各 Phase の詳細

### Phase 0: 初期化

- 引数からプロジェクトタイプを判定（`@src/*` → package, `--type agent` → agent, 等）
- セッションディレクトリ作成、`session-meta.json` 書出し
- **HF0**: タイプ確認 + 「何を作りたいか」の自由記述取得

### Phase 1: リサーチ（project-researcher）

- タイプに応じたディレクトリ探索（Glob/Grep/Read）
- 既存パターン・類似実装の発見
- 不足情報（information_gaps）の特定
- `gh issue list` で関連 Issue 確認
- **HF1**: リサーチ結果を提示、ギャップの質問を AskUserQuestion で実施

### Phase 2: 計画策定（project-planner）

- research-findings.json + user-answers.json を読み込み
- タイプ別アーキテクチャ設計（モジュール構造/エージェントトポロジー/スキル構造等）
- 作成・変更・削除ファイルマップ生成
- リスク評価
- **HF2**: 完全な計画書を提示、ユーザー承認を取得

### Phase 3: タスク分解（project-decomposer）

- implementation-plan.json を読み込み
- 1-2時間粒度でタスク分解
- 依存関係分析（明示・暗黙・循環検出）
- Wave グルーピング（並行開発可能なグループ化）
- Issue テンプレート生成（日本語タイトル・本文）
- **HF3**: タスクリスト + Mermaid 依存関係図を提示

### Phase 4: GitHub Project・Issue 登録（plan-lead 直接）

- `docs/project/project-{N}/project.md` 作成
- `gh project create` → `gh issue create` → `gh project item-add`
- project.md に Issue リンクを反映
- 完了レポート表示

## 作成するファイル一覧

### 新規作成（8ファイル）

| # | ファイルパス | サイズ | 説明 |
|---|------------|--------|------|
| 1 | `.claude/skills/plan-project/SKILL.md` | ~3KB | スキル定義（Phase 概要、タイプ一覧、使用例） |
| 2 | `.claude/skills/plan-project/guide.md` | ~15KB | 詳細ガイド（JSON スキーマ、エージェント協調、HF 仕様） |
| 3 | `.claude/skills/plan-project/templates/project-template.md` | ~2KB | project.md テンプレート |
| 4 | `.claude/skills/plan-project/templates/issue-template.md` | ~1KB | Issue 本文テンプレート |
| 5 | `.claude/agents/project-researcher.md` | ~3KB | コードベース調査エージェント |
| 6 | `.claude/agents/project-planner.md` | ~3KB | 実装計画エージェント |
| 7 | `.claude/agents/project-decomposer.md` | ~3KB | タスク分解エージェント |
| 8 | `.claude/commands/plan-project.md` | ~1.5KB | コマンド定義 |

### 変更するファイル（2ファイル）

| # | ファイルパス | 変更内容 |
|---|------------|----------|
| 1 | `CLAUDE.md` | `/plan-project` をコマンド・スキル・エージェント各テーブルに追加。`/new-project` を非推奨表記に変更 |
| 2 | `.claude/skills/new-project/SKILL.md` | 冒頭に非推奨メッセージと `/plan-project` への誘導を追加 |

### 削除なし

`/new-project` は非推奨メッセージ付きで残す（即時破壊を避ける）。

## 実装順序

### Wave 1: 基盤（依存なし）
1. `.claude/skills/plan-project/SKILL.md` — スキル定義
2. `.claude/skills/plan-project/templates/project-template.md` — テンプレート
3. `.claude/skills/plan-project/templates/issue-template.md` — テンプレート

### Wave 2: エージェント定義（SKILL.md を参照）
4. `.claude/agents/project-researcher.md`
5. `.claude/agents/project-planner.md`
6. `.claude/agents/project-decomposer.md`

### Wave 3: 詳細ガイド（Wave 1+2 の内容を参照）
7. `.claude/skills/plan-project/guide.md`

### Wave 4: コマンド・登録（全体完成後）
8. `.claude/commands/plan-project.md`
9. `CLAUDE.md` 更新
10. `.claude/skills/new-project/SKILL.md` 非推奨メッセージ追加

## 再利用する既存リソース

| リソース | パス | 用途 |
|---------|------|------|
| task-decomposition スキル | `.claude/skills/task-decomposition/` | project-decomposer が参照するタスク分解手法 |
| task-decomposer エージェント | `.claude/agents/task-decomposer.md` | 双方向同期・Issue 操作のパターン参照 |
| new-project テンプレート | `.claude/skills/new-project/template.md` | project.md テンプレートのベース |
| 既存コマンドパターン | `.claude/commands/finance-research.md` | Phase 構造・HF ゲート・完了レポートのパターン |
| サブエージェントデータ渡しルール | `.claude/rules/subagent-data-passing.md` | JSON 完全データ渡しの規約 |

## 検証方法

1. `/plan-project` をインタラクティブモードで実行し、全5 Phase が正常に進行することを確認
2. 各 HF ゲートで AskUserQuestion が適切に表示されることを確認
3. `.tmp/plan-project-{session_id}/` に全 JSON ファイルが生成されることを確認
4. `gh project list` で GitHub Project が作成されていることを確認
5. `gh issue list` で Issue が登録されていることを確認
6. `docs/project/project-{N}/project.md` の内容に Issue リンクが含まれていることを確認

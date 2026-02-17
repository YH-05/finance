---
name: plan-project
description: |
  リサーチ→設計→タスク分解→GitHub Project 登録のユニバーサルな計画ワークフロー。
  /plan-project コマンドで使用。
  Python パッケージ、エージェント、スキル、コマンド、ドキュメント等あらゆるプロジェクトタイプに対応。
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, AskUserQuestion, Task
---

# Plan Project

リサーチベースのプロジェクト計画ワークフローを提供するスキルです。

## 概要

Agent Teams を活用した「リサーチ→設計→タスク分解→GitHub Project 登録」の4フェーズワークフローで、あらゆるプロジェクトタイプに対応します。

## 対応プロジェクトタイプ

| タイプ | 判定条件 | 主な成果物 |
|--------|---------|-----------|
| **package** | `@src/*` 引数 | `src/` 配下の Python パッケージ |
| **from_plan_file** | `@docs/plan/*` 引数 | プランファイルから推測したタイプ（Phase 4 でプランファイルを `original-plan.md` として移動） |
| **agent** | `--type agent` | `.claude/agents/` 配下のエージェント定義 |
| **skill** | `--type skill` | `.claude/skills/` 配下のスキル定義 |
| **command** | `--type command` | `.claude/commands/` 配下のコマンド定義 |
| **workflow** | `--type workflow` | スキル+エージェント+コマンドの組み合わせ |
| **docs** | `--type docs` | `docs/` 配下のドキュメント |
| **general** | 引数なし or テキスト | タイプ混合の汎用プロジェクト |

## 使用方法

```bash
# 汎用（インタラクティブ）
/plan-project

# プロジェクト名指定
/plan-project "認証システムの実装"

# タイプ指定
/plan-project --type agent "ニュース分析エージェント"

# パッケージ開発
/plan-project @src/market_analysis/docs/project.md

# プランファイルから実行（プランファイルは Phase 4 で移動）
/plan-project @docs/plan/2026-02-15_example.md
```

## ワークフロー

```
Phase 0: 初期化・方向確認 ─── [HF0] 方向確認
    |
Phase 1: リサーチ (project-researcher) ─── [HF1] リサーチ結果・ギャップ質問
    |
Phase 2: 計画策定 (project-planner) ─── [HF2] 計画承認
    |
Phase 3: タスク分解 (project-decomposer) ─── [HF3] タスク確認
    |
Phase 4: GitHub Project・Issue 登録 (plan-lead 直接) ─── 完了レポート
```

### HF（Human Feedback）ゲート

各フェーズ完了時に AskUserQuestion でユーザー確認を取得。
確認なしには次フェーズに進まない。

| ゲート | タイミング | 確認内容 |
|--------|-----------|---------|
| HF0 | Phase 0 完了時 | プロジェクトタイプ・方向性の確認 |
| HF1 | Phase 1 完了時 | リサーチ結果の確認、情報ギャップへの回答 |
| HF2 | Phase 2 完了時 | 実装計画の承認 |
| HF3 | Phase 3 完了時 | タスクリスト・依存関係の確認 |

## Agent Team 構成

| メンバー | エージェントタイプ | 役割 |
|---------|------------------|------|
| **plan-lead** | メイン会話（スキル読込） | HF ゲート管理、GitHub操作、全体制御 |
| **project-researcher** | `.claude/agents/project-researcher.md` | コードベース探索、パターン識別、ギャップ分析 |
| **project-planner** | `.claude/agents/project-planner.md` | アーキテクチャ設計、ファイルマップ、リスク評価 |
| **project-decomposer** | `.claude/agents/project-decomposer.md` | タスク分解、依存関係、Wave グルーピング |

## データフロー

```
.tmp/plan-project-{session_id}/
├── session-meta.json          <- Phase 0 出力
├── research-findings.json     <- Phase 1 出力
├── user-answers.json          <- HF1 出力
├── implementation-plan.json   <- Phase 2 出力
├── task-breakdown.json        <- Phase 3 出力
└── workflow-status.json       <- 進捗管理
```

## リソース

### ./guide.md

詳細ガイド（JSON スキーマ、エージェント協調手順、HF ゲート仕様）。

### ./templates/project-template.md

`docs/project/project-{N}/project.md` 生成用テンプレート。

### ./templates/issue-template.md

GitHub Issue 本文テンプレート。

## 完了条件

- [ ] 全 HF ゲートを通過している
- [ ] `.tmp/plan-project-{session_id}/` に全 JSON ファイルが生成されている
- [ ] `docs/project/project-{N}/project.md` が作成されている
- [ ] プランファイルが指定されていた場合、`docs/project/project-{N}/original-plan.md` として移動されている
- [ ] GitHub Project が作成されている
- [ ] Issue が登録されている
- [ ] 完了レポートが表示されている

## 関連

- **前身**: `/new-project`（非推奨）
- **後続**: `/plan-worktrees`, `/issue-implement`
- **参照スキル**: `task-decomposition`, `project-management`

---
description: GitHub Issue番号から自動実装・PR作成まで一括実行
---

# /issue-implement - Issue 自動実装

> **役割の明確化**: このコマンドは **Issue から PR 作成までの完全自動化** に特化しています。
>
> - テスト作成のみ → `/write-tests`
> - 品質チェックのみ → `/ensure-quality`
> - PR作成のみ → `/commit-and-pr`

**目的**: GitHub Issue 番号を指定し、開発タイプに応じた適切なワークフローで実装→PR作成を一括実行

## 対応する開発タイプ

| タイプ | 対象 | ワークフロー |
|--------|------|--------------|
| `python` | Pythonコード開発 | テスト作成→実装→品質保証→PR作成 |
| `agent` | エージェント開発 | 要件分析→設計・作成→検証→PR作成 |
| `command` | コマンド開発 | 要件分析→設計・作成→検証→PR作成 |
| `skill` | スキル開発 | 要件分析→設計・作成→検証→PR作成 |

## 使用例

```bash
/issue-implement 123
```

## スキルの呼び出し

このコマンドは **issue-implementation** スキルを使用します。

**スキル情報**:

- **スキル名**: issue-implementation
- **配置先**: `.claude/skills/issue-implementation/`
- **主な機能**:
  - 開発タイプ判定: ラベル・キーワードから適切なワークフローを自動選択
  - Python ワークフロー: テスト作成→実装→品質保証→PR作成
  - Agent/Command/Skill ワークフロー: 要件分析→設計・作成→検証→PR作成
  - 自動品質チェック: make check-all の自動実行と修正

## 処理フロー

```
/issue-implement {number}
    │
    └─ Skill ツールで issue-implementation スキルを呼び出し
        │
        ├─ Phase 0: Issue検証・タイプ判定
        │   ├─ gh issue view {number}
        │   ├─ チェックリスト抽出
        │   └─ 開発タイプ判定（python/agent/command/skill）
        │
        ├─ 開発タイプに応じたワークフロー
        │   ├─ python: Phase 1-5
        │   ├─ agent: Phase A1-A4
        │   ├─ command: Phase C1-C4
        │   └─ skill: Phase S1-S4
        │
        └─ 完了処理・レポート出力
```

## 引数の渡し方

コマンドの引数は **$ARGUMENTS** プレースホルダーでスキルに渡されます。

**例**:

- `/issue-implement 123` → `$ARGUMENTS = "123"`
- `/issue-implement 456` → `$ARGUMENTS = "456"`

## サブエージェント連携

| エージェント | 用途 |
|--------------|------|
| test-writer | テスト作成（Python実装） |
| feature-implementer | TDD実装（Python実装） |
| quality-checker | 品質自動修正 |
| code-simplifier | コード整理 |
| agent-expert | エージェント作成 |
| command-expert | コマンド作成 |
| skill-expert | スキル作成 |

## 関連スキル

| スキル | 用途 |
|--------|------|
| issue-creation | Issue 作成・タスク分解 |
| issue-implementation | Issue の自動実装（このコマンド） |
| issue-refinement | Issue のブラッシュアップ |
| issue-sync | コメントからの同期 |

## 詳細情報

詳細なガイドラインとテンプレートは以下のスキルリソースを参照:

- `.claude/skills/issue-implementation/SKILL.md` - スキル定義
- `.claude/skills/issue-implementation/guide.md` - 詳細ガイド
- `.claude/skills/issue-implementation/template.md` - 完了レポートテンプレート

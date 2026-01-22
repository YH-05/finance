---
description: プロジェクト全体の適合性チェックとタスク再構成を行う
skill: project-management
---

# /project-refine - プロジェクト健全性チェック & 再構成

このコマンドは project-management スキルを使用してプロジェクトの整合性を検証します。

> **役割の明確化**: このコマンドは **プロジェクト全体の整合性検証とタスク最適化** に特化しています。
>
> - 個別 Issue のブラッシュアップ → `/issue-refine`
> - Issue の新規作成・同期 → `/issue`
> - 並列開発計画 → `/plan-worktrees`

## コマンド構文

```bash
# パッケージ開発モード
/project-refine @src/<library_name>/docs/project.md

# 軽量プロジェクトモード
/project-refine @docs/project/<project-slug>.md

# GitHub Project 番号を直接指定
/project-refine <project_number>
```

## 処理概要

1. GitHub Project / Issues / project.md を読み込み
2. 適合性チェック（依存関係・優先度・ステータス矛盾）
3. 問題の重大度分類と一覧表示
4. タスク再構成の提案生成
5. ユーザー確認後に修正を適用
6. 結果レポートを表示

## チェック項目

| カテゴリ | チェック項目 | 重大度 |
|----------|--------------|--------|
| 依存関係 | 循環依存 | 🔴 Critical |
| 依存関係 | 完了タスクへの未完了依存 | 🟠 Warning |
| 優先度 | 高優先度が低優先度に依存 | 🟠 Warning |
| 優先度 | ブロッカーの優先度が低い | 🟠 Warning |
| ステータス | GitHub vs project.md 不整合 | 🟠 Warning |
| ステータス | GitHub vs Project 不整合 | 🟠 Warning |
| 構造 | 孤立タスク | 🟡 Info |
| 担当者 | 過負荷（3件以上 in_progress） | 🟡 Info |
| 担当者 | 高優先度タスクが未割当 | 🟡 Info |

## 修正適用モード

AskUserQuestion で以下のモードを選択:

1. **すべて自動修正（推奨）**: Critical と Warning を自動修正、Info は表示のみ
2. **個別に確認**: 各修正を個別に確認してから適用
3. **レポートのみ**: 修正は行わず、レポートのみ出力

## 詳細ガイド

詳細な処理手順、アルゴリズム、エラーハンドリングについては project-management スキルを参照:

- **SKILL.md**: `.claude/skills/project-management/SKILL.md`
- **ガイド**: `.claude/skills/project-management/guide.md`

## 関連コマンド

- `/new-project`: プロジェクト作成（パッケージ開発/軽量モード）
- `/issue`: GitHub Issue と project.md の双方向同期
- `/issue-refine`: 個別 Issue のブラッシュアップ
- `/plan-worktrees`: 並列開発計画

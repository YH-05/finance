---
summary: "worktree作成時は /worktree コマンド（Skillツール）を使用する。git worktree add を直接使用しない"
created: 2026-01-14
status: resolved
tags: [worktree, git, workflow, skill]
---

# Worktree 作成ルール

## ルール

worktree を作成する際は、必ず `/worktree` コマンド（Skill ツール）を使用する。

## 禁止事項

```bash
# 直接 git worktree add を使用しない
git worktree add -b feature/xxx /path/to/worktree main  # NG
```

## 正しい方法

```bash
# Skill ツールで /worktree コマンドを使用
/worktree feature/issue-64
/worktree feature/issue-67
```

## 複数の worktree を作成する場合

各 worktree ごとに `/worktree` コマンドを順番に実行する。

```bash
/worktree feature/issue-64  # 1つ目
/worktree feature/issue-67  # 2つ目
```

## 理由

- `/worktree` コマンドは以下を自動で行う:
  - 事前チェック（ブランチ存在確認、リポジトリ確認）
  - 適切なパスへの worktree 作成
  - `.mcp.json` のコピー
  - 次のステップの案内

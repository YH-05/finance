---
name: create-worktrees
description: "/plan-worktreesの結果から複数のworktreeを一括作成するスキル。Issue番号のリストを受け取り、各Issueに対して/worktreeコマンドを順番に実行する。"
---

# Create Worktrees - 複数Worktree一括作成

`/plan-worktrees` の結果を受けて、複数の worktree を一括で作成します。

## 使用例

```bash
# Issue番号を指定して一括作成
/create-worktrees 64 67

# Wave 1 の Issue を一括作成
/create-worktrees 64 67 --wave 1
```

## 実行フロー

### ステップ 1: 引数解析

引数から Issue 番号のリストを取得:
- スペース区切りで複数の Issue 番号を指定
- 各 Issue に対して `feature/issue-{番号}` 形式のブランチを作成

### ステップ 2: 各 Issue に対して /worktree を実行

**重要**: 直接 `git worktree add` を使用せず、必ず `/worktree` コマンド（Skill）を使用する。

各 Issue 番号に対して順番に実行:

```bash
/worktree feature/issue-64
/worktree feature/issue-67
```

### ステップ 3: 結果サマリー

```
================================================================================
✅ Worktree 一括作成完了
================================================================================

| Issue | ブランチ | パス | 状態 |
|-------|----------|------|------|
| #64 | feature/issue-64 | ~/.worktrees/finance/feature-issue-64 | ✓ 作成済み |
| #67 | feature/issue-67 | ~/.worktrees/finance/feature-issue-67 | ✓ 作成済み |

## 開発開始

各 worktree で開発を開始:

cd /path/to/worktree
claude

================================================================================
```

## 注意事項

1. **必ず /worktree コマンドを使用**: `git worktree add` を直接使用しない
2. **順番に実行**: 各 worktree は順番に作成する（並列実行しない）
3. **エラー時も継続**: 1つの worktree 作成に失敗しても、残りは継続して作成

## 関連コマンド

| コマンド | 説明 |
|----------|------|
| `/plan-worktrees` | 並列開発計画の作成（Wave グルーピング） |
| `/worktree` | 単一の worktree を作成 |
| `/worktree-done` | worktree の完了とクリーンアップ |

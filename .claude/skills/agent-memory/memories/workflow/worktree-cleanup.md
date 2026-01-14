---
summary: "worktree 削除時は /worktree-done コマンドを使用する（git worktree remove を直接使わない）"
created: 2026-01-14
tags: [worktree, git, workflow]
---

# Worktree 削除の規則

## ルール

worktree を削除する場合は、`git worktree remove` を直接実行せず、**`/worktree-done` コマンド**を使用すること。

## 理由

`/worktree-done` コマンドは以下を自動的に処理する:
- PR のマージ状態確認
- worktree のクリーンアップ
- ブランチの削除
- 適切なエラーハンドリング

## 正しい使い方

```bash
# ✅ 正しい
/worktree-done feature/issue-49

# ❌ 避ける
git worktree remove /path/to/worktree
```

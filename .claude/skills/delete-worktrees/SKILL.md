---
name: delete-worktrees
description: 複数のworktreeとブランチを一括削除するスキル。
/delete-worktrees コマンドで使用。開発完了後、複数のworktreeを効率的にクリーンアップする。

allowed-tools: Read, Bash
---

# Delete Worktrees - 複数Worktree一括削除

複数の worktree とブランチを一括で削除します。

**目的**: 開発完了後、複数の worktree を効率的にクリーンアップ

## 使用例

```bash
# ブランチ名を指定して一括削除
/delete-worktrees feature/issue-64 feature/issue-67

# 3つ以上も可能
/delete-worktrees feature/issue-64 feature/issue-65 feature/issue-66
```

---

## ステップ 0: 引数解析

1. 引数からブランチ名のリストを取得（スペース区切り）
2. **引数がない場合**: 現在のworktree一覧を表示してエラー

```
エラー: 削除するブランチ名を指定してください。

使用方法:
  /delete-worktrees <branch-name1> <branch-name2> ...

例:
  /delete-worktrees feature/issue-64 feature/issue-67

現在のworktree一覧:
<git worktree list の出力>
```

---

## ステップ 1: 各ブランチに対して /worktree-done を実行

**重要**: 直接 `git worktree remove` を使用せず、必ず `/worktree-done` コマンド（Skill ツール）を使用する。

各ブランチ名に対して順番に `/worktree-done` を実行:

```bash
# feature/issue-64 のクリーンアップ
Skill tool: /worktree-done feature/issue-64

# feature/issue-67 のクリーンアップ
Skill tool: /worktree-done feature/issue-67
```

### 実行手順

1. ブランチ名のリストを取得
2. 各ブランチに対して Skill ツールで `/worktree-done {ブランチ名}` を実行
3. 次のブランチに進む
4. 全て完了するまで繰り返す

---

## ステップ 2: 結果サマリー

```
================================================================================
✅ Worktree 一括削除完了
================================================================================

削除数: X 件

| ブランチ | 状態 | 結果 |
|----------|------|------|
| feature/issue-64 | 成功 | worktree, ローカル, リモート削除済み |
| feature/issue-67 | 成功 | worktree, ローカル, リモート削除済み |

## 次のステップ

- 新しい開発を開始: /worktree <feature-name>
- 並列開発計画: /plan-worktrees <project-number>
- メインリポジトリに移動: cd <main-repo-path>

================================================================================
```

---

## エラーハンドリング

| ケース | 対処 |
|--------|------|
| 引数未指定 | エラーメッセージと現在のworktree一覧を表示 |
| worktreeが見つからない | 警告を表示し、次のブランチへ継続 |
| PRが未マージ | `/worktree-done` のエラー処理に従う（スキップまたは中断） |
| 削除失敗 | エラーを表示し、残りのブランチは継続 |

### エラー時の継続判断

各ブランチの削除は独立しているため、1つのブランチで失敗しても残りは継続します。

```
⚠️ feature/issue-64 の削除に失敗しました
理由: <error message>

次のブランチの削除を継続します...
```

---

## 注意事項

1. **必ず /worktree-done コマンドを使用**: `git worktree remove` を直接使用しない
2. **順番に実行**: 各 worktree は順番に削除（並列実行しない）
3. **PRのマージ確認**: `/worktree-done` が各ブランチのマージ状態を確認
4. **エラー時も継続**: 1つの worktree 削除に失敗しても、残りは継続
5. **mainブランチは削除不可**: `/worktree-done` が検証するため安全

---

## 完了前の確認事項

削除前に以下を確認することを推奨:

1. **PRのマージ状態**: 全てのPRがマージされているか
2. **未コミット変更**: worktreeに未保存の作業がないか
3. **関連Issue**: GitHub Projectで「Done」に移動されるか

---

## 関連コマンド

| コマンド | 説明 |
|----------|------|
| `/plan-worktrees` | 並列開発計画の作成（Wave グルーピング） |
| `/create-worktrees` | 複数の worktree を一括作成 |
| `/worktree-done` | 単一の worktree をクリーンアップ |
| `/worktree` | 単一の worktree を作成 |

---

## ワークフロー例

```bash
# 1. 並列開発計画
/plan-worktrees 1

# 2. Wave 1 のworktreeを一括作成
/create-worktrees 64 67 68

# 開発作業...
# PRマージ...

# 3. 完了したworktreeを一括削除
/delete-worktrees feature/issue-64 feature/issue-67 feature/issue-68
```

---

## 完了条件

- 全ての指定ブランチに対して `/worktree-done` が実行されている
- 各ブランチの処理結果（成功/失敗）が記録されている
- 結果サマリーが表示されている
- 次のステップが案内されている

# /create-worktrees - 複数Worktree一括作成

`/plan-worktrees` の結果から複数の worktree を一括作成します。

**目的**: Wave 1 など、並列開発可能な Issue の worktree を一括で作成

## 使用例

```bash
# Issue番号を指定して一括作成
/create-worktrees 64 67

# 3つ以上も可能
/create-worktrees 64 65 66 67
```

---

## ステップ 0: 引数解析

1. 引数から Issue 番号のリストを取得（スペース区切り）
2. **引数がない場合**: AskUserQuestion でヒアリング

```yaml
questions:
  - question: "作成する worktree の Issue 番号を入力してください（カンマ区切り）"
    header: "Issue番号"
    options:
      - label: "/plan-worktrees を実行"
        description: "まず並列開発計画を確認する"
      - label: "番号を直接入力"
        description: "例: 64, 67"
```

---

## ステップ 1: 各 Issue に対して /worktree を実行

**重要**: 直接 `git worktree add` を使用せず、必ず `/worktree` コマンド（Skill ツール）を使用する。

各 Issue 番号に対して順番に `/worktree` を実行:

```bash
# Issue #64 の worktree を作成
Skill tool: /worktree feature/issue-64

# Issue #67 の worktree を作成
Skill tool: /worktree feature/issue-67
```

### 実行手順

1. Issue 番号からブランチ名を生成: `feature/issue-{番号}`
2. Skill ツールで `/worktree {ブランチ名}` を実行
3. 次の Issue に進む
4. 全て完了するまで繰り返す

---

## ステップ 2: 結果サマリー

```
================================================================================
✅ Worktree 一括作成完了
================================================================================

作成数: X 件

| Issue | ブランチ | パス |
|-------|----------|------|
| #64 | feature/issue-64 | ~/.worktrees/finance/feature-issue-64 |
| #67 | feature/issue-67 | ~/.worktrees/finance/feature-issue-67 |

## 開発開始

# 各ターミナルで実行
cd /path/to/worktree-1 && claude
cd /path/to/worktree-2 && claude

## 開発完了後

/commit-and-pr
/worktree-done <branch-name>

================================================================================
```

---

## エラーハンドリング

| ケース | 対処 |
|--------|------|
| 引数未指定 | Issue 番号のヒアリング |
| ブランチが既に存在 | 警告を表示し、スキップまたは既存ブランチを使用 |
| worktree 作成失敗 | エラーを表示し、残りの Issue は継続 |

---

## 注意事項

1. **必ず /worktree コマンドを使用**: `git worktree add` を直接使用しない
2. **順番に実行**: 各 worktree は順番に作成（並列実行しない）
3. **エラー時も継続**: 1つの worktree 作成に失敗しても、残りは継続

---

## 関連コマンド

| コマンド | 説明 |
|----------|------|
| `/plan-worktrees` | 並列開発計画の作成（Wave グルーピング） |
| `/worktree` | 単一の worktree を作成 |
| `/worktree-done` | worktree の完了とクリーンアップ |

---

## 完了条件

- 全ての指定 Issue に対して `/worktree` が実行されている
- 結果サマリーが表示されている
- 次のステップが案内されている

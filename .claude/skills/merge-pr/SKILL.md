---
name: merge-pr
description: PRのコンフリクトチェック・CI確認・マージを実行。/merge-pr コマンドで使用。mainブランチ上からPR番号を指定し安全にマージ。
allowed-tools: Read, Bash
---

# Merge PR - PRマージ

> **役割の明確化**: このコマンドは**PRのマージ実行**に特化しています。
>
> - PRの詳細レビュー → `/review-pr`
> - 変更のコミット・PR作成 → `/commit-and-pr`
> - worktreeのクリーンアップ → `/worktree-done`

**目的**: mainブランチ上からPR番号を指定し、安全にマージを実行する

## 使用例

```bash
# 基本的な使用（デフォルト: squash merge）
/merge-pr 123

# マージ方法を指定
/merge-pr 123 --merge       # 通常マージ
/merge-pr 123 --squash      # スカッシュマージ（デフォルト）
/merge-pr 123 --rebase      # リベースマージ

# マージ後にブランチを削除
/merge-pr 123 --delete-branch
/merge-pr 123 -d

# ドライラン（実際にはマージしない）
/merge-pr 123 --dry-run
```

## 実行フロー

### ステップ 0: 前提条件の確認

#### 0.1 引数の確認

**引数（$ARGUMENTS）を解析**:
- PR番号: 必須
- オプション: --merge, --squash, --rebase, -d/--delete-branch, --dry-run, -y/--no-confirm

**引数がない場合**: エラーを表示して処理を中断

```
エラー: PR番号を指定してください。

使用方法:
  /merge-pr <pr-number> [options]

オプション:
  --merge         通常マージ
  --squash        スカッシュマージ（デフォルト）
  --rebase        リベースマージ
  -d, --delete-branch  マージ後にブランチを削除
  --dry-run       実際にはマージせず確認のみ
  -y, --no-confirm     確認プロンプトをスキップ

例:
  /merge-pr 123
  /merge-pr 123 --squash -d
```

#### 0.2 現在のブランチ確認

```bash
git rev-parse --abbrev-ref HEAD
```

**mainブランチ以外の場合**: 警告を表示し、AskUserQuestionで確認

```
警告: 現在 main ブランチ上ではありません。

現在のブランチ: <current-branch>

main ブランチに移動しますか？
1. はい（git checkout main を実行）
2. いいえ（処理を中断）
```

#### 0.3 GitHub CLI の確認

```bash
gh auth status 2>/dev/null
```

**認証されていない場合**: エラーを表示して終了

```
エラー: GitHub CLI が認証されていません。

セットアップ方法:
  gh auth login

認証完了後に再度 /merge-pr を実行してください。
```

### ステップ 1: PR情報の取得

#### 1.1 PR詳細情報の取得

```bash
gh pr view <pr-number> --json number,title,state,mergeable,mergeStateStatus,baseRefName,headRefName,author,url,additions,deletions,changedFiles,isDraft
```

#### 1.2 PR状態のバリデーション

| 状態 | 対処 |
|------|------|
| PRが存在しない | エラー表示して終了 |
| CLOSED（未マージ） | エラー表示して終了 |
| MERGED | 「既にマージ済み」と表示して終了 |
| DRAFT | AskUserQuestionで確認 |
| OPEN | 次のステップへ |

### ステップ 2: コンフリクトチェック

#### 2.1 マージ可能性の確認

`mergeable` と `mergeStateStatus` フィールドを確認:

| mergeable | mergeStateStatus | 状態 |
|-----------|------------------|------|
| MERGEABLE | CLEAN | マージ可能 ✓ |
| MERGEABLE | HAS_HOOKS | マージ可能 ✓ |
| CONFLICTING | DIRTY | コンフリクトあり ✗ |
| UNKNOWN | UNKNOWN | 判定中 |

**マージ可能な場合**:

```
✓ コンフリクトチェック: OK

PR #<number>: <title>
ベースブランチ: <baseRefName>
ヘッドブランチ: <headRefName>
```

**コンフリクトがある場合**: /analyze-conflicts を自動実行

```
エラー: PR #<number> にコンフリクトがあります。

詳細な分析を実行します...
```

### ステップ 3: CIステータスの確認

#### 3.1 チェック結果の取得

```bash
gh pr checks <pr-number> --json name,state,bucket,description
```

#### 3.2 チェック結果の分析

| bucket | 意味 |
|--------|------|
| pass | 成功 |
| fail | 失敗 |
| pending | 実行中 |
| skipping | スキップ |

**全て成功の場合**:

```
✓ CIステータス: 全てパス

| チェック名 | 状態 |
|------------|------|
| [name1]    | ✓    |
| [name2]    | ✓    |
```

**失敗がある場合**: 詳細を表示して終了

```
エラー: CIチェックに失敗があります。

| チェック名 | 状態 | 説明 |
|------------|------|------|
| [name1]    | ✗    | [description] |

詳細を確認: gh pr checks <number> --web
```

### ステップ 4: マージ確認

#### 4.1 マージ内容のサマリー表示

```
================================================================================
                           PR マージ確認
================================================================================

PR情報:
  番号: #<number>
  タイトル: <title>
  作成者: <author>
  URL: <url>

変更内容:
  変更ファイル数: <changedFiles>
  追加行数: +<additions>
  削除行数: -<deletions>

マージ設定:
  ベースブランチ: <baseRefName>
  ヘッドブランチ: <headRefName>
  マージ方法: <merge|squash|rebase>
  ブランチ削除: <はい|いいえ>

チェック結果:
  コンフリクト: なし ✓
  CIステータス: 全てパス ✓

================================================================================
```

**--dry-run の場合**: サマリー表示のみで終了

#### 4.2 マージ確認

**--no-confirm がない場合**: AskUserQuestionで確認

### ステップ 5: マージの実行

#### 5.1 マージコマンドの実行

```bash
# squash の場合（デフォルト）
gh pr merge <number> --squash

# merge の場合
gh pr merge <number> --merge

# rebase の場合
gh pr merge <number> --rebase

# ブランチ削除オプション付き
gh pr merge <number> --squash --delete-branch
```

**成功の場合**:

```
✓ PR #<number> がマージされました

マージ方法: <merge|squash|rebase>
マージ先: <baseRefName>
```

### ステップ 6: ローカルの同期

#### 6.1 ローカルブランチの更新

```bash
git fetch origin
git pull origin main
```

### ステップ 7: 完了報告

```
================================================================================
                           マージ完了
================================================================================

✓ PR #<number> のマージが完了しました

PR情報:
  タイトル: <title>
  マージ方法: <merge|squash|rebase>
  マージ先: <baseRefName>

ローカル main: 最新に同期済み

次のステップ:
  - 新しい開発を開始: /worktree <feature-name>
  - 次のPRをマージ: /merge-pr <pr-number>

================================================================================
```

## オプション一覧

| オプション | 短縮形 | 説明 | デフォルト |
|------------|--------|------|------------|
| `--merge` | - | 通常マージ | - |
| `--squash` | - | スカッシュマージ | ✓ |
| `--rebase` | - | リベースマージ | - |
| `--delete-branch` | `-d` | マージ後にブランチを削除 | - |
| `--dry-run` | - | 確認のみ | - |
| `--no-confirm` | `-y` | 確認プロンプトをスキップ | - |

## エラーハンドリング

| 状況 | 対処 |
|------|------|
| PR番号未指定 | 使用方法を表示して終了 |
| PRが存在しない | エラーメッセージを表示して終了 |
| PRがクローズ/マージ済み | 状態を表示して終了 |
| コンフリクトあり | **/analyze-conflicts を自動実行**し、詳細な分析レポートを提示して終了 |
| CI失敗 | 失敗詳細を表示して終了 |
| CI実行中 | 待機オプションを提示 |
| GitHub CLI未認証 | セットアップ方法を表示して終了 |
| マージ権限なし | 権限エラーを表示して終了 |

## 関連コマンド

| コマンド | 説明 |
|----------|------|
| `/analyze-conflicts` | コンフリクトの詳細分析（自動実行） |
| `/review-pr` | PRの詳細レビュー |
| `/commit-and-pr` | 変更のコミットとPR作成 |
| `/worktree-done` | worktreeのクリーンアップ |

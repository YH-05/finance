---
name: worktree-done
description: worktreeの開発完了後、PRマージ確認を経て安全にクリーンアップするスキル。
/worktree-done コマンドで使用。マージ確認→worktree削除→ブランチ削除の安全なクリーンアップを実行。

allowed-tools: Read, Bash
---

# Worktree Done - Worktree 完了・クリーンアップ

worktree での開発完了後、PR がメインブランチにマージされたことを確認してから、worktree とブランチを安全に削除します。

**目的**: マージ確認 → worktree削除 → ブランチ削除の安全なクリーンアップ

## 使用例

```bash
# ブランチ名を指定してクリーンアップ（必須）
/worktree-done feature/user-auth
/worktree-done fix/login-bug
```

---

## ステップ 0: 現在地とworktree情報の確認

### 0.1 引数の確認

**引数がない場合**: エラーを表示して処理を中断

```
エラー: ブランチ名を指定してください。

使用方法:
  /worktree-done <branch-name>

例:
  /worktree-done feature/user-auth
  /worktree-done fix/login-bug

現在のworktree一覧:
<git worktree list の出力>
```

### 0.2 worktree一覧の取得

```bash
git worktree list
```

### 0.3 対象worktreeの特定

指定されたブランチ名から対象worktreeを特定する:
- worktree一覧からブランチ名が一致するエントリを探す
- 見つからない場合はエラー

### 0.4 worktreeパスの取得

```bash
# worktree一覧からブランチ名に対応するパスを取得
git worktree list | grep "<branch-name>"
```

**worktreeが見つからない場合**:

```
エラー: ブランチ '<branch-name>' のworktreeが見つかりません。

現在のworktree一覧:
<git worktree list の出力>

ブランチ名を確認してください。
```

### 0.5 ブランチの検証

**mainブランチの場合**:

```
エラー: mainブランチのworktreeは削除できません。
対象: <worktree-path>

feature/*, fix/* などの作業ブランチのworktreeを指定してください。
```

---

## ステップ 1: PRの検索と状態確認

### 1.1 関連PRの検索

```bash
gh pr list --head <branch-name> --state all --json number,state,mergedAt,url,title
```

### 1.2 PR状態による分岐

**ケースA: PRが存在しない**

```
PRが見つかりません。

ブランチ: <branch-name>
worktree: <worktree-path>

次のステップ:
1. 変更をコミット & プッシュ: /push
2. PRを作成: /commit-and-pr
3. PRがマージされてから再度 /worktree-done を実行
```

処理を中断する。

**ケースB: PRがオープン（OPEN）**

```
PRはまだマージされていません。

PR: #<number> - <title>
URL: <url>
状態: オープン

次のステップ:
1. PRをレビュー & マージしてください
2. マージ後に再度 /worktree-done を実行

PRを確認: gh pr view <number> --web
```

処理を中断する。

**ケースC: PRがマージ済み（MERGED）**

```
✓ PRがマージされています

PR: #<number> - <title>
マージ日時: <mergedAt>

クリーンアップを続行します...
```

→ ステップ1.5へ進む

**ケースD: PRがクローズ（CLOSED, 未マージ）**

```
警告: PRはマージされずにクローズされています。

PR: #<number> - <title>
状態: クローズ（未マージ）

オプション:
1. 開発内容を破棄してworktreeを削除（--force）
2. PRを再オープン: gh pr reopen <number>
3. 処理を中断
```

AskUserQuestion で確認を求める。

---

## ステップ 1.5: 関連IssueのGitHub Project更新

PRがマージされた場合、関連するIssueをGitHub Projectで「Done」に移動する。

### 1.5.1 関連Issueの特定

PRの本文から関連Issueを抽出:

```bash
gh pr view <pr-number> --json body,closingIssuesReferences --jq '.closingIssuesReferences[].number'
```

**注意**: `closes #XX`, `fixes #XX`, `resolves #XX` などのキーワードで紐付けられたIssueが対象

### 1.5.2 各IssueのProject情報取得

各Issueについて、所属するGitHub Projectを確認:

```bash
gh issue view <issue-number> --json projectItems --jq '.projectItems[] | "\(.project.title)|\(.project.number)"'
```

### 1.5.3 ProjectのフィールドID取得

各Projectについて、StatusフィールドのIDとDoneオプションのIDを取得:

```bash
# Statusフィールドの情報を取得
gh project field-list <project-number> --owner <owner> --format json | \
  jq -r '.fields[] | select(.name == "Status") | "\(.id)|\(.options[] | select(.name == "Done") | .id)"'
```

### 1.5.4 ステータスを「Done」に更新

```bash
# ProjectアイテムIDを取得
ITEM_ID=$(gh project item-list <project-number> --owner <owner> --format json | \
  jq -r '.items[] | select(.content.number == <issue-number>) | .id')

# ステータスを更新
gh project item-edit \
  --project-id <project-id> \
  --id $ITEM_ID \
  --field-id <status-field-id> \
  --single-select-option-id <done-option-id>
```

### 1.5.5 更新結果の表示

```
GitHub Project のステータスを更新しました:

Project: <project-name>
  - Issue #<number>: <title> → Done ✓
  - Issue #<number>: <title> → Done ✓

（Projectに未登録のIssueはスキップされます）
```

**関連Issueがない場合**:

```
PRに関連するIssueが見つかりませんでした。
GitHub Projectの更新をスキップします。
```

→ ステップ2へ進む

---

## ステップ 2: 未保存変更の確認

### 2.1 未コミット変更の確認

```bash
git -C <worktree-path> status --porcelain
```

**未コミット変更がある場合**:

```
警告: worktreeに未コミットの変更があります。

変更ファイル:
<modified files>

オプション:
1. 変更をコミット: /push を実行
2. 変更を破棄: git checkout . && git clean -fd
3. 処理を中断
```

AskUserQuestion で確認を求める。

### 2.2 未プッシュコミットの確認

```bash
git -C <worktree-path> log @{u}..HEAD --oneline 2>/dev/null
```

**未プッシュコミットがある場合**:

```
警告: worktreeに未プッシュのコミットがあります。

未プッシュコミット:
<commit list>

これらのコミットはPRに含まれていない可能性があります。

オプション:
1. コミットをプッシュ: /push を実行
2. コミットを無視してクリーンアップを続行（--force）
3. 処理を中断
```

AskUserQuestion で確認を求める。

---

## ステップ 3: Worktree削除

### 3.1 メインリポジトリのパス特定

```bash
# worktreeリストからメインリポジトリを特定
git worktree list | head -1 | awk '{print $1}'
```

### 3.2 Worktree削除の実行

```bash
# メインリポジトリから削除コマンドを実行
git -C <main-repo-path> worktree remove <worktree-path>
```

**削除に失敗した場合**:

```bash
# 強制削除（未コミット変更がある場合など）
git -C <main-repo-path> worktree remove --force <worktree-path>
```

### 3.3 参照のクリーンアップ

```bash
git -C <main-repo-path> worktree prune
```

---

## ステップ 4: ブランチ削除

### 4.1 ローカルブランチ削除

```bash
# マージ済みブランチの安全な削除
git -C <main-repo-path> branch -d <branch-name>
```

**削除失敗時（未マージ扱い）**:

```bash
# 強制削除（PRがマージ済みなので安全）
git -C <main-repo-path> branch -D <branch-name>
```

### 4.2 リモートブランチ削除

```bash
git -C <main-repo-path> push origin --delete <branch-name>
```

**リモートブランチが既に削除されている場合**: 警告をスキップ

---

## ステップ 5: 完了報告

```
✓ Worktree のクリーンアップが完了しました

削除したworktree: <worktree-path>
削除したブランチ: <branch-name>（ローカル + リモート）
マージされたPR: #<pr-number>

GitHub Project 更新:
  - Issue #<number>: Done ✓
  - Issue #<number>: Done ✓

メインリポジトリ: <main-repo-path>

次のステップ:
- 新しい開発を開始: /worktree <feature-name>
- メインリポジトリに移動: cd <main-repo-path>
```

---

## オプション

| オプション | 説明 |
|------------|------|
| `--force` | 未マージPRや未コミット変更があっても強制削除 |
| `--dry-run` | 実際には削除せず、何が削除されるか表示 |
| `--keep-remote` | リモートブランチを削除しない |

---

## エラーハンドリング

### E1: worktreeが見つからない

```
エラー: 指定されたworktreeが見つかりません。

指定パス: <path>

現在のworktree一覧:
<git worktree list output>

正しいパスを指定してください。
```

### E2: GitHub CLI未設定

```
エラー: GitHub CLI (gh) が設定されていません。

PRのマージ状態を確認できないため、処理を中断します。

セットアップ方法:
1. gh auth login
2. 認証を完了
3. 再度 /worktree-done を実行
```

### E3: ネットワークエラー

```
エラー: GitHubへの接続に失敗しました。

ネットワーク接続を確認してください。
オフラインでクリーンアップする場合は --force オプションを使用してください。
```

### E4: パーミッションエラー

```
エラー: ディレクトリを削除できません。

worktree: <path>
理由: パーミッション不足

手動で削除してください:
rm -rf <path>
git worktree prune
```

---

## 関連コマンド

| コマンド | 説明 |
|----------|------|
| `/worktree` | 新しいworktreeとブランチを作成 |
| `/push` | 変更をコミット & プッシュ |
| `/commit-and-pr` | コミット & PR作成 |

---

## ワークフロー例

```
/worktree feature/new-api     # 1. worktree作成
cd ../.worktrees/.../feature-new-api
# 開発作業...
/commit-and-pr                # 2. PR作成
# PRレビュー & マージ（GitHub上）
/worktree-done                # 3. クリーンアップ
```

---

## 完了条件

このワークフローは、以下の全ての条件を満たした時点で完了:

- ステップ 1: PRがMERGED状態であることが確認されている
- ステップ 1.5: 関連IssueがGitHub Projectで「Done」に更新されている
- ステップ 2: 未保存変更がないか、ユーザーが確認済み
- ステップ 3: worktreeが削除されている（`git worktree list` で確認）
- ステップ 4: ローカル・リモートブランチが削除されている
- ステップ 5: 完了報告がユーザーに表示されている

# GitHub Projects 自動化設定ガイド

## 概要

GitHub Projects v2 のワークフロー自動化を設定し、PR作成時とマージ時のIssueステータスを適切に管理します。

## 目標

- **PR作成時**: Issue ステータスを `In Progress` に変更
- **PRマージ時**: Issue ステータスを `Done` に変更

## 設定手順

### 1. GitHub Project にアクセス

```bash
# プロジェクトURLを取得
gh project list
```

または、Webブラウザで以下にアクセス:
```
https://github.com/users/<username>/projects/<project-number>
```

### 2. ワークフロー自動化設定

#### 2.1 既存の自動化を確認

1. GitHub Project ページを開く
2. 右上の `...` メニュー → `Workflows` をクリック
3. 既存のワークフローを確認

#### 2.2 不要なワークフローを無効化

**削除または無効化すべき設定**:
- ❌ "Pull request opened" → "Set status: Done"
- ❌ "Pull request created" → "Set status: Done"

**手順**:
1. 該当するワークフローの `...` メニューをクリック
2. `Disable` または `Delete` を選択

#### 2.3 新しいワークフローを作成

**ワークフロー1: PR作成時にIn Progressに移動**

1. `Workflows` タブで `Create workflow` をクリック
2. 以下のように設定:
   ```
   When: Pull request
   Activity: opened

   Then: Set field
   Field: Status
   Value: In Progress
   ```

**ワークフロー2: PRマージ時にDoneに移動**

1. `Workflows` タブで `Create workflow` をクリック
2. 以下のように設定:
   ```
   When: Pull request
   Activity: merged

   Then: Set field
   Field: Status
   Value: Done
   ```

### 3. 設定の確認

#### 3.1 手動テスト

1. テスト用のIssueを作成
2. Issue に対してPRを作成:
   ```bash
   # ブランチ作成
   git checkout -b test/github-projects-automation

   # 変更をコミット
   echo "test" > test.txt
   git add test.txt
   git commit -m "test: GitHub Projects automation"

   # PRを作成（Issue番号を本文に含める）
   gh pr create --title "test: GitHub Projects automation" --body "Test for #<issue-number>"
   ```

3. **期待される動作**:
   - PR作成直後: Issue が `In Progress` に移動
   - PRマージ後: Issue が `Done` に移動

#### 3.2 ワークフローの動作確認

```bash
# PRをマージ
gh pr merge <pr-number> --squash

# Issueステータスを確認（gh project item-list等）
gh project item-list <project-number> --owner <username>
```

## CLI でのステータス確認・変更（参考）

### プロジェクト情報の取得

```bash
# プロジェクト一覧
gh project list --owner <username>

# プロジェクト内のアイテム一覧
gh project item-list <project-number> --owner <username>
```

### 手動でステータス変更（緊急時）

```bash
# Issueステータスを手動で変更
gh project item-edit \
  --project-id <project-id> \
  --id <item-id> \
  --field-id <field-id> \
  --value "Done"
```

**注意**: 通常はワークフロー自動化に任せ、手動変更は緊急時のみ使用してください。

## トラブルシューティング

### Issue が自動で Done に移動しない

**原因1: PRとIssueがリンクされていない**

PRの本文に以下のキーワードを含める必要があります:
- `Fixes #<issue-number>`
- `Closes #<issue-number>`
- `Resolves #<issue-number>`

**原因2: ワークフローが無効になっている**

1. Project → Workflows で設定を確認
2. 該当するワークフローが有効か確認

**原因3: 権限不足**

```bash
# project スコープで再認証
gh auth refresh -s project
```

### Issue が PR作成時に Done に移動してしまう

**原因: 誤ったワークフローが有効になっている**

1. Project → Workflows を開く
2. "Pull request opened" → "Done" のワークフローを削除/無効化
3. "Pull request opened" → "In Progress" のワークフローを確認

## ベストプラクティス

### PR作成時のIssueリンク

```bash
# /commit-and-pr で自動的に以下の形式でリンク
gh pr create --title "feat: 新機能追加" --body "$(cat <<'EOF'
## 概要
- 新機能を追加

Fixes #123

## テストプラン
- [ ] make check-all が成功することを確認
EOF
)"
```

### ワークフロー設定の定期確認

1ヶ月に1回、以下を確認:
- [ ] "PR opened" → "In Progress" が有効
- [ ] "PR merged" → "Done" が有効
- [ ] 不要なワークフローが無効

## 参考リンク

- [GitHub Projects documentation](https://docs.github.com/en/issues/planning-and-tracking-with-projects)
- [Automating Projects](https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project)
- [GitHub CLI project commands](https://cli.github.com/manual/gh_project)

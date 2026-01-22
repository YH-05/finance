# Project Management Guide

GitHub Project と project.md 管理の詳細ガイドです。

## GitHub Project 操作

### Project の作成

```bash
# 新規 Project 作成
gh project create --title "プロジェクト名" --owner @me

# 作成結果の確認（Project 番号と URL を取得）
gh project list --owner @me --format json
```

### Project フィールドの取得

Status フィールドのオプション ID を取得するには：

```bash
# フィールド一覧を取得
gh project field-list {project_number} --owner @me --format json

# Status フィールドの構造例：
# {
#   "id": "FIELD_ID",
#   "name": "Status",
#   "type": "SingleSelect",
#   "options": [
#     {"id": "OPTION_ID_1", "name": "Todo"},
#     {"id": "OPTION_ID_2", "name": "In Progress"},
#     {"id": "OPTION_ID_3", "name": "Done"}
#   ]
# }
```

### Project Item の操作

```bash
# Item 一覧取得
gh project item-list {project_number} --owner @me --format json --limit 100

# Issue を Project に追加
gh project item-add {project_number} --owner @me --url {issue_url}

# Item のステータス変更
gh project item-edit \
  --project-id {project_id} \
  --id {item_id} \
  --field-id {status_field_id} \
  --single-select-option-id {option_id}
```

### Project 情報の取得例

```bash
# Project ID を取得
gh project list --owner @me --format json | jq '.projects[] | select(.title == "プロジェクト名") | .id'

# 特定 Project の全アイテム
gh project item-list 14 --owner @me --format json | jq '.items[] | {title: .content.title, number: .content.number, status: .status}'
```

## Issue 操作

### Issue 作成（HEREDOC 形式）

シェルエスケープの問題を防ぐため、必ず HEREDOC 形式を使用：

```bash
gh issue create \
  --title "[カテゴリ] タイトル" \
  --body "$(cat <<'EOF'
## 概要

[機能・問題の概要を記載]

## 詳細

[詳細な説明を記載]

## 受け入れ条件

- [ ] 条件1
- [ ] 条件2
- [ ] 条件3

## 関連

- 計画書: docs/project/xxx.md
- GitHub Project: #XX
EOF
)" \
  --label "enhancement"
```

**重要**: `'EOF'` はシングルクォートで囲むこと（変数展開を防止）

### ラベル自動判定

| キーワード | ラベル |
|------------|--------|
| 新機能、追加、feature | `enhancement` |
| バグ、修正、fix | `bug` |
| リファクタ、改善 | `refactor` |
| ドキュメント、docs | `documentation` |
| テスト | `test` |

### Issue 編集

```bash
# ラベル変更
gh issue edit {number} --remove-label "priority:low" --add-label "priority:high"

# ステータス変更
gh issue close {number}
gh issue reopen {number}

# 担当者変更
gh issue edit {number} --add-assignee "{user}"

# 本文更新（依存関係修正など）
gh issue edit {number} --body "{updated_body}"
```

## project.md 構造

### パッケージ開発用

```markdown
# [パッケージ名] プロジェクト

## 概要

[パッケージの目的と背景]

**背景**:
- [理由1]
- [理由2]

**解決する課題**:
- [課題1]
- [課題2]

## 実装計画

### マイルストーン 1: 基本機能 (期限: YYYY-MM-DD)

#### 機能 1.1: [機能名]
- 優先度: P0
- 説明: [詳細説明]
- 受け入れ条件:
  - [ ] [測定可能な条件1]
  - [ ] [測定可能な条件2]

## 技術的考慮事項

### アーキテクチャ
- [設計パターン]

### 依存関係
- [外部ライブラリ]

### 制約事項
- [既知の制限]
```

### 軽量プロジェクト用

```markdown
# {プロジェクト名}

**作成日**: YYYY-MM-DD
**ステータス**: 計画中 | 進行中 | 完了
**GitHub Project**: [#N](URL)

## 背景と目的

### 背景
- 背景の種類: [選択された背景]
- 詳細: [具体的な状況]

### 目的
[達成したいこと]

## スコープ

### 含むもの
- 変更範囲: [新規のみ / 既存修正のみ / 両方]
- 影響ディレクトリ: [.claude/ / src/ / tests/ / docs/]

### 含まないもの
- [スコープ外の項目]

## 成果物

| 種類 | 名前 | 説明 |
| ---- | ---- | ---- |
| [種別] | [成果物名] | [説明] |

## 成功基準

- [ ] [基準1]
- [ ] [基準2]

## タスク一覧

### 準備
- [ ] 関連コードの調査
  - Issue: [#番号](URL)
  - ステータス: todo

### 実装
- [ ] タスク1
  - Issue: [#番号](URL)
  - ステータス: todo

---

**最終更新**: YYYY-MM-DD
```

## ステータス同期ルール

### Issue → project.md 同期

| GitHub Issue | GitHub Project | project.md アクション |
|--------------|----------------|----------------------|
| open | Todo | 変更なし |
| open | In Progress | `ステータス: in_progress` に更新 |
| closed | Done | `- [x]` と `ステータス: done` に更新 |

### project.md → GitHub 同期

| project.md | 期待する GitHub 状態 | 不一致時のアクション |
|------------|---------------------|---------------------|
| `- [x]` + `done` | Issue: closed, Project: Done | Issue を close、Project を Done に |
| `- [ ]` + `todo` | Issue: open, Project: Todo | 変更なし |
| `ステータス: 完了` | 全 Issue closed | 全 Issue を close |

## 整合性検証アルゴリズム

### 1. 循環依存検出（DFS）

```python
# 疑似コード
def detect_cycles(issues):
    visited = set()
    rec_stack = set()
    cycles = []

    def dfs(issue_id, path):
        if issue_id in rec_stack:
            cycle_start = path.index(issue_id)
            cycles.append(path[cycle_start:] + [issue_id])
            return
        if issue_id in visited:
            return

        visited.add(issue_id)
        rec_stack.add(issue_id)
        path.append(issue_id)

        for dep in issues[issue_id].depends_on:
            dfs(dep, path)

        path.pop()
        rec_stack.remove(issue_id)

    for issue_id in issues:
        dfs(issue_id, [])

    return cycles
```

### 2. 優先度矛盾検出

```
for each issue:
    for each dependency in issue.depends_on:
        if issue.priority > dependency.priority:
            report_warning(
                issue=issue,
                dependency=dependency,
                suggestion=f"Raise {dependency} priority to {issue.priority}"
            )
```

### 3. ステータス不整合検出

```
for each issue:
    github_state = get_github_issue_state(issue.number)
    project_state = get_project_item_status(issue.number)
    doc_state = get_project_md_status(issue.number)

    if github_state == "closed" and doc_state != "done":
        report_warning(sync_needed=True, target="project.md")

    if project_state == "Done" and github_state == "open":
        report_warning(sync_needed=True, target="GitHub Issue")
```

## トラブルシューティング

### 「Project が見つかりません」

**原因**: Project 番号が間違っている、またはアクセス権限がない

**確認手順**:
```bash
# 自分の Project 一覧を確認
gh project list --owner @me

# 特定の Project にアクセスできるか確認
gh project view {project_number} --owner @me
```

### 「Item の追加に失敗」

**原因**: Issue が存在しない、または既に追加済み

**確認手順**:
```bash
# Issue の存在確認
gh issue view {issue_number}

# Project 内の既存アイテムを確認
gh project item-list {project_number} --owner @me --format json | grep {issue_number}
```

### 「ステータス変更が反映されない」

**原因**: Field ID または Option ID が間違っている

**確認手順**:
```bash
# 正しい Field ID と Option ID を取得
gh project field-list {project_number} --owner @me --format json | jq '.fields[] | select(.name == "Status")'
```

### 「認証エラー」

**対処法**:
```bash
# 再認証
gh auth login

# Project スコープの追加
gh auth refresh -s project
```

## ベストプラクティス

### 1. 定期的な同期

- PR マージ後は必ずステータス同期を実行
- 週次で `/project-refine` による整合性チェックを推奨

### 2. 明確な受け入れ条件

```markdown
# 悪い例
- [ ] テストを書く

# 良い例
- [ ] 全公開関数にユニットテストを追加（カバレッジ80%以上）
- [ ] make test が成功する
```

### 3. 適切な優先度設定

| 優先度 | 定義 | 目安 |
|--------|------|------|
| P0 | 必須 | MVI に含める機能 |
| P1 | 重要 | 初期リリース後すぐに追加 |
| P2 | できれば | 将来的に検討 |

### 4. 依存関係の明示

```markdown
#### 機能 1.2: データ変換
- 優先度: P0
- 依存: 機能 1.1（データ取得）
- ブロック: 機能 2.1（レポート生成）
```

### 5. コミットメッセージの一貫性

```bash
git commit -m "docs: GitHub Projects とドキュメントを同期

変更内容:
- project-name.md を GitHub Project #XX と同期
- タスク (#YY, #ZZ) のステータスを done に更新
- プロジェクトステータスを「完了」に更新

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

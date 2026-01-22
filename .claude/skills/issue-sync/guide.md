# Issue Sync Guide

コメント同期の詳細ガイドです。

---

## 1. 引数解析

### パターン A: Issue 番号指定

- 形式: `#123` または `#123 #124 #125`
- 抽出: `#` に続く数字を Issue 番号として取得
- 複数指定された場合は順番に処理

### パターン B: project.md パス指定

- 形式: `@src/<library_name>/docs/project.md` または `@docs/project/<slug>.md`
- 処理:
  1. project.md を読み込み
  2. `Issue: [#番号](URL)` から全 Issue 番号を抽出
  3. 抽出した全 Issue を対象に同期

### オプション

- `--since="YYYY-MM-DD"`: 指定日以降のコメントのみ対象

**引数が不正な場合**:

```text
エラー: 引数の形式が正しくありません。

使用例:
- 単一 Issue: /sync-issue #123
- 複数 Issue: /sync-issue #123 #124 #125
- project.md: /sync-issue @src/market_analysis/docs/project.md
```

---

## 2. データ取得

### 2.1 リポジトリ情報の取得

```bash
gh repo view --json owner,name -q '"\(.owner.login)/\(.name)"'
```

### 2.2 Issue 情報の取得

```bash
gh issue view {issue_number} --json number,title,body,state,labels
```

### 2.3 コメント取得（GraphQL）

```bash
gh api graphql -f owner="{owner}" -f repo="{repo}" -F number={issue_number} -f query='
  query($owner:String!, $repo:String!, $number:Int!) {
    repository(owner:$owner, name:$repo) {
      issue(number:$number) {
        title
        body
        state
        comments(last:100) {
          nodes {
            author { login }
            body
            createdAt
          }
        }
      }
    }
  }
'
```

**`--since` オプションが指定された場合**:

取得したコメントから `createdAt` が指定日以降のものだけをフィルタリング

### 2.4 GitHub Project 情報の取得

project.md から `**GitHub Project**: [#N](URL)` 形式でプロジェクト番号を抽出した場合:

```bash
# フィールド情報取得
gh project field-list {project_number} --owner @me --format json

# Item 一覧取得
gh project item-list {project_number} --owner @me --format json
```

**認証スコープ不足の場合**:

```text
警告: GitHub Project へのアクセス権限がありません。

解決方法:
gh auth refresh -s project

Project 同期なしで Issue 管理のみ実行します。
```

---

## 3. コメント解析（comment-analyzer）

### 3.1 サブエージェント起動

```yaml
subagent_type: "comment-analyzer"
description: "Issue comment analysis"
prompt: |
  Issue コメントを解析し、進捗・サブタスク・仕様変更を抽出してください。

  ## Issue 情報

  ### Issue #{issue_number}: {title}

  **本文**:
  {body}

  **現在の状態**: {state}

  **コメント一覧**:
  {comments_formatted}

  ## 出力

  以下の形式で抽出結果を報告してください:

  ```yaml
  extracted_updates:
    status_changes: [...]
    acceptance_criteria_updates: [...]
    new_subtasks: [...]
    requirement_changes: [...]

  confidence_summary:
    overall: 0.XX
    needs_confirmation: true/false
  ```
```

### 3.2 出力形式

```yaml
extracted_updates:
  status_changes:
    - description: "完了"
      evidence: "対応完了しました"
      confidence: 0.95

  acceptance_criteria_updates:
    - criteria: "OAuth対応"
      status: "completed"
      confidence: 0.90

  new_subtasks:
    - title: "GitHub OAuth対応"
      confidence: 0.85

  requirement_changes:
    - change: "Apple Sign-In 追加"
      confidence: 0.80

confidence_summary:
  overall: 0.87
  needs_confirmation: false
```

---

## 4. 確信度ベース確認

### 4.1 確信度レベル

| レベル | 範囲 | アクション |
|--------|------|-----------|
| HIGH | 0.80+ | 自動適用 |
| MEDIUM | 0.70-0.79 | 適用、確認なし |
| LOW | < 0.70 | ユーザー確認必須 |

### 4.2 確認必須ケース

- ステータスダウングレード（done → in_progress）
- 受け入れ条件の削除
- 複数の矛盾するステータス変更

### 4.3 確認ダイアログ

```yaml
questions:
  - question: "以下の変更を適用しますか？"
    header: "コメントから検出された更新"
    options:
      - label: "すべて適用"
        description: "検出された全ての更新を適用"
      - label: "確認しながら適用"
        description: "各更新を個別に確認（低確信度の項目のみ）"
      - label: "適用しない"
        description: "変更をスキップし、現状を維持"
```

### 4.4 個別確認

低確信度の各項目について:

```yaml
questions:
  - question: "{evidence} から「{description}」を検出しました。適用しますか？"
    header: "{update_type}"
    options:
      - label: "適用する"
        description: "この変更を適用"
      - label: "スキップ"
        description: "この変更をスキップ"
```

---

## 5. 同期実行（task-decomposer）

### 5.1 サブエージェント起動

```yaml
subagent_type: "task-decomposer"
description: "Comment sync execution"
prompt: |
  コメント解析結果を反映して同期を実行してください。

  ## 実行モード
  {package_mode / lightweight_mode}

  ## ライブラリ名 / プロジェクト名
  {library_name または slug}

  ## project.md パス
  {project_md_path}

  ## GitHub Issues（JSON）
  {gh issue list の結果}

  ## GitHub Project 情報（軽量プロジェクトモードのみ）
  - Project 番号: {project_number}
  - Project ID: {project_id}
  - Status フィールド ID: {status_field_id}
  - ステータスオプション:
    - Todo: {todo_option_id}
    - In Progress: {in_progress_option_id}
    - Done: {done_option_id}
  - Project Items: {item_list}

  ## 入力モード
  comment_sync

  ## コメント解析結果
  {comment_analysis_result}

  ## 適用する更新
  {filtered_updates（確認で承認されたもの）}
```

### 5.2 処理内容（comment_sync モード）

1. **ステータス変更の適用**:
   - Issue の状態を更新（必要に応じて close/reopen）
   - project.md のステータスを更新
   - GitHub Project のステータスを更新

2. **受け入れ条件の更新**:
   - Issue 本文のチェックボックスを更新
   - project.md の受け入れ条件を同期

3. **新規サブタスクの作成**:
   - 新規 Issue を作成
   - 親 Issue の Tasklist に追加
   - project.md に追加
   - GitHub Project に追加

4. **仕様変更の反映**:
   - Issue 本文に追記
   - project.md の説明・条件を更新

---

## 6. 競合解決ルール

| 状況 | 解決策 |
|------|--------|
| コメント vs project.md で状態が異なる | コメント優先（最新情報） |
| コメント vs GitHub Project で状態が異なる | コメント優先 |
| 複数コメントで矛盾 | 最新のコメント優先 |
| Issue が closed だが完了コメントなし | closed 状態を維持 |
| confidence < 0.70 | ユーザーに確認 |
| ステータスダウングレード | ユーザーに確認（再オープンの意図を確認） |

---

## 7. エラーハンドリング

| ケース | 対処 |
|--------|------|
| GitHub 認証エラー | `gh auth login` を案内 |
| Issue が存在しない | エラーメッセージを表示 |
| project.md が見つからない | `/issue` で作成を提案 |
| コメント取得に失敗 | リトライ後、部分同期を提案 |
| GraphQL クエリエラー | REST API にフォールバック |
| LLM 解析タイムアウト | 部分結果を使用して続行 |

---

## 8. コマンド完了条件

- [ ] 引数が正しく解析されている
- [ ] Issue 情報とコメントが取得されている
- [ ] comment-analyzer による解析が完了している
- [ ] 確認が必要な場合はユーザー確認が完了している
- [ ] task-decomposer による同期が完了している
- [ ] 結果が表示されている

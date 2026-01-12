---
description: 計画書からタスクを分解し、GitHub Issues を作成して Project に登録します。
argument-hint: <計画書パス> [--dry-run] [--project <project-name>]
---

計画書からタスクを分解し、GitHub に登録します。

## 入力パラメータの解析

ユーザーが指定したパラメータを確認します：

- **計画書パス** (必須): 計画書ファイルのパス
  - 例: `docs/project/youtube-search-plan.md`
- **--dry-run** (任意): GitHub に登録せず、タスク一覧を確認のみ
- **--project** (任意): GitHub Project 名を明示的に指定
  - 省略時: 計画書名から自動生成

### パラメータ検証

**1. 計画書パスの検証**

```
if 計画書パスが指定されていない:
    エラー [E001] を表示:

    ❌ エラー [E001]: 必須パラメータが不足しています

    不足パラメータ: 計画書パス

    💡 対処法:
    - /make-task <計画書パス> の形式で実行してください
    - 例: /make-task docs/project/youtube-search-plan.md

    処理を中断

if 計画書ファイルが存在しない:
    エラー [E002] を表示:

    ❌ エラー [E002]: ファイルが見つかりません

    パス: {指定されたパス}

    💡 対処法:
    - ファイルパスを確認してください
    - /new-plan で計画書を作成してください

    処理を中断
```

## 実行手順

### Step 1: GitHub 認証確認

```bash
gh auth status
```

**認証済みの場合**: Step 2 に進む

**未認証の場合**:

```
⚠️ GitHub 認証が必要です

以下のコマンドで認証を行ってください:
  gh auth login

認証完了後、再度 /make-task を実行してください。
```

処理を中断

### Step 2: 計画書の解析

計画書を読み込み、タスクを抽出します。

**タスク抽出ルール**:

1. 「## タスク」「## タスク一覧」セクションを探す
2. チェックボックス形式（`- [ ]`）の項目をタスクとして抽出
3. インデントされた項目はサブタスクとして親タスクに含める

**抽出例**:

```markdown
## タスク一覧

### /make-task 実装

- [ ] tasks.schema.json の作成
- [ ] /make-task コマンド定義作成
  - gh CLI による Issue 作成ロジック
  - --dry-run オプション実装
```

↓ 抽出結果

```json
{
  "tasks": [
    {
      "task_id": "T001",
      "title": "tasks.schema.json の作成",
      "description": "",
      "status": "todo",
      "type": "feature",
      "phase": "infra"
    },
    {
      "task_id": "T002",
      "title": "/make-task コマンド定義作成",
      "description": "- gh CLI による Issue 作成ロジック\n- --dry-run オプション実装",
      "status": "todo",
      "type": "feature",
      "phase": "infra"
    }
  ]
}
```

### Step 3: タスク情報の補完

抽出したタスクに以下の情報を補完します：

**priority の判断**:
- 「重要」「必須」「最優先」→ high
- 「任意」「後回し」「低優先」→ low
- それ以外 → medium

**type の判断**:
- 「追加」「新規」「実装」→ feature
- 「修正」「バグ」「fix」→ bug
- 「リファクタ」「整理」「改善」→ refactor
- 「ドキュメント」「文書」「README」→ docs
- 「テスト」「検証」→ test

**phase の判断**:
- 「リサーチ」「調査」「research」→ research
- 「執筆」「記事」「edit」→ edit
- 「公開」「publish」→ publish
- それ以外 → infra

### Step 4: tasks.json の生成

タスクリストを JSON 形式で出力します。

**出力先**: 計画書と同じディレクトリに `tasks.json` として保存

```json
{
  "plan_id": "youtube-search-plan",
  "plan_path": "docs/project/youtube-search-plan.md",
  "project_name": "youtube-search-plan",
  "created_at": "2026-01-06T12:00:00+09:00",
  "tasks": [...],
  "statistics": {
    "total": 5,
    "by_status": { "todo": 5, "in_progress": 0, "done": 0 },
    "by_priority": { "high": 2, "medium": 2, "low": 1 },
    "issues_created": 0,
    "issues_failed": 0
  }
}
```

### Step 5: タスク一覧の確認

生成したタスクを表示します：

```
📋 タスク一覧

| ID   | タイトル                        | 優先度 | 種別    | フェーズ |
|------|--------------------------------|--------|---------|----------|
| T001 | tasks.schema.json の作成       | high   | feature | infra    |
| T002 | /make-task コマンド定義作成     | high   | feature | infra    |
| T003 | /new-plan コマンド定義作成      | medium | feature | infra    |

合計: 3 タスク
```

**--dry-run の場合**:

```
🔍 dry-run モード: GitHub には登録しません

tasks.json を保存しました: docs/project/tasks.json

GitHub に登録する場合は --dry-run を外して再実行してください:
  /make-task docs/project/youtube-search-plan.md
```

処理を終了

### Step 6: GitHub Project の確認

指定された Project が存在するか確認します。

```bash
gh project list --owner @me
```

**Project が存在する場合**: Step 7 に進む

**Project が存在しない場合**:

```
⚠️ GitHub Project が見つかりません

Project 名: {project_name}

対処法:
1. /new-plan で計画書を作成すると Project も自動作成されます
2. または以下のコマンドで手動作成:
   gh project create --title "{project_name}" --owner @me
```

AskUserQuestion で確認:
- 「Project を作成して続行」
- 「処理を中断」

### Step 7: GitHub Issues の作成

各タスクに対して Issue を作成します。

**Issue 作成コマンド**:

```bash
gh issue create \
  --title "{task.title}" \
  --body "{Issue本文}" \
  --label "priority:{task.priority}" \
  --label "type:{task.type}" \
  --label "phase:{task.phase}"
```

**Issue 本文テンプレート**:

```markdown
## 概要

{task.description}

## 依存タスク

{dependencies がある場合}
- [ ] #{依存タスクのIssue番号} {依存タスクのタイトル}

## 完了条件

{acceptance_criteria がある場合}
- [ ] {条件1}
- [ ] {条件2}

## 関連ドキュメント

- [{plan_filename}]({full_github_url})

---
*このIssueは /make-task コマンドで自動生成されました*
```

**リンク記述ルール（重要）**:

1. **絶対URLを使用**: Issue内の相対パスはGitHub上で404エラーになるため、必ず絶対URLを使用
   - ❌ `[計画書](docs/project/plan.md)`
   - ✅ `[PLAN-NAME](https://github.com/{owner}/{repo}/blob/main/docs/project/plan.md)`

2. **リンクテキストはファイル名**: 「計画書」等の一般名称ではなく、実際のファイル名を使用
   - ❌ `[計画書](https://...)`
   - ✅ `[IMPLEMENTATION-PLAN-v7](https://...)`

3. **URLの形式**: `https://github.com/{owner}/{repo}/blob/main/{path}`

**エラー発生時**:

```
❌ Issue 作成に失敗しました

タスク: T002 - /make-task コマンド定義作成
エラー: {エラーメッセージ}
```

AskUserQuestion で確認:
- 「スキップして続行」: 失敗したタスクを飛ばして次へ
- 「リトライ」: 同じタスクを再試行
- 「処理を中断」: 全体を中止

### Step 8: Project への追加

作成した Issue を Project に追加します。

```bash
gh project item-add {project_number} --owner @me --url {issue_url}
```

### Step 9: tasks.json の更新

作成した Issue 番号を tasks.json に記録します。

```json
{
  "task_id": "T001",
  "title": "tasks.schema.json の作成",
  "github_issue_number": 123,
  "github_issue_url": "https://github.com/user/repo/issues/123"
}
```

### Step 10: 完了レポート

```
✅ タスク登録完了

📊 統計:
- 作成した Issue: 5 件
- Project に追加: 5 件
- 失敗: 0 件

📁 出力ファイル:
- tasks.json: docs/project/tasks.json

🔗 GitHub Project:
- {project_url}

📝 次のステップ:
- GitHub Project でタスクの優先順位を確認
- 各 Issue にアサインを設定
- 作業を開始
```

## エラーハンドリング

### E001: パラメータエラー

必須パラメータが不足、または値が無効な場合。

### E002: ファイル不存在

指定された計画書ファイルが見つからない場合。

### E003: 認証エラー

GitHub 認証が必要な場合。

### E004: API エラー

GitHub API 呼び出しが失敗した場合。ユーザーに確認して続行/中断を選択。

### E005: Project 不存在

指定された GitHub Project が見つからない場合。

## 使用例

**基本的な使用**:

```
/make-task docs/project/youtube-search-plan.md
```

**dry-run で確認**:

```
/make-task docs/project/youtube-search-plan.md --dry-run
```

**Project 名を指定**:

```
/make-task docs/project/youtube-search-plan.md --project "YouTube検索機能追加"
```

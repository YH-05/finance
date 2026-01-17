---
description: GitHub Issue番号から自動実装・PR作成まで一括実行
---

# /issue-implement - Issue 自動実装

> **役割の明確化**: このコマンドは **Issue から PR 作成までの完全自動化** に特化しています。
>
> - テスト作成のみ → `/write-tests`
> - 品質チェックのみ → `/ensure-quality`
> - PR作成のみ → `/commit-and-pr`

**目的**: GitHub Issue 番号を指定し、テスト作成→実装→品質保証→PR作成を一括実行

## 使用例

```bash
/issue-implement 123
```

---

## Phase 0: Issue検証・準備

### 0.1 引数の検証

**引数がない場合**:

```
エラー: Issue番号を指定してください。

使用方法:
  /issue-implement <issue_number>

例:
  /issue-implement 123
```

### 0.2 Issue情報の取得

```bash
gh issue view {number} --json number,title,body,labels,state,url
```

**Issue が見つからない場合**:

```
エラー: Issue #{number} が見つかりません。

解決方法:
  gh issue list --state open
```

**Issue がクローズ済みの場合**:

AskUserQuestion で確認:
- 続行する（再オープンせずに実装）
- 処理を中断

### 0.3 チェックリスト抽出

Issue本文から以下のパターンを抽出:
- `- [ ] タスク内容`
- `## 受け入れ条件` セクション配下の項目

**チェックリストがない場合**:

AskUserQuestion で確認:
- Issue本文から受け入れ条件を自動生成
- 手動でタスクを入力

### 0.4 対象パッケージの特定

Issue本文またはラベルから対象パッケージを推定:
- `market_analysis`, `rss`, `finance`, `factor`, `strategy` など

**特定できない場合**:

AskUserQuestion でユーザーに確認:

```yaml
question: "どのパッケージに実装しますか？"
header: "対象パッケージ"
options:
  - label: "market_analysis"
    description: "市場分析ライブラリ"
  - label: "rss"
    description: "RSSフィード監視"
  - label: "finance"
    description: "コアインフラ"
  - label: "factor"
    description: "ファクター分析"
```

### 0.5 GitHub Project情報の取得（オプション）

```bash
# Project Item一覧を取得
gh project item-list {project_number} --owner @me --format json

# Statusフィールド情報を取得
gh project field-list {project_number} --owner @me --format json
```

**アクセス権限がない場合**: 警告を出してProject更新をスキップ

### 0.6 Phase 0 完了出力

```
================================================================================
                    /issue-implement #{number} 開始
================================================================================

## Issue 情報
- タイトル: {title}
- ラベル: {labels}
- URL: {url}

## チェックリスト
- [ ] {task1}
- [ ] {task2}
- [ ] {task3}

## 対象パッケージ
{library_name}

## 実装先
- コード: src/{library_name}/core/
- テスト: tests/{library_name}/unit/

Phase 0: 検証・準備 ✓ 完了
```

---

## Phase 1: テスト作成

**test-writer サブエージェント** を起動:

```yaml
subagent_type: "test-writer"
description: "Create tests from issue"
prompt: |
  Issue #{number} のテストを作成してください。

  ## Issue情報
  タイトル: {title}

  ## 受け入れ条件（テスト対象）
  {checklist_items}

  ## 対象パッケージ
  {library_name}

  ## テスト配置先
  tests/{library_name}/unit/

  ## 要件
  1. 受け入れ条件ごとにテストケースを作成
  2. 日本語命名（test_正常系_xxx, test_異常系_xxx）
  3. Red状態（失敗するテスト）で完了

  ## 参照テンプレート
  template/tests/unit/test_example.py
```

### Phase 1 完了条件

- [ ] テストファイルが作成されている
- [ ] `make test` で Red（失敗）状態が確認できる
- [ ] 受け入れ条件に対応するテストケースが存在する

---

## Phase 2: 実装

**feature-implementer サブエージェント** を起動:

```yaml
subagent_type: "feature-implementer"
description: "Implement issue with TDD"
prompt: |
  Issue #{number} を実装してください。

  ## Issue番号
  {number}

  ## ライブラリ名
  {library_name}

  ## 実装先
  src/{library_name}/core/

  ## テンプレート参照
  template/src/template_package/core/example.py

  ## 要件
  1. TDDサイクル（Red→Green→Refactor）を実行
  2. 各タスク完了時にIssueチェックボックスを [x] に更新
  3. quality-checker(--quick) でパスを確認

  ## Issueチェックボックス更新方法
  gh issue edit {number} --body "$(更新後の本文)"
```

### Phase 2 完了条件

- [ ] 全タスクが実装されている
- [ ] `make test` で Green（成功）状態
- [ ] Issue のチェックボックスが全て `[x]` に更新されている

---

## Phase 3: 品質保証

**quality-checker サブエージェント（--auto-fix）** を起動:

```yaml
subagent_type: "quality-checker"
description: "Auto-fix quality issues"
prompt: |
  コード品質の自動修正を実行してください。

  ## モード
  --auto-fix

  ## 目標
  make check-all が成功するまで以下を繰り返し修正:
  1. make format - コードフォーマット
  2. make lint - リントチェック
  3. make typecheck - 型チェック
  4. make test - テスト実行

  ## 参照
  - CLAUDE.md のコーディング規約
  - template/ ディレクトリの実装例
```

### Phase 3 完了条件

- [ ] `make format` がエラーなし
- [ ] `make lint` がエラーなし
- [ ] `make typecheck` がエラーなし
- [ ] `make test` が全テストパス

---

## Phase 4: PR作成

### 4.1 コード整理

**code-simplifier サブエージェント** を起動:

```yaml
subagent_type: "code-simplifier"
description: "Simplify code before commit"
prompt: |
  git diff で変更されたファイルのコード整理を実行してください。

  ## 対象
  Phase 2-3 で変更されたファイル

  ## 整理観点
  - 型ヒント完全化
  - Docstring追加（NumPy形式）
  - 命名規則統一
  - 不要コードの削除
```

### 4.2 コミット & PR作成

**`/commit-and-pr` コマンド** を実行:

code-simplifier 完了後、`/commit-and-pr` コマンドを呼び出してコミットとPR作成を一括実行する。

**追加要件**:
- コミットメッセージに `Fixes #{number}` を含める
- PR本文に Issue へのリンクを含める
- ブランチ名は `feature/issue-{number}-{slug}` 形式

### 4.3 CI確認

```bash
# PR番号を取得
PR_NUMBER=$(gh pr view --json number -q .number)

# CIステータスをチェック（最大5分待機）
gh pr checks "$PR_NUMBER" --watch
```

**CIエラーがある場合**:
1. エラー内容を分析
2. 必要な修正を実施
3. 修正をコミット＆プッシュ
4. CI再実行を待機

### Phase 4 完了条件

- [ ] ブランチが作成されている
- [ ] コミットが作成されている（`Fixes #{number}` 含む）
- [ ] PRが作成されている
- [ ] CIが全てパスしている

---

## Phase 5: 完了処理

### 5.1 GitHub Project ステータス更新

PRが作成されたら、Issueを「In Progress」に更新:

```bash
gh project item-edit \
  --project-id {project_id} \
  --id {item_id} \
  --field-id {status_field_id} \
  --single-select-option-id {in_progress_option_id}
```

**注意**: 「Done」への更新は PR の `Fixes #{number}` により、PRマージ時に GitHub Workflow が自動実行

### 5.2 完了レポート出力

```
================================================================================
                    /issue-implement #{number} 完了
================================================================================

## サマリー
- Issue: #{number} - {title}
- 実行時間: {duration}
- 作成したPR: #{pr_number}

## Phase 結果

| Phase | 状態 | 詳細 |
|-------|------|------|
| 0. 検証・準備 | ✓ | Issue情報取得済み |
| 1. テスト作成 | ✓ | {test_count} tests |
| 2. 実装 | ✓ | {task_count}/{task_count} tasks |
| 3. 品質保証 | ✓ | make check-all PASS |
| 4. PR作成 | ✓ | #{pr_number} |
| 5. 完了処理 | ✓ | Project: In Progress |

## 作成したファイル
- tests/{library_name}/unit/test_{feature}.py
- src/{library_name}/core/{feature}.py

## 次のステップ

1. PRをレビュー:
   gh pr view {pr_number} --web

2. PRをマージ:
   /merge-pr {pr_number}

3. クリーンアップ（マージ後）:
   /worktree-done feature/issue-{number}-{slug}

================================================================================
```

---

## エラーハンドリング

| Phase | エラー | 対処 |
|-------|--------|------|
| 0 | Issue not found | 処理中断、番号確認を案内 |
| 0 | Issue closed | ユーザーに確認 |
| 0 | No checklist | 受け入れ条件から自動生成を提案 |
| 1 | Test creation failed | 最大3回リトライ |
| 2 | Implementation failed | タスク分割して再試行 |
| 2 | Test still failing | 最大5回ループ後、ユーザーに確認 |
| 3 | Quality check failed | 自動修正（最大5回） |
| 4 | Branch exists | タイムスタンプ追加で新規作成 |
| 4 | CI failed | エラー分析 → 修正 → 再プッシュ |

### エラー時の出力

```
================================================================================
                    /issue-implement #{number} エラー
================================================================================

## エラー発生 Phase
Phase {n}: {phase_name}

## エラー内容
- 種類: {error_type}
- 詳細: {error_detail}

## 実行された処理
- Phase 0: 検証・準備 ✓
- Phase 1: テスト作成 ✓
- Phase 2: 実装 ✗ ({completed}/{total} tasks)
- Phase 3: 品質保証 - (未実行)
- Phase 4: PR作成 - (未実行)
- Phase 5: 完了処理 - (未実行)

## 推奨アクション
1. {action1}
2. {action2}

================================================================================
```

---

## 完了条件

このワークフローは、以下の全ての条件を満たした時点で完了:

- [ ] Phase 0: Issue情報が取得できている
- [ ] Phase 1: テストがRed状態で作成されている
- [ ] Phase 2: 全タスクが実装され、Issueチェックボックスが更新されている
- [ ] Phase 3: make check-all が成功している
- [ ] Phase 4: PRが作成され、CIがパスしている
- [ ] Phase 5: GitHub Projectが更新され、完了レポートが出力されている

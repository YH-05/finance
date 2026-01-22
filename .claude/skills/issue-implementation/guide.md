# Issue Implementation Guide

Issue 自動実装の詳細ガイドです。

---

## 1. Phase 0: Issue検証・準備・タイプ判定

### 1.1 引数の検証

**引数がない場合**:

```
エラー: Issue番号を指定してください。

使用方法:
  /issue-implement <issue_number>

例:
  /issue-implement 123
```

### 1.2 Issue情報の取得

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

### 1.3 チェックリスト抽出

Issue本文から以下のパターンを抽出:
- `- [ ] タスク内容`
- `## 受け入れ条件` セクション配下の項目

**チェックリストがない場合**:

AskUserQuestion で確認:
- Issue本文から受け入れ条件を自動生成
- 手動でタスクを入力

### 1.4 開発タイプの判定

#### 判定ロジック（優先順位順）

```yaml
判定順序:
  1. ラベルによる判定:
     - "agent" | "エージェント" → agent
     - "command" | "コマンド" → command
     - "skill" | "スキル" → skill
     - 上記以外 → python

  2. タイトル・本文のキーワードによる判定（ラベルがない場合）:
     agent:
       - "エージェントを作成" | "エージェントを追加"
       - "agent" (英語)
       - ".claude/agents/" パスへの言及

     command:
       - "コマンドを作成" | "コマンドを追加"
       - "/xxx を追加" | "/xxx コマンド"
       - ".claude/commands/" パスへの言及

     skill:
       - "スキルを作成" | "スキルを追加"
       - ".claude/skills/" パスへの言及

     python:
       - 上記以外のすべて（デフォルト）
```

#### 判定結果の確認

AskUserQuestion で確認（自動判定に確信がない場合）:

```yaml
question: "この Issue の開発タイプを確認してください"
header: "開発タイプ"
options:
  - label: "Python（推奨）"
    description: "Pythonコード開発（テスト→実装→品質保証）"
  - label: "Agent"
    description: "エージェント開発（.claude/agents/）"
  - label: "Command"
    description: "コマンド開発（.claude/commands/）"
  - label: "Skill"
    description: "スキル開発（.claude/skills/）"
```

---

## 2. Python ワークフロー（Phase 1-5）

### Phase 1: テスト作成

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

**完了条件**:
- [ ] テストファイルが作成されている
- [ ] `make test` で Red（失敗）状態が確認できる
- [ ] 受け入れ条件に対応するテストケースが存在する

### Phase 2: 実装

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

**完了条件**:
- [ ] 全タスクが実装されている
- [ ] `make test` で Green（成功）状態
- [ ] Issue のチェックボックスが全て `[x]` に更新されている

### Phase 3: 品質保証

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

**完了条件**:
- [ ] `make format` がエラーなし
- [ ] `make lint` がエラーなし
- [ ] `make typecheck` がエラーなし
- [ ] `make test` が全テストパス

### Phase 4: PR作成

#### 4.1 コード整理

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

#### 4.2 コミット & PR作成

`/commit-and-pr` コマンドを実行:

- コミットメッセージに `Fixes #{number}` を含める
- PR本文に Issue へのリンクを含める
- ブランチ名は `feature/issue-{number}-{slug}` 形式

#### 4.3 CI確認

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

### Phase 5: 完了処理

#### 5.1 GitHub Project ステータス更新

PRが作成されたら、Issueを「In Progress」に更新:

```bash
gh project item-edit \
  --project-id {project_id} \
  --id {item_id} \
  --field-id {status_field_id} \
  --single-select-option-id {in_progress_option_id}
```

**注意**: 「Done」への更新は PR の `Fixes #{number}` により、PRマージ時に GitHub Workflow が自動実行

---

## 3. Agent ワークフロー（Phase A1-A4）

### Phase A1: 要件分析

**agent-expert エージェント** を起動:

```yaml
subagent_type: "agent-expert"
description: "Analyze agent requirements"
prompt: |
  Issue #{number} のエージェント要件を分析してください。

  ## Issue情報
  タイトル: {title}
  本文: {body}

  ## 受け入れ条件
  {checklist_items}

  ## 要件
  1. AskUserQuestion でエージェントの詳細を確認
     - エージェント名（kebab-case）
     - 主要な責任と専門性
     - トリガー条件
     - 使用するツール
  2. 既存のエージェントとの重複確認
  3. 設計方針を決定

  ## 参照
  - .claude/agents/ の既存エージェント
  - .claude/skills/agent-expert/template.md
```

### Phase A2: 設計・作成

```yaml
description: "Create agent file"
prompt: |
  分析結果に基づいてエージェントファイルを作成してください。

  ## 作成先
  .claude/agents/{agent-name}.md

  ## 要件
  1. template.md に基づいた構造
  2. フロントマター（name, category, description）
  3. 目的、いつ使用するか、処理フロー
  4. 3-4個の使用例
  5. ガイドライン
```

### Phase A3: 検証

以下を確認:
- [ ] フロントマターの name がファイル名と一致
- [ ] description が簡潔で目的を説明
- [ ] category が適切に設定
- [ ] トリガー条件が明確
- [ ] 使用例が実用的

### Phase A4: PR作成

- ブランチ名: `feature/issue-{number}-agent-{name}`
- コミットメッセージ: `feat(agent): {name} エージェントを追加\n\nFixes #{number}`

---

## 4. Command ワークフロー（Phase C1-C4）

### Phase C1: 要件分析

**command-expert エージェント** を起動:

```yaml
subagent_type: "command-expert"
prompt: |
  Issue #{number} のコマンド要件を分析してください。

  ## 要件
  1. AskUserQuestion でコマンドの詳細を確認
     - コマンド名（kebab-case）
     - 目的と入力/出力
     - 処理ステップ
     - 使用するサブエージェント
  2. 類似コマンドの調査
```

### Phase C2: 設計・作成

```yaml
## 作成先
.claude/commands/{command-name}.md

## 要件
1. フロントマター（description）
2. 使用例
3. Phase構造（論理的なステップ分割）
4. 完了条件
5. エラーハンドリング
```

### Phase C3: 検証

以下を確認:
- [ ] フロントマターの description が設定されている
- [ ] 使用例が明確
- [ ] Phase の順序が論理的
- [ ] エラーハンドリングが定義されている

### Phase C4: PR作成

- ブランチ名: `feature/issue-{number}-command-{name}`
- コミットメッセージ: `feat(command): /{name} コマンドを追加\n\nFixes #{number}`

---

## 5. Skill ワークフロー（Phase S1-S4）

### Phase S1: 要件分析

**skill-expert エージェント** を起動:

```yaml
subagent_type: "skill-expert"
prompt: |
  Issue #{number} のスキル要件を分析してください。

  ## 要件
  1. AskUserQuestion でスキルの詳細を確認
     - スキル名（kebab-case）
     - 目的とドメイン
     - 必要なリソースファイル（guide.md, template.md）
     - 使用するツール
  2. 既存のスキル構造を調査
```

### Phase S2: 設計・作成

```yaml
## 作成先
.claude/skills/{skill-name}/
├── SKILL.md
├── guide.md（必要に応じて）
└── template.md（必要に応じて）

## SKILL.md 要件
1. フロントマター（name, description, allowed-tools）
2. 目的
3. いつ使用するか
4. プロセス
5. リソース（guide.md, template.md がある場合）
```

### Phase S3: 検証

以下を確認:
- [ ] SKILL.md のフロントマターが正しい
- [ ] name がディレクトリ名と一致
- [ ] allowed-tools が最小限に設定
- [ ] プロセスが論理的
- [ ] リソースファイルが正しく参照されている

### Phase S4: PR作成

- ブランチ名: `feature/issue-{number}-skill-{name}`
- コミットメッセージ: `feat(skill): {name} スキルを追加\n\nFixes #{number}`

---

## 6. エラーハンドリング

### Python ワークフロー

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

### Agent/Command/Skill ワークフロー

| Phase | エラー | 対処 |
|-------|--------|------|
| 0 | タイプ判定失敗 | AskUserQuestion でユーザーに確認 |
| X1 | 名前の重複 | 別名を提案、または既存の改善を提案 |
| X2 | ファイル作成失敗 | ディレクトリ権限を確認、リトライ |
| X3 | 検証エラー | 前フェーズに戻って修正 |
| X4 | PR作成失敗 | ブランチ名変更、またはリトライ |

---

## 7. 対象パッケージの特定

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

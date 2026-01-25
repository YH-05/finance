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

## 2. Python ワークフロー（Phase 1-7）

**🚨 重要: Python開発では必ずサブエージェントに委譲してください**

Python開発フローでは、直接コードを書くことは**禁止**です。
各 Phase で指定されたサブエージェントに**全ての開発作業を委譲**してください。

### Phase 1: テスト作成

**🚨 test-writer サブエージェントに全委譲**（必須）:

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

### Phase 2: データモデル設計

**🚨 pydantic-model-designer サブエージェントに全委譲**（必須）:

```yaml
subagent_type: "pydantic-model-designer"
description: "Design Pydantic models from issue"
prompt: |
  Issue #{number} に必要なPydanticモデルを設計・作成してください。

  ## Issue情報
  タイトル: {title}
  本文:
  {body}

  ## 受け入れ条件
  {checklist_items}

  ## 対象パッケージ
  {library_name}

  ## Phase 1 で作成されたテストファイル
  {test_files}

  ## 要件
  1. Issue要件から必要なデータ構造を特定
  2. テストコードから期待される型情報を抽出
  3. Pydanticモデルを types.py または models/ に作成
  4. フィールドに型、制約、description を設定
  5. 必要なバリデーターを実装
  6. make typecheck でパスを確認

  ## 参照
  - .claude/agents/pydantic-model-designer.md
  - template/src/template_package/types.py
```

**完了条件**:
- [ ] Issue要件に基づいたPydanticモデルが作成されている
- [ ] 全フィールドに型ヒントと description がある
- [ ] `make typecheck` がパス
- [ ] モデルが適切な場所に配置されている
- [ ] __init__.py でエクスポートされている

### Phase 3: 実装

**🚨 feature-implementer サブエージェントに全委譲**（必須）:

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

  ## Phase 2 で作成されたPydanticモデル
  {created_models}

  ## テンプレート参照
  template/src/template_package/core/example.py

  ## 要件
  1. TDDサイクル（Red→Green→Refactor）を実行
  2. Phase 2で作成したPydanticモデルを活用
  3. 各タスク完了時にIssueチェックボックスを [x] に更新
  4. quality-checker(--quick) でパスを確認

  ## Issueチェックボックス更新方法
  gh issue edit {number} --body "$(更新後の本文)"
```

**完了条件**:
- [ ] 全タスクが実装されている
- [ ] Phase 2のPydanticモデルが適切に使用されている
- [ ] `make test` で Green（成功）状態
- [ ] Issue のチェックボックスが全て `[x]` に更新されている

### Phase 4: コード整理

**🚨 code-simplifier サブエージェントに全委譲**（必須）:

```yaml
subagent_type: "code-simplifier"
description: "Simplify code before quality check"
prompt: |
  git diff で変更されたファイルのコード整理を実行してください。

  ## 対象
  Phase 1-3 で変更されたファイル

  ## 整理観点
  - 型ヒント完全化
  - Docstring追加（NumPy形式）
  - 命名規則統一
  - 不要コードの削除

  ## 参照
  - CLAUDE.md のコーディング規約
  - template/ ディレクトリの実装例
```

**完了条件**:
- [ ] 変更されたファイルのコード整理が完了
- [ ] 型ヒントが適切に追加されている
- [ ] Docstringが NumPy 形式で記述されている

### Phase 5: 品質保証

**🚨 quality-checker サブエージェントに全委譲**（--auto-fix、必須）:

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

### Phase 6: PR作成

#### 6.1 コミット & PR作成

`/commit-and-pr` コマンドを実行:

- コミットメッセージに `Fixes #{number}` を含める
- PR本文に Issue へのリンクを含める
- ブランチ名は `feature/issue-{number}-{slug}` 形式

#### 6.2 CI確認

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

### Phase 7: 完了処理

#### 7.1 GitHub Project ステータス更新

PRが作成されたら、Issueを「In Progress」に更新:

```bash
gh project item-edit \
  --project-id {project_id} \
  --id {item_id} \
  --field-id {status_field_id} \
  --single-select-option-id {in_progress_option_id}
```

**注意**: 「Done」への更新は PR の `Fixes #{number}` により、PRマージ時に GitHub Workflow が自動実行

### 🚨 Python ワークフローの禁止事項

以下の行為は**禁止**です：

| 禁止行為 | 理由 |
|----------|------|
| 直接テストコードを書く | test-writer に委譲すること |
| 直接モデルを定義する | pydantic-model-designer に委譲すること |
| 直接実装コードを書く | feature-implementer に委譲すること |
| 直接品質修正を行う | quality-checker に委譲すること |
| 直接コード整理を行う | code-simplifier に委譲すること |

**正しい実装パターン**:
1. Issue情報を取得してタイプ判定（Phase 0）
2. サブエージェントにタスクを委譲（Phase 1-5）
3. 結果を確認して次のPhaseに進む
4. 最終的にPR作成と完了処理（Phase 6-7）

---

## 3. Agent ワークフロー（Phase A1-A4）

### Phase A1-A3: agent-creator エージェントに委譲

**🚨 重要**: Agent 開発では `agent-creator` エージェントが要件分析→設計→実装→検証を一貫して実行します。

**agent-creator サブエージェント** を起動:

```yaml
subagent_type: "agent-creator"
description: "Create agent from issue"
prompt: |
  Issue #{number} に基づいてエージェントを作成してください。

  ## Issue情報
  - 番号: #{number}
  - タイトル: {title}
  - 本文:
  {body}

  ## 受け入れ条件
  {checklist_items}

  ## 要件
  1. agent-expert スキルのガイドラインに厳密に従う
  2. 要件分析 → 設計 → 実装 → 検証を一貫して実行
  3. フロントマター検証を必ず実行（agent-expert スキル参照）
  4. 既存エージェントとの重複確認

  ## 参照
  - .claude/skills/agent-expert/guide.md - 設計原則
  - .claude/skills/agent-expert/template.md - テンプレート
  - .claude/skills/agent-expert/frontmatter-review.md - 検証ルール

  ## 完了条件
  - [ ] .claude/agents/{agent-name}.md が作成されている
  - [ ] フロントマター検証がPASS
  - [ ] 3-4個の実用的な使用例が含まれている
  - [ ] MUST/NEVERガイドラインが明記されている
```

**agent-creator が実行する内容**:
1. **要件分析**: 既存エージェント確認、AskUserQuestion で詳細確認
2. **設計**: エージェント名（kebab-case）、カテゴリ、description 決定
3. **実装**: template.md に基づきファイル作成
4. **検証**: frontmatter-review.md に基づく品質検証

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

### Phase S1-S3: skill-creator エージェントに委譲

**🚨 重要**: Skill 開発では `skill-creator` エージェントが要件分析→設計→実装→検証を一貫して実行します。

**skill-creator サブエージェント** を起動:

```yaml
subagent_type: "skill-creator"
description: "Create skill from issue"
prompt: |
  Issue #{number} に基づいてスキルを作成してください。

  ## Issue情報
  - 番号: #{number}
  - タイトル: {title}
  - 本文:
  {body}

  ## 受け入れ条件
  {checklist_items}

  ## 要件
  1. skill-expert スキルのガイドラインに厳密に従う
  2. 要件分析 → 設計 → 実装 → 検証を一貫して実行
  3. フロントマター検証を必ず実行（skill-expert スキル参照）
  4. 既存スキルとの重複確認
  5. ナレッジベースの原則に従う（知識提供に徹し、実処理はツールに委譲）

  ## 参照
  - .claude/skills/skill-expert/guide.md - 設計原則
  - .claude/skills/skill-expert/template.md - テンプレート

  ## 作成先
  .claude/skills/{skill-name}/
  ├── SKILL.md（必須）
  ├── guide.md（必要に応じて）
  └── template.md（必要に応じて）

  ## 完了条件
  - [ ] .claude/skills/{skill-name}/SKILL.md が作成されている
  - [ ] フロントマター検証がPASS
  - [ ] 3-4個の実用的な使用例が含まれている
  - [ ] MUST/SHOULD品質基準が明記されている
  - [ ] 必要なリソースファイル（guide.md等）が作成されている
```

**skill-creator が実行する内容**:
1. **要件分析**: 既存スキル確認、AskUserQuestion で詳細確認
2. **設計**: スキル名（kebab-case）、カテゴリ、リソース構成決定
3. **実装**: SKILL.md + 必要なリソースファイル作成
4. **検証**: フロントマター・構造・実用性の品質検証

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
| 2 | Model design failed | 要件を再確認、シンプルなモデルから開始 |
| 3 | Implementation failed | タスク分割して再試行 |
| 3 | Test still failing | 最大5回ループ後、ユーザーに確認 |
| 4 | Code simplification failed | 変更対象を絞って再試行 |
| 5 | Quality check failed | 自動修正（最大5回） |
| 6 | Branch exists | タイムスタンプ追加で新規作成 |
| 6 | CI failed | エラー分析 → 修正 → 再プッシュ |

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

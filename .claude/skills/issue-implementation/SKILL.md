---
name: issue-implementation
description: |
  GitHub Issue の自動実装と PR 作成を行うスキル。
  /issue-implement コマンドで使用。
  Python/Agent/Command/Skill の4つの開発タイプに対応。
  複数Issue番号を指定すると連続実装し、1つのPRにまとめる。
allowed-tools: Bash, Read, Write, Glob, Grep, AskUserQuestion, Task
---

# Issue Implementation

GitHub Issue から自動実装・PR作成までを一括実行するナレッジベーススキルです。

## 目的

このスキルは以下を提供します：

- **開発タイプ判定**: ラベル・キーワードから適切なワークフローを自動選択
- **Python ワークフロー**: テスト作成→実装→品質保証→PR作成
- **Agent/Command/Skill ワークフロー**: 要件分析→設計・作成→検証→PR作成
- **自動品質チェック**: make check-all の自動実行と修正
- **複数Issue連続実装**: 複数のIssueを連続実装し、1つのPRにまとめる

## いつ使用するか

### プロアクティブ使用（自動で検討）

以下の状況では、ユーザーが明示的に要求しなくても使用を検討：

1. **Issue 実装の議論**
   - 「#XXX を実装して」
   - 「この Issue を進めて」
   - 実装開始の意思表示

### 明示的な使用（ユーザー要求）

- `/issue-implement <番号>` コマンドの実行時
- `/issue-implement <番号1> <番号2> ...` 複数Issue連続実装時

## 対応する開発タイプ

| タイプ | 対象 | ワークフロー |
|--------|------|--------------|
| `python` | Pythonコード開発 | テスト作成→データモデル設計→実装→コード整理→品質保証→PR作成 |
| `agent` | エージェント開発 | 要件分析→設計・作成→検証→PR作成 |
| `command` | コマンド開発 | 要件分析→設計・作成→検証→PR作成 |
| `skill` | スキル開発 | 要件分析→設計・作成→検証→PR作成 |

## 複数Issue連続実装モード

複数のIssue番号を指定すると、連続実装モードが有効になります。

### コマンド構文

```bash
# 単一Issue（従来通り）
/issue-implement 958

# 複数Issue（連続実装モード）
/issue-implement 958 959 960
```

### 処理フロー（複数Issue）

```
issue-implementer サブエージェントに Issue #958 を委譲 → コミット
     ↓（コンテキスト分離）
issue-implementer サブエージェントに Issue #959 を委譲 → コミット
     ↓（コンテキスト分離）
issue-implementer サブエージェントに Issue #960 を委譲 → コミット → PR作成（最後のみ）
```

**重要**: 各Issueを別のサブエージェントに委譲することで、コンテキストが自動的に分離されます。

### 動作の違い

| 項目 | 単一Issue | 複数Issue |
|------|-----------|-----------|
| 実行方式 | 直接実行 | issue-implementer サブエージェントに委譲 |
| 各Issue完了後 | コミット + PR作成 | コミットのみ（コンテキスト自動分離） |
| PR作成タイミング | 即座 | 最後のIssueのみ |
| PR形式 | 1 Issue = 1 PR | 複数 Issue = 1 PR |
| エラー時 | 即座に停止 | ユーザーに確認（続行/停止） |

### エラーハンドリング（複数Issue）

途中でエラーが発生した場合、ユーザーに確認します：

```yaml
question: "Issue #{number} でエラーが発生しました。どうしますか？"
header: "エラー対応"
options:
  - label: "スキップして次へ進む"
    description: "このIssueをスキップし、次のIssueに進む"
  - label: "停止してここまでをPR"
    description: "エラー発生前までの変更でPRを作成"
  - label: "全て中断"
    description: "処理を中断し、変更はコミット済みのまま維持"
```

## プロセス

### Phase 0: Issue検証・タイプ判定（共通）

```
Phase 0: Issue検証・タイプ判定
    │
    ├─ Issue 情報取得
    │   └─ gh issue view {number} --json ...
    │
    ├─ チェックリスト抽出
    │   └─ `- [ ]` パターンまたは受け入れ条件セクション
    │
    ├─ 開発タイプ判定
    │   │
    │   ├─ ラベル判定（優先）
    │   │   ├─ "agent" | "エージェント" → agent
    │   │   ├─ "command" | "コマンド" → command
    │   │   ├─ "skill" | "スキル" → skill
    │   │   └─ 上記以外 → python
    │   │
    │   └─ キーワード判定（ラベルなし時）
    │       ├─ ".claude/agents/" パスへの言及 → agent
    │       ├─ ".claude/commands/" パスへの言及 → command
    │       ├─ ".claude/skills/" パスへの言及 → skill
    │       └─ 上記以外 → python
    │
    └─ 対象パッケージ特定（python タイプの場合）
```

### Python ワークフロー（Phase 1-7）

**🚨 重要**: Python 開発では、各 Phase を専門のサブエージェントに**必ず委譲**します。
直接コードを書くのではなく、サブエージェントに全ての開発作業を委譲してください。

```
Phase 1: テスト作成
    └─ 🚨 test-writer サブエージェントに**全委譲**
        ├─ 受け入れ条件ごとにテストケース作成
        └─ Red状態（失敗するテスト）で完了

Phase 2: データモデル設計
    └─ 🚨 pydantic-model-designer サブエージェントに**全委譲**
        ├─ Issue要件からPydanticモデルを設計
        ├─ types.py または models/ に配置
        ├─ フィールド定義（型、制約、バリデーション）
        └─ make typecheck でパス確認

Phase 3: 実装
    └─ 🚨 feature-implementer サブエージェントに**全委譲**
        ├─ TDDサイクル実行（Red→Green→Refactor）
        ├─ Phase 2で作成したモデルを活用
        ├─ 各タスク完了時に Issue チェックボックス更新
        └─ quality-checker(--quick) でパス確認

Phase 4: コード整理
    └─ 🚨 code-simplifier サブエージェントに**全委譲**
        ├─ 型ヒント完全化
        ├─ Docstring追加（NumPy形式）
        ├─ 命名規則統一
        └─ 不要コードの削除

Phase 5: 品質保証
    └─ 🚨 quality-checker サブエージェントに**全委譲**（--auto-fix）
        ├─ 自動修正ループ（最大5回）
        └─ make check-all 成功で完了

Phase 6: PR作成
    ├─ /commit-and-pr コマンド実行
    └─ CI確認（最大5分待機）

Phase 7: 完了処理
    ├─ GitHub Project ステータス更新
    └─ 完了レポート出力
```

**禁止事項**: Python開発フローで直接コードを編集することは禁止です。必ずサブエージェントに委譲してください。

### Agent/Command/Skill ワークフロー

```
Phase A1-A3/S1-S3: 開発（専門エージェントに委譲）
    │
    ├─ Agent開発 → agent-creator エージェントに全委譲
    │   └─ 要件分析→設計→実装→検証を一貫実行
    │
    ├─ Skill開発 → skill-creator エージェントに全委譲
    │   └─ 要件分析→設計→実装→検証を一貫実行
    │
    └─ Command開発 → command-expert エージェント起動
        └─ 要件分析→設計→実装→検証

Phase A4/C4/S4: PR作成
    └─ /commit-and-pr コマンド実行
```

**重要**: Agent/Skill 開発では、`agent-creator`/`skill-creator` エージェントが
expert スキルを参照して設計・実装・検証を一貫して実行します。

## 活用ツールの使用方法

### gh CLI

```bash
# Issue 情報取得
gh issue view {number} --json number,title,body,labels,state,url

# Issue チェックボックス更新
gh issue edit {number} --body "$(更新後の本文)"

# PR作成後のCI確認
gh pr checks "$PR_NUMBER" --watch
```

### サブエージェント連携

**🚨 重要**: Python開発フローでは、以下のエージェントに**必ず委譲**してください。直接コードを書くことは禁止です。

| エージェント | 用途 | 委譲 |
|--------------|------|------|
| test-writer | 🚨 **テスト作成を全委譲**（Python実装） | 必須 |
| pydantic-model-designer | 🚨 **データモデル設計を全委譲**（Pydanticモデル作成） | 必須 |
| feature-implementer | 🚨 **TDD実装を全委譲**（Python実装） | 必須 |
| quality-checker | 🚨 **品質自動修正を全委譲** | 必須 |
| code-simplifier | 🚨 **コード整理を全委譲** | 必須 |
| agent-creator | 🚨 **Agent開発を一括実行**（要件分析→設計→実装→検証） | 必須 |
| skill-creator | 🚨 **Skill開発を一括実行**（要件分析→設計→実装→検証） | 必須 |
| command-expert | 🚨 **コマンド作成を全委譲** | 必須 |

## リソース

このスキルには以下のリソースが含まれています：

### ./guide.md

Issue 実装の詳細ガイド：

- 各 Phase の詳細フロー
- 開発タイプ判定ロジック
- サブエージェントの起動方法
- エラーハンドリング

### ./template.md

完了レポートテンプレート：

- 成功時のレポート形式
- エラー時のレポート形式

## 使用例

### 例1: Python 実装（単一Issue）

**状況**: Python コードの Issue を実装したい

**処理**:
```bash
/issue-implement 123
```

1. Phase 0: Issue検証（python タイプ判定）
2. Phase 1: test-writer でテスト作成
3. Phase 2: pydantic-model-designer でデータモデル設計
4. Phase 3: feature-implementer で実装
5. Phase 4: code-simplifier でコード整理
6. Phase 5: quality-checker で品質保証
7. Phase 6: PR作成
8. Phase 7: 完了処理

**期待される出力**:
```markdown
## /issue-implement #123 完了

- Issue: #123 - ユーザー認証機能の追加
- 作成したPR: #456

| Phase | 状態 |
|-------|------|
| 0. 検証・準備 | ✓ |
| 1. テスト作成 | ✓ (5 tests) |
| 2. データモデル設計 | ✓ (3 models) |
| 3. 実装 | ✓ (3/3 tasks) |
| 4. コード整理 | ✓ code-simplifier |
| 5. 品質保証 | ✓ make check-all PASS |
| 6. PR作成 | ✓ #456 |
| 7. 完了処理 | ✓ |
```

---

### 例2: 複数Issue連続実装

**状況**: 依存関係のある複数のIssueを連続で実装したい

**処理**:
```bash
/issue-implement 958 959 960
```

**処理フロー**:
1. issue-implementer サブエージェントに Issue #958 を委譲 → コミット（コンテキスト分離）
2. issue-implementer サブエージェントに Issue #959 を委譲 → コミット（コンテキスト分離）
3. issue-implementer サブエージェントに Issue #960 を委譲 → コミット → PR作成

**期待される出力**:
```markdown
## /issue-implement #958 #959 #960 完了

### サマリー
- 実装したIssue: 3件
- 作成したPR: #500

### Issue別結果
| Issue | タイトル | 状態 |
|-------|----------|------|
| #958 | analyze → market依存関係の確立 | ✓ |
| #959 | factor連携 | ✓ |
| #960 | strategy連携 | ✓ |

### コミット履歴
1. feat(analyze): market依存関係を確立 (Fixes #958)
2. feat(factor): market+analyze依存関係を確立 (Fixes #959)
3. feat(strategy): 全パッケージ依存関係を確立 (Fixes #960)

### 作成したPR
- PR: #500
- URL: https://github.com/YH-05/finance/pull/500

### 次のステップ
1. PRをレビュー: gh pr view 500 --web
2. PRをマージ: /merge-pr 500
```

---

### 例4: エージェント作成

**状況**: 新しいエージェントを作成する Issue

**処理**:
```bash
/issue-implement 200  # ラベル: agent
```

1. Phase 0: Issue検証（agent タイプ判定）
2. Phase A1: agent-expert で要件分析
3. Phase A2: エージェントファイル作成
4. Phase A3: 検証
5. Phase A4: PR作成

## 品質基準

### 必須（MUST）

- [ ] Issue 情報が正しく取得されている
- [ ] 開発タイプが正しく判定されている
- [ ] 適切なワークフローが実行されている
- [ ] PR が作成され CI がパスしている

### 推奨（SHOULD）

- Issue のチェックボックスが更新されている
- GitHub Project ステータスが更新されている
- 完了レポートが出力されている

### 複数Issue連続実装時の追加基準

**必須（MUST）**:
- [ ] 各Issueごとにコミットが作成されている
- [ ] 最後のIssue完了後にPRが作成されている
- [ ] エラー発生時にユーザーに確認している
- [ ] 全Issueの変更が1つのPRにまとまっている

**推奨（SHOULD）**:
- 各Issueのコミットメッセージに `Fixes #<number>` が含まれている
- PR本文に全ての実装Issueがリストされている
- 進捗レポートが各Issue完了時に出力されている

## 出力フォーマット

### 開始時

```
================================================================================
                    /issue-implement #{number} 開始
================================================================================

## Issue 情報
- タイトル: {title}
- ラベル: {labels}
- URL: {url}

## 開発タイプ
{development_type} → {workflow_description}

## チェックリスト
- [ ] {task1}
- [ ] {task2}

Phase 0: 検証・準備・タイプ判定 ✓ 完了
```

### 完了時

```
================================================================================
                    /issue-implement #{number} 完了
================================================================================

## サマリー
- Issue: #{number} - {title}
- 作成したPR: #{pr_number}

## Phase 結果
| Phase | 状態 | 詳細 |
|-------|------|------|
| 0. 検証・準備 | ✓ | Issue情報取得済み |
| 1. テスト作成 | ✓ | {test_count} tests |
| 2. データモデル設計 | ✓ | {model_count} models |
| 3. 実装 | ✓ | {task_count} tasks |
| 4. コード整理 | ✓ | code-simplifier |
| 5. 品質保証 | ✓ | make check-all PASS |
| 6. PR作成 | ✓ | #{pr_number} |
| 7. 完了処理 | ✓ | Project更新済み |

## 次のステップ
1. PRをレビュー: gh pr view {pr_number} --web
2. PRをマージ: /merge-pr {pr_number}
```

## エラーハンドリング

### Python ワークフロー

| Phase | エラー | 対処 |
|-------|--------|------|
| 0 | Issue not found | 処理中断、番号確認を案内 |
| 1 | Test creation failed | 最大3回リトライ |
| 2 | Model design failed | 要件を再確認、シンプルなモデルから開始 |
| 3 | Implementation failed | タスク分割して再試行 |
| 4 | Code simplification failed | 変更対象を絞って再試行 |
| 5 | Quality check failed | 自動修正（最大5回） |
| 6 | CI failed | エラー分析 → 修正 → 再プッシュ |

### Agent/Command/Skill ワークフロー

| Phase | エラー | 対処 |
|-------|--------|------|
| 0 | タイプ判定失敗 | AskUserQuestion でユーザーに確認 |
| X1 | 名前の重複 | 別名を提案、または既存の改善を提案 |
| X2 | ファイル作成失敗 | ディレクトリ権限を確認、リトライ |
| X3 | 検証エラー | 前フェーズに戻って修正 |

## 完了条件

### Python ワークフロー

- [ ] Phase 0: Issue情報が取得でき、開発タイプが `python` と判定
- [ ] Phase 1: 🚨 **test-writer に委譲**してテストがRed状態で作成
- [ ] Phase 2: 🚨 **pydantic-model-designer に委譲**してPydanticモデルが作成され、make typecheckがパス
- [ ] Phase 3: 🚨 **feature-implementer に委譲**して全タスクが実装され、Issueチェックボックスが更新
- [ ] Phase 4: 🚨 **code-simplifier に委譲**してコード整理が完了
- [ ] Phase 5: 🚨 **quality-checker に委譲**して make check-all が成功
- [ ] Phase 6: PRが作成され、CIがパス
- [ ] Phase 7: 完了レポートが出力

**🚨 禁止**: 直接コードを編集することは禁止。必ず上記エージェントに委譲すること。

### Agent/Command/Skill ワークフロー

- [ ] Phase 0: Issue情報が取得でき、開発タイプが判定
- [ ] Phase X1-X3: 専門エージェントによる開発が完了
  - [ ] 🚨 **Agent開発**: `agent-creator` エージェントが要件分析→設計→実装→検証を一括実行
  - [ ] 🚨 **Skill開発**: `skill-creator` エージェントが要件分析→設計→実装→検証を一括実行
  - [ ] Command開発: `command-expert` エージェントで実行
- [ ] Phase X4: PRが作成され、CIがパス

### 複数Issue連続実装ワークフロー

- [ ] 引数から複数のIssue番号が正しく解析されている
- [ ] 各Issueが issue-implementer サブエージェントに委譲されている
- [ ] 各Issue完了後にコミットが作成されている（コンテキスト自動分離）
- [ ] エラー発生時にユーザーに確認し、選択に応じた処理が実行されている
- [ ] 最後のIssue完了後にPRが作成されている
- [ ] PR本文に全ての実装Issueがリストされている
- [ ] 完了レポートに全Issueの結果が含まれている

## 関連スキル

- **issue-creation**: Issue の作成
- **issue-refinement**: Issue のブラッシュアップ
- **issue-sync**: コメントからの同期
- **agent-expert**: エージェント設計
- **skill-expert**: スキル設計

## 参考資料

- `CLAUDE.md`: プロジェクト全体のガイドライン
- `.claude/commands/issue-implement.md`: /issue-implement コマンド定義
- `docs/testing-strategy.md`: テスト戦略

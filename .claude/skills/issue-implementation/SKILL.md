---
name: issue-implementation
description: |
  GitHub Issue の自動実装と PR 作成を行うスキル。
  /issue-implement コマンドで使用。
  Python/Agent/Command/Skill の4つの開発タイプに対応。
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

## いつ使用するか

### プロアクティブ使用（自動で検討）

以下の状況では、ユーザーが明示的に要求しなくても使用を検討：

1. **Issue 実装の議論**
   - 「#XXX を実装して」
   - 「この Issue を進めて」
   - 実装開始の意思表示

### 明示的な使用（ユーザー要求）

- `/issue-implement <番号>` コマンドの実行時

## 対応する開発タイプ

| タイプ | 対象 | ワークフロー |
|--------|------|--------------|
| `python` | Pythonコード開発 | テスト作成→実装→品質保証→PR作成 |
| `agent` | エージェント開発 | 要件分析→設計・作成→検証→PR作成 |
| `command` | コマンド開発 | 要件分析→設計・作成→検証→PR作成 |
| `skill` | スキル開発 | 要件分析→設計・作成→検証→PR作成 |

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

### Python ワークフロー（Phase 1-5）

```
Phase 1: テスト作成
    └─ test-writer サブエージェント起動
        ├─ 受け入れ条件ごとにテストケース作成
        └─ Red状態（失敗するテスト）で完了

Phase 2: 実装
    └─ feature-implementer サブエージェント起動
        ├─ TDDサイクル実行（Red→Green→Refactor）
        ├─ 各タスク完了時に Issue チェックボックス更新
        └─ quality-checker(--quick) でパス確認

Phase 3: 品質保証
    └─ quality-checker サブエージェント起動（--auto-fix）
        ├─ 自動修正ループ（最大5回）
        └─ make check-all 成功で完了

Phase 4: PR作成
    ├─ code-simplifier サブエージェント起動
    ├─ /commit-and-pr コマンド実行
    └─ CI確認（最大5分待機）

Phase 5: 完了処理
    ├─ GitHub Project ステータス更新
    └─ 完了レポート出力
```

### Agent/Command/Skill ワークフロー

```
Phase A1/C1/S1: 要件分析
    └─ xxx-expert サブエージェント起動
        ├─ AskUserQuestion で詳細確認
        └─ 既存との重複確認

Phase A2/C2/S2: 設計・作成
    └─ テンプレートに基づきファイル作成

Phase A3/C3/S3: 検証
    ├─ フロントマター検証
    ├─ 構造検証
    └─ エラー時は前フェーズに戻る

Phase A4/C4/S4: PR作成
    └─ /commit-and-pr コマンド実行
```

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

| エージェント | 用途 |
|--------------|------|
| test-writer | テスト作成（Python実装） |
| feature-implementer | TDD実装（Python実装） |
| quality-checker | 品質自動修正 |
| code-simplifier | コード整理 |
| agent-expert | エージェント作成 |
| command-expert | コマンド作成 |
| skill-expert | スキル作成 |

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

### 例1: Python 実装

**状況**: Python コードの Issue を実装したい

**処理**:
```bash
/issue-implement 123
```

1. Phase 0: Issue検証（python タイプ判定）
2. Phase 1: test-writer でテスト作成
3. Phase 2: feature-implementer で実装
4. Phase 3: quality-checker で品質保証
5. Phase 4: PR作成
6. Phase 5: 完了処理

**期待される出力**:
```markdown
## /issue-implement #123 完了

- Issue: #123 - ユーザー認証機能の追加
- 作成したPR: #456

| Phase | 状態 |
|-------|------|
| 0. 検証・準備 | ✓ |
| 1. テスト作成 | ✓ (5 tests) |
| 2. 実装 | ✓ (3/3 tasks) |
| 3. 品質保証 | ✓ make check-all PASS |
| 4. PR作成 | ✓ #456 |
| 5. 完了処理 | ✓ |
```

---

### 例2: エージェント作成

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
...

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
| 2 | Implementation failed | タスク分割して再試行 |
| 3 | Quality check failed | 自動修正（最大5回） |
| 4 | CI failed | エラー分析 → 修正 → 再プッシュ |

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
- [ ] Phase 1: テストがRed状態で作成
- [ ] Phase 2: 全タスクが実装され、Issueチェックボックスが更新
- [ ] Phase 3: make check-all が成功
- [ ] Phase 4: PRが作成され、CIがパス
- [ ] Phase 5: 完了レポートが出力

### Agent/Command/Skill ワークフロー

- [ ] Phase 0: Issue情報が取得でき、開発タイプが判定
- [ ] Phase X1: 要件が分析され、名前が決定
- [ ] Phase X2: ファイルが作成され、必須セクションが含まれる
- [ ] Phase X3: 検証チェックリストがすべてパス
- [ ] Phase X4: PRが作成され、CIがパス

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

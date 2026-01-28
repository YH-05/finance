---
name: issue-implement-single
description: |
  単一の GitHub Issue を実装するスキル（コンテキスト分離）。
  context: fork により分離されたコンテキストで実行される。
  Python/Agent/Command/Skill の4つの開発タイプに対応。
context: fork
agent: general-purpose
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, Task
---

# Issue Implement Single

単一の GitHub Issue を分離されたコンテキストで実装するスキルです。

## 重要: このスキルは context: fork で実行される

- 親のコンテキストから分離された環境で実行されます
- 実装の詳細は親に返りません（サマリーのみ）
- 複数Issue連続実装時のコンテキスト増大を防ぎます

---

## 入力

```
$ARGUMENTS = <issue_number> [--skip-pr]
```

- `issue_number`: 実装する GitHub Issue 番号（必須）
- `--skip-pr`: PR作成をスキップ（複数Issue連続実装時に使用）

---

## 🚨 必須ルール: Task ツールによるサブエージェント起動

**直接コードを書くことは絶対に禁止です。**

Python ワークフローでは、各 Phase で必ず **Task ツール**を使用してサブエージェントを起動してください。

### 禁止される行為

- Read/Write/Edit ツールで直接テストコードを書く
- Read/Write/Edit ツールで直接実装コードを書く
- サブエージェントを起動せずに Phase を完了したとみなす

### 必須の行為

各 Phase で Task ツールを呼び出し、以下のエージェントを起動すること：

| Phase | subagent_type | 用途 |
|-------|---------------|------|
| 1 | `test-writer` | テスト作成 |
| 2 | `pydantic-model-designer` | データモデル設計 |
| 3 | `feature-implementer` | TDD実装 |
| 4 | `code-simplifier` | コード整理 |
| 5 | `quality-checker` | 品質自動修正 |

### 判定基準

Task ツールを使わずに直接実装した場合、そのワークフローは **失敗** とみなします。

---

## 対応する開発タイプ

| タイプ | 対象 | ワークフロー |
|--------|------|--------------|
| `python` | Pythonコード開発 | テスト作成→データモデル設計→実装→コード整理→品質保証→コミット |
| `agent` | エージェント開発 | agent-creator に委譲→コミット |
| `command` | コマンド開発 | command-expert に委譲→コミット |
| `skill` | スキル開発 | skill-creator に委譲→コミット |

---

## 処理フロー

```
┌─────────────────────────────────────────────────────────────┐
│ Phase 0: Issue検証・タイプ判定                               │
│    ├─ gh issue view {number} で情報取得                     │
│    ├─ チェックリスト抽出                                     │
│    └─ 開発タイプ判定（ラベル/キーワード）                    │
│                                                             │
│ タイプ別ワークフロー実行                                     │
│    │                                                        │
│    ├─ Python: Phase 1-5                                     │
│    │  ├─ Task(test-writer) でテスト作成（Red）              │
│    │  ├─ Task(pydantic-model-designer) でモデル設計         │
│    │  ├─ Task(feature-implementer) で実装                   │
│    │  ├─ Task(code-simplifier) でコード整理                 │
│    │  └─ Task(quality-checker) で品質保証                   │
│    │                                                        │
│    └─ Agent/Command/Skill:                                  │
│       └─ Task(xxx-creator/expert) に全委譲                  │
│                                                             │
│ 🚨 Phase 6: コミット前検証（必須）                           │
│    ├─ make check-all を実行                                 │
│    ├─ 失敗時: エラー詳細を出力して処理中断                  │
│    └─ 成功時: コミット作成へ進む                            │
│                                                             │
│ コミット作成（Phase 6 成功時のみ）                          │
│    └─ git commit -m "feat: ... Fixes #{number}"             │
│                                                             │
│ PR作成（--skip-pr でない場合のみ）                          │
│    └─ gh pr create ...                                      │
│                                                             │
│ 🚨 Phase 7: CIチェック検証（PR作成時のみ、--skip-pr 時は省略）│
│    ├─ gh pr checks --watch --fail-fast で完了待ち           │
│    ├─ 全パス: 作業完了                                      │
│    └─ 失敗: エラー修正→再プッシュ→再検証（最大3回）        │
│                                                             │
│ サマリー出力（親に返却される情報）                           │
└─────────────────────────────────────────────────────────────┘
```

---

## 開発タイプ判定ロジック

```yaml
判定順序:
  1. ラベルによる判定（優先）:
     - "agent" | "エージェント" → agent
     - "command" | "コマンド" → command
     - "skill" | "スキル" → skill
     - 上記以外 → python

  2. キーワード判定（ラベルなし時）:
     - ".claude/agents/" パスへの言及 → agent
     - ".claude/commands/" パスへの言及 → command
     - ".claude/skills/" パスへの言及 → skill
     - 上記以外 → python
```

---

## サブエージェント連携

### Python ワークフロー

| Phase | subagent_type | prompt に含める情報 |
|-------|---------------|---------------------|
| 1 | `test-writer` | Issue情報、受け入れ条件、対象パッケージ |
| 2 | `pydantic-model-designer` | Issue情報、Phase 1のテストファイル |
| 3 | `feature-implementer` | Issue番号、ライブラリ名、Phase 2のモデル |
| 4 | `code-simplifier` | 変更されたファイル一覧 |
| 5 | `quality-checker` | --auto-fix モード |
| 6 | **直接実行** | `make check-all` でコミット前検証 |

### Agent/Command/Skill ワークフロー

| タイプ | subagent_type | 備考 |
|--------|---------------|------|
| agent | `agent-creator` | 要件分析→設計→実装→検証を一括実行 |
| command | `command-expert` | コマンド設計→作成 |
| skill | `skill-creator` | 要件分析→設計→実装→検証を一括実行 |

---

## 🚨 Phase 6: コミット前検証（必須）

**コミット前に `make check-all` を実行し、成功した場合のみコミットを作成する。**

この検証により、CI で発生するエラーを事前に防止します。

### 実行手順

```bash
# 1. make check-all を実行
make check-all

# 2. 終了コードを確認
# - 0: 成功 → コミット作成へ進む
# - 非0: 失敗 → エラー詳細を出力して処理中断
```

### 失敗時の対応

`make check-all` が失敗した場合:

1. **エラー内容を詳細に出力**
   ```yaml
   phase6_failure:
     format: [PASS/FAIL]
     lint: [PASS/FAIL] - エラー詳細
     typecheck: [PASS/FAIL] - エラー詳細
     test: [PASS/FAIL] - 失敗したテスト一覧
   ```

2. **処理を中断**（コミットは作成しない）

3. **サマリーにエラー情報を含めて返却**

### 成功時の対応

`make check-all` が成功した場合:

1. **成功ログを出力**
   ```
   ✅ Phase 6: コミット前検証成功
   - format: PASS
   - lint: PASS
   - typecheck: PASS
   - test: PASS (XX tests)
   ```

2. **コミット作成へ進む**

### 重要: 検証をスキップしない

以下の理由により、Phase 6 の検証は**絶対にスキップしてはいけない**:

- CI でのエラーを事前に防止
- pre-commit フックはテストを含まない
- quality-checker の修正後に新たな問題が発生する可能性がある

---

## 🚨 Phase 7: CIチェック検証（PR作成時のみ）

**PR作成後（`--skip-pr` でない場合）、GitHub Actions の CIチェックが全てパスするまで作業を完了としない。**

`--skip-pr` の場合は、親スキル（issue-implementation-serial）がPR作成後にCIチェックを検証するため、このPhaseはスキップする。

### 実行手順

#### 7.1 CIチェックの完了待ち

```bash
# CIチェックの完了を待つ（最大10分）
gh pr checks <pr-number> --watch --fail-fast
```

#### 7.2 CIチェック結果の確認

```bash
gh pr checks <pr-number> --json name,state,bucket,description
```

#### 7.3 全チェックがパスした場合

→ 作業完了としてサマリーを出力

#### 7.4 いずれかのチェックが失敗した場合

1. **失敗したチェックのログを確認**
   ```bash
   gh run view <run-id> --log-failed
   ```

2. **エラー原因を分析し修正を実施**

3. **修正をコミット・プッシュ**
   ```bash
   git add <修正ファイル>
   git commit -m "fix: CI エラーを修正"
   git push
   ```

4. **再度CIチェックを検証（7.1 に戻る）**
   - 最大3回まで修正→再検証を繰り返す
   - 3回失敗した場合はエラーサマリーを返却

---

## コミットメッセージ形式

```bash
git commit -m "$(cat <<'EOF'
feat(<scope>): <変更内容の要約>

<詳細説明>

Fixes #<issue_number>

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"
```

---

## 出力フォーマット（親に返却されるサマリー）

### 成功時

```yaml
status: success
issue:
  number: 123
  title: "ユーザー認証機能の追加"
  type: python
implementation:
  files_created:
    - src/finance/auth/authenticator.py
    - tests/finance/unit/auth/test_authenticator.py
  files_modified:
    - src/finance/__init__.py
pre_commit_validation:  # Phase 6 の結果
  status: passed
  format: PASS
  lint: PASS
  typecheck: PASS
  test: PASS (15 tests)
commit:
  hash: "abc1234"
  message: "feat(auth): ユーザー認証機能を追加"
pr:
  number: 456  # --skip-pr の場合は null
  url: "https://github.com/YH-05/finance/pull/456"
ci_checks:  # Phase 7 の結果（PR作成時のみ、--skip-pr の場合は null）
  status: passed
  checks:
    - name: "check-all"
      state: "pass"
  fix_attempts: 0  # CI修正の試行回数
```

### 失敗時（Phase 6 コミット前検証失敗）

```yaml
status: failed
issue:
  number: 123
  title: "ユーザー認証機能の追加"
  type: python
error:
  phase: 6
  message: "コミット前検証（make check-all）が失敗しました"
  details: |
    format: PASS
    lint: FAIL - src/finance/auth/authenticator.py:15: F401 unused import
    typecheck: PASS
    test: FAIL - test_正常系_認証成功 で AssertionError
pre_commit_validation:
  status: failed
  format: PASS
  lint: FAIL
  typecheck: PASS
  test: FAIL
partial_commit:
  hash: null  # コミットは作成されていない
```

### 失敗時（その他のPhase）

```yaml
status: failed
issue:
  number: 123
  title: "ユーザー認証機能の追加"
  type: python
error:
  phase: 3
  message: "feature-implementer がテストを通せませんでした"
  details: "test_正常系_認証成功 で AssertionError"
partial_commit:
  hash: null  # コミット前に失敗した場合
```

---

## エラーハンドリング

| Phase | エラー | 対処 |
|-------|--------|------|
| 0 | Issue not found | 処理中断、エラーサマリーを返却 |
| 0 | Issue closed | 処理中断、エラーサマリーを返却 |
| 1 | Test creation failed | 最大3回リトライ |
| 2 | Model design failed | 要件を再確認、シンプルなモデルから開始 |
| 3 | Implementation failed | タスク分割して再試行 |
| 4 | Code simplification failed | 変更対象を絞って再試行 |
| 5 | Quality check failed | 自動修正（最大5回） |
| 6 | **make check-all failed** | **処理中断、コミットしない、エラー詳細を返却** |
| 7 | **CIチェック失敗** | **エラー修正→再プッシュ→再検証（最大3回）** |
| 7 | **CI修正不可（3回失敗）** | **失敗詳細をサマリーに含めて返却** |

---

## 完了条件

### Python ワークフロー

- [ ] Phase 0: Issue情報が取得でき、開発タイプが判定
- [ ] Phase 1: Task(test-writer) でテストがRed状態で作成
- [ ] Phase 2: Task(pydantic-model-designer) でモデルが作成
- [ ] Phase 3: Task(feature-implementer) で全タスクが実装
- [ ] Phase 4: Task(code-simplifier) でコード整理が完了
- [ ] Phase 5: Task(quality-checker) で品質自動修正が完了
- [ ] **Phase 6: `make check-all` が成功（コミット前検証）**
- [ ] コミットが作成されている（Phase 6 成功後のみ）
- [ ] **Phase 7: PR作成後のCIチェックが全てパス（`--skip-pr` でない場合のみ）**
- [ ] サマリーが出力されている

### Agent/Command/Skill ワークフロー

- [ ] Phase 0: Issue情報が取得でき、開発タイプが判定
- [ ] Task(xxx-creator/expert) で開発が完了
- [ ] **`make check-all` が成功（コミット前検証）**
- [ ] コミットが作成されている（検証成功後のみ）
- [ ] **PR作成後のCIチェックが全てパス（`--skip-pr` でない場合のみ）**
- [ ] サマリーが出力されている

---

## 関連スキル

- **issue-implementation-serial**: 複数Issue連続実装（このスキルを繰り返し呼び出す）
- **tdd-development**: TDD開発のナレッジベース
- **agent-expert**: エージェント設計のナレッジベース
- **skill-expert**: スキル設計のナレッジベース

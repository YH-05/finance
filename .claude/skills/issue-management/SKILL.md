---
name: issue-management
description: |
  GitHub Issue の作成・実装・ブラッシュアップ・同期を統合管理するスキル。
  /issue, /issue-implement, /issue-refine, /sync-issue コマンドで使用。
  Issue 作成時、タスク分解時、進捗管理時にプロアクティブに使用。
allowed-tools: Bash, Read, Write, Glob, Grep, AskUserQuestion, Task
---

# Issue Management

GitHub Issue のライフサイクル全体を管理するナレッジベーススキルです。

## 目的

このスキルは以下を提供します：

- **Issue 作成**: クイック発行、パッケージ開発、軽量プロジェクトの3モード
- **Issue 実装**: 開発タイプに応じた自動実装ワークフロー
- **Issue ブラッシュアップ**: 8項目の詳細確認による内容改善
- **Issue 同期**: コメントからの進捗・タスク・仕様変更の自動抽出
- **project.md 連携**: GitHub Project との双方向同期

## いつ使用するか

### プロアクティブ使用（自動で検討）

以下の状況では、ユーザーが明示的に要求しなくても使用を検討：

1. **Issue 作成の議論**
   - 「〜を追加したい」「〜が必要」
   - バグ報告、機能要望の発生
   - タスクの分解・整理が必要

2. **進捗管理**
   - Issue のステータス確認・更新
   - コメントからの進捗同期
   - project.md との整合性確認

3. **Issue 品質改善**
   - 曖昧な Issue の明確化
   - 受け入れ条件の具体化
   - テンプレートへの準拠

### 明示的な使用（ユーザー要求）

- `/issue` - Issue 作成・タスク分解
- `/issue-implement` - Issue 自動実装
- `/issue-refine` - Issue ブラッシュアップ
- `/sync-issue` - コメント同期

## スキル設計原則

### 1. 3つの作成モード

Issue の性質に応じて最適なモードを選択します。

**モード選択ガイド**:
```yaml
quick_add:
  トリガー: /issue --add <要件>
  用途: 小さな Issue を素早く作成
  特徴: 対話的ヒアリング → 即時作成

package_mode:
  トリガー: /issue @src/<library>/docs/project.md
  用途: パッケージ開発のタスク管理
  特徴: project.md 連携、タスク分解、類似性判定

lightweight_mode:
  トリガー: /issue @docs/project/<slug>.md
  用途: 軽量プロジェクトのタスク管理
  特徴: GitHub Project 連携、ステータス同期
```

### 2. 開発タイプ別ワークフロー

Issue の内容から自動判定し、適切なワークフローを選択します。

| タイプ | 対象 | ワークフロー |
|--------|------|--------------|
| python | Pythonコード | テスト→実装→品質保証→PR作成 |
| agent | エージェント | 要件分析→設計・作成→検証→PR作成 |
| command | コマンド | 要件分析→設計・作成→検証→PR作成 |
| skill | スキル | 要件分析→設計・作成→検証→PR作成 |

### 3. 確信度ベース確認

コメント同期時の変更は確信度で判断します。

```yaml
確信度判定:
  high (0.80+): 自動適用
  medium (0.70-0.79): 適用、確認なし
  low (< 0.70): ユーザー確認必須

確認必須ケース:
  - ステータスダウングレード（done → in_progress）
  - 受け入れ条件の削除
  - 複数の矛盾する変更
```

## プロセス

### 1. Issue 作成（/issue）

#### クイック発行モード（--add）

```bash
/issue --add ログイン画面にパスワードリセット機能を追加したい
```

1. 要件概要を解析
2. AskUserQuestion で詳細確認:
   - Issue の種類（新機能/改善/バグ修正/リファクタ）
   - 対象パッケージ
   - 優先度
   - 追加の詳細
3. Issue 内容を生成・確認
4. Issue 作成、GitHub Project 追加（オプション）

#### パッケージ開発モード

```bash
/issue @src/market_analysis/docs/project.md
```

1. GitHub Issues と project.md を読み込み
2. 入力方法を選択（自然言語/外部ファイル/同期のみ）
3. task-decomposer で類似性判定・タスク分解
4. 双方向同期を実行

#### 軽量プロジェクトモード

```bash
/issue @docs/project/research-agent.md
```

1. project.md から GitHub Project 番号を抽出
2. Project フィールド情報を取得
3. パッケージ開発モードと同様に処理
4. GitHub Project ステータスも同期

### 2. Issue 実装（/issue-implement）

```bash
/issue-implement 123
```

#### Phase 0: Issue検証・タイプ判定

1. Issue 情報取得
2. チェックリスト抽出
3. 開発タイプ判定（ラベル → キーワード）

#### Python ワークフロー（Phase 1-5）

1. **テスト作成**: test-writer でRed状態のテスト作成
2. **実装**: feature-implementer でTDD実装
3. **品質保証**: quality-checker で自動修正
4. **PR作成**: code-simplifier → /commit-and-pr
5. **完了処理**: GitHub Project 更新、レポート出力

#### Agent/Command/Skill ワークフロー

1. **要件分析**: xxx-expert で詳細確認
2. **設計・作成**: テンプレートに基づきファイル作成
3. **検証**: フロントマター・構造の検証
4. **PR作成**: /commit-and-pr

### 3. Issue ブラッシュアップ（/issue-refine）

```bash
/issue-refine 123
```

1. Issue 情報取得
2. 改善対象選択（本文全体/受け入れ条件/タイトルと概要）
3. **8項目の詳細確認**:
   - 背景・目的
   - 実装スコープ
   - 連携・依存関係
   - 優先度・期限
   - ユースケース
   - 受け入れ条件詳細
   - 実装時の注意点
   - 関連 Issue
4. 改善案生成（収集情報を反映）
5. 差分表示、確認、更新

### 4. コメント同期（/sync-issue）

```bash
/sync-issue #123
```

1. Issue 情報・コメント取得
2. comment-analyzer で解析:
   - ステータス変更
   - 受け入れ条件更新
   - 新規サブタスク
   - 仕様変更
3. 確信度に基づく確認
4. task-decomposer で同期実行
5. project.md・GitHub Project 更新

## 活用ツールの使用方法

### gh CLI（GitHub 操作）

```bash
# Issue 一覧
gh issue list --state all --json number,title,body,labels,state,url --limit 100

# Issue 作成（日本語で記述）
gh issue create --title "[タイトル]" --body "[本文]" --label "[ラベル]"

# Issue 更新
gh issue edit [番号] --title "[新タイトル]" --body "[新本文]"

# Issue クローズ/リオープン
gh issue close [番号]
gh issue reopen [番号]

# コメント追加
gh issue comment [番号] --body "[コメント]"

# コメント取得（GraphQL）
gh api graphql -f query='...'
```

### GitHub Project 操作

```bash
# Project Item 一覧
gh project item-list {number} --owner @me --format json

# Project フィールド情報
gh project field-list {number} --owner @me --format json

# Project に Issue 追加
gh project item-add {number} --owner @me --url {issue_url}

# Project Item ステータス更新
gh project item-edit \
  --project-id {project_id} \
  --id {item_id} \
  --field-id {status_field_id} \
  --single-select-option-id {option_id}
```

### サブエージェント連携

| エージェント | 用途 |
|--------------|------|
| task-decomposer | タスク分解、類似性判定、同期実行 |
| comment-analyzer | コメント解析、進捗抽出 |
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

Issue 操作・同期の詳細ガイド：

- 各コマンドの詳細フロー
- ラベル自動判定ルール
- project.md フォーマット
- 競合解決ルール
- エラーハンドリング

### ./template.md

Issue テンプレート：

- 標準 Issue テンプレート
- 受け入れ条件テンプレート
- Tasklist テンプレート
- コメント同期レポート形式

## 使用例

### 例1: クイック Issue 発行

**状況**: 小さなバグを素早く Issue 化したい

**処理**:
```bash
/issue --add RSSフィードの取得でタイムアウトエラーが出る
```

1. 要件解析
2. 種類選択: バグ修正
3. 対象: rss パッケージ
4. 優先度: Medium
5. Issue 作成

**期待される出力**:
```markdown
## Issue を作成しました

- **Issue**: [#456](URL)
- **タイトル**: RSSフィードの取得でタイムアウトエラーが発生する問題を修正
- **ラベル**: bug, priority:medium, rss
```

---

### 例2: Issue 自動実装（Python）

**状況**: テスト→実装→PR作成を自動化したい

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

### 例3: Issue ブラッシュアップ

**状況**: 曖昧な Issue を明確化したい

**処理**:
```bash
/issue-refine 123
```

1. Issue 情報取得
2. 改善対象: 本文全体
3. 8項目の詳細確認（AskUserQuestion）
4. 改善案生成
5. 差分表示・確認
6. Issue 更新

**期待される出力**:
```markdown
## ブラッシュアップ結果

### Issue #123
- **タイトル改善**: より具体的に変更
- **受け入れ条件**: 5項目を測定可能な形式に変換

### 改善内容
- 概要: 「処理が遅い」→「APIレスポンスが3秒以上かかる」
- 受け入れ条件: 「パフォーマンス改善」→「平均レスポンス500ms以下」
```

---

### 例4: コメント同期

**状況**: Issue コメントから進捗を自動抽出したい

**処理**:
```bash
/sync-issue #123
```

1. コメント取得
2. comment-analyzer で解析
3. 確信度判定（low: ユーザー確認）
4. task-decomposer で同期
5. project.md・GitHub Project 更新

**期待される出力**:
```markdown
## コメント同期結果

### ステータス更新
| Issue | 変更前 | 変更後 | 根拠 |
|-------|--------|--------|------|
| #123 | in_progress | done | 「対応完了」|

### 受け入れ条件更新
| Issue | 条件 | 状態 |
|-------|------|------|
| #123 | OAuth対応 | ✅ 完了 |
```

## 品質基準

### 必須（MUST）

- [ ] Issue タイトル・本文は日本語で記述
- [ ] 受け入れ条件は測定可能な形式
- [ ] ラベルが適切に設定されている
- [ ] project.md と GitHub の整合性が保たれている
- [ ] 低確信度の変更はユーザー確認を経ている

### 推奨（SHOULD）

- Issue テンプレートに準拠している
- 依存関係が明記されている
- 関連 Issue がリンクされている
- GitHub Project ステータスが最新である

## 出力フォーマット

### Issue 作成完了時

```markdown
## Issue を作成しました

- **Issue**: [#番号](URL)
- **タイトル**: [タイトル]
- **ラベル**: [ラベル一覧]
- **Project**: [追加先]（オプション）

### 次のステップ
- 実装を開始: `/issue-implement {番号}`
```

### 同期完了時

```markdown
## 同期結果

### 更新した Issue
| Issue | 更新内容 |
|-------|----------|
| #123 | ステータス: done, 条件2件完了 |

### project.md の更新
- [更新内容]

### GitHub Project の更新
- [更新内容]
```

## エラーハンドリング

### GitHub 認証エラー

**原因**: 認証トークンの期限切れまたは未設定

**対処法**:
```bash
gh auth login
gh auth refresh -s project  # Project スコープ追加
```

### Issue が見つからない

**原因**: Issue 番号の誤り、削除済み

**対処法**:
- `gh issue list --state all` で確認
- 番号を再確認

### 類似性判定の曖昧さ

**原因**: 既存 Issue との類似度が中程度（40-70%）

**対処法**:
- AskUserQuestion でユーザーに確認
- 新規作成または既存 Issue への追加を選択

## 完了条件

このスキルは以下の条件を満たした場合に完了とする：

- [ ] 対象 Issue が特定されている
- [ ] 適切なモード/ワークフローが選択されている
- [ ] 必要な情報が収集されている
- [ ] Issue/project.md/GitHub Project が更新されている
- [ ] 結果レポートが出力されている

## 関連スキル

- **project-file**: project.md の作成・管理
- **workflow-expert**: ワークフロー設計・管理
- **agent-expert**: エージェント設計（skill タイプ実装時）
- **skill-expert**: スキル設計（skill タイプ実装時）

## 参考資料

- `CLAUDE.md`: プロジェクト全体のガイドライン
- `.claude/commands/issue.md`: /issue コマンド定義
- `.claude/commands/issue-implement.md`: /issue-implement コマンド定義
- `.claude/commands/issue-refine.md`: /issue-refine コマンド定義
- `.claude/commands/sync-issue.md`: /sync-issue コマンド定義
- `docs/github-projects-automation.md`: GitHub Projects 自動化

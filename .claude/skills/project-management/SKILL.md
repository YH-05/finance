---
name: project-management
description: |
  GitHub Project と project.md の作成・管理・同期を行うスキル。
  /new-project, /project-refine コマンドで使用。
  プロジェクト作成、整合性検証、ステータス同期時にプロアクティブに使用。
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, AskUserQuestion, TodoWrite
---

# Project Management

GitHub Project と project.md の管理機能を統合したナレッジベーススキルです。

## 目的

このスキルは以下を提供します：

- **プロジェクト作成**: GitHub Project と project.md の新規作成（パッケージ/軽量モード）
- **整合性検証**: GitHub Project、Issues、project.md 間の不整合検出と修正
- **ステータス同期**: Issue 完了状態と project.md の双方向同期
- **タスク管理**: タスク分解、依存関係管理、優先度設定

## いつ使用するか

### プロアクティブ使用（自動で使用を検討）

以下の状況では、ユーザーが明示的に要求しなくても使用を検討してください：

1. **新規プロジェクト開始時**
   - 「新しいプロジェクトを始めたい」
   - 「〜を開発したい」
   - パッケージ開発や軽量プロジェクトの立ち上げ

2. **プロジェクト状態の確認時**
   - 「プロジェクトの進捗を確認して」
   - 「Issue と project.md を同期して」
   - 複数 Issue の完了後

3. **整合性問題の検出時**
   - GitHub Issue と project.md のステータス不一致
   - 依存関係の循環検出
   - 優先度と依存関係の矛盾

### 明示的な使用（ユーザー要求）

- `/new-project` - プロジェクト作成
- `/project-refine` - 整合性検証と再構成
- 「project.md を更新して」などの直接的な要求

## 統合機能

このスキルは以下の機能を統合しています：

### /new-project コマンド

| モード | 用途 | 引数 |
|--------|------|------|
| **パッケージ開発** | LRD→設計→実装の正式フロー | `@src/<lib>/docs/project.md` |
| **軽量プロジェクト** | エージェント開発、ワークフロー改善等 | `"プロジェクト名"` or `--interactive` |

**パッケージ開発モードの流れ**:
```
project.md 読み込み → インタビュー → LRD作成 → 設計ドキュメント
    → タスク分解 → GitHub Project 登録
```

**軽量モードの流れ**:
```
インタビュー（10-12問） → 計画書作成 → GitHub Project 作成
    → Issue 登録 → 完了レポート
```

### /project-refine コマンド

プロジェクト全体の整合性を検証し、問題を修正します。

**チェック項目**:

| カテゴリ | チェック項目 | 重大度 |
|----------|--------------|--------|
| 依存関係 | 循環依存 | Critical |
| 依存関係 | 完了タスクへの未完了依存 | Warning |
| 優先度 | 高優先度が低優先度に依存 | Warning |
| ステータス | GitHub vs project.md 不整合 | Warning |
| 構造 | 孤立タスク | Info |
| 担当者 | 過負荷（3件以上 in_progress） | Info |

### project-status-sync 機能

GitHub Project の Issue 完了状態と project.md のタスクステータスを同期します。

**同期パターン**:

| ドキュメント | GitHub | 対処 |
|------------|--------|------|
| `- [ ]` (todo) | Done | → `- [x]` に更新 |
| `ステータス: todo` | Done | → `ステータス: done` に更新 |
| `ステータス: 計画中` | 全Done | → `ステータス: 完了` に更新 |

## プロセス

### 1. プロジェクト作成（/new-project）

#### パッケージ開発モード

1. **project.md 読み込み**: `@src/<lib>/docs/project.md` から基本情報取得
2. **インタビュー**: 最低5回の質問で要件詳細化
3. **LRD 作成**: `prd-writing` スキルを使用
4. **設計ドキュメント作成**: サブエージェントによる自動生成
5. **タスク分解**: `task-decomposer` による実装タスク分解
6. **GitHub Project 登録**: gh CLI で Issue 作成・Project 追加

#### 軽量プロジェクトモード

1. **インタビュー**: 10-12回の質問で要件収集
   - フェーズ1: 背景理解（質問1-3）
   - フェーズ2: 目標設定（質問4-6）
   - フェーズ3: スコープ定義（質問7-9）
   - フェーズ4: 技術詳細（質問10-12）
2. **計画書作成**: `docs/project/{slug}.md` に出力
3. **GitHub Project 作成**: `gh project create`
4. **Issue 登録**: タスクを Issue として作成、Project に追加

### 2. 整合性検証（/project-refine）

1. **データ収集**: GitHub Issues / Project / project.md を取得
2. **適合性チェック**: 循環依存、優先度矛盾、ステータス不整合を検出
3. **問題一覧表示**: 重大度別サマリー
4. **再構成提案**: 優先度調整、依存関係最適化の提案
5. **修正適用**: ユーザー確認後に GitHub / project.md を更新

### 3. ステータス同期

1. **対象プロジェクト特定**: docs/project/ のドキュメントを確認
2. **GitHub Project 状態取得**: `gh project item-list` で Issue ステータス取得
3. **ドキュメント比較**: タスクステータスの不整合を検出
4. **ドキュメント更新**: チェックボックス、ステータス、完了日を更新
5. **コミット・プッシュ**: 変更を Git にコミット

## 活用ツールの使用方法

### gh CLI（GitHub 操作）

```bash
# Project 作成
gh project create --title "{プロジェクト名}" --owner @me

# Project 一覧
gh project list --owner @me

# Project Item 一覧
gh project item-list {project_number} --owner @me --format json

# Project にアイテム追加
gh project item-add {project_number} --owner @me --url {issue_url}

# Project Item 編集（ステータス変更）
gh project item-edit --project-id {project_id} --id {item_id} \
  --field-id {status_field_id} --single-select-option-id {option_id}

# Project フィールド情報取得
gh project field-list {project_number} --owner @me --format json
```

### gh CLI（Issue 操作）

```bash
# Issue 一覧
gh issue list --state all --json number,title,body,labels,state,url

# Issue 作成（HEREDOC形式）
gh issue create \
  --title "[日本語タイトル]" \
  --body "$(cat <<'EOF'
## 概要
...
## 受け入れ条件
- [ ] ...
EOF
)" \
  --label "[ラベル]"

# Issue 編集
gh issue edit {number} --add-label "priority:high"
gh issue close {number}
gh issue reopen {number}
```

### 組み込みツール

| ツール | 用途 |
|--------|------|
| Read | project.md、Issue 本文の読み取り |
| Write | 新規 project.md の作成 |
| Edit | 既存 project.md のステータス更新 |
| Glob | docs/project/*.md の検索 |
| Grep | GitHub Project 番号の抽出 |

## リソース

このスキルには以下のリソースが含まれています：

### ./guide.md

GitHub Project と project.md 管理の詳細ガイド：

- GitHub Project 操作の詳細手順
- project.md 構造と更新ルール
- 整合性検証アルゴリズム
- トラブルシューティング

### ./template.md

project.md のテンプレート：

- パッケージ開発用テンプレート
- 軽量プロジェクト用テンプレート
- マイルストーン・機能の記述形式
- 優先度・受け入れ条件の記述形式

## 使用例

### 例1: 軽量プロジェクトの新規作成

**状況**: 新しいエージェント開発プロジェクトを開始したい

**処理**:
1. `/new-project "エージェント開発"` を実行
2. インタビューに回答（背景→目標→スコープ→技術詳細）
3. 計画書 `docs/project/agent-development.md` が作成される
4. GitHub Project が作成される
5. Issue が登録される

**期待される出力**:
```
軽量プロジェクトのセットアップが完了しました!

計画書:
- docs/project/agent-development.md

GitHub Project:
- 名前: エージェント開発
- URL: https://github.com/users/xxx/projects/XX

作成した Issue:
- [#123](URL): 要件定義
- [#124](URL): 設計
- [#125](URL): 実装
```

---

### 例2: プロジェクト整合性検証

**状況**: GitHub Project と project.md の状態が不一致になっている

**処理**:
1. `/project-refine @docs/project/my-project.md` を実行
2. 不整合を検出（循環依存1件、ステータス不整合3件）
3. 修正提案を確認
4. 「すべて自動修正」を選択
5. GitHub と project.md が同期される

**期待される出力**:
```
## 適合性チェック結果

### サマリー
| 重大度 | 件数 |
|--------|------|
| Critical | 1 |
| Warning | 3 |
| Info | 0 |

### 修正後
- 循環依存: 解消
- ステータス同期: 完了
- 健全性スコア: 62% → 95%
```

---

### 例3: Issue 完了後のステータス同期

**状況**: PR がマージされ、複数の Issue が完了した

**処理**:
1. GitHub Project の状態を確認
2. 完了した Issue に対応する project.md のタスクを特定
3. チェックボックスを `[x]` に更新
4. プロジェクトステータスを「完了」に更新（全 Issue 完了の場合）
5. 変更をコミット・プッシュ

**期待される出力**:
```
完了しました。以下を更新：
- my-project.md のタスク (#147-150) を done に更新
- プロジェクトステータスを「完了」に更新
- 完了日を追加
- コミット・プッシュ完了
```

---

### 例4: パッケージ開発プロジェクトの開始

**状況**: 新しい Python パッケージの開発を開始したい

**処理**:
1. `/new-package market_analysis` でパッケージ作成（事前に実行済み）
2. `/new-project @src/market_analysis/docs/project.md` を実行
3. インタビューで要件を詳細化
4. LRD を作成・承認
5. 設計ドキュメントを自動生成
6. タスクを分解し、GitHub Project に登録

**期待される出力**:
```
開発プロジェクトのセットアップが完了しました!

作成/更新したドキュメント:
- src/market_analysis/docs/library-requirements.md
- src/market_analysis/docs/functional-design.md
- src/market_analysis/docs/architecture.md
- src/market_analysis/docs/repository-structure.md
- src/market_analysis/docs/development-guidelines.md
- src/market_analysis/docs/glossary.md
- src/market_analysis/docs/tasks.md

プロジェクト管理:
- GitHub Project に登録済み
```

## 品質基準

### 必須（MUST）

- [ ] project.md は指定されたテンプレート形式に従う
- [ ] GitHub Project との同期が正常に動作する
- [ ] 整合性チェックで Critical エラーがない状態を維持
- [ ] Issue 作成時は HEREDOC 形式を使用（シェルエスケープ対策）
- [ ] プロジェクト名は検証ルールに従う（1-100文字、許可文字のみ）

### 推奨（SHOULD）

- 全タスクに受け入れ条件が定義されている
- 優先度（P0/P1/P2）が適切に設定されている
- 依存関係が明確に記述されている
- 定期的にステータス同期を実行

## 出力フォーマット

### プロジェクト作成完了時

```
================================================================================
                    プロジェクト作成完了
================================================================================

## プロジェクト情報
- 名前: {project_name}
- モード: {パッケージ開発 / 軽量プロジェクト}
- 計画書: {path_to_project_md}

## GitHub Project
- 番号: #{project_number}
- URL: {project_url}

## 作成した Issue
| # | タイトル | ラベル |
|---|---------|--------|
| {number} | {title} | {labels} |

## 次のステップ
1. 計画書の内容を確認
2. /issue-implement でタスクを実装
3. /project-refine で定期的に整合性確認

================================================================================
```

### 整合性検証結果

```
================================================================================
                    プロジェクト整合性検証結果
================================================================================

## サマリー
| 重大度 | 件数 | 説明 |
|--------|------|------|
| Critical | {n} | 即時対応必要 |
| Warning | {n} | 要確認 |
| Info | {n} | 推奨事項 |

## 健全性スコア
修正前: {before}% → 修正後: {after}%

## 適用した修正
- {修正内容1}
- {修正内容2}

================================================================================
```

## エラーハンドリング

### GitHub 認証エラー

**原因**: gh CLI が認証されていない

**対処法**:
```bash
gh auth login
```

### Project アクセス権限エラー

**原因**: Project 操作のスコープが不足

**対処法**:
```bash
gh auth refresh -s project
```

### project.md が見つからない

**原因**: 指定されたパスに project.md が存在しない

**対処法**:
- パッケージ開発の場合: `/new-package` を先に実行
- 軽量プロジェクトの場合: 引数なしで `/new-project` を実行

### 循環依存の検出

**原因**: タスク間の依存関係が循環している

**対処法**:
- `/project-refine` で自動検出・修正提案を取得
- 依存関係を見直し、循環を解消

## 完了条件

このスキルは以下の条件を満たした場合に完了とする：

- [ ] プロジェクト作成が正常に完了している
- [ ] GitHub Project が作成されている（軽量モード / パッケージ開発モード）
- [ ] project.md が作成・更新されている
- [ ] Issue が登録されている
- [ ] 整合性検証で Critical エラーがない

## 関連コマンド・スキル

- `/new-package`: パッケージディレクトリの作成（/new-project の前提）
- `/issue`: GitHub Issue と project.md の双方向同期
- `/sync-issue`: Issue コメントからの進捗・タスク同期
- `/plan-worktrees`: 並列開発計画（依存関係解析→Wave グルーピング）
- `/issue-implement`: Issue から PR 作成までの自動化
- `task-decomposer`: タスク分解と依存関係管理

## 参考資料

- `CLAUDE.md`: プロジェクト全体のガイドライン
- `docs/guidelines/github-projects-automation.md`: GitHub Projects 自動化の詳細
- `.claude/commands/new-project.md`: /new-project コマンドの詳細
- `.claude/commands/project-refine.md`: /project-refine コマンドの詳細

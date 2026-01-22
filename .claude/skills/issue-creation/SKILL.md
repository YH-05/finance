---
name: issue-creation
description: |
  GitHub Issue の作成とタスク分解を行うスキル。
  /issue コマンドで使用。
  クイック発行、パッケージ開発、軽量プロジェクトの3モードに対応。
allowed-tools: Bash, Read, Write, Glob, Grep, AskUserQuestion, Task
---

# Issue Creation

GitHub Issue の作成とタスク分解を行うナレッジベーススキルです。

## 目的

このスキルは以下を提供します：

- **クイック発行モード**: 自然言語から素早く Issue を作成
- **パッケージ開発モード**: project.md と連携したタスク管理
- **軽量プロジェクトモード**: GitHub Project との双方向同期
- **類似性判定**: 既存 Issue との重複チェック
- **タスク分解**: 大きな要件を実装可能なサイズに分割

## いつ使用するか

### プロアクティブ使用（自動で検討）

以下の状況では、ユーザーが明示的に要求しなくても使用を検討：

1. **Issue 作成の議論**
   - 「〜を追加したい」「〜が必要」
   - バグ報告、機能要望の発生
   - タスクの分解・整理が必要

2. **タスク管理**
   - project.md との整合性確認
   - GitHub Issues の同期

### 明示的な使用（ユーザー要求）

- `/issue` コマンドの実行時

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

### 2. 類似性判定基準

| 類似度 | 判定 | アクション |
|--------|------|-----------|
| 70%+ | 高 | 既存 Issue に Tasklist として追加 |
| 40-70% | 中 | ユーザーに確認 |
| 40%未満 | 低 | 新規 Issue 作成 |

## プロセス

### クイック発行モード（--add）

```
/issue --add <要件概要>
    │
    ├─ Q1: GitHub Project 選択
    │
    ├─ Q2: Issue の種類（新機能/改善/バグ/リファクタ）
    │
    ├─ Q3: 対象パッケージ（multiSelect）
    │
    ├─ Q4: 優先度
    │
    ├─ Q5: 追加の詳細
    │
    ├─ Issue プレビュー表示
    │
    └─ 確認 → 作成 / 修正 / キャンセル
```

### パッケージ開発モード

```
/issue @src/<library>/docs/project.md
    │
    ├─ ステップ 1: 現状把握
    │   ├─ gh issue list で既存 Issue 取得
    │   └─ project.md 読み込み
    │
    ├─ ステップ 2: 入力トリガー選択
    │   ├─ 自然言語で説明
    │   ├─ 外部ファイルから読み込み
    │   └─ 同期のみ
    │
    ├─ ステップ 3: 入力処理
    │   ├─ A: ヒアリング（概要、種類、詳細、条件、優先度）
    │   ├─ B: ファイルパース
    │   └─ C: スキップ
    │
    ├─ ステップ 4: task-decomposer 起動
    │   ├─ 類似性判定
    │   ├─ タスク分解
    │   └─ 双方向同期
    │
    └─ ステップ 5: 結果表示
```

### 軽量プロジェクトモード

パッケージ開発モード + GitHub Project 連携:

```
/issue @docs/project/<slug>.md
    │
    ├─ パッケージ開発モードの全処理を実行
    │
    └─ 追加処理
        ├─ project.md から Project 番号抽出
        ├─ gh project field-list → Status フィールド情報
        ├─ gh project item-list → Item 一覧
        └─ Issue 作成/更新時に Project Item も更新
```

## 活用ツールの使用方法

### gh CLI（GitHub 操作）

```bash
# Issue 一覧
gh issue list --state all --json number,title,body,labels,state,url --limit 100

# Issue 作成（日本語で記述）
gh issue create --title "[タイトル]" --body "[本文]" --label "[ラベル]"

# Issue 更新
gh issue edit [番号] --title "[新タイトル]" --body "[新本文]"

# GitHub Project に追加
gh project item-add {number} --owner @me --url {issue_url}
```

### サブエージェント連携

| エージェント | 用途 |
|--------------|------|
| task-decomposer | タスク分解、類似性判定、同期実行 |

## リソース

このスキルには以下のリソースが含まれています：

### ./guide.md

Issue 作成の詳細ガイド：

- クイック発行モードの詳細フロー
- パッケージ開発モードの詳細フロー
- 軽量プロジェクトモードの詳細フロー
- ラベル自動判定ルール
- project.md フォーマット

### ./template.md

Issue テンプレート：

- 標準 Issue テンプレート（新機能/バグ/リファクタ）
- 受け入れ条件テンプレート
- Tasklist テンプレート

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

### 例2: パッケージ開発モード

**状況**: market_analysis パッケージに新機能を追加したい

**処理**:
```bash
/issue @src/market_analysis/docs/project.md
```

1. GitHub Issues と project.md を読み込み
2. 自然言語で新機能を説明
3. task-decomposer でタスク分解
4. 新規 Issue を作成、project.md を更新

---

### 例3: 軽量プロジェクトモード

**状況**: GitHub Project と連携したプロジェクト管理

**処理**:
```bash
/issue @docs/project/research-agent.md
```

1. project.md から GitHub Project 番号を抽出
2. 既存 Issue と Project Item を取得
3. タスク分解と Issue 作成
4. GitHub Project ステータスも同期

## 品質基準

### 必須（MUST）

- [ ] Issue タイトル・本文は日本語で記述
- [ ] 受け入れ条件は測定可能な形式
- [ ] ラベルが適切に設定されている
- [ ] project.md と GitHub の整合性が保たれている

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
## 処理結果

### 作成した Issue
- [#123](URL): 機能 1.1 - ユーザー認証

### 更新した Issue
- [#100](URL): Tasklist に #123 を追加

### project.md の更新
- 機能 1.1: Issue #123 を紐付け

### 現在のタスク一覧
| 優先度 | タイトル | ステータス | Issue |
|--------|----------|------------|-------|
| high | 機能 1.1 | todo | [#123](URL) |
```

## エラーハンドリング

### GitHub 認証エラー

```bash
gh auth login
gh auth refresh -s project  # Project スコープ追加
```

### Issue が見つからない

- `gh issue list --state all` で確認
- 番号を再確認

### 類似性判定の曖昧さ

- AskUserQuestion でユーザーに確認
- 新規作成または既存 Issue への追加を選択

## 完了条件

このスキルは以下の条件を満たした場合に完了とする：

- [ ] 引数が正しく解析されている
- [ ] 適切なモードが選択されている
- [ ] GitHub Issues と project.md が読み込まれている
- [ ] task-decomposer が実行されている（必要な場合）
- [ ] Issue が作成/更新されている
- [ ] 結果レポートが出力されている

## 関連スキル

- **issue-implementation**: Issue の自動実装
- **issue-refinement**: Issue のブラッシュアップ
- **issue-sync**: コメントからの同期
- **project-file**: project.md の作成・管理

## 参考資料

- `CLAUDE.md`: プロジェクト全体のガイドライン
- `.claude/commands/issue.md`: /issue コマンド定義
- `docs/github-projects-automation.md`: GitHub Projects 自動化

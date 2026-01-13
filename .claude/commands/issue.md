---
description: GitHub Issue とタスクの管理・同期を行う
---

# /issue - Issue とタスク管理

> **役割の明確化**: このコマンドは **Issue 管理とタスク分解** に特化しています。
>
> - 開発キックオフ・設計ドキュメント作成 → `/new-project`
> - 品質チェック・自動修正 → `/ensure-quality`

**目的**: GitHub Issues と project.md の双方向同期、タスク分解、類似 Issue の判定

## コマンド構文

```bash
# パッケージ開発モード
/issue @src/<library_name>/docs/project.md

# 軽量プロジェクトモード
/issue @docs/project/<project-slug>.md
```

## 概要

1. GitHub Issues と project.md を読み込み、現状を把握
2. ユーザー入力または外部ファイルから新規タスクを収集
3. 既存 Issue との類似性を AI で判定
4. 類似あり → 既存 Issue に Tasklist として sub-issue を追加
5. 類似なし → 新規 Issue を作成
6. project.md と GitHub Issues を双方向同期
7. タスク一覧を表示して終了（実装は別途実行）

---

## ステップ 0: 引数解析とモード判定

1. `@` で指定されたパスを解析する
2. パス形式に応じてモードを判定:

### パターン A: パッケージ開発モード

- パターン: `@src/<library_name>/docs/project.md`
- 抽出: `<library_name>` を `src/` と `/docs/` の間から取得
- 例: `@src/market_analysis/docs/project.md` → `library_name = "market_analysis"`
- 設定: `mode = "package_mode"`

### パターン B: 軽量プロジェクトモード（新規）

- パターン: `@docs/project/<slug>.md`
- 抽出: `<slug>` をファイル名から取得（拡張子を除去）
- 例: `@docs/project/research-agent.md` → `slug = "research-agent"`
- 設定: `mode = "lightweight_mode"`
- **GitHub Project 番号の抽出**:
  1. project.md を読み込み
  2. `**GitHub Project**: [#N](URL)` 形式からプロジェクト番号 N を抽出
  3. 番号が見つからない場合は警告を表示し、Project なしで続行

**引数が不正な場合**:

```text
エラー: 引数の形式が正しくありません。

使用例:
- パッケージ開発: /issue @src/<library_name>/docs/project.md
- 軽量プロジェクト: /issue @docs/project/<project-slug>.md
```

---

## ステップ 1: 現状把握

### 1.1 GitHub Issues の取得

```bash
gh issue list --state all --json number,title,body,labels,state,url --limit 100
```

**認証エラーの場合**:

```text
エラー: GitHub 認証に失敗しました。

解決方法:
gh auth login
```

### 1.2 project.md の読み込み

1. 指定されたプロジェクトファイルの存在を確認
2. **ファイルが存在しない場合**:
   - **project-file スキル** をロードしてテンプレートから作成
   - AskUserQuestion でパッケージの概要をヒアリング

3. project.md を読み込み、既存タスクを抽出

### 1.3 対応関係の確認

- project.md の `Issue: [#番号](URL)` から Issue 番号を抽出
- GitHub Issues とのマッチングを確認
- 不整合があれば警告を表示

### 1.4 GitHub Project 情報の取得（軽量プロジェクトモードのみ）

ステップ 0 でプロジェクト番号が取得できた場合、以下を実行:

#### 1.4.1 Project フィールド情報の取得

```bash
gh project field-list {project_number} --owner @me --format json
```

**取得する情報**:
- Status フィールド ID
- ステータスオプション（Todo, In Progress, Done など）の ID

#### 1.4.2 Project Item 一覧の取得

```bash
gh project item-list {project_number} --owner @me --format json
```

**取得する情報**:
- 各 Item の ID
- 紐付けられた Issue URL
- 現在のステータス

#### 1.4.3 Issue と Project Item の対応表作成

- Issue 番号 → Item ID のマッピングを作成
- 現在のステータス値を保持

**認証スコープ不足の場合**:

```text
警告: GitHub Project へのアクセス権限がありません。

解決方法:
gh auth refresh -s project

Project 同期なしで Issue 管理のみ実行します。
```

---

## ステップ 2: 入力トリガー選択

AskUserQuestion ツールで入力方法を選択:

```yaml
questions:
  - question: "どのように Issue を追加しますか？"
    header: "入力方法"
    options:
      - label: "自然言語で説明"
        description: "機能や要件を自由に説明します"
      - label: "外部ファイルから読み込み"
        description: "md/yaml/json ファイルから要件を抽出"
      - label: "同期のみ"
        description: "新規追加せず GitHub と project.md を同期"
```

---

## ステップ 3: 入力に応じた処理

### パターン A: 自然言語で説明（構造化ヒアリング）

5回のヒアリングを実施:

#### 質問 1: 機能の概要

```yaml
question: "どのような機能を追加しますか？"
header: "概要"
options: なし（自由記述）
```

#### 質問 2: 機能の種類

```yaml
question: "この機能はどのカテゴリですか？"
header: "種類"
options:
  - label: "新機能の追加"
    description: "これまでなかった機能を追加"
  - label: "既存機能の改善"
    description: "既存機能の拡張・強化"
  - label: "バグ修正"
    description: "不具合の修正"
  - label: "リファクタリング"
    description: "動作を変えずにコードを改善"
```

#### 質問 3: 具体的な振る舞い

```yaml
question: "期待する動作を具体的に教えてください"
header: "詳細"
options: なし（自由記述）
```

#### 質問 4: 受け入れ条件

```yaml
question: "完了と判断する条件は？"
header: "受け入れ条件"
multiSelect: true
options:
  - label: "ユニットテストが通る"
    description: "pytest tests/unit/ が成功"
  - label: "統合テストが通る"
    description: "pytest tests/integration/ が成功"
  - label: "ドキュメントが更新されている"
    description: "関連ドキュメントの更新を含む"
  - label: "make check-all が成功する"
    description: "format, lint, typecheck, test 全て成功"
```

#### 質問 5: 優先度

```yaml
question: "この機能の優先度は？"
header: "優先度"
options:
  - label: "high"
    description: "すぐに必要"
  - label: "medium"
    description: "次のリリースまでに"
  - label: "low"
    description: "将来的に"
```

### パターン B: 外部ファイルから読み込み

1. AskUserQuestion でファイルパスを取得
2. Read ツールでファイル内容を取得
3. ファイル形式に応じてパース:
   - `.md`: マークダウンから要件を抽出
   - `.yaml` / `.yml`: YAML をパース
   - `.json`: JSON をパース
4. 複数の機能が含まれる場合は個別にタスク化

### パターン C: 同期のみ

ステップ 3 をスキップし、ステップ 4 に進む（mode = "sync"）

---

## ステップ 4: task-decomposer エージェント起動

Task ツールを使用して **task-decomposer** サブエージェントを起動:

```yaml
subagent_type: "task-decomposer"
description: "Task decomposition and issue sync"
prompt: |
  タスク分解と Issue 同期を実行してください。

  ## 実行モード
  [package_mode / lightweight_mode]

  ## ライブラリ名 / プロジェクト名
  [library_name または slug]

  ## project.md パス
  [project.md のパス]

  ## GitHub Issues（JSON）
  [gh issue list の結果]

  ## GitHub Project 情報（軽量プロジェクトモードのみ）
  - Project 番号: {project_number}
  - Project ID: {project_id}（gh project view で取得）
  - Status フィールド ID: {status_field_id}
  - ステータスオプション:
    - Todo: {todo_option_id}
    - In Progress: {in_progress_option_id}
    - Done: {done_option_id}
  - Project Items: [item_list の結果]

  ## ユーザー入力
  [ヒアリング結果またはファイル内容]

  ## 入力モード
  [new / external / sync]
```

**パッケージ開発モードの場合**: GitHub Project 情報セクションは省略される。

### task-decomposer の処理

1. **類似性判定**: 新規タスクと既存 Issue を AI で比較
   - 高類似度（70%以上）: 既存 Issue に Tasklist として追加
   - 中類似度（40-70%）: ユーザーに確認
   - 低類似度（40%未満）: 新規 Issue 作成

2. **タスク分解**: 大きな要件を実装可能なサイズに分解

3. **依存関係計算**: タスク間の依存関係を分析
   - `depends_on`: 先行タスク
   - `blocks`: 後続タスク
   - 循環依存の検出と警告

4. **双方向同期**:
   - GitHub → project.md: 新規 Issue を追加
   - project.md → GitHub: Issue 未作成のタスクを作成
   - チェックボックス状態を同期

### GitHub Issue 操作

**Issue のタイトルと本文は日本語で記述すること。**

```bash
# 新規 Issue 作成（日本語で記述）
gh issue create \
  --title "[日本語タイトル]" \
  --body "[日本語本文]" \
  --label "[ラベル]"

# Issue 更新（Tasklist 追加）
gh issue edit [番号] --body "[更新本文（日本語）]"

# ラベル更新
gh issue edit [番号] --add-label "[ラベル]"
```

### Issue テンプレート

```markdown
## 概要
[機能・問題の概要を日本語で記述]

## 詳細
[詳細な説明]

## 受け入れ条件
- [ ] [条件1]
- [ ] [条件2]

## 備考
[補足情報があれば記載]
```

### ラベル自動判定

| 入力キーワード | ラベル |
|----------------|--------|
| 新機能、追加 | `enhancement` |
| バグ、修正 | `bug` |
| リファクタ | `refactor` |
| ドキュメント | `documentation` |
| テスト | `test` |
| 優先度: high | `priority:high` |
| 優先度: medium | `priority:medium` |
| 優先度: low | `priority:low` |

---

## ステップ 5: 結果表示

処理結果を表示:

```markdown
## 処理結果

### 作成した Issue
- [#123](URL): 機能 1.1 - ユーザー認証
- [#124](URL): 機能 1.2 - セッション管理

### 更新した Issue
- [#100](URL): Tasklist に #123 を追加
- [#101](URL): チェックボックス状態を同期

### project.md の更新
- 機能 1.1: Issue #123 を紐付け
- 機能 1.2: Issue #124 を紐付け

### 現在のタスク一覧

| 優先度 | タイトル | ステータス | Issue |
|--------|----------|------------|-------|
| high | 機能 1.1 | todo | [#123](URL) |
| medium | 機能 1.2 | in_progress | [#124](URL) |
| low | 機能 1.3 | done | [#125](URL) |

### 依存関係
- #124 depends_on #123
- #125 depends_on #124

## 次のステップ

タスクの実装を開始するには:

1. Issue の「実装タスク」セクションのチェックボックスを確認
2. タスクを実装し、完了したら `gh issue edit` でチェックボックスを更新
3. `/ensure-quality` で品質チェック
4. `/commit-and-pr` で PR を作成

### 進捗管理

Issue のチェックボックスで進捗を管理します:

```bash
# Issue の本文を更新してチェックボックスを完了に
gh issue edit 123 --body "$(gh issue view 123 --json body -q .body | sed 's/- \[ \] タスク1/- [x] タスク1/')"
```
```

---

## project.md フォーマット

### 期待するフォーマット

```markdown
### マイルストーン 1: 基本機能

#### 機能 1.1: [機能名]
- Issue: [#123](https://github.com/owner/repo/issues/123)
- 優先度: high | medium | low
- ステータス: todo | in_progress | done
- 依存関係:
  - depends_on: [#120](https://github.com/owner/repo/issues/120)
  - blocks: [#125](https://github.com/owner/repo/issues/125)
- 説明: [詳細説明]
- 受け入れ条件:
  - [ ] [測定可能な条件1]
  - [x] [完了した条件]
```

### 同期ルール

| 項目 | ルール |
|------|--------|
| タイトル | project.md を正とする |
| チェックボックス | 双方向マージ（どちらかが[x]なら[x]）|
| ステータス | closed 優先（完了状態は変更しない）|
| 優先度 | project.md を正とする |

---

## エラーハンドリング

| ケース | 対処 |
|--------|------|
| GitHub 認証エラー | `gh auth login` を案内 |
| Issue 作成権限なし | 権限不足を通知 |
| project.md 構文エラー | パースエラー箇所を特定 |
| 類似性判定の曖昧さ | ユーザーに確認を求める |
| 依存関係の循環 | 検出して警告、修正を促す |
| 削除された Issue の参照 | 警告を出して参照を削除 |

---

## 完了条件

このワークフローは、以下の全ての条件を満たした時点で完了:

- ステップ 0: 引数が正しく解析されている
- ステップ 1: GitHub Issues と project.md が読み込まれている
- ステップ 2: 入力方法が選択されている
- ステップ 3: ユーザー入力が収集されている（同期のみの場合はスキップ）
- ステップ 4: task-decomposer が実行され、同期が完了している
- ステップ 5: 結果が表示されている

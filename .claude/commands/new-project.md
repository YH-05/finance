---
description: プロジェクトファイルから開発を開始。LRD・設計ドキュメント作成とタスク分解を行う
---

# プロジェクトファイルからの開発キックオフ

このコマンドは、`/new-package` で作成されたパッケージの開発プロジェクトを開始します。
GitHub Project をメインとし、マークダウン形式でリポジトリ内でプロジェクト管理を行います。

**繰り返し実行可能**: プロジェクトファイルを更新するたびに実行してください。

## 実行方法

**引数:** `@src/<library_name>/docs/project.md`（必須）

```bash
claude
> /new-project @src/<library_name>/docs/project.md
```

## `/new-package` との関係

| コマンド         | 目的                                 | 実行順序   |
| ---------------- | ------------------------------------ | ---------- |
| `/new-package`   | パッケージディレクトリの作成         | **1. 先** |
| `/new-project`   | 開発プロジェクトの開始（設計・タスク分解） | **2. 後** |

## 開発サイクルフロー

1. `/new-package <package_name>` でパッケージを作成（project.md テンプレート含む）
2. （任意）project.md を編集して概要を記入
3. `/new-project @src/<library_name>/docs/project.md` 実行
4. インタビュー（最低 5 回の質問）で要件を詳細化 → **project.md を更新**
5. LRD 作成/更新 --> ユーザー承認（必須）
6. 設計ドキュメント作成/更新（サブエージェントによる自動実行）
7. **タスク分解**（task-decomposer による実装タスクの分解）
8. GitHub Project 連携 or ローカルタスクファイル作成
9. `/issue @src/<library_name>/docs/project.md` で Issue 管理、feature-implementer で実装開始

### サブエージェント実行フロー

```
ステップ 0: 引数検証・project.md 読み込み
    ↓
ステップ 1-1: インタビュー → project.md 更新
    ↓
ステップ 1-2: LRD 作成・承認（メインエージェント）
    ↓
ステップ 2: functional-design-writer（逐次）
    ↓
ステップ 3: architecture-design-writer（逐次）
    ↓
ステップ 4: repository-structure-writer（逐次）
    ↓
ステップ 5: development-guidelines-writer（逐次）
    ↓
ステップ 6: glossary-writer（逐次）
    ↓
ステップ 7: task-decomposer（タスク分解）
```

**注意**: 全ステップは依存関係があるため逐次実行が必須。

## 手順

### ステップ 0: 引数検証とインプットの読み込み

1. 引数がない場合、エラーメッセージを表示して終了:

```
エラー: プロジェクトファイルのパスを引数で指定してください。

使用例: /new-project @src/<library_name>/docs/project.md

1. まず /new-package <package_name> でパッケージを作成
2. /new-project @src/<library_name>/docs/project.md を実行
```

2. `@` で指定されたパスを解析する
3. パスから `<library_name>` を抽出する（`src/` と `/docs/` の間の部分）
4. **プロジェクトファイルの存在を確認**:
   - **存在しない場合**: エラーメッセージを表示して終了:
     ```
     エラー: project.md が見つかりません。

     先に /new-package <package_name> を実行してパッケージを作成してください。
     ```
   - **存在する場合**: 内容を読み込み、ステップ 1-1 に進む

---

### ステップ 1-1: インタビューによる要件収集

プロジェクトファイルの内容を元に、AskUserQuestion ツールを使用してユーザーにインタビューを行う。

**最低 5 回の質問を必須とする。** 以下のカテゴリから質問を選択:

1. **機能要件の詳細化**

    - 具体的な使用例は？
    - 入力/出力の形式は？
    - エッジケースの扱いは？

2. **技術的実装**

    - 使用したい技術スタック/ライブラリは？
    - 既存コードとの統合方法は？
    - パフォーマンス要件は？

3. **API 設計**

    - 公開インターフェースの形式は？
    - エラー時の挙動は？
    - 戻り値の形式は？

4. **スコープと優先度**

    - MVI（最小実装）の範囲は？
    - 将来的な拡張予定は？
    - 優先度の高い機能は？

5. **懸念点とトレードオフ**

    - 技術的な懸念点は？
    - 互換性の考慮事項は？
    - 既知の制約や制限は？

6. **テストと品質**
    - テスト戦略は？
    - 成功の定義は？
    - 品質基準は？

**インタビューのルール:**

-   1 回の質問で 2〜4 個のオプションを提示
-   プロジェクトファイルの内容に基づいて質問をカスタマイズ
-   回答に応じて次の質問を調整（アダプティブ）
-   最低 5 回、必要に応じてさらに質問を追加

**インタビュー完了後:**

インタビュー結果を元に `src/<library_name>/docs/project.md` を更新する:
- 概要セクションを具体化
- 主要機能を詳細化
- 技術的考慮事項を追記
- 成功基準を明確化

### ステップ 1-2: LRD の作成/更新

1. **prd-writing スキル**をロード
2. プロジェクトファイル + インタビュー結果を元に`src/<library_name>/docs/library-requirements.md`を作成/更新
3. アイデアを具体化：
    - 詳細な使用例
    - 受け入れ条件
    - 非機能要件
    - 成功指標
4. ユーザーに確認を求め、**承認されるまで待機**

**重要: LRD の承認なしに次のステップには進まない**

### ステップ 2: 機能設計書の作成/更新

Task tool を使用して **functional-design-writer** サブエージェントを起動:

```yaml
subagent_type: "functional-design-writer"
description: "Create functional design document"
prompt: |
    機能設計書を作成/更新してください。

    ## ライブラリ名
    <library_name>

    ## 入力
    - LRD: src/<library_name>/docs/library-requirements.md（承認済み）

    ## 参照
    - スキル: .claude/skills/functional-design/
    - 既存設計書（あれば）: src/<library_name>/docs/functional-design.md

    ## 出力
    - src/<library_name>/docs/functional-design.md
```

**完了条件**: `src/<library_name>/docs/functional-design.md` が作成/更新されていること

### ステップ 3: アーキテクチャ設計書の作成/更新

Task tool を使用して **architecture-design-writer** サブエージェントを起動:

```yaml
subagent_type: "architecture-design-writer"
description: "Create architecture design document"
prompt: |
    アーキテクチャ設計書を作成/更新してください。

    ## ライブラリ名
    <library_name>

    ## 入力
    - LRD: src/<library_name>/docs/library-requirements.md
    - 機能設計書: src/<library_name>/docs/functional-design.md

    ## 参照
    - スキル: .claude/skills/architecture-design/
    - 既存設計書（あれば）: src/<library_name>/docs/architecture.md

    ## 出力
    - src/<library_name>/docs/architecture.md
```

**完了条件**: `src/<library_name>/docs/architecture.md` が作成/更新されていること

### ステップ 4: リポジトリ構造定義書の作成/更新

Task tool を使用して **repository-structure-writer** サブエージェントを起動:

```yaml
subagent_type: "repository-structure-writer"
description: "Create repository structure document"
prompt: |
    リポジトリ構造定義書を作成/更新してください。

    ## ライブラリ名
    <library_name>

    ## 入力
    - LRD: src/<library_name>/docs/library-requirements.md
    - 機能設計書: src/<library_name>/docs/functional-design.md
    - アーキテクチャ設計書: src/<library_name>/docs/architecture.md

    ## 参照
    - スキル: .claude/skills/repository-structure/
    - 既存定義書（あれば）: src/<library_name>/docs/repository-structure.md

    ## 出力
    - src/<library_name>/docs/repository-structure.md
```

**完了条件**: `src/<library_name>/docs/repository-structure.md` が作成/更新されていること

### ステップ 5-6: 開発ガイドラインと用語集の作成/更新（逐次実行）

ステップ 5 と 6 は依存関係があるため、**逐次で実行**してください。
（glossary-writer は development-guidelines.md を入力として参照）

#### ステップ 5: 開発ガイドラインの作成/更新

Task tool を使用して **development-guidelines-writer** サブエージェントを起動:

```yaml
subagent_type: "development-guidelines-writer"
description: "Create development guidelines"
prompt: |
    開発ガイドラインを作成/更新してください。

    ## ライブラリ名
    <library_name>

    ## 入力
    - アーキテクチャ設計書: src/<library_name>/docs/architecture.md
    - リポジトリ構造定義書: src/<library_name>/docs/repository-structure.md

    ## 参照
    - スキル: .claude/skills/development-guidelines/
    - 既存ガイドライン（あれば）: src/<library_name>/docs/development-guidelines.md
    - コーディング規約: docs/coding-standards.md
    - 開発プロセス: docs/development-process.md

    ## 出力
    - src/<library_name>/docs/development-guidelines.md
```

#### ステップ 6: 用語集の作成/更新

Task tool を使用して **glossary-writer** サブエージェントを起動:

```yaml
subagent_type: "glossary-writer"
description: "Create glossary"
prompt: |
    用語集を作成/更新してください。

    ## ライブラリ名
    <library_name>

    ## 入力
    - 全ドキュメント:
      - src/<library_name>/docs/library-requirements.md
      - src/<library_name>/docs/functional-design.md
      - src/<library_name>/docs/architecture.md
      - src/<library_name>/docs/repository-structure.md
      - src/<library_name>/docs/development-guidelines.md

    ## 参照
    - スキル: .claude/skills/glossary-creation/
    - 既存用語集（あれば）: src/<library_name>/docs/glossary.md

    ## 出力
    - src/<library_name>/docs/glossary.md
```

**完了条件**: 両方のドキュメントが作成/更新されていること

### ステップ 7: タスク分解（task-decomposer）

Task tool を使用して **task-decomposer** サブエージェントを起動:

```yaml
subagent_type: "task-decomposer"
description: "Decompose requirements into implementation tasks"
prompt: |
    要件定義から実装タスクを分解してください。

    ## ライブラリ名
    <library_name>

    ## 入力
    - LRD: src/<library_name>/docs/library-requirements.md
    - 機能設計書: src/<library_name>/docs/functional-design.md
    - アーキテクチャ設計書: src/<library_name>/docs/architecture.md
    - リポジトリ構造: src/<library_name>/docs/repository-structure.md

    ## 出力
    - src/<library_name>/docs/tasks.md（実装タスク一覧）

    ## タスク分解の要件
    - 各タスクは一意に実装が再現可能な粒度
    - 依存関係を明確化
    - 実装順序を定義
    - 各タスクに受け入れ条件を記載
```

**完了条件**: `src/<library_name>/docs/tasks.md` が作成されていること

### ステップ 8: プロジェクト管理方式の選択

AskUserQuestion ツールを使用してプロジェクト管理方式を選択:

```yaml
question: "プロジェクト管理方式を選択してください"
options:
    - label: "GitHub Project に登録（推奨）"
      description: "gh CLI を使用してタスクを GitHub Project に Issue として登録"
    - label: "ローカルファイルのみ"
      description: "tasks.md をローカルで管理。後から GitHub に移行可能"
```

**選択肢 1（GitHub Project）の場合**:

1. `gh project list` で既存プロジェクトを確認
2. 新規プロジェクト作成 or 既存プロジェクトを選択
3. tasks.md の各タスクを Issue として作成
4. Project に Issue を追加

**選択肢 2（ローカル）の場合**:
tasks.md をそのまま使用

### ステップ 9: 次のアクション選択

AskUserQuestion ツールを使用して次のステップを確認:

```yaml
question: "次のステップを選択してください"
options:
    - label: "実装を開始（推奨）"
      description: "/issue でタスク管理、feature-implementer で実装を開始"
    - label: "設計レビューを行う"
      description: "設計ドキュメントを確認してから実装"
```

## 完了条件

-   LRD がユーザーに承認されていること
-   6 つのライブラリドキュメントが全て作成/更新されていること
-   tasks.md が作成されていること
-   プロジェクト管理方式が選択されていること

完了時のメッセージ:

```text
「開発プロジェクトのセットアップが完了しました!

作成/更新したドキュメント:
- src/<library_name>/docs/library-requirements.md
- src/<library_name>/docs/functional-design.md
- src/<library_name>/docs/architecture.md
- src/<library_name>/docs/repository-structure.md
- src/<library_name>/docs/development-guidelines.md
- src/<library_name>/docs/glossary.md
- src/<library_name>/docs/tasks.md

プロジェクト管理:
- [GitHub Project に登録済み / ローカルファイルで管理]

次のステップ:
- /issue @src/<library_name>/docs/project.md で Issue 管理
- feature-implementer で TDD ベースの実装を開始

- ドキュメントの編集が必要な場合は会話で依頼してください
  例: 「LRDに新機能を追加して」「architecture.mdを見直して」
」
```

---
description: 開発プロジェクトを開始。パッケージ開発または軽量プロジェクトに対応
---

# プロジェクト開始コマンド

このコマンドは2つのモードで動作します:

| モード | 用途 | 引数 |
|--------|------|------|
| **パッケージ開発** | LRD→設計→実装の正式フロー | `@src/<lib>/docs/project.md` |
| **軽量プロジェクト** | エージェント開発、ワークフロー改善等 | `"プロジェクト名"` or `--interactive` |

## 実行方法

```bash
# モード1: パッケージ開発（設計ドキュメント付き）
/new-project @src/<library_name>/docs/project.md

# モード2: 軽量プロジェクト（GitHub Project中心）
/new-project "プロジェクト名または説明"
/new-project --interactive
```

---

## ステップ 0: 引数解析とモード判定

引数を解析してモードを判定する:

```
引数の形式を確認:
├─ 引数なし → エラー表示
├─ @src/.../docs/project.md 形式 → パッケージ開発モード（従来）
├─ --interactive → 軽量モード（対話的に名前を決定）
└─ その他の文字列 → 軽量モード（引数をプロジェクト名として使用）
```

**引数がない場合のエラーメッセージ:**

```
エラー: 引数を指定してください。

使用例:
- パッケージ開発: /new-project @src/<library_name>/docs/project.md
- 軽量プロジェクト: /new-project "プロジェクト名"
- 対話的に作成: /new-project --interactive
```

**モード判定後:**
- パッケージ開発モード → [パッケージ開発モード](#パッケージ開発モード)へ進む
- 軽量モード → [軽量プロジェクトモード](#軽量プロジェクトモード)へ進む

---

# 軽量プロジェクトモード

エージェント開発、ワークフロー改善、一般的なタスク管理に適したモード。
GitHub Project を中心としたプロジェクト管理を行う。

## 軽量モード: ステップ 1 - インタビュー

10-12回の質問で一意な実装を導く。回答に応じて質問を分岐させる。

### フェーズ1: 背景理解（質問1-3）

**質問1: プロジェクトの背景**

```yaml
question: "このプロジェクトが必要になった背景は？"
header: "背景"
options:
  - label: "現状の課題がある"
    description: "既存の仕組みに問題や非効率がある"
  - label: "新しいニーズが発生"
    description: "これまでなかった要件が出てきた"
  - label: "技術的負債の解消"
    description: "古いコードや設計の改善が必要"
  - label: "外部要因への対応"
    description: "ライブラリ更新、API変更、規制対応など"
```

**質問2: 課題の種類**（質問1の回答に応じて分岐）

質問1が「現状の課題がある」の場合:
```yaml
question: "どのような種類の課題ですか？"
header: "課題種別"
options:
  - label: "機能が不足している"
    description: "必要な機能がない、または不十分"
  - label: "パフォーマンスが悪い"
    description: "処理速度、メモリ使用量などの問題"
  - label: "使いにくい"
    description: "UI/UX、API設計の問題"
  - label: "エラーが発生する"
    description: "バグ、例外、データ不整合"
```

質問1が「新しいニーズが発生」の場合:
```yaml
question: "どのようなニーズですか？"
header: "ニーズ種別"
options:
  - label: "新機能の追加"
    description: "これまでなかった機能が必要"
  - label: "既存機能の拡張"
    description: "既存機能に新しい能力を追加"
  - label: "統合・連携"
    description: "他システムとの連携が必要"
  - label: "自動化"
    description: "手動プロセスの自動化"
```

質問1が「技術的負債の解消」の場合:
```yaml
question: "どのような技術的負債ですか？"
header: "負債種別"
options:
  - label: "コード品質の問題"
    description: "読みにくい、テストがない、重複が多い"
  - label: "設計の問題"
    description: "拡張しにくい、依存関係が複雑"
  - label: "古い技術"
    description: "非推奨のライブラリ、古いパターン"
  - label: "ドキュメント不足"
    description: "仕様が不明確、ドキュメントがない"
```

質問1が「外部要因への対応」の場合:
```yaml
question: "どのような外部要因ですか？"
header: "要因種別"
options:
  - label: "ライブラリ・依存関係の更新"
    description: "破壊的変更、セキュリティパッチ"
  - label: "API・仕様変更"
    description: "外部APIの変更、規格の更新"
  - label: "インフラ・環境変更"
    description: "サーバ、CI/CD、ランタイムの変更"
  - label: "規制・コンプライアンス"
    description: "法規制、セキュリティ基準への対応"
```

**質問3: 背景の詳細**（自由記述）

```yaml
question: "具体的な状況を教えてください（例: どの処理で何が問題か、何を実現したいか）"
header: "詳細"
# 自由記述を受け付ける
```

### フェーズ2: 目標設定（質問4-6）

**質問4: 達成したい目標**

```yaml
question: "このプロジェクトで達成したいことは？"
header: "目標"
options:
  - label: "新機能を追加する"
    description: "新しいエージェント、コマンド、ワークフローなど"
  - label: "既存機能を改善する"
    description: "パフォーマンス、使いやすさ、信頼性の向上"
  - label: "問題を修正する"
    description: "バグ修正、エラー対応、データ不整合の解消"
  - label: "開発体験を向上する"
    description: "CI/CD改善、テスト追加、ドキュメント整備"
```

**質問5: 成果物種別**（質問4の回答に応じて分岐）

質問4が「新機能を追加する」の場合:
```yaml
question: "どの種類の成果物を作成しますか？"
header: "成果物種別"
options:
  - label: "エージェント"
    description: ".claude/agents/ に追加"
  - label: "コマンド"
    description: ".claude/commands/ に追加"
  - label: "スキル"
    description: ".claude/skills/ に追加"
  - label: "Pythonモジュール"
    description: "src/ 配下に追加"
```

質問4が「既存機能を改善する」の場合:
```yaml
question: "どのような改善を行いますか？"
header: "改善種別"
options:
  - label: "パフォーマンス改善"
    description: "速度、メモリ使用量の最適化"
  - label: "使いやすさ改善"
    description: "API設計、エラーメッセージの改善"
  - label: "信頼性向上"
    description: "エラーハンドリング、リトライ機構"
  - label: "保守性向上"
    description: "リファクタリング、テスト追加"
```

質問4が「問題を修正する」の場合:
```yaml
question: "どのような問題を修正しますか？"
header: "修正対象"
options:
  - label: "機能的なバグ"
    description: "期待通り動作しない"
  - label: "パフォーマンスの問題"
    description: "遅い、メモリリーク"
  - label: "データの問題"
    description: "不整合、破損、欠損"
  - label: "セキュリティの問題"
    description: "脆弱性、認証・認可の問題"
```

質問4が「開発体験を向上する」の場合:
```yaml
question: "どの開発体験を向上しますか？"
header: "DX改善"
options:
  - label: "CI/CD改善"
    description: "ビルド、テスト、デプロイの自動化"
  - label: "テスト改善"
    description: "テストカバレッジ、テスト速度"
  - label: "ドキュメント整備"
    description: "README、API仕様、ガイドライン"
  - label: "ツール整備"
    description: "リンター、フォーマッター、開発ツール"
```

**質問6: 成功基準**（複数選択）

```yaml
question: "成功と言える条件は？（複数選択可）"
header: "成功基準"
multiSelect: true
options:
  - label: "特定の入力に対して期待する出力が得られる"
    description: "機能要件を満たす"
  - label: "既存の問題が解決する"
    description: "エラーが発生しなくなる等"
  - label: "make check-all が成功する"
    description: "品質基準を満たす"
  - label: "ドキュメントが整備される"
    description: "使い方が明確になる"
```

### フェーズ3: スコープ定義（質問7-9）

**質問7: 変更範囲**

```yaml
question: "変更が及ぶ範囲は？"
header: "範囲"
options:
  - label: "新規ファイルのみ"
    description: "既存コードは変更しない"
  - label: "既存ファイルの修正のみ"
    description: "新規ファイルは作成しない"
  - label: "新規 + 既存の両方"
    description: "新規作成と既存修正の両方が必要"
```

**質問8: 影響ディレクトリ**（複数選択）

```yaml
question: "どのディレクトリに影響しますか？"
header: "ディレクトリ"
multiSelect: true
options:
  - label: ".claude/"
    description: "エージェント、コマンド、スキル"
  - label: "src/"
    description: "Pythonパッケージ"
  - label: "tests/"
    description: "テストコード"
  - label: "docs/"
    description: "ドキュメント"
```

**質問9: スコープ外**（複数選択）

```yaml
question: "このプロジェクトで対応しないことは？"
header: "スコープ外"
multiSelect: true
options:
  - label: "他のパッケージへの影響"
    description: "変更は対象ディレクトリに限定"
  - label: "後方互換性の維持"
    description: "破壊的変更を許容"
  - label: "パフォーマンス最適化"
    description: "まずは動作することを優先"
  - label: "ドキュメント更新"
    description: "コード変更のみ"
```

### フェーズ4: 技術詳細（質問10-12）

**質問10: 実装アプローチ**

```yaml
question: "どのような実装アプローチを取りますか？"
header: "アプローチ"
options:
  - label: "既存パターンに従う"
    description: "リポジトリ内の類似実装を参考に"
  - label: "テンプレートを使用"
    description: "template/ のテンプレートを使用"
  - label: "新しいパターンを導入"
    description: "新しい設計パターンやライブラリを使用"
```

**質問11: 依存関係**（複数選択）

```yaml
question: "このプロジェクトが依存する既存機能は？"
header: "依存"
multiSelect: true
options:
  - label: "finance.utils.logging_config"
    description: "ロギング機能"
  - label: "finance.db"
    description: "データベースクライアント"
  - label: "既存のエージェント/コマンド"
    description: "他のエージェントやコマンドを呼び出す"
  - label: "外部API"
    description: "yfinance, FRED等"
```

**質問12: テスト要件**（複数選択）

```yaml
question: "必要なテストの種類は？"
header: "テスト"
multiSelect: true
options:
  - label: "ユニットテスト"
    description: "個別関数/クラスのテスト"
  - label: "統合テスト"
    description: "複数コンポーネントの連携テスト"
  - label: "プロパティテスト"
    description: "Hypothesisによるプロパティベーステスト"
  - label: "手動テストのみ"
    description: "自動テストは後で追加"
```

---

## 軽量モード: ステップ 2 - 計画書作成

インタビュー結果を元に計画書を作成する。

### プロジェクト名のスラッグ化

プロジェクト名から URL セーフなスラッグを生成:
- 英語のケバブケース（小文字、ハイフン区切り）
- 30文字以内
- 日本語は英語に変換

例:
- "記事執筆ワークフローの改善" → `article-workflow-improvement`
- "エージェントのエラーハンドリング" → `agent-error-handling`
- "新しいデータソース追加" → `new-data-source`

### 計画書テンプレート

出力先: `docs/project/{slug}.md`

```markdown
# {プロジェクト名}

**作成日**: {今日の日付}
**ステータス**: 計画中
**GitHub Project**: （ステップ3で追記）

## 背景と目的

### 背景

{質問1-3の回答から生成}
- 背景の種類: {質問1の回答}
- 詳細: {質問2の回答}
- 具体的な状況: {質問3の回答}

### 目的

{質問4の回答から生成}

## スコープ

### 含むもの

{質問7-8の回答から生成}
- 変更範囲: {質問7の回答}
- 影響ディレクトリ: {質問8の回答}

### 含まないもの

{質問9の回答から生成}

## 成果物

| 種類 | 名前 | 説明 |
| ---- | ---- | ---- |
| {質問5から} | {成果物名} | {説明} |

## 成功基準

{質問6の回答から生成}
- [ ] {基準1}
- [ ] {基準2}

## 技術的考慮事項

### 実装アプローチ

{質問10の回答から生成}

### 依存関係

{質問11の回答から生成}

### テスト要件

{質問12の回答から生成}

## タスク一覧

インタビュー結果から導出したタスク:

### 準備

- [ ] 関連コードの調査
- [ ] 設計方針の確定

### 実装

- [ ] {タスク1}
- [ ] {タスク2}

### テスト・検証

- [ ] テストの作成
- [ ] make check-all の実行

### ドキュメント

- [ ] README/ドキュメントの更新（必要な場合）

---

**最終更新**: {今日の日付}
```

---

## 軽量モード: ステップ 3 - GitHub Project 作成

### GitHub 認証確認

```bash
gh auth status
```

認証エラーの場合:
```
GitHub 認証が必要です。

以下のコマンドで認証してください:
  gh auth login

認証完了後、再度実行してください。
```

### プロジェクト作成

```bash
gh project create --title "{プロジェクト名}" --owner @me
```

成功した場合、Project 番号と URL を取得し、計画書に追記する。

失敗した場合:
```
GitHub Project の作成に失敗しました。

エラー: {エラーメッセージ}

計画書は作成されています: docs/project/{slug}.md

対処法:
1. 手動で Project を作成:
   gh project create --title "{プロジェクト名}" --owner @me
2. 後からステップ4でIssueを登録可能
```

---

## 軽量モード: ステップ 4 - タスク分解と Issue 登録

### タスク分解

計画書のタスク一覧を元に、実装可能な粒度にタスクを分解する。

分解の基準:
- 1タスク = 1-2時間で完了できるサイズ
- 依存関係を明確化
- 受け入れ条件を定義

### Issue 作成

**Issue のタイトルと本文は日本語で記述すること。**

各タスクを GitHub Issue として作成:

```bash
gh issue create \
  --title "[日本語タイトル]" \
  --body "[日本語本文]" \
  --label "[ラベル]"
```

### Issue 本文テンプレート

```markdown
## 概要

[タスクの概要]

## 詳細

[詳細な説明]

## 受け入れ条件

- [ ] [条件1]
- [ ] [条件2]

## 関連

- 計画書: docs/project/{slug}.md
- GitHub Project: {project_url}
```

### ラベル自動判定

| キーワード | ラベル |
|------------|--------|
| 新機能、追加、feature | `enhancement` |
| バグ、修正、fix | `bug` |
| リファクタ、改善 | `refactor` |
| ドキュメント、docs | `documentation` |
| テスト | `test` |

### Project への追加

作成した Issue を GitHub Project に追加:

```bash
gh project item-add {project_number} --owner @me --url {issue_url}
```

---

## 軽量モード: ステップ 5 - 完了レポート

```text
軽量プロジェクトのセットアップが完了しました!

計画書:
- docs/project/{slug}.md

GitHub Project:
- 名前: {プロジェクト名}
- URL: {project_url}

作成した Issue:
- [#123](URL): タスク1
- [#124](URL): タスク2
- ...

次のステップ:
1. 計画書の内容を確認してください
2. Issue を順番に実装してください
3. 完了したらチェックボックスを更新してください

実装のヒント:
- feature-implementer でTDDベースの実装を開始
- /ensure-quality で品質チェック
- /commit-and-pr でPR作成
```

---

# パッケージ開発モード

`/new-package` で作成されたパッケージの開発プロジェクトを開始する正式フロー。
LRD→設計ドキュメント→タスク分解の順に進む。

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

---

## パッケージ開発モード: ステップ 0 - 引数検証

1. `@` で指定されたパスを解析する
2. パスから `<library_name>` を抽出する（`src/` と `/docs/` の間の部分）
3. **プロジェクトファイルの存在を確認**:
   - **存在しない場合**: エラーメッセージを表示して終了:
     ```
     エラー: project.md が見つかりません。

     先に /new-package <package_name> を実行してパッケージを作成してください。
     ```
   - **存在する場合**: 内容を読み込み、ステップ 1-1 に進む

---

## パッケージ開発モード: ステップ 1-1 - インタビュー

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

---

## パッケージ開発モード: ステップ 1-2 - LRD 作成

1. **prd-writing スキル**をロード
2. プロジェクトファイル + インタビュー結果を元に`src/<library_name>/docs/library-requirements.md`を作成/更新
3. アイデアを具体化：
    - 詳細な使用例
    - 受け入れ条件
    - 非機能要件
    - 成功指標
4. ユーザーに確認を求め、**承認されるまで待機**

**重要: LRD の承認なしに次のステップには進まない**

---

## パッケージ開発モード: ステップ 2 - 機能設計書

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

---

## パッケージ開発モード: ステップ 3 - アーキテクチャ設計書

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

---

## パッケージ開発モード: ステップ 4 - リポジトリ構造定義書

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

---

## パッケージ開発モード: ステップ 5-6 - 開発ガイドラインと用語集

ステップ 5 と 6 は依存関係があるため、**逐次で実行**してください。
（glossary-writer は development-guidelines.md を入力として参照）

### ステップ 5: 開発ガイドラインの作成/更新

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

### ステップ 6: 用語集の作成/更新

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

---

## パッケージ開発モード: ステップ 7 - タスク分解

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

---

## パッケージ開発モード: ステップ 8 - プロジェクト管理方式の選択

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
2. 新規プロジェクト作成:
   ```bash
   gh project create --title "{library_name}" --owner @me
   ```
3. tasks.md の各タスクを Issue として作成
4. Project に Issue を追加:
   ```bash
   gh project item-add {project_number} --owner @me --url {issue_url}
   ```

**選択肢 2（ローカル）の場合**:
tasks.md をそのまま使用

---

## パッケージ開発モード: ステップ 9 - 次のアクション選択

AskUserQuestion ツールを使用して次のステップを確認:

```yaml
question: "次のステップを選択してください"
options:
    - label: "実装を開始（推奨）"
      description: "/issue でタスク管理、feature-implementer で実装を開始"
    - label: "設計レビューを行う"
      description: "設計ドキュメントを確認してから実装"
```

---

## パッケージ開発モード: 完了条件

-   LRD がユーザーに承認されていること
-   6 つのライブラリドキュメントが全て作成/更新されていること
-   tasks.md が作成されていること
-   プロジェクト管理方式が選択されていること

完了時のメッセージ:

```text
開発プロジェクトのセットアップが完了しました!

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
```

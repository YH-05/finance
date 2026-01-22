# Issue Creation Guide

Issue 作成の詳細ガイドです。

---

## 1. クイック発行モード（--add）

小さな Issue を素早く作成するためのモードです。

### 1.1 コマンド構文

```bash
/issue --add <要件概要>
```

### 1.2 処理フロー

```
/issue --add <要件概要>
    │
    ├─ Q1: GitHub Project 選択
    │   ├─ Project なし
    │   └─ Project 番号を指定
    │
    ├─ Q2: Issue の種類
    │   ├─ 新機能の追加 → enhancement
    │   ├─ 既存機能の改善 → enhancement
    │   ├─ バグ修正 → bug
    │   └─ リファクタリング → refactor
    │
    ├─ Q3: 対象パッケージ（multiSelect）
    │   ├─ finance
    │   ├─ market_analysis
    │   ├─ rss
    │   ├─ factor
    │   └─ strategy
    │
    ├─ Q4: 優先度
    │   ├─ High → priority:high
    │   ├─ Medium → priority:medium
    │   └─ Low → priority:low
    │
    ├─ Q5: 追加の詳細（オプション）
    │
    ├─ Issue プレビュー表示
    │
    └─ 確認 → 作成 / 修正 / キャンセル
```

### 1.3 使用例

```bash
/issue --add ログイン画面にパスワードリセット機能を追加したい
/issue --add RSSフィードの取得でタイムアウトエラーが出る
```

### 1.4 ラベル自動判定

| 種類 | 自動付与ラベル |
|------|----------------|
| 新機能の追加 | `enhancement` |
| 既存機能の改善 | `enhancement` |
| バグ修正 | `bug` |
| リファクタリング | `refactor` |

| 優先度 | 自動付与ラベル |
|--------|----------------|
| High | `priority:high` |
| Medium | `priority:medium` |
| Low | `priority:low` |

### 1.5 受け入れ条件テンプレート（種類別）

| 種類 | 標準受け入れ条件 |
|------|------------------|
| 新機能の追加 | ユニットテストが追加されている, 機能が正常に動作する |
| 既存機能の改善 | 既存テストが通る, 改善内容が動作する |
| バグ修正 | バグが再現しなくなる, リグレッションテストが追加されている |
| リファクタリング | 既存テストが全て通る, 動作に変更がない |

---

## 2. パッケージ開発モード

パッケージ開発のタスク管理に特化したモードです。

### 2.1 コマンド構文

```bash
/issue @src/<library_name>/docs/project.md
```

### 2.2 処理フロー

```
/issue @src/<library>/docs/project.md
    │
    ├─ ステップ 0: 引数解析
    │   └─ library_name 抽出
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
    │   ├─ A: 5回のヒアリング（概要、種類、詳細、条件、優先度）
    │   ├─ B: ファイルパース
    │   └─ C: スキップ
    │
    ├─ ステップ 4: task-decomposer 起動
    │   ├─ 類似性判定（70%+: 既存に追加、40-70%: 確認、40%未満: 新規）
    │   ├─ タスク分解
    │   └─ 双方向同期（GitHub ↔ project.md）
    │
    └─ ステップ 5: 結果表示
```

### 2.3 使用例

```bash
/issue @src/market_analysis/docs/project.md
```

---

## 3. 軽量プロジェクトモード

GitHub Project と連携した軽量プロジェクト管理用のモードです。

### 3.1 コマンド構文

```bash
/issue @docs/project/<slug>.md
```

### 3.2 処理フロー

```
/issue @docs/project/<slug>.md
    │
    ├─ パッケージ開発モードの全処理を実行
    │
    ├─ 追加処理
    │   │
    │   ├─ project.md から Project 番号抽出
    │   │   └─ `**GitHub Project**: [#N](URL)` 形式
    │   │
    │   ├─ gh project field-list → Status フィールド情報
    │   │
    │   ├─ gh project item-list → Item 一覧
    │   │
    │   └─ Issue 作成/更新時に Project Item も更新
    │
    └─ ステップ 5: 結果表示（Project 更新含む）
```

### 3.3 使用例

```bash
/issue @docs/project/research-agent.md
```

---

## 4. ラベル自動判定ルール

### 4.1 種類ラベル

| キーワード | ラベル |
|-----------|--------|
| 新機能、追加、feat | `enhancement` |
| 改善、update | `enhancement` |
| バグ、修正、fix | `bug` |
| リファクタ、refactor | `refactor` |
| ドキュメント、docs | `documentation` |
| テスト、test | `test` |

### 4.2 優先度ラベル

| 優先度 | ラベル |
|--------|--------|
| High | `priority:high` |
| Medium | `priority:medium` |
| Low | `priority:low` |

---

## 5. project.md フォーマット

### 5.1 標準構造

```markdown
# プロジェクト名

**GitHub Project**: [#N](URL)

## マイルストーン 1: [名前]

### 機能 1.1: [機能名]
- Issue: [#123](https://github.com/owner/repo/issues/123)
- 優先度: high | medium | low
- ステータス: todo | in_progress | done
- 依存関係:
  - depends_on: [#120](URL)
  - blocks: [#125](URL)
- 説明: [詳細説明]
- 受け入れ条件:
  - [ ] [測定可能な条件1]
  - [x] [完了した条件]
```

### 5.2 同期ルール

| 項目 | ルール |
|------|--------|
| タイトル | project.md を正とする |
| チェックボックス | 双方向マージ（どちらかが[x]なら[x]）|
| ステータス | closed 優先（完了状態は変更しない）|
| 優先度 | project.md を正とする |

---

## 6. 類似性判定

### 6.1 判定基準

| 類似度 | 判定 | アクション |
|--------|------|-----------|
| 70%+ | 高 | 既存 Issue に Tasklist として追加 |
| 40-70% | 中 | ユーザーに確認 |
| 40%未満 | 低 | 新規 Issue 作成 |

### 6.2 類似性計算要素

- タイトルの類似度
- 概要の類似度
- 対象パッケージの一致
- ラベルの一致
- キーワードの重複

---

## 7. task-decomposer サブエージェント

### 7.1 入力

- 実行モード（package_mode / lightweight_mode）
- project.md パス
- GitHub Issues（JSON）
- GitHub Project 情報（オプション）
- ユーザー入力

### 7.2 処理

- 類似性判定
- タスク分解
- 依存関係計算
- 双方向同期

### 7.3 起動方法

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
  - Status フィールド ID: {status_field_id}
  - ステータスオプション:
    - Todo: {todo_option_id}
    - In Progress: {in_progress_option_id}
    - Done: {done_option_id}

  ## ユーザー入力
  [ヒアリング結果またはファイル内容]

  ## 入力モード
  [new / external / sync]
```

---

## 8. エラーハンドリング

### 8.1 認証エラー

```bash
# 基本認証
gh auth login

# Project スコープ追加
gh auth refresh -s project
```

### 8.2 Issue 操作エラー

| エラー | 対処 |
|--------|------|
| Issue not found | 番号確認、`gh issue list` で検索 |
| Permission denied | リポジトリ権限を確認 |
| Rate limit | 待機後にリトライ |
| Invalid state | Issue 状態を確認 |

### 8.3 同期エラー

| エラー | 対処 |
|--------|------|
| project.md 構文エラー | パースエラー箇所を特定、修正 |
| 循環依存検出 | 警告を出して修正を促す |
| 削除された Issue 参照 | 警告を出して参照を削除 |

---

## 9. コマンド完了条件

- [ ] 引数が正しく解析されている
- [ ] GitHub Issues と project.md が読み込まれている
- [ ] 入力方法が選択されている
- [ ] ユーザー入力が収集されている（同期のみの場合はスキップ）
- [ ] task-decomposer が実行され、同期が完了している
- [ ] 結果が表示されている

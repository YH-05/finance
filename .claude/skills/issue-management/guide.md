# Issue Management Guide

Issue 操作・同期の詳細ガイドです。

## 1. Issue 作成フロー

### 1.1 クイック発行モード（--add）

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

### 1.2 パッケージ開発モード

```
/issue @src/<library>/docs/project.md
    │
    ├─ ステップ 0: 引数解析
    │   └─ library_name 抽出
    │
    ├─ ステップ 1: 現状把握
    │   ├─ gh issue list
    │   └─ project.md 読み込み
    │
    ├─ ステップ 2: 入力トリガー選択
    │   ├─ 自然言語で説明
    │   ├─ 外部ファイルから読み込み
    │   └─ 同期のみ
    │
    ├─ ステップ 3: 入力処理
    │   ├─ A: 5回のヒアリング
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

### 1.3 軽量プロジェクトモード

パッケージ開発モードに加えて以下を実行:

```
project.md から Project 番号抽出
    │
    ├─ gh project field-list → Status フィールド情報
    │
    ├─ gh project item-list → Item 一覧
    │
    └─ Issue 作成/更新時に Project Item も更新
```

## 2. ラベル自動判定ルール

### 2.1 種類ラベル

| キーワード | ラベル |
|-----------|--------|
| 新機能、追加、feat | `enhancement` |
| 改善、update | `enhancement` |
| バグ、修正、fix | `bug` |
| リファクタ、refactor | `refactor` |
| ドキュメント、docs | `documentation` |
| テスト、test | `test` |

### 2.2 優先度ラベル

| 優先度 | ラベル |
|--------|--------|
| High | `priority:high` |
| Medium | `priority:medium` |
| Low | `priority:low` |

### 2.3 開発タイプラベル

| キーワード | タイプ |
|-----------|--------|
| agent, エージェント | agent |
| command, コマンド | command |
| skill, スキル | skill |
| 上記以外 | python |

## 3. project.md フォーマット

### 3.1 標準構造

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

### 3.2 同期ルール

| 項目 | ルール |
|------|--------|
| タイトル | project.md を正とする |
| チェックボックス | 双方向マージ（どちらかが[x]なら[x]）|
| ステータス | closed 優先（完了状態は変更しない）|
| 優先度 | project.md を正とする |

## 4. 開発タイプ判定ロジック

```yaml
判定順序:
  1. ラベルによる判定:
     - "agent" | "エージェント" → agent
     - "command" | "コマンド" → command
     - "skill" | "スキル" → skill
     - 上記以外 → python

  2. タイトル・本文のキーワードによる判定:
     agent:
       - "エージェントを作成" | "エージェントを追加"
       - ".claude/agents/" パスへの言及
     command:
       - "コマンドを作成" | "/xxx を追加"
       - ".claude/commands/" パスへの言及
     skill:
       - "スキルを作成" | "スキルを追加"
       - ".claude/skills/" パスへの言及
     python:
       - 上記以外のすべて
```

## 5. 類似性判定

### 5.1 判定基準

| 類似度 | 判定 | アクション |
|--------|------|-----------|
| 70%+ | 高 | 既存 Issue に Tasklist として追加 |
| 40-70% | 中 | ユーザーに確認 |
| 40%未満 | 低 | 新規 Issue 作成 |

### 5.2 類似性計算要素

- タイトルの類似度
- 概要の類似度
- 対象パッケージの一致
- ラベルの一致
- キーワードの重複

## 6. 確信度ベース確認

### 6.1 確信度レベル

| レベル | 範囲 | アクション |
|--------|------|-----------|
| HIGH | 0.80+ | 自動適用 |
| MEDIUM | 0.70-0.79 | 適用、確認なし |
| LOW | < 0.70 | ユーザー確認必須 |

### 6.2 確認必須ケース

- ステータスダウングレード（done → in_progress）
- 受け入れ条件の削除
- 複数の矛盾するステータス変更

## 7. 競合解決ルール

| 状況 | 解決策 |
|------|--------|
| コメント vs project.md | コメント優先（最新情報）|
| コメント vs GitHub Project | コメント優先 |
| 複数コメントで矛盾 | 最新のコメント優先 |
| Issue が closed だが完了コメントなし | closed 状態を維持 |
| confidence < 0.70 | ユーザーに確認 |

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

## 9. サブエージェント連携

### 9.1 task-decomposer

**入力**:
- 実行モード（package_mode / lightweight_mode）
- project.md パス
- GitHub Issues（JSON）
- GitHub Project 情報（オプション）
- ユーザー入力/コメント解析結果

**処理**:
- 類似性判定
- タスク分解
- 依存関係計算
- 双方向同期

### 9.2 comment-analyzer

**入力**:
- Issue 情報（番号、タイトル、本文）
- コメント一覧

**出力**:
```yaml
extracted_updates:
  status_changes:
    - description: "完了"
      evidence: "対応完了しました"
      confidence: 0.95
  acceptance_criteria_updates:
    - criteria: "OAuth対応"
      status: "completed"
      confidence: 0.90
  new_subtasks:
    - title: "GitHub OAuth対応"
      confidence: 0.85
  requirement_changes:
    - change: "Apple Sign-In 追加"
      confidence: 0.80

confidence_summary:
  overall: 0.87
  needs_confirmation: false
```

## 10. コマンド別完了条件

### /issue

- [ ] 引数が正しく解析されている
- [ ] GitHub Issues と project.md が読み込まれている
- [ ] 入力方法が選択されている
- [ ] task-decomposer が実行されている
- [ ] 結果が表示されている

### /issue-implement

- [ ] Issue 情報が取得できている
- [ ] 開発タイプが判定されている
- [ ] 適切なワークフローが完了している
- [ ] PR が作成されている
- [ ] CI がパスしている

### /issue-refine

- [ ] Issue 情報が取得されている
- [ ] 改善対象が選択されている
- [ ] 8項目の詳細確認が完了している
- [ ] 改善案が生成されている
- [ ] ユーザー確認が完了している
- [ ] Issue が更新されている

### /sync-issue

- [ ] Issue 情報とコメントが取得されている
- [ ] comment-analyzer による解析が完了している
- [ ] 確認が必要な場合はユーザー確認が完了している
- [ ] task-decomposer による同期が完了している
- [ ] 結果が表示されている

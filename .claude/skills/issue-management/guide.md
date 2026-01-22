# Issue Management Guide

Issue 操作・同期の詳細ガイドです。

---

## 1. Issue 作成手順（3モード）

Issue の性質に応じて最適なモードを選択します。

### 1.1 クイック発行モード（--add）

小さな Issue を素早く作成するためのモードです。

**コマンド構文**:
```bash
/issue --add <要件概要>
```

**処理フロー**:
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

**使用例**:
```bash
/issue --add ログイン画面にパスワードリセット機能を追加したい
/issue --add RSSフィードの取得でタイムアウトエラーが出る
```

### 1.2 パッケージ開発モード

パッケージ開発のタスク管理に特化したモードです。

**コマンド構文**:
```bash
/issue @src/<library>/docs/project.md
```

**処理フロー**:
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

**使用例**:
```bash
/issue @src/market_analysis/docs/project.md
```

### 1.3 軽量プロジェクトモード

GitHub Project と連携した軽量プロジェクト管理用のモードです。

**コマンド構文**:
```bash
/issue @docs/project/<slug>.md
```

**処理フロー**:
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

**使用例**:
```bash
/issue @docs/project/research-agent.md
```

---

## 2. Issue 自動実装ワークフロー（5フェーズ）

`/issue-implement` コマンドは、開発タイプに応じた5フェーズのワークフローを実行します。

### 2.1 Phase 0: Issue検証・タイプ判定

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

### 2.2 Python ワークフロー（Phase 1-5）

```
Phase 1: テスト作成
    │
    ├─ test-writer サブエージェント起動
    │
    ├─ 受け入れ条件ごとにテストケース作成
    │   └─ 日本語命名（test_正常系_xxx, test_異常系_xxx）
    │
    └─ Red状態（失敗するテスト）で完了
        └─ make test で失敗を確認

Phase 2: 実装
    │
    ├─ feature-implementer サブエージェント起動
    │
    ├─ TDDサイクル実行
    │   ├─ Red: テスト失敗確認
    │   ├─ Green: 最小実装
    │   └─ Refactor: コード整理
    │
    ├─ 各タスク完了時に Issue チェックボックス更新
    │   └─ gh issue edit {number} --body "..."
    │
    └─ quality-checker(--quick) でパス確認

Phase 3: 品質保証
    │
    ├─ quality-checker サブエージェント起動（--auto-fix モード）
    │
    ├─ 自動修正ループ（最大5回）
    │   ├─ make format
    │   ├─ make lint
    │   ├─ make typecheck
    │   └─ make test
    │
    └─ make check-all 成功で完了

Phase 4: PR作成
    │
    ├─ code-simplifier サブエージェント起動
    │   ├─ 型ヒント完全化
    │   ├─ Docstring追加（NumPy形式）
    │   ├─ 命名規則統一
    │   └─ 不要コードの削除
    │
    ├─ /commit-and-pr コマンド実行
    │   ├─ ブランチ: feature/issue-{number}-{slug}
    │   ├─ コミットメッセージに Fixes #{number} 含む
    │   └─ PR本文に Issue リンク含む
    │
    └─ CI確認（最大5分待機）
        └─ gh pr checks "$PR_NUMBER" --watch

Phase 5: 完了処理
    │
    ├─ GitHub Project ステータス更新
    │   └─ Issue を「In Progress」に更新
    │
    └─ 完了レポート出力
```

### 2.3 Agent/Command/Skill ワークフロー

```
Phase A1/C1/S1: 要件分析
    │
    ├─ xxx-expert サブエージェント起動
    │   ├─ agent-expert（エージェント）
    │   ├─ command-expert（コマンド）
    │   └─ skill-expert（スキル）
    │
    ├─ AskUserQuestion で詳細確認
    │   ├─ 名前（kebab-case）
    │   ├─ 主要な責任と専門性
    │   ├─ トリガー条件
    │   └─ 使用するツール
    │
    └─ 既存との重複確認

Phase A2/C2/S2: 設計・作成
    │
    ├─ テンプレートに基づきファイル作成
    │   ├─ .claude/agents/{name}.md
    │   ├─ .claude/commands/{name}.md
    │   └─ .claude/skills/{name}/SKILL.md
    │
    └─ 必須セクション含む
        ├─ フロントマター
        ├─ 目的
        ├─ 処理フロー
        └─ 使用例

Phase A3/C3/S3: 検証
    │
    ├─ フロントマター検証
    │   ├─ name がファイル名と一致
    │   └─ description が設定されている
    │
    ├─ 構造検証
    │   ├─ 必須セクション存在
    │   └─ トリガー条件が明確
    │
    └─ エラー時は前フェーズに戻る

Phase A4/C4/S4: PR作成
    │
    ├─ /commit-and-pr コマンド実行
    │   ├─ ブランチ: feature/issue-{number}-{type}-{name}
    │   └─ コミット: Fixes #{number}
    │
    └─ CI確認
```

---

## 3. Issue ブラッシュアップ手順（8項目確認）

`/issue-refine` コマンドは、Issue の内容を改善するために8項目の詳細確認を行います。

### 3.1 ブラッシュアップフロー

```
/issue-refine {number}
    │
    ├─ ステップ 1: Issue 情報取得
    │
    ├─ ステップ 2: 改善対象選択
    │   ├─ 本文全体
    │   ├─ 受け入れ条件のみ
    │   └─ タイトルと概要
    │
    ├─ ステップ 2.5: 8項目の詳細確認
    │   └─ (詳細は 3.2 参照)
    │
    ├─ ステップ 3: 改善案生成
    │   └─ 収集情報を反映
    │
    ├─ ステップ 4: 差分表示・確認
    │   ├─ 適用する
    │   ├─ 修正して適用
    │   └─ スキップ
    │
    └─ ステップ 5: Issue 更新
```

### 3.2 8項目の詳細確認

Issue の不明点・曖昧な点を明確化するため、以下の8項目を順番に確認します。

#### 項目 1: 背景・目的

```yaml
question: "この機能の主な目的は何ですか？"
header: "目的"
options:
  - 運用効率化（既存業務の効率化・自動化）
  - 新機能追加（新しい機能の提供）
  - 問題解決（既存の問題・バグの修正）
  - 品質改善（パフォーマンス・保守性の向上）
```

確認ポイント:
- なぜこの機能/修正が必要か
- どのような問題を解決するか
- 誰が使うのか（ターゲットユーザー）

#### 項目 2: 実装スコープ

```yaml
question: "実装のスコープはどこまでですか？"
header: "スコープ"
multiSelect: true
options:
  - 基本機能のみ（最小限の機能実装）
  - エラーハンドリング（例外処理・バリデーション含む）
  - テスト実装（ユニットテスト・統合テスト含む）
  - ドキュメント（README・API ドキュメント含む）
```

確認ポイント:
- 何をやる/やらないか
- 既存機能との関係
- MVPの範囲

#### 項目 3: 連携・依存関係

```yaml
question: "他の機能との連携はありますか？"
header: "連携"
multiSelect: true
options:
  - 単独動作（他機能に依存しない）
  - 既存機能を利用（既存のモジュール・API を使用）
  - 既存機能を拡張（既存機能に機能追加）
  - 新規統合（外部サービス・ライブラリと統合）
```

確認ポイント:
- 依存する Issue（depends_on）
- ブロックする Issue（blocks）
- 外部サービス連携

#### 項目 4: 優先度・期限

```yaml
question: "優先度と期限について教えてください"
header: "優先度"
options:
  - 緊急（P0）- 今すぐ対応が必要
  - 高（P1）- 1週間以内に対応
  - 中（P2）- 1ヶ月以内に対応
  - 低（P3）- いつでもよい
```

#### 項目 5: ユースケース

自由記述で具体的な使用シナリオを収集:
- 「この機能を使う具体的なユースケースを教えてください」

#### 項目 6: 受け入れ条件詳細

自由記述で完了判断基準を収集:
- 「受け入れ条件として、どのような状態になれば完了と判断しますか？」

#### 項目 7: 実装時の注意点

自由記述で技術的制約を収集:
- 「実装時に特に注意すべき点はありますか？」

#### 項目 8: 関連 Issue

自由記述で関連情報を収集:
- 「関連する Issue や参考資料があれば教えてください」

### 3.3 収集情報の構造化

```json
{
  "purpose": "運用効率化",
  "scope": ["基本機能のみ", "エラーハンドリング", "テスト実装"],
  "integration": ["既存機能を利用"],
  "priority": "中（P2）",
  "use_cases": "ユーザーの自由記述",
  "acceptance_criteria_detail": "ユーザーの自由記述",
  "notes": "ユーザーの自由記述",
  "related_issues": ["#123", "#456"]
}
```

### 3.4 改善案への反映チェックリスト

- [ ] 「目的」が概要に反映されている
- [ ] 「スコープ」が詳細セクションに明記されている
- [ ] 「連携」が詳細セクションまたは関連 Issue に記載されている
- [ ] 「優先度」が備考または Issue ラベルとして設定されている
- [ ] 「ユースケース」が概要または詳細に含まれている
- [ ] 「受け入れ条件の詳細」が測定可能な受け入れ条件に変換されている
- [ ] 「実装時の注意点」が詳細または備考に記載されている
- [ ] 「関連 Issue」が備考セクションに追加されている

---

## 4. コメント同期フロー

`/sync-issue` コマンドは、Issue コメントから進捗・タスク・仕様変更を抽出し、project.md と GitHub Project に反映します。

### 4.1 同期フロー概要

```
/sync-issue #123
    │
    ├─ ステップ 1: データ取得
    │   ├─ Issue 情報取得
    │   ├─ コメント取得（GraphQL）
    │   ├─ project.md 読み込み
    │   └─ GitHub Project 情報取得
    │
    ├─ ステップ 2: コメント解析
    │   └─ comment-analyzer サブエージェント起動
    │
    ├─ ステップ 3: 競合解決・確認
    │   └─ 低確信度の場合ユーザー確認
    │
    ├─ ステップ 4: 同期実行
    │   └─ task-decomposer サブエージェント起動
    │
    └─ ステップ 5: 結果表示
```

### 4.2 comment-analyzer の出力形式

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

### 4.3 確信度ベース確認

| レベル | 範囲 | アクション |
|--------|------|-----------|
| HIGH | 0.80+ | 自動適用 |
| MEDIUM | 0.70-0.79 | 適用、確認なし |
| LOW | < 0.70 | ユーザー確認必須 |

**確認必須ケース**:
- ステータスダウングレード（done → in_progress）
- 受け入れ条件の削除
- 複数の矛盾するステータス変更

### 4.4 同期処理

task-decomposer（comment_sync モード）が以下を実行:

1. **ステータス変更の適用**:
   - Issue の状態を更新（close/reopen）
   - project.md のステータスを更新
   - GitHub Project のステータスを更新

2. **受け入れ条件の更新**:
   - Issue 本文のチェックボックスを更新
   - project.md の受け入れ条件を同期

3. **新規サブタスクの作成**:
   - 新規 Issue を作成
   - 親 Issue の Tasklist に追加
   - project.md に追加
   - GitHub Project に追加

4. **仕様変更の反映**:
   - Issue 本文に追記
   - project.md の説明・条件を更新

### 4.5 競合解決ルール

| 状況 | 解決策 |
|------|--------|
| コメント vs project.md で状態が異なる | コメント優先（最新情報） |
| コメント vs GitHub Project で状態が異なる | コメント優先 |
| 複数コメントで矛盾 | 最新のコメント優先 |
| Issue が closed だが完了コメントなし | closed 状態を維持 |
| confidence < 0.70 | ユーザーに確認 |
| ステータスダウングレード | ユーザーに確認（再オープンの意図を確認） |

---

## 5. ラベル自動判定ルール

### 5.1 種類ラベル

| キーワード | ラベル |
|-----------|--------|
| 新機能、追加、feat | `enhancement` |
| 改善、update | `enhancement` |
| バグ、修正、fix | `bug` |
| リファクタ、refactor | `refactor` |
| ドキュメント、docs | `documentation` |
| テスト、test | `test` |

### 5.2 優先度ラベル

| 優先度 | ラベル |
|--------|--------|
| High | `priority:high` |
| Medium | `priority:medium` |
| Low | `priority:low` |

### 5.3 開発タイプラベル

| キーワード | タイプ |
|-----------|--------|
| agent, エージェント | agent |
| command, コマンド | command |
| skill, スキル | skill |
| 上記以外 | python |

---

## 6. project.md フォーマット

### 6.1 標準構造

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

### 6.2 同期ルール

| 項目 | ルール |
|------|--------|
| タイトル | project.md を正とする |
| チェックボックス | 双方向マージ（どちらかが[x]なら[x]）|
| ステータス | closed 優先（完了状態は変更しない）|
| 優先度 | project.md を正とする |

---

## 7. 類似性判定

### 7.1 判定基準

| 類似度 | 判定 | アクション |
|--------|------|-----------|
| 70%+ | 高 | 既存 Issue に Tasklist として追加 |
| 40-70% | 中 | ユーザーに確認 |
| 40%未満 | 低 | 新規 Issue 作成 |

### 7.2 類似性計算要素

- タイトルの類似度
- 概要の類似度
- 対象パッケージの一致
- ラベルの一致
- キーワードの重複

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
- ステータス変更
- 受け入れ条件更新
- 新規サブタスク
- 仕様変更
- 確信度サマリー

### 9.3 実装系サブエージェント

| エージェント | 用途 |
|--------------|------|
| test-writer | テスト作成（Python実装） |
| feature-implementer | TDD実装（Python実装） |
| quality-checker | 品質自動修正 |
| code-simplifier | コード整理 |

### 9.4 設計系サブエージェント

| エージェント | 用途 |
|--------------|------|
| agent-expert | エージェント作成 |
| command-expert | コマンド作成 |
| skill-expert | スキル作成 |

---

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

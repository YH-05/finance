---
description: GitHub Projectを参照し、Todoの Issue を並列開発用にグルーピング表示
---

# /plan-worktrees - Worktree 並列開発計画

GitHub Project の Todo 状態の Issue を分析し、worktree による並列開発のためのグルーピングを提案します。

**目的**: 依存関係を考慮した並列開発計画の可視化

## コマンド構文

```bash
# GitHub Project 番号を指定
/plan-worktrees <project_number>

# 例
/plan-worktrees 1
/plan-worktrees 3
```

---

## ステップ 0: 引数解析

1. 引数から GitHub Project 番号を取得
2. **引数がない場合**: AskUserQuestion でヒアリング

```yaml
questions:
  - question: "対象の GitHub Project 番号を入力してください"
    header: "Project番号"
    options:
      - label: "プロジェクト一覧を表示"
        description: "gh project list で一覧を確認"
      - label: "番号を直接入力"
        description: "プロジェクト番号を入力"
```

**プロジェクト一覧の表示**:

```bash
gh project list --owner "@me" --format json
```

---

## ステップ 1: プロジェクト情報の取得

### 1.1 認証確認

```bash
gh auth status
```

**認証スコープ不足の場合**:

```
エラー: GitHub Project へのアクセス権限がありません。

解決方法:
gh auth refresh -s project
```

### 1.2 プロジェクト Item の取得

```bash
gh project item-list <project_number> --owner "@me" --format json --limit 100
```

### 1.3 プロジェクトフィールドの取得

```bash
gh project field-list <project_number> --owner "@me" --format json
```

**プロジェクトが存在しない場合**:

```
エラー: Project #<number> が見つかりません。

解決方法:
gh project list --owner "@me" でプロジェクト一覧を確認してください。
```

---

## ステップ 2: Todo Issue のフィルタリング

取得したアイテムから以下の条件でフィルタリング:

1. **status が "Todo"** のアイテムのみ抽出
2. **type が "Issue"** のアイテムのみ（Draft は除外）
3. 各アイテムから以下の情報を抽出:
   - `number`: Issue 番号
   - `title`: タイトル
   - `labels`: ラベル配列
   - `body`: 本文（依存関係解析用）
   - `url`: Issue URL
   - `repository`: リポジトリ名

**Todo Issue がない場合**:

```
Project #<number> に Todo 状態の Issue がありません。

現在のステータス:
- In Progress: X 件
- Done: Y 件

次のステップ:
- 新しい Issue を作成して Project に追加
- In Progress の Issue を確認
```

---

## ステップ 3: 依存関係の解析

各 Issue の body から依存関係を抽出:

### 3.1 依存関係パターンの検出

以下のパターンを検索:

```markdown
## 依存タスク
- [ ] #<number>
- [x] #<number>

depends on #<number>
depends_on: #<number>
blocked by #<number>
requires #<number>
```

### 3.2 依存グラフの構築

```python
# 依存関係グラフ（概念）
dependencies = {
    12: [9, 10, 11],  # Issue #12 は #9, #10, #11 に依存
    15: [12],         # Issue #15 は #12 に依存
    10: [],           # Issue #10 は依存なし
}
```

### 3.3 循環依存の検出

循環依存がある場合は警告:

```
警告: 循環依存を検出しました

#10 → #12 → #15 → #10

解決方法:
Issue の依存関係を見直してください。
```

---

## ステップ 4: Wave グルーピング

依存関係に基づいて Issue を「Wave（波）」にグルーピング:

### 4.1 Wave の定義

| Wave | 条件 | 並列開発 |
|------|------|----------|
| Wave 1 | 依存関係なし、または全ての依存が Done | 即座に並列開発可能 |
| Wave 2 | Wave 1 の Issue に依存 | Wave 1 完了後に開発可能 |
| Wave 3 | Wave 2 の Issue に依存 | Wave 2 完了後に開発可能 |
| ... | ... | ... |

### 4.2 グルーピングアルゴリズム

```python
# 概念的なアルゴリズム
def assign_waves(issues, dependencies, done_issues):
    waves = {}
    remaining = set(issues)
    current_wave = 1

    while remaining:
        # このWaveで開発可能なIssue
        ready = []
        for issue in remaining:
            deps = dependencies.get(issue, [])
            # 依存がDoneまたは前のWaveに含まれていれば開発可能
            if all(d in done_issues or d in assigned for d in deps):
                ready.append(issue)

        if not ready:
            # 残りは循環依存または未解決の依存あり
            waves["unresolved"] = list(remaining)
            break

        waves[current_wave] = ready
        assigned.update(ready)
        remaining -= set(ready)
        current_wave += 1

    return waves
```

### 4.3 サブグルーピング（Wave 内）

同じ Wave 内でさらにグルーピング:

1. **ラベルベース**: `type:*`, `phase:*` でグルーピング
2. **優先度ソート**: `priority:high` → `priority:medium` → `priority:low`
3. **リポジトリベース**: 異なるリポジトリの Issue は自然に並列開発可能

---

## ステップ 5: 結果表示

### 5.1 サマリー表示

```
================================================================================
📋 Worktree 並列開発計画
================================================================================

Project: #<number>
リポジトリ: <repository>
Todo Issue: X 件
Wave 数: Y

================================================================================
```

### 5.2 Wave ごとの Issue 一覧

```markdown
## 🌊 Wave 1（即座に並列開発可能）

以下の Issue は依存関係がなく、同時に worktree を作成して並列開発できます。

| # | タイトル | ラベル | worktree コマンド |
|---|----------|--------|-------------------|
| #10 | 計画書テンプレートの作成 | priority:high, type:feature | `/worktree feature/issue-10` |
| #11 | GitHub Project 新規作成機能 | priority:high, type:feature | `/worktree feature/issue-11` |

**推奨 worktree 作成**:
```bash
# 複数の worktree を作成（別々のターミナルで実行）
/worktree feature/issue-10
/worktree feature/issue-11
```

---

## 🌊 Wave 2（Wave 1 完了後に開発可能）

以下の Issue は Wave 1 の完了を待つ必要があります。

| # | タイトル | 依存 | ラベル |
|---|----------|------|--------|
| #12 | /polish-plan との連携確認 | #9, #10, #11 | priority:medium, type:test |
| #13 | コマンドのユニットテスト | #10 | priority:medium, type:test |

**依存関係**:
- #12 depends on #9, #10, #11（全て Wave 1）
- #13 depends on #10（Wave 1）

---

## ⚠️ 未解決の依存関係

以下の Issue は解決できない依存関係があります:

| # | タイトル | 問題 |
|---|----------|------|
| #20 | 機能X | 依存先 #99 が存在しない |
| #21 | 機能Y | 循環依存: #21 → #22 → #21 |
```

### 5.3 推奨開発フロー

```markdown
## 📝 推奨開発フロー

### Phase 1: Wave 1 を並列開発

1. 各開発者が Wave 1 の Issue を担当
2. worktree を作成して独立した環境で開発

```bash
# 開発者A
/worktree feature/issue-10

# 開発者B（別ターミナル）
/worktree feature/issue-11
```

3. 各 worktree で開発 → PR 作成 → マージ

### Phase 2: Wave 2 を並列開発

Wave 1 の PR がマージされたら Wave 2 に進む。

### 単独開発の場合

一人で開発する場合も worktree を活用できます:

1. Wave 1 の Issue を 1-2 個選んで worktree 作成
2. 開発中に別の Issue のレビュー待ちが発生したら、別の worktree で次の Issue に着手
3. コンテキストスイッチを最小化しながら効率的に開発
```

---

## ステップ 6: 追加情報（オプション）

### 6.1 ラベル別サマリー

```markdown
## 📊 ラベル別サマリー

| ラベル | Issue 数 | Wave 分布 |
|--------|----------|-----------|
| priority:high | 3 | Wave 1: 2, Wave 2: 1 |
| priority:medium | 5 | Wave 1: 1, Wave 2: 3, Wave 3: 1 |
| type:feature | 4 | Wave 1: 2, Wave 2: 2 |
| type:test | 2 | Wave 2: 2 |
```

### 6.2 クリティカルパス

```markdown
## 🛤️ クリティカルパス

最も長い依存チェーン:

#10 → #12 → #15 → #18（4 ステップ）

このパスの Issue を優先的に完了させることで、全体のリードタイムを短縮できます。
```

---

## エラーハンドリング

| ケース | 対処 |
|--------|------|
| 引数未指定 | プロジェクト番号のヒアリング |
| プロジェクトが存在しない | エラーメッセージとプロジェクト一覧表示 |
| 認証スコープ不足 | `gh auth refresh -s project` を案内 |
| Todo Issue なし | ステータス別件数を表示 |
| 循環依存 | 警告と該当 Issue を表示 |
| 存在しない Issue への依存 | 警告と該当 Issue を表示 |

---

## 出力例

```
================================================================================
📋 Worktree 並列開発計画
================================================================================

Project: #1
リポジトリ: YH-05/prj-note
Todo Issue: 4 件
Wave 数: 2

================================================================================

## 🌊 Wave 1（即座に並列開発可能）- 2 件

| # | タイトル | 優先度 | worktree |
|---|----------|--------|----------|
| #14 | ドキュメント整備 | medium | `/worktree docs/issue-14` |
| #16 | CI設定追加 | high | `/worktree feature/issue-16` |

## 🌊 Wave 2（Wave 1 完了後）- 2 件

| # | タイトル | 依存 | 優先度 |
|---|----------|------|--------|
| #17 | E2Eテスト追加 | #16 | medium |
| #18 | リリース準備 | #14, #16 | low |

================================================================================

## 📝 次のステップ

Wave 1 の開発を開始するには:

```bash
/worktree docs/issue-14
/worktree feature/issue-16
```

worktree 完了後:
```bash
/commit-and-pr
/worktree-done <branch-name>
```
================================================================================
```

---

## 関連コマンド

| コマンド | 説明 |
|----------|------|
| `/worktree` | 新しい worktree を作成 |
| `/worktree-done` | worktree の完了とクリーンアップ |
| `/issue` | Issue 管理・タスク分解 |
| `/commit-and-pr` | コミットと PR 作成 |

---

## 完了条件

このワークフローは、以下の全ての条件を満たした時点で完了:

- ステップ 0: 引数が正しく解析されている
- ステップ 1: プロジェクト情報が取得できている
- ステップ 2: Todo Issue がフィルタリングされている
- ステップ 3: 依存関係が解析されている
- ステップ 4: Wave グルーピングが完了している
- ステップ 5: 結果が表示されている

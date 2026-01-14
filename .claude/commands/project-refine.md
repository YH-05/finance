---
description: プロジェクト全体の適合性チェックとタスク再構成を行う
---

# /project-refine - プロジェクト健全性チェック & 再構成

> **役割の明確化**: このコマンドは **プロジェクト全体の整合性検証とタスク最適化** に特化しています。
>
> - 個別 Issue のブラッシュアップ → `/issue-refine`
> - Issue の新規作成・同期 → `/issue`
> - 並列開発計画 → `/plan-worktrees`

**目的**: GitHub Project と project.md の整合性を検証し、不整合の検出・タスク再構成の提案を行う

## コマンド構文

```bash
# パッケージ開発モード
/project-refine @src/<library_name>/docs/project.md

# 軽量プロジェクトモード
/project-refine @docs/project/<project-slug>.md

# GitHub Project 番号を直接指定
/project-refine <project_number>
```

## 概要

1. GitHub Project / Issues / project.md を読み込み
2. 適合性チェック（依存関係・優先度・ステータス矛盾）
3. 問題の重大度分類と一覧表示
4. タスク再構成の提案生成
5. ユーザー確認後に修正を適用
6. 結果レポートを表示

---

## ステップ 0: 引数解析とモード判定

### パターン A: project.md パス指定

- 形式: `@src/<library_name>/docs/project.md` または `@docs/project/<slug>.md`
- 処理:
  1. project.md を読み込み
  2. `**GitHub Project**: [#N](URL)` からプロジェクト番号を抽出
  3. Issue 番号を `Issue: [#番号](URL)` から抽出

### パターン B: プロジェクト番号指定

- 形式: `<project_number>`（数値）
- 処理:
  1. GitHub Project から直接情報を取得
  2. 関連する project.md を検索（見つからない場合は Project のみで検証）

**引数が不正な場合**:

```text
エラー: 引数の形式が正しくありません。

使用例:
- パッケージ開発: /project-refine @src/market_analysis/docs/project.md
- 軽量プロジェクト: /project-refine @docs/project/research-agent.md
- Project番号: /project-refine 1
```

---

## ステップ 1: データ収集

### 1.1 GitHub Issues の取得

```bash
gh issue list --state all --json number,title,body,labels,state,url,assignees --limit 200
```

### 1.2 GitHub Project 情報の取得

```bash
# Project フィールド情報
gh project field-list {project_number} --owner @me --format json

# Project Items
gh project item-list {project_number} --owner @me --format json
```

### 1.3 project.md の読み込み

- 全タスクの抽出（マイルストーン、機能、サブタスク）
- 依存関係の抽出（`depends_on`, `blocks`）
- 優先度の抽出（high / medium / low）
- ステータスの抽出（todo / in_progress / done）

### 1.4 データ構造化

```yaml
issues:
  - number: 123
    title: "機能A"
    state: open
    labels: [enhancement, priority:high]
    depends_on: [120, 121]
    blocks: [125, 126]
    assignees: [user1]

project_items:
  - issue_number: 123
    status: "In Progress"

project_md_tasks:
  - id: "1.1"
    title: "機能A"
    issue: 123
    priority: high
    status: in_progress
    depends_on: [120, 121]
```

---

## ステップ 2: 適合性チェック

### 2.1 依存関係の循環検出

**アルゴリズム**: 深さ優先探索（DFS）で循環を検出

```
検出例:
#123 → #124 → #125 → #123 (循環!)
```

**重大度**: 🔴 Critical

### 2.2 優先度と依存関係の矛盾検出

**ルール**:
- 高優先度タスクが低優先度タスクに依存 → 警告
- ブロッカーの優先度が被ブロックより低い → 警告

```
検出例:
#123 (high) depends_on #120 (low) → 矛盾
  → 提案: #120 の優先度を high に引き上げ
```

**重大度**: 🟠 Warning

### 2.3 完了タスクへの依存検出

**ルール**:
- 未完了タスクが完了タスクに依存 → 正常（ブロック解除済み）
- 完了タスクが未完了タスクに依存 → 異常（早期完了？）

```
検出例:
#123 (done) depends_on #120 (open) → 異常
  → 提案: #123 のステータスを再確認、または #120 を完了に
```

**重大度**: 🟠 Warning

### 2.4 孤立タスクの検出

**ルール**:
- どのマイルストーンにも属さないタスク
- 依存関係が一切ないが優先度が低いタスク

**重大度**: 🟡 Info

### 2.5 ステータス不整合の検出

**ルール**:
- GitHub Issue: closed だが project.md: in_progress → 不整合
- GitHub Project: Done だが Issue: open → 不整合

**重大度**: 🟠 Warning

### 2.6 担当者の過負荷検出

**ルール**:
- 同一担当者に in_progress タスクが 3 件以上 → 警告
- high 優先度タスクが担当者未割当 → 警告

**重大度**: 🟡 Info

---

## ステップ 3: 問題一覧の表示

### 3.1 重大度別サマリー

```markdown
## 適合性チェック結果

### サマリー

| 重大度 | 件数 | 説明 |
|--------|------|------|
| 🔴 Critical | 1 | 即時対応必要（循環依存など） |
| 🟠 Warning | 5 | 要確認（優先度矛盾、ステータス不整合） |
| 🟡 Info | 3 | 推奨事項（孤立タスク、担当者バランス） |

### 🔴 Critical Issues

#### 1. 依存関係の循環
- **検出パス**: #123 → #124 → #125 → #123
- **影響**: 開発が進行不可能
- **推奨アクション**: 依存関係を見直し、循環を解消

### 🟠 Warning Issues

#### 1. 優先度と依存関係の矛盾
- **Issue**: #123 (high) depends_on #120 (low)
- **推奨アクション**: #120 の優先度を high に変更

#### 2. ステータス不整合
- **Issue**: #125 - GitHub: closed, project.md: in_progress
- **推奨アクション**: project.md のステータスを done に更新

### 🟡 Info

#### 1. 担当者の過負荷
- **担当者**: @user1 - 4件の in_progress タスク
- **推奨アクション**: タスクの分散を検討
```

---

## ステップ 4: タスク再構成の提案

### 4.1 優先度の自動調整提案

依存関係グラフを分析し、最適な優先度を計算:

```markdown
## 優先度調整提案

| Issue | 現在 | 提案 | 理由 |
|-------|------|------|------|
| #120 | low | high | #123(high) のブロッカーのため |
| #122 | high | medium | ブロッカーがないため優先度下げ可能 |
```

### 4.2 依存関係の最適化提案

```markdown
## 依存関係の最適化

### 循環解消
- **提案**: #125 → #123 の依存を削除
- **理由**: #125 は #123 と並列実装可能

### 不要な依存の削除
- **提案**: #130 → #120 の依存を削除
- **理由**: 実際には独立して実装可能
```

### 4.3 担当者バランスの最適化提案

```markdown
## 担当者バランス

### 現状
| 担当者 | In Progress | Todo | 合計 |
|--------|-------------|------|------|
| @user1 | 4 | 2 | 6 |
| @user2 | 1 | 1 | 2 |
| 未割当 | 0 | 3 | 3 |

### 提案
| Issue | 現在 | 提案 | 理由 |
|-------|------|------|------|
| #128 | @user1 | @user2 | 負荷分散 |
| #130 | 未割当 | @user2 | high優先度のため割当必要 |
```

---

## ステップ 5: 修正の適用確認

### 5.1 適用モード選択

AskUserQuestion ツールで確認:

```yaml
questions:
  - question: "検出された問題にどのように対応しますか？"
    header: "適用モード"
    options:
      - label: "すべて自動修正 (Recommended)"
        description: "Critical と Warning を自動修正、Info は表示のみ"
      - label: "個別に確認"
        description: "各修正を個別に確認してから適用"
      - label: "レポートのみ"
        description: "修正は行わず、レポートのみ出力"
```

### 5.2 個別確認（選択時）

Critical/Warning の各項目について:

```yaml
questions:
  - question: "#120 の優先度を low → high に変更しますか？"
    header: "優先度変更"
    options:
      - label: "適用する"
        description: "GitHub Issue と project.md を更新"
      - label: "スキップ"
        description: "この変更をスキップ"
```

---

## ステップ 6: 修正の実行

### 6.1 GitHub Issue の更新

```bash
# ラベル更新（優先度変更）
gh issue edit {number} --remove-label "priority:low" --add-label "priority:high"

# ステータス変更（クローズ）
gh issue close {number}

# ステータス変更（再オープン）
gh issue reopen {number}

# 担当者変更
gh issue edit {number} --add-assignee "{user}"
```

### 6.2 GitHub Project の更新

```bash
# ステータス変更
gh project item-edit --project-id {project_id} --id {item_id} --field-id {status_field_id} --single-select-option-id {option_id}
```

### 6.3 project.md の更新

Edit ツールを使用して project.md を更新:
- 優先度の変更
- ステータスの変更
- 依存関係の修正

### 6.4 依存関係の循環解消（Issue 本文の編集）

```bash
gh issue edit {number} --body "{updated_body}"
```

---

## ステップ 7: 結果レポート

```markdown
## プロジェクト再構成結果

### 実行日時
2026-01-14T12:00:00+09:00

### 適用した修正

#### 優先度変更
| Issue | 変更前 | 変更後 |
|-------|--------|--------|
| #120 | low | high |
| #122 | high | medium |

#### ステータス同期
| Issue | GitHub | project.md | 結果 |
|-------|--------|------------|------|
| #125 | closed | done | 同期完了 |

#### 依存関係修正
| Issue | 修正内容 |
|-------|----------|
| #125 | #123 への依存を削除（循環解消） |

#### 担当者変更
| Issue | 変更前 | 変更後 |
|-------|--------|--------|
| #128 | @user1 | @user2 |

### スキップした項目
- #130 の担当者割当（ユーザーによりスキップ）

### プロジェクト健全性スコア

| 項目 | 修正前 | 修正後 |
|------|--------|--------|
| 循環依存 | 1 | 0 |
| 優先度矛盾 | 3 | 0 |
| ステータス不整合 | 2 | 0 |
| **健全性スコア** | **62%** | **95%** |

## 次のステップ

- `/plan-worktrees {project_number}` で並列開発計画を確認
- `/issue-refine` で個別 Issue の内容をブラッシュアップ
- 残りの Info レベルの推奨事項を検討
```

---

## チェック項目一覧

| カテゴリ | チェック項目 | 重大度 |
|----------|--------------|--------|
| 依存関係 | 循環依存 | 🔴 Critical |
| 依存関係 | 完了タスクへの未完了依存 | 🟠 Warning |
| 優先度 | 高優先度が低優先度に依存 | 🟠 Warning |
| 優先度 | ブロッカーの優先度が低い | 🟠 Warning |
| ステータス | GitHub vs project.md 不整合 | 🟠 Warning |
| ステータス | GitHub vs Project 不整合 | 🟠 Warning |
| 構造 | 孤立タスク | 🟡 Info |
| 担当者 | 過負荷（3件以上 in_progress） | 🟡 Info |
| 担当者 | 高優先度タスクが未割当 | 🟡 Info |

---

## エラーハンドリング

| ケース | 対処 |
|--------|------|
| GitHub 認証エラー | `gh auth login` を案内 |
| Project アクセス権限なし | `gh auth refresh -s project` を案内 |
| project.md が見つからない | Project のみで検証、警告表示 |
| Issue が存在しない | 警告を出して該当項目をスキップ |
| 依存関係のパースエラー | 警告を出して該当項目をスキップ |

---

## 完了条件

このワークフローは、以下の全ての条件を満たした時点で完了:

- ステップ 0: 引数が正しく解析されている
- ステップ 1: GitHub / project.md のデータが収集されている
- ステップ 2: 適合性チェックが完了している
- ステップ 3: 問題一覧が表示されている
- ステップ 4: 再構成提案が生成されている
- ステップ 5: ユーザーが適用モードを選択している
- ステップ 6: 選択された修正が適用されている
- ステップ 7: 結果レポートが表示されている

---
name: new-project
description: |
  新規プロジェクトを作成するスキル。
  /new-project コマンドで使用。
  パッケージ開発モードと軽量プロジェクトモードに対応。
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, AskUserQuestion, TodoWrite, Task
---

# New Project

新規プロジェクトを作成するスキルです。

## 概要

このスキルは以下の2つのモードでプロジェクトを作成します：

| モード | 用途 | 引数 |
|--------|------|------|
| **パッケージ開発** | LRD→設計→実装の正式フロー | `@src/<lib>/docs/project.md` |
| **軽量プロジェクト** | エージェント開発、ワークフロー改善等 | `"プロジェクト名"` または引数なし |

## 使用方法

```bash
# 軽量プロジェクト（インタラクティブ）
/new-project

# 軽量プロジェクト（名前指定）
/new-project "CI/CD改善"

# パッケージ開発
/new-project @src/market_analysis/docs/project.md
```

## プロセス

### モード判定

引数から自動判定：

```
引数なし or 文字列 → 軽量プロジェクトモード
@src/*/docs/project.md → パッケージ開発モード
```

### 軽量プロジェクトモード

#### ステップ1: インタビュー（10-12問）

AskUserQuestion を使用して要件を収集：

**フェーズ1: 背景理解（質問1-3）**

```yaml
質問1:
  question: "このプロジェクトの背景は何ですか？"
  header: "背景"
  options:
    - label: "新機能の追加"
      description: "既存システムに新しい機能を追加"
    - label: "既存機能の改善"
      description: "パフォーマンス、UX、保守性の向上"
    - label: "バグ修正・問題解決"
      description: "既知の問題や障害の解消"
    - label: "リファクタリング"
      description: "コード品質・構造の改善"

質問2:
  question: "具体的にどのような問題や課題がありますか？"
  header: "課題"
  # 自由記述を促す選択肢

質問3:
  question: "この課題はいつから発生していますか？"
  header: "期間"
  options:
    - label: "最近発生"
      description: "数日〜1週間以内"
    - label: "しばらく前から"
      description: "数週間〜1ヶ月"
    - label: "以前から認識"
      description: "1ヶ月以上前から"
```

**フェーズ2: 目標設定（質問4-6）**

```yaml
質問4:
  question: "このプロジェクトで達成したい目標は何ですか？"
  header: "目標"
  # 自由記述を促す選択肢

質問5:
  question: "主な成果物は何ですか？"
  header: "成果物"
  multiSelect: true
  options:
    - label: "コード（スキル/エージェント）"
      description: ".claude/ 配下の実装"
    - label: "コード（Python）"
      description: "src/ 配下の実装"
    - label: "テスト"
      description: "tests/ 配下のテスト"
    - label: "ドキュメント"
      description: "docs/ 配下のドキュメント"

質問6:
  question: "成功基準は何ですか？"
  header: "成功基準"
  # 自由記述を促す選択肢
```

**フェーズ3: スコープ定義（質問7-9）**

```yaml
質問7:
  question: "変更の範囲はどの程度ですか？"
  header: "変更範囲"
  options:
    - label: "新規追加のみ"
      description: "既存コードへの影響なし"
    - label: "既存修正のみ"
      description: "既存コードの変更"
    - label: "新規追加 + 既存修正"
      description: "両方を含む"

質問8:
  question: "影響するディレクトリはどこですか？"
  header: "対象"
  multiSelect: true
  options:
    - label: ".claude/"
      description: "エージェント、スキル、コマンド"
    - label: "src/"
      description: "Pythonパッケージ"
    - label: "tests/"
      description: "テストコード"
    - label: "docs/"
      description: "ドキュメント"

質問9:
  question: "スコープ外とするものは何ですか？"
  header: "除外"
  # 自由記述を促す選択肢
```

**フェーズ4: 技術詳細（質問10-12）**

```yaml
質問10:
  question: "実装アプローチの方針は？"
  header: "方針"
  options:
    - label: "シンプル優先"
      description: "最小限の実装で動作を優先"
    - label: "拡張性優先"
      description: "将来の拡張を考慮した設計"
    - label: "パフォーマンス優先"
      description: "処理速度・効率を重視"

質問11:
  question: "既存の依存関係はありますか？"
  header: "依存"
  # 自由記述を促す選択肢

質問12:
  question: "テスト要件は？"
  header: "テスト"
  options:
    - label: "ユニットテストのみ"
      description: "基本的なテスト"
    - label: "ユニット + 統合テスト"
      description: "コンポーネント間連携も検証"
    - label: "テスト不要"
      description: "ドキュメントのみの変更など"
```

#### ステップ2: 計画書の作成

インタビュー結果から `docs/project/{slug}.md` を作成：

```bash
# slug の生成: プロジェクト名をケバブケースに変換
# 例: "CI/CD改善" → "ci-cd-improvement"
```

テンプレート（`./template.md` を参照）を使用して計画書を生成。

#### ステップ3: GitHub Project の作成

```bash
# Project 作成
gh project create --title "{プロジェクト名}" --owner @me

# 作成結果の確認
gh project list --owner @me --format json | jq '.projects[0]'
```

#### ステップ4: Issue の作成と登録

タスクを Issue として作成し、Project に追加：

```bash
# Issue 作成（HEREDOC形式）
gh issue create \
  --title "[{カテゴリ}] {タイトル}" \
  --body "$(cat <<'EOF'
## 概要

{タスクの概要}

## 受け入れ条件

- [ ] {条件1}
- [ ] {条件2}

## 関連

- 計画書: docs/project/{slug}.md
- GitHub Project: #{project_number}
EOF
)" \
  --label "enhancement"

# Project に追加
gh project item-add {project_number} --owner @me --url {issue_url}
```

#### ステップ5: 完了レポートの表示

```
================================================================================
                    プロジェクト作成完了
================================================================================

## プロジェクト情報
- 名前: {project_name}
- モード: 軽量プロジェクト
- 計画書: docs/project/{slug}.md

## GitHub Project
- 番号: #{project_number}
- URL: {project_url}

## 作成した Issue
| # | タイトル | ラベル |
|---|---------|--------|
| #{number} | {title} | {labels} |

## 次のステップ
1. 計画書の内容を確認
2. /plan-worktrees #{project_number} で並列開発計画を確認
3. /issue-implement #{issue_number} でタスクを実装

================================================================================
```

---

### パッケージ開発モード

#### ステップ1: project.md の読み込み

```bash
# 指定されたパスから project.md を読み込む
Read @src/{package}/docs/project.md
```

#### ステップ2: インタビュー（要件詳細化）

最低5回の質問で要件を詳細化：

- パッケージの主要ユースケース
- 想定ユーザー
- パフォーマンス要件
- 互換性要件
- 制約事項

#### ステップ3: LRD の作成

`prd-writing` スキルを使用して Library Requirements Document を作成：

```
Task(subagent_type="functional-design-writer", ...)
```

成果物: `src/{package}/docs/library-requirements.md`

#### ステップ4: 設計ドキュメントの作成

サブエージェントを使用して以下を自動生成：

| エージェント | 成果物 |
|-------------|--------|
| `functional-design-writer` | `functional-design.md` |
| `architecture-design-writer` | `architecture.md` |
| `repository-structure-writer` | `repository-structure.md` |
| `development-guidelines-writer` | `development-guidelines.md` |
| `glossary-writer` | `glossary.md` |

#### ステップ5: タスク分解

`task-decomposer` エージェントでタスクを分解：

```
Task(subagent_type="task-decomposer", ...)
```

成果物: `src/{package}/docs/tasks.md`

#### ステップ6: GitHub Project への登録

軽量モードと同様に Issue を作成し、Project に登録。

#### ステップ7: 完了レポートの表示

```
================================================================================
                    開発プロジェクト作成完了
================================================================================

## プロジェクト情報
- パッケージ: {package_name}
- モード: パッケージ開発

## 作成/更新したドキュメント
- src/{package}/docs/library-requirements.md
- src/{package}/docs/functional-design.md
- src/{package}/docs/architecture.md
- src/{package}/docs/repository-structure.md
- src/{package}/docs/development-guidelines.md
- src/{package}/docs/glossary.md
- src/{package}/docs/tasks.md

## GitHub Project
- 番号: #{project_number}
- URL: {project_url}

## 次のステップ
1. ドキュメントの内容を確認
2. /plan-worktrees #{project_number} で並列開発計画を確認
3. /issue-implement #{issue_number} でタスクを実装

================================================================================
```

## リソース

### ./template.md

軽量プロジェクト用の `project.md` テンプレート。

## エラーハンドリング

### GitHub 認証エラー

```bash
# 対処法
gh auth login
gh auth refresh -s project
```

### Project 作成失敗

```bash
# 原因確認
gh project list --owner @me

# 権限確認
gh auth status
```

### project.md が見つからない

- パッケージ開発の場合: `/new-package` を先に実行
- 軽量プロジェクトの場合: 引数なしで `/new-project` を実行

## 完了条件

- [ ] インタビューが完了している
- [ ] 計画書（project.md）が作成されている
- [ ] GitHub Project が作成されている
- [ ] Issue が登録されている
- [ ] 完了レポートが表示されている

## 関連コマンド・スキル

- `/new-package`: パッケージディレクトリの作成（パッケージ開発モードの前提）
- `/issue`: Issue の追加作成
- `/plan-worktrees`: 並列開発計画の表示
- `/issue-implement`: Issue の自動実装
- `project-management`: プロジェクト整合性検証（/project-refine）

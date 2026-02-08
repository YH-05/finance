# project.md テンプレート

以下のテンプレートを使用して `docs/project/project-{N}/project.md` を作成します。

```markdown
# {プロジェクト名}

**作成日**: {今日の日付}
**ステータス**: 計画中
**タイプ**: {project_type}
**GitHub Project**: [#{project_number}]({project_url})

## 背景と目的

### 背景

{リサーチで判明した背景情報}

### 目的

{プロジェクトの目的}

### 成功基準

- [ ] {測定可能な基準1}
- [ ] {測定可能な基準2}

## リサーチ結果

### 既存パターン

{project-researcher が発見した既存の類似実装・パターン}

### 参考実装

| ファイル | 説明 |
|---------|------|
| {パス1} | {参考にすべき点} |
| {パス2} | {参考にすべき点} |

### 技術的考慮事項

{リサーチで判明した制約・注意点}

## 実装計画

### アーキテクチャ概要

{project-planner が策定した設計概要}

### ファイルマップ

| 操作 | ファイルパス | 説明 |
|------|------------|------|
| 新規作成 | {パス} | {説明} |
| 変更 | {パス} | {変更内容} |

### リスク評価

| リスク | 影響度 | 対策 |
|--------|--------|------|
| {リスク1} | 高/中/低 | {対策} |

## タスク一覧

### Wave 1（並行開発可能）

- [ ] {タスク1}
  - Issue: [#{番号}]({URL})
  - ステータス: todo
  - 見積もり: {時間}

### Wave 2（Wave 1 完了後）

- [ ] {タスク2}
  - Issue: [#{番号}]({URL})
  - ステータス: todo
  - 依存: #{先行Issue番号}
  - 見積もり: {時間}

### Wave 3（Wave 2 完了後）

- [ ] {タスク3}
  - Issue: [#{番号}]({URL})
  - ステータス: todo
  - 依存: #{先行Issue番号}
  - 見積もり: {時間}

## 依存関係図

```mermaid
graph TD
    A[#{番号} タスク1] --> C[#{番号} タスク3]
    B[#{番号} タスク2] --> C
```

---

**最終更新**: {今日の日付}
```

## テンプレート変数

| 変数 | 説明 | 生成元 |
|------|------|--------|
| `{プロジェクト名}` | プロジェクト名 | HF0 |
| `{project_type}` | プロジェクトタイプ | Phase 0 |
| `{project_number}` | GitHub Project 番号 | Phase 4 |
| `{project_url}` | GitHub Project URL | Phase 4 |
| リサーチ結果系 | 既存パターン、参考実装 | Phase 1 (research-findings.json) |
| 実装計画系 | 設計、ファイルマップ、リスク | Phase 2 (implementation-plan.json) |
| タスク系 | Wave分類、依存関係、見積もり | Phase 3 (task-breakdown.json) |
| Issue リンク | `#{番号}` と URL | Phase 4 |

## project 番号の採番

既存の `docs/project/project-{N}/` を Glob で走査し、最大番号 + 1 を使用：

```bash
ls -d docs/project/project-* | sort -t- -k2 -n | tail -1
```

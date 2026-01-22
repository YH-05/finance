---
description: GitHub Issue とタスクの管理・同期を行う
---

# /issue - Issue とタスク管理

> **役割の明確化**: このコマンドは **Issue 管理とタスク分解** に特化しています。
>
> - 開発キックオフ・設計ドキュメント作成 → `/new-project`
> - 品質チェック・自動修正 → `/ensure-quality`

**目的**: GitHub Issues と project.md の双方向同期、タスク分解、類似 Issue の判定、クイックチケット発行

## コマンド構文

```bash
# クイックチケット発行モード（新規）
/issue --add <要件を自然言語で簡単に記述>

# パッケージ開発モード
/issue @src/<library_name>/docs/project.md

# 軽量プロジェクトモード
/issue @docs/project/<project-slug>.md
```

## スキルの呼び出し

このコマンドは **issue-creation** スキルを使用します。

**スキル情報**:

- **スキル名**: issue-creation
- **配置先**: `.claude/skills/issue-creation/`
- **主な機能**:
  - クイック発行モード: 自然言語から素早く Issue を作成
  - パッケージ開発モード: project.md と連携したタスク管理
  - 軽量プロジェクトモード: GitHub Project との双方向同期
  - 類似性判定: 既存 Issue との重複チェック
  - タスク分解: 大きな要件を実装可能なサイズに分割

## 処理フロー

```
/issue [引数]
    │
    └─ Skill ツールで issue-creation スキルを呼び出し
        │
        ├─ 引数解析
        │   ├─ --add <要件> → クイック発行モード
        │   ├─ @src/.../project.md → パッケージ開発モード
        │   └─ @docs/.../xxx.md → 軽量プロジェクトモード
        │
        ├─ モードに応じた処理
        │   ├─ クイック発行: ヒアリング → Issue 作成
        │   ├─ パッケージ開発: task-decomposer → 同期
        │   └─ 軽量プロジェクト: GitHub Project 連携
        │
        └─ 結果表示
```

## 引数の渡し方

コマンドの引数は **$ARGUMENTS** プレースホルダーでスキルに渡されます。

**例**:

- `/issue --add ログイン機能の追加` → `$ARGUMENTS = "--add ログイン機能の追加"`
- `/issue @src/market_analysis/docs/project.md` → `$ARGUMENTS = "@src/market_analysis/docs/project.md"`

## 関連スキル

| スキル | 用途 |
|--------|------|
| issue-creation | Issue 作成・タスク分解（このコマンド） |
| issue-implementation | Issue の自動実装 |
| issue-refinement | Issue のブラッシュアップ |
| issue-sync | コメントからの同期 |

## 詳細情報

詳細なガイドラインとテンプレートは以下のスキルリソースを参照:

- `.claude/skills/issue-creation/SKILL.md` - スキル定義
- `.claude/skills/issue-creation/guide.md` - 詳細ガイド
- `.claude/skills/issue-creation/template.md` - Issue テンプレート

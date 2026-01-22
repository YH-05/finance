---
description: GitHub Issue の内容をブラッシュアップして更新する
---

# /issue-refine - Issue ブラッシュアップ

> **役割の明確化**: このコマンドは **既存 Issue の内容改善** に特化しています。
>
> - 新規 Issue 作成・タスク分解 → `/issue`
> - コメントからの進捗同期 → `/sync-issue`

**目的**: 既存の GitHub Issue を明確化・具体化し、テンプレートに準拠した形式に改善する

## コマンド構文

```bash
# 単一 Issue のブラッシュアップ
/issue-refine 123

# 複数 Issue のブラッシュアップ
/issue-refine 123 124 125

# project.md に紐づく全 Issue をブラッシュアップ
/issue-refine @src/<library_name>/docs/project.md
/issue-refine @docs/project/<project-slug>.md
```

## スキルの呼び出し

このコマンドは **issue-refinement** スキルを使用します。

**スキル情報**:

- **スキル名**: issue-refinement
- **配置先**: `.claude/skills/issue-refinement/`
- **主な機能**:
  - Issue 内容の改善: 曖昧な表現を具体的に
  - 8項目の詳細確認: ユーザーへの体系的なヒアリング
  - 受け入れ条件の測定可能化: 曖昧な条件を具体的な基準に変換
  - テンプレート準拠: 標準フォーマットへの整形

## 処理フロー

```
/issue-refine {number|path}
    │
    └─ Skill ツールで issue-refinement スキルを呼び出し
        │
        ├─ ステップ 1: Issue 情報取得
        │
        ├─ ステップ 2: 改善対象選択
        │   ├─ 本文全体
        │   ├─ 受け入れ条件のみ
        │   └─ タイトルと概要
        │
        ├─ ステップ 2.5: 8項目の詳細確認
        │   └─ AskUserQuestion でユーザーにヒアリング
        │
        ├─ ステップ 3: 改善案生成
        │
        ├─ ステップ 4: 差分表示・確認
        │
        └─ ステップ 5: Issue 更新
```

## 8項目の詳細確認

Issue の不明点・曖昧な点を明確化するため、以下の8項目を順番に確認:

1. **背景・目的**: なぜこの機能/修正が必要か
2. **実装スコープ**: 何をやる/やらないか
3. **連携・依存関係**: 他機能との関係
4. **優先度・期限**: 緊急度と時間軸
5. **ユースケース**: 具体的な使用シナリオ
6. **受け入れ条件詳細**: 完了判断基準
7. **実装時の注意点**: 技術的制約
8. **関連 Issue**: 関連情報

## 引数の渡し方

コマンドの引数は **$ARGUMENTS** プレースホルダーでスキルに渡されます。

**例**:

- `/issue-refine 123` → `$ARGUMENTS = "123"`
- `/issue-refine 123 124 125` → `$ARGUMENTS = "123 124 125"`
- `/issue-refine @src/market_analysis/docs/project.md` → `$ARGUMENTS = "@src/market_analysis/docs/project.md"`

## 関連スキル

| スキル | 用途 |
|--------|------|
| issue-creation | Issue 作成・タスク分解 |
| issue-implementation | Issue の自動実装 |
| issue-refinement | Issue のブラッシュアップ（このコマンド） |
| issue-sync | コメントからの同期 |

## 詳細情報

詳細なガイドラインとテンプレートは以下のスキルリソースを参照:

- `.claude/skills/issue-refinement/SKILL.md` - スキル定義
- `.claude/skills/issue-refinement/guide.md` - 詳細ガイド（8項目確認フロー）
- `.claude/skills/issue-refinement/template.md` - 改善用テンプレート

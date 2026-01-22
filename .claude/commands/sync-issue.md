---
description: GitHub Issue のコメントから進捗・タスク・仕様変更を同期
---

# /sync-issue - コメント同期

> **役割の明確化**: このコマンドは **Issue コメントからの情報抽出と同期** に特化しています。
>
> - 新規 Issue 作成・タスク分解 → `/issue`
> - 品質チェック・自動修正 → `/ensure-quality`

**目的**: GitHub Issue のコメントから進捗情報・新規サブタスク・仕様変更を抽出し、`project.md` と GitHub Project の両方に反映する

## コマンド構文

```bash
# 単一 Issue 同期
/sync-issue #123

# 複数 Issue 同期
/sync-issue #123 #124 #125

# project.md に紐づく全 Issue 同期
/sync-issue @src/<library_name>/docs/project.md
/sync-issue @docs/project/<project-slug>.md

# 特定期間のコメントのみ対象
/sync-issue #123 --since="2026-01-01"
```

## スキルの呼び出し

このコマンドは **issue-sync** スキルを使用します。

**スキル情報**:

- **スキル名**: issue-sync
- **配置先**: `.claude/skills/issue-sync/`
- **主な機能**:
  - コメント解析: AI によるコメントからの情報抽出
  - 確信度ベース確認: 自動適用と手動確認の適切な使い分け
  - 三方向同期: Issue・project.md・GitHub Project の同期
  - ステータス更新: 進捗に応じた自動ステータス更新

## 処理フロー

```
/sync-issue #123
    │
    └─ Skill ツールで issue-sync スキルを呼び出し
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

## 確信度ベース確認

| レベル | 範囲 | アクション |
|--------|------|-----------|
| HIGH | 0.80+ | 自動適用 |
| MEDIUM | 0.70-0.79 | 適用、確認なし |
| LOW | < 0.70 | ユーザー確認必須 |

**確認必須ケース**:
- ステータスダウングレード（done → in_progress）
- 受け入れ条件の削除
- 複数の矛盾するステータス変更

## 引数の渡し方

コマンドの引数は **$ARGUMENTS** プレースホルダーでスキルに渡されます。

**例**:

- `/sync-issue #123` → `$ARGUMENTS = "#123"`
- `/sync-issue #123 #124 #125` → `$ARGUMENTS = "#123 #124 #125"`
- `/sync-issue @docs/project/research-agent.md` → `$ARGUMENTS = "@docs/project/research-agent.md"`
- `/sync-issue #123 --since="2026-01-01"` → `$ARGUMENTS = "#123 --since=\"2026-01-01\""`

## サブエージェント連携

| エージェント | 用途 |
|--------------|------|
| comment-analyzer | コメント解析、進捗抽出 |
| task-decomposer | 同期実行、project.md 更新 |

## 関連スキル

| スキル | 用途 |
|--------|------|
| issue-creation | Issue 作成・タスク分解 |
| issue-implementation | Issue の自動実装 |
| issue-refinement | Issue のブラッシュアップ |
| issue-sync | コメントからの同期（このコマンド） |

## 詳細情報

詳細なガイドラインとテンプレートは以下のスキルリソースを参照:

- `.claude/skills/issue-sync/SKILL.md` - スキル定義
- `.claude/skills/issue-sync/guide.md` - 詳細ガイド（競合解決ルール）
- `.claude/skills/issue-sync/template.md` - 同期レポートテンプレート

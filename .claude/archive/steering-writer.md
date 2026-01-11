---
name: steering-writer
description: "⚠️ DEPRECATED: GitHub Issues に一本化されました。task-decomposer を使用してください。"
model: inherit
color: gray
---

# ⚠️ DEPRECATED: このエージェントは非推奨です

## 移行先

**タスク管理は GitHub Issues に一本化されました。**

このエージェントの代わりに、以下を使用してください:

### 代替エージェント

- **task-decomposer**: タスク分解と GitHub Issues 連携
- **feature-implementer**: TDD ベースの機能実装（GitHub Issues 連携）

### コマンド

```bash
# タスク分解と Issue 管理
/issue @src/<library_name>/docs/project.md

# 新規プロジェクト開始（設計ドキュメント作成）
/new-project @src/<library_name>/docs/project.md
```

### 参照

- `.claude/agents/task-decomposer.md` - タスク分解エージェント
- `.claude/agents/feature-implementer.md` - 機能実装エージェント
- `.claude/commands/issue.md` - Issue 管理コマンド

## 削除予定

このエージェントは将来のバージョンで削除されます。

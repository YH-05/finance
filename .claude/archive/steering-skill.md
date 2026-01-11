---
name: steering
description: "⚠️ DEPRECATED: GitHub Issues に一本化されました。このスキルは使用しないでください。"
allowed-tools: Read
---

# ⚠️ DEPRECATED: このスキルは非推奨です

## 移行先

**タスク管理は GitHub Issues に一本化されました。**

### 以前の方法（非推奨）

```
src/<package_name>/docs/.steering/YYYYMMDD_xxx/
├── requirements.md
├── design.md
└── tasklist.md
```

### 新しい方法（推奨）

1. **機能要望**: GitHub Issue テンプレート `feature_request.yml` を使用
2. **実装タスク**: GitHub Issue テンプレート `implementation_task.yml` を使用
3. **タスク管理**: `/issue @src/<library_name>/docs/project.md` コマンドを使用

### コマンド

```bash
# Issue 管理・同期
/issue @src/<library_name>/docs/project.md

# 機能実装（GitHub Issues 連携）
feature-implementer サブエージェントを使用
```

### 参照

- `.github/ISSUE_TEMPLATE/feature_request.yml` - 機能要望テンプレート
- `.github/ISSUE_TEMPLATE/implementation_task.yml` - 実装タスクテンプレート
- `.claude/commands/issue.md` - Issue 管理コマンド

## 削除予定

このスキルと関連ファイルは将来のバージョンで削除されます。
早めに GitHub Issues への移行を完了してください。

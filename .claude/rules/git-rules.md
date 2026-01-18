# Git 運用ルール

## ブランチ戦略

```
main (本番環境)
└── develop (開発・統合環境) ※必要に応じて
    ├── feature/* (新機能開発)
    ├── fix/* (バグ修正)
    ├── refactor/* (リファクタリング)
    ├── docs/* (ドキュメント)
    ├── test/* (テスト追加)
    └── release/* (リリース準備)
```

## ブランチ名規則

- `feature/` - 新機能開発
- `fix/` - バグ修正
- `refactor/` - リファクタリング
- `docs/` - ドキュメント
- `test/` - テスト追加
- `release/` - リリース準備

## コミットメッセージ（Conventional Commits）

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Type 一覧

| Type | 説明 |
|------|------|
| feat | 新機能 (minor version up) |
| fix | バグ修正 (patch version up) |
| docs | ドキュメント |
| style | フォーマット (コードの動作に影響なし) |
| refactor | リファクタリング |
| perf | パフォーマンス改善 |
| test | テスト追加・修正 |
| build | ビルドシステム |
| ci | CI/CD設定 |
| chore | その他 (依存関係更新など) |
| BREAKING CHANGE | 破壊的変更 (major version up) |

### コミットメッセージ例

```
feat(task): 優先度設定機能を追加

ユーザーがタスクに優先度(高/中/低)を設定できるようになりました。

実装内容:
- Taskモデルにpriorityフィールド追加
- CLI に --priority オプション追加

Closes #123
```

## PR / Issue 規則

- **言語**: タイトル・本文は**日本語**で記述
- **ラベル**: `enhancement` | `bug` | `refactor` | `documentation` | `test`

### PRテンプレート

```markdown
## 概要
- <変更点1>
- <変更点2>

## テストプラン
- [ ] make check-all が成功することを確認
```

### Issueテンプレート

```markdown
## 概要
[機能・問題の概要]

## 詳細
[詳細な説明]

## 受け入れ条件
- [ ] [条件1]
```

## pre-push hook

プロジェクト整合性チェック（循環依存・ステータス不整合を検出）

- Critical エラー → push をブロック
- Warning → 警告表示（`--strict` でブロック）
- スキップ: `git push --no-verify`

## GitHub Projects 自動化

- PR作成時: Issue → In Progress
- PRマージ時: Issue → Done
- 詳細: `docs/github-projects-automation.md`

## 必須コマンド

```bash
# 品質チェック（PRマージ前に必須）
make check-all          # 全チェック（format, lint, typecheck, test）

# Git操作
/commit-and-pr          # PR作成
/merge-pr <number>      # PRマージ
```

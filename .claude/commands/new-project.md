---
description: 開発プロジェクトを開始。パッケージ開発または軽量プロジェクトに対応
skill: project-management
---

# プロジェクト開始コマンド

このコマンドは project-management スキルを使用してプロジェクトを作成します。

## 実行方法

```bash
# モード1: パッケージ開発（設計ドキュメント付き）
/new-project @src/<library_name>/docs/project.md

# モード2: 軽量プロジェクト（GitHub Project中心）
/new-project "プロジェクト名または説明"
/new-project --interactive
```

## モード

| モード | 用途 | 引数 |
|--------|------|------|
| **パッケージ開発** | LRD→設計→実装の正式フロー | `@src/<lib>/docs/project.md` |
| **軽量プロジェクト** | エージェント開発、ワークフロー改善等 | `"プロジェクト名"` or `--interactive` |

## 処理フロー

### ステップ 0: 引数解析とモード判定

引数を解析してモードを判定:

```
引数の形式を確認:
├─ 引数なし → エラー表示
├─ @ で始まる引数:
│   ├─ @src/*/docs/project.md パターンに一致 → パッケージ開発モード
│   └─ パターン不一致 → エラー表示
├─ --interactive → 軽量モード（対話的に名前を決定）
└─ その他の文字列 → 軽量モード（引数をプロジェクト名として使用）
```

### パッケージ開発モード

```
project.md 読み込み → インタビュー → LRD作成 → 設計ドキュメント
    → タスク分解 → GitHub Project 登録
```

**サブエージェント実行順序:**
1. インタビュー → project.md 更新
2. LRD 作成・承認（prd-writing スキル）
3. functional-design-writer
4. architecture-design-writer
5. repository-structure-writer
6. development-guidelines-writer
7. glossary-writer
8. task-decomposer

### 軽量プロジェクトモード

```
インタビュー（10-12問） → 計画書作成 → GitHub Project 作成
    → Issue 登録 → 完了レポート
```

**インタビューフェーズ:**
- フェーズ1: 背景理解（質問1-3）
- フェーズ2: 目標設定（質問4-6）
- フェーズ3: スコープ定義（質問7-9）
- フェーズ4: 技術詳細（質問10-12）

## 詳細ガイド

詳細な処理手順、テンプレート、エラーハンドリングについては project-management スキルを参照:

- **SKILL.md**: `.claude/skills/project-management/SKILL.md`
- **ガイド**: `.claude/skills/project-management/guide.md`
- **テンプレート**: `.claude/skills/project-management/template.md`

## 関連コマンド

- `/new-package`: パッケージディレクトリの作成（/new-project の前提）
- `/project-refine`: プロジェクト整合性検証と再構成
- `/issue`: GitHub Issue と project.md の双方向同期
- `/issue-implement`: Issue から PR 作成までの自動化

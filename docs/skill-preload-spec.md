# スキルプリロード仕様書

## 概要

サブエージェントのフロントマターに `skills:` フィールドを使用することで、起動時にスキルコンテンツをサブエージェントのコンテキストに自動注入できます。この仕様書では、スキルプリロード機構の詳細を定義します。

## フロントマター `skills:` フィールドの仕様

### 基本構文

```yaml
---
name: agent-name
description: エージェントの説明
skills:
  - skill-name-1
  - skill-name-2
  - skill-name-3
allowed-tools: Read, Write, Bash
---
```

### フィールド定義

| フィールド | 必須 | 型 | 説明 |
|-----------|------|-----|------|
| `skills` | オプション | 配列（string[]） | プリロードするスキル名のリスト |

### スキル名の形式

- **kebab-case** で記述（例: `coding-standards`, `tdd-development`）
- スキルディレクトリ名と一致させる（例: `.claude/skills/coding-standards/`）
- 大文字小文字を区別する

### 配列の記述方法

```yaml
# YAML リスト形式（推奨）
skills:
  - coding-standards
  - tdd-development
  - error-handling

# インラインリスト形式（短い場合）
skills: [coding-standards, tdd-development]
```

---

## スキルコンテンツの注入タイミング

### 注入タイミング

| タイミング | 説明 |
|-----------|------|
| サブエージェント起動時 | `Task` ツールでサブエージェントが起動される際に注入 |
| フロントマター解析後 | フロントマターが解析された直後 |
| プロンプト処理前 | サブエージェントのメインプロンプトが処理される前 |

### 注入プロセス

```
1. Task ツールがサブエージェントを起動
2. サブエージェントのフロントマターを解析
3. skills: フィールドを検出
4. 各スキル名に対応する SKILL.md を検索
5. スキルコンテンツをコンテキストに注入
6. サブエージェントのメインプロンプトを実行
```

### 注入内容

`skills:` フィールドで指定されたスキルの **完全なコンテンツ** が注入されます：

- 各スキルの `SKILL.md` の全内容
- フロントマターを含む（name, description, allowed-tools）
- リソースファイル（guide.md, template.md 等）は**含まれない**

**重要**: スキルの `SKILL.md` 内で `./guide.md` などを参照している場合、サブエージェントは必要に応じて `Read` ツールでリソースを読み込む必要があります。

---

## スキル参照の解決方法

### 参照解決の優先順位

スキル名は以下の順序で解決されます：

| 優先度 | 検索場所 | パス |
|--------|---------|------|
| 1 | プロジェクトスキル | `.claude/skills/{skill-name}/SKILL.md` |
| 2 | ユーザースキル | `~/.claude/skills/{skill-name}/SKILL.md` |
| 3 | プラグインスキル | インストール済みプラグインから |

### 解決プロセス

```
スキル名: "coding-standards"

1. .claude/skills/coding-standards/SKILL.md を検索
   → 存在すれば使用
2. ~/.claude/skills/coding-standards/SKILL.md を検索
   → 存在すれば使用
3. プラグインから検索
   → 存在すれば使用
4. 見つからない場合 → エラー
```

### 複数スキルの解決順序

```yaml
skills:
  - coding-standards    # 1番目に解決・注入
  - tdd-development     # 2番目に解決・注入
  - error-handling      # 3番目に解決・注入
```

スキルは配列の順序で解決され、同じ順序でコンテキストに注入されます。

---

## スキル継承ルール

### 重要な特性

| 特性 | 説明 |
|------|------|
| **継承なし** | サブエージェントは親の会話からスキルを継承しない |
| **明示的指定必須** | 必要なスキルは必ず `skills:` フィールドで指定 |
| **スコープ限定** | プリロードされたスキルはそのサブエージェント内のみで有効 |

### 継承しない理由

- **予測可能性**: エージェントの動作が明示的な設定のみに依存
- **独立性**: 各サブエージェントが独立して機能
- **デバッグ容易性**: 問題発生時の原因特定が容易

### 正しいパターン

```yaml
# ✅ 正しい: 必要なスキルを明示的に指定
---
name: feature-implementer
skills:
  - coding-standards
  - tdd-development
  - error-handling
---
```

### 誤ったパターン（期待どおり動作しない）

```yaml
# ❌ 誤り: 親が coding-standards を使用していても、
#         子エージェントには自動的に継承されない
---
name: child-agent
skills:
  # coding-standards が必要な場合、ここに明示的に指定する必要がある
  - tdd-development
---
```

---

## エラーハンドリング

### エラーパターン

| エラー | 原因 | 対処法 |
|--------|------|--------|
| スキル未発見 | 指定されたスキル名が存在しない | スキル名のスペルを確認、スキルディレクトリを確認 |
| SKILL.md 未発見 | スキルディレクトリに SKILL.md がない | SKILL.md を作成 |
| 構文エラー | YAML フロントマターの構文エラー | YAML 構文を修正 |
| 循環参照 | スキル A がスキル B を参照し、B が A を参照 | スキル間の依存関係を整理 |

### スキル未発見エラー

```
エラー: スキル 'coding-standars' が見つかりません

解決方法:
1. スキル名のスペルを確認してください
   - 正: coding-standards
   - 誤: coding-standars

2. スキルディレクトリの存在を確認:
   .claude/skills/coding-standards/SKILL.md

3. 利用可能なスキル一覧:
   ls .claude/skills/
```

### SKILL.md 未発見エラー

```
エラー: スキル 'my-skill' のエントリーポイントが見つかりません
       .claude/skills/my-skill/SKILL.md が存在しません

解決方法:
1. SKILL.md ファイルを作成してください:
   .claude/skills/my-skill/SKILL.md

2. テンプレートを使用:
   cp template/skill/SKILL.md .claude/skills/my-skill/SKILL.md
```

### 構文エラー

```
エラー: エージェント 'my-agent' のフロントマターが不正です
       Line 5: 'skills' フィールドの値が配列ではありません

解決方法:
# 誤り
skills: coding-standards

# 正しい形式
skills:
  - coding-standards
```

---

## 使用例

### 例1: 機能実装エージェント

```yaml
---
name: feature-implementer
description: TDDで機能を実装するサブエージェント
skills:
  - coding-standards
  - tdd-development
  - error-handling
allowed-tools: Read, Edit, Bash, Grep, Task
---

# 機能実装エージェント

プリロードされたスキルの規約とパターンに従って実装してください。

## 処理フロー

1. coding-standards の型ヒント・命名規則に従う
2. tdd-development の Red → Green → Refactor サイクルを実行
3. error-handling のパターンでエラー処理を実装
```

### 例2: テストエージェント

```yaml
---
name: test-planner
description: テスト計画を策定するサブエージェント
skills:
  - tdd-development
  - coding-standards
allowed-tools: Read, Write, Glob, Grep
---

# テスト計画エージェント

プリロードされた TDD 開発スキルに基づいてテスト計画を策定します。

## プリロードされたスキルの活用

- **tdd-development**: テスト種別、命名規則、ファイル配置
- **coding-standards**: テストコードのスタイル規約
```

### 例3: コードレビューエージェント

```yaml
---
name: quality-checker
description: コード品質をチェックするサブエージェント
skills:
  - coding-standards
allowed-tools: Read, Bash, Grep
---

# 品質チェックエージェント

coding-standards スキルの規約に基づいて品質をチェックします。
```

### 例4: プロジェクト管理エージェント（スキルなし）

```yaml
---
name: task-manager
description: タスク管理を行うサブエージェント
allowed-tools: Read, Write, Bash
---

# タスク管理エージェント

このエージェントは特定のスキルをプリロードせず、
一般的なタスク管理機能を提供します。
```

---

## スキル設計のベストプラクティス

### プリロード対象スキルの設計

プリロードされることを想定したスキルは以下を考慮：

1. **自己完結性**: SKILL.md 単体で主要な情報が得られる
2. **コンパクトさ**: 過度に長くない（コンテキストを圧迫しない）
3. **参照明示**: 追加情報は `./guide.md` などへの参照を明記

### スキル粒度のガイドライン

| 粒度 | 用途 | 例 |
|------|------|-----|
| 粗粒度 | 広範なドメインをカバー | `coding-standards` |
| 中粒度 | 特定の機能領域 | `tdd-development` |
| 細粒度 | 特定のタスク | `type-hint-converter` |

### 推奨される skills 数

| 数 | 評価 | 説明 |
|----|------|------|
| 0-2 | 推奨 | コンテキスト効率が高い |
| 3-4 | 許容 | 必要に応じて使用 |
| 5+ | 非推奨 | コンテキストを圧迫する可能性 |

---

## 関連ドキュメント

### 内部参照

- スキル標準構造テンプレート: `template/skill/SKILL.md`
- エージェントテンプレート: `.claude/skills/agent-expert/template.md`
- 計画書: `docs/plan/2026-01-21_System-Update-Implementation.md`

### 外部参照

- [Claude Code 公式ドキュメント: サブエージェント](https://code.claude.com/docs/ja/sub-agents)

---

## 変更履歴

| 日付 | バージョン | 変更内容 |
|------|-----------|---------|
| 2026-01-22 | 1.0.0 | 初版作成 |

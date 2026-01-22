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

## エージェントフロントマターでの `skills:` 記述パターン

### 基本パターン

```yaml
---
name: agent-name
description: エージェントの説明
skills:
  - skill-name-1
  - skill-name-2
allowed-tools: Read, Write, Bash
---
```

### パターン1: 単一スキル参照

コード品質チェック等、単一の専門性に特化したエージェント：

```yaml
---
name: quality-checker
description: コード品質をチェックするサブエージェント
skills:
  - coding-standards
allowed-tools: Read, Bash, Grep
---
```

### パターン2: 複数スキル参照（関連スキルの組み合わせ）

TDD実装等、複数の知識領域を必要とするエージェント：

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
```

### パターン3: 専門ドメイン＋共通スキル

専門領域と共通規約の両方を必要とするエージェント：

```yaml
---
name: test-planner
description: テスト計画を策定するサブエージェント
skills:
  - tdd-development
  - coding-standards
allowed-tools: Read, Write, Glob, Grep
---
```

### パターン4: スキルなし

特定のスキルを必要としない汎用エージェント：

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

## 複数スキル参照時の順序・優先度

### 配列順序の重要性

`skills:` フィールドの配列順序は、スキルの**注入順序**を決定します：

```yaml
skills:
  - coding-standards    # 1番目に注入
  - tdd-development     # 2番目に注入
  - error-handling      # 3番目に注入
```

### 推奨される順序

| 位置 | 内容 | 理由 |
|------|------|------|
| 1番目 | 最も基本的なスキル | コンテキストの土台となる |
| 2番目 | 主要な専門スキル | タスクの中心となる知識 |
| 3番目以降 | 補助的なスキル | 追加の参照情報 |

### 順序決定の原則

**原則1: 汎用→特化**

```yaml
# ✅ 推奨: 汎用的なスキルから特化したスキルへ
skills:
  - coding-standards    # 汎用（コーディング全般）
  - tdd-development     # 特化（テスト駆動開発）
```

**原則2: 依存関係順**

スキルAがスキルBの知識を前提とする場合、Aを後に配置：

```yaml
# ✅ 推奨: error-handling は coding-standards の知識を前提
skills:
  - coding-standards    # 前提知識
  - error-handling      # 前提知識を活用
```

**原則3: 参照頻度順**

より頻繁に参照されるスキルを先に配置：

```yaml
# ✅ 推奨: TDDエージェントでは tdd-development を先に
skills:
  - tdd-development     # 主要（高頻度参照）
  - coding-standards    # 補助（低頻度参照）
```

### 順序が影響するケース

1. **競合する定義**: 同一概念に対して異なる定義がある場合、後のスキルが優先
2. **コンテキスト構築**: 先に注入されたスキルがコンテキストの基盤となる
3. **プロンプト長**: 先に注入されたスキルが長い場合、後のスキルの影響が相対的に低下

### 注意事項

- スキル間に明示的な依存関係がある場合、依存されるスキルを先に配置
- 競合を避けるため、同一領域の複数スキルの同時参照は避ける
- 3-4個を超えるスキルの同時参照は推奨しない（コンテキスト効率の低下）

---

## スキルとエージェントの責務分担ガイドライン

### 責務の違い

| 観点 | スキル | エージェント |
|------|--------|------------|
| **役割** | 知識・規約・パターンの提供 | タスクの実行・オーケストレーション |
| **内容** | What（何をすべきか）、Why（なぜそうすべきか） | How（どう実行するか）、When（いつ実行するか） |
| **更新頻度** | 低（規約・ベストプラクティスの変更時） | 高（ワークフロー改善時） |
| **依存関係** | 他スキルへの参照なし（自己完結） | 複数スキルを参照可能 |

### スキルに含めるべき内容

```yaml
スキルの内容:
  - コーディング規約・ベストプラクティス
  - 命名規則・フォーマット規約
  - パターン・テンプレート
  - チェックリスト・検証基準
  - 参考例・アンチパターン
```

**例: `coding-standards` スキル**

```markdown
# コーディング規約スキル

## 型ヒント（Python 3.12+ / PEP 695）
- `list[str]` を使用（`List[str]` ではなく）
- ジェネリクスは `def first[T](items: list[T]) -> T | None:`

## 命名規則
- 変数: snake_case
- クラス: PascalCase
- 定数: UPPER_SNAKE

## Docstring
- NumPy形式を使用
- Parameters, Returns, Raises を必須に
```

### エージェントに含めるべき内容

```yaml
エージェントの内容:
  - 処理フロー（ステップバイステップ）
  - 入力/出力の定義
  - ツールの使用方法
  - 条件分岐・エラーハンドリング
  - 完了条件・チェックポイント
```

**例: `feature-implementer` エージェント**

```markdown
# 機能実装エージェント

## 処理フロー

1. GitHub Issue を読み込み
2. TDDサイクルを実行
   - 🔴 Red: テスト作成
   - 🟢 Green: 最小実装
   - 🔵 Refactor: 整理
3. Issue のチェックボックスを更新
4. ループ継続

## ツールの使用

```bash
gh issue view <number> --json body
```
```

### 責務分担の判断基準

以下の質問で責務を判断：

| 質問 | スキルに含める | エージェントに含める |
|------|--------------|-------------------|
| 複数のエージェントで共有される知識か？ | ✅ | ❌ |
| 特定のワークフローに依存するか？ | ❌ | ✅ |
| 「規約」「ルール」「パターン」に関するか？ | ✅ | ❌ |
| 「実行」「処理」「フロー」に関するか？ | ❌ | ✅ |
| 変更頻度が低いか？ | ✅ | ❌ |

### 分担パターン

**パターンA: 規約参照型**

```
スキル: コーディング規約、命名規則、Docstring形式
    ↓ 参照
エージェント: 実装時に規約を適用、違反をチェック
```

**パターンB: テンプレート活用型**

```
スキル: テストテンプレート、コード例
    ↓ 参照
エージェント: テンプレートを使用してコード生成
```

**パターンC: チェックリスト型**

```
スキル: 品質チェックリスト、検証基準
    ↓ 参照
エージェント: チェックリストを順番に実行
```

---

## 既存エージェントへの適用例

### 例1: `feature-implementer` エージェントの更新

**現状（スキル参照なし）**:

```yaml
---
name: feature-implementer
description: TDDループを自動実行するサブエージェント
model: inherit
color: cyan
---
```

**更新後（スキル参照あり）**:

```yaml
---
name: feature-implementer
description: TDDループを自動実行するサブエージェント
skills:
  - coding-standards      # コーディング規約
  - tdd-development       # TDD開発プロセス
  - error-handling        # エラーハンドリングパターン
model: inherit
color: cyan
---
```

**変更点**:
- `skills:` フィールドを追加
- 本文から規約の詳細説明を削除（スキルに移譲）
- 「プリロードされたスキルの規約に従う」という記述を追加

**本文の更新例**:

```markdown
# 機能実装エージェント

あなたはTDD（テスト駆動開発）に基づいて機能を実装する専門のエージェントです。

**プリロードされたスキル**:
- `coding-standards`: 型ヒント、命名規則、Docstring形式
- `tdd-development`: Red → Green → Refactor サイクル
- `error-handling`: 例外クラス設計、エラーメッセージパターン

これらのスキルの規約に従って実装を行ってください。
```

### 例2: `test-writer` エージェントの更新

**現状**:

```yaml
---
name: test-writer
description: t-wada流TDDに基づいてテストを作成するサブエージェント
model: inherit
color: orange
---
```

**更新後**:

```yaml
---
name: test-writer
description: t-wada流TDDに基づいてテストを作成するサブエージェント
skills:
  - tdd-development       # TDD開発プロセス・テストテンプレート
  - coding-standards      # テストコードのスタイル規約
model: inherit
color: orange
---
```

**本文の更新**:
- TDDサイクルの詳細説明 → `tdd-development` スキルに移譲
- テスト命名規則の詳細 → `coding-standards` スキルに移譲
- エージェント本文はフローと実行手順に集中

### 例3: `quality-checker` エージェントの更新

**現状**: スキル参照なし

**更新後**:

```yaml
---
name: quality-checker
description: コード品質をチェック・修正するサブエージェント
skills:
  - coding-standards      # コーディング規約（チェック基準）
model: inherit
color: green
---
```

**変更点**:
- `coding-standards` スキルを参照
- 品質チェック基準をスキルから取得
- エージェントは「どうチェックするか」「どう修正するか」に集中

### 例4: テストエージェント群の統一

複数のテスト関連エージェントで同一スキルを参照：

```yaml
# test-orchestrator.md
skills:
  - tdd-development
  - coding-standards

# test-planner.md
skills:
  - tdd-development
  - coding-standards

# test-unit-writer.md
skills:
  - tdd-development
  - coding-standards

# test-property-writer.md
skills:
  - tdd-development
  - coding-standards

# test-integration-writer.md
skills:
  - tdd-development
  - coding-standards
```

**メリット**:
- テスト関連エージェントが同一の規約を参照
- 規約の更新が一箇所で完結
- エージェント間の一貫性が保証

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
| 2026-01-22 | 1.1.0 | エージェントへのスキル参照パターン、複数スキル参照時のルール、責務分担ガイドライン、既存エージェント更新例を追加 |
| 2026-01-22 | 1.0.0 | 初版作成 |

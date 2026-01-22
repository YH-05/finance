# System Update: スキルベースシステムへのマイグレーション計画

## エグゼクティブサマリー

既存のコマンドベースシステムをスキルベースのシステムに移行し、エージェントへのスキルプリロード機構を実装する。これにより、より柔軟で保守性の高いシステムを実現する。

## 決定事項

| 項目 | 決定内容 | 備考 |
|------|----------|------|
| 移行範囲 | ワークフロー/複雑ロジックを含むコマンドを優先 | |
| 後方互換性 | コマンドは廃止（スキル移行後、削除） | |
| スキル構造 | ナレッジベース（SKILL.md + guide.md + examples/）| Python スクリプト不要 |
| スキルプリロード | フロントマター方式（skills: でスキル指定、公式仕様準拠） | スキルコンテンツが自動注入 |
| エージェント移行 | 段階的移行（新規スキル作成時に関連エージェントを更新） | |
| 開始カテゴリ | レポジトリ管理 | |
| GitHub Project | 新規「System Update」を作成 | |
| 移行方式 | 即時置換（並存期間なし） | スキル完成後すぐに既存コマンド削除 |
| ツール活用 | 既存MCP/CLI/組み込みツール | Python スクリプト実装不要 |
| 実装順序 | 並列実装 | Wave単位で並列化 |

---

## フェーズ 0: 基盤整備

### 目標
- GitHub Project の作成
- スキルプリロード仕様の確定
- テンプレート整備

### タスク

| # | タスク | 依存 | 成果物 |
|---|--------|------|--------|
| 0.1 | GitHub Project「System Update」の作成 | なし | Project URL |
| 0.2 | スキル標準構造テンプレートの作成 | なし | `template/skill/` |
| 0.3 | スキルプリロード仕様書の作成 | 0.2 | `docs/skill-preload-spec.md` |
| 0.4 | エージェントへのスキル参照パターンの確定 | 0.3 | 仕様書更新 |

### スキル標準構造

```
.claude/skills/{skill-name}/
├── SKILL.md           # エントリーポイント（必須）
├── guide.md           # 詳細ガイド（オプション）
├── template.md        # 出力テンプレート（オプション）
└── examples/          # 使用例・パターン集（オプション）
```

**設計方針**: スキルは「ナレッジ（知識・手順・テンプレート）」を提供し、実際の処理は既存ツール（MCP サーバー、gh CLI、組み込みツール）を活用する。

### スキルプリロード実装方式: フロントマター skills フィールド

サブエージェントのフロントマターに `skills:` フィールドを記述し、起動時にスキルコンテンツをコンテキストに注入する方式を採用（[公式ドキュメント](https://code.claude.com/docs/ja/sub-agents)準拠）。

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
```

**重要な特性**:
- スキル名のリスト形式（配列）で指定
- 各スキルの**完全なコンテンツ**がサブエージェントのコンテキストに注入される
- サブエージェントは**親の会話からスキルを継承しない** - 明示的にリストする必要がある

**メリット**:
- Claude Code 公式仕様に準拠
- フロントマターで依存関係が明示される
- スキルコンテンツが自動的にコンテキストに読み込まれる

### 活用する既存ツール

スキルは以下の既存ツールを活用し、Python スクリプトの実装は行わない。

| カテゴリ | ツール | 用途 |
|---------|--------|------|
| ファイルシステム | `mcp__filesystem__directory_tree` | ディレクトリ構造取得（excludePatterns対応） |
| ファイルシステム | `mcp__filesystem__list_directory` | ディレクトリ一覧 |
| ファイルシステム | `mcp__filesystem__search_files` | ファイル検索（glob パターン） |
| Git | `mcp__git__*` | Git操作全般 |
| GitHub | Bash + `gh` CLI | Issue/PR/Project操作 |
| ファイル操作 | Read, Write, Edit, Glob, Grep | 組み込みツール |
| コード品質 | Bash + `ruff`, `pyright` | リント・型チェック |

### スキルフォルダ構成

```
.claude/skills/
├── skill-expert/              # 新規スキル（最優先）
├── agent-expert/              # 拡張（レビュー機能追加、最優先）
├── workflow-expert/           # 新規スキル（最優先）
├── index/                     # 新規スキル
├── project-management/        # 新規スキル
├── task-decomposition/        # 新規スキル（task-decomposerエージェントのみ統合）
└── issue-management/          # 新規スキル（issue系コマンドを統合）
```

---

## フェーズ 1: レポジトリ管理スキル

### 目標
7つのスキルを実装（スキル/エージェント/ワークフロー管理を最初に開発）：

**Wave 0（基盤スキル - 最優先）**:
1. スキル管理スキル（skill-expert）
2. エージェント管理スキル（agent-expert 拡張）
3. ワークフロー管理スキル（workflow-expert）

**Wave 1（レポジトリ管理スキル）**:
4. index スキル
5. プロジェクト管理スキル
6. タスク分解スキル（task-decomposer エージェントのみ統合）
7. Issue管理スキル（issue系コマンドを統合）

### ツール活用ガイド

スキルは基本的に既存ツールを活用するが、必要な機能をカバーするためにPythonスクリプトの実装が必要な場合は適宜実装を行う。

#### ディレクトリ操作

```bash
# ディレクトリツリー取得（MCP）
mcp__filesystem__directory_tree(path=".", excludePatterns=["node_modules", ".git", "__pycache__"])

# ファイル検索（MCP）
mcp__filesystem__search_files(path=".", pattern="**/*.md")
```

#### GitHub 操作

```bash
# Issue 一覧
gh issue list --json number,title,state,labels

# Project Item 一覧
gh project item-list <project_number> --format json

# Issue 作成
gh issue create --title "タイトル" --body "本文"

# Project Item 追加
gh project item-add <project_number> --owner <owner> --url <issue_url>
```

#### ファイル操作

```
# 組み込みツール
Read    - ファイル読み取り
Write   - ファイル書き込み
Edit    - ファイル編集（マーカーセクション更新等）
Glob    - パターンマッチング
Grep    - 正規表現検索
```

---

### タスク分解 (GitHub Issue)

#### Wave 0: 基盤スキル（最優先・並列実装可）

**skill-expert スキル（新規）**

| # | タイトル | 工数 | 依存 |
|---|---------|------|------|
| 1 | [スキル移行] skill-expert スキル SKILL.md の作成 | M | なし |
| 2 | [スキル移行] skill-expert スキル guide.md の作成 | M | #1 |
| 3 | [スキル移行] skill-expert スキル template.md の作成 | S | #1 |

**agent-expert スキル拡張**

| # | タイトル | 工数 | 依存 |
|---|---------|------|------|
| 4 | [スキル移行] agent-expert スキルにフロントマターレビュー機能を追加 | S | なし |

**workflow-expert スキル（新規）**

| # | タイトル | 工数 | 依存 |
|---|---------|------|------|
| 5 | [スキル移行] workflow-expert スキル SKILL.md の作成 | M | なし |
| 6 | [スキル移行] workflow-expert スキル guide.md の作成 | M | #5 |

#### Wave 1: レポジトリ管理スキル（並列実装可）

**index スキル**

| # | タイトル | 工数 | 依存 |
|---|---------|------|------|
| 7 | [スキル移行] index スキル SKILL.md の作成 | M | #3 |
| 8 | [スキル移行] index スキル guide.md の作成 | S | #7 |
| 9 | [スキル移行] 既存 /index コマンドを index スキルに置換 | S | #8 |

**プロジェクト管理スキル**

| # | タイトル | 工数 | 依存 |
|---|---------|------|------|
| 10 | [スキル移行] プロジェクト管理スキル SKILL.md の作成 | M | #3 |
| 11 | [スキル移行] プロジェクト管理スキル guide.md の作成 | M | #10 |
| 12 | [スキル移行] 既存プロジェクト管理コマンド/スキルを置換 | M | #11 |

**タスク分解スキル**

| # | タイトル | 工数 | 依存 |
|---|---------|------|------|
| 13 | [スキル移行] タスク分解スキル SKILL.md の作成 | M | #3 |
| 14 | [スキル移行] タスク分解スキル guide.md の作成 | M | #13 |
| 15 | [スキル移行] task-decomposer エージェントをスキルに統合 | M | #14 |

**Issue管理スキル**

| # | タイトル | 工数 | 依存 |
|---|---------|------|------|
| 16 | [スキル移行] Issue管理スキル SKILL.md の作成 | M | #3 |
| 17 | [スキル移行] Issue管理スキル guide.md の作成 | M | #16 |
| 18 | [スキル移行] 既存 issue 系コマンドを Issue管理スキルに置換 | L | #17 |

#### Wave 2: 統合

| # | タイトル | 工数 | 依存 |
|---|---------|------|------|
| 19 | [スキル移行] フェーズ1全スキルの統合テスト実施 | M | #4, #6, #9, #12, #15, #18 |

#### 依存関係グラフ

```
Wave 0 (基盤スキル - 最優先)                    Wave 1 (レポジトリ管理)              Wave 2
┌──────────────────────────────┐   ┌────────────────────────────────────┐
│ skill-expert:   #1 -> #2, #3 ┼───┼─> index:        #7 -> #8 -> #9 ────┼─┐
│ agent-expert:   #4 ──────────┼───┼─> project-mgmt: #10 -> #11 -> #12 ─┼─┤
│ workflow-expert: #5 -> #6 ───┼───┼─> task-decomp:  #13 -> #14 -> #15 ─┼─┼─> #19
└──────────────────────────────┘   │   issue-mgmt:   #16 -> #17 -> #18 ─┼─┘
                                   └────────────────────────────────────┘
```

---

### 1.1 index スキル

**移行元**: `/index` コマンド（`.claude/commands/index.md`）

**構造**:
```
.claude/skills/index/
├── SKILL.md              # メイン定義
├── guide.md              # CLAUDE.md/README.md 更新ガイド
└── template.md           # ディレクトリ構成テンプレート
```

**機能**:
- CLAUDE.md の自動更新（ディレクトリ構成セクション）
- README.md の自動更新
- コマンド/スキル/エージェント一覧の検出
- ディレクトリ構造の可視化（4層まで）

**活用ツール**:
- `mcp__filesystem__directory_tree` - ディレクトリ構造取得
- `Glob` - コマンド/スキル/エージェントファイル検出
- `Edit` - マーカーセクション更新

---

### 1.2 プロジェクト管理スキル

**新規作成**: `.claude/skills/project-management/`

**統合対象**:
- `/new-project` コマンド
- `/project-refine` コマンド
- `project-file` スキル
- `project-status-sync` スキル

**構造**:
```
.claude/skills/project-management/
├── SKILL.md              # メイン定義
├── guide.md              # GitHub Project/project.md 管理ガイド
└── template.md           # project.md テンプレート
```

**機能**:
- GitHub Project の作成・管理
- project.md の作成・編集
- GitHub Project と project.md の双方向同期
- ステータス自動更新（PR作成→In Progress、マージ→Done）

**活用ツール**:
- `gh project` - GitHub Project 操作
- `gh issue` - Issue 操作
- `Read`, `Edit` - project.md の読み書き

---

### 1.3 タスク分解スキル

**新規作成**: `.claude/skills/task-decomposition/`

**統合対象**:
- `task-decomposer` エージェント（類似性判定、依存関係解析）

**構造**:
```
.claude/skills/task-decomposition/
├── SKILL.md              # メイン定義
├── guide.md              # タスク分解・依存関係管理ガイド
└── template.md           # タスク分解テンプレート
```

**機能**:
- 要件定義からのタスク分解
- 依存関係の解析・可視化
- 類似タスクの判定
- Mermaid形式でのグラフ生成

**活用ツール**:
- Claude の推論能力 - 依存関係解析、類似性判定
- `Read`, `Write` - ドキュメント読み書き

---

### 1.4 Issue管理スキル

**新規作成**: `.claude/skills/issue-management/`

**統合対象**:
- `/issue` コマンド
- `/issue-implement` コマンド
- `/issue-refine` コマンド
- `/sync-issue` コマンド

**構造**:
```
.claude/skills/issue-management/
├── SKILL.md              # メイン定義
├── guide.md              # Issue操作・同期ガイド
└── template.md           # Issue テンプレート
```

**機能**:
- Issue の作成（3モード: quick_add/package/lightweight）
- Issue の自動実装（開発タイプ判定、5フェーズワークフロー）
- Issue のブラッシュアップ（8項目ユーザー詳細確認）
- Issue コメントからの進捗同期
- project.md との同期

**活用ツール**:
- `gh issue` - Issue CRUD
- `gh project` - Project Item 操作
- `Read`, `Edit` - project.md の読み書き

---

### 1.5 エージェント管理スキル（agent-expert 拡張）

**拡張対象**: `.claude/skills/agent-expert/`

**既存の agent-expert スキルにフロントマターレビュー機能を追加**

**構造**:
```
.claude/skills/agent-expert/
├── SKILL.md              # メイン定義（拡張）
├── guide.md              # エージェント設計ガイド（既存）
├── template.md           # エージェントテンプレート（既存）
└── frontmatter-review.md # フロントマターレビューガイド（新規）
```

**機能**:
- エージェントの作成・管理（既存）
- エージェントフロントマターのレビュー・検証（新規）
- スキルプリロード設定の検証（新規）

---

### 1.6 スキル管理スキル（skill-expert 新規）

**新規作成**: `.claude/skills/skill-expert/`

**構造**:
```
.claude/skills/skill-expert/
├── SKILL.md              # メイン定義
├── guide.md              # スキル設計ガイド
├── template.md           # スキルテンプレート
└── frontmatter-review.md # フロントマターレビューガイド
```

**機能**:
- スキルの作成・管理
- スキルフロントマターのレビュー・検証
- スキル構造（SKILL.md + guide.md + examples/）の検証

---

### 1.7 ワークフロー管理スキル（workflow-expert 新規）

**新規作成**: `.claude/skills/workflow-expert/`

**構造**:
```
.claude/skills/workflow-expert/
├── SKILL.md              # メイン定義
└── guide.md              # ワークフロー設計ガイド
```

**機能**:
- ワークフローの設計・管理
- マルチエージェントワークフローの設計支援
- スキル連携パターンの提供

---

### 受け入れ条件（詳細）

#### Wave 0: 基盤スキル

##### Issue #1: skill-expert SKILL.md

- [ ] スキル設計原則記載
- [ ] スキルカテゴリ分類記載
- [ ] 活用ツールの使用方法記載
- [ ] 使用例 3つ以上

##### Issue #2: skill-expert guide.md

- [ ] スキル構造（SKILL.md + guide.md + examples/）の説明
- [ ] プロンプトエンジニアリングガイド
- [ ] スキルフロントマター検証ルール

##### Issue #3: skill-expert template.md

- [ ] スキル用フロントマター構造
- [ ] スキルセクション構成
- [ ] コメント付きガイド

##### Issue #4: agent-expert フロントマターレビュー機能

- [ ] エージェントフロントマター検証ルール
- [ ] skills: フィールドの検証
- [ ] allowed-tools の検証
- [ ] 既存 guide.md と整合性

##### Issue #5: workflow-expert SKILL.md

- [ ] ワークフロー設計原則記載
- [ ] マルチエージェント連携パターン記載
- [ ] 使用例 3つ以上

##### Issue #6: workflow-expert guide.md

- [ ] ワークフロー設計手順
- [ ] スキル連携パターン
- [ ] オーケストレーション設計

#### Wave 1: レポジトリ管理スキル

##### Issue #7: index スキル SKILL.md

- [ ] skill-expert テンプレートに準拠
- [ ] 既存 /index コマンドの機能を網羅
  - 表示モード（/index）
  - 更新モード（/index --update）
  - コマンド、スキル、エージェント、ディレクトリ構成
- [ ] 活用ツールの使用方法記載（`mcp__filesystem__directory_tree`, `Glob`, `Edit`）
- [ ] 使用例 3つ以上

##### Issue #8: index スキル guide.md

- [ ] CLAUDE.md 更新手順
- [ ] README.md 更新手順
- [ ] マーカーセクション形式の説明
- [ ] 除外パターン一覧

##### Issue #9: /index 置換

- [ ] .claude/commands/index.md が index スキルを呼び出すよう変更
- [ ] /index と /index --update が動作
- [ ] 移行検証テスト通過
- [ ] 既存機能と同等の出力

##### Issue #10: プロジェクト管理スキル SKILL.md

- [ ] skill-expert テンプレートに準拠
- [ ] 統合対象の機能を網羅
  - /new-project（パッケージ/軽量モード）
  - /project-refine（整合性検証、自動修正）
  - project-file スキル（project.md テンプレート）
  - project-status-sync スキル（完了状態同期）
- [ ] 各モードの使い分け記載
- [ ] 活用ツールの使用方法記載（`gh project`, `gh issue`, `Read`, `Edit`）
- [ ] 使用例 3つ以上

##### Issue #11: プロジェクト管理スキル guide.md

- [ ] GitHub Project 操作手順（gh CLI）
- [ ] project.md パース形式（パッケージ/軽量）
- [ ] 双方向同期ルール（GitHub が Single Source of Truth）
- [ ] ステータス更新フロー

##### Issue #12: プロジェクト管理置換

- [ ] /new-project がプロジェクト管理スキルを使用
- [ ] /project-refine がプロジェクト管理スキルを使用
- [ ] project-status-sync スキルが統合
- [ ] 移行検証テスト通過

##### Issue #13: タスク分解スキル SKILL.md

- [ ] skill-expert テンプレートに準拠
- [ ] task-decomposer エージェントの機能を網羅
  - 依存関係解析
  - 類似タスク判定
  - Mermaid形式での可視化
- [ ] 活用ツールの使用方法記載
- [ ] 使用例 3つ以上

##### Issue #14: タスク分解スキル guide.md

- [ ] 依存関係解析手順（Claude の推論能力活用）
- [ ] 循環依存検出方法
- [ ] 類似タスク判定基準
- [ ] Mermaid 形式での可視化方法

##### Issue #15: task-decomposer エージェント統合

- [ ] task-decomposer エージェントがタスク分解スキルを参照
- [ ] 移行検証テスト通過

##### Issue #16: Issue管理スキル SKILL.md

- [ ] skill-expert テンプレートに準拠
- [ ] 統合対象の機能を網羅
  - /issue（3モード: quick_add/package/lightweight）
  - /issue-implement（開発タイプ判定、5フェーズワークフロー）
  - /issue-refine（8項目ユーザー詳細確認）
  - /sync-issue（コメント同期、確信度ベース確認）
- [ ] 各入力モード記載
- [ ] 活用ツールの使用方法記載（`gh issue`, `gh project`）
- [ ] 使用例 3つ以上

##### Issue #17: Issue管理スキル guide.md

- [ ] Issue 作成手順（3モード）
- [ ] Issue 自動実装ワークフロー
- [ ] Issue ブラッシュアップ手順
- [ ] コメント同期フロー

##### Issue #18: issue 系コマンド置換

- [ ] /issue がIssue管理スキルを使用
- [ ] /issue-implement がIssue管理スキルを使用
- [ ] /issue-refine がIssue管理スキルを使用
- [ ] /sync-issue がIssue管理スキルを使用
- [ ] 移行検証テスト通過

#### Wave 2: 統合

##### Issue #19: 統合テスト

- [ ] 全スキルが連携して動作
- [ ] 既存コマンドとの機能同等性検証
- [ ] エッジケーステスト実施
- [ ] ドキュメント最終更新

---

### フェーズ1 検証戦略

スキルは基本的にナレッジベースとして機能するため、以下の検証を実施。Pythonスクリプトを含むスキルについては、該当スクリプトのユニットテストも追加する。

| 種別 | 対象 | 検証方法 |
|------|------|---------|
| 機能同等性検証 | 各スキル | 既存コマンドと同等の出力を確認 |
| ツール連携検証 | MCP/gh CLI | 実際のツール呼び出しで動作確認 |
| スキル参照検証 | エージェント | `skills:` フィールドでのロード確認 |

---

## フェーズ 2: コーディングスキル

### 目標
- Pythonコーディング規約スキル
- TDD開発スキル
- エラーハンドリングスキル

### 設計方針

#### 1. スキルの粒度

**決定**: 3つの大スキル + 内部モジュール分割

調査で推奨された7つの小スキル（hint-converter, naming-normalizer等）は、3つの大スキル内の`examples/`や`templates/`として組み込む。

**理由**:
- フェーズ1のスキル構造（SKILL.md + guide.md + examples/）と統一
- スキルプリロードで1-2個のスキルを参照する設計と整合
- エージェントからの参照しやすさ

#### 2. 既存エージェントとの関係

**決定**: エージェントはスキルを参照する形に更新

- エージェントの役割（オーケストレーション、実行）は維持
- スキルはナレッジベースとして機能
- エージェント定義にフロントマターで`skills:`を追加

---

### 2.1 コーディング規約スキル (coding-standards)

#### 構造

```
.claude/skills/coding-standards/
├── SKILL.md              # クイックリファレンス（型ヒント、命名、Docstring）
├── guide.md              # 詳細規約（docs/coding-standards.mdから移行・整理）
└── examples/
    ├── type-hints.md     # PEP 695詳細例
    ├── docstrings.md     # NumPy形式詳細例
    ├── error-messages.md # エラーメッセージパターン
    ├── naming.md         # 命名規則詳細例
    └── logging.md        # ロギング実装パターン
```

**活用ツール**: スタイルチェックは `ruff`、`pyright` を Bash 経由で使用

#### SKILL.md 概要

```markdown
---
name: coding-standards
description: Pythonコーディング規約。型ヒント(PEP695)、命名規則、Docstring、エラーメッセージ、ロギングの標準。
allowed-tools: Read
---
```

**クイックリファレンス内容**:
- 型ヒント: `list[str]`, `def first[T](...)`, `type Alias = ...`
- 命名規則: snake_case/PascalCase/UPPER_SNAKE、Boolean接頭辞
- Docstring: NumPy形式の必須セクション
- エラーメッセージ: 具体的で解決策を示す
- ロギング: `get_logger(__name__)`

**プリロード対象エージェント**:
- `feature-implementer`
- `code-simplifier`
- `quality-checker`
- `test-*-writer`

#### タスクテーブル

| # | タスク | 依存 | 成果物 |
|---|--------|------|--------|
| 2.1.1 | SKILL.md の作成 | なし | `.claude/skills/coding-standards/SKILL.md` |
| 2.1.2 | guide.md の作成（docs/coding-standards.mdから移行・整理） | 2.1.1 | `guide.md` |
| 2.1.3 | examples/type-hints.md の作成 | 2.1.1 | `examples/type-hints.md` |
| 2.1.4 | examples/docstrings.md の作成 | 2.1.1 | `examples/docstrings.md` |
| 2.1.5 | examples/error-messages.md の作成 | 2.1.1 | `examples/error-messages.md` |
| 2.1.6 | examples/naming.md の作成 | 2.1.1 | `examples/naming.md` |
| 2.1.7 | examples/logging.md の作成 | 2.1.1 | `examples/logging.md` |
| 2.1.8 | エージェントへのスキル参照追加 | 2.1.2 | エージェント更新 |
| 2.1.9 | .claude/rules/coding-standards.md の更新 | 2.1.2 | ルール更新 |
| 2.1.10 | docs/coding-standards.md の移行・更新 | 2.1.2 | docsをリンクのみに |
| 2.1.11 | 検証 | 2.1.8 | 動作確認 |

**並列実行可能**: 2.1.3〜2.1.7

---

### 2.2 TDD開発スキル (tdd-development)

#### 構造

```
.claude/skills/tdd-development/
├── SKILL.md              # TDDサイクル、命名規則、ファイル配置
├── guide.md              # 詳細プロセス（三角測量、優先度付け、context7連携）
└── templates/
    ├── unit-test.md      # 単体テストテンプレート
    ├── property-test.md  # プロパティテストテンプレート
    └── integration-test.md # 統合テストテンプレート
```

**活用ツール**: テスト実行は `pytest` を Bash 経由で使用、テスト設計は Claude の推論能力を活用

#### SKILL.md 概要

```markdown
---
name: tdd-development
description: t-wada流TDD（Red→Green→Refactor）。テスト設計、単体・プロパティ・統合テストのテンプレート。
allowed-tools: Read, Bash
---
```

**クイックリファレンス内容**:
- TDDサイクル: 🔴Red → 🟢Green → 🔵Refactor
- テスト命名: `test_正常系_xxx`, `test_異常系_xxx`, `test_エッジケース_xxx`
- ファイル配置: `tests/{library}/unit/`, `property/`, `integration/`
- context7必須ケース: pytest高度機能、Hypothesis、pytest-asyncio

**プリロード対象エージェント**:
- `test-orchestrator`
- `test-planner`
- `test-*-writer`
- `feature-implementer`

#### タスクテーブル

| # | タスク | 依存 | 成果物 |
|---|--------|------|--------|
| 2.2.1 | SKILL.md の作成 | なし | `.claude/skills/tdd-development/SKILL.md` |
| 2.2.2 | guide.md の作成（test-writer, test-plannerから統合） | 2.2.1 | `guide.md` |
| 2.2.3 | templates/unit-test.md の作成 | 2.2.1 | `templates/unit-test.md` |
| 2.2.4 | templates/property-test.md の作成 | 2.2.1 | `templates/property-test.md` |
| 2.2.5 | templates/integration-test.md の作成 | 2.2.1 | `templates/integration-test.md` |
| 2.2.6 | テストエージェント群へのスキル参照追加 | 2.2.2 | エージェント更新 |
| 2.2.7 | /write-tests コマンドの更新 | 2.2.2 | コマンド更新 |
| 2.2.8 | .claude/rules/testing-strategy.md の更新 | 2.2.2 | ルール更新 |
| 2.2.9 | docs/testing-strategy.md の移行・更新 | 2.2.2 | docsをリンクのみに |
| 2.2.10 | 検証 | 2.2.6 | 動作確認 |

**並列実行可能**: 2.2.3〜2.2.5

---

### 2.3 エラーハンドリングスキル (error-handling)

#### 構造

```
.claude/skills/error-handling/
├── SKILL.md              # パターン選択ガイド、シンプル/リッチ概要
├── guide.md              # 詳細設計原則、例外階層、リトライ戦略
└── examples/
    ├── simple-pattern.md   # シンプルパターン（RSS方式）
    ├── rich-pattern.md     # リッチパターン（Market Analysis方式）
    ├── retry-patterns.md   # リトライ・フォールバック
    └── logging-integration.md # ロギング統合パターン
```

**活用ツール**: 例外クラス生成は Claude の生成能力 + examples/ のテンプレートを活用

#### SKILL.md 概要

```markdown
---
name: error-handling
description: Pythonエラーハンドリングパターン。シンプル/リッチ例外設計、リトライ、ロギング統合。
allowed-tools: Read, Write
---
```

**パターン選択ガイド**:
| 条件 | 推奨パターン |
|------|------------|
| 内部ライブラリ、シンプルな例外 | シンプルパターン（RSS方式） |
| 外部API連携、詳細情報必要 | リッチパターン（Market Analysis方式） |
| エラーのシリアライズ必要 | リッチパターン |

**プリロード対象エージェント**:
- `feature-implementer`
- `code-simplifier`

#### タスクテーブル

| # | タスク | 依存 | 成果物 |
|---|--------|------|--------|
| 2.3.1 | SKILL.md の作成 | なし | `.claude/skills/error-handling/SKILL.md` |
| 2.3.2 | guide.md の作成 | 2.3.1 | `guide.md` |
| 2.3.3 | examples/simple-pattern.md の作成 | 2.3.1 | `examples/simple-pattern.md` |
| 2.3.4 | examples/rich-pattern.md の作成 | 2.3.1 | `examples/rich-pattern.md` |
| 2.3.5 | examples/retry-patterns.md の作成 | 2.3.1 | `examples/retry-patterns.md` |
| 2.3.6 | examples/logging-integration.md の作成 | 2.3.1 | `examples/logging-integration.md` |
| 2.3.7 | エージェントへのスキル参照追加 | 2.3.2 | エージェント更新 |
| 2.3.8 | 検証 | 2.3.7 | 動作確認 |

**並列実行可能**: 2.3.3〜2.3.6

---

### フェーズ2 依存関係グラフ

```
フェーズ0（基盤整備）
    │
    └── フェーズ1（レポジトリ管理）
            │
            └── フェーズ2（コーディング）
                    │
                    ├── 2.1 coding-standards ─┐
                    ├── 2.2 tdd-development  ─┼─ 並列実行可能
                    └── 2.3 error-handling  ─┘
```

---

## フェーズ 3: 金融分析スキル

### 目標

6つの金融分析スキルを実装し、金融エージェント群に統合する：

**Wave 0（データ取得・基盤）**:
1. market-data スキル（MarketData API、yfinance/FRED統合）
2. rss-integration スキル（RSSライブラリ統合）

**Wave 1（分析スキル）**:
3. technical-analysis スキル（Analysis API、テクニカル指標）
4. financial-calculations スキル（リターン計算、相関分析）

**Wave 2（外部連携）**:
5. sec-edgar スキル（SEC EDGAR MCP統合）
6. web-research スキル（Tavily MCP、Web検索）

### 設計方針

#### 1. 既存ライブラリとの関係

**決定**: スキルは既存ライブラリ（`src/market_analysis/`, `src/rss/`）の使用ガイドとベストプラクティスを提供

- スキルは「ナレッジ（知識・手順・テンプレート）」を提供
- 実際の処理は既存の Python ライブラリと MCP ツールを活用
- Python スクリプトの新規実装は行わない

#### 2. スキルの粒度

**決定**: 機能領域ごとに独立したスキル

- データ取得系（market-data, rss-integration）
- 分析系（technical-analysis, financial-calculations）
- 外部連携系（sec-edgar, web-research）

#### 3. エージェントへの統合

**決定**: 金融エージェント群のフロントマターにスキル参照を追加

```yaml
# 例: finance-technical-analysis エージェント
skills:
  - market-data
  - technical-analysis
```

---

### 3.1 market-data スキル

#### 構造

```
.claude/skills/market-data/
├── SKILL.md              # クイックリファレンス（API概要、基本使用法）
├── guide.md              # 詳細ガイド（キャッシュ、リトライ、エラーハンドリング）
└── examples/
    ├── stock-data.md     # 株式データ取得パターン
    ├── forex-data.md     # 為替データ取得パターン
    ├── fred-data.md      # 経済指標（FRED）取得パターン
    └── multi-asset.md    # 複数資産並列取得パターン
```

#### SKILL.md 概要

```markdown
---
name: market-data
description: market_analysis.api.MarketData を使用した市場データ取得のベストプラクティス。yfinance/FRED統合、キャッシュ、リトライ戦略。
allowed-tools: Read, Bash
---
```

**クイックリファレンス内容**:
- MarketData 初期化パターン（キャッシュ・リトライ設定）
- `fetch_stock()`, `fetch_forex()`, `fetch_fred()` の使用法
- `to_agent_json()` でのエージェント出力変換
- 主要エラーコードと対処法

**プリロード対象エージェント**:
- `finance-technical-analysis`
- `finance-economic-analysis`
- `finance-market-data`
- `dr-source-aggregator`

#### タスクテーブル

| # | タスク | 依存 | 成果物 |
|---|--------|------|--------|
| 3.1.1 | SKILL.md の作成 | なし | `.claude/skills/market-data/SKILL.md` |
| 3.1.2 | guide.md の作成 | 3.1.1 | `guide.md` |
| 3.1.3 | examples/stock-data.md の作成 | 3.1.1 | `examples/stock-data.md` |
| 3.1.4 | examples/forex-data.md の作成 | 3.1.1 | `examples/forex-data.md` |
| 3.1.5 | examples/fred-data.md の作成 | 3.1.1 | `examples/fred-data.md` |
| 3.1.6 | examples/multi-asset.md の作成 | 3.1.1 | `examples/multi-asset.md` |
| 3.1.7 | エージェントへのスキル参照追加 | 3.1.2 | エージェント更新 |
| 3.1.8 | 検証 | 3.1.7 | 動作確認 |

**並列実行可能**: 3.1.3〜3.1.6

---

### 3.2 rss-integration スキル

#### 構造

```
.claude/skills/rss-integration/
├── SKILL.md              # クイックリファレンス（API概要、基本使用法）
├── guide.md              # 詳細ガイド（フィード管理、差分検出、バッチ処理）
└── examples/
    ├── feed-management.md    # フィード登録・管理パターン
    ├── item-fetching.md      # アイテム取得・検索パターン
    └── mcp-integration.md    # MCP ツール活用パターン
```

#### SKILL.md 概要

```markdown
---
name: rss-integration
description: rss ライブラリを使用したフィード管理・取得のベストプラクティス。差分検出、重複排除、MCP統合。
allowed-tools: Read, Bash
---
```

**クイックリファレンス内容**:
- FeedManager, FeedFetcher, FeedReader の使用法
- MCP ツール（`mcp__rss__*`）の活用
- 差分検出・重複排除パターン
- バッチスケジューリング

**プリロード対象エージェント**:
- `finance-news-collector`
- `finance-news-*`（テーマ別エージェント群）

#### タスクテーブル

| # | タスク | 依存 | 成果物 |
|---|--------|------|--------|
| 3.2.1 | SKILL.md の作成 | なし | `.claude/skills/rss-integration/SKILL.md` |
| 3.2.2 | guide.md の作成 | 3.2.1 | `guide.md` |
| 3.2.3 | examples/feed-management.md の作成 | 3.2.1 | `examples/feed-management.md` |
| 3.2.4 | examples/item-fetching.md の作成 | 3.2.1 | `examples/item-fetching.md` |
| 3.2.5 | examples/mcp-integration.md の作成 | 3.2.1 | `examples/mcp-integration.md` |
| 3.2.6 | エージェントへのスキル参照追加 | 3.2.2 | エージェント更新 |
| 3.2.7 | 検証 | 3.2.6 | 動作確認 |

**並列実行可能**: 3.2.3〜3.2.5

---

### 3.3 technical-analysis スキル

#### 構造

```
.claude/skills/technical-analysis/
├── SKILL.md              # クイックリファレンス（Analysis API、指標一覧）
├── guide.md              # 詳細ガイド（メソッドチェーン、指標計算、判定基準）
└── examples/
    ├── trend-analysis.md     # トレンド分析（SMA, EMA, MACD）
    ├── momentum-analysis.md  # モメンタム分析（RSI, Stochastic）
    ├── volatility-analysis.md # ボラティリティ分析（BB, ATR）
    └── signal-generation.md  # シグナル生成パターン
```

#### SKILL.md 概要

```markdown
---
name: technical-analysis
description: market_analysis.api.Analysis を使用したテクニカル分析のベストプラクティス。メソッドチェーン、指標計算、シグナル生成。
allowed-tools: Read, Bash
---
```

**クイックリファレンス内容**:
- Analysis クラスのメソッドチェーン設計
- 主要テクニカル指標（SMA, EMA, RSI, MACD, BB）
- AnalysisResult の活用
- 判定基準テーブル（トレンド、買われ過ぎ/売られ過ぎ）

**プリロード対象エージェント**:
- `finance-technical-analysis`
- `dr-stock-analyzer`
- `dr-sector-analyzer`

#### タスクテーブル

| # | タスク | 依存 | 成果物 |
|---|--------|------|--------|
| 3.3.1 | SKILL.md の作成 | 3.1.2 | `.claude/skills/technical-analysis/SKILL.md` |
| 3.3.2 | guide.md の作成 | 3.3.1 | `guide.md` |
| 3.3.3 | examples/trend-analysis.md の作成 | 3.3.1 | `examples/trend-analysis.md` |
| 3.3.4 | examples/momentum-analysis.md の作成 | 3.3.1 | `examples/momentum-analysis.md` |
| 3.3.5 | examples/volatility-analysis.md の作成 | 3.3.1 | `examples/volatility-analysis.md` |
| 3.3.6 | examples/signal-generation.md の作成 | 3.3.1 | `examples/signal-generation.md` |
| 3.3.7 | エージェントへのスキル参照追加 | 3.3.2 | エージェント更新 |
| 3.3.8 | 検証 | 3.3.7 | 動作確認 |

**並列実行可能**: 3.3.3〜3.3.6

---

### 3.4 financial-calculations スキル

#### 構造

```
.claude/skills/financial-calculations/
├── SKILL.md              # クイックリファレンス（リターン計算、相関分析）
├── guide.md              # 詳細ガイド（計算式、年率化、統計量）
└── examples/
    ├── return-calculations.md    # 多期間リターン計算
    ├── correlation-analysis.md   # 相関分析パターン
    ├── risk-metrics.md           # リスク指標（ボラティリティ、シャープ比）
    └── performance-attribution.md # パフォーマンス帰属分析
```

#### SKILL.md 概要

```markdown
---
name: financial-calculations
description: 金融計算のベストプラクティス。リターン計算、相関分析、リスク指標、年率化。
allowed-tools: Read, Bash
---
```

**クイックリファレンス内容**:
- `MultiPeriodReturns` の使用法
- `CorrelationAnalyzer` の使用法
- 年率化係数（252日、12ヶ月、52週）
- 統計量（平均、標準偏差、シャープ比、最大ドローダウン）

**プリロード対象エージェント**:
- `finance-technical-analysis`
- `dr-stock-analyzer`
- `dr-macro-analyzer`

#### タスクテーブル

| # | タスク | 依存 | 成果物 |
|---|--------|------|--------|
| 3.4.1 | SKILL.md の作成 | 3.1.2 | `.claude/skills/financial-calculations/SKILL.md` |
| 3.4.2 | guide.md の作成 | 3.4.1 | `guide.md` |
| 3.4.3 | examples/return-calculations.md の作成 | 3.4.1 | `examples/return-calculations.md` |
| 3.4.4 | examples/correlation-analysis.md の作成 | 3.4.1 | `examples/correlation-analysis.md` |
| 3.4.5 | examples/risk-metrics.md の作成 | 3.4.1 | `examples/risk-metrics.md` |
| 3.4.6 | examples/performance-attribution.md の作成 | 3.4.1 | `examples/performance-attribution.md` |
| 3.4.7 | エージェントへのスキル参照追加 | 3.4.2 | エージェント更新 |
| 3.4.8 | 検証 | 3.4.7 | 動作確認 |

**並列実行可能**: 3.4.3〜3.4.6

---

### 3.5 sec-edgar スキル

#### 構造

```
.claude/skills/sec-edgar/
├── SKILL.md              # クイックリファレンス（MCP ツール一覧、基本使用法）
├── guide.md              # 詳細ガイド（ファイリング種別、財務データ抽出）
└── examples/
    ├── company-info.md       # 企業情報取得パターン
    ├── financial-statements.md # 財務諸表取得パターン
    ├── insider-trading.md    # インサイダー取引分析パターン
    └── filing-analysis.md    # 8-K/10-K/10-Q 分析パターン
```

#### SKILL.md 概要

```markdown
---
name: sec-edgar
description: SEC EDGAR MCP ツールを使用した企業情報・財務データ取得のベストプラクティス。
allowed-tools: Read, ToolSearch, mcp__sec-edgar-mcp__*
---
```

**クイックリファレンス内容**:
- MCP ツール一覧（`mcp__sec-edgar-mcp__*`）
- CIK 取得、企業情報、財務諸表
- インサイダー取引データ
- ファイリング分析（8-K, 10-K, 10-Q）

**プリロード対象エージェント**:
- `finance-sec-filings`
- `dr-stock-analyzer`
- `finance-fact-checker`

#### タスクテーブル

| # | タスク | 依存 | 成果物 |
|---|--------|------|--------|
| 3.5.1 | SKILL.md の作成 | なし | `.claude/skills/sec-edgar/SKILL.md` |
| 3.5.2 | guide.md の作成 | 3.5.1 | `guide.md` |
| 3.5.3 | examples/company-info.md の作成 | 3.5.1 | `examples/company-info.md` |
| 3.5.4 | examples/financial-statements.md の作成 | 3.5.1 | `examples/financial-statements.md` |
| 3.5.5 | examples/insider-trading.md の作成 | 3.5.1 | `examples/insider-trading.md` |
| 3.5.6 | examples/filing-analysis.md の作成 | 3.5.1 | `examples/filing-analysis.md` |
| 3.5.7 | エージェントへのスキル参照追加 | 3.5.2 | エージェント更新 |
| 3.5.8 | 検証 | 3.5.7 | 動作確認 |

**並列実行可能**: 3.5.3〜3.5.6

---

### 3.6 web-research スキル

#### 構造

```
.claude/skills/web-research/
├── SKILL.md              # クイックリファレンス（Tavily MCP、WebFetch、検索戦略）
├── guide.md              # 詳細ガイド（検索クエリ設計、ソース評価、情報統合）
└── examples/
    ├── news-search.md        # ニュース検索パターン
    ├── company-research.md   # 企業調査パターン
    ├── market-analysis.md    # 市場分析調査パターン
    └── fact-verification.md  # ファクトチェックパターン
```

#### SKILL.md 概要

```markdown
---
name: web-research
description: Tavily MCP および WebFetch を使用した Web 調査のベストプラクティス。検索戦略、ソース評価、情報統合。
allowed-tools: Read, WebFetch, WebSearch, ToolSearch, mcp__tavily__*
---
```

**クイックリファレンス内容**:
- Tavily MCP ツール（`mcp__tavily__tavily-search`, `tavily-extract`）
- WebFetch / WebSearch の使用法
- 検索クエリ設計パターン
- ソース信頼性評価基準

**プリロード対象エージェント**:
- `finance-web`
- `finance-wiki`
- `finance-fact-checker`
- `dr-source-aggregator`

#### タスクテーブル

| # | タスク | 依存 | 成果物 |
|---|--------|------|--------|
| 3.6.1 | SKILL.md の作成 | なし | `.claude/skills/web-research/SKILL.md` |
| 3.6.2 | guide.md の作成 | 3.6.1 | `guide.md` |
| 3.6.3 | examples/news-search.md の作成 | 3.6.1 | `examples/news-search.md` |
| 3.6.4 | examples/company-research.md の作成 | 3.6.1 | `examples/company-research.md` |
| 3.6.5 | examples/market-analysis.md の作成 | 3.6.1 | `examples/market-analysis.md` |
| 3.6.6 | examples/fact-verification.md の作成 | 3.6.1 | `examples/fact-verification.md` |
| 3.6.7 | エージェントへのスキル参照追加 | 3.6.2 | エージェント更新 |
| 3.6.8 | 検証 | 3.6.7 | 動作確認 |

**並列実行可能**: 3.6.3〜3.6.6

---

### フェーズ3 タスク分解（GitHub Issue）

#### Wave 0: データ取得・基盤スキル（並列実装可）

**market-data スキル**

| # | タイトル | 工数 | 依存 |
|---|---------|------|------|
| 3.1 | [スキル移行] market-data スキル SKILL.md の作成 | M | なし |
| 3.2 | [スキル移行] market-data スキル guide.md の作成 | M | #3.1 |
| 3.3 | [スキル移行] market-data スキル examples/ の作成 | M | #3.1 |
| 3.4 | [スキル移行] market-data スキル エージェント統合 | S | #3.2 |

**rss-integration スキル**

| # | タイトル | 工数 | 依存 |
|---|---------|------|------|
| 3.5 | [スキル移行] rss-integration スキル SKILL.md の作成 | M | なし |
| 3.6 | [スキル移行] rss-integration スキル guide.md の作成 | M | #3.5 |
| 3.7 | [スキル移行] rss-integration スキル examples/ の作成 | M | #3.5 |
| 3.8 | [スキル移行] rss-integration スキル エージェント統合 | S | #3.6 |

#### Wave 1: 分析スキル（並列実装可、Wave 0 依存）

**technical-analysis スキル**

| # | タイトル | 工数 | 依存 |
|---|---------|------|------|
| 3.9 | [スキル移行] technical-analysis スキル SKILL.md の作成 | M | #3.2 |
| 3.10 | [スキル移行] technical-analysis スキル guide.md の作成 | M | #3.9 |
| 3.11 | [スキル移行] technical-analysis スキル examples/ の作成 | M | #3.9 |
| 3.12 | [スキル移行] technical-analysis スキル エージェント統合 | S | #3.10 |

**financial-calculations スキル**

| # | タイトル | 工数 | 依存 |
|---|---------|------|------|
| 3.13 | [スキル移行] financial-calculations スキル SKILL.md の作成 | M | #3.2 |
| 3.14 | [スキル移行] financial-calculations スキル guide.md の作成 | M | #3.13 |
| 3.15 | [スキル移行] financial-calculations スキル examples/ の作成 | M | #3.13 |
| 3.16 | [スキル移行] financial-calculations スキル エージェント統合 | S | #3.14 |

#### Wave 2: 外部連携スキル（並列実装可）

**sec-edgar スキル**

| # | タイトル | 工数 | 依存 |
|---|---------|------|------|
| 3.17 | [スキル移行] sec-edgar スキル SKILL.md の作成 | M | なし |
| 3.18 | [スキル移行] sec-edgar スキル guide.md の作成 | M | #3.17 |
| 3.19 | [スキル移行] sec-edgar スキル examples/ の作成 | M | #3.17 |
| 3.20 | [スキル移行] sec-edgar スキル エージェント統合 | S | #3.18 |

**web-research スキル**

| # | タイトル | 工数 | 依存 |
|---|---------|------|------|
| 3.21 | [スキル移行] web-research スキル SKILL.md の作成 | M | なし |
| 3.22 | [スキル移行] web-research スキル guide.md の作成 | M | #3.21 |
| 3.23 | [スキル移行] web-research スキル examples/ の作成 | M | #3.21 |
| 3.24 | [スキル移行] web-research スキル エージェント統合 | S | #3.22 |

#### Wave 3: 統合テスト

| # | タイトル | 工数 | 依存 |
|---|---------|------|------|
| 3.25 | [スキル移行] フェーズ3 全スキルの統合テスト実施 | M | #3.4, #3.8, #3.12, #3.16, #3.20, #3.24 |

---

### フェーズ3 依存関係グラフ

```
フェーズ2（コーディング）
    │
    └── フェーズ3（金融分析）
            │
            ├── Wave 0 (データ取得・基盤)
            │   ├── market-data:      #3.1 -> #3.2, #3.3 -> #3.4
            │   └── rss-integration:  #3.5 -> #3.6, #3.7 -> #3.8
            │
            ├── Wave 1 (分析) ← market-data
            │   ├── technical-analysis:     #3.9 -> #3.10, #3.11 -> #3.12
            │   └── financial-calculations: #3.13 -> #3.14, #3.15 -> #3.16
            │
            ├── Wave 2 (外部連携)
            │   ├── sec-edgar:     #3.17 -> #3.18, #3.19 -> #3.20
            │   └── web-research:  #3.21 -> #3.22, #3.23 -> #3.24
            │
            └── Wave 3 (統合)
                    └── #3.25 ← #3.4, #3.8, #3.12, #3.16, #3.20, #3.24
```

---

### フェーズ3 検証戦略

| 種別 | 対象 | 検証方法 |
|------|------|---------||
| API 使用例検証 | 各スキル | examples/ のコードが実行可能であることを確認 |
| エージェント統合検証 | 金融エージェント群 | `skills:` フィールドでのスキルロード確認 |
| ワークフロー検証 | 記事作成フロー | `/finance-research` コマンドでのスキル参照確認 |

### フェーズ3 完了基準

#### スキル作成
- [ ] `.claude/skills/market-data/` が存在し、SKILL.md, guide.md, examples/ が揃っている
- [ ] `.claude/skills/rss-integration/` が存在し、SKILL.md, guide.md, examples/ が揃っている
- [ ] `.claude/skills/technical-analysis/` が存在し、SKILL.md, guide.md, examples/ が揃っている
- [ ] `.claude/skills/financial-calculations/` が存在し、SKILL.md, guide.md, examples/ が揃っている
- [ ] `.claude/skills/sec-edgar/` が存在し、SKILL.md, guide.md, examples/ が揃っている
- [ ] `.claude/skills/web-research/` が存在し、SKILL.md, guide.md, examples/ が揃っている

#### エージェント更新
- [ ] `finance-technical-analysis.md` が `skills: [market-data, technical-analysis]` を参照
- [ ] `finance-economic-analysis.md` が `skills: [market-data, financial-calculations]` を参照
- [ ] `finance-news-collector.md` が `skills: [rss-integration]` を参照
- [ ] `finance-sec-filings.md` が `skills: [sec-edgar]` を参照
- [ ] `finance-web.md` が `skills: [web-research]` を参照

#### 品質確認
- [ ] 全スキルで examples/ のコードが実行可能
- [ ] `/finance-research` コマンドが正常動作

---

### フェーズ3 重要ファイル一覧

#### 参照元（既存ライブラリ）

| ファイル | 役割 |
|---------|------|
| `src/market_analysis/api/market_data.py` | MarketData API |
| `src/market_analysis/api/analysis.py` | Analysis API |
| `src/market_analysis/analysis/*.py` | 分析モジュール群 |
| `src/market_analysis/types.py` | 型定義 |
| `src/market_analysis/errors.py` | 例外クラス |
| `src/rss/services/*.py` | RSS サービス層 |
| `src/rss/types.py` | RSS 型定義 |

#### 新規作成

| ファイル | 内容 |
|----------|------|
| `.claude/skills/market-data/` | 市場データ取得スキル一式 |
| `.claude/skills/rss-integration/` | RSS 統合スキル一式 |
| `.claude/skills/technical-analysis/` | テクニカル分析スキル一式 |
| `.claude/skills/financial-calculations/` | 金融計算スキル一式 |
| `.claude/skills/sec-edgar/` | SEC EDGAR スキル一式 |
| `.claude/skills/web-research/` | Web 調査スキル一式 |

#### 変更対象（エージェント）

| ファイル | 変更内容 |
|----------|----------|
| `.claude/agents/finance-technical-analysis.md` | `skills: [market-data, technical-analysis]` を追加 |
| `.claude/agents/finance-economic-analysis.md` | `skills: [market-data, financial-calculations]` を追加 |
| `.claude/agents/finance-market-data.md` | `skills: [market-data]` を追加 |
| `.claude/agents/finance-news-collector.md` | `skills: [rss-integration]` を追加 |
| `.claude/agents/finance-sec-filings.md` | `skills: [sec-edgar]` を追加 |
| `.claude/agents/finance-web.md` | `skills: [web-research]` を追加 |
| `.claude/agents/finance-wiki.md` | `skills: [web-research]` を追加 |
| `.claude/agents/finance-fact-checker.md` | `skills: [sec-edgar, web-research]` を追加 |
| `.claude/agents/dr-source-aggregator.md` | `skills: [market-data, web-research]` を追加 |
| `.claude/agents/dr-stock-analyzer.md` | `skills: [market-data, technical-analysis, sec-edgar]` を追加 |

---

## フェーズ 4: 記事執筆スキル（後続フェーズ）

- 記事構成スキル
- 批評・推敲スキル
- コンプライアンススキル

---

## 重要ファイル一覧

### 移行元（参照）

| ファイル | 役割 |
|---------|------|
| `.claude/commands/index.md` | 9サブエージェント並列実行アーキテクチャ |
| `.claude/commands/new-project.md` | インタビュー→計画書→GitHub Project→Issue |
| `.claude/commands/project-refine.md` | 循環依存検出、ステータス不整合修正 |
| `.claude/commands/issue.md` | 3モード（quick_add/package/lightweight） |
| `.claude/commands/issue-implement.md` | 開発タイプ判定、5フェーズワークフロー |
| `.claude/commands/issue-refine.md` | 8項目ユーザー詳細確認 |
| `.claude/commands/sync-issue.md` | コメント同期、確信度ベース確認 |
| `.claude/agents/task-decomposer.md` | 類似性判定、依存関係解析 |
| `.claude/skills/project-status-sync/SKILL.md` | GitHub Project同期パターン |
| `.claude/skills/agent-expert/template.md` | スキル作成テンプレート |
| `docs/coding-standards.md` | コーディング規約元データ |
| `docs/testing-strategy.md` | テスト戦略元データ |
| `src/rss/exceptions.py` | シンプルエラーパターン |
| `src/market_analysis/errors.py` | リッチエラーパターン |
| `.claude/agents/test-writer.md` | test-writer実装 |
| `.claude/agents/test-planner.md` | test-planner実装 |

### 新規作成

| ファイル | 内容 |
|----------|------|
| `.claude/skills/skill-expert/` | スキル管理スキル一式（最優先） |
| `.claude/skills/workflow-expert/` | ワークフロー管理スキル一式（最優先） |
| `.claude/skills/agent-expert/frontmatter-review.md` | フロントマターレビューガイド（最優先） |
| `.claude/skills/index/` | index スキル一式 |
| `.claude/skills/project-management/` | プロジェクト管理スキル一式 |
| `.claude/skills/task-decomposition/` | タスク分解スキル一式（task-decomposerのみ） |
| `.claude/skills/issue-management/` | Issue管理スキル一式（issue系コマンド統合） |
| `.claude/skills/coding-standards/` | コーディング規約スキル一式 |
| `.claude/skills/tdd-development/` | TDD開発スキル一式 |
| `.claude/skills/error-handling/` | エラーハンドリングスキル一式 |
| `docs/skill-preload-spec.md` | スキルプリロード仕様書 |

### 変更対象

| ファイル | 変更内容 |
|----------|----------|
| `.claude/commands/index.md` | index スキル呼び出しに変更後、削除 |
| `.claude/commands/new-project.md` | プロジェクト管理スキル呼び出しに変更後、削除 |
| `.claude/commands/project-refine.md` | プロジェクト管理スキル呼び出しに変更後、削除 |
| `.claude/commands/issue.md` | Issue管理スキル呼び出しに変更後、削除 |
| `.claude/commands/issue-implement.md` | Issue管理スキル呼び出しに変更後、削除 |
| `.claude/commands/issue-refine.md` | Issue管理スキル呼び出しに変更後、削除 |
| `.claude/commands/sync-issue.md` | Issue管理スキル呼び出しに変更後、削除 |
| `.claude/skills/project-file/` | プロジェクト管理スキルに統合後、削除 |
| `.claude/skills/project-status-sync/` | プロジェクト管理スキルに統合後、削除 |
| `.claude/skills/agent-expert/SKILL.md` | フロントマターレビュー機能を追加 |
| `.claude/agents/feature-implementer.md` | スキルプリロード参照を追加、`skills: [coding-standards, tdd-development, error-handling]` |
| `.claude/agents/code-simplifier.md` | `skills: [coding-standards, error-handling]` を参照 |
| `.claude/agents/quality-checker.md` | `skills: [coding-standards]` を参照 |
| `.claude/agents/test-orchestrator.md` | `skills: [tdd-development, coding-standards]` を参照 |
| `.claude/agents/test-planner.md` | `skills: [tdd-development, coding-standards]` を参照 |
| `.claude/agents/test-unit-writer.md` | skills参照追加 |
| `.claude/agents/test-property-writer.md` | skills参照追加 |
| `.claude/agents/test-integration-writer.md` | skills参照追加 |
| `.claude/agents/task-decomposer.md` | タスク分解スキル参照を追加、`skills: [task-decomposition]` |
| `.claude/commands/write-tests.md` | スキル参照追加 |
| `.claude/rules/coding-standards.md` | スキルへのリンク追加 |
| `.claude/rules/testing-strategy.md` | スキルへのリンク追加 |
| `docs/coding-standards.md` | スキルへ移行（docs/はスキルへの参照リンクのみ残す） |
| `docs/testing-strategy.md` | スキルへ移行（docs/はスキルへの参照リンクのみ残す） |

---

## 検証方法

### フェーズ 0 完了基準

- [ ] GitHub Project「System Update」が作成されている
- [ ] スキル標準構造のテンプレートが存在する
- [ ] スキルプリロード仕様書が完成している

### フェーズ 1 完了基準

**Wave 0（基盤スキル）**:
- [ ] skill-expert スキルがスキル作成とフロントマターレビューをサポートする
- [ ] agent-expert スキルがエージェント作成とフロントマターレビューをサポートする
- [ ] workflow-expert スキルがワークフロー設計をサポートする

**Wave 1（レポジトリ管理スキル）**:
- [ ] index スキルが `/index --update` と同等の機能を持つ
- [ ] project-management スキルが GitHub Project と project.md を同期できる
- [ ] task-decomposition スキルが依存関係解析・類似タスク判定をサポートする
- [ ] issue-management スキルが Issue の作成・実装・ブラッシュアップ・同期をサポートする

**全体**:
- [ ] 全スキルで `make check-all` が成功する
- [ ] 移行元コマンド/スキルが削除されている
- [ ] 統合テストが通過する

#### フェーズ1 検証手順

**Wave 0: 基盤スキル検証**

1. **skill-expert スキル検証**
   - 新規スキル作成時にテンプレートが適用されることを確認
   - フロントマターレビュー機能の動作確認

2. **agent-expert スキル検証**
   - エージェントフロントマターのレビュー機能確認
   - skills: フィールドの検証動作確認

3. **workflow-expert スキル検証**
   - ワークフロー設計ガイドの参照確認

**Wave 1: レポジトリ管理スキル検証**

4. **index スキル検証**
   ```bash
   # 表示モード
   /index
   # 更新モード
   /index --update
   # 出力比較（既存と新規）
   ```

5. **プロジェクト管理スキル検証**
   ```bash
   # 新規プロジェクト作成
   /new-project "テストプロジェクト"
   # 整合性検証
   /project-refine @docs/project/test-project.md
   ```

6. **タスク分解スキル検証**
   - task-decomposer エージェントがスキルを参照して動作することを確認
   - 依存関係グラフがMermaid形式で出力されることを確認

7. **Issue管理スキル検証**
   ```bash
   # Issue作成
   /issue @docs/project/test-project.md
   # Issue自動実装
   /issue-implement #XXX
   # Issueブラッシュアップ
   /issue-refine #XXX
   # コメント同期
   /sync-issue #XXX
   ```

### フェーズ 2 完了基準

#### スキル作成
- [ ] `.claude/skills/coding-standards/` が存在し、SKILL.md, guide.md, examples/ が揃っている
- [ ] `.claude/skills/tdd-development/` が存在し、SKILL.md, guide.md, templates/ が揃っている
- [ ] `.claude/skills/error-handling/` が存在し、SKILL.md, guide.md, examples/ が揃っている

#### エージェント更新
- [ ] `feature-implementer.md` が `skills: [coding-standards, tdd-development, error-handling]` を参照
- [ ] `code-simplifier.md` が `skills: [coding-standards, error-handling]` を参照
- [ ] `quality-checker.md` が `skills: [coding-standards]` を参照
- [ ] テスト関連エージェント群が `skills: [tdd-development, coding-standards]` を参照

#### 品質確認
- [ ] `make check-all` が成功
- [ ] 既存のテストが全てパス

#### フェーズ2 検証手順

1. **スキル参照テスト**: feature-implementerエージェントを起動し、coding-standardsスキルが参照されることを確認
2. **TDDワークフローテスト**: /write-testsコマンドを実行し、tdd-developmentスキルのテンプレートが使用されることを確認
3. **エラー設計テスト**: 新規パッケージでerror-handlingスキルを参照し、例外クラスが適切に生成されることを確認

---

## リスクと緩和策

| リスク | 緩和策 |
|--------|--------|
| スキルプリロードでプロンプトが長くなりすぎる | guide.md は必要時のみ読み込み |
| 移行中の機能破壊 | 移行検証テストで同等性を確認 |
| gh CLI 認証エラー | 明確なエラーメッセージと `gh auth login` 案内 |
| MCP ツールの動作不安定 | Bash + gh CLI へのフォールバック手順を guide.md に記載 |

---

## 決定事項（フェーズ2追加）

| 項目 | 決定内容 |
|------|----------|
| Pythonスクリプト | **実装しない**（既存ツール ruff/pyright/pytest を活用） |
| docs/coding-standards.md | スキルへ移行（docs/はスキルへの参照リンクのみ残す） |
| docs/testing-strategy.md | スキルへ移行（docs/はスキルへの参照リンクのみ残す） |

---

## 次のアクション

1. **GitHub Project「System Update」の作成**（フェーズ0）
2. **Issue #1-#19 を作成**（フェーズ1: スキル作成・統合）
3. **Wave 0 のスキル作成開始**（skill-expert, agent-expert, workflow-expert を並列・最優先）
4. **Wave 1 のスキル作成**（index, project-management, task-decomposition, issue-management を並列）

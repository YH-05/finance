# フェーズ 1: レポジトリ管理スキル

> 元ドキュメント: `2026-01-21_System-Update-Implementation.md`

## 目標

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

---

## ツール活用ガイド

スキルは基本的に既存ツールを活用するが、必要な機能をカバーするためにPythonスクリプトの実装が必要な場合は適宜実装を行う。

### ディレクトリ操作

```bash
# ディレクトリツリー取得（MCP）
mcp__filesystem__directory_tree(path=".", excludePatterns=["node_modules", ".git", "__pycache__"])

# ファイル検索（MCP）
mcp__filesystem__search_files(path=".", pattern="**/*.md")
```

### GitHub 操作

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

### ファイル操作

```
# 組み込みツール
Read    - ファイル読み取り
Write   - ファイル書き込み
Edit    - ファイル編集（マーカーセクション更新等）
Glob    - パターンマッチング
Grep    - 正規表現検索
```

---

## タスク分解 (GitHub Issue)

### Wave 0: 基盤スキル（最優先・並列実装可）

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

### Wave 1: レポジトリ管理スキル（並列実装可）

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

### Wave 2: 統合

| # | タイトル | 工数 | 依存 |
|---|---------|------|------|
| 19 | [スキル移行] フェーズ1全スキルの統合テスト実施 | M | #4, #6, #9, #12, #15, #18 |

### 依存関係グラフ

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

## 1.1 index スキル

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

## 1.2 プロジェクト管理スキル

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

## 1.3 タスク分解スキル

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

## 1.4 Issue管理スキル

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

## 1.5 エージェント管理スキル（agent-expert 拡張）

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

## 1.6 スキル管理スキル（skill-expert 新規）

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

## 1.7 ワークフロー管理スキル（workflow-expert 新規）

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

## 受け入れ条件（詳細）

### Wave 0: 基盤スキル

#### Issue #1: skill-expert SKILL.md

- [ ] スキル設計原則記載
- [ ] スキルカテゴリ分類記載
- [ ] 活用ツールの使用方法記載
- [ ] 使用例 3つ以上

#### Issue #2: skill-expert guide.md

- [ ] スキル構造（SKILL.md + guide.md + examples/）の説明
- [ ] プロンプトエンジニアリングガイド
- [ ] スキルフロントマター検証ルール

#### Issue #3: skill-expert template.md

- [ ] スキル用フロントマター構造
- [ ] スキルセクション構成
- [ ] コメント付きガイド

#### Issue #4: agent-expert フロントマターレビュー機能

- [ ] エージェントフロントマター検証ルール
- [ ] skills: フィールドの検証
- [ ] allowed-tools の検証
- [ ] 既存 guide.md と整合性

#### Issue #5: workflow-expert SKILL.md

- [ ] ワークフロー設計原則記載
- [ ] マルチエージェント連携パターン記載
- [ ] 使用例 3つ以上

#### Issue #6: workflow-expert guide.md

- [ ] ワークフロー設計手順
- [ ] スキル連携パターン
- [ ] オーケストレーション設計

### Wave 1: レポジトリ管理スキル

#### Issue #7: index スキル SKILL.md

- [ ] skill-expert テンプレートに準拠
- [ ] 既存 /index コマンドの機能を網羅
  - 表示モード（/index）
  - 更新モード（/index --update）
  - コマンド、スキル、エージェント、ディレクトリ構成
- [ ] 活用ツールの使用方法記載（`mcp__filesystem__directory_tree`, `Glob`, `Edit`）
- [ ] 使用例 3つ以上

#### Issue #8: index スキル guide.md

- [ ] CLAUDE.md 更新手順
- [ ] README.md 更新手順
- [ ] マーカーセクション形式の説明
- [ ] 除外パターン一覧

#### Issue #9: /index 置換

- [ ] .claude/commands/index.md が index スキルを呼び出すよう変更
- [ ] /index と /index --update が動作
- [ ] 移行検証テスト通過
- [ ] 既存機能と同等の出力

#### Issue #10: プロジェクト管理スキル SKILL.md

- [ ] skill-expert テンプレートに準拠
- [ ] 統合対象の機能を網羅
  - /new-project（パッケージ/軽量モード）
  - /project-refine（整合性検証、自動修正）
  - project-file スキル（project.md テンプレート）
  - project-status-sync スキル（完了状態同期）
- [ ] 各モードの使い分け記載
- [ ] 活用ツールの使用方法記載（`gh project`, `gh issue`, `Read`, `Edit`）
- [ ] 使用例 3つ以上

#### Issue #11: プロジェクト管理スキル guide.md

- [ ] GitHub Project 操作手順（gh CLI）
- [ ] project.md パース形式（パッケージ/軽量）
- [ ] 双方向同期ルール（GitHub が Single Source of Truth）
- [ ] ステータス更新フロー

#### Issue #12: プロジェクト管理置換

- [ ] /new-project がプロジェクト管理スキルを使用
- [ ] /project-refine がプロジェクト管理スキルを使用
- [ ] project-status-sync スキルが統合
- [ ] 移行検証テスト通過

#### Issue #13: タスク分解スキル SKILL.md

- [ ] skill-expert テンプレートに準拠
- [ ] task-decomposer エージェントの機能を網羅
  - 依存関係解析
  - 類似タスク判定
  - Mermaid形式での可視化
- [ ] 活用ツールの使用方法記載
- [ ] 使用例 3つ以上

#### Issue #14: タスク分解スキル guide.md

- [ ] 依存関係解析手順（Claude の推論能力活用）
- [ ] 循環依存検出方法
- [ ] 類似タスク判定基準
- [ ] Mermaid 形式での可視化方法

#### Issue #15: task-decomposer エージェント統合

- [ ] task-decomposer エージェントがタスク分解スキルを参照
- [ ] 移行検証テスト通過

#### Issue #16: Issue管理スキル SKILL.md

- [ ] skill-expert テンプレートに準拠
- [ ] 統合対象の機能を網羅
  - /issue（3モード: quick_add/package/lightweight）
  - /issue-implement（開発タイプ判定、5フェーズワークフロー）
  - /issue-refine（8項目ユーザー詳細確認）
  - /sync-issue（コメント同期、確信度ベース確認）
- [ ] 各入力モード記載
- [ ] 活用ツールの使用方法記載（`gh issue`, `gh project`）
- [ ] 使用例 3つ以上

#### Issue #17: Issue管理スキル guide.md

- [ ] Issue 作成手順（3モード）
- [ ] Issue 自動実装ワークフロー
- [ ] Issue ブラッシュアップ手順
- [ ] コメント同期フロー

#### Issue #18: issue 系コマンド置換

- [ ] /issue がIssue管理スキルを使用
- [ ] /issue-implement がIssue管理スキルを使用
- [ ] /issue-refine がIssue管理スキルを使用
- [ ] /sync-issue がIssue管理スキルを使用
- [ ] 移行検証テスト通過

### Wave 2: 統合

#### Issue #19: 統合テスト

- [ ] 全スキルが連携して動作
- [ ] 既存コマンドとの機能同等性検証
- [ ] エッジケーステスト実施
- [ ] ドキュメント最終更新

---

## 検証戦略

スキルは基本的にナレッジベースとして機能するため、以下の検証を実施。Pythonスクリプトを含むスキルについては、該当スクリプトのユニットテストも追加する。

| 種別 | 対象 | 検証方法 |
|------|------|---------|
| 機能同等性検証 | 各スキル | 既存コマンドと同等の出力を確認 |
| ツール連携検証 | MCP/gh CLI | 実際のツール呼び出しで動作確認 |
| スキル参照検証 | エージェント | `skills:` フィールドでのロード確認 |

---

## 完了基準

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

---

## 検証手順

### Wave 0: 基盤スキル検証

1. **skill-expert スキル検証**
   - 新規スキル作成時にテンプレートが適用されることを確認
   - フロントマターレビュー機能の動作確認

2. **agent-expert スキル検証**
   - エージェントフロントマターのレビュー機能確認
   - skills: フィールドの検証動作確認

3. **workflow-expert スキル検証**
   - ワークフロー設計ガイドの参照確認

### Wave 1: レポジトリ管理スキル検証

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
| `.claude/agents/task-decomposer.md` | タスク分解スキル参照を追加、`skills: [task-decomposition]` |

---

## 関連ドキュメント

- [フェーズ0: 基盤整備](./2026-01-21_Phase-0_Foundation.md)
- [フェーズ2: コーディング+Git操作スキル](./2026-01-21_Phase-2_Coding-Git-Skills.md)
- [フェーズ3: 金融分析スキル](./2026-01-21_Phase-3_Finance-Skills.md)

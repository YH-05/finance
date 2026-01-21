# フェーズ1 詳細実装計画: スキルベースシステム移行

## エグゼクティブサマリー

既存のコマンドベースシステムをスキルベースシステムに移行し、4つのスキル（index、プロジェクト管理、タスク分解、エージェント/スキル管理）を実装する。

## 決定事項

| 項目 | 決定内容 | 備考 |
|------|----------|------|
| スキルプリロード | ハイブリッド方式（明示的指示 + 将来の自動展開準備） | 下記詳細参照 |
| 移行方式 | 即時置換（並存期間なし） | スキル完成後すぐに既存コマンド削除 |
| 実行環境 | uv run | pyproject.tomlで依存関係管理 |
| 実装順序 | 並列実装 | Wave単位で並列化 |

---

## スキルプリロード実装方式

### 採用方式: フロントマター依存関係宣言

エージェント/スキルのフロントマターに `depends-on:` を記述し、エージェントが実行時に参照してロードする方式を採用。

```yaml
---
name: project-management
description: プロジェクト管理統合スキル
depends-on:
  - common/github-api
  - common/project-md-parser
allowed-tools: Read, Edit, Bash, Grep, Task
---

# プロジェクト管理スキル

フロントマターに記載された依存スキルを参照し、必要に応じてロードしてください。
```

**メリット**:
- フロントマターで依存関係が明示される
- エージェントが自律的に必要なスキルをロード
- 将来のClaude Code機能拡張で自動展開が可能になった場合も対応可能

### 共通スキルフォルダの新設

```
.claude/skills/
├── common/                    # 共通モジュール（新設）
│   ├── github-api/
│   │   ├── SKILL.md
│   │   └── api_reference.md
│   ├── project-md-parser/
│   │   ├── SKILL.md
│   │   └── format_spec.md
│   └── markdown-utils/
│       ├── SKILL.md
│       └── markers.md
├── index/                     # 新規スキル
├── project-management/        # 新規スキル
├── task-decomposition/        # 新規スキル
└── agent-expert/             # 拡張
```

---

## アーキテクチャ

### スキル構造（標準）

```
.claude/skills/{skill-name}/
├── SKILL.md           # エントリーポイント（必須）
├── guide.md           # 詳細ガイド（オプション）
├── template.md        # 出力テンプレート（オプション）
└── scripts/           # Pythonスクリプト（オプション）
    ├── __init__.py
    └── {module}.py
```

### 共通モジュール

| モジュール | 目的 | 主要機能 |
|-----------|------|---------|
| `github_api.py` | gh CLI ラッパー | Issue CRUD, Project操作, Item編集 |
| `project_md_parser.py` | project.md パーサー | 2モード対応（パッケージ/軽量） |
| `markdown_utils.py` | マークダウン処理 | マーカーペア処理, チェックボックス操作 |

---

## Python スクリプト API 設計

### 1. directory_scanner.py (index スキル)

```python
# 入力
scan_directory(
    root: Path,
    depth: int = 4,
    excludes: list[str] | None = None,
    annotations: dict[str, str] | None = None,
) -> ScanResult

# 出力
ScanResult = {
    "root": str,
    "depth": int,
    "excludes": list[str],
    "structure": DirectoryNode,  # 再帰的なツリー構造
    "stats": {"files_count": int, "directories_count": int}
}

# CLI
uv run python .claude/skills/index/scripts/directory_scanner.py \
    --root . --depth 4 --output tree
```

### 2. document_updater.py (index スキル)

```python
# 入力
update_marker_content(
    file_path: Path,
    marker: str,  # "DIRECTORY", "COMMANDS", "SKILLS", "AGENTS"
    new_content: str,
    dry_run: bool = False,
) -> UpdateResult

# 出力
UpdateResult = {
    "file": str,
    "marker": str,
    "updated": bool,
    "old_content_length": int,
    "new_content_length": int,
    "error": str | None
}

# CLI
uv run python .claude/skills/index/scripts/document_updater.py \
    --file CLAUDE.md --marker DIRECTORY --content-file tree.txt
```

### 3. project_sync.py (プロジェクト管理スキル)

```python
# 入力
sync_github_to_md(project_number: int, md_path: Path, dry_run: bool = False) -> SyncResult
sync_md_to_github(project_number: int, md_path: Path, dry_run: bool = False) -> SyncResult

# 出力
SyncResult = {
    "direction": str,
    "items_synced": int,
    "items_created": int,
    "items_updated": int,
    "conflicts": list[dict],
    "errors": list[str]
}

# CLI
uv run python .claude/skills/project-management/scripts/project_sync.py \
    --project 14 --md-file docs/project/README.md --direction github-to-md
```

### 4. dependency_analyzer.py (タスク分解スキル)

```python
# 入力
analyze(
    input_source: Path | list[int],  # project.md または Issue番号リスト
    priority_map: dict[int, str] | None = None,
) -> AnalysisResult

# 出力
AnalysisResult = {
    "graph": DependencyGraph,  # nodes, edges, cycles, topological_order
    "priority_issues": list[dict],
    "orphan_nodes": list[int],
    "blocking_bottlenecks": list[dict]
}

# CLI
uv run python .claude/skills/task-decomposition/scripts/dependency_analyzer.py \
    --input docs/project/README.md --format mermaid
```

---

## タスク分解 (GitHub Issue)

### Wave 1: 基盤モジュール（並列実装可）

| # | タイトル | 工数 | 依存 |
|---|---------|------|------|
| 1 | [スキル移行] 共通モジュール github_api.py の実装 | M | なし |
| 2 | [スキル移行] 共通モジュール project_md_parser.py の実装 | M | なし |
| 3 | [スキル移行] 共通モジュール markdown_utils.py の実装 | S | なし |

### Wave 2: スキル実装（並列実装可、各スキル内は逐次）

**index スキル**

| # | タイトル | 工数 | 依存 |
|---|---------|------|------|
| 4 | [スキル移行] index スキル directory_scanner.py の実装 | M | なし |
| 5 | [スキル移行] index スキル document_updater.py の実装 | S | #3 |
| 6 | [スキル移行] index スキル SKILL.md の作成 | S | #4, #5 |
| 7 | [スキル移行] 既存 /index コマンドを index スキルに置換 | S | #6 |

**プロジェクト管理スキル**

| # | タイトル | 工数 | 依存 |
|---|---------|------|------|
| 8 | [スキル移行] プロジェクト管理スキル project_sync.py の実装 | L | #1, #2 |
| 9 | [スキル移行] プロジェクト管理スキル SKILL.md の作成 | M | #8 |
| 10 | [スキル移行] 既存プロジェクト管理コマンド/スキルを置換 | M | #9 |

**タスク分解スキル**

| # | タイトル | 工数 | 依存 |
|---|---------|------|------|
| 11 | [スキル移行] タスク分解スキル dependency_analyzer.py の実装 | L | #2 |
| 12 | [スキル移行] タスク分解スキル SKILL.md の作成 | M | #11 |
| 13 | [スキル移行] 既存タスク分解コマンド/エージェントを置換 | L | #12 |

**agent-expert スキル拡張**

| # | タイトル | 工数 | 依存 |
|---|---------|------|------|
| 14 | [スキル移行] agent-expert スキルに skill-guide.md を追加 | S | なし |
| 15 | [スキル移行] agent-expert スキルに skill-template.md を追加 | S | #14 |

### Wave 3: 統合

| # | タイトル | 工数 | 依存 |
|---|---------|------|------|
| 16 | [スキル移行] フェーズ1全スキルの統合テスト実施 | M | #7, #10, #13, #15 |

### 依存関係グラフ

```
Wave 1 (並列)     Wave 2 (スキル別並列)              Wave 3
┌─────┐
│ #1  │──────────────────┬──────────────> #8 -> #9 -> #10 ─┐
└─────┘                  │                                  │
┌─────┐                  │                                  │
│ #2  │──────────────────┼──────────────> #11 -> #12 -> #13─┼─> #16
└─────┘                  │                                  │
┌─────┐                  │                                  │
│ #3  │──────> #5 ───────┼──> #4 ─> #6 -> #7 ──────────────┤
└─────┘                                                     │
                         #14 -> #15 ────────────────────────┘
```

---

## 受け入れ条件（詳細）

### Issue #1: github_api.py

- [ ] GitHubClient クラスが gh CLI をラップしている
- [ ] Issue 操作: list_issues, get_issue, create_issue, update_issue, close_issue
- [ ] Project 操作: list_project_items, get_project_fields, add_item_to_project, update_project_item_status
- [ ] 認証エラー時に GitHubAPIError を raise し、`gh auth login` を案内
- [ ] rate limit エラー時にリトライロジック
- [ ] ユニットテスト 80%+ カバレッジ
- [ ] make check-all 成功

### Issue #2: project_md_parser.py

- [ ] パッケージモード（`#### 機能 X.X:` 形式）のパース
- [ ] 軽量モード（`- [ ] タスク` 形式）のパース
- [ ] モード自動検出 (detect_mode)
- [ ] メタデータ抽出（GitHub Project 番号、ステータス、作成日等）
- [ ] タスクステータス更新 (update_task_status)
- [ ] シリアライズ (serialize) でMarkdownに戻す
- [ ] ユニットテスト 80%+ カバレッジ
- [ ] make check-all 成功

### Issue #3: markdown_utils.py

- [ ] マーカーセクション検出 (find_marker_sections)
- [ ] マーカーセクション更新 (update_marker_section)
- [ ] チェックボックス検出 (find_checkboxes)
- [ ] チェックボックス更新 (toggle_checkbox, update_checkboxes_by_pattern)
- [ ] テーブル抽出/生成 (extract_table_rows, build_table)
- [ ] ユニットテスト 80%+ カバレッジ
- [ ] プロパティテスト追加
- [ ] make check-all 成功

### Issue #4: directory_scanner.py

- [ ] JSON形式出力
- [ ] ASCIIツリー形式出力
- [ ] 除外パターン適用（DEFAULT_EXCLUDES: 13パターン）
- [ ] アノテーション（コメント）付与
- [ ] CLAUDE.md の既存ディレクトリ構成と同等の出力
- [ ] ユニットテスト 80%+ カバレッジ
- [ ] make check-all 成功

### Issue #5: document_updater.py

- [ ] 単一ファイルのマーカー更新
- [ ] 複数ファイルのバッチ更新 (batch_update)
- [ ] dry-run モード
- [ ] markdown_utils.py を使用
- [ ] ユニットテスト 80%+ カバレッジ
- [ ] make check-all 成功

### Issue #6: index スキル SKILL.md

- [ ] agent-expert テンプレートに準拠
- [ ] 既存 /index コマンドの機能を網羅
  - 表示モード（/index）
  - 更新モード（/index --update）
  - 37コマンド、13スキル、18エージェント、ディレクトリ構成
- [ ] Python スクリプトの使用方法記載
- [ ] 使用例 3つ以上

### Issue #7: /index 置換

- [ ] .claude/commands/index.md が index スキルを呼び出すよう変更
- [ ] /index と /index --update が動作
- [ ] 移行検証テスト通過
- [ ] 既存機能と同等の出力

### Issue #8: project_sync.py

- [ ] GitHub → MD 同期 (sync_github_to_md)
- [ ] MD → GitHub 同期 (sync_md_to_github)
- [ ] 双方向同期（GitHub優先）
- [ ] github_api.py と project_md_parser.py を使用
- [ ] 競合解決ルール実装（GitHub が Single Source of Truth）
- [ ] ユニットテスト 80%+ カバレッジ
- [ ] make check-all 成功

### Issue #9: プロジェクト管理スキル SKILL.md

- [ ] agent-expert テンプレートに準拠
- [ ] 統合対象の機能を網羅
  - /new-project（パッケージ/軽量モード）
  - /project-refine（整合性検証、自動修正）
  - project-file スキル（project.md テンプレート）
  - project-status-sync スキル（完了状態同期）
- [ ] 各モードの使い分け記載
- [ ] Python スクリプトの使用方法記載
- [ ] 使用例 3つ以上

### Issue #10: プロジェクト管理置換

- [ ] /new-project がプロジェクト管理スキルを使用
- [ ] /project-refine がプロジェクト管理スキルを使用
- [ ] project-status-sync スキルが統合
- [ ] 移行検証テスト通過

### Issue #11: dependency_analyzer.py

- [ ] 依存グラフ構築（project.md / Issue リストから）
- [ ] 循環依存検出（DFS アルゴリズム）
- [ ] トポロジカルソート
- [ ] 優先度矛盾検出
- [ ] 孤立ノード検出
- [ ] ボトルネック検出（多くをブロック）
- [ ] Mermaid 形式出力
- [ ] ユニットテスト 80%+ カバレッジ
- [ ] make check-all 成功

### Issue #12: タスク分解スキル SKILL.md

- [ ] agent-expert テンプレートに準拠
- [ ] 統合対象の機能を網羅
  - /issue（3モード: quick_add/package/lightweight）
  - /issue-implement（開発タイプ判定、5フェーズワークフロー）
  - /issue-refine（8項目ユーザー詳細確認）
  - /sync-issue（コメント同期、確信度ベース確認）
  - task-decomposer エージェント（類似性判定、依存関係解析）
- [ ] 各入力モード記載
- [ ] Python スクリプトの使用方法記載
- [ ] 使用例 3つ以上

### Issue #13: タスク分解置換

- [ ] /issue がタスク分解スキルを使用
- [ ] /issue-implement がタスク分解スキルを使用
- [ ] /issue-refine がタスク分解スキルを使用
- [ ] /sync-issue がタスク分解スキルを使用
- [ ] task-decomposer エージェントがスキルに統合
- [ ] 移行検証テスト通過

### Issue #14: skill-guide.md

- [ ] スキル設計原則
- [ ] スキルカテゴリ分類
- [ ] プロンプトエンジニアリングガイド
- [ ] 既存 guide.md と整合性

### Issue #15: skill-template.md

- [ ] スキル用フロントマター構造
- [ ] スキルセクション構成
- [ ] コメント付きガイド
- [ ] 既存 template.md と整合性

### Issue #16: 統合テスト

- [ ] 全スキルが連携して動作
- [ ] 既存コマンドとの機能同等性検証
- [ ] エッジケーステスト追加
- [ ] ドキュメント最終更新

---

## テスト戦略

### ディレクトリ構造

```
tests/
├── skills/
│   ├── index/
│   │   ├── unit/
│   │   │   ├── test_directory_scanner.py
│   │   │   └── test_document_updater.py
│   │   └── integration/
│   │       └── test_index_skill.py
│   ├── project_management/
│   │   ├── unit/
│   │   │   └── test_project_sync.py
│   │   └── integration/
│   │       └── test_project_management_skill.py
│   ├── task_decomposition/
│   │   ├── unit/
│   │   │   └── test_dependency_analyzer.py
│   │   └── integration/
│   │       └── test_task_decomposition_skill.py
│   └── common/
│       ├── unit/
│       │   ├── test_github_api.py
│       │   ├── test_project_md_parser.py
│       │   └── test_markdown_utils.py
│       └── property/
│           └── test_markdown_utils_property.py
```

### テスト種別

| 種別 | 対象 | カバレッジ目標 |
|------|------|---------------|
| ユニットテスト | 各Python関数 | 80%+ |
| 統合テスト | gh CLI連携（モック使用） | 主要フロー |
| 移行検証テスト | 既存コマンドとの同等性 | 全機能 |
| プロパティテスト | markdown_utils.py | エッジケース |

---

## 重要ファイル一覧

### 移行元（参照）

| ファイル | 役割 |
|---------|------|
| `.claude/commands/index.md` | 9サブエージェント並列実行アーキテクチャ |
| `.claude/commands/new-project.md` | インタビュー→計画書→GitHub Project→Issue |
| `.claude/commands/project-refine.md` | 循環依存検出、ステータス不整合修正 |
| `.claude/commands/issue.md` | 3モード（quick_add/package/lightweight） |
| `.claude/agents/task-decomposer.md` | 類似性判定、依存関係解析 |
| `.claude/skills/project-status-sync/SKILL.md` | GitHub Project同期パターン |
| `.claude/skills/agent-expert/template.md` | スキル作成テンプレート |

### 新規作成

| ファイル | 内容 |
|---------|------|
| `.claude/skills/common/github-api/` | gh CLI ラッパー |
| `.claude/skills/common/project-md-parser/` | project.md パーサー |
| `.claude/skills/common/markdown-utils/` | マーカー/チェックボックス処理 |
| `.claude/skills/index/` | index スキル一式 |
| `.claude/skills/project-management/` | プロジェクト管理スキル一式 |
| `.claude/skills/task-decomposition/` | タスク分解スキル一式 |
| `.claude/skills/agent-expert/skill-guide.md` | スキル設計ガイド |
| `.claude/skills/agent-expert/skill-template.md` | スキルテンプレート |

### 変更対象

| ファイル | 変更内容 |
|---------|----------|
| `.claude/commands/index.md` | index スキル呼び出しに変更後、削除 |
| `.claude/commands/new-project.md` | プロジェクト管理スキル呼び出しに変更後、削除 |
| `.claude/commands/project-refine.md` | プロジェクト管理スキル呼び出しに変更後、削除 |
| `.claude/commands/issue.md` | タスク分解スキル呼び出しに変更後、削除 |
| `.claude/skills/project-file/` | プロジェクト管理スキルに統合後、削除 |
| `.claude/skills/project-status-sync/` | プロジェクト管理スキルに統合後、削除 |

---

## 検証方法

### フェーズ1完了基準

- [ ] index スキルが `/index --update` と同等の機能を持つ
- [ ] project-management スキルが GitHub Project と project.md を同期できる
- [ ] task-decomposition スキルが Issue を作成・管理できる
- [ ] agent-expert スキルがスキル作成をサポートする
- [ ] 全スキルで `make check-all` が成功する
- [ ] 移行元コマンド/スキルが削除されている
- [ ] 統合テストが通過する

### 検証手順

1. **index スキル検証**
   ```bash
   # 表示モード
   /index
   # 更新モード
   /index --update
   # 出力比較（既存と新規）
   ```

2. **プロジェクト管理スキル検証**
   ```bash
   # 新規プロジェクト作成
   /new-project "テストプロジェクト"
   # 整合性検証
   /project-refine @docs/project/test-project.md
   ```

3. **タスク分解スキル検証**
   ```bash
   # Issue作成
   /issue @docs/project/test-project.md
   # コメント同期
   /sync-issue #XXX
   ```

---

## リスクと緩和策

| リスク | 緩和策 |
|--------|--------|
| スキルプリロードでプロンプトが長くなりすぎる | 共通スキルは必要時のみロード、guide.md は必要時のみ読み込み |
| Python スクリプトの実行エラー | uv run での実行を標準化、詳細なエラーメッセージ |
| 移行中の機能破壊 | 移行検証テストで同等性を確認 |
| gh CLI 認証エラー | 明確なエラーメッセージと `gh auth login` 案内 |

---

## 次のアクション

1. **GitHub Project「System Update」の作成**（フェーズ0）
2. **Issue #1-#3 を作成**（Wave 1: 基盤モジュール）
3. **Issue #4-#15 を作成**（Wave 2: スキル実装）
4. **Issue #16 を作成**（Wave 3: 統合テスト）
5. **Wave 1 の並列実装開始**

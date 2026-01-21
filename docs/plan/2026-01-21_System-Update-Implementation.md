# System Update: スキルベースシステムへのマイグレーション計画

## エグゼクティブサマリー

既存のコマンドベースシステムをスキルベースのシステムに移行し、エージェントへのスキルプリロード機構を実装する。これにより、より柔軟で保守性の高いシステムを実現する。

## 決定事項

| 項目 | 決定内容 |
|------|----------|
| 移行範囲 | ワークフロー/複雑ロジックを含むコマンドを優先 |
| 後方互換性 | コマンドは廃止（スキル移行後、削除） |
| スキル構造 | スキル内埋め込み（`.claude/skills/{skill}/scripts/`） |
| スキルプリロード | フロントマター方式、エージェント定義内で展開 |
| エージェント移行 | 段階的移行（新規スキル作成時に関連エージェントを更新） |
| 開始カテゴリ | レポジトリ管理 |
| GitHub Project | 新規「System Update」を作成 |

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
└── scripts/           # Pythonスクリプト（オプション）
    ├── __init__.py
    └── {module}.py
```

### スキルプリロード実装方式

エージェント定義内で明示的にスキルを参照し、起動時に読み込む：

```markdown
---
name: feature-implementer
description: TDDループを自動実行
skills:
  - coding-standards
  - tdd-development
---

# 機能実装エージェント

## 参照スキル

以下のスキルの原則に従って実装してください：

1. **コーディング規約**: @.claude/skills/coding-standards/SKILL.md
2. **TDD開発**: @.claude/skills/tdd-development/SKILL.md

各スキルの内容を Read ツールで読み込み、規約に従って実装を進めてください。
```

---

## フェーズ 1: レポジトリ管理スキル

### 目標
4つのスキルを最初に実装：
1. index スキル
2. プロジェクト管理スキル
3. タスク分解スキル
4. エージェント/スキル管理スキル

---

### 1.1 index スキル

**移行元**: `/index` コマンド（`.claude/commands/index.md`）

**構造**:
```
.claude/skills/index/
├── SKILL.md              # メイン定義
├── guide.md              # CLAUDE.md/README.md 更新ガイド
├── template.md           # ディレクトリ構成テンプレート
└── scripts/
    ├── __init__.py
    ├── directory_scanner.py   # ディレクトリスキャン
    └── document_updater.py    # ドキュメント更新
```

**機能**:
- CLAUDE.md の自動更新（ディレクトリ構成セクション）
- README.md の自動更新
- コマンド/スキル/エージェント一覧の検出
- ディレクトリ構造の可視化（4層まで）

**タスク**:

| # | タスク | 依存 | 成果物 |
|---|--------|------|--------|
| 1.1.1 | SKILL.md の作成 | 0.2 | `.claude/skills/index/SKILL.md` |
| 1.1.2 | guide.md の作成 | 1.1.1 | `.claude/skills/index/guide.md` |
| 1.1.3 | directory_scanner.py の実装 | 1.1.1 | `scripts/directory_scanner.py` |
| 1.1.4 | document_updater.py の実装 | 1.1.3 | `scripts/document_updater.py` |
| 1.1.5 | 既存 /index コマンドの移行・削除 | 1.1.4 | コマンド削除 |
| 1.1.6 | テスト・検証 | 1.1.5 | 動作確認 |

**scripts/directory_scanner.py の仕様**:
```python
# 入力: プロジェクトルートパス、最大深度、除外パターン
# 出力: JSON形式のディレクトリ構造
# 除外: __pycache__, .git, .venv, .pytest_cache, .ruff_cache, node_modules, *.egg-info
```

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
├── template.md           # project.md テンプレート
└── scripts/
    ├── __init__.py
    ├── project_sync.py       # GitHub Project 同期
    └── status_updater.py     # ステータス更新
```

**機能**:
- GitHub Project の作成・管理
- project.md の作成・編集
- GitHub Project と project.md の双方向同期
- ステータス自動更新（PR作成→In Progress、マージ→Done）

**タスク**:

| # | タスク | 依存 | 成果物 |
|---|--------|------|--------|
| 1.2.1 | 既存スキル（project-file, project-status-sync）の統合設計 | 0.2 | 設計ドキュメント |
| 1.2.2 | SKILL.md の作成 | 1.2.1 | `.claude/skills/project-management/SKILL.md` |
| 1.2.3 | guide.md の作成 | 1.2.2 | `.claude/skills/project-management/guide.md` |
| 1.2.4 | project_sync.py の実装 | 1.2.2 | `scripts/project_sync.py` |
| 1.2.5 | status_updater.py の実装 | 1.2.4 | `scripts/status_updater.py` |
| 1.2.6 | 既存コマンド・スキルの移行・削除 | 1.2.5 | 統合完了 |
| 1.2.7 | テスト・検証 | 1.2.6 | 動作確認 |

---

### 1.3 タスク分解スキル

**新規作成**: `.claude/skills/task-decomposition/`

**統合対象**:
- `/issue` コマンド
- `/issue-implement` コマンド
- `/issue-refine` コマンド
- `/sync-issue` コマンド
- `task-decomposer` エージェント

**構造**:
```
.claude/skills/task-decomposition/
├── SKILL.md              # メイン定義
├── guide.md              # タスク分解・依存関係管理ガイド
├── template.md           # Issue テンプレート
└── scripts/
    ├── __init__.py
    ├── issue_manager.py      # Issue 作成・更新
    └── dependency_analyzer.py # 依存関係解析
```

**機能**:
- 要件定義からの Issue 作成
- 依存関係の管理・可視化
- 類似 Issue の判定
- project.md との同期
- Issue コメントからの進捗同期

**タスク**:

| # | タスク | 依存 | 成果物 |
|---|--------|------|--------|
| 1.3.1 | task-decomposer エージェントの分析 | 0.2 | 分析レポート |
| 1.3.2 | SKILL.md の作成 | 1.3.1 | `.claude/skills/task-decomposition/SKILL.md` |
| 1.3.3 | guide.md の作成 | 1.3.2 | `.claude/skills/task-decomposition/guide.md` |
| 1.3.4 | issue_manager.py の実装 | 1.3.2 | `scripts/issue_manager.py` |
| 1.3.5 | dependency_analyzer.py の実装 | 1.3.4 | `scripts/dependency_analyzer.py` |
| 1.3.6 | 既存コマンドの移行・削除 | 1.3.5 | 統合完了 |
| 1.3.7 | task-decomposer エージェントの更新 | 1.3.6 | エージェント更新 |
| 1.3.8 | テスト・検証 | 1.3.7 | 動作確認 |

---

### 1.4 エージェント/スキル管理スキル

**拡張対象**: `.claude/skills/agent-expert/`

**既存の agent-expert スキルを拡張し、スキル・ワークフロー管理機能を追加**

**構造**:
```
.claude/skills/agent-expert/
├── SKILL.md              # メイン定義（拡張）
├── guide.md              # エージェント設計ガイド（既存）
├── template.md           # エージェントテンプレート（既存）
├── skill-guide.md        # スキル設計ガイド（新規）
├── skill-template.md     # スキルテンプレート（新規）
└── workflow-guide.md     # ワークフロー設計ガイド（新規）
```

**機能**:
- エージェントの作成・管理（既存）
- スキルの作成・管理（新規）
- ワークフローの設計・管理（新規）
- スキルプリロードの設定支援（新規）

**タスク**:

| # | タスク | 依存 | 成果物 |
|---|--------|------|--------|
| 1.4.1 | skill-guide.md の作成 | 0.3 | `.claude/skills/agent-expert/skill-guide.md` |
| 1.4.2 | skill-template.md の作成 | 1.4.1 | `.claude/skills/agent-expert/skill-template.md` |
| 1.4.3 | workflow-guide.md の作成 | 1.4.2 | `.claude/skills/agent-expert/workflow-guide.md` |
| 1.4.4 | SKILL.md の拡張 | 1.4.3 | SKILL.md 更新 |
| 1.4.5 | テスト・検証 | 1.4.4 | 動作確認 |

---

## フェーズ 2: コーディングスキル

### 目標
- Pythonコーディング規約スキル
- TDD開発スキル
- エラーハンドリングスキル

### 2.1 コーディング規約スキル

**新規作成**: `.claude/skills/coding-standards/`

```
.claude/skills/coding-standards/
├── SKILL.md              # メイン定義
├── guide.md              # 詳細コーディング規約
└── examples/
    ├── type-hints.md
    ├── docstrings.md
    └── error-messages.md
```

**プリロード対象エージェント**:
- `feature-implementer`
- `test-writer`
- `code-simplifier`
- `quality-checker`

### 2.2 TDD開発スキル

**新規作成**: `.claude/skills/tdd-development/`

```
.claude/skills/tdd-development/
├── SKILL.md              # メイン定義
├── guide.md              # TDD プロセスガイド
└── templates/
    ├── unit-test.md
    ├── property-test.md
    └── integration-test.md
```

**移行元**:
- `/write-tests` コマンド
- `test-writer` エージェント

### 2.3 エラーハンドリングスキル

**新規作成**: `.claude/skills/error-handling/`

```
.claude/skills/error-handling/
├── SKILL.md              # メイン定義
├── guide.md              # エラーハンドリングガイド
└── examples/
    ├── custom-exceptions.md
    ├── retry-patterns.md
    └── logging-patterns.md
```

---

## フェーズ 3: 金融分析スキル（後続フェーズ）

- yfinance ベストプラクティススキル
- 市場分析スキル
- SEC EDGAR スキル
- リターン計算スキル
- RSS読み取りスキル
- Web検索スキル

---

## フェーズ 4: 記事執筆スキル（後続フェーズ）

- 記事構成スキル
- 批評・推敲スキル
- コンプライアンススキル

---

## 重要ファイル

### 変更対象

| ファイル | 変更内容 |
|----------|----------|
| `.claude/skills/agent-expert/SKILL.md` | スキル・ワークフロー管理機能を追加 |
| `.claude/commands/index.md` | スキルへ移行後、削除 |
| `.claude/agents/feature-implementer.md` | スキルプリロード参照を追加 |
| `.claude/agents/task-decomposer.md` | タスク分解スキル参照を追加 |
| `.claude/commands/new-project.md` | project-management スキルへ統合後、削除 |

### 新規作成

| ファイル | 内容 |
|----------|------|
| `.claude/skills/index/` | index スキル一式 |
| `.claude/skills/project-management/` | プロジェクト管理スキル一式 |
| `.claude/skills/task-decomposition/` | タスク分解スキル一式 |
| `.claude/skills/coding-standards/` | コーディング規約スキル一式 |
| `.claude/skills/tdd-development/` | TDD開発スキル一式 |
| `.claude/skills/error-handling/` | エラーハンドリングスキル一式 |
| `docs/skill-preload-spec.md` | スキルプリロード仕様書 |

---

## 検証方法

### フェーズ 0 完了基準
- [ ] GitHub Project「System Update」が作成されている
- [ ] スキル標準構造のテンプレートが存在する
- [ ] スキルプリロード仕様書が完成している

### フェーズ 1 完了基準
- [ ] index スキルが `/index --update` と同等の機能を持つ
- [ ] project-management スキルが GitHub Project と project.md を同期できる
- [ ] task-decomposition スキルが Issue を作成・管理できる
- [ ] agent-expert スキルがスキル作成をサポートする
- [ ] 全スキルで `make check-all` が成功する
- [ ] 移行元コマンドが削除されている

### フェーズ 2 完了基準
- [ ] coding-standards スキルが存在し、エージェントから参照可能
- [ ] tdd-development スキルが存在し、テストワークフローが動作する
- [ ] error-handling スキルが存在し、エージェントから参照可能
- [ ] feature-implementer エージェントがスキルを参照して動作する

---

## リスクと緩和策

| リスク | 緩和策 |
|--------|--------|
| スキルプリロードでプロンプトが長くなりすぎる | 必要最小限のスキルのみ参照、guide.md は必要時のみ読み込み |
| 移行中の機能破壊 | 段階的移行、テスト完了まで旧コマンドは並存 |
| Python スクリプトの実行エラー | uv run での実行を標準化、エラーハンドリングを実装 |

---

## 次のアクション

1. **GitHub Project「System Update」の作成**
2. **スキル標準構造テンプレートの作成**
3. **スキルプリロード仕様書の作成**
4. **index スキルの実装開始**

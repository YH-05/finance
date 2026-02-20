# finance プロジェクト分離 - 整理・分類計画

## Context

finance プロジェクトは Python 16パッケージ（約124,000行）、122+ エージェント、48+ スキル、24 コマンドを含む大規模モノリポに成長。関心の分離・Quants統合・規模縮小のため、まずは資産の正確な分類と依存関係を整理する。

**目的**: 実際の分離は後で判断。今は6グループへの分類と依存関係の明確化。
**優先**: A（汎用開発ツール）、E（AIリサーチ）

---

## 6グループ分類

### グループ A: 汎用開発フレームワーク

金融ドメインに依存しない開発ツール群。既に finance↔Quants 同期ルールあり。

**エージェント（70個）**

| カテゴリ | エージェント |
|---------|------------|
| テスト (8) | `test-lead`, `test-orchestrator`, `test-planner`, `test-unit-writer`, `test-property-writer`, `test-integration-writer`, `test-writer`, `feature-implementer` |
| 品質 (6) | `quality-checker`, `code-analyzer`, `code-simplifier`, `security-scanner`, `implementation-validator`, `improvement-implementer` |
| PRレビュー (7) | `pr-readability`, `pr-design`, `pr-performance`, `pr-security-code`, `pr-security-infra`, `pr-test-coverage`, `pr-test-quality` |
| ドキュメント (6) | `functional-design-writer`, `architecture-design-writer`, `repository-structure-writer`, `development-guidelines-writer`, `glossary-writer`, `doc-reviewer` |
| プロジェクト管理 (6) | `project-researcher`, `project-planner`, `project-decomposer`, `comment-analyzer`, `task-decomposer`, `package-readme-updater` |
| エキスパート (6) | `agent-creator`, `skill-creator`, `command-expert`, `workflow-designer`, `pydantic-model-designer`, `api-usage-researcher` |
| 実装 (3) | `issue-implementer`, `debugger`, `feature-implementer` |
| 実験的 (10) | `prototype-team-lead`, `prototype-worker-a/b`, `file-passing-team-lead`, `file-passing-worker-a/b`, `error-handling-team-lead`, `error-handling-worker-a/b/c` |

**スキル（37個）**

| カテゴリ | スキル |
|---------|-------|
| コーディング (8) | `coding-standards`, `tdd-development`, `error-handling`, `ensure-quality`, `analyze`, `improve`, `safe-refactor`, `troubleshoot` |
| Issue/プロジェクト (10) | `issue-creation`, `issue-refinement`, `issue-implementation-serial`, `issue-implement-single`, `issue-sync`, `project-implementation`, `plan-project`, `new-project`, `project-management`, `task-decomposition` |
| Git/Worktree (9) | `commit-and-pr`, `push`, `merge-pr`, `worktree`, `plan-worktrees`, `create-worktrees`, `worktree-done`, `delete-worktrees`, `analyze-conflicts` |
| レビュー (2) | `review-pr`, `review-docs` |
| エキスパート (4) | `agent-expert`, `skill-expert`, `workflow-expert`, `agent-memory` |
| ドキュメント設計 (6) | `prd-writing`, `functional-design`, `architecture-design`, `repository-structure`, `development-guidelines`, `glossary-creation` |
| その他 (5) | `scan`, `index`, `agent-teams-prototype`, `agent-teams-file-passing`, `agent-teams-error-handling` |

**コマンド（14個）**: `commit-and-pr`, `push`, `merge-pr`, `worktree`, `worktree-done`, `delete-worktrees`, `plan-project`, `plan-worktrees`, `task`, `write-tests`, `index`, `new-package`, `setup-repository`, `gemini-search`

**ルール（8個）**: `coding-standards`, `common-instructions`, `development-process`, `evidence-based`, `git-rules`, `testing-strategy`, `subagent-data-passing`, `README`

**その他**: `template/src/template_package/`（Pythonパッケージテンプレート）

**注意点**:
- 一部エージェントに金融ドメインの**例示参照**あり（`code-simplifier` 内の `from finance.utils.logging_config` 等）。実コード依存ではなく置換容易
- `common-instructions.md` の import 例も同様に置換可能

---

### グループ B: 金融データ基盤

市場データ取得・保存のコアインフラ。他グループの基盤。

**Python パッケージ（~37,400行）**

| パッケージ | 行数 | ファイル数 | 内部依存 |
|-----------|------|-----------|---------|
| `utils_core` | 1,083 | 6 | なし |
| `database` | 2,218 | 12 | `utils_core` |
| `market` | 31,141 | 72 | `utils_core` |
| `edgar` | 2,969 | 13 | `utils_core` |

**データ**: `data/raw/`（yfinance, FRED, RSS）, `data/config/`, `data/schemas/`, `data/duckdb/`, `data/sqlite/`

**外部API**: yfinance, FRED, SEC EDGAR, Bloomberg, NASDAQ

**utils_core の金融固有コード**:
- `settings.py:153-172` の `get_fred_api_key()` のみが金融固有
- 他の関数（`load_project_env`, `get_log_level` 等）は完全に汎用

---

### グループ C: 定量分析（Quants統合候補）

ファクター分析・投資戦略構築。既存 Quants プロジェクトとの統合候補。

**Python パッケージ（~35,750行）**

| パッケージ | 行数 | ファイル数 | 内部依存 |
|-----------|------|-----------|---------|
| `analyze` | 17,369 | 47 | `market`, `utils_core` |
| `factor` | 13,638 | 45 | `market`, `analyze`, `utils_core` |
| `strategy` | 4,750 | 23 | `utils_core`（integration層で market/analyze/factor を遅延import） |

**依存チェーン**: `strategy` → `factor` → `analyze` → `market`（3段の依存）

**データ**: `data/processed/`, `data/exports/`

---

### グループ D: コンテンツ・ニュースパイプライン

note.com コンテンツ発信に特化。RSS監視→記事抽出→LLM要約→GitHub Issue投稿。

**Python パッケージ（~31,350行）**

| パッケージ | 行数 | ファイル数 | 内部依存 |
|-----------|------|-----------|---------|
| `rss` | 12,262 | 48 | `utils_core` |
| `news` | 18,687 | 51 | `rss`, `utils_core` |
| `automation` | 401 | 4 | Claude Agent SDK 経由 |

**エージェント（24個）**: 記事作成(9), 記事批評(5), 週次レポート(10+)
**スキル（8個）**: `finance-news-workflow`, `ai-research-workflow`, `generate-market-report`, `weekly-*`(4)
**コマンド（6個）**: `/finance-suggest-topics`, `/new-finance-article`, `/finance-edit`, `/finance-full`, `/generate-market-report`, `/ai-research-collect`
**データ**: `template/`（記事テンプレート）, `snippets/`（免責事項等）

**GitHub Projects**: #15, #21, #24, #27, #34, #44

---

### グループ E: AIリサーチ・投資戦略（最アクティブ）

ディープリサーチ・競争優位性評価・AI投資戦略PoC。直近のコミットが最も集中。

**Python パッケージ（~8,300行）**

| パッケージ | 行数 | ファイル数 | 内部依存 |
|-----------|------|-----------|---------|
| `dev/ca_strategy` | 8,294 | 20 | `factor.core.normalizer`, `strategy.risk.calculator`, `utils_core` |

**エージェント（42個）**

| カテゴリ | エージェント |
|---------|------------|
| Deep Research (15) | `dr-orchestrator`, `dr-stock-lead`, `dr-industry-lead`, `ca-eval-lead`, `dr-macro-analyzer`, `dr-stock-analyzer`, `dr-sector-analyzer`, `dr-theme-analyzer`, `dr-source-aggregator`, `dr-cross-validator`, `dr-bias-detector`, `dr-confidence-scorer`, `dr-report-generator`, `dr-visualizer`, `industry-researcher` |
| CA Eval (6) | `ca-report-parser`, `ca-claim-extractor`, `ca-fact-checker`, `ca-pattern-verifier`, `ca-report-generator`, `competitive-advantage-critique` |
| CA Strategy (8) | `ca-strategy-lead`, `transcript-loader`, `transcript-claim-extractor`, `transcript-claim-scorer`, `score-aggregator`, `sector-neutralizer`, `portfolio-constructor`, `output-generator` |
| Research ワーカー (14) | `research-lead`, `finance-query-generator`, `finance-web`, `finance-wiki`, `finance-source`, `finance-claims`, `finance-claims-analyzer`, `finance-fact-checker`, `finance-decisions`, `finance-market-data`, `finance-technical-analysis`, `finance-economic-analysis`, `finance-sec-filings`, `finance-sentiment-analyzer`, `finance-visualize` |

**スキル（4個）**: `deep-research`, `dr-stock`, `dr-industry`, `ca-eval`
**コマンド（4個）**: `/dr-stock`, `/dr-industry`, `/ca-eval`, `/finance-research`
**データ**: `research/`, `data/Transcript/`（~260MB）, `analyst/`（KBルール集）

**Agent Teams ワーカー共有問題**: `finance-sec-filings`, `finance-market-data`, `finance-web`, `industry-researcher` は複数のリーダー（research-lead, dr-stock-lead, ca-eval-lead）で共有

**GitHub Projects**: #43, #47

---

### グループ F: NotebookLM（完全独立）

Playwright ベースの NotebookLM MCP サーバー。金融ドメインへの依存なし。

**Python パッケージ（~10,600行）**

| パッケージ | 行数 | ファイル数 | 内部依存 |
|-----------|------|-----------|---------|
| `notebooklm` | 10,631 | 28 | `utils_core.logging` のみ |

**GitHub Projects**: #48

---

## グループ間依存関係

```
A: 汎用開発ツール ──── 独立（全プロジェクトで共有可能）

F: NotebookLM ──────── 独立（utils_core.logging のみ）

B: 金融データ基盤
  ↑
  ├── C: 定量分析 ──── analyze→market, factor→market+analyze
  ├── D: コンテンツ ── news→rss, rss は utils_core のみ
  └── E: AIリサーチ ── ca_strategy→factor+strategy, ワーカー→market+edgar
             ↑
             └── C: 定量分析（ca_strategy が factor, strategy に依存）
```

### 重要な依存ポイント

| 依存元 | 依存先 | 具体的なコード |
|--------|--------|--------------|
| `dev/ca_strategy/neutralizer.py:14` | `factor.core.normalizer.Normalizer` | SectorNeutralizer が Normalizer をラップ |
| `dev/ca_strategy/evaluator.py` | `strategy.risk.calculator.RiskCalculator` | パフォーマンス評価 |
| `analyze/reporting/*.py` | `market.yfinance`, `market.fred` | レポート生成 |
| `factor/integration/*.py` | `market.yfinance`, `analyze.statistics` | データ取得連携 |
| `news/collectors/rss.py` | `rss.core.parser.FeedParser` | RSS収集 |
| 全パッケージ | `utils_core.logging.get_logger` | ロギング（204箇所） |
| `utils_core/settings.py:153` | `FRED_API_KEY` 環境変数 | 唯一の金融固有関数 |

---

## 分離難易度

| グループ | 難易度 | 理由 |
|---------|-------|------|
| **F: NotebookLM** | 容易 | 完全独立。logging を structlog 直接利用に置換するだけ |
| **A: 汎用開発ツール** | 容易〜中 | 既に同期ルールあり。例示内の金融参照を汎用化するだけ |
| **D: コンテンツ** | 中 | rss は独立性高い。news→rss 依存、週次レポートは GitHub Project #15 と密結合 |
| **B: データ基盤** | 中 | utils_core の `get_fred_api_key()` 分離が必要。他は独立 |
| **C: 定量分析** | 困難 | analyze→market の3段依存チェーン。Quants統合時に market の扱いが課題 |
| **E: AIリサーチ** | 困難 | ca_strategy→factor+strategy 依存。ワーカーエージェント共有問題 |

---

## 推奨する分離順序

```
Phase 1（即座に可能）:
  1-1. F: NotebookLM → 独立リポジトリ
  1-2. A: 汎用開発ツール → 共通ツールキット化

Phase 2（Phase 1 完了後）:
  2-1. B: 金融データ基盤 → 共通パッケージ化
  2-2. D: コンテンツ → finance-content リポジトリ

Phase 3（最も慎重に）:
  3-1. C: 定量分析 → Quants 統合
  3-2. E: AIリサーチ → Cの決定後に実行
```

---

## 今回の整理アクション（実際の分離は行わない）

### 1. レガシーパッケージの整理

| 対象 | 状態 | アクション |
|------|------|----------|
| `src/finance/` | 空ディレクトリ | `trash/` に移動 |
| `src/market_analysis/` | 空ディレクトリ | `trash/` に移動 |
| `src/utils/` | レガシー（28行） | `trash/` に移動 |
| `src/preprocess/` | レガシー（345行） | `trash/` に移動 |

### 2. エージェントの再配置

| 対象 | アクション |
|------|----------|
| `competitive-advantage-critique.md` | `.claude/agents/deep-research/` に移動（グループ E に帰属） |

### 3. CLAUDE.md にグループ分類セクション追加

エージェント/スキル/コマンド一覧に `[A]`〜`[F]` のグループタグを付与し、分離時の参照とする。

### 4. utils_core の金融固有コード分離準備

`settings.py` の `get_fred_api_key()` を `finance_settings.py` に移動し、汎用/金融固有の境界を明確化。

---

## 検証方法

1. レガシー削除後: `make check-all` で既存コードに影響がないことを確認
2. エージェント移動後: 該当エージェントを参照するリーダーエージェントの動作確認
3. CLAUDE.md 更新後: `/index` コマンドで一覧との整合性を確認
4. utils_core 分離後: `make test` で全テスト通過を確認

---

## 重要ファイル

| ファイル | グループ | 説明 |
|---------|---------|------|
| `src/utils_core/settings.py` | B | 金融固有 `get_fred_api_key()` の分離対象 |
| `src/dev/ca_strategy/neutralizer.py` | E | E→C 依存の象徴（`factor.core.normalizer` import） |
| `src/dev/ca_strategy/evaluator.py` | E | E→C 依存（`strategy.risk.calculator` import） |
| `src/analyze/integration/market_integration.py` | C | C→B 依存（market import） |
| `src/factor/integration/` | C | C内の統合層（market+analyze import） |
| `src/news/collectors/rss.py` | D | D→D内依存（rss import） |
| `pyproject.toml` | - | 全パッケージの依存定義。将来の分割起点 |
| `CLAUDE.md` | - | 全資産一覧。グループタグ付与対象 |

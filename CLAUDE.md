---
title: CLAUDE.md
created_at: 2025-12-30
updated_at: 2026-01-28
---

# finance - 金融市場分析・コンテンツ発信支援ライブラリ

**Python 3.12+** | uv | Ruff | pyright | pytest + Hypothesis

金融市場の分析とnote.comでの金融・投資コンテンツ発信を効率化するPythonライブラリ。

## 基本ルール
- 曖昧な表現はせず、可能な限り正確な情報を書く
	- 非推奨: このAPIは制限を受ける可能性がある。
	- 推奨: Github APIは短時間のリクエストを5000件に
- 情報が不足していたり曖昧な状況であったりした場合は、ユーザーにAskUserQeestionsツールを使って詳細を尋ねる
- 自分だけで作業しない。可能な限りサブエージェントに作業を移譲する。適切なサブエージェントがなければ作成を提案する。

## Python実装時の必須サブエージェント

**Python コードを書く際は、必ず以下のサブエージェントに作業を委譲すること。**

### 目的別サブエージェント一覧

| 目的 | サブエージェント | 説明 |
|------|------------------|------|
| **機能実装** | `feature-implementer` | TDDループ（Red→Green→Refactor）を自動実行。Issue のチェックボックスを更新しながら実装 |
| **テスト作成** | `test-writer` | t-wada流TDDに基づくテスト作成 |
| **単体テスト** | `test-unit-writer` | 関数・クラス単位の単体テスト作成 |
| **プロパティテスト** | `test-property-writer` | Hypothesisを使用した不変条件テスト作成 |
| **統合テスト** | `test-integration-writer` | コンポーネント間連携のテスト作成 |
| **品質チェック** | `quality-checker` | `make check-all` 相当の品質検証・自動修正 |
| **コード整理** | `code-simplifier` | 複雑性削減、可読性・保守性向上 |
| **デバッグ** | `debugger` | 問題特定→根本原因分析→解決策実装 |
| **セキュリティ** | `security-scanner` | OWASP Top 10に基づくセキュリティ監査 |

### 実装フロー例

```
1. 機能実装時
   → feature-implementer（TDDサイクル実行）
   → quality-checker --quick（各サイクル後の品質確認）

2. テスト追加時
   → test-planner（テスト設計）
   → test-unit-writer / test-property-writer（テスト実装）

3. 品質改善時
   → quality-checker --auto-fix（自動修正）
   → code-simplifier（コード整理）

4. バグ修正時
   → debugger（原因特定・修正）
   → quality-checker --validate-only（修正確認）
```

### quality-checker のモード

| モード | 用途 |
|--------|------|
| `--validate-only` | 検証のみ（CI/CD、最終確認） |
| `--auto-fix` | 自動修正（`make check-all` 成功まで繰り返し） |
| `--quick` | フォーマット・リントのみ（TDDサイクル中の高速チェック） |

## 目的別クイックガイド

### コード実装
- コードを書く → `@.claude/rules/coding-standards.md` 参照
- テストを書く → `/write-tests`
- 品質チェック → `make check-all`
- Issue を実装 → `/issue-implement <番号>`

### Git・PR操作
- コミット・PR作成 → `/commit-and-pr`
- PRマージ → `/merge-pr <番号>`
- PRレビュー → `/review-pr`
- コンフリクト分析 → `/analyze-conflicts`

### プロジェクト管理
- Issue作成 → `/issue`
- Issue改善 → `/issue-refine <番号>`
- プロジェクト作成 → `/new-project`
- 並行開発計画 → `/plan-worktrees <project_number>`
- worktree作成 → `/worktree <branch_name>`

### 金融コンテンツ作成
- ニュース収集 → `/finance-news-workflow`
- トピック提案 → `/finance-suggest-topics`
- 記事フォルダ作成 → `/new-finance-article`
- リサーチ実行 → `/finance-research`
- 全工程一括 → `/finance-full`

### 分析・改善
- コード分析 → `/analyze`
- 品質改善 → `/ensure-quality`
- セキュリティ検証 → `/scan`
- デバッグ → `/troubleshoot`

### 一覧表示
- 全コマンド一覧 → `/index`

---

## コマンド一覧

### Git・PR操作

| コマンド | 説明 | スキル |
|----------|------|--------|
| `/commit-and-pr` | 変更のコミットとPR作成 | `commit-and-pr` |
| `/push` | 変更をコミットしてリモートにプッシュ | `push` |
| `/merge-pr <番号>` | PRのコンフリクトチェック・CI確認・マージ | `merge-pr` |
| `/review-pr` | PRレビュー（コード品質・セキュリティ・テスト） | - |
| `/analyze-conflicts` | コンフリクト分析と解決策提示 | - |

### Worktree・並行開発

| コマンド | 説明 | スキル |
|----------|------|--------|
| `/worktree <branch_name>` | 新しいworktreeとブランチを作成して開発開始 | `worktree` |
| `/plan-worktrees <project>` | GitHub Projectを参照し並列開発計画を表示 | `plan-worktrees` |
| `/create-worktrees <issues>` | 複数のworktreeを一括作成 | `create-worktrees` |
| `/worktree-done <branch>` | PRマージ確認後にworktreeを安全にクリーンアップ | `worktree-done` |
| `/delete-worktrees <branches>` | 複数のworktreeとブランチを一括削除 | `delete-worktrees` |

### コード品質・分析

| コマンド | 説明 | スキル |
|----------|------|--------|
| `/write-tests` | t-wada流TDDによるテスト作成 | `tdd-development` |
| `/ensure-quality` | コード品質の自動改善（make check-all相当） | `ensure-quality` |
| `/analyze` | 多次元コード分析（品質・アーキテクチャ・性能） | `analyze` |
| `/improve` | エビデンスベースの改善実装 | `improve` |
| `/safe-refactor` | 安全なリファクタリング | `safe-refactor` |
| `/scan` | セキュリティと品質の包括的検証 | `scan` |
| `/troubleshoot` | 体系的なデバッグ | `troubleshoot` |

### Issue・プロジェクト管理

| コマンド | 説明 | スキル |
|----------|------|--------|
| `/issue` | GitHub Issueの作成とタスク分解 | `issue-creation` |
| `/issue-refine <番号>` | Issueの内容をブラッシュアップ | `issue-refinement` |
| `/issue-implement <番号>` | GitHub Issueの自動実装とPR作成 | `issue-implementation-serial` |
| `/sync-issue <番号>` | Issueコメントから進捗・タスク・仕様変更を同期 | `issue-sync` |
| `/new-project` | プロジェクト作成（GitHub Project連携） | `project-management` |
| `/task` | 複雑なタスクの管理 | `task-decomposition` |

### 金融コンテンツ作成

| コマンド | 説明 | スキル |
|----------|------|--------|
| `/finance-suggest-topics` | 金融記事のトピックを提案しスコアリング | - |
| `/new-finance-article` | 新規金融記事フォルダを作成し初期構造を生成 | - |
| `/finance-research` | 金融記事のリサーチワークフロー（データ収集→分析→検証→可視化） | `deep-research` |
| `/finance-edit` | 金融記事の編集ワークフロー（初稿作成→批評→修正） | - |
| `/finance-full` | 記事作成の全工程を一括実行 | - |
| `/generate-market-report` | 週次マーケットレポートを自動生成（`--weekly` で週次レポート生成モード） | `generate-market-report` |

### ドキュメント・その他

| コマンド | 説明 | スキル |
|----------|------|--------|
| `/review-pr` | PRレビュー（コード品質・セキュリティ・テスト） | `review-pr` |
| `/review-docs` | ドキュメントレビュー | `review-docs` |
| `/analyze-conflicts` | PRのコンフリクト分析と解決策提示 | `analyze-conflicts` |
| `/new-package <name>` | モノレポ内に新しいPythonパッケージを作成 | - |
| `/setup-repository` | テンプレートリポジトリの初期化（初回のみ） | - |
| `/index` | コマンド・スキル・エージェント・ディレクトリ構成の一覧表示と更新 | `index` |
| `/gemini-search` | Gemini CLIを使用したWeb検索 | `gemini-search` |

---

## スキル一覧

### コーディング・開発

| スキル | 説明 | 呼び出し方法 |
|--------|------|--------------|
| `coding-standards` | Python 3.12+コーディング規約（PEP 695型ヒント、命名規則、Docstring） | プロアクティブ |
| `tdd-development` | t-wada流TDD（Red→Green→Refactor、テスト命名規則） | `/write-tests` |
| `error-handling` | Pythonエラーハンドリングパターン（Simple/Richパターン選択） | プロアクティブ |
| `development-guidelines` | 開発プロセスとコーディング規約の確立 | ドキュメント作成時 |
| `ensure-quality` | コード品質の自動改善（品質修正→コード整理の2フェーズ） | `/ensure-quality` |
| `analyze` | 多次元コード分析（コード・アーキテクチャ・セキュリティ・パフォーマンス） | `/analyze` |
| `improve` | エビデンスベースの改善実装（測定→改善→検証） | `/improve` |
| `safe-refactor` | テストカバレッジを維持しながら安全にリファクタリング | `/safe-refactor` |
| `scan` | セキュリティと品質の包括的検証（OWASP Top 10準拠） | `/scan` |
| `troubleshoot` | 体系的なデバッグ（問題特定→原因分析→解決策実装） | `/troubleshoot` |

### Issue・プロジェクト管理

| スキル | 説明 | 呼び出し方法 |
|--------|------|--------------|
| `issue-creation` | GitHub Issue作成とタスク分解（クイック/パッケージ/軽量の3モード） | `/issue` |
| `issue-refinement` | Issue内容のブラッシュアップ（8項目の詳細確認） | `/issue-refine` |
| `issue-implementation-serial` | 複数Issue連続実装とPR作成（context: forkでコンテキスト分離） | `/issue-implement` |
| `issue-implement-single` | 単一Issue実装（context: forkで分離実行） | `issue-implementation-serial`から呼出 |
| `project-implementation` | Project内のTodo/In Progress Issueを依存関係順に自動実装 | `/project-implement` |
| `issue-sync` | Issueコメントから進捗・タスク・仕様変更の同期 | `/sync-issue` |
| `new-project` | 新規プロジェクト作成（パッケージ/軽量の2モード） | `/new-project` |
| `project-management` | GitHub Projectとproject.mdの作成・管理・同期 | `/new-project` |
| `task-decomposition` | タスク分解、依存関係解析、類似タスク判定 | `/task` |

### Git・Worktree

| スキル | 説明 | 呼び出し方法 |
|--------|------|--------------|
| `commit-and-pr` | 品質確認、コミット、プッシュ、PR作成、CIチェック | `/commit-and-pr` |
| `push` | コミットメッセージ自動生成、ステージング、プッシュ | `/push` |
| `merge-pr` | PRのコンフリクト確認・CI確認・マージ実行 | `/merge-pr` |
| `worktree` | 並列開発用の独立した作業環境を即座に準備 | `/worktree` |
| `plan-worktrees` | 依存関係を考慮した並列開発計画の可視化 | `/plan-worktrees` |
| `create-worktrees` | 複数worktree一括作成 | `/create-worktrees` |
| `worktree-done` | マージ確認→worktree削除→ブランチ削除の安全なクリーンアップ | `/worktree-done` |
| `delete-worktrees` | 複数worktree一括削除 | `/delete-worktrees` |

### レビュー・検証

| スキル | 説明 | 呼び出し方法 |
|--------|------|--------------|
| `review-pr` | PRの包括的レビュー（7サブエージェント並列実行：品質・セキュリティ・テスト） | `/review-pr` |
| `review-docs` | ドキュメントの詳細レビュー（完全性・具体性・一貫性・測定可能性） | `/review-docs` |
| `analyze-conflicts` | PRコンフリクトの詳細分析と解決策提示（リスク評価・依存関係分析） | `/analyze-conflicts` |

### ドキュメント作成

| スキル | 説明 | 呼び出し方法 |
|--------|------|--------------|
| `prd-writing` | ライブラリ要求定義書(LRD)作成 | `/new-project` |
| `functional-design` | 機能設計書作成 | ドキュメント作成時 |
| `architecture-design` | アーキテクチャ設計書作成 | ドキュメント作成時 |
| `repository-structure` | リポジトリ構造定義書作成 | ドキュメント作成時 |
| `glossary-creation` | 用語集作成 | ドキュメント作成時 |

### 専門スキル

| スキル | 説明 | 呼び出し方法 |
|--------|------|--------------|
| `agent-expert` | Claude Codeエージェントの設計・最適化 | プロアクティブ |
| `skill-expert` | Claude Codeスキルの設計・最適化 | プロアクティブ |
| `workflow-expert` | ワークフロー設計とマルチエージェント連携 | プロアクティブ |
| `agent-memory` | 会話をまたいで知識を保存・参照 | `remember this`等 |
| `deep-research` | 金融市場・投資テーマのディープリサーチ | `/finance-research` |
| `finance-news-workflow` | 金融ニュース収集の4フェーズワークフロー | `/finance-news-workflow` |
| `generate-market-report` | 週次マーケットレポート自動生成（データ収集→ニュース検索→レポート作成） | `/generate-market-report` |
| `index` | CLAUDE.md/README.mdの自動更新 | `/index` |
| `gemini-search` | Gemini CLIを使用したWeb検索 | `/gemini-search` |

---

## エージェント一覧

### ドキュメント作成エージェント

| エージェント | 説明 |
|--------------|------|
| `functional-design-writer` | 機能設計書を作成/更新（LRDを元に技術的な機能設計を詳細化） |
| `architecture-design-writer` | アーキテクチャ設計書を作成/更新（技術スタックとシステム構造を定義） |
| `repository-structure-writer` | リポジトリ構造定義書を作成/更新（具体的なディレクトリ構造を定義） |
| `development-guidelines-writer` | 開発ガイドラインを作成/更新（コーディング規約と開発プロセス） |
| `glossary-writer` | 用語集を作成/更新（ライブラリ固有の用語と技術用語を定義） |
| `doc-reviewer` | ドキュメントの品質をレビューし改善提案 |

### コード品質・分析エージェント

| エージェント | 説明 |
|--------------|------|
| `api-usage-researcher` | 外部API使用時のドキュメント調査（Context7・プロジェクトパターン・ベストプラクティス収集） |
| `code-analyzer` | コード品質・アーキテクチャ・パフォーマンスの多次元分析 |
| `code-simplifier` | コードの複雑性削減、可読性・保守性向上 |
| `quality-checker` | コード品質の検証・自動修正（検証のみ/自動修正/クイックの3モード） |
| `security-scanner` | OWASP Top 10に基づくセキュリティ監査 |
| `debugger` | 体系的なデバッグ（問題特定→根本原因分析→解決策実装） |
| `improvement-implementer` | エビデンスベースの改善実装（メトリクス測定→改善→検証） |
| `implementation-validator` | 実装コードの品質検証とスペック整合性確認 |

### テストエージェント

| エージェント | 説明 |
|--------------|------|
| `test-orchestrator` | テスト作成の並列実行を制御するオーケストレーター |
| `test-planner` | テスト設計（TODOリスト作成、テストケース分類、優先度付け） |
| `test-unit-writer` | 単体テスト作成（関数・クラス単位） |
| `test-property-writer` | Hypothesisを使用したプロパティベーステスト作成 |
| `test-integration-writer` | コンポーネント間連携の統合テスト作成 |
| `test-writer` | t-wada流TDDに基づくテスト作成 |
| `feature-implementer` | TDDループ自動実行（Issue更新しながらRed→Green→Refactor） |

### PRレビューエージェント

| エージェント | 説明 |
|--------------|------|
| `pr-readability` | PRの可読性・命名規則・ドキュメント検証 |
| `pr-design` | PRのSOLID原則・設計パターン・DRY検証 |
| `pr-performance` | PRのアルゴリズム複雑度・メモリ効率・I/O検証 |
| `pr-security-code` | PRのコード内セキュリティ脆弱性検証（OWASP A01-A05） |
| `pr-security-infra` | PRのインフラセキュリティ検証（OWASP A06-A10） |
| `pr-test-coverage` | PRのテストカバレッジとエッジケース網羅性検証 |
| `pr-test-quality` | PRのテスト品質検証（命名・アサーション・モック・独立性） |

### Issue・タスク管理エージェント

| エージェント | 説明 |
|--------------|------|
| `issue-implementer` | GitHub Issueの自動実装とPR作成（4タイプ対応） |
| `task-decomposer` | タスク分解、Issue類似性判定、依存関係管理、双方向同期 |
| `comment-analyzer` | Issueコメントを解析し進捗・サブタスク・仕様変更を抽出 |

### 金融ニュース収集エージェント

| エージェント | 説明 |
|--------------|------|
| `finance-news-orchestrator` | テーマ別ニュース収集の並列実行を制御 |
| `finance-news-collector` | RSSフィードから金融ニュースを収集しGitHub Projectに投稿 |
| `finance-news-index` | Index（株価指数）関連ニュース収集 |
| `finance-news-stock` | Stock（個別銘柄）関連ニュース収集 |
| `finance-news-sector` | Sector（セクター分析）関連ニュース収集 |
| `finance-news-macro` | Macro Economics（マクロ経済）関連ニュース収集 |
| `finance-news-finance` | Finance（金融・財務）関連ニュース収集 |
| `finance-news-ai` | AI（人工知能・テクノロジー）関連ニュース収集 |

### 金融リサーチエージェント

| エージェント | 説明 |
|--------------|------|
| `finance-query-generator` | 金融トピックから検索クエリを生成 |
| `finance-web` | Web検索で金融情報を収集しraw-data.jsonに追記 |
| `finance-wiki` | Wikipediaから金融関連の背景情報を収集 |
| `finance-source` | raw-data.jsonから情報源を抽出・整理しsources.jsonを生成 |
| `finance-claims` | sources.jsonから主張・事実を抽出しclaims.jsonを生成 |
| `finance-claims-analyzer` | claims.jsonを分析し情報ギャップと追加調査の必要性を判定 |
| `finance-fact-checker` | claims.jsonの各主張を検証し信頼度を判定 |
| `finance-decisions` | 各主張の採用可否を判定 |
| `finance-market-data` | YFinance/FREDを使用して市場データを取得 |
| `finance-technical-analysis` | 市場データからテクニカル指標を計算・分析 |
| `finance-economic-analysis` | FRED経済指標データを分析しマクロ経済状況を評価 |
| `finance-sec-filings` | SEC EDGARから企業決算・財務データを取得・分析 |
| `finance-sentiment-analyzer` | ニュース・ソーシャルメディアのセンチメント分析 |
| `finance-visualize` | リサーチ結果を可視化しチャートやサマリーを生成 |

### 金融記事作成エージェント

| エージェント | 説明 |
|--------------|------|
| `finance-topic-suggester` | 金融記事のトピックを提案しスコアリング |
| `finance-article-writer` | リサーチ結果から金融記事の初稿を生成 |
| `finance-critic-fact` | 記事の事実正確性を検証 |
| `finance-critic-data` | 記事内のデータ・数値の正確性を検証 |
| `finance-critic-structure` | 記事の文章構成を評価 |
| `finance-critic-readability` | 記事の読みやすさと読者への訴求力を評価 |
| `finance-critic-compliance` | 金融規制・コンプライアンスへの準拠を確認 |
| `finance-reviser` | 批評結果を反映して記事を修正 |
| `research-image-collector` | note記事用の画像を収集しimages.jsonを生成 |
| `news-article-fetcher` | 記事URLから本文を取得し日本語要約を生成 |

### 週次レポートエージェント

| エージェント | 説明 |
|--------------|------|
| `weekly-report-news-aggregator` | GitHub Project からニュースを集約し週次レポート用データを生成 |
| `weekly-report-writer` | 4つのスキルをロードして週次マーケットレポートを生成 |
| `weekly-report-publisher` | 週次レポートを GitHub Issue として投稿し Project #15 に追加 |
| `weekly-comment-indices-fetcher` | 週次コメント用の指数関連ニュースを収集 |
| `weekly-comment-mag7-fetcher` | 週次コメント用のMAG7関連ニュースを収集 |
| `weekly-comment-sectors-fetcher` | 週次コメント用のセクター関連ニュースを収集 |

### 設計・作成支援エージェント

| エージェント | 説明 |
|--------------|------|
| `agent-creator` | agent-expertスキルを参照しエージェントの設計・実装・検証を実行 |
| `skill-creator` | skill-expertスキルを参照しスキルの設計・実装・検証を実行 |
| `command-expert` | Claude Codeコマンドの設計・最適化 |
| `workflow-designer` | ワークフロー設計とマルチエージェント連携 |
| `package-readme-updater` | パッケージREADMEを自動更新（構成・API・使用例） |

---

## Pythonパッケージ一覧

| パッケージ | 説明 | 主な機能 |
|------------|------|----------|
| `database` | コアインフラパッケージ | DB接続、ユーティリティ、ロギング、日付ユーティリティ |
| `market` | 市場データ取得パッケージ | yfinance連携、FRED連携 |
| `analyze` | 市場データ分析パッケージ | テクニカル分析、騰落率計算、セクター分析 |
| `rss` | RSSフィード管理パッケージ | フィード監視、記事取得、重複チェック |
| `factor` | ファクター投資・分析パッケージ | マルチファクターモデル、ファクター分析 |
| `strategy` | 投資戦略パッケージ | 戦略構築、バックテスト、評価 |

---

## 依存関係

### Pythonパッケージ

- `database` (コア) → `market`, `analyze`, `rss`
- `market` → `analyze`, `factor`, `strategy`
- `analyze` → `strategy`
- `factor` → `strategy`

### コマンド → スキル → エージェント

- `/commit-and-pr` → `commit-and-pr` → `quality-checker`, `code-simplifier`
- `/finance-news-workflow` → `finance-news-workflow` → `finance-news-orchestrator` → 6テーマ別エージェント
- `/finance-research` → `deep-research` → 14リサーチエージェント
- `/issue-implement <番号>` → `issue-implement-single` → `api-usage-researcher`(条件付き), `test-writer`, `pydantic-model-designer`, `feature-implementer`, `code-simplifier`, `quality-checker`
- `/new-project` → `new-project` → 6設計エージェント, `task-decomposer`
- `/write-tests` → `tdd-development` → `test-orchestrator` → 5テストエージェント
- `/index` → `index` → `Explore`, `package-readme-updater`

詳細なMermaid図は [README.md](README.md#-依存関係図) を参照。

---

## 規約・詳細参照

| 規約 | パス |
|------|------|
| コーディング規約 | `@.claude/rules/coding-standards.md` |
| テスト戦略 | `@.claude/rules/testing-strategy.md` |
| Git運用 | `@.claude/rules/git-rules.md` |
| 開発プロセス | `@.claude/rules/development-process.md` |
| 共通指示 | `@.claude/rules/common-instructions.md` |
| エビデンスベース | `@.claude/rules/evidence-based.md` |
| サブエージェント | `@.claude/rules/subagent-data-passing.md` |

---

## ディレクトリ構成

```
finance/
├── .claude/                    # Claude Code 設定
│   ├── agents/                 # サブエージェント定義（85個）
│   ├── commands/               # スラッシュコマンド（19個）
│   ├── rules/                  # 共有ルール（規約詳細）
│   └── skills/                 # スキル定義（48個）
│
├── src/                        # ソースコード
│   ├── database/               # コアインフラ（DB, utils, logging）
│   ├── market/                 # 市場データ取得（yfinance, FRED）
│   ├── analyze/                # 市場分析（テクニカル分析）
│   ├── rss/                    # RSSフィード監視
│   ├── factor/                 # ファクター分析
│   └── strategy/               # 投資戦略
│
├── tests/                      # テストスイート
│   ├── {package}/unit/         # 単体テスト
│   ├── {package}/property/     # プロパティテスト
│   └── {package}/integration/  # 統合テスト
│
├── data/                       # データ層
│   ├── raw/                    # 生データ（Parquet, JSON）
│   ├── processed/              # 加工済みデータ
│   └── exports/                # エクスポート（CSV, JSON）
│
├── template/                   # 参照テンプレート（読み取り専用）
├── articles/                   # 金融記事ワークスペース
├── docs/                       # ドキュメント
├── snippets/                   # 再利用可能コンテンツ
└── trash/                      # 削除待ちファイル
```

---

## 制約事項

- AIエージェント用スクリプトは `.claude/skills/` 内のみ実装を許可
- `template/` は変更・削除禁止
- `trash/` はユーザーが定期的に確認・削除

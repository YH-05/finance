---
description: コマンド・スキル・エージェント・ディレクトリ構成の一覧表示と更新
---

# Index

プロジェクトのリファレンス情報を管理します。

## 使用方法

- `/index` - リファレンス表示
- `/index --update` - 自動検出して更新

## コマンド一覧 (18件)

| コマンド | 説明 |
|----------|------|
| /commit-and-pr | 変更のコミットとPR作成 |
| /delete-worktrees | 複数のworktreeとブランチを一括削除 |
| /finance-edit | 金融記事の編集ワークフロー（初稿→批評→修正） |
| /finance-full | 記事作成の全工程を一括実行（フォルダ作成→リサーチ→執筆） |
| /finance-research | 金融記事のリサーチワークフロー（データ収集→分析→検証→可視化） |
| /finance-suggest-topics | 金融記事のトピックを提案（スコアリング付き） |
| /gemini-search | Web search using Gemini CLI |
| /generate-market-report | 週次マーケットレポートを自動生成 |
| /merge-pr | PRのコンフリクトチェック・CI確認・マージを実行 |
| /new-finance-article | 新規金融記事フォルダを作成 |
| /new-package | モノレポ内に新しいPythonパッケージを作成 |
| /plan-worktrees | GitHub Projectを参照し、Todoの Issue を並列開発用にグルーピング表示 |
| /push | 変更をコミットしてリモートにプッシュ |
| /setup-repository | テンプレートリポジトリの初期化（初回のみ） |
| /task | 複雑なタスクの管理 |
| /worktree | 新しいworktreeとブランチを作成して開発を開始 |
| /worktree-done | worktreeの開発完了後、PRマージ確認を経て安全にクリーンアップ |
| /write-tests | t-wada流TDDによるテスト作成 |

## スキル一覧 (46件)

| スキル | 説明 |
|--------|------|
| agent-expert | エージェント設計・作成・最適化の専門スキル |
| agent-memory | メモリの保存・呼び出し・整理を行うスキル |
| analyze | 多次元コード分析（コード・アーキテクチャ・セキュリティ・パフォーマンス） |
| analyze-conflicts | PRコンフリクトの詳細分析と解決策提示 |
| architecture-design | アーキテクチャ設計書作成のガイドとテンプレート |
| coding-standards | Pythonコーディング規約のナレッジベース |
| commit-and-pr | 変更のコミットとPR作成を一括実行 |
| create-worktrees | 複数worktreeを一括作成 |
| deep-research | 金融市場・投資テーマ専用のディープリサーチ |
| delete-worktrees | 複数worktreeとブランチを一括削除 |
| development-guidelines | 開発プロセスとコーディング規約のガイド |
| ensure-quality | コード品質の自動改善（品質修正→コード整理の2フェーズ） |
| error-handling | Pythonエラーハンドリングパターンのナレッジベース |
| finance-news-workflow | 金融ニュース収集の4フェーズワークフロー |
| functional-design | 機能設計書作成のガイドとテンプレート |
| gemini-search | Gemini CLIを使用したWeb検索 |
| generate-market-report | 週次マーケットレポート自動生成 |
| glossary-creation | 用語集作成のガイドとテンプレート |
| improve | エビデンスベースの改善実装（測定→改善→検証） |
| index | CLAUDE.md/README.md の自動更新機能 |
| issue-creation | GitHub Issue作成とタスク分解 |
| issue-implement-single | 単一Issue実装（context: forkで分離実行） |
| issue-implementation-serial | 複数Issue連続実装とPR作成 |
| issue-refinement | GitHub Issueのブラッシュアップ |
| issue-sync | Issueコメントから進捗・タスク・仕様を同期 |
| merge-pr | PRコンフリクトチェック・CI確認・マージ |
| new-project | 新規プロジェクトを作成（パッケージ/軽量の2モード） |
| plan-worktrees | Todoの Issueを並列開発用にグルーピング |
| prd-writing | ライブラリ要求定義書(LRD)作成のガイド |
| project-implementation | Project内のTodo/In Progress Issueを依存関係順に自動実装 |
| project-management | GitHub Projectとproject.mdの管理・同期 |
| push | 変更をコミットしてリモートにプッシュ |
| repository-structure | リポジトリ構造定義書作成のガイド |
| review-docs | ドキュメントの詳細レビュー |
| review-pr | PRの包括的レビュー（7サブエージェント並列実行） |
| safe-refactor | テストカバレッジを維持しながら安全にリファクタリング |
| scan | セキュリティと品質の包括的検証（OWASP Top 10準拠） |
| skill-expert | スキル設計・作成・最適化の専門スキル |
| task-decomposition | タスク分解と依存関係解析のナレッジベース |
| tdd-development | t-wada流TDDのナレッジベース |
| troubleshoot | 体系的なデバッグ（問題特定→原因分析→解決策実装） |
| weekly-comment-generation | 週次レポートの各セクション向けコメント文を生成 |
| weekly-data-aggregation | 週次レポート用の入力データを集約・正規化 |
| weekly-report-validation | 週次レポートの品質検証 |
| weekly-template-rendering | 週次レポートのテンプレートにデータとコメントを埋め込む |
| workflow-expert | ワークフロー設計とマルチエージェント連携 |
| worktree | 新しいworktreeとブランチを作成 |
| worktree-done | worktree完了後の安全なクリーンアップ |

## エージェント一覧 (92件)

詳細は `.claude/agents.md` を参照してください。

### 汎用エージェント

| エージェント | 説明 |
|-------------|------|
| Bash | コマンド実行。git操作、ターミナルタスク用 |
| general-purpose | 複雑な質問の調査、コード検索、マルチステップタスク |
| Explore | コードベース探索。ファイルパターン検索、キーワード検索 |
| Plan | 実装計画の設計。ステップバイステップの計画作成 |

### 品質・分析エージェント

| エージェント | 説明 |
|-------------|------|
| quality-checker | コード品質の検証・自動修正（検証のみ/自動修正/クイックの3モード） |
| code-analyzer | コード品質・アーキテクチャ・パフォーマンスの多次元分析 |
| code-simplifier | コードの複雑性削減、可読性・保守性向上 |
| security-scanner | OWASP Top 10 に基づくセキュリティ脆弱性の検証 |
| implementation-validator | 実装コードの品質検証、スペックとの整合性確認 |
| debugger | 体系的なデバッグ（問題特定→根本原因分析→解決策実装） |
| improvement-implementer | エビデンスベースの改善実装（メトリクス測定→改善→検証） |

### 開発エージェント

| エージェント | 説明 |
|-------------|------|
| feature-implementer | TDDループ自動実行（Issue更新しながらRed→Green→Refactor） |
| api-usage-researcher | 外部API使用時のドキュメント調査（Context7・プロジェクトパターン収集） |
| pydantic-model-designer | Pydanticモデルを設計・作成（テスト作成後、実装前に型安全に定義） |

### テストエージェント

| エージェント | 説明 |
|-------------|------|
| test-orchestrator | テスト作成の並列実行を制御するオーケストレーター |
| test-planner | テスト設計（TODOリスト作成、テストケース分類、優先度付け） |
| test-unit-writer | 単体テスト作成（関数・クラス単位） |
| test-property-writer | Hypothesisを使用したプロパティベーステスト作成 |
| test-integration-writer | コンポーネント間連携の統合テスト作成 |
| test-writer | t-wada流TDDに基づくテスト作成 |

### ドキュメントエージェント

| エージェント | 説明 |
|-------------|------|
| functional-design-writer | 機能設計書を作成/更新（LRDを元に技術的な機能設計を詳細化） |
| architecture-design-writer | アーキテクチャ設計書を作成/更新（技術スタックとシステム構造を定義） |
| repository-structure-writer | リポジトリ構造定義書を作成/更新（具体的なディレクトリ構造を定義） |
| development-guidelines-writer | 開発ガイドラインを作成/更新（コーディング規約と開発プロセス） |
| glossary-writer | 用語集を作成/更新（ライブラリ固有の用語と技術用語を定義） |
| doc-reviewer | ドキュメントの品質をレビューし改善提案 |
| package-readme-updater | パッケージREADMEを自動更新（構成・API・使用例） |

### PRレビューエージェント

| エージェント | 説明 |
|-------------|------|
| pr-readability | PRの可読性・命名規則・ドキュメント検証 |
| pr-design | PRのSOLID原則・設計パターン・DRY検証 |
| pr-performance | PRのアルゴリズム複雑度・メモリ効率・I/O検証 |
| pr-security-code | PRのコード内セキュリティ脆弱性検証（OWASP A01-A05） |
| pr-security-infra | PRのインフラセキュリティ検証（OWASP A06-A10） |
| pr-test-coverage | PRのテストカバレッジとエッジケース網羅性検証 |
| pr-test-quality | PRのテスト品質検証（命名・アサーション・モック・独立性） |

### Issue・タスク管理エージェント

| エージェント | 説明 |
|-------------|------|
| issue-implementer | GitHub Issueの自動実装とPR作成（4タイプ対応） |
| task-decomposer | タスク分解、Issue類似性判定、依存関係管理、双方向同期 |
| comment-analyzer | Issueコメントを解析し進捗・サブタスク・仕様変更を抽出 |

### 金融ニュース収集エージェント

| エージェント | 説明 |
|-------------|------|
| finance-news-orchestrator | テーマ別ニュース収集の並列実行を制御 |
| finance-news-collector | RSSフィードから金融ニュースを収集しGitHub Projectに投稿 |
| finance-news-index | Index（株価指数）関連ニュース収集 |
| finance-news-stock | Stock（個別銘柄）関連ニュース収集 |
| finance-news-sector | Sector（セクター分析）関連ニュース収集 |
| finance-news-macro-cnbc | Macro Economics（CNBC系フィード）関連ニュース収集 |
| finance-news-macro-other | Macro Economics（経済指標・中央銀行）関連ニュース収集 |
| finance-news-finance-cnbc | Finance（CNBC系フィード）関連ニュース収集 |
| finance-news-finance-nasdaq | Finance（NASDAQ系フィード）関連ニュース収集 |
| finance-news-finance-other | Finance（金融メディア）関連ニュース収集 |
| finance-news-ai-cnbc | AI（CNBC Technology）関連ニュース収集 |
| finance-news-ai-nasdaq | AI（NASDAQ系フィード）関連ニュース収集 |
| finance-news-ai-tech | AI（テック系メディア）関連ニュース収集 |
| news-article-fetcher | 記事URLから本文を取得し日本語要約を生成 |

### 金融リサーチエージェント

| エージェント | 説明 |
|-------------|------|
| finance-query-generator | 金融トピックから検索クエリを生成 |
| finance-web | Web検索で金融情報を収集しraw-data.jsonに追記 |
| finance-wiki | Wikipediaから金融関連の背景情報を収集 |
| finance-source | raw-data.jsonから情報源を抽出・整理しsources.jsonを生成 |
| finance-claims | sources.jsonから主張・事実を抽出しclaims.jsonを生成 |
| finance-claims-analyzer | claims.jsonを分析し情報ギャップと追加調査の必要性を判定 |
| finance-fact-checker | claims.jsonの各主張を検証し信頼度を判定 |
| finance-decisions | 各主張の採用可否を判定 |
| finance-market-data | YFinance/FREDを使用して市場データを取得 |
| finance-technical-analysis | 市場データからテクニカル指標を計算・分析 |
| finance-economic-analysis | FRED経済指標データを分析しマクロ経済状況を評価 |
| finance-sec-filings | SEC EDGARから企業決算・財務データを取得・分析 |
| finance-sentiment-analyzer | ニュース・ソーシャルメディアのセンチメント分析 |
| finance-visualize | リサーチ結果を可視化しチャートやサマリーを生成 |

### ディープリサーチエージェント

| エージェント | 説明 |
|-------------|------|
| dr-orchestrator | ディープリサーチワークフローの全体制御 |
| dr-source-aggregator | マルチソースからデータを並列収集し統合 |
| dr-cross-validator | 複数ソースのデータを照合し主張の一貫性を検証 |
| dr-bias-detector | データソースとコンテンツのバイアスを検出・分析 |
| dr-confidence-scorer | データポイントと主張の信頼度スコアを算出 |
| dr-stock-analyzer | 個別銘柄の深掘り分析（財務・バリュエーション・カタリスト） |
| dr-sector-analyzer | セクター比較分析（ローテーション・銘柄選定） |
| dr-macro-analyzer | マクロ経済分析（経済指標・金融政策・市場影響） |
| dr-theme-analyzer | テーマ投資分析（バリューチェーン・投資機会） |
| dr-visualizer | 分析結果を可視化しチャート・図表を生成 |
| dr-report-generator | 分析結果から形式別レポートを生成 |
| market-hypothesis-generator | 市場パフォーマンスデータを分析し仮説と検索クエリを生成 |

### 金融記事作成エージェント

| エージェント | 説明 |
|-------------|------|
| finance-topic-suggester | 金融記事のトピックを提案しスコアリング |
| finance-article-writer | リサーチ結果から金融記事の初稿を生成 |
| finance-critic-fact | 記事の事実正確性を検証 |
| finance-critic-data | 記事内のデータ・数値の正確性を検証 |
| finance-critic-structure | 記事の文章構成を評価 |
| finance-critic-readability | 記事の読みやすさと読者への訴求力を評価 |
| finance-critic-compliance | 金融規制・コンプライアンスへの準拠を確認 |
| finance-reviser | 批評結果を反映して記事を修正 |
| research-image-collector | note記事用の画像を収集しimages.jsonを生成 |

### 週次レポートエージェント

| エージェント | 説明 |
|-------------|------|
| weekly-report-news-aggregator | GitHub Project からニュースを集約し週次レポート用データを生成 |
| weekly-report-writer | 4つのスキルをロードして週次マーケットレポートを生成 |
| weekly-report-publisher | 週次レポートを GitHub Issue として投稿し Project #15 に追加 |
| weekly-comment-indices-fetcher | 週次コメント用の指数関連ニュースを収集 |
| weekly-comment-mag7-fetcher | 週次コメント用のMAG7関連ニュースを収集 |
| weekly-comment-sectors-fetcher | 週次コメント用のセクター関連ニュースを収集 |

### 設計・エキスパートエージェント

| エージェント | 説明 |
|-------------|------|
| agent-creator | agent-expertスキルを参照しエージェントの設計・実装・検証を実行 |
| skill-creator | skill-expertスキルを参照しスキルの設計・実装・検証を実行 |
| command-expert | Claude Codeコマンドの設計・最適化 |
| workflow-designer | ワークフロー設計とマルチエージェント連携 |

### その他エージェント

| エージェント | 説明 |
|-------------|------|
| claude-code-guide | Claude Code CLI・Agent SDK・API質問対応 |
| statusline-setup | ステータスライン設定 |

## 更新日時

最終更新: 2026-01-29

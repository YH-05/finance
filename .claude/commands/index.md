---
description: コマンド・スキル・エージェント・ディレクトリ構成の一覧表示と更新
---

# Index

プロジェクトのリファレンス情報を管理します。

## 使用方法

- `/index` - リファレンス表示
- `/index --update` - 自動検出して更新

## コマンド一覧 (28件)

| コマンド | 説明 |
|----------|------|
| /analyze | 多次元コード分析（分析レポート出力） |
| /analyze-conflicts | PRのコンフリクトを詳細分析し、問題点と解決策を提示 |
| /commit-and-pr | 変更のコミットとPR作成 |
| /delete-worktrees | 複数のworktreeとブランチを一括削除 |
| /ensure-quality | コード品質の自動改善（make check-all相当） |
| /finance-edit | 金融記事の編集ワークフロー（初稿→批評→修正） |
| /finance-full | 記事作成の全工程を一括実行（フォルダ作成→リサーチ→執筆） |
| /finance-research | 金融記事のリサーチワークフロー（データ収集→分析→検証→可視化） |
| /finance-suggest-topics | 金融記事のトピックを提案（スコアリング付き） |
| /gemini-search | Gemini CLIを使用したWeb検索 |
| /generate-market-report | 週次マーケットレポートを自動生成 |
| /improve | エビデンスベースの改善実装 |
| /index | コマンド・スキル・エージェント・ディレクトリ構成の一覧表示と更新 |
| /merge-pr | PRのコンフリクトチェック・CI確認・マージを実行 |
| /new-finance-article | 新規金融記事フォルダを作成 |
| /new-package | モノレポ内に新しいPythonパッケージを作成 |
| /plan-worktrees | GitHub Projectを参照し、Todoの Issue を並列開発用にグルーピング表示 |
| /push | 変更をコミットしてリモートにプッシュ |
| /review-docs | ドキュメントの詳細レビューをサブエージェントで実行 |
| /review-pr | PRレビュー（コード品質・セキュリティ・テスト） |
| /safe-refactor | 安全なリファクタリング |
| /scan | セキュリティと品質の包括的検証 |
| /setup-repository | テンプレートリポジトリの初期化（初回のみ） |
| /task | 複雑なタスクの管理 |
| /troubleshoot | 体系的なデバッグ |
| /worktree | 新しいworktreeとブランチを作成して開発を開始 |
| /worktree-done | worktreeの開発完了後、PRマージ確認を経て安全にクリーンアップ |
| /write-tests | t-wada流TDDによるテスト作成 |

## スキル一覧 (32件)

| スキル | 説明 |
|--------|------|
| agent-expert | エージェント設計・作成・最適化の専門スキル |
| agent-memory | メモリの保存・呼び出し・整理を行うスキル |
| architecture-design | アーキテクチャ設計書作成のガイドとテンプレート |
| coding-standards | Pythonコーディング規約のナレッジベース |
| commit-and-pr | 変更のコミットとPR作成を一括実行 |
| create-worktrees | 複数worktreeを一括作成 |
| deep-research | 金融市場・投資テーマ専用のディープリサーチ |
| delete-worktrees | 複数worktreeとブランチを一括削除 |
| development-guidelines | 開発プロセスとコーディング規約のガイド |
| error-handling | Pythonエラーハンドリングパターンのナレッジベース |
| finance-news-workflow | 金融ニュース収集の4フェーズワークフロー |
| functional-design | 機能設計書作成のガイドとテンプレート |
| gemini-search | Gemini CLIを使用したWeb検索 |
| glossary-creation | 用語集作成のガイドとテンプレート |
| index | CLAUDE.md/README.md の自動更新機能 |
| issue-creation | GitHub Issue作成とタスク分解 |
| issue-implementation | GitHub Issue自動実装とPR作成 |
| issue-refinement | GitHub Issueのブラッシュアップ |
| issue-sync | Issueコメントから進捗・タスク・仕様を同期 |
| merge-pr | PRコンフリクトチェック・CI確認・マージ |
| new-project | 新規プロジェクトを作成（パッケージ/軽量の2モード） |
| plan-worktrees | Todoの Issueを並列開発用にグルーピング |
| prd-writing | ライブラリ要求定義書(LRD)作成のガイド |
| project-management | GitHub Projectとproject.mdの管理・同期 |
| push | 変更をコミットしてリモートにプッシュ |
| repository-structure | リポジトリ構造定義書作成のガイド |
| skill-expert | スキル設計・作成・最適化の専門スキル |
| task-decomposition | タスク分解と依存関係解析のナレッジベース |
| tdd-development | t-wada流TDDのナレッジベース |
| workflow-expert | ワークフロー設計とマルチエージェント連携 |
| worktree | 新しいworktreeとブランチを作成 |
| worktree-done | worktree完了後の安全なクリーンアップ |

## エージェント一覧 (70件 - `.claude/agents.md` 参照)

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
| quality-checker | コード品質の検証・自動修正 |
| code-analyzer | コード品質、アーキテクチャ、パフォーマンスの多次元分析 |
| security-scanner | OWASP Top 10 に基づくセキュリティ脆弱性の検証 |
| implementation-validator | 実装コードの品質検証、スペックとの整合性確認 |

### 開発エージェント

| エージェント | 説明 |
|-------------|------|
| issue-implementer | Issue自動実装・PR作成 |
| test-writer | t-wada流TDDに基づくテスト作成 |
| feature-implementer | TDDループを自動実行 |
| debugger | 体系的なデバッグ |
| improvement-implementer | エビデンスベースの改善実装 |
| code-simplifier | コードの複雑性削減と可読性向上 |

### テストエージェント

| エージェント | 説明 |
|-------------|------|
| test-planner | テスト設計とTODOリスト作成 |
| test-unit-writer | 単体テスト作成 |
| test-property-writer | プロパティベーステスト作成 |
| test-integration-writer | 統合テスト作成 |
| test-orchestrator | テスト作成の並列実行制御 |

### ドキュメントエージェント

| エージェント | 説明 |
|-------------|------|
| functional-design-writer | 機能設計書作成 |
| architecture-design-writer | アーキテクチャ設計書作成 |
| development-guidelines-writer | 開発ガイドライン作成 |
| repository-structure-writer | リポジトリ構造定義書作成 |
| glossary-writer | 用語集作成 |
| doc-reviewer | ドキュメントの品質レビュー |

### PRレビューエージェント

| エージェント | 説明 |
|-------------|------|
| pr-readability | 可読性・命名規則・ドキュメント検証 |
| pr-design | SOLID原則・設計パターン・DRY検証 |
| pr-performance | アルゴリズム複雑度・メモリ効率・I/O検証 |
| pr-security-code | コードセキュリティ（OWASP A01-A05）検証 |
| pr-security-infra | インフラセキュリティ（OWASP A06-A10）検証 |
| pr-test-coverage | テストカバレッジ・エッジケース検証 |
| pr-test-quality | テスト品質（命名・アサーション・モック）検証 |

### 金融記事エージェント

| エージェント | 説明 |
|-------------|------|
| finance-article-writer | リサーチ結果から記事初稿を生成 |
| finance-claims | 金融関連の主張・事実を抽出 |
| finance-claims-analyzer | 情報ギャップと追加調査の必要性を判定 |
| finance-critic-compliance | 金融規制・コンプライアンス準拠確認 |
| finance-critic-data | データ・数値の正確性検証 |
| finance-critic-fact | 事実正確性検証 |
| finance-critic-readability | 読みやすさと訴求力評価 |
| finance-critic-structure | 文章構成評価 |
| finance-decisions | 主張の採用可否判定 |
| finance-economic-analysis | FRED経済指標分析 |
| finance-fact-checker | 主張の信頼度判定 |
| finance-market-data | 市場データ取得・保存 |
| finance-query-generator | 検索クエリ生成 |
| finance-reviser | 批評結果を反映した記事修正 |
| finance-sec-filings | SEC EDGAR財務データ取得・分析 |
| finance-sentiment-analyzer | センチメント分析 |
| finance-source | 情報源の抽出・整理 |
| finance-technical-analysis | テクニカル指標分析 |
| finance-topic-suggester | トピック提案・スコアリング |
| finance-visualize | 分析結果の可視化 |
| finance-web | Web検索で金融情報収集 |
| finance-wiki | Wikipedia背景情報収集 |

### 金融ニュースエージェント

| エージェント | 説明 |
|-------------|------|
| finance-news-collector | RSSから金融ニュース収集・投稿 |
| finance-news-orchestrator | テーマ別収集の並列実行制御 |
| finance-news-ai | AI関連ニュース収集・投稿 |
| finance-news-index | 株価指数関連ニュース収集・投稿 |
| finance-news-stock | 個別銘柄関連ニュース収集・投稿 |
| finance-news-sector | セクター分析関連ニュース収集・投稿 |
| finance-news-macro | マクロ経済関連ニュース収集・投稿 |
| finance-news-finance | 金融・財務関連ニュース収集・投稿 |
| news-article-fetcher | 記事URLから本文取得・日本語要約生成 |
| weekly-comment-indices-fetcher | 週次コメント用指数ニュース収集 |
| weekly-comment-mag7-fetcher | 週次コメント用MAG7ニュース収集 |
| weekly-comment-sectors-fetcher | 週次コメント用セクターニュース収集 |

### 設計・エキスパートエージェント

| エージェント | 説明 |
|-------------|------|
| workflow-designer | ワークフロー設計とマルチエージェント連携 |
| agent-creator | エージェント設計・作成・最適化 |
| skill-creator | スキル設計・作成・最適化 |
| command-expert | コマンド設計・作成・最適化 |
| task-decomposer | タスク分解・Issue連携・双方向同期 |
| comment-analyzer | Issueコメント解析 |

### その他エージェント

| エージェント | 説明 |
|-------------|------|
| claude-code-guide | Claude Code CLI・Agent SDK・API質問対応 |
| statusline-setup | ステータスライン設定 |
| research-image-collector | note記事用画像収集 |
| package-readme-updater | パッケージREADME自動更新 |

## 更新日時

最終更新: 2026-01-22

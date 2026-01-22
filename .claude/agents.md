# エージェント定義

Task ツールで使用可能なサブエージェント（subagent_type）の一覧です。

## 汎用エージェント

| エージェント | 説明 |
|-------------|------|
| `Bash` | コマンド実行。git操作、ターミナルタスク用 |
| `general-purpose` | 複雑な質問の調査、コード検索、マルチステップタスク |
| `Explore` | コードベース探索。ファイルパターン検索、キーワード検索 |
| `Plan` | 実装計画の設計。ステップバイステップの計画作成 |

## 品質・分析エージェント

| エージェント | 説明 |
|-------------|------|
| `quality-checker` | コード品質の検証・自動修正 |
| `code-analyzer` | コード品質、アーキテクチャ、パフォーマンスの多次元分析 |
| `security-scanner` | OWASP Top 10 に基づくセキュリティ脆弱性の検証 |
| `implementation-validator` | 実装コードの品質検証、スペックとの整合性確認 |

## 開発エージェント

| エージェント | 説明 |
|-------------|------|
| `issue-implementer` | issue-implementation スキルをロードして Issue 自動実装・PR作成。Python/Agent/Command/Skill の4タイプ対応 |
| `test-writer` | t-wada流TDDに基づくテスト作成。Red→Green→Refactorサイクル |
| `feature-implementer` | TDDループを自動実行。GitHub Issueのチェックボックスを更新しながら実装 |
| `debugger` | 体系的なデバッグ。問題特定、根本原因分析、解決策実装 |
| `improvement-implementer` | エビデンスベースの改善実装。メトリクス測定→改善→検証 |
| `code-simplifier` | コードの複雑性削減と可読性向上 |

## テストエージェント

| エージェント | 説明 |
|-------------|------|
| `test-planner` | テスト設計とTODOリスト作成 |
| `test-unit-writer` | 単体テスト作成 |
| `test-property-writer` | プロパティベーステスト作成 |
| `test-integration-writer` | 統合テスト作成 |
| `test-orchestrator` | テスト作成の並列実行制御 |

## ドキュメントエージェント

| エージェント | 説明 |
|-------------|------|
| `functional-design-writer` | 機能設計書作成。LRDを元に技術的な機能設計を詳細化 |
| `architecture-design-writer` | アーキテクチャ設計書作成。技術スタックとシステム構造を定義 |
| `development-guidelines-writer` | 開発ガイドライン作成。コーディング規約と開発プロセスを定義 |
| `repository-structure-writer` | リポジトリ構造定義書作成。ディレクトリ構造を定義 |
| `glossary-writer` | 用語集作成。ライブラリ固有の用語と技術用語を定義 |
| `doc-reviewer` | ドキュメントの品質レビューと改善提案 |
| `task-decomposer` | タスク分解とGitHub Issues連携。類似性判定、依存関係管理、project.mdとの双方向同期 |

## PRレビューエージェント

| エージェント | 説明 |
|-------------|------|
| `pr-readability` | 可読性・命名規則・ドキュメント検証 |
| `pr-design` | SOLID原則・設計パターン・DRY検証 |
| `pr-performance` | アルゴリズム複雑度・メモリ効率・I/O検証 |
| `pr-security-code` | コードセキュリティ（OWASP A01-A05）検証 |
| `pr-security-infra` | インフラセキュリティ（OWASP A06-A10）検証 |
| `pr-test-coverage` | テストカバレッジ・エッジケース検証 |
| `pr-test-quality` | テスト品質（命名・アサーション・モック）検証 |

## Issue管理エージェント

| エージェント | 説明 |
|-------------|------|
| `comment-analyzer` | Issueコメントを解析し、進捗・サブタスク・仕様変更を構造化データとして抽出 |

## リサーチエージェント

| エージェント | 説明 |
|-------------|------|
| `research-image-collector` | note記事用の画像を収集し images.json を生成 |

## 金融エージェント

| エージェント | 説明 |
|-------------|------|
| `finance-news-collector` | RSSフィードから金融ニュースを収集し、GitHub Projectに投稿 |
| `finance-news-orchestrator` | テーマ別ニュース収集の並列実行制御 |
| `finance-news-ai` | AI関連ニュースを収集・投稿 |
| `finance-news-index` | 株価指数関連ニュースを収集・投稿 |
| `finance-news-stock` | 個別銘柄関連ニュースを収集・投稿 |
| `finance-news-sector` | セクター分析関連ニュースを収集・投稿 |
| `finance-news-macro` | マクロ経済関連ニュースを収集・投稿 |
| `finance-news-finance` | 金融・財務関連ニュースを収集・投稿 |
| `news-article-fetcher` | 記事URLから本文取得・日本語要約生成 |
| `weekly-comment-indices-fetcher` | 週次コメント用指数ニュース収集 |
| `weekly-comment-mag7-fetcher` | 週次コメント用MAG7ニュース収集 |
| `weekly-comment-sectors-fetcher` | 週次コメント用セクターニュース収集 |
| `finance-article-writer` | リサーチ結果から記事初稿を生成 |
| `finance-claims` | 金融関連の主張・事実を抽出 |
| `finance-claims-analyzer` | 情報ギャップと追加調査の必要性を判定 |
| `finance-critic-compliance` | 金融規制・コンプライアンス準拠確認 |
| `finance-critic-data` | データ・数値の正確性検証 |
| `finance-critic-fact` | 事実正確性検証 |
| `finance-critic-readability` | 読みやすさと訴求力評価 |
| `finance-critic-structure` | 文章構成評価 |
| `finance-decisions` | 主張の採用可否判定 |
| `finance-economic-analysis` | FRED経済指標分析 |
| `finance-fact-checker` | 主張の信頼度判定 |
| `finance-market-data` | 市場データ取得・保存 |
| `finance-query-generator` | 検索クエリ生成 |
| `finance-reviser` | 批評結果を反映した記事修正 |
| `finance-sec-filings` | SEC EDGAR財務データ取得・分析 |
| `finance-sentiment-analyzer` | センチメント分析 |
| `finance-source` | 情報源の抽出・整理 |
| `finance-technical-analysis` | テクニカル指標分析 |
| `finance-topic-suggester` | トピック提案・スコアリング |
| `finance-visualize` | 分析結果の可視化 |
| `finance-web` | Web検索で金融情報収集 |
| `finance-wiki` | Wikipedia背景情報収集 |

## 設計・エキスパートエージェント

| エージェント | 説明 |
|-------------|------|
| `workflow-designer` | ワークフロー設計とマルチエージェント連携の専門。Phase分解、連携パターン設計、スキルプリロード設計 |
| `agent-creator` | エージェント単体の設計・作成・最適化 |
| `skill-creator` | スキル単体の設計・作成・最適化 |
| `command-expert` | コマンドの設計・作成・最適化 |

## 特殊エージェント

| エージェント | 説明 |
|-------------|------|
| `claude-code-guide` | Claude Code CLI、Agent SDK、APIに関する質問対応 |
| `statusline-setup` | ステータスライン設定 |
| `package-readme-updater` | パッケージREADME自動更新 |

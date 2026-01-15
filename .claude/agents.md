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
| `test-writer` | t-wada流TDDに基づくテスト作成。Red→Green→Refactorサイクル |
| `feature-implementer` | TDDループを自動実行。GitHub Issueのチェックボックスを更新しながら実装 |
| `debugger` | 体系的なデバッグ。問題特定、根本原因分析、解決策実装 |
| `improvement-implementer` | エビデンスベースの改善実装。メトリクス測定→改善→検証 |

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

## 特殊エージェント

| エージェント | 説明 |
|-------------|------|
| `claude-code-guide` | Claude Code CLI、Agent SDK、APIに関する質問対応 |
| `statusline-setup` | ステータスライン設定 |

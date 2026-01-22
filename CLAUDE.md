---
title: CLAUDE.md
created_at: 2025-12-30
updated_at: 2026-01-22
---

# finance - 金融市場分析・コンテンツ発信支援ライブラリ

**Python 3.12+** | uv | Ruff | pyright | pytest + Hypothesis

金融市場の分析とnote.comでの金融・投資コンテンツ発信を効率化するPythonライブラリ。

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
- ニュース収集 → `/collect-finance-news`
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

## 規約・詳細参照

- コーディング規約 → `@.claude/rules/coding-standards.md`
- テスト戦略 → `@.claude/rules/testing-strategy.md`
- Git運用 → `@.claude/rules/git-rules.md`
- 開発プロセス → `@.claude/rules/development-process.md`
- 共通指示 → `@.claude/rules/common-instructions.md`
- エビデンスベース → `@.claude/rules/evidence-based.md`
- サブエージェント → `@.claude/rules/subagent-data-passing.md`

## ディレクトリ構成

```
finance/
├── .claude/                    # Claude Code 設定
│   ├── agents/                 # サブエージェント定義
│   ├── commands/               # スラッシュコマンド
│   ├── rules/                  # 共有ルール（規約詳細）
│   └── skills/                 # スキル定義
│
├── src/                        # ソースコード
│   ├── finance/                # コアインフラ（DB, utils）
│   ├── market_analysis/        # 市場分析（yfinance, FRED）
│   ├── rss/                    # RSSフィード監視
│   ├── factor/                 # ファクター分析
│   ├── strategy/               # 投資戦略
│   └── bloomberg/              # Bloomberg連携
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

## 制約事項

- AIエージェント用スクリプトは `.claude/skills/` 内のみ実装を許可
- `template/` は変更・削除禁止
- `trash/` はユーザーが定期的に確認・削除

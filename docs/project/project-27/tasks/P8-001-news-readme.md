# P8-001: src/news/README.md 更新

## 概要

news パッケージの README を更新し、新しいワークフローの使用方法を記載する。

## フェーズ

Phase 8: ドキュメント・移行

## 依存タスク

- P7-003: CLI ログ設定

## 成果物

- `src/news/README.md`（更新）

## 実装内容

以下のセクションを追加/更新：

```markdown
# news パッケージ

ニュース処理パイプラインを提供するパッケージ。

## 金融ニュース収集ワークフロー（Python版）

### 概要

RSSフィードから金融ニュースを収集し、AI要約を生成してGitHub Issueとして公開するワークフロー。

### 使用方法

```bash
# 基本実行
uv run python -m news.scripts.finance_news_workflow

# 特定Statusのみ
uv run python -m news.scripts.finance_news_workflow --status index,stock

# ドライラン（Issue作成なし）
uv run python -m news.scripts.finance_news_workflow --dry-run

# 記事数制限
uv run python -m news.scripts.finance_news_workflow --max-articles 50
```

### アーキテクチャ

```
CLI
 │
 ▼
┌─────────────┐
│ Orchestrator│
└─────────────┘
 │
 ├── RSSCollector      # RSS フィード収集
 ├── TrafilaturaExtractor  # 本文抽出
 ├── Summarizer        # AI 要約
 └── Publisher         # GitHub Issue 作成
```

### 設定ファイル

`data/config/news-collection-config.yaml`

### 出力

- ログ: `logs/news-workflow-{date}.log`
- 結果: `data/exports/news-workflow/workflow-result-{timestamp}.json`

### モジュール構成

```
src/news/
├── collectors/          # 情報源別コレクター
│   ├── base.py         # BaseCollector
│   └── rss.py          # RSSCollector
├── extractors/          # 本文抽出
│   ├── base.py         # BaseExtractor
│   └── trafilatura.py  # TrafilaturaExtractor
├── summarizer.py        # AI 要約
├── publisher.py         # GitHub Issue 作成
├── orchestrator.py      # オーケストレーション
├── models.py            # データモデル
├── config.py            # 設定読み込み
└── scripts/
    └── finance_news_workflow.py  # CLI
```
```

## 受け入れ条件

- [ ] 使用方法が記載されている
- [ ] アーキテクチャ図が含まれている
- [ ] 設定ファイルのパスが記載されている
- [ ] 出力ファイルの場所が記載されている
- [ ] モジュール構成が記載されている
- [ ] Markdown 構文が正しい

## 参照

- project.md: 全セクション

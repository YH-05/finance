# news.scripts

ニュース収集の CLI スクリプトモジュール。

## 概要

ニュース収集ワークフローの CLI エントリーポイントを提供します。コマンドラインから直接実行、または cron スケジュール実行に対応。

**利用可能なスクリプト:**

| スクリプト | 説明 | 実行方法 |
|-----------|------|---------|
| `collect` | 自動ニュース収集 | `python -m news.scripts.collect` |
| `finance_news_workflow` | 金融ニュースワークフロー | `python -m news.scripts.finance_news_workflow` |
| `__main__` | パッケージ直接実行 | `python -m news.scripts` |

## クイックスタート

### 基本的な実行

```bash
# デフォルト設定で収集
python -m news.scripts.collect

# ドライランモード（Issue 作成なし）
python -m news.scripts.collect --dry-run

# ソース指定
python -m news.scripts.collect --source yfinance_ticker

# 設定ファイル指定
python -m news.scripts.collect --config data/config/news_sources.yaml
```

### 金融ニュースワークフロー

```bash
# 4ステージパイプライン実行
# 収集 → 抽出 → 要約 → 公開
python -m news.scripts.finance_news_workflow
```

## CLI オプション

### collect スクリプト

| オプション | 説明 | デフォルト |
|-----------|------|-----------|
| `--config` | 設定ファイルパス | `data/config/news_sources.yaml` |
| `--source` | ソースフィルタ | 全ソース |
| `--dry-run` | ドライランモード | False |

## モジュール構成

```
news/scripts/
├── __init__.py                  # パッケージ docstring
├── __main__.py                  # パッケージ直接実行エントリー
├── collect.py                   # 自動ニュース収集 CLI
├── finance_news_workflow.py     # 金融ニュースワークフロー CLI
└── README.md                    # このファイル
```

## 関連モジュール

- [news.config](../config/README.md) - CLI 設定の読み込み
- [news.collectors](../collectors/README.md) - 収集処理
- [news.processors](../processors/README.md) - パイプライン実行

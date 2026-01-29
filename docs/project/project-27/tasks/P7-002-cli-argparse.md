# P7-002: CLI 引数パース

## 概要

argparse を使用して CLI 引数をパースする。

## フェーズ

Phase 7: CLI

## 依存タスク

- P7-001: CLI エントリーポイント作成

## 成果物

- `src/news/scripts/finance_news_workflow.py`（更新）

## 実装内容

```python
import argparse
from pathlib import Path

def parse_args() -> argparse.Namespace:
    """CLI 引数をパース

    Returns
    -------
    argparse.Namespace
        パースされた引数
    """
    parser = argparse.ArgumentParser(
        description="金融ニュース収集ワークフロー",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # 基本実行
  uv run python -m news.scripts.finance_news_workflow

  # 特定Statusのみ
  uv run python -m news.scripts.finance_news_workflow --status index,stock

  # ドライラン
  uv run python -m news.scripts.finance_news_workflow --dry-run

  # 記事数制限
  uv run python -m news.scripts.finance_news_workflow --max-articles 50
        """
    )

    parser.add_argument(
        "--status",
        type=str,
        default=None,
        help="対象Statusをカンマ区切りで指定 (例: index,stock,ai)"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Issue作成をスキップ（テスト用）"
    )

    parser.add_argument(
        "--config",
        type=Path,
        default=Path("data/config/news-collection-config.yaml"),
        help="設定ファイルパス"
    )

    parser.add_argument(
        "--max-articles",
        type=int,
        default=None,
        help="最大記事数"
    )

    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="詳細ログを出力"
    )

    return parser.parse_args()


async def main() -> int:
    """メインエントリーポイント"""
    args = parse_args()

    # Status リストのパース
    statuses = None
    if args.status:
        statuses = [s.strip() for s in args.status.split(",")]

    config = load_config(args.config)
    orchestrator = NewsWorkflowOrchestrator(config)

    result = await orchestrator.run(
        statuses=statuses,
        max_articles=args.max_articles,
        dry_run=args.dry_run,
    )

    ...
```

## 受け入れ条件

- [ ] `--status`: 対象 Status をカンマ区切りで指定
- [ ] `--dry-run`: Issue 作成をスキップ
- [ ] `--config`: カスタム設定ファイルパス
- [ ] `--max-articles`: 最大記事数
- [ ] `--verbose` / `-v`: 詳細ログ
- [ ] `--help` で使用方法が表示される
- [ ] pyright 型チェック成功

## 参照

- project.md: CLI使用方法 セクション

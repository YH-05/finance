# P7-001: CLI エントリーポイント作成

## 概要

CLI のエントリーポイントを作成する。

## フェーズ

Phase 7: CLI

## 依存タスク

- P6-003: Orchestrator 結果 JSON 出力

## 成果物

- `src/news/scripts/finance_news_workflow.py`（新規作成）

## 実装内容

```python
#!/usr/bin/env python
"""金融ニュース収集ワークフロー CLI

Usage:
    uv run python -m news.scripts.finance_news_workflow
    uv run python -m news.scripts.finance_news_workflow --dry-run
    uv run python -m news.scripts.finance_news_workflow --status index,stock
"""
import asyncio
import sys
from pathlib import Path

from news.config import load_config
from news.orchestrator import NewsWorkflowOrchestrator


async def main() -> int:
    """メインエントリーポイント

    Returns
    -------
    int
        終了コード（0: 成功, 1: 失敗）
    """
    # TODO: 引数パース（P7-002）
    # TODO: ログ設定（P7-003）

    # デフォルト設定ファイルパス
    config_path = Path("data/config/news-collection-config.yaml")

    try:
        config = load_config(config_path)
        orchestrator = NewsWorkflowOrchestrator(config)

        result = await orchestrator.run()

        # 結果サマリー出力
        print(f"\n=== Workflow Result ===")
        print(f"Collected: {result.total_collected}")
        print(f"Extracted: {result.total_extracted}")
        print(f"Summarized: {result.total_summarized}")
        print(f"Published: {result.total_published}")
        print(f"Duplicates: {result.total_duplicates}")
        print(f"Elapsed: {result.elapsed_seconds:.1f}s")

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
```

## 受け入れ条件

- [ ] `python -m news.scripts.finance_news_workflow` で実行できる
- [ ] 正常終了時は終了コード 0
- [ ] 異常終了時は終了コード 1
- [ ] 結果サマリーがコンソールに出力される
- [ ] pyright 型チェック成功

## 参照

- project.md: CLI使用方法 セクション

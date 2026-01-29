# P7-003: CLI ログ設定

## 概要

ファイル出力とコンソール出力の両方に対応するログ設定を実装する。

## フェーズ

Phase 7: CLI

## 依存タスク

- P7-002: CLI 引数パース

## 成果物

- `src/news/scripts/finance_news_workflow.py`（更新）

## 実装内容

```python
import logging
from datetime import datetime
from pathlib import Path
from utils_core.logging_config import get_logger, configure_logging

logger = get_logger(__name__)

def setup_logging(verbose: bool = False) -> None:
    """ログ設定を初期化

    Parameters
    ----------
    verbose : bool, optional
        Trueの場合、DEBUG レベルで出力
    """
    log_level = logging.DEBUG if verbose else logging.INFO

    # ログディレクトリ作成
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # 日付ベースのログファイル名
    log_file = log_dir / f"news-workflow-{datetime.now().strftime('%Y-%m-%d')}.log"

    # utils_core のログ設定を使用
    configure_logging(
        level=log_level,
        log_file=str(log_file),
    )

    logger.info("Logging initialized", log_file=str(log_file), level=logging.getLevelName(log_level))


async def main() -> int:
    """メインエントリーポイント"""
    args = parse_args()

    # ログ設定
    setup_logging(verbose=args.verbose)

    logger.info("Starting finance news workflow", args=vars(args))

    try:
        ...
        logger.info("Workflow completed successfully")
        return 0

    except Exception as e:
        logger.exception("Workflow failed", error=str(e))
        return 1
```

ログファイル出力例（`logs/news-workflow-2026-01-29.log`）：
```
2026-01-29 12:00:00 INFO  [finance_news_workflow] Starting finance news workflow
2026-01-29 12:00:00 INFO  [orchestrator] Workflow started
...
2026-01-29 12:15:00 INFO  [orchestrator] Workflow completed in 900.5s
2026-01-29 12:15:00 INFO  [finance_news_workflow] Workflow completed successfully
```

## 受け入れ条件

- [ ] ログファイルが `logs/news-workflow-{date}.log` に出力される
- [ ] コンソールにもログが出力される
- [ ] `--verbose` で DEBUG レベルログが出力される
- [ ] 通常時は INFO レベル以上のログが出力される
- [ ] utils_core.logging_config を使用
- [ ] pyright 型チェック成功

## 参照

- project.md: ログ出力 セクション
- `src/utils_core/logging_config.py`: ログ設定の実装

# P6-004: Orchestrator 進捗ログ

## 概要

utils_core のログ機能を使用して、ワークフローの進捗ログを出力する。

## フェーズ

Phase 6: オーケストレーター

## 依存タスク

- P6-001: Orchestrator 全コンポーネント統合

## 成果物

- `src/news/orchestrator.py`（更新）

## 実装内容

```python
from utils_core.logging_config import get_logger

logger = get_logger(__name__)

class NewsWorkflowOrchestrator:
    async def run(
        self,
        statuses: list[str] | None = None,
        max_articles: int | None = None,
        dry_run: bool = False,
    ) -> WorkflowResult:
        """ワークフローを実行"""
        started_at = datetime.now(timezone.utc)
        logger.info("Workflow started", statuses=statuses, max_articles=max_articles, dry_run=dry_run)

        # 1. 記事収集
        logger.info("[rss_collector] Collecting from feeds...")
        collected = await self._collector.collect(...)
        logger.info(f"[rss_collector] Collected {len(collected)} articles")

        # 2. 本文抽出
        logger.info(f"[trafilatura] Extracting body text (concurrency={self._config.extraction.concurrency})...")
        extracted = await self._extractor.extract_batch(...)

        success_count = sum(1 for e in extracted if e.extraction_status == ExtractionStatus.SUCCESS)
        failed_count = len(extracted) - success_count
        logger.info(f"[trafilatura] Extracted {success_count}/{len(extracted)} articles")

        if failed_count > 0:
            paywall_count = sum(1 for e in extracted if e.extraction_status == ExtractionStatus.PAYWALL)
            timeout_count = sum(1 for e in extracted if e.extraction_status == ExtractionStatus.TIMEOUT)
            logger.warning(f"[trafilatura] Failed: {failed_count} articles (paywall: {paywall_count}, timeout: {timeout_count})")

        # 3. AI要約
        logger.info(f"[summarizer] Summarizing {len(extracted_success)} articles (concurrency={self._config.summarization.concurrency})...")
        summarized = await self._summarizer.summarize_batch(...)
        logger.info(f"[summarizer] Summarized {len(summarized_success)}/{len(summarized)} articles")

        # 4. Issue 公開
        logger.info(f"[publisher] Publishing {len(summarized_success)} articles...")
        published = await self._publisher.publish_batch(...)

        success_count = sum(1 for p in published if p.publication_status == PublicationStatus.SUCCESS)
        duplicate_count = sum(1 for p in published if p.publication_status == PublicationStatus.DUPLICATE)
        logger.info(f"[publisher] Published {success_count} issues, skipped {duplicate_count} duplicates")

        # 完了
        elapsed = (datetime.now(timezone.utc) - started_at).total_seconds()
        logger.info(f"[orchestrator] Workflow completed in {elapsed:.1f}s")

        return result
```

ログ出力例：
```
2026-01-29 12:00:00 INFO  [orchestrator] Workflow started
2026-01-29 12:00:01 INFO  [rss_collector] Collecting from 29 feeds...
2026-01-29 12:00:05 INFO  [rss_collector] Collected 100 articles
2026-01-29 12:00:05 INFO  [trafilatura] Extracting body text (concurrency=5)...
2026-01-29 12:02:00 INFO  [trafilatura] Extracted 85/100 articles
2026-01-29 12:02:00 WARN  [trafilatura] Failed: 15 articles (paywall: 10, timeout: 5)
2026-01-29 12:02:00 INFO  [summarizer] Summarizing 85 articles (concurrency=3)...
2026-01-29 12:10:00 INFO  [summarizer] Summarized 80/85 articles
2026-01-29 12:10:00 INFO  [publisher] Publishing 80 articles...
2026-01-29 12:15:00 INFO  [publisher] Published 75 issues, skipped 5 duplicates
2026-01-29 12:15:00 INFO  [orchestrator] Workflow completed in 900.5s
```

## 受け入れ条件

- [ ] utils_core.logging_config.get_logger を使用
- [ ] 各ステージの開始・完了ログが出力される
- [ ] 失敗時は WARNING レベルでログ出力
- [ ] 処理件数がログに含まれる
- [ ] 処理時間がログに含まれる
- [ ] pyright 型チェック成功

## 参照

- project.md: ログ出力 セクション
- `src/utils_core/logging_config.py`: get_logger の実装

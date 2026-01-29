# P4-004: Summarizer セマフォベース並列処理

## 概要

asyncio.Semaphore を使用して並列要約処理を実装する。

## フェーズ

Phase 4: AI要約

## 依存タスク

- P4-003: Summarizer JSON 出力パース・バリデーション

## 成果物

- `src/news/summarizer.py`（更新）

## 実装内容

```python
import asyncio
from utils_core.logging_config import get_logger

logger = get_logger(__name__)

class Summarizer:
    async def summarize_batch(
        self,
        articles: list[ExtractedArticle],
        concurrency: int = 3,
    ) -> list[SummarizedArticle]:
        """複数記事を並列要約

        Parameters
        ----------
        articles : list[ExtractedArticle]
            本文抽出済み記事リスト
        concurrency : int, optional
            並列処理数（デフォルト: 3）

        Returns
        -------
        list[SummarizedArticle]
            要約結果リスト
        """
        logger.info(
            "Starting batch summarization",
            article_count=len(articles),
            concurrency=concurrency
        )

        semaphore = asyncio.Semaphore(concurrency)

        async def summarize_with_semaphore(article: ExtractedArticle) -> SummarizedArticle:
            async with semaphore:
                return await self.summarize(article)

        tasks = [summarize_with_semaphore(article) for article in articles]
        results = await asyncio.gather(*tasks)

        success_count = sum(1 for r in results if r.summarization_status == SummarizationStatus.SUCCESS)
        logger.info(
            "Batch summarization completed",
            total=len(articles),
            success=success_count,
            failed=len(articles) - success_count
        )

        return results
```

## 受け入れ条件

- [ ] `summarize_batch(articles, concurrency=3)` が実装されている
- [ ] Semaphore で同時実行数を制限（API レート制限対策）
- [ ] 全記事の処理完了まで待機
- [ ] 進捗ログが出力される
- [ ] pyright 型チェック成功

## 参照

- project.md: 処理設定 - summarization.concurrency

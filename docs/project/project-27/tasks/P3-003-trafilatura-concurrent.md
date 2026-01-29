# P3-003: TrafilaturaExtractor セマフォベース並列処理

## 概要

asyncio.Semaphore を使用して並列処理を実装する。

## フェーズ

Phase 3: 本文抽出

## 依存タスク

- P3-002: TrafilaturaExtractor 基本実装

## 成果物

- `src/news/extractors/trafilatura.py`（更新）

## 実装内容

BaseExtractor の `extract_batch` を継承・カスタマイズ：

```python
import asyncio
from utils_core.logging_config import get_logger

logger = get_logger(__name__)

class TrafilaturaExtractor(BaseExtractor):
    ...

    async def extract_batch(
        self,
        articles: list[CollectedArticle],
        concurrency: int = 5,
    ) -> list[ExtractedArticle]:
        """複数記事の本文を並列抽出

        Parameters
        ----------
        articles : list[CollectedArticle]
            収集された記事リスト
        concurrency : int, optional
            並列処理数（デフォルト: 5）

        Returns
        -------
        list[ExtractedArticle]
            本文抽出結果リスト
        """
        logger.info(
            "Starting batch extraction",
            article_count=len(articles),
            concurrency=concurrency
        )

        semaphore = asyncio.Semaphore(concurrency)
        results: list[ExtractedArticle] = []

        async def extract_with_semaphore(article: CollectedArticle) -> ExtractedArticle:
            async with semaphore:
                return await self.extract(article)

        tasks = [extract_with_semaphore(article) for article in articles]
        results = await asyncio.gather(*tasks, return_exceptions=False)

        success_count = sum(1 for r in results if r.extraction_status == ExtractionStatus.SUCCESS)
        logger.info(
            "Batch extraction completed",
            total=len(articles),
            success=success_count,
            failed=len(articles) - success_count
        )

        return results
```

## 受け入れ条件

- [ ] `extract_batch(articles, concurrency=5)` が実装されている
- [ ] Semaphore で同時実行数を制限
- [ ] 全記事の処理完了まで待機
- [ ] 進捗ログが出力される
- [ ] pyright 型チェック成功

## 参照

- project.md: 処理設定 - extraction.concurrency

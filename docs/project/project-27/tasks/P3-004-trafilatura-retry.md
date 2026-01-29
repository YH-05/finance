# P3-004: TrafilaturaExtractor リトライロジック

## 概要

失敗時に最大 3 回リトライする機能を追加する。

## フェーズ

Phase 3: 本文抽出

## 依存タスク

- P3-003: TrafilaturaExtractor セマフォベース並列処理

## 成果物

- `src/news/extractors/trafilatura.py`（更新）

## 実装内容

```python
import asyncio
from utils_core.logging_config import get_logger

logger = get_logger(__name__)

class TrafilaturaExtractor(BaseExtractor):
    def __init__(
        self,
        min_body_length: int = 200,
        max_retries: int = 3,
        timeout_seconds: int = 30,
    ) -> None:
        self._extractor = ArticleExtractor()
        self._min_body_length = min_body_length
        self._max_retries = max_retries
        self._timeout_seconds = timeout_seconds

    async def extract(self, article: CollectedArticle) -> ExtractedArticle:
        """単一記事の本文を抽出（リトライ付き）"""
        last_error: Exception | None = None

        for attempt in range(self._max_retries):
            try:
                # タイムアウト付きで抽出
                result = await asyncio.wait_for(
                    self._extract_impl(article),
                    timeout=self._timeout_seconds
                )
                return result

            except asyncio.TimeoutError:
                last_error = asyncio.TimeoutError(f"Timeout after {self._timeout_seconds}s")
                logger.warning(
                    "Extraction timeout",
                    url=str(article.url),
                    attempt=attempt + 1,
                    max_retries=self._max_retries
                )
            except Exception as e:
                last_error = e
                logger.warning(
                    "Extraction failed",
                    url=str(article.url),
                    attempt=attempt + 1,
                    max_retries=self._max_retries,
                    error=str(e)
                )

            # 指数バックオフ（1s, 2s, 4s）
            if attempt < self._max_retries - 1:
                await asyncio.sleep(2 ** attempt)

        # 全リトライ失敗
        return ExtractedArticle(
            collected=article,
            body_text=None,
            extraction_status=self._classify_error(last_error),
            extraction_method=self.extractor_name,
            error_message=str(last_error)
        )

    async def _extract_impl(self, article: CollectedArticle) -> ExtractedArticle:
        """実際の抽出処理（リトライなし）"""
        ...
```

## 受け入れ条件

- [ ] 最大 3 回のリトライ
- [ ] 指数バックオフ（1s, 2s, 4s）
- [ ] タイムアウト処理（デフォルト 30 秒）
- [ ] リトライ後も失敗した場合は適切なステータス
- [ ] リトライのログが出力される
- [ ] pyright 型チェック成功

## 参照

- project.md: 処理設定 - extraction.max_retries, extraction.timeout_seconds

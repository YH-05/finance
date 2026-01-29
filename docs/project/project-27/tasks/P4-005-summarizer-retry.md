# P4-005: Summarizer リトライロジック

## 概要

失敗時に最大 3 回リトライする機能を追加する。

## フェーズ

Phase 4: AI要約

## 依存タスク

- P4-004: Summarizer セマフォベース並列処理

## 成果物

- `src/news/summarizer.py`（更新）

## 実装内容

```python
import asyncio
from utils_core.logging_config import get_logger

logger = get_logger(__name__)

class Summarizer:
    def __init__(self, config: NewsWorkflowConfig) -> None:
        self._config = config
        self._prompt_template = config.summarization.prompt_template
        self._max_retries = config.summarization.max_retries
        self._timeout_seconds = config.summarization.timeout_seconds
        self._client = Anthropic()

    async def summarize(self, article: ExtractedArticle) -> SummarizedArticle:
        """単一記事を要約（リトライ付き）"""
        if article.body_text is None:
            return SummarizedArticle(
                extracted=article,
                summary=None,
                summarization_status=SummarizationStatus.SKIPPED,
                error_message="No body text available"
            )

        last_error: Exception | None = None

        for attempt in range(self._max_retries):
            try:
                response = await asyncio.wait_for(
                    self._call_claude(article),
                    timeout=self._timeout_seconds
                )
                summary = self._parse_response(response)

                return SummarizedArticle(
                    extracted=article,
                    summary=summary,
                    summarization_status=SummarizationStatus.SUCCESS,
                )

            except asyncio.TimeoutError:
                last_error = asyncio.TimeoutError(f"Timeout after {self._timeout_seconds}s")
                logger.warning(
                    "Summarization timeout",
                    title=article.collected.title,
                    attempt=attempt + 1,
                    max_retries=self._max_retries
                )
            except Exception as e:
                last_error = e
                logger.warning(
                    "Summarization failed",
                    title=article.collected.title,
                    attempt=attempt + 1,
                    max_retries=self._max_retries,
                    error=str(e)
                )

            # 指数バックオフ（1s, 2s, 4s）
            if attempt < self._max_retries - 1:
                await asyncio.sleep(2 ** attempt)

        # 全リトライ失敗
        status = SummarizationStatus.TIMEOUT if isinstance(last_error, asyncio.TimeoutError) else SummarizationStatus.FAILED
        return SummarizedArticle(
            extracted=article,
            summary=None,
            summarization_status=status,
            error_message=str(last_error)
        )
```

## 受け入れ条件

- [ ] 最大 3 回のリトライ
- [ ] 指数バックオフ（1s, 2s, 4s）
- [ ] タイムアウト処理（デフォルト 60 秒）
- [ ] リトライ後も失敗した場合は適切なステータス
- [ ] リトライのログが出力される
- [ ] pyright 型チェック成功

## 参照

- project.md: 処理設定 - summarization.max_retries, summarization.timeout_seconds

"""Summarizer for generating structured Japanese summaries of news articles.

This module provides the Summarizer class that uses Claude Agent SDK to generate
structured 4-section Japanese summaries of news articles.

The Summarizer works with ExtractedArticle inputs (articles that have undergone
body text extraction) and produces SummarizedArticle outputs with structured
summaries.

Claude Agent SDK Types
----------------------
The following types from claude-agent-sdk are used in this module:

- ``query`` : async function that returns an async iterator for streaming responses
- ``ClaudeAgentOptions`` : Configuration options (system_prompt, max_turns, allowed_tools)
- ``AssistantMessage`` : Response message from Claude containing content blocks
- ``TextBlock`` : Text content block within an AssistantMessage
- ``ResultMessage`` : Final result message with cost information

Examples
--------
>>> from news.summarizer import Summarizer
>>> from news.config.workflow import load_config
>>> config = load_config("data/config/news-collection-config.yaml")
>>> summarizer = Summarizer(config=config)
>>> result = await summarizer.summarize(extracted_article)
>>> result.summarization_status
<SummarizationStatus.SUCCESS: 'success'>
"""

from __future__ import annotations

import asyncio
import json
import re
from typing import TYPE_CHECKING

from pydantic import ValidationError

from news.models import (
    ExtractedArticle,
    StructuredSummary,
    SummarizationStatus,
    SummarizedArticle,
)
from news.utils.logging_config import get_logger

if TYPE_CHECKING:
    from news.config.workflow import NewsWorkflowConfig

logger = get_logger(__name__, module="summarizer")

# Claude model and max tokens configuration
CLAUDE_MODEL = "claude-sonnet-4-20250514"
CLAUDE_MAX_TOKENS = 1024


class Summarizer:
    """Claude Agent SDK を使用した構造化要約。

    記事本文を分析し、4セクション構造の日本語要約を生成する。

    Parameters
    ----------
    config : NewsWorkflowConfig
        ワークフロー設定。summarization セクションからプロンプトテンプレートと
        並列処理数、タイムアウト設定を取得する。

    Attributes
    ----------
    _config : NewsWorkflowConfig
        ワークフロー設定の参照。
    _prompt_template : str
        AI 要約に使用するプロンプトテンプレート。
    _max_retries : int
        最大リトライ回数。
    _timeout_seconds : int
        タイムアウト秒数。

    Examples
    --------
    >>> from news.summarizer import Summarizer
    >>> from news.config.workflow import load_config
    >>> config = load_config("config.yaml")
    >>> summarizer = Summarizer(config=config)
    >>> result = await summarizer.summarize(extracted_article)
    >>> result.summary.overview
    'S&P 500が上昇...'

    Notes
    -----
    - 本文抽出が失敗している記事（body_text が None）は SKIPPED ステータスで返す
    - Claude Agent SDK を使用して Claude API を呼び出す（P9-002で実装）
    """

    def __init__(self, config: NewsWorkflowConfig) -> None:
        """Summarizer を初期化する。

        Parameters
        ----------
        config : NewsWorkflowConfig
            ワークフロー設定。summarization セクションを使用する。
        """
        self._config = config
        self._prompt_template = config.summarization.prompt_template
        self._max_retries = config.summarization.max_retries
        self._timeout_seconds = config.summarization.timeout_seconds
        # Note: Anthropic client removed - claude-agent-sdk uses query() function directly

        logger.debug(
            "Summarizer initialized",
            prompt_template_length=len(self._prompt_template),
            concurrency=config.summarization.concurrency,
            timeout_seconds=self._timeout_seconds,
            max_retries=self._max_retries,
        )

    async def summarize(self, article: ExtractedArticle) -> SummarizedArticle:
        """単一記事を要約する。

        記事の本文を分析し、4セクション構造の日本語要約を生成する。
        本文抽出が失敗している記事は SKIPPED ステータスで即座に返す。

        Parameters
        ----------
        article : ExtractedArticle
            本文抽出済み記事。extraction_status が SUCCESS で body_text が
            存在する場合のみ要約を実行する。

        Returns
        -------
        SummarizedArticle
            要約結果を含む記事オブジェクト。以下のいずれかの状態：
            - SUCCESS: 要約成功。summary フィールドに StructuredSummary を含む
            - SKIPPED: 本文なしでスキップ
            - FAILED: 要約処理中にエラー発生
            - TIMEOUT: 要約処理がタイムアウト

        Notes
        -----
        - 非同期メソッドとして実装されており、await が必要
        - Anthropic SDK を使用して Claude API を呼び出す

        Examples
        --------
        >>> result = await summarizer.summarize(extracted_article)
        >>> if result.summarization_status == SummarizationStatus.SUCCESS:
        ...     print(result.summary.overview)
        """
        logger.debug(
            "Starting summarization",
            article_url=str(article.collected.url),
            has_body_text=article.body_text is not None,
            extraction_status=str(article.extraction_status),
        )

        # 本文抽出が失敗している場合はスキップ
        if article.body_text is None:
            logger.info(
                "Skipping summarization: no body text",
                article_url=str(article.collected.url),
                extraction_status=str(article.extraction_status),
            )
            return SummarizedArticle(
                extracted=article,
                summary=None,
                summarization_status=SummarizationStatus.SKIPPED,
                error_message="No body text available",
            )

        # Claude API を呼び出して要約を生成（リトライ付き）
        last_error: Exception | None = None

        for attempt in range(self._max_retries):
            try:
                response_text = self._call_claude(article)
                summary = self._parse_response(response_text)

                logger.info(
                    "Summarization completed",
                    article_url=str(article.collected.url),
                    overview_length=len(summary.overview),
                    key_points_count=len(summary.key_points),
                    attempt=attempt + 1,
                )

                return SummarizedArticle(
                    extracted=article,
                    summary=summary,
                    summarization_status=SummarizationStatus.SUCCESS,
                    error_message=None,
                )

            except ValueError as e:
                # JSON parse error or Pydantic validation error - don't retry
                error_message = str(e)
                logger.error(
                    "Parse/validation error",
                    article_url=str(article.collected.url),
                    error=error_message,
                )
                return SummarizedArticle(
                    extracted=article,
                    summary=None,
                    summarization_status=SummarizationStatus.FAILED,
                    error_message=error_message,
                )

            except TimeoutError:
                last_error = TimeoutError(f"Timeout after {self._timeout_seconds}s")
                logger.warning(
                    "Summarization timeout",
                    article_url=str(article.collected.url),
                    attempt=attempt + 1,
                    max_retries=self._max_retries,
                )

            except Exception as e:
                last_error = e
                logger.warning(
                    "Summarization failed",
                    article_url=str(article.collected.url),
                    attempt=attempt + 1,
                    max_retries=self._max_retries,
                    error=str(e),
                )

            # 指数バックオフ（1s, 2s, 4s）- 最後の試行後はスリープしない
            if attempt < self._max_retries - 1:
                await asyncio.sleep(2**attempt)

        # 全リトライ失敗
        if isinstance(last_error, TimeoutError):
            status = SummarizationStatus.TIMEOUT
        else:
            status = SummarizationStatus.FAILED

        error_message = str(last_error) if last_error else "Unknown error"
        return SummarizedArticle(
            extracted=article,
            summary=None,
            summarization_status=status,
            error_message=error_message,
        )

    def _call_claude(self, article: ExtractedArticle) -> str:
        """Claude API を呼び出して要約を生成する。

        .. deprecated::
            This method uses the legacy Anthropic SDK and will be replaced
            by ``_call_claude_sdk`` in P9-002 which uses claude-agent-sdk.

        Parameters
        ----------
        article : ExtractedArticle
            本文抽出済み記事。

        Returns
        -------
        str
            Claude からの JSON レスポンス。

        Raises
        ------
        RuntimeError
            Anthropic SDK が削除されたため、このメソッドは現在動作しません。
            P9-002 で _call_claude_sdk に置き換えられます。

        Notes
        -----
        - 記事情報（タイトル、ソース、公開日、本文）をプロンプトに含める
        - レスポンスは JSON 形式の StructuredSummary を期待
        """
        # 記事情報をプロンプトに含める
        collected = article.collected
        published_str = (
            collected.published.isoformat() if collected.published else "不明"
        )

        prompt = f"""以下のニュース記事を日本語で要約してください。

## 記事情報
- タイトル: {collected.title}
- ソース: {collected.source.source_name}
- 公開日: {published_str}

## 本文
{article.body_text}

## 出力形式
以下のJSON形式で回答してください：
{{
    "overview": "記事の概要（1-2文）",
    "key_points": ["キーポイント1", "キーポイント2", ...],
    "market_impact": "市場への影響",
    "related_info": "関連情報（任意、なければnull）"
}}

JSONのみを出力し、他のテキストは含めないでください。"""

        logger.debug(
            "Calling Claude API",
            article_url=str(collected.url),
            prompt_length=len(prompt),
        )

        # AIDEV-NOTE: Anthropic SDK removed in P9-001
        # This method will be replaced by _call_claude_sdk in P9-002
        raise NotImplementedError(
            "Anthropic SDK has been removed. "
            "Use _call_claude_sdk (to be implemented in P9-002) instead."
        )

    def _parse_response(self, response_text: str) -> StructuredSummary:
        """Claude のレスポンスを StructuredSummary にパースする。

        Parameters
        ----------
        response_text : str
            Claude からの JSON レスポンス。```json ... ``` 形式にも対応。

        Returns
        -------
        StructuredSummary
            パースされた構造化要約。

        Raises
        ------
        ValueError
            JSON パースまたは Pydantic バリデーションに失敗した場合。
        """
        # ```json ... ``` 形式の抽出
        json_match = re.search(r"```json\s*(.*?)\s*```", response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            # 直接 JSON の場合
            json_str = response_text.strip()

        try:
            data = json.loads(json_str)
            return StructuredSummary.model_validate(data)
        except json.JSONDecodeError as e:
            raise ValueError(f"JSON parse error: {e}") from e
        except ValidationError as e:
            raise ValueError(f"Validation error: {e}") from e

    async def summarize_batch(
        self,
        articles: list[ExtractedArticle],
        concurrency: int = 3,
    ) -> list[SummarizedArticle]:
        """複数記事を並列要約する。

        指定された並列数で複数の記事を同時に要約処理する。
        結果は入力と同じ順序で返される。

        Parameters
        ----------
        articles : list[ExtractedArticle]
            本文抽出済み記事のリスト。空リストの場合は空リストを返す。
        concurrency : int, optional
            並列処理数。デフォルトは 3。config.summarization.concurrency を
            上書きする場合に使用する。

        Returns
        -------
        list[SummarizedArticle]
            要約結果のリスト。入力と同じ順序を保持する。

        Notes
        -----
        - セマフォを使用して並列数を制限
        - 個々の要約が失敗しても他の要約は継続
        - 各記事の結果は独立して成功/失敗を判定

        Examples
        --------
        >>> articles = [article1, article2, article3]
        >>> results = await summarizer.summarize_batch(articles, concurrency=5)
        >>> len(results)
        3
        >>> all(isinstance(r, SummarizedArticle) for r in results)
        True
        """
        if not articles:
            logger.debug("summarize_batch called with empty list")
            return []

        logger.info(
            "Starting batch summarization",
            article_count=len(articles),
            concurrency=concurrency,
        )

        # セマフォで並列数を制限
        semaphore = asyncio.Semaphore(concurrency)

        async def _summarize_with_semaphore(
            article: ExtractedArticle,
        ) -> SummarizedArticle:
            async with semaphore:
                return await self.summarize(article)

        # 全記事を並列処理
        tasks = [_summarize_with_semaphore(article) for article in articles]
        results = await asyncio.gather(*tasks)

        logger.info(
            "Batch summarization completed",
            total=len(results),
            success=sum(
                1
                for r in results
                if r.summarization_status == SummarizationStatus.SUCCESS
            ),
            skipped=sum(
                1
                for r in results
                if r.summarization_status == SummarizationStatus.SKIPPED
            ),
            failed=sum(
                1
                for r in results
                if r.summarization_status == SummarizationStatus.FAILED
            ),
        )

        return list(results)


__all__ = [
    "Summarizer",
]

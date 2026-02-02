"""Summarizer processor for generating Japanese summaries of news articles.

This module provides the SummarizerProcessor class that uses Claude Agent SDK
to generate Japanese summaries of English news articles.

Examples
--------
>>> from news.processors.summarizer import SummarizerProcessor
>>> processor = SummarizerProcessor()
>>> result = processor.process(article)
>>> result.summary_ja
'記事の日本語要約...'
"""

from __future__ import annotations

import json
from typing import Any

from utils_core.logging import get_logger

from ..core.article import Article  # noqa: TC001
from ..core.processor import ProcessorType
from .agent_base import AgentProcessor, AgentProcessorError

logger = get_logger(__name__, module="summarizer")


class SummarizerProcessor(AgentProcessor):
    """Processor for generating Japanese summaries of news articles.

    This processor uses Claude Agent SDK to summarize English news articles
    in Japanese. It implements the ProcessorProtocol interface and inherits
    from AgentProcessor for Claude SDK integration.

    Attributes
    ----------
    processor_name : str
        Returns "claude_summarizer".
    processor_type : ProcessorType
        Returns ProcessorType.SUMMARIZER.

    Notes
    -----
    - The processor expects the article to have a title and optionally a summary.
    - The AI response must be a JSON object with a "summary_ja" field.
    - The original article is not modified; a new Article with updated
      summary_ja is returned.

    Examples
    --------
    >>> processor = SummarizerProcessor()
    >>> result = processor.process(article)
    >>> result.summary_ja
    'Appleは四半期決算で過去最高の業績を発表。'

    >>> results = processor.process_batch([article1, article2])
    >>> all(r.summary_ja is not None for r in results)
    True
    """

    @property
    def processor_name(self) -> str:
        """Name of the summarizer processor.

        Returns
        -------
        str
            "claude_summarizer"
        """
        return "claude_summarizer"

    @property
    def processor_type(self) -> ProcessorType:
        """Type of the processor.

        Returns
        -------
        ProcessorType
            ProcessorType.SUMMARIZER
        """
        return ProcessorType.SUMMARIZER

    def _build_prompt(self, article: Article) -> str:
        """Build the prompt for Japanese summarization.

        Parameters
        ----------
        article : Article
            The article to summarize.

        Returns
        -------
        str
            The prompt string for Claude Agent SDK.

        Notes
        -----
        The prompt instructs the AI to:
        1. Read the article title and summary (if available)
        2. Generate a concise Japanese summary
        3. Return the result in JSON format
        """
        summary_text = article.summary or "(内容なし)"

        prompt = f"""以下のニュース記事を日本語で簡潔に要約してください。

## 記事情報

**タイトル**: {article.title}

**内容**: {summary_text}

## 指示

1. 記事の主要なポイントを日本語で要約してください
2. 2〜3文程度の簡潔な要約にしてください
3. 専門用語は適切に翻訳または説明してください

## 出力形式

以下のJSON形式で回答してください。JSON以外の文章は含めないでください。

{{"summary_ja": "日本語の要約文"}}
"""

        logger.debug(
            "Built summarization prompt",
            processor_name=self.processor_name,
            article_title=article.title[:50] + "..."
            if len(article.title) > 50
            else article.title,
            prompt_length=len(prompt),
        )

        return prompt

    def _parse_response(self, response: str, article: Article) -> dict[str, Any]:
        """Parse the AI response to extract the Japanese summary.

        Parameters
        ----------
        response : str
            The raw JSON response from Claude Agent SDK.
        article : Article
            The original article being processed.

        Returns
        -------
        dict[str, Any]
            Dictionary containing the "summary_ja" field.

        Raises
        ------
        AgentProcessorError
            If the response is not valid JSON or doesn't contain "summary_ja".
        """
        logger.debug(
            "Parsing summarization response",
            processor_name=self.processor_name,
            response_length=len(response),
        )

        try:
            data = json.loads(response)
        except json.JSONDecodeError as e:
            logger.error(
                "Failed to parse JSON response",
                processor_name=self.processor_name,
                error=str(e),
                response_preview=response[:100] if len(response) > 100 else response,
            )
            raise AgentProcessorError(
                message=f"Failed to parse JSON response: {e}",
                processor_name=self.processor_name,
                cause=e,
            ) from e

        if "summary_ja" not in data:
            logger.error(
                "Response missing summary_ja field",
                processor_name=self.processor_name,
                response_keys=list(data.keys()),
            )
            raise AgentProcessorError(
                message="Response missing required 'summary_ja' field",
                processor_name=self.processor_name,
            )

        logger.debug(
            "Successfully parsed summarization response",
            processor_name=self.processor_name,
            summary_length=len(data["summary_ja"]),
        )

        return {"summary_ja": data["summary_ja"]}


__all__ = [
    "SummarizerProcessor",
]

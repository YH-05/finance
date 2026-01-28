"""Classifier processor for categorizing and tagging news articles.

This module provides the ClassifierProcessor class that uses Claude Agent SDK
to classify news articles into categories and extract relevant tags.

Examples
--------
>>> from news.processors.classifier import ClassifierProcessor
>>> processor = ClassifierProcessor()
>>> result = processor.process(article)
>>> result.category
'finance'
>>> result.tags
['earnings', 'apple', 'technology']
"""

from __future__ import annotations

import json
from typing import Any

from ..core.article import Article  # noqa: TC001
from ..core.processor import ProcessorType
from ..utils.logging_config import get_logger
from .agent_base import AgentProcessor, AgentProcessorError

logger = get_logger(__name__, module="classifier")


class ClassifierProcessor(AgentProcessor):
    """Processor for categorizing and tagging news articles.

    This processor uses Claude Agent SDK to classify news articles into
    predefined categories and extract relevant tags/keywords. It implements
    the ProcessorProtocol interface and inherits from AgentProcessor for
    Claude SDK integration.

    Attributes
    ----------
    processor_name : str
        Returns "claude_classifier".
    processor_type : ProcessorType
        Returns ProcessorType.CLASSIFIER.

    Notes
    -----
    - The processor expects the article to have a title and optionally a summary.
    - The AI response must be a JSON object with "category" and "tags" fields.
    - The original article is not modified; a new Article with updated
      category and tags is returned.
    - Supported categories include: finance, technology, macro_economy,
      market, company, politics, other.

    Examples
    --------
    >>> processor = ClassifierProcessor()
    >>> result = processor.process(article)
    >>> result.category
    'finance'
    >>> result.tags
    ['earnings', 'quarterly_report', 'apple']

    >>> results = processor.process_batch([article1, article2])
    >>> all(r.category is not None for r in results)
    True
    """

    @property
    def processor_name(self) -> str:
        """Name of the classifier processor.

        Returns
        -------
        str
            "claude_classifier"
        """
        return "claude_classifier"

    @property
    def processor_type(self) -> ProcessorType:
        """Type of the processor.

        Returns
        -------
        ProcessorType
            ProcessorType.CLASSIFIER
        """
        return ProcessorType.CLASSIFIER

    def _build_prompt(self, article: Article) -> str:
        """Build the prompt for classification and tagging.

        Parameters
        ----------
        article : Article
            The article to classify and tag.

        Returns
        -------
        str
            The prompt string for Claude Agent SDK.

        Notes
        -----
        The prompt instructs the AI to:
        1. Read the article title and summary (if available)
        2. Classify into one of the predefined categories
        3. Extract relevant tags/keywords
        4. Return the result in JSON format
        """
        summary_text = article.summary or "(内容なし)"

        prompt = f"""以下のニュース記事を分類し、関連するタグを抽出してください。

## 記事情報

**タイトル**: {article.title}

**内容**: {summary_text}

## 指示

1. 記事を以下のカテゴリのいずれかに分類してください:
   - finance: 金融・投資・銀行・保険関連
   - technology: テクノロジー・IT・AI・ソフトウェア関連
   - macro_economy: マクロ経済・金利・インフレ・GDP・中央銀行関連
   - market: 株式市場・債券市場・為替市場・商品市場関連
   - company: 企業ニュース・決算・M&A・人事関連
   - politics: 政治・規制・政策関連
   - other: 上記に該当しない場合

2. 記事から重要なキーワード・エンティティを抽出してタグとして設定してください:
   - 企業名、人名、製品名などの固有名詞
   - 重要な概念やトピック
   - 3〜8個程度のタグを抽出

## 出力形式

以下のJSON形式で回答してください。JSON以外の文章は含めないでください。

{{"category": "カテゴリ名", "tags": ["タグ1", "タグ2", "タグ3"]}}
"""

        logger.debug(
            "Built classification prompt",
            processor_name=self.processor_name,
            article_title=article.title[:50] + "..."
            if len(article.title) > 50
            else article.title,
            prompt_length=len(prompt),
        )

        return prompt

    def _parse_response(self, response: str, article: Article) -> dict[str, Any]:
        """Parse the AI response to extract category and tags.

        Parameters
        ----------
        response : str
            The raw JSON response from Claude Agent SDK.
        article : Article
            The original article being processed.

        Returns
        -------
        dict[str, Any]
            Dictionary containing the "category" and "tags" fields.

        Raises
        ------
        AgentProcessorError
            If the response is not valid JSON or doesn't contain required fields.
        """
        logger.debug(
            "Parsing classification response",
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

        if "category" not in data:
            logger.error(
                "Response missing category field",
                processor_name=self.processor_name,
                response_keys=list(data.keys()),
            )
            raise AgentProcessorError(
                message="Response missing required 'category' field",
                processor_name=self.processor_name,
            )

        if "tags" not in data:
            logger.error(
                "Response missing tags field",
                processor_name=self.processor_name,
                response_keys=list(data.keys()),
            )
            raise AgentProcessorError(
                message="Response missing required 'tags' field",
                processor_name=self.processor_name,
            )

        logger.debug(
            "Successfully parsed classification response",
            processor_name=self.processor_name,
            category=data["category"],
            tag_count=len(data["tags"]),
        )

        return {"category": data["category"], "tags": data["tags"]}


__all__ = [
    "ClassifierProcessor",
]

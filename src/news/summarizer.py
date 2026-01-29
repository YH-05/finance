"""Summarizer for generating structured Japanese summaries of news articles.

This module provides the Summarizer class that uses Anthropic SDK to generate
structured 4-section Japanese summaries of news articles.

The Summarizer works with ExtractedArticle inputs (articles that have undergone
body text extraction) and produces SummarizedArticle outputs with structured
summaries.

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
from typing import TYPE_CHECKING

from anthropic import Anthropic

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
    """Anthropic SDK を使用した構造化要約。

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
    _client : Anthropic
        Anthropic API クライアント。

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
    - Anthropic SDK を使用して Claude API を呼び出す
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
        self._client = Anthropic()

        logger.debug(
            "Summarizer initialized",
            prompt_template_length=len(self._prompt_template),
            concurrency=config.summarization.concurrency,
            timeout_seconds=config.summarization.timeout_seconds,
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

        # Claude API を呼び出して要約を生成
        try:
            response_text = self._call_claude(article)
            summary = self._parse_response(response_text)

            logger.info(
                "Summarization completed",
                article_url=str(article.collected.url),
                overview_length=len(summary.overview),
                key_points_count=len(summary.key_points),
            )

            return SummarizedArticle(
                extracted=article,
                summary=summary,
                summarization_status=SummarizationStatus.SUCCESS,
                error_message=None,
            )
        except json.JSONDecodeError as e:
            error_message = f"Failed to parse Claude response as JSON: {e}"
            logger.error(
                "JSON parse error",
                article_url=str(article.collected.url),
                error=str(e),
            )
            return SummarizedArticle(
                extracted=article,
                summary=None,
                summarization_status=SummarizationStatus.FAILED,
                error_message=error_message,
            )
        except Exception as e:
            error_message = f"Claude API error: {e}"
            logger.error(
                "Claude API error",
                article_url=str(article.collected.url),
                error=str(e),
                exc_info=True,
            )
            return SummarizedArticle(
                extracted=article,
                summary=None,
                summarization_status=SummarizationStatus.FAILED,
                error_message=error_message,
            )

    def _call_claude(self, article: ExtractedArticle) -> str:
        """Claude API を呼び出して要約を生成する。

        Parameters
        ----------
        article : ExtractedArticle
            本文抽出済み記事。

        Returns
        -------
        str
            Claude からの JSON レスポンス。

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

        response = self._client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=CLAUDE_MAX_TOKENS,
            messages=[{"role": "user", "content": prompt}],
        )

        response_text = response.content[0].text

        logger.debug(
            "Claude API response received",
            article_url=str(collected.url),
            response_length=len(response_text),
        )

        return response_text

    def _parse_response(self, response_text: str) -> StructuredSummary:
        """Claude のレスポンスを StructuredSummary にパースする。

        Parameters
        ----------
        response_text : str
            Claude からの JSON レスポンス。

        Returns
        -------
        StructuredSummary
            パースされた構造化要約。

        Raises
        ------
        json.JSONDecodeError
            JSON パースに失敗した場合。
        """
        data = json.loads(response_text)

        return StructuredSummary(
            overview=data["overview"],
            key_points=data["key_points"],
            market_impact=data["market_impact"],
            related_info=data.get("related_info"),
        )

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

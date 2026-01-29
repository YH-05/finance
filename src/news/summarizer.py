"""Summarizer for generating structured Japanese summaries of news articles.

This module provides the Summarizer class that uses Claude Agent SDK to generate
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
from typing import TYPE_CHECKING

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
    - Claude Agent SDK との統合は P4-002 で実装予定
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
        - Claude Agent SDK との統合は P4-002 で実装予定
        - 現在の実装は body_text がある場合でも TODO として処理継続

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

        # TODO: Claude Agent SDK 統合（P4-002）
        # 現在は基本構造のみ。実際の要約処理は P4-002 で実装予定。
        logger.debug(
            "Summarization will be implemented in P4-002",
            article_url=str(article.collected.url),
            body_text_length=len(article.body_text),
        )

        # P4-002 までの仮実装: 基本的な StructuredSummary を返す
        # 実際の AI 要約は P4-002 で実装
        placeholder_summary = StructuredSummary(
            overview="[要約は P4-002 で実装予定]",
            key_points=["[キーポイントは P4-002 で実装予定]"],
            market_impact="[市場への影響は P4-002 で実装予定]",
            related_info=None,
        )

        return SummarizedArticle(
            extracted=article,
            summary=placeholder_summary,
            summarization_status=SummarizationStatus.SUCCESS,
            error_message=None,
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

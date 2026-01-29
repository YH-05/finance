"""Publisher for creating GitHub Issues from summarized articles.

This module provides the Publisher class that creates GitHub Issues from
summarized news articles and adds them to a GitHub Project.

The Publisher works with SummarizedArticle inputs (articles that have undergone
AI summarization) and produces PublishedArticle outputs with Issue information.

Examples
--------
>>> from news.publisher import Publisher
>>> from news.config.workflow import load_config
>>> config = load_config("data/config/news-collection-config.yaml")
>>> publisher = Publisher(config=config)
>>> result = await publisher.publish(summarized_article)
>>> result.publication_status
<PublicationStatus.SUCCESS: 'success'>
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from news.models import (
    PublicationStatus,
    PublishedArticle,
    SummarizedArticle,
)
from news.utils.logging_config import get_logger

if TYPE_CHECKING:
    from news.config.workflow import NewsWorkflowConfig

logger = get_logger(__name__, module="publisher")


class Publisher:
    """GitHub Issue作成とProject追加。

    要約済み記事を GitHub Issue として作成し、
    指定された Project に追加する。

    Parameters
    ----------
    config : NewsWorkflowConfig
        ワークフロー設定。github セクションから Issue 作成先の
        リポジトリ、Project ID、Status フィールド ID などを取得する。

    Attributes
    ----------
    _config : NewsWorkflowConfig
        ワークフロー設定の参照。
    _repo : str
        Issue を作成する GitHub リポジトリ（"owner/repo" 形式）。
    _project_id : str
        GitHub Project ID（PVT_...）。
    _project_number : int
        GitHub Project 番号。
    _status_field_id : str
        GitHub Project の Status フィールド ID。
    _published_date_field_id : str
        GitHub Project の公開日フィールド ID。
    _status_mapping : dict[str, str]
        カテゴリから GitHub Status 名へのマッピング。
    _status_ids : dict[str, str]
        GitHub Status 名から Status ID へのマッピング。

    Examples
    --------
    >>> from news.publisher import Publisher
    >>> from news.config.workflow import load_config
    >>> config = load_config("config.yaml")
    >>> publisher = Publisher(config=config)
    >>> result = await publisher.publish(summarized_article)
    >>> result.issue_number
    123

    Notes
    -----
    - 要約が失敗している記事（summary が None）は SKIPPED ステータスで返す
    - 重複チェックは publish_batch() 内で行う
    - 実際の Issue 作成処理は P5-002 以降で実装
    """

    def __init__(self, config: NewsWorkflowConfig) -> None:
        """Publisher を初期化する。

        Parameters
        ----------
        config : NewsWorkflowConfig
            ワークフロー設定。github セクションを使用する。
        """
        self._config = config
        self._repo = config.github.repository
        self._project_id = config.github.project_id
        self._project_number = config.github.project_number
        self._status_field_id = config.github.status_field_id
        self._published_date_field_id = config.github.published_date_field_id
        self._status_mapping = config.status_mapping
        self._status_ids = config.github_status_ids

        logger.debug(
            "Publisher initialized",
            repository=self._repo,
            project_number=self._project_number,
            status_mapping_count=len(self._status_mapping),
        )

    async def publish(self, article: SummarizedArticle) -> PublishedArticle:
        """単一記事をIssueとして公開。

        要約済み記事を分析し、GitHub Issue を作成する。
        要約が失敗している記事は SKIPPED ステータスで即座に返す。

        Parameters
        ----------
        article : SummarizedArticle
            要約済み記事。summarization_status が SUCCESS で summary が
            存在する場合のみ Issue を作成する。

        Returns
        -------
        PublishedArticle
            公開結果を含むオブジェクト。以下のいずれかの状態：
            - SUCCESS: Issue 作成成功。issue_number と issue_url を含む
            - SKIPPED: 要約なしでスキップ
            - FAILED: Issue 作成中にエラー発生
            - DUPLICATE: 重複 Issue が検出されスキップ

        Notes
        -----
        - 非同期メソッドとして実装されており、await が必要
        - 実際の Issue 作成は P5-002 以降で実装

        Examples
        --------
        >>> result = await publisher.publish(summarized_article)
        >>> if result.publication_status == PublicationStatus.SUCCESS:
        ...     print(f"Created Issue #{result.issue_number}")
        """
        logger.debug(
            "Starting publish",
            article_url=str(article.extracted.collected.url),
            has_summary=article.summary is not None,
            summarization_status=str(article.summarization_status),
        )

        # 要約が失敗している場合はスキップ
        if article.summary is None:
            logger.info(
                "Skipping publish: no summary",
                article_url=str(article.extracted.collected.url),
                summarization_status=str(article.summarization_status),
            )
            return PublishedArticle(
                summarized=article,
                issue_number=None,
                issue_url=None,
                publication_status=PublicationStatus.SKIPPED,
                error_message="No summary available",
            )

        # TODO: Issue 作成処理（P5-002以降）
        raise NotImplementedError("Issue creation will be implemented in P5-002")

    async def publish_batch(
        self,
        articles: list[SummarizedArticle],
        dry_run: bool = False,
    ) -> list[PublishedArticle]:
        """複数記事を公開（重複チェック含む）。

        指定された記事を順番に GitHub Issue として公開する。
        重複チェックを行い、既に公開済みの記事はスキップする。

        Parameters
        ----------
        articles : list[SummarizedArticle]
            要約済み記事のリスト。空リストの場合は空リストを返す。
        dry_run : bool, optional
            True の場合、実際の Issue 作成をスキップする。
            デフォルトは False。

        Returns
        -------
        list[PublishedArticle]
            公開結果のリスト。入力と同じ順序を保持する。

        Notes
        -----
        - 個々の記事の公開が失敗しても他の記事は継続
        - dry_run=True の場合、Issue は作成されないがログ出力は行う
        - 重複チェックは P5-004 以降で実装

        Examples
        --------
        >>> articles = [article1, article2, article3]
        >>> results = await publisher.publish_batch(articles, dry_run=True)
        >>> len(results)
        3
        """
        if not articles:
            logger.debug("publish_batch called with empty list")
            return []

        logger.info(
            "Starting batch publish",
            article_count=len(articles),
            dry_run=dry_run,
        )

        results: list[PublishedArticle] = []

        for article in articles:
            result = await self.publish(article)
            results.append(result)

        logger.info(
            "Batch publish completed",
            total=len(results),
            success=sum(
                1 for r in results if r.publication_status == PublicationStatus.SUCCESS
            ),
            skipped=sum(
                1 for r in results if r.publication_status == PublicationStatus.SKIPPED
            ),
            failed=sum(
                1 for r in results if r.publication_status == PublicationStatus.FAILED
            ),
        )

        return results


__all__ = [
    "Publisher",
]

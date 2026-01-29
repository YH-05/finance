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

import subprocess  # nosec B404 - gh CLI is trusted
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

        # Issue 本文とタイトルを生成
        issue_body = self._generate_issue_body(article)
        issue_title = self._generate_issue_title(article)

        logger.debug(
            "Generated issue content",
            article_url=str(article.extracted.collected.url),
            title_length=len(issue_title),
            body_length=len(issue_body),
        )

        # Issue 作成
        try:
            issue_number, issue_url = await self._create_issue(article)

            # Project に追加してフィールドを設定
            await self._add_to_project(issue_number, article)

            logger.info(
                "Issue created successfully",
                issue_number=issue_number,
                issue_url=issue_url,
                article_url=str(article.extracted.collected.url),
            )

            return PublishedArticle(
                summarized=article,
                issue_number=issue_number,
                issue_url=issue_url,
                publication_status=PublicationStatus.SUCCESS,
            )

        except subprocess.CalledProcessError as e:
            error_msg = f"gh command failed: {e.stderr if e.stderr else str(e)}"
            logger.error(
                "Issue creation failed",
                error=error_msg,
                article_url=str(article.extracted.collected.url),
            )
            return PublishedArticle(
                summarized=article,
                issue_number=None,
                issue_url=None,
                publication_status=PublicationStatus.FAILED,
                error_message=error_msg,
            )
        except Exception as e:
            error_msg = f"Unexpected error: {e}"
            logger.error(
                "Issue creation failed unexpectedly",
                error=error_msg,
                error_type=type(e).__name__,
                article_url=str(article.extracted.collected.url),
            )
            return PublishedArticle(
                summarized=article,
                issue_number=None,
                issue_url=None,
                publication_status=PublicationStatus.FAILED,
                error_message=error_msg,
            )

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

    def _generate_issue_body(self, article: SummarizedArticle) -> str:
        """Issue本文を生成。

        4セクション構造（概要、キーポイント、市場への影響、関連情報）と
        メタデータ（ソース、公開日、URL）を含むMarkdown形式の本文を生成する。

        Parameters
        ----------
        article : SummarizedArticle
            要約済み記事。summary が存在することを前提とする。

        Returns
        -------
        str
            Markdown形式のIssue本文。

        Notes
        -----
        - summary が None の場合の動作は未定義（呼び出し元で事前にチェックすること）
        - related_info が None の場合、関連情報セクションは省略される
        - published が None の場合、公開日は「不明」と表示される
        """
        # article.summary is not None であることは呼び出し元で保証されている
        summary = article.summary
        assert summary is not None  # type: ignore[union-attr]

        collected = article.extracted.collected

        # キーポイントをマークダウンリストに変換
        key_points_md = "\n".join(f"- {point}" for point in summary.key_points)

        # 関連情報（オプション）
        related_info_section = ""
        if summary.related_info:
            related_info_section = f"""
## 関連情報
{summary.related_info}
"""

        # 公開日のフォーマット
        published_str = (
            collected.published.strftime("%Y-%m-%d %H:%M")
            if collected.published
            else "不明"
        )

        body = f"""# {collected.title}

## 概要
{summary.overview}

## キーポイント
{key_points_md}

## 市場への影響
{summary.market_impact}
{related_info_section}
---
**ソース**: {collected.source.source_name}
**公開日**: {published_str}
**URL**: {collected.url}
"""
        return body

    def _generate_issue_title(self, article: SummarizedArticle) -> str:
        """Issueタイトルを生成。

        カテゴリに基づくプレフィックスを付与したタイトルを生成する。

        Parameters
        ----------
        article : SummarizedArticle
            要約済み記事。

        Returns
        -------
        str
            プレフィックス付きのIssueタイトル（例: "[index] 記事タイトル"）。

        Notes
        -----
        - カテゴリから status へのマッピングは _status_mapping を使用
        - マッピングにないカテゴリの場合は "other" をプレフィックスとして使用
        """
        category = article.extracted.collected.source.category
        status = self._status_mapping.get(category, "other")
        return f"[{status}] {article.extracted.collected.title}"

    def _resolve_status(self, article: SummarizedArticle) -> tuple[str, str]:
        """カテゴリからGitHub Statusを解決。

        ArticleSource.category から status_mapping を使用して Status 名を取得し、
        github_status_ids から Status Option ID を取得する。

        Parameters
        ----------
        article : SummarizedArticle
            要約済み記事。

        Returns
        -------
        tuple[str, str]
            (Status名, Status Option ID) のタプル。
            - Status名: "index", "stock", "sector", "macro", "ai", "finance" など
            - Status Option ID: GitHub Project の Status フィールドの Option ID

        Notes
        -----
        - 未知のカテゴリの場合は "finance" がデフォルト Status 名として使用される
        - Status 名が github_status_ids に存在しない場合も "finance" の ID が使用される

        Examples
        --------
        >>> publisher._resolve_status(article)
        ("index", "3925acc3")
        """
        category = article.extracted.collected.source.category

        # status_mapping でカテゴリ → Status名 を解決
        # 例: "market" → "index", "tech" → "ai"
        status_name = self._status_mapping.get(category, "finance")

        # github_status_ids で Status名 → Option ID を解決
        # 例: "index" → "3925acc3"
        status_id = self._status_ids.get(status_name, self._status_ids["finance"])

        logger.debug(
            "Resolved status from category",
            category=category,
            status_name=status_name,
            status_id=status_id,
        )

        return status_name, status_id

    async def _create_issue(self, article: SummarizedArticle) -> tuple[int, str]:
        """Issue を作成。

        gh issue create コマンドを使用して GitHub Issue を作成する。

        Parameters
        ----------
        article : SummarizedArticle
            要約済み記事。summary が存在することを前提とする。

        Returns
        -------
        tuple[int, str]
            (Issue番号, Issue URL) のタプル。

        Raises
        ------
        subprocess.CalledProcessError
            gh コマンドの実行に失敗した場合。

        Examples
        --------
        >>> issue_number, issue_url = await publisher._create_issue(article)
        >>> issue_number
        123
        >>> issue_url
        'https://github.com/YH-05/finance/issues/123'
        """
        title = self._generate_issue_title(article)
        body = self._generate_issue_body(article)

        result = subprocess.run(  # nosec B603 - gh CLI with safe args
            [
                "gh",
                "issue",
                "create",
                "--repo",
                self._repo,
                "--title",
                title,
                "--body",
                body,
            ],
            capture_output=True,
            text=True,
            check=True,
        )

        # gh issue create は Issue URL を返す
        issue_url = result.stdout.strip()
        issue_number = int(issue_url.split("/")[-1])

        logger.debug(
            "Created issue via gh CLI",
            issue_number=issue_number,
            issue_url=issue_url,
        )

        return issue_number, issue_url

    async def _add_to_project(
        self, issue_number: int, article: SummarizedArticle
    ) -> None:
        """Issue を Project に追加し、フィールドを設定。

        gh project item-add で Issue を追加し、
        gh project item-edit で Status と PublishedDate フィールドを設定する。

        Parameters
        ----------
        issue_number : int
            追加する Issue 番号。
        article : SummarizedArticle
            要約済み記事。Status 解決と公開日取得に使用する。

        Raises
        ------
        subprocess.CalledProcessError
            gh コマンドの実行に失敗した場合。

        Notes
        -----
        - Status フィールドは常に設定される
        - PublishedDate フィールドは article.extracted.collected.published が
          存在する場合のみ設定される
        """
        # 1. Issue を Project に追加
        issue_url = f"https://github.com/{self._repo}/issues/{issue_number}"
        owner = self._repo.split("/")[0]

        add_result = subprocess.run(  # nosec B603 - gh CLI with safe args
            [
                "gh",
                "project",
                "item-add",
                str(self._project_number),
                "--owner",
                owner,
                "--url",
                issue_url,
            ],
            capture_output=True,
            text=True,
            check=True,
        )

        item_id = add_result.stdout.strip()

        logger.debug(
            "Added issue to project",
            issue_number=issue_number,
            project_number=self._project_number,
            item_id=item_id,
        )

        # 2. Status フィールドを設定
        _, status_id = self._resolve_status(article)

        subprocess.run(  # nosec B603 - gh CLI with safe args
            [
                "gh",
                "project",
                "item-edit",
                "--project-id",
                self._project_id,
                "--id",
                item_id,
                "--field-id",
                self._status_field_id,
                "--single-select-option-id",
                status_id,
            ],
            check=True,
        )

        logger.debug(
            "Set status field",
            item_id=item_id,
            status_id=status_id,
        )

        # 3. PublishedDate フィールドを設定（公開日がある場合のみ）
        published = article.extracted.collected.published
        if published:
            date_str = published.strftime("%Y-%m-%d")
            subprocess.run(  # nosec B603 - gh CLI with safe args
                [
                    "gh",
                    "project",
                    "item-edit",
                    "--project-id",
                    self._project_id,
                    "--id",
                    item_id,
                    "--field-id",
                    self._published_date_field_id,
                    "--date",
                    date_str,
                ],
                check=True,
            )

            logger.debug(
                "Set published date field",
                item_id=item_id,
                date=date_str,
            )


__all__ = [
    "Publisher",
]

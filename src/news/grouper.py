"""Article grouper for categorizing summarized articles.

This module provides the ArticleGrouper class that groups summarized articles
by category and date, producing CategoryGroup objects for category-based
Issue publishing.

The grouper uses status_mapping to normalize source categories (e.g., "tech" -> "ai",
"market" -> "index") and category_labels for human-readable Japanese labels.

Examples
--------
>>> from news.grouper import ArticleGrouper
>>> from news.config.models import CategoryLabelsConfig
>>> grouper = ArticleGrouper(
...     status_mapping={"tech": "ai", "market": "index"},
...     category_labels=CategoryLabelsConfig(),
... )
>>> groups = grouper.group(summarized_articles)
>>> groups[0].category
'ai'
"""

from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING

from utils_core.logging import get_logger

from .models import CategoryGroup

if TYPE_CHECKING:
    from .config.models import CategoryLabelsConfig
    from .models import SummarizedArticle

logger = get_logger(__name__, module="grouper")

# Default fallback category when source category is not in status_mapping
_DEFAULT_CATEGORY = "finance"


class ArticleGrouper:
    """記事をカテゴリと日付でグループ化する.

    source.category を status_mapping で正規化し、published から日付を抽出して
    (category, date) ペアでグループ化する。

    Parameters
    ----------
    status_mapping : dict[str, str]
        ソースカテゴリから正規化カテゴリへのマッピング。
        例: {"tech": "ai", "market": "index", "economy": "macro"}
    category_labels : CategoryLabelsConfig
        カテゴリキーから日本語ラベルへのマッピング設定。

    Examples
    --------
    >>> grouper = ArticleGrouper(
    ...     status_mapping={"tech": "ai"},
    ...     category_labels=CategoryLabelsConfig(),
    ... )
    >>> groups = grouper.group(articles)
    """

    def __init__(
        self,
        status_mapping: dict[str, str],
        category_labels: CategoryLabelsConfig,
    ) -> None:
        self._status_mapping = status_mapping
        self._category_labels = category_labels

        logger.debug(
            "ArticleGrouper initialized",
            status_mapping_count=len(status_mapping),
        )

    def group(self, articles: list[SummarizedArticle]) -> list[CategoryGroup]:
        """記事をカテゴリと日付でグループ化する.

        Parameters
        ----------
        articles : list[SummarizedArticle]
            グループ化対象の要約済み記事リスト。

        Returns
        -------
        list[CategoryGroup]
            (category, date) でグループ化された結果。
            category と date の昇順でソートされる。
            空の入力に対しては空リストを返す。

        Notes
        -----
        - source.category を status_mapping で正規化する
        - 未知のカテゴリは "finance" にフォールバックする
        - published が None の場合は collected_at から日付を抽出する
        - 結果は (category, date) の昇順でソートされる
        """
        if not articles:
            logger.debug("No articles to group")
            return []

        logger.info("Grouping articles", article_count=len(articles))

        # (category, date) -> list[SummarizedArticle]
        groups: defaultdict[tuple[str, str], list[SummarizedArticle]] = defaultdict(
            list
        )

        for article in articles:
            category = self._resolve_category(article)
            date = self._extract_date(article)
            groups[(category, date)].append(article)

        # CategoryGroup オブジェクトのリストを作成し、ソートして返す
        result = [
            CategoryGroup(
                category=category,
                category_label=self._category_labels.get_label(category),
                date=date,
                articles=group_articles,
            )
            for (category, date), group_articles in groups.items()
        ]

        # (category, date) の昇順でソート
        result.sort(key=lambda g: (g.category, g.date))

        logger.info(
            "Grouping completed",
            group_count=len(result),
            article_count=len(articles),
            categories=[g.category for g in result],
        )

        return result

    def _resolve_category(self, article: SummarizedArticle) -> str:
        """ソースカテゴリを正規化カテゴリに解決する.

        Parameters
        ----------
        article : SummarizedArticle
            対象記事。

        Returns
        -------
        str
            正規化されたカテゴリ（例: "index", "ai", "stock"）。
            status_mapping に存在しない場合は "finance" を返す。
        """
        source_category = article.extracted.collected.source.category
        resolved = self._status_mapping.get(source_category, _DEFAULT_CATEGORY)

        if source_category not in self._status_mapping:
            logger.debug(
                "Unknown category, falling back to default",
                source_category=source_category,
                resolved_category=resolved,
            )

        return resolved

    def _extract_date(self, article: SummarizedArticle) -> str:
        """記事から日付文字列を抽出する.

        Parameters
        ----------
        article : SummarizedArticle
            対象記事。

        Returns
        -------
        str
            YYYY-MM-DD 形式の日付文字列。
            published が None の場合は collected_at から抽出する。
        """
        collected = article.extracted.collected
        dt = collected.published or collected.collected_at
        return dt.strftime("%Y-%m-%d")


__all__ = [
    "ArticleGrouper",
]

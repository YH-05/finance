"""Markdown generator for category-based news Issue publishing.

This module provides classes for generating Markdown content from
CategoryGroup objects and exporting them to files.

- CategoryMarkdownGenerator: generates Issue titles and body content
- MarkdownExporter: exports CategoryGroup content to Markdown files

Examples
--------
>>> from news.markdown_generator import CategoryMarkdownGenerator, MarkdownExporter
>>> generator = CategoryMarkdownGenerator()
>>> title = generator.generate_issue_title(group)
>>> body = generator.generate_issue_body(group)

>>> exporter = MarkdownExporter()
>>> path = exporter.export(group, export_dir=Path("data/exports/news-workflow"))
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from utils_core.logging import get_logger

if TYPE_CHECKING:
    from pathlib import Path

    from .models import CategoryGroup, SummarizedArticle

logger = get_logger(__name__, module="markdown_generator")


class CategoryMarkdownGenerator:
    """カテゴリ別Issue本文のMarkdownを生成する.

    CategoryGroup からIssueタイトルと本文のMarkdownを生成する。
    各記事は番号付きセクションとして、概要・キーポイント・市場への影響を含む。

    Examples
    --------
    >>> generator = CategoryMarkdownGenerator()
    >>> title = generator.generate_issue_title(group)
    >>> title
    '[株価指数] ニュースまとめ - 2026-02-09'
    >>> body = generator.generate_issue_body(group)
    """

    def generate_issue_title(self, group: CategoryGroup) -> str:
        """Issueタイトルを生成する.

        Parameters
        ----------
        group : CategoryGroup
            カテゴリグループ。

        Returns
        -------
        str
            "[{category_label}] ニュースまとめ - {date}" 形式のタイトル。

        Examples
        --------
        >>> generator = CategoryMarkdownGenerator()
        >>> generator.generate_issue_title(group)
        '[株価指数] ニュースまとめ - 2026-02-09'
        """
        return f"[{group.category_label}] ニュースまとめ - {group.date}"

    def generate_issue_body(self, group: CategoryGroup) -> str:
        """Issue本文のMarkdownを生成する.

        Parameters
        ----------
        group : CategoryGroup
            カテゴリグループ。articles に含まれる記事が本文に展開される。

        Returns
        -------
        str
            Markdown形式のIssue本文。ヘッダー、記事一覧を含む。

        Notes
        -----
        テンプレート構造:
        - ヘッダー: カテゴリラベル、日付、記事件数
        - 記事一覧: 番号付きサブセクション（タイトル、ソース、URL、概要、キーポイント、市場への影響）
        - 記事間セパレータ: "---"
        """
        article_count = len(group.articles)

        logger.debug(
            "Generating issue body",
            category=group.category,
            date=group.date,
            article_count=article_count,
        )

        # ヘッダー
        header = (
            f"# [{group.category_label}] ニュースまとめ - {group.date}\n"
            f"\n"
            f"> {article_count}件の記事を収集\n"
            f"\n"
            f"## 記事一覧\n"
        )

        # 記事セクション
        article_sections: list[str] = []
        for idx, article in enumerate(group.articles, start=1):
            section = self._render_article_section(idx, article)
            article_sections.append(section)

        body = header + "\n---\n".join(article_sections)

        logger.debug(
            "Issue body generated",
            body_length=len(body),
            article_count=article_count,
        )

        return body

    def _render_article_section(self, index: int, article: SummarizedArticle) -> str:
        """個別記事のMarkdownセクションを生成する.

        Parameters
        ----------
        index : int
            記事の番号（1始まり）。
        article : SummarizedArticle
            要約済み記事。

        Returns
        -------
        str
            Markdown形式の記事セクション。
        """
        collected = article.extracted.collected
        summary = article.summary

        # 公開日のフォーマット
        published_str = (
            collected.published.strftime("%Y-%m-%d %H:%M")
            if collected.published
            else "不明"
        )

        # ヘッダー行
        section = (
            f"\n### {index}. {collected.title}\n"
            f"**ソース**: {collected.source.source_name} | "
            f"**公開日**: {published_str}\n"
            f"**URL**: {collected.url}\n"
        )

        # 要約セクション（summary が None の場合はスキップ）
        if summary is not None:
            # キーポイントのリスト化
            key_points_md = "\n".join(f"- {point}" for point in summary.key_points)

            section += (
                f"\n#### 概要\n"
                f"{summary.overview}\n"
                f"\n#### キーポイント\n"
                f"{key_points_md}\n"
                f"\n#### 市場への影響\n"
                f"{summary.market_impact}\n"
            )

        return section


class MarkdownExporter:
    """CategoryGroup のMarkdownをファイルに出力する.

    出力先パス: {export_dir}/{date}/{category}.md

    Examples
    --------
    >>> exporter = MarkdownExporter()
    >>> path = exporter.export(group, export_dir=Path("data/exports/news-workflow"))
    >>> path
    PosixPath('data/exports/news-workflow/2026-02-09/index.md')
    """

    def export(self, group: CategoryGroup, export_dir: Path) -> Path:
        """カテゴリグループのMarkdownをファイルに出力する.

        Parameters
        ----------
        group : CategoryGroup
            出力対象のカテゴリグループ。
        export_dir : Path
            出力先の基底ディレクトリ。

        Returns
        -------
        Path
            出力されたファイルのパス。
            形式: {export_dir}/{date}/{category}.md

        Notes
        -----
        - 出力先ディレクトリが存在しない場合は自動で作成する
        - 既存ファイルは上書きされる
        """
        # 出力先パスの構築
        date_dir = export_dir / group.date
        output_path = date_dir / f"{group.category}.md"

        # ディレクトリ作成
        date_dir.mkdir(parents=True, exist_ok=True)

        # Markdown 生成
        generator = CategoryMarkdownGenerator()
        content = generator.generate_issue_body(group)

        # ファイル出力
        output_path.write_text(content, encoding="utf-8")

        logger.info(
            "Markdown exported",
            path=str(output_path),
            category=group.category,
            date=group.date,
            article_count=len(group.articles),
        )

        return output_path


__all__ = [
    "CategoryMarkdownGenerator",
    "MarkdownExporter",
]

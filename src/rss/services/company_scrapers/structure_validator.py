"""Structure validator for detecting CSS selector health changes.

Validates that CompanyConfig CSS selectors still match a company's blog
page structure. When a company redesigns their blog, selectors may stop
matching, causing scraping failures. This module detects such changes
early by computing selector hit rates and emitting threshold-based alerts.

Threshold levels:
- hit_rate == 0   -> ERROR  (complete structure change)
- hit_rate <  0.5 -> WARNING (major change)
- hit_rate <  0.8 -> WARNING (partial change)
- hit_rate >= 0.8 -> INFO   (healthy)
"""

from typing import Any

from lxml.html import HtmlElement, fromstring

from .types import CompanyConfig, StructureReport


def _get_logger() -> Any:
    """Get logger with lazy initialization to avoid circular imports."""
    try:
        from utils_core.logging import get_logger

        return get_logger(__name__, module="structure_validator")
    except ImportError:
        import logging

        return logging.getLogger(__name__)


logger: Any = _get_logger()


class StructureValidator:
    """Validate CSS selector health against a company's blog HTML.

    Checks that the selectors defined in a ``CompanyConfig`` still match
    elements on the company's blog page, computing a hit rate that
    indicates how much of the expected structure is intact.

    The hit rate is calculated as:

        hit_rate = (title_found_count + date_found_count) / (2 * article_list_hits)

    where ``article_list_hits`` is the number of elements matching
    the article list selector, and ``title_found_count`` /
    ``date_found_count`` are the counts of articles where the title
    and date selectors respectively found a match.

    Examples
    --------
    >>> validator = StructureValidator()
    >>> report = validator.validate(html_content, company_config)
    >>> report.hit_rate
    0.95
    """

    def validate(self, html: str, config: CompanyConfig) -> StructureReport:
        """Validate selector health for a company's blog page.

        Parameters
        ----------
        html : str
            Raw HTML content of the company's blog/news page.
        config : CompanyConfig
            Company configuration containing CSS selectors to validate.

        Returns
        -------
        StructureReport
            Report containing hit counts and overall hit rate.
        """
        report = StructureReport(company=config.key)

        doc = self._parse_html(html)
        if doc is None:
            logger.error(
                "Failed to parse HTML",
                company=config.key,
                blog_url=config.blog_url,
            )
            self._emit_alert(report, config)
            return report

        # Step 1: Count article list selector hits
        article_elements = doc.cssselect(config.article_list_selector)
        report.article_list_hits = len(article_elements)

        if report.article_list_hits == 0:
            logger.debug(
                "No articles found with selector",
                company=config.key,
                selector=config.article_list_selector,
            )
            self._emit_alert(report, config)
            return report

        # Step 2: For each article element, check title and date selectors
        title_count = 0
        date_count = 0
        for article_el in article_elements:
            if article_el.cssselect(config.article_title_selector):
                title_count += 1
            if article_el.cssselect(config.article_date_selector):
                date_count += 1

        report.title_found_count = title_count
        report.date_found_count = date_count

        # Step 3: Calculate hit rate
        # Total possible matches = 2 selectors * number of articles
        total_possible = 2 * report.article_list_hits
        total_hits = title_count + date_count
        report.hit_rate = total_hits / total_possible

        # Step 4: Emit threshold-based alert
        self._emit_alert(report, config)

        return report

    @staticmethod
    def _parse_html(html: str) -> HtmlElement | None:
        """Parse raw HTML into an lxml HtmlElement.

        Parameters
        ----------
        html : str
            Raw HTML string.

        Returns
        -------
        HtmlElement | None
            Parsed document, or None if parsing fails.
        """
        try:
            return fromstring(html)
        except Exception:
            return None

    @staticmethod
    def _emit_alert(report: StructureReport, config: CompanyConfig) -> None:
        """Emit a log message based on the hit rate threshold.

        Parameters
        ----------
        report : StructureReport
            The validated structure report.
        config : CompanyConfig
            Company configuration for context in log messages.
        """
        hit_rate = report.hit_rate
        company = report.company

        log_context = {
            "company": company,
            "hit_rate": hit_rate,
            "article_list_hits": report.article_list_hits,
            "title_found_count": report.title_found_count,
            "date_found_count": report.date_found_count,
            "blog_url": config.blog_url,
        }

        if hit_rate == 0.0:
            logger.error(
                f"Structure validation failed for {company}: "
                "complete structure change detected (hit_rate=0)",
                **log_context,
            )
        elif hit_rate < 0.5:
            logger.warning(
                f"Structure validation warning for {company}: "
                f"major change detected (hit_rate={hit_rate:.2f})",
                **log_context,
            )
        elif hit_rate < 0.8:
            logger.warning(
                f"Structure validation warning for {company}: "
                f"partial change detected (hit_rate={hit_rate:.2f})",
                **log_context,
            )
        else:
            logger.info(
                f"Structure validation passed for {company}: "
                f"selectors healthy (hit_rate={hit_rate:.2f})",
                **log_context,
            )

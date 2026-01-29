"""Trafilatura-based article body extractor.

This module provides a TrafilaturaExtractor class that wraps the existing
rss.services.article_extractor.ArticleExtractor to extract article body
text from URLs. It conforms to the BaseExtractor interface for use in
the news collection pipeline.

Examples
--------
>>> from news.extractors.trafilatura import TrafilaturaExtractor
>>> from news.models import CollectedArticle
>>> extractor = TrafilaturaExtractor()
>>> result = await extractor.extract(article)
>>> result.extraction_status
<ExtractionStatus.SUCCESS: 'success'>
"""

from news.extractors.base import BaseExtractor
from news.models import CollectedArticle, ExtractedArticle, ExtractionStatus
from rss.services.article_extractor import ArticleExtractor
from rss.services.article_extractor import (
    ExtractionStatus as RssExtractionStatus,
)


class TrafilaturaExtractor(BaseExtractor):
    """Trafilatura-based article body extractor.

    This class wraps the existing ArticleExtractor from rss.services to
    extract article body text from URLs. It conforms to the BaseExtractor
    interface and handles the mapping between the RSS extraction types
    and the news pipeline types.

    Parameters
    ----------
    min_body_length : int, optional
        Minimum body text length in characters to consider extraction
        successful. Texts shorter than this threshold will result in
        FAILED status. Default is 200.

    Attributes
    ----------
    extractor_name : str
        Returns "trafilatura" to identify this extractor.

    Examples
    --------
    >>> from news.extractors.trafilatura import TrafilaturaExtractor
    >>> from news.models import CollectedArticle, ArticleSource, SourceType
    >>> from datetime import datetime, timezone
    >>>
    >>> extractor = TrafilaturaExtractor(min_body_length=100)
    >>> source = ArticleSource(
    ...     source_type=SourceType.RSS,
    ...     source_name="CNBC",
    ...     category="market",
    ... )
    >>> article = CollectedArticle(
    ...     url="https://example.com/article",
    ...     title="Test Article",
    ...     source=source,
    ...     collected_at=datetime.now(tz=timezone.utc),
    ... )
    >>> result = await extractor.extract(article)
    >>> result.extraction_status
    <ExtractionStatus.SUCCESS: 'success'>
    """

    def __init__(self, min_body_length: int = 200) -> None:
        """Initialize the TrafilaturaExtractor.

        Parameters
        ----------
        min_body_length : int, optional
            Minimum body text length in characters. Default is 200.
        """
        self._extractor = ArticleExtractor()
        self._min_body_length = min_body_length

    @property
    def extractor_name(self) -> str:
        """Return the name of this extractor.

        Returns
        -------
        str
            The string "trafilatura".

        Examples
        --------
        >>> extractor = TrafilaturaExtractor()
        >>> extractor.extractor_name
        'trafilatura'
        """
        return "trafilatura"

    async def extract(self, article: CollectedArticle) -> ExtractedArticle:
        """Extract body text from a single article.

        Uses the underlying ArticleExtractor to fetch the article content
        and maps the result to the news pipeline's ExtractedArticle format.

        Parameters
        ----------
        article : CollectedArticle
            The collected article to extract body text from.

        Returns
        -------
        ExtractedArticle
            The extraction result containing:
            - The original collected article
            - Extracted body text (or None if failed)
            - Extraction status (SUCCESS, FAILED, PAYWALL, TIMEOUT)
            - Extraction method identifier
            - Error message (if failed)

        Notes
        -----
        - Texts shorter than min_body_length are considered failed
        - The RssExtractionStatus is mapped to ExtractionStatus
        - Exceptions are caught and result in FAILED status

        Examples
        --------
        >>> result = await extractor.extract(article)
        >>> if result.extraction_status == ExtractionStatus.SUCCESS:
        ...     print(f"Extracted {len(result.body_text)} characters")
        >>> else:
        ...     print(f"Extraction failed: {result.error_message}")
        """
        try:
            result = await self._extractor.extract(str(article.url))

            # Map the RSS extraction status to news pipeline status
            status = self._map_status(result.status)

            # Check if extraction succeeded but body is too short/empty
            if result.status == RssExtractionStatus.SUCCESS:
                if result.text is None or len(result.text) < self._min_body_length:
                    return ExtractedArticle(
                        collected=article,
                        body_text=None,
                        extraction_status=ExtractionStatus.FAILED,
                        extraction_method=self.extractor_name,
                        error_message="Body text too short or empty",
                    )

                # Success case
                return ExtractedArticle(
                    collected=article,
                    body_text=result.text,
                    extraction_status=ExtractionStatus.SUCCESS,
                    extraction_method=self.extractor_name,
                    error_message=None,
                )

            # Non-success status from extractor
            return ExtractedArticle(
                collected=article,
                body_text=None,
                extraction_status=status,
                extraction_method=self.extractor_name,
                error_message=result.error,
            )

        except Exception as e:
            # Handle unexpected exceptions
            return ExtractedArticle(
                collected=article,
                body_text=None,
                extraction_status=ExtractionStatus.FAILED,
                extraction_method=self.extractor_name,
                error_message=str(e),
            )

    def _map_status(self, rss_status: RssExtractionStatus) -> ExtractionStatus:
        """Map RSS extraction status to news pipeline status.

        Parameters
        ----------
        rss_status : RssExtractionStatus
            The status from the RSS article extractor.

        Returns
        -------
        ExtractionStatus
            The corresponding news pipeline extraction status.

        Notes
        -----
        The mapping is:
        - SUCCESS -> SUCCESS
        - FAILED -> FAILED
        - PAYWALL -> PAYWALL
        - TIMEOUT -> TIMEOUT
        """
        status_map = {
            RssExtractionStatus.SUCCESS: ExtractionStatus.SUCCESS,
            RssExtractionStatus.FAILED: ExtractionStatus.FAILED,
            RssExtractionStatus.PAYWALL: ExtractionStatus.PAYWALL,
            RssExtractionStatus.TIMEOUT: ExtractionStatus.TIMEOUT,
        }
        return status_map.get(rss_status, ExtractionStatus.FAILED)


__all__ = ["TrafilaturaExtractor"]

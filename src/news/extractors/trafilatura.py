"""Trafilatura-based article body extractor.

This module provides a TrafilaturaExtractor class that wraps the existing
rss.services.article_extractor.ArticleExtractor to extract article body
text from URLs. It conforms to the BaseExtractor interface for use in
the news collection pipeline.

Features
--------
- Automatic retry on failure with exponential backoff (1s, 2s, 4s)
- Configurable maximum retries and timeout
- User-Agent rotation for avoiding rate limiting
- Graceful error handling with status classification
- Playwright fallback for JS-rendered pages (Issue #2608)

Examples
--------
>>> from news.extractors.trafilatura import TrafilaturaExtractor
>>> from news.models import CollectedArticle
>>> extractor = TrafilaturaExtractor()
>>> result = await extractor.extract(article)
>>> result.extraction_status
<ExtractionStatus.SUCCESS: 'success'>

>>> # With Playwright fallback (requires async context manager)
>>> from news.config.workflow import ExtractionConfig
>>> config = ExtractionConfig()
>>> async with TrafilaturaExtractor.from_config(config) as extractor:
...     result = await extractor.extract(article)
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any, Self

from news.extractors.base import BaseExtractor
from news.models import CollectedArticle, ExtractedArticle, ExtractionStatus
from rss.services.article_extractor import ArticleExtractor
from rss.services.article_extractor import (
    ExtractionStatus as RssExtractionStatus,
)
from utils_core.logging import get_logger

if TYPE_CHECKING:
    from news.config.workflow import (
        ExtractionConfig,
        PlaywrightFallbackConfig,
        UserAgentRotationConfig,
    )
    from news.extractors.playwright import PlaywrightExtractor

logger = get_logger(__name__)


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
    max_retries : int, optional
        Maximum number of retry attempts for failed extractions.
        Default is 3.
    timeout_seconds : int, optional
        Timeout in seconds for each extraction attempt.
        Default is 30.
    user_agent_config : UserAgentRotationConfig | None, optional
        User-Agent rotation configuration. If provided, enables random
        User-Agent selection for each request. Default is None.
    playwright_config : PlaywrightFallbackConfig | None, optional
        Playwright fallback configuration. If provided and enabled,
        falls back to Playwright when trafilatura fails. Default is None.
    extraction_config : ExtractionConfig | None, optional
        Full extraction configuration. Used internally by from_config().
        Default is None.

    Attributes
    ----------
    extractor_name : str
        Returns "trafilatura" to identify this extractor.

    Notes
    -----
    Retry behavior:
    - On failure or timeout, the extractor will retry up to max_retries times
    - Uses exponential backoff between retries (1s, 2s, 4s, ...)
    - If all retries fail, returns appropriate error status

    User-Agent rotation:
    - When user_agent_config is provided and enabled, a random User-Agent
      is selected for each request from the configured list
    - The selected User-Agent is logged at DEBUG level
    - When disabled or list is empty, the default User-Agent is used

    Playwright fallback (Issue #2608):
    - When playwright_config is provided and enabled, and trafilatura
      fails or returns body text shorter than min_body_length, the
      extractor will fall back to Playwright for JS-rendered pages
    - Requires using async context manager to manage browser lifecycle
    - On fallback success, extraction_method is "trafilatura+playwright"

    Examples
    --------
    >>> from news.extractors.trafilatura import TrafilaturaExtractor
    >>> from news.models import CollectedArticle, ArticleSource, SourceType
    >>> from datetime import datetime, timezone
    >>>
    >>> extractor = TrafilaturaExtractor(min_body_length=100, max_retries=3)
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

    >>> # With Playwright fallback
    >>> from news.config.workflow import ExtractionConfig
    >>> config = ExtractionConfig()
    >>> async with TrafilaturaExtractor.from_config(config) as extractor:
    ...     result = await extractor.extract(article)
    """

    def __init__(
        self,
        min_body_length: int = 200,
        max_retries: int = 3,
        timeout_seconds: int = 30,
        user_agent_config: UserAgentRotationConfig | None = None,
        playwright_config: PlaywrightFallbackConfig | None = None,
        extraction_config: ExtractionConfig | None = None,
    ) -> None:
        """Initialize the TrafilaturaExtractor.

        Parameters
        ----------
        min_body_length : int, optional
            Minimum body text length in characters. Default is 200.
        max_retries : int, optional
            Maximum number of retry attempts. Default is 3.
        timeout_seconds : int, optional
            Timeout in seconds for each attempt. Default is 30.
        user_agent_config : UserAgentRotationConfig | None, optional
            User-Agent rotation configuration. Default is None.
        playwright_config : PlaywrightFallbackConfig | None, optional
            Playwright fallback configuration. Default is None.
        extraction_config : ExtractionConfig | None, optional
            Full extraction configuration for Playwright. Default is None.
        """
        self._extractor = ArticleExtractor()
        self._min_body_length = min_body_length
        self._max_retries = max_retries
        self._timeout_seconds = timeout_seconds
        self._user_agent_config = user_agent_config
        self._playwright_config = playwright_config
        self._extraction_config = extraction_config
        self._playwright_extractor: PlaywrightExtractor | None = None

    @classmethod
    def from_config(cls, config: ExtractionConfig) -> Self:
        """Create a TrafilaturaExtractor from ExtractionConfig.

        Parameters
        ----------
        config : ExtractionConfig
            The extraction configuration containing all settings.

        Returns
        -------
        TrafilaturaExtractor
            A new extractor instance configured from the config.

        Examples
        --------
        >>> from news.config.workflow import ExtractionConfig
        >>> config = ExtractionConfig()
        >>> extractor = TrafilaturaExtractor.from_config(config)
        """
        return cls(
            min_body_length=config.min_body_length,
            max_retries=config.max_retries,
            timeout_seconds=config.timeout_seconds,
            user_agent_config=config.user_agent_rotation,
            playwright_config=config.playwright_fallback,
            extraction_config=config,
        )

    async def __aenter__(self) -> Self:
        """Enter async context manager.

        Initializes the Playwright extractor if fallback is enabled.

        Returns
        -------
        TrafilaturaExtractor
            Self for use in async with statement.
        """
        if (
            self._playwright_config
            and self._playwright_config.enabled
            and self._extraction_config
        ):
            from news.extractors.playwright import PlaywrightExtractor

            self._playwright_extractor = PlaywrightExtractor(self._extraction_config)
            await self._playwright_extractor.__aenter__()
            logger.debug(
                "Playwright fallback initialized",
                browser=self._playwright_config.browser,
            )
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        """Exit async context manager.

        Closes the Playwright extractor if it was initialized.

        Parameters
        ----------
        exc_type : type[BaseException] | None
            Exception type if an exception was raised.
        exc_val : BaseException | None
            Exception value if an exception was raised.
        exc_tb : Any
            Exception traceback if an exception was raised.
        """
        if self._playwright_extractor:
            await self._playwright_extractor.__aexit__(exc_type, exc_val, exc_tb)
            self._playwright_extractor = None
            logger.debug("Playwright fallback closed")

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
        """Extract body text from a single article with retry logic.

        Uses the underlying ArticleExtractor to fetch the article content
        and maps the result to the news pipeline's ExtractedArticle format.
        Automatically retries on failure with exponential backoff.

        If Playwright fallback is enabled and trafilatura fails or returns
        body text shorter than min_body_length, the extractor will attempt
        to extract using Playwright.

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
            - Extraction method identifier ("trafilatura" or "trafilatura+playwright")
            - Error message (if failed)

        Notes
        -----
        - Retries up to max_retries times on failure
        - Uses exponential backoff (1s, 2s, 4s, ...)
        - Texts shorter than min_body_length are considered failed
        - The RssExtractionStatus is mapped to ExtractionStatus
        - If fallback is enabled and trafilatura fails, Playwright is tried
        - Fallback success results in extraction_method="trafilatura+playwright"

        Examples
        --------
        >>> result = await extractor.extract(article)
        >>> if result.extraction_status == ExtractionStatus.SUCCESS:
        ...     print(f"Extracted {len(result.body_text)} characters")
        >>> else:
        ...     print(f"Extraction failed: {result.error_message}")
        """
        # First, try trafilatura extraction
        result = await self._extract_with_trafilatura(article)

        # Check if we should fallback to Playwright
        if self._should_fallback(result):
            logger.debug(
                "Falling back to Playwright",
                url=str(article.url),
                original_status=result.extraction_status,
                original_error=result.error_message,
            )

            playwright_result = await self._extract_with_playwright(article)

            if playwright_result.extraction_status == ExtractionStatus.SUCCESS:
                logger.info(
                    "Playwright fallback succeeded",
                    url=str(article.url),
                )
                return playwright_result

            # Fallback also failed, return original trafilatura result
            logger.debug(
                "Playwright fallback also failed",
                url=str(article.url),
                playwright_error=playwright_result.error_message,
            )

        return result

    async def _extract_with_trafilatura(
        self,
        article: CollectedArticle,
    ) -> ExtractedArticle:
        """Extract using trafilatura with retry logic.

        Parameters
        ----------
        article : CollectedArticle
            The collected article to extract body text from.

        Returns
        -------
        ExtractedArticle
            The extraction result from trafilatura.
        """
        last_error: Exception | None = None
        last_was_timeout = False

        for attempt in range(self._max_retries):
            try:
                result = await self._extract_impl(article)
                # If extraction succeeded, return immediately
                if result.extraction_status == ExtractionStatus.SUCCESS:
                    return result
                # If it's a non-retryable failure (e.g., PAYWALL), return
                if result.extraction_status == ExtractionStatus.PAYWALL:
                    return result
                # Otherwise, treat as failure and retry
                last_error = Exception(result.error_message or "Extraction failed")
                last_was_timeout = result.extraction_status == ExtractionStatus.TIMEOUT

            except asyncio.TimeoutError as e:
                last_error = e
                last_was_timeout = True
                logger.warning(
                    "Extraction timeout",
                    url=str(article.url),
                    attempt=attempt + 1,
                    max_retries=self._max_retries,
                )
            except Exception as e:
                last_error = e
                last_was_timeout = False
                logger.warning(
                    "Extraction failed",
                    url=str(article.url),
                    attempt=attempt + 1,
                    max_retries=self._max_retries,
                    error=str(e),
                )

            # Apply exponential backoff (1s, 2s, 4s, ...) if not the last attempt
            if attempt < self._max_retries - 1:
                backoff_seconds = 2**attempt
                await asyncio.sleep(backoff_seconds)

        # All retries exhausted
        error_message = str(last_error) if last_error else "All retries failed"
        status = (
            ExtractionStatus.TIMEOUT if last_was_timeout else ExtractionStatus.FAILED
        )

        return ExtractedArticle(
            collected=article,
            body_text=None,
            extraction_status=status,
            extraction_method=self.extractor_name,
            error_message=error_message,
        )

    def _should_fallback(self, result: ExtractedArticle) -> bool:
        """Determine whether to fallback to Playwright.

        Fallback is triggered when:
        - Playwright fallback is enabled
        - Playwright extractor is initialized
        - Extraction failed (FAILED status)
        - Or body text is too short (SUCCESS but short body)

        PAYWALL status does not trigger fallback as Playwright
        likely cannot bypass paywalls either.

        Parameters
        ----------
        result : ExtractedArticle
            The result from trafilatura extraction.

        Returns
        -------
        bool
            True if fallback should be attempted, False otherwise.
        """
        # Check if fallback is enabled and extractor is available
        if not self._playwright_config or not self._playwright_config.enabled:
            return False

        if self._playwright_extractor is None:
            return False

        # Fallback on FAILED status
        if result.extraction_status == ExtractionStatus.FAILED:
            return True

        # Fallback on SUCCESS but body too short
        return (
            result.extraction_status == ExtractionStatus.SUCCESS
            and result.body_text is not None
            and len(result.body_text) < self._min_body_length
        )

    async def _extract_with_playwright(
        self,
        article: CollectedArticle,
    ) -> ExtractedArticle:
        """Extract using Playwright fallback.

        Parameters
        ----------
        article : CollectedArticle
            The collected article to extract body text from.

        Returns
        -------
        ExtractedArticle
            The extraction result with extraction_method="trafilatura+playwright"
            if successful.
        """
        if self._playwright_extractor is None:
            return ExtractedArticle(
                collected=article,
                body_text=None,
                extraction_status=ExtractionStatus.FAILED,
                extraction_method="playwright",
                error_message="Playwright extractor not initialized",
            )

        result = await self._playwright_extractor.extract(article)

        # Update extraction_method to indicate fallback was used
        if result.extraction_status == ExtractionStatus.SUCCESS:
            return ExtractedArticle(
                collected=result.collected,
                body_text=result.body_text,
                extraction_status=result.extraction_status,
                extraction_method="trafilatura+playwright",
                error_message=result.error_message,
            )

        return result

    async def _extract_impl(self, article: CollectedArticle) -> ExtractedArticle:
        """Perform the actual extraction without retry logic.

        Parameters
        ----------
        article : CollectedArticle
            The collected article to extract body text from.

        Returns
        -------
        ExtractedArticle
            The extraction result.
        """
        try:
            # Get random User-Agent if rotation is enabled
            user_agent: str | None = None
            if self._user_agent_config:
                user_agent = self._user_agent_config.get_random_user_agent()
                if user_agent:
                    logger.debug(
                        "Using custom User-Agent",
                        url=str(article.url),
                        user_agent=user_agent[:50] + "..."
                        if len(user_agent) > 50
                        else user_agent,
                    )

            result = await self._extractor.extract(str(article.url), user_agent)

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
            # Re-raise to trigger retry in the caller
            raise

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

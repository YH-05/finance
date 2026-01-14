"""URL and string length validation for RSS feeds."""

from typing import Any
from urllib.parse import urlparse

from ..exceptions import InvalidURLError


def _get_logger() -> Any:
    """Get logger with lazy initialization to avoid circular imports."""
    try:
        from ..utils.logging_config import get_logger

        return get_logger(__name__, module="url_validator")
    except ImportError:
        import logging

        return logging.getLogger(__name__)


logger: Any = _get_logger()


class URLValidator:
    """Validator for URLs and string length constraints.

    This class provides validation methods for URLs (HTTP/HTTPS only),
    titles (1-200 characters), and categories (1-50 characters).

    Examples
    --------
    >>> validator = URLValidator()
    >>> validator.validate_url("https://example.com/feed")
    >>> validator.validate_title("My Feed Title")
    >>> validator.validate_category("technology")
    """

    def validate_url(self, url: str) -> None:
        """Validate that a URL uses HTTP or HTTPS scheme.

        Parameters
        ----------
        url : str
            The URL to validate

        Raises
        ------
        InvalidURLError
            If the URL doesn't use HTTP or HTTPS scheme, is empty, or is malformed

        Examples
        --------
        >>> validator = URLValidator()
        >>> validator.validate_url("https://example.com")
        >>> validator.validate_url("ftp://example.com")
        Traceback (most recent call last):
            ...
        InvalidURLError: Invalid URL 'ftp://example.com': Only HTTP/HTTPS schemes are allowed
        """
        logger.debug("Validating URL", url=url)

        if not url or not url.strip():
            logger.error("URL validation failed", url=url, reason="empty or blank URL")
            raise InvalidURLError(
                f"Invalid URL: URL cannot be empty or blank, got '{url}'"
            )

        try:
            parsed = urlparse(url)
            scheme = parsed.scheme.lower()

            logger.debug(
                "Parsed URL",
                url=url,
                scheme=scheme,
                netloc=parsed.netloc,
                path=parsed.path,
            )

            if scheme not in ("http", "https"):
                logger.error(
                    "URL validation failed",
                    url=url,
                    scheme=scheme,
                    reason="invalid scheme",
                    allowed_schemes=["http", "https"],
                )
                raise InvalidURLError(
                    f"Invalid URL '{url}': Only HTTP/HTTPS schemes are allowed, got '{scheme}'"
                )

            # Check if netloc (domain) exists
            if not parsed.netloc:
                logger.error(
                    "URL validation failed",
                    url=url,
                    reason="missing domain",
                )
                raise InvalidURLError(
                    f"Invalid URL '{url}': URL must have a valid domain"
                )

            logger.debug("URL validation passed", url=url, scheme=scheme)

        except InvalidURLError:
            raise
        except Exception as e:
            logger.error(
                "URL parsing failed",
                url=url,
                error=str(e),
                exc_info=True,
            )
            raise InvalidURLError(
                f"Invalid URL '{url}': Failed to parse URL - {e}"
            ) from e

    def validate_title(self, title: str) -> None:
        """Validate that a title is between 1 and 200 characters.

        Whitespace-only titles are considered invalid.

        Parameters
        ----------
        title : str
            The title to validate

        Raises
        ------
        ValueError
            If the title is empty, whitespace-only, or exceeds 200 characters

        Examples
        --------
        >>> validator = URLValidator()
        >>> validator.validate_title("Valid Title")
        >>> validator.validate_title("")
        Traceback (most recent call last):
            ...
        ValueError: Invalid title: Title must be between 1 and 200 characters, got 0 characters
        """
        logger.debug("Validating title", title_length=len(title))

        stripped_title = title.strip()

        if not stripped_title:
            logger.error(
                "Title validation failed",
                title=title,
                stripped_length=len(stripped_title),
                reason="empty or whitespace-only",
            )
            raise ValueError(
                f"Invalid title: Title must be between 1 and 200 characters, got {len(title)} characters (whitespace-only)"
            )

        title_length = len(title)

        if title_length < 1 or title_length > 200:
            logger.error(
                "Title validation failed",
                title_length=title_length,
                reason="length out of range",
                min_length=1,
                max_length=200,
            )
            raise ValueError(
                f"Invalid title: Title must be between 1 and 200 characters, got {title_length} characters"
            )

        logger.debug(
            "Title validation passed",
            title_length=title_length,
            title_preview=title[:50] if len(title) > 50 else title,
        )

    def validate_category(self, category: str) -> None:
        """Validate that a category is between 1 and 50 characters.

        Whitespace-only categories are considered invalid.

        Parameters
        ----------
        category : str
            The category to validate

        Raises
        ------
        ValueError
            If the category is empty, whitespace-only, or exceeds 50 characters

        Examples
        --------
        >>> validator = URLValidator()
        >>> validator.validate_category("technology")
        >>> validator.validate_category("")
        Traceback (most recent call last):
            ...
        ValueError: Invalid category: Category must be between 1 and 50 characters, got 0 characters
        """
        logger.debug("Validating category", category_length=len(category))

        stripped_category = category.strip()

        if not stripped_category:
            logger.error(
                "Category validation failed",
                category=category,
                stripped_length=len(stripped_category),
                reason="empty or whitespace-only",
            )
            raise ValueError(
                f"Invalid category: Category must be between 1 and 50 characters, got {len(category)} characters (whitespace-only)"
            )

        category_length = len(category)

        if category_length < 1 or category_length > 50:
            logger.error(
                "Category validation failed",
                category_length=category_length,
                reason="length out of range",
                min_length=1,
                max_length=50,
            )
            raise ValueError(
                f"Invalid category: Category must be between 1 and 50 characters, got {category_length} characters"
            )

        logger.debug("Category validation passed", category_length=category_length)

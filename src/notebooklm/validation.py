"""Input validation utilities for security hardening.

Provides validation functions to protect against common web security
vulnerabilities including XSS, SSRF, path traversal, and injection attacks.

Functions
---------
validate_text_input
    Validate text input for XSS and injection attacks.
validate_url_input
    Validate URL input for SSRF attacks.
validate_file_path
    Validate file path for path traversal attacks.

Examples
--------
>>> from notebooklm.validation import validate_text_input
>>> text = validate_text_input("Hello, world!")
>>> print(text)
'Hello, world!'

See Also
--------
OWASP Top 10 : https://owasp.org/www-project-top-ten/
"""

from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import urlparse

from utils_core.logging import get_logger

logger = get_logger(__name__)

# Security constants
MAX_TEXT_LENGTH = 1_000_000  # 1MB of text
MAX_URL_LENGTH = 2048
PRIVATE_IP_RANGES = [
    r"^127\.",  # Loopback
    r"^10\.",  # Private class A
    r"^172\.(1[6-9]|2[0-9]|3[01])\.",  # Private class B
    r"^192\.168\.",  # Private class C
    r"^169\.254\.",  # Link-local
    r"^::1$",  # IPv6 loopback
    r"^fe80:",  # IPv6 link-local
    r"^fc00:",  # IPv6 unique local
]


def validate_text_input(
    text: str,
    *,
    max_length: int = MAX_TEXT_LENGTH,
    allow_empty: bool = False,
) -> str:
    """Validate text input for XSS and injection attacks.

    Parameters
    ----------
    text : str
        Text to validate.
    max_length : int
        Maximum allowed length (default: 1MB).
    allow_empty : bool
        Whether to allow empty strings.

    Returns
    -------
    str
        Validated text.

    Raises
    ------
    ValueError
        If validation fails.
    """
    if not isinstance(text, str):
        raise ValueError(f"Expected str, got {type(text).__name__}")

    if not allow_empty and not text.strip():
        raise ValueError("Text must not be empty")

    if len(text) > max_length:
        raise ValueError(
            f"Text exceeds maximum length of {max_length} characters (got {len(text)})"
        )

    # Check for script tags (basic XSS prevention)
    script_pattern = re.compile(r"<script[^>]*>.*?</script>", re.IGNORECASE | re.DOTALL)
    if script_pattern.search(text):
        logger.warning("Detected script tag in text input", text_preview=text[:100])
        raise ValueError("Text contains disallowed <script> tags")

    # Check for NUL bytes (common in injection attacks)
    if "\x00" in text:
        raise ValueError("Text contains NUL bytes")

    return text


def validate_url_input(
    url: str,
    *,
    allowed_schemes: list[str] | None = None,
) -> str:
    """Validate URL input for SSRF attacks.

    Parameters
    ----------
    url : str
        URL to validate.
    allowed_schemes : list[str] | None
        Allowed URL schemes (default: ["http", "https"]).

    Returns
    -------
    str
        Validated URL.

    Raises
    ------
    ValueError
        If validation fails.
    """
    if not isinstance(url, str):
        raise ValueError(f"Expected str, got {type(url).__name__}")

    if not url.strip():
        raise ValueError("URL must not be empty")

    if len(url) > MAX_URL_LENGTH:
        raise ValueError(
            f"URL exceeds maximum length of {MAX_URL_LENGTH} characters "
            f"(got {len(url)})"
        )

    # Parse URL
    try:
        parsed = urlparse(url)
    except Exception as e:
        raise ValueError(f"Invalid URL format: {e}") from e

    # Validate scheme
    if allowed_schemes is None:
        allowed_schemes = ["http", "https"]

    if parsed.scheme not in allowed_schemes:
        raise ValueError(
            f"URL scheme '{parsed.scheme}' not allowed. Allowed: {allowed_schemes}"
        )

    # Detect private IP addresses (SSRF prevention)
    hostname = parsed.hostname or ""

    for pattern in PRIVATE_IP_RANGES:
        if re.match(pattern, hostname):
            logger.warning(
                "Detected private IP in URL",
                url=url,
                hostname=hostname,
            )
            raise ValueError(f"URL points to private IP address: {hostname}")

    # Block localhost variations
    localhost_patterns = ["localhost", "0.0.0.0"]  # nosec B104
    if hostname.lower() in localhost_patterns:
        raise ValueError(f"URL points to localhost: {hostname}")

    return url


def validate_file_path(
    file_path: str,
    *,
    allowed_directories: list[str] | None = None,
    must_exist: bool = True,
) -> Path:
    """Validate file path for path traversal attacks.

    Parameters
    ----------
    file_path : str
        File path to validate.
    allowed_directories : list[str] | None
        List of allowed parent directories (if None, any path is allowed).
    must_exist : bool
        Whether the file must exist.

    Returns
    -------
    Path
        Validated, resolved Path object.

    Raises
    ------
    ValueError
        If validation fails.
    """
    if not isinstance(file_path, str):
        raise ValueError(f"Expected str, got {type(file_path).__name__}")

    if not file_path.strip():
        raise ValueError("File path must not be empty")

    # Convert to Path and resolve (follows symlinks)
    try:
        path = Path(file_path).resolve()
    except Exception as e:
        raise ValueError(f"Invalid file path: {e}") from e

    # Check if path exists
    if must_exist and not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    # Validate against allowed directories
    if allowed_directories is not None:
        allowed_paths = [Path(d).resolve() for d in allowed_directories]

        # Check if path is under any allowed directory
        is_allowed = any(
            path == allowed or allowed in path.parents for allowed in allowed_paths
        )

        if not is_allowed:
            logger.warning(
                "File path outside allowed directories",
                file_path=str(path),
                allowed=allowed_directories,
            )
            raise ValueError(f"File path not in allowed directories: {file_path}")

    return path


__all__ = [
    "validate_file_path",
    "validate_text_input",
    "validate_url_input",
]

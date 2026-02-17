"""Constants for the NotebookLM MCP server package.

This module defines all constants used by the NotebookLM Playwright automation,
including URL patterns, timeout values, polling intervals, session file paths,
and stealth browser configuration.

Constants are organized into the following categories:

1. URL patterns (base URL, notebook URL template)
2. Timeout values (navigation, element wait, generation operations)
3. Polling intervals (generation status checks)
4. Session management (file paths, cookie settings)
5. Stealth browser settings (viewport, user agent, init scripts)
6. Retry settings (max attempts, backoff)

Notes
-----
All constants use ``typing.Final`` type annotations to prevent reassignment.
The ``__all__`` list exports all public constants for use by other modules.

See Also
--------
market.etfcom.constants : Similar constant pattern used by the ETF.com module.
"""

from typing import Final

# ---------------------------------------------------------------------------
# 1. URL constants
# ---------------------------------------------------------------------------

NOTEBOOKLM_BASE_URL: Final[str] = "https://notebooklm.google.com"
"""Base URL for Google NotebookLM."""

NOTEBOOK_URL_TEMPLATE: Final[str] = (
    "https://notebooklm.google.com/notebook/{notebook_id}"
)
"""URL template for a specific notebook page.

Format with a notebook ID to get the notebook URL.

Examples
--------
>>> NOTEBOOK_URL_TEMPLATE.format(notebook_id="c9354f3f-f55b-4f90-a5c4-219e582945cf")
'https://notebooklm.google.com/notebook/c9354f3f-f55b-4f90-a5c4-219e582945cf'
"""

GOOGLE_LOGIN_URL: Final[str] = "https://accounts.google.com"
"""Base URL for Google login page.

Used to detect authentication redirects during session validation.
"""

# ---------------------------------------------------------------------------
# 2. Timeout constants (milliseconds)
# ---------------------------------------------------------------------------

DEFAULT_NAVIGATION_TIMEOUT_MS: Final[int] = 30_000
"""Default timeout for page navigation in milliseconds.

Maximum time to wait for a page to load after navigation.
Applies to ``page.goto()`` and ``page.wait_for_url()`` calls.
"""

DEFAULT_ELEMENT_TIMEOUT_MS: Final[int] = 10_000
"""Default timeout for element visibility/availability in milliseconds.

Maximum time to wait for a UI element to appear or become interactive.
Applies to ``page.wait_for_selector()`` and ``locator.wait_for()`` calls.
"""

CHAT_RESPONSE_TIMEOUT_MS: Final[int] = 60_000
"""Timeout for AI chat response in milliseconds.

Maximum time to wait for the AI to generate a response to a chat query.
Most responses complete within 10-30 seconds; 60 seconds provides margin.
"""

AUDIO_OVERVIEW_TIMEOUT_MS: Final[int] = 600_000
"""Timeout for Audio Overview generation in milliseconds (10 minutes).

Audio Overview (podcast) generation can take several minutes.
A 10-minute timeout provides sufficient margin for long content.
"""

STUDIO_GENERATION_TIMEOUT_MS: Final[int] = 600_000
"""Timeout for Studio content generation in milliseconds (10 minutes).

Studio features have varying generation times:
- Report: ~15 seconds
- Infographic: ~50 seconds
- Data Table: ~30 seconds
- Slides: ~5 minutes (longest)

A 10-minute timeout accommodates all content types with margin.
"""

DEEP_RESEARCH_TIMEOUT_MS: Final[int] = 1_800_000
"""Timeout for Deep Research operation in milliseconds (30 minutes).

Deep Research runs a 5-step process that can take 25+ minutes.
A 30-minute timeout provides sufficient margin.
"""

FAST_RESEARCH_TIMEOUT_MS: Final[int] = 120_000
"""Timeout for Fast Research operation in milliseconds (2 minutes).

Fast Research typically completes in 15-30 seconds.
A 2-minute timeout provides margin for slower responses.
"""

SOURCE_ADD_TIMEOUT_MS: Final[int] = 60_000
"""Timeout for source addition in milliseconds.

Maximum time to wait for a source (text, URL, file) to be added and processed.
"""

FILE_UPLOAD_TIMEOUT_MS: Final[int] = 120_000
"""Timeout for file upload in milliseconds (2 minutes).

Maximum time to wait for a file upload to complete.
Large PDF or media files may require additional time.
"""

LOGIN_WAIT_TIMEOUT_MS: Final[int] = 300_000
"""Timeout for manual login wait in milliseconds (5 minutes).

Maximum time to wait for the user to complete manual Google login
during the initial authentication flow.
"""

# ---------------------------------------------------------------------------
# 3. Polling intervals (seconds)
# ---------------------------------------------------------------------------

GENERATION_POLL_INTERVAL_SECONDS: Final[float] = 2.0
"""Polling interval for checking generation status in seconds.

Used when waiting for long-running operations such as
Audio Overview, Studio content, and Deep Research.
"""

DEEP_RESEARCH_POLL_INTERVAL_SECONDS: Final[float] = 5.0
"""Polling interval for Deep Research status checks in seconds.

Deep Research uses a longer poll interval since each step takes minutes.
"""

# ---------------------------------------------------------------------------
# 4. Session management constants
# ---------------------------------------------------------------------------

DEFAULT_SESSION_FILE: Final[str] = ".notebooklm-session.json"
"""Default path for the Playwright session state file.

Stores browser cookies and local storage for session persistence.
This file is added to ``.gitignore`` to prevent credential leakage.
"""

SESSION_CHECK_URL: Final[str] = "https://notebooklm.google.com"
"""URL used to validate whether the stored session is still active.

The browser navigates to this URL and checks if it redirects to
Google login, indicating session expiration.
"""

# ---------------------------------------------------------------------------
# 5. Stealth browser configuration
# ---------------------------------------------------------------------------

STEALTH_VIEWPORT: Final[dict[str, int]] = {
    "width": 1920,
    "height": 1080,
}
"""Default viewport size for Playwright stealth mode.

Uses a common 1080p desktop resolution to appear as a real user.
"""

STEALTH_USER_AGENT: Final[str] = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0.0.0 Safari/537.36"
)
"""Default User-Agent string for stealth mode.

Mimics a real Chrome browser on macOS to avoid bot detection.
"""

STEALTH_LOCALE: Final[str] = "ja-JP"
"""Default locale for the browser context.

Set to Japanese to match NotebookLM's expected locale for
Japanese-language selectors and UI elements.
"""

STEALTH_TIMEZONE: Final[str] = "Asia/Tokyo"
"""Default timezone for the browser context."""

STEALTH_INIT_SCRIPT: Final[str] = """\
// Hide navigator.webdriver property
Object.defineProperty(navigator, 'webdriver', {
    get: () => undefined,
});

// Override WebGL vendor and renderer
const getParameter = WebGLRenderingContext.prototype.getParameter;
WebGLRenderingContext.prototype.getParameter = function(parameter) {
    if (parameter === 37445) {
        return 'Intel Inc.';
    }
    if (parameter === 37446) {
        return 'Intel Iris OpenGL Engine';
    }
    return getParameter.call(this, parameter);
};

// Add chrome.runtime to appear as a Chrome extension environment
if (!window.chrome) {
    window.chrome = {};
}
if (!window.chrome.runtime) {
    window.chrome.runtime = {};
}
"""
"""JavaScript initialization script for Playwright stealth mode.

Hides automation indicators from bot detection scripts:

- ``navigator.webdriver``: Set to undefined (default is true in automation).
- WebGL vendor/renderer: Overridden to Intel values instead of generic ones.
- ``chrome.runtime``: Added to simulate a Chrome extension environment.
"""

# ---------------------------------------------------------------------------
# 6. Retry settings
# ---------------------------------------------------------------------------

DEFAULT_MAX_RETRIES: Final[int] = 3
"""Default maximum number of retry attempts for failed operations."""

DEFAULT_RETRY_BACKOFF_SECONDS: Final[float] = 1.0
"""Default base backoff time between retries in seconds.

Uses exponential backoff: ``backoff * (2 ** attempt)``.
"""

# ---------------------------------------------------------------------------
# Module exports
# ---------------------------------------------------------------------------

__all__ = [
    "AUDIO_OVERVIEW_TIMEOUT_MS",
    "CHAT_RESPONSE_TIMEOUT_MS",
    "DEEP_RESEARCH_POLL_INTERVAL_SECONDS",
    "DEEP_RESEARCH_TIMEOUT_MS",
    "DEFAULT_ELEMENT_TIMEOUT_MS",
    "DEFAULT_MAX_RETRIES",
    "DEFAULT_NAVIGATION_TIMEOUT_MS",
    "DEFAULT_RETRY_BACKOFF_SECONDS",
    "DEFAULT_SESSION_FILE",
    "FAST_RESEARCH_TIMEOUT_MS",
    "FILE_UPLOAD_TIMEOUT_MS",
    "GENERATION_POLL_INTERVAL_SECONDS",
    "GOOGLE_LOGIN_URL",
    "LOGIN_WAIT_TIMEOUT_MS",
    "NOTEBOOKLM_BASE_URL",
    "NOTEBOOK_URL_TEMPLATE",
    "SESSION_CHECK_URL",
    "SOURCE_ADD_TIMEOUT_MS",
    "STEALTH_INIT_SCRIPT",
    "STEALTH_LOCALE",
    "STEALTH_TIMEZONE",
    "STEALTH_USER_AGENT",
    "STEALTH_VIEWPORT",
    "STUDIO_GENERATION_TIMEOUT_MS",
]

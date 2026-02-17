"""Pytest configuration and fixtures for notebooklm tests.

Provides shared fixtures for testing NotebookLM automation components:
- ``mock_browser_manager``: Mocked ``NotebookLMBrowserManager`` instance.
- ``mock_page``: Mocked Playwright ``Page`` object with common stubs.
- ``sample_notebook_data``: Sample notebook metadata for assertion targets.
"""

import logging
from collections.abc import Iterator
from datetime import datetime, timezone
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from notebooklm.browser.manager import NotebookLMBrowserManager
from notebooklm.types import NotebookInfo, SourceInfo

# ---------------------------------------------------------------------------
# Browser fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_page() -> AsyncMock:
    """Create a mocked Playwright Page object with common stubs.

    The mock page provides async stubs for frequently used Playwright
    Page methods: ``goto``, ``wait_for_selector``, ``query_selector``,
    ``query_selector_all``, ``evaluate``, ``close``, ``url``, ``title``,
    ``fill``, ``click``, ``type``, ``wait_for_url``, and
    ``wait_for_load_state``.

    Returns
    -------
    AsyncMock
        A mocked Playwright Page object.
    """
    page = AsyncMock()
    page.url = "https://notebooklm.google.com"
    page.title = AsyncMock(return_value="NotebookLM")

    # Navigation
    page.goto = AsyncMock(return_value=None)
    page.wait_for_url = AsyncMock(return_value=None)
    page.wait_for_load_state = AsyncMock(return_value=None)

    # Element interaction
    page.wait_for_selector = AsyncMock(return_value=MagicMock())
    page.query_selector = AsyncMock(return_value=MagicMock())
    page.query_selector_all = AsyncMock(return_value=[])
    page.fill = AsyncMock(return_value=None)
    page.click = AsyncMock(return_value=None)
    page.type = AsyncMock(return_value=None)

    # Evaluation
    page.evaluate = AsyncMock(return_value=None)

    # Cleanup
    page.close = AsyncMock(return_value=None)

    return page


@pytest.fixture
def mock_browser_manager(mock_page: AsyncMock) -> MagicMock:
    """Create a mocked ``NotebookLMBrowserManager`` instance.

    The manager is configured as a MagicMock with spec matching
    ``NotebookLMBrowserManager``. Key methods are stubbed:

    - ``new_page()`` returns ``mock_page``.
    - ``save_session()`` is a no-op async mock.
    - ``has_session()`` returns False.
    - ``is_session_valid()`` returns True.
    - ``close()`` is a no-op async mock.
    - Async context manager (``__aenter__``/``__aexit__``) is supported.

    Parameters
    ----------
    mock_page : AsyncMock
        The mocked page fixture (auto-injected by pytest).

    Returns
    -------
    MagicMock
        A mocked ``NotebookLMBrowserManager`` instance.
    """
    manager = MagicMock(spec=NotebookLMBrowserManager)

    # Attributes
    manager.headless = True
    manager.session_file = ".notebooklm-session.json"

    # Async methods
    manager.new_page = AsyncMock(return_value=mock_page)
    manager.save_session = AsyncMock(return_value=None)
    manager.close = AsyncMock(return_value=None)
    manager.is_session_valid = AsyncMock(return_value=True)

    # Sync methods
    manager.has_session = MagicMock(return_value=False)

    # Async context manager support
    manager.__aenter__ = AsyncMock(return_value=manager)
    manager.__aexit__ = AsyncMock(return_value=None)

    return manager


# ---------------------------------------------------------------------------
# Data fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_notebook_data() -> dict[str, Any]:
    """Create sample notebook data for testing.

    Provides a dictionary containing sample data representing a typical
    NotebookLM notebook with sources, suitable for use as assertion
    targets or test input data.

    Returns
    -------
    dict[str, Any]
        Dictionary with keys:
        - ``notebook``: A ``NotebookInfo`` instance.
        - ``sources``: A list of ``SourceInfo`` instances.
        - ``raw``: Raw dictionary data for the notebook.
    """
    now = datetime.now(tz=timezone.utc)
    notebook = NotebookInfo(
        notebook_id="c9354f3f-f55b-4f90-a5c4-219e582945cf",
        title="AI Research Notes",
        updated_at=now,
        source_count=3,
    )
    sources = [
        SourceInfo(
            source_id="src-001",
            title="Machine Learning Overview",
            source_type="url",
            added_at=now,
        ),
        SourceInfo(
            source_id="src-002",
            title="Deep Learning Paper",
            source_type="file",
            added_at=now,
        ),
        SourceInfo(
            source_id="src-003",
            title="User Notes",
            source_type="text",
            added_at=now,
        ),
    ]
    raw = {
        "notebook_id": "c9354f3f-f55b-4f90-a5c4-219e582945cf",
        "title": "AI Research Notes",
        "source_count": 3,
        "sources": [
            {
                "source_id": "src-001",
                "title": "Machine Learning Overview",
                "source_type": "url",
            },
            {
                "source_id": "src-002",
                "title": "Deep Learning Paper",
                "source_type": "file",
            },
            {
                "source_id": "src-003",
                "title": "User Notes",
                "source_type": "text",
            },
        ],
    }
    return {
        "notebook": notebook,
        "sources": sources,
        "raw": raw,
    }


# ---------------------------------------------------------------------------
# Logging fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def capture_logs(
    caplog: pytest.LogCaptureFixture,
) -> Iterator[pytest.LogCaptureFixture]:
    """Capture logs for testing with proper level.

    Sets the log level to DEBUG so that all log messages from
    notebooklm modules are captured during the test.

    Parameters
    ----------
    caplog : pytest.LogCaptureFixture
        Pytest's built-in log capture fixture.

    Yields
    ------
    pytest.LogCaptureFixture
        The configured log capture fixture.
    """
    caplog.set_level(logging.DEBUG)
    yield caplog

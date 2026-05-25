"""Pytest configuration and shared fixtures for ``market.fraser`` tests.

This module provides reusable fixtures for testing the FRASER REST API
client module, including a test-friendly ``FraserConfig``, mock HTTP
responses, a sample FOMC items JSON payload, an isolated download
directory, and ``FRASER_API_KEY`` injection via ``monkeypatch``.

Fixtures
--------
sample_fraser_config : FraserConfig
    Test-friendly ``FraserConfig`` with short timeout.
sample_fomc_items_response : dict[str, object]
    Sample FRASER ``/title/677/items`` style response with 5 items
    covering the camelCase ↔ snake_case alias path.
mock_httpx_response_factory : Callable[..., MagicMock]
    Factory producing ``MagicMock(spec=httpx.Response)`` instances with
    configurable ``status_code`` / ``json_data`` / ``headers`` /
    ``chunks``.
fraser_data_dir : Path
    Isolated download directory rooted at ``tmp_path``.
fraser_env_key (autouse) : None
    Sets ``FRASER_API_KEY=dummy_test_key`` for the duration of each
    test via ``monkeypatch.setenv``.

See Also
--------
tests.market.alphavantage.conftest : Reference fixture template
    (``sample_alphavantage_config``, ``mock_alphavantage_session``).
"""

from collections.abc import Callable
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import httpx
import pytest

from market.fraser.types import FraserConfig

# =============================================================================
# Configuration fixtures
# =============================================================================


@pytest.fixture
def sample_fraser_config() -> FraserConfig:
    """Create a test-friendly ``FraserConfig`` with short timeout.

    Returns
    -------
    FraserConfig
        ``FraserConfig`` with ``api_key="dummy_test_key"``,
        ``timeout=5.0`` and default rate limits.
    """
    return FraserConfig(
        api_key="dummy_test_key",
        timeout=5.0,
    )


# =============================================================================
# API response fixtures
# =============================================================================


@pytest.fixture
def sample_beige_book_items_response() -> dict[str, object]:
    """Sample FRASER Beige Book ``/title/.../items`` style response.

    Provides 4 items spanning 2023-2024 plus 1 historical 1995 entry
    so that year-range filtering can be exercised. The 2024 items
    include both PDF-only and PDF+TXT location variants.

    Returns
    -------
    dict[str, object]
        Mock JSON response containing 5 Beige Book items.
    """
    return {
        "titleId": 1234,
        "name": "Beige Book",
        "items": [
            {
                "itemId": 2001,
                "titleId": 1234,
                "title": "Beige Book, January 2023",
                "date": "2023-01-18",
                "location": {
                    "pdfUrl": ["https://fraser.stlouisfed.org/files/doc/2001.pdf"],
                    "textUrl": ["https://fraser.stlouisfed.org/files/doc/2001.txt"],
                },
            },
            {
                "itemId": 2002,
                "titleId": 1234,
                "title": "Beige Book, October 2023",
                "date": "2023-10-18",
                "location": {
                    "pdfUrl": ["https://fraser.stlouisfed.org/files/doc/2002.pdf"],
                },
            },
            {
                "itemId": 2003,
                "titleId": 1234,
                "title": "Beige Book, March 2024",
                "date": "2024-03-06",
                "location": {
                    "pdfUrl": ["https://fraser.stlouisfed.org/files/doc/2003.pdf"],
                    "textUrl": ["https://fraser.stlouisfed.org/files/doc/2003.txt"],
                },
            },
            {
                "itemId": 2004,
                "titleId": 1234,
                "title": "Beige Book, September 2024",
                "date": "2024-09-04",
                "location": {
                    "pdfUrl": ["https://fraser.stlouisfed.org/files/doc/2004.pdf"],
                },
            },
            {
                "itemId": 2099,
                "titleId": 1234,
                "title": "Historical Beige Book Document",
                "date": "1995",
            },
        ],
    }


@pytest.fixture
def sample_speech_items_response() -> dict[str, object]:
    """Sample FRASER FRB Speeches ``/title/.../items`` style response.

    Includes speeches from multiple speakers (Powell, Volcker) in both
    modern (2024) and historical (1980) years so that speaker filtering
    and historical-archive year ranges can be exercised. Speaker
    metadata is attached via the ``authors[]`` field.

    Returns
    -------
    dict[str, object]
        Mock JSON response containing 5 speech items.
    """
    return {
        "titleId": 5678,
        "name": "Speeches and Statements",
        "items": [
            {
                "itemId": 3001,
                "titleId": 5678,
                "title": "Economic Outlook",
                "date": "2024-02-07",
                "authors": [{"name": "Jerome H. Powell", "role": "speaker"}],
                "location": {
                    "textUrl": ["https://fraser.stlouisfed.org/files/doc/3001.txt"],
                },
            },
            {
                "itemId": 3002,
                "titleId": 5678,
                "title": "Monetary Policy and Inflation",
                "date": "2024-05-15",
                "authors": [{"name": "Jerome H. Powell", "role": "speaker"}],
                "location": {
                    "pdfUrl": ["https://fraser.stlouisfed.org/files/doc/3002.pdf"],
                },
            },
            {
                "itemId": 3003,
                "titleId": 5678,
                "title": "Financial Stability",
                "date": "2024-09-21",
                "authors": [{"name": "Lisa D. Cook", "role": "speaker"}],
            },
            {
                "itemId": 3004,
                "titleId": 5678,
                "title": "Anti-Inflation Strategy",
                "date": "1980-10-09",
                "authors": [{"name": "Paul A. Volcker", "role": "speaker"}],
            },
            {
                "itemId": 3005,
                "titleId": 5678,
                "title": "Speech without author metadata",
                "date": "2024-06-01",
                "description": "Delivered by Powell at the Jackson Hole symposium",
            },
        ],
    }


@pytest.fixture
def sample_mpr_items_response() -> dict[str, object]:
    """Sample FRASER Monetary Policy Report ``/title/.../items`` response.

    Includes modern semi-annual reports (2024 Feb / Jul) plus a
    Humphrey-Hawkins-era report (1979 Jul) and a 2000 report so that
    historical archive lookups can be exercised. All items are
    PDF-only because the legacy archive rarely exposes TXT renditions.

    Returns
    -------
    dict[str, object]
        Mock JSON response containing 4 Monetary Policy Report items.
    """
    return {
        "titleId": 9012,
        "name": "Monetary Policy Report to the Congress",
        "items": [
            {
                "itemId": 4001,
                "titleId": 9012,
                "title": "Monetary Policy Report - February 2024",
                "date": "2024-02-09",
                "reportPeriod": "February 2024",
                "location": {
                    "pdfUrl": ["https://fraser.stlouisfed.org/files/doc/4001.pdf"],
                },
            },
            {
                "itemId": 4002,
                "titleId": 9012,
                "title": "Monetary Policy Report - July 2024",
                "date": "2024-07-05",
                "reportPeriod": "July 2024",
                "location": {
                    "pdfUrl": ["https://fraser.stlouisfed.org/files/doc/4002.pdf"],
                },
            },
            {
                "itemId": 4099,
                "titleId": 9012,
                "title": "Monetary Policy Report - July 1979 (Humphrey-Hawkins)",
                "date": "1979-07-17",
                "reportPeriod": "July 1979",
                "location": {
                    "pdfUrl": ["https://fraser.stlouisfed.org/files/doc/4099.pdf"],
                },
            },
            {
                "itemId": 4100,
                "titleId": 9012,
                "title": "Monetary Policy Report - July 2000",
                "date": "2000-07-20",
                "reportPeriod": "July 2000",
                "location": {
                    "pdfUrl": ["https://fraser.stlouisfed.org/files/doc/4100.pdf"],
                },
            },
        ],
    }


@pytest.fixture
def sample_fomc_items_response() -> dict[str, object]:
    """Sample FRASER ``/title/677/items`` style response with 5 items.

    The payload deliberately mixes:

    - All three accepted ``date`` formats (``YYYY-MM-DD``, ``YYYY-MM``,
      ``YYYY``).
    - camelCase aliases (``itemId``, ``titleId``, ``pdfUrl``,
      ``textUrl``) so that ``populate_by_name=True`` is exercised.
    - Items both with and without an embedded ``location`` block.

    Returns
    -------
    dict[str, object]
        Mock JSON response containing 5 items under the ``items`` key
        plus minimal title metadata.
    """
    return {
        "titleId": 677,
        "name": "Federal Open Market Committee",
        "items": [
            {
                "itemId": 1001,
                "titleId": 677,
                "title": "Minutes of the Federal Open Market Committee, January 2024",
                "date": "2024-01-31",
                "description": "FOMC Minutes January 2024 meeting",
                "location": {
                    "pdfUrl": ["https://fraser.stlouisfed.org/files/doc/1001.pdf"],
                    "textUrl": ["https://fraser.stlouisfed.org/files/doc/1001.txt"],
                },
            },
            {
                "itemId": 1002,
                "titleId": 677,
                "title": "Minutes of the Federal Open Market Committee, March 2024",
                "date": "2024-03-20",
                "location": {
                    "pdfUrl": ["https://fraser.stlouisfed.org/files/doc/1002.pdf"],
                },
            },
            {
                "itemId": 1003,
                "titleId": 677,
                "title": "Minutes of the Federal Open Market Committee, April 2024",
                "date": "2024-04",
            },
            {
                "itemId": 1004,
                "titleId": 677,
                "title": "Historical FOMC Document",
                "date": "1995",
            },
            {
                "itemId": 1005,
                "titleId": 677,
                "title": "Minutes of the Federal Open Market Committee, June 2024",
                "date": "2024-06-12",
                "location": {
                    "pdfUrl": ["https://fraser.stlouisfed.org/files/doc/1005.pdf"],
                    "textUrl": ["https://fraser.stlouisfed.org/files/doc/1005.txt"],
                },
            },
        ],
    }


# =============================================================================
# Mock object fixtures
# =============================================================================


@pytest.fixture
def mock_httpx_response_factory() -> Callable[..., MagicMock]:
    """Factory producing ``MagicMock(spec=httpx.Response)`` instances.

    Returns
    -------
    Callable[..., MagicMock]
        Function with signature ``(status_code, json_data, headers=None,
        chunks=None)`` returning a configured ``MagicMock``. The mock
        exposes ``status_code``, ``headers``, ``json()`` (returning
        ``json_data``), ``text`` (JSON-serialised ``json_data``), and
        ``iter_bytes()`` (yielding ``chunks`` when provided).
    """

    def _factory(
        status_code: int,
        json_data: dict[str, Any] | None,
        headers: dict[str, str] | None = None,
        chunks: list[bytes] | None = None,
    ) -> MagicMock:
        response = MagicMock(spec=httpx.Response)
        response.status_code = status_code
        response.headers = headers or {}
        response.json.return_value = json_data
        # Provide a ``text`` attribute mirroring the JSON-encoded body.
        if json_data is not None:
            import json as _json

            response.text = _json.dumps(json_data)
        else:
            response.text = ""
        if chunks is not None:
            response.iter_bytes.return_value = iter(chunks)
        return response

    return _factory


# =============================================================================
# Filesystem fixtures
# =============================================================================


@pytest.fixture
def fraser_data_dir(tmp_path: Path) -> Path:
    """Isolated download directory for FRASER tests.

    Parameters
    ----------
    tmp_path : Path
        Pytest-provided temporary directory.

    Returns
    -------
    Path
        Path to a freshly-created ``fraser/`` directory under
        ``tmp_path``.
    """
    target = tmp_path / "fraser"
    target.mkdir(parents=True, exist_ok=True)
    return target


# =============================================================================
# Environment fixtures
# =============================================================================


@pytest.fixture(autouse=True)
def fraser_env_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """Inject ``FRASER_API_KEY=dummy_test_key`` for every test.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Pytest monkeypatch fixture.
    """
    monkeypatch.setenv("FRASER_API_KEY", "dummy_test_key")

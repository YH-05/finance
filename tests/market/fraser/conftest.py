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

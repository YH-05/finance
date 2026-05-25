"""Integration tests for the FRASER REST API client (live HTTP).

These tests hit the real FRASER endpoints and are gated by the
``FRASER_API_KEY`` environment variable — the module is skipped when the
key is absent. The ``FraserClient`` fixture is module-scoped so that the
30 req/min rate limiter state is shared across all tests, ensuring the
entire file completes within a single rate-limit window.

Coverage
--------
- ``FraserClient.list_items(title_id=677)`` returns ``FraserItem`` models.
- ``FOMCMinutesFetcher.list_minutes((2024, 2024))`` returns at least
  6 ``FOMCMeeting`` entries (calendar year 2024 has 8 FOMC meetings).
- ``FOMCMinutesFetcher.fetch_text`` writes ``<YYYY-MM-DD>_<itemId>.txt``
  (> 1 KB) and a ``.meta.json`` sidecar.

Run with::

    FRASER_API_KEY=<key> uv run pytest \\
        tests/market/fraser/integration/ -m integration -v

See Also
--------
tests.market.alphavantage.integration.test_alphavantage_integration :
    Reference live-API integration test pattern
    (``pytestmark`` + ``_has_api_key`` + ``scope='module'`` fixture).
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

import pytest

from market.fraser.client import FraserClient
from market.fraser.constants import KNOWN_TITLE_IDS
from market.fraser.downloader import FraserDownloader
from market.fraser.fetchers.beige_book import BeigeBookFetcher
from market.fraser.fetchers.fomc import (
    FOMCMinutesFetcher,
    FOMCPressConferencesFetcher,
    FOMCStatementsFetcher,
)
from market.fraser.fetchers.monetary_policy import MonetaryPolicyReportFetcher
from market.fraser.fetchers.speeches import FRBSpeechFetcher
from market.fraser.models import (
    BeigeBookReport,
    FOMCMeeting,
    FraserItem,
    FRBSpeech,
    MonetaryPolicyReport,
)

if TYPE_CHECKING:
    from collections.abc import Generator
    from pathlib import Path

# ---------------------------------------------------------------------------
# Module-level markers
# ---------------------------------------------------------------------------


def _has_api_key() -> bool:
    """Return ``True`` when the FRASER API key is available."""
    return bool(os.environ.get("FRASER_API_KEY"))


pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        not _has_api_key(),
        reason="FRASER_API_KEY not set -- skipping live API tests",
    ),
]


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def fraser_client() -> Generator[FraserClient]:
    """Build a module-scoped :class:`FraserClient` reading the env key.

    Module scope is essential so that the underlying ``DualWindowRateLimiter``
    state is shared between tests — otherwise the 30 req/min cap could be
    breached if a fresh limiter were instantiated per test.

    Yields
    ------
    FraserClient
        A live client using the ``FRASER_API_KEY`` environment variable.
    """
    client = FraserClient()
    try:
        yield client
    finally:
        client.close()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestFraserClientListItems:
    """E2E coverage for :meth:`FraserClient.list_items`."""

    def test_E2E_FraserClient_list_items_titleId_677(
        self, fraser_client: FraserClient
    ) -> None:
        items = fraser_client.list_items(title_id=677, limit=10)
        assert len(items) >= 1
        assert all(isinstance(i, FraserItem) for i in items)


class TestFOMCMinutesFetcherListMinutes:
    """E2E coverage for :meth:`FOMCMinutesFetcher.list_minutes`."""

    def test_E2E_FOMCMinutesFetcher_list_minutes_2024(
        self, fraser_client: FraserClient
    ) -> None:
        fetcher = FOMCMinutesFetcher(client=fraser_client)
        meetings = fetcher.list_minutes(year_range=(2024, 2024))
        # Calendar year 2024 should expose at least 6 of the 8 FOMC meetings.
        assert len(meetings) >= 6
        assert all(isinstance(m, FOMCMeeting) for m in meetings)
        assert all(m.date.year == 2024 for m in meetings)


class TestFOMCMinutesFetcherFetchText:
    """E2E coverage for :meth:`FOMCMinutesFetcher.fetch_text`."""

    def test_E2E_fetch_text_txt_size_over_1KB(
        self, fraser_client: FraserClient, tmp_path: Path
    ) -> None:
        fetcher = FOMCMinutesFetcher(
            client=fraser_client,
            downloader=FraserDownloader(
                session=fraser_client._session, base_dir=tmp_path
            ),
        )
        meetings = fetcher.list_minutes(year_range=(2024, 2024))
        assert meetings, "No 2024 FOMC meetings returned"

        # Pick the first item that exposes either txt or pdf URLs.
        item_id = next(
            (
                m.item_id
                for m in meetings
                if m.location is not None
                and (m.location.text_url or m.location.pdf_url)
            ),
            None,
        )
        if item_id is None:
            pytest.skip("No 2024 FOMC item exposes downloadable URLs")

        path, meeting = fetcher.fetch_text(item_id, prefer="txt")

        assert path.exists()
        assert path.stat().st_size > 1024
        meta_path = path.with_suffix(".meta.json")
        assert meta_path.exists()
        assert isinstance(meeting, FOMCMeeting)


# ---------------------------------------------------------------------------
# FOMCStatementsFetcher / FOMCPressConferencesFetcher E2E smoke tests
# ---------------------------------------------------------------------------

# These two fetchers depend on FRASER ``title_id`` values that are not
# yet hard-coded in :data:`KNOWN_TITLE_IDS`. The integration tests are
# skipped automatically when the title_id is unknown so that the E2E
# suite remains green until task-2 (discover_titles) populates the
# mapping (per project-108 plan).


class TestFOMCStatementsFetcherE2E:
    """E2E smoke coverage for :class:`FOMCStatementsFetcher`."""

    def test_E2E_FOMCStatementsFetcher_list_statements_2024(
        self, fraser_client: FraserClient
    ) -> None:
        if KNOWN_TITLE_IDS.get("fomc_statements") is None:
            pytest.skip(
                "title_id for 'fomc_statements' is not yet configured "
                "(run discover_titles to populate)"
            )
        fetcher = FOMCStatementsFetcher(client=fraser_client)
        statements = fetcher.list_statements(year_range=(2024, 2024))
        # Calendar year 2024 has 8 FOMC meetings; accept >= 1 to keep
        # the smoke test tolerant of partial coverage in FRASER.
        assert len(statements) >= 1
        assert all(isinstance(m, FOMCMeeting) for m in statements)
        assert all(m.date.year == 2024 for m in statements)


class TestFOMCPressConferencesFetcherE2E:
    """E2E smoke coverage for :class:`FOMCPressConferencesFetcher`."""

    def test_E2E_FOMCPressConferencesFetcher_list_press_conferences_2024(
        self, fraser_client: FraserClient
    ) -> None:
        if KNOWN_TITLE_IDS.get("fomc_press_conferences") is None:
            pytest.skip(
                "title_id for 'fomc_press_conferences' is not yet configured "
                "(run discover_titles to populate)"
            )
        fetcher = FOMCPressConferencesFetcher(client=fraser_client)
        press_confs = fetcher.list_press_conferences(year_range=(2024, 2024))
        assert len(press_confs) >= 1
        assert all(isinstance(m, FOMCMeeting) for m in press_confs)
        assert all(m.date.year == 2024 for m in press_confs)


# ---------------------------------------------------------------------------
# PR4 後半: Beige Book / FRB Speeches / Monetary Policy Report E2E smoke tests
# ---------------------------------------------------------------------------


class TestBeigeBookFetcherE2E:
    """E2E smoke coverage for :class:`BeigeBookFetcher`."""

    def test_E2E_BeigeBookFetcher_list_reports_2024(
        self, fraser_client: FraserClient
    ) -> None:
        if KNOWN_TITLE_IDS.get("beige_book") is None:
            pytest.skip(
                "title_id for 'beige_book' is not yet configured "
                "(run discover_titles to populate)"
            )
        fetcher = BeigeBookFetcher(client=fraser_client)
        reports = fetcher.list_reports(year_range=(2024, 2024))
        # Calendar year 2024 has 8 Beige Book releases; accept >= 1 to keep
        # the smoke test tolerant of partial coverage in FRASER.
        assert len(reports) >= 1
        assert all(isinstance(r, BeigeBookReport) for r in reports)
        assert all(r.date.year == 2024 for r in reports)


class TestFRBSpeechFetcherE2E:
    """E2E smoke coverage for :class:`FRBSpeechFetcher`."""

    def test_E2E_FRBSpeechFetcher_list_speeches_Powell_2024(
        self, fraser_client: FraserClient
    ) -> None:
        if KNOWN_TITLE_IDS.get("frb_speeches") is None:
            pytest.skip(
                "title_id for 'frb_speeches' is not yet configured "
                "(run discover_titles to populate)"
            )
        fetcher = FRBSpeechFetcher(client=fraser_client)
        powell_speeches = fetcher.list_speeches(
            year_range=(2024, 2024), speaker="Powell"
        )
        # Powell delivers several speeches per year; accept >= 1 to be
        # tolerant of partial coverage.
        assert len(powell_speeches) >= 1
        assert all(isinstance(s, FRBSpeech) for s in powell_speeches)
        assert all(s.date.year == 2024 for s in powell_speeches)


class TestMonetaryPolicyReportFetcherE2E:
    """E2E smoke coverage for :class:`MonetaryPolicyReportFetcher`."""

    def test_E2E_MonetaryPolicyReportFetcher_list_reports_2024(
        self, fraser_client: FraserClient
    ) -> None:
        if KNOWN_TITLE_IDS.get("monetary_policy_report") is None:
            pytest.skip(
                "title_id for 'monetary_policy_report' is not yet configured "
                "(run discover_titles to populate)"
            )
        fetcher = MonetaryPolicyReportFetcher(client=fraser_client)
        reports = fetcher.list_reports(year_range=(2024, 2024))
        # MPR is semi-annual: 2 reports per calendar year.
        assert len(reports) >= 1
        assert all(isinstance(r, MonetaryPolicyReport) for r in reports)
        assert all(r.date.year == 2024 for r in reports)

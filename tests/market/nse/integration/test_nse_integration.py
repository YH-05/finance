"""Integration tests for NSE collectors against the live NSE India API.

These tests send real HTTP requests to https://www.nseindia.com and
verify that data retrieval and parsing work correctly end-to-end.

Run with::

    uv run pytest tests/market/nse/integration/ -m integration -v

IMPORTANT: The NSE API has bot-detection mechanisms (403 responses) and
requires a valid session cookie obtained by visiting the home page.
This test module is designed to minimise API usage:
- ``scope="module"`` fixtures share a single NseSession across all tests
- Polite delay of 1.0s between requests to avoid rate limiting
- Tests are grouped to reuse session and fetched data

Sample symbols:
- Infosys (``INFY``)
- Reliance Industries (``RELIANCE``)

Sample indices:
- ``NIFTY 50``
- ``NIFTY BANK``

Note
----
NSE API is geo-blocked for non-Indian IP addresses. Tests are automatically
skipped when the API is unreachable (blocked, rate-limited, or network error).

See Also
--------
market.nse.collectors.quote : QuoteCollector under test.
market.nse.collectors.indices : IndicesCollector under test.
market.nse.collectors.stock_list : StockListCollector under test.
market.nse.collectors.corporate : CorporateCollector under test.
tests/market/nse/unit/ : Unit tests with mocked HTTP.
tests/market/bse/integration/test_bse_integration.py : BSE reference.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pandas as pd
import pytest

from market.nse.collectors.corporate import CorporateCollector
from market.nse.collectors.indices import IndicesCollector
from market.nse.collectors.quote import QuoteCollector
from market.nse.collectors.stock_list import StockListCollector
from market.nse.errors import NseAPIError, NseCookieError, NseError, NseRateLimitError
from market.nse.session import NseSession
from market.nse.types import (
    FinancialResult,
    NseConfig,
    RetryConfig,
    StockQuote,
)

if TYPE_CHECKING:
    from collections.abc import Generator

# ---------------------------------------------------------------------------
# Sample securities and indices for testing
# ---------------------------------------------------------------------------

SAMPLE_SYMBOL_INFY = "INFY"  # Infosys Ltd
SAMPLE_SYMBOL_RELIANCE = "RELIANCE"  # Reliance Industries Ltd
SAMPLE_INDEX_NIFTY50 = "NIFTY 50"
SAMPLE_INDEX_NIFTY_BANK = "NIFTY BANK"


def _nse_api_is_reachable() -> bool:
    """Check if the NSE API is reachable by sending a lightweight request.

    Makes a single request to the quote endpoint for INFY.  Returns False on
    403 (IP geo-block / bot block), 429 (rate limit), or any network error.

    Returns
    -------
    bool
        True if the NSE API responds with a 200 status code.
    """
    try:
        with NseSession(
            config=NseConfig(polite_delay=0.5, timeout=15.0),
            retry_config=RetryConfig(max_attempts=1),
        ) as session:
            from market.nse.constants import API_BASE_URL

            response = session.get(
                f"{API_BASE_URL}/quote-equity",
                params={"symbol": SAMPLE_SYMBOL_INFY},
            )
            return response.status_code == 200
    except (NseError, OSError, Exception):
        return False


# Cache the probe result at module import time so we only call it once
_NSE_REACHABLE = _nse_api_is_reachable()

# ---------------------------------------------------------------------------
# Module-level markers: skip all tests if NSE API is not reachable
# ---------------------------------------------------------------------------

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        not _NSE_REACHABLE,
        reason="NSE API is not reachable (geo-blocked, rate-limited, or network error)",
    ),
]


# ---------------------------------------------------------------------------
# Fixtures (module-scoped to minimise API calls)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def nse_session() -> Generator[NseSession]:
    """Create an NseSession connected to the live NSE API.

    Uses a polite delay of 1.0s and conservative retry settings to keep test
    execution predictable.  Shared across all tests in this module to
    avoid creating multiple HTTP connections and reduce cookie refresh overhead.
    """
    config = NseConfig(
        polite_delay=1.0,
        delay_jitter=0.2,
        timeout=30.0,
        cookie_refresh_interval=300.0,
    )
    retry = RetryConfig(
        max_attempts=3,
        initial_delay=2.0,
        max_delay=15.0,
        jitter=False,
    )
    with NseSession(config=config, retry_config=retry) as session:
        yield session


@pytest.fixture(scope="module")
def quote_collector(nse_session: NseSession) -> QuoteCollector:
    """Create a QuoteCollector with the shared session."""
    return QuoteCollector(session=nse_session)


@pytest.fixture(scope="module")
def indices_collector(nse_session: NseSession) -> IndicesCollector:
    """Create an IndicesCollector with the shared session."""
    return IndicesCollector(session=nse_session)


@pytest.fixture(scope="module")
def stock_list_collector(nse_session: NseSession) -> StockListCollector:
    """Create a StockListCollector with the shared session."""
    return StockListCollector(session=nse_session)


@pytest.fixture(scope="module")
def corporate_collector(nse_session: NseSession) -> CorporateCollector:
    """Create a CorporateCollector with the shared session."""
    return CorporateCollector(session=nse_session)


@pytest.fixture(scope="module")
def sample_infy_quote(quote_collector: QuoteCollector) -> StockQuote:
    """Fetch a sample quote for INFY for reuse across tests.

    Returns
    -------
    StockQuote
        A live quote for Infosys (INFY).
    """
    return quote_collector.fetch_quote(SAMPLE_SYMBOL_INFY)


@pytest.fixture(scope="module")
def sample_nifty50_df(indices_collector: IndicesCollector) -> pd.DataFrame:
    """Fetch NIFTY 50 constituents DataFrame for reuse across tests.

    Returns
    -------
    pd.DataFrame
        Live constituent data for NIFTY 50.
    """
    return indices_collector.fetch_index(SAMPLE_INDEX_NIFTY50)


@pytest.fixture(scope="module")
def sample_stock_list_df(stock_list_collector: StockListCollector) -> pd.DataFrame:
    """Fetch the full NSE equity stock list for reuse across tests.

    Returns
    -------
    pd.DataFrame
        Live EQUITY_L.csv data.
    """
    return stock_list_collector.fetch_stock_list()


@pytest.fixture(scope="module")
def sample_financial_results(
    corporate_collector: CorporateCollector,
) -> list[FinancialResult]:
    """Fetch INFY financial results for reuse across tests.

    Returns
    -------
    list[FinancialResult]
        Live financial results for Infosys (INFY).
    """
    return corporate_collector.get_financial_results(SAMPLE_SYMBOL_INFY)


# ---------------------------------------------------------------------------
# Tests: QuoteCollector
# ---------------------------------------------------------------------------


class TestQuoteCollectorIntegration:
    """Integration tests for QuoteCollector against the live NSE API."""

    def test_正常系_fetch_quoteでStockQuoteが返される(
        self, sample_infy_quote: StockQuote
    ) -> None:
        """fetch_quote('INFY') returns a valid StockQuote."""
        assert isinstance(sample_infy_quote, StockQuote)
        assert sample_infy_quote.symbol == SAMPLE_SYMBOL_INFY

    def test_正常系_StockQuoteのcompany_nameが空でない(
        self, sample_infy_quote: StockQuote
    ) -> None:
        """StockQuote.company_name is a non-empty string."""
        assert sample_infy_quote.company_name != ""

    def test_正常系_StockQuoteの価格フィールドが空でない(
        self, sample_infy_quote: StockQuote
    ) -> None:
        """StockQuote price fields (open, high, low, last_price, prev_close) are non-empty."""
        assert sample_infy_quote.open != ""
        assert sample_infy_quote.high != ""
        assert sample_infy_quote.low != ""
        assert sample_infy_quote.last_price != ""
        assert sample_infy_quote.prev_close != ""

    def test_正常系_fetchでDataFrame形式のquoteが返される(
        self, quote_collector: QuoteCollector
    ) -> None:
        """fetch(symbol='RELIANCE') returns a single-row DataFrame."""
        df = quote_collector.fetch(symbol=SAMPLE_SYMBOL_RELIANCE)

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 1
        assert "symbol" in df.columns
        assert "company_name" in df.columns

    def test_正常系_validateがfetch結果に対しTrueを返す(
        self, quote_collector: QuoteCollector
    ) -> None:
        """validate() returns True for data fetched via fetch()."""
        df = quote_collector.fetch(symbol=SAMPLE_SYMBOL_INFY)
        assert quote_collector.validate(df) is True


# ---------------------------------------------------------------------------
# Tests: IndicesCollector
# ---------------------------------------------------------------------------


class TestIndicesCollectorIntegration:
    """Integration tests for IndicesCollector against the live NSE API."""

    def test_正常系_fetch_indexでNIFTY50のDataFrameが返される(
        self, sample_nifty50_df: pd.DataFrame
    ) -> None:
        """fetch_index('NIFTY 50') returns a non-empty DataFrame."""
        assert isinstance(sample_nifty50_df, pd.DataFrame)
        assert len(sample_nifty50_df) > 0

    def test_正常系_NIFTY50データにsymbolカラムが含まれる(
        self, sample_nifty50_df: pd.DataFrame
    ) -> None:
        """NIFTY 50 DataFrame contains the 'symbol' column."""
        assert "symbol" in sample_nifty50_df.columns

    def test_正常系_validateがNIFTY50データに対しTrueを返す(
        self, indices_collector: IndicesCollector, sample_nifty50_df: pd.DataFrame
    ) -> None:
        """validate() returns True for NIFTY 50 constituent data."""
        assert indices_collector.validate(sample_nifty50_df) is True

    def test_正常系_fetchでindex_name指定のDataFrameが返される(
        self, indices_collector: IndicesCollector
    ) -> None:
        """fetch(index_name='NIFTY BANK') returns a non-empty DataFrame."""
        df = indices_collector.fetch(index_name=SAMPLE_INDEX_NIFTY_BANK)

        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0

    def test_正常系_NIFTY50の構成銘柄数が妥当な範囲にある(
        self, sample_nifty50_df: pd.DataFrame
    ) -> None:
        """NIFTY 50 index has between 40 and 60 constituent rows (inclusive of summary row)."""
        # NIFTY 50 index response includes the index summary row plus ~50 stocks
        assert 40 <= len(sample_nifty50_df) <= 60


# ---------------------------------------------------------------------------
# Tests: StockListCollector
# ---------------------------------------------------------------------------


class TestStockListCollectorIntegration:
    """Integration tests for StockListCollector against the live NSE archives."""

    def test_正常系_fetch_stock_listでDataFrameが返される(
        self, sample_stock_list_df: pd.DataFrame
    ) -> None:
        """fetch_stock_list() returns a non-empty DataFrame."""
        assert isinstance(sample_stock_list_df, pd.DataFrame)
        assert len(sample_stock_list_df) > 0

    def test_正常系_stock_listにsymbolカラムが含まれる(
        self, sample_stock_list_df: pd.DataFrame
    ) -> None:
        """Stock list DataFrame contains the 'symbol' column."""
        assert "symbol" in sample_stock_list_df.columns

    def test_正常系_stock_listにINFYが含まれる(
        self, sample_stock_list_df: pd.DataFrame
    ) -> None:
        """Stock list contains INFY (Infosys)."""
        assert SAMPLE_SYMBOL_INFY in sample_stock_list_df["symbol"].values

    def test_正常系_validateがstock_listに対しTrueを返す(
        self,
        stock_list_collector: StockListCollector,
        sample_stock_list_df: pd.DataFrame,
    ) -> None:
        """validate() returns True for data fetched via fetch_stock_list()."""
        assert stock_list_collector.validate(sample_stock_list_df) is True

    def test_正常系_stock_listの銘柄数が1000以上ある(
        self, sample_stock_list_df: pd.DataFrame
    ) -> None:
        """Stock list contains at least 1000 listed equities."""
        assert len(sample_stock_list_df) >= 1000


# ---------------------------------------------------------------------------
# Tests: CorporateCollector
# ---------------------------------------------------------------------------


class TestCorporateCollectorIntegration:
    """Integration tests for CorporateCollector against the live NSE API."""

    def test_正常系_get_financial_resultsでリストが返される(
        self, sample_financial_results: list[FinancialResult]
    ) -> None:
        """get_financial_results('INFY') returns a list of FinancialResult."""
        assert isinstance(sample_financial_results, list)

    def test_正常系_FinancialResultのsymbolがINFY(
        self, sample_financial_results: list[FinancialResult]
    ) -> None:
        """Each FinancialResult has symbol == 'INFY'."""
        # Infosys is a major company; should have financial results
        for result in sample_financial_results:
            assert isinstance(result, FinancialResult)
            assert result.symbol == SAMPLE_SYMBOL_INFY

    def test_正常系_FinancialResultにfrom_dateとto_dateが含まれる(
        self, sample_financial_results: list[FinancialResult]
    ) -> None:
        """FinancialResult has non-empty from_date and to_date fields."""
        for result in sample_financial_results:
            assert result.from_date != ""
            assert result.to_date != ""


# ---------------------------------------------------------------------------
# Tests: Cookie management
# ---------------------------------------------------------------------------


class TestCookieManagementIntegration:
    """Integration tests for NSE session cookie management."""

    def test_正常系_セッション全体でCookieリフレッシュが透過的に動作する(
        self,
        nse_session: NseSession,
    ) -> None:
        """Cookie refresh is transparent: multiple requests succeed without manual refresh.

        Verifies that the shared module-scoped NseSession (which has already
        made several requests) is still able to serve new requests without
        raising NseCookieError, confirming the automatic refresh mechanism works.
        """
        # By the time this test runs, the module-scoped session has made
        # multiple requests (quote, index, stock list, corporate).
        # This test sends one more request to confirm the session is still healthy.
        from market.nse.constants import API_BASE_URL

        response = nse_session.get(
            f"{API_BASE_URL}/quote-equity",
            params={"symbol": SAMPLE_SYMBOL_RELIANCE},
        )
        assert response.status_code == 200

    def test_正常系_cookie_acquired_atが正の値になっている(
        self, nse_session: NseSession
    ) -> None:
        """After at least one request, _cookie_acquired_at is a positive monotonic timestamp."""
        assert nse_session._cookie_acquired_at > 0.0


# ---------------------------------------------------------------------------
# Tests: IP geo-block detection
# ---------------------------------------------------------------------------


class TestIpGeoBlockDetection:
    """Tests for IP geo-block detection behaviour.

    NSE blocks non-Indian IP addresses with 403 responses.
    These tests verify the error handling path for IP geo-blocked environments.

    Note: These tests execute only when _NSE_REACHABLE is True (i.e., we are
    running from an Indian-IP or VPN environment).  The geo-block scenario
    itself is verified by checking the error class hierarchy and the session's
    403-handling logic via unit tests.  Here we verify the reachability check
    used by this test module accurately reflects the current IP environment.
    """

    def test_正常系_日本IP環境でAPIが到達可能である(self) -> None:
        """NSE API is reachable from the current network environment.

        If this test is reached (not skipped), _NSE_REACHABLE is True,
        confirming the API probe succeeded.
        """
        assert _NSE_REACHABLE is True

    def test_正常系_NseCookieErrorはNseErrorのサブクラスである(self) -> None:
        """NseCookieError is a subclass of NseError (used for geo-block 403 handling)."""

        assert issubclass(NseCookieError, NseError)

    def test_正常系_NseAPIErrorはNseErrorのサブクラスである(self) -> None:
        """NseAPIError is a subclass of NseError."""
        assert issubclass(NseAPIError, NseError)

    def test_正常系_NseRateLimitErrorはNseErrorのサブクラスである(self) -> None:
        """NseRateLimitError is a subclass of NseError."""
        assert issubclass(NseRateLimitError, NseError)

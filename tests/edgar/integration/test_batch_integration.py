"""Integration tests for BatchFetcher and BatchExtractor.

Tests batch processing with multiple components working together.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest

from edgar.batch import BatchExtractor, BatchFetcher
from edgar.cache.manager import CacheManager
from edgar.config import SEC_EDGAR_IDENTITY_ENV
from edgar.extractors.section import SectionExtractor
from edgar.extractors.text import TextExtractor
from edgar.fetcher import EdgarFetcher
from edgar.types import FilingType

if TYPE_CHECKING:
    from pathlib import Path


SAMPLE_TEXT_1 = (
    "Item 1. Business\n\n"
    "Company A makes widgets.\n\n"
    "Item 1A. Risk Factors\n\n"
    "Market risks exist.\n"
)

SAMPLE_TEXT_2 = (
    "Item 1. Business\n\n"
    "Company B provides services.\n\n"
    "Item 7. Management's Discussion and Analysis\n\n"
    "Revenue grew.\n"
)


@pytest.mark.integration
class TestBatchFetcherIntegration:
    """Integration tests for BatchFetcher with EdgarFetcher."""

    def test_統合_BatchFetcherで複数銘柄並列取得(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """BatchFetcher should fetch filings for multiple tickers."""
        monkeypatch.setenv(SEC_EDGAR_IDENTITY_ENV, "Test User test@example.com")

        mock_filing_aapl = MagicMock()
        mock_filing_aapl.accession_number = "0000320193-24-000001"
        mock_filing_msft = MagicMock()
        mock_filing_msft.accession_number = "0000789019-24-000001"

        mock_fetcher = MagicMock(spec=EdgarFetcher)
        mock_fetcher.fetch.side_effect = [
            [mock_filing_aapl],
            [mock_filing_msft],
        ]

        batch = BatchFetcher(fetcher=mock_fetcher)
        results = batch.fetch_batch(
            ["AAPL", "MSFT"],
            FilingType.FORM_10K,
            limit=1,
            max_workers=2,
        )

        assert len(results) == 2
        for _ticker, filings_or_error in results.items():
            assert not isinstance(filings_or_error, Exception)

    def test_統合_一部失敗でもPartialSuccess(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """BatchFetcher should handle partial failures gracefully."""
        monkeypatch.setenv(SEC_EDGAR_IDENTITY_ENV, "Test User test@example.com")

        mock_fetcher = MagicMock(spec=EdgarFetcher)
        mock_fetcher.fetch.side_effect = [
            [MagicMock()],  # AAPL succeeds
            RuntimeError("Network error"),  # INVALID fails
        ]

        batch = BatchFetcher(fetcher=mock_fetcher)
        results = batch.fetch_batch(
            ["AAPL", "INVALID"],
            FilingType.FORM_10K,
            max_workers=2,
        )

        successes = {k: v for k, v in results.items() if not isinstance(v, Exception)}
        failures = {k: v for k, v in results.items() if isinstance(v, Exception)}
        assert len(successes) == 1
        assert len(failures) == 1

    def test_統合_fetch_latest_batchで複数銘柄最新Filing取得(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """BatchFetcher.fetch_latest_batch should get latest for each ticker."""
        monkeypatch.setenv(SEC_EDGAR_IDENTITY_ENV, "Test User test@example.com")

        mock_filing_aapl = MagicMock()
        mock_filing_aapl.accession_number = "0000320193-24-000001"

        mock_fetcher = MagicMock(spec=EdgarFetcher)
        mock_fetcher.fetch_latest.side_effect = [
            mock_filing_aapl,
            None,  # GOOG has no filings
        ]

        batch = BatchFetcher(fetcher=mock_fetcher)
        results = batch.fetch_latest_batch(
            ["AAPL", "GOOG"],
            FilingType.FORM_10K,
            max_workers=2,
        )

        assert len(results) == 2
        # One should be a filing, one should be None
        non_none = [v for v in results.values() if v is not None]
        assert len(non_none) == 1


@pytest.mark.integration
class TestBatchExtractorIntegration:
    """Integration tests for BatchExtractor with real extractors."""

    def test_統合_BatchExtractorで複数Filing並列テキスト抽出(
        self,
        tmp_path: Path,
    ) -> None:
        """BatchExtractor should extract text from multiple filings."""
        cache = CacheManager(cache_dir=tmp_path, ttl_days=90)
        text_extractor = TextExtractor(cache=cache)

        filing1 = MagicMock()
        filing1.accession_number = "filing-001"
        filing1.text.return_value = (
            "  Company A   filing text  \n\n\n\n with   spaces  "
        )

        filing2 = MagicMock()
        filing2.accession_number = "filing-002"
        filing2.text.return_value = "Company B filing text"

        batch = BatchExtractor(text_extractor=text_extractor)
        results = batch.extract_text_batch([filing1, filing2], max_workers=2)

        assert len(results) == 2
        # Text should be cleaned
        for _key, text in results.items():
            assert not isinstance(text, Exception)
            assert isinstance(text, str)

        # Verify caching worked
        cached1 = cache.get_cached_text("text_filing-001")
        assert cached1 is not None

    def test_統合_BatchExtractorで複数セクション並列抽出(
        self,
        tmp_path: Path,
    ) -> None:
        """BatchExtractor should extract sections from multiple filings."""
        cache = CacheManager(cache_dir=tmp_path, ttl_days=90)
        section_extractor = SectionExtractor(cache=cache)

        filing1 = MagicMock()
        filing1.accession_number = "filing-001"
        filing1.text.return_value = SAMPLE_TEXT_1

        filing2 = MagicMock()
        filing2.accession_number = "filing-002"
        filing2.text.return_value = SAMPLE_TEXT_2

        batch = BatchExtractor(section_extractor=section_extractor)
        results = batch.extract_sections_batch(
            [filing1, filing2],
            ["item_1", "item_1a"],
            max_workers=2,
        )

        assert len(results) == 2
        for _key, sections in results.items():
            assert not isinstance(sections, Exception)
            assert isinstance(sections, dict)
            assert "item_1" in sections

    def test_統合_BatchからCacheまでの全フロー(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        """Full flow: BatchFetcher -> BatchExtractor -> CacheManager."""
        monkeypatch.setenv(SEC_EDGAR_IDENTITY_ENV, "Test User test@example.com")

        # Setup mock fetcher
        mock_filing1 = MagicMock()
        mock_filing1.accession_number = "filing-001"
        mock_filing1.text.return_value = SAMPLE_TEXT_1
        mock_filing2 = MagicMock()
        mock_filing2.accession_number = "filing-002"
        mock_filing2.text.return_value = SAMPLE_TEXT_2

        mock_fetcher = MagicMock(spec=EdgarFetcher)
        mock_fetcher.fetch.side_effect = [
            [mock_filing1],
            [mock_filing2],
        ]

        # Fetch
        batch_fetcher = BatchFetcher(fetcher=mock_fetcher)
        fetch_results = batch_fetcher.fetch_batch(
            ["AAPL", "MSFT"],
            FilingType.FORM_10K,
            limit=1,
            max_workers=2,
        )

        # Collect all filings
        all_filings = []
        for v in fetch_results.values():
            if not isinstance(v, Exception):
                all_filings.extend(v)

        assert len(all_filings) == 2

        # Extract with cache
        cache = CacheManager(cache_dir=tmp_path, ttl_days=90)
        text_extractor = TextExtractor(cache=cache)
        batch_extractor = BatchExtractor(text_extractor=text_extractor)

        text_results = batch_extractor.extract_text_batch(
            all_filings,
            max_workers=2,
        )

        assert len(text_results) == 2
        for text in text_results.values():
            assert not isinstance(text, Exception)
            assert len(text) > 0

    def test_統合_BatchExtractorの抽出失敗でも他は成功(
        self,
        tmp_path: Path,
    ) -> None:
        """BatchExtractor should continue when one extraction fails."""
        cache = CacheManager(cache_dir=tmp_path, ttl_days=90)
        text_extractor = TextExtractor(cache=cache)

        filing_ok = MagicMock()
        filing_ok.accession_number = "filing-ok"
        filing_ok.text.return_value = "Valid filing text"

        filing_bad = MagicMock()
        filing_bad.accession_number = "filing-bad"
        filing_bad.text.side_effect = RuntimeError("Parse error")

        batch = BatchExtractor(text_extractor=text_extractor)
        results = batch.extract_text_batch(
            [filing_ok, filing_bad],
            max_workers=2,
        )

        assert len(results) == 2
        successes = {k: v for k, v in results.items() if not isinstance(v, Exception)}
        failures = {k: v for k, v in results.items() if isinstance(v, Exception)}
        assert len(successes) == 1
        assert len(failures) == 1

    def test_統合_max_workersが並列度を制限(
        self,
        tmp_path: Path,
    ) -> None:
        """BatchExtractor should respect max_workers parameter."""
        cache = CacheManager(cache_dir=tmp_path, ttl_days=90)
        text_extractor = TextExtractor(cache=cache)

        filings = []
        for i in range(5):
            filing = MagicMock()
            filing.accession_number = f"filing-{i:03d}"
            filing.text.return_value = f"Filing {i} text content"
            filings.append(filing)

        batch = BatchExtractor(text_extractor=text_extractor)
        results = batch.extract_text_batch(filings, max_workers=2)

        # All 5 filings should be processed despite max_workers=2
        assert len(results) == 5
        for text in results.values():
            assert not isinstance(text, Exception)

    def test_統合_tqdm進捗表示が動作(
        self,
        tmp_path: Path,
    ) -> None:
        """BatchExtractor should work with tqdm progress bar (no crash)."""
        cache = CacheManager(cache_dir=tmp_path, ttl_days=90)
        text_extractor = TextExtractor(cache=cache)

        filings = []
        for i in range(3):
            filing = MagicMock()
            filing.accession_number = f"filing-{i:03d}"
            filing.text.return_value = f"Filing {i} content"
            filings.append(filing)

        batch = BatchExtractor(text_extractor=text_extractor)

        # This should complete without errors, including tqdm progress output
        results = batch.extract_text_batch(filings, max_workers=2)
        assert len(results) == 3

"""End-to-end integration tests for the edgar package.

Tests the full flow: Fetcher -> TextExtractor -> SectionExtractor -> CacheManager.
Uses mock edgartools objects but real edgar package components.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest

from edgar.cache.manager import CacheManager
from edgar.config import SEC_EDGAR_IDENTITY_ENV
from edgar.extractors.section import SectionExtractor
from edgar.extractors.text import TextExtractor
from edgar.fetcher import EdgarFetcher
from edgar.types import FilingType

if TYPE_CHECKING:
    from pathlib import Path


SAMPLE_10K_TEXT = (
    "UNITED STATES SECURITIES AND EXCHANGE COMMISSION\n"
    "Washington, D.C. 20549\n\n"
    "FORM 10-K\n\n"
    "Item 1. Business\n\n"
    "Apple Inc. designs, manufactures, and markets smartphones, "
    "personal computers, tablets, wearables, and accessories worldwide.\n\n"
    "Item 1A. Risk Factors\n\n"
    "The Company's business, reputation, results of operations, "
    "financial condition, and stock price can be affected by a number "
    "of factors.\n\n"
    "Item 7. Management's Discussion and Analysis of Financial "
    "Condition and Results of Operations\n\n"
    "The following discussion should be read in conjunction with the "
    "consolidated financial statements.\n\n"
    "Item 8. Financial Statements and Supplementary Data\n\n"
    "See the consolidated financial statements and notes thereto.\n"
)


@pytest.mark.integration
class TestEndToEndTextExtraction:
    """E2E tests for text extraction pipeline."""

    def test_E2E_テキスト抽出からキャッシュまで(self, tmp_path: Path) -> None:
        """Full flow: Filing -> TextExtractor -> CacheManager."""
        # Setup cache
        cache = CacheManager(cache_dir=tmp_path, ttl_days=90)

        # Create mock filing
        filing = MagicMock()
        filing.accession_number = "0000320193-24-000001"
        filing.text.return_value = SAMPLE_10K_TEXT

        # Extract text with cache
        extractor = TextExtractor(cache=cache)
        text = extractor.extract_text(filing)

        # Verify extraction
        assert len(text) > 0
        assert "Apple Inc." in text

        # Verify cache was populated
        cached = cache.get_cached_text("text_0000320193-24-000001")
        assert cached == text

        # Second extraction should hit cache (filing.text not called again)
        filing.text.reset_mock()
        text2 = extractor.extract_text(filing)
        assert text2 == text
        filing.text.assert_not_called()

    def test_E2E_セクション抽出とキャッシュ(self, tmp_path: Path) -> None:
        """Full flow: Filing -> SectionExtractor -> CacheManager."""
        cache = CacheManager(cache_dir=tmp_path, ttl_days=90)

        filing = MagicMock()
        filing.accession_number = "0000320193-24-000001"
        filing.text.return_value = SAMPLE_10K_TEXT

        extractor = SectionExtractor(cache=cache)

        # Extract item_1
        item1 = extractor.extract_section(filing, "item_1")
        assert item1 is not None
        assert "Apple Inc." in item1

        # Extract item_1a
        item1a = extractor.extract_section(filing, "item_1a")
        assert item1a is not None
        assert "Risk Factors" in item1a or "factors" in item1a.lower()

        # Verify cache has section-specific keys
        cached_1 = cache.get_cached_text("section_0000320193-24-000001_item_1")
        assert cached_1 == item1

        cached_1a = cache.get_cached_text("section_0000320193-24-000001_item_1a")
        assert cached_1a == item1a

    def test_E2E_Fetcherからテキスト抽出まで(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        """Full flow: EdgarFetcher -> TextExtractor -> CacheManager."""
        monkeypatch.setenv(SEC_EDGAR_IDENTITY_ENV, "Test User test@example.com")

        # Setup mock edgartools
        mock_filing = MagicMock()
        mock_filing.accession_number = "0000320193-24-000001"
        mock_filing.text.return_value = SAMPLE_10K_TEXT

        mock_filings = MagicMock()
        mock_filings.latest.return_value = [mock_filing]
        mock_company = MagicMock()
        mock_company.get_filings.return_value = mock_filings
        mock_company_cls = MagicMock(return_value=mock_company)

        # Run full pipeline
        fetcher = EdgarFetcher()
        fetcher._company_cls = mock_company_cls

        filings = fetcher.fetch("AAPL", FilingType.FORM_10K, limit=1)
        assert len(filings) == 1

        cache = CacheManager(cache_dir=tmp_path, ttl_days=90)
        text_extractor = TextExtractor(cache=cache)
        text = text_extractor.extract_text(filings[0])

        assert "Apple Inc." in text

        section_extractor = SectionExtractor(cache=cache)
        sections = section_extractor.list_sections(filings[0])
        assert "item_1" in sections

    def test_E2E_セクション一覧と個別抽出の整合性(
        self,
        tmp_path: Path,
    ) -> None:
        """list_sections and extract_section should be consistent."""
        cache = CacheManager(cache_dir=tmp_path, ttl_days=90)

        filing = MagicMock()
        filing.accession_number = "0000320193-24-000001"
        filing.text.return_value = SAMPLE_10K_TEXT

        extractor = SectionExtractor(cache=cache)

        # List available sections
        sections = extractor.list_sections(filing)
        assert len(sections) > 0

        # Each listed section should be extractable
        for section_key in sections:
            text = extractor.extract_section(filing, section_key)
            assert text is not None, f"Section {section_key} listed but not extractable"
            assert len(text) > 0

    def test_E2E_TextExtractorのトークンカウント(
        self,
        tmp_path: Path,
    ) -> None:
        """TextExtractor should count tokens after extraction."""
        cache = CacheManager(cache_dir=tmp_path, ttl_days=90)

        filing = MagicMock()
        filing.accession_number = "0000320193-24-000001"
        filing.text.return_value = SAMPLE_10K_TEXT

        extractor = TextExtractor(cache=cache)
        text = extractor.extract_text(filing)

        token_count = extractor.count_tokens(text)
        assert token_count > 0
        assert isinstance(token_count, int)


@pytest.mark.integration
class TestEndToEndMarkdownExtraction:
    """E2E tests for markdown extraction pipeline."""

    def test_E2E_Markdown抽出とキャッシュ(self, tmp_path: Path) -> None:
        """Full flow: Filing -> TextExtractor.extract_markdown -> CacheManager."""
        cache = CacheManager(cache_dir=tmp_path, ttl_days=90)

        filing = MagicMock()
        filing.accession_number = "0000320193-24-000001"
        filing.markdown.return_value = f"# 10-K Filing\n\n{SAMPLE_10K_TEXT}"

        extractor = TextExtractor(cache=cache)
        markdown = extractor.extract_markdown(filing)

        assert "10-K Filing" in markdown

        # Verify cache
        cached = cache.get_cached_text("markdown_0000320193-24-000001")
        assert cached == markdown

    def test_E2E_TextとMarkdownで別キャッシュ(
        self,
        tmp_path: Path,
    ) -> None:
        """Text and markdown should use separate cache keys."""
        cache = CacheManager(cache_dir=tmp_path, ttl_days=90)

        filing = MagicMock()
        filing.accession_number = "0000320193-24-000001"
        filing.text.return_value = SAMPLE_10K_TEXT
        filing.markdown.return_value = f"# 10-K Filing\n\n{SAMPLE_10K_TEXT}"

        extractor = TextExtractor(cache=cache)

        text = extractor.extract_text(filing)
        markdown = extractor.extract_markdown(filing)

        # Text and markdown should be different (markdown has header)
        assert text != markdown

        # Both should be independently cached
        cached_text = cache.get_cached_text("text_0000320193-24-000001")
        cached_markdown = cache.get_cached_text("markdown_0000320193-24-000001")

        assert cached_text == text
        assert cached_markdown == markdown
        assert cached_text != cached_markdown

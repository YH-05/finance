"""Unit tests for edgar.extractors.section module.

Tests for SectionExtractor class and helper functions for
section-level text extraction from SEC EDGAR filings.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from edgar.extractors._helpers import get_accession_number, get_filing_text
from edgar.extractors.section import (
    SECTION_PATTERNS,
    SectionExtractor,
    _build_cache_key,
    _extract_section_text,
    _find_section_positions,
)

# Sample filing text that mimics a real 10-K filing structure.
SAMPLE_FILING_TEXT = (
    "HEADER CONTENT\n\n"
    "Item 1. Business\n\n"
    "We are a technology company.\n\n"
    "Item 1A. Risk Factors\n\n"
    "Our business faces various risks.\n\n"
    "Item 7. Management's Discussion and Analysis\n\n"
    "Revenue increased year over year.\n\n"
    "Item 8. Financial Statements and Supplementary Data\n\n"
    "See notes to financial statements.\n"
)


class TestGetFilingText:
    """Tests for get_filing_text helper function."""

    def test_正常系_text_methodでテキスト取得(self) -> None:
        """get_filing_text should use text() method first."""
        filing = MagicMock()
        filing.text.return_value = "Filing text from text()"

        result = get_filing_text(filing)

        assert result == "Filing text from text()"

    def test_正常系_full_text属性でテキスト取得(self) -> None:
        """get_filing_text should fall back to full_text attribute."""
        filing = MagicMock(spec=["full_text"])
        filing.full_text = "Filing text from full_text"

        result = get_filing_text(filing)

        assert result == "Filing text from full_text"

    def test_正常系_obj_methodでテキスト取得(self) -> None:
        """get_filing_text should fall back to obj() method."""
        filing = MagicMock(spec=["obj"])
        filing.obj.return_value = "Filing text from obj()"

        result = get_filing_text(filing)

        assert result == "Filing text from obj()"

    def test_エッジケース_テキスト取得不可でNone(self) -> None:
        """get_filing_text should return None when no method is available."""
        filing = MagicMock(spec=[])

        result = get_filing_text(filing)

        assert result is None

    def test_エッジケース_text_methodが空文字列の場合fallback(self) -> None:
        """get_filing_text should fall back when text() returns empty string."""
        filing = MagicMock()
        filing.text.return_value = ""
        filing.full_text = "Fallback text"

        result = get_filing_text(filing)

        assert result == "Fallback text"

    def test_エッジケース_例外発生時にNone(self) -> None:
        """get_filing_text should return None when an exception occurs."""
        filing = MagicMock()
        filing.text.side_effect = RuntimeError("Unexpected error")
        # Make hasattr return True for text, but the call raises
        # MagicMock hasattr returns True by default, text is callable

        result = get_filing_text(filing)

        assert result is None


class TestGetAccessionNumber:
    """Tests for get_accession_number helper function."""

    def test_正常系_accession_numberから取得(self) -> None:
        """get_accession_number should return accession_number attribute."""
        filing = MagicMock()
        filing.accession_number = "0001234567-24-000001"

        result = get_accession_number(filing)

        assert result == "0001234567-24-000001"

    def test_正常系_accession_noから取得(self) -> None:
        """get_accession_number should fall back to accession_no attribute."""
        filing = MagicMock(spec=["accession_no"])
        filing.accession_no = "0001234567-24-000001"

        result = get_accession_number(filing)

        assert result == "0001234567-24-000001"

    def test_エッジケース_属性なしでNone(self) -> None:
        """get_accession_number should return None when no attribute exists."""
        filing = MagicMock(spec=[])

        result = get_accession_number(filing)

        assert result is None


class TestBuildCacheKey:
    """Tests for _build_cache_key helper function."""

    def test_正常系_セクションキャッシュキー生成(self) -> None:
        """Cache key should be formatted as section_accession_section_key."""
        result = _build_cache_key("0001234567-24-000001", "item_1")

        assert result == "section_0001234567-24-000001_item_1"


class TestFindSectionPositions:
    """Tests for _find_section_positions helper function."""

    def test_正常系_全セクションを検出(self) -> None:
        """_find_section_positions should find all 4 known sections."""
        positions = _find_section_positions(SAMPLE_FILING_TEXT)

        assert "item_1" in positions
        assert "item_1a" in positions
        assert "item_7" in positions
        assert "item_8" in positions

    def test_正常系_セクション位置が昇順(self) -> None:
        """Section positions should be in ascending order."""
        positions = _find_section_positions(SAMPLE_FILING_TEXT)

        assert positions["item_1"] < positions["item_1a"]
        assert positions["item_1a"] < positions["item_7"]
        assert positions["item_7"] < positions["item_8"]

    def test_エッジケース_セクションなしで空dict(self) -> None:
        """_find_section_positions should return empty dict for no sections."""
        positions = _find_section_positions("Plain text without sections.")

        assert positions == {}

    def test_正常系_大文字小文字を無視して検出(self) -> None:
        """_find_section_positions should match case-insensitively."""
        text = "ITEM 1. BUSINESS\n\nContent here."
        positions = _find_section_positions(text)

        assert "item_1" in positions

    def test_正常系_一部セクションのみ存在(self) -> None:
        """_find_section_positions should find only present sections."""
        text = "Item 1. Business\n\nSome content\n\nItem 7. Management's Discussion\n\n"
        positions = _find_section_positions(text)

        assert "item_1" in positions
        assert "item_7" in positions
        assert "item_1a" not in positions
        assert "item_8" not in positions


class TestExtractSectionText:
    """Tests for _extract_section_text helper function."""

    def test_正常系_Item1セクション抽出(self) -> None:
        """_extract_section_text should extract Item 1 section text."""
        positions = _find_section_positions(SAMPLE_FILING_TEXT)
        text = _extract_section_text(SAMPLE_FILING_TEXT, "item_1", positions)

        assert text is not None
        assert "technology company" in text
        assert "Risk Factors" not in text  # should stop before next section

    def test_正常系_最後のセクション抽出(self) -> None:
        """_extract_section_text should extract the last section to end of text."""
        positions = _find_section_positions(SAMPLE_FILING_TEXT)
        text = _extract_section_text(SAMPLE_FILING_TEXT, "item_8", positions)

        assert text is not None
        assert "financial statements" in text

    def test_異常系_存在しないセクションでNone(self) -> None:
        """_extract_section_text should return None for a missing section."""
        text = _extract_section_text(SAMPLE_FILING_TEXT, "item_99", {})

        assert text is None

    def test_エッジケース_位置情報にないセクションキーでNone(self) -> None:
        """_extract_section_text returns None when key is not in positions."""
        positions = {"item_1": 0}
        text = _extract_section_text(SAMPLE_FILING_TEXT, "item_7", positions)

        assert text is None


class TestSectionExtractor:
    """Tests for SectionExtractor class."""

    def test_正常系_Item1セクション抽出成功(self) -> None:
        """extract_section should extract Item 1 text."""
        filing = MagicMock()
        filing.accession_number = "0001234567-24-000001"
        filing.text.return_value = SAMPLE_FILING_TEXT

        extractor = SectionExtractor()
        result = extractor.extract_section(filing, "item_1")

        assert result is not None
        assert "technology company" in result

    def test_正常系_Item1Aセクション抽出成功(self) -> None:
        """extract_section should extract Item 1A text."""
        filing = MagicMock()
        filing.accession_number = "0001234567-24-000001"
        filing.text.return_value = SAMPLE_FILING_TEXT

        extractor = SectionExtractor()
        result = extractor.extract_section(filing, "item_1a")

        assert result is not None
        assert "risks" in result

    def test_正常系_Item7セクション抽出成功(self) -> None:
        """extract_section should extract Item 7 text."""
        filing = MagicMock()
        filing.accession_number = "0001234567-24-000001"
        filing.text.return_value = SAMPLE_FILING_TEXT

        extractor = SectionExtractor()
        result = extractor.extract_section(filing, "item_7")

        assert result is not None
        assert "Revenue" in result

    def test_正常系_list_sectionsで一覧取得(self) -> None:
        """list_sections should return all found section keys."""
        filing = MagicMock()
        filing.text.return_value = SAMPLE_FILING_TEXT

        extractor = SectionExtractor()
        sections = extractor.list_sections(filing)

        assert "item_1" in sections
        assert "item_1a" in sections
        assert "item_7" in sections
        assert "item_8" in sections

    def test_正常系_list_sectionsは正規順序で返却(self) -> None:
        """list_sections should return keys in canonical order."""
        filing = MagicMock()
        filing.text.return_value = SAMPLE_FILING_TEXT

        extractor = SectionExtractor()
        sections = extractor.list_sections(filing)

        expected_order = ["item_1", "item_1a", "item_7", "item_8"]
        assert sections == expected_order

    def test_正常系_キャッシュヒットで再抽出しない(self) -> None:
        """extract_section should return cached result without extraction."""
        mock_cache = MagicMock()
        mock_cache.get_cached_text.return_value = "Cached section text"

        filing = MagicMock()
        filing.accession_number = "0001234567-24-000001"

        extractor = SectionExtractor(cache=mock_cache)
        result = extractor.extract_section(filing, "item_1")

        assert result == "Cached section text"
        filing.text.assert_not_called()

    def test_正常系_キャッシュミス時はキャッシュに保存(self) -> None:
        """extract_section should save to cache on cache miss."""
        mock_cache = MagicMock()
        mock_cache.get_cached_text.return_value = None

        filing = MagicMock()
        filing.accession_number = "0001234567-24-000001"
        filing.text.return_value = SAMPLE_FILING_TEXT

        extractor = SectionExtractor(cache=mock_cache)
        extractor.extract_section(filing, "item_1")

        mock_cache.save_text.assert_called_once()

    def test_異常系_不明なセクションキーでNone(self) -> None:
        """extract_section should return None for unknown section key."""
        filing = MagicMock()

        extractor = SectionExtractor()
        result = extractor.extract_section(filing, "item_99_unknown")

        assert result is None

    def test_エッジケース_セクション0件で空リスト(self) -> None:
        """list_sections should return empty list when no sections found."""
        filing = MagicMock()
        filing.text.return_value = "Plain text without section headers."

        extractor = SectionExtractor()
        sections = extractor.list_sections(filing)

        assert sections == []

    def test_エッジケース_テキスト取得不可でNone(self) -> None:
        """extract_section should return None when text extraction fails."""
        filing = MagicMock(spec=["accession_number"])
        filing.accession_number = "0001234567-24-000001"

        extractor = SectionExtractor()
        result = extractor.extract_section(filing, "item_1")

        assert result is None

    def test_エッジケース_テキスト取得不可でlist_sectionsは空リスト(self) -> None:
        """list_sections should return empty list when text extraction fails."""
        filing = MagicMock(spec=[])

        extractor = SectionExtractor()
        sections = extractor.list_sections(filing)

        assert sections == []

    def test_エッジケース_キャッシュ書き込みエラーは無視(self) -> None:
        """extract_section should succeed even if cache write fails."""
        mock_cache = MagicMock()
        mock_cache.get_cached_text.return_value = None
        mock_cache.save_text.side_effect = RuntimeError("Cache write error")

        filing = MagicMock()
        filing.accession_number = "0001234567-24-000001"
        filing.text.return_value = SAMPLE_FILING_TEXT

        extractor = SectionExtractor(cache=mock_cache)
        result = extractor.extract_section(filing, "item_1")

        assert result is not None
        assert "technology company" in result

    def test_正常系_reprはキャッシュ状態を表示(self) -> None:
        """__repr__ should show cache enabled status."""
        extractor_no_cache = SectionExtractor()
        assert "cache_enabled=False" in repr(extractor_no_cache)

        extractor_with_cache = SectionExtractor(cache=MagicMock())
        assert "cache_enabled=True" in repr(extractor_with_cache)

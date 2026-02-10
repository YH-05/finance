"""Unit tests for edgar.extractors.text module.

Tests for TextExtractor class and _clean_text helper function.
Covers text extraction, markdown extraction, token counting,
caching behavior, and error handling.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from edgar.errors import EdgarError
from edgar.extractors.text import TextExtractor, _build_cache_key, _clean_text


class TestCleanText:
    """Tests for _clean_text helper function."""

    def test_正常系_連続空白を1つに統一(self) -> None:
        """Consecutive spaces should be collapsed to a single space."""
        result = _clean_text("hello    world")
        assert result == "hello world"

    def test_正常系_タブを空白に変換(self) -> None:
        """Tabs should be collapsed to a single space."""
        result = _clean_text("hello\t\tworld")
        assert result == "hello world"

    def test_正常系_3つ以上の改行を2つに統一(self) -> None:
        """Three or more consecutive newlines should be collapsed to two."""
        result = _clean_text("paragraph1\n\n\n\nparagraph2")
        assert result == "paragraph1\n\nparagraph2"

    def test_正常系_先頭末尾の空白を除去(self) -> None:
        """Leading and trailing whitespace should be stripped."""
        result = _clean_text("  hello world  ")
        assert result == "hello world"

    def test_正常系_複合的なクリーニング(self) -> None:
        """Multiple cleaning rules should be applied together."""
        # Spaces adjacent to newlines become single spaces (not removed),
        # but leading/trailing whitespace of the entire string is stripped.
        result = _clean_text("  Hello    world  \n\n\n\n  foo  ")
        assert result == "Hello world \n\n foo"

    def test_エッジケース_空文字列で空文字列(self) -> None:
        """Empty string input should return empty string."""
        result = _clean_text("")
        assert result == ""

    def test_エッジケース_改行のみで空文字列(self) -> None:
        """Input with only newlines should return empty string."""
        result = _clean_text("\n\n\n")
        assert result == ""

    def test_エッジケース_2つの改行はそのまま(self) -> None:
        """Exactly two consecutive newlines should be preserved."""
        result = _clean_text("para1\n\npara2")
        assert result == "para1\n\npara2"

    def test_エッジケース_1つの改行はそのまま(self) -> None:
        """A single newline should be preserved."""
        result = _clean_text("line1\nline2")
        assert result == "line1\nline2"


class TestBuildCacheKey:
    """Tests for _build_cache_key helper function."""

    def test_正常系_プレフィクスとアクセッション番号でキー生成(self) -> None:
        """Cache key should be formatted as prefix_accession_number."""
        result = _build_cache_key("text", "0001234567-24-000001")
        assert result == "text_0001234567-24-000001"

    def test_正常系_markdownプレフィクスでキー生成(self) -> None:
        """Cache key should work with markdown prefix."""
        result = _build_cache_key("markdown", "0001234567-24-000001")
        assert result == "markdown_0001234567-24-000001"


class TestTextExtractor:
    """Tests for TextExtractor class."""

    def test_正常系_filing_textからクリーンテキスト抽出(self) -> None:
        """extract_text should return cleaned text from filing.text()."""
        filing = MagicMock()
        filing.accession_number = "0001234567-24-000001"
        filing.text.return_value = "Hello    world\n\n\n\nfoo"

        extractor = TextExtractor()
        result = extractor.extract_text(filing)

        assert result == "Hello world\n\nfoo"
        filing.text.assert_called_once()

    def test_正常系_filing_markdownからMarkdown抽出(self) -> None:
        """extract_markdown should return cleaned markdown from filing.markdown()."""
        filing = MagicMock()
        filing.accession_number = "0001234567-24-000001"
        filing.markdown.return_value = "# Title\n\n\n\nContent"

        extractor = TextExtractor()
        result = extractor.extract_markdown(filing)

        assert result == "# Title\n\nContent"
        filing.markdown.assert_called_once()

    def test_正常系_count_tokensでトークン数カウント(self) -> None:
        """count_tokens should return a positive integer for non-empty text."""
        extractor = TextExtractor()
        count = extractor.count_tokens("Hello, world!")

        assert isinstance(count, int)
        assert count > 0

    def test_正常系_count_tokensで空文字列は0(self) -> None:
        """count_tokens should return 0 for empty string."""
        extractor = TextExtractor()
        count = extractor.count_tokens("")

        assert count == 0

    def test_正常系_キャッシュヒット時は再抽出しない(self) -> None:
        """extract_text should return cached text without calling filing.text()."""
        mock_cache = MagicMock()
        mock_cache.get_cached_text.return_value = "Cached text"

        filing = MagicMock()
        filing.accession_number = "0001234567-24-000001"

        extractor = TextExtractor(cache=mock_cache)
        result = extractor.extract_text(filing)

        assert result == "Cached text"
        filing.text.assert_not_called()

    def test_正常系_キャッシュミス時はキャッシュに保存(self) -> None:
        """extract_text should save to cache on cache miss."""
        mock_cache = MagicMock()
        mock_cache.get_cached_text.return_value = None

        filing = MagicMock()
        filing.accession_number = "0001234567-24-000001"
        filing.text.return_value = "Filing text"

        extractor = TextExtractor(cache=mock_cache)
        extractor.extract_text(filing)

        mock_cache.save_text.assert_called_once()

    def test_正常系_markdownもキャッシュから取得(self) -> None:
        """extract_markdown should return cached markdown on cache hit."""
        mock_cache = MagicMock()
        mock_cache.get_cached_text.return_value = "Cached markdown"

        filing = MagicMock()
        filing.accession_number = "0001234567-24-000001"

        extractor = TextExtractor(cache=mock_cache)
        result = extractor.extract_markdown(filing)

        assert result == "Cached markdown"
        filing.markdown.assert_not_called()

    def test_異常系_filing_textエラーでEdgarError(self) -> None:
        """extract_text should raise EdgarError when filing.text() fails."""
        filing = MagicMock()
        filing.accession_number = "0001234567-24-000001"
        filing.text.side_effect = RuntimeError("Network error")

        extractor = TextExtractor()
        with pytest.raises(EdgarError, match="Failed to extract text"):
            extractor.extract_text(filing)

    def test_異常系_filing_markdownエラーでEdgarError(self) -> None:
        """extract_markdown should raise EdgarError when filing.markdown() fails."""
        filing = MagicMock()
        filing.accession_number = "0001234567-24-000001"
        filing.markdown.side_effect = RuntimeError("Network error")

        extractor = TextExtractor()
        with pytest.raises(EdgarError, match="Failed to extract markdown"):
            extractor.extract_markdown(filing)

    def test_異常系_accession_number欠落でEdgarError(self) -> None:
        """extract_text should raise EdgarError when accession_number is missing."""
        filing = MagicMock(spec=[])  # no attributes

        extractor = TextExtractor()
        with pytest.raises(EdgarError, match="accession_number"):
            extractor.extract_text(filing)

    def test_エッジケース_空テキストで空文字列返却(self) -> None:
        """extract_text should return empty string for empty filing text."""
        filing = MagicMock()
        filing.accession_number = "0001234567-24-000001"
        filing.text.return_value = ""

        extractor = TextExtractor()
        result = extractor.extract_text(filing)

        assert result == ""

    def test_エッジケース_キャッシュ読み取りエラーは無視(self) -> None:
        """extract_text should proceed without cache if cache read fails."""
        mock_cache = MagicMock()
        mock_cache.get_cached_text.side_effect = RuntimeError("Cache read error")

        filing = MagicMock()
        filing.accession_number = "0001234567-24-000001"
        filing.text.return_value = "Filing text"

        extractor = TextExtractor(cache=mock_cache)
        result = extractor.extract_text(filing)

        assert result == "Filing text"
        filing.text.assert_called_once()

    def test_エッジケース_キャッシュ書き込みエラーは無視(self) -> None:
        """extract_text should succeed even if cache write fails."""
        mock_cache = MagicMock()
        mock_cache.get_cached_text.return_value = None
        mock_cache.save_text.side_effect = RuntimeError("Cache write error")

        filing = MagicMock()
        filing.accession_number = "0001234567-24-000001"
        filing.text.return_value = "Filing text"

        extractor = TextExtractor(cache=mock_cache)
        result = extractor.extract_text(filing)

        assert result == "Filing text"

    def test_正常系_reprはキャッシュ状態を表示(self) -> None:
        """__repr__ should show cache enabled status."""
        extractor_no_cache = TextExtractor()
        assert "cache_enabled=False" in repr(extractor_no_cache)

        extractor_with_cache = TextExtractor(cache=MagicMock())
        assert "cache_enabled=True" in repr(extractor_with_cache)

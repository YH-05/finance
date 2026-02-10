"""Unit tests for edgar.extractors._helpers module.

Tests for shared helper functions: get_accession_number and get_filing_text.
These functions are used by both TextExtractor and SectionExtractor.
"""

from __future__ import annotations

from unittest.mock import MagicMock

from edgar.extractors._helpers import get_accession_number, get_filing_text


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

    def test_エッジケース_例外発生時にNone(self) -> None:
        """get_accession_number should return None on exception."""
        filing = MagicMock()
        type(filing).accession_number = property(
            lambda self: (_ for _ in ()).throw(RuntimeError("attr error"))
        )

        result = get_accession_number(filing)

        assert result is None

    def test_正常系_数値を文字列に変換(self) -> None:
        """get_accession_number should convert non-string values to str."""
        filing = MagicMock()
        filing.accession_number = 12345

        result = get_accession_number(filing)

        assert result == "12345"
        assert isinstance(result, str)


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

        result = get_filing_text(filing)

        assert result is None

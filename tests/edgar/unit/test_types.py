"""Unit tests for edgar.types module.

Tests for FilingType, SectionKey enums and EdgarResult dataclass.
"""

from datetime import datetime

import pytest

from edgar.types import EdgarResult, FilingType, SectionKey


class TestFilingType:
    """Tests for FilingType enum."""

    def test_正常系_FilingTypeはすべての値を持つ(self) -> None:
        """FilingType enum should have all expected form types.

        Verify that FilingType enum contains FORM_10K, FORM_10Q, and FORM_13F.
        """
        assert hasattr(FilingType, "FORM_10K")
        assert hasattr(FilingType, "FORM_10Q")
        assert hasattr(FilingType, "FORM_13F")

        assert FilingType.FORM_10K.value == "10-K"
        assert FilingType.FORM_10Q.value == "10-Q"
        assert FilingType.FORM_13F.value == "13F"

    def test_正常系_from_stringで10Kを変換できる(self) -> None:
        """from_string() should convert '10-K' to FORM_10K.

        Verify that FilingType.from_string() correctly converts
        the string '10-K' to FilingType.FORM_10K.
        """
        result = FilingType.from_string("10-K")
        assert result == FilingType.FORM_10K

    def test_正常系_from_stringで10Qを変換できる(self) -> None:
        """from_string() should convert '10-Q' to FORM_10Q.

        Verify that FilingType.from_string() correctly converts
        the string '10-Q' to FilingType.FORM_10Q.
        """
        result = FilingType.from_string("10-Q")
        assert result == FilingType.FORM_10Q

    def test_正常系_from_stringで13Fを変換できる(self) -> None:
        """from_string() should convert '13F' to FORM_13F.

        Verify that FilingType.from_string() correctly converts
        the string '13F' to FilingType.FORM_13F.
        """
        result = FilingType.from_string("13F")
        assert result == FilingType.FORM_13F

    def test_異常系_from_stringで不正な文字列でValueError(self) -> None:
        """from_string() should raise ValueError for invalid form type.

        Verify that FilingType.from_string() raises ValueError
        when given an unsupported form type string.
        """
        with pytest.raises(ValueError, match="Unsupported filing type"):
            FilingType.from_string("INVALID")


class TestSectionKey:
    """Tests for SectionKey enum."""

    def test_正常系_SectionKeyはすべての値を持つ(self) -> None:
        """SectionKey enum should have all expected section keys.

        Verify that SectionKey enum contains ITEM_1, ITEM_1A, ITEM_7, ITEM_8.
        """
        assert hasattr(SectionKey, "ITEM_1")
        assert hasattr(SectionKey, "ITEM_1A")
        assert hasattr(SectionKey, "ITEM_7")
        assert hasattr(SectionKey, "ITEM_8")

        assert SectionKey.ITEM_1.value == "item_1"
        assert SectionKey.ITEM_1A.value == "item_1a"
        assert SectionKey.ITEM_7.value == "item_7"
        assert SectionKey.ITEM_8.value == "item_8"


class TestEdgarResult:
    """Tests for EdgarResult dataclass."""

    def test_正常系_EdgarResultは全フィールドを持つ(self) -> None:
        """EdgarResult should have all expected fields.

        Verify that EdgarResult dataclass can be instantiated with
        filing_id, text, sections, and metadata fields.
        """
        fetched_at = datetime.now()
        result = EdgarResult(
            filing_id="0001234567-24-000001",
            text="Full filing text content",
            sections={SectionKey.ITEM_1: "Business section text"},
            metadata={"company": "Example Corp", "fetched_at": fetched_at},
        )

        assert result.filing_id == "0001234567-24-000001"
        assert result.text == "Full filing text content"
        assert result.sections == {SectionKey.ITEM_1: "Business section text"}
        assert result.metadata == {"company": "Example Corp", "fetched_at": fetched_at}

    def test_正常系_EdgarResultはデフォルト値を持つ(self) -> None:
        """EdgarResult should use default values for optional fields.

        Verify that sections and metadata have proper default values
        when not provided.
        """
        result = EdgarResult(
            filing_id="0001234567-24-000001",
            text="Full filing text content",
        )

        assert result.sections == {}
        assert result.metadata == {}

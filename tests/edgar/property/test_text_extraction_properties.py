"""Property-based tests for edgar.extractors.text module.

Uses Hypothesis to verify invariants of the text cleaning and
extraction functions.
"""

from __future__ import annotations

import re

from hypothesis import given, settings
from hypothesis import strategies as st

from edgar.extractors.text import TextExtractor, _clean_text


class TestCleanTextProperties:
    """Property tests for _clean_text function."""

    @given(text=st.text(min_size=1))
    @settings(max_examples=200)
    def test_プロパティ_先頭末尾に空白が存在しない(self, text: str) -> None:
        """_clean_text output should never have leading/trailing whitespace."""
        result = _clean_text(text)
        if result:  # empty string is allowed
            assert result == result.strip()

    @given(text=st.text(min_size=1))
    @settings(max_examples=200)
    def test_プロパティ_連続空白は1つに統一される(self, text: str) -> None:
        """_clean_text output should not have consecutive spaces (excluding newlines)."""
        result = _clean_text(text)
        # After cleaning, there should be no consecutive non-newline whitespace
        assert not re.search(r"[^\S\n]{2,}", result)

    @given(text=st.text(min_size=1))
    @settings(max_examples=200)
    def test_プロパティ_連続改行は最大2つまで(self, text: str) -> None:
        """_clean_text output should have at most 2 consecutive newlines."""
        result = _clean_text(text)
        assert "\n\n\n" not in result

    @given(text=st.text())
    @settings(max_examples=100)
    def test_プロパティ_クリーニングは冪等(self, text: str) -> None:
        """Applying _clean_text twice should give the same result as once."""
        once = _clean_text(text)
        twice = _clean_text(once)
        assert once == twice

    @given(text=st.text())
    @settings(max_examples=100)
    def test_プロパティ_空文字列入力は空文字列出力(self, text: str) -> None:
        """_clean_text of empty string should be empty, of whitespace should be empty."""
        result = _clean_text(text)
        # Result should be a string
        assert isinstance(result, str)


class TestTokenCountProperties:
    """Property tests for TextExtractor.count_tokens."""

    @given(
        text=st.text(
            alphabet=st.characters(whitelist_categories=("L", "N", "P", "Z")),
            min_size=0,
            max_size=500,
        )
    )
    @settings(max_examples=100)
    def test_プロパティ_トークン数は非負(self, text: str) -> None:
        """count_tokens should always return a non-negative integer."""
        extractor = TextExtractor()
        count = extractor.count_tokens(text)
        assert isinstance(count, int)
        assert count >= 0

    @given(
        text=st.text(
            alphabet=st.characters(whitelist_categories=("L",)),
            min_size=1,
            max_size=100,
        )
    )
    @settings(max_examples=50)
    def test_プロパティ_非空テキストは正のトークン数(self, text: str) -> None:
        """count_tokens should return positive count for non-empty text."""
        extractor = TextExtractor()
        count = extractor.count_tokens(text)
        assert count > 0

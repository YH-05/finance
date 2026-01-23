"""Property-based tests for news categorizer module."""

from hypothesis import given, settings
from hypothesis import strategies as st

from rss.services.news_categorizer import (
    CategorizationResult,
    NewsCategorizer,
    NewsCategory,
)


class TestNewsCategorizer:
    """Property-based tests for NewsCategorizer."""

    @given(
        title=st.text(min_size=0, max_size=500),
        content=st.text(min_size=0, max_size=2000),
    )
    @settings(max_examples=100)
    def test_プロパティ_任意の入力に対して有効なカテゴリを返す(
        self,
        title: str,
        content: str,
    ) -> None:
        """Any input should return a valid NewsCategory."""
        categorizer = NewsCategorizer()
        result = categorizer.categorize(title=title, content=content)

        # Result should be a CategorizationResult
        assert isinstance(result, CategorizationResult)
        # Category should be a valid NewsCategory
        assert result.category in NewsCategory
        # Confidence should be between 0 and 1
        assert 0.0 <= result.confidence <= 1.0
        # matched_keywords should be a list
        assert isinstance(result.matched_keywords, list)

    @given(
        items=st.lists(
            st.fixed_dictionaries(
                {
                    "title": st.text(min_size=0, max_size=200),
                    "content": st.text(min_size=0, max_size=500),
                }
            ),
            min_size=0,
            max_size=50,
        )
    )
    @settings(max_examples=50)
    def test_プロパティ_バッチ処理が入力数と同じ結果を返す(
        self,
        items: list[dict[str, str]],
    ) -> None:
        """Batch categorization should return same number of results as inputs."""
        categorizer = NewsCategorizer()
        results = categorizer.categorize_batch(items)

        assert len(results) == len(items)
        for result in results:
            assert isinstance(result, CategorizationResult)
            assert result.category in NewsCategory

    @given(
        title=st.text(min_size=1, max_size=200),
        content=st.text(min_size=0, max_size=500),
    )
    @settings(max_examples=50)
    def test_プロパティ_大文字小文字変換しても結果が同じ(
        self,
        title: str,
        content: str,
    ) -> None:
        """Case conversion should not change the category result."""
        categorizer = NewsCategorizer()
        result_original = categorizer.categorize(title=title, content=content)
        result_upper = categorizer.categorize(
            title=title.upper(), content=content.upper()
        )
        result_lower = categorizer.categorize(
            title=title.lower(), content=content.lower()
        )

        assert result_original.category == result_upper.category
        assert result_original.category == result_lower.category

    @given(
        title=st.text(min_size=0, max_size=200),
        content=st.text(min_size=0, max_size=500),
    )
    @settings(max_examples=50)
    def test_プロパティ_同じ入力で同じ結果を返す_冪等性(
        self,
        title: str,
        content: str,
    ) -> None:
        """Same input should always produce same output (idempotency)."""
        categorizer = NewsCategorizer()
        result1 = categorizer.categorize(title=title, content=content)
        result2 = categorizer.categorize(title=title, content=content)

        assert result1.category == result2.category
        assert result1.confidence == result2.confidence
        assert result1.matched_keywords == result2.matched_keywords

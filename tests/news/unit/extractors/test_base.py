"""Unit tests for BaseExtractor ABC.

This module tests the BaseExtractor abstract base class to ensure:
- It cannot be instantiated directly
- Concrete implementations must implement extractor_name property
- Concrete implementations must implement extract() method
- The extract_batch() method correctly handles parallel extraction
"""

import asyncio
from abc import ABC
from datetime import datetime, timezone

import pytest
from news.extractors.base import BaseExtractor
from news.models import (
    ArticleSource,
    CollectedArticle,
    ExtractedArticle,
    ExtractionStatus,
    SourceType,
)


@pytest.fixture
def sample_collected_article() -> CollectedArticle:
    """Create a sample CollectedArticle for testing."""
    return CollectedArticle(
        url="https://www.cnbc.com/article/123",  # type: ignore[arg-type]
        title="Test Article",
        published=datetime(2025, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
        raw_summary="This is a test summary",
        source=ArticleSource(
            source_type=SourceType.RSS,
            source_name="CNBC Markets",
            category="market",
        ),
        collected_at=datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc),
    )


@pytest.fixture
def sample_collected_articles() -> list[CollectedArticle]:
    """Create multiple sample CollectedArticles for testing."""
    return [
        CollectedArticle(
            url=f"https://www.cnbc.com/article/{i}",  # type: ignore[arg-type]
            title=f"Test Article {i}",
            published=datetime(2025, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
            raw_summary=f"This is test summary {i}",
            source=ArticleSource(
                source_type=SourceType.RSS,
                source_name="CNBC Markets",
                category="market",
            ),
            collected_at=datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc),
        )
        for i in range(5)
    ]


class TestBaseExtractorDefinition:
    """Tests for BaseExtractor class definition."""

    def test_正常系_BaseExtractorはABCを継承している(self) -> None:
        """BaseExtractor should inherit from ABC."""
        assert issubclass(BaseExtractor, ABC)

    def test_異常系_BaseExtractorは直接インスタンス化できない(self) -> None:
        """BaseExtractor cannot be instantiated directly."""
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            BaseExtractor()  # type: ignore[abstract]


class TestBaseExtractorAbstractMethods:
    """Tests for BaseExtractor abstract methods."""

    def test_正常系_extractor_nameプロパティが抽象プロパティとして定義されている(
        self,
    ) -> None:
        """extractor_name should be defined as an abstract property."""
        assert hasattr(BaseExtractor, "extractor_name")
        # Check it's an abstract property by checking __abstractmethods__
        assert "extractor_name" in BaseExtractor.__abstractmethods__

    def test_正常系_extractメソッドが抽象メソッドとして定義されている(self) -> None:
        """extract should be defined as an abstract method."""
        assert hasattr(BaseExtractor, "extract")
        assert "extract" in BaseExtractor.__abstractmethods__

    def test_正常系_extract_batchメソッドが具象メソッドとして定義されている(
        self,
    ) -> None:
        """extract_batch should be defined as a concrete method."""
        assert hasattr(BaseExtractor, "extract_batch")
        # extract_batch is NOT abstract - it's a concrete method
        assert "extract_batch" not in BaseExtractor.__abstractmethods__


class TestConcreteExtractorImplementation:
    """Tests for concrete implementations of BaseExtractor."""

    def test_正常系_具象クラスはextractor_nameを実装できる(self) -> None:
        """Concrete class can implement extractor_name property."""

        class TrafilaturaExtractor(BaseExtractor):
            @property
            def extractor_name(self) -> str:
                return "trafilatura"

            async def extract(self, article: CollectedArticle) -> ExtractedArticle:
                return ExtractedArticle(
                    collected=article,
                    body_text="Extracted text",
                    extraction_status=ExtractionStatus.SUCCESS,
                    extraction_method=self.extractor_name,
                )

        extractor = TrafilaturaExtractor()
        assert extractor.extractor_name == "trafilatura"

    def test_正常系_具象クラスはextractメソッドを実装できる(
        self,
        sample_collected_article: CollectedArticle,
    ) -> None:
        """Concrete class can implement extract method."""

        class TestExtractor(BaseExtractor):
            @property
            def extractor_name(self) -> str:
                return "test"

            async def extract(self, article: CollectedArticle) -> ExtractedArticle:
                return ExtractedArticle(
                    collected=article,
                    body_text="Extracted text",
                    extraction_status=ExtractionStatus.SUCCESS,
                    extraction_method=self.extractor_name,
                )

        extractor = TestExtractor()
        # Method exists and is callable
        assert callable(extractor.extract)

    def test_異常系_extractor_nameを実装しないとインスタンス化できない(self) -> None:
        """Cannot instantiate if extractor_name is not implemented."""

        class IncompleteExtractor(BaseExtractor):
            async def extract(self, article: CollectedArticle) -> ExtractedArticle:
                return ExtractedArticle(
                    collected=article,
                    body_text="Extracted text",
                    extraction_status=ExtractionStatus.SUCCESS,
                    extraction_method="test",
                )

        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            IncompleteExtractor()  # type: ignore[abstract]

    def test_異常系_extractを実装しないとインスタンス化できない(self) -> None:
        """Cannot instantiate if extract is not implemented."""

        class IncompleteExtractor(BaseExtractor):
            @property
            def extractor_name(self) -> str:
                return "test"

        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            IncompleteExtractor()  # type: ignore[abstract]


class TestExtractMethodSignature:
    """Tests for extract method signature."""

    @pytest.mark.asyncio
    async def test_正常系_extractはExtractedArticleを返す(
        self,
        sample_collected_article: CollectedArticle,
    ) -> None:
        """extract should return an ExtractedArticle."""

        class TestExtractor(BaseExtractor):
            @property
            def extractor_name(self) -> str:
                return "test"

            async def extract(self, article: CollectedArticle) -> ExtractedArticle:
                return ExtractedArticle(
                    collected=article,
                    body_text="Full article content here...",
                    extraction_status=ExtractionStatus.SUCCESS,
                    extraction_method=self.extractor_name,
                )

        extractor = TestExtractor()
        result = await extractor.extract(sample_collected_article)
        assert isinstance(result, ExtractedArticle)
        assert result.extraction_status == ExtractionStatus.SUCCESS
        assert result.body_text == "Full article content here..."
        assert result.extraction_method == "test"

    @pytest.mark.asyncio
    async def test_正常系_extractはCollectedArticleを保持する(
        self,
        sample_collected_article: CollectedArticle,
    ) -> None:
        """extract result should contain the original CollectedArticle."""

        class TestExtractor(BaseExtractor):
            @property
            def extractor_name(self) -> str:
                return "test"

            async def extract(self, article: CollectedArticle) -> ExtractedArticle:
                return ExtractedArticle(
                    collected=article,
                    body_text="Content",
                    extraction_status=ExtractionStatus.SUCCESS,
                    extraction_method=self.extractor_name,
                )

        extractor = TestExtractor()
        result = await extractor.extract(sample_collected_article)
        assert result.collected == sample_collected_article
        assert result.collected.title == "Test Article"


class TestExtractBatchMethod:
    """Tests for extract_batch method."""

    @pytest.mark.asyncio
    async def test_正常系_extract_batchは複数記事を抽出できる(
        self,
        sample_collected_articles: list[CollectedArticle],
    ) -> None:
        """extract_batch should extract multiple articles."""

        class TestExtractor(BaseExtractor):
            @property
            def extractor_name(self) -> str:
                return "test"

            async def extract(self, article: CollectedArticle) -> ExtractedArticle:
                return ExtractedArticle(
                    collected=article,
                    body_text=f"Content for {article.title}",
                    extraction_status=ExtractionStatus.SUCCESS,
                    extraction_method=self.extractor_name,
                )

        extractor = TestExtractor()
        results = await extractor.extract_batch(sample_collected_articles)

        assert len(results) == 5
        assert all(isinstance(r, ExtractedArticle) for r in results)
        assert all(r.extraction_status == ExtractionStatus.SUCCESS for r in results)

    @pytest.mark.asyncio
    async def test_正常系_extract_batchはデフォルトで並列数5(
        self,
        sample_collected_articles: list[CollectedArticle],
    ) -> None:
        """extract_batch should have default concurrency of 5."""
        import inspect

        class TestExtractor(BaseExtractor):
            @property
            def extractor_name(self) -> str:
                return "test"

            async def extract(self, article: CollectedArticle) -> ExtractedArticle:
                return ExtractedArticle(
                    collected=article,
                    body_text="Content",
                    extraction_status=ExtractionStatus.SUCCESS,
                    extraction_method=self.extractor_name,
                )

        extractor = TestExtractor()
        sig = inspect.signature(extractor.extract_batch)
        concurrency_param = sig.parameters.get("concurrency")
        assert concurrency_param is not None
        assert concurrency_param.default == 5

    @pytest.mark.asyncio
    async def test_正常系_extract_batchは並列数を制限する(
        self,
        sample_collected_articles: list[CollectedArticle],
    ) -> None:
        """extract_batch should limit concurrency with semaphore."""
        concurrent_count = 0
        max_concurrent = 0

        class TestExtractor(BaseExtractor):
            @property
            def extractor_name(self) -> str:
                return "test"

            async def extract(self, article: CollectedArticle) -> ExtractedArticle:
                nonlocal concurrent_count, max_concurrent
                concurrent_count += 1
                max_concurrent = max(max_concurrent, concurrent_count)
                await asyncio.sleep(0.01)  # Simulate I/O
                concurrent_count -= 1
                return ExtractedArticle(
                    collected=article,
                    body_text="Content",
                    extraction_status=ExtractionStatus.SUCCESS,
                    extraction_method=self.extractor_name,
                )

        extractor = TestExtractor()
        # Use concurrency=2 to test limiting
        await extractor.extract_batch(sample_collected_articles, concurrency=2)

        # max_concurrent should not exceed 2
        assert max_concurrent <= 2

    @pytest.mark.asyncio
    async def test_エッジケース_extract_batchは空リストを処理できる(self) -> None:
        """extract_batch should handle empty list."""

        class TestExtractor(BaseExtractor):
            @property
            def extractor_name(self) -> str:
                return "test"

            async def extract(self, article: CollectedArticle) -> ExtractedArticle:
                return ExtractedArticle(
                    collected=article,
                    body_text="Content",
                    extraction_status=ExtractionStatus.SUCCESS,
                    extraction_method=self.extractor_name,
                )

        extractor = TestExtractor()
        results = await extractor.extract_batch([])

        assert results == []
        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_正常系_extract_batchは順序を保持する(
        self,
        sample_collected_articles: list[CollectedArticle],
    ) -> None:
        """extract_batch should preserve order of articles."""

        class TestExtractor(BaseExtractor):
            @property
            def extractor_name(self) -> str:
                return "test"

            async def extract(self, article: CollectedArticle) -> ExtractedArticle:
                # Add varying delays to test order preservation
                delay = hash(str(article.url)) % 10 / 1000  # 0-10ms
                await asyncio.sleep(delay)
                return ExtractedArticle(
                    collected=article,
                    body_text=f"Content for {article.title}",
                    extraction_status=ExtractionStatus.SUCCESS,
                    extraction_method=self.extractor_name,
                )

        extractor = TestExtractor()
        results = await extractor.extract_batch(sample_collected_articles)

        # Verify order is preserved
        for i, result in enumerate(results):
            assert result.collected.title == f"Test Article {i}"

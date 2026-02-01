"""Unit tests for BaseCollector ABC.

This module tests the BaseCollector abstract base class to ensure:
- It cannot be instantiated directly
- Concrete implementations must implement source_type property
- Concrete implementations must implement collect() method
- The collect() method has correct signature and return type
"""

from abc import ABC

import pytest
from news.collectors.base import BaseCollector
from news.models import CollectedArticle, SourceType


class TestBaseCollectorDefinition:
    """Tests for BaseCollector class definition."""

    def test_正常系_BaseCollectorはABCを継承している(self) -> None:
        """BaseCollector should inherit from ABC."""
        assert issubclass(BaseCollector, ABC)

    def test_異常系_BaseCollectorは直接インスタンス化できない(self) -> None:
        """BaseCollector cannot be instantiated directly."""
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            BaseCollector()  # type: ignore[abstract]


class TestBaseCollectorAbstractMethods:
    """Tests for BaseCollector abstract methods."""

    def test_正常系_source_typeプロパティが抽象プロパティとして定義されている(
        self,
    ) -> None:
        """source_type should be defined as an abstract property."""
        assert hasattr(BaseCollector, "source_type")
        # Check it's an abstract property by checking __abstractmethods__
        assert "source_type" in BaseCollector.__abstractmethods__

    def test_正常系_collectメソッドが抽象メソッドとして定義されている(self) -> None:
        """collect should be defined as an abstract method."""
        assert hasattr(BaseCollector, "collect")
        assert "collect" in BaseCollector.__abstractmethods__


class TestConcreteCollectorImplementation:
    """Tests for concrete implementations of BaseCollector."""

    def test_正常系_具象クラスはsource_typeを実装できる(self) -> None:
        """Concrete class can implement source_type property."""

        class RSSCollector(BaseCollector):
            @property
            def source_type(self) -> SourceType:
                return SourceType.RSS

            async def collect(
                self,
                max_age_hours: int = 168,
            ) -> list[CollectedArticle]:
                return []

        collector = RSSCollector()
        assert collector.source_type == SourceType.RSS

    def test_正常系_具象クラスはcollectメソッドを実装できる(self) -> None:
        """Concrete class can implement collect method."""

        class YFinanceCollector(BaseCollector):
            @property
            def source_type(self) -> SourceType:
                return SourceType.YFINANCE

            async def collect(
                self,
                max_age_hours: int = 168,
            ) -> list[CollectedArticle]:
                return []

        collector = YFinanceCollector()
        # Method exists and is callable
        assert callable(collector.collect)

    def test_異常系_source_typeを実装しないとインスタンス化できない(self) -> None:
        """Cannot instantiate if source_type is not implemented."""

        class IncompleteCollector(BaseCollector):
            async def collect(
                self,
                max_age_hours: int = 168,
            ) -> list[CollectedArticle]:
                return []

        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            IncompleteCollector()  # type: ignore[abstract]

    def test_異常系_collectを実装しないとインスタンス化できない(self) -> None:
        """Cannot instantiate if collect is not implemented."""

        class IncompleteCollector(BaseCollector):
            @property
            def source_type(self) -> SourceType:
                return SourceType.RSS

        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            IncompleteCollector()  # type: ignore[abstract]


class TestCollectMethodSignature:
    """Tests for collect method signature."""

    def test_正常系_collectメソッドのデフォルト引数が168(self) -> None:
        """collect method should have max_age_hours default of 168."""

        class TestCollector(BaseCollector):
            @property
            def source_type(self) -> SourceType:
                return SourceType.RSS

            async def collect(
                self,
                max_age_hours: int = 168,
            ) -> list[CollectedArticle]:
                self.last_max_age = max_age_hours
                return []

        collector = TestCollector()
        # Check default value in signature
        import inspect

        sig = inspect.signature(collector.collect)
        max_age_param = sig.parameters.get("max_age_hours")
        assert max_age_param is not None
        assert max_age_param.default == 168

    @pytest.mark.asyncio
    async def test_正常系_collectは空リストを返せる(self) -> None:
        """collect should be able to return an empty list."""

        class TestCollector(BaseCollector):
            @property
            def source_type(self) -> SourceType:
                return SourceType.RSS

            async def collect(
                self,
                max_age_hours: int = 168,
            ) -> list[CollectedArticle]:
                return []

        collector = TestCollector()
        result = await collector.collect()
        assert result == []
        assert isinstance(result, list)

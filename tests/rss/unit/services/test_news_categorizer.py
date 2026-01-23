"""Tests for news categorizer module."""

import time

import pytest

from rss.services.news_categorizer import (
    CategorizationResult,
    NewsCategorizer,
    NewsCategory,
)


class TestNewsCategory:
    """Tests for NewsCategory enum."""

    def test_正常系_全カテゴリが定義されている(self) -> None:
        expected_categories = {"index", "mag7", "sector", "macro", "theme", "other"}
        actual_categories = {c.value for c in NewsCategory}
        assert actual_categories == expected_categories


class TestNewsCategorizer:
    """Tests for NewsCategorizer class."""

    @pytest.fixture
    def categorizer(self) -> NewsCategorizer:
        """Create a NewsCategorizer instance."""
        return NewsCategorizer()

    # === Index Category Tests ===
    class TestIndexCategory:
        @pytest.fixture
        def categorizer(self) -> NewsCategorizer:
            return NewsCategorizer()

        def test_正常系_SP500関連ニュースがindex判定(
            self, categorizer: NewsCategorizer
        ) -> None:
            result = categorizer.categorize(
                title="S&P 500 hits record high amid tech rally",
                content="The S&P 500 index reached a new all-time high...",
            )
            assert result.category == NewsCategory.INDEX

        def test_正常系_NASDAQ関連ニュースがindex判定(
            self, categorizer: NewsCategorizer
        ) -> None:
            result = categorizer.categorize(
                title="NASDAQ Composite surges 2%",
                content="Technology stocks led the gains...",
            )
            assert result.category == NewsCategory.INDEX

        def test_正常系_日経平均関連ニュースがindex判定(
            self, categorizer: NewsCategorizer
        ) -> None:
            result = categorizer.categorize(
                title="日経平均が4万円突破",
                content="日経平均株価が史上最高値を更新...",
            )
            assert result.category == NewsCategory.INDEX

        def test_正常系_DowJones関連ニュースがindex判定(
            self, categorizer: NewsCategorizer
        ) -> None:
            result = categorizer.categorize(
                title="Dow Jones Industrial Average drops 500 points",
                content="The Dow fell sharply...",
            )
            assert result.category == NewsCategory.INDEX

    # === MAG7 Category Tests ===
    class TestMAG7Category:
        @pytest.fixture
        def categorizer(self) -> NewsCategorizer:
            return NewsCategorizer()

        def test_正常系_Apple関連ニュースがmag7判定(
            self, categorizer: NewsCategorizer
        ) -> None:
            result = categorizer.categorize(
                title="Apple announces new iPhone",
                content="Apple Inc. unveiled its latest smartphone...",
            )
            assert result.category == NewsCategory.MAG7

        def test_正常系_NVIDIA関連ニュースがmag7判定(
            self, categorizer: NewsCategorizer
        ) -> None:
            result = categorizer.categorize(
                title="NVIDIA reports record quarterly earnings",
                content="NVIDIA Corporation announced...",
            )
            assert result.category == NewsCategory.MAG7

        def test_正常系_Microsoft関連ニュースがmag7判定(
            self, categorizer: NewsCategorizer
        ) -> None:
            result = categorizer.categorize(
                title="Microsoft Azure growth exceeds expectations",
                content="Microsoft Corp. reported strong cloud revenue...",
            )
            assert result.category == NewsCategory.MAG7

        def test_正常系_Tesla関連ニュースがmag7判定(
            self, categorizer: NewsCategorizer
        ) -> None:
            result = categorizer.categorize(
                title="Tesla delivers record number of vehicles",
                content="Tesla Inc. announced quarterly delivery...",
            )
            assert result.category == NewsCategory.MAG7

        def test_正常系_Amazon関連ニュースがmag7判定(
            self, categorizer: NewsCategorizer
        ) -> None:
            result = categorizer.categorize(
                title="Amazon Web Services announces new AI tools",
                content="Amazon.com Inc.'s cloud division...",
            )
            assert result.category == NewsCategory.MAG7

        def test_正常系_Google関連ニュースがmag7判定(
            self, categorizer: NewsCategorizer
        ) -> None:
            result = categorizer.categorize(
                title="Google launches new AI model",
                content="Alphabet Inc.'s Google division...",
            )
            assert result.category == NewsCategory.MAG7

        def test_正常系_Meta関連ニュースがmag7判定(
            self, categorizer: NewsCategorizer
        ) -> None:
            result = categorizer.categorize(
                title="Meta unveils new VR headset",
                content="Meta Platforms Inc. announced...",
            )
            assert result.category == NewsCategory.MAG7

    # === Macro Category Tests ===
    class TestMacroCategory:
        @pytest.fixture
        def categorizer(self) -> NewsCategorizer:
            return NewsCategorizer()

        def test_正常系_Fed関連ニュースがmacro判定(
            self, categorizer: NewsCategorizer
        ) -> None:
            result = categorizer.categorize(
                title="Fed holds interest rates steady",
                content="The Federal Reserve announced...",
            )
            assert result.category == NewsCategory.MACRO

        def test_正常系_inflation関連ニュースがmacro判定(
            self, categorizer: NewsCategorizer
        ) -> None:
            result = categorizer.categorize(
                title="Inflation data exceeds expectations",
                content="Consumer prices rose more than expected...",
            )
            assert result.category == NewsCategory.MACRO

        def test_正常系_GDP関連ニュースがmacro判定(
            self, categorizer: NewsCategorizer
        ) -> None:
            result = categorizer.categorize(
                title="US GDP grows 3% in Q3",
                content="The economy expanded at a stronger pace...",
            )
            assert result.category == NewsCategory.MACRO

        def test_正常系_雇用統計関連ニュースがmacro判定(
            self, categorizer: NewsCategorizer
        ) -> None:
            result = categorizer.categorize(
                title="Non-farm payrolls beat expectations",
                content="The US economy added 250,000 jobs...",
            )
            assert result.category == NewsCategory.MACRO

        def test_正常系_金利関連ニュースがmacro判定(
            self, categorizer: NewsCategorizer
        ) -> None:
            result = categorizer.categorize(
                title="Interest rate decision looms",
                content="Markets await the central bank's policy...",
            )
            assert result.category == NewsCategory.MACRO

    # === Sector Category Tests ===
    class TestSectorCategory:
        @pytest.fixture
        def categorizer(self) -> NewsCategorizer:
            return NewsCategorizer()

        def test_正常系_technology_sector関連ニュースがsector判定(
            self, categorizer: NewsCategorizer
        ) -> None:
            result = categorizer.categorize(
                title="Technology sector leads market gains",
                content="Tech stocks outperformed...",
            )
            assert result.category == NewsCategory.SECTOR

        def test_正常系_energy_sector関連ニュースがsector判定(
            self, categorizer: NewsCategorizer
        ) -> None:
            result = categorizer.categorize(
                title="Energy sector rallies on oil prices",
                content="Oil and gas companies gained...",
            )
            assert result.category == NewsCategory.SECTOR

        def test_正常系_healthcare_sector関連ニュースがsector判定(
            self, categorizer: NewsCategorizer
        ) -> None:
            result = categorizer.categorize(
                title="Healthcare stocks surge",
                content="Pharmaceutical companies led gains...",
            )
            assert result.category == NewsCategory.SECTOR

        def test_正常系_financials_sector関連ニュースがsector判定(
            self, categorizer: NewsCategorizer
        ) -> None:
            result = categorizer.categorize(
                title="Financial sector outperforms",
                content="Banks reported strong earnings...",
            )
            assert result.category == NewsCategory.SECTOR

    # === Theme Category Tests ===
    class TestThemeCategory:
        @pytest.fixture
        def categorizer(self) -> NewsCategorizer:
            return NewsCategorizer()

        def test_正常系_AI投資テーマがtheme判定(
            self, categorizer: NewsCategorizer
        ) -> None:
            result = categorizer.categorize(
                title="AI investment boom continues",
                content="Artificial intelligence stocks surge...",
            )
            assert result.category == NewsCategory.THEME

        def test_正常系_semiconductor投資テーマがtheme判定(
            self, categorizer: NewsCategorizer
        ) -> None:
            result = categorizer.categorize(
                title="Semiconductor demand drives growth",
                content="Chip makers benefit from AI demand...",
            )
            assert result.category == NewsCategory.THEME

        def test_正常系_EV投資テーマがtheme判定(
            self, categorizer: NewsCategorizer
        ) -> None:
            result = categorizer.categorize(
                title="Electric vehicle sales accelerate",
                content="EV adoption continues to grow...",
            )
            assert result.category == NewsCategory.THEME

        def test_正常系_renewable_energy投資テーマがtheme判定(
            self, categorizer: NewsCategorizer
        ) -> None:
            result = categorizer.categorize(
                title="Renewable energy investments surge",
                content="Solar and wind power capacity grows...",
            )
            assert result.category == NewsCategory.THEME

    # === Other Category Tests ===
    class TestOtherCategory:
        @pytest.fixture
        def categorizer(self) -> NewsCategorizer:
            return NewsCategorizer()

        def test_正常系_該当なしニュースがother判定(
            self, categorizer: NewsCategorizer
        ) -> None:
            result = categorizer.categorize(
                title="Local weather update",
                content="Sunny skies expected tomorrow...",
            )
            assert result.category == NewsCategory.OTHER

    # === Priority Tests ===
    class TestPriority:
        @pytest.fixture
        def categorizer(self) -> NewsCategorizer:
            return NewsCategorizer()

        def test_正常系_複数カテゴリマッチ時に優先度順で判定(
            self, categorizer: NewsCategorizer
        ) -> None:
            # S&P 500 (index) + Apple (MAG7) -> index が優先
            result = categorizer.categorize(
                title="S&P 500 rises as Apple reports earnings",
                content="The index gained as Apple announced...",
            )
            # 優先度: index > mag7 > macro > sector > theme > other
            assert result.category == NewsCategory.INDEX

        def test_正常系_MAG7とMacroが競合時MAG7が優先(
            self, categorizer: NewsCategorizer
        ) -> None:
            # Apple (MAG7) + Fed (macro) -> MAG7 が優先
            result = categorizer.categorize(
                title="Apple stock rises after Fed decision",
                content="Apple shares gained...",
            )
            assert result.category == NewsCategory.MAG7

    # === Confidence Score Tests ===
    class TestConfidenceScore:
        @pytest.fixture
        def categorizer(self) -> NewsCategorizer:
            return NewsCategorizer()

        def test_正常系_高い信頼度スコアを返す(
            self, categorizer: NewsCategorizer
        ) -> None:
            result = categorizer.categorize(
                title="S&P 500 S&P500 index hits record",
                content="The S&P 500 benchmark index reached...",
            )
            assert result.confidence >= 0.5

        def test_正常系_信頼度スコアが0から1の範囲(
            self, categorizer: NewsCategorizer
        ) -> None:
            result = categorizer.categorize(
                title="Random news article",
                content="Some content here...",
            )
            assert 0.0 <= result.confidence <= 1.0

    # === Matched Keywords Tests ===
    class TestMatchedKeywords:
        @pytest.fixture
        def categorizer(self) -> NewsCategorizer:
            return NewsCategorizer()

        def test_正常系_マッチしたキーワードを返す(
            self, categorizer: NewsCategorizer
        ) -> None:
            result = categorizer.categorize(
                title="S&P 500 hits record high",
                content="The index continued its rally...",
            )
            assert len(result.matched_keywords) > 0
            assert any("s&p 500" in kw.lower() for kw in result.matched_keywords)

    # === Batch Categorization Tests ===
    class TestBatchCategorization:
        @pytest.fixture
        def categorizer(self) -> NewsCategorizer:
            return NewsCategorizer()

        def test_正常系_複数ニュースを一括分類(
            self, categorizer: NewsCategorizer
        ) -> None:
            news_items = [
                {"title": "S&P 500 rises", "content": "Index gains..."},
                {"title": "Apple reports earnings", "content": "Tech giant..."},
                {"title": "Fed holds rates", "content": "Central bank..."},
            ]
            results = categorizer.categorize_batch(news_items)
            assert len(results) == 3
            assert results[0].category == NewsCategory.INDEX
            assert results[1].category == NewsCategory.MAG7
            assert results[2].category == NewsCategory.MACRO

    # === Performance Tests ===
    class TestPerformance:
        @pytest.fixture
        def categorizer(self) -> NewsCategorizer:
            return NewsCategorizer()

        def test_正常系_100件秒以上の処理速度(
            self, categorizer: NewsCategorizer
        ) -> None:
            """100件/秒以上の処理速度を確認."""
            news_items = [
                {"title": f"News item {i}", "content": f"Content {i}"}
                for i in range(100)
            ]
            start_time = time.perf_counter()
            categorizer.categorize_batch(news_items)
            elapsed = time.perf_counter() - start_time

            # 100件を1秒以内に処理できること
            assert elapsed < 1.0, f"Processing took {elapsed:.2f}s, expected < 1.0s"

    # === Edge Cases ===
    class TestEdgeCases:
        @pytest.fixture
        def categorizer(self) -> NewsCategorizer:
            return NewsCategorizer()

        def test_正常系_空タイトルでother判定(
            self, categorizer: NewsCategorizer
        ) -> None:
            result = categorizer.categorize(title="", content="Some content")
            assert result.category == NewsCategory.OTHER

        def test_正常系_空コンテンツでタイトルのみで判定(
            self, categorizer: NewsCategorizer
        ) -> None:
            result = categorizer.categorize(title="S&P 500 hits record", content="")
            assert result.category == NewsCategory.INDEX

        def test_正常系_両方空でother判定(self, categorizer: NewsCategorizer) -> None:
            result = categorizer.categorize(title="", content="")
            assert result.category == NewsCategory.OTHER

        def test_正常系_大文字小文字を区別しない(
            self, categorizer: NewsCategorizer
        ) -> None:
            result = categorizer.categorize(
                title="APPLE REPORTS EARNINGS",
                content="apple inc announced...",
            )
            assert result.category == NewsCategory.MAG7


class TestCategorizationResult:
    """Tests for CategorizationResult dataclass."""

    def test_正常系_結果が正しく作成される(self) -> None:
        result = CategorizationResult(
            category=NewsCategory.INDEX,
            confidence=0.85,
            matched_keywords=["S&P 500", "index"],
        )
        assert result.category == NewsCategory.INDEX
        assert result.confidence == 0.85
        assert result.matched_keywords == ["S&P 500", "index"]

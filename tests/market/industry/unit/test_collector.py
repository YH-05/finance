"""Unit tests for market.industry.collector module.

Tests the IndustryCollector class which provides the CLI entry point
for collecting industry reports from all configured sources.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from market.industry.types import IndustryReport, ScrapingResult, SourceTier

# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def sample_reports() -> list[IndustryReport]:
    """Create sample IndustryReport instances for testing."""
    return [
        IndustryReport(
            source="McKinsey",
            title="Semiconductor Outlook 2026",
            url="https://mckinsey.com/insights/semiconductor-outlook",
            published_at=datetime(2026, 1, 15, tzinfo=timezone.utc),
            sector="Technology",
            summary="Report on semiconductor trends",
            tier=SourceTier.SCRAPING,
        ),
        IndustryReport(
            source="BCG",
            title="Tech Industry Trends",
            url="https://bcg.com/publications/tech-trends",
            published_at=datetime(2026, 1, 10, tzinfo=timezone.utc),
            sector="Technology",
            summary="BCG perspective on tech industry",
            tier=SourceTier.SCRAPING,
        ),
    ]


@pytest.fixture
def sample_scraping_result(
    sample_reports: list[IndustryReport],
) -> ScrapingResult:
    """Create a sample ScrapingResult."""
    return ScrapingResult(
        success=True,
        source="McKinsey",
        url="https://mckinsey.com/insights",
        reports=sample_reports,
    )


@pytest.fixture
def failed_scraping_result() -> ScrapingResult:
    """Create a failed ScrapingResult."""
    return ScrapingResult(
        success=False,
        source="BCG",
        url="https://bcg.com/publications",
        reports=[],
        error_message="Connection timeout",
    )


# =============================================================================
# CollectionResult Tests
# =============================================================================


class TestCollectionResult:
    """Tests for the CollectionResult data model."""

    def test_正常系_成功した収集結果を作成できる(self) -> None:
        from market.industry.collector import CollectionResult

        result = CollectionResult(
            source="McKinsey",
            success=True,
            report_count=5,
            error_message=None,
            duration_seconds=2.5,
        )
        assert result.source == "McKinsey"
        assert result.success is True
        assert result.report_count == 5
        assert result.error_message is None
        assert result.duration_seconds == 2.5

    def test_正常系_失敗した収集結果を作成できる(self) -> None:
        from market.industry.collector import CollectionResult

        result = CollectionResult(
            source="BCG",
            success=False,
            report_count=0,
            error_message="Connection timeout",
            duration_seconds=30.0,
        )
        assert result.success is False
        assert result.error_message == "Connection timeout"


class TestCollectionStats:
    """Tests for the CollectionStats data model."""

    def test_正常系_統計情報を作成できる(self) -> None:
        from market.industry.collector import CollectionStats

        stats = CollectionStats(
            total_sources=7,
            success_count=5,
            failure_count=2,
            total_reports=42,
            duration_seconds=120.5,
        )
        assert stats.total_sources == 7
        assert stats.success_count == 5
        assert stats.failure_count == 2
        assert stats.total_reports == 42
        assert stats.duration_seconds == 120.5


# =============================================================================
# IndustryCollector Tests
# =============================================================================


class TestIndustryCollector:
    """Tests for the IndustryCollector class."""

    def test_正常系_デフォルトパラメータで初期化できる(self) -> None:
        from market.industry.collector import IndustryCollector

        collector = IndustryCollector()
        assert collector.sector == "all"
        assert collector.ticker is None
        assert collector.source is None

    def test_正常系_セクター指定で初期化できる(self) -> None:
        from market.industry.collector import IndustryCollector

        collector = IndustryCollector(sector="Technology")
        assert collector.sector == "Technology"

    def test_正常系_ティッカー指定で初期化できる(self) -> None:
        from market.industry.collector import IndustryCollector

        collector = IndustryCollector(ticker="AAPL")
        assert collector.ticker == "AAPL"

    def test_正常系_ソース指定で初期化できる(self) -> None:
        from market.industry.collector import IndustryCollector

        collector = IndustryCollector(source="mckinsey")
        assert collector.source == "mckinsey"

    def test_正常系_出力ディレクトリを指定できる(self) -> None:
        from market.industry.collector import IndustryCollector

        output = Path("/tmp/test_output")
        collector = IndustryCollector(output_dir=output)
        assert collector.output_dir == output

    def test_正常系_get_scrapers_allで全スクレイパーを取得できる(self) -> None:
        from market.industry.collector import IndustryCollector

        collector = IndustryCollector(sector="Technology")
        scrapers = collector._get_scrapers()
        # Should include consulting + investment bank scrapers
        assert len(scrapers) >= 7  # 4 consulting + 3 IB

    def test_正常系_get_scrapers_sourceフィルタでスクレイパーを絞り込める(
        self,
    ) -> None:
        from market.industry.collector import IndustryCollector

        collector = IndustryCollector(source="mckinsey")
        scrapers = collector._get_scrapers()
        assert len(scrapers) == 1
        assert scrapers[0].source_name == "McKinsey"

    def test_異常系_存在しないソースでget_scrapersが空リストを返す(self) -> None:
        from market.industry.collector import IndustryCollector

        collector = IndustryCollector(source="nonexistent")
        scrapers = collector._get_scrapers()
        assert scrapers == []


class TestIndustryCollectorCollect:
    """Tests for the IndustryCollector.collect() async method."""

    @pytest.mark.asyncio
    async def test_正常系_collectで全スクレイパーを実行して結果を返す(
        self,
        sample_reports: list[IndustryReport],
    ) -> None:
        from market.industry.collector import IndustryCollector

        collector = IndustryCollector(sector="Technology")

        # Mock all scrapers to return success
        mock_scraper = AsyncMock()
        mock_scraper.source_name = "McKinsey"
        mock_scraper.scrape = AsyncMock(
            return_value=ScrapingResult(
                success=True,
                source="McKinsey",
                url="https://mckinsey.com/insights",
                reports=sample_reports,
            )
        )
        mock_scraper.save_reports = AsyncMock(return_value=[])
        mock_scraper.__aenter__ = AsyncMock(return_value=mock_scraper)
        mock_scraper.__aexit__ = AsyncMock(return_value=None)

        with patch.object(collector, "_get_scrapers", return_value=[mock_scraper]):
            stats = await collector.collect()

        assert stats.total_sources == 1
        assert stats.success_count == 1
        assert stats.failure_count == 0
        assert stats.total_reports == 2

    @pytest.mark.asyncio
    async def test_正常系_スクレイパーが失敗しても他のスクレイパーは継続する(
        self,
        sample_reports: list[IndustryReport],
    ) -> None:
        from market.industry.collector import IndustryCollector

        collector = IndustryCollector(sector="Technology")

        # One successful, one failed scraper
        success_scraper = AsyncMock()
        success_scraper.source_name = "McKinsey"
        success_scraper.scrape = AsyncMock(
            return_value=ScrapingResult(
                success=True,
                source="McKinsey",
                url="https://mckinsey.com/insights",
                reports=sample_reports,
            )
        )
        success_scraper.save_reports = AsyncMock(return_value=[])
        success_scraper.__aenter__ = AsyncMock(return_value=success_scraper)
        success_scraper.__aexit__ = AsyncMock(return_value=None)

        fail_scraper = AsyncMock()
        fail_scraper.source_name = "BCG"
        fail_scraper.scrape = AsyncMock(
            return_value=ScrapingResult(
                success=False,
                source="BCG",
                url="https://bcg.com/publications",
                reports=[],
                error_message="Connection timeout",
            )
        )
        fail_scraper.__aenter__ = AsyncMock(return_value=fail_scraper)
        fail_scraper.__aexit__ = AsyncMock(return_value=None)

        with patch.object(
            collector,
            "_get_scrapers",
            return_value=[success_scraper, fail_scraper],
        ):
            stats = await collector.collect()

        assert stats.total_sources == 2
        assert stats.success_count == 1
        assert stats.failure_count == 1
        assert stats.total_reports == 2

    @pytest.mark.asyncio
    async def test_正常系_スクレイパーがゼロ件でも正常に完了する(self) -> None:
        from market.industry.collector import IndustryCollector

        collector = IndustryCollector(source="nonexistent")

        with patch.object(collector, "_get_scrapers", return_value=[]):
            stats = await collector.collect()

        assert stats.total_sources == 0
        assert stats.success_count == 0
        assert stats.total_reports == 0


# =============================================================================
# CLI (main) Tests
# =============================================================================


class TestMainCLI:
    """Tests for the main() CLI entry point."""

    def test_正常系_デフォルト引数でmainが呼び出せる(self) -> None:
        from market.industry.collector import build_parser

        parser = build_parser()
        args = parser.parse_args([])
        assert args.sector == "all"
        assert args.ticker is None
        assert args.source is None

    def test_正常系_sectorオプションをパースできる(self) -> None:
        from market.industry.collector import build_parser

        parser = build_parser()
        args = parser.parse_args(["--sector", "Technology"])
        assert args.sector == "Technology"

    def test_正常系_tickerオプションをパースできる(self) -> None:
        from market.industry.collector import build_parser

        parser = build_parser()
        args = parser.parse_args(["--ticker", "AAPL"])
        assert args.ticker == "AAPL"

    def test_正常系_sourceオプションをパースできる(self) -> None:
        from market.industry.collector import build_parser

        parser = build_parser()
        args = parser.parse_args(["--source", "mckinsey"])
        assert args.source == "mckinsey"

    def test_正常系_複数オプションを同時に指定できる(self) -> None:
        from market.industry.collector import build_parser

        parser = build_parser()
        args = parser.parse_args(
            ["--sector", "Technology", "--ticker", "AAPL", "--source", "mckinsey"]
        )
        assert args.sector == "Technology"
        assert args.ticker == "AAPL"
        assert args.source == "mckinsey"

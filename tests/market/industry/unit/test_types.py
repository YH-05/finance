"""Unit tests for market.industry.types module.

Tests cover Pydantic model validation, serialization, defaults,
and edge cases for IndustryReport, ScrapingResult, PeerGroup,
ScrapingConfig, and RetryConfig.
"""

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from market.industry.types import (
    IndustryReport,
    PeerGroup,
    RetryConfig,
    ScrapingConfig,
    ScrapingResult,
    SourceTier,
)


class TestSourceTier:
    """Tests for SourceTier enum."""

    def test_正常系_全てのティアが定義されている(self) -> None:
        assert SourceTier.API == "api"
        assert SourceTier.SCRAPING == "scraping"
        assert SourceTier.MEDIA == "media"

    def test_正常系_文字列比較が可能(self) -> None:
        assert SourceTier.API == "api"
        assert SourceTier.SCRAPING == "scraping"


class TestIndustryReport:
    """Tests for IndustryReport Pydantic model."""

    def test_正常系_必須フィールドのみで作成できる(self) -> None:
        report = IndustryReport(
            source="McKinsey",
            title="Semiconductor Industry Outlook 2026",
            url="https://mckinsey.com/insights/semiconductor-outlook",
            published_at=datetime(2026, 1, 15, tzinfo=timezone.utc),
            sector="Technology",
        )
        assert report.source == "McKinsey"
        assert report.title == "Semiconductor Industry Outlook 2026"
        assert report.url == "https://mckinsey.com/insights/semiconductor-outlook"
        assert report.sector == "Technology"
        assert report.sub_sector is None
        assert report.summary is None
        assert report.content is None
        assert report.tier == SourceTier.SCRAPING

    def test_正常系_全フィールドで作成できる(self) -> None:
        report = IndustryReport(
            source="BLS",
            title="Employment Statistics Q4 2025",
            url="https://bls.gov/data/employment",
            published_at=datetime(2026, 1, 10, tzinfo=timezone.utc),
            sector="Technology",
            sub_sector="Semiconductors",
            summary="Semiconductor employment rose 5% in Q4.",
            content="Full report text...",
            tier=SourceTier.API,
        )
        assert report.sub_sector == "Semiconductors"
        assert report.summary == "Semiconductor employment rose 5% in Q4."
        assert report.content == "Full report text..."
        assert report.tier == SourceTier.API

    def test_異常系_必須フィールドが欠けているとValidationError(self) -> None:
        with pytest.raises(ValidationError):
            IndustryReport(
                source="McKinsey",
                title="Missing URL and sector",
                published_at=datetime(2026, 1, 15, tzinfo=timezone.utc),
            )

    def test_正常系_model_dumpでdict変換できる(self) -> None:
        report = IndustryReport(
            source="BCG",
            title="Test Report",
            url="https://bcg.com/test",
            published_at=datetime(2026, 2, 1, tzinfo=timezone.utc),
            sector="Healthcare",
        )
        data = report.model_dump()
        assert data["source"] == "BCG"
        assert data["sector"] == "Healthcare"
        assert data["tier"] == "scraping"

    def test_正常系_frozen属性で不変である(self) -> None:
        report = IndustryReport(
            source="BCG",
            title="Test",
            url="https://bcg.com/test",
            published_at=datetime(2026, 2, 1, tzinfo=timezone.utc),
            sector="Tech",
        )
        with pytest.raises(ValidationError):
            report.source = "Modified"


class TestScrapingResult:
    """Tests for ScrapingResult Pydantic model."""

    def test_正常系_成功結果を作成できる(self) -> None:
        report = IndustryReport(
            source="Goldman",
            title="Market Outlook",
            url="https://goldman.com/insights",
            published_at=datetime(2026, 1, 20, tzinfo=timezone.utc),
            sector="Financials",
        )
        result = ScrapingResult(
            success=True,
            source="Goldman",
            url="https://goldman.com/insights",
            reports=[report],
        )
        assert result.success is True
        assert len(result.reports) == 1
        assert result.error_message is None

    def test_正常系_失敗結果を作成できる(self) -> None:
        result = ScrapingResult(
            success=False,
            source="McKinsey",
            url="https://mckinsey.com/insights",
            reports=[],
            error_message="HTTP 403: Bot detected",
        )
        assert result.success is False
        assert result.reports == []
        assert result.error_message == "HTTP 403: Bot detected"

    def test_正常系_デフォルト値が適用される(self) -> None:
        result = ScrapingResult(
            success=True,
            source="BLS",
            url="https://bls.gov/data",
        )
        assert result.reports == []
        assert result.error_message is None


class TestPeerGroup:
    """Tests for PeerGroup Pydantic model."""

    def test_正常系_ピアグループを作成できる(self) -> None:
        group = PeerGroup(
            sector="Technology",
            sub_sector="Semiconductors",
            companies=["NVDA", "AMD", "INTC", "TSM", "AVGO"],
            description="Major semiconductor manufacturers and designers",
        )
        assert group.sector == "Technology"
        assert group.sub_sector == "Semiconductors"
        assert len(group.companies) == 5
        assert "NVDA" in group.companies

    def test_正常系_descriptionはオプショナル(self) -> None:
        group = PeerGroup(
            sector="Energy",
            sub_sector="Oil_Gas",
            companies=["XOM", "CVX"],
        )
        assert group.description is None

    def test_異常系_companiesが空でも作成可能(self) -> None:
        group = PeerGroup(
            sector="Financials",
            sub_sector="Banks",
            companies=[],
        )
        assert group.companies == []


class TestScrapingConfig:
    """Tests for ScrapingConfig Pydantic model."""

    def test_正常系_デフォルト値で作成できる(self) -> None:
        config = ScrapingConfig()
        assert config.polite_delay == 2.0
        assert config.delay_jitter == 1.0
        assert config.timeout == 30.0
        assert config.headless is True
        assert config.user_agents == ()
        assert config.impersonate == "chrome"

    def test_正常系_カスタム値で作成できる(self) -> None:
        config = ScrapingConfig(
            polite_delay=5.0,
            delay_jitter=2.0,
            timeout=60.0,
            headless=False,
        )
        assert config.polite_delay == 5.0
        assert config.headless is False

    def test_正常系_frozen属性で不変である(self) -> None:
        config = ScrapingConfig()
        with pytest.raises(ValidationError):
            config.polite_delay = 10.0


class TestRetryConfig:
    """Tests for RetryConfig Pydantic model."""

    def test_正常系_デフォルト値で作成できる(self) -> None:
        config = RetryConfig()
        assert config.max_attempts == 3
        assert config.initial_delay == 1.0
        assert config.max_delay == 30.0
        assert config.exponential_base == 2.0
        assert config.jitter is True

    def test_正常系_カスタム値で作成できる(self) -> None:
        config = RetryConfig(max_attempts=5, initial_delay=0.5)
        assert config.max_attempts == 5
        assert config.initial_delay == 0.5

    def test_異常系_max_attemptsが0以下でValidationError(self) -> None:
        with pytest.raises(ValidationError):
            RetryConfig(max_attempts=0)

    def test_異常系_max_attemptsが10超でValidationError(self) -> None:
        with pytest.raises(ValidationError):
            RetryConfig(max_attempts=11)

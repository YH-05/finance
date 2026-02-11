"""Unit tests for market.industry.peer_groups module.

Tests cover preset-based peer group retrieval, dynamic peer group
generation via yfinance industry/sector info, and combined lookup.
"""

from unittest.mock import MagicMock, patch

import pytest

from market.industry.config import IndustryPreset, IndustryPresetsConfig, SourceConfig
from market.industry.peer_groups import (
    get_dynamic_peer_group,
    get_peer_group,
    get_preset_peer_group,
)
from market.industry.types import PeerGroup

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture()
def sample_presets_config() -> IndustryPresetsConfig:
    """Create a sample IndustryPresetsConfig for testing."""
    return IndustryPresetsConfig(
        version="1.0",
        presets=[
            IndustryPreset(
                sector="Technology",
                sub_sectors=["Semiconductors", "Software_Infrastructure"],
                sources=[
                    SourceConfig(
                        name="McKinsey",
                        url="https://mckinsey.com/insights",
                        tier="scraping",
                    ),
                ],
                peer_tickers=["NVDA", "AMD", "INTC", "TSM", "AVGO"],
            ),
            IndustryPreset(
                sector="Healthcare",
                sub_sectors=["Pharmaceuticals"],
                sources=[],
                peer_tickers=["JNJ", "PFE", "MRK", "ABBV", "LLY"],
            ),
            IndustryPreset(
                sector="Financials",
                sub_sectors=["Banks"],
                sources=[],
                peer_tickers=["JPM", "BAC", "GS", "MS", "C"],
            ),
        ],
    )


# =============================================================================
# Tests for get_preset_peer_group
# =============================================================================


class TestGetPresetPeerGroup:
    """Tests for get_preset_peer_group function."""

    def test_正常系_セクター名でプリセットピアグループを取得できる(
        self, sample_presets_config: IndustryPresetsConfig
    ) -> None:
        result = get_preset_peer_group("Technology", sample_presets_config)
        assert result is not None
        assert result.sector == "Technology"
        assert "NVDA" in result.companies
        assert "AMD" in result.companies
        assert len(result.companies) == 5

    def test_正常系_サブセクター指定でフィルタリングできる(
        self, sample_presets_config: IndustryPresetsConfig
    ) -> None:
        result = get_preset_peer_group(
            "Technology",
            sample_presets_config,
            sub_sector="Semiconductors",
        )
        assert result is not None
        assert result.sector == "Technology"
        assert result.sub_sector == "Semiconductors"

    def test_異常系_存在しないセクターでNoneを返す(
        self, sample_presets_config: IndustryPresetsConfig
    ) -> None:
        result = get_preset_peer_group("NonExistent", sample_presets_config)
        assert result is None

    def test_正常系_ヘルスケアセクターのピアグループを取得できる(
        self, sample_presets_config: IndustryPresetsConfig
    ) -> None:
        result = get_preset_peer_group("Healthcare", sample_presets_config)
        assert result is not None
        assert result.sector == "Healthcare"
        assert "LLY" in result.companies

    def test_異常系_存在しないサブセクター指定でNoneを返す(
        self, sample_presets_config: IndustryPresetsConfig
    ) -> None:
        result = get_preset_peer_group(
            "Technology",
            sample_presets_config,
            sub_sector="NonExistent",
        )
        assert result is None


# =============================================================================
# Tests for get_dynamic_peer_group
# =============================================================================


class TestGetDynamicPeerGroup:
    """Tests for get_dynamic_peer_group function."""

    def test_正常系_yfinanceからピアグループを動的生成できる(self) -> None:
        mock_ticker = MagicMock()
        mock_ticker.info = {
            "sector": "Technology",
            "industry": "Semiconductors",
        }
        with patch("market.industry.peer_groups.yf.Ticker", return_value=mock_ticker):
            result = get_dynamic_peer_group("NVDA")
            assert result is not None
            assert result.sector == "Technology"
            assert result.sub_sector == "Semiconductors"

    def test_異常系_yfinanceでセクター情報が取得できない場合Noneを返す(
        self,
    ) -> None:
        mock_ticker = MagicMock()
        mock_ticker.info = {}
        with patch("market.industry.peer_groups.yf.Ticker", return_value=mock_ticker):
            result = get_dynamic_peer_group("INVALID")
            assert result is None

    def test_異常系_yfinanceで例外発生時にNoneを返す(self) -> None:
        with patch(
            "market.industry.peer_groups.yf.Ticker",
            side_effect=Exception("API Error"),
        ):
            result = get_dynamic_peer_group("NVDA")
            assert result is None

    def test_正常系_動的生成でティッカーシンボルが含まれる(self) -> None:
        mock_ticker = MagicMock()
        mock_ticker.info = {
            "sector": "Technology",
            "industry": "Semiconductors",
        }
        with patch("market.industry.peer_groups.yf.Ticker", return_value=mock_ticker):
            result = get_dynamic_peer_group("NVDA")
            assert result is not None
            assert "NVDA" in result.companies


# =============================================================================
# Tests for get_peer_group
# =============================================================================


class TestGetPeerGroup:
    """Tests for get_peer_group combined function."""

    def test_正常系_プリセット優先でピアグループを取得できる(
        self, sample_presets_config: IndustryPresetsConfig
    ) -> None:
        mock_ticker = MagicMock()
        mock_ticker.info = {
            "sector": "Technology",
            "industry": "Semiconductors",
        }
        with patch("market.industry.peer_groups.yf.Ticker", return_value=mock_ticker):
            result = get_peer_group("NVDA", sample_presets_config)
            assert result is not None
            assert result.sector == "Technology"
            # Preset has 5 tickers
            assert len(result.companies) == 5

    def test_正常系_プリセットにない場合は動的生成にフォールバック(
        self, sample_presets_config: IndustryPresetsConfig
    ) -> None:
        mock_ticker = MagicMock()
        mock_ticker.info = {
            "sector": "Real Estate",
            "industry": "REIT",
        }
        with patch("market.industry.peer_groups.yf.Ticker", return_value=mock_ticker):
            result = get_peer_group("O", sample_presets_config)
            assert result is not None
            assert result.sector == "Real Estate"
            assert result.sub_sector == "REIT"

    def test_異常系_プリセットも動的生成も失敗した場合Noneを返す(
        self, sample_presets_config: IndustryPresetsConfig
    ) -> None:
        mock_ticker = MagicMock()
        mock_ticker.info = {}
        with patch("market.industry.peer_groups.yf.Ticker", return_value=mock_ticker):
            result = get_peer_group("INVALID", sample_presets_config)
            assert result is None

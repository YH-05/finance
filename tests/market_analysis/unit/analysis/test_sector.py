"""Unit tests for sector analysis module.

This module tests the sector.py implementation for Issue #470.
Tests cover:
- Sector ETF returns calculation for all 11 sectors
- Top/Bottom 3 sectors ranking
- Top companies retrieval using yf.Sector
- Stock return calculation for contributors

References:
- Issue #470: セクター分析モジュールの実装 (sector.py)
- template/tests/unit/test_example.py
- tests/market_analysis/unit/analysis/test_returns.py
"""

from datetime import datetime
from typing import Any
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest

# AIDEV-NOTE: Importing from the module that will be implemented.
# Tests are expected to fail (Red state) until implementation is complete.
from market_analysis.analysis.sector import (
    SECTOR_ETF_MAP,
    SECTOR_KEYS,
    SectorAnalysisResult,
    SectorContributor,
    SectorInfo,
    analyze_sector_performance,
    fetch_sector_etf_returns,
    fetch_top_companies,
    get_top_bottom_sectors,
)

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_etf_prices() -> dict[str, pd.Series]:
    """Create mock ETF price series for all 11 sectors.

    Returns dictionary mapping ETF tickers to price series.
    """
    np.random.seed(42)
    dates = pd.date_range("2024-01-01", periods=10, freq="B")

    prices = {}
    base_prices = {
        "XLB": 100.0,  # Materials
        "XLC": 110.0,  # Communication Services
        "XLY": 120.0,  # Consumer Discretionary
        "XLP": 90.0,  # Consumer Staples
        "XLE": 80.0,  # Energy
        "XLF": 95.0,  # Financials
        "XLV": 105.0,  # Healthcare
        "XLI": 115.0,  # Industrials
        "XLRE": 85.0,  # Real Estate
        "XLK": 130.0,  # Technology
        "XLU": 75.0,  # Utilities
    }

    # Generate prices with different returns
    returns_multipliers = {
        "XLB": 1.02,  # +2% weekly
        "XLC": 0.98,  # -2% weekly
        "XLY": 1.03,  # +3% weekly (top performer)
        "XLP": 1.01,  # +1% weekly
        "XLE": 0.97,  # -3% weekly (worst performer)
        "XLF": 1.015,  # +1.5% weekly
        "XLV": 1.005,  # +0.5% weekly
        "XLI": 1.025,  # +2.5% weekly
        "XLRE": 0.99,  # -1% weekly
        "XLK": 1.035,  # +3.5% weekly (best performer)
        "XLU": 0.985,  # -1.5% weekly
    }

    for ticker, base in base_prices.items():
        daily_return = returns_multipliers[ticker] ** (1 / 5)  # Convert weekly to daily
        price_values = [base * (daily_return**i) for i in range(10)]
        prices[ticker] = pd.Series(price_values, index=dates, name="Close")

    return prices


@pytest.fixture
def mock_top_companies() -> list[dict[str, Any]]:
    """Create mock top companies data for a sector."""
    return [
        {"symbol": "NVDA", "name": "NVIDIA Corporation", "weight": 0.15},
        {"symbol": "AAPL", "name": "Apple Inc.", "weight": 0.20},
        {"symbol": "MSFT", "name": "Microsoft Corporation", "weight": 0.18},
        {"symbol": "AVGO", "name": "Broadcom Inc.", "weight": 0.08},
        {"symbol": "ORCL", "name": "Oracle Corporation", "weight": 0.05},
    ]


@pytest.fixture
def mock_stock_prices() -> dict[str, pd.Series]:
    """Create mock stock price series for top companies."""
    np.random.seed(123)
    dates = pd.date_range("2024-01-01", periods=10, freq="B")

    prices = {}
    stock_data = {
        "NVDA": (500.0, 1.05),  # +5% weekly (top contributor)
        "AAPL": (175.0, 1.02),  # +2% weekly
        "MSFT": (380.0, 1.03),  # +3% weekly
        "AVGO": (1100.0, 1.04),  # +4% weekly
        "ORCL": (120.0, 1.01),  # +1% weekly
    }

    for ticker, (base, weekly_mult) in stock_data.items():
        daily_return = weekly_mult ** (1 / 5)
        price_values = [base * (daily_return**i) for i in range(10)]
        prices[ticker] = pd.Series(price_values, index=dates, name="Close")

    return prices


@pytest.fixture
def mock_yfinance_download() -> pd.DataFrame:
    """Create mock yfinance download result."""
    dates = pd.date_range("2024-01-01", periods=10, freq="B")
    np.random.seed(456)
    prices = 100 * np.cumprod(1 + np.random.normal(0.002, 0.01, 10))
    return pd.DataFrame(
        {
            "Open": prices * 0.99,
            "High": prices * 1.01,
            "Low": prices * 0.98,
            "Close": prices,
            "Volume": np.random.randint(1000000, 5000000, 10),
        },
        index=dates,
    )


# =============================================================================
# Tests for SECTOR_KEYS constant
# =============================================================================


class TestSectorKeysConstant:
    """Tests for SECTOR_KEYS list constant."""

    def test_正常系_全11セクターキーが含まれる(self) -> None:
        """SECTOR_KEYS が全11セクターを含むことを確認。"""
        expected_keys = [
            "basic-materials",
            "communication-services",
            "consumer-cyclical",
            "consumer-defensive",
            "energy",
            "financial-services",
            "healthcare",
            "industrials",
            "real-estate",
            "technology",
            "utilities",
        ]
        assert set(SECTOR_KEYS) == set(expected_keys)

    def test_正常系_セクターキーが11個(self) -> None:
        """SECTOR_KEYS が正確に11個のセクターを含むことを確認。"""
        assert len(SECTOR_KEYS) == 11


# =============================================================================
# Tests for SECTOR_ETF_MAP constant
# =============================================================================


class TestSectorEtfMapConstant:
    """Tests for SECTOR_ETF_MAP dictionary constant."""

    def test_正常系_全セクターにETFがマッピングされている(self) -> None:
        """全セクターキーにETFティッカーがマッピングされていることを確認。"""
        for sector_key in SECTOR_KEYS:
            assert sector_key in SECTOR_ETF_MAP
            assert isinstance(SECTOR_ETF_MAP[sector_key], str)

    def test_正常系_主要ETFが正しくマッピングされている(self) -> None:
        """主要なセクターETFが正しくマッピングされていることを確認。"""
        expected_mappings = {
            "technology": "XLK",
            "financial-services": "XLF",
            "healthcare": "XLV",
            "energy": "XLE",
            "consumer-cyclical": "XLY",
            "basic-materials": "XLB",
            "utilities": "XLU",
        }
        for sector, etf in expected_mappings.items():
            assert SECTOR_ETF_MAP[sector] == etf


# =============================================================================
# Tests for fetch_sector_etf_returns function
# =============================================================================


class TestFetchSectorEtfReturns:
    """Tests for fetch_sector_etf_returns function."""

    @patch("market_analysis.analysis.sector.yf.download")
    def test_正常系_全11セクターのETF騰落率を取得できる(
        self,
        mock_download: MagicMock,
        mock_yfinance_download: pd.DataFrame,
    ) -> None:
        """全11セクターのETF騰落率を取得できることを確認。"""
        mock_download.return_value = mock_yfinance_download

        result = fetch_sector_etf_returns()

        assert isinstance(result, dict)
        assert len(result) == 11
        for sector_key in SECTOR_KEYS:
            assert sector_key in result

    @patch("market_analysis.analysis.sector.yf.download")
    def test_正常系_騰落率が正しい型で返される(
        self,
        mock_download: MagicMock,
        mock_yfinance_download: pd.DataFrame,
    ) -> None:
        """騰落率が float | None 型で返されることを確認。"""
        mock_download.return_value = mock_yfinance_download

        result = fetch_sector_etf_returns()

        for _sector_key, return_value in result.items():
            assert return_value is None or isinstance(return_value, float)

    @patch("market_analysis.analysis.sector.yf.download")
    def test_正常系_1週間騰落率がデフォルト(
        self,
        mock_download: MagicMock,
        mock_yfinance_download: pd.DataFrame,
    ) -> None:
        """デフォルトで1週間騰落率が計算されることを確認。"""
        mock_download.return_value = mock_yfinance_download

        result = fetch_sector_etf_returns()  # period=5 (1W) by default

        # 結果が返されることを確認
        assert result is not None
        assert len(result) > 0

    @patch("market_analysis.analysis.sector.yf.download")
    def test_正常系_期間指定で騰落率を計算できる(
        self,
        mock_download: MagicMock,
        mock_yfinance_download: pd.DataFrame,
    ) -> None:
        """期間を指定して騰落率を計算できることを確認。"""
        mock_download.return_value = mock_yfinance_download

        result = fetch_sector_etf_returns(period=1)  # 1日騰落率

        assert isinstance(result, dict)
        assert len(result) == 11

    @patch("market_analysis.analysis.sector.yf.download")
    def test_異常系_API失敗時は空の辞書を返す(
        self,
        mock_download: MagicMock,
    ) -> None:
        """yfinance APIが失敗した場合、空の辞書を返すことを確認。"""
        mock_download.return_value = pd.DataFrame()  # 空のDataFrame

        result = fetch_sector_etf_returns()

        # 値がNoneの辞書または空の辞書を返す
        assert isinstance(result, dict)

    @patch("market_analysis.analysis.sector.yf.download")
    def test_異常系_例外発生時も辞書を返す(
        self,
        mock_download: MagicMock,
    ) -> None:
        """例外が発生した場合でも辞書を返すことを確認。"""
        mock_download.side_effect = Exception("API Error")

        result = fetch_sector_etf_returns()

        assert isinstance(result, dict)


# =============================================================================
# Tests for get_top_bottom_sectors function
# =============================================================================


class TestGetTopBottomSectors:
    """Tests for get_top_bottom_sectors function."""

    def test_正常系_上位3セクターを正しくランキングできる(self) -> None:
        """上位3セクターを正しくランキングできることを確認。"""
        returns = {
            "technology": 0.05,
            "financial-services": 0.03,
            "healthcare": 0.02,
            "energy": -0.02,
            "consumer-cyclical": 0.04,
            "utilities": -0.01,
            "basic-materials": 0.01,
            "industrials": 0.025,
            "real-estate": -0.015,
            "communication-services": 0.015,
            "consumer-defensive": 0.005,
        }

        top, _bottom = get_top_bottom_sectors(returns, n=3)

        # 上位3セクター（technology, consumer-cyclical, financial-services）
        assert len(top) == 3
        assert top[0][0] == "technology"  # 1位
        assert top[1][0] == "consumer-cyclical"  # 2位
        assert top[2][0] == "financial-services"  # 3位

    def test_正常系_下位3セクターを正しくランキングできる(self) -> None:
        """下位3セクターを正しくランキングできることを確認。"""
        returns = {
            "technology": 0.05,
            "financial-services": 0.03,
            "healthcare": 0.02,
            "energy": -0.02,
            "consumer-cyclical": 0.04,
            "utilities": -0.01,
            "basic-materials": 0.01,
            "industrials": 0.025,
            "real-estate": -0.015,
            "communication-services": 0.015,
            "consumer-defensive": 0.005,
        }

        _top, bottom = get_top_bottom_sectors(returns, n=3)

        # 下位3セクター（energy, real-estate, utilities）
        assert len(bottom) == 3
        assert bottom[0][0] == "energy"  # 最下位
        assert bottom[1][0] == "real-estate"  # 下から2位
        assert bottom[2][0] == "utilities"  # 下から3位

    def test_正常系_Noneを含む場合はスキップされる(self) -> None:
        """騰落率がNoneのセクターはランキングから除外されることを確認。"""
        returns = {
            "technology": 0.05,
            "financial-services": None,  # データなし
            "healthcare": 0.02,
            "energy": -0.02,
            "consumer-cyclical": None,  # データなし
            "utilities": -0.01,
            "basic-materials": 0.01,
            "industrials": 0.025,
            "real-estate": -0.015,
            "communication-services": 0.015,
            "consumer-defensive": 0.005,
        }

        top, bottom = get_top_bottom_sectors(returns, n=3)

        # Noneはランキングに含まれない
        assert all(
            sector not in ["financial-services", "consumer-cyclical"]
            for sector, _ in top
        )
        assert all(
            sector not in ["financial-services", "consumer-cyclical"]
            for sector, _ in bottom
        )

    def test_エッジケース_セクター数がN未満の場合(self) -> None:
        """有効なセクター数がN未満の場合、利用可能な分だけ返すことを確認。"""
        returns = {
            "technology": 0.05,
            "healthcare": 0.02,
        }

        top, bottom = get_top_bottom_sectors(returns, n=3)

        assert len(top) == 2
        assert len(bottom) == 2

    def test_エッジケース_空の辞書(self) -> None:
        """空の辞書で空のリストを返すことを確認。"""
        top, bottom = get_top_bottom_sectors({}, n=3)

        assert top == []
        assert bottom == []

    def test_異常系_Nが0以下でValueError(self) -> None:
        """Nが0以下の場合、ValueErrorが発生することを確認。"""
        returns = {"technology": 0.05}

        with pytest.raises(ValueError, match="n must be positive"):
            get_top_bottom_sectors(returns, n=0)


# =============================================================================
# Tests for fetch_top_companies function
# =============================================================================


class TestFetchTopCompanies:
    """Tests for fetch_top_companies function."""

    @patch("market_analysis.analysis.sector.yf.Sector")
    def test_正常系_セクターの代表銘柄を取得できる(
        self,
        mock_sector_class: MagicMock,
        mock_top_companies: list[dict[str, Any]],
    ) -> None:
        """yf.Sector.top_companies で代表銘柄を取得できることを確認。"""
        mock_sector = MagicMock()
        mock_sector.top_companies = pd.DataFrame(mock_top_companies)
        mock_sector_class.return_value = mock_sector

        result = fetch_top_companies("technology")

        assert result is not None
        assert len(result) > 0
        mock_sector_class.assert_called_once_with("technology")

    @patch("market_analysis.analysis.sector.yf.Sector")
    def test_正常系_銘柄情報にシンボルと名前が含まれる(
        self,
        mock_sector_class: MagicMock,
        mock_top_companies: list[dict[str, Any]],
    ) -> None:
        """取得した銘柄情報にシンボルと名前が含まれることを確認。"""
        mock_sector = MagicMock()
        mock_sector.top_companies = pd.DataFrame(mock_top_companies)
        mock_sector_class.return_value = mock_sector

        result = fetch_top_companies("technology")

        assert result is not None
        for company in result:
            assert "symbol" in company or "ticker" in company
            assert "name" in company

    @patch("market_analysis.analysis.sector.yf.Sector")
    def test_正常系_全セクターキーで取得できる(
        self,
        mock_sector_class: MagicMock,
        mock_top_companies: list[dict[str, Any]],
    ) -> None:
        """全てのセクターキーで代表銘柄を取得できることを確認。"""
        mock_sector = MagicMock()
        mock_sector.top_companies = pd.DataFrame(mock_top_companies)
        mock_sector_class.return_value = mock_sector

        for sector_key in SECTOR_KEYS:
            result = fetch_top_companies(sector_key)
            assert result is not None or result == []

    @patch("market_analysis.analysis.sector.yf.Sector")
    def test_異常系_無効なセクターキーでNoneを返す(
        self,
        mock_sector_class: MagicMock,
    ) -> None:
        """無効なセクターキーでNoneまたは空リストを返すことを確認。"""
        mock_sector_class.side_effect = Exception("Invalid sector")

        result = fetch_top_companies("invalid-sector")

        assert result is None or result == []

    @patch("market_analysis.analysis.sector.yf.Sector")
    def test_異常系_API失敗時はNoneを返す(
        self,
        mock_sector_class: MagicMock,
    ) -> None:
        """yfinance APIが失敗した場合、Noneを返すことを確認。"""
        mock_sector_class.side_effect = Exception("API Error")

        result = fetch_top_companies("technology")

        assert result is None or result == []


# =============================================================================
# Tests for SectorContributor dataclass
# =============================================================================


class TestSectorContributorDataclass:
    """Tests for SectorContributor dataclass."""

    def test_正常系_インスタンス作成(self) -> None:
        """SectorContributor インスタンスを正しく作成できることを確認。"""
        contributor = SectorContributor(
            ticker="NVDA",
            name="NVIDIA Corporation",
            return_1w=0.052,
            weight=0.15,
        )

        assert contributor.ticker == "NVDA"
        assert contributor.name == "NVIDIA Corporation"
        assert contributor.return_1w == 0.052
        assert contributor.weight == 0.15

    def test_正常系_辞書変換(self) -> None:
        """SectorContributor を辞書に変換できることを確認。"""
        contributor = SectorContributor(
            ticker="AAPL",
            name="Apple Inc.",
            return_1w=0.018,
            weight=0.20,
        )

        result = contributor.to_dict()

        assert isinstance(result, dict)
        assert result["ticker"] == "AAPL"
        assert result["name"] == "Apple Inc."
        assert result["return_1w"] == 0.018
        assert result["weight"] == 0.20


# =============================================================================
# Tests for SectorInfo dataclass
# =============================================================================


class TestSectorInfoDataclass:
    """Tests for SectorInfo dataclass."""

    def test_正常系_インスタンス作成(self) -> None:
        """SectorInfo インスタンスを正しく作成できることを確認。"""
        contributors = [
            SectorContributor("NVDA", "NVIDIA", 0.05, 0.15),
            SectorContributor("AAPL", "Apple", 0.02, 0.20),
        ]

        sector_info = SectorInfo(
            name="Information Technology",
            key="technology",
            etf="XLK",
            return_1w=0.035,
            top_contributors=contributors,
        )

        assert sector_info.name == "Information Technology"
        assert sector_info.key == "technology"
        assert sector_info.etf == "XLK"
        assert sector_info.return_1w == 0.035
        assert len(sector_info.top_contributors) == 2

    def test_正常系_辞書変換(self) -> None:
        """SectorInfo を辞書に変換できることを確認。"""
        contributors = [
            SectorContributor("NVDA", "NVIDIA", 0.05, 0.15),
        ]

        sector_info = SectorInfo(
            name="Information Technology",
            key="technology",
            etf="XLK",
            return_1w=0.035,
            top_contributors=contributors,
        )

        result = sector_info.to_dict()

        assert isinstance(result, dict)
        assert result["name"] == "Information Technology"
        assert result["etf"] == "XLK"
        assert result["return_1w"] == 0.035
        assert isinstance(result["top_contributors"], list)


# =============================================================================
# Tests for SectorAnalysisResult dataclass
# =============================================================================


class TestSectorAnalysisResultDataclass:
    """Tests for SectorAnalysisResult dataclass."""

    def test_正常系_インスタンス作成(self) -> None:
        """SectorAnalysisResult インスタンスを正しく作成できることを確認。"""
        top_sectors = [
            SectorInfo("Tech", "technology", "XLK", 0.035, []),
        ]
        bottom_sectors = [
            SectorInfo("Energy", "energy", "XLE", -0.02, []),
        ]

        result = SectorAnalysisResult(
            as_of=datetime(2024, 6, 15, 16, 0, 0),
            top_sectors=top_sectors,
            bottom_sectors=bottom_sectors,
        )

        assert result.as_of == datetime(2024, 6, 15, 16, 0, 0)
        assert len(result.top_sectors) == 1
        assert len(result.bottom_sectors) == 1

    def test_正常系_辞書変換が出力形式に準拠(self) -> None:
        """SectorAnalysisResult の辞書変換がIssueの出力形式に準拠していることを確認。"""
        contributors = [
            SectorContributor("NVDA", "NVIDIA", 0.052, 0.15),
            SectorContributor("AAPL", "Apple", 0.018, 0.20),
        ]
        top_sectors = [
            SectorInfo(
                "Information Technology", "technology", "XLK", 0.025, contributors
            ),
        ]
        bottom_sectors = [
            SectorInfo("Energy", "energy", "XLE", -0.02, []),
        ]

        result = SectorAnalysisResult(
            as_of=datetime(2024, 6, 15, 16, 0, 0),
            top_sectors=top_sectors,
            bottom_sectors=bottom_sectors,
        )

        output = result.to_dict()

        # Issue仕様に準拠した構造を確認
        assert "top_sectors" in output
        assert "bottom_sectors" in output
        assert isinstance(output["top_sectors"], list)
        assert isinstance(output["bottom_sectors"], list)

        # top_sectorsの構造を確認
        top_sector = output["top_sectors"][0]
        assert "name" in top_sector
        assert "etf" in top_sector
        assert "return_1w" in top_sector
        assert "top_contributors" in top_sector

        # top_contributorsの構造を確認
        contributor = top_sector["top_contributors"][0]
        assert "ticker" in contributor
        assert "name" in contributor
        assert "return_1w" in contributor
        assert "weight" in contributor


# =============================================================================
# Tests for analyze_sector_performance function
# =============================================================================


class TestAnalyzeSectorPerformance:
    """Tests for analyze_sector_performance function (main function)."""

    @patch("market_analysis.analysis.sector.yf.download")
    @patch("market_analysis.analysis.sector.yf.Sector")
    def test_正常系_セクター分析結果を取得できる(
        self,
        mock_sector_class: MagicMock,
        mock_download: MagicMock,
        mock_yfinance_download: pd.DataFrame,
        mock_top_companies: list[dict[str, Any]],
    ) -> None:
        """analyze_sector_performance がセクター分析結果を返すことを確認。"""
        mock_download.return_value = mock_yfinance_download
        mock_sector = MagicMock()
        mock_sector.top_companies = pd.DataFrame(mock_top_companies)
        mock_sector_class.return_value = mock_sector

        result = analyze_sector_performance()

        assert isinstance(result, SectorAnalysisResult)

    @patch("market_analysis.analysis.sector.yf.download")
    @patch("market_analysis.analysis.sector.yf.Sector")
    def test_正常系_上位3セクターを含む(
        self,
        mock_sector_class: MagicMock,
        mock_download: MagicMock,
        mock_yfinance_download: pd.DataFrame,
        mock_top_companies: list[dict[str, Any]],
    ) -> None:
        """結果に上位3セクターが含まれることを確認。"""
        mock_download.return_value = mock_yfinance_download
        mock_sector = MagicMock()
        mock_sector.top_companies = pd.DataFrame(mock_top_companies)
        mock_sector_class.return_value = mock_sector

        result = analyze_sector_performance()

        assert len(result.top_sectors) == 3

    @patch("market_analysis.analysis.sector.yf.download")
    @patch("market_analysis.analysis.sector.yf.Sector")
    def test_正常系_下位3セクターを含む(
        self,
        mock_sector_class: MagicMock,
        mock_download: MagicMock,
        mock_yfinance_download: pd.DataFrame,
        mock_top_companies: list[dict[str, Any]],
    ) -> None:
        """結果に下位3セクターが含まれることを確認。"""
        mock_download.return_value = mock_yfinance_download
        mock_sector = MagicMock()
        mock_sector.top_companies = pd.DataFrame(mock_top_companies)
        mock_sector_class.return_value = mock_sector

        result = analyze_sector_performance()

        assert len(result.bottom_sectors) == 3

    @patch("market_analysis.analysis.sector.yf.download")
    @patch("market_analysis.analysis.sector.yf.Sector")
    def test_正常系_寄与銘柄が含まれる(
        self,
        mock_sector_class: MagicMock,
        mock_download: MagicMock,
        mock_yfinance_download: pd.DataFrame,
        mock_top_companies: list[dict[str, Any]],
    ) -> None:
        """各セクターに寄与銘柄（top_contributors）が含まれることを確認。"""
        mock_download.return_value = mock_yfinance_download
        mock_sector = MagicMock()
        mock_sector.top_companies = pd.DataFrame(mock_top_companies)
        mock_sector_class.return_value = mock_sector

        result = analyze_sector_performance()

        # 少なくとも1つのセクターに寄与銘柄がある
        has_contributors = any(
            len(sector.top_contributors) > 0
            for sector in result.top_sectors + result.bottom_sectors
        )
        assert has_contributors

    @patch("market_analysis.analysis.sector.yf.download")
    @patch("market_analysis.analysis.sector.yf.Sector")
    def test_正常系_指定日時でレポート生成(
        self,
        mock_sector_class: MagicMock,
        mock_download: MagicMock,
        mock_yfinance_download: pd.DataFrame,
        mock_top_companies: list[dict[str, Any]],
    ) -> None:
        """指定した日時で結果が生成されることを確認。"""
        mock_download.return_value = mock_yfinance_download
        mock_sector = MagicMock()
        mock_sector.top_companies = pd.DataFrame(mock_top_companies)
        mock_sector_class.return_value = mock_sector

        specified_time = datetime(2024, 6, 15, 16, 0, 0)
        result = analyze_sector_performance(as_of=specified_time)

        assert result.as_of == specified_time

    @patch("market_analysis.analysis.sector.yf.download")
    @patch("market_analysis.analysis.sector.yf.Sector")
    def test_正常系_JSON出力形式に準拠(
        self,
        mock_sector_class: MagicMock,
        mock_download: MagicMock,
        mock_yfinance_download: pd.DataFrame,
        mock_top_companies: list[dict[str, Any]],
    ) -> None:
        """結果がIssueで指定されたJSON出力形式に準拠していることを確認。"""
        mock_download.return_value = mock_yfinance_download
        mock_sector = MagicMock()
        mock_sector.top_companies = pd.DataFrame(mock_top_companies)
        mock_sector_class.return_value = mock_sector

        result = analyze_sector_performance()
        output = result.to_dict()

        # Issue #470 で指定された出力形式の検証
        assert "top_sectors" in output
        assert "bottom_sectors" in output

        # top_sectorsの各要素の構造を検証
        if output["top_sectors"]:
            sector = output["top_sectors"][0]
            assert "name" in sector
            assert "etf" in sector
            assert "return_1w" in sector
            assert "top_contributors" in sector


# =============================================================================
# Tests for edge cases and error handling
# =============================================================================


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    @patch("market_analysis.analysis.sector.yf.download")
    def test_エッジケース_一部セクターのデータ取得失敗(
        self,
        mock_download: MagicMock,
    ) -> None:
        """一部のセクターでデータ取得に失敗しても処理が継続することを確認。"""

        def side_effect(*args, **kwargs):
            ticker = args[0] if args else kwargs.get("tickers", "")
            if "XLE" in str(ticker):
                return pd.DataFrame()  # Energy ETF は空
            dates = pd.date_range("2024-01-01", periods=10, freq="B")
            prices = np.linspace(100, 105, 10)
            return pd.DataFrame({"Close": prices}, index=dates)

        mock_download.side_effect = side_effect

        result = fetch_sector_etf_returns()

        # Energyセクター以外はデータがある
        assert isinstance(result, dict)

    @patch("market_analysis.analysis.sector.yf.Sector")
    def test_エッジケース_top_companiesが空(
        self,
        mock_sector_class: MagicMock,
    ) -> None:
        """top_companies が空の場合でも処理が継続することを確認。"""
        mock_sector = MagicMock()
        mock_sector.top_companies = pd.DataFrame()  # 空のDataFrame
        mock_sector_class.return_value = mock_sector

        result = fetch_top_companies("technology")

        assert result is None or result == []

    def test_エッジケース_騰落率がゼロのセクター(self) -> None:
        """騰落率がゼロのセクターも正しくランキングされることを確認。"""
        returns = {
            "technology": 0.05,
            "financial-services": 0.0,  # ゼロ
            "healthcare": 0.02,
            "energy": -0.02,
        }

        top, bottom = get_top_bottom_sectors(returns, n=2)

        assert len(top) == 2
        assert len(bottom) == 2
        # financial-services (0.0) は中間に位置するはず

    @pytest.mark.parametrize(
        "period,expected_days",
        [
            (1, 1),  # 1日
            (5, 5),  # 1週間
            (21, 21),  # 1ヶ月
        ],
    )
    @patch("market_analysis.analysis.sector.yf.download")
    def test_パラメトライズ_様々な期間で騰落率を計算できる(
        self,
        mock_download: MagicMock,
        period: int,
        expected_days: int,
        mock_yfinance_download: pd.DataFrame,
    ) -> None:
        """様々な期間で騰落率を計算できることを確認。"""
        mock_download.return_value = mock_yfinance_download

        result = fetch_sector_etf_returns(period=period)

        assert isinstance(result, dict)
        assert len(result) == 11


# =============================================================================
# Tests for returns.calculate_return integration
# =============================================================================


class TestCalculateReturnIntegration:
    """Tests for integration with market_analysis.analysis.returns.calculate_return."""

    @patch("market_analysis.analysis.sector.calculate_return")
    @patch("market_analysis.analysis.sector.yf.download")
    def test_正常系_calculate_return関数を再利用(
        self,
        mock_download: MagicMock,
        mock_calculate_return: MagicMock,
        mock_yfinance_download: pd.DataFrame,
    ) -> None:
        """returns モジュールの calculate_return 関数を再利用することを確認。"""
        mock_download.return_value = mock_yfinance_download
        mock_calculate_return.return_value = 0.025

        _result = fetch_sector_etf_returns()

        # calculate_return が呼び出されることを確認
        assert mock_calculate_return.called

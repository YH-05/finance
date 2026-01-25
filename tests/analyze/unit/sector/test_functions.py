"""Unit tests for analyze.sector functions.

This module tests the functions used in sector analysis:
- fetch_sector_etf_returns: Fetch ETF returns for all 11 sectors
- get_top_bottom_sectors: Get top/bottom N sectors by return
- fetch_top_companies: Fetch top companies for a sector
- analyze_sector_performance: Main analysis function
- _build_sector_info_list: Helper to build SectorInfo list
- _build_contributors: Helper to build SectorContributor list

Note: These tests are in TDD Red state - they will fail until the
analyze.sector module is implemented.

All yfinance calls are mocked to avoid external API dependencies.
"""

from datetime import datetime
from typing import Any
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

# NOTE: analyze パッケージはまだ存在しないため、インポートは失敗する（Red 状態）
from analyze.sector import (
    SECTOR_ETF_MAP,
    SECTOR_KEYS,
    SECTOR_NAMES,
    SectorAnalysisResult,
    SectorContributor,
    _build_contributors,
    _build_sector_info_list,
    analyze_sector_performance,
    fetch_sector_etf_returns,
    fetch_top_companies,
    get_top_bottom_sectors,
)


class TestFetchSectorEtfReturns:
    """Test fetch_sector_etf_returns function."""

    @patch("analyze.sector.sector.yf.download")
    def test_正常系_全セクターのリターン取得(
        self,
        mock_download: MagicMock,
        mock_price_dataframe: pd.DataFrame,
    ) -> None:
        """全11セクターのETFリターンが取得されることを確認。"""
        mock_download.return_value = mock_price_dataframe

        result = fetch_sector_etf_returns()

        # 全セクターキーが結果に含まれることを確認
        assert len(result) == len(SECTOR_KEYS)
        for key in SECTOR_KEYS:
            assert key in result

    @patch("analyze.sector.sector.yf.download")
    def test_正常系_カスタム期間指定でリターン取得(
        self,
        mock_download: MagicMock,
        mock_price_dataframe: pd.DataFrame,
    ) -> None:
        """カスタム期間（10営業日）でリターンが取得されることを確認。"""
        mock_download.return_value = mock_price_dataframe

        result = fetch_sector_etf_returns(period=10)

        assert len(result) == len(SECTOR_KEYS)
        # period=10 でも呼び出しは正常に行われる
        mock_download.assert_called_once()

    @patch("analyze.sector.sector.yf.download")
    def test_エッジケース_データなしでNone値を返す(
        self,
        mock_download: MagicMock,
    ) -> None:
        """yfinance からデータが返らない場合、全セクターが None になることを確認。"""
        mock_download.return_value = pd.DataFrame()

        result = fetch_sector_etf_returns()

        assert len(result) == len(SECTOR_KEYS)
        for key in SECTOR_KEYS:
            assert result[key] is None

    @patch("analyze.sector.sector.yf.download")
    def test_異常系_yfinanceエラーでNone値を返す(
        self,
        mock_download: MagicMock,
    ) -> None:
        """yfinance がエラーを発生させた場合、全セクターが None になることを確認。"""
        mock_download.side_effect = Exception("API Error")

        result = fetch_sector_etf_returns()

        assert len(result) == len(SECTOR_KEYS)
        for key in SECTOR_KEYS:
            assert result[key] is None


class TestGetTopBottomSectors:
    """Test get_top_bottom_sectors function."""

    def test_正常系_トップNとボトムNセクター取得(
        self,
        mock_etf_returns: dict[str, float | None],
    ) -> None:
        """トップ3とボトム3のセクターが正しく取得されることを確認。"""
        top, bottom = get_top_bottom_sectors(mock_etf_returns, n=3)

        # トップ3の検証
        assert len(top) == 3
        # リターン降順で technology が最大
        assert top[0][0] == "technology"
        assert top[0][1] == 0.035

        # ボトム3の検証
        assert len(bottom) == 3
        # リターン昇順で real-estate が最小
        assert bottom[0][0] == "real-estate"
        assert bottom[0][1] == -0.015

    def test_正常系_n1でトップ1ボトム1取得(
        self,
        mock_etf_returns: dict[str, float | None],
    ) -> None:
        """n=1 でトップ1とボトム1のセクターが取得されることを確認。"""
        top, bottom = get_top_bottom_sectors(mock_etf_returns, n=1)

        assert len(top) == 1
        assert len(bottom) == 1
        assert top[0][0] == "technology"
        assert bottom[0][0] == "real-estate"

    def test_異常系_nが0でValueError(
        self,
        mock_etf_returns: dict[str, float | None],
    ) -> None:
        """n が 0 の場合、ValueError が発生することを確認。"""
        with pytest.raises(ValueError, match="n must be positive"):
            get_top_bottom_sectors(mock_etf_returns, n=0)

    def test_異常系_nが負でValueError(
        self,
        mock_etf_returns: dict[str, float | None],
    ) -> None:
        """n が負の場合、ValueError が発生することを確認。"""
        with pytest.raises(ValueError, match="n must be positive"):
            get_top_bottom_sectors(mock_etf_returns, n=-1)

    def test_エッジケース_空のマッピングで空タプル(self) -> None:
        """空のマッピングが渡された場合、空のタプルが返されることを確認。"""
        top, bottom = get_top_bottom_sectors({}, n=3)

        assert top == []
        assert bottom == []

    def test_エッジケース_None値を含むマッピング(
        self,
        mock_etf_returns_with_none: dict[str, float | None],
    ) -> None:
        """None 値を含むマッピングが渡された場合、None を除外して処理することを確認。"""
        top, bottom = get_top_bottom_sectors(mock_etf_returns_with_none, n=3)

        # None 値は除外される
        assert len(top) == 3
        assert len(bottom) == 3

        # None 値を含むセクターは結果に含まれない
        all_keys = [k for k, _ in top] + [k for k, _ in bottom]
        assert "communication-services" not in all_keys
        assert "consumer-defensive" not in all_keys
        assert "healthcare" not in all_keys

    def test_正常系_nがセクター数より大きい場合(self) -> None:
        """n がセクター数より大きい場合、利用可能な全セクターを返すことを確認。"""
        small_returns = {
            "technology": 0.035,
            "energy": -0.012,
        }

        top, bottom = get_top_bottom_sectors(small_returns, n=5)

        # 利用可能なセクター数に制限される
        assert len(top) == 2
        assert len(bottom) == 2


class TestFetchTopCompanies:
    """Test fetch_top_companies function."""

    @patch("analyze.sector.sector.yf.Sector")
    def test_正常系_セクターのトップ企業取得(
        self,
        mock_sector_class: MagicMock,
        mock_top_companies: list[dict[str, Any]],
    ) -> None:
        """セクターのトップ企業が取得されることを確認。"""
        # モックの設定
        mock_sector_instance = MagicMock()
        mock_df = pd.DataFrame(mock_top_companies)
        mock_df = mock_df.set_index("symbol")
        mock_df = mock_df.rename(columns={"weight": "market weight"})
        mock_sector_instance.top_companies = mock_df
        mock_sector_class.return_value = mock_sector_instance

        result = fetch_top_companies("technology")

        assert result is not None
        assert len(result) == 5
        # 最初の企業が NVDA であることを確認
        first_company = result[0]
        assert first_company["symbol"] == "NVDA"

    @patch("analyze.sector.sector.yf.Sector")
    def test_エッジケース_データなしでNone(
        self,
        mock_sector_class: MagicMock,
    ) -> None:
        """yf.Sector からデータが返らない場合、None を返すことを確認。"""
        mock_sector_instance = MagicMock()
        mock_sector_instance.top_companies = None
        mock_sector_class.return_value = mock_sector_instance

        result = fetch_top_companies("technology")

        assert result is None

    @patch("analyze.sector.sector.yf.Sector")
    def test_エッジケース_空DataFrameでNone(
        self,
        mock_sector_class: MagicMock,
    ) -> None:
        """空の DataFrame が返された場合、None を返すことを確認。"""
        mock_sector_instance = MagicMock()
        mock_sector_instance.top_companies = pd.DataFrame()
        mock_sector_class.return_value = mock_sector_instance

        result = fetch_top_companies("technology")

        assert result is None

    @patch("analyze.sector.sector.yf.Sector")
    def test_異常系_yfinanceエラーでNone(
        self,
        mock_sector_class: MagicMock,
    ) -> None:
        """yfinance がエラーを発生させた場合、None を返すことを確認。"""
        mock_sector_class.side_effect = Exception("API Error")

        result = fetch_top_companies("technology")

        assert result is None


class TestAnalyzeSectorPerformance:
    """Test analyze_sector_performance function."""

    @patch("analyze.sector.sector.fetch_top_companies")
    @patch("analyze.sector.sector.fetch_sector_etf_returns")
    def test_正常系_セクターパフォーマンス分析(
        self,
        mock_fetch_returns: MagicMock,
        mock_fetch_companies: MagicMock,
        mock_etf_returns: dict[str, float | None],
        sample_as_of: datetime,
    ) -> None:
        """セクターパフォーマンス分析が正常に実行されることを確認。"""
        mock_fetch_returns.return_value = mock_etf_returns
        mock_fetch_companies.return_value = None  # 簡略化

        result = analyze_sector_performance(as_of=sample_as_of)

        assert isinstance(result, SectorAnalysisResult)
        assert result.as_of == sample_as_of
        assert len(result.top_sectors) == 3
        assert len(result.bottom_sectors) == 3

    @patch("analyze.sector.sector.fetch_top_companies")
    @patch("analyze.sector.sector.fetch_sector_etf_returns")
    def test_正常系_カスタムn_sectors指定(
        self,
        mock_fetch_returns: MagicMock,
        mock_fetch_companies: MagicMock,
        mock_etf_returns: dict[str, float | None],
    ) -> None:
        """カスタム n_sectors でセクター数が変わることを確認。"""
        mock_fetch_returns.return_value = mock_etf_returns
        mock_fetch_companies.return_value = None

        result = analyze_sector_performance(n_sectors=5)

        assert len(result.top_sectors) == 5
        assert len(result.bottom_sectors) == 5

    @patch("analyze.sector.sector.fetch_top_companies")
    @patch("analyze.sector.sector.fetch_sector_etf_returns")
    def test_正常系_as_ofなしで現在時刻が使用される(
        self,
        mock_fetch_returns: MagicMock,
        mock_fetch_companies: MagicMock,
        mock_etf_returns: dict[str, float | None],
    ) -> None:
        """as_of が指定されない場合、現在時刻が使用されることを確認。"""
        mock_fetch_returns.return_value = mock_etf_returns
        mock_fetch_companies.return_value = None

        before = datetime.now()
        result = analyze_sector_performance()
        after = datetime.now()

        assert before <= result.as_of <= after

    @patch("analyze.sector.sector.fetch_top_companies")
    @patch("analyze.sector.sector.fetch_sector_etf_returns")
    def test_正常系_トップセクターが正しくソートされる(
        self,
        mock_fetch_returns: MagicMock,
        mock_fetch_companies: MagicMock,
        mock_etf_returns: dict[str, float | None],
    ) -> None:
        """トップセクターがリターン降順でソートされることを確認。"""
        mock_fetch_returns.return_value = mock_etf_returns
        mock_fetch_companies.return_value = None

        result = analyze_sector_performance(n_sectors=3)

        # トップセクターはリターン降順
        assert result.top_sectors[0].return_1w >= result.top_sectors[1].return_1w
        assert result.top_sectors[1].return_1w >= result.top_sectors[2].return_1w

    @patch("analyze.sector.sector.fetch_top_companies")
    @patch("analyze.sector.sector.fetch_sector_etf_returns")
    def test_正常系_ボトムセクターが正しくソートされる(
        self,
        mock_fetch_returns: MagicMock,
        mock_fetch_companies: MagicMock,
        mock_etf_returns: dict[str, float | None],
    ) -> None:
        """ボトムセクターがリターン昇順でソートされることを確認。"""
        mock_fetch_returns.return_value = mock_etf_returns
        mock_fetch_companies.return_value = None

        result = analyze_sector_performance(n_sectors=3)

        # ボトムセクターはリターン昇順
        assert result.bottom_sectors[0].return_1w <= result.bottom_sectors[1].return_1w
        assert result.bottom_sectors[1].return_1w <= result.bottom_sectors[2].return_1w


class TestBuildSectorInfoList:
    """Test _build_sector_info_list helper function."""

    @patch("analyze.sector.sector.fetch_top_companies")
    def test_正常系_SectorInfoリスト構築(
        self,
        mock_fetch_companies: MagicMock,
    ) -> None:
        """SectorInfo リストが正しく構築されることを確認。"""
        mock_fetch_companies.return_value = None

        sectors_raw = [
            ("technology", 0.035),
            ("financial-services", 0.018),
        ]

        result = _build_sector_info_list(sectors_raw)

        assert len(result) == 2
        assert result[0].key == "technology"
        assert result[0].return_1w == 0.035
        assert result[0].name == SECTOR_NAMES["technology"]
        assert result[0].etf == SECTOR_ETF_MAP["technology"]

        assert result[1].key == "financial-services"
        assert result[1].return_1w == 0.018

    @patch("analyze.sector.sector.fetch_top_companies")
    def test_エッジケース_空リストで空結果(
        self,
        mock_fetch_companies: MagicMock,
    ) -> None:
        """空のリストが渡された場合、空の結果が返されることを確認。"""
        result = _build_sector_info_list([])

        assert result == []

    @patch("analyze.sector.sector._build_contributors")
    @patch("analyze.sector.sector.fetch_top_companies")
    def test_正常系_top_companiesありでcontributorsが設定される(
        self,
        mock_fetch_companies: MagicMock,
        mock_build_contributors: MagicMock,
        mock_top_companies: list[dict[str, Any]],
    ) -> None:
        """fetch_top_companies がデータを返す場合、contributors が設定されることを確認。"""
        mock_fetch_companies.return_value = mock_top_companies
        mock_contributors = [
            SectorContributor("NVDA", "NVIDIA", 0.052, 0.15),
        ]
        mock_build_contributors.return_value = mock_contributors

        sectors_raw = [("technology", 0.035)]

        result = _build_sector_info_list(sectors_raw)

        assert len(result) == 1
        assert result[0].top_contributors == mock_contributors


class TestBuildContributors:
    """Test _build_contributors helper function."""

    @patch("analyze.sector.sector.yf.download")
    def test_正常系_SectorContributorリスト構築(
        self,
        mock_download: MagicMock,
        mock_top_companies: list[dict[str, Any]],
    ) -> None:
        """SectorContributor リストが正しく構築されることを確認。"""
        # 株価データのモック
        dates = pd.date_range(start="2024-01-01", periods=30, freq="B")
        price_data = {
            sym: [100 + i * 0.5 for i in range(30)]
            for sym in ["NVDA", "AAPL", "MSFT", "GOOGL", "META"]
        }
        df = pd.DataFrame(price_data, index=dates)
        df.columns = pd.MultiIndex.from_product([["Close"], df.columns])
        mock_download.return_value = df

        result = _build_contributors(mock_top_companies)

        assert len(result) == 5
        assert result[0].ticker == "NVDA"
        assert result[0].name == "NVIDIA Corporation"
        assert result[0].weight == 0.15

    def test_エッジケース_空リストで空結果(self) -> None:
        """空のリストが渡された場合、空の結果が返されることを確認。"""
        result = _build_contributors([])

        assert result == []

    @patch("analyze.sector.sector.yf.download")
    def test_正常系_max_contributors制限(
        self,
        mock_download: MagicMock,
        mock_top_companies: list[dict[str, Any]],
    ) -> None:
        """max_contributors で結果の数が制限されることを確認。"""
        # 株価データのモック
        dates = pd.date_range(start="2024-01-01", periods=30, freq="B")
        price_data = {
            sym: [100 + i * 0.5 for i in range(30)] for sym in ["NVDA", "AAPL", "MSFT"]
        }
        df = pd.DataFrame(price_data, index=dates)
        df.columns = pd.MultiIndex.from_product([["Close"], df.columns])
        mock_download.return_value = df

        result = _build_contributors(mock_top_companies, max_contributors=3)

        assert len(result) == 3

    @patch("analyze.sector.sector.yf.download")
    def test_正常系_カスタムperiod指定(
        self,
        mock_download: MagicMock,
        mock_top_companies: list[dict[str, Any]],
    ) -> None:
        """カスタム period でリターン計算が行われることを確認。"""
        dates = pd.date_range(start="2024-01-01", periods=30, freq="B")
        price_data = {"NVDA": [100 + i * 0.5 for i in range(30)]}
        df = pd.DataFrame(price_data, index=dates)
        df.columns = pd.MultiIndex.from_product([["Close"], df.columns])
        mock_download.return_value = df

        result = _build_contributors(
            mock_top_companies[:1],
            max_contributors=1,
            period=10,
        )

        assert len(result) == 1
        # リターン計算は calculate_return に依存（ここではモック）

    @patch("analyze.sector.sector.yf.download")
    def test_エッジケース_yfinanceエラーでリターン0(
        self,
        mock_download: MagicMock,
        mock_top_companies: list[dict[str, Any]],
    ) -> None:
        """yfinance がエラーを発生させた場合、リターンが 0 になることを確認。"""
        mock_download.side_effect = Exception("API Error")

        result = _build_contributors(mock_top_companies[:2], max_contributors=2)

        assert len(result) == 2
        for contributor in result:
            assert contributor.return_1w == 0.0


class TestConstants:
    """Test module constants."""

    def test_正常系_SECTOR_KEYSが11セクター(self) -> None:
        """SECTOR_KEYS が 11 セクター含むことを確認。"""
        assert len(SECTOR_KEYS) == 11

    def test_正常系_SECTOR_ETF_MAPが11エントリ(self) -> None:
        """SECTOR_ETF_MAP が 11 エントリ含むことを確認。"""
        assert len(SECTOR_ETF_MAP) == 11

    def test_正常系_SECTOR_NAMESが11エントリ(self) -> None:
        """SECTOR_NAMES が 11 エントリ含むことを確認。"""
        assert len(SECTOR_NAMES) == 11

    def test_正常系_全キーが一致(self) -> None:
        """SECTOR_KEYS, SECTOR_ETF_MAP, SECTOR_NAMES のキーが一致することを確認。"""
        assert set(SECTOR_KEYS) == set(SECTOR_ETF_MAP.keys())
        assert set(SECTOR_KEYS) == set(SECTOR_NAMES.keys())

    def test_正常系_主要セクターが含まれる(self) -> None:
        """主要セクターがすべて含まれていることを確認。"""
        expected_sectors = [
            "technology",
            "healthcare",
            "financial-services",
            "energy",
        ]
        for sector in expected_sectors:
            assert sector in SECTOR_KEYS

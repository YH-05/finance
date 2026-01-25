"""Unit tests for analyze.sector dataclasses.

This module tests the dataclasses used in sector analysis:
- SectorContributor: Represents a contributing stock within a sector
- SectorInfo: Represents sector information with performance data
- SectorAnalysisResult: Result of sector performance analysis

Note: These tests are in TDD Red state - they will fail until the
analyze.sector module is implemented.
"""

from datetime import datetime

# NOTE: analyze パッケージはまだ存在しないため、インポートは失敗する（Red 状態）
from analyze.sector import (
    SectorAnalysisResult,
    SectorContributor,
    SectorInfo,
)


class TestSectorContributor:
    """Test SectorContributor dataclass."""

    def test_正常系_基本的な属性で初期化される(self) -> None:
        """SectorContributor が基本的な属性で初期化されることを確認。"""
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

    def test_正常系_to_dictで正しく辞書変換される(self) -> None:
        """to_dict() が正しく辞書に変換することを確認。"""
        contributor = SectorContributor(
            ticker="AAPL",
            name="Apple Inc.",
            return_1w=0.035,
            weight=0.12,
        )

        result = contributor.to_dict()

        expected = {
            "ticker": "AAPL",
            "name": "Apple Inc.",
            "return_1w": 0.035,
            "weight": 0.12,
        }
        assert result == expected

    def test_正常系_マイナスリターンでも初期化される(self) -> None:
        """マイナスのリターンでも SectorContributor が初期化されることを確認。"""
        contributor = SectorContributor(
            ticker="XOM",
            name="Exxon Mobil",
            return_1w=-0.025,
            weight=0.08,
        )

        assert contributor.return_1w == -0.025
        assert contributor.to_dict()["return_1w"] == -0.025

    def test_正常系_ゼロリターンでも初期化される(self) -> None:
        """ゼロのリターンでも SectorContributor が初期化されることを確認。"""
        contributor = SectorContributor(
            ticker="TEST",
            name="Test Corp",
            return_1w=0.0,
            weight=0.05,
        )

        assert contributor.return_1w == 0.0


class TestSectorInfo:
    """Test SectorInfo dataclass."""

    def test_正常系_基本的な属性で初期化される(self) -> None:
        """SectorInfo が基本的な属性で初期化されることを確認。"""
        sector = SectorInfo(
            name="Information Technology",
            key="technology",
            etf="XLK",
            return_1w=0.025,
        )

        assert sector.name == "Information Technology"
        assert sector.key == "technology"
        assert sector.etf == "XLK"
        assert sector.return_1w == 0.025
        assert sector.top_contributors == []

    def test_正常系_top_contributorsありで初期化される(self) -> None:
        """top_contributors を指定して SectorInfo が初期化されることを確認。"""
        contributors = [
            SectorContributor("NVDA", "NVIDIA", 0.052, 0.15),
            SectorContributor("AAPL", "Apple", 0.035, 0.12),
        ]

        sector = SectorInfo(
            name="Information Technology",
            key="technology",
            etf="XLK",
            return_1w=0.025,
            top_contributors=contributors,
        )

        assert len(sector.top_contributors) == 2
        assert sector.top_contributors[0].ticker == "NVDA"
        assert sector.top_contributors[1].ticker == "AAPL"

    def test_正常系_to_dictで空リストが正しく変換される(self) -> None:
        """to_dict() が空の top_contributors を正しく変換することを確認。"""
        sector = SectorInfo(
            name="Energy",
            key="energy",
            etf="XLE",
            return_1w=-0.015,
        )

        result = sector.to_dict()

        expected = {
            "name": "Energy",
            "etf": "XLE",
            "return_1w": -0.015,
            "top_contributors": [],
        }
        assert result == expected

    def test_正常系_to_dictでcontributorsありが正しく変換される(self) -> None:
        """to_dict() が top_contributors を正しく変換することを確認。"""
        contributors = [
            SectorContributor("NVDA", "NVIDIA", 0.052, 0.15),
        ]

        sector = SectorInfo(
            name="Information Technology",
            key="technology",
            etf="XLK",
            return_1w=0.025,
            top_contributors=contributors,
        )

        result = sector.to_dict()

        assert len(result["top_contributors"]) == 1
        assert result["top_contributors"][0] == {
            "ticker": "NVDA",
            "name": "NVIDIA",
            "return_1w": 0.052,
            "weight": 0.15,
        }


class TestSectorAnalysisResult:
    """Test SectorAnalysisResult dataclass."""

    def test_正常系_基本的な属性で初期化される(self) -> None:
        """SectorAnalysisResult が基本的な属性で初期化されることを確認。"""
        as_of = datetime(2024, 1, 15, 10, 30, 0)

        result = SectorAnalysisResult(as_of=as_of)

        assert result.as_of == as_of
        assert result.top_sectors == []
        assert result.bottom_sectors == []

    def test_正常系_top_sectorsとbottom_sectorsありで初期化される(self) -> None:
        """top_sectors と bottom_sectors を指定して初期化されることを確認。"""
        as_of = datetime(2024, 1, 15)

        top_sectors = [
            SectorInfo("Technology", "technology", "XLK", 0.035),
            SectorInfo("Financials", "financial-services", "XLF", 0.018),
        ]
        bottom_sectors = [
            SectorInfo("Real Estate", "real-estate", "XLRE", -0.015),
            SectorInfo("Energy", "energy", "XLE", -0.012),
        ]

        result = SectorAnalysisResult(
            as_of=as_of,
            top_sectors=top_sectors,
            bottom_sectors=bottom_sectors,
        )

        assert len(result.top_sectors) == 2
        assert len(result.bottom_sectors) == 2
        assert result.top_sectors[0].name == "Technology"
        assert result.bottom_sectors[0].name == "Real Estate"

    def test_正常系_to_dictで空リストが正しく変換される(self) -> None:
        """to_dict() が空のリストを正しく変換することを確認。"""
        as_of = datetime(2024, 1, 15)

        result = SectorAnalysisResult(as_of=as_of)

        dict_result = result.to_dict()

        expected = {
            "top_sectors": [],
            "bottom_sectors": [],
        }
        assert dict_result == expected

    def test_正常系_to_dictでセクターありが正しく変換される(self) -> None:
        """to_dict() が top_sectors と bottom_sectors を正しく変換することを確認。"""
        as_of = datetime(2024, 1, 15)

        top_sectors = [
            SectorInfo("Technology", "technology", "XLK", 0.035),
        ]
        bottom_sectors = [
            SectorInfo("Energy", "energy", "XLE", -0.012),
        ]

        result = SectorAnalysisResult(
            as_of=as_of,
            top_sectors=top_sectors,
            bottom_sectors=bottom_sectors,
        )

        dict_result = result.to_dict()

        assert len(dict_result["top_sectors"]) == 1
        assert len(dict_result["bottom_sectors"]) == 1
        assert dict_result["top_sectors"][0]["name"] == "Technology"
        assert dict_result["bottom_sectors"][0]["name"] == "Energy"

    def test_正常系_ネストした構造が正しく変換される(self) -> None:
        """to_dict() がネストした構造を正しく変換することを確認。"""
        as_of = datetime(2024, 1, 15)

        contributors = [
            SectorContributor("NVDA", "NVIDIA", 0.052, 0.15),
        ]
        top_sectors = [
            SectorInfo("Technology", "technology", "XLK", 0.035, contributors),
        ]

        result = SectorAnalysisResult(
            as_of=as_of,
            top_sectors=top_sectors,
        )

        dict_result = result.to_dict()

        # ネストした構造の検証
        assert len(dict_result["top_sectors"]) == 1
        sector_dict = dict_result["top_sectors"][0]
        assert len(sector_dict["top_contributors"]) == 1
        assert sector_dict["top_contributors"][0]["ticker"] == "NVDA"

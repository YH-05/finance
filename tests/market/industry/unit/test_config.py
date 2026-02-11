"""Unit tests for market.industry.config module.

Tests cover preset JSON loading, validation, sector lookup,
and error handling for missing or malformed configuration files.
"""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from market.industry.config import (
    IndustryPreset,
    IndustryPresetsConfig,
    SourceConfig,
    load_presets,
)


class TestSourceConfig:
    """Tests for SourceConfig Pydantic model."""

    def test_正常系_ソース設定を作成できる(self) -> None:
        source = SourceConfig(
            name="McKinsey Insights",
            url="https://mckinsey.com/featured-insights",
            tier="scraping",
            difficulty="medium",
            enabled=True,
        )
        assert source.name == "McKinsey Insights"
        assert source.url == "https://mckinsey.com/featured-insights"
        assert source.tier == "scraping"
        assert source.enabled is True

    def test_正常系_デフォルト値が適用される(self) -> None:
        source = SourceConfig(
            name="BLS API",
            url="https://api.bls.gov/publicAPI/v2/timeseries/data/",
            tier="api",
        )
        assert source.difficulty is None
        assert source.enabled is True


class TestIndustryPreset:
    """Tests for IndustryPreset Pydantic model."""

    def test_正常系_プリセットを作成できる(self) -> None:
        preset = IndustryPreset(
            sector="Technology",
            sub_sectors=["Semiconductors", "Software_Infrastructure"],
            sources=[
                SourceConfig(
                    name="McKinsey",
                    url="https://mckinsey.com/insights",
                    tier="scraping",
                ),
            ],
            peer_tickers=["NVDA", "AMD", "INTC"],
        )
        assert preset.sector == "Technology"
        assert len(preset.sub_sectors) == 2
        assert len(preset.sources) == 1
        assert "NVDA" in preset.peer_tickers

    def test_正常系_peer_tickersのデフォルトは空リスト(self) -> None:
        preset = IndustryPreset(
            sector="Energy",
            sub_sectors=["Oil_Gas"],
            sources=[],
        )
        assert preset.peer_tickers == []


class TestIndustryPresetsConfig:
    """Tests for IndustryPresetsConfig Pydantic model."""

    def test_正常系_設定全体を作成できる(self) -> None:
        config = IndustryPresetsConfig(
            version="1.0",
            presets=[
                IndustryPreset(
                    sector="Technology",
                    sub_sectors=["Semiconductors"],
                    sources=[],
                ),
            ],
        )
        assert config.version == "1.0"
        assert len(config.presets) == 1

    def test_正常系_get_sectorでセクターを取得できる(self) -> None:
        config = IndustryPresetsConfig(
            version="1.0",
            presets=[
                IndustryPreset(
                    sector="Technology",
                    sub_sectors=["Semiconductors"],
                    sources=[],
                ),
                IndustryPreset(
                    sector="Healthcare",
                    sub_sectors=["Pharmaceuticals"],
                    sources=[],
                ),
            ],
        )
        tech = config.get_sector("Technology")
        assert tech is not None
        assert tech.sector == "Technology"

    def test_正常系_get_sectorで存在しないセクターはNone(self) -> None:
        config = IndustryPresetsConfig(
            version="1.0",
            presets=[],
        )
        assert config.get_sector("NonExistent") is None

    def test_正常系_sector_namesでセクター名一覧を取得できる(self) -> None:
        config = IndustryPresetsConfig(
            version="1.0",
            presets=[
                IndustryPreset(
                    sector="Technology",
                    sub_sectors=[],
                    sources=[],
                ),
                IndustryPreset(
                    sector="Healthcare",
                    sub_sectors=[],
                    sources=[],
                ),
            ],
        )
        names = config.sector_names
        assert names == ["Technology", "Healthcare"]


class TestLoadPresets:
    """Tests for load_presets function."""

    def test_正常系_JSONファイルからプリセットを読み込める(
        self, tmp_path: Path
    ) -> None:
        preset_data = {
            "version": "1.0",
            "presets": [
                {
                    "sector": "Technology",
                    "sub_sectors": ["Semiconductors"],
                    "sources": [
                        {
                            "name": "McKinsey",
                            "url": "https://mckinsey.com/insights",
                            "tier": "scraping",
                            "difficulty": "medium",
                            "enabled": True,
                        },
                    ],
                    "peer_tickers": ["NVDA", "AMD"],
                },
            ],
        }
        config_file = tmp_path / "test-presets.json"
        config_file.write_text(json.dumps(preset_data, ensure_ascii=False))

        config = load_presets(config_file)
        assert config.version == "1.0"
        assert len(config.presets) == 1
        assert config.presets[0].sector == "Technology"

    def test_異常系_ファイルが存在しない場合FileNotFoundError(self) -> None:
        with pytest.raises(FileNotFoundError):
            load_presets(Path("/nonexistent/path/presets.json"))

    def test_異常系_不正なJSONでValueError(self, tmp_path: Path) -> None:
        bad_file = tmp_path / "bad.json"
        bad_file.write_text("{invalid json")

        with pytest.raises(ValueError, match="Failed to parse"):
            load_presets(bad_file)

    def test_正常系_デフォルトパスから読み込める(self, tmp_path: Path) -> None:
        """load_presets with no argument uses the default config path."""
        preset_data = {
            "version": "1.0",
            "presets": [],
        }
        config_file = tmp_path / "industry-research-presets.json"
        config_file.write_text(json.dumps(preset_data))

        with patch(
            "market.industry.config.DEFAULT_PRESETS_PATH",
            config_file,
        ):
            config = load_presets()
            assert config.version == "1.0"

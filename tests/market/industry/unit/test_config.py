"""Unit tests for market.industry.config module.

Tests cover preset JSON loading, validation, sector lookup,
expanded preset fields (peer_groups, scraping_queries, competitive_factors,
industry_media, key_metrics), and error handling for missing or malformed
configuration files.
"""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from market.industry.config import (
    CompetitiveFactorConfig,
    IndustryMediaConfig,
    IndustryPreset,
    IndustryPresetsConfig,
    KeyMetricConfig,
    PeerGroupConfig,
    ScrapingQueryConfig,
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


class TestPeerGroupConfig:
    """Tests for PeerGroupConfig Pydantic model."""

    def test_正常系_ピアグループ設定を作成できる(self) -> None:
        group = PeerGroupConfig(
            sub_sector="Semiconductors",
            companies=["NVDA", "AMD", "INTC", "TSM", "AVGO"],
            description="Major semiconductor manufacturers",
        )
        assert group.sub_sector == "Semiconductors"
        assert len(group.companies) == 5
        assert "NVDA" in group.companies
        assert group.description == "Major semiconductor manufacturers"

    def test_正常系_descriptionのデフォルトはNone(self) -> None:
        group = PeerGroupConfig(
            sub_sector="Banks",
            companies=["JPM", "BAC", "GS"],
        )
        assert group.description is None


class TestScrapingQueryConfig:
    """Tests for ScrapingQueryConfig Pydantic model."""

    def test_正常系_スクレイピングクエリを作成できる(self) -> None:
        query = ScrapingQueryConfig(
            query="semiconductor industry outlook 2026",
            target_sources=["McKinsey", "BCG"],
            sector_specific=True,
        )
        assert query.query == "semiconductor industry outlook 2026"
        assert len(query.target_sources) == 2
        assert query.sector_specific is True

    def test_正常系_デフォルト値が適用される(self) -> None:
        query = ScrapingQueryConfig(
            query="industry trends",
        )
        assert query.target_sources == []
        assert query.sector_specific is False


class TestCompetitiveFactorConfig:
    """Tests for CompetitiveFactorConfig Pydantic model."""

    def test_正常系_競争要因を作成できる(self) -> None:
        factor = CompetitiveFactorConfig(
            factor_name="R&D Investment",
            description="Annual R&D spending as percentage of revenue",
            importance="high",
        )
        assert factor.factor_name == "R&D Investment"
        assert factor.importance == "high"

    def test_正常系_importanceのデフォルトはmedium(self) -> None:
        factor = CompetitiveFactorConfig(
            factor_name="Brand Recognition",
            description="Consumer brand awareness level",
        )
        assert factor.importance == "medium"


class TestIndustryMediaConfig:
    """Tests for IndustryMediaConfig Pydantic model."""

    def test_正常系_業界メディアを作成できる(self) -> None:
        media = IndustryMediaConfig(
            name="TechCrunch",
            url="https://techcrunch.com",
            focus_areas=["startups", "AI", "semiconductors"],
        )
        assert media.name == "TechCrunch"
        assert len(media.focus_areas) == 3

    def test_正常系_focus_areasのデフォルトは空リスト(self) -> None:
        media = IndustryMediaConfig(
            name="Bloomberg",
            url="https://bloomberg.com",
        )
        assert media.focus_areas == []


class TestKeyMetricConfig:
    """Tests for KeyMetricConfig Pydantic model."""

    def test_正常系_キーメトリクスを作成できる(self) -> None:
        metric = KeyMetricConfig(
            name="Gross Margin",
            description="Revenue minus cost of goods sold divided by revenue",
            data_source="SEC filings",
        )
        assert metric.name == "Gross Margin"
        assert metric.data_source == "SEC filings"

    def test_正常系_data_sourceのデフォルトはNone(self) -> None:
        metric = KeyMetricConfig(
            name="Revenue Growth",
            description="Year-over-year revenue growth rate",
        )
        assert metric.data_source is None


class TestExpandedIndustryPreset:
    """Tests for IndustryPreset with expanded fields."""

    def test_正常系_拡張フィールド付きプリセットを作成できる(self) -> None:
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
            peer_groups=[
                PeerGroupConfig(
                    sub_sector="Semiconductors",
                    companies=["NVDA", "AMD", "INTC", "TSM", "AVGO"],
                    description="Major semiconductor manufacturers",
                ),
            ],
            scraping_queries=[
                ScrapingQueryConfig(
                    query="semiconductor industry outlook",
                    target_sources=["McKinsey"],
                    sector_specific=True,
                ),
            ],
            competitive_factors=[
                CompetitiveFactorConfig(
                    factor_name="R&D Investment",
                    description="Annual R&D spending",
                    importance="high",
                ),
            ],
            industry_media=[
                IndustryMediaConfig(
                    name="SemiWiki",
                    url="https://semiwiki.com",
                    focus_areas=["semiconductors"],
                ),
            ],
            key_metrics=[
                KeyMetricConfig(
                    name="Gross Margin",
                    description="Gross margin percentage",
                ),
            ],
        )
        assert len(preset.peer_groups) == 1
        assert len(preset.scraping_queries) == 1
        assert len(preset.competitive_factors) == 1
        assert len(preset.industry_media) == 1
        assert len(preset.key_metrics) == 1

    def test_正常系_拡張フィールドのデフォルトは空リスト(self) -> None:
        preset = IndustryPreset(
            sector="Energy",
            sub_sectors=["Oil_Gas"],
            sources=[],
        )
        assert preset.peer_groups == []
        assert preset.scraping_queries == []
        assert preset.competitive_factors == []
        assert preset.industry_media == []
        assert preset.key_metrics == []


class TestPresetsFileValidation:
    """Tests for validating the actual presets JSON file structure."""

    @pytest.fixture()
    def full_preset_data(self) -> dict:
        """Return a full 5-sector preset dataset for testing."""
        return {
            "version": "1.0",
            "presets": [
                {
                    "sector": "Technology",
                    "sub_sectors": ["Semiconductors", "Software_Infrastructure"],
                    "sources": [
                        {
                            "name": "McKinsey Insights",
                            "url": "https://www.mckinsey.com/featured-insights",
                            "tier": "scraping",
                            "difficulty": "medium",
                            "enabled": True,
                        },
                    ],
                    "peer_tickers": [
                        "NVDA",
                        "AMD",
                        "INTC",
                        "TSM",
                        "AVGO",
                        "MSFT",
                        "ORCL",
                        "CRM",
                    ],
                    "peer_groups": [
                        {
                            "sub_sector": "Semiconductors",
                            "companies": ["NVDA", "AMD", "INTC", "TSM", "AVGO"],
                            "description": "Major semiconductor manufacturers",
                        },
                        {
                            "sub_sector": "Software_Infrastructure",
                            "companies": ["MSFT", "ORCL", "CRM", "ADBE", "NOW"],
                            "description": "Enterprise software leaders",
                        },
                    ],
                    "scraping_queries": [
                        {
                            "query": "semiconductor industry outlook 2026",
                            "target_sources": ["McKinsey", "BCG"],
                            "sector_specific": True,
                        },
                        {
                            "query": "AI chip market analysis",
                            "target_sources": ["Goldman Sachs"],
                            "sector_specific": True,
                        },
                        {
                            "query": "cloud infrastructure market trends",
                            "target_sources": ["McKinsey"],
                            "sector_specific": True,
                        },
                    ],
                    "competitive_factors": [
                        {
                            "factor_name": "R&D Investment",
                            "description": "Annual R&D spending as % of revenue",
                            "importance": "high",
                        },
                    ],
                    "industry_media": [
                        {
                            "name": "SemiWiki",
                            "url": "https://semiwiki.com",
                            "focus_areas": ["semiconductors"],
                        },
                    ],
                    "key_metrics": [
                        {
                            "name": "Gross Margin",
                            "description": "Gross margin percentage",
                        },
                    ],
                },
                {
                    "sector": "Healthcare",
                    "sub_sectors": ["Pharmaceuticals"],
                    "sources": [],
                    "peer_tickers": ["JNJ", "PFE", "MRK", "ABBV", "LLY", "UNH"],
                    "peer_groups": [
                        {
                            "sub_sector": "Pharmaceuticals",
                            "companies": ["JNJ", "PFE", "MRK", "ABBV", "LLY"],
                        },
                    ],
                    "scraping_queries": [
                        {"query": "pharmaceutical industry trends"},
                        {"query": "drug pipeline analysis"},
                        {"query": "healthcare regulation impact"},
                    ],
                    "competitive_factors": [],
                    "industry_media": [],
                    "key_metrics": [],
                },
                {
                    "sector": "Financials",
                    "sub_sectors": ["Banks"],
                    "sources": [],
                    "peer_tickers": ["JPM", "BAC", "GS", "MS", "C", "WFC"],
                    "peer_groups": [
                        {
                            "sub_sector": "Banks",
                            "companies": ["JPM", "BAC", "GS", "MS", "C", "WFC"],
                        },
                    ],
                    "scraping_queries": [
                        {"query": "banking sector outlook"},
                        {"query": "fintech disruption analysis"},
                        {"query": "interest rate impact on banks"},
                    ],
                    "competitive_factors": [],
                    "industry_media": [],
                    "key_metrics": [],
                },
                {
                    "sector": "Consumer_Discretionary",
                    "sub_sectors": ["Retail"],
                    "sources": [],
                    "peer_tickers": ["AMZN", "WMT", "TGT", "COST", "HD"],
                    "peer_groups": [
                        {
                            "sub_sector": "Retail",
                            "companies": ["AMZN", "WMT", "TGT", "COST", "HD"],
                        },
                    ],
                    "scraping_queries": [
                        {"query": "retail industry trends"},
                        {"query": "e-commerce market analysis"},
                        {"query": "consumer spending outlook"},
                    ],
                    "competitive_factors": [],
                    "industry_media": [],
                    "key_metrics": [],
                },
                {
                    "sector": "Energy",
                    "sub_sectors": ["Oil_Gas"],
                    "sources": [],
                    "peer_tickers": ["XOM", "CVX", "COP", "SLB", "EOG"],
                    "peer_groups": [
                        {
                            "sub_sector": "Oil_Gas",
                            "companies": ["XOM", "CVX", "COP", "SLB", "EOG"],
                        },
                    ],
                    "scraping_queries": [
                        {"query": "oil and gas industry outlook"},
                        {"query": "energy transition analysis"},
                        {"query": "OPEC production impact"},
                    ],
                    "competitive_factors": [],
                    "industry_media": [],
                    "key_metrics": [],
                },
            ],
        }

    def test_正常系_5セクター分のプリセットが読み込める(
        self, tmp_path: Path, full_preset_data: dict
    ) -> None:
        config_file = tmp_path / "presets.json"
        config_file.write_text(json.dumps(full_preset_data, ensure_ascii=False))

        config = load_presets(config_file)
        assert len(config.presets) == 5

    def test_正常系_全セクター名が正しい(
        self, tmp_path: Path, full_preset_data: dict
    ) -> None:
        config_file = tmp_path / "presets.json"
        config_file.write_text(json.dumps(full_preset_data, ensure_ascii=False))

        config = load_presets(config_file)
        expected_sectors = [
            "Technology",
            "Healthcare",
            "Financials",
            "Consumer_Discretionary",
            "Energy",
        ]
        assert config.sector_names == expected_sectors

    def test_正常系_各セクターに5から10銘柄のピアグループがある(
        self, tmp_path: Path, full_preset_data: dict
    ) -> None:
        config_file = tmp_path / "presets.json"
        config_file.write_text(json.dumps(full_preset_data, ensure_ascii=False))

        config = load_presets(config_file)
        for preset in config.presets:
            assert 5 <= len(preset.peer_tickers) <= 10, (
                f"Sector {preset.sector} has {len(preset.peer_tickers)} "
                f"peer tickers (expected 5-10)"
            )

    def test_正常系_各セクターに最低3つのスクレイピングクエリがある(
        self, tmp_path: Path, full_preset_data: dict
    ) -> None:
        config_file = tmp_path / "presets.json"
        config_file.write_text(json.dumps(full_preset_data, ensure_ascii=False))

        config = load_presets(config_file)
        for preset in config.presets:
            assert len(preset.scraping_queries) >= 3, (
                f"Sector {preset.sector} has {len(preset.scraping_queries)} "
                f"scraping queries (expected >= 3)"
            )

    def test_正常系_各セクターにpeer_groupsがある(
        self, tmp_path: Path, full_preset_data: dict
    ) -> None:
        config_file = tmp_path / "presets.json"
        config_file.write_text(json.dumps(full_preset_data, ensure_ascii=False))

        config = load_presets(config_file)
        for preset in config.presets:
            assert len(preset.peer_groups) >= 1, (
                f"Sector {preset.sector} has no peer_groups"
            )

    def test_正常系_peer_groupsの各グループに5銘柄以上がある(
        self, tmp_path: Path, full_preset_data: dict
    ) -> None:
        config_file = tmp_path / "presets.json"
        config_file.write_text(json.dumps(full_preset_data, ensure_ascii=False))

        config = load_presets(config_file)
        for preset in config.presets:
            for group in preset.peer_groups:
                assert len(group.companies) >= 5, (
                    f"Sector {preset.sector}/{group.sub_sector} has "
                    f"{len(group.companies)} companies (expected >= 5)"
                )


class TestActualPresetsFile:
    """Tests that validate the actual presets JSON file on disk."""

    def test_正常系_実際のプリセットファイルが正常に読み込める(self) -> None:
        """Validate the actual presets file loads and has 5 sectors."""
        config_path = Path("data/config/industry-research-presets.json")
        if not config_path.exists():
            pytest.skip("Presets file not found (expected in CI)")

        config = load_presets(config_path)
        assert config.version == "1.0"
        assert len(config.presets) == 5

    def test_正常系_実際のプリセットで各セクターに3クエリ以上(self) -> None:
        """Validate the actual presets file has >= 3 scraping queries per sector."""
        config_path = Path("data/config/industry-research-presets.json")
        if not config_path.exists():
            pytest.skip("Presets file not found (expected in CI)")

        config = load_presets(config_path)
        for preset in config.presets:
            assert len(preset.scraping_queries) >= 3, (
                f"Sector {preset.sector} has {len(preset.scraping_queries)} "
                f"scraping queries (expected >= 3)"
            )

    def test_正常系_実際のプリセットで各セクターに5から10銘柄(self) -> None:
        """Validate the actual presets file has 5-10 peer tickers per sector."""
        config_path = Path("data/config/industry-research-presets.json")
        if not config_path.exists():
            pytest.skip("Presets file not found (expected in CI)")

        config = load_presets(config_path)
        for preset in config.presets:
            assert 5 <= len(preset.peer_tickers) <= 10, (
                f"Sector {preset.sector} has {len(preset.peer_tickers)} "
                f"peer tickers (expected 5-10)"
            )


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

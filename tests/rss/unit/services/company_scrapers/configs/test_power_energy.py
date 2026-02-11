"""Unit tests for Power & Energy Infrastructure CompanyConfig definitions and snapshot selector extraction.

Validates that:
1. All 7 Power & Energy companies have correct CompanyConfig definitions
2. CSS selectors extract articles from HTML snapshots correctly
3. POWER_ENERGY_COMPANIES list is complete and well-formed
"""

from pathlib import Path

import pytest
from lxml.html import fromstring

from rss.services.company_scrapers.configs.power_energy import (
    BLOOM_ENERGY,
    CONSTELLATION_ENERGY,
    EATON_CORPORATION,
    NEXTERA_ENERGY,
    NVENT_ELECTRIC,
    POWER_ENERGY_COMPANIES,
    SCHNEIDER_ELECTRIC,
    VISTRA_ENERGY,
)
from rss.services.company_scrapers.types import CompanyConfig, InvestmentContext

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_SNAPSHOTS_DIR = Path(__file__).parent.parent / "snapshots" / "power_energy"
"""Directory containing HTML snapshots for Power & Energy companies."""

_EXPECTED_COMPANY_COUNT = 7
"""Number of Power & Energy companies expected."""

_ALL_CONFIGS: list[CompanyConfig] = [
    CONSTELLATION_ENERGY,
    NEXTERA_ENERGY,
    VISTRA_ENERGY,
    BLOOM_ENERGY,
    EATON_CORPORATION,
    SCHNEIDER_ELECTRIC,
    NVENT_ELECTRIC,
]
"""All individual config constants for parametrized tests."""

_CONFIG_SNAPSHOT_MAP: dict[str, str] = {
    "constellation_energy": "constellation_energy.html",
    "nextera_energy": "nextera_energy.html",
    "vistra_energy": "vistra_energy.html",
    "bloom_energy": "bloom_energy.html",
    "eaton_corporation": "eaton_corporation.html",
    "schneider_electric": "schneider_electric.html",
    "nvent_electric": "nvent_electric.html",
}
"""Mapping from company key to snapshot filename."""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _load_snapshot(company_key: str) -> str:
    """Load HTML snapshot for a company.

    Parameters
    ----------
    company_key : str
        Company key matching the snapshot filename.

    Returns
    -------
    str
        HTML content of the snapshot.
    """
    filename = _CONFIG_SNAPSHOT_MAP[company_key]
    snapshot_path = _SNAPSHOTS_DIR / filename
    return snapshot_path.read_text(encoding="utf-8")


def _extract_articles_from_snapshot(
    html: str,
    config: CompanyConfig,
) -> list[dict[str, str | None]]:
    """Extract article metadata from snapshot HTML using config selectors.

    Parameters
    ----------
    html : str
        HTML content.
    config : CompanyConfig
        Company configuration with CSS selectors.

    Returns
    -------
    list[dict[str, str | None]]
        List of dicts with 'title', 'url', and 'date' keys.
    """
    doc = fromstring(html)
    article_elements = doc.cssselect(config.article_list_selector)

    results: list[dict[str, str | None]] = []
    for el in article_elements:
        # Extract title
        title_els = el.cssselect(config.article_title_selector)
        title = title_els[0].text_content().strip() if title_els else None

        # Extract date
        date_els = el.cssselect(config.article_date_selector)
        date = date_els[0].text_content().strip() if date_els else None

        # Extract URL from <a> href
        url: str | None = None
        href = el.get("href")
        if href:
            url = href
        else:
            links = el.cssselect("a")
            if links:
                url = links[0].get("href")

        results.append({"title": title, "url": url, "date": date})

    return results


# ---------------------------------------------------------------------------
# POWER_ENERGY_COMPANIES list
# ---------------------------------------------------------------------------


class TestPowerEnergyCompaniesList:
    """Tests for the POWER_ENERGY_COMPANIES list."""

    def test_正常系_7社全てが含まれている(self) -> None:
        assert len(POWER_ENERGY_COMPANIES) == _EXPECTED_COMPANY_COUNT

    def test_正常系_全要素がCompanyConfig型(self) -> None:
        for config in POWER_ENERGY_COMPANIES:
            assert isinstance(config, CompanyConfig)

    def test_正常系_キーが一意(self) -> None:
        keys = [c.key for c in POWER_ENERGY_COMPANIES]
        assert len(keys) == len(set(keys))

    def test_正常系_全てカテゴリがpower_energy(self) -> None:
        for config in POWER_ENERGY_COMPANIES:
            assert config.category == "power_energy"

    def test_正常系_全てblog_urlがhttpsで始まる(self) -> None:
        for config in POWER_ENERGY_COMPANIES:
            assert config.blog_url.startswith("https://"), (
                f"{config.key}: blog_url must start with https://"
            )

    def test_正常系_リスト内容が個別定数と一致(self) -> None:
        assert POWER_ENERGY_COMPANIES == _ALL_CONFIGS

    def test_正常系_期待される企業キーが全て存在する(self) -> None:
        expected_keys = {
            "constellation_energy",
            "nextera_energy",
            "vistra_energy",
            "bloom_energy",
            "eaton_corporation",
            "schneider_electric",
            "nvent_electric",
        }
        actual_keys = {c.key for c in POWER_ENERGY_COMPANIES}
        assert actual_keys == expected_keys


# ---------------------------------------------------------------------------
# Individual CompanyConfig validation
# ---------------------------------------------------------------------------


class TestCompanyConfigFields:
    """Tests that each CompanyConfig has valid field values."""

    @pytest.mark.parametrize(
        "config",
        _ALL_CONFIGS,
        ids=[c.key for c in _ALL_CONFIGS],
    )
    def test_正常系_keyが空でない(self, config: CompanyConfig) -> None:
        assert config.key
        assert isinstance(config.key, str)

    @pytest.mark.parametrize(
        "config",
        _ALL_CONFIGS,
        ids=[c.key for c in _ALL_CONFIGS],
    )
    def test_正常系_nameが空でない(self, config: CompanyConfig) -> None:
        assert config.name
        assert isinstance(config.name, str)

    @pytest.mark.parametrize(
        "config",
        _ALL_CONFIGS,
        ids=[c.key for c in _ALL_CONFIGS],
    )
    def test_正常系_セレクタが空でない(self, config: CompanyConfig) -> None:
        assert config.article_list_selector
        assert config.article_title_selector
        assert config.article_date_selector

    @pytest.mark.parametrize(
        "config",
        _ALL_CONFIGS,
        ids=[c.key for c in _ALL_CONFIGS],
    )
    def test_正常系_rate_limitが正の値(self, config: CompanyConfig) -> None:
        assert config.rate_limit_seconds > 0

    @pytest.mark.parametrize(
        "config",
        _ALL_CONFIGS,
        ids=[c.key for c in _ALL_CONFIGS],
    )
    def test_正常系_investment_contextが設定されている(
        self,
        config: CompanyConfig,
    ) -> None:
        assert isinstance(config.investment_context, InvestmentContext)
        # At least sectors should be set
        assert len(config.investment_context.sectors) > 0
        # At least keywords should be set
        assert len(config.investment_context.keywords) > 0


# ---------------------------------------------------------------------------
# Specific company field validation
# ---------------------------------------------------------------------------


class TestSpecificCompanyConfigs:
    """Tests for specific company configuration values."""

    def test_正常系_ConstellationEnergyのティッカーがCEG(self) -> None:
        assert CONSTELLATION_ENERGY.investment_context.tickers == ("CEG",)

    def test_正常系_NextEraEnergyのティッカーがNEE(self) -> None:
        assert NEXTERA_ENERGY.investment_context.tickers == ("NEE",)

    def test_正常系_VistraEnergyのティッカーがVST(self) -> None:
        assert VISTRA_ENERGY.investment_context.tickers == ("VST",)

    def test_正常系_BloomEnergyのティッカーがBE(self) -> None:
        assert BLOOM_ENERGY.investment_context.tickers == ("BE",)

    def test_正常系_EatonCorporationのティッカーがETN(self) -> None:
        assert EATON_CORPORATION.investment_context.tickers == ("ETN",)

    def test_正常系_SchneiderElectricのティッカーがSU(self) -> None:
        assert SCHNEIDER_ELECTRIC.investment_context.tickers == ("SU",)

    def test_正常系_nVentElectricのティッカーがNVT(self) -> None:
        assert NVENT_ELECTRIC.investment_context.tickers == ("NVT",)

    def test_正常系_全社Playwright不要(self) -> None:
        for config in POWER_ENERGY_COMPANIES:
            assert config.requires_playwright is False, (
                f"{config.key}: requires_playwright should be False"
            )

    def test_正常系_全社rate_limitが3秒(self) -> None:
        for config in POWER_ENERGY_COMPANIES:
            assert config.rate_limit_seconds == 3.0, (
                f"{config.key}: rate_limit_seconds should be 3.0"
            )

    def test_正常系_ConstellationEnergyのblog_urlが正しい(self) -> None:
        assert CONSTELLATION_ENERGY.blog_url == (
            "https://www.constellationenergy.com/newsroom.html"
        )

    def test_正常系_NextEraEnergyのblog_urlが正しい(self) -> None:
        assert NEXTERA_ENERGY.blog_url == (
            "https://investor.nexteraenergy.com/news-releases"
        )

    def test_正常系_VistraEnergyのblog_urlが正しい(self) -> None:
        assert VISTRA_ENERGY.blog_url == "https://investor.vistracorp.com/news"

    def test_正常系_BloomEnergyのblog_urlが正しい(self) -> None:
        assert BLOOM_ENERGY.blog_url == "https://www.bloomenergy.com/newsroom/"

    def test_正常系_SchneiderElectricのblog_urlが正しい(self) -> None:
        assert SCHNEIDER_ELECTRIC.blog_url == "https://blog.se.com/"

    def test_正常系_nVentElectricのblog_urlが正しい(self) -> None:
        assert NVENT_ELECTRIC.blog_url == "https://blog.nvent.com/"


# ---------------------------------------------------------------------------
# HTML snapshot existence
# ---------------------------------------------------------------------------


class TestSnapshotFiles:
    """Tests that HTML snapshots exist for all companies."""

    def test_正常系_スナップショットディレクトリが存在する(self) -> None:
        assert _SNAPSHOTS_DIR.is_dir()

    @pytest.mark.parametrize(
        "company_key",
        list(_CONFIG_SNAPSHOT_MAP.keys()),
        ids=list(_CONFIG_SNAPSHOT_MAP.keys()),
    )
    def test_正常系_スナップショットファイルが存在する(
        self,
        company_key: str,
    ) -> None:
        filename = _CONFIG_SNAPSHOT_MAP[company_key]
        snapshot_path = _SNAPSHOTS_DIR / filename
        assert snapshot_path.is_file(), f"Snapshot not found: {snapshot_path}"

    @pytest.mark.parametrize(
        "company_key",
        list(_CONFIG_SNAPSHOT_MAP.keys()),
        ids=list(_CONFIG_SNAPSHOT_MAP.keys()),
    )
    def test_正常系_スナップショットが空でない(
        self,
        company_key: str,
    ) -> None:
        html = _load_snapshot(company_key)
        assert len(html) > 100, f"Snapshot for {company_key} appears too small"


# ---------------------------------------------------------------------------
# Snapshot selector extraction
# ---------------------------------------------------------------------------


class TestSnapshotSelectorExtraction:
    """Tests that CSS selectors correctly extract articles from snapshots."""

    @pytest.mark.parametrize(
        ("config", "company_key"),
        [(c, c.key) for c in _ALL_CONFIGS],
        ids=[c.key for c in _ALL_CONFIGS],
    )
    def test_正常系_記事リストセレクタが記事を検出する(
        self,
        config: CompanyConfig,
        company_key: str,
    ) -> None:
        html = _load_snapshot(company_key)
        doc = fromstring(html)
        articles = doc.cssselect(config.article_list_selector)
        assert len(articles) >= 1, (
            f"{company_key}: article_list_selector '{config.article_list_selector}' "
            f"found 0 elements"
        )

    @pytest.mark.parametrize(
        ("config", "company_key"),
        [(c, c.key) for c in _ALL_CONFIGS],
        ids=[c.key for c in _ALL_CONFIGS],
    )
    def test_正常系_タイトルセレクタがタイトルを抽出する(
        self,
        config: CompanyConfig,
        company_key: str,
    ) -> None:
        html = _load_snapshot(company_key)
        articles = _extract_articles_from_snapshot(html, config)
        assert len(articles) >= 1

        for article in articles:
            assert article["title"], f"{company_key}: title not extracted for article"
            assert len(article["title"]) > 0

    @pytest.mark.parametrize(
        ("config", "company_key"),
        [(c, c.key) for c in _ALL_CONFIGS],
        ids=[c.key for c in _ALL_CONFIGS],
    )
    def test_正常系_日付セレクタが日付を抽出する(
        self,
        config: CompanyConfig,
        company_key: str,
    ) -> None:
        html = _load_snapshot(company_key)
        articles = _extract_articles_from_snapshot(html, config)
        assert len(articles) >= 1

        for article in articles:
            assert article["date"], f"{company_key}: date not extracted for article"

    @pytest.mark.parametrize(
        ("config", "company_key"),
        [(c, c.key) for c in _ALL_CONFIGS],
        ids=[c.key for c in _ALL_CONFIGS],
    )
    def test_正常系_URLが抽出できる(
        self,
        config: CompanyConfig,
        company_key: str,
    ) -> None:
        html = _load_snapshot(company_key)
        articles = _extract_articles_from_snapshot(html, config)
        assert len(articles) >= 1

        for article in articles:
            assert article["url"], f"{company_key}: URL not extracted for article"

    @pytest.mark.parametrize(
        ("config", "company_key"),
        [(c, c.key) for c in _ALL_CONFIGS],
        ids=[c.key for c in _ALL_CONFIGS],
    )
    def test_正常系_3記事以上を抽出する(
        self,
        config: CompanyConfig,
        company_key: str,
    ) -> None:
        html = _load_snapshot(company_key)
        articles = _extract_articles_from_snapshot(html, config)
        assert len(articles) >= 3, (
            f"{company_key}: expected >= 3 articles, got {len(articles)}"
        )


# ---------------------------------------------------------------------------
# StructureValidator integration (hit rate)
# ---------------------------------------------------------------------------


class TestStructureValidatorIntegration:
    """Tests that StructureValidator produces healthy hit rates for snapshots."""

    @pytest.mark.parametrize(
        ("config", "company_key"),
        [(c, c.key) for c in _ALL_CONFIGS],
        ids=[c.key for c in _ALL_CONFIGS],
    )
    def test_正常系_ヒット率が0_8以上(
        self,
        config: CompanyConfig,
        company_key: str,
    ) -> None:
        from rss.services.company_scrapers.structure_validator import (
            StructureValidator,
        )

        html = _load_snapshot(company_key)
        validator = StructureValidator()
        report = validator.validate(html, config)

        assert report.hit_rate >= 0.8, (
            f"{company_key}: hit_rate={report.hit_rate:.2f} "
            f"(article_list_hits={report.article_list_hits}, "
            f"title_found={report.title_found_count}, "
            f"date_found={report.date_found_count})"
        )

    @pytest.mark.parametrize(
        ("config", "company_key"),
        [(c, c.key) for c in _ALL_CONFIGS],
        ids=[c.key for c in _ALL_CONFIGS],
    )
    def test_正常系_記事リストヒット数が1以上(
        self,
        config: CompanyConfig,
        company_key: str,
    ) -> None:
        from rss.services.company_scrapers.structure_validator import (
            StructureValidator,
        )

        html = _load_snapshot(company_key)
        validator = StructureValidator()
        report = validator.validate(html, config)

        assert report.article_list_hits >= 1, (
            f"{company_key}: no articles found with selector "
            f"'{config.article_list_selector}'"
        )


# ---------------------------------------------------------------------------
# Package imports
# ---------------------------------------------------------------------------


class TestConfigsPackageImport:
    """Tests for package-level imports."""

    def test_正常系_configsパッケージからインポートできる(self) -> None:
        from rss.services.company_scrapers.configs import POWER_ENERGY_COMPANIES

        assert len(POWER_ENERGY_COMPANIES) == _EXPECTED_COMPANY_COUNT

    def test_正常系_power_energyモジュールから全定数をインポートできる(self) -> None:
        from rss.services.company_scrapers.configs.power_energy import (
            BLOOM_ENERGY,
            CONSTELLATION_ENERGY,
            EATON_CORPORATION,
            NEXTERA_ENERGY,
            NVENT_ELECTRIC,
            POWER_ENERGY_COMPANIES,
            SCHNEIDER_ELECTRIC,
            VISTRA_ENERGY,
        )

        all_names = [
            CONSTELLATION_ENERGY,
            NEXTERA_ENERGY,
            VISTRA_ENERGY,
            BLOOM_ENERGY,
            EATON_CORPORATION,
            SCHNEIDER_ELECTRIC,
            NVENT_ELECTRIC,
        ]
        assert len(all_names) == _EXPECTED_COMPANY_COUNT
        assert all_names == POWER_ENERGY_COMPANIES

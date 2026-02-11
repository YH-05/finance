"""Unit tests for Physical AI & Robotics CompanyConfig definitions and snapshot selector extraction.

Validates that:
1. All 9 Physical AI & Robotics companies have correct CompanyConfig definitions
2. CSS selectors extract articles from HTML snapshots correctly
3. PHYSICAL_AI_COMPANIES list is complete and well-formed
"""

from pathlib import Path

import pytest
from lxml.html import fromstring

from rss.services.company_scrapers.configs.physical_ai import (
    ABB,
    AGILITY_ROBOTICS,
    BOSTON_DYNAMICS,
    FANUC,
    FIGURE_AI,
    INTUITIVE_SURGICAL,
    PHYSICAL_AI_COMPANIES,
    PHYSICAL_INTELLIGENCE,
    SYMBOTIC,
    TESLA_OPTIMUS,
)
from rss.services.company_scrapers.types import CompanyConfig, InvestmentContext

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_SNAPSHOTS_DIR = Path(__file__).parent.parent / "snapshots" / "physical_ai"
"""Directory containing HTML snapshots for Physical AI & Robotics companies."""

_EXPECTED_COMPANY_COUNT = 9
"""Number of Physical AI & Robotics companies expected."""

_ALL_CONFIGS: list[CompanyConfig] = [
    TESLA_OPTIMUS,
    INTUITIVE_SURGICAL,
    FANUC,
    ABB,
    BOSTON_DYNAMICS,
    FIGURE_AI,
    PHYSICAL_INTELLIGENCE,
    AGILITY_ROBOTICS,
    SYMBOTIC,
]
"""All individual config constants for parametrized tests."""

_CONFIG_SNAPSHOT_MAP: dict[str, str] = {
    "tesla_optimus": "tesla_optimus.html",
    "intuitive_surgical": "intuitive_surgical.html",
    "fanuc": "fanuc.html",
    "abb": "abb.html",
    "boston_dynamics": "boston_dynamics.html",
    "figure_ai": "figure_ai.html",
    "physical_intelligence": "physical_intelligence.html",
    "agility_robotics": "agility_robotics.html",
    "symbotic": "symbotic.html",
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
# PHYSICAL_AI_COMPANIES list
# ---------------------------------------------------------------------------


class TestPhysicalAiCompaniesList:
    """Tests for the PHYSICAL_AI_COMPANIES list."""

    def test_正常系_9社全てが含まれている(self) -> None:
        assert len(PHYSICAL_AI_COMPANIES) == _EXPECTED_COMPANY_COUNT

    def test_正常系_全要素がCompanyConfig型(self) -> None:
        for config in PHYSICAL_AI_COMPANIES:
            assert isinstance(config, CompanyConfig)

    def test_正常系_キーが一意(self) -> None:
        keys = [c.key for c in PHYSICAL_AI_COMPANIES]
        assert len(keys) == len(set(keys))

    def test_正常系_全てカテゴリがphysical_ai(self) -> None:
        for config in PHYSICAL_AI_COMPANIES:
            assert config.category == "physical_ai"

    def test_正常系_全てblog_urlがhttpsで始まる(self) -> None:
        for config in PHYSICAL_AI_COMPANIES:
            assert config.blog_url.startswith("https://"), (
                f"{config.key}: blog_url must start with https://"
            )

    def test_正常系_リスト内容が個別定数と一致(self) -> None:
        assert PHYSICAL_AI_COMPANIES == _ALL_CONFIGS

    def test_正常系_期待される企業キーが全て存在する(self) -> None:
        expected_keys = {
            "tesla_optimus",
            "intuitive_surgical",
            "fanuc",
            "abb",
            "boston_dynamics",
            "figure_ai",
            "physical_intelligence",
            "agility_robotics",
            "symbotic",
        }
        actual_keys = {c.key for c in PHYSICAL_AI_COMPANIES}
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

    def test_正常系_TeslaOptimusのティッカーがTSLA(self) -> None:
        assert TESLA_OPTIMUS.investment_context.tickers == ("TSLA",)

    def test_正常系_IntuitiveSurgicalのティッカーがISRG(self) -> None:
        assert INTUITIVE_SURGICAL.investment_context.tickers == ("ISRG",)

    def test_正常系_Fanucのティッカーが6954T(self) -> None:
        assert FANUC.investment_context.tickers == ("6954.T",)

    def test_正常系_ABBのティッカーがABB(self) -> None:
        assert ABB.investment_context.tickers == ("ABB",)

    def test_正常系_BostonDynamicsのティッカーが空(self) -> None:
        assert BOSTON_DYNAMICS.investment_context.tickers == ()

    def test_正常系_FigureAIのティッカーが空(self) -> None:
        assert FIGURE_AI.investment_context.tickers == ()

    def test_正常系_PhysicalIntelligenceのティッカーが空(self) -> None:
        assert PHYSICAL_INTELLIGENCE.investment_context.tickers == ()

    def test_正常系_AgilityRoboticsのティッカーが空(self) -> None:
        assert AGILITY_ROBOTICS.investment_context.tickers == ()

    def test_正常系_SymboticのティッカーがSYM(self) -> None:
        assert SYMBOTIC.investment_context.tickers == ("SYM",)

    def test_正常系_FanucはPlaywright必要(self) -> None:
        assert FANUC.requires_playwright is True

    def test_正常系_PhysicalIntelligenceはPlaywright必要(self) -> None:
        assert PHYSICAL_INTELLIGENCE.requires_playwright is True

    def test_正常系_Fanucのrate_limitが5秒(self) -> None:
        assert FANUC.rate_limit_seconds == 5.0

    def test_正常系_PhysicalIntelligenceのrate_limitが5秒(self) -> None:
        assert PHYSICAL_INTELLIGENCE.rate_limit_seconds == 5.0

    def test_正常系_Playwright不要な社のrate_limitが3秒(self) -> None:
        non_playwright = [c for c in PHYSICAL_AI_COMPANIES if not c.requires_playwright]
        for config in non_playwright:
            assert config.rate_limit_seconds == 3.0, (
                f"{config.key}: rate_limit_seconds should be 3.0"
            )

    def test_正常系_TeslaOptimusのblog_urlが正しい(self) -> None:
        assert TESLA_OPTIMUS.blog_url == "https://www.tesla.com/blog"

    def test_正常系_IntuitiveSurgicalのblog_urlが正しい(self) -> None:
        assert INTUITIVE_SURGICAL.blog_url == (
            "https://investor.intuitivesurgical.com/news-events/press-releases"
        )

    def test_正常系_Fanucのblog_urlが正しい(self) -> None:
        assert FANUC.blog_url == (
            "https://www.fanuc.co.jp/en/product/new_product/index.html"
        )

    def test_正常系_ABBのblog_urlが正しい(self) -> None:
        assert ABB.blog_url == "https://new.abb.com/news"

    def test_正常系_BostonDynamicsのblog_urlが正しい(self) -> None:
        assert BOSTON_DYNAMICS.blog_url == "https://bostondynamics.com/blog"

    def test_正常系_FigureAIのblog_urlが正しい(self) -> None:
        assert FIGURE_AI.blog_url == "https://www.figure.ai/news"

    def test_正常系_PhysicalIntelligenceのblog_urlが正しい(self) -> None:
        assert PHYSICAL_INTELLIGENCE.blog_url == (
            "https://www.physicalintelligence.company/blog"
        )

    def test_正常系_AgilityRoboticsのblog_urlが正しい(self) -> None:
        assert AGILITY_ROBOTICS.blog_url == ("https://agilityrobotics.com/about/press")

    def test_正常系_Symboticのblog_urlが正しい(self) -> None:
        assert SYMBOTIC.blog_url == (
            "https://www.symbotic.com/innovation-insights/blog"
        )


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
        from rss.services.company_scrapers.configs import PHYSICAL_AI_COMPANIES

        assert len(PHYSICAL_AI_COMPANIES) == _EXPECTED_COMPANY_COUNT

    def test_正常系_physical_aiモジュールから全定数をインポートできる(self) -> None:
        from rss.services.company_scrapers.configs.physical_ai import (
            ABB,
            AGILITY_ROBOTICS,
            BOSTON_DYNAMICS,
            FANUC,
            FIGURE_AI,
            INTUITIVE_SURGICAL,
            PHYSICAL_AI_COMPANIES,
            PHYSICAL_INTELLIGENCE,
            SYMBOTIC,
            TESLA_OPTIMUS,
        )

        all_names = [
            TESLA_OPTIMUS,
            INTUITIVE_SURGICAL,
            FANUC,
            ABB,
            BOSTON_DYNAMICS,
            FIGURE_AI,
            PHYSICAL_INTELLIGENCE,
            AGILITY_ROBOTICS,
            SYMBOTIC,
        ]
        assert len(all_names) == _EXPECTED_COMPANY_COUNT
        assert all_names == PHYSICAL_AI_COMPANIES

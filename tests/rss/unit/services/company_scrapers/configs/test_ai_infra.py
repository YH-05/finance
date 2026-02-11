"""Unit tests for AI infra / MLOps CompanyConfig definitions and snapshot selector extraction.

Validates that:
1. All 7 AI infra companies have correct CompanyConfig definitions
2. CSS selectors extract articles from HTML snapshots correctly
3. AI_INFRA_COMPANIES list is complete and well-formed
"""

from pathlib import Path

import pytest
from lxml.html import fromstring

from rss.services.company_scrapers.configs.ai_infra import (
    AI_INFRA_COMPANIES,
    ANYSCALE,
    ELASTIC,
    HUGGINGFACE,
    REPLICATE,
    SCALE_AI,
    TOGETHER_AI,
    WANDB,
)
from rss.services.company_scrapers.types import CompanyConfig, InvestmentContext

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_SNAPSHOTS_DIR = Path(__file__).parent.parent / "snapshots" / "ai_infra"
"""Directory containing HTML snapshots for AI infra companies."""

_EXPECTED_COMPANY_COUNT = 7
"""Number of AI infra companies expected."""

_ALL_CONFIGS: list[CompanyConfig] = [
    HUGGINGFACE,
    SCALE_AI,
    WANDB,
    TOGETHER_AI,
    ANYSCALE,
    REPLICATE,
    ELASTIC,
]
"""All individual config constants for parametrized tests."""

_CONFIG_SNAPSHOT_MAP: dict[str, str] = {
    "huggingface": "huggingface.html",
    "scale_ai": "scale_ai.html",
    "wandb": "wandb.html",
    "together_ai": "together_ai.html",
    "anyscale": "anyscale.html",
    "replicate": "replicate.html",
    "elastic": "elastic.html",
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
# AI_INFRA_COMPANIES list
# ---------------------------------------------------------------------------


class TestAiInfraCompaniesList:
    """Tests for the AI_INFRA_COMPANIES list."""

    def test_正常系_7社全てが含まれている(self) -> None:
        assert len(AI_INFRA_COMPANIES) == _EXPECTED_COMPANY_COUNT

    def test_正常系_全要素がCompanyConfig型(self) -> None:
        for config in AI_INFRA_COMPANIES:
            assert isinstance(config, CompanyConfig)

    def test_正常系_キーが一意(self) -> None:
        keys = [c.key for c in AI_INFRA_COMPANIES]
        assert len(keys) == len(set(keys))

    def test_正常系_全てカテゴリがai_infra(self) -> None:
        for config in AI_INFRA_COMPANIES:
            assert config.category == "ai_infra"

    def test_正常系_全てblog_urlがhttpsで始まる(self) -> None:
        for config in AI_INFRA_COMPANIES:
            assert config.blog_url.startswith("https://"), (
                f"{config.key}: blog_url must start with https://"
            )

    def test_正常系_リスト内容が個別定数と一致(self) -> None:
        assert AI_INFRA_COMPANIES == _ALL_CONFIGS

    def test_正常系_期待される企業キーが全て存在する(self) -> None:
        expected_keys = {
            "huggingface",
            "scale_ai",
            "wandb",
            "together_ai",
            "anyscale",
            "replicate",
            "elastic",
        }
        actual_keys = {c.key for c in AI_INFRA_COMPANIES}
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

    def test_正常系_HuggingFaceのティッカーが空(self) -> None:
        assert HUGGINGFACE.investment_context.tickers == ()

    def test_正常系_ScaleAIのティッカーが空(self) -> None:
        assert SCALE_AI.investment_context.tickers == ()

    def test_正常系_WandBのティッカーが空(self) -> None:
        assert WANDB.investment_context.tickers == ()

    def test_正常系_TogetherAIのティッカーが空(self) -> None:
        assert TOGETHER_AI.investment_context.tickers == ()

    def test_正常系_Anyscaleのティッカーが空(self) -> None:
        assert ANYSCALE.investment_context.tickers == ()

    def test_正常系_Replicateのティッカーが空(self) -> None:
        assert REPLICATE.investment_context.tickers == ()

    def test_正常系_ElasticのティッカーがESTC(self) -> None:
        assert ELASTIC.investment_context.tickers == ("ESTC",)

    def test_正常系_WandBはPlaywright必須(self) -> None:
        assert WANDB.requires_playwright is True

    def test_正常系_WandBのrate_limitが5秒(self) -> None:
        assert WANDB.rate_limit_seconds == 5.0

    def test_正常系_HuggingFaceのblog_urlが正しい(self) -> None:
        assert HUGGINGFACE.blog_url == "https://huggingface.co/blog"

    def test_正常系_WandBのblog_urlが正しい(self) -> None:
        assert WANDB.blog_url == "https://wandb.ai/fully-connected/blog"

    def test_正常系_Playwright不要の企業は6社(self) -> None:
        non_playwright = [c for c in AI_INFRA_COMPANIES if not c.requires_playwright]
        assert len(non_playwright) == 6  # W&B requires Playwright


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
        from rss.services.company_scrapers.configs import AI_INFRA_COMPANIES

        assert len(AI_INFRA_COMPANIES) == _EXPECTED_COMPANY_COUNT

    def test_正常系_ai_infraモジュールから全定数をインポートできる(self) -> None:
        from rss.services.company_scrapers.configs.ai_infra import (
            AI_INFRA_COMPANIES,
            ANYSCALE,
            ELASTIC,
            HUGGINGFACE,
            REPLICATE,
            SCALE_AI,
            TOGETHER_AI,
            WANDB,
        )

        all_names = [
            HUGGINGFACE,
            SCALE_AI,
            WANDB,
            TOGETHER_AI,
            ANYSCALE,
            REPLICATE,
            ELASTIC,
        ]
        assert len(all_names) == _EXPECTED_COMPANY_COUNT
        assert all_names == AI_INFRA_COMPANIES

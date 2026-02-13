"""Unit tests for GPU/Compute Chip CompanyConfig definitions and snapshot selector extraction.

Validates that:
1. All 10 GPU/Compute Chip companies have correct CompanyConfig definitions
2. CSS selectors extract articles from HTML snapshots correctly
3. GPU_CHIPS_COMPANIES list is complete and well-formed
"""

from pathlib import Path

import pytest
from lxml.html import fromstring

from rss.services.company_scrapers.configs.gpu_chips import (
    AMD,
    ARM,
    BROADCOM,
    CEREBRAS,
    GPU_CHIPS_COMPANIES,
    INTEL,
    MARVELL,
    NVIDIA,
    QUALCOMM,
    SAMBANOVA,
    TENSTORRENT,
)
from rss.services.company_scrapers.types import CompanyConfig, InvestmentContext

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_SNAPSHOTS_DIR = Path(__file__).parent.parent / "snapshots" / "gpu_chips"
"""Directory containing HTML snapshots for GPU/Compute Chip companies."""

_EXPECTED_COMPANY_COUNT = 10
"""Number of GPU/Compute Chip companies expected."""

_ALL_CONFIGS: list[CompanyConfig] = [
    NVIDIA,
    AMD,
    INTEL,
    BROADCOM,
    QUALCOMM,
    ARM,
    MARVELL,
    CEREBRAS,
    SAMBANOVA,
    TENSTORRENT,
]
"""All individual config constants for parametrized tests."""

_CONFIG_SNAPSHOT_MAP: dict[str, str] = {
    "nvidia": "nvidia.html",
    "amd": "amd.html",
    "intel": "intel.html",
    "broadcom": "broadcom.html",
    "qualcomm": "qualcomm.html",
    "arm": "arm.html",
    "marvell": "marvell.html",
    "cerebras": "cerebras.html",
    "sambanova": "sambanova.html",
    "tenstorrent": "tenstorrent.html",
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
# GPU_CHIPS_COMPANIES list
# ---------------------------------------------------------------------------


class TestGpuChipsCompaniesList:
    """Tests for the GPU_CHIPS_COMPANIES list."""

    def test_正常系_10社全てが含まれている(self) -> None:
        assert len(GPU_CHIPS_COMPANIES) == _EXPECTED_COMPANY_COUNT

    def test_正常系_全要素がCompanyConfig型(self) -> None:
        for config in GPU_CHIPS_COMPANIES:
            assert isinstance(config, CompanyConfig)

    def test_正常系_キーが一意(self) -> None:
        keys = [c.key for c in GPU_CHIPS_COMPANIES]
        assert len(keys) == len(set(keys))

    def test_正常系_全てカテゴリがgpu_chips(self) -> None:
        for config in GPU_CHIPS_COMPANIES:
            assert config.category == "gpu_chips"

    def test_正常系_全てblog_urlがhttpsで始まる(self) -> None:
        for config in GPU_CHIPS_COMPANIES:
            assert config.blog_url.startswith("https://"), (
                f"{config.key}: blog_url must start with https://"
            )

    def test_正常系_リスト内容が個別定数と一致(self) -> None:
        assert GPU_CHIPS_COMPANIES == _ALL_CONFIGS

    def test_正常系_期待される企業キーが全て存在する(self) -> None:
        expected_keys = {
            "nvidia",
            "amd",
            "intel",
            "broadcom",
            "qualcomm",
            "arm",
            "marvell",
            "cerebras",
            "sambanova",
            "tenstorrent",
        }
        actual_keys = {c.key for c in GPU_CHIPS_COMPANIES}
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

    def test_正常系_NVIDIAのティッカーがNVDA(self) -> None:
        assert NVIDIA.investment_context.tickers == ("NVDA",)

    def test_正常系_AMDのティッカーがAMD(self) -> None:
        assert AMD.investment_context.tickers == ("AMD",)

    def test_正常系_IntelのティッカーがINTC(self) -> None:
        assert INTEL.investment_context.tickers == ("INTC",)

    def test_正常系_BroadcomのティッカーがAVGO(self) -> None:
        assert BROADCOM.investment_context.tickers == ("AVGO",)

    def test_正常系_QualcommのティッカーがQCOM(self) -> None:
        assert QUALCOMM.investment_context.tickers == ("QCOM",)

    def test_正常系_ARMのティッカーがARM(self) -> None:
        assert ARM.investment_context.tickers == ("ARM",)

    def test_正常系_MarvellのティッカーがMRVL(self) -> None:
        assert MARVELL.investment_context.tickers == ("MRVL",)

    def test_正常系_Cerebrasのティッカーが空(self) -> None:
        assert CEREBRAS.investment_context.tickers == ()

    def test_正常系_SambaNovaのティッカーが空(self) -> None:
        assert SAMBANOVA.investment_context.tickers == ()

    def test_正常系_Tenstorrentのティッカーが空(self) -> None:
        assert TENSTORRENT.investment_context.tickers == ()

    def test_正常系_CerebrasはPlaywright必須(self) -> None:
        assert CEREBRAS.requires_playwright is True

    def test_正常系_SambaNovaはPlaywright必須(self) -> None:
        assert SAMBANOVA.requires_playwright is True

    def test_正常系_Cerebrasのrate_limitが5秒(self) -> None:
        assert CEREBRAS.rate_limit_seconds == 5.0

    def test_正常系_SambaNovaのrate_limitが5秒(self) -> None:
        assert SAMBANOVA.rate_limit_seconds == 5.0

    def test_正常系_NVIDIAのblog_urlが正しい(self) -> None:
        assert NVIDIA.blog_url == "https://blogs.nvidia.com/"

    def test_正常系_Tenstorrentのblog_urlがvision(self) -> None:
        assert TENSTORRENT.blog_url == "https://tenstorrent.com/vision"


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
        from rss.services.company_scrapers.configs import GPU_CHIPS_COMPANIES

        assert len(GPU_CHIPS_COMPANIES) == _EXPECTED_COMPANY_COUNT

    def test_正常系_gpu_chipsモジュールから全定数をインポートできる(self) -> None:
        from rss.services.company_scrapers.configs.gpu_chips import (
            AMD,
            ARM,
            BROADCOM,
            CEREBRAS,
            GPU_CHIPS_COMPANIES,
            INTEL,
            MARVELL,
            NVIDIA,
            QUALCOMM,
            SAMBANOVA,
            TENSTORRENT,
        )

        all_names = [
            NVIDIA,
            AMD,
            INTEL,
            BROADCOM,
            QUALCOMM,
            ARM,
            MARVELL,
            CEREBRAS,
            SAMBANOVA,
            TENSTORRENT,
        ]
        assert len(all_names) == _EXPECTED_COMPANY_COUNT
        assert all_names == GPU_CHIPS_COMPANIES

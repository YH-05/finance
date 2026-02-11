"""CompanyConfig definitions for Nuclear & Fusion companies (Category 7).

Defines scraping configurations for 8 companies in the nuclear and
fusion energy category. Each configuration specifies the company's
news/press URL, CSS selectors for article extraction, and
investment context.

Company list:
    1. Oklo
    2. NuScale Power
    3. Cameco
    4. Centrus Energy
    5. Commonwealth Fusion
    6. TAE Technologies
    7. Helion Energy
    8. General Fusion
"""

from rss.services.company_scrapers.types import CompanyConfig, InvestmentContext

# ---------------------------------------------------------------------------
# Category constant
# ---------------------------------------------------------------------------

_CATEGORY = "nuclear_fusion"
"""Category key for all Nuclear & Fusion companies."""


# ---------------------------------------------------------------------------
# Company configurations
# ---------------------------------------------------------------------------

OKLO = CompanyConfig(
    key="oklo",
    name="Oklo",
    category=_CATEGORY,
    blog_url="https://oklo.com/newsroom/news",
    article_list_selector="div.news-item",
    article_title_selector="h3.news-item__title",
    article_date_selector="span.news-item__date",
    requires_playwright=False,
    rate_limit_seconds=3.0,
    investment_context=InvestmentContext(
        tickers=("OKLO",),
        sectors=("Nuclear", "Advanced Reactors"),
        keywords=("advanced reactor", "Meta power", "microreactor", "Oklo"),
    ),
)

NUSCALE_POWER = CompanyConfig(
    key="nuscale_power",
    name="NuScale Power",
    category=_CATEGORY,
    blog_url="https://www.nuscalepower.com/press-releases",
    article_list_selector="div.press-release",
    article_title_selector="h3.press-release__title",
    article_date_selector="span.press-release__date",
    requires_playwright=False,
    rate_limit_seconds=3.0,
    investment_context=InvestmentContext(
        tickers=("SMR",),
        sectors=("Nuclear", "SMR"),
        keywords=("small modular reactor", "SMR", "data center power", "NuScale"),
    ),
)

CAMECO = CompanyConfig(
    key="cameco",
    name="Cameco",
    category=_CATEGORY,
    blog_url="https://www.cameco.com/media/news",
    article_list_selector="div.news-article",
    article_title_selector="h3.news-article__title",
    article_date_selector="span.news-article__date",
    requires_playwright=False,
    rate_limit_seconds=3.0,
    investment_context=InvestmentContext(
        tickers=("CCJ",),
        sectors=("Nuclear", "Uranium"),
        keywords=("uranium", "nuclear fuel", "mining", "Cameco"),
    ),
)

CENTRUS_ENERGY = CompanyConfig(
    key="centrus_energy",
    name="Centrus Energy",
    category=_CATEGORY,
    blog_url="https://www.centrusenergy.com/news",
    article_list_selector="div.news-entry",
    article_title_selector="h3.news-entry__title",
    article_date_selector="span.news-entry__date",
    requires_playwright=False,
    rate_limit_seconds=3.0,
    investment_context=InvestmentContext(
        tickers=("LEU",),
        sectors=("Nuclear", "Uranium Enrichment"),
        keywords=("LEU", "HALEU", "uranium enrichment", "Centrus"),
    ),
)

COMMONWEALTH_FUSION = CompanyConfig(
    key="commonwealth_fusion",
    name="Commonwealth Fusion",
    category=_CATEGORY,
    blog_url="https://cfs.energy/news-and-media",
    article_list_selector="div.media-item",
    article_title_selector="h3.media-item__title",
    article_date_selector="span.media-item__date",
    requires_playwright=False,
    rate_limit_seconds=3.0,
    investment_context=InvestmentContext(
        tickers=(),
        sectors=("Fusion", "Energy"),
        keywords=("fusion", "SPARC", "ARC", "Google", "NVIDIA", "Commonwealth Fusion"),
    ),
)

TAE_TECHNOLOGIES = CompanyConfig(
    key="tae_technologies",
    name="TAE Technologies",
    category=_CATEGORY,
    blog_url="https://tae.com/category/press-releases",
    article_list_selector="article.press-release",
    article_title_selector="h2.press-release__title",
    article_date_selector="span.press-release__date",
    requires_playwright=False,
    rate_limit_seconds=3.0,
    investment_context=InvestmentContext(
        tickers=(),
        sectors=("Fusion", "Energy"),
        keywords=("fusion", "field-reversed configuration", "TAE Technologies"),
    ),
)

HELION_ENERGY = CompanyConfig(
    key="helion_energy",
    name="Helion Energy",
    category=_CATEGORY,
    blog_url="https://www.helionenergy.com/news",
    article_list_selector="div.news-post",
    article_title_selector="h3.news-post__title",
    article_date_selector="span.news-post__date",
    requires_playwright=False,
    rate_limit_seconds=3.0,
    investment_context=InvestmentContext(
        tickers=(),
        sectors=("Fusion", "Energy"),
        keywords=("fusion", "commercial fusion", "Helion Energy"),
    ),
)

GENERAL_FUSION = CompanyConfig(
    key="general_fusion",
    name="General Fusion",
    category=_CATEGORY,
    blog_url="https://generalfusion.com/post/category/press-releases",
    article_list_selector="div.post-item",
    article_title_selector="h3.post-item__title",
    article_date_selector="span.post-item__date",
    requires_playwright=False,
    rate_limit_seconds=3.0,
    investment_context=InvestmentContext(
        tickers=(),
        sectors=("Fusion", "Energy"),
        keywords=("fusion", "LM26", "magnetized target fusion", "General Fusion"),
    ),
)


# ---------------------------------------------------------------------------
# Category list
# ---------------------------------------------------------------------------

NUCLEAR_FUSION_COMPANIES: list[CompanyConfig] = [
    OKLO,
    NUSCALE_POWER,
    CAMECO,
    CENTRUS_ENERGY,
    COMMONWEALTH_FUSION,
    TAE_TECHNOLOGIES,
    HELION_ENERGY,
    GENERAL_FUSION,
]
"""All 8 Nuclear & Fusion company configurations."""

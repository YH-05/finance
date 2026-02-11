"""CompanyConfig definitions for Data Center & Cloud Infrastructure companies (Category 4).

Defines scraping configurations for 7 companies in the data center
and cloud infrastructure category. Each configuration specifies the
company's news/press URL, CSS selectors for article extraction, and
investment context.

Company list:
    1. Equinix
    2. Digital Realty
    3. CoreWeave
    4. Lambda Labs
    5. Arista Networks
    6. Vertiv
    7. Super Micro Computer
"""

from rss.services.company_scrapers.types import CompanyConfig, InvestmentContext

# ---------------------------------------------------------------------------
# Category constant
# ---------------------------------------------------------------------------

_CATEGORY = "data_center"
"""Category key for all Data Center & Cloud Infrastructure companies."""


# ---------------------------------------------------------------------------
# Company configurations
# ---------------------------------------------------------------------------

EQUINIX = CompanyConfig(
    key="equinix",
    name="Equinix",
    category=_CATEGORY,
    blog_url="https://newsroom.equinix.com/",
    article_list_selector="div.news-release",
    article_title_selector="h3.news-release__title",
    article_date_selector="span.news-release__date",
    requires_playwright=False,
    rate_limit_seconds=3.0,
    investment_context=InvestmentContext(
        tickers=("EQIX",),
        sectors=("Data Center", "REIT"),
        keywords=("colocation", "interconnection", "xScale", "AI data center"),
    ),
)

DIGITAL_REALTY = CompanyConfig(
    key="digital_realty",
    name="Digital Realty",
    category=_CATEGORY,
    blog_url="https://www.digitalrealty.com/about/newsroom",
    article_list_selector="div.newsroom-item",
    article_title_selector="h3.newsroom-item__title",
    article_date_selector="span.newsroom-item__date",
    requires_playwright=False,
    rate_limit_seconds=3.0,
    investment_context=InvestmentContext(
        tickers=("DLR",),
        sectors=("Data Center", "REIT"),
        keywords=("PlatformDIGITAL", "colocation", "CapEx", "AI campus"),
    ),
)

COREWEAVE = CompanyConfig(
    key="coreweave",
    name="CoreWeave",
    category=_CATEGORY,
    blog_url="https://www.coreweave.com/newsroom",
    article_list_selector="div.newsroom-card",
    article_title_selector="h3.newsroom-card__title",
    article_date_selector="span.newsroom-card__date",
    requires_playwright=False,
    rate_limit_seconds=3.0,
    investment_context=InvestmentContext(
        tickers=("CRWV",),
        sectors=("Cloud", "AI Infrastructure"),
        keywords=("GPU cloud", "NVIDIA", "AI inference", "Kubernetes"),
    ),
)

LAMBDA_LABS = CompanyConfig(
    key="lambda_labs",
    name="Lambda Labs",
    category=_CATEGORY,
    blog_url="https://lambda.ai/blog",
    article_list_selector="div.blog-post",
    article_title_selector="h2.blog-post__title",
    article_date_selector="span.blog-post__date",
    requires_playwright=True,
    rate_limit_seconds=5.0,
    investment_context=InvestmentContext(
        tickers=(),
        sectors=("Cloud", "AI Infrastructure"),
        keywords=("GPU cloud", "AI training", "deep learning", "Lambda Cloud"),
    ),
)

ARISTA_NETWORKS = CompanyConfig(
    key="arista_networks",
    name="Arista Networks",
    category=_CATEGORY,
    blog_url="https://www.arista.com/en/company/news",
    article_list_selector="div.news-item",
    article_title_selector="h3.news-item__title",
    article_date_selector="span.news-item__date",
    requires_playwright=False,
    rate_limit_seconds=3.0,
    investment_context=InvestmentContext(
        tickers=("ANET",),
        sectors=("Data Center", "Networking"),
        keywords=("Ethernet", "400G", "800G", "AI spine", "CloudVision"),
    ),
)

VERTIV = CompanyConfig(
    key="vertiv",
    name="Vertiv",
    category=_CATEGORY,
    blog_url="https://www.vertiv.com/en-us/about/news-and-insights/",
    article_list_selector="div.insights-card",
    article_title_selector="h3.insights-card__title",
    article_date_selector="span.insights-card__date",
    requires_playwright=False,
    rate_limit_seconds=3.0,
    investment_context=InvestmentContext(
        tickers=("VRT",),
        sectors=("Data Center", "Power Management"),
        keywords=("liquid cooling", "UPS", "thermal management", "CDU"),
    ),
)

SUPER_MICRO = CompanyConfig(
    key="super_micro",
    name="Super Micro Computer",
    category=_CATEGORY,
    blog_url="https://www.prnewswire.com/news/supermicro/",
    article_list_selector="div.news-release",
    article_title_selector="h3.news-release__title",
    article_date_selector="span.news-release__date",
    requires_playwright=False,
    rate_limit_seconds=3.0,
    investment_context=InvestmentContext(
        tickers=("SMCI",),
        sectors=("Data Center", "Server"),
        keywords=("AI server", "Blackwell", "GPU server", "liquid cooling"),
    ),
)


# ---------------------------------------------------------------------------
# Category list
# ---------------------------------------------------------------------------

DATA_CENTER_COMPANIES: list[CompanyConfig] = [
    EQUINIX,
    DIGITAL_REALTY,
    COREWEAVE,
    LAMBDA_LABS,
    ARISTA_NETWORKS,
    VERTIV,
    SUPER_MICRO,
]
"""All 7 Data Center & Cloud Infrastructure company configurations."""

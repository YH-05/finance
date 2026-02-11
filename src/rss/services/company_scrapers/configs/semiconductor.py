"""CompanyConfig definitions for Semiconductor Equipment companies (Category 3).

Defines scraping configurations for 6 companies in the semiconductor
equipment category. Each configuration specifies the company's
news/press URL, CSS selectors for article extraction, and investment context.

Company list:
    1. TSMC
    2. ASML
    3. Applied Materials
    4. Lam Research
    5. KLA Corporation
    6. Tokyo Electron
"""

from rss.services.company_scrapers.types import CompanyConfig, InvestmentContext

# ---------------------------------------------------------------------------
# Category constant
# ---------------------------------------------------------------------------

_CATEGORY = "semiconductor_equipment"
"""Category key for all Semiconductor Equipment companies."""


# ---------------------------------------------------------------------------
# Company configurations
# ---------------------------------------------------------------------------

TSMC = CompanyConfig(
    key="tsmc",
    name="TSMC",
    category=_CATEGORY,
    blog_url="https://pr.tsmc.com/english/latest-news",
    article_list_selector="div.news-item",
    article_title_selector="h3.news-item__title",
    article_date_selector="span.news-item__date",
    requires_playwright=False,
    rate_limit_seconds=3.0,
    investment_context=InvestmentContext(
        tickers=("TSM",),
        sectors=("Semiconductor", "Foundry"),
        keywords=("3nm", "2nm", "CoWoS", "advanced packaging", "AI chip manufacturing"),
    ),
)

ASML = CompanyConfig(
    key="asml",
    name="ASML",
    category=_CATEGORY,
    blog_url="https://www.asml.com/en/news",
    article_list_selector="div.news-card",
    article_title_selector="h3.news-card__title",
    article_date_selector="span.news-card__date",
    requires_playwright=False,
    rate_limit_seconds=3.0,
    investment_context=InvestmentContext(
        tickers=("ASML",),
        sectors=("Semiconductor", "Lithography"),
        keywords=("EUV", "High-NA EUV", "lithography", "TWINSCAN"),
    ),
)

APPLIED_MATERIALS = CompanyConfig(
    key="applied_materials",
    name="Applied Materials",
    category=_CATEGORY,
    blog_url="https://www.appliedmaterials.com/us/en/newsroom.html",
    article_list_selector="div.newsroom-item",
    article_title_selector="h3.newsroom-item__title",
    article_date_selector="span.newsroom-item__date",
    requires_playwright=False,
    rate_limit_seconds=3.0,
    investment_context=InvestmentContext(
        tickers=("AMAT",),
        sectors=("Semiconductor", "Equipment"),
        keywords=("CVD", "etching", "Centura", "materials engineering"),
    ),
)

LAM_RESEARCH = CompanyConfig(
    key="lam_research",
    name="Lam Research",
    category=_CATEGORY,
    blog_url="https://newsroom.lamresearch.com/",
    article_list_selector="div.press-release",
    article_title_selector="h3.press-release__title",
    article_date_selector="span.press-release__date",
    requires_playwright=False,
    rate_limit_seconds=3.0,
    investment_context=InvestmentContext(
        tickers=("LRCX",),
        sectors=("Semiconductor", "Equipment"),
        keywords=("etching", "deposition", "advanced packaging", "CSBG"),
    ),
)

KLA = CompanyConfig(
    key="kla",
    name="KLA Corporation",
    category=_CATEGORY,
    blog_url="https://www.kla.com/advance",
    article_list_selector="article.advance-post",
    article_title_selector="h2.advance-post__title",
    article_date_selector="time.advance-post__date",
    requires_playwright=False,
    rate_limit_seconds=3.0,
    investment_context=InvestmentContext(
        tickers=("KLAC",),
        sectors=("Semiconductor", "Process Control"),
        keywords=("process control", "yield optimization", "inspection", "metrology"),
    ),
)

TOKYO_ELECTRON = CompanyConfig(
    key="tokyo_electron",
    name="Tokyo Electron",
    category=_CATEGORY,
    blog_url="https://www.tel.co.jp/news/",
    article_list_selector="div.news-entry",
    article_title_selector="h3.news-entry__title",
    article_date_selector="span.news-entry__date",
    requires_playwright=False,
    rate_limit_seconds=3.0,
    investment_context=InvestmentContext(
        tickers=("8035.T",),
        sectors=("Semiconductor", "Equipment"),
        keywords=("coater/developer", "etching", "bonding", "front-end/back-end"),
    ),
)


# ---------------------------------------------------------------------------
# Category list
# ---------------------------------------------------------------------------

SEMICONDUCTOR_COMPANIES: list[CompanyConfig] = [
    TSMC,
    ASML,
    APPLIED_MATERIALS,
    LAM_RESEARCH,
    KLA,
    TOKYO_ELECTRON,
]
"""All 6 Semiconductor Equipment company configurations."""

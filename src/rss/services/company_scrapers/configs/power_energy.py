"""CompanyConfig definitions for Power & Energy Infrastructure companies (Category 6).

Defines scraping configurations for 7 companies in the power and
energy infrastructure category. Each configuration specifies the
company's news/press URL, CSS selectors for article extraction, and
investment context.

Company list:
    1. Constellation Energy
    2. NextEra Energy
    3. Vistra Energy
    4. Bloom Energy
    5. Eaton Corporation
    6. Schneider Electric
    7. nVent Electric
"""

from rss.services.company_scrapers.types import CompanyConfig, InvestmentContext

# ---------------------------------------------------------------------------
# Category constant
# ---------------------------------------------------------------------------

_CATEGORY = "power_energy"
"""Category key for all Power & Energy Infrastructure companies."""


# ---------------------------------------------------------------------------
# Company configurations
# ---------------------------------------------------------------------------

CONSTELLATION_ENERGY = CompanyConfig(
    key="constellation_energy",
    name="Constellation Energy",
    category=_CATEGORY,
    blog_url="https://www.constellationenergy.com/newsroom.html",
    article_list_selector="div.newsroom-item",
    article_title_selector="h3.newsroom-item__title",
    article_date_selector="span.newsroom-item__date",
    requires_playwright=False,
    rate_limit_seconds=3.0,
    investment_context=InvestmentContext(
        tickers=("CEG",),
        sectors=("Power", "Nuclear"),
        keywords=(
            "nuclear power",
            "data center power",
            "clean energy",
            "Constellation",
        ),
    ),
)

NEXTERA_ENERGY = CompanyConfig(
    key="nextera_energy",
    name="NextEra Energy",
    category=_CATEGORY,
    blog_url="https://investor.nexteraenergy.com/news-releases",
    article_list_selector="div.news-release",
    article_title_selector="h3.news-release__title",
    article_date_selector="span.news-release__date",
    requires_playwright=False,
    rate_limit_seconds=3.0,
    investment_context=InvestmentContext(
        tickers=("NEE",),
        sectors=("Power", "Renewable Energy"),
        keywords=("renewable energy", "solar", "wind", "FPL", "NextEra"),
    ),
)

VISTRA_ENERGY = CompanyConfig(
    key="vistra_energy",
    name="Vistra Energy",
    category=_CATEGORY,
    blog_url="https://investor.vistracorp.com/news",
    article_list_selector="div.news-item",
    article_title_selector="h3.news-item__title",
    article_date_selector="span.news-item__date",
    requires_playwright=False,
    rate_limit_seconds=3.0,
    investment_context=InvestmentContext(
        tickers=("VST",),
        sectors=("Power", "Energy"),
        keywords=("power generation", "AI power", "Meta", "natural gas", "Vistra"),
    ),
)

BLOOM_ENERGY = CompanyConfig(
    key="bloom_energy",
    name="Bloom Energy",
    category=_CATEGORY,
    blog_url="https://www.bloomenergy.com/newsroom/",
    article_list_selector="div.newsroom-card",
    article_title_selector="h3.newsroom-card__title",
    article_date_selector="span.newsroom-card__date",
    requires_playwright=False,
    rate_limit_seconds=3.0,
    investment_context=InvestmentContext(
        tickers=("BE",),
        sectors=("Power", "Fuel Cell"),
        keywords=("SOFC", "fuel cell", "data center power", "hydrogen", "Bloom Energy"),
    ),
)

EATON_CORPORATION = CompanyConfig(
    key="eaton_corporation",
    name="Eaton Corporation",
    category=_CATEGORY,
    blog_url="https://www.eaton.com/us/en-us/company/news-announcements/news-releases.html",
    article_list_selector="div.news-release",
    article_title_selector="h3.news-release__title",
    article_date_selector="span.news-release__date",
    requires_playwright=False,
    rate_limit_seconds=3.0,
    investment_context=InvestmentContext(
        tickers=("ETN",),
        sectors=("Power Management", "Electrical"),
        keywords=(
            "power management",
            "electrical distribution",
            "data center",
            "Eaton",
        ),
    ),
)

SCHNEIDER_ELECTRIC = CompanyConfig(
    key="schneider_electric",
    name="Schneider Electric",
    category=_CATEGORY,
    blog_url="https://blog.se.com/",
    article_list_selector="article.blog-post",
    article_title_selector="h2.blog-post__title",
    article_date_selector="span.blog-post__date",
    requires_playwright=False,
    rate_limit_seconds=3.0,
    investment_context=InvestmentContext(
        tickers=("SU",),
        sectors=("Power Management", "Data Center Cooling"),
        keywords=(
            "data center cooling",
            "power management",
            "EcoStruxure",
            "Schneider Electric",
        ),
    ),
)

NVENT_ELECTRIC = CompanyConfig(
    key="nvent_electric",
    name="nVent Electric",
    category=_CATEGORY,
    blog_url="https://blog.nvent.com/",
    article_list_selector="article.blog-entry",
    article_title_selector="h2.blog-entry__title",
    article_date_selector="span.blog-entry__date",
    requires_playwright=False,
    rate_limit_seconds=3.0,
    investment_context=InvestmentContext(
        tickers=("NVT",),
        sectors=("Electrical Protection", "Data Center"),
        keywords=(
            "electrical protection",
            "liquid cooling",
            "data center",
            "nVent",
        ),
    ),
)


# ---------------------------------------------------------------------------
# Category list
# ---------------------------------------------------------------------------

POWER_ENERGY_COMPANIES: list[CompanyConfig] = [
    CONSTELLATION_ENERGY,
    NEXTERA_ENERGY,
    VISTRA_ENERGY,
    BLOOM_ENERGY,
    EATON_CORPORATION,
    SCHNEIDER_ELECTRIC,
    NVENT_ELECTRIC,
]
"""All 7 Power & Energy Infrastructure company configurations."""

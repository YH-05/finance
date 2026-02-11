"""CompanyConfig definitions for Networking companies (Category 5).

Defines scraping configurations for 2 companies in the networking
category. Each configuration specifies the company's news/press URL,
CSS selectors for article extraction, and investment context.

Note: Arista Networks is listed in Category 4 (Data Center) and is
not duplicated here.

Company list:
    1. Cisco
    2. Juniper Networks
"""

from rss.services.company_scrapers.types import CompanyConfig, InvestmentContext

# ---------------------------------------------------------------------------
# Category constant
# ---------------------------------------------------------------------------

_CATEGORY = "networking"
"""Category key for all Networking companies."""


# ---------------------------------------------------------------------------
# Company configurations
# ---------------------------------------------------------------------------

CISCO = CompanyConfig(
    key="cisco",
    name="Cisco",
    category=_CATEGORY,
    blog_url="https://newsroom.cisco.com/",
    article_list_selector="div.press-release",
    article_title_selector="h3.press-release__title",
    article_date_selector="span.press-release__date",
    requires_playwright=False,
    rate_limit_seconds=3.0,
    investment_context=InvestmentContext(
        tickers=("CSCO",),
        sectors=("Networking", "Security"),
        keywords=("network security", "AI networking", "Webex", "Meraki"),
    ),
)

JUNIPER_NETWORKS = CompanyConfig(
    key="juniper_networks",
    name="Juniper Networks",
    category=_CATEGORY,
    blog_url="https://newsroom.juniper.net/",
    article_list_selector="div.news-item",
    article_title_selector="h3.news-item__title",
    article_date_selector="span.news-item__date",
    requires_playwright=False,
    rate_limit_seconds=3.0,
    investment_context=InvestmentContext(
        tickers=("JNPR",),
        sectors=("Networking",),
        keywords=("AI-native networking", "Mist AI", "Junos", "Apstra"),
    ),
)


# ---------------------------------------------------------------------------
# Category list
# ---------------------------------------------------------------------------

NETWORKING_COMPANIES: list[CompanyConfig] = [
    CISCO,
    JUNIPER_NETWORKS,
]
"""All 2 Networking company configurations."""

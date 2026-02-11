"""CompanyConfig definitions for Physical AI & Robotics companies (Category 8).

Defines scraping configurations for 9 companies in the physical AI and
robotics category. Each configuration specifies the company's
news/press URL, CSS selectors for article extraction, and
investment context.

Company list:
    1. Tesla (Optimus)
    2. Intuitive Surgical
    3. Fanuc
    4. ABB
    5. Boston Dynamics
    6. Figure AI
    7. Physical Intelligence
    8. Agility Robotics
    9. Symbotic
"""

from rss.services.company_scrapers.types import CompanyConfig, InvestmentContext

# ---------------------------------------------------------------------------
# Category constant
# ---------------------------------------------------------------------------

_CATEGORY = "physical_ai"
"""Category key for all Physical AI & Robotics companies."""


# ---------------------------------------------------------------------------
# Company configurations
# ---------------------------------------------------------------------------

TESLA_OPTIMUS = CompanyConfig(
    key="tesla_optimus",
    name="Tesla (Optimus)",
    category=_CATEGORY,
    blog_url="https://www.tesla.com/blog",
    article_list_selector="div.blog-post",
    article_title_selector="h2.blog-post__title",
    article_date_selector="span.blog-post__date",
    requires_playwright=False,
    rate_limit_seconds=3.0,
    investment_context=InvestmentContext(
        tickers=("TSLA",),
        sectors=("Robotics", "Autonomous Vehicles"),
        keywords=("Optimus", "humanoid robot", "Tesla Bot", "FSD", "Tesla"),
    ),
)

INTUITIVE_SURGICAL = CompanyConfig(
    key="intuitive_surgical",
    name="Intuitive Surgical",
    category=_CATEGORY,
    blog_url="https://investor.intuitivesurgical.com/news-events/press-releases",
    article_list_selector="div.press-release",
    article_title_selector="h3.press-release__title",
    article_date_selector="span.press-release__date",
    requires_playwright=False,
    rate_limit_seconds=3.0,
    investment_context=InvestmentContext(
        tickers=("ISRG",),
        sectors=("Medical Robotics", "Healthcare"),
        keywords=("da Vinci", "surgical robot", "Ion", "Intuitive Surgical"),
    ),
)

FANUC = CompanyConfig(
    key="fanuc",
    name="Fanuc",
    category=_CATEGORY,
    blog_url="https://www.fanuc.co.jp/en/product/new_product/index.html",
    article_list_selector="div.product-news",
    article_title_selector="h3.product-news__title",
    article_date_selector="span.product-news__date",
    requires_playwright=True,
    rate_limit_seconds=5.0,
    investment_context=InvestmentContext(
        tickers=("6954.T",),
        sectors=("Industrial Robotics", "CNC"),
        keywords=("industrial robot", "CNC", "factory automation", "Fanuc"),
    ),
)

ABB = CompanyConfig(
    key="abb",
    name="ABB",
    category=_CATEGORY,
    blog_url="https://new.abb.com/news",
    article_list_selector="div.news-item",
    article_title_selector="h3.news-item__title",
    article_date_selector="span.news-item__date",
    requires_playwright=False,
    rate_limit_seconds=3.0,
    investment_context=InvestmentContext(
        tickers=("ABB",),
        sectors=("Robotics", "Electrification"),
        keywords=("robotics", "electrification", "automation", "ABB"),
    ),
)

BOSTON_DYNAMICS = CompanyConfig(
    key="boston_dynamics",
    name="Boston Dynamics",
    category=_CATEGORY,
    blog_url="https://bostondynamics.com/blog",
    article_list_selector="div.blog-card",
    article_title_selector="h3.blog-card__title",
    article_date_selector="span.blog-card__date",
    requires_playwright=False,
    rate_limit_seconds=3.0,
    investment_context=InvestmentContext(
        tickers=(),
        sectors=("Robotics", "Humanoid"),
        keywords=("Atlas", "Spot", "humanoid robot", "Hyundai", "Boston Dynamics"),
    ),
)

FIGURE_AI = CompanyConfig(
    key="figure_ai",
    name="Figure AI",
    category=_CATEGORY,
    blog_url="https://www.figure.ai/news",
    article_list_selector="div.news-card",
    article_title_selector="h3.news-card__title",
    article_date_selector="span.news-card__date",
    requires_playwright=False,
    rate_limit_seconds=3.0,
    investment_context=InvestmentContext(
        tickers=(),
        sectors=("Robotics", "Humanoid"),
        keywords=("Helix", "humanoid robot", "logistics", "Figure AI"),
    ),
)

PHYSICAL_INTELLIGENCE = CompanyConfig(
    key="physical_intelligence",
    name="Physical Intelligence",
    category=_CATEGORY,
    blog_url="https://www.physicalintelligence.company/blog",
    article_list_selector="div.blog-entry",
    article_title_selector="h3.blog-entry__title",
    article_date_selector="span.blog-entry__date",
    requires_playwright=True,
    rate_limit_seconds=5.0,
    investment_context=InvestmentContext(
        tickers=(),
        sectors=("Robotics", "Foundation Models"),
        keywords=(
            "robot foundation model",
            "generalist robot",
            "pi0",
            "Physical Intelligence",
        ),
    ),
)

AGILITY_ROBOTICS = CompanyConfig(
    key="agility_robotics",
    name="Agility Robotics",
    category=_CATEGORY,
    blog_url="https://agilityrobotics.com/about/press",
    article_list_selector="div.press-item",
    article_title_selector="h3.press-item__title",
    article_date_selector="span.press-item__date",
    requires_playwright=False,
    rate_limit_seconds=3.0,
    investment_context=InvestmentContext(
        tickers=(),
        sectors=("Robotics", "Warehouse Automation"),
        keywords=("Digit", "humanoid robot", "warehouse", "Agility Robotics"),
    ),
)

SYMBOTIC = CompanyConfig(
    key="symbotic",
    name="Symbotic",
    category=_CATEGORY,
    blog_url="https://www.symbotic.com/innovation-insights/blog",
    article_list_selector="div.blog-post",
    article_title_selector="h3.blog-post__title",
    article_date_selector="span.blog-post__date",
    requires_playwright=False,
    rate_limit_seconds=3.0,
    investment_context=InvestmentContext(
        tickers=("SYM",),
        sectors=("Warehouse Automation", "AI"),
        keywords=("AI warehouse", "supply chain", "automation", "Symbotic"),
    ),
)


# ---------------------------------------------------------------------------
# Category list
# ---------------------------------------------------------------------------

PHYSICAL_AI_COMPANIES: list[CompanyConfig] = [
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
"""All 9 Physical AI & Robotics company configurations."""

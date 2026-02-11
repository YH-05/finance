"""CompanyConfig definitions for SaaS / AI-powered software companies (Category 9).

Defines scraping configurations for 10 companies in the SaaS / AI-powered
software category. Each configuration specifies the company's blog URL,
CSS selectors for article extraction, and investment context.

Company list:
    1. Salesforce
    2. ServiceNow
    3. Palantir
    4. Snowflake
    5. Datadog
    6. CrowdStrike
    7. MongoDB
    8. UiPath
    9. C3.ai
    10. Databricks
"""

from rss.services.company_scrapers.types import CompanyConfig, InvestmentContext

# ---------------------------------------------------------------------------
# Category constant
# ---------------------------------------------------------------------------

_CATEGORY = "saas"
"""Category key for all SaaS / AI-powered software companies."""


# ---------------------------------------------------------------------------
# Company configurations
# ---------------------------------------------------------------------------

SALESFORCE = CompanyConfig(
    key="salesforce",
    name="Salesforce",
    category=_CATEGORY,
    blog_url="https://salesforce.com/blog",
    article_list_selector="article.blog-card",
    article_title_selector="h3.blog-card__title",
    article_date_selector="span.blog-card__date",
    requires_playwright=False,
    rate_limit_seconds=3.0,
    investment_context=InvestmentContext(
        tickers=("CRM",),
        sectors=("SaaS", "Enterprise AI"),
        keywords=("Einstein AI", "Agentforce", "Salesforce", "Data Cloud"),
    ),
)

SERVICENOW = CompanyConfig(
    key="servicenow",
    name="ServiceNow",
    category=_CATEGORY,
    blog_url="https://servicenow.com/community/now-platform-blog/bg-p/now-platform",
    article_list_selector="div.lia-message-body-content",
    article_title_selector="h2.message-subject",
    article_date_selector="span.message-date",
    requires_playwright=True,
    rate_limit_seconds=5.0,
    investment_context=InvestmentContext(
        tickers=("NOW",),
        sectors=("SaaS", "Workflow Automation"),
        keywords=("Now Platform", "ServiceNow", "AI workflow", "ITSM"),
    ),
)

PALANTIR = CompanyConfig(
    key="palantir",
    name="Palantir",
    category=_CATEGORY,
    blog_url="https://blog.palantir.com",
    article_list_selector="div.blog-post",
    article_title_selector="h2.blog-post__title",
    article_date_selector="span.blog-post__date",
    requires_playwright=False,
    rate_limit_seconds=3.0,
    investment_context=InvestmentContext(
        tickers=("PLTR",),
        sectors=("SaaS", "Data Analytics", "Government AI"),
        keywords=("Foundry", "Gotham", "AIP", "Palantir"),
    ),
)

SNOWFLAKE = CompanyConfig(
    key="snowflake",
    name="Snowflake",
    category=_CATEGORY,
    blog_url="https://snowflake.com/en/engineering-blog",
    article_list_selector="div.blog-card",
    article_title_selector="h3.blog-card__title",
    article_date_selector="span.blog-card__date",
    requires_playwright=False,
    rate_limit_seconds=3.0,
    investment_context=InvestmentContext(
        tickers=("SNOW",),
        sectors=("SaaS", "Data Cloud"),
        keywords=("Snowflake", "data cloud", "Cortex AI", "Snowpark"),
    ),
)

DATADOG = CompanyConfig(
    key="datadog",
    name="Datadog",
    category=_CATEGORY,
    blog_url="https://datadoghq.com/blog",
    article_list_selector="article.blog-entry",
    article_title_selector="h2.blog-entry__title",
    article_date_selector="time.blog-entry__date",
    requires_playwright=False,
    rate_limit_seconds=3.0,
    investment_context=InvestmentContext(
        tickers=("DDOG",),
        sectors=("SaaS", "Observability"),
        keywords=("Datadog", "AI observability", "LLM monitoring", "APM"),
    ),
)

CROWDSTRIKE = CompanyConfig(
    key="crowdstrike",
    name="CrowdStrike",
    category=_CATEGORY,
    blog_url="https://crowdstrike.com/en-us/blog",
    article_list_selector="div.blog-post",
    article_title_selector="h2.blog-post__title",
    article_date_selector="span.blog-post__date",
    requires_playwright=False,
    rate_limit_seconds=3.0,
    investment_context=InvestmentContext(
        tickers=("CRWD",),
        sectors=("SaaS", "Cybersecurity"),
        keywords=("Falcon", "CrowdStrike", "AI threat detection", "XDR"),
    ),
)

MONGODB = CompanyConfig(
    key="mongodb",
    name="MongoDB",
    category=_CATEGORY,
    blog_url="https://mongodb.com/company/blog",
    article_list_selector="article.blog-card",
    article_title_selector="h3.blog-card__title",
    article_date_selector="span.blog-card__date",
    requires_playwright=False,
    rate_limit_seconds=3.0,
    investment_context=InvestmentContext(
        tickers=("MDB",),
        sectors=("SaaS", "Database"),
        keywords=("MongoDB", "Atlas", "vector search", "document database"),
    ),
)

UIPATH = CompanyConfig(
    key="uipath",
    name="UiPath",
    category=_CATEGORY,
    blog_url="https://uipath.com/newsroom",
    article_list_selector="div.news-card",
    article_title_selector="h3.news-card__title",
    article_date_selector="span.news-card__date",
    requires_playwright=False,
    rate_limit_seconds=3.0,
    investment_context=InvestmentContext(
        tickers=("PATH",),
        sectors=("SaaS", "RPA"),
        keywords=("UiPath", "agentic automation", "RPA", "process mining"),
    ),
)

C3AI = CompanyConfig(
    key="c3ai",
    name="C3.ai",
    category=_CATEGORY,
    blog_url="https://c3.ai/blog",
    article_list_selector="article.post-card",
    article_title_selector="h2.post-card__title",
    article_date_selector="time.post-card__date",
    requires_playwright=False,
    rate_limit_seconds=3.0,
    investment_context=InvestmentContext(
        tickers=("AI",),
        sectors=("SaaS", "Enterprise AI"),
        keywords=("C3 AI", "enterprise AI", "generative AI", "predictive"),
    ),
)

DATABRICKS = CompanyConfig(
    key="databricks",
    name="Databricks",
    category=_CATEGORY,
    blog_url="https://databricks.com/blog",
    article_list_selector="div.blog-post-card",
    article_title_selector="h3.blog-post-card__title",
    article_date_selector="span.blog-post-card__date",
    requires_playwright=False,
    rate_limit_seconds=3.0,
    investment_context=InvestmentContext(
        tickers=(),
        sectors=("SaaS", "Data & AI"),
        keywords=("Databricks", "Lakehouse", "Unity Catalog", "Mosaic ML"),
    ),
)


# ---------------------------------------------------------------------------
# Category list
# ---------------------------------------------------------------------------

SAAS_COMPANIES: list[CompanyConfig] = [
    SALESFORCE,
    SERVICENOW,
    PALANTIR,
    SNOWFLAKE,
    DATADOG,
    CROWDSTRIKE,
    MONGODB,
    UIPATH,
    C3AI,
    DATABRICKS,
]
"""All 10 SaaS / AI-powered software company configurations."""

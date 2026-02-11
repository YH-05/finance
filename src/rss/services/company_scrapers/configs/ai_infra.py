"""CompanyConfig definitions for AI infrastructure / MLOps companies (Category 10).

Defines scraping configurations for 7 companies in the AI infrastructure
and MLOps category. Each configuration specifies the company's blog URL,
CSS selectors for article extraction, and investment context.

Company list:
    1. HuggingFace
    2. Scale AI
    3. Weights & Biases
    4. Together AI
    5. Anyscale
    6. Replicate
    7. Elastic
"""

from rss.services.company_scrapers.types import CompanyConfig, InvestmentContext

# ---------------------------------------------------------------------------
# Category constant
# ---------------------------------------------------------------------------

_CATEGORY = "ai_infra"
"""Category key for all AI infrastructure / MLOps companies."""


# ---------------------------------------------------------------------------
# Company configurations
# ---------------------------------------------------------------------------

HUGGINGFACE = CompanyConfig(
    key="huggingface",
    name="HuggingFace",
    category=_CATEGORY,
    blog_url="https://huggingface.co/blog",
    article_list_selector="article.blog-post",
    article_title_selector="h2.blog-post__title",
    article_date_selector="time.blog-post__date",
    requires_playwright=False,
    rate_limit_seconds=3.0,
    investment_context=InvestmentContext(
        tickers=(),
        sectors=("AI Infrastructure", "MLOps"),
        keywords=("HuggingFace", "Transformers", "model hub", "open source AI"),
    ),
)

SCALE_AI = CompanyConfig(
    key="scale_ai",
    name="Scale AI",
    category=_CATEGORY,
    blog_url="https://scale.com/blog",
    article_list_selector="div.blog-card",
    article_title_selector="h3.blog-card__title",
    article_date_selector="span.blog-card__date",
    requires_playwright=False,
    rate_limit_seconds=3.0,
    investment_context=InvestmentContext(
        tickers=(),
        sectors=("AI Infrastructure", "Data Labeling"),
        keywords=("Scale AI", "data labeling", "agentic AI", "RLHF"),
    ),
)

WANDB = CompanyConfig(
    key="wandb",
    name="Weights & Biases",
    category=_CATEGORY,
    blog_url="https://wandb.ai/fully-connected/blog",
    article_list_selector="article.blog-entry",
    article_title_selector="h2.blog-entry__title",
    article_date_selector="span.blog-entry__date",
    requires_playwright=True,
    rate_limit_seconds=5.0,
    investment_context=InvestmentContext(
        tickers=(),
        sectors=("AI Infrastructure", "MLOps"),
        keywords=("Weights & Biases", "W&B", "experiment tracking", "ML platform"),
    ),
)

TOGETHER_AI = CompanyConfig(
    key="together_ai",
    name="Together AI",
    category=_CATEGORY,
    blog_url="https://together.ai/blog",
    article_list_selector="div.post-card",
    article_title_selector="h3.post-card__title",
    article_date_selector="span.post-card__date",
    requires_playwright=False,
    rate_limit_seconds=3.0,
    investment_context=InvestmentContext(
        tickers=(),
        sectors=("AI Infrastructure", "Inference"),
        keywords=("Together AI", "open source inference", "Refuel.ai", "GPU cloud"),
    ),
)

ANYSCALE = CompanyConfig(
    key="anyscale",
    name="Anyscale",
    category=_CATEGORY,
    blog_url="https://anyscale.com/blog",
    article_list_selector="div.blog-post",
    article_title_selector="h2.blog-post__title",
    article_date_selector="span.blog-post__date",
    requires_playwright=False,
    rate_limit_seconds=3.0,
    investment_context=InvestmentContext(
        tickers=(),
        sectors=("AI Infrastructure", "Distributed Computing"),
        keywords=("Anyscale", "Ray", "distributed computing", "ML scaling"),
    ),
)

REPLICATE = CompanyConfig(
    key="replicate",
    name="Replicate",
    category=_CATEGORY,
    blog_url="https://replicate.com/blog",
    article_list_selector="article.post-item",
    article_title_selector="h2.post-item__title",
    article_date_selector="time.post-item__date",
    requires_playwright=False,
    rate_limit_seconds=3.0,
    investment_context=InvestmentContext(
        tickers=(),
        sectors=("AI Infrastructure", "Model Hosting"),
        keywords=("Replicate", "model hosting", "inference API", "Cog"),
    ),
)

ELASTIC = CompanyConfig(
    key="elastic",
    name="Elastic",
    category=_CATEGORY,
    blog_url="https://elastic.co/blog",
    article_list_selector="article.blog-card",
    article_title_selector="h3.blog-card__title",
    article_date_selector="span.blog-card__date",
    requires_playwright=False,
    rate_limit_seconds=3.0,
    investment_context=InvestmentContext(
        tickers=("ESTC",),
        sectors=("AI Infrastructure", "Search"),
        keywords=("Elasticsearch", "Elastic", "vector search", "AI agent"),
    ),
)


# ---------------------------------------------------------------------------
# Category list
# ---------------------------------------------------------------------------

AI_INFRA_COMPANIES: list[CompanyConfig] = [
    HUGGINGFACE,
    SCALE_AI,
    WANDB,
    TOGETHER_AI,
    ANYSCALE,
    REPLICATE,
    ELASTIC,
]
"""All 7 AI infrastructure / MLOps company configurations."""

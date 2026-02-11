"""CompanyConfig definitions for AI/LLM development companies (Category 1).

Defines scraping configurations for 11 companies in the AI/LLM
development category. Each configuration specifies the company's
blog URL, CSS selectors for article extraction, and investment context.

Company list:
    1. OpenAI
    2. Google DeepMind
    3. Meta AI
    4. Anthropic
    5. Microsoft AI
    6. xAI
    7. Mistral AI
    8. Cohere
    9. Stability AI
    10. Perplexity AI
    11. Inflection AI
"""

from rss.services.company_scrapers.types import CompanyConfig, InvestmentContext

# ---------------------------------------------------------------------------
# Category constant
# ---------------------------------------------------------------------------

_CATEGORY = "ai_llm"
"""Category key for all AI/LLM development companies."""


# ---------------------------------------------------------------------------
# Company configurations
# ---------------------------------------------------------------------------

OPENAI = CompanyConfig(
    key="openai",
    name="OpenAI",
    category=_CATEGORY,
    blog_url="https://openai.com/news/",
    article_list_selector="li[data-testid='card']",
    article_title_selector="h3",
    article_date_selector="time",
    requires_playwright=False,
    rate_limit_seconds=3.0,
    investment_context=InvestmentContext(
        tickers=("MSFT",),
        sectors=("AI/LLM",),
        keywords=("ChatGPT", "GPT", "OpenAI", "DALL-E", "Sora"),
    ),
)

DEEPMIND = CompanyConfig(
    key="deepmind",
    name="Google DeepMind",
    category=_CATEGORY,
    blog_url="https://deepmind.google/blog",
    article_list_selector="article.blog-card",
    article_title_selector="h3.blog-card__title",
    article_date_selector="span.blog-card__date",
    requires_playwright=False,
    rate_limit_seconds=3.0,
    investment_context=InvestmentContext(
        tickers=("GOOGL",),
        sectors=("AI/LLM", "Cloud"),
        keywords=("Gemini", "DeepMind", "AlphaFold", "TPU"),
    ),
)

META_AI = CompanyConfig(
    key="meta_ai",
    name="Meta AI",
    category=_CATEGORY,
    blog_url="https://ai.meta.com/blog",
    article_list_selector="div.blog-post-card",
    article_title_selector="h2.blog-post-card__title",
    article_date_selector="span.blog-post-card__date",
    requires_playwright=False,
    rate_limit_seconds=3.0,
    investment_context=InvestmentContext(
        tickers=("META",),
        sectors=("AI/LLM", "Social Media"),
        keywords=("Llama", "Meta AI", "Reality Labs", "PyTorch"),
    ),
)

ANTHROPIC = CompanyConfig(
    key="anthropic",
    name="Anthropic",
    category=_CATEGORY,
    blog_url="https://anthropic.com/research",
    article_list_selector="a[class*='PostCard_post-card']",
    article_title_selector="h3[class*='PostCard_post-card-title']",
    article_date_selector="div[class*='PostCard_post-card-date']",
    requires_playwright=False,
    rate_limit_seconds=3.0,
    investment_context=InvestmentContext(
        tickers=("AMZN", "GOOGL"),
        sectors=("AI/LLM", "AI Safety"),
        keywords=("Claude", "Anthropic", "Constitutional AI", "AWS Bedrock"),
    ),
)

MICROSOFT_AI = CompanyConfig(
    key="microsoft_ai",
    name="Microsoft AI",
    category=_CATEGORY,
    blog_url="https://microsoft.com/en-us/ai/blog",
    article_list_selector="div.card[role='listitem']",
    article_title_selector="h3.card__title",
    article_date_selector="time.card__date",
    requires_playwright=False,
    rate_limit_seconds=3.0,
    investment_context=InvestmentContext(
        tickers=("MSFT",),
        sectors=("AI/LLM", "Cloud", "Enterprise"),
        keywords=("Copilot", "Azure AI", "Microsoft AI", "Phi"),
    ),
)

XAI = CompanyConfig(
    key="xai",
    name="xAI",
    category=_CATEGORY,
    blog_url="https://x.ai/news",
    article_list_selector="article.news-item",
    article_title_selector="h2.news-item__title",
    article_date_selector="time.news-item__date",
    requires_playwright=False,
    rate_limit_seconds=3.0,
    investment_context=InvestmentContext(
        tickers=(),
        sectors=("AI/LLM",),
        keywords=("Grok", "xAI", "Colossus"),
    ),
)

MISTRAL_AI = CompanyConfig(
    key="mistral_ai",
    name="Mistral AI",
    category=_CATEGORY,
    blog_url="https://mistral.ai/news",
    article_list_selector="div.news-card",
    article_title_selector="h3.news-card__title",
    article_date_selector="span.news-card__date",
    requires_playwright=False,
    rate_limit_seconds=3.0,
    investment_context=InvestmentContext(
        tickers=(),
        sectors=("AI/LLM",),
        keywords=("Mistral", "Le Chat", "Mixtral"),
    ),
)

COHERE = CompanyConfig(
    key="cohere",
    name="Cohere",
    category=_CATEGORY,
    blog_url="https://cohere.com/blog",
    article_list_selector="article.blog-entry",
    article_title_selector="h2.blog-entry__title",
    article_date_selector="span.blog-entry__date",
    requires_playwright=False,
    rate_limit_seconds=3.0,
    investment_context=InvestmentContext(
        tickers=(),
        sectors=("AI/LLM", "Enterprise AI"),
        keywords=("Command R", "Cohere", "RAG", "Embed"),
    ),
)

STABILITY_AI = CompanyConfig(
    key="stability_ai",
    name="Stability AI",
    category=_CATEGORY,
    blog_url="https://stability.ai/news",
    article_list_selector="article.post-card",
    article_title_selector="h2.post-card__title",
    article_date_selector="time.post-card__date",
    requires_playwright=False,
    rate_limit_seconds=3.0,
    investment_context=InvestmentContext(
        tickers=(),
        sectors=("AI/LLM", "Generative AI"),
        keywords=("Stable Diffusion", "Stability AI", "Stable Video"),
    ),
)

PERPLEXITY_AI = CompanyConfig(
    key="perplexity_ai",
    name="Perplexity AI",
    category=_CATEGORY,
    blog_url="https://perplexity.ai/hub",
    article_list_selector="div.hub-post",
    article_title_selector="h2.hub-post__title",
    article_date_selector="span.hub-post__date",
    requires_playwright=True,
    rate_limit_seconds=5.0,
    investment_context=InvestmentContext(
        tickers=(),
        sectors=("AI/LLM", "Search"),
        keywords=("Perplexity", "AI Search", "Sonar"),
    ),
)

INFLECTION_AI = CompanyConfig(
    key="inflection_ai",
    name="Inflection AI",
    category=_CATEGORY,
    blog_url="https://inflection.ai/blog",
    article_list_selector="article.blog-item",
    article_title_selector="h2.blog-item__title",
    article_date_selector="time.blog-item__date",
    requires_playwright=False,
    rate_limit_seconds=3.0,
    investment_context=InvestmentContext(
        tickers=("MSFT", "NVDA"),
        sectors=("AI/LLM",),
        keywords=("Pi", "Inflection AI", "Personal AI"),
    ),
)


# ---------------------------------------------------------------------------
# Category list
# ---------------------------------------------------------------------------

AI_LLM_COMPANIES: list[CompanyConfig] = [
    OPENAI,
    DEEPMIND,
    META_AI,
    ANTHROPIC,
    MICROSOFT_AI,
    XAI,
    MISTRAL_AI,
    COHERE,
    STABILITY_AI,
    PERPLEXITY_AI,
    INFLECTION_AI,
]
"""All 11 AI/LLM development company configurations."""

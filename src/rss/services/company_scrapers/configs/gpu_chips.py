"""CompanyConfig definitions for GPU/Compute Chip companies (Category 2).

Defines scraping configurations for 10 companies in the GPU and
compute chip category. Each configuration specifies the company's
blog URL, CSS selectors for article extraction, and investment context.

Company list:
    1. NVIDIA
    2. AMD
    3. Intel
    4. Broadcom
    5. Qualcomm
    6. ARM Holdings
    7. Marvell Technology
    8. Cerebras Systems
    9. SambaNova
    10. Tenstorrent
"""

from rss.services.company_scrapers.types import CompanyConfig, InvestmentContext

# ---------------------------------------------------------------------------
# Category constant
# ---------------------------------------------------------------------------

_CATEGORY = "gpu_chips"
"""Category key for all GPU/Compute Chip companies."""


# ---------------------------------------------------------------------------
# Company configurations
# ---------------------------------------------------------------------------

NVIDIA = CompanyConfig(
    key="nvidia",
    name="NVIDIA",
    category=_CATEGORY,
    blog_url="https://blogs.nvidia.com/",
    article_list_selector="article.post-item",
    article_title_selector="h2.post-item__title",
    article_date_selector="time.post-item__date",
    requires_playwright=False,
    rate_limit_seconds=3.0,
    investment_context=InvestmentContext(
        tickers=("NVDA",),
        sectors=("Semiconductor", "Data Center"),
        keywords=("GPU", "CUDA", "H100", "Blackwell", "inference"),
    ),
)

AMD = CompanyConfig(
    key="amd",
    name="AMD",
    category=_CATEGORY,
    blog_url="https://www.amd.com/en/blogs.html",
    article_list_selector="div.blog-card",
    article_title_selector="h3.blog-card__title",
    article_date_selector="span.blog-card__date",
    requires_playwright=False,
    rate_limit_seconds=3.0,
    investment_context=InvestmentContext(
        tickers=("AMD",),
        sectors=("Semiconductor", "Data Center"),
        keywords=("MI300X", "ROCm", "EPYC", "Ryzen AI", "Instinct"),
    ),
)

INTEL = CompanyConfig(
    key="intel",
    name="Intel",
    category=_CATEGORY,
    blog_url="https://www.intc.com/news-events/press-releases",
    article_list_selector="div.press-release-item",
    article_title_selector="h3.press-release-item__title",
    article_date_selector="time.press-release-item__date",
    requires_playwright=False,
    rate_limit_seconds=3.0,
    investment_context=InvestmentContext(
        tickers=("INTC",),
        sectors=("Semiconductor", "Foundry"),
        keywords=("Xeon", "Gaudi", "Intel Foundry", "AI inference"),
    ),
)

BROADCOM = CompanyConfig(
    key="broadcom",
    name="Broadcom",
    category=_CATEGORY,
    blog_url="https://news.broadcom.com/releases",
    article_list_selector="div.news-release",
    article_title_selector="h3.news-release__title",
    article_date_selector="span.news-release__date",
    requires_playwright=False,
    rate_limit_seconds=3.0,
    investment_context=InvestmentContext(
        tickers=("AVGO",),
        sectors=("Semiconductor", "Networking"),
        keywords=("Custom ASIC", "Tomahawk", "VMware", "AI networking"),
    ),
)

QUALCOMM = CompanyConfig(
    key="qualcomm",
    name="Qualcomm",
    category=_CATEGORY,
    blog_url="https://www.qualcomm.com/news/releases",
    article_list_selector="div.news-item",
    article_title_selector="h3.news-item__title",
    article_date_selector="span.news-item__date",
    requires_playwright=False,
    rate_limit_seconds=3.0,
    investment_context=InvestmentContext(
        tickers=("QCOM",),
        sectors=("Semiconductor", "Edge AI"),
        keywords=("Snapdragon", "Cloud AI 100", "edge AI", "NPU"),
    ),
)

ARM = CompanyConfig(
    key="arm",
    name="ARM Holdings",
    category=_CATEGORY,
    blog_url="https://newsroom.arm.com/blog",
    article_list_selector="article.blog-entry",
    article_title_selector="h2.blog-entry__title",
    article_date_selector="time.blog-entry__date",
    requires_playwright=False,
    rate_limit_seconds=3.0,
    investment_context=InvestmentContext(
        tickers=("ARM",),
        sectors=("Semiconductor", "IP Licensing"),
        keywords=("Armv9", "Cortex", "Ethos NPU", "edge AI"),
    ),
)

MARVELL = CompanyConfig(
    key="marvell",
    name="Marvell Technology",
    category=_CATEGORY,
    blog_url="https://www.marvell.com/blogs.html",
    article_list_selector="div.blog-post",
    article_title_selector="h3.blog-post__title",
    article_date_selector="span.blog-post__date",
    requires_playwright=False,
    rate_limit_seconds=3.0,
    investment_context=InvestmentContext(
        tickers=("MRVL",),
        sectors=("Semiconductor", "Data Center"),
        keywords=("custom silicon", "electro-optics", "DPU", "AI interconnect"),
    ),
)

CEREBRAS = CompanyConfig(
    key="cerebras",
    name="Cerebras Systems",
    category=_CATEGORY,
    blog_url="https://cerebras.ai/blog",
    article_list_selector="div.post-card",
    article_title_selector="h2.post-card__title",
    article_date_selector="span.post-card__date",
    requires_playwright=True,
    rate_limit_seconds=5.0,
    investment_context=InvestmentContext(
        tickers=(),
        sectors=("Semiconductor", "AI Accelerator"),
        keywords=("Wafer-Scale Engine", "CS-3", "Condor Galaxy", "inference"),
    ),
)

SAMBANOVA = CompanyConfig(
    key="sambanova",
    name="SambaNova",
    category=_CATEGORY,
    blog_url="https://sambanova.ai/blog",
    article_list_selector="div.blog-card",
    article_title_selector="h2.blog-card__title",
    article_date_selector="span.blog-card__date",
    requires_playwright=True,
    rate_limit_seconds=5.0,
    investment_context=InvestmentContext(
        tickers=(),
        sectors=("Semiconductor", "AI Accelerator"),
        keywords=("RDU", "SN40L", "dataflow", "energy-efficient inference"),
    ),
)

TENSTORRENT = CompanyConfig(
    key="tenstorrent",
    name="Tenstorrent",
    category=_CATEGORY,
    blog_url="https://tenstorrent.com/vision",
    article_list_selector="article.vision-post",
    article_title_selector="h2.vision-post__title",
    article_date_selector="time.vision-post__date",
    requires_playwright=False,
    rate_limit_seconds=3.0,
    investment_context=InvestmentContext(
        tickers=(),
        sectors=("Semiconductor", "AI Accelerator"),
        keywords=("RISC-V", "Wormhole", "Grayskull", "Jim Keller"),
    ),
)


# ---------------------------------------------------------------------------
# Category list
# ---------------------------------------------------------------------------

GPU_CHIPS_COMPANIES: list[CompanyConfig] = [
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
"""All 10 GPU/Compute Chip company configurations."""

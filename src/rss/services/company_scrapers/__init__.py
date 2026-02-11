"""Company scrapers package for AI investment value chain tracking.

Provides data types, exception classes, and scraping infrastructure
for collecting corporate blog/news articles from 70+ companies across
the AI value chain.
"""

from .structure_validator import StructureValidator
from .types import (
    ArticleMetadata,
    CompanyConfig,
    CompanyScrapeResult,
    InvestmentContext,
    PdfMetadata,
    ScrapedArticle,
    StructureReport,
)

__all__ = [
    # Data types
    "ArticleMetadata",
    "CompanyConfig",
    "CompanyScrapeResult",
    "InvestmentContext",
    "PdfMetadata",
    "ScrapedArticle",
    "StructureReport",
    # Services
    "StructureValidator",
    # Exceptions are accessed via company_scrapers.types or directly
]

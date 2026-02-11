"""Company scrapers package for AI investment value chain tracking.

Provides data types, exception classes, and scraping infrastructure
for collecting corporate blog/news articles from 70+ companies across
the AI value chain.
"""

from .base import BaseCompanyScraper
from .engine import CompanyScraperEngine
from .pdf_handler import PdfHandler, find_pdf_links, is_pdf_url
from .registry import CompanyScraperRegistry
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
    "ArticleMetadata",
    "BaseCompanyScraper",
    "CompanyConfig",
    "CompanyScrapeResult",
    "CompanyScraperEngine",
    "CompanyScraperRegistry",
    "InvestmentContext",
    "PdfHandler",
    "PdfMetadata",
    "ScrapedArticle",
    "StructureReport",
    "StructureValidator",
    "find_pdf_links",
    "is_pdf_url",
]

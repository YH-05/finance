"""Industry report scraping and competitive analysis module.

This package provides tools for scraping industry reports from consulting
firms, investment banks, and government statistical APIs, as well as
competitive advantage analysis based on the dogma.md evaluation framework.

Modules
-------
types : Pydantic data models (IndustryReport, ScrapingResult, PeerGroup, etc.).
config : Preset configuration loader for industry-research-presets.json.
scrapers.base : BaseScraper abstract base class with 2-layer fallback.
scrapers.consulting : Consulting firm scrapers (McKinsey, BCG, Deloitte, PwC).
scrapers.investment_bank : Investment bank scrapers (Goldman Sachs, Morgan Stanley, JP Morgan).
api_clients.bls : BLS API v2.0 client for employment/wage/productivity data.
api_clients.census : Census Bureau API client for international trade data.
downloaders.pdf_downloader : PDF download with size limiting and deduplication.
downloaders.report_parser : PDF/HTML text extraction and metadata extraction.
peer_groups : Peer group definition and retrieval (preset + dynamic via yfinance).
competitive_analysis : Competitive advantage analysis (dogma.md 12 rules, moat scoring, Porter's 5 Forces).
collector : Integrated CLI collector for all industry report sources.
scheduler : APScheduler weekly execution for automated collection.

Public API
----------
IndustryReport
    A single industry report record.
ScrapingResult
    Container for scraping operation results.
PeerGroup
    Peer group definition for competitive analysis.
ScrapingConfig
    Configuration for industry report scraping behaviour.
RetryConfig
    Configuration for retry behaviour with exponential backoff.
SourceTier
    Classification tier for industry report sources.
BaseScraper
    Abstract base class for industry report scrapers.
BLSClient
    Async client for the BLS Public Data API v2.0.
CensusClient
    Async client for the Census Bureau International Trade API.
PDFDownloader
    Async PDF downloader with size limits and hash-based deduplication.
ReportParser
    Parser for extracting text and metadata from PDF and HTML documents.
CompetitiveAnalyzer
    Orchestrator for competitive advantage assessment.
IndustryCollector
    CLI orchestrator for collecting industry reports from all sources.
IndustryScheduler
    APScheduler-based weekly scheduler for automated collection.

Configuration
-------------
IndustryPresetsConfig
    Top-level configuration for industry research presets.
IndustryPreset
    Per-sector preset configuration.
SourceConfig
    Configuration for a single data source.
load_presets
    Load and validate industry research presets from a JSON file.

Examples
--------
>>> from market.industry import IndustryReport, SourceTier
>>> from market.industry import load_presets
>>> config = load_presets()
>>> config.sector_names
['Technology', 'Healthcare', 'Financials', 'Consumer_Discretionary', 'Energy']

See Also
--------
market.etfcom : ETF.com scraping module (reference implementation for scraping patterns).
"""

from market.industry.api_clients.bls import BLSClient
from market.industry.api_clients.census import CensusClient
from market.industry.collector import (
    CollectionResult,
    CollectionStats,
    IndustryCollector,
)
from market.industry.competitive_analysis import (
    CompetitiveAnalyzer,
    evaluate_advantage_claim,
    evaluate_porter_forces,
    score_moat,
)
from market.industry.config import (
    IndustryPreset,
    IndustryPresetsConfig,
    SourceConfig,
    load_presets,
)
from market.industry.downloaders.pdf_downloader import PDFDownloader
from market.industry.downloaders.report_parser import ReportParser
from market.industry.peer_groups import (
    get_dynamic_peer_group,
    get_peer_group,
    get_preset_peer_group,
)
from market.industry.scheduler import IndustryScheduler
from market.industry.scrapers.base import BaseScraper
from market.industry.scrapers.consulting import (
    BCGScraper,
    ConsultingScraper,
    DeloitteScraper,
    McKinseyScraper,
    PwCScraper,
)
from market.industry.scrapers.investment_bank import (
    GoldmanSachsScraper,
    InvestmentBankScraper,
    JPMorganScraper,
    MorganStanleyScraper,
)
from market.industry.types import (
    AdvantageAssessment,
    AdvantageClaim,
    ConfidenceLevel,
    DogmaRuleResult,
    DownloadResult,
    IndustryReport,
    MoatScore,
    MoatStrength,
    MoatType,
    ParsedContent,
    PeerGroup,
    PorterForce,
    PorterForcesAssessment,
    PorterForceStrength,
    ReportMetadata,
    RetryConfig,
    ScrapingConfig,
    ScrapingResult,
    SourceTier,
)

__all__ = [
    "AdvantageAssessment",
    "AdvantageClaim",
    "BCGScraper",
    "BLSClient",
    "BaseScraper",
    "CensusClient",
    "CollectionResult",
    "CollectionStats",
    "CompetitiveAnalyzer",
    "ConfidenceLevel",
    "ConsultingScraper",
    "DeloitteScraper",
    "DogmaRuleResult",
    "DownloadResult",
    "GoldmanSachsScraper",
    "IndustryCollector",
    "IndustryPreset",
    "IndustryPresetsConfig",
    "IndustryReport",
    "IndustryScheduler",
    "InvestmentBankScraper",
    "JPMorganScraper",
    "McKinseyScraper",
    "MoatScore",
    "MoatStrength",
    "MoatType",
    "MorganStanleyScraper",
    "PDFDownloader",
    "ParsedContent",
    "PeerGroup",
    "PorterForce",
    "PorterForceStrength",
    "PorterForcesAssessment",
    "PwCScraper",
    "ReportMetadata",
    "ReportParser",
    "RetryConfig",
    "ScrapingConfig",
    "ScrapingResult",
    "SourceConfig",
    "SourceTier",
    "evaluate_advantage_claim",
    "evaluate_porter_forces",
    "get_dynamic_peer_group",
    "get_peer_group",
    "get_preset_peer_group",
    "load_presets",
    "score_moat",
]

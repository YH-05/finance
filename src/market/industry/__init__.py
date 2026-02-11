"""Industry report scraping module for market data retrieval.

This package provides tools for scraping industry reports from consulting
firms, investment banks, and government statistical APIs.

Modules
-------
types : Pydantic data models (IndustryReport, ScrapingResult, PeerGroup, etc.).
config : Preset configuration loader for industry-research-presets.json.
scrapers.base : BaseScraper abstract base class with 2-layer fallback.
scrapers.consulting : Consulting firm scrapers (McKinsey, BCG, Deloitte, PwC).

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

from market.industry.config import (
    IndustryPreset,
    IndustryPresetsConfig,
    SourceConfig,
    load_presets,
)
from market.industry.scrapers.base import BaseScraper
from market.industry.scrapers.consulting import (
    BCGScraper,
    ConsultingScraper,
    DeloitteScraper,
    McKinseyScraper,
    PwCScraper,
)
from market.industry.types import (
    IndustryReport,
    PeerGroup,
    RetryConfig,
    ScrapingConfig,
    ScrapingResult,
    SourceTier,
)

__all__ = [
    "BCGScraper",
    "BaseScraper",
    "ConsultingScraper",
    "DeloitteScraper",
    "IndustryPreset",
    "IndustryPresetsConfig",
    "IndustryReport",
    "McKinseyScraper",
    "PeerGroup",
    "PwCScraper",
    "RetryConfig",
    "ScrapingConfig",
    "ScrapingResult",
    "SourceConfig",
    "SourceTier",
    "load_presets",
]

"""Sector analysis module.

This module provides functions for analyzing sector performance,
including ETF returns, top/bottom sector rankings, and contributor stocks.
"""

from analyze.sector.sector import (
    SECTOR_ETF_MAP,
    SECTOR_KEYS,
    SECTOR_NAMES,
    SectorAnalysisResult,
    SectorContributor,
    SectorInfo,
    _build_contributors,
    _build_sector_info_list,
    analyze_sector_performance,
    fetch_sector_etf_returns,
    fetch_top_companies,
    get_top_bottom_sectors,
)

__all__ = [
    "SECTOR_ETF_MAP",
    "SECTOR_KEYS",
    "SECTOR_NAMES",
    "SectorAnalysisResult",
    "SectorContributor",
    "SectorInfo",
    "_build_contributors",
    "_build_sector_info_list",
    "analyze_sector_performance",
    "fetch_sector_etf_returns",
    "fetch_top_companies",
    "get_top_bottom_sectors",
]

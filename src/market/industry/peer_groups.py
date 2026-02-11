"""Peer group definition and retrieval for competitive analysis.

This module provides functions for obtaining peer groups either from
preset configurations or dynamically via yfinance industry/sector data.

Functions
---------
get_preset_peer_group
    Retrieve a peer group from the preset configuration file.
get_dynamic_peer_group
    Generate a peer group dynamically using yfinance Ticker info.
get_peer_group
    Combined lookup: preset first, then dynamic fallback.

See Also
--------
market.industry.config : Preset configuration loader.
market.industry.types : PeerGroup data model.
market.industry.competitive_analysis : Competitive advantage analysis.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import yfinance as yf

from market.industry.types import PeerGroup
from utils_core.logging import get_logger

if TYPE_CHECKING:
    from market.industry.config import IndustryPresetsConfig

logger = get_logger(__name__)


def get_preset_peer_group(
    sector: str,
    config: IndustryPresetsConfig,
    *,
    sub_sector: str | None = None,
) -> PeerGroup | None:
    """Retrieve a peer group from preset configuration.

    Looks up the sector in the presets and returns a ``PeerGroup`` with
    the configured ticker symbols. Optionally filters by sub-sector.

    Parameters
    ----------
    sector : str
        GICS-style sector name (e.g. ``"Technology"``).
    config : IndustryPresetsConfig
        Loaded industry presets configuration.
    sub_sector : str | None
        Optional sub-sector to filter by. If provided and not found
        in the preset's sub-sectors list, returns ``None``.
        Defaults to ``None``.

    Returns
    -------
    PeerGroup | None
        The peer group if found, or ``None`` if the sector (or
        sub-sector) does not exist in presets.

    Examples
    --------
    >>> from market.industry.config import load_presets
    >>> config = load_presets()
    >>> group = get_preset_peer_group("Technology", config)
    >>> group.companies
    ['NVDA', 'AMD', 'INTC', 'TSM', 'AVGO', 'MSFT', 'ORCL', 'CRM']
    """
    logger.debug(
        "Looking up preset peer group",
        sector=sector,
        sub_sector=sub_sector,
    )

    preset = config.get_sector(sector)
    if preset is None:
        logger.debug("Sector not found in presets", sector=sector)
        return None

    if sub_sector is not None and sub_sector not in preset.sub_sectors:
        logger.debug(
            "Sub-sector not found in preset",
            sector=sector,
            sub_sector=sub_sector,
            available_sub_sectors=preset.sub_sectors,
        )
        return None

    resolved_sub_sector = sub_sector or (
        preset.sub_sectors[0] if preset.sub_sectors else sector
    )

    peer_group = PeerGroup(
        sector=sector,
        sub_sector=resolved_sub_sector,
        companies=preset.peer_tickers,
        description=f"Preset peer group for {sector}/{resolved_sub_sector}",
    )

    logger.info(
        "Preset peer group found",
        sector=sector,
        sub_sector=resolved_sub_sector,
        company_count=len(peer_group.companies),
    )

    return peer_group


def get_dynamic_peer_group(ticker: str) -> PeerGroup | None:
    """Generate a peer group dynamically using yfinance Ticker info.

    Fetches the ``sector`` and ``industry`` fields from yfinance's
    ``Ticker.info`` dictionary to classify the company. The resulting
    peer group contains only the queried ticker, as yfinance does not
    provide a list of peer companies.

    Parameters
    ----------
    ticker : str
        Stock ticker symbol (e.g. ``"NVDA"``).

    Returns
    -------
    PeerGroup | None
        A peer group with sector/industry information, or ``None``
        if the ticker info could not be retrieved.

    Examples
    --------
    >>> group = get_dynamic_peer_group("NVDA")  # doctest: +SKIP
    >>> group.sector
    'Technology'
    >>> group.sub_sector
    'Semiconductors'
    """
    logger.debug("Generating dynamic peer group", ticker=ticker)

    try:
        yf_ticker = yf.Ticker(ticker)
        info: dict = yf_ticker.info
    except Exception:
        logger.warning(
            "Failed to fetch yfinance Ticker info",
            ticker=ticker,
            exc_info=True,
        )
        return None

    sector = info.get("sector")
    industry = info.get("industry")

    if not sector:
        logger.debug(
            "No sector information available from yfinance",
            ticker=ticker,
        )
        return None

    sub_sector = industry or sector

    peer_group = PeerGroup(
        sector=sector,
        sub_sector=sub_sector,
        companies=[ticker],
        description=f"Dynamic peer group for {ticker} ({sector}/{sub_sector})",
    )

    logger.info(
        "Dynamic peer group generated",
        ticker=ticker,
        sector=sector,
        sub_sector=sub_sector,
    )

    return peer_group


def get_peer_group(
    ticker: str,
    config: IndustryPresetsConfig,
) -> PeerGroup | None:
    """Retrieve a peer group using preset-first, dynamic-fallback strategy.

    First attempts to determine the ticker's sector via yfinance, then
    looks up the preset peer group. If no preset exists for the sector,
    falls back to the dynamically generated peer group.

    Parameters
    ----------
    ticker : str
        Stock ticker symbol (e.g. ``"NVDA"``).
    config : IndustryPresetsConfig
        Loaded industry presets configuration.

    Returns
    -------
    PeerGroup | None
        The peer group (from preset or dynamic), or ``None`` if both
        methods fail.

    Examples
    --------
    >>> from market.industry.config import load_presets
    >>> config = load_presets()
    >>> group = get_peer_group("NVDA", config)  # doctest: +SKIP
    >>> group.sector
    'Technology'
    """
    logger.debug("Looking up peer group with fallback", ticker=ticker)

    # Step 1: Get sector/industry from yfinance
    dynamic_group = get_dynamic_peer_group(ticker)

    if dynamic_group is None:
        logger.debug(
            "Dynamic peer group generation failed, cannot determine sector",
            ticker=ticker,
        )
        return None

    # Step 2: Try preset lookup using the dynamically determined sector
    preset_group = get_preset_peer_group(
        dynamic_group.sector,
        config,
    )

    if preset_group is not None:
        logger.info(
            "Using preset peer group",
            ticker=ticker,
            sector=preset_group.sector,
            company_count=len(preset_group.companies),
        )
        return preset_group

    # Step 3: Fall back to dynamic group
    logger.info(
        "Using dynamic peer group (no preset found)",
        ticker=ticker,
        sector=dynamic_group.sector,
    )
    return dynamic_group


__all__ = [
    "get_dynamic_peer_group",
    "get_peer_group",
    "get_preset_peer_group",
]

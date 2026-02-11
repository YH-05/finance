"""Type definitions for the analyze package.

This module provides shared type definitions used across the analyze package:
- TickerInfo: Ticker metadata (name, sector, industry, asset class)
- AssetClass: Asset class literal type

Examples
--------
>>> from analyze.types import TickerInfo
>>> info = TickerInfo(ticker="AAPL", name="Apple Inc.", sector="Technology")
>>> info.ticker
'AAPL'
>>> info.asset_class
'equity'
"""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

# =============================================================================
# Type Aliases
# =============================================================================

type AssetClass = Literal[
    "equity", "etf", "index", "mutual_fund", "currency", "futures", "bond", "other"
]

# Mapping from yfinance quoteType to AssetClass
QUOTE_TYPE_TO_ASSET_CLASS: dict[str, AssetClass] = {
    "EQUITY": "equity",
    "ETF": "etf",
    "INDEX": "index",
    "MUTUALFUND": "mutual_fund",
    "CURRENCY": "currency",
    "FUTURE": "futures",
    "BOND": "bond",
}


# =============================================================================
# TickerInfo Model
# =============================================================================


class TickerInfo(BaseModel):
    """Ticker metadata information.

    Stores basic metadata about a financial instrument including
    its name, sector, industry, and asset class.

    Parameters
    ----------
    ticker : str
        Ticker symbol (e.g., "AAPL", "VOO", "^GSPC").
    name : str
        Display name of the instrument (e.g., "Apple Inc.").
    sector : str | None, default=None
        Sector classification (e.g., "Technology"). None for non-equity assets.
    industry : str | None, default=None
        Industry classification (e.g., "Consumer Electronics"). None for non-equity assets.
    asset_class : AssetClass, default="equity"
        Asset class of the instrument.

    Examples
    --------
    >>> info = TickerInfo(
    ...     ticker="AAPL",
    ...     name="Apple Inc.",
    ...     sector="Technology",
    ...     industry="Consumer Electronics",
    ... )
    >>> info.ticker
    'AAPL'
    >>> info.asset_class
    'equity'

    >>> etf = TickerInfo(ticker="VOO", name="Vanguard S&P 500 ETF", asset_class="etf")
    >>> etf.asset_class
    'etf'
    """

    model_config = ConfigDict(
        frozen=True,
        str_strip_whitespace=True,
        validate_default=True,
    )

    ticker: Annotated[
        str,
        Field(
            ...,
            min_length=1,
            description="Ticker symbol (e.g., 'AAPL', 'VOO', '^GSPC')",
        ),
    ]

    name: Annotated[
        str,
        Field(
            ...,
            min_length=1,
            description="Display name of the instrument",
        ),
    ]

    sector: Annotated[
        str | None,
        Field(
            default=None,
            description="Sector classification (e.g., 'Technology')",
        ),
    ] = None

    industry: Annotated[
        str | None,
        Field(
            default=None,
            description="Industry classification (e.g., 'Consumer Electronics')",
        ),
    ] = None

    asset_class: Annotated[
        AssetClass,
        Field(
            default="equity",
            description="Asset class of the instrument",
        ),
    ] = "equity"

    @field_validator("ticker")
    @classmethod
    def validate_ticker_not_whitespace(cls, v: str) -> str:
        """Validate that ticker is not whitespace only."""
        if not v.strip():
            raise ValueError("ticker must not be empty or whitespace only")
        return v

    @field_validator("name")
    @classmethod
    def validate_name_not_whitespace(cls, v: str) -> str:
        """Validate that name is not whitespace only."""
        if not v.strip():
            raise ValueError("name must not be empty or whitespace only")
        return v


# =============================================================================
# Helper Functions
# =============================================================================


def map_quote_type_to_asset_class(quote_type: str | None) -> AssetClass:
    """Map yfinance quoteType string to AssetClass.

    Parameters
    ----------
    quote_type : str | None
        The quoteType value from yfinance Ticker.info.

    Returns
    -------
    AssetClass
        The corresponding asset class. Defaults to "equity" for unknown types.

    Examples
    --------
    >>> map_quote_type_to_asset_class("EQUITY")
    'equity'
    >>> map_quote_type_to_asset_class("ETF")
    'etf'
    >>> map_quote_type_to_asset_class("UNKNOWN")
    'equity'
    >>> map_quote_type_to_asset_class(None)
    'equity'
    """
    if quote_type is None:
        return "equity"
    return QUOTE_TYPE_TO_ASSET_CLASS.get(quote_type.upper(), "equity")


# =============================================================================
# __all__ Export
# =============================================================================

__all__ = [
    "QUOTE_TYPE_TO_ASSET_CLASS",
    "AssetClass",
    "TickerInfo",
    "map_quote_type_to_asset_class",
]

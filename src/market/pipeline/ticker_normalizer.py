"""Ticker symbol normalisation for multiple data sources.

This module provides a single pure function, ``normalize_ticker``, that
converts a NASDAQ-format ticker symbol to the format expected by a given
downstream data source.

Normalisation rules
-------------------
- ``"nasdaq"``       -- no change (identity transform)
- ``"alphavantage"`` -- split on ``"."`` and take the first component
  (e.g. ``"GEF.B"`` → ``"GEF"``)
- ``"sec_edgar"``    -- no change (identity transform)
- ``"yfinance"``     -- replace ``"."`` with ``"-"``
  (e.g. ``"GEF.B"`` → ``"GEF-B"``)

Notes
-----
This function intentionally has no dependencies (no I/O, no imports beyond
``typing``). It is safe to call from any thread and in any context.

See Also
--------
market.pipeline.errors : ``TickerNormalizationError`` for invalid targets.
"""

from typing import Literal

from market.pipeline.errors import TickerNormalizationError
from utils_core.logging import get_logger

logger = get_logger(__name__)

# Type alias for supported normalisation targets
NormalizationTarget = Literal["nasdaq", "alphavantage", "sec_edgar", "yfinance"]


def normalize_ticker(
    nasdaq_symbol: str,
    target: NormalizationTarget,
) -> str:
    """Normalise a NASDAQ ticker symbol for a specific data source.

    Parameters
    ----------
    nasdaq_symbol : str
        Ticker symbol in NASDAQ format (e.g. ``"GEF.B"``, ``"BRK.B"``).
    target : Literal['nasdaq', 'alphavantage', 'sec_edgar', 'yfinance']
        Target data source format.

    Returns
    -------
    str
        Normalised ticker symbol for the specified target.

    Raises
    ------
    TickerNormalizationError
        When ``target`` is not one of the supported values.

    Examples
    --------
    >>> normalize_ticker("GEF.B", "alphavantage")
    'GEF'
    >>> normalize_ticker("GEF.B", "yfinance")
    'GEF-B'
    >>> normalize_ticker("AAPL", "nasdaq")
    'AAPL'
    >>> normalize_ticker("AAPL", "sec_edgar")
    'AAPL'
    """
    logger.debug(
        "Normalising ticker symbol",
        nasdaq_symbol=nasdaq_symbol,
        target=target,
    )

    if target == "alphavantage":
        return nasdaq_symbol.split(".")[0]

    if target == "yfinance":
        return nasdaq_symbol.replace(".", "-")

    if target in ("nasdaq", "sec_edgar"):
        return nasdaq_symbol

    raise TickerNormalizationError(
        f"Unknown normalisation target: {target!r}",
        context={"symbol": nasdaq_symbol, "target": target},
    )


__all__ = [
    "NormalizationTarget",
    "normalize_ticker",
]

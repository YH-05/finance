"""Bloomberg ticker to yfinance ticker conversion module.

Converts Bloomberg format tickers (e.g. ``AAPL UW Equity``) to yfinance
format (e.g. ``AAPL``) using exchange-code suffix mapping and an optional
override dictionary.

Exchange code mapping covers the most common markets:
- US equities: UW (NASDAQ), UN (NYSE), UA, UR, UF → no suffix
- UK: LN → .L
- France: FP → .PA
- Germany: GY → .DE
- Japan: JT → .T
- Canada: CN → .TO, CT → .TO
- Switzerland: SW → .SW
- Netherlands: NA → .AS
- Australia: AT → .AX
- Hong Kong: HK → .HK
- Italy: IM → .MI
- Spain: SM → .MC
- Sweden: SS → .ST
- Denmark: DC → .CO
- Norway: NO → .OL
- Finland: FH → .HE
- Belgium: BB → .BR
- Singapore: SP → .SI
- South Korea: KS → .KS
"""

from __future__ import annotations

from utils_core.logging import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Exchange code → yfinance suffix mapping
# ---------------------------------------------------------------------------
_EXCHANGE_SUFFIX_MAP: dict[str, str] = {
    # United States (no suffix)
    "UW": "",  # NASDAQ
    "UN": "",  # NYSE
    "UA": "",  # NYSE American
    "UR": "",  # NYSE Arca
    "UF": "",  # OTC / Pink Sheets
    # Europe
    "LN": ".L",  # London Stock Exchange
    "FP": ".PA",  # Euronext Paris
    "GY": ".DE",  # XETRA (Germany)
    "NA": ".AS",  # Euronext Amsterdam
    "SW": ".SW",  # SIX Swiss Exchange
    "IM": ".MI",  # Borsa Italiana (Milan)
    "SM": ".MC",  # Bolsa de Madrid
    "SS": ".ST",  # Nasdaq Stockholm
    "DC": ".CO",  # Nasdaq Copenhagen
    "NO": ".OL",  # Oslo Bors
    "FH": ".HE",  # Nasdaq Helsinki
    "BB": ".BR",  # Euronext Brussels
    # Americas
    "CN": ".TO",  # Toronto Stock Exchange
    "CT": ".TO",  # Toronto (alternative)
    # Asia Pacific
    "JT": ".T",  # Tokyo Stock Exchange
    "HK": ".HK",  # Hong Kong Stock Exchange
    "AT": ".AX",  # Australian Securities Exchange
    "SP": ".SI",  # Singapore Exchange
    "KS": ".KS",  # Korea Stock Exchange
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
class TickerConverter:
    """Convert Bloomberg format tickers to yfinance format.

    Parses Bloomberg tickers in the form ``TICKER EXCHANGE Equity``
    and maps the exchange code to the appropriate yfinance suffix.

    Parameters
    ----------
    overrides : dict[str, str] | None, optional
        Custom ticker overrides that take precedence over automatic
        conversion.  Keys are Bloomberg tickers (e.g. ``"BRK/B UN Equity"``),
        values are yfinance tickers (e.g. ``"BRK-B"``).

    Examples
    --------
    >>> converter = TickerConverter()
    >>> converter.convert("AAPL UW Equity")
    'AAPL'
    >>> converter.convert("7203 JT Equity")
    '7203.T'

    >>> converter = TickerConverter(overrides={"BRK/B UN Equity": "BRK-B"})
    >>> converter.convert("BRK/B UN Equity")
    'BRK-B'
    """

    def __init__(
        self,
        overrides: dict[str, str] | None = None,
    ) -> None:
        self._overrides: dict[str, str] = overrides or {}
        logger.debug(
            "TickerConverter initialized",
            override_count=len(self._overrides),
        )

    def convert(self, bloomberg_ticker: str) -> str:
        """Convert a single Bloomberg ticker to yfinance format.

        Parameters
        ----------
        bloomberg_ticker : str
            Bloomberg format ticker, e.g. ``"AAPL UW Equity"``.

        Returns
        -------
        str
            yfinance format ticker, e.g. ``"AAPL"``.  Returns the
            original input unchanged if conversion fails, with a warning
            logged.

        Notes
        -----
        Returns the input string unchanged when:
        - The input is empty or whitespace-only
        - The format does not match ``TICKER EXCHANGE Equity``
        - The exchange code is unknown
        """
        # Empty / whitespace-only input
        stripped = bloomberg_ticker.strip()
        if not stripped:
            logger.warning(
                "Empty Bloomberg ticker received",
                bloomberg_ticker=repr(bloomberg_ticker),
            )
            return bloomberg_ticker

        # Override dictionary takes precedence
        if stripped in self._overrides:
            result = self._overrides[stripped]
            logger.debug(
                "Override applied",
                bloomberg_ticker=stripped,
                yfinance_ticker=result,
            )
            return result

        # Parse format: TICKER EXCHANGE [Equity|...]
        parts = stripped.split()
        if len(parts) < 2:
            logger.warning(
                "Unrecognised Bloomberg ticker format",
                bloomberg_ticker=stripped,
                expected="TICKER EXCHANGE [Equity]",
            )
            return stripped

        raw_ticker = parts[0]
        exchange_code = parts[1].upper()

        # Look up exchange suffix
        if exchange_code not in _EXCHANGE_SUFFIX_MAP:
            logger.warning(
                "Unknown exchange code",
                bloomberg_ticker=stripped,
                exchange_code=exchange_code,
            )
            return stripped

        suffix = _EXCHANGE_SUFFIX_MAP[exchange_code]
        result = f"{raw_ticker}{suffix}"

        logger.debug(
            "Ticker converted",
            bloomberg_ticker=stripped,
            exchange_code=exchange_code,
            yfinance_ticker=result,
        )
        return result

    def convert_batch(
        self,
        tickers: list[str],
    ) -> dict[str, str]:
        """Convert a list of Bloomberg tickers to yfinance format.

        Parameters
        ----------
        tickers : list[str]
            List of Bloomberg format tickers.

        Returns
        -------
        dict[str, str]
            Mapping from Bloomberg ticker to yfinance ticker.
            Tickers that fail conversion are included with their
            original value (warning logged).

        Examples
        --------
        >>> converter = TickerConverter()
        >>> converter.convert_batch(["AAPL UW Equity", "7203 JT Equity"])
        {'AAPL UW Equity': 'AAPL', '7203 JT Equity': '7203.T'}
        """
        result: dict[str, str] = {}
        for bloomberg_ticker in tickers:
            result[bloomberg_ticker] = self.convert(bloomberg_ticker)

        logger.info(
            "Batch conversion completed",
            total=len(tickers),
        )
        return result


__all__ = ["TickerConverter"]

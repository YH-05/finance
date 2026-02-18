"""Transcript loader with Pydantic validation and PoiT filtering.

Reads parsed transcript JSON files (produced by TranscriptParser),
validates them as Transcript Pydantic models, and applies Point-in-Time
(cutoff_date) filtering to prevent look-ahead bias.

Features
--------
- Single transcript loading with Pydantic validation
- Batch loading across multiple tickers
- Automatic PoiT filtering via pit.filter_by_pit()
- Graceful handling of missing files and validation errors

Output Directory Structure
--------------------------
Reads from::

    {base_dir}/{TICKER}/{YYYYMM}_earnings_call.json
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

from pydantic import ValidationError

from dev.ca_strategy.pit import CUTOFF_DATE, filter_by_pit
from dev.ca_strategy.types import Transcript
from utils_core.logging import get_logger

if TYPE_CHECKING:
    from datetime import date

logger = get_logger(__name__)


class TranscriptLoader:
    """Load and validate parsed transcript JSON files.

    Parameters
    ----------
    base_dir : Path | str
        Root directory containing per-ticker transcript subdirectories.
        Expected structure: ``{base_dir}/{TICKER}/{YYYYMM}_earnings_call.json``.
    cutoff_date : date, optional
        Point-in-Time cutoff date for filtering.  Transcripts with
        event_date after this date are excluded.  Defaults to
        ``pit.CUTOFF_DATE`` (2015-09-30).

    Examples
    --------
    >>> loader = TranscriptLoader(
    ...     base_dir=Path("research/ca_strategy_poc/transcripts"),
    ...     cutoff_date=date(2015, 9, 30),
    ... )
    >>> transcript = loader.load_single("AAPL", "201501")
    >>> batch = loader.load_batch(["AAPL", "MSFT", "GOOGL"])
    """

    def __init__(
        self,
        base_dir: Path | str,
        cutoff_date: date = CUTOFF_DATE,
    ) -> None:
        self._base_dir = Path(base_dir)
        self._cutoff_date = cutoff_date
        logger.debug(
            "TranscriptLoader initialized",
            base_dir=str(self._base_dir),
            cutoff_date=cutoff_date.isoformat(),
        )

    def load_single(
        self,
        ticker: str,
        year_month: str,
    ) -> Transcript | None:
        """Load a single transcript file by ticker and year-month.

        Parameters
        ----------
        ticker : str
            Ticker symbol (e.g. "AAPL").
        year_month : str
            Year-month string (e.g. "201501").

        Returns
        -------
        Transcript | None
            Validated Transcript if the file exists, passes validation,
            and its event_date is on or before the cutoff_date.
            None otherwise.
        """
        filepath = self._build_filepath(ticker, year_month)

        if not filepath.exists():
            logger.warning(
                "Transcript file not found",
                ticker=ticker,
                year_month=year_month,
                path=str(filepath),
            )
            return None

        data = self._read_json(filepath)
        if data is None:
            return None

        transcript = self._validate_transcript(data, filepath)
        if transcript is None:
            return None

        # Apply PoiT filter
        filtered = filter_by_pit([transcript], self._cutoff_date)
        if not filtered:
            logger.debug(
                "Transcript excluded by PoiT filter",
                ticker=ticker,
                year_month=year_month,
                event_date=transcript.metadata.event_date.isoformat(),
                cutoff_date=self._cutoff_date.isoformat(),
            )
            return None

        return filtered[0]

    def load_batch(
        self,
        tickers: list[str],
    ) -> dict[str, list[Transcript]]:
        """Load all transcripts for multiple tickers.

        Scans each ticker's subdirectory for ``*_earnings_call.json`` files,
        validates them, and applies PoiT filtering.

        Parameters
        ----------
        tickers : list[str]
            List of ticker symbols to load.

        Returns
        -------
        dict[str, list[Transcript]]
            Mapping of ticker to list of validated, PoiT-filtered transcripts.
            Tickers with no valid transcripts map to empty lists.
        """
        if not tickers:
            return {}

        result: dict[str, list[Transcript]] = {}

        for ticker in tickers:
            transcripts = self._load_ticker_transcripts(ticker)
            filtered = filter_by_pit(transcripts, self._cutoff_date)
            result[ticker] = filtered
            logger.debug(
                "Batch load completed for ticker",
                ticker=ticker,
                loaded=len(transcripts),
                after_pit_filter=len(filtered),
            )

        logger.info(
            "Batch loading completed",
            ticker_count=len(tickers),
            total_transcripts=sum(len(v) for v in result.values()),
        )

        return result

    def _build_filepath(self, ticker: str, year_month: str) -> Path:
        """Build the expected file path for a transcript.

        Parameters
        ----------
        ticker : str
            Ticker symbol.
        year_month : str
            Year-month string (e.g. "201501").

        Returns
        -------
        Path
            Expected transcript file path.
        """
        return self._base_dir / ticker / f"{year_month}_earnings_call.json"

    def _load_ticker_transcripts(self, ticker: str) -> list[Transcript]:
        """Load all transcript files for a single ticker.

        Parameters
        ----------
        ticker : str
            Ticker symbol.

        Returns
        -------
        list[Transcript]
            List of validated transcripts (before PoiT filtering).
        """
        ticker_dir = self._base_dir / ticker
        if not ticker_dir.exists():
            logger.debug("Ticker directory not found", ticker=ticker)
            return []

        transcripts: list[Transcript] = []
        for filepath in sorted(ticker_dir.glob("*_earnings_call.json")):
            data = self._read_json(filepath)
            if data is None:
                continue

            transcript = self._validate_transcript(data, filepath)
            if transcript is not None:
                transcripts.append(transcript)

        logger.debug(
            "Loaded transcripts for ticker",
            ticker=ticker,
            count=len(transcripts),
        )
        return transcripts

    @staticmethod
    def _read_json(filepath: Path) -> dict | None:
        """Read and parse a JSON file.

        Parameters
        ----------
        filepath : Path
            Path to the JSON file.

        Returns
        -------
        dict | None
            Parsed JSON data, or None if reading/parsing fails.
        """
        try:
            text = filepath.read_text(encoding="utf-8")
            return json.loads(text)
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning(
                "Failed to read JSON file",
                path=str(filepath),
                error=str(exc),
            )
            return None

    @staticmethod
    def _validate_transcript(
        data: dict,
        filepath: Path,
    ) -> Transcript | None:
        """Validate raw dict data as a Transcript Pydantic model.

        Parameters
        ----------
        data : dict
            Raw transcript data from JSON file.
        filepath : Path
            File path for error logging.

        Returns
        -------
        Transcript | None
            Validated Transcript, or None if validation fails.
        """
        try:
            return Transcript.model_validate(data)
        except ValidationError as exc:
            logger.warning(
                "Transcript validation failed",
                path=str(filepath),
                error=str(exc),
            )
            return None


__all__ = [
    "TranscriptLoader",
]

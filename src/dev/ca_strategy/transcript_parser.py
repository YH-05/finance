"""S&P Capital IQ transcript JSON parser.

Parses monthly transcript exports (list_transcript_YYYY-MM.json) and converts
them into per-ticker structured JSON files suitable for the CA Strategy pipeline.

Features
--------
- Trailing comma JSON fix for malformed exports
- Tag-based section splitting (presentation / question / answer)
- Bloomberg Ticker to simple ticker conversion (space-split first element)
- Non-standard ticker mapping via ticker_mapping.json (digit-starting tickers)
- TRANSCRIPTID deduplication with Audited Copy priority
- 32767-character truncation detection and metadata recording

Output
------
Structured JSON files at:
    ``{output_dir}/{TICKER}/{YYYYMM}_earnings_call.json``
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from utils_core.logging import get_logger

if TYPE_CHECKING:
    from pathlib import Path

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
TRUNCATION_THRESHOLD = 32767
"""Excel cell character limit; text fields at or above this are truncated."""

TAG_PATTERN = re.compile(
    r"【(プレゼン|質問|回答):\s*(.+?)\s*\(([^)]+)\)】\n(.*?)(?=(?:【(?:プレゼン|質問|回答):)|$)",
    re.DOTALL,
)
"""Regex pattern for parsing Japanese-tagged transcript sections.

Groups:
    1 - Section type tag (プレゼン/質問/回答)
    2 - Speaker name
    3 - Role (Executives/Analysts)
    4 - Content text
"""

SECTION_TYPE_MAP: dict[str, str] = {
    "プレゼン": "prepared_remarks",
    "質問": "question",
    "回答": "answer",
}
"""Mapping from Japanese section tags to English section type identifiers."""

MONTH_FILE_PATTERN = re.compile(r"list_transcript_(\d{4})-(\d{2})\.json$")
"""Pattern for matching monthly transcript filenames."""


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class ParseResult:
    """Result of parsing all monthly transcript files.

    Parameters
    ----------
    total_count : int
        Total number of transcript records encountered.
    success_count : int
        Number of successfully parsed and written transcripts.
    error_count : int
        Number of records that failed to parse.
    errors : list[str]
        Error messages for failed records.
    """

    total_count: int = 0
    success_count: int = 0
    error_count: int = 0
    errors: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# TranscriptParser
# ---------------------------------------------------------------------------
class TranscriptParser:
    """Parse S&P Capital IQ transcript JSONs into per-ticker structured files.

    Parameters
    ----------
    source_dir : Path
        Directory containing ``list_transcript_YYYY-MM.json`` files.
    output_dir : Path
        Directory for output files (``{TICKER}/{YYYYMM}_earnings_call.json``).
    ticker_mapping_path : Path
        Path to ``ticker_mapping.json`` for non-standard ticker resolution.

    Examples
    --------
    >>> parser = TranscriptParser(
    ...     source_dir=Path("data/Transcript"),
    ...     output_dir=Path("research/ca_strategy_poc/transcripts"),
    ...     ticker_mapping_path=Path("research/ca_strategy_poc/config/ticker_mapping.json"),
    ... )
    >>> result = parser.parse_all_months()
    >>> result.success_count
    42
    """

    def __init__(
        self,
        source_dir: Path,
        output_dir: Path,
        ticker_mapping_path: Path,
    ) -> None:
        self._source_dir = source_dir
        self._output_dir = output_dir
        self._ticker_mapping = self._load_ticker_mapping(ticker_mapping_path)

    @staticmethod
    def _load_ticker_mapping(path: Path) -> dict[str, dict[str, str]]:
        """Load ticker mapping from JSON file.

        Parameters
        ----------
        path : Path
            Path to ticker_mapping.json.

        Returns
        -------
        dict[str, dict[str, str]]
            Mapping of non-standard Bloomberg ticker prefixes to ticker info.
        """
        if not path.exists():
            logger.warning("Ticker mapping file not found", path=str(path))
            return {}
        data: dict[str, dict[str, str]] = json.loads(path.read_text())
        logger.debug("Ticker mapping loaded", entry_count=len(data))
        return data

    def parse_all_months(self) -> ParseResult:
        """Parse all monthly transcript files in source_dir.

        Returns
        -------
        ParseResult
            Aggregated parsing statistics.
        """
        source_files = sorted(self._source_dir.glob("list_transcript_*.json"))
        if not source_files:
            logger.info("No transcript files found", source_dir=str(self._source_dir))
            return ParseResult()

        logger.info(
            "Starting transcript parsing",
            file_count=len(source_files),
            source_dir=str(self._source_dir),
        )

        total = 0
        success = 0
        error_count = 0
        errors: list[str] = []

        # Phase 1: Load all records and deduplicate by TRANSCRIPTID
        all_records: list[tuple[str, str, dict[str, Any]]] = []
        for filepath in source_files:
            match = MONTH_FILE_PATTERN.search(filepath.name)
            if not match:
                logger.warning("Skipping non-matching file", filename=filepath.name)
                continue
            year_month = f"{match.group(1)}{match.group(2)}"

            raw_text = filepath.read_text(encoding="utf-8")
            data = self._parse_json_with_trailing_comma(raw_text, filepath.name)
            if data is None:
                error_count += 1
                errors.append(f"Failed to parse JSON: {filepath.name}")
                continue

            for _sedol, records in data.items():
                if not isinstance(records, list):
                    continue
                for record in records:
                    if not isinstance(record, dict):
                        continue
                    all_records.append((year_month, filepath.name, record))

        # Phase 2: Deduplicate by TRANSCRIPTID (Audited Copy priority)
        deduped_records = self._deduplicate_records(all_records)

        total = len(deduped_records)

        # Phase 3: Parse and write each record
        for year_month, _filename, record in deduped_records:
            try:
                written = self._process_record(record, year_month)
                if written:
                    success += 1
                else:
                    # Skipped (e.g. empty text)
                    total -= 1
            except Exception as exc:
                error_count += 1
                transcript_id = record.get("TRANSCRIPTID", "unknown")
                msg = f"Error processing TRANSCRIPTID={transcript_id}: {exc}"
                errors.append(msg)
                logger.error(
                    "Record processing failed",
                    transcript_id=transcript_id,
                    error=str(exc),
                    exc_info=True,
                )

        logger.info(
            "Transcript parsing completed",
            total=total,
            success=success,
            errors=error_count,
        )

        return ParseResult(
            total_count=total,
            success_count=success,
            error_count=error_count,
            errors=errors,
        )

    def _deduplicate_records(
        self,
        records: list[tuple[str, str, dict[str, Any]]],
    ) -> list[tuple[str, str, dict[str, Any]]]:
        """Deduplicate records by TRANSCRIPTID, preferring Audited Copy.

        Parameters
        ----------
        records : list[tuple[str, str, dict[str, Any]]]
            List of (year_month, filename, record) tuples.

        Returns
        -------
        list[tuple[str, str, dict[str, Any]]]
            Deduplicated records.
        """
        best_by_id: dict[float, tuple[str, str, dict[str, Any]]] = {}

        for year_month, filename, record in records:
            transcript_id = record.get("TRANSCRIPTID")
            if transcript_id is None:
                continue

            collection_type = record.get("TRANSCRIPTCOLLECTIONTYPENAME", "")
            existing = best_by_id.get(transcript_id)

            if existing is None:
                best_by_id[transcript_id] = (year_month, filename, record)
            else:
                existing_type = existing[2].get("TRANSCRIPTCOLLECTIONTYPENAME", "")
                # Audited Copy wins over anything else
                if (
                    collection_type == "Audited Copy"
                    and existing_type != "Audited Copy"
                ):
                    best_by_id[transcript_id] = (year_month, filename, record)
                    logger.debug(
                        "Dedup: replaced with Audited Copy",
                        transcript_id=transcript_id,
                    )

        return list(best_by_id.values())

    def _process_record(
        self,
        record: dict[str, Any],
        year_month: str,
    ) -> bool:
        """Process a single transcript record and write output file.

        Parameters
        ----------
        record : dict[str, Any]
            A single transcript record from the source JSON.
        year_month : str
            Year-month string (e.g. "201501").

        Returns
        -------
        bool
            True if the record was successfully written, False if skipped.
        """
        text2 = record.get("transcript_text2") or ""
        text4 = record.get("transcript_text4") or ""

        if not text2.strip() and not text4.strip():
            logger.debug(
                "Skipping empty transcript",
                transcript_id=record.get("TRANSCRIPTID"),
            )
            return False

        # Extract ticker
        bloomberg_ticker = record.get("Bloomberg_Ticker", "")
        ticker = self._resolve_ticker(bloomberg_ticker)

        # Parse sections
        sections = self._parse_sections(text2, text4)
        if not sections:
            logger.debug(
                "No sections parsed",
                transcript_id=record.get("TRANSCRIPTID"),
                ticker=ticker,
            )
            return False

        # Detect truncation
        is_truncated = self._detect_truncation(record, text2, text4)

        # Extract metadata
        event_date = self._extract_event_date(record)
        fiscal_quarter = self._extract_fiscal_quarter(record)

        # Build output
        output = {
            "metadata": {
                "ticker": ticker,
                "event_date": event_date,
                "fiscal_quarter": fiscal_quarter,
                "is_truncated": is_truncated,
                "transcript_id": record.get("TRANSCRIPTID"),
                "company_name": record.get("COMPANYNAME", ""),
                "collection_type": record.get("TRANSCRIPTCOLLECTIONTYPENAME", ""),
            },
            "sections": sections,
        }

        # Write output file
        output_path = self._output_dir / ticker / f"{year_month}_earnings_call.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(output, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        logger.debug(
            "Transcript written",
            ticker=ticker,
            year_month=year_month,
            output_path=str(output_path),
        )

        return True

    def _resolve_ticker(self, bloomberg_ticker: str) -> str:
        """Convert Bloomberg Ticker to simple ticker.

        For standard tickers (e.g. "AAPL US Equity"), splits by space and
        takes the first element. For non-standard tickers starting with
        digits, looks up ticker_mapping.json.

        Parameters
        ----------
        bloomberg_ticker : str
            Bloomberg Ticker string (e.g. "AAPL US Equity").

        Returns
        -------
        str
            Simple ticker symbol (e.g. "AAPL").
        """
        if not bloomberg_ticker:
            return "UNKNOWN"

        parts = bloomberg_ticker.split()
        raw_ticker = parts[0] if parts else bloomberg_ticker

        # Check if raw ticker starts with a digit (non-standard)
        if raw_ticker and raw_ticker[0].isdigit():
            mapping_entry = self._ticker_mapping.get(raw_ticker)
            if mapping_entry:
                resolved = mapping_entry.get("ticker", raw_ticker)
                logger.debug(
                    "Non-standard ticker resolved",
                    raw=raw_ticker,
                    resolved=resolved,
                )
                return resolved
            logger.debug(
                "Non-standard ticker not in mapping, using raw",
                raw=raw_ticker,
            )

        return raw_ticker

    @staticmethod
    def _parse_sections(text2: str, text4: str) -> list[dict[str, str | None]]:
        """Parse tagged transcript text into structured sections.

        Parameters
        ----------
        text2 : str
            Presentation text with tags.
        text4 : str
            Q&A text with tags.

        Returns
        -------
        list[dict[str, str | None]]
            Ordered list of section dicts with speaker, role, section_type, content.
        """
        sections: list[dict[str, str | None]] = []

        for text in [text2, text4]:
            if not text or not text.strip():
                continue
            matches = TAG_PATTERN.findall(text)
            for tag_type, speaker, role, content in matches:
                section_type = SECTION_TYPE_MAP.get(tag_type, tag_type)
                # Remove trailing separators (---) and whitespace
                cleaned = re.sub(r"[\s\-]*---[\s]*$", "", content.strip()).strip()
                if cleaned:
                    sections.append(
                        {
                            "speaker": speaker.strip(),
                            "role": role.strip(),
                            "section_type": section_type,
                            "content": cleaned,
                        }
                    )

        return sections

    @staticmethod
    def _detect_truncation(
        record: dict[str, Any],
        text2: str,
        text4: str,
    ) -> bool:
        """Detect if transcript text was truncated at 32767 characters.

        Parameters
        ----------
        record : dict[str, Any]
            The transcript record.
        text2 : str
            Presentation text.
        text4 : str
            Q&A text.

        Returns
        -------
        bool
            True if truncation is detected.
        """
        total_chars = record.get("total_characters", 0)
        if total_chars and float(total_chars) >= TRUNCATION_THRESHOLD:
            return True

        # Also check individual text field lengths
        return len(text2) >= TRUNCATION_THRESHOLD or len(text4) >= TRUNCATION_THRESHOLD

    @staticmethod
    def _extract_event_date(record: dict[str, Any]) -> str:
        """Extract event date as ISO format string.

        Parameters
        ----------
        record : dict[str, Any]
            The transcript record.

        Returns
        -------
        str
            Date string in YYYY-MM-DD format.
        """
        event_date_str = record.get("eventDateOnly", "")
        if event_date_str:
            # Parse "2015-01-28T00:00:00.000" to "2015-01-28"
            return event_date_str[:10]
        return ""

    @staticmethod
    def _extract_fiscal_quarter(record: dict[str, Any]) -> str:
        """Extract fiscal quarter from event headline.

        Parameters
        ----------
        record : dict[str, Any]
            The transcript record.

        Returns
        -------
        str
            Fiscal quarter label (e.g. "Q1 2015").
        """
        headline = record.get("eventHeadline", "")
        # Pattern: "Apple Inc., Q1 2015 Earnings Call, Jan 28, 2015"
        match = re.search(r"(Q[1-4]\s+\d{4})", headline)
        if match:
            return match.group(1)

        # Fallback: "H1 2015" pattern
        match = re.search(r"(H[12]\s+\d{4})", headline)
        if match:
            return match.group(1)

        # Fallback: use calendar year and month
        year = record.get("calendar_year", 0)
        month = record.get("calendar_month", 0)
        if year and month:
            quarter = (int(month) - 1) // 3 + 1
            return f"Q{quarter} {int(year)}"

        return ""

    @staticmethod
    def _parse_json_with_trailing_comma(
        raw_text: str,
        filename: str,
    ) -> dict[str, Any] | None:
        """Parse JSON text, fixing trailing commas if needed.

        Parameters
        ----------
        raw_text : str
            Raw JSON text that may contain trailing commas.
        filename : str
            Filename for error logging.

        Returns
        -------
        dict[str, Any] | None
            Parsed JSON data, or None if parsing fails.
        """
        try:
            return json.loads(raw_text)
        except json.JSONDecodeError:
            pass

        # Fix trailing commas: ,] or ,}
        fixed = re.sub(r",\s*([}\]])", r"\1", raw_text)
        try:
            data: dict[str, Any] = json.loads(fixed)
            logger.debug("Fixed trailing comma in JSON", filename=filename)
            return data
        except json.JSONDecodeError as exc:
            logger.error(
                "Failed to parse JSON even after trailing comma fix",
                filename=filename,
                error=str(exc),
            )
            return None


__all__ = [
    "ParseResult",
    "TranscriptParser",
]

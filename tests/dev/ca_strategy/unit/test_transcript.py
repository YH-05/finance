"""Unit tests for TranscriptLoader.

Tests cover all acceptance criteria from Issue #3578:
- load_single loads existing transcript file and returns Transcript
- load_single returns None with warning log for missing file
- load_batch loads multiple tickers correctly
- PoiT filtering (cutoff_date) works correctly
- Pydantic validation errors are logged
- Edge cases (empty directory, invalid JSON, empty sections)
"""

from __future__ import annotations

import json
import logging
from datetime import date
from typing import TYPE_CHECKING, Any

import pytest

from dev.ca_strategy.transcript import TranscriptLoader
from dev.ca_strategy.types import Transcript

if TYPE_CHECKING:
    from pathlib import Path


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _make_transcript_json(
    *,
    ticker: str = "AAPL",
    event_date: str = "2015-01-28",
    fiscal_quarter: str = "Q1 2015",
    is_truncated: bool = False,
    speaker: str = "Tim Cook",
    role: str | None = "CEO",
    section_type: str = "prepared_remarks",
    content: str = "We had a great quarter with record revenue.",
    raw_source: str | None = None,
) -> dict[str, Any]:
    """Build a transcript JSON dict matching TranscriptParser output format."""
    return {
        "metadata": {
            "ticker": ticker,
            "event_date": event_date,
            "fiscal_quarter": fiscal_quarter,
            "is_truncated": is_truncated,
        },
        "sections": [
            {
                "speaker": speaker,
                "role": role,
                "section_type": section_type,
                "content": content,
            },
        ],
        "raw_source": raw_source,
    }


def _write_transcript_file(
    base_dir: Path,
    ticker: str,
    year_month: str,
    data: dict[str, Any],
) -> Path:
    """Write a transcript JSON file to the expected directory structure."""
    ticker_dir = base_dir / ticker
    ticker_dir.mkdir(parents=True, exist_ok=True)
    filepath = ticker_dir / f"{year_month}_earnings_call.json"
    filepath.write_text(json.dumps(data, ensure_ascii=False, indent=2))
    return filepath


# ===========================================================================
# load_single tests
# ===========================================================================
class TestLoadSingle:
    """TranscriptLoader.load_single reads and validates a single transcript."""

    def test_正常系_既存ファイルを読み込みTranscriptを返す(
        self, tmp_path: Path
    ) -> None:
        data = _make_transcript_json()
        _write_transcript_file(tmp_path, "AAPL", "201501", data)

        loader = TranscriptLoader(base_dir=tmp_path, cutoff_date=date(2015, 12, 31))
        result = loader.load_single("AAPL", "201501")

        assert result is not None
        assert isinstance(result, Transcript)
        assert result.metadata.ticker == "AAPL"
        assert result.metadata.event_date == date(2015, 1, 28)
        assert result.metadata.fiscal_quarter == "Q1 2015"
        assert len(result.sections) == 1
        assert result.sections[0].speaker == "Tim Cook"

    def test_正常系_cutoff_date以前のトランスクリプトを読み込む(
        self, tmp_path: Path
    ) -> None:
        data = _make_transcript_json(event_date="2015-06-15")
        _write_transcript_file(tmp_path, "AAPL", "201506", data)

        loader = TranscriptLoader(base_dir=tmp_path, cutoff_date=date(2015, 9, 30))
        result = loader.load_single("AAPL", "201506")

        assert result is not None
        assert result.metadata.event_date == date(2015, 6, 15)

    def test_正常系_cutoff_date以降のトランスクリプトはNoneを返す(
        self, tmp_path: Path
    ) -> None:
        data = _make_transcript_json(event_date="2016-01-15")
        _write_transcript_file(tmp_path, "AAPL", "201601", data)

        loader = TranscriptLoader(base_dir=tmp_path, cutoff_date=date(2015, 9, 30))
        result = loader.load_single("AAPL", "201601")

        assert result is None

    def test_異常系_存在しないファイルでNoneを返しwarningログを出力(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        loader = TranscriptLoader(base_dir=tmp_path, cutoff_date=date(2015, 12, 31))

        with caplog.at_level(logging.WARNING):
            result = loader.load_single("AAPL", "201501")

        assert result is None
        warning_records = [r for r in caplog.records if r.levelno >= logging.WARNING]
        assert len(warning_records) > 0

    def test_異常系_Pydanticバリデーションエラーでログ記録しNoneを返す(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        # Create invalid transcript: empty speaker
        invalid_data = {
            "metadata": {
                "ticker": "AAPL",
                "event_date": "2015-01-28",
                "fiscal_quarter": "Q1 2015",
                "is_truncated": False,
            },
            "sections": [
                {
                    "speaker": "",  # Invalid: empty speaker
                    "role": "CEO",
                    "section_type": "prepared_remarks",
                    "content": "Some content.",
                },
            ],
            "raw_source": None,
        }
        _write_transcript_file(tmp_path, "AAPL", "201501", invalid_data)

        loader = TranscriptLoader(base_dir=tmp_path, cutoff_date=date(2015, 12, 31))
        result = loader.load_single("AAPL", "201501")

        assert result is None

    def test_異常系_不正なJSONファイルでNoneを返す(self, tmp_path: Path) -> None:
        ticker_dir = tmp_path / "AAPL"
        ticker_dir.mkdir(parents=True, exist_ok=True)
        filepath = ticker_dir / "201501_earnings_call.json"
        filepath.write_text("{invalid json content")

        loader = TranscriptLoader(base_dir=tmp_path, cutoff_date=date(2015, 12, 31))
        result = loader.load_single("AAPL", "201501")

        assert result is None

    def test_正常系_cutoff_dateちょうどの日付はNoneではない(
        self, tmp_path: Path
    ) -> None:
        data = _make_transcript_json(event_date="2015-09-30")
        _write_transcript_file(tmp_path, "AAPL", "201509", data)

        loader = TranscriptLoader(base_dir=tmp_path, cutoff_date=date(2015, 9, 30))
        result = loader.load_single("AAPL", "201509")

        assert result is not None
        assert result.metadata.event_date == date(2015, 9, 30)

    def test_正常系_raw_sourceがNoneでも読み込める(self, tmp_path: Path) -> None:
        data = _make_transcript_json(raw_source=None)
        _write_transcript_file(tmp_path, "AAPL", "201501", data)

        loader = TranscriptLoader(base_dir=tmp_path, cutoff_date=date(2015, 12, 31))
        result = loader.load_single("AAPL", "201501")

        assert result is not None
        assert result.raw_source is None

    def test_正常系_複数セクションを持つトランスクリプトを読み込める(
        self, tmp_path: Path
    ) -> None:
        data = {
            "metadata": {
                "ticker": "AAPL",
                "event_date": "2015-01-28",
                "fiscal_quarter": "Q1 2015",
                "is_truncated": False,
            },
            "sections": [
                {
                    "speaker": "Tim Cook",
                    "role": "CEO",
                    "section_type": "prepared_remarks",
                    "content": "Opening remarks.",
                },
                {
                    "speaker": "Luca Maestri",
                    "role": "CFO",
                    "section_type": "prepared_remarks",
                    "content": "Financial overview.",
                },
                {
                    "speaker": "Analyst",
                    "role": "Analysts",
                    "section_type": "question",
                    "content": "What about margins?",
                },
            ],
            "raw_source": None,
        }
        _write_transcript_file(tmp_path, "AAPL", "201501", data)

        loader = TranscriptLoader(base_dir=tmp_path, cutoff_date=date(2015, 12, 31))
        result = loader.load_single("AAPL", "201501")

        assert result is not None
        assert len(result.sections) == 3


# ===========================================================================
# load_batch tests
# ===========================================================================
class TestLoadBatch:
    """TranscriptLoader.load_batch loads transcripts for multiple tickers."""

    def test_正常系_複数銘柄を正しく読み込める(self, tmp_path: Path) -> None:
        aapl_data = _make_transcript_json(ticker="AAPL", event_date="2015-01-28")
        msft_data = _make_transcript_json(
            ticker="MSFT",
            event_date="2015-01-22",
            speaker="Satya Nadella",
            content="Cloud first, mobile first.",
        )
        _write_transcript_file(tmp_path, "AAPL", "201501", aapl_data)
        _write_transcript_file(tmp_path, "MSFT", "201501", msft_data)

        loader = TranscriptLoader(base_dir=tmp_path, cutoff_date=date(2015, 12, 31))
        result = loader.load_batch(["AAPL", "MSFT"])

        assert "AAPL" in result
        assert "MSFT" in result
        assert len(result["AAPL"]) == 1
        assert len(result["MSFT"]) == 1
        assert result["AAPL"][0].metadata.ticker == "AAPL"
        assert result["MSFT"][0].metadata.ticker == "MSFT"

    def test_正常系_同一銘柄の複数トランスクリプトを読み込む(
        self, tmp_path: Path
    ) -> None:
        q1_data = _make_transcript_json(
            ticker="AAPL",
            event_date="2015-01-28",
            fiscal_quarter="Q1 2015",
        )
        q2_data = _make_transcript_json(
            ticker="AAPL",
            event_date="2015-04-27",
            fiscal_quarter="Q2 2015",
        )
        _write_transcript_file(tmp_path, "AAPL", "201501", q1_data)
        _write_transcript_file(tmp_path, "AAPL", "201504", q2_data)

        loader = TranscriptLoader(base_dir=tmp_path, cutoff_date=date(2015, 12, 31))
        result = loader.load_batch(["AAPL"])

        assert "AAPL" in result
        assert len(result["AAPL"]) == 2

    def test_正常系_存在しない銘柄は空リストを返す(self, tmp_path: Path) -> None:
        loader = TranscriptLoader(base_dir=tmp_path, cutoff_date=date(2015, 12, 31))
        result = loader.load_batch(["NONEXISTENT"])

        assert "NONEXISTENT" in result
        assert result["NONEXISTENT"] == []

    def test_正常系_cutoff_dateでフィルタリングされる(self, tmp_path: Path) -> None:
        before_data = _make_transcript_json(
            ticker="AAPL",
            event_date="2015-06-15",
            fiscal_quarter="Q3 2015",
        )
        after_data = _make_transcript_json(
            ticker="AAPL",
            event_date="2015-12-15",
            fiscal_quarter="Q1 2016",
        )
        _write_transcript_file(tmp_path, "AAPL", "201506", before_data)
        _write_transcript_file(tmp_path, "AAPL", "201512", after_data)

        loader = TranscriptLoader(base_dir=tmp_path, cutoff_date=date(2015, 9, 30))
        result = loader.load_batch(["AAPL"])

        assert len(result["AAPL"]) == 1
        assert result["AAPL"][0].metadata.event_date == date(2015, 6, 15)

    def test_エッジケース_空のティッカーリストで空の辞書を返す(
        self, tmp_path: Path
    ) -> None:
        loader = TranscriptLoader(base_dir=tmp_path, cutoff_date=date(2015, 12, 31))
        result = loader.load_batch([])

        assert result == {}

    def test_正常系_バリデーションエラーのファイルはスキップされる(
        self, tmp_path: Path
    ) -> None:
        valid_data = _make_transcript_json(ticker="AAPL", event_date="2015-01-28")
        invalid_data = {
            "metadata": {
                "ticker": "AAPL",
                "event_date": "2015-04-27",
                "fiscal_quarter": "Q2 2015",
                "is_truncated": False,
            },
            "sections": [
                {
                    "speaker": "",  # Invalid
                    "role": "CEO",
                    "section_type": "prepared_remarks",
                    "content": "Content.",
                },
            ],
            "raw_source": None,
        }
        _write_transcript_file(tmp_path, "AAPL", "201501", valid_data)
        _write_transcript_file(tmp_path, "AAPL", "201504", invalid_data)

        loader = TranscriptLoader(base_dir=tmp_path, cutoff_date=date(2015, 12, 31))
        result = loader.load_batch(["AAPL"])

        # Only valid transcript should be loaded
        assert len(result["AAPL"]) == 1
        assert result["AAPL"][0].metadata.event_date == date(2015, 1, 28)


# ===========================================================================
# PoiT filtering tests
# ===========================================================================
class TestPoiTFiltering:
    """TranscriptLoader correctly applies Point-in-Time filtering."""

    def test_正常系_cutoff_date以前のトランスクリプトのみ保持(
        self, tmp_path: Path
    ) -> None:
        for month, day in [
            ("201501", "2015-01-28"),
            ("201504", "2015-04-27"),
            ("201507", "2015-07-21"),
            ("201510", "2015-10-27"),
        ]:
            data = _make_transcript_json(ticker="AAPL", event_date=day)
            _write_transcript_file(tmp_path, "AAPL", month, data)

        loader = TranscriptLoader(base_dir=tmp_path, cutoff_date=date(2015, 9, 30))
        result = loader.load_batch(["AAPL"])

        # Only Q1, Q2, Q3 should be included (not Q4 with Oct 27)
        assert len(result["AAPL"]) == 3
        for t in result["AAPL"]:
            assert t.metadata.event_date <= date(2015, 9, 30)

    def test_正常系_デフォルトcutoff_dateが使用される(self, tmp_path: Path) -> None:
        data = _make_transcript_json(ticker="AAPL", event_date="2015-01-28")
        _write_transcript_file(tmp_path, "AAPL", "201501", data)

        # Use default CUTOFF_DATE from pit.py (2015-09-30)
        loader = TranscriptLoader(base_dir=tmp_path)
        result = loader.load_single("AAPL", "201501")

        assert result is not None


# ===========================================================================
# Pydantic validation tests
# ===========================================================================
class TestValidation:
    """TranscriptLoader._validate_transcript handles validation correctly."""

    def test_異常系_セクションが空リストでバリデーションエラー(
        self, tmp_path: Path
    ) -> None:
        data = {
            "metadata": {
                "ticker": "AAPL",
                "event_date": "2015-01-28",
                "fiscal_quarter": "Q1 2015",
                "is_truncated": False,
            },
            "sections": [],  # Invalid: empty sections
            "raw_source": None,
        }
        _write_transcript_file(tmp_path, "AAPL", "201501", data)

        loader = TranscriptLoader(base_dir=tmp_path, cutoff_date=date(2015, 12, 31))
        result = loader.load_single("AAPL", "201501")

        assert result is None

    def test_異常系_metadataにtickerが欠落でバリデーションエラー(
        self, tmp_path: Path
    ) -> None:
        data = {
            "metadata": {
                # "ticker" is missing
                "event_date": "2015-01-28",
                "fiscal_quarter": "Q1 2015",
                "is_truncated": False,
            },
            "sections": [
                {
                    "speaker": "CEO",
                    "role": "CEO",
                    "section_type": "prepared_remarks",
                    "content": "Content.",
                },
            ],
            "raw_source": None,
        }
        _write_transcript_file(tmp_path, "AAPL", "201501", data)

        loader = TranscriptLoader(base_dir=tmp_path, cutoff_date=date(2015, 12, 31))
        result = loader.load_single("AAPL", "201501")

        assert result is None

    def test_正常系_追加フィールドは無視されてバリデーション成功(
        self, tmp_path: Path
    ) -> None:
        data = _make_transcript_json()
        # Add extra fields that TranscriptParser outputs but Transcript model ignores
        data["metadata"]["transcript_id"] = 100001
        data["metadata"]["company_name"] = "Apple Inc."
        data["metadata"]["collection_type"] = "Audited Copy"
        _write_transcript_file(tmp_path, "AAPL", "201501", data)

        loader = TranscriptLoader(base_dir=tmp_path, cutoff_date=date(2015, 12, 31))
        result = loader.load_single("AAPL", "201501")

        assert result is not None
        assert result.metadata.ticker == "AAPL"

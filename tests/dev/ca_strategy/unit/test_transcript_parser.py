"""Unit tests for TranscriptParser.

Tests cover all acceptance criteria from Issue #3576:
- Tag parsing regex (presentation/question/answer sections)
- Bloomberg Ticker to simple ticker conversion
- Non-standard ticker (digit-starting) mapping via ticker_mapping.json
- TRANSCRIPTID deduplication with Audited Copy priority
- Trailing comma JSON fix
- 32767-character truncation detection
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pathlib import Path

import pytest

from dev.ca_strategy.transcript_parser import (
    ParseResult,
    TranscriptParser,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _make_transcript_record(
    *,
    bloomberg_ticker: str = "AAPL US Equity",
    transcript_id: float = 100001.0,
    collection_type: str = "Audited Copy",
    event_date: str = "2015-01-28T00:00:00.000",
    event_headline: str = "Apple Inc., Q1 2015 Earnings Call, Jan 28, 2015",
    text2: str = "【プレゼン: Tim Cook (Executives)】\nWe had a great quarter.",
    text4: str = "【質問: Analyst One (Analysts)】\nWhat about margins?\n\n---\n\n【回答: Tim Cook (Executives)】\nMargins are strong.",
    total_characters: float = 100.0,
    company_name: str = "Apple Inc.",
    calendar_year: float = 2015.0,
    calendar_month: float = 1.0,
) -> dict[str, Any]:
    """Build a minimal transcript record matching S&P Capital IQ schema."""
    return {
        "COMPANYID": 12345.0,
        "COMPANYNAME": company_name,
        "ISOCOUNTRY2": "US",
        "IDENTIFIERSTARTDATE": "1980-01-02T00:00:00.000",
        "IDENTIFIERENDDATE": None,
        "ACTIVEFLAG": 1.0,
        "SECURITYID": 20000001.0,
        "TRADINGITEMID": 100000001.0,
        "EXCHANGEID": 132.0,
        "PRIMARYFLAG": 1.0,
        "EXCHANGENAME": "NASDAQ",
        "exchangeCountry": 213.0,
        "calendar_year": calendar_year,
        "calendar_month": calendar_month,
        "year_month": f"{int(calendar_year)}-{int(calendar_month):02d}-01T00:00:00.000",
        "year_month_label": f"{int(calendar_year)}-{int(calendar_month):02d}",
        "KEYDEVID": 280000000.0,
        "eventDate": "2015-01-28T09:30:00.000",
        "eventDateOnly": event_date,
        "eventHeadline": event_headline,
        "eventType": "Earnings Calls",
        "KEYDEVEVENTTYPEID": 48.0,
        "event_link_effective_date": "2018-08-12T01:00:02.000",
        "event_effective_date": "2018-08-12T01:00:02.000",
        "is_current_event_link": 1.0,
        "is_current_event": 1.0,
        "TRANSCRIPTID": transcript_id,
        "TRANSCRIPTCOLLECTIONTYPEID": 8.0,
        "transcript_language_code": "EN",
        "TRANSCRIPTCOLLECTIONTYPENAME": collection_type,
        "has_transcript": 1.0,
        "is_japanese": 0.0,
        "is_english": 1.0,
        "transcript_text1": "Some raw text",
        "transcript_text2": text2,
        "transcript_text3": "Q&A raw text",
        "transcript_text4": text4,
        "total_component_count": 10.0,
        "total_characters": total_characters,
        "first_component_order": 0.0,
        "last_component_order": 9.0,
        "All": text2 + " " + text4,
        "Bloomberg_Ticker": bloomberg_ticker,
        "FIGI": "BBG000B9XRY4",
    }


def _write_source_json(
    source_dir: Path,
    filename: str,
    data: dict[str, list[dict[str, Any]]],
) -> Path:
    """Write a transcript JSON file to source_dir."""
    source_dir.mkdir(parents=True, exist_ok=True)
    filepath = source_dir / filename
    filepath.write_text(json.dumps(data, ensure_ascii=False))
    return filepath


def _write_ticker_mapping(path: Path, mapping: dict[str, dict[str, str]]) -> None:
    """Write a ticker_mapping.json file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(mapping, ensure_ascii=False, indent=2))


# ===========================================================================
# Tag parsing regex tests
# ===========================================================================
class TestTagParsing:
    """Tag parsing regex correctly splits presentation/question/answer sections."""

    def test_正常系_プレゼンタグをパースできる(self, tmp_path: Path) -> None:
        text2 = "【プレゼン: Tim Cook (Executives)】\nWe had a great quarter."
        record = _make_transcript_record(text2=text2, text4="")
        source_dir = tmp_path / "source"
        output_dir = tmp_path / "output"
        mapping_path = tmp_path / "ticker_mapping.json"
        _write_source_json(
            source_dir, "list_transcript_2015-01.json", {"2046251": [record]}
        )
        _write_ticker_mapping(mapping_path, {})

        parser = TranscriptParser(source_dir, output_dir, mapping_path)
        result = parser.parse_all_months()

        assert result.success_count >= 1
        # Check output file exists
        output_files = list(output_dir.rglob("*.json"))
        assert len(output_files) >= 1
        output_data = json.loads(output_files[0].read_text())
        sections = output_data["sections"]
        pres_sections = [s for s in sections if s["section_type"] == "prepared_remarks"]
        assert len(pres_sections) == 1
        assert pres_sections[0]["speaker"] == "Tim Cook"
        assert pres_sections[0]["role"] == "Executives"
        assert "great quarter" in pres_sections[0]["content"]

    def test_正常系_質問タグをパースできる(self, tmp_path: Path) -> None:
        text4 = "【質問: Analyst One (Analysts)】\nWhat about margins?"
        record = _make_transcript_record(
            text2="【プレゼン: CEO (Executives)】\nHello.",
            text4=text4,
        )
        source_dir = tmp_path / "source"
        output_dir = tmp_path / "output"
        mapping_path = tmp_path / "ticker_mapping.json"
        _write_source_json(
            source_dir, "list_transcript_2015-01.json", {"2046251": [record]}
        )
        _write_ticker_mapping(mapping_path, {})

        parser = TranscriptParser(source_dir, output_dir, mapping_path)
        result = parser.parse_all_months()

        assert result.success_count >= 1
        output_files = list(output_dir.rglob("*.json"))
        output_data = json.loads(output_files[0].read_text())
        qa_sections = [
            s for s in output_data["sections"] if s["section_type"] == "question"
        ]
        assert len(qa_sections) == 1
        assert qa_sections[0]["speaker"] == "Analyst One"
        assert qa_sections[0]["role"] == "Analysts"

    def test_正常系_回答タグをパースできる(self, tmp_path: Path) -> None:
        text4 = (
            "【質問: Analyst (Analysts)】\nQuestion?\n\n---\n\n"
            "【回答: CFO Person (Executives)】\nAnswer here."
        )
        record = _make_transcript_record(
            text2="【プレゼン: CEO (Executives)】\nHello.",
            text4=text4,
        )
        source_dir = tmp_path / "source"
        output_dir = tmp_path / "output"
        mapping_path = tmp_path / "ticker_mapping.json"
        _write_source_json(
            source_dir, "list_transcript_2015-01.json", {"2046251": [record]}
        )
        _write_ticker_mapping(mapping_path, {})

        parser = TranscriptParser(source_dir, output_dir, mapping_path)
        result = parser.parse_all_months()

        assert result.success_count >= 1
        output_files = list(output_dir.rglob("*.json"))
        output_data = json.loads(output_files[0].read_text())
        answer_sections = [
            s for s in output_data["sections"] if s["section_type"] == "answer"
        ]
        assert len(answer_sections) == 1
        assert answer_sections[0]["speaker"] == "CFO Person"
        assert answer_sections[0]["role"] == "Executives"

    def test_正常系_複数セクションを正しい順序でパースできる(
        self, tmp_path: Path
    ) -> None:
        text2 = (
            "【プレゼン: CEO (Executives)】\nOpening remarks.\n\n---\n\n"
            "【プレゼン: CFO (Executives)】\nFinancial overview."
        )
        text4 = (
            "【質問: Analyst A (Analysts)】\nQ1?\n\n---\n\n"
            "【回答: CEO (Executives)】\nA1.\n\n---\n\n"
            "【質問: Analyst B (Analysts)】\nQ2?\n\n---\n\n"
            "【回答: CFO (Executives)】\nA2."
        )
        record = _make_transcript_record(text2=text2, text4=text4)
        source_dir = tmp_path / "source"
        output_dir = tmp_path / "output"
        mapping_path = tmp_path / "ticker_mapping.json"
        _write_source_json(
            source_dir, "list_transcript_2015-01.json", {"2046251": [record]}
        )
        _write_ticker_mapping(mapping_path, {})

        parser = TranscriptParser(source_dir, output_dir, mapping_path)
        parser.parse_all_months()

        output_files = list(output_dir.rglob("*.json"))
        output_data = json.loads(output_files[0].read_text())
        sections = output_data["sections"]
        assert len(sections) == 6
        assert sections[0]["section_type"] == "prepared_remarks"
        assert sections[1]["section_type"] == "prepared_remarks"
        assert sections[2]["section_type"] == "question"
        assert sections[3]["section_type"] == "answer"
        assert sections[4]["section_type"] == "question"
        assert sections[5]["section_type"] == "answer"


# ===========================================================================
# Bloomberg Ticker conversion tests
# ===========================================================================
class TestBloombergTickerConversion:
    """Bloomberg Ticker to simple ticker conversion works correctly."""

    def test_正常系_スペース分割で先頭要素を取得できる(self, tmp_path: Path) -> None:
        record = _make_transcript_record(bloomberg_ticker="AAPL US Equity")
        source_dir = tmp_path / "source"
        output_dir = tmp_path / "output"
        mapping_path = tmp_path / "ticker_mapping.json"
        _write_source_json(
            source_dir, "list_transcript_2015-01.json", {"2046251": [record]}
        )
        _write_ticker_mapping(mapping_path, {})

        parser = TranscriptParser(source_dir, output_dir, mapping_path)
        result = parser.parse_all_months()

        assert result.success_count == 1
        # Output should be in AAPL directory
        aapl_dir = output_dir / "AAPL"
        assert aapl_dir.exists()

    def test_正常系_カナダティッカーを変換できる(self, tmp_path: Path) -> None:
        record = _make_transcript_record(bloomberg_ticker="CNR CN Equity")
        source_dir = tmp_path / "source"
        output_dir = tmp_path / "output"
        mapping_path = tmp_path / "ticker_mapping.json"
        _write_source_json(
            source_dir, "list_transcript_2015-01.json", {"9999999": [record]}
        )
        _write_ticker_mapping(mapping_path, {})

        parser = TranscriptParser(source_dir, output_dir, mapping_path)
        result = parser.parse_all_months()

        assert result.success_count == 1
        cnr_dir = output_dir / "CNR"
        assert cnr_dir.exists()

    def test_正常系_UKティッカーを変換できる(self, tmp_path: Path) -> None:
        record = _make_transcript_record(bloomberg_ticker="DGE LN Equity")
        source_dir = tmp_path / "source"
        output_dir = tmp_path / "output"
        mapping_path = tmp_path / "ticker_mapping.json"
        _write_source_json(
            source_dir, "list_transcript_2015-01.json", {"0237400": [record]}
        )
        _write_ticker_mapping(mapping_path, {})

        parser = TranscriptParser(source_dir, output_dir, mapping_path)
        result = parser.parse_all_months()

        assert result.success_count == 1
        dge_dir = output_dir / "DGE"
        assert dge_dir.exists()


# ===========================================================================
# Non-standard ticker (digit-starting) mapping tests
# ===========================================================================
class TestNonStandardTickerMapping:
    """Non-standard tickers (starting with digits) use ticker_mapping.json."""

    def test_正常系_数字開始ティッカーがticker_mappingで変換される(
        self, tmp_path: Path
    ) -> None:
        record = _make_transcript_record(
            bloomberg_ticker="1715651D US Equity",
            company_name="EIDP, Inc.",
        )
        source_dir = tmp_path / "source"
        output_dir = tmp_path / "output"
        mapping_path = tmp_path / "ticker_mapping.json"
        _write_source_json(
            source_dir, "list_transcript_2015-01.json", {"1715651": [record]}
        )
        _write_ticker_mapping(
            mapping_path,
            {
                "1715651D": {
                    "ticker": "DD",
                    "company_name": "EIDP, Inc.",
                    "note": "DuPont",
                }
            },
        )

        parser = TranscriptParser(source_dir, output_dir, mapping_path)
        result = parser.parse_all_months()

        assert result.success_count == 1
        dd_dir = output_dir / "DD"
        assert dd_dir.exists()

    def test_正常系_複数の非標準ティッカーが正しく変換される(
        self, tmp_path: Path
    ) -> None:
        record1 = _make_transcript_record(
            bloomberg_ticker="1541931D US Equity",
            transcript_id=200001.0,
        )
        record2 = _make_transcript_record(
            bloomberg_ticker="2258717D US Equity",
            transcript_id=200002.0,
        )
        source_dir = tmp_path / "source"
        output_dir = tmp_path / "output"
        mapping_path = tmp_path / "ticker_mapping.json"
        _write_source_json(
            source_dir,
            "list_transcript_2015-01.json",
            {"1541931": [record1], "2258717": [record2]},
        )
        _write_ticker_mapping(
            mapping_path,
            {
                "1541931D": {
                    "ticker": "ALTR",
                    "company_name": "Altera Corporation",
                    "note": "Intel acquired",
                },
                "2258717D": {
                    "ticker": "EMC",
                    "company_name": "Dell EMC",
                    "note": "Dell acquired",
                },
            },
        )

        parser = TranscriptParser(source_dir, output_dir, mapping_path)
        result = parser.parse_all_months()

        assert result.success_count == 2
        assert (output_dir / "ALTR").exists()
        assert (output_dir / "EMC").exists()

    def test_異常系_mappingに存在しない数字ティッカーはそのまま使用(
        self, tmp_path: Path
    ) -> None:
        record = _make_transcript_record(
            bloomberg_ticker="9999999D US Equity",
        )
        source_dir = tmp_path / "source"
        output_dir = tmp_path / "output"
        mapping_path = tmp_path / "ticker_mapping.json"
        _write_source_json(
            source_dir, "list_transcript_2015-01.json", {"9999999": [record]}
        )
        _write_ticker_mapping(mapping_path, {})

        parser = TranscriptParser(source_dir, output_dir, mapping_path)
        result = parser.parse_all_months()

        # Should still succeed using the raw Bloomberg ticker first part
        assert result.success_count == 1
        assert (output_dir / "9999999D").exists()


# ===========================================================================
# TRANSCRIPTID deduplication tests
# ===========================================================================
class TestTranscriptDedup:
    """TRANSCRIPTID deduplication with Audited Copy priority."""

    def test_正常系_同一TRANSCRIPTIDでAuditedCopyが優先される(
        self, tmp_path: Path
    ) -> None:
        audited = _make_transcript_record(
            transcript_id=100001.0,
            collection_type="Audited Copy",
            text2="【プレゼン: CEO (Executives)】\nAudited version.",
        )
        preliminary = _make_transcript_record(
            transcript_id=100001.0,
            collection_type="Preliminary",
            text2="【プレゼン: CEO (Executives)】\nPreliminary version.",
        )
        source_dir = tmp_path / "source"
        output_dir = tmp_path / "output"
        mapping_path = tmp_path / "ticker_mapping.json"
        _write_source_json(
            source_dir,
            "list_transcript_2015-01.json",
            {"2046251": [preliminary, audited]},
        )
        _write_ticker_mapping(mapping_path, {})

        parser = TranscriptParser(source_dir, output_dir, mapping_path)
        result = parser.parse_all_months()

        assert result.success_count == 1
        output_files = list(output_dir.rglob("*.json"))
        assert len(output_files) == 1
        output_data = json.loads(output_files[0].read_text())
        pres = [
            s
            for s in output_data["sections"]
            if s["section_type"] == "prepared_remarks"
        ]
        assert "Audited version" in pres[0]["content"]

    def test_正常系_異なるTRANSCRIPTIDは別トランスクリプトとして扱われる(
        self, tmp_path: Path
    ) -> None:
        record1 = _make_transcript_record(
            transcript_id=100001.0,
            event_date="2015-01-28T00:00:00.000",
            event_headline="Apple Inc., Q1 2015 Earnings Call, Jan 28, 2015",
        )
        record2 = _make_transcript_record(
            transcript_id=100002.0,
            event_date="2015-04-28T00:00:00.000",
            event_headline="Apple Inc., Q2 2015 Earnings Call, Apr 28, 2015",
            calendar_month=4.0,
        )
        source_dir = tmp_path / "source"
        output_dir = tmp_path / "output"
        mapping_path = tmp_path / "ticker_mapping.json"
        _write_source_json(
            source_dir,
            "list_transcript_2015-01.json",
            {"2046251": [record1]},
        )
        _write_source_json(
            source_dir,
            "list_transcript_2015-04.json",
            {"2046251": [record2]},
        )
        _write_ticker_mapping(mapping_path, {})

        parser = TranscriptParser(source_dir, output_dir, mapping_path)
        result = parser.parse_all_months()

        assert result.success_count == 2


# ===========================================================================
# Trailing comma JSON fix tests
# ===========================================================================
class TestTrailingCommaFix:
    """Trailing comma in JSON is handled gracefully."""

    def test_正常系_末尾カンマのJSONを修正して読める(self, tmp_path: Path) -> None:
        record = _make_transcript_record()
        source_dir = tmp_path / "source"
        output_dir = tmp_path / "output"
        mapping_path = tmp_path / "ticker_mapping.json"

        # Write JSON with trailing comma manually
        source_dir.mkdir(parents=True, exist_ok=True)
        json_str = json.dumps({"2046251": [record]}, ensure_ascii=False)
        # Insert trailing comma before closing bracket
        # e.g. ...}] -> ...},]
        json_with_trailing = json_str.replace("}]}", "},]}")
        filepath = source_dir / "list_transcript_2015-01.json"
        filepath.write_text(json_with_trailing)
        _write_ticker_mapping(mapping_path, {})

        parser = TranscriptParser(source_dir, output_dir, mapping_path)
        result = parser.parse_all_months()

        assert result.success_count == 1


# ===========================================================================
# 32767 character truncation detection tests
# ===========================================================================
class TestTruncationDetection:
    """32767-character truncation is detected and recorded in metadata."""

    def test_正常系_32767文字以下はtruncatedがFalse(self, tmp_path: Path) -> None:
        record = _make_transcript_record(total_characters=1000.0)
        source_dir = tmp_path / "source"
        output_dir = tmp_path / "output"
        mapping_path = tmp_path / "ticker_mapping.json"
        _write_source_json(
            source_dir, "list_transcript_2015-01.json", {"2046251": [record]}
        )
        _write_ticker_mapping(mapping_path, {})

        parser = TranscriptParser(source_dir, output_dir, mapping_path)
        parser.parse_all_months()

        output_files = list(output_dir.rglob("*.json"))
        output_data = json.loads(output_files[0].read_text())
        assert output_data["metadata"]["is_truncated"] is False

    def test_正常系_テキストがちょうど32767文字でtruncatedがTrue(
        self, tmp_path: Path
    ) -> None:
        # Create text that is exactly 32767 chars in text2 or text4
        long_content = "x" * 32700
        text2 = f"【プレゼン: CEO (Executives)】\n{long_content}"
        record = _make_transcript_record(
            text2=text2,
            text4="",
            total_characters=32767.0,
        )
        source_dir = tmp_path / "source"
        output_dir = tmp_path / "output"
        mapping_path = tmp_path / "ticker_mapping.json"
        _write_source_json(
            source_dir, "list_transcript_2015-01.json", {"2046251": [record]}
        )
        _write_ticker_mapping(mapping_path, {})

        parser = TranscriptParser(source_dir, output_dir, mapping_path)
        parser.parse_all_months()

        output_files = list(output_dir.rglob("*.json"))
        output_data = json.loads(output_files[0].read_text())
        assert output_data["metadata"]["is_truncated"] is True

    def test_正常系_text2が32767文字でtruncated検出(self, tmp_path: Path) -> None:
        # Build text2 so that total_characters field equals TRUNCATION_THRESHOLD
        tag_prefix = "【プレゼン: CEO (Executives)】\n"
        filler_len = 32767 - len(tag_prefix)
        text2 = f"{tag_prefix}{'a' * filler_len}"
        record = _make_transcript_record(
            text2=text2,
            text4="",
            total_characters=32767.0,
        )
        source_dir = tmp_path / "source"
        output_dir = tmp_path / "output"
        mapping_path = tmp_path / "ticker_mapping.json"
        _write_source_json(
            source_dir, "list_transcript_2015-01.json", {"2046251": [record]}
        )
        _write_ticker_mapping(mapping_path, {})

        parser = TranscriptParser(source_dir, output_dir, mapping_path)
        parser.parse_all_months()

        output_files = list(output_dir.rglob("*.json"))
        output_data = json.loads(output_files[0].read_text())
        # Truncation is detected via total_characters field
        assert output_data["metadata"]["is_truncated"] is True


# ===========================================================================
# Output format tests
# ===========================================================================
class TestOutputFormat:
    """Output file format and directory structure are correct."""

    def test_正常系_出力パスが正しい形式(self, tmp_path: Path) -> None:
        record = _make_transcript_record()
        source_dir = tmp_path / "source"
        output_dir = tmp_path / "output"
        mapping_path = tmp_path / "ticker_mapping.json"
        _write_source_json(
            source_dir, "list_transcript_2015-01.json", {"2046251": [record]}
        )
        _write_ticker_mapping(mapping_path, {})

        parser = TranscriptParser(source_dir, output_dir, mapping_path)
        parser.parse_all_months()

        expected_file = output_dir / "AAPL" / "201501_earnings_call.json"
        assert expected_file.exists()

    def test_正常系_出力JSONに必要なフィールドが含まれる(self, tmp_path: Path) -> None:
        record = _make_transcript_record()
        source_dir = tmp_path / "source"
        output_dir = tmp_path / "output"
        mapping_path = tmp_path / "ticker_mapping.json"
        _write_source_json(
            source_dir, "list_transcript_2015-01.json", {"2046251": [record]}
        )
        _write_ticker_mapping(mapping_path, {})

        parser = TranscriptParser(source_dir, output_dir, mapping_path)
        parser.parse_all_months()

        output_file = output_dir / "AAPL" / "201501_earnings_call.json"
        output_data = json.loads(output_file.read_text())

        assert "metadata" in output_data
        assert "sections" in output_data
        metadata = output_data["metadata"]
        assert metadata["ticker"] == "AAPL"
        assert "event_date" in metadata
        assert "fiscal_quarter" in metadata
        assert "is_truncated" in metadata

    def test_正常系_セクションに必要なフィールドが含まれる(
        self, tmp_path: Path
    ) -> None:
        record = _make_transcript_record()
        source_dir = tmp_path / "source"
        output_dir = tmp_path / "output"
        mapping_path = tmp_path / "ticker_mapping.json"
        _write_source_json(
            source_dir, "list_transcript_2015-01.json", {"2046251": [record]}
        )
        _write_ticker_mapping(mapping_path, {})

        parser = TranscriptParser(source_dir, output_dir, mapping_path)
        parser.parse_all_months()

        output_file = output_dir / "AAPL" / "201501_earnings_call.json"
        output_data = json.loads(output_file.read_text())
        for section in output_data["sections"]:
            assert "speaker" in section
            assert "role" in section
            assert "section_type" in section
            assert "content" in section


# ===========================================================================
# ParseResult tests
# ===========================================================================
class TestParseResult:
    """ParseResult correctly tracks parsing statistics."""

    def test_正常系_成功と失敗がカウントされる(self, tmp_path: Path) -> None:
        record = _make_transcript_record()
        source_dir = tmp_path / "source"
        output_dir = tmp_path / "output"
        mapping_path = tmp_path / "ticker_mapping.json"
        _write_source_json(
            source_dir, "list_transcript_2015-01.json", {"2046251": [record]}
        )
        _write_ticker_mapping(mapping_path, {})

        parser = TranscriptParser(source_dir, output_dir, mapping_path)
        result = parser.parse_all_months()

        assert isinstance(result, ParseResult)
        assert result.success_count >= 1
        assert result.total_count >= 1
        assert result.error_count == 0

    def test_エッジケース_空のソースディレクトリで結果が0(self, tmp_path: Path) -> None:
        source_dir = tmp_path / "source"
        source_dir.mkdir(parents=True, exist_ok=True)
        output_dir = tmp_path / "output"
        mapping_path = tmp_path / "ticker_mapping.json"
        _write_ticker_mapping(mapping_path, {})

        parser = TranscriptParser(source_dir, output_dir, mapping_path)
        result = parser.parse_all_months()

        assert result.total_count == 0
        assert result.success_count == 0
        assert result.error_count == 0


# ===========================================================================
# Multiple months tests
# ===========================================================================
class TestMultipleMonths:
    """Processing multiple month files works correctly."""

    def test_正常系_複数月のファイルを処理できる(self, tmp_path: Path) -> None:
        record_jan = _make_transcript_record(
            transcript_id=100001.0,
            event_date="2015-01-28T00:00:00.000",
            calendar_month=1.0,
        )
        record_apr = _make_transcript_record(
            transcript_id=100002.0,
            event_date="2015-04-28T00:00:00.000",
            calendar_month=4.0,
        )
        source_dir = tmp_path / "source"
        output_dir = tmp_path / "output"
        mapping_path = tmp_path / "ticker_mapping.json"
        _write_source_json(
            source_dir, "list_transcript_2015-01.json", {"2046251": [record_jan]}
        )
        _write_source_json(
            source_dir, "list_transcript_2015-04.json", {"2046251": [record_apr]}
        )
        _write_ticker_mapping(mapping_path, {})

        parser = TranscriptParser(source_dir, output_dir, mapping_path)
        result = parser.parse_all_months()

        assert result.success_count == 2
        assert (output_dir / "AAPL" / "201501_earnings_call.json").exists()
        assert (output_dir / "AAPL" / "201504_earnings_call.json").exists()


# ===========================================================================
# Edge case tests
# ===========================================================================
class TestEdgeCases:
    """Edge case handling."""

    def test_エッジケース_text2とtext4が空文字の場合スキップされる(
        self, tmp_path: Path
    ) -> None:
        record = _make_transcript_record(text2="", text4="")
        source_dir = tmp_path / "source"
        output_dir = tmp_path / "output"
        mapping_path = tmp_path / "ticker_mapping.json"
        _write_source_json(
            source_dir, "list_transcript_2015-01.json", {"2046251": [record]}
        )
        _write_ticker_mapping(mapping_path, {})

        parser = TranscriptParser(source_dir, output_dir, mapping_path)
        result = parser.parse_all_months()

        # Empty transcripts should be skipped
        assert result.success_count == 0

    def test_エッジケース_text2がNoneの場合スキップされる(self, tmp_path: Path) -> None:
        record = _make_transcript_record(text2="", text4="")
        record["transcript_text2"] = None
        record["transcript_text4"] = None
        source_dir = tmp_path / "source"
        output_dir = tmp_path / "output"
        mapping_path = tmp_path / "ticker_mapping.json"
        _write_source_json(
            source_dir, "list_transcript_2015-01.json", {"2046251": [record]}
        )
        _write_ticker_mapping(mapping_path, {})

        parser = TranscriptParser(source_dir, output_dir, mapping_path)
        result = parser.parse_all_months()

        assert result.success_count == 0

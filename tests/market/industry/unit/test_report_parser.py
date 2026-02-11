"""Unit tests for market.industry.downloaders.report_parser module.

Tests cover PDF text extraction (pymupdf), HTML text extraction (trafilatura),
and metadata extraction (title, author, date).
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from market.industry.downloaders.report_parser import ReportParser
from market.industry.types import ParsedContent, ReportMetadata


class TestReportParserInit:
    """Tests for ReportParser initialization."""

    def test_正常系_デフォルト設定で初期化できる(self) -> None:
        parser = ReportParser()
        assert parser.min_text_length == 100


class TestReportParserPDF:
    """Tests for PDF text extraction."""

    @pytest.fixture()
    def parser(self) -> ReportParser:
        return ReportParser()

    def test_正常系_PDFからテキストを抽出できる(
        self, parser: ReportParser, tmp_path: Path
    ) -> None:
        # Create a mock PDF file path
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"%PDF-1.4 dummy")

        mock_doc = MagicMock()
        mock_page = MagicMock()
        mock_page.get_text.return_value = (
            "This is extracted text from the PDF document. " * 10
        )
        mock_doc.__iter__ = MagicMock(return_value=iter([mock_page]))
        mock_doc.__len__ = MagicMock(return_value=1)
        mock_doc.metadata = {
            "title": "Test Report",
            "author": "John Doe",
            "creationDate": "D:20260115120000",
        }
        mock_doc.close = MagicMock()

        with patch("market.industry.downloaders.report_parser.pymupdf") as mock_pymupdf:
            mock_pymupdf.open.return_value = mock_doc

            result = parser.parse_pdf(pdf_path)

        assert result.text is not None
        assert len(result.text) > 0
        assert result.source_format == "pdf"
        assert result.page_count == 1

    def test_正常系_PDFメタデータを抽出できる(
        self, parser: ReportParser, tmp_path: Path
    ) -> None:
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"%PDF-1.4 dummy")

        mock_doc = MagicMock()
        mock_page = MagicMock()
        mock_page.get_text.return_value = "Sufficient text content for testing. " * 10
        mock_doc.__iter__ = MagicMock(return_value=iter([mock_page]))
        mock_doc.__len__ = MagicMock(return_value=1)
        mock_doc.metadata = {
            "title": "Industry Analysis Report",
            "author": "McKinsey & Company",
            "creationDate": "D:20260115120000+00'00'",
        }
        mock_doc.close = MagicMock()

        with patch("market.industry.downloaders.report_parser.pymupdf") as mock_pymupdf:
            mock_pymupdf.open.return_value = mock_doc

            result = parser.parse_pdf(pdf_path)

        assert result.metadata is not None
        assert result.metadata.title == "Industry Analysis Report"
        assert result.metadata.author == "McKinsey & Company"

    def test_正常系_複数ページPDFのテキストを結合できる(
        self, parser: ReportParser, tmp_path: Path
    ) -> None:
        pdf_path = tmp_path / "multi_page.pdf"
        pdf_path.write_bytes(b"%PDF-1.4 dummy")

        mock_page1 = MagicMock()
        mock_page1.get_text.return_value = "Page 1 content. " * 10
        mock_page2 = MagicMock()
        mock_page2.get_text.return_value = "Page 2 content. " * 10

        mock_doc = MagicMock()
        mock_doc.__iter__ = MagicMock(return_value=iter([mock_page1, mock_page2]))
        mock_doc.__len__ = MagicMock(return_value=2)
        mock_doc.metadata = {}
        mock_doc.close = MagicMock()

        with patch("market.industry.downloaders.report_parser.pymupdf") as mock_pymupdf:
            mock_pymupdf.open.return_value = mock_doc

            result = parser.parse_pdf(pdf_path)

        assert result.page_count == 2
        assert "Page 1" in result.text
        assert "Page 2" in result.text

    def test_異常系_PDFファイルが存在しない場合FileNotFoundError(
        self, parser: ReportParser
    ) -> None:
        with pytest.raises(FileNotFoundError):
            parser.parse_pdf(Path("/nonexistent/report.pdf"))

    def test_異常系_破損PDFでエラーを返す(
        self, parser: ReportParser, tmp_path: Path
    ) -> None:
        pdf_path = tmp_path / "corrupt.pdf"
        pdf_path.write_bytes(b"not a valid pdf")

        with patch("market.industry.downloaders.report_parser.pymupdf") as mock_pymupdf:
            mock_pymupdf.open.side_effect = RuntimeError("Cannot open document")

            with pytest.raises(RuntimeError, match="Cannot open document"):
                parser.parse_pdf(pdf_path)

    def test_エッジケース_テキストが空のPDFで空文字を返す(
        self, parser: ReportParser, tmp_path: Path
    ) -> None:
        pdf_path = tmp_path / "empty_text.pdf"
        pdf_path.write_bytes(b"%PDF-1.4 dummy")

        mock_page = MagicMock()
        mock_page.get_text.return_value = ""

        mock_doc = MagicMock()
        mock_doc.__iter__ = MagicMock(return_value=iter([mock_page]))
        mock_doc.__len__ = MagicMock(return_value=1)
        mock_doc.metadata = {}
        mock_doc.close = MagicMock()

        with patch("market.industry.downloaders.report_parser.pymupdf") as mock_pymupdf:
            mock_pymupdf.open.return_value = mock_doc

            result = parser.parse_pdf(pdf_path)

        assert result.text == ""
        assert result.page_count == 1


class TestReportParserHTML:
    """Tests for HTML text extraction via trafilatura."""

    @pytest.fixture()
    def parser(self) -> ReportParser:
        return ReportParser()

    def test_正常系_HTMLからテキストを抽出できる(self, parser: ReportParser) -> None:
        html_content = """
        <html>
        <head><title>Market Analysis</title></head>
        <body>
        <article>
            <h1>Semiconductor Industry Outlook 2026</h1>
            <p>The semiconductor industry is expected to grow significantly
            in the coming years driven by AI demand and advanced packaging
            technologies. Major players include NVIDIA, AMD, and Intel.</p>
        </article>
        </body>
        </html>
        """

        with patch(
            "market.industry.downloaders.report_parser.trafilatura_extract"
        ) as mock_extract:
            mock_extract.return_value = (
                "Semiconductor Industry Outlook 2026\n\n"
                "The semiconductor industry is expected to grow significantly "
                "in the coming years driven by AI demand and advanced packaging "
                "technologies. Major players include NVIDIA, AMD, and Intel."
            )

            result = parser.parse_html(html_content)

        assert result.text is not None
        assert len(result.text) > 0
        assert result.source_format == "html"

    def test_正常系_HTMLメタデータを抽出できる(self, parser: ReportParser) -> None:
        html_content = """
        <html>
        <head>
            <title>Industry Report</title>
            <meta name="author" content="Goldman Sachs Research">
            <meta name="date" content="2026-01-15">
        </head>
        <body><p>Content here.</p></body>
        </html>
        """

        with patch(
            "market.industry.downloaders.report_parser.trafilatura_extract"
        ) as mock_extract:
            mock_extract.return_value = "Content here."

            with patch(
                "market.industry.downloaders.report_parser.trafilatura_extract_metadata"
            ) as mock_meta:
                mock_meta_result = MagicMock()
                mock_meta_result.title = "Industry Report"
                mock_meta_result.author = "Goldman Sachs Research"
                mock_meta_result.date = "2026-01-15"
                mock_meta.return_value = mock_meta_result

                result = parser.parse_html(html_content)

        assert result.metadata is not None
        assert result.metadata.title == "Industry Report"
        assert result.metadata.author == "Goldman Sachs Research"

    def test_異常系_trafilaturaが抽出失敗でNoneを返す場合(
        self, parser: ReportParser
    ) -> None:
        html_content = "<html><body></body></html>"

        with patch(
            "market.industry.downloaders.report_parser.trafilatura_extract"
        ) as mock_extract:
            mock_extract.return_value = None

            result = parser.parse_html(html_content)

        assert result.text == ""
        assert result.source_format == "html"

    def test_エッジケース_空のHTMLで空文字を返す(self, parser: ReportParser) -> None:
        with patch(
            "market.industry.downloaders.report_parser.trafilatura_extract"
        ) as mock_extract:
            mock_extract.return_value = None

            result = parser.parse_html("")

        assert result.text == ""


class TestReportParserMetadata:
    """Tests for metadata extraction helpers."""

    @pytest.fixture()
    def parser(self) -> ReportParser:
        return ReportParser()

    def test_正常系_PDF日付文字列をdatetimeに変換できる(
        self, parser: ReportParser
    ) -> None:
        # Standard PDF date format: D:YYYYMMDDHHmmSS
        result = parser._parse_pdf_date("D:20260115120000")
        assert result is not None
        assert result.year == 2026
        assert result.month == 1
        assert result.day == 15

    def test_正常系_タイムゾーン付きPDF日付文字列を変換できる(
        self, parser: ReportParser
    ) -> None:
        result = parser._parse_pdf_date("D:20260115120000+00'00'")
        assert result is not None
        assert result.year == 2026

    def test_エッジケース_不正な日付文字列でNoneを返す(
        self, parser: ReportParser
    ) -> None:
        result = parser._parse_pdf_date("invalid date")
        assert result is None

    def test_エッジケース_空の日付文字列でNoneを返す(
        self, parser: ReportParser
    ) -> None:
        result = parser._parse_pdf_date("")
        assert result is None

    def test_エッジケース_Noneの日付でNoneを返す(self, parser: ReportParser) -> None:
        result = parser._parse_pdf_date(None)
        assert result is None

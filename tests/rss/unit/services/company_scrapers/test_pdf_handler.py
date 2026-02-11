"""Unit tests for PdfHandler (PDF link detection + download)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from rss.services.company_scrapers.pdf_handler import (
    PdfHandler,
    find_pdf_links,
    is_pdf_url,
)
from rss.services.company_scrapers.types import PdfMetadata

# ---------------------------------------------------------------------------
# is_pdf_url
# ---------------------------------------------------------------------------


class TestIsPdfUrl:
    """Tests for is_pdf_url function."""

    def test_正常系_pdf拡張子のURLをPDFと判定する(self) -> None:
        assert is_pdf_url("https://example.com/report.pdf") is True

    def test_正常系_大文字PDF拡張子のURLをPDFと判定する(self) -> None:
        assert is_pdf_url("https://example.com/REPORT.PDF") is True

    def test_正常系_クエリパラメータ付きPDF_URLを判定する(self) -> None:
        assert is_pdf_url("https://example.com/report.pdf?token=abc") is True

    def test_正常系_フラグメント付きPDF_URLを判定する(self) -> None:
        assert is_pdf_url("https://example.com/report.pdf#page=1") is True

    def test_正常系_パスにPDF拡張子がないURLは非PDFと判定する(self) -> None:
        assert is_pdf_url("https://example.com/article") is False

    def test_正常系_HTML拡張子のURLは非PDFと判定する(self) -> None:
        assert is_pdf_url("https://example.com/page.html") is False

    def test_正常系_pdfを含むがpdf拡張子でないURLは非PDFと判定する(self) -> None:
        assert is_pdf_url("https://example.com/pdf-viewer") is False

    def test_エッジケース_空URLは非PDFと判定する(self) -> None:
        assert is_pdf_url("") is False


# ---------------------------------------------------------------------------
# find_pdf_links
# ---------------------------------------------------------------------------


class TestFindPdfLinks:
    """Tests for find_pdf_links function."""

    def test_正常系_aタグのhrefからPDFリンクを検出する(self) -> None:
        html = """
        <html>
        <body>
            <a href="https://example.com/report.pdf">Download PDF</a>
            <a href="https://example.com/page.html">Read more</a>
        </body>
        </html>
        """
        links = find_pdf_links(html)
        assert links == ["https://example.com/report.pdf"]

    def test_正常系_複数のPDFリンクを検出する(self) -> None:
        html = """
        <html>
        <body>
            <a href="https://example.com/report.pdf">Report</a>
            <a href="https://example.com/slides.pdf">Slides</a>
            <a href="https://example.com/page.html">Page</a>
        </body>
        </html>
        """
        links = find_pdf_links(html)
        assert len(links) == 2
        assert "https://example.com/report.pdf" in links
        assert "https://example.com/slides.pdf" in links

    def test_正常系_PDFリンクがない場合は空リストを返す(self) -> None:
        html = """
        <html>
        <body>
            <a href="https://example.com/page.html">Page</a>
        </body>
        </html>
        """
        links = find_pdf_links(html)
        assert links == []

    def test_正常系_大文字PDF拡張子のリンクも検出する(self) -> None:
        html = """
        <html>
        <body>
            <a href="https://example.com/REPORT.PDF">Report</a>
        </body>
        </html>
        """
        links = find_pdf_links(html)
        assert links == ["https://example.com/REPORT.PDF"]

    def test_正常系_重複リンクを除外する(self) -> None:
        html = """
        <html>
        <body>
            <a href="https://example.com/report.pdf">Download 1</a>
            <a href="https://example.com/report.pdf">Download 2</a>
        </body>
        </html>
        """
        links = find_pdf_links(html)
        assert links == ["https://example.com/report.pdf"]

    def test_正常系_hrefがないaタグをスキップする(self) -> None:
        html = """
        <html>
        <body>
            <a name="anchor">Anchor</a>
            <a href="https://example.com/report.pdf">PDF</a>
        </body>
        </html>
        """
        links = find_pdf_links(html)
        assert links == ["https://example.com/report.pdf"]

    def test_エッジケース_空HTMLで空リストを返す(self) -> None:
        links = find_pdf_links("")
        assert links == []

    def test_エッジケース_不正なHTMLでもクラッシュしない(self) -> None:
        html = "<html><body><a href='test.pdf'>PDF</a>"
        links = find_pdf_links(html)
        assert links == ["test.pdf"]


# ---------------------------------------------------------------------------
# PdfHandler.download
# ---------------------------------------------------------------------------


class TestPdfHandlerDownload:
    """Tests for PdfHandler.download method."""

    @pytest.fixture
    def handler(self, tmp_path: Path) -> PdfHandler:
        """Create PdfHandler with temporary base directory."""
        return PdfHandler(base_dir=tmp_path)

    @pytest.mark.asyncio
    async def test_正常系_PDFをダウンロードしてPdfMetadataを返す(
        self,
        handler: PdfHandler,
        tmp_path: Path,
    ) -> None:
        pdf_content = b"%PDF-1.4 fake pdf content"
        url = "https://example.com/reports/annual-report.pdf"

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = pdf_content
        mock_response.headers = {"content-type": "application/pdf"}
        mock_response.raise_for_status = MagicMock()

        with patch(
            "rss.services.company_scrapers.pdf_handler.httpx.AsyncClient"
        ) as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_cls.return_value = mock_client

            result = await handler.download(url, "nvidia")

        assert isinstance(result, PdfMetadata)
        assert result.url == url
        assert result.company_key == "nvidia"
        assert result.filename == "annual-report.pdf"
        assert Path(result.local_path).exists()
        assert Path(result.local_path).read_bytes() == pdf_content

    @pytest.mark.asyncio
    async def test_正常系_保存先ディレクトリが自動作成される(
        self,
        handler: PdfHandler,
        tmp_path: Path,
    ) -> None:
        pdf_content = b"%PDF-1.4 test"
        url = "https://example.com/doc.pdf"

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = pdf_content
        mock_response.headers = {"content-type": "application/pdf"}
        mock_response.raise_for_status = MagicMock()

        with patch(
            "rss.services.company_scrapers.pdf_handler.httpx.AsyncClient"
        ) as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_cls.return_value = mock_client

            result = await handler.download(url, "deepmind")

        # Verify company directory was created
        company_dir = tmp_path / "deepmind"
        assert company_dir.exists()
        assert Path(result.local_path).parent == company_dir

    @pytest.mark.asyncio
    async def test_正常系_ファイル名に日付プレフィックスが付く(
        self,
        handler: PdfHandler,
    ) -> None:
        pdf_content = b"%PDF-1.4 test"
        url = "https://example.com/report.pdf"

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = pdf_content
        mock_response.headers = {"content-type": "application/pdf"}
        mock_response.raise_for_status = MagicMock()

        with patch(
            "rss.services.company_scrapers.pdf_handler.httpx.AsyncClient"
        ) as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_cls.return_value = mock_client

            result = await handler.download(url, "openai")

        filename = Path(result.local_path).name
        # Should have format: YYYY-MM-DD_report.pdf
        assert filename.endswith("_report.pdf")
        # Date portion should be 10 characters (YYYY-MM-DD)
        date_part = filename.split("_")[0]
        assert len(date_part) == 10

    @pytest.mark.asyncio
    async def test_異常系_HTTPエラーで例外を送出する(
        self,
        handler: PdfHandler,
    ) -> None:
        url = "https://example.com/missing.pdf"

        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.raise_for_status = MagicMock(
            side_effect=httpx.HTTPStatusError(
                "404 Not Found",
                request=MagicMock(),
                response=mock_response,
            ),
        )

        with patch(
            "rss.services.company_scrapers.pdf_handler.httpx.AsyncClient"
        ) as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_cls.return_value = mock_client

            with pytest.raises(httpx.HTTPStatusError):
                await handler.download(url, "test_company")

    @pytest.mark.asyncio
    async def test_正常系_クエリパラメータ付きURLからファイル名を正しく抽出する(
        self,
        handler: PdfHandler,
    ) -> None:
        pdf_content = b"%PDF-1.4 test"
        url = "https://example.com/report.pdf?token=abc123&page=1"

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = pdf_content
        mock_response.headers = {"content-type": "application/pdf"}
        mock_response.raise_for_status = MagicMock()

        with patch(
            "rss.services.company_scrapers.pdf_handler.httpx.AsyncClient"
        ) as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_cls.return_value = mock_client

            result = await handler.download(url, "meta")

        assert result.filename == "report.pdf"

    @pytest.mark.asyncio
    async def test_正常系_URLにファイル名がない場合はデフォルト名を使う(
        self,
        handler: PdfHandler,
    ) -> None:
        pdf_content = b"%PDF-1.4 test"
        url = "https://example.com/download/"

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = pdf_content
        mock_response.headers = {"content-type": "application/pdf"}
        mock_response.raise_for_status = MagicMock()

        with patch(
            "rss.services.company_scrapers.pdf_handler.httpx.AsyncClient"
        ) as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_cls.return_value = mock_client

            result = await handler.download(url, "test_co")

        assert result.filename == "document.pdf"


# ---------------------------------------------------------------------------
# PdfHandler default base_dir
# ---------------------------------------------------------------------------


class TestPdfHandlerDefaultBaseDir:
    """Tests for PdfHandler default base directory."""

    def test_正常系_デフォルトのbase_dirが設定される(self) -> None:
        handler = PdfHandler()
        assert "data/raw/ai-research/pdfs" in str(handler.base_dir)

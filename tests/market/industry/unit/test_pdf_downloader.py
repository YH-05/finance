"""Unit tests for market.industry.downloaders.pdf_downloader module.

Tests cover PDF downloading with size limits, hash-based deduplication,
error handling, and file storage.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from market.industry.downloaders.pdf_downloader import (
    DEFAULT_MAX_FILE_SIZE,
    PDFDownloader,
)
from market.industry.types import DownloadResult


class TestPDFDownloaderInit:
    """Tests for PDFDownloader initialization."""

    def test_正常系_デフォルト設定で初期化できる(self, tmp_path: Path) -> None:
        downloader = PDFDownloader(download_dir=tmp_path)
        assert downloader.download_dir == tmp_path
        assert downloader.max_file_size == DEFAULT_MAX_FILE_SIZE

    def test_正常系_カスタム設定で初期化できる(self, tmp_path: Path) -> None:
        downloader = PDFDownloader(
            download_dir=tmp_path,
            max_file_size=10 * 1024 * 1024,
            timeout=60.0,
        )
        assert downloader.max_file_size == 10 * 1024 * 1024
        assert downloader.timeout == 60.0

    def test_正常系_ダウンロードディレクトリが自動作成される(
        self, tmp_path: Path
    ) -> None:
        download_dir = tmp_path / "new_dir" / "pdfs"
        PDFDownloader(download_dir=download_dir)
        assert download_dir.exists()


class TestPDFDownloaderDownload:
    """Tests for PDFDownloader.download method."""

    @pytest.fixture()
    def downloader(self, tmp_path: Path) -> PDFDownloader:
        return PDFDownloader(download_dir=tmp_path)

    @pytest.fixture()
    def sample_pdf_bytes(self) -> bytes:
        """Minimal PDF bytes for testing."""
        return b"%PDF-1.4 test content for hashing purposes"

    @pytest.mark.asyncio()
    async def test_正常系_PDFをダウンロードして保存できる(
        self, downloader: PDFDownloader, sample_pdf_bytes: bytes, tmp_path: Path
    ) -> None:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = sample_pdf_bytes
        mock_response.headers = {"content-type": "application/pdf"}

        with patch.object(
            downloader, "_fetch_content", new_callable=AsyncMock
        ) as mock_fetch:
            mock_fetch.return_value = mock_response

            result = await downloader.download("https://example.com/report.pdf")

        assert result.success is True
        assert result.file_path is not None
        assert result.content_hash is not None
        assert result.file_size == len(sample_pdf_bytes)
        assert Path(result.file_path).exists()

    @pytest.mark.asyncio()
    async def test_正常系_SHA256ハッシュが正しく計算される(
        self, downloader: PDFDownloader, sample_pdf_bytes: bytes
    ) -> None:
        expected_hash = hashlib.sha256(sample_pdf_bytes).hexdigest()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = sample_pdf_bytes
        mock_response.headers = {"content-type": "application/pdf"}

        with patch.object(
            downloader, "_fetch_content", new_callable=AsyncMock
        ) as mock_fetch:
            mock_fetch.return_value = mock_response

            result = await downloader.download("https://example.com/report.pdf")

        assert result.content_hash == expected_hash

    @pytest.mark.asyncio()
    async def test_正常系_重複ダウンロードを検出してスキップする(
        self, downloader: PDFDownloader, sample_pdf_bytes: bytes
    ) -> None:
        content_hash = hashlib.sha256(sample_pdf_bytes).hexdigest()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = sample_pdf_bytes
        mock_response.headers = {"content-type": "application/pdf"}

        with patch.object(
            downloader, "_fetch_content", new_callable=AsyncMock
        ) as mock_fetch:
            mock_fetch.return_value = mock_response

            # First download
            result1 = await downloader.download("https://example.com/report.pdf")
            assert result1.success is True

            # Second download - same content, should be detected as duplicate
            result2 = await downloader.download("https://example.com/report2.pdf")
            assert result2.success is True
            assert result2.is_duplicate is True
            assert result2.content_hash == content_hash

    @pytest.mark.asyncio()
    async def test_異常系_ファイルサイズ制限を超えるとエラー(
        self, tmp_path: Path
    ) -> None:
        downloader = PDFDownloader(
            download_dir=tmp_path,
            max_file_size=100,  # 100 bytes limit
        )
        large_content = b"x" * 200  # 200 bytes

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = large_content
        mock_response.headers = {
            "content-type": "application/pdf",
            "content-length": "200",
        }

        with patch.object(
            downloader, "_fetch_content", new_callable=AsyncMock
        ) as mock_fetch:
            mock_fetch.return_value = mock_response

            result = await downloader.download("https://example.com/large.pdf")

        assert result.success is False
        assert "size" in (result.error_message or "").lower()

    @pytest.mark.asyncio()
    async def test_異常系_HTTP404でエラーを返す(
        self, downloader: PDFDownloader
    ) -> None:
        with patch.object(
            downloader, "_fetch_content", new_callable=AsyncMock
        ) as mock_fetch:
            mock_fetch.side_effect = httpx.HTTPStatusError(
                "Not Found",
                request=MagicMock(),
                response=MagicMock(status_code=404),
            )

            result = await downloader.download("https://example.com/missing.pdf")

        assert result.success is False
        assert result.error_message is not None

    @pytest.mark.asyncio()
    async def test_異常系_ネットワークエラーでエラーを返す(
        self, downloader: PDFDownloader
    ) -> None:
        with patch.object(
            downloader, "_fetch_content", new_callable=AsyncMock
        ) as mock_fetch:
            mock_fetch.side_effect = httpx.ConnectError("Connection refused")

            result = await downloader.download("https://example.com/report.pdf")

        assert result.success is False
        assert result.error_message is not None

    @pytest.mark.asyncio()
    async def test_異常系_タイムアウトでエラーを返す(
        self, downloader: PDFDownloader
    ) -> None:
        with patch.object(
            downloader, "_fetch_content", new_callable=AsyncMock
        ) as mock_fetch:
            mock_fetch.side_effect = httpx.ReadTimeout("Read timed out")

            result = await downloader.download("https://example.com/report.pdf")

        assert result.success is False
        assert result.error_message is not None


class TestPDFDownloaderContentLengthCheck:
    """Tests for Content-Length header pre-check."""

    @pytest.mark.asyncio()
    async def test_正常系_ContentLengthヘッダーで事前にサイズを検証する(
        self, tmp_path: Path
    ) -> None:
        downloader = PDFDownloader(
            download_dir=tmp_path,
            max_file_size=1000,
        )

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"x" * 2000
        mock_response.headers = {
            "content-type": "application/pdf",
            "content-length": "2000",
        }

        with patch.object(
            downloader, "_fetch_content", new_callable=AsyncMock
        ) as mock_fetch:
            mock_fetch.return_value = mock_response

            result = await downloader.download("https://example.com/report.pdf")

        assert result.success is False


class TestPDFDownloaderHashRegistry:
    """Tests for hash-based deduplication registry."""

    def test_正常系_ハッシュを登録して存在確認できる(self, tmp_path: Path) -> None:
        downloader = PDFDownloader(download_dir=tmp_path)
        test_hash = "abc123def456"

        assert downloader.has_hash(test_hash) is False
        downloader.register_hash(test_hash, tmp_path / "test.pdf")
        assert downloader.has_hash(test_hash) is True

    def test_正常系_ハッシュからファイルパスを取得できる(self, tmp_path: Path) -> None:
        downloader = PDFDownloader(download_dir=tmp_path)
        test_hash = "abc123def456"
        file_path = tmp_path / "test.pdf"

        downloader.register_hash(test_hash, file_path)
        assert downloader.get_path_by_hash(test_hash) == file_path

    def test_正常系_未登録ハッシュのパス取得はNone(self, tmp_path: Path) -> None:
        downloader = PDFDownloader(download_dir=tmp_path)
        assert downloader.get_path_by_hash("nonexistent") is None

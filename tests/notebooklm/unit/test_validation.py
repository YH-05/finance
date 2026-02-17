"""Tests for input validation utilities."""

import tempfile
from pathlib import Path

import pytest

from notebooklm.validation import (
    validate_file_path,
    validate_text_input,
    validate_url_input,
)


class TestValidateTextInput:
    """Tests for validate_text_input."""

    def test_正常系_有効なテキストが受け入れられる(self) -> None:
        """Valid text is accepted."""
        text = "This is a normal text input"
        result = validate_text_input(text)
        assert result == text

    def test_異常系_スクリプトタグでValueError(self) -> None:
        """Script tags are rejected."""
        text = "Hello <script>alert('XSS')</script> World"

        with pytest.raises(ValueError, match="script"):
            validate_text_input(text)

    def test_異常系_NULバイトでValueError(self) -> None:
        """NUL bytes are rejected."""
        text = "Hello\x00World"

        with pytest.raises(ValueError, match="NUL"):
            validate_text_input(text)

    def test_異常系_長さ制限超過でValueError(self) -> None:
        """Text exceeding max length is rejected."""
        text = "a" * 2_000_000

        with pytest.raises(ValueError, match="exceeds maximum length"):
            validate_text_input(text)

    def test_異常系_空文字列でValueError(self) -> None:
        """Empty string is rejected by default."""
        with pytest.raises(ValueError, match="empty"):
            validate_text_input("")

    def test_正常系_allow_emptyでtrueの場合空文字列が受け入れられる(self) -> None:
        """Empty string is accepted with allow_empty=True."""
        result = validate_text_input("", allow_empty=True)
        assert result == ""

    def test_正常系_スクリプトタグなしのHTMLが受け入れられる(self) -> None:
        """HTML without script tags is accepted."""
        text = "<p>Hello <b>World</b></p>"
        result = validate_text_input(text)
        assert result == text

    def test_異常系_大文字スクリプトタグでValueError(self) -> None:
        """Case-insensitive script tag detection."""
        text = "Hello <SCRIPT>alert('XSS')</SCRIPT> World"

        with pytest.raises(ValueError, match="script"):
            validate_text_input(text)

    def test_正常系_カスタム長さ制限で受け入れられる(self) -> None:
        """Custom max_length is respected."""
        text = "a" * 100
        result = validate_text_input(text, max_length=200)
        assert result == text

    def test_異常系_カスタム長さ制限超過でValueError(self) -> None:
        """Custom max_length rejects longer text."""
        text = "a" * 201

        with pytest.raises(ValueError, match="exceeds maximum length"):
            validate_text_input(text, max_length=200)


class TestValidateURLInput:
    """Tests for validate_url_input."""

    def test_正常系_有効なHTTPSのURLが受け入れられる(self) -> None:
        """Valid HTTPS URL is accepted."""
        url = "https://example.com/page"
        result = validate_url_input(url)
        assert result == url

    def test_正常系_有効なHTTPのURLが受け入れられる(self) -> None:
        """Valid HTTP URL is accepted."""
        url = "http://example.com/page"
        result = validate_url_input(url)
        assert result == url

    def test_異常系_プライベートIPでValueError(self) -> None:
        """Private IP addresses are rejected."""
        urls = [
            "http://127.0.0.1/",
            "http://10.0.0.1/",
            "http://192.168.1.1/",
            "http://172.16.0.1/",
        ]

        for url in urls:
            with pytest.raises(ValueError, match="private IP"):
                validate_url_input(url)

    def test_異常系_localhostでValueError(self) -> None:
        """Localhost is rejected."""
        urls = [
            "http://localhost/",
            "http://0.0.0.0/",
        ]

        for url in urls:
            with pytest.raises(ValueError, match="localhost"):
                validate_url_input(url)

    def test_異常系_不正なスキームでValueError(self) -> None:
        """Disallowed schemes are rejected."""
        urls = [
            "file:///etc/passwd",
            "javascript:alert('XSS')",
            "ftp://example.com",
        ]

        for url in urls:
            with pytest.raises(ValueError, match="scheme"):
                validate_url_input(url)

    def test_異常系_長さ制限超過でValueError(self) -> None:
        """URL exceeding max length is rejected."""
        url = "https://example.com/" + "a" * 3000

        with pytest.raises(ValueError, match="exceeds maximum length"):
            validate_url_input(url)

    def test_異常系_空URLでValueError(self) -> None:
        """Empty URL is rejected."""
        with pytest.raises(ValueError, match="empty"):
            validate_url_input("")

    def test_正常系_カスタムスキームが受け入れられる(self) -> None:
        """Custom allowed schemes are respected."""
        url = "ftp://example.com/file.txt"
        result = validate_url_input(url, allowed_schemes=["ftp", "sftp"])
        assert result == url


class TestValidateFilePath:
    """Tests for validate_file_path."""

    def test_正常系_有効なファイルパスが受け入れられる(self) -> None:
        """Valid file path is accepted."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name

        try:
            result = validate_file_path(tmp_path)
            assert isinstance(result, Path)
            assert result.exists()
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    def test_異常系_存在しないファイルでFileNotFoundError(self) -> None:
        """Non-existent file is rejected by default."""
        with pytest.raises(FileNotFoundError, match="File not found"):
            validate_file_path("/nonexistent/path/file.txt")

    def test_正常系_must_existがfalseの場合存在しないファイルが受け入れられる(
        self,
    ) -> None:
        """Non-existent file is accepted with must_exist=False."""
        result = validate_file_path(
            "/tmp/nonexistent.txt",
            must_exist=False,
        )
        assert isinstance(result, Path)

    def test_異常系_許可ディレクトリ外でValueError(self) -> None:
        """Path outside allowed directories is rejected."""
        with tempfile.TemporaryDirectory() as tmpdir:
            allowed_dir = Path(tmpdir) / "allowed"
            allowed_dir.mkdir()

            # Create file outside allowed directory
            with tempfile.NamedTemporaryFile(
                dir=tmpdir,
                delete=False,
            ) as tmp:
                tmp_path = tmp.name

            try:
                with pytest.raises(ValueError, match="not in allowed"):
                    validate_file_path(
                        tmp_path,
                        allowed_directories=[str(allowed_dir)],
                    )
            finally:
                Path(tmp_path).unlink(missing_ok=True)

    def test_異常系_空のパスでValueError(self) -> None:
        """Empty path is rejected."""
        with pytest.raises(ValueError, match="empty"):
            validate_file_path("")

    def test_正常系_許可ディレクトリ内のファイルが受け入れられる(self) -> None:
        """File within allowed directory is accepted."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create file inside the allowed directory
            with tempfile.NamedTemporaryFile(
                dir=tmpdir,
                delete=False,
            ) as tmp:
                tmp_path = tmp.name

            try:
                result = validate_file_path(
                    tmp_path,
                    allowed_directories=[tmpdir],
                )
                assert isinstance(result, Path)
                assert result.exists()
            finally:
                Path(tmp_path).unlink(missing_ok=True)

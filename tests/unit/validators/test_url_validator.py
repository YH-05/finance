"""Unit tests for URLValidator."""

import pytest
from rss.exceptions import InvalidURLError
from rss.validators import URLValidator


class TestValidateURL:
    """Tests for validate_url method."""

    def test_valid_http_url(self) -> None:
        """Test that valid HTTP URLs are accepted."""
        validator = URLValidator()
        # Should not raise an exception
        validator.validate_url("http://example.com")
        validator.validate_url("http://example.com/feed")
        validator.validate_url("http://example.com/feed?param=value")

    def test_valid_https_url(self) -> None:
        """Test that valid HTTPS URLs are accepted."""
        validator = URLValidator()
        # Should not raise an exception
        validator.validate_url("https://example.com")
        validator.validate_url("https://example.com/feed")
        validator.validate_url("https://example.com/feed?param=value")

    def test_invalid_ftp_scheme(self) -> None:
        """Test that FTP URLs are rejected with InvalidURLError."""
        validator = URLValidator()
        with pytest.raises(InvalidURLError) as exc_info:
            validator.validate_url("ftp://example.com")
        assert "ftp://example.com" in str(exc_info.value)
        assert "HTTP" in str(exc_info.value) or "HTTPS" in str(exc_info.value)

    def test_invalid_file_scheme(self) -> None:
        """Test that file URLs are rejected with InvalidURLError."""
        validator = URLValidator()
        with pytest.raises(InvalidURLError) as exc_info:
            validator.validate_url("file:///path/to/file")
        assert "file:///path/to/file" in str(exc_info.value)

    def test_invalid_no_scheme(self) -> None:
        """Test that URLs without scheme are rejected with InvalidURLError."""
        validator = URLValidator()
        with pytest.raises(InvalidURLError) as exc_info:
            validator.validate_url("example.com")
        assert "example.com" in str(exc_info.value)

    def test_invalid_empty_url(self) -> None:
        """Test that empty URLs are rejected with InvalidURLError."""
        validator = URLValidator()
        with pytest.raises(InvalidURLError) as exc_info:
            validator.validate_url("")
        assert (
            "empty" in str(exc_info.value).lower()
            or "blank" in str(exc_info.value).lower()
        )

    def test_invalid_mailto_scheme(self) -> None:
        """Test that mailto URLs are rejected with InvalidURLError."""
        validator = URLValidator()
        with pytest.raises(InvalidURLError) as exc_info:
            validator.validate_url("mailto:user@example.com")
        assert "mailto:user@example.com" in str(exc_info.value)


class TestValidateTitle:
    """Tests for validate_title method."""

    def test_valid_title_min_length(self) -> None:
        """Test that title with minimum length (1 char) is accepted."""
        validator = URLValidator()
        # Should not raise an exception
        validator.validate_title("A")

    def test_valid_title_max_length(self) -> None:
        """Test that title with maximum length (200 chars) is accepted."""
        validator = URLValidator()
        title = "A" * 200
        # Should not raise an exception
        validator.validate_title(title)

    def test_valid_title_medium_length(self) -> None:
        """Test that title with medium length is accepted."""
        validator = URLValidator()
        # Should not raise an exception
        validator.validate_title("Valid Title")
        validator.validate_title("A" * 100)

    def test_invalid_title_empty(self) -> None:
        """Test that empty title raises ValueError."""
        validator = URLValidator()
        with pytest.raises(ValueError) as exc_info:
            validator.validate_title("")
        assert "title" in str(exc_info.value).lower()
        assert "1" in str(exc_info.value)
        assert "200" in str(exc_info.value)

    def test_invalid_title_too_long(self) -> None:
        """Test that title longer than 200 chars raises ValueError."""
        validator = URLValidator()
        title = "A" * 201
        with pytest.raises(ValueError) as exc_info:
            validator.validate_title(title)
        assert "title" in str(exc_info.value).lower()
        assert "200" in str(exc_info.value)
        assert "201" in str(exc_info.value)

    def test_invalid_title_whitespace_only(self) -> None:
        """Test that whitespace-only title raises ValueError."""
        validator = URLValidator()
        with pytest.raises(ValueError) as exc_info:
            validator.validate_title("   ")
        assert "title" in str(exc_info.value).lower()


class TestValidateCategory:
    """Tests for validate_category method."""

    def test_valid_category_min_length(self) -> None:
        """Test that category with minimum length (1 char) is accepted."""
        validator = URLValidator()
        # Should not raise an exception
        validator.validate_category("A")

    def test_valid_category_max_length(self) -> None:
        """Test that category with maximum length (50 chars) is accepted."""
        validator = URLValidator()
        category = "A" * 50
        # Should not raise an exception
        validator.validate_category(category)

    def test_valid_category_medium_length(self) -> None:
        """Test that category with medium length is accepted."""
        validator = URLValidator()
        # Should not raise an exception
        validator.validate_category("technology")
        validator.validate_category("A" * 25)

    def test_invalid_category_empty(self) -> None:
        """Test that empty category raises ValueError."""
        validator = URLValidator()
        with pytest.raises(ValueError) as exc_info:
            validator.validate_category("")
        assert "category" in str(exc_info.value).lower()
        assert "1" in str(exc_info.value)
        assert "50" in str(exc_info.value)

    def test_invalid_category_too_long(self) -> None:
        """Test that category longer than 50 chars raises ValueError."""
        validator = URLValidator()
        category = "A" * 51
        with pytest.raises(ValueError) as exc_info:
            validator.validate_category(category)
        assert "category" in str(exc_info.value).lower()
        assert "50" in str(exc_info.value)
        assert "51" in str(exc_info.value)

    def test_invalid_category_whitespace_only(self) -> None:
        """Test that whitespace-only category raises ValueError."""
        validator = URLValidator()
        with pytest.raises(ValueError) as exc_info:
            validator.validate_category("   ")
        assert "category" in str(exc_info.value).lower()

"""Tests for market_analysis.utils.validators module."""

from datetime import datetime

import pytest

from market_analysis.errors import ValidationError
from market_analysis.utils.validators import Validator, validate_fetch_options


class TestValidatorSymbol:
    """Tests for symbol validation."""

    def test_valid_symbol(self) -> None:
        """Test valid symbols are accepted."""
        assert Validator.validate_symbol("AAPL") == "AAPL"
        assert Validator.validate_symbol("aapl") == "AAPL"  # Normalized to uppercase
        assert Validator.validate_symbol("BRK.B") == "BRK.B"
        assert Validator.validate_symbol("^GSPC") == "^GSPC"
        assert Validator.validate_symbol("EUR-USD") == "EUR-USD"

    def test_empty_symbol_raises(self) -> None:
        """Test empty symbol raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            Validator.validate_symbol("")
        assert "cannot be empty" in str(exc_info.value)

    def test_invalid_symbol_raises(self) -> None:
        """Test invalid symbol characters raise ValidationError."""
        with pytest.raises(ValidationError):
            Validator.validate_symbol("AAPL@#$")

    def test_too_long_symbol_raises(self) -> None:
        """Test too long symbol raises ValidationError."""
        with pytest.raises(ValidationError):
            Validator.validate_symbol("A" * 20)


class TestValidatorSymbols:
    """Tests for symbol list validation."""

    def test_valid_symbols(self) -> None:
        """Test valid symbol list."""
        symbols = Validator.validate_symbols(["aapl", "googl", "msft"])
        assert symbols == ["AAPL", "GOOGL", "MSFT"]

    def test_empty_list_raises(self) -> None:
        """Test empty symbol list raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            Validator.validate_symbols([])
        assert "cannot be empty" in str(exc_info.value)

    def test_invalid_symbol_in_list_raises(self) -> None:
        """Test invalid symbol in list raises ValidationError."""
        with pytest.raises(ValidationError):
            Validator.validate_symbols(["AAPL", "", "MSFT"])


class TestValidatorDate:
    """Tests for date validation."""

    def test_parse_date_string(self) -> None:
        """Test parsing date strings."""
        result = Validator.parse_date("2024-01-15")
        assert result == datetime(2024, 1, 15, 0, 0)

    def test_parse_date_various_formats(self) -> None:
        """Test parsing various date formats."""
        assert Validator.parse_date("2024-01-15") == datetime(2024, 1, 15)
        assert Validator.parse_date("2024/01/15") == datetime(2024, 1, 15)
        assert Validator.parse_date("20240115") == datetime(2024, 1, 15)

    def test_parse_date_none(self) -> None:
        """Test parsing None returns None."""
        assert Validator.parse_date(None) is None

    def test_parse_date_datetime_passthrough(self) -> None:
        """Test datetime objects pass through."""
        dt = datetime(2024, 1, 15, 12, 30)
        assert Validator.parse_date(dt) == dt

    def test_parse_invalid_date_raises(self) -> None:
        """Test invalid date raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            Validator.parse_date("not-a-date")
        assert "Cannot parse date" in str(exc_info.value)


class TestValidatorDateRange:
    """Tests for date range validation."""

    def test_valid_date_range(self) -> None:
        """Test valid date range."""
        start, end = Validator.validate_date_range("2024-01-01", "2024-12-31")
        assert start == datetime(2024, 1, 1)
        assert end == datetime(2024, 12, 31)

    def test_date_range_with_none(self) -> None:
        """Test date range with None values."""
        start, end = Validator.validate_date_range(None, "2024-12-31")
        assert start is None
        assert end == datetime(2024, 12, 31)

    def test_invalid_date_range_raises(self) -> None:
        """Test start > end raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            Validator.validate_date_range("2024-12-31", "2024-01-01")
        assert "must be before" in str(exc_info.value)


class TestValidatorPositiveInt:
    """Tests for positive integer validation."""

    def test_valid_positive_int(self) -> None:
        """Test valid positive integer."""
        assert Validator.validate_positive_int(50) == 50

    def test_with_bounds(self) -> None:
        """Test with min/max bounds."""
        assert Validator.validate_positive_int(50, min_value=1, max_value=100) == 50

    def test_below_min_raises(self) -> None:
        """Test value below min raises ValidationError."""
        with pytest.raises(ValidationError):
            Validator.validate_positive_int(0)

    def test_above_max_raises(self) -> None:
        """Test value above max raises ValidationError."""
        with pytest.raises(ValidationError):
            Validator.validate_positive_int(200, max_value=100)


class TestValidatorPositiveFloat:
    """Tests for positive float validation."""

    def test_valid_positive_float(self) -> None:
        """Test valid positive float."""
        assert Validator.validate_positive_float(0.5) == 0.5

    def test_zero_not_allowed(self) -> None:
        """Test zero raises when not allowed."""
        with pytest.raises(ValidationError):
            Validator.validate_positive_float(0.0)

    def test_zero_allowed(self) -> None:
        """Test zero allowed when specified."""
        assert Validator.validate_positive_float(0.0, allow_zero=True) == 0.0


class TestValidatorEnumValue:
    """Tests for enum value validation."""

    def test_valid_enum_value(self) -> None:
        """Test valid enum value."""
        result = Validator.validate_enum_value("daily", ["daily", "weekly", "monthly"])
        assert result == "daily"

    def test_invalid_enum_value_raises(self) -> None:
        """Test invalid enum value raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            Validator.validate_enum_value("hourly", ["daily", "weekly", "monthly"])
        assert "Must be one of" in str(exc_info.value)


class TestValidatorWindowSizes:
    """Tests for window sizes validation."""

    def test_valid_window_sizes(self) -> None:
        """Test valid window sizes."""
        result = Validator.validate_window_sizes([20, 50, 200])
        assert result == [20, 50, 200]

    def test_window_sizes_sorted_deduped(self) -> None:
        """Test window sizes are sorted and deduplicated."""
        result = Validator.validate_window_sizes([200, 20, 50, 20])
        assert result == [20, 50, 200]

    def test_empty_window_sizes_raises(self) -> None:
        """Test empty window sizes raises ValidationError."""
        with pytest.raises(ValidationError):
            Validator.validate_window_sizes([])

    def test_window_size_exceeds_max_raises(self) -> None:
        """Test window size exceeding max raises ValidationError."""
        with pytest.raises(ValidationError):
            Validator.validate_window_sizes([1000], max_size=500)


class TestValidateFetchOptions:
    """Tests for validate_fetch_options helper."""

    def test_valid_fetch_options(self) -> None:
        """Test valid fetch options."""
        symbols, start, end = validate_fetch_options(
            ["AAPL", "GOOGL"],
            "2024-01-01",
            "2024-12-31",
        )
        assert symbols == ["AAPL", "GOOGL"]
        assert start == datetime(2024, 1, 1)
        assert end == datetime(2024, 12, 31)

    def test_fetch_options_with_none_dates(self) -> None:
        """Test fetch options with None dates."""
        symbols, start, end = validate_fetch_options(["AAPL"])
        assert symbols == ["AAPL"]
        assert start is None
        assert end is None

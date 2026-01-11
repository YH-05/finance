"""Input validation utilities for market_analysis.

This module provides validation functions for:
- Ticker symbols
- Date ranges
- Numeric parameters
- Configuration options
"""

import re
from datetime import datetime
from typing import Any

from ..errors import ErrorCode, ValidationError
from .logging_config import get_logger

logger = get_logger(__name__)

# Valid ticker symbol pattern: 1-10 alphanumeric chars, may include dots, hyphens, carets
SYMBOL_PATTERN = re.compile(r"^[A-Z0-9\.\-\^]{1,15}$", re.IGNORECASE)

# Date formats supported for parsing
DATE_FORMATS = [
    "%Y-%m-%d",
    "%Y/%m/%d",
    "%Y%m%d",
    "%d-%m-%Y",
    "%d/%m/%Y",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%d %H:%M:%S",
]


class Validator:
    """Input validation utility class.

    Provides static methods for validating various input types
    used in market data operations.

    Examples
    --------
    >>> Validator.validate_symbol("AAPL")
    'AAPL'
    >>> Validator.validate_date_range("2024-01-01", "2024-12-31")
    (datetime(2024, 1, 1), datetime(2024, 12, 31))
    """

    @staticmethod
    def validate_symbol(symbol: str) -> str:
        """Validate and normalize a ticker symbol.

        Parameters
        ----------
        symbol : str
            The ticker symbol to validate

        Returns
        -------
        str
            The validated and normalized symbol (uppercase)

        Raises
        ------
        ValidationError
            If the symbol is empty or contains invalid characters

        Examples
        --------
        >>> Validator.validate_symbol("aapl")
        'AAPL'
        >>> Validator.validate_symbol("BRK.B")
        'BRK.B'
        >>> Validator.validate_symbol("^GSPC")
        '^GSPC'
        """
        logger.debug("Validating symbol", symbol=symbol)

        if not symbol:
            logger.error("Empty symbol provided")
            raise ValidationError(
                "Symbol cannot be empty",
                field="symbol",
                value=symbol,
                code=ErrorCode.INVALID_SYMBOL,
            )

        symbol = symbol.strip()

        if not SYMBOL_PATTERN.match(symbol):
            logger.error(
                "Invalid symbol format",
                symbol=symbol,
                pattern=SYMBOL_PATTERN.pattern,
            )
            raise ValidationError(
                f"Invalid symbol format: {symbol!r}. "
                "Symbol must be 1-15 alphanumeric characters, "
                "dots, hyphens, or carets",
                field="symbol",
                value=symbol,
                code=ErrorCode.INVALID_SYMBOL,
            )

        normalized = symbol.upper()
        logger.debug("Symbol validated", original=symbol, normalized=normalized)
        return normalized

    @staticmethod
    def validate_symbols(symbols: list[str]) -> list[str]:
        """Validate a list of ticker symbols.

        Parameters
        ----------
        symbols : list[str]
            List of ticker symbols to validate

        Returns
        -------
        list[str]
            List of validated and normalized symbols

        Raises
        ------
        ValidationError
            If the list is empty or any symbol is invalid

        Examples
        --------
        >>> Validator.validate_symbols(["aapl", "googl", "msft"])
        ['AAPL', 'GOOGL', 'MSFT']
        """
        logger.debug("Validating symbol list", count=len(symbols) if symbols else 0)

        if not symbols:
            logger.error("Empty symbol list provided")
            raise ValidationError(
                "Symbol list cannot be empty",
                field="symbols",
                value=symbols,
                code=ErrorCode.INVALID_PARAMETER,
            )

        validated = [Validator.validate_symbol(s) for s in symbols]
        logger.debug("Symbol list validated", count=len(validated))
        return validated

    @staticmethod
    def parse_date(
        date_input: str | datetime | None,
        field_name: str = "date",
    ) -> datetime | None:
        """Parse a date string or datetime into a datetime object.

        Parameters
        ----------
        date_input : str | datetime | None
            The date to parse (string or datetime)
        field_name : str
            Name of the field for error messages

        Returns
        -------
        datetime | None
            Parsed datetime object, or None if input is None

        Raises
        ------
        ValidationError
            If the date string cannot be parsed

        Examples
        --------
        >>> Validator.parse_date("2024-01-15")
        datetime.datetime(2024, 1, 15, 0, 0)
        >>> Validator.parse_date(None)
        None
        """
        if date_input is None:
            return None

        if isinstance(date_input, datetime):
            return date_input

        logger.debug("Parsing date string", date_input=date_input, field=field_name)

        date_str = str(date_input).strip()

        for fmt in DATE_FORMATS:
            try:
                parsed = datetime.strptime(date_str, fmt)
                logger.debug(
                    "Date parsed successfully",
                    input=date_str,
                    format=fmt,
                    result=parsed.isoformat(),
                )
                return parsed
            except ValueError:
                continue

        logger.error(
            "Failed to parse date",
            date_input=date_str,
            field=field_name,
            supported_formats=DATE_FORMATS,
        )
        raise ValidationError(
            f"Cannot parse date: {date_str!r}. "
            f"Supported formats: {', '.join(DATE_FORMATS[:3])}...",
            field=field_name,
            value=date_str,
            code=ErrorCode.INVALID_DATE,
        )

    @staticmethod
    def validate_date_range(
        start_date: str | datetime | None,
        end_date: str | datetime | None,
    ) -> tuple[datetime | None, datetime | None]:
        """Validate a date range.

        Parameters
        ----------
        start_date : str | datetime | None
            Start date of the range
        end_date : str | datetime | None
            End date of the range

        Returns
        -------
        tuple[datetime | None, datetime | None]
            Validated (start_date, end_date) tuple

        Raises
        ------
        ValidationError
            If start_date is after end_date

        Examples
        --------
        >>> Validator.validate_date_range("2024-01-01", "2024-12-31")
        (datetime(2024, 1, 1), datetime(2024, 12, 31))
        """
        logger.debug(
            "Validating date range",
            start_date=start_date,
            end_date=end_date,
        )

        parsed_start = Validator.parse_date(start_date, "start_date")
        parsed_end = Validator.parse_date(end_date, "end_date")

        if parsed_start and parsed_end and parsed_start > parsed_end:
            logger.error(
                "Invalid date range: start > end",
                start_date=parsed_start.isoformat(),
                end_date=parsed_end.isoformat(),
            )
            raise ValidationError(
                f"Start date ({parsed_start.date()}) must be before "
                f"end date ({parsed_end.date()})",
                field="date_range",
                value={"start": str(parsed_start), "end": str(parsed_end)},
                code=ErrorCode.INVALID_DATE,
            )

        logger.debug(
            "Date range validated",
            start=parsed_start.isoformat() if parsed_start else None,
            end=parsed_end.isoformat() if parsed_end else None,
        )
        return parsed_start, parsed_end

    @staticmethod
    def validate_positive_int(
        value: int,
        field_name: str = "value",
        min_value: int = 1,
        max_value: int | None = None,
    ) -> int:
        """Validate that a value is a positive integer within bounds.

        Parameters
        ----------
        value : int
            The value to validate
        field_name : str
            Name of the field for error messages
        min_value : int
            Minimum allowed value (default: 1)
        max_value : int | None
            Maximum allowed value (default: None, no upper limit)

        Returns
        -------
        int
            The validated value

        Raises
        ------
        ValidationError
            If the value is out of bounds

        Examples
        --------
        >>> Validator.validate_positive_int(50, "window_size", min_value=1, max_value=500)
        50
        """
        logger.debug(
            "Validating positive integer",
            value=value,
            field=field_name,
            min_value=min_value,
            max_value=max_value,
        )

        if not isinstance(value, int):
            raise ValidationError(
                f"{field_name} must be an integer, got {type(value).__name__}",
                field=field_name,
                value=value,
                code=ErrorCode.INVALID_PARAMETER,
            )

        if value < min_value:
            raise ValidationError(
                f"{field_name} must be at least {min_value}, got {value}",
                field=field_name,
                value=value,
                code=ErrorCode.INVALID_PARAMETER,
            )

        if max_value is not None and value > max_value:
            raise ValidationError(
                f"{field_name} must be at most {max_value}, got {value}",
                field=field_name,
                value=value,
                code=ErrorCode.INVALID_PARAMETER,
            )

        logger.debug("Positive integer validated", field=field_name, value=value)
        return value

    @staticmethod
    def validate_positive_float(
        value: float,
        field_name: str = "value",
        min_value: float = 0.0,
        max_value: float | None = None,
        allow_zero: bool = False,
    ) -> float:
        """Validate that a value is a positive float within bounds.

        Parameters
        ----------
        value : float
            The value to validate
        field_name : str
            Name of the field for error messages
        min_value : float
            Minimum allowed value (default: 0.0)
        max_value : float | None
            Maximum allowed value (default: None)
        allow_zero : bool
            Whether to allow zero (default: False)

        Returns
        -------
        float
            The validated value

        Raises
        ------
        ValidationError
            If the value is out of bounds

        Examples
        --------
        >>> Validator.validate_positive_float(0.5, "threshold")
        0.5
        """
        logger.debug(
            "Validating positive float",
            value=value,
            field=field_name,
            min_value=min_value,
            max_value=max_value,
        )

        if not isinstance(value, (int, float)):
            raise ValidationError(
                f"{field_name} must be a number, got {type(value).__name__}",
                field=field_name,
                value=value,
                code=ErrorCode.INVALID_PARAMETER,
            )

        if not allow_zero and value == 0:
            raise ValidationError(
                f"{field_name} cannot be zero",
                field=field_name,
                value=value,
                code=ErrorCode.INVALID_PARAMETER,
            )

        if value < min_value:
            raise ValidationError(
                f"{field_name} must be at least {min_value}, got {value}",
                field=field_name,
                value=value,
                code=ErrorCode.INVALID_PARAMETER,
            )

        if max_value is not None and value > max_value:
            raise ValidationError(
                f"{field_name} must be at most {max_value}, got {value}",
                field=field_name,
                value=value,
                code=ErrorCode.INVALID_PARAMETER,
            )

        logger.debug("Positive float validated", field=field_name, value=value)
        return float(value)

    @staticmethod
    def validate_enum_value(
        value: Any,
        allowed_values: list[Any] | set[Any],
        field_name: str = "value",
    ) -> Any:
        """Validate that a value is one of the allowed values.

        Parameters
        ----------
        value : Any
            The value to validate
        allowed_values : list[Any] | set[Any]
            Set of allowed values
        field_name : str
            Name of the field for error messages

        Returns
        -------
        Any
            The validated value

        Raises
        ------
        ValidationError
            If the value is not in allowed_values

        Examples
        --------
        >>> Validator.validate_enum_value("daily", ["daily", "weekly", "monthly"], "interval")
        'daily'
        """
        logger.debug(
            "Validating enum value",
            value=value,
            field=field_name,
            allowed_count=len(allowed_values),
        )

        if value not in allowed_values:
            allowed_str = ", ".join(repr(v) for v in sorted(allowed_values, key=str))
            raise ValidationError(
                f"Invalid {field_name}: {value!r}. Must be one of: {allowed_str}",
                field=field_name,
                value=value,
                code=ErrorCode.INVALID_PARAMETER,
            )

        logger.debug("Enum value validated", field=field_name, value=value)
        return value

    @staticmethod
    def validate_window_sizes(
        window_sizes: list[int],
        max_size: int = 500,
    ) -> list[int]:
        """Validate a list of window sizes for moving averages.

        Parameters
        ----------
        window_sizes : list[int]
            List of window sizes to validate
        max_size : int
            Maximum allowed window size (default: 500)

        Returns
        -------
        list[int]
            Validated and sorted window sizes

        Raises
        ------
        ValidationError
            If any window size is invalid

        Examples
        --------
        >>> Validator.validate_window_sizes([20, 50, 200])
        [20, 50, 200]
        """
        logger.debug(
            "Validating window sizes",
            window_sizes=window_sizes,
            max_size=max_size,
        )

        if not window_sizes:
            raise ValidationError(
                "Window sizes list cannot be empty",
                field="window_sizes",
                value=window_sizes,
                code=ErrorCode.INVALID_PARAMETER,
            )

        validated = []
        for size in window_sizes:
            validated.append(
                Validator.validate_positive_int(
                    size,
                    field_name=f"window_size[{size}]",
                    min_value=1,
                    max_value=max_size,
                )
            )

        # Sort and remove duplicates
        result = sorted(set(validated))
        logger.debug("Window sizes validated", result=result)
        return result


def validate_fetch_options(
    symbols: list[str],
    start_date: str | datetime | None = None,
    end_date: str | datetime | None = None,
) -> tuple[list[str], datetime | None, datetime | None]:
    """Validate common fetch operation parameters.

    Parameters
    ----------
    symbols : list[str]
        List of ticker symbols
    start_date : str | datetime | None
        Start date for data range
    end_date : str | datetime | None
        End date for data range

    Returns
    -------
    tuple[list[str], datetime | None, datetime | None]
        Validated (symbols, start_date, end_date) tuple

    Raises
    ------
    ValidationError
        If any parameter is invalid

    Examples
    --------
    >>> symbols, start, end = validate_fetch_options(
    ...     ["AAPL", "GOOGL"],
    ...     "2024-01-01",
    ...     "2024-12-31",
    ... )
    """
    validated_symbols = Validator.validate_symbols(symbols)
    validated_start, validated_end = Validator.validate_date_range(start_date, end_date)

    return validated_symbols, validated_start, validated_end


__all__ = [
    "DATE_FORMATS",
    "SYMBOL_PATTERN",
    "Validator",
    "validate_fetch_options",
]

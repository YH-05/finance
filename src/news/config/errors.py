"""Custom exception classes for configuration management.

This module provides a hierarchy of exceptions for error handling in the
configuration module. All exceptions inherit from the base ConfigError class.

Exception Hierarchy
-------------------
- ConfigError (base, inherits from NewsError)
  - ConfigParseError (parsing errors)
  - ConfigValidationError (validation errors)

Examples
--------
>>> raise ConfigError("Configuration error")
>>> raise ConfigParseError("Invalid YAML", file_path="/path/to/config.yaml")
>>> raise ConfigValidationError("Invalid value", field="timeout", value=-1)
"""

from utils_core.logging import get_logger

from ..core.errors import NewsError

logger = get_logger(__name__, module="config.errors")


class ConfigError(NewsError):
    """Base exception for configuration errors.

    All configuration-related exceptions should inherit from this class.
    This allows catching all config errors with a single except clause.

    Examples
    --------
    >>> try:
    ...     raise ConfigError("Configuration error")
    ... except ConfigError as e:
    ...     print(f"Config error: {e}")
    Config error: Configuration error
    """

    pass


class ConfigParseError(ConfigError):
    """Exception raised when parsing a configuration file fails.

    This exception is used for errors that occur while parsing configuration
    files (YAML, JSON, etc.).

    Parameters
    ----------
    message : str
        Human-readable error message.
    file_path : str
        Path to the configuration file that failed to parse.
    cause : Exception | None, optional
        Original exception that caused this error.

    Attributes
    ----------
    file_path : str
        Path to the configuration file.
    cause : Exception | None
        Original exception that caused this error.

    Examples
    --------
    >>> error = ConfigParseError(
    ...     message="Invalid YAML syntax",
    ...     file_path="/path/to/config.yaml",
    ... )
    >>> error.file_path
    '/path/to/config.yaml'
    """

    def __init__(
        self,
        message: str,
        file_path: str,
        cause: Exception | None = None,
    ) -> None:
        """Initialize ConfigParseError with file information."""
        super().__init__(f"{message} (file: {file_path})")
        self.file_path = file_path
        self.cause = cause

        logger.debug(
            "ConfigParseError created",
            message=message,
            file_path=file_path,
            has_cause=cause is not None,
        )


class ConfigValidationError(ConfigError):
    """Exception raised when configuration validation fails.

    This exception is used for validation errors, such as invalid values,
    missing required fields, or out-of-range parameters.

    Parameters
    ----------
    message : str
        Human-readable error message.
    field : str
        Name of the field that failed validation.
    value : object
        The invalid value that was provided.

    Attributes
    ----------
    field : str
        Name of the field that failed validation.
    value : object
        The invalid value that was provided.

    Examples
    --------
    >>> error = ConfigValidationError(
    ...     message="Value must be positive",
    ...     field="timeout",
    ...     value=-1,
    ... )
    >>> error.field
    'timeout'
    >>> error.value
    -1
    """

    def __init__(
        self,
        message: str,
        field: str,
        value: object,
    ) -> None:
        """Initialize ConfigValidationError with field information."""
        super().__init__(message)
        self.field = field
        self.value = value

        logger.debug(
            "ConfigValidationError created",
            message=message,
            field=field,
            value_type=type(value).__name__,
        )


# Export all public symbols
__all__ = [
    "ConfigError",
    "ConfigParseError",
    "ConfigValidationError",
]

"""Common type definitions for the finance package."""

from collections.abc import Mapping
from pathlib import Path
from typing import Annotated, Literal, Self, TypedDict

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

# Database types
type DatabaseType = Literal["sqlite", "duckdb"]
type DataSource = Literal["yfinance", "fred"]
type AssetCategory = Literal["stocks", "forex", "indices", "indicators"]

# File format types
type FileFormat = Literal["parquet", "csv", "json"]


class DatabaseConfig(TypedDict):
    """Database configuration."""

    db_type: DatabaseType
    name: str
    path: str


class FetchResult(TypedDict):
    """Result of a data fetch operation."""

    source: DataSource
    symbol: str
    start_date: str
    end_date: str
    row_count: int
    success: bool
    error: str | None


class MigrationInfo(TypedDict):
    """Migration file information."""

    filename: str
    applied_at: str | None


# JSON types (shared with market_analysis)
type JSONPrimitive = str | int | float | bool | None
type JSONValue = JSONPrimitive | Mapping[str, "JSONValue"] | list["JSONValue"]
type JSONObject = Mapping[str, JSONValue]

# Compression types for Parquet
type ParquetCompression = Literal["snappy", "gzip", "brotli", "lz4", "zstd", "none"]

# JSON orient types
type JsonOrient = Literal["records", "columns", "index", "split", "table", "values"]

# Date format types
type DateFormat = Literal["iso", "epoch", "epoch_ms"]


# =============================================================================
# Pydantic Models for Format Conversion (Issue #951)
# =============================================================================


class TypeMapping(BaseModel):
    """Data type mapping information for a column.

    Represents the type transformation applied to a single column
    during format conversion between Parquet and JSON.

    Parameters
    ----------
    column_name : str
        Name of the column being mapped.
    source_type : str
        Original data type before conversion (e.g., "int64", "string").
    target_type : str
        Data type after conversion (e.g., "integer", "string").

    Examples
    --------
    >>> mapping = TypeMapping(
    ...     column_name="user_id",
    ...     source_type="int64",
    ...     target_type="integer"
    ... )
    >>> mapping.column_name
    'user_id'
    """

    model_config = ConfigDict(frozen=True)

    column_name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Name of the column being mapped",
    )
    source_type: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Original data type before conversion",
    )
    target_type: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Data type after conversion",
    )

    @field_validator("column_name")
    @classmethod
    def validate_column_name(cls, v: str) -> str:
        """Validate that column name is not empty after stripping whitespace."""
        stripped = v.strip()
        if not stripped:
            raise ValueError("Column name cannot be empty or whitespace only")
        return stripped


class ConversionOptions(BaseModel):
    """Configuration options for format conversion.

    Controls how data is transformed during Parquet/JSON conversion,
    including compression, JSON structure, and type inference settings.

    Parameters
    ----------
    compression : ParquetCompression | None, default=None
        Compression algorithm for Parquet output.
        Options: "snappy", "gzip", "brotli", "lz4", "zstd", "none".
        If None, uses Parquet default (typically snappy).
    orient : JsonOrient, default="records"
        JSON output structure format.
        Options: "records", "columns", "index", "split", "table", "values".
    date_format : DateFormat, default="iso"
        Format for datetime serialization.
        Options: "iso" (ISO 8601), "epoch" (seconds), "epoch_ms" (milliseconds).
    infer_types : bool, default=True
        Whether to automatically infer data types during conversion.

    Examples
    --------
    >>> options = ConversionOptions(compression="gzip", orient="records")
    >>> options.infer_types
    True

    >>> options = ConversionOptions(date_format="epoch", infer_types=False)
    >>> options.date_format
    'epoch'
    """

    model_config = ConfigDict(frozen=True)

    compression: Annotated[
        Literal["snappy", "gzip", "brotli", "lz4", "zstd", "none"] | None,
        Field(
            default=None,
            description="Compression algorithm for Parquet output",
        ),
    ] = None

    orient: Annotated[
        Literal["records", "columns", "index", "split", "table", "values"],
        Field(
            default="records",
            description="JSON output structure format",
        ),
    ] = "records"

    date_format: Annotated[
        Literal["iso", "epoch", "epoch_ms"],
        Field(
            default="iso",
            description="Format for datetime serialization",
        ),
    ] = "iso"

    infer_types: Annotated[
        bool,
        Field(
            default=True,
            description="Whether to automatically infer data types",
        ),
    ] = True


class ConversionResult(BaseModel):
    """Result of a format conversion operation.

    Contains comprehensive information about a completed format conversion,
    including success status, file paths, row counts, and any error details.

    Parameters
    ----------
    success : bool
        Whether the conversion completed successfully.
    input_path : Path
        Path to the source file that was converted.
    output_path : Path
        Path to the generated output file.
    rows_converted : int
        Number of data rows that were converted.
    columns : list[str]
        List of column names in the converted data.
    error_message : str | None, default=None
        Error message if conversion failed, None otherwise.
    type_mappings : list[TypeMapping] | None, default=None
        Optional list of type transformations applied to columns.

    Examples
    --------
    >>> result = ConversionResult(
    ...     success=True,
    ...     input_path=Path("data.parquet"),
    ...     output_path=Path("data.json"),
    ...     rows_converted=1000,
    ...     columns=["id", "name", "value"]
    ... )
    >>> result.success
    True
    >>> result.rows_converted
    1000

    >>> # Failed conversion
    >>> result = ConversionResult(
    ...     success=False,
    ...     input_path=Path("invalid.parquet"),
    ...     output_path=Path("output.json"),
    ...     rows_converted=0,
    ...     columns=[],
    ...     error_message="Invalid Parquet file format"
    ... )
    >>> result.error_message
    'Invalid Parquet file format'
    """

    model_config = ConfigDict(frozen=True)

    success: bool = Field(
        ...,
        description="Whether the conversion completed successfully",
    )
    input_path: Path = Field(
        ...,
        description="Path to the source file that was converted",
    )
    output_path: Path = Field(
        ...,
        description="Path to the generated output file",
    )
    rows_converted: Annotated[
        int,
        Field(
            ...,
            ge=0,
            description="Number of data rows that were converted",
        ),
    ]
    columns: list[str] = Field(
        ...,
        description="List of column names in the converted data",
    )
    error_message: str | None = Field(
        default=None,
        description="Error message if conversion failed",
    )
    type_mappings: list[TypeMapping] | None = Field(
        default=None,
        description="Optional list of type transformations applied",
    )

    @field_validator("columns")
    @classmethod
    def validate_columns(cls, v: list[str]) -> list[str]:
        """Validate column names are not empty strings."""
        for col in v:
            if not col or not col.strip():
                raise ValueError("Column names cannot be empty or whitespace only")
        return v

    @model_validator(mode="after")
    def validate_consistency(self) -> Self:
        """Validate that success status is consistent with other fields."""
        if self.success:
            if self.error_message is not None:
                raise ValueError("error_message must be None when success is True")
            if self.rows_converted < 0:
                raise ValueError(
                    "rows_converted must be non-negative when success is True"
                )
        elif self.error_message is None:
            raise ValueError("error_message is required when success is False")
        return self

    @classmethod
    def create_success(
        cls,
        input_path: Path,
        output_path: Path,
        rows_converted: int,
        columns: list[str],
        type_mappings: list[TypeMapping] | None = None,
    ) -> Self:
        """Factory method to create a successful conversion result.

        Parameters
        ----------
        input_path : Path
            Path to the source file.
        output_path : Path
            Path to the output file.
        rows_converted : int
            Number of rows converted.
        columns : list[str]
            List of column names.
        type_mappings : list[TypeMapping] | None, default=None
            Optional type mapping information.

        Returns
        -------
        ConversionResult
            A ConversionResult instance with success=True.

        Examples
        --------
        >>> result = ConversionResult.create_success(
        ...     input_path=Path("data.parquet"),
        ...     output_path=Path("data.json"),
        ...     rows_converted=100,
        ...     columns=["id", "name"]
        ... )
        >>> result.success
        True
        """
        return cls(
            success=True,
            input_path=input_path,
            output_path=output_path,
            rows_converted=rows_converted,
            columns=columns,
            error_message=None,
            type_mappings=type_mappings,
        )

    @classmethod
    def create_failure(
        cls,
        input_path: Path,
        output_path: Path,
        error_message: str,
    ) -> Self:
        """Factory method to create a failed conversion result.

        Parameters
        ----------
        input_path : Path
            Path to the source file.
        output_path : Path
            Path to the output file.
        error_message : str
            Description of what went wrong.

        Returns
        -------
        ConversionResult
            A ConversionResult instance with success=False.

        Examples
        --------
        >>> result = ConversionResult.create_failure(
        ...     input_path=Path("invalid.parquet"),
        ...     output_path=Path("output.json"),
        ...     error_message="File not found"
        ... )
        >>> result.success
        False
        >>> result.error_message
        'File not found'
        """
        return cls(
            success=False,
            input_path=input_path,
            output_path=output_path,
            rows_converted=0,
            columns=[],
            error_message=error_message,
            type_mappings=None,
        )

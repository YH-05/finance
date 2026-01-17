"""Common type definitions for the strategy package."""

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date
from typing import Literal, TypeAlias, TypedDict

from dateutil.relativedelta import relativedelta

# Status types
type ProcessorStatus = Literal["success", "error", "pending"]
type ValidationStatus = Literal["valid", "invalid", "skipped"]


# Common data structures
class ItemDict(TypedDict):
    """Typed dictionary for item data."""

    id: int
    name: str
    value: int


class ItemDictWithStatus(ItemDict):
    """Extended item dictionary with status."""

    status: ProcessorStatus
    processed: bool


class ConfigDict(TypedDict, total=False):
    """Typed dictionary for configuration data."""

    name: str
    max_items: int
    enable_validation: bool
    debug: bool
    timeout: float


class ErrorInfo(TypedDict):
    """Typed dictionary for error information."""

    code: str
    message: str
    details: Mapping[str, str | int | None]


# Result types
class ProcessingResult(TypedDict):
    """Result of a processing operation."""

    status: ProcessorStatus
    data: list[ItemDict]
    errors: list[ErrorInfo]
    processed_count: int
    skipped_count: int


class ValidationResult(TypedDict):
    """Result of a validation operation."""

    is_valid: bool
    errors: list[str]
    warnings: list[str]


# JSON types
type JSONPrimitive = str | int | float | bool | None
type JSONValue = JSONPrimitive | Mapping[str, "JSONValue"] | list["JSONValue"]
type JSONObject = Mapping[str, JSONValue]

# File operation types
type FileOperation = Literal["read", "write", "append", "delete"]
type FileFormat = Literal["json", "yaml", "csv", "txt"]

# Sorting and filtering
type SortOrder = Literal["asc", "desc"]
type FilterOperator = Literal["eq", "ne", "gt", "lt", "gte", "lte", "in", "contains"]


# Structured logging types
class LogContext(TypedDict, total=False):
    """Context information for structured logging."""

    user_id: str | int | None
    request_id: str | None
    session_id: str | None
    trace_id: str | None
    module: str | None
    function: str | None
    line_number: int | None
    extra: Mapping[str, JSONValue]


class LogEvent(TypedDict):
    """Structured log event."""

    event: str
    level: Literal["debug", "info", "warning", "error", "critical"]
    timestamp: str
    logger: str
    context: LogContext | None
    exception: str | None
    duration_ms: float | None


# Log formatting types
type LogFormat = Literal["json", "console", "plain"]
type LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


# =============================================================================
# Strategy Package Specific Types
# =============================================================================

# Asset class type alias
# AIDEV-NOTE: TypeAlias形式を使用（get_argsとの互換性のため）
AssetClass: TypeAlias = Literal[
    "equity", "bond", "commodity", "real_estate", "cash", "other"
]

# Preset period type alias
# AIDEV-NOTE: TypeAlias形式を使用（get_argsとの互換性のため）
PresetPeriod: TypeAlias = Literal["1y", "3y", "5y", "10y", "ytd", "max"]


@dataclass(frozen=True)
class Holding:
    """ポートフォリオ内の個別保有銘柄.

    Parameters
    ----------
    ticker : str
        ティッカーシンボル（例: "VOO", "BND"）
    weight : float
        ポートフォリオ内での比率（0.0 - 1.0）

    Raises
    ------
    ValueError
        ticker が空文字列または空白のみの場合
        weight が 0.0-1.0 の範囲外の場合

    Examples
    --------
    >>> holding = Holding(ticker="VOO", weight=0.6)
    >>> holding.ticker
    'VOO'
    >>> holding.weight
    0.6
    """

    ticker: str
    weight: float

    def __post_init__(self) -> None:
        """初期化後のバリデーション."""
        if not self.ticker or not self.ticker.strip():
            msg = f"ticker must be non-empty string, got {self.ticker!r}"
            raise ValueError(msg)
        if not 0.0 <= self.weight <= 1.0:
            msg = f"weight must be between 0.0 and 1.0, got {self.weight}"
            raise ValueError(msg)


@dataclass(frozen=True)
class TickerInfo:
    """ティッカーの詳細情報.

    Parameters
    ----------
    ticker : str
        ティッカーシンボル
    name : str
        銘柄名（例: "Vanguard S&P 500 ETF"）
    sector : str | None, default=None
        セクター（例: "Technology"）
    industry : str | None, default=None
        業種（例: "Exchange Traded Fund"）
    asset_class : AssetClass, default="equity"
        資産クラス

    Examples
    --------
    >>> info = TickerInfo(ticker="VOO", name="Vanguard S&P 500 ETF")
    >>> info.ticker
    'VOO'
    >>> info.asset_class
    'equity'
    """

    ticker: str
    name: str
    sector: str | None = None
    industry: str | None = None
    asset_class: AssetClass = "equity"


@dataclass(frozen=True)
class Period:
    """分析期間の定義.

    Parameters
    ----------
    start : date
        開始日
    end : date
        終了日
    preset : PresetPeriod | None, default=None
        プリセット期間（設定時は start/end を自動計算）

    Examples
    --------
    >>> from datetime import date
    >>> period = Period(start=date(2020, 1, 1), end=date(2024, 12, 31))
    >>> period.start
    datetime.date(2020, 1, 1)

    >>> period = Period.from_preset("1y")
    >>> period.preset
    '1y'
    """

    start: date
    end: date
    preset: PresetPeriod | None = None

    @classmethod
    def from_preset(cls, preset: PresetPeriod) -> "Period":
        """プリセット期間から Period を作成.

        Parameters
        ----------
        preset : PresetPeriod
            プリセット期間 ("1y", "3y", "5y", "10y", "ytd", "max")

        Returns
        -------
        Period
            計算された期間

        Notes
        -----
        - 1y: 1年前から今日まで
        - 3y: 3年前から今日まで
        - 5y: 5年前から今日まで
        - 10y: 10年前から今日まで
        - ytd: 今年の1月1日から今日まで
        - max: 30年前から今日まで

        Examples
        --------
        >>> period = Period.from_preset("ytd")
        >>> period.preset
        'ytd'
        """
        today = date.today()

        if preset == "1y":
            start = today - relativedelta(years=1)
        elif preset == "3y":
            start = today - relativedelta(years=3)
        elif preset == "5y":
            start = today - relativedelta(years=5)
        elif preset == "10y":
            start = today - relativedelta(years=10)
        elif preset == "ytd":
            start = date(today.year, 1, 1)
        elif preset == "max":
            start = today - relativedelta(years=30)
        else:
            # 型チェッカーのための exhaustive check
            msg = f"Unknown preset: {preset}"
            raise ValueError(msg)

        return cls(start=start, end=today, preset=preset)

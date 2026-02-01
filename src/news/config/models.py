"""Pydantic models for news configuration.

This module defines the configuration models for the news package, including
source configurations, sink configurations, and general settings.

Configuration Hierarchy
-----------------------
- NewsConfig (root)
  - SourcesConfig
    - YFinanceTickerSourceConfig
    - YFinanceSearchSourceConfig
  - SinksConfig
    - FileSinkConfig
    - GitHubSinkConfig
  - SettingsConfig
    - RetryConfig

Examples
--------
>>> config = NewsConfig()
>>> config.settings.max_articles_per_source
10

>>> config = NewsConfig.model_validate({
...     "sources": {"yfinance_ticker": {"symbols_file": "symbols.yaml"}},
...     "settings": {"max_articles_per_source": 20},
... })
"""

from pydantic import BaseModel, Field

from utils_core.logging import get_logger

logger = get_logger(__name__, module="config.models")


class RetryConfig(BaseModel):
    """Retry configuration for network operations.

    Parameters
    ----------
    max_attempts : int
        Maximum number of retry attempts (default: 3).
    initial_delay : float
        Initial delay in seconds before first retry (default: 1.0).

    Examples
    --------
    >>> config = RetryConfig()
    >>> config.max_attempts
    3
    """

    max_attempts: int = Field(
        default=3,
        ge=1,
        description="Maximum number of retry attempts",
    )
    initial_delay: float = Field(
        default=1.0,
        gt=0,
        description="Initial delay in seconds before first retry",
    )


class YFinanceTickerSourceConfig(BaseModel):
    """Configuration for YFinance Ticker news source.

    Parameters
    ----------
    enabled : bool
        Whether this source is enabled (default: True).
    symbols_file : str
        Path to the symbols YAML file (required).
    categories : list[str]
        List of symbol categories to fetch (default: []).
        Available categories: indices, mag7, sectors, commodities, etc.

    Examples
    --------
    >>> config = YFinanceTickerSourceConfig(
    ...     symbols_file="src/analyze/config/symbols.yaml",
    ...     categories=["indices", "mag7"],
    ... )
    """

    enabled: bool = Field(default=True, description="Whether this source is enabled")
    symbols_file: str = Field(..., description="Path to the symbols YAML file")
    categories: list[str] = Field(
        default_factory=list,
        description="List of symbol categories to fetch",
    )


class YFinanceSearchSourceConfig(BaseModel):
    """Configuration for YFinance Search news source.

    Parameters
    ----------
    enabled : bool
        Whether this source is enabled (default: True).
    keywords_file : str
        Path to the keywords YAML file (required).

    Examples
    --------
    >>> config = YFinanceSearchSourceConfig(
    ...     keywords_file="data/config/news_search_keywords.yaml",
    ... )
    """

    enabled: bool = Field(default=True, description="Whether this source is enabled")
    keywords_file: str = Field(..., description="Path to the keywords YAML file")


class SourcesConfig(BaseModel):
    """Configuration for all news sources.

    Parameters
    ----------
    yfinance_ticker : YFinanceTickerSourceConfig | None
        Configuration for YFinance Ticker source (optional).
    yfinance_search : YFinanceSearchSourceConfig | None
        Configuration for YFinance Search source (optional).

    Examples
    --------
    >>> config = SourcesConfig()
    >>> config.yfinance_ticker is None
    True
    """

    yfinance_ticker: YFinanceTickerSourceConfig | None = Field(
        default=None,
        description="Configuration for YFinance Ticker source",
    )
    yfinance_search: YFinanceSearchSourceConfig | None = Field(
        default=None,
        description="Configuration for YFinance Search source",
    )


class FileSinkConfig(BaseModel):
    """Configuration for file output sink.

    Parameters
    ----------
    enabled : bool
        Whether this sink is enabled (default: True).
    output_dir : str
        Directory path for output files (required).
    filename_pattern : str
        Pattern for output filenames (default: "news_{date}.json").
        The {date} placeholder will be replaced with the current date.

    Examples
    --------
    >>> config = FileSinkConfig(output_dir="data/news")
    >>> config.filename_pattern
    'news_{date}.json'
    """

    enabled: bool = Field(default=True, description="Whether this sink is enabled")
    output_dir: str = Field(..., description="Directory path for output files")
    filename_pattern: str = Field(
        default="news_{date}.json",
        description="Pattern for output filenames",
    )


class GitHubSinkConfig(BaseModel):
    """Configuration for GitHub output sink.

    Parameters
    ----------
    enabled : bool
        Whether this sink is enabled (default: True).
    project_number : int
        GitHub Project number for posting news (required).

    Examples
    --------
    >>> config = GitHubSinkConfig(project_number=24)
    >>> config.enabled
    True
    """

    enabled: bool = Field(default=True, description="Whether this sink is enabled")
    project_number: int = Field(
        ...,
        ge=1,
        description="GitHub Project number for posting news",
    )


class SinksConfig(BaseModel):
    """Configuration for all output sinks.

    Parameters
    ----------
    file : FileSinkConfig | None
        Configuration for file output sink (optional).
    github : GitHubSinkConfig | None
        Configuration for GitHub output sink (optional).

    Examples
    --------
    >>> config = SinksConfig()
    >>> config.file is None
    True
    """

    file: FileSinkConfig | None = Field(
        default=None,
        description="Configuration for file output sink",
    )
    github: GitHubSinkConfig | None = Field(
        default=None,
        description="Configuration for GitHub output sink",
    )


class SettingsConfig(BaseModel):
    """General settings for news collection.

    Parameters
    ----------
    max_articles_per_source : int
        Maximum number of articles to fetch per source (default: 10).
    retry_config : RetryConfig
        Retry configuration for network operations.

    Examples
    --------
    >>> config = SettingsConfig()
    >>> config.max_articles_per_source
    10
    >>> config.retry_config.max_attempts
    3
    """

    max_articles_per_source: int = Field(
        default=10,
        ge=1,
        description="Maximum number of articles to fetch per source",
    )
    retry_config: RetryConfig = Field(
        default_factory=RetryConfig,
        description="Retry configuration for network operations",
    )


class NewsConfig(BaseModel):
    """Root configuration model for news collection.

    This is the main configuration class that contains all settings for
    the news collection pipeline.

    Parameters
    ----------
    sources : SourcesConfig
        Configuration for news sources.
    sinks : SinksConfig
        Configuration for output sinks.
    settings : SettingsConfig
        General settings.

    Examples
    --------
    >>> config = NewsConfig()
    >>> config.settings.max_articles_per_source
    10

    >>> data = {
    ...     "sources": {
    ...         "yfinance_ticker": {
    ...             "symbols_file": "symbols.yaml",
    ...             "categories": ["indices"],
    ...         }
    ...     },
    ...     "settings": {"max_articles_per_source": 5},
    ... }
    >>> config = NewsConfig.model_validate(data)
    >>> config.settings.max_articles_per_source
    5
    """

    sources: SourcesConfig = Field(
        default_factory=SourcesConfig,
        description="Configuration for news sources",
    )
    sinks: SinksConfig = Field(
        default_factory=SinksConfig,
        description="Configuration for output sinks",
    )
    settings: SettingsConfig = Field(
        default_factory=SettingsConfig,
        description="General settings",
    )


# Export all public symbols
__all__ = [
    "FileSinkConfig",
    "GitHubSinkConfig",
    "NewsConfig",
    "RetryConfig",
    "SettingsConfig",
    "SinksConfig",
    "SourcesConfig",
    "YFinanceSearchSourceConfig",
    "YFinanceTickerSourceConfig",
]

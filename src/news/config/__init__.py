"""Configuration management for the news package.

This module provides configuration loading and management for the news package.

Examples
--------
>>> from news.config import ConfigLoader, NewsConfig
>>> loader = ConfigLoader()
>>> config = loader.load("config.yaml")
>>> config.settings.max_articles_per_source
10
"""

from .errors import ConfigError, ConfigParseError, ConfigValidationError
from .loader import DEFAULT_CONFIG_PATH, ConfigLoader
from .models import (
    FileSinkConfig,
    GitHubSinkConfig,
    NewsConfig,
    RetryConfig,
    SettingsConfig,
    SinksConfig,
    SourcesConfig,
    YFinanceSearchSourceConfig,
    YFinanceTickerSourceConfig,
)

__all__ = [
    "DEFAULT_CONFIG_PATH",
    "ConfigError",
    "ConfigLoader",
    "ConfigParseError",
    "ConfigValidationError",
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

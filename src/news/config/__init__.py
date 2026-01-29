"""Configuration management for the news package.

This module provides configuration loading and management for the news package.

Examples
--------
>>> from news.config import ConfigLoader, NewsConfig
>>> loader = ConfigLoader()
>>> config = loader.load("config.yaml")
>>> config.settings.max_articles_per_source
10

>>> # Workflow configuration
>>> from news.config import NewsWorkflowConfig, load_config
>>> config = load_config("data/config/news-collection-config.yaml")
>>> config.version
'1.0'
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
from .workflow import (
    ExtractionConfig,
    FilteringConfig,
    GitHubConfig,
    NewsWorkflowConfig,
    OutputConfig,
    RssConfig,
    SummarizationConfig,
    load_config,
)

__all__ = [
    "DEFAULT_CONFIG_PATH",
    "ConfigError",
    "ConfigLoader",
    "ConfigParseError",
    "ConfigValidationError",
    "ExtractionConfig",
    "FileSinkConfig",
    "FilteringConfig",
    "GitHubConfig",
    "GitHubSinkConfig",
    "NewsConfig",
    "NewsWorkflowConfig",
    "OutputConfig",
    "RetryConfig",
    "RssConfig",
    "SettingsConfig",
    "SinksConfig",
    "SourcesConfig",
    "SummarizationConfig",
    "YFinanceSearchSourceConfig",
    "YFinanceTickerSourceConfig",
    "load_config",
]

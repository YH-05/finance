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

from .models import (
    DEFAULT_CONFIG_PATH,
    # Category configuration models
    CategoryLabelsConfig,
    # Exception classes
    ConfigError,
    # Loader
    ConfigLoader,
    ConfigParseError,
    ConfigValidationError,
    # Workflow configuration models
    DomainFilteringConfig,
    ExtractionConfig,
    # Basic configuration models
    FileSinkConfig,
    FilteringConfig,
    GitHubConfig,
    GitHubSinkConfig,
    NewsConfig,
    NewsWorkflowConfig,
    OutputConfig,
    PlaywrightFallbackConfig,
    PublishingConfig,
    RetryConfig,
    RssConfig,
    SettingsConfig,
    SinksConfig,
    SourcesConfig,
    SummarizationConfig,
    UserAgentRotationConfig,
    YFinanceSearchSourceConfig,
    YFinanceTickerSourceConfig,
    load_config,
)

__all__ = [
    "DEFAULT_CONFIG_PATH",
    "CategoryLabelsConfig",
    "ConfigError",
    "ConfigLoader",
    "ConfigParseError",
    "ConfigValidationError",
    "DomainFilteringConfig",
    "ExtractionConfig",
    "FileSinkConfig",
    "FilteringConfig",
    "GitHubConfig",
    "GitHubSinkConfig",
    "NewsConfig",
    "NewsWorkflowConfig",
    "OutputConfig",
    "PlaywrightFallbackConfig",
    "PublishingConfig",
    "RetryConfig",
    "RssConfig",
    "SettingsConfig",
    "SinksConfig",
    "SourcesConfig",
    "SummarizationConfig",
    "UserAgentRotationConfig",
    "YFinanceSearchSourceConfig",
    "YFinanceTickerSourceConfig",
    "load_config",
]

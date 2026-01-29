"""Workflow configuration models and loader for news collection.

This module defines the configuration models for the news collection workflow,
including RSS settings, extraction settings, summarization settings, GitHub
settings, and the main workflow configuration model.

Configuration Hierarchy
-----------------------
- NewsWorkflowConfig (root)
  - RssConfig (RSS feed settings)
  - ExtractionConfig (article body extraction settings)
  - SummarizationConfig (AI summarization settings)
  - GitHubConfig (GitHub Project/Issue settings)
  - FilteringConfig (article filtering settings)
  - OutputConfig (output file settings)

Examples
--------
>>> config = load_config("data/config/news-collection-config.yaml")
>>> config.version
'1.0'
>>> config.extraction.concurrency
5
>>> config.github.project_number
15

>>> # Resolve category to GitHub Status
>>> status = config.status_mapping.get("tech")  # "ai"
>>> status_id = config.github_status_ids.get(status)  # "6fbb43d0"
"""

from pathlib import Path

import yaml
from pydantic import BaseModel, Field

from ..utils.logging_config import get_logger

logger = get_logger(__name__, module="config.workflow")


class RssConfig(BaseModel):
    """RSS feed configuration.

    Parameters
    ----------
    presets_file : str
        Path to the RSS presets JSON file containing feed definitions.

    Examples
    --------
    >>> config = RssConfig(presets_file="data/config/rss-presets.json")
    >>> config.presets_file
    'data/config/rss-presets.json'
    """

    presets_file: str = Field(
        ...,
        description="Path to the RSS presets JSON file",
    )


class ExtractionConfig(BaseModel):
    """Article body extraction configuration.

    Parameters
    ----------
    concurrency : int
        Number of concurrent extraction tasks (default: 5).
    timeout_seconds : int
        Timeout for each extraction request in seconds (default: 30).
    min_body_length : int
        Minimum body text length to consider extraction successful (default: 200).
    max_retries : int
        Maximum retry attempts for failed extractions (default: 3).

    Examples
    --------
    >>> config = ExtractionConfig()
    >>> config.concurrency
    5
    >>> config.timeout_seconds
    30
    """

    concurrency: int = Field(
        default=5,
        ge=1,
        description="Number of concurrent extraction tasks",
    )
    timeout_seconds: int = Field(
        default=30,
        ge=1,
        description="Timeout for each extraction request in seconds",
    )
    min_body_length: int = Field(
        default=200,
        ge=0,
        description="Minimum body text length for successful extraction",
    )
    max_retries: int = Field(
        default=3,
        ge=0,
        description="Maximum retry attempts for failed extractions",
    )


class SummarizationConfig(BaseModel):
    """AI summarization configuration.

    Parameters
    ----------
    concurrency : int
        Number of concurrent summarization tasks (default: 3).
    timeout_seconds : int
        Timeout for each summarization request in seconds (default: 60).
    max_retries : int
        Maximum retry attempts for failed summarizations (default: 3).
    prompt_template : str
        Prompt template for the AI summarization.

    Examples
    --------
    >>> config = SummarizationConfig(prompt_template="Summarize: {body}")
    >>> config.concurrency
    3
    >>> config.timeout_seconds
    60
    """

    concurrency: int = Field(
        default=3,
        ge=1,
        description="Number of concurrent summarization tasks",
    )
    timeout_seconds: int = Field(
        default=60,
        ge=1,
        description="Timeout for each summarization request in seconds",
    )
    max_retries: int = Field(
        default=3,
        ge=0,
        description="Maximum retry attempts for failed summarizations",
    )
    prompt_template: str = Field(
        ...,
        description="Prompt template for AI summarization",
    )


class GitHubConfig(BaseModel):
    """GitHub Project and Issue configuration.

    Parameters
    ----------
    project_number : int
        GitHub Project number for posting news.
    project_id : str
        GitHub Project ID (PVT_...).
    status_field_id : str
        Status field ID in the GitHub Project.
    published_date_field_id : str
        Published date field ID in the GitHub Project.
    repository : str
        GitHub repository in "owner/repo" format.
    duplicate_check_days : int
        Number of days to check for duplicate articles (default: 7).
    dry_run : bool
        If True, skip actual Issue creation (default: False).

    Examples
    --------
    >>> config = GitHubConfig(
    ...     project_number=15,
    ...     project_id="PVT_kwHOBoK6AM4BMpw_",
    ...     status_field_id="PVTSSF_lAHOBoK6AM4BMpw_zg739ZE",
    ...     published_date_field_id="PVTF_lAHOBoK6AM4BMpw_zg8BzrI",
    ...     repository="YH-05/finance",
    ... )
    >>> config.project_number
    15
    >>> config.dry_run
    False
    """

    project_number: int = Field(
        ...,
        ge=1,
        description="GitHub Project number for posting news",
    )
    project_id: str = Field(
        ...,
        description="GitHub Project ID (PVT_...)",
    )
    status_field_id: str = Field(
        ...,
        description="Status field ID in the GitHub Project",
    )
    published_date_field_id: str = Field(
        ...,
        description="Published date field ID in the GitHub Project",
    )
    repository: str = Field(
        ...,
        description='GitHub repository in "owner/repo" format',
    )
    duplicate_check_days: int = Field(
        default=7,
        ge=1,
        description="Number of days to check for duplicate articles",
    )
    dry_run: bool = Field(
        default=False,
        description="If True, skip actual Issue creation",
    )


class FilteringConfig(BaseModel):
    """Article filtering configuration.

    Parameters
    ----------
    max_age_hours : int
        Maximum age of articles to collect in hours (default: 168 = 7 days).

    Examples
    --------
    >>> config = FilteringConfig()
    >>> config.max_age_hours
    168
    """

    max_age_hours: int = Field(
        default=168,  # 7 days
        ge=1,
        description="Maximum age of articles to collect in hours",
    )


class OutputConfig(BaseModel):
    """Output file configuration.

    Parameters
    ----------
    result_dir : str
        Directory path for output result files.

    Examples
    --------
    >>> config = OutputConfig(result_dir="data/exports/news-workflow")
    >>> config.result_dir
    'data/exports/news-workflow'
    """

    result_dir: str = Field(
        ...,
        description="Directory path for output result files",
    )


class NewsWorkflowConfig(BaseModel):
    """Root configuration model for news collection workflow.

    This is the main configuration class that contains all settings for
    the news collection workflow pipeline.

    Parameters
    ----------
    version : str
        Configuration version string.
    status_mapping : dict[str, str]
        Mapping from article category to GitHub Status name.
    github_status_ids : dict[str, str]
        Mapping from GitHub Status name to Status ID.
    rss : RssConfig
        RSS feed configuration.
    extraction : ExtractionConfig
        Article body extraction configuration.
    summarization : SummarizationConfig
        AI summarization configuration.
    github : GitHubConfig
        GitHub Project/Issue configuration.
    filtering : FilteringConfig
        Article filtering configuration.
    output : OutputConfig
        Output file configuration.

    Examples
    --------
    >>> config = NewsWorkflowConfig(
    ...     version="1.0",
    ...     status_mapping={"tech": "ai"},
    ...     github_status_ids={"ai": "6fbb43d0"},
    ...     rss=RssConfig(presets_file="rss-presets.json"),
    ...     extraction=ExtractionConfig(),
    ...     summarization=SummarizationConfig(prompt_template="test"),
    ...     github=GitHubConfig(
    ...         project_number=15,
    ...         project_id="PVT_test",
    ...         status_field_id="PVTSSF_test",
    ...         published_date_field_id="PVTF_test",
    ...         repository="owner/repo",
    ...     ),
    ...     filtering=FilteringConfig(),
    ...     output=OutputConfig(result_dir="data/exports"),
    ... )
    >>> config.version
    '1.0'

    Notes
    -----
    To resolve a category to a GitHub Status ID:

    1. Get the status name from status_mapping:
       status_name = config.status_mapping.get("tech")  # "ai"

    2. Get the status ID from github_status_ids:
       status_id = config.github_status_ids.get(status_name)  # "6fbb43d0"
    """

    version: str = Field(
        ...,
        description="Configuration version string",
    )
    status_mapping: dict[str, str] = Field(
        ...,
        description="Mapping from article category to GitHub Status name",
    )
    github_status_ids: dict[str, str] = Field(
        ...,
        description="Mapping from GitHub Status name to Status ID",
    )
    rss: RssConfig = Field(
        ...,
        description="RSS feed configuration",
    )
    extraction: ExtractionConfig = Field(
        default_factory=ExtractionConfig,
        description="Article body extraction configuration",
    )
    summarization: SummarizationConfig = Field(
        ...,
        description="AI summarization configuration",
    )
    github: GitHubConfig = Field(
        ...,
        description="GitHub Project/Issue configuration",
    )
    filtering: FilteringConfig = Field(
        default_factory=FilteringConfig,
        description="Article filtering configuration",
    )
    output: OutputConfig = Field(
        ...,
        description="Output file configuration",
    )


def load_config(path: Path | str) -> NewsWorkflowConfig:
    """Load workflow configuration from a YAML file.

    Parameters
    ----------
    path : Path | str
        Path to the YAML configuration file.

    Returns
    -------
    NewsWorkflowConfig
        Parsed and validated workflow configuration object.

    Raises
    ------
    FileNotFoundError
        If the configuration file does not exist.
    yaml.YAMLError
        If YAML parsing fails.
    pydantic.ValidationError
        If configuration validation fails.

    Examples
    --------
    >>> config = load_config("data/config/news-collection-config.yaml")
    >>> config.version
    '1.0'
    >>> config.extraction.concurrency
    5
    """
    file_path = Path(path)

    if not file_path.exists():
        logger.error("Configuration file not found", file_path=str(file_path))
        raise FileNotFoundError(f"Configuration file not found: {file_path}")

    logger.debug("Loading workflow configuration", file_path=str(file_path))

    content = file_path.read_text(encoding="utf-8")
    data = yaml.safe_load(content)

    config = NewsWorkflowConfig.model_validate(data)

    logger.info(
        "Workflow configuration loaded successfully",
        file_path=str(file_path),
        version=config.version,
    )

    return config


# Export all public symbols
__all__ = [
    "ExtractionConfig",
    "FilteringConfig",
    "GitHubConfig",
    "NewsWorkflowConfig",
    "OutputConfig",
    "RssConfig",
    "SummarizationConfig",
    "load_config",
]

"""Output sinks for the news package.

This module provides various output destinations for news articles, including
file-based output (JSON), GitHub Issue/Project output, and report data output.

Available Sinks
---------------
FileSink
    JSON file output with configurable path and append/overwrite modes.
GitHubSink
    GitHub Issue/Project output with duplicate checking and Project integration.
"""

from .file import FileSink, WriteMode
from .github import GitHubSink, GitHubSinkConfig

__all__ = [
    "FileSink",
    "GitHubSink",
    "GitHubSinkConfig",
    "WriteMode",
]

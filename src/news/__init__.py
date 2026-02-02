"""news package.

A generic news collection package for fetching news from various data sources
and writing to various output destinations.

Core Models
-----------
Article
    Unified news article model.
ArticleSource
    Enumeration of article sources.
ContentType
    Enumeration of content types.
FetchResult
    Result of a news fetch operation.

Sinks
-----
FileSink
    JSON file output sink.
WriteMode
    Write mode enumeration (OVERWRITE/APPEND).

Protocol Classes
----------------
SinkProtocol
    Protocol for output destinations.
SinkType
    Enumeration of sink types.
"""

from utils_core.logging import get_logger

from .core.article import Article, ArticleSource, ContentType, Provider, Thumbnail
from .core.result import FetchResult, RetryConfig
from .core.sink import SinkProtocol, SinkType
from .sinks.file import FileSink, WriteMode
from .summarizer import Summarizer

__all__ = [
    "Article",
    "ArticleSource",
    "ContentType",
    "FetchResult",
    "FileSink",
    "Provider",
    "RetryConfig",
    "SinkProtocol",
    "SinkType",
    "Summarizer",
    "Thumbnail",
    "WriteMode",
    "get_logger",
]

__version__ = "0.1.0"

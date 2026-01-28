"""Core functionality of the news package."""

from .article import (
    Article,
    ArticleSource,
    ContentType,
    Provider,
    Thumbnail,
)
from .errors import (
    NewsError,
    RateLimitError,
    SourceError,
    ValidationError,
)
from .processor import (
    ProcessorProtocol,
    ProcessorType,
)
from .result import (
    FetchResult,
    RetryConfig,
)
from .sink import (
    SinkProtocol,
    SinkType,
)
from .source import (
    SourceProtocol,
)

__all__: list[str] = [
    "Article",
    "ArticleSource",
    "ContentType",
    "FetchResult",
    "NewsError",
    "ProcessorProtocol",
    "ProcessorType",
    "Provider",
    "RateLimitError",
    "RetryConfig",
    "SinkProtocol",
    "SinkType",
    "SourceError",
    "SourceProtocol",
    "Thumbnail",
    "ValidationError",
]

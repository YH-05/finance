"""Core functionality of the news package."""

from .article import (
    Article,
    ArticleSource,
    ContentType,
    Provider,
    Thumbnail,
)

__all__: list[str] = [
    "Article",
    "ArticleSource",
    "ContentType",
    "Provider",
    "Thumbnail",
]

"""Core functionality of the rss package."""

from .diff_detector import DiffDetector
from .parser import FeedParser

__all__: list[str] = ["DiffDetector", "FeedParser"]

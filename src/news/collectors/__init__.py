"""Collectors module for news data collection.

This module provides collector implementations for gathering news articles
from various sources (RSS feeds, yfinance, web scraping).

The BaseCollector ABC defines the interface that all collectors must implement.
"""

from news.collectors.base import BaseCollector

__all__ = ["BaseCollector"]

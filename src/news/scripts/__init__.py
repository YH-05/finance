"""Scripts module for the news package.

Provides CLI scripts for automated news collection workflows.

Available Scripts
-----------------
collect
    Automated news collection script with CLI interface.
    Supports cron-based scheduling, config file specification,
    source filtering, and dry-run mode.

Usage
-----
>>> python -m news.scripts.collect
>>> python -m news.scripts.collect --source yfinance_ticker --dry-run
>>> python -m news.scripts.collect --config data/config/news_sources.yaml
"""

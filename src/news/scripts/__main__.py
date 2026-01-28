"""Entry point for ``python -m news.scripts.collect``.

This module allows running the news collection script as a module:

    python -m news.scripts.collect
    python -m news.scripts.collect --source yfinance_ticker --dry-run
    python -m news.scripts.collect --config data/config/news_sources.yaml
"""

import sys

from .collect import main

sys.exit(main())

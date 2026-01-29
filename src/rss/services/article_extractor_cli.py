"""CLI script for ArticleExtractor.

This module provides a command-line interface for extracting article content
from URLs using trafilatura.

Examples
--------
Single URL extraction:
    $ uv run python -m rss.services.article_extractor_cli "https://example.com/article"

Multiple URLs:
    $ uv run python -m rss.services.article_extractor_cli "url1" "url2" "url3"

With custom timeout:
    $ uv run python -m rss.services.article_extractor_cli --timeout 60 "https://example.com/article"
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from typing import Any

from .article_extractor import ArticleExtractor


def main() -> None:
    """Run the ArticleExtractor CLI."""
    parser = argparse.ArgumentParser(
        description="Extract article content from URLs using trafilatura",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s "https://example.com/article"
  %(prog)s --timeout 60 "https://example.com/article"
  %(prog)s "url1" "url2" "url3"
""",
    )
    parser.add_argument(
        "urls",
        nargs="+",
        help="One or more URLs to extract content from",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=30,
        help="Request timeout in seconds (default: 30)",
    )
    parser.add_argument(
        "--rate-limit",
        type=float,
        default=1.0,
        help="Rate limit between requests in seconds (default: 1.0)",
    )

    args = parser.parse_args()

    async def run_extraction() -> list[dict[str, Any]]:
        extractor = ArticleExtractor(timeout=args.timeout)

        if len(args.urls) == 1:
            result = await extractor.extract(args.urls[0])
            return [
                {
                    "url": result.url,
                    "status": result.status.value,
                    "title": result.title,
                    "text": result.text,
                    "author": result.author,
                    "date": result.date,
                    "source": result.source,
                    "language": result.language,
                    "extraction_method": result.extraction_method,
                    "error": result.error,
                }
            ]
        else:
            results = await extractor.extract_batch(
                args.urls,
                rate_limit=args.rate_limit,
            )
            return [
                {
                    "url": r.url,
                    "status": r.status.value,
                    "title": r.title,
                    "text": r.text,
                    "author": r.author,
                    "date": r.date,
                    "source": r.source,
                    "language": r.language,
                    "extraction_method": r.extraction_method,
                    "error": r.error,
                }
                for r in results
            ]

    results = asyncio.run(run_extraction())

    # Output as JSON (single result unwrapped, multiple as array)
    if len(results) == 1:
        print(json.dumps(results[0], ensure_ascii=False, indent=2))
    else:
        print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

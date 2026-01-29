"""
get_finance_news.py
"""

import datetime
import json
from pathlib import Path

import feedparser


class RSSFeed:
    def __init__(self):
        self.rss_presets_json_path: Path = Path(
            "/Users/yukihata/Desktop/finance/data/config/rss-presets.json"
        )

    def load_rss_list(self) -> list[dict]:
        with open(self.rss_presets_json_path) as f:
            rss = json.load(f)["presets"]
            rss = [s for s in rss if s["enabled"]]

        return rss

    def get_cnbc_news_list(self) -> list[dict]:
        all_rss_list = self.load_rss_list()
        cnbc_rss_list = [s for s in all_rss_list if s["title"].startswith("CNBC")]

        return cnbc_rss_list

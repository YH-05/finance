"""Custom company scrapers for Tier 3 sites requiring special handling.

Contains company-specific scraper implementations that inherit from
``BaseCompanyScraper`` and override ``extract_article_list`` for sites
with non-standard HTML structures (SPA, JS-heavy, etc.).
"""

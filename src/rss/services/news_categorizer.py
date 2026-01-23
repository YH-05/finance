"""News categorizer module for classifying financial news articles.

This module provides functionality to automatically categorize financial news
based on keywords matching in title and content.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any


# Logger lazy initialization to avoid circular imports
def _get_logger() -> Any:
    try:
        from ..utils.logging_config import get_logger

        return get_logger(__name__, module="news_categorizer")
    except ImportError:
        import logging

        return logging.getLogger(__name__)


logger: Any = _get_logger()


class NewsCategory(str, Enum):
    """News category types.

    Attributes
    ----------
    INDEX : str
        Stock index related news (S&P 500, NASDAQ, Dow Jones, etc.)
    MAG7 : str
        Magnificent 7 company related news (Apple, Microsoft, etc.)
    SECTOR : str
        Sector analysis related news (technology, energy, etc.)
    MACRO : str
        Macroeconomic related news (Fed, interest rates, etc.)
    THEME : str
        Investment theme related news (AI, semiconductor, EV, etc.)
    OTHER : str
        News that does not fit into above categories
    """

    INDEX = "index"
    MAG7 = "mag7"
    SECTOR = "sector"
    MACRO = "macro"
    THEME = "theme"
    OTHER = "other"


@dataclass
class CategorizationResult:
    """Result of news categorization.

    Attributes
    ----------
    category : NewsCategory
        Determined category for the news item
    confidence : float
        Confidence score between 0.0 and 1.0
    matched_keywords : list[str]
        List of keywords that matched during categorization
    """

    category: NewsCategory
    confidence: float
    matched_keywords: list[str]


# Keyword definitions for each category
# Priority order: INDEX > MAG7 > MACRO > SECTOR > THEME > OTHER

INDEX_KEYWORDS: list[str] = [
    # US indices
    "s&p 500",
    "s&p500",
    "sp500",
    "nasdaq",
    "dow jones",
    "djia",
    "russell 2000",
    "russell2000",
    "vix",
    # Japanese indices
    "日経平均",
    "日経225",
    "nikkei",
    "topix",
    # European indices
    "ftse",
    "dax",
    "stoxx",
    "cac 40",
    # Index-related terms
    "stock index",
    "株価指数",
    "指数",
]

MAG7_KEYWORDS: list[str] = [
    # Apple
    "apple",
    "aapl",
    "iphone",
    "アップル",
    # Microsoft
    "microsoft",
    "msft",
    "azure",
    "マイクロソフト",
    # Google/Alphabet
    "google",
    "googl",
    "goog",
    "alphabet",
    "グーグル",
    # Amazon
    "amazon",
    "amzn",
    "aws",
    "アマゾン",
    # NVIDIA
    "nvidia",
    "nvda",
    "エヌビディア",
    # Meta
    "meta platforms",
    "meta",
    "facebook",
    "メタ",
    # Tesla
    "tesla",
    "tsla",
    "テスラ",
]

MACRO_KEYWORDS: list[str] = [
    # Central banks
    "fed",
    "federal reserve",
    "fomc",
    "boj",
    "ecb",
    "日銀",
    "中央銀行",
    # Interest rates
    "interest rate",
    "金利",
    "利上げ",
    "利下げ",
    "rate cut",
    "rate hike",
    # Inflation
    "inflation",
    "cpi",
    "インフレ",
    "物価",
    # GDP and economy
    "gdp",
    "economic growth",
    "recession",
    "景気",
    # Employment
    "employment",
    "unemployment",
    "payroll",
    "non-farm",
    "nonfarm",
    "jobless",
    "雇用",
    "失業率",
    # Bond market
    "treasury",
    "yield",
    "国債",
    "債券",
]

SECTOR_KEYWORDS: list[str] = [
    # Sector names
    "technology sector",
    "tech sector",
    "energy sector",
    "healthcare sector",
    "healthcare stocks",
    "financial sector",
    "financials",
    "consumer discretionary",
    "consumer staples",
    "industrials",
    "materials",
    "utilities",
    "real estate",
    "pharmaceutical",
    # Sector-related terms
    "sector rotation",
    "sector performance",
    "セクター",
    "業種",
]

THEME_KEYWORDS: list[str] = [
    # AI
    "artificial intelligence",
    "ai investment",
    "ai stocks",
    "generative ai",
    "人工知能",
    "生成ai",
    # Semiconductor
    "semiconductor",
    "chip",
    "半導体",
    # EV
    "electric vehicle",
    "ev",
    "電気自動車",
    # Renewable energy
    "renewable energy",
    "clean energy",
    "solar",
    "wind power",
    "再生可能エネルギー",
    "クリーンエネルギー",
    # Other themes
    "blockchain",
    "cryptocurrency",
    "quantum computing",
    "space economy",
    "cybersecurity",
]


class NewsCategorizer:
    """Categorizer for financial news articles.

    This class categorizes news articles into predefined categories
    based on keyword matching in title and content.

    The priority order for categories when multiple matches occur is:
    INDEX > MAG7 > MACRO > SECTOR > THEME > OTHER

    Examples
    --------
    >>> categorizer = NewsCategorizer()
    >>> result = categorizer.categorize(
    ...     title="S&P 500 hits record high",
    ...     content="The index continued its rally..."
    ... )
    >>> result.category
    <NewsCategory.INDEX: 'index'>
    """

    def __init__(self) -> None:
        """Initialize the NewsCategorizer with keyword sets."""
        logger.debug("Initializing NewsCategorizer")
        # Store keywords as sets for O(1) lookup, lowercased
        self._index_keywords = {kw.lower() for kw in INDEX_KEYWORDS}
        self._mag7_keywords = {kw.lower() for kw in MAG7_KEYWORDS}
        self._macro_keywords = {kw.lower() for kw in MACRO_KEYWORDS}
        self._sector_keywords = {kw.lower() for kw in SECTOR_KEYWORDS}
        self._theme_keywords = {kw.lower() for kw in THEME_KEYWORDS}

        # Categories in priority order
        self._categories_in_order: list[tuple[NewsCategory, set[str]]] = [
            (NewsCategory.INDEX, self._index_keywords),
            (NewsCategory.MAG7, self._mag7_keywords),
            (NewsCategory.MACRO, self._macro_keywords),
            (NewsCategory.SECTOR, self._sector_keywords),
            (NewsCategory.THEME, self._theme_keywords),
        ]
        logger.info(
            "NewsCategorizer initialized",
            index_keywords=len(self._index_keywords),
            mag7_keywords=len(self._mag7_keywords),
            macro_keywords=len(self._macro_keywords),
            sector_keywords=len(self._sector_keywords),
            theme_keywords=len(self._theme_keywords),
        )

    def categorize(
        self,
        title: str,
        content: str | None = None,
    ) -> CategorizationResult:
        """Categorize a single news article.

        Parameters
        ----------
        title : str
            News article title
        content : str | None
            News article content (optional)

        Returns
        -------
        CategorizationResult
            Categorization result with category, confidence, and matched keywords
        """
        logger.debug(
            "Categorizing news",
            title_length=len(title),
            content_length=len(content) if content else 0,
        )

        # Combine and lowercase text for matching
        text = (title + " " + (content or "")).lower()

        # Try each category in priority order
        for category, keywords in self._categories_in_order:
            matched = self._find_matched_keywords(text, keywords)
            if matched:
                # Calculate confidence based on number of matches
                confidence = min(len(matched) * 0.25, 1.0)
                logger.debug(
                    "Category matched",
                    category=category.value,
                    matched_count=len(matched),
                    confidence=confidence,
                )
                return CategorizationResult(
                    category=category,
                    confidence=confidence,
                    matched_keywords=matched,
                )

        # No match found, return OTHER
        logger.debug("No category matched, returning OTHER")
        return CategorizationResult(
            category=NewsCategory.OTHER,
            confidence=0.0,
            matched_keywords=[],
        )

    def categorize_batch(
        self,
        news_items: list[dict[str, str]],
    ) -> list[CategorizationResult]:
        """Categorize multiple news articles.

        Parameters
        ----------
        news_items : list[dict[str, str]]
            List of news items with 'title' and optional 'content' keys

        Returns
        -------
        list[CategorizationResult]
            List of categorization results
        """
        logger.debug("Batch categorization started", item_count=len(news_items))
        results = []
        for item in news_items:
            result = self.categorize(
                title=item.get("title", ""),
                content=item.get("content"),
            )
            results.append(result)

        # Log summary
        category_counts = {}
        for r in results:
            category_counts[r.category.value] = (
                category_counts.get(r.category.value, 0) + 1
            )
        logger.info(
            "Batch categorization completed",
            total_items=len(news_items),
            category_distribution=category_counts,
        )
        return results

    def _find_matched_keywords(
        self,
        text: str,
        keywords: set[str],
    ) -> list[str]:
        """Find all keywords that match in the text.

        Parameters
        ----------
        text : str
            Text to search in (already lowercased)
        keywords : set[str]
            Set of keywords to search for (already lowercased)

        Returns
        -------
        list[str]
            List of matched keywords
        """
        matched = []
        for keyword in keywords:
            if keyword in text:
                matched.append(keyword)
        return matched

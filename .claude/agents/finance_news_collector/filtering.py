"""Filtering logic for finance news collection.

金融ニュースのフィルタリングロジックを提供します。
"""

from rss.types import FeedItem


def matches_financial_keywords(item: FeedItem, filter_config: dict) -> bool:
    """Check if feed item matches financial keywords.

    Parameters
    ----------
    item : FeedItem
        Feed item to check
    filter_config : dict
        Filter configuration containing keyword rules

    Returns
    -------
    bool
        True if item matches financial keywords, False otherwise

    Examples
    --------
    >>> item = FeedItem(
    ...     item_id="1",
    ...     title="株価が上昇",
    ...     link="https://example.com",
    ...     published="2026-01-15T10:00:00Z",
    ...     summary="市場動向",
    ...     content="詳細",
    ...     author="著者",
    ...     fetched_at="2026-01-15T11:00:00Z",
    ... )
    >>> config = {
    ...     "keywords": {
    ...         "include": {"market": ["株価", "株式"]},
    ...     },
    ...     "filtering": {"min_keyword_matches": 1},
    ... }
    >>> matches_financial_keywords(item, config)
    True
    """
    # Combine all text fields for searching
    title = item.title or ""
    summary = item.summary or ""
    content = item.content or ""
    text = f"{title} {summary} {content}".lower()

    # Get include keywords from config
    include_keywords = filter_config.get("keywords", {}).get("include", {})

    # Count keyword matches
    match_count = 0
    for _category, keywords in include_keywords.items():
        for keyword in keywords:
            if keyword.lower() in text:
                match_count += 1

    # Check against minimum threshold
    filtering_config = filter_config.get("filtering", {})
    min_matches = filtering_config.get("min_keyword_matches", 1)

    return match_count >= min_matches


def is_excluded(item: FeedItem, filter_config: dict) -> bool:
    """Check if feed item should be excluded.

    Parameters
    ----------
    item : FeedItem
        Feed item to check
    filter_config : dict
        Filter configuration containing exclusion rules

    Returns
    -------
    bool
        True if item should be excluded, False otherwise

    Examples
    --------
    >>> item = FeedItem(
    ...     item_id="1",
    ...     title="サッカーの試合",
    ...     link="https://example.com",
    ...     published="2026-01-15T10:00:00Z",
    ...     summary="スポーツニュース",
    ...     content="詳細",
    ...     author="著者",
    ...     fetched_at="2026-01-15T11:00:00Z",
    ... )
    >>> config = {
    ...     "keywords": {
    ...         "include": {"market": ["株価"]},
    ...         "exclude": {"sports": ["サッカー"]},
    ...     },
    ... }
    >>> is_excluded(item, config)
    True
    """
    # Combine title and summary for exclusion check
    title = item.title or ""
    summary = item.summary or ""
    text = f"{title} {summary}".lower()

    # Get exclude keywords from config
    exclude_keywords = filter_config.get("keywords", {}).get("exclude", {})

    # Check for exclusion keywords
    for _category, keywords in exclude_keywords.items():
        for keyword in keywords:
            if keyword.lower() in text:
                # If item also has financial keywords, don't exclude
                return not matches_financial_keywords(item, filter_config)

    return False


def calculate_reliability_score(item: FeedItem, filter_config: dict) -> int:
    """Calculate reliability score for feed item.

    Parameters
    ----------
    item : FeedItem
        Feed item to score
    filter_config : dict
        Filter configuration containing source tier information

    Returns
    -------
    int
        Reliability score (0-100+)

    Examples
    --------
    >>> item = FeedItem(
    ...     item_id="1",
    ...     title="株価と為替の動向",
    ...     link="https://www.nikkei.com/article/test",
    ...     published="2026-01-15T10:00:00Z",
    ...     summary="金利政策",
    ...     content="詳細",
    ...     author="著者",
    ...     fetched_at="2026-01-15T11:00:00Z",
    ... )
    >>> config = {
    ...     "keywords": {
    ...         "include": {
    ...             "market": ["株価", "為替"],
    ...             "policy": ["金利"],
    ...         },
    ...     },
    ...     "sources": {
    ...         "tier1": ["nikkei.com"],
    ...         "tier2": ["asahi.com"],
    ...         "tier3": [],
    ...     },
    ... }
    >>> score = calculate_reliability_score(item, config)
    >>> score > 0
    True
    """
    sources = filter_config.get("sources", {})

    # Determine source tier
    tier = 0
    for tier_name, domains in sources.items():
        for domain in domains:
            if domain in item.link:
                if tier_name == "tier1":
                    tier = 3
                elif tier_name == "tier2":
                    tier = 2
                else:
                    tier = 1
                break
        if tier > 0:
            break

    # If no matching source found, score is 0
    if tier == 0:
        return 0

    # Count keyword matches for keyword match ratio
    title = item.title or ""
    summary = item.summary or ""
    content = item.content or ""
    text = f"{title} {summary} {content}".lower()

    keyword_matches = 0
    include_keywords = filter_config.get("keywords", {}).get("include", {})
    for _category, keywords in include_keywords.items():
        for keyword in keywords:
            if keyword.lower() in text:
                keyword_matches += 1

    # Calculate keyword match ratio
    # Avoid division by zero
    text_length = max(len(text), 1)
    keyword_match_ratio = keyword_matches / text_length

    # Calculate final score
    # tier (1-3) * keyword_match_ratio * 100
    score = tier * keyword_match_ratio * 100

    return int(score)

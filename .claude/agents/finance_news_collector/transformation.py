"""Data transformation for finance news collection.

RSSフィードアイテムをGitHub Issue形式に変換する機能を提供します。
"""

from rss.types import FeedItem

from .filtering import calculate_reliability_score


def convert_to_issue_format(item: FeedItem, filter_config: dict) -> dict[str, str]:
    """Convert FeedItem to GitHub Issue format.

    Parameters
    ----------
    item : FeedItem
        Feed item to convert
    filter_config : dict
        Filter configuration for reliability scoring

    Returns
    -------
    dict[str, str]
        Dictionary with 'title' and 'body' keys for GitHub Issue

    Examples
    --------
    >>> item = FeedItem(
    ...     item_id="1",
    ...     title="株価が上昇",
    ...     link="https://www.nikkei.com/article/test",
    ...     published="2026-01-15T10:00:00Z",
    ...     summary="市場動向",
    ...     content="詳細な内容",
    ...     author="記者A",
    ...     fetched_at="2026-01-15T11:00:00Z",
    ... )
    >>> config = {
    ...     "sources": {
    ...         "tier1": ["nikkei.com"],
    ...         "tier2": [],
    ...         "tier3": [],
    ...     },
    ... }
    >>> result = convert_to_issue_format(item, config)
    >>> result["title"]
    '株価が上昇'
    >>> "## 概要" in result["body"]
    True
    """
    # Calculate reliability score
    reliability_score = calculate_reliability_score(item, filter_config)

    # Extract category from config if available
    category = filter_config.get("category", "finance")

    # Build issue title (same as feed item title)
    issue_title = item.title

    # Build issue body in markdown format
    body_parts = []

    # Summary section
    body_parts.append("## 概要")
    body_parts.append("")
    if item.summary:
        body_parts.append(item.summary)
    else:
        body_parts.append("（要約なし）")
    body_parts.append("")

    # Source information section
    body_parts.append("## 情報源")
    body_parts.append("")
    body_parts.append(f"- **URL**: {item.link}")

    if item.published:
        body_parts.append(f"- **公開日**: {item.published}")

    body_parts.append(f"- **信頼性スコア**: {reliability_score}")

    if "category" in filter_config:
        body_parts.append(f"- **カテゴリ**: {category}")

    if item.author:
        body_parts.append(f"- **著者**: {item.author}")

    body_parts.append("")

    # Detailed content section
    body_parts.append("## 詳細")
    body_parts.append("")
    if item.content:
        body_parts.append(item.content)
    else:
        body_parts.append("（詳細なし）")
    body_parts.append("")

    # Footer with auto-generation note
    body_parts.append("---")
    body_parts.append("")
    body_parts.append(
        "**自動収集**: このIssueは finance-news-collector エージェントによって自動作成されました。"
    )

    # Join all parts
    issue_body = "\n".join(body_parts)

    return {
        "title": issue_title,
        "body": issue_body,
    }

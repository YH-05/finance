"""RSS MCP API デモスクリプト.

RSS パッケージの API を直接使用して、金融ニュースを取得するデモスクリプト。

Usage
-----
    $ uv run python examples/rss_api_demo.py
"""

from __future__ import annotations

from pathlib import Path

from rss.services.feed_manager import FeedManager
from rss.services.feed_reader import FeedReader
from rss.utils.logging_config import get_logger

logger = get_logger(__name__)

# データディレクトリ
DATA_DIR = Path("data/raw/rss")


def demo_list_feeds() -> None:
    """フィード一覧を取得するデモ.

    全フィードと金融カテゴリのフィードを取得し、詳細情報を表示します。

    Examples
    --------
    >>> demo_list_feeds()
    全フィード数: 5
    金融フィード数: 3
    """
    logger.debug("Starting demo_list_feeds")

    print("\n" + "=" * 60)
    print("Demo 1: フィード一覧の取得")
    print("=" * 60)

    try:
        manager = FeedManager(DATA_DIR)

        # 全フィードを取得
        all_feeds = manager.list_feeds()
        logger.info("Retrieved all feeds", feed_count=len(all_feeds))
        print(f"\n全フィード数: {len(all_feeds)}")

        # 金融カテゴリのフィードのみ取得
        finance_feeds = manager.list_feeds(category="finance", enabled_only=True)
        logger.info("Retrieved finance feeds", feed_count=len(finance_feeds))
        print(f"金融フィード数: {len(finance_feeds)}")

        print("\n金融フィード一覧:")
        for feed in finance_feeds:
            print(f"- {feed.title}")
            print(f"  URL: {feed.url}")
            print(f"  最終取得: {feed.last_fetched}")
            print(f"  ステータス: {feed.last_status}")
            print()

    except Exception as e:
        logger.error("Failed to list feeds", error=str(e), exc_info=True)
        raise


def demo_get_items() -> None:
    """記事一覧を取得するデモ.

    全フィードから最新記事を取得し、上位5件の詳細を表示します。

    Examples
    --------
    >>> demo_get_items()
    取得した記事数: 10
    最新記事:
    1. Market Update...
    """
    logger.debug("Starting demo_get_items")

    print("\n" + "=" * 60)
    print("Demo 2: 記事一覧の取得")
    print("=" * 60)

    try:
        reader = FeedReader(DATA_DIR)

        # 金融フィードから最新10件を取得
        items = reader.get_items(feed_id=None, limit=10)
        logger.info("Retrieved items", item_count=len(items))
        print(f"\n取得した記事数: {len(items)}")

        print("\n最新記事:")
        for i, item in enumerate(items[:5], 1):
            print(f"\n{i}. {item.title}")
            print(f"   公開日: {item.published}")
            print(f"   URL: {item.link}")
            if item.summary:
                summary = (
                    item.summary[:100] + "..."
                    if len(item.summary) > 100
                    else item.summary
                )
                print(f"   要約: {summary}")

    except Exception as e:
        logger.error("Failed to get items", error=str(e), exc_info=True)
        raise


def demo_get_items_by_feed() -> None:
    """特定フィードから記事を取得するデモ.

    金融カテゴリから特定のフィード（Yahoo Financeを優先）を選択し、
    最新5件の記事を取得・表示します。

    Examples
    --------
    >>> demo_get_items_by_feed()
    フィード: Yahoo Finance - Market News
    取得した記事数: 5
    """
    logger.debug("Starting demo_get_items_by_feed")

    print("\n" + "=" * 60)
    print("Demo 3: 特定フィードからの記事取得")
    print("=" * 60)

    try:
        manager = FeedManager(DATA_DIR)
        reader = FeedReader(DATA_DIR)

        # Yahoo Finance フィードを取得
        finance_feeds = manager.list_feeds(category="finance")
        if not finance_feeds:
            logger.warning("No finance feeds found")
            print("金融フィードが見つかりません")
            return

        yahoo_feed = next(
            (f for f in finance_feeds if "Yahoo" in f.title), finance_feeds[0]
        )
        logger.info(
            "Selected feed", feed_title=yahoo_feed.title, feed_id=yahoo_feed.feed_id
        )
        print(f"\nフィード: {yahoo_feed.title}")

        # Yahoo Finance から最新5件を取得
        items = reader.get_items(feed_id=yahoo_feed.feed_id, limit=5)
        logger.info(
            "Retrieved items from feed",
            item_count=len(items),
            feed_id=yahoo_feed.feed_id,
        )
        print(f"取得した記事数: {len(items)}")

        print("\n記事一覧:")
        for i, item in enumerate(items, 1):
            print(f"\n{i}. {item.title}")
            print(f"   公開日: {item.published}")
            print(f"   URL: {item.link}")

    except Exception as e:
        logger.error("Failed to get items by feed", error=str(e), exc_info=True)
        raise


def demo_search_items() -> None:
    """キーワード検索のデモ.

    指定したキーワードで記事を検索し、上位5件を表示します。

    Examples
    --------
    >>> demo_search_items()
    キーワード "market" の検索結果: 10件
    """
    logger.debug("Starting demo_search_items")

    print("\n" + "=" * 60)
    print("Demo 4: キーワード検索")
    print("=" * 60)

    try:
        reader = FeedReader(DATA_DIR)

        # "market" というキーワードで検索
        query = "market"
        logger.debug("Searching items", query=query, category="finance")

        items = reader.search_items(
            query=query,
            category="finance",
            fields=["title", "summary", "content"],
            limit=10,
        )

        logger.info("Search completed", query=query, result_count=len(items))
        print(f'\nキーワード "{query}" の検索結果: {len(items)}件')

        if items:
            print("\n検索結果:")
            for i, item in enumerate(items[:5], 1):
                print(f"\n{i}. {item.title}")
                print(f"   公開日: {item.published}")
                print(f"   URL: {item.link}")

    except Exception as e:
        logger.error("Failed to search items", error=str(e), exc_info=True)
        raise


def demo_pagination() -> None:
    """ページネーションのデモ.

    記事を5件ずつ2ページに分けて取得し、各ページの記事タイトルを表示します。

    Examples
    --------
    >>> demo_pagination()
    1ページ目: 5件
    2ページ目: 5件
    """
    logger.debug("Starting demo_pagination")

    print("\n" + "=" * 60)
    print("Demo 5: ページネーション")
    print("=" * 60)

    try:
        reader = FeedReader(DATA_DIR)

        # 1ページ目（最新5件）
        page1 = reader.get_items(limit=5, offset=0)
        logger.info("Retrieved page 1", item_count=len(page1))
        print(f"\n1ページ目: {len(page1)}件")
        for item in page1:
            print(f"- {item.title}")

        # 2ページ目（次の5件）
        page2 = reader.get_items(limit=5, offset=5)
        logger.info("Retrieved page 2", item_count=len(page2))
        print(f"\n2ページ目: {len(page2)}件")
        for item in page2:
            print(f"- {item.title}")

    except Exception as e:
        logger.error("Failed to demonstrate pagination", error=str(e), exc_info=True)
        raise


def main() -> None:
    """メイン関数.

    RSS MCP APIの各機能を順次デモンストレーションします。

    Examples
    --------
    >>> main()
    RSS MCP API デモスクリプト
    ...
    デモ完了
    """
    logger.info("Starting RSS MCP API demo script")

    print("\n" + "=" * 60)
    print("RSS MCP API デモスクリプト")
    print("=" * 60)

    try:
        # デモ1: フィード一覧の取得
        demo_list_feeds()

        # デモ2: 記事一覧の取得
        demo_get_items()

        # デモ3: 特定フィードからの記事取得
        demo_get_items_by_feed()

        # デモ4: キーワード検索
        demo_search_items()

        # デモ5: ページネーション
        demo_pagination()

        print("\n" + "=" * 60)
        print("デモ完了")
        print("=" * 60 + "\n")

        logger.info("Demo script completed successfully")

    except Exception as e:
        logger.error("Demo script failed", error=str(e), exc_info=True)
        print(f"\nエラーが発生しました: {e!s}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""直近24時間のRSS記事を一覧化するスクリプト."""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from pathlib import Path

from rss import FeedFetcher, FeedReader


async def main() -> None:
    """メイン処理."""
    data_dir = Path("data/raw/rss")

    print("=" * 80)
    print("RSS記事取得開始")
    print("=" * 80)

    # 1. 全フィードを取得
    print("\n[1] 全フィードを取得中...")
    fetcher = FeedFetcher(data_dir)
    results = await fetcher.fetch_all_async()

    # 取得結果のサマリー表示
    success_count = sum(1 for r in results if r.success)
    total_new = sum(r.new_items for r in results if r.success)

    print(f"✓ 完了: {success_count}/{len(results)} フィード")
    print(f"✓ 新規記事: {total_new} 件")

    for result in results:
        if result.success:
            print(f"  - {result.feed_id[:8]}: {result.new_items} 件の新規記事")
        else:
            print(f"  - {result.feed_id[:8]}: 失敗 ({result.error_message})")

    # 2. フィード情報を取得
    print("\n[2] フィード情報を取得中...")
    import json

    feeds_file = data_dir / "feeds.json"
    with feeds_file.open("r", encoding="utf-8") as f:
        feeds_data = json.load(f)

    feed_map = {feed["feed_id"]: feed["title"] for feed in feeds_data.get("feeds", [])}

    # 3. 各フィードから直近24時間の記事を取得
    print("\n[3] 直近24時間の記事を取得中...")
    reader = FeedReader(data_dir)

    # 24時間前のタイムスタンプ
    now = datetime.now(timezone.utc)
    yesterday = now - timedelta(hours=24)

    # 各フィードから記事を取得
    recent_items = []
    for feed_id, feed_title in feed_map.items():
        # 各フィードからアイテムを取得
        items = reader.get_items(feed_id=feed_id, limit=100)

        for item in items:
            # published が None の場合は fetched_at を使用
            pub_time_str = item.published or item.fetched_at
            if pub_time_str:
                # ISO 8601 形式のパース
                try:
                    pub_time = datetime.fromisoformat(
                        pub_time_str.replace("Z", "+00:00")
                    )
                    if pub_time >= yesterday:
                        recent_items.append((pub_time, feed_id, feed_title, item))
                except (ValueError, AttributeError):
                    # パース失敗した場合はスキップ
                    continue

    # 新しい順にソート
    recent_items.sort(key=lambda x: x[0], reverse=True)

    # 4. 結果を表示
    print(f"\n✓ 直近24時間の記事: {len(recent_items)} 件")
    print("=" * 80)

    if not recent_items:
        print("\n直近24時間の記事はありませんでした。")
        return

    # 記事を表示
    print("\n📰 記事一覧:\n")
    for idx, (pub_time, feed_id, feed_title, item) in enumerate(recent_items, 1):
        # フィード名を使用
        pass  # feed_title は既に取得済み

        # 時間差を計算
        time_diff = now - pub_time
        hours_ago = int(time_diff.total_seconds() / 3600)

        print(f"{idx}. [{feed_title}]")
        print(f"   {item.title}")
        print(f"   {item.link}")
        print(f"   {hours_ago}時間前 ({pub_time.strftime('%Y-%m-%d %H:%M:%S %Z')})")

        if item.summary:
            # サマリーを100文字に制限
            summary = (
                item.summary[:100] + "..." if len(item.summary) > 100 else item.summary
            )
            # 改行を除去
            summary = summary.replace("\n", " ").replace("\r", " ")
            print(f"   📝 {summary}")

        print()

    print("=" * 80)
    print(f"合計: {len(recent_items)} 件の記事")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())

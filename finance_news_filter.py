#!/usr/bin/env python3
"""
金融ニュース収集・フィルタリングスクリプト

RSSフィードから金融ニュースを収集し、フィルタリングを実行します。
dry-runモードでは、GitHub Projectへの投稿は行わず、収集・フィルタリング結果のみを表示します。
"""

import json
from pathlib import Path
from typing import Any


def load_filter_config(config_path: Path) -> dict[str, Any]:
    """フィルター設定を読み込む"""
    with open(config_path) as f:
        return json.load(f)


def load_feed_items(feed_dir: Path) -> list[dict[str, Any]]:
    """フィードの記事を読み込む"""
    items_file = feed_dir / "items.json"
    with open(items_file) as f:
        data = json.load(f)
        return data.get("items", [])


def matches_financial_keywords(
    item: dict[str, Any], filter_config: dict[str, Any]
) -> tuple[bool, int]:
    """金融キーワードにマッチするかチェック

    Returns:
        (マッチしたか, マッチ数)
    """
    # 検索対象テキスト
    title = item.get("title", "")
    summary = item.get("summary", "")
    content = item.get("content", "")
    text = f"{title} {summary} {content}".lower()

    # 金融キーワードチェック
    include_keywords = filter_config["keywords"]["include"]

    match_count = 0
    matched_keywords = []

    for category, keywords in include_keywords.items():
        for keyword in keywords:
            if keyword.lower() in text:
                match_count += 1
                matched_keywords.append(f"{category}:{keyword}")

    # 最低マッチ数チェック
    min_matches = filter_config["filtering"]["min_keyword_matches"]

    return match_count >= min_matches, match_count


def is_excluded(
    item: dict[str, Any], filter_config: dict[str, Any]
) -> tuple[bool, str | None]:
    """除外対象かチェック

    Returns:
        (除外するか, 除外理由)
    """
    title = item.get("title", "")
    summary = item.get("summary", "")
    text = f"{title} {summary}".lower()

    # 除外キーワードチェック
    exclude_keywords = filter_config["keywords"]["exclude"]

    for category, keywords in exclude_keywords.items():
        for keyword in keywords:
            if keyword.lower() in text:
                # 金融キーワードも含む場合は除外しない
                has_finance, _ = matches_financial_keywords(item, filter_config)
                if has_finance:
                    return False, None
                return True, f"{category}:{keyword}"

    return False, None


def calculate_reliability_score(
    item: dict[str, Any], filter_config: dict[str, Any], keyword_match_count: int
) -> int:
    """信頼性スコアを計算

    信頼性スコア = (Tier × キーワードマッチ数 × 10)
    - Tier1: 30 (日経、Reuters、Bloomberg等)
    - Tier2: 20 (朝日、読売、東洋経済等)
    - Tier3: 10 (その他)
    """
    link = item.get("link", "")
    sources = filter_config["sources"]

    # 情報源のTierを判定
    tier = 1  # デフォルトはTier3
    for tier_name, domains in sources.items():
        for domain in domains:
            if domain in link:
                if tier_name == "tier1":
                    tier = 3
                elif tier_name == "tier2":
                    tier = 2
                else:
                    tier = 1
                break
        if tier > 1:
            break

    # スコア計算
    score = tier * keyword_match_count * 10

    return score


def filter_items(
    items: list[dict[str, Any]], filter_config: dict[str, Any], limit: int = 10
) -> dict[str, Any]:
    """記事をフィルタリングする

    Returns:
        フィルタリング結果の統計情報とマッチした記事
    """
    stats = {
        "total": len(items),
        "keyword_matched": 0,
        "excluded": 0,
        "low_reliability": 0,
        "passed": 0,
        "filtered_items": [],
    }

    for item in items:
        # 金融キーワードマッチング
        has_finance, match_count = matches_financial_keywords(item, filter_config)

        if not has_finance:
            continue

        stats["keyword_matched"] += 1

        # 除外判定
        excluded, _exclude_reason = is_excluded(item, filter_config)

        if excluded:
            stats["excluded"] += 1
            continue

        # 信頼性スコアリング
        reliability_score = calculate_reliability_score(
            item, filter_config, match_count
        )
        min_score = filter_config["filtering"]["min_reliability_score"]

        if reliability_score < min_score:
            stats["low_reliability"] += 1
            continue

        # フィルタリング通過
        stats["passed"] += 1
        stats["filtered_items"].append(
            {
                "item": item,
                "match_count": match_count,
                "reliability_score": reliability_score,
            }
        )

        # limit数に達したら終了
        if stats["passed"] >= limit:
            break

    # スコアでソート
    stats["filtered_items"].sort(key=lambda x: x["reliability_score"], reverse=True)

    return stats


def main():
    # 設定ファイルの読み込み
    config_path = Path("data/config/finance-news-filter.json")
    print(f"[INFO] フィルター設定ファイル読み込み: {config_path}")
    filter_config = load_filter_config(config_path)
    print(
        f"[INFO] 最低キーワードマッチ数: {filter_config['filtering']['min_keyword_matches']}"
    )
    print(
        f"[INFO] 最低信頼性スコア: {filter_config['filtering']['min_reliability_score']}"
    )
    print()

    # 金融フィードの特定
    rss_dir = Path("data/raw/rss")
    feeds_file = rss_dir / "feeds.json"

    with open(feeds_file) as f:
        feeds_data = json.load(f)

    finance_feeds = [
        feed
        for feed in feeds_data["feeds"]
        if feed["category"] in ["finance", "market"]
    ]

    print(f"[INFO] 金融フィード数: {len(finance_feeds)}件")
    for feed in finance_feeds:
        print(f"  - {feed['title']} ({feed['category']})")
    print()

    # 各フィードから記事を取得してフィルタリング
    all_stats = {
        "total_articles": 0,
        "total_keyword_matched": 0,
        "total_excluded": 0,
        "total_low_reliability": 0,
        "total_passed": 0,
        "all_filtered_items": [],
    }

    for feed in finance_feeds:
        feed_id = feed["feed_id"]
        feed_dir = rss_dir / feed_id

        print(f"[INFO] 記事取得中: {feed['title']}")

        try:
            items = load_feed_items(feed_dir)
            print(f"[INFO] 記事数: {len(items)}件")

            # フィルタリング実行
            stats = filter_items(items, filter_config, limit=10)

            print("[INFO] フィルタリング結果:")
            print(f"  - 金融キーワードマッチ: {stats['keyword_matched']}件")
            print(f"  - 除外: {stats['excluded']}件")
            print(f"  - 信頼性スコア不足: {stats['low_reliability']}件")
            print(f"  - 通過: {stats['passed']}件")
            print()

            # 統計を集約
            all_stats["total_articles"] += stats["total"]
            all_stats["total_keyword_matched"] += stats["keyword_matched"]
            all_stats["total_excluded"] += stats["excluded"]
            all_stats["total_low_reliability"] += stats["low_reliability"]
            all_stats["total_passed"] += stats["passed"]

            # フィルタリング通過記事を追加
            for filtered in stats["filtered_items"]:
                all_stats["all_filtered_items"].append(
                    {"feed": feed["title"], **filtered}
                )

        except Exception as e:
            print(f"[ERROR] 記事取得失敗: {e}")
            print()
            continue

    # 全体統計を表示
    print("=" * 80)
    print("[INFO] 全体統計:")
    print(f"  - 総記事数: {all_stats['total_articles']}件")
    print(f"  - 金融キーワードマッチ: {all_stats['total_keyword_matched']}件")
    print(f"  - 除外: {all_stats['total_excluded']}件")
    print(f"  - 信頼性スコア不足: {all_stats['total_low_reliability']}件")
    print(f"  - フィルタリング通過: {all_stats['total_passed']}件")
    print("=" * 80)
    print()

    # スコア順にソート
    all_stats["all_filtered_items"].sort(
        key=lambda x: x["reliability_score"], reverse=True
    )

    # 上位10件を表示
    print("[INFO] フィルタリング通過記事（上位10件）:")
    print()

    for i, filtered in enumerate(all_stats["all_filtered_items"][:10], 1):
        item = filtered["item"]
        match_count = filtered["match_count"]
        reliability_score = filtered["reliability_score"]
        feed = filtered["feed"]

        print(f"[{i}] {item['title']}")
        print(f"    情報源: {feed}")
        print(f"    URL: {item['link']}")
        print(f"    公開日: {item['published']}")
        print(f"    キーワードマッチ数: {match_count}")
        print(f"    信頼性スコア: {reliability_score}")
        print()

    print("[INFO] dry-runモードのため、GitHub Projectへの投稿は行いません")
    print("[INFO] 処理完了")


if __name__ == "__main__":
    main()

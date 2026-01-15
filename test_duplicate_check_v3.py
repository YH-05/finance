#!/usr/bin/env python3
"""重複チェック機能のテストスクリプト v3

タイトル類似度チェックの動作を確認します。
"""

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class FeedItem:
    """RSSフィード記事"""

    title: str
    link: str
    published: str
    summary: str = ""


@dataclass
class GitHubIssue:
    """GitHub Issue"""

    number: int
    title: str
    url: str  # GitHub IssueのURL
    article_url: str  # 記事のURL


def load_filter_config() -> dict:
    """フィルター設定ファイルを読み込む"""
    config_path = Path("data/config/finance-news-filter.json")
    with open(config_path) as f:
        return json.load(f)


def calculate_title_similarity(title1: str, title2: str) -> float:
    """タイトルの類似度を計算（簡易版）"""
    words1 = set(title1.lower().split())
    words2 = set(title2.lower().split())

    if not words1 or not words2:
        return 0.0

    common = words1.intersection(words2)
    total = words1.union(words2)

    return len(common) / len(total)


def is_duplicate(item: FeedItem, existing_issues: list[GitHubIssue], threshold: float) -> tuple[bool, str]:
    """重複チェックを実行

    Returns:
        (is_duplicate, reason)
    """
    for issue in existing_issues:
        # URL完全一致チェック
        if item.link == issue.article_url:
            return True, f"URL完全一致: Issue #{issue.number}"

        # タイトル類似度チェック
        similarity = calculate_title_similarity(item.title, issue.title)
        if similarity >= threshold:
            return True, f"タイトル類似度 {similarity:.2f} (閾値: {threshold}): Issue #{issue.number}"

    return False, ""


def main():
    """メイン処理"""
    print("=" * 80)
    print("重複チェック機能テスト v3 - タイトル類似度チェック")
    print("=" * 80)
    print()

    # 1. フィルター設定読み込み
    print("[1] フィルター設定ファイル読み込み")
    filter_config = load_filter_config()
    threshold = filter_config["filtering"]["title_similarity_threshold"]
    print(f"    ✓ 類似度閾値: {threshold}")
    print()

    # 2. テスト用の既存Issue
    print("[2] テスト用の既存Issue")
    existing_issues = [
        GitHubIssue(
            number=171,
            title="Your wealth and investments are on the line if Trump torpedoes the Fed's independence",
            url="https://github.com/YH-05/finance/issues/171",
            article_url="https://www.marketwatch.com/story/example",
        ),
        GitHubIssue(
            number=172,
            title="Global Central Bankers Line Up to Support Fed Chair. Markets, Not So Much.",
            url="https://github.com/YH-05/finance/issues/172",
            article_url="https://www.barrons.com/articles/example",
        ),
    ]

    for issue in existing_issues:
        print(f"    - Issue #{issue.number}: {issue.title}")
    print()

    # 3. テストケース
    print("[3] テストケース")
    print()

    test_cases = [
        # ケース1: 完全一致（URLが異なる）
        FeedItem(
            title="Your wealth and investments are on the line if Trump torpedoes the Fed's independence",
            link="https://different-url.com/article1",
            published="2026-01-15T00:00:00Z",
        ),
        # ケース2: 類似度が高い（一部単語が異なる）
        FeedItem(
            title="Your wealth and investments would be on the line if Trump torpedoes Fed independence",
            link="https://different-url.com/article2",
            published="2026-01-15T00:00:00Z",
        ),
        # ケース3: 類似度が中程度
        FeedItem(
            title="Trump's actions could impact Fed independence and your investments",
            link="https://different-url.com/article3",
            published="2026-01-15T00:00:00Z",
        ),
        # ケース4: 類似度が低い（一部の単語のみ共通）
        FeedItem(
            title="Trump announces new policy on trade negotiations",
            link="https://different-url.com/article4",
            published="2026-01-15T00:00:00Z",
        ),
        # ケース5: 完全に異なる記事
        FeedItem(
            title="Bitcoin price reaches new all-time high",
            link="https://different-url.com/article5",
            published="2026-01-15T00:00:00Z",
        ),
    ]

    for i, item in enumerate(test_cases, 1):
        print(f"ケース{i}: {item.title}")

        # 類似度を計算
        for issue in existing_issues:
            similarity = calculate_title_similarity(item.title, issue.title)
            print(f"  vs Issue #{issue.number}: 類似度 {similarity:.4f}")

        # 重複チェック
        is_dup, reason = is_duplicate(item, existing_issues, threshold)

        if is_dup:
            print(f"  → 🔴 重複検出: {reason}")
        else:
            print(f"  → 🟢 新規記事")
        print()

    # 4. 閾値の妥当性検証
    print("=" * 80)
    print("閾値の妥当性検証")
    print("=" * 80)

    original_title = "Your wealth and investments are on the line if Trump torpedoes the Fed's independence"

    print(f"基準タイトル: {original_title}")
    print()

    variations = [
        ("完全一致", "Your wealth and investments are on the line if Trump torpedoes the Fed's independence"),
        ("1語変更", "Your wealth and investments would be on the line if Trump torpedoes the Fed's independence"),
        ("2語変更", "Your wealth and investments would be at risk if Trump torpedoes Fed independence"),
        ("5語変更", "Your investments could be at risk if Trump undermines Fed independence"),
        ("大幅変更", "Trump's potential interference with Fed independence threatens your financial security"),
        ("完全に異なる", "Bitcoin price surges to new record high amid market volatility"),
    ]

    print(f"類似度閾値: {threshold}")
    print()

    for desc, variant_title in variations:
        similarity = calculate_title_similarity(original_title, variant_title)
        status = "🔴 重複" if similarity >= threshold else "🟢 新規"

        print(f"{status} [{desc}] 類似度: {similarity:.4f}")
        if len(variant_title) > 80:
            print(f"     {variant_title[:77]}...")
        else:
            print(f"     {variant_title}")
        print()

    # 推奨閾値の提案
    print("=" * 80)
    print("推奨閾値の提案")
    print("=" * 80)
    print(f"現在の閾値: {threshold}")
    print()
    print("分析結果:")
    print("  - 0.85以上: 完全一致または1-2語の変更")
    print("  - 0.70-0.84: 一部の語句が異なるが同じ内容")
    print("  - 0.50-0.69: 関連するトピックだが異なる視点")
    print("  - 0.50未満: 異なる記事")
    print()
    print("推奨:")
    print("  - 保守的（重複を厳密に判定）: 0.90")
    print("  - バランス（現在の設定）: 0.85")
    print("  - 緩和（類似記事も重複とみなす）: 0.75")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""重複チェック機能のテストスクリプト

既存のGitHub Issues (#171-175) と同じ記事を再度取得し、
重複チェックが正しく機能することを確認します。
"""

import json
import subprocess
import sys
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


def load_rss_items() -> list[FeedItem]:
    """RSSデータファイルから記事を読み込む"""
    items = []
    rss_dir = Path("data/raw/rss")

    # 各フィードのitemsファイルを読み込み
    for items_file in rss_dir.glob("*/items.json"):
        with open(items_file) as f:
            data = json.load(f)
            # データは {"version": "1.0", "feed_id": "...", "items": [...]} の構造
            for item in data.get("items", []):
                items.append(
                    FeedItem(
                        title=item.get("title", ""),
                        link=item.get("link", ""),
                        published=item.get("published", ""),
                        summary=item.get("summary") or "",
                    )
                )

    return items


def get_existing_issues() -> list[GitHubIssue]:
    """既存のGitHub Issueを取得"""
    issues = []

    # Issue #171-175を個別に取得
    for issue_number in range(171, 176):
        try:
            result = subprocess.run(  # nosec B607
                [
                    "gh",
                    "issue",
                    "view",
                    str(issue_number),
                    "--repo",
                    "YH-05/finance",
                    "--json",
                    "number,title,url,body",
                ],
                capture_output=True,
                text=True,
                check=True,
            )

            issue_data = json.loads(result.stdout)

            # body から記事URLを抽出
            body = issue_data.get("body", "")
            article_url = ""
            for line in body.split("\n"):
                if line.startswith("- **URL**:"):
                    article_url = line.replace("- **URL**:", "").strip()
                    break

            issues.append(
                GitHubIssue(
                    number=issue_data["number"],
                    title=issue_data["title"],
                    url=issue_data["url"],
                    article_url=article_url,
                )
            )

        except subprocess.CalledProcessError as e:
            print(f"警告: Issue #{issue_number} の取得に失敗しました: {e}")

    return issues


def calculate_title_similarity(title1: str, title2: str) -> float:
    """タイトルの類似度を計算（簡易版）"""
    words1 = set(title1.lower().split())
    words2 = set(title2.lower().split())

    if not words1 or not words2:
        return 0.0

    common = words1.intersection(words2)
    total = words1.union(words2)

    return len(common) / len(total)


def is_duplicate(
    item: FeedItem, existing_issues: list[GitHubIssue], threshold: float
) -> tuple[bool, str]:
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
            return (
                True,
                f"タイトル類似度 {similarity:.2f} (閾値: {threshold}): Issue #{issue.number}",
            )

    return False, ""


def matches_financial_keywords(item: FeedItem, filter_config: dict) -> bool:
    """金融キーワードにマッチするかチェック"""
    text = f"{item.title} {item.summary}".lower()

    # 金融キーワードチェック
    include_keywords = filter_config["keywords"]["include"]

    match_count = 0
    for category, keywords in include_keywords.items():
        for keyword in keywords:
            if keyword.lower() in text:
                match_count += 1

    # 最低マッチ数チェック
    min_matches = filter_config["filtering"]["min_keyword_matches"]
    return match_count >= min_matches


def main():
    """メイン処理"""
    print("=" * 80)
    print("重複チェック機能テスト")
    print("=" * 80)
    print()

    # 1. フィルター設定読み込み
    print("[1] フィルター設定ファイル読み込み")
    filter_config = load_filter_config()
    threshold = filter_config["filtering"]["title_similarity_threshold"]
    print(f"    ✓ 類似度閾値: {threshold}")
    print()

    # 2. 既存Issue取得
    print("[2] 既存GitHub Issue取得（#171-175）")
    existing_issues = get_existing_issues()
    print(f"    ✓ 取得件数: {len(existing_issues)}件")
    for issue in existing_issues:
        print(f"      - Issue #{issue.number}: {issue.title}")
        print(f"        URL: {issue.article_url}")
    print()

    # 3. RSS記事取得
    print("[3] RSSデータから記事を取得")
    all_items = load_rss_items()
    print(f"    ✓ 総記事数: {len(all_items)}件")
    print()

    # 4. フィルタリング
    print("[4] 金融キーワードでフィルタリング")
    filtered_items = [
        item for item in all_items if matches_financial_keywords(item, filter_config)
    ]
    print(f"    ✓ フィルタリング後: {len(filtered_items)}件")
    print()

    # 5. 上位5件を選択
    print("[5] 上位5件を選択")
    top_items = filtered_items[:5]
    print(f"    ✓ 選択件数: {len(top_items)}件")
    print()

    # 6. 重複チェック実行
    print("[6] 重複チェック実行")
    print()

    duplicates = []
    new_items = []

    for i, item in enumerate(top_items, 1):
        is_dup, reason = is_duplicate(item, existing_issues, threshold)

        if is_dup:
            duplicates.append((item, reason))
            print(f"    [{i}] 🔴 重複検出")
            print(f"        タイトル: {item.title}")
            print(f"        URL: {item.link}")
            print(f"        理由: {reason}")
        else:
            new_items.append(item)
            print(f"    [{i}] 🟢 新規記事")
            print(f"        タイトル: {item.title}")
            print(f"        URL: {item.link}")
        print()

    # 7. 結果サマリー
    print("=" * 80)
    print("テスト結果サマリー")
    print("=" * 80)
    print(f"対象記事数: {len(top_items)}件")
    print(f"重複検出数: {len(duplicates)}件")
    print(f"新規記事数: {len(new_items)}件")
    print()

    if duplicates:
        print("【重複検出された記事】")
        for item, reason in duplicates:
            print(f"  - {item.title}")
            print(f"    URL: {item.link}")
            print(f"    理由: {reason}")
        print()

    if new_items:
        print("【新規記事】")
        for item in new_items:
            print(f"  - {item.title}")
            print(f"    URL: {item.link}")
        print()

    # 期待結果との比較
    print("=" * 80)
    print("期待結果との比較")
    print("=" * 80)
    expected_duplicates = 5
    expected_new = 0

    if len(duplicates) == expected_duplicates and len(new_items) == expected_new:
        print("✅ テスト成功: 期待通りの結果です")
        print(f"   - 重複検出数: {len(duplicates)}件（期待: {expected_duplicates}件）")
        print(f"   - 新規記事数: {len(new_items)}件（期待: {expected_new}件）")
        return 0
    else:
        print("❌ テスト失敗: 期待と異なる結果です")
        print(f"   - 重複検出数: {len(duplicates)}件（期待: {expected_duplicates}件）")
        print(f"   - 新規記事数: {len(new_items)}件（期待: {expected_new}件）")
        return 1


if __name__ == "__main__":
    sys.exit(main())

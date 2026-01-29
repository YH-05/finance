# P5-005: Publisher 重複チェック

## 概要

既存 Issue との重複をチェックする機能を実装する。

## フェーズ

Phase 5: GitHub Publisher

## 依存タスク

- P5-004: Publisher Project フィールド更新

## 成果物

- `src/news/publisher.py`（更新）

## 実装内容

```python
import subprocess
import json
from datetime import datetime, timedelta, timezone

class Publisher:
    async def _get_existing_issues(self, days: int = 7) -> set[str]:
        """直近N日のIssue URLを取得

        Parameters
        ----------
        days : int, optional
            取得対象期間（デフォルト: 7日）

        Returns
        -------
        set[str]
            既存IssueのURLセット
        """
        since_date = datetime.now(timezone.utc) - timedelta(days=days)

        result = subprocess.run(
            ["gh", "issue", "list",
             "--repo", self._repo,
             "--state", "all",
             "--limit", "500",
             "--json", "body,createdAt"],
            capture_output=True,
            text=True,
            check=True
        )

        issues = json.loads(result.stdout)
        urls = set()

        for issue in issues:
            created_at = datetime.fromisoformat(issue["createdAt"].replace("Z", "+00:00"))
            if created_at >= since_date:
                # Issue本文からURLを抽出（**URL**: https://... の形式）
                body = issue.get("body", "")
                if "**URL**:" in body:
                    for line in body.split("\n"):
                        if line.startswith("**URL**:"):
                            url = line.replace("**URL**:", "").strip()
                            urls.add(url)

        return urls

    def _is_duplicate(self, article: SummarizedArticle, existing_urls: set[str]) -> bool:
        """記事が重複しているか判定

        Parameters
        ----------
        article : SummarizedArticle
            要約済み記事
        existing_urls : set[str]
            既存IssueのURLセット

        Returns
        -------
        bool
            重複している場合True
        """
        article_url = str(article.extracted.collected.url)
        return article_url in existing_urls
```

## 受け入れ条件

- [ ] `gh issue list` で直近 7 日の Issue を取得
- [ ] Issue 本文から URL を抽出
- [ ] URL で照合して重複を検出
- [ ] 重複検出時は DUPLICATE ステータス
- [ ] pyright 型チェック成功

## 参照

- project.md: GitHub設定 - duplicate_check_days セクション

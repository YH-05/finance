# P5-004: Publisher Project フィールド更新

## 概要

gh project item-edit で Status と PublishedDate を更新する。

## フェーズ

Phase 5: GitHub Publisher

## 依存タスク

- P5-003: Publisher カテゴリ → GitHub Status 解決

## 成果物

- `src/news/publisher.py`（更新）

## 実装内容

```python
import subprocess
import json
from datetime import datetime

class Publisher:
    async def _create_issue(self, article: SummarizedArticle) -> tuple[int, str]:
        """Issue を作成

        Returns
        -------
        tuple[int, str]
            (Issue番号, Issue URL)
        """
        title = self._generate_issue_title(article)
        body = self._generate_issue_body(article)

        result = subprocess.run(
            ["gh", "issue", "create",
             "--repo", self._repo,
             "--title", title,
             "--body", body],
            capture_output=True,
            text=True,
            check=True
        )

        # gh issue create は Issue URL を返す
        issue_url = result.stdout.strip()
        issue_number = int(issue_url.split("/")[-1])

        return issue_number, issue_url

    async def _add_to_project(self, issue_number: int, article: SummarizedArticle) -> None:
        """Issue を Project に追加し、フィールドを設定

        Parameters
        ----------
        issue_number : int
            Issue 番号
        article : SummarizedArticle
            要約済み記事
        """
        # 1. Issue を Project に追加
        add_result = subprocess.run(
            ["gh", "project", "item-add", str(self._project_number),
             "--owner", "YH-05",
             "--url", f"https://github.com/{self._repo}/issues/{issue_number}"],
            capture_output=True,
            text=True,
            check=True
        )

        item_id = add_result.stdout.strip()

        # 2. Status フィールドを設定
        _, status_id = self._resolve_status(article)

        subprocess.run(
            ["gh", "project", "item-edit",
             "--project-id", self._project_id,
             "--id", item_id,
             "--field-id", self._status_field_id,
             "--single-select-option-id", status_id],
            check=True
        )

        # 3. PublishedDate フィールドを設定
        published = article.extracted.collected.published
        if published:
            date_str = published.strftime("%Y-%m-%d")
            subprocess.run(
                ["gh", "project", "item-edit",
                 "--project-id", self._project_id,
                 "--id", item_id,
                 "--field-id", self._published_date_field_id,
                 "--date", date_str],
                check=True
            )
```

## 受け入れ条件

- [ ] `gh issue create` で Issue を作成
- [ ] `gh project item-add` で Project に追加
- [ ] `gh project item-edit` で Status フィールドを設定
- [ ] `gh project item-edit` で PublishedDate フィールドを設定
- [ ] エラー時は適切な例外を発生
- [ ] pyright 型チェック成功

## 参照

- project.md: GitHub設定 セクション
- `src/news/sinks/github.py`: GitHubSink の実装パターン

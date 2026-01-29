# P5-006: Publisher ドライランモード

## 概要

dry_run オプションで Issue 作成をスキップする機能を実装する。

## フェーズ

Phase 5: GitHub Publisher

## 依存タスク

- P5-005: Publisher 重複チェック

## 成果物

- `src/news/publisher.py`（更新）

## 実装内容

```python
class Publisher:
    async def publish_batch(
        self,
        articles: list[SummarizedArticle],
        dry_run: bool = False,
    ) -> list[PublishedArticle]:
        """複数記事を公開（重複チェック含む）

        Parameters
        ----------
        articles : list[SummarizedArticle]
            要約済み記事リスト
        dry_run : bool, optional
            Trueの場合、Issue作成をスキップ

        Returns
        -------
        list[PublishedArticle]
            公開結果リスト
        """
        logger.info(
            "Starting batch publication",
            article_count=len(articles),
            dry_run=dry_run
        )

        # 重複チェック用に既存Issueを取得
        existing_urls = await self._get_existing_issues(
            days=self._config.github.duplicate_check_days
        )

        results: list[PublishedArticle] = []

        for article in articles:
            # 要約がない場合はスキップ
            if article.summary is None:
                results.append(PublishedArticle(
                    summarized=article,
                    issue_number=None,
                    issue_url=None,
                    publication_status=PublicationStatus.SKIPPED,
                    error_message="No summary available"
                ))
                continue

            # 重複チェック
            if self._is_duplicate(article, existing_urls):
                logger.info(
                    "Skipping duplicate article",
                    title=article.extracted.collected.title,
                    url=str(article.extracted.collected.url)
                )
                results.append(PublishedArticle(
                    summarized=article,
                    issue_number=None,
                    issue_url=None,
                    publication_status=PublicationStatus.DUPLICATE,
                ))
                continue

            # ドライランの場合は Issue 作成をスキップ
            if dry_run:
                logger.info(
                    "[DRY RUN] Would create issue",
                    title=article.extracted.collected.title
                )
                results.append(PublishedArticle(
                    summarized=article,
                    issue_number=None,
                    issue_url=None,
                    publication_status=PublicationStatus.SUCCESS,  # ドライランでも SUCCESS
                ))
                continue

            # Issue 作成
            try:
                issue_number, issue_url = await self._create_issue(article)
                await self._add_to_project(issue_number, article)

                results.append(PublishedArticle(
                    summarized=article,
                    issue_number=issue_number,
                    issue_url=issue_url,
                    publication_status=PublicationStatus.SUCCESS,
                ))

                # 作成した Issue の URL を既存リストに追加（重複防止）
                existing_urls.add(str(article.extracted.collected.url))

            except Exception as e:
                logger.error(
                    "Failed to create issue",
                    title=article.extracted.collected.title,
                    error=str(e)
                )
                results.append(PublishedArticle(
                    summarized=article,
                    issue_number=None,
                    issue_url=None,
                    publication_status=PublicationStatus.FAILED,
                    error_message=str(e)
                ))

        success_count = sum(1 for r in results if r.publication_status == PublicationStatus.SUCCESS)
        duplicate_count = sum(1 for r in results if r.publication_status == PublicationStatus.DUPLICATE)
        logger.info(
            "Batch publication completed",
            total=len(articles),
            success=success_count,
            duplicates=duplicate_count,
            failed=len(articles) - success_count - duplicate_count
        )

        return results
```

## 受け入れ条件

- [ ] `publish_batch(articles, dry_run=True)` で Issue 作成をスキップ
- [ ] ドライランでもログに "Would create issue" と出力
- [ ] 重複チェックは通常通り動作
- [ ] ドライラン時も SUCCESS ステータスを返す
- [ ] pyright 型チェック成功

## 参照

- project.md: CLI使用方法 - --dry-run オプション

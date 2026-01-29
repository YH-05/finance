# P6-002: Orchestrator WorkflowResult 生成

## 概要

ワークフロー実行結果を WorkflowResult モデルに集約する。

## フェーズ

Phase 6: オーケストレーター

## 依存タスク

- P6-001: Orchestrator 全コンポーネント統合
- P1-006: FailureRecord, WorkflowResult モデル作成

## 成果物

- `src/news/orchestrator.py`（更新）

## 実装内容

```python
from news.models import (
    CollectedArticle,
    ExtractedArticle,
    SummarizedArticle,
    PublishedArticle,
    WorkflowResult,
    FailureRecord,
    ExtractionStatus,
    SummarizationStatus,
    PublicationStatus,
)

class NewsWorkflowOrchestrator:
    def _build_result(
        self,
        collected: list[CollectedArticle],
        extracted: list[ExtractedArticle],
        summarized: list[SummarizedArticle],
        published: list[PublishedArticle],
        started_at: datetime,
        finished_at: datetime,
    ) -> WorkflowResult:
        """WorkflowResult を構築

        Parameters
        ----------
        collected, extracted, summarized, published
            各ステージの処理結果
        started_at, finished_at
            開始・終了時刻

        Returns
        -------
        WorkflowResult
            ワークフロー実行結果
        """
        # 抽出失敗の記録
        extraction_failures = [
            FailureRecord(
                url=str(e.collected.url),
                title=e.collected.title,
                stage="extraction",
                error=e.error_message or "Unknown error"
            )
            for e in extracted
            if e.extraction_status != ExtractionStatus.SUCCESS
        ]

        # 要約失敗の記録
        summarization_failures = [
            FailureRecord(
                url=str(s.extracted.collected.url),
                title=s.extracted.collected.title,
                stage="summarization",
                error=s.error_message or "Unknown error"
            )
            for s in summarized
            if s.summarization_status != SummarizationStatus.SUCCESS
        ]

        # 公開失敗の記録
        publication_failures = [
            FailureRecord(
                url=str(p.summarized.extracted.collected.url),
                title=p.summarized.extracted.collected.title,
                stage="publication",
                error=p.error_message or "Unknown error"
            )
            for p in published
            if p.publication_status == PublicationStatus.FAILED
        ]

        # 成功した公開記事
        published_success = [
            p for p in published
            if p.publication_status == PublicationStatus.SUCCESS
        ]

        # 重複記事数
        duplicates = sum(
            1 for p in published
            if p.publication_status == PublicationStatus.DUPLICATE
        )

        elapsed = (finished_at - started_at).total_seconds()

        return WorkflowResult(
            total_collected=len(collected),
            total_extracted=sum(1 for e in extracted if e.extraction_status == ExtractionStatus.SUCCESS),
            total_summarized=sum(1 for s in summarized if s.summarization_status == SummarizationStatus.SUCCESS),
            total_published=len(published_success),
            total_duplicates=duplicates,
            extraction_failures=extraction_failures,
            summarization_failures=summarization_failures,
            publication_failures=publication_failures,
            started_at=started_at,
            finished_at=finished_at,
            elapsed_seconds=elapsed,
            published_articles=published_success,
        )
```

## 受け入れ条件

- [ ] WorkflowResult が正しく構築される
- [ ] 件数（collected, extracted, summarized, published, duplicates）が正確
- [ ] 失敗記録（extraction_failures, summarization_failures, publication_failures）が正確
- [ ] 処理時間（started_at, finished_at, elapsed_seconds）が正確
- [ ] 成功した記事（published_articles）が含まれる
- [ ] pyright 型チェック成功

## 参照

- project.md: データモデル - WorkflowResult セクション

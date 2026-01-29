# P6-001: Orchestrator 全コンポーネント統合

## 概要

Collector → Extractor → Summarizer → Publisher のパイプラインを統合する。

## フェーズ

Phase 6: オーケストレーター

## 依存タスク

- P2-004: RSSCollector 日時フィルタリング実装
- P3-004: TrafilaturaExtractor リトライロジック
- P4-005: Summarizer リトライロジック
- P5-006: Publisher ドライランモード

## 成果物

- `src/news/orchestrator.py`（新規作成）

## 実装内容

```python
from news.collectors.rss import RSSCollector
from news.config import NewsWorkflowConfig, load_config
from news.extractors.trafilatura import TrafilaturaExtractor
from news.models import WorkflowResult, ExtractionStatus, SummarizationStatus, PublicationStatus
from news.publisher import Publisher
from news.summarizer import Summarizer
from utils_core.logging_config import get_logger

logger = get_logger(__name__)

class NewsWorkflowOrchestrator:
    """ニュース収集ワークフローのオーケストレーター

    Collector → Extractor → Summarizer → Publisher の
    パイプラインを統合して実行する。

    Parameters
    ----------
    config : NewsWorkflowConfig
        ワークフロー設定
    """

    def __init__(self, config: NewsWorkflowConfig) -> None:
        self._config = config
        self._collector = RSSCollector(config)
        self._extractor = TrafilaturaExtractor(
            min_body_length=config.extraction.min_body_length,
            max_retries=config.extraction.max_retries,
            timeout_seconds=config.extraction.timeout_seconds,
        )
        self._summarizer = Summarizer(config)
        self._publisher = Publisher(config)

    async def run(
        self,
        statuses: list[str] | None = None,
        max_articles: int | None = None,
        dry_run: bool = False,
    ) -> WorkflowResult:
        """ワークフローを実行

        Parameters
        ----------
        statuses : list[str] | None, optional
            対象Statusリスト（None の場合は全Status）
        max_articles : int | None, optional
            最大記事数（None の場合は制限なし）
        dry_run : bool, optional
            Trueの場合、Issue作成をスキップ

        Returns
        -------
        WorkflowResult
            ワークフロー実行結果
        """
        started_at = datetime.now(timezone.utc)
        logger.info("Workflow started", statuses=statuses, max_articles=max_articles, dry_run=dry_run)

        # 1. 記事収集
        logger.info("Collecting articles...")
        collected = await self._collector.collect(
            max_age_hours=self._config.filtering.max_age_hours
        )

        # Status フィルタリング
        if statuses:
            collected = [a for a in collected if self._get_status(a) in statuses]

        # 件数制限
        if max_articles:
            collected = collected[:max_articles]

        logger.info("Collected articles", count=len(collected))

        # 2. 本文抽出
        logger.info("Extracting body text...")
        extracted = await self._extractor.extract_batch(
            collected,
            concurrency=self._config.extraction.concurrency
        )

        # 抽出成功のみフィルタ
        extracted_success = [e for e in extracted if e.extraction_status == ExtractionStatus.SUCCESS]
        logger.info("Extracted articles", success=len(extracted_success), total=len(extracted))

        # 3. AI要約
        logger.info("Summarizing articles...")
        summarized = await self._summarizer.summarize_batch(
            extracted_success,
            concurrency=self._config.summarization.concurrency
        )

        # 要約成功のみフィルタ
        summarized_success = [s for s in summarized if s.summarization_status == SummarizationStatus.SUCCESS]
        logger.info("Summarized articles", success=len(summarized_success), total=len(summarized))

        # 4. Issue 公開
        logger.info("Publishing articles...")
        published = await self._publisher.publish_batch(summarized_success, dry_run=dry_run)

        finished_at = datetime.now(timezone.utc)

        # 結果集計
        return self._build_result(
            collected, extracted, summarized, published,
            started_at, finished_at
        )
```

## 受け入れ条件

- [ ] `NewsWorkflowOrchestrator` クラスが実装されている
- [ ] `run(statuses, max_articles, dry_run) -> WorkflowResult` メソッド
- [ ] 各ステージで成功した記事のみ次のステージに渡す
- [ ] Status フィルタリングが機能する
- [ ] 件数制限が機能する
- [ ] エラー発生時も処理を継続
- [ ] 各ステージの進捗ログが出力される
- [ ] pyright 型チェック成功

## 参照

- project.md: データフロー セクション

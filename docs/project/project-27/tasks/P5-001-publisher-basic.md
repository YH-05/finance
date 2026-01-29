# P5-001: Publisher 基本クラス構造作成

## 概要

GitHub Issue 作成のための基本クラス構造を作成する。

## フェーズ

Phase 5: GitHub Publisher

## 依存タスク

- P1-005: PublicationStatus, PublishedArticle モデル作成
- P1-007: config.py 設定ファイル読み込み機能実装

## 成果物

- `src/news/publisher.py`（新規作成）

## 実装内容

```python
from news.config import NewsWorkflowConfig
from news.models import SummarizedArticle, PublishedArticle, PublicationStatus
from utils_core.logging_config import get_logger

logger = get_logger(__name__)

class Publisher:
    """GitHub Issue作成とProject追加

    要約済み記事を GitHub Issue として作成し、
    指定された Project に追加する。

    Parameters
    ----------
    config : NewsWorkflowConfig
        ワークフロー設定
    """

    def __init__(self, config: NewsWorkflowConfig) -> None:
        self._config = config
        self._repo = config.github.repository
        self._project_id = config.github.project_id
        self._project_number = config.github.project_number
        self._status_field_id = config.github.status_field_id
        self._published_date_field_id = config.github.published_date_field_id
        self._status_mapping = config.status_mapping
        self._status_ids = config.github_status_ids

    async def publish(self, article: SummarizedArticle) -> PublishedArticle:
        """単一記事をIssueとして公開

        Parameters
        ----------
        article : SummarizedArticle
            要約済み記事

        Returns
        -------
        PublishedArticle
            公開結果
        """
        # 要約が失敗している場合はスキップ
        if article.summary is None:
            return PublishedArticle(
                summarized=article,
                issue_number=None,
                issue_url=None,
                publication_status=PublicationStatus.SKIPPED,
                error_message="No summary available"
            )

        # TODO: Issue 作成処理（P5-002以降）
        ...

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
        ...
```

## 受け入れ条件

- [ ] `Publisher` クラスが作成されている
- [ ] コンストラクタで設定を受け取る
- [ ] `publish()` と `publish_batch()` のシグネチャが定義されている
- [ ] 要約なしの記事は SKIPPED ステータスを返す
- [ ] NumPy スタイル Docstring が記載されている
- [ ] pyright 型チェック成功

## 参照

- project.md: インターフェース設計 - Publisher セクション
- `src/news/sinks/github.py`: GitHubSink の参考

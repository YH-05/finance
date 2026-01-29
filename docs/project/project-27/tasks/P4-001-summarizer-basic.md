# P4-001: Summarizer 基本クラス構造作成

## 概要

AI 要約のための基本クラス構造を作成する。

## フェーズ

Phase 4: AI要約

## 依存タスク

- P1-004: StructuredSummary, SummarizedArticle モデル作成

## 成果物

- `src/news/summarizer.py`（新規作成）

## 実装内容

```python
from news.config import NewsWorkflowConfig
from news.models import ExtractedArticle, SummarizedArticle, SummarizationStatus, StructuredSummary
from utils_core.logging_config import get_logger

logger = get_logger(__name__)

class Summarizer:
    """Claude Agent SDKを使用した構造化要約

    記事本文を分析し、4セクション構造の日本語要約を生成する。

    Parameters
    ----------
    config : NewsWorkflowConfig
        ワークフロー設定
    """

    def __init__(self, config: NewsWorkflowConfig) -> None:
        self._config = config
        self._prompt_template = config.summarization.prompt_template

    async def summarize(self, article: ExtractedArticle) -> SummarizedArticle:
        """単一記事を要約

        Parameters
        ----------
        article : ExtractedArticle
            本文抽出済み記事

        Returns
        -------
        SummarizedArticle
            要約結果
        """
        # 本文抽出が失敗している場合はスキップ
        if article.body_text is None:
            return SummarizedArticle(
                extracted=article,
                summary=None,
                summarization_status=SummarizationStatus.SKIPPED,
                error_message="No body text available"
            )

        # TODO: Claude Agent SDK 統合（P4-002）
        ...

    async def summarize_batch(
        self,
        articles: list[ExtractedArticle],
        concurrency: int = 3,
    ) -> list[SummarizedArticle]:
        """複数記事を並列要約

        Parameters
        ----------
        articles : list[ExtractedArticle]
            本文抽出済み記事リスト
        concurrency : int, optional
            並列処理数（デフォルト: 3）

        Returns
        -------
        list[SummarizedArticle]
            要約結果リスト
        """
        ...
```

## 受け入れ条件

- [ ] `Summarizer` クラスが作成されている
- [ ] コンストラクタで設定を受け取る
- [ ] `summarize()` と `summarize_batch()` のシグネチャが定義されている
- [ ] 本文なしの記事は SKIPPED ステータスを返す
- [ ] NumPy スタイル Docstring が記載されている
- [ ] pyright 型チェック成功

## 参照

- project.md: インターフェース設計 - Summarizer セクション
- `src/news/processors/agent_base.py`: AgentProcessor の参考

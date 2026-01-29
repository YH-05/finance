# P2-002: RSSCollector 基本実装

## 概要

既存の FeedParser を使用して RSS フィードから記事を収集する RSSCollector を実装する。

## フェーズ

Phase 2: RSS収集

## 依存タスク

- P2-001: collectors/__init__.py 作成
- P1-007: config.py 設定ファイル読み込み機能実装

## 成果物

- `src/news/collectors/rss.py`（新規作成）

## 実装内容

```python
from news.collectors.base import BaseCollector
from news.config import NewsWorkflowConfig
from news.models import ArticleSource, CollectedArticle, SourceType
from rss.core.parser import FeedParser

class RSSCollector(BaseCollector):
    """RSSフィードからの記事収集

    既存の FeedParser を使用して、設定されたRSSフィードから
    記事メタデータを収集する。

    Parameters
    ----------
    config : NewsWorkflowConfig
        ワークフロー設定
    """

    def __init__(self, config: NewsWorkflowConfig) -> None:
        self._config = config
        self._parser = FeedParser()

    @property
    def source_type(self) -> SourceType:
        return SourceType.RSS

    async def collect(
        self,
        max_age_hours: int = 168,
    ) -> list[CollectedArticle]:
        """RSSフィードから記事を収集

        Parameters
        ----------
        max_age_hours : int, optional
            収集対象の最大経過時間（デフォルト: 168 = 7日）

        Returns
        -------
        list[CollectedArticle]
            収集された記事リスト
        """
        # 1. presets_file からフィード一覧を読み込み
        # 2. 各フィードから記事を取得
        # 3. CollectedArticle に変換
        ...
```

## 受け入れ条件

- [ ] `RSSCollector(BaseCollector)` クラスが実装されている
- [ ] `rss.core.parser.FeedParser` を内部で使用している
- [ ] `collect()` が `list[CollectedArticle]` を返す
- [ ] 設定ファイルから presets_file パスを読み込む
- [ ] NumPy スタイル Docstring が記載されている
- [ ] pyright 型チェック成功

## 参照

- `src/rss/core/parser.py`: FeedParser の実装
- `data/config/rss-presets.json`: RSSフィード設定

# P1-009: BaseCollector 抽象クラス作成

## 概要

情報源別コレクターの基底クラスを作成する。

## フェーズ

Phase 1: 基盤（モデル・設定・インターフェース）

## 依存タスク

- P1-002: CollectedArticle モデル作成

## 成果物

- `src/news/collectors/base.py`（新規作成）

## 実装内容

```python
from abc import ABC, abstractmethod

from news.models import CollectedArticle, SourceType

class BaseCollector(ABC):
    """情報源からの記事収集を担当する基底クラス

    情報源（RSS, yfinance, Webスクレイピング等）から
    記事メタデータを収集するコレクターの抽象基底クラス。
    """

    @property
    @abstractmethod
    def source_type(self) -> SourceType:
        """情報源タイプを返す

        Returns
        -------
        SourceType
            この Collector が対応する情報源タイプ
        """

    @abstractmethod
    async def collect(
        self,
        max_age_hours: int = 168,
    ) -> list[CollectedArticle]:
        """記事メタデータを収集

        Parameters
        ----------
        max_age_hours : int, optional
            収集対象の最大経過時間（デフォルト: 168 = 7日）

        Returns
        -------
        list[CollectedArticle]
            収集された記事リスト
        """
```

## 受け入れ条件

- [ ] `BaseCollector` ABC が定義されている
- [ ] `source_type` プロパティ（抽象）が定義されている
- [ ] `collect(max_age_hours: int) -> list[CollectedArticle]` メソッド（抽象）が定義されている
- [ ] NumPy スタイル Docstring が記載されている
- [ ] pyright 型チェック成功

## 参照

- project.md: インターフェース設計 - BaseCollector セクション

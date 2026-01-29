# P1-010: BaseExtractor 抽象クラス作成

## 概要

本文抽出の基底クラスを作成する。

## フェーズ

Phase 1: 基盤（モデル・設定・インターフェース）

## 依存タスク

- P1-003: ExtractionStatus, ExtractedArticle モデル作成

## 成果物

- `src/news/extractors/base.py`（新規作成）

## 実装内容

```python
import asyncio
from abc import ABC, abstractmethod

from news.models import CollectedArticle, ExtractedArticle

class BaseExtractor(ABC):
    """記事本文の抽出を担当する基底クラス

    URLから記事本文を抽出するエクストラクターの抽象基底クラス。
    """

    @property
    @abstractmethod
    def extractor_name(self) -> str:
        """抽出器名を返す

        Returns
        -------
        str
            抽出器の名前（例: "trafilatura"）
        """

    @abstractmethod
    async def extract(self, article: CollectedArticle) -> ExtractedArticle:
        """単一記事の本文を抽出

        Parameters
        ----------
        article : CollectedArticle
            収集された記事

        Returns
        -------
        ExtractedArticle
            本文抽出結果
        """

    async def extract_batch(
        self,
        articles: list[CollectedArticle],
        concurrency: int = 5,
    ) -> list[ExtractedArticle]:
        """複数記事の本文を並列抽出

        Parameters
        ----------
        articles : list[CollectedArticle]
            収集された記事リスト
        concurrency : int, optional
            並列処理数（デフォルト: 5）

        Returns
        -------
        list[ExtractedArticle]
            本文抽出結果リスト
        """
        semaphore = asyncio.Semaphore(concurrency)

        async def extract_with_semaphore(article: CollectedArticle) -> ExtractedArticle:
            async with semaphore:
                return await self.extract(article)

        tasks = [extract_with_semaphore(article) for article in articles]
        return await asyncio.gather(*tasks)
```

## 受け入れ条件

- [ ] `BaseExtractor` ABC が定義されている
- [ ] `extractor_name` プロパティ（抽象）が定義されている
- [ ] `extract(article: CollectedArticle) -> ExtractedArticle` メソッド（抽象）が定義されている
- [ ] `extract_batch(articles, concurrency) -> list[ExtractedArticle]` メソッドが実装されている
- [ ] セマフォベース並列処理の基本構造が含まれている
- [ ] NumPy スタイル Docstring が記載されている
- [ ] pyright 型チェック成功

## 参照

- project.md: インターフェース設計 - BaseExtractor セクション

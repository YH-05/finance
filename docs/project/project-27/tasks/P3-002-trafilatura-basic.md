# P3-002: TrafilaturaExtractor 基本実装

## 概要

既存の ArticleExtractor をラップして TrafilaturaExtractor を実装する。

## フェーズ

Phase 3: 本文抽出

## 依存タスク

- P3-001: extractors/__init__.py 作成

## 成果物

- `src/news/extractors/trafilatura.py`（新規作成）

## 実装内容

```python
from news.extractors.base import BaseExtractor
from news.models import CollectedArticle, ExtractedArticle, ExtractionStatus
from rss.services.article_extractor import ArticleExtractor

class TrafilaturaExtractor(BaseExtractor):
    """trafilaturaベースの本文抽出

    既存の ArticleExtractor をラップして、
    URLから記事本文を抽出する。

    Parameters
    ----------
    min_body_length : int, optional
        最小本文長（デフォルト: 200）
    """

    def __init__(self, min_body_length: int = 200) -> None:
        self._extractor = ArticleExtractor()
        self._min_body_length = min_body_length

    @property
    def extractor_name(self) -> str:
        return "trafilatura"

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
        try:
            result = await self._extractor.extract(str(article.url))

            if result is None or len(result) < self._min_body_length:
                return ExtractedArticle(
                    collected=article,
                    body_text=None,
                    extraction_status=ExtractionStatus.FAILED,
                    extraction_method=self.extractor_name,
                    error_message="Body text too short or empty"
                )

            return ExtractedArticle(
                collected=article,
                body_text=result,
                extraction_status=ExtractionStatus.SUCCESS,
                extraction_method=self.extractor_name,
            )
        except Exception as e:
            # エラータイプに応じてステータスを設定
            status = self._classify_error(e)
            return ExtractedArticle(
                collected=article,
                body_text=None,
                extraction_status=status,
                extraction_method=self.extractor_name,
                error_message=str(e)
            )
```

## 受け入れ条件

- [ ] `TrafilaturaExtractor(BaseExtractor)` クラスが実装されている
- [ ] `rss.services.article_extractor.ArticleExtractor` を内部で使用している
- [ ] `extract()` が `ExtractedArticle` を返す
- [ ] 抽出結果を正しいステータスにマッピング
- [ ] min_body_length によるバリデーションが機能する
- [ ] NumPy スタイル Docstring が記載されている
- [ ] pyright 型チェック成功

## 参照

- `src/rss/services/article_extractor.py`: ArticleExtractor の実装

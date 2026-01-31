# P10-012: trafilatura→Playwrightフォールバック

## 概要

trafilatura抽出失敗時にPlaywrightで再試行するフォールバック機能を実装する。

## 変更内容

### 変更ファイル

| ファイル | 変更内容 |
|----------|----------|
| `src/news/extractors/trafilatura.py` | フォールバック呼び出し追加 |
| `src/news/extractors/__init__.py` | FallbackExtractor公開 |

### 実装詳細

```python
# src/news/extractors/trafilatura.py

class TrafilaturaExtractor(BaseExtractor):
    """trafilaturaを使用した本文抽出（Playwrightフォールバック付き）。"""

    def __init__(self, config: NewsWorkflowConfig) -> None:
        self._config = config
        self._min_body_length = config.extraction.min_body_length
        self._playwright_config = config.extraction.playwright_fallback
        self._playwright_extractor: PlaywrightExtractor | None = None

    async def __aenter__(self) -> TrafilaturaExtractor:
        """非同期コンテキストマネージャ開始。"""
        if self._playwright_config.enabled:
            from news.extractors.playwright import PlaywrightExtractor
            self._playwright_extractor = PlaywrightExtractor(self._config)
            await self._playwright_extractor.__aenter__()
        return self

    async def __aexit__(self, *args) -> None:
        """非同期コンテキストマネージャ終了。"""
        if self._playwright_extractor:
            await self._playwright_extractor.__aexit__(*args)

    async def extract(self, article: CollectedArticle) -> ExtractedArticle:
        """記事本文を抽出（フォールバック付き）。"""
        # 1. trafilaturaで抽出試行
        result = await self._extract_with_trafilatura(article)

        # 2. 失敗時はPlaywrightでフォールバック
        if self._should_fallback(result):
            logger.debug(
                "Falling back to Playwright",
                url=str(article.url),
                original_status=result.extraction_status,
                original_error=result.error_message,
            )

            playwright_result = await self._extract_with_playwright(article)

            if playwright_result.extraction_status == ExtractionStatus.SUCCESS:
                logger.info(
                    "Playwright fallback succeeded",
                    url=str(article.url),
                )
                return playwright_result

            # フォールバックも失敗した場合は元の結果を返す
            logger.debug(
                "Playwright fallback also failed",
                url=str(article.url),
                playwright_error=playwright_result.error_message,
            )

        return result

    def _should_fallback(self, result: ExtractedArticle) -> bool:
        """フォールバックすべきかどうかを判定。

        以下の条件でフォールバックを試行:
        - フォールバックが有効
        - 抽出失敗（FAILED）
        - または本文が短すぎる
        """
        if not self._playwright_config.enabled:
            return False

        if self._playwright_extractor is None:
            return False

        if result.extraction_status == ExtractionStatus.FAILED:
            return True

        if result.extraction_status == ExtractionStatus.SUCCESS:
            if result.body_text and len(result.body_text) < self._min_body_length:
                return True

        return False

    async def _extract_with_trafilatura(
        self,
        article: CollectedArticle,
    ) -> ExtractedArticle:
        """trafilaturaで抽出（既存ロジック）。"""
        # 既存の実装
        ...

    async def _extract_with_playwright(
        self,
        article: CollectedArticle,
    ) -> ExtractedArticle:
        """Playwrightで抽出。"""
        if self._playwright_extractor is None:
            return ExtractedArticle(
                collected=article,
                body_text=None,
                extraction_status=ExtractionStatus.FAILED,
                extraction_method="playwright",
                error_message="Playwright extractor not initialized",
            )

        result = await self._playwright_extractor.extract(article)

        # extraction_methodを更新
        return ExtractedArticle(
            collected=article,
            body_text=result.body_text,
            extraction_status=result.extraction_status,
            extraction_method="trafilatura+playwright",  # フォールバック使用を明示
            error_message=result.error_message,
        )
```

## 受け入れ条件

- [ ] trafilatura失敗時にPlaywrightで再試行される
- [ ] フォールバック成功時は `extraction_method="trafilatura+playwright"` になる
- [ ] フォールバック無効時は従来通りtrafilaturaのみ
- [ ] 非同期コンテキストマネージャでブラウザが適切に管理される
- [ ] 単体テストが通る

## テストケース

```python
class TestFallbackExtraction:
    @pytest.mark.asyncio
    async def test_fallback_on_trafilatura_failure(self, extractor, mocker):
        """trafilatura失敗時にPlaywrightで再試行する。"""
        # trafilaturaは失敗
        mocker.patch.object(
            extractor, "_extract_with_trafilatura",
            return_value=ExtractedArticle(
                extraction_status=ExtractionStatus.FAILED
            )
        )
        # Playwrightは成功
        mocker.patch.object(
            extractor, "_extract_with_playwright",
            return_value=ExtractedArticle(
                extraction_status=ExtractionStatus.SUCCESS,
                body_text="Playwright extracted text"
            )
        )

        result = await extractor.extract(article)

        assert result.extraction_status == ExtractionStatus.SUCCESS
        assert "playwright" in result.extraction_method

    @pytest.mark.asyncio
    async def test_no_fallback_on_success(self, extractor, mocker):
        """trafilatura成功時はフォールバックしない。"""
        mocker.patch.object(
            extractor, "_extract_with_trafilatura",
            return_value=ExtractedArticle(
                extraction_status=ExtractionStatus.SUCCESS,
                body_text="Long enough body text..."
            )
        )

        result = await extractor.extract(article)

        assert result.extraction_method == "trafilatura"
```

## 依存関係

- 依存先: P10-011
- ブロック: P10-013

## 見積もり

- 作業時間: 40分
- 複雑度: 高

# P10-013: フォールバックテスト

## 概要

Playwrightフォールバック機能の統合テストを作成する。

## 変更内容

### 新規ファイル

| ファイル | 説明 |
|----------|------|
| `tests/news/integration/test_playwright_fallback.py` | フォールバック統合テスト |
| `tests/news/unit/test_playwright_extractor.py` | PlaywrightExtractor単体テスト |

### テスト構成

#### 単体テスト

```python
# tests/news/unit/test_playwright_extractor.py

"""PlaywrightExtractor unit tests."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from news.extractors.playwright import PlaywrightExtractor
from news.models import CollectedArticle, ExtractionStatus


class TestPlaywrightExtractor:
    """PlaywrightExtractor tests."""

    @pytest.fixture
    def config(self):
        """テスト用設定。"""
        # モック設定
        ...

    @pytest.fixture
    def mock_playwright(self):
        """Playwrightモック。"""
        ...

    @pytest.mark.asyncio
    async def test_正常系_article要素から本文を抽出(
        self,
        config,
        mock_playwright,
    ):
        """article要素が存在する場合、その内容を抽出する。"""
        ...

    @pytest.mark.asyncio
    async def test_正常系_main要素にフォールバック(
        self,
        config,
        mock_playwright,
    ):
        """article要素がない場合、main要素にフォールバックする。"""
        ...

    @pytest.mark.asyncio
    async def test_異常系_タイムアウトでTIMEOUTステータス(
        self,
        config,
        mock_playwright,
    ):
        """ページ読み込みタイムアウト時はTIMEOUTを返す。"""
        ...

    @pytest.mark.asyncio
    async def test_異常系_本文が短いとFAILED(
        self,
        config,
        mock_playwright,
    ):
        """抽出した本文が短すぎる場合はFAILEDを返す。"""
        ...

    @pytest.mark.asyncio
    async def test_コンテキストマネージャでブラウザが終了(
        self,
        config,
        mock_playwright,
    ):
        """async withを抜けるとブラウザが終了する。"""
        ...
```

#### 統合テスト

```python
# tests/news/integration/test_playwright_fallback.py

"""Playwright fallback integration tests."""

import pytest
from news.extractors.trafilatura import TrafilaturaExtractor
from news.models import CollectedArticle, ExtractionStatus


@pytest.mark.integration
@pytest.mark.playwright
class TestPlaywrightFallback:
    """Playwrightフォールバック統合テスト。

    Note
    ----
    実際のブラウザを使用するため、CIでは `--ignore` で除外するか、
    `@pytest.mark.skipif` で条件付き実行にする。
    """

    @pytest.fixture
    def config(self):
        """実際の設定ファイルを読み込む。"""
        ...

    @pytest.mark.asyncio
    async def test_正常系_フォールバックで抽出成功(self, config):
        """trafilatura失敗→Playwrightで成功するケース。"""
        # JS動的レンダリングが必要なサイトをテスト
        article = CollectedArticle(
            url="https://example.com/js-rendered-page",
            title="Test",
            ...
        )

        async with TrafilaturaExtractor(config) as extractor:
            result = await extractor.extract(article)

        # フォールバックで成功
        assert result.extraction_status == ExtractionStatus.SUCCESS
        assert "playwright" in result.extraction_method

    @pytest.mark.asyncio
    async def test_正常系_trafilaturaのみで成功(self, config):
        """trafilaturaで成功する場合はフォールバックしない。"""
        article = CollectedArticle(
            url="https://example.com/static-page",
            title="Test",
            ...
        )

        async with TrafilaturaExtractor(config) as extractor:
            result = await extractor.extract(article)

        assert result.extraction_method == "trafilatura"
```

### pytest設定

```toml
# pyproject.toml

[tool.pytest.ini_options]
markers = [
    "playwright: marks tests as requiring playwright (deselect with '-m \"not playwright\"')",
]
```

## 受け入れ条件

- [ ] PlaywrightExtractorの単体テストが作成される
- [ ] フォールバック機能の統合テストが作成される
- [ ] 全テストがCI環境で実行可能
- [ ] Playwright未インストール環境でもテストがスキップされる

## CI対応

```yaml
# .github/workflows/test.yml

- name: Install Playwright
  run: uv run playwright install chromium --with-deps
  if: matrix.test-type == 'integration'

- name: Run tests (excluding playwright)
  run: uv run pytest -m "not playwright"
  if: matrix.test-type == 'unit'

- name: Run playwright tests
  run: uv run pytest -m "playwright"
  if: matrix.test-type == 'integration'
```

## 依存関係

- 依存先: P10-012
- ブロック: P10-016

## 見積もり

- 作業時間: 45分
- 複雑度: 中

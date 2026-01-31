# P9-006: テストのモック更新

## 概要

`tests/news/unit/summarizers/test_summarizer.py` のモックを claude-agent-sdk 用に更新する。

## フェーズ

Phase 9: claude-agent-sdk 移行

## 依存タスク

- P9-005: Anthropic クライアント削除とクリーンアップ

## 成果物

- `tests/news/unit/summarizers/test_summarizer.py`（更新）

## 実装内容

### 変更前のモックパターン

```python
with patch("news.summarizer.Anthropic") as mock_anthropic:
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_content = MagicMock()
    mock_content.text = '{"overview": "Test", ...}'
    mock_response.content = [mock_content]
    mock_client.messages.create.return_value = mock_response
    mock_anthropic.return_value = mock_client
```

### 変更後のモックパターン

```python
from unittest.mock import AsyncMock, MagicMock, patch


def create_mock_assistant_message(text: str) -> MagicMock:
    """AssistantMessage のモックを作成する。"""
    mock_text_block = MagicMock()
    mock_text_block.text = text

    mock_message = MagicMock()
    mock_message.content = [mock_text_block]

    return mock_message


async def mock_query_success(text: str):
    """成功時の query() モックジェネレータ。"""
    yield create_mock_assistant_message(text)


async def mock_query_error(error: Exception):
    """エラー時の query() モックジェネレータ。"""
    raise error
    yield  # ジェネレータにするため


@pytest.mark.asyncio
async def test_正常系_claude_sdkを使用して要約成功(
    sample_config: NewsWorkflowConfig,
    extracted_article_with_body: ExtractedArticle,
) -> None:
    """Claude Agent SDK を使用して要約が成功する。"""
    from news.summarizer import Summarizer

    response_json = """{
        "overview": "S&P 500が上昇した。",
        "key_points": ["ポイント1", "ポイント2"],
        "market_impact": "市場への影響",
        "related_info": "関連情報"
    }"""

    with patch("news.summarizer.query") as mock_query:
        # query() が非同期イテレータを返すようモック
        mock_query.return_value = mock_query_success(response_json).__aiter__()

        # TextBlock と AssistantMessage もモック
        with patch("news.summarizer.AssistantMessage", MagicMock):
            with patch("news.summarizer.TextBlock", MagicMock):
                summarizer = Summarizer(config=sample_config)
                result = await summarizer.summarize(extracted_article_with_body)

    assert result.summarization_status == SummarizationStatus.SUCCESS
    assert result.summary is not None
    assert result.summary.overview == "S&P 500が上昇した。"
```

### SDK エラーのモックパターン

```python
@pytest.mark.asyncio
async def test_異常系_CLINotFoundErrorでFAILED(
    sample_config: NewsWorkflowConfig,
    extracted_article_with_body: ExtractedArticle,
) -> None:
    """CLINotFoundError で FAILED ステータスを返す。"""
    from news.summarizer import Summarizer

    # CLINotFoundError をモック
    mock_error = MagicMock()
    mock_error.__class__.__name__ = "CLINotFoundError"

    with patch("news.summarizer.query") as mock_query:
        mock_query.side_effect = Exception("CLI not found")

        summarizer = Summarizer(config=sample_config)
        result = await summarizer.summarize(extracted_article_with_body)

    assert result.summarization_status == SummarizationStatus.FAILED
    assert "CLI" in result.error_message or "not found" in result.error_message.lower()
```

### 簡略化されたモックヘルパー

```python
@pytest.fixture
def mock_claude_sdk():
    """claude-agent-sdk のモックフィクスチャ。"""

    class MockSDK:
        def __init__(self):
            self.responses: list[str] = []
            self.errors: list[Exception] = []

        def set_response(self, text: str) -> None:
            self.responses.append(text)

        def set_error(self, error: Exception) -> None:
            self.errors.append(error)

        async def mock_query(self, **kwargs):
            if self.errors:
                raise self.errors.pop(0)

            if self.responses:
                text = self.responses.pop(0)
                mock_message = MagicMock()
                mock_block = MagicMock()
                mock_block.text = text
                mock_message.content = [mock_block]
                yield mock_message

    return MockSDK()
```

## 受け入れ条件

- [ ] `Anthropic` のモックが削除されている
- [ ] `query()` 関数のモックが実装されている
- [ ] `AssistantMessage`, `TextBlock` のモックが実装されている
- [ ] 成功ケースのテストが通る
- [ ] エラーケースのテストが通る
- [ ] リトライのテストが通る（`asyncio.sleep` モック含む）
- [ ] タイムアウトのテストが通る
- [ ] `make test` で全テスト成功
- [ ] `make check-all` 成功

## 参照

- 現在の `tests/news/unit/summarizers/test_summarizer.py`
- Python unittest.mock ドキュメント
- pytest-asyncio ドキュメント

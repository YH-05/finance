# P9-004: SDK エラーハンドリング実装

## 概要

claude-agent-sdk 固有の例外（`CLINotFoundError`, `ProcessError`, `CLIConnectionError` 等）をハンドリングする。

## フェーズ

Phase 9: claude-agent-sdk 移行

## 依存タスク

- P9-003: summarize メソッドの更新

## 成果物

- `src/news/summarizer.py`（更新）

## 背景

claude-agent-sdk は Claude Code CLI をラップしており、以下の固有例外が発生する可能性がある：

| 例外 | 説明 |
|---|---|
| `CLINotFoundError` | Claude Code CLI がインストールされていない |
| `ProcessError` | CLI プロセスがエラー終了（exit code != 0） |
| `CLIJSONDecodeError` | CLI の出力が不正な JSON |
| `CLIConnectionError` | CLI との通信エラー |
| `ClaudeSDKError` | その他の SDK エラー（基底クラス） |

## 実装内容

### _call_claude_sdk メソッドのエラーハンドリング

```python
async def _call_claude_sdk(self, prompt: str) -> str:
    """Claude Agent SDK を使用して要約を取得。

    Parameters
    ----------
    prompt : str
        要約プロンプト。

    Returns
    -------
    str
        Claude からのレスポンステキスト。

    Raises
    ------
    RuntimeError
        claude-agent-sdk がインストールされていない場合。
    CLINotFoundError
        Claude Code CLI がインストールされていない場合。
    ProcessError
        CLI プロセスがエラー終了した場合。
    CLIConnectionError
        CLI との通信エラーが発生した場合。
    """
    try:
        from claude_agent_sdk import (
            query,
            ClaudeAgentOptions,
            AssistantMessage,
            TextBlock,
            CLINotFoundError,
            ProcessError,
            CLIConnectionError,
            ClaudeSDKError,
        )
    except ImportError as e:
        raise RuntimeError(
            "claude-agent-sdk is not installed. "
            "Install with: uv add claude-agent-sdk"
        ) from e

    options = ClaudeAgentOptions(
        allowed_tools=[],
        max_turns=1,
    )

    try:
        response_parts: list[str] = []
        async for message in query(prompt=prompt, options=options):
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        response_parts.append(block.text)

        return "".join(response_parts)

    except CLINotFoundError:
        logger.error(
            "Claude Code CLI not found",
            hint="Install with: curl -fsSL https://claude.ai/install.sh | bash",
        )
        raise

    except ProcessError as e:
        logger.error(
            "CLI process error",
            exit_code=e.exit_code,
            stderr=e.stderr[:200] if e.stderr else None,
        )
        raise

    except CLIConnectionError as e:
        logger.error("CLI connection error", error=str(e))
        raise

    except ClaudeSDKError as e:
        logger.error("SDK error", error=str(e))
        raise
```

### summarize メソッドでの例外マッピング

```python
async def summarize(self, article: ExtractedArticle) -> SummarizedArticle:
    # ...
    for attempt in range(self._max_retries):
        try:
            # ...
        except asyncio.TimeoutError:
            # タイムアウト処理（既存）
            pass

        except ValueError as e:
            # JSON parse/validation error - リトライしない
            return SummarizedArticle(
                extracted=article,
                summary=None,
                summarization_status=SummarizationStatus.FAILED,
                error_message=str(e),
            )

        except RuntimeError as e:
            # SDK未インストール - リトライしない
            logger.error("SDK not installed", error=str(e))
            return SummarizedArticle(
                extracted=article,
                summary=None,
                summarization_status=SummarizationStatus.FAILED,
                error_message=str(e),
            )

        except Exception as e:
            # その他のエラー（CLINotFoundError, ProcessError等）- リトライ
            last_error = e
            logger.warning(
                "Summarization failed",
                article_url=str(article.collected.url),
                attempt=attempt + 1,
                max_retries=self._max_retries,
                error=str(e),
                error_type=type(e).__name__,
            )

        # 指数バックオフ
        if attempt < self._max_retries - 1:
            await asyncio.sleep(2 ** attempt)
```

## 受け入れ条件

- [ ] `CLINotFoundError` のインポートとハンドリング
- [ ] `ProcessError` のインポートとハンドリング
- [ ] `CLIConnectionError` のインポートとハンドリング
- [ ] `ClaudeSDKError` のインポートとハンドリング（基底クラス）
- [ ] 各例外で適切なログ出力
- [ ] `ProcessError` で `exit_code` と `stderr` をログ出力
- [ ] リトライ対象とリトライ不可の例外を区別
- [ ] NumPy スタイル Docstring に例外を記載
- [ ] pyright 型チェック成功

## 参照

- [Claude Agent SDK - Error Handling](https://github.com/anthropics/claude-agent-sdk-python#error-handling)
- `CLINotFoundError`: CLI未インストール時に発生
- `ProcessError`: exit_code, stderr 属性を持つ

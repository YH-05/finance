# P9-002: _call_claude_sdk メソッド実装

## 概要

claude-agent-sdk の `query()` 関数を使用して Claude を呼び出す `_call_claude_sdk` メソッドを実装する。

## フェーズ

Phase 9: claude-agent-sdk 移行

## 依存タスク

- P9-001: claude-agent-sdk インポート変更

## 成果物

- `src/news/summarizer.py`（更新）

## 実装内容

### 新規メソッド: _call_claude_sdk

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
    """
    try:
        from claude_agent_sdk import (
            query,
            ClaudeAgentOptions,
            AssistantMessage,
            TextBlock,
        )
    except ImportError as e:
        raise RuntimeError(
            "claude-agent-sdk is not installed. "
            "Install with: uv add claude-agent-sdk"
        ) from e

    options = ClaudeAgentOptions(
        allowed_tools=[],  # ツール不要（テキスト生成のみ）
        max_turns=1,       # 1ターンのみ
    )

    response_parts: list[str] = []
    async for message in query(prompt=prompt, options=options):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    response_parts.append(block.text)

    return "".join(response_parts)
```

### query() 関数の特徴

| 特徴 | 説明 |
|---|---|
| 非同期イテレータ | `async for` でストリーミング処理 |
| ステートレス | 各呼び出しが独立（会話履歴なし） |
| ClaudeAgentOptions | システムプロンプト、ツール許可、最大ターン数を設定 |
| メッセージ型 | `AssistantMessage`, `ResultMessage` 等を yield |

### AssistantMessage の構造

```python
# AssistantMessage の content は ContentBlock のリスト
for block in message.content:
    if isinstance(block, TextBlock):
        # テキストコンテンツ
        text = block.text
    elif isinstance(block, ToolUseBlock):
        # ツール使用（今回は不使用）
        pass
```

## 受け入れ条件

- [ ] `_call_claude_sdk` メソッドが実装されている
- [ ] `query()` 関数を使用している
- [ ] `ClaudeAgentOptions` で `allowed_tools=[]` を設定している
- [ ] `AssistantMessage` と `TextBlock` からテキストを抽出している
- [ ] 遅延インポートで `ImportError` を適切にハンドリング
- [ ] NumPy スタイル Docstring が記載されている
- [ ] pyright 型チェック成功

## 参照

- [Claude Agent SDK - query() function](https://platform.claude.com/docs/en/agent-sdk/python)
- 現在の `_call_claude` メソッド: 参考として残しておく

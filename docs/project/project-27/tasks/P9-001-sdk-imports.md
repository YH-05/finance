# P9-001: claude-agent-sdk インポート変更

## 概要

`src/news/summarizer.py` のインポートを Anthropic SDK から claude-agent-sdk に変更する。

## フェーズ

Phase 9: claude-agent-sdk 移行

## 依存タスク

- P4-005: Summarizer リトライ（既存実装）

## 成果物

- `src/news/summarizer.py`（更新）

## 背景

現在の実装:
```python
from anthropic import Anthropic
```

移行先:
```python
from claude_agent_sdk import (
    query,
    ClaudeAgentOptions,
    AssistantMessage,
    TextBlock,
)
```

## 実装内容

### 変更前

```python
from anthropic import Anthropic
from pydantic import ValidationError

# ...

class Summarizer:
    def __init__(self, config: NewsWorkflowConfig) -> None:
        # ...
        self._client = Anthropic()
```

### 変更後

```python
from pydantic import ValidationError

# claude-agent-sdk は _call_claude_sdk メソッド内で遅延インポート
# （インストールされていない場合のエラーハンドリングのため）

# ...

class Summarizer:
    def __init__(self, config: NewsWorkflowConfig) -> None:
        # self._client = Anthropic() を削除
        pass
```

### claude-agent-sdk の主要な型

| 型 | 説明 |
|---|---|
| `query` | 非同期イテレータを返す関数。ステートレスな1ショットクエリ用 |
| `ClaudeAgentOptions` | オプション設定（system_prompt, max_turns, allowed_tools等） |
| `AssistantMessage` | Claudeからのレスポンスメッセージ |
| `TextBlock` | メッセージ内のテキストコンテンツ |
| `ResultMessage` | 処理結果（コスト情報等を含む） |

## 受け入れ条件

- [ ] `from anthropic import Anthropic` が削除されている
- [ ] `self._client = Anthropic()` が削除されている
- [ ] claude-agent-sdk の型がドキュメントに記載されている
- [ ] pyright 型チェック成功
- [ ] 既存のテストがモック更新なしでは失敗することを確認

## 参照

- [Claude Agent SDK Python リファレンス](https://platform.claude.com/docs/en/agent-sdk/python)
- [GitHub: anthropics/claude-agent-sdk-python](https://github.com/anthropics/claude-agent-sdk-python)
- `pyproject.toml`: `claude-agent-sdk>=0.1.22` が既に含まれている

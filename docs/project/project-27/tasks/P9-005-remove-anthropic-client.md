# P9-005: Anthropic クライアント削除とクリーンアップ

## 概要

`_call_claude` メソッドと `Anthropic` クライアント関連のコードを削除し、コードをクリーンアップする。

## フェーズ

Phase 9: claude-agent-sdk 移行

## 依存タスク

- P9-004: SDK エラーハンドリング実装

## 成果物

- `src/news/summarizer.py`（更新）

## 実装内容

### 削除対象

1. **インポート文**
```python
# 削除
from anthropic import Anthropic
```

2. **定数**
```python
# 削除
CLAUDE_MODEL = "claude-sonnet-4-20250514"
CLAUDE_MAX_TOKENS = 1024
```

3. **__init__ 内のクライアント初期化**
```python
# 削除
self._client = Anthropic()
```

4. **_call_claude メソッド全体**
```python
# 削除
def _call_claude(self, article: ExtractedArticle) -> str:
    """Claude API を呼び出して要約を生成する。
    ...
    """
    # メソッド全体を削除
```

### Docstring の更新

```python
class Summarizer:
    """Claude Agent SDK を使用した構造化要約。

    Claude Code サブスクリプション（Pro/Max）を活用して
    記事本文を分析し、4セクション構造の日本語要約を生成する。

    Parameters
    ----------
    config : NewsWorkflowConfig
        ワークフロー設定。summarization セクションからプロンプトテンプレートと
        並列処理数、タイムアウト設定を取得する。

    Attributes
    ----------
    _config : NewsWorkflowConfig
        ワークフロー設定の参照。
    _prompt_template : str
        AI 要約に使用するプロンプトテンプレート。
    _max_retries : int
        最大リトライ回数。
    _timeout_seconds : int
        タイムアウト秒数。

    Notes
    -----
    - 事前に `claude` コマンドで認証が必要
    - CI/CD では環境変数 ANTHROPIC_API_KEY を設定
    - 本文抽出が失敗している記事（body_text が None）は SKIPPED ステータスで返す

    Examples
    --------
    >>> from news.summarizer import Summarizer
    >>> from news.config.workflow import load_config
    >>> config = load_config("config.yaml")
    >>> summarizer = Summarizer(config=config)
    >>> result = await summarizer.summarize(extracted_article)
    >>> result.summary.overview
    'S&P 500が上昇...'
    """
```

### 更新後の __init__

```python
def __init__(self, config: NewsWorkflowConfig) -> None:
    """Summarizer を初期化する。

    Parameters
    ----------
    config : NewsWorkflowConfig
        ワークフロー設定。summarization セクションを使用する。
    """
    self._config = config
    self._prompt_template = config.summarization.prompt_template
    self._max_retries = config.summarization.max_retries
    self._timeout_seconds = config.summarization.timeout_seconds

    logger.debug(
        "Summarizer initialized",
        prompt_template_length=len(self._prompt_template),
        concurrency=config.summarization.concurrency,
        timeout_seconds=self._timeout_seconds,
        max_retries=self._max_retries,
    )
```

## 受け入れ条件

- [ ] `from anthropic import Anthropic` が削除されている
- [ ] `CLAUDE_MODEL`, `CLAUDE_MAX_TOKENS` 定数が削除されている
- [ ] `self._client = Anthropic()` が削除されている
- [ ] `_call_claude` メソッドが削除されている
- [ ] クラス Docstring が claude-agent-sdk 用に更新されている
- [ ] `__init__` から `_client` 属性が削除されている
- [ ] pyright 型チェック成功
- [ ] 既存のテストが新しいモックで動作する（P9-006 で対応）

## 参照

- 現在の `src/news/summarizer.py` 実装

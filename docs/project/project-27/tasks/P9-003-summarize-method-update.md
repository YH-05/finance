# P9-003: summarize メソッドの更新

## 概要

`summarize` メソッドを更新し、`_call_claude_sdk` を呼び出すように変更する。タイムアウト処理も `asyncio.timeout` で実装する。

## フェーズ

Phase 9: claude-agent-sdk 移行

## 依存タスク

- P9-002: _call_claude_sdk メソッド実装

## 成果物

- `src/news/summarizer.py`（更新）

## 実装内容

### 変更箇所

1. `_call_claude` の呼び出しを `_call_claude_sdk` に変更
2. `asyncio.timeout` でタイムアウト処理をラップ
3. SDK 固有の例外ハンドリング追加

### 変更前

```python
async def summarize(self, article: ExtractedArticle) -> SummarizedArticle:
    # ...
    for attempt in range(self._max_retries):
        try:
            response_text = self._call_claude(article)  # 同期呼び出し
            summary = self._parse_response(response_text)
            # ...
```

### 変更後

```python
async def summarize(self, article: ExtractedArticle) -> SummarizedArticle:
    # ...
    prompt = self._build_prompt(article)

    for attempt in range(self._max_retries):
        try:
            async with asyncio.timeout(self._timeout_seconds):
                response_text = await self._call_claude_sdk(prompt)  # 非同期呼び出し

            summary = self._parse_response(response_text)
            # ...

        except asyncio.TimeoutError:
            logger.warning(
                "Summarization timeout",
                attempt=attempt + 1,
                max_retries=self._max_retries,
            )
            if attempt == self._max_retries - 1:
                return SummarizedArticle(
                    extracted=article,
                    summary=None,
                    summarization_status=SummarizationStatus.TIMEOUT,
                    error_message=f"Timeout after {self._timeout_seconds}s",
                )
```

### プロンプト構築の分離

```python
def _build_prompt(self, article: ExtractedArticle) -> str:
    """要約プロンプトを構築する。

    Parameters
    ----------
    article : ExtractedArticle
        本文抽出済み記事。

    Returns
    -------
    str
        構築されたプロンプト文字列。
    """
    collected = article.collected
    published_str = (
        collected.published.isoformat() if collected.published else "不明"
    )

    return f"""以下のニュース記事を日本語で要約してください。

## 記事情報
- タイトル: {collected.title}
- ソース: {collected.source.source_name}
- 公開日: {published_str}

## 本文
{article.body_text}

## 出力形式
以下のJSON形式で回答してください：
{{
    "overview": "記事の概要（1-2文）",
    "key_points": ["キーポイント1", "キーポイント2", ...],
    "market_impact": "市場への影響",
    "related_info": "関連情報（任意、なければnull）"
}}

JSONのみを出力し、他のテキストは含めないでください。"""
```

## 受け入れ条件

- [ ] `_call_claude` の代わりに `_call_claude_sdk` を呼び出している
- [ ] `_build_prompt` メソッドでプロンプト構築を分離
- [ ] `asyncio.timeout` でタイムアウト処理を実装
- [ ] `asyncio.TimeoutError` を適切にハンドリング
- [ ] 既存のリトライロジックが維持されている
- [ ] 既存の `_parse_response` メソッドが流用されている
- [ ] NumPy スタイル Docstring が記載されている
- [ ] pyright 型チェック成功

## 参照

- 現在の `summarize` メソッド実装
- Python asyncio.timeout ドキュメント

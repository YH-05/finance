# P4-002: Summarizer Claude Agent SDK 統合

## 概要

Claude Agent SDK を使用して記事を要約する機能を実装する。

## フェーズ

Phase 4: AI要約

## 依存タスク

- P4-001: Summarizer 基本クラス構造作成

## 成果物

- `src/news/summarizer.py`（更新）

## 実装内容

```python
from anthropic import Anthropic

class Summarizer:
    def __init__(self, config: NewsWorkflowConfig) -> None:
        self._config = config
        self._prompt_template = config.summarization.prompt_template
        self._client = Anthropic()

    async def _call_claude(self, article: ExtractedArticle) -> str:
        """Claude API を呼び出して要約を生成

        Parameters
        ----------
        article : ExtractedArticle
            本文抽出済み記事

        Returns
        -------
        str
            Claude からの JSON レスポンス
        """
        prompt = self._prompt_template.format(
            title=article.collected.title,
            source=article.collected.source.source_name,
            published=article.collected.published.isoformat() if article.collected.published else "不明",
            body=article.body_text
        )

        response = self._client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        return response.content[0].text
```

## 受け入れ条件

- [ ] Anthropic クライアントを使用している
- [ ] プロンプトテンプレートが設定ファイルから読み込まれる
- [ ] 記事情報（タイトル、ソース、公開日、本文）がプロンプトに含まれる
- [ ] Claude のレスポンスが取得できる
- [ ] NumPy スタイル Docstring が記載されている
- [ ] pyright 型チェック成功

## 参照

- `src/news/processors/agent_base.py`: AgentProcessor の実装パターン
- `notebook/claude-agent-test.ipynb`: Claude Agent SDK 使用例

# P4-003: Summarizer JSON 出力パース・バリデーション

## 概要

Claude の出力を StructuredSummary モデルにパースする機能を実装する。

## フェーズ

Phase 4: AI要約

## 依存タスク

- P4-002: Summarizer Claude Agent SDK 統合

## 成果物

- `src/news/summarizer.py`（更新）

## 実装内容

```python
import json
import re
from pydantic import ValidationError

class Summarizer:
    def _parse_response(self, response: str) -> StructuredSummary:
        """Claude のレスポンスをパース

        Parameters
        ----------
        response : str
            Claude からの JSON レスポンス

        Returns
        -------
        StructuredSummary
            パースされた構造化要約

        Raises
        ------
        ValueError
            JSON パースまたはバリデーションに失敗した場合
        """
        # JSON ブロックを抽出（```json ... ``` 形式に対応）
        json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            # 直接 JSON の場合
            json_str = response.strip()

        try:
            data = json.loads(json_str)
            return StructuredSummary.model_validate(data)
        except json.JSONDecodeError as e:
            raise ValueError(f"JSON parse error: {e}")
        except ValidationError as e:
            raise ValueError(f"Validation error: {e}")

    async def summarize(self, article: ExtractedArticle) -> SummarizedArticle:
        """単一記事を要約"""
        if article.body_text is None:
            return SummarizedArticle(
                extracted=article,
                summary=None,
                summarization_status=SummarizationStatus.SKIPPED,
                error_message="No body text available"
            )

        try:
            response = await self._call_claude(article)
            summary = self._parse_response(response)

            return SummarizedArticle(
                extracted=article,
                summary=summary,
                summarization_status=SummarizationStatus.SUCCESS,
            )
        except ValueError as e:
            return SummarizedArticle(
                extracted=article,
                summary=None,
                summarization_status=SummarizationStatus.FAILED,
                error_message=str(e)
            )
```

## 受け入れ条件

- [ ] JSON 出力を正しくパース
- [ ] `\`\`\`json ... \`\`\`` 形式に対応
- [ ] StructuredSummary モデルでバリデーション
- [ ] パースエラー時は適切なエラーメッセージ
- [ ] バリデーションエラー時は適切なエラーメッセージ
- [ ] pyright 型チェック成功

## 参照

- project.md: 要約設定 - 出力形式 (JSON)

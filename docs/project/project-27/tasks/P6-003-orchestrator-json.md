# P6-003: Orchestrator 結果 JSON 出力

## 概要

WorkflowResult を JSON ファイルとして保存する機能を実装する。

## フェーズ

Phase 6: オーケストレーター

## 依存タスク

- P6-002: Orchestrator WorkflowResult 生成

## 成果物

- `src/news/orchestrator.py`（更新）

## 実装内容

```python
import json
from pathlib import Path
from datetime import datetime

class NewsWorkflowOrchestrator:
    async def run(
        self,
        statuses: list[str] | None = None,
        max_articles: int | None = None,
        dry_run: bool = False,
    ) -> WorkflowResult:
        """ワークフローを実行"""
        ...

        # 結果を構築
        result = self._build_result(...)

        # JSON ファイルに保存
        self._save_result(result)

        logger.info(
            "Workflow completed",
            elapsed_seconds=result.elapsed_seconds,
            collected=result.total_collected,
            extracted=result.total_extracted,
            summarized=result.total_summarized,
            published=result.total_published,
            duplicates=result.total_duplicates,
        )

        return result

    def _save_result(self, result: WorkflowResult) -> Path:
        """結果を JSON ファイルに保存

        Parameters
        ----------
        result : WorkflowResult
            ワークフロー実行結果

        Returns
        -------
        Path
            保存先ファイルパス
        """
        output_dir = Path(self._config.output.result_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
        output_path = output_dir / f"workflow-result-{timestamp}.json"

        # Pydantic モデルを JSON 形式で保存
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(result.model_dump_json(indent=2))

        logger.info("Result saved", path=str(output_path))

        return output_path
```

出力例：
```json
{
  "total_collected": 100,
  "total_extracted": 85,
  "total_summarized": 80,
  "total_published": 75,
  "total_duplicates": 5,
  "extraction_failures": [...],
  "summarization_failures": [...],
  "publication_failures": [...],
  "started_at": "2026-01-29T12:00:00",
  "finished_at": "2026-01-29T12:15:00",
  "elapsed_seconds": 900.5,
  "published_articles": [...]
}
```

## 受け入れ条件

- [ ] 結果が JSON ファイルとして保存される
- [ ] 出力先ディレクトリが自動作成される
- [ ] ファイル名にタイムスタンプが含まれる
- [ ] JSON が正しくフォーマットされている
- [ ] 保存先パスがログに出力される
- [ ] pyright 型チェック成功

## 参照

- project.md: 出力ファイル セクション

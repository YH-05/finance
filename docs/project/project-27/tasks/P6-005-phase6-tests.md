# P6-005: Phase 6 統合テスト作成

## 概要

Phase 6 で作成した NewsWorkflowOrchestrator の統合テストを作成する。

## フェーズ

Phase 6: オーケストレーター

## 依存タスク

- P6-003: Orchestrator 結果 JSON 出力
- P6-004: Orchestrator 進捗ログ

## 成果物

- `tests/news/integration/test_orchestrator.py`（新規作成）

## テスト内容

```python
class TestNewsWorkflowOrchestrator:
    def test_正常系_全パイプラインが正常に動作する(self) -> None:
        """E2E テスト（モック使用）"""
        ...

    def test_正常系_Statusフィルタリングが機能する(self) -> None:
        ...

    def test_正常系_max_articlesで件数制限される(self) -> None:
        ...

    def test_正常系_dry_runでIssue作成スキップ(self) -> None:
        ...

    def test_正常系_結果JSONが保存される(self, tmp_path: Path) -> None:
        ...

    def test_正常系_WorkflowResultが正しく構築される(self) -> None:
        ...

    def test_正常系_抽出失敗でも処理継続(self) -> None:
        ...

    def test_正常系_要約失敗でも処理継続(self) -> None:
        ...

class TestWorkflowResultBuild:
    def test_正常系_件数が正確に集計される(self) -> None:
        ...

    def test_正常系_失敗記録が正しく生成される(self) -> None:
        ...

    def test_正常系_処理時間が正しく計算される(self) -> None:
        ...
```

## 受け入れ条件

- [ ] E2E のモック統合テストが存在
- [ ] 各コンポーネントのモック/スタブが適切に使用されている
- [ ] Status フィルタリングのテストが含まれている
- [ ] 件数制限のテストが含まれている
- [ ] ドライランのテストが含まれている
- [ ] JSON 出力のテストが含まれている
- [ ] エラー継続処理のテストが含まれている
- [ ] `make test` 成功
- [ ] テスト命名規則に従っている

## 参照

- `.claude/rules/testing-strategy.md`: テスト命名規則

# P4-006: Phase 4 単体テスト作成

## 概要

Phase 4 で作成した Summarizer のテストを作成する。

## フェーズ

Phase 4: AI要約

## 依存タスク

- P4-005: Summarizer リトライロジック

## 成果物

- `tests/news/unit/test_summarizer.py`（新規作成）

## テスト内容

```python
class TestSummarizer:
    def test_正常系_記事を要約できる(self) -> None:
        ...

    def test_正常系_本文なしでSKIPPEDステータス(self) -> None:
        ...

    def test_正常系_JSONレスポンスをパースできる(self) -> None:
        ...

    def test_正常系_JSONブロック形式をパースできる(self) -> None:
        ...

    def test_異常系_不正なJSONでFAILEDステータス(self) -> None:
        ...

    def test_異常系_タイムアウトでTIMEOUTステータス(self) -> None:
        ...

    def test_正常系_リトライ後に成功する(self) -> None:
        ...

    def test_異常系_最大リトライ後にFAILED(self) -> None:
        ...

class TestSummarizerBatch:
    def test_正常系_並列要約が機能する(self) -> None:
        ...

    def test_正常系_concurrencyで同時実行数が制限される(self) -> None:
        ...

    def test_正常系_一部失敗でも全結果が返る(self) -> None:
        ...
```

## 受け入れ条件

- [ ] Summarizer の全機能がテストされている
- [ ] Anthropic クライアントのモック/スタブが適切に使用されている
- [ ] JSON パース処理のテストが含まれている
- [ ] リトライロジックのテストが含まれている
- [ ] 並列処理のテストが含まれている
- [ ] `make test` 成功
- [ ] テスト命名規則に従っている

## 参照

- `.claude/rules/testing-strategy.md`: テスト命名規則

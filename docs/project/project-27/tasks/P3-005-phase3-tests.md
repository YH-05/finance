# P3-005: Phase 3 単体テスト作成

## 概要

Phase 3 で作成した TrafilaturaExtractor のテストを作成する。

## フェーズ

Phase 3: 本文抽出

## 依存タスク

- P3-004: TrafilaturaExtractor リトライロジック

## 成果物

- `tests/news/unit/test_trafilatura_extractor.py`（新規作成）

## テスト内容

```python
class TestTrafilaturaExtractor:
    def test_正常系_本文を抽出できる(self) -> None:
        ...

    def test_正常系_本文が短い場合FAILEDステータス(self) -> None:
        ...

    def test_異常系_タイムアウトでTIMEOUTステータス(self) -> None:
        ...

    def test_正常系_リトライ後に成功する(self) -> None:
        ...

    def test_異常系_最大リトライ後にFAILED(self) -> None:
        ...

    def test_正常系_指数バックオフが適用される(self) -> None:
        ...

class TestTrafilaturaExtractorBatch:
    def test_正常系_並列抽出が機能する(self) -> None:
        ...

    def test_正常系_concurrencyで同時実行数が制限される(self) -> None:
        ...

    def test_正常系_一部失敗でも全結果が返る(self) -> None:
        ...
```

## 受け入れ条件

- [ ] TrafilaturaExtractor の全機能がテストされている
- [ ] ArticleExtractor のモック/スタブが適切に使用されている
- [ ] リトライロジックのテストが含まれている
- [ ] 並列処理のテストが含まれている
- [ ] `make test` 成功
- [ ] テスト命名規則に従っている

## 参照

- `.claude/rules/testing-strategy.md`: テスト命名規則

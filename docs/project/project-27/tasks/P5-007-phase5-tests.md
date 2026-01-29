# P5-007: Phase 5 単体テスト作成

## 概要

Phase 5 で作成した Publisher のテストを作成する。

## フェーズ

Phase 5: GitHub Publisher

## 依存タスク

- P5-006: Publisher ドライランモード

## 成果物

- `tests/news/unit/test_publisher.py`（新規作成）

## テスト内容

```python
class TestPublisher:
    def test_正常系_Issue本文を生成できる(self) -> None:
        ...

    def test_正常系_関連情報なしでセクション省略(self) -> None:
        ...

    def test_正常系_カテゴリからStatusを解決できる(self) -> None:
        ...

    def test_正常系_未知のカテゴリでfinanceがフォールバック(self) -> None:
        ...

    def test_正常系_要約なしでSKIPPEDステータス(self) -> None:
        ...

class TestPublisherDuplicate:
    def test_正常系_重複記事を検出できる(self) -> None:
        ...

    def test_正常系_重複なしで正常処理(self) -> None:
        ...

class TestPublisherDryRun:
    def test_正常系_ドライランでIssue作成スキップ(self) -> None:
        ...

    def test_正常系_ドライランでもSUCCESSステータス(self) -> None:
        ...

class TestPublisherBatch:
    def test_正常系_複数記事を公開できる(self) -> None:
        ...

    def test_正常系_一部失敗でも全結果が返る(self) -> None:
        ...
```

## 受け入れ条件

- [ ] Publisher の全機能がテストされている
- [ ] `gh` コマンドのモック/スタブが適切に使用されている
- [ ] Issue 本文生成のテストが含まれている
- [ ] Status 解決のテストが含まれている
- [ ] 重複チェックのテストが含まれている
- [ ] ドライランのテストが含まれている
- [ ] `make test` 成功
- [ ] テスト命名規則に従っている

## 参照

- `.claude/rules/testing-strategy.md`: テスト命名規則

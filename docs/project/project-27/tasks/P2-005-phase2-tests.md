# P2-005: Phase 2 単体テスト作成

## 概要

Phase 2 で作成した RSSCollector のテストを作成する。

## フェーズ

Phase 2: RSS収集

## 依存タスク

- P2-004: RSSCollector 日時フィルタリング実装

## 成果物

- `tests/news/unit/test_rss_collector.py`（新規作成）

## テスト内容

```python
class TestRSSCollector:
    def test_正常系_フィードから記事を収集できる(self) -> None:
        ...

    def test_正常系_categoryが正しく設定される(self) -> None:
        ...

    def test_正常系_category未指定でデフォルト値が設定される(self) -> None:
        ...

    def test_正常系_日時フィルタリングが機能する(self) -> None:
        ...

    def test_エッジケース_published_Noneの記事は含まれる(self) -> None:
        ...

    def test_正常系_空のフィードで空リストを返す(self) -> None:
        ...
```

## 受け入れ条件

- [ ] RSSCollector の全機能がテストされている
- [ ] FeedParser のモック/スタブが適切に使用されている
- [ ] 正常系・異常系・エッジケースがカバーされている
- [ ] `make test` 成功
- [ ] テスト命名規則に従っている

## 参照

- `.claude/rules/testing-strategy.md`: テスト命名規則

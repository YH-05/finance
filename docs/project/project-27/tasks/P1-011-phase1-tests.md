# P1-011: Phase 1 単体テスト作成

## 概要

Phase 1 で作成したモデル・設定・基底クラスのテストを作成する。

## フェーズ

Phase 1: 基盤（モデル・設定・インターフェース）

## 依存タスク

- P1-006: FailureRecord, WorkflowResult モデル作成
- P1-009: BaseCollector 抽象クラス作成
- P1-010: BaseExtractor 抽象クラス作成

## 成果物

- `tests/news/unit/test_models.py`（新規作成）
- `tests/news/unit/test_config.py`（新規作成）

## テスト内容

### test_models.py

```python
class TestSourceType:
    def test_正常系_全ての情報源タイプが定義されている(self) -> None:
        assert SourceType.RSS == "rss"
        assert SourceType.YFINANCE == "yfinance"
        assert SourceType.SCRAPE == "scrape"

class TestArticleSource:
    def test_正常系_有効なデータで作成できる(self) -> None:
        source = ArticleSource(
            source_type=SourceType.RSS,
            source_name="CNBC Markets",
            category="market",
            feed_id="cnbc-markets"
        )
        assert source.source_type == SourceType.RSS

class TestCollectedArticle:
    def test_正常系_有効なデータで作成できる(self) -> None:
        ...

class TestExtractedArticle:
    def test_正常系_有効なデータで作成できる(self) -> None:
        ...

class TestSummarizedArticle:
    def test_正常系_有効なデータで作成できる(self) -> None:
        ...

class TestPublishedArticle:
    def test_正常系_有効なデータで作成できる(self) -> None:
        ...

class TestWorkflowResult:
    def test_正常系_有効なデータで作成できる(self) -> None:
        ...
```

### test_config.py

```python
class TestLoadConfig:
    def test_正常系_設定ファイルを読み込める(self, tmp_path: Path) -> None:
        ...

    def test_異常系_存在しないファイルでFileNotFoundError(self) -> None:
        ...

    def test_正常系_status_mappingでカテゴリ解決できる(self) -> None:
        ...
```

## 受け入れ条件

- [ ] 全 Pydantic モデルのバリデーションテストが存在
- [ ] 正常系・異常系・エッジケースがカバーされている
- [ ] 設定ファイル読み込みテストが存在
- [ ] `make test` 成功
- [ ] テスト命名規則に従っている

## 参照

- `.claude/rules/testing-strategy.md`: テスト命名規則

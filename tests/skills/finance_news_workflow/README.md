# Finance News Workflow Tests

`finance-news-workflow` スキルのユーティリティ関数テストスイート。

## ディレクトリ構成

```
tests/skills/finance_news_workflow/
├── __init__.py
├── README.md              # このファイル
└── unit/                  # 単体テスト
    ├── __init__.py
    ├── test_filtering.py       # フィルタリングロジックのテスト
    ├── test_transformation.py  # データ変換のテスト
    └── test_edge_cases.py      # エッジケースのテスト
```

## テスト実行

```bash
# 全テスト実行
uv run pytest tests/skills/finance_news_workflow/ -v

# カバレッジ付き
uv run pytest tests/skills/finance_news_workflow/ --cov=.claude.skills.finance_news_workflow.utils --cov-report=term-missing

# 特定テストのみ
uv run pytest tests/skills/finance_news_workflow/unit/test_filtering.py -v

# 特定のテストクラス
uv run pytest tests/skills/finance_news_workflow/unit/test_filtering.py::TestMatchesFinancialKeywords -v
```

## テストケース概要

### test_filtering.py

- `TestMatchesFinancialKeywords`: 金融キーワードマッチングのテスト
  - 正常系: 複数キーワードマッチ
  - エッジケース: キーワードなし、空文字列
  - 大文字小文字の区別なし

- `TestIsExcluded`: 除外判定のテスト
  - 除外キーワードを含む記事
  - 金融キーワードと除外キーワード両方を含む場合の優先順位

### test_transformation.py

- `TestConvertToIssueFormat`: GitHub Issue形式変換のテスト
  - 完全なデータからの変換
  - 一部フィールド欠損時のフォールバック
  - Markdown形式の検証

### test_edge_cases.py

- エッジケース全般のテスト
  - None値、空文字列の処理
  - 不正なデータ形式への対応
  - 境界値テスト

## フィクスチャ

各テストファイルで共通のフィクスチャを定義:

```python
@pytest.fixture
def filter_config() -> dict:
    """フィルタ設定のフィクスチャ"""

@pytest.fixture
def sample_feed_item() -> FeedItem:
    """サンプル記事のフィクスチャ"""
```

## テスト戦略

`.claude/rules/testing-strategy.md` に準拠:

- **TDD**: Red → Green → Refactor
- **命名規則**: `test_[正常系|異常系|エッジケース]_条件で結果`
- **カバレッジ目標**: 80%以上

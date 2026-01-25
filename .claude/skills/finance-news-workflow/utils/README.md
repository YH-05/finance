# Finance News Workflow Utils

金融ニュース収集ワークフローで使用されるPythonユーティリティ関数を提供します。

## モジュール構成

```
utils/
├── __init__.py           # パッケージ初期化、API エクスポート
├── filtering.py          # フィルタリングロジック
├── transformation.py     # データ変換ロジック
└── README.md            # このファイル
```

## API

### filtering.py

```python
from .filtering import matches_financial_keywords, is_excluded

def matches_financial_keywords(item: FeedItem, filter_config: dict) -> bool:
    """金融キーワードにマッチするかチェック"""

def is_excluded(item: FeedItem, filter_config: dict) -> bool:
    """除外対象かチェック"""
```

### transformation.py

```python
from .transformation import convert_to_issue_format

def convert_to_issue_format(item: FeedItem, filter_config: dict) -> dict[str, str]:
    """FeedItemをGitHub Issue形式に変換"""
```

## 使用例

```python
from .claude.skills.finance_news_workflow.utils import (
    matches_financial_keywords,
    is_excluded,
    convert_to_issue_format,
)
from rss.types import FeedItem

# フィルタリング設定
config = {
    "keywords": {
        "include": {"market": ["株価", "株式"]},
        "exclude": {"sports": ["サッカー"]},
    },
    "filtering": {"min_keyword_matches": 1},
}

# フィード記事
item = FeedItem(
    item_id="1",
    title="株価が上昇",
    link="https://example.com",
    published="2026-01-15T10:00:00Z",
    summary="市場動向",
    content="詳細",
    author="記者A",
    fetched_at="2026-01-15T11:00:00Z",
)

# フィルタリング
if matches_financial_keywords(item, config) and not is_excluded(item, config):
    # GitHub Issue形式に変換
    issue = convert_to_issue_format(item, config)
    print(issue["title"])
    print(issue["body"])
```

## テスト

```bash
# 全テスト実行
uv run pytest tests/skills/finance_news_workflow/ -v

# 特定テストのみ
uv run pytest tests/skills/finance_news_workflow/unit/test_filtering.py -v
```

## 設計方針

### スキルベースアーキテクチャ

このユーティリティは `finance-news-workflow` スキルの一部として実装されています。

**利点**:
- スキル内で完結した実装
- ドキュメント（guide.md）とコードの近接配置
- 再利用可能なユーティリティとしてのパッケージ化

### 依存関係

- `rss.types.FeedItem`: RSS記事の型定義
- Python 3.12+: 型ヒント（PEP 695）を使用

### コーディング規約

`.claude/rules/coding-standards.md` に準拠:
- NumPy形式のDocstring
- PEP 695型ヒント
- snake_case命名規則

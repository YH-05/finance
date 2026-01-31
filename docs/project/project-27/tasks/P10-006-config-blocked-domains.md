# P10-006: NewsWorkflowConfigにブロックリスト読み込み

## 概要

`blocked_domains` 設定をNewsWorkflowConfigクラスで読み込めるようにする。

## 変更内容

### 変更ファイル

| ファイル | 変更内容 |
|----------|----------|
| `src/news/config/workflow.py` | `DomainFilteringConfig` 追加 |

### 実装詳細

```python
# src/news/config/workflow.py

from pydantic import BaseModel, Field


class DomainFilteringConfig(BaseModel):
    """ドメインフィルタリング設定。"""

    enabled: bool = True
    log_blocked: bool = True
    blocked_domains: list[str] = Field(default_factory=list)

    def is_blocked(self, url: str) -> bool:
        """URLがブロック対象かどうかを判定。

        Parameters
        ----------
        url : str
            チェックするURL。

        Returns
        -------
        bool
            ブロック対象の場合True。
        """
        if not self.enabled:
            return False

        from urllib.parse import urlparse
        parsed = urlparse(url)
        domain = parsed.netloc.lower()

        # サブドメインも含めてチェック
        for blocked in self.blocked_domains:
            if domain == blocked or domain.endswith(f".{blocked}"):
                return True

        return False


class NewsWorkflowConfig(BaseModel):
    """ワークフロー設定。"""

    # 既存フィールド
    status_mapping: dict[str, str]
    github_status_ids: dict[str, str]
    rss: RssConfig
    extraction: ExtractionConfig
    summarization: SummarizationConfig
    github: GitHubConfig
    filtering: FilteringConfig
    output: OutputConfig

    # 追加
    domain_filtering: DomainFilteringConfig = Field(
        default_factory=DomainFilteringConfig
    )


def load_config(config_path: Path) -> NewsWorkflowConfig:
    """設定ファイルを読み込む。"""
    with open(config_path) as f:
        data = yaml.safe_load(f)

    # blocked_domains を domain_filtering に変換
    if "blocked_domains" in data:
        data["domain_filtering"] = {
            "blocked_domains": data.pop("blocked_domains"),
            **data.get("domain_filtering", {}),
        }

    return NewsWorkflowConfig(**data)
```

## 受け入れ条件

- [ ] `DomainFilteringConfig` クラスが追加される
- [ ] `is_blocked` メソッドがサブドメインを正しく判定する
- [ ] 設定ファイルから正しく読み込める
- [ ] デフォルト値（enabled=True, 空リスト）で動作する
- [ ] 単体テストが通る

## テストケース

```python
class TestDomainFilteringConfig:
    def test_blocked_domain_returns_true(self):
        """ブロックドメインはTrueを返す。"""
        config = DomainFilteringConfig(
            blocked_domains=["seekingalpha.com"]
        )

        assert config.is_blocked("https://seekingalpha.com/article/123")
        assert config.is_blocked("https://www.seekingalpha.com/article/123")

    def test_allowed_domain_returns_false(self):
        """許可ドメインはFalseを返す。"""
        config = DomainFilteringConfig(
            blocked_domains=["seekingalpha.com"]
        )

        assert not config.is_blocked("https://cnbc.com/article/123")

    def test_disabled_filtering_allows_all(self):
        """無効時は全て許可。"""
        config = DomainFilteringConfig(
            enabled=False,
            blocked_domains=["seekingalpha.com"]
        )

        assert not config.is_blocked("https://seekingalpha.com/article/123")
```

## 依存関係

- 依存先: P10-005
- ブロック: P10-007

## 見積もり

- 作業時間: 25分
- 複雑度: 中

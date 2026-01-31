# P10-009: TrafilaturaExtractorにUser-Agent設定

## 概要

TrafilaturaExtractorでUser-Agentをローテーションする機能を実装する。

## 変更内容

### 変更ファイル

| ファイル | 変更内容 |
|----------|----------|
| `src/news/config/workflow.py` | `UserAgentConfig` 追加 |
| `src/news/extractors/trafilatura.py` | User-Agentローテーション実装 |

### 実装詳細

#### config/workflow.py

```python
class UserAgentRotationConfig(BaseModel):
    """User-Agentローテーション設定。"""

    enabled: bool = True
    user_agents: list[str] = Field(default_factory=list)

    def get_random_user_agent(self) -> str | None:
        """ランダムにUser-Agentを選択。

        Returns
        -------
        str | None
            User-Agent文字列、リストが空の場合はNone。
        """
        if not self.enabled or not self.user_agents:
            return None

        import random
        return random.choice(self.user_agents)


class ExtractionConfig(BaseModel):
    """本文抽出設定。"""

    concurrency: int = 5
    timeout_seconds: int = 30
    min_body_length: int = 200
    max_retries: int = 3
    user_agent_rotation: UserAgentRotationConfig = Field(
        default_factory=UserAgentRotationConfig
    )
```

#### extractors/trafilatura.py

```python
class TrafilaturaExtractor(BaseExtractor):
    """trafilaturaを使用した本文抽出。"""

    def __init__(self, config: NewsWorkflowConfig) -> None:
        self._config = config
        self._extraction_config = config.extraction
        self._ua_config = config.extraction.user_agent_rotation
        # ...

    async def extract(self, article: CollectedArticle) -> ExtractedArticle:
        """単一記事の本文を抽出。"""
        # User-Agent選択
        user_agent = self._ua_config.get_random_user_agent()

        if user_agent:
            logger.debug(
                "Using custom User-Agent",
                url=str(article.url),
                user_agent=user_agent[:50] + "...",
            )

        # trafilaturaに渡す（既存ArticleExtractorを経由）
        result = await self._extractor.extract(
            str(article.url),
            user_agent=user_agent,
        )
        # ...
```

#### rss/services/article_extractor.py（参考）

```python
# ArticleExtractor側も対応が必要な場合
async def extract(
    self,
    url: str,
    user_agent: str | None = None,
) -> ExtractionResult:
    """記事本文を抽出。

    Parameters
    ----------
    user_agent : str | None
        カスタムUser-Agent。
    """
    # httpxクライアントにUser-Agentを設定
    headers = {}
    if user_agent:
        headers["User-Agent"] = user_agent

    # ...
```

## 受け入れ条件

- [ ] リクエスト毎にランダムなUser-Agentが使用される
- [ ] 設定無効時はデフォルトUser-Agentが使用される
- [ ] User-Agentがログに出力される（DEBUG）
- [ ] 単体テストが通る

## テストケース

```python
class TestUserAgentRotation:
    def test_random_selection(self):
        """User-Agentがランダムに選択される。"""
        config = UserAgentRotationConfig(
            user_agents=["UA1", "UA2", "UA3"]
        )

        selections = {config.get_random_user_agent() for _ in range(100)}

        assert len(selections) >= 2  # 複数種類が選択される

    def test_disabled_returns_none(self):
        """無効時はNoneを返す。"""
        config = UserAgentRotationConfig(
            enabled=False,
            user_agents=["UA1"]
        )

        assert config.get_random_user_agent() is None
```

## 依存関係

- 依存先: P10-008
- ブロック: P10-016

## 見積もり

- 作業時間: 30分
- 複雑度: 中

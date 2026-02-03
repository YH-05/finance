# RSS Collector の User-Agent 設定追加（429/接続拒否エラー修正）

## 問題概要

`finance_news_workflow.py` のフェーズ 1（RSS 収集）で、Yahoo Finance が `429 Too Many Requests`、Nasdaq 系フィードが接続拒否（空エラー）を返す。

### 発生エラー

```
[error] Feed collection failed [news.collectors.rss]
  error="Client error '429 Too Many Requests' ..."
  feed_name='Yahoo Finance'
  feed_url=https://finance.yahoo.com/news/rssindex

[error] Feed collection failed [news.collectors.rss]
  error=
  feed_name='Nasdaq Stock News'
  feed_url='https://www.nasdaq.com/feed/rssoutbound?category=stocks'

[error] Feed collection failed [news.collectors.rss]
  error=
  feed_name='Nasdaq ETFs'
  feed_url='https://www.nasdaq.com/feed/rssoutbound?category=etfs'

[error] Feed collection failed [news.collectors.rss]
  error=
  feed_name='Nasdaq Markets'
  feed_url='https://www.nasdaq.com/feed/rssoutbound?category=markets'
```

### 根本原因

`RSSCollector` が `httpx.AsyncClient` を User-Agent ヘッダーなしで生成している。

```python
# src/news/collectors/rss.py:155
async with httpx.AsyncClient(timeout=30.0) as client:
```

httpx のデフォルト User-Agent は `python-httpx/0.x.x` であり、Yahoo Finance・Nasdaq はこれをボットと判定してリクエストを拒否する。

### 現状の UA 設定状況

| フェーズ | コンポーネント | UA 設定 | 状態 |
|---------|---------------|---------|------|
| 1. 収集 | `RSSCollector` | **なし** | httpx デフォルト (`python-httpx/...`) |
| 2. 抽出 | `TrafilaturaExtractor` | **あり** | `config.extraction.user_agent_rotation` を使用 |
| 3. 要約 | `Summarizer` | N/A | Claude API のため不要 |
| 4. 公開 | `Publisher` | N/A | gh CLI のため不要 |

フェーズ 2 では `extraction.user_agent_rotation` が正しく参照されブラウザ UA が使用されるが、フェーズ 1 では完全に未設定。

### ワークフローへの影響

フェーズ 1 のフィードエラーはフィード単位で `except` → `continue` されるため（`src/news/collectors/rss.py:169`）、ワークフロー自体は**停止せず続行する**。ただし以下の問題が発生する。

#### 1. 4フィード分の記事がサイレントに欠落する

該当フィードの記事がフェーズ 2 以降に一切渡らず、GitHub Issue として公開されない。

| フィード | カテゴリ | 失われる記事 |
|---------|---------|-------------|
| Yahoo Finance | market | Yahoo Finance 発のニュース全件 |
| Nasdaq Stock News | stock | Nasdaq 個別株ニュース全件 |
| Nasdaq ETFs | etfs | Nasdaq ETF ニュース全件 |
| Nasdaq Markets | market | Nasdaq 市場ニュース全件 |

#### 2. 欠落がコンソール出力に表示されない

`print_failure_summary()` は抽出・要約・公開の失敗のみを表示する。フィードエラーは `WorkflowResult.feed_errors` に記録されるが、最終サマリーには含まれない。欠落に気付くには実行時のログ出力（`[error] Feed collection failed`）を確認するか、`feed_errors` フィールドの件数を見る必要がある。

#### 3. 成功フィードへの影響はなし

残りの成功したフィード（504件）はフェーズ 2 → 3 → 4 と正常に処理され、Issue 作成まで完了する。

---

## 変更対象ファイル

| ファイル | 変更内容 |
|----------|----------|
| `src/news/config/models.py` | `RssConfig` に `user_agent_rotation` フィールド追加 |
| `src/news/collectors/rss.py` | `httpx.AsyncClient` に UA ヘッダーを設定 |
| `data/config/news-collection-config.yaml` | `rss` セクションに `user_agent_rotation` 設定追加 |
| `tests/news/unit/collectors/test_rss.py` | UA ヘッダー送信のテスト追加 |

---

## 修正方針

既存の `UserAgentRotationConfig` モデルと `extraction.user_agent_rotation` の設計パターンを `RssConfig` にも適用する。フェーズ 2 で実績のある仕組みをそのまま再利用し、設定ファイルでは同じ UA リストを `rss` セクション内にも配置する。

### 方針選定の理由

| 案 | 内容 | 採否 | 理由 |
|----|------|------|------|
| A. `RssConfig` に専用 UA 設定を追加 | `rss.user_agent_rotation` | **採用** | フェーズごとに独立して設定可能。既存の `extraction` 設定に影響なし |
| B. `extraction.user_agent_rotation` を共有参照 | オーケストレータが `extraction` の UA を `RSSCollector` に注入 | 不採用 | 設定の責務が混在する。RSS 収集と本文抽出は独立した関心事 |
| C. トップレベルに共通 UA 設定を新設 | `user_agent_rotation` をルートに配置 | 不採用 | 既存設定ファイルの構造変更が大きい。後方互換性の問題 |

---

## 修正内容

### 1. `src/news/config/models.py` — `RssConfig` にフィールド追加

```python
class RssConfig(BaseModel):
    presets_file: str = Field(
        ...,
        description="Path to the RSS presets JSON file",
    )
    retry: RssRetryConfig = Field(
        default_factory=RssRetryConfig,
        description="Retry configuration for feed collection",
    )
    # ---- 追加 ----
    user_agent_rotation: UserAgentRotationConfig = Field(
        default_factory=UserAgentRotationConfig,
        description="User-Agent rotation configuration for RSS feed fetching",
    )
```

`UserAgentRotationConfig` は既存モデル（`src/news/config/models.py:554`）をそのまま再利用する。新規モデル定義は不要。

### 2. `src/news/collectors/rss.py` — UA ヘッダーの設定

#### 2.1 `__init__` に UA 設定参照を追加

```python
def __init__(self, config: NewsWorkflowConfig) -> None:
    self._config = config
    self._parser = FeedParser()
    self._domain_filter = config.domain_filtering
    self._feed_errors: list[FeedError] = []
    # ---- 追加 ----
    self._ua_config = config.rss.user_agent_rotation
```

#### 2.2 `collect()` の `httpx.AsyncClient` にヘッダーを設定

**変更前**（155行目）:
```python
async with httpx.AsyncClient(timeout=30.0) as client:
```

**変更後**:
```python
headers = self._build_headers()
async with httpx.AsyncClient(timeout=30.0, headers=headers) as client:
```

#### 2.3 `_build_headers()` メソッドを新規追加

```python
def _build_headers(self) -> dict[str, str]:
    """Build HTTP headers with User-Agent for RSS feed requests.

    Returns
    -------
    dict[str, str]
        HTTP headers dictionary. If UA rotation is enabled,
        includes a randomly selected browser User-Agent.
    """
    headers: dict[str, str] = {
        "Accept": "application/rss+xml, application/xml, text/xml, */*",
    }

    if self._ua_config:
        ua = self._ua_config.get_random_user_agent()
        if ua:
            headers["User-Agent"] = ua
            logger.debug(
                "Using custom User-Agent for RSS collection",
                user_agent=ua[:50] + "..." if len(ua) > 50 else ua,
            )

    return headers
```

**設計上のポイント**:
- `Accept` ヘッダーも追加する。RSS/XML を明示的に受け入れることで、サーバーが適切な Content-Type で応答しやすくなる
- UA はクライアント生成時（全フィード共通）に 1 回設定する。フィードごとのローテーションは不要（短時間での同一 IP からの異なる UA はかえって不審と判定される可能性がある）

### 3. `data/config/news-collection-config.yaml` — 設定追加

```yaml
rss:
  presets_file: "data/config/rss-presets.json"

  # User-Agent ローテーション（ボット検出回避）
  user_agent_rotation:
    enabled: true
    user_agents:
      # Chrome (Windows)
      - "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
      # Chrome (macOS)
      - "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
      # Firefox (Windows)
      - "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0"
      # Safari (macOS)
      - "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15"
      # Chrome (Linux)
      - "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
```

`extraction.user_agent_rotation.user_agents` と同じリストを使用する。設定ファイル上は重複するが、フェーズ間の設定独立性を優先する。

### 4. テスト追加

`tests/news/unit/collectors/test_rss.py` に以下のテストケースを追加:

| テスト名 | 検証内容 |
|---------|---------|
| `test_正常系_ブラウザUAでリクエストを送信` | httpx リクエストに UA ヘッダーが含まれることを検証 |
| `test_正常系_UA無効時はデフォルトUAで送信` | `enabled: false` 時に UA ヘッダーが設定されないことを検証 |
| `test_正常系_AcceptヘッダーにRSS形式が含まれる` | Accept ヘッダーに `application/rss+xml` が含まれることを検証 |

---

## 実装チェックリスト

- [ ] `src/news/config/models.py`: `RssConfig` に `user_agent_rotation: UserAgentRotationConfig` フィールド追加
- [ ] `src/news/collectors/rss.py`: `__init__` に `self._ua_config` 追加
- [ ] `src/news/collectors/rss.py`: `_build_headers()` メソッド追加
- [ ] `src/news/collectors/rss.py`: `httpx.AsyncClient` に `headers` 引数追加
- [ ] `data/config/news-collection-config.yaml`: `rss.user_agent_rotation` セクション追加
- [ ] `tests/news/unit/collectors/test_rss.py`: UA ヘッダー検証テスト追加
- [ ] `make check-all` が成功することを確認
- [ ] Yahoo Finance フィード（`https://finance.yahoo.com/news/rssindex`）で 429 が解消されることを確認
- [ ] Nasdaq フィード（3 件）で接続拒否が解消されることを確認

---

## 補足: フィードごとの UA ローテーションを行わない理由

フィードごとに異なる UA を設定する方式（`_fetch_feed` 内でリクエストごとにローテーション）も検討したが、以下の理由で不採用とした:

1. **フィンガープリンティング対策**: 同一 IP から短時間で異なる UA が送信されると、逆にボット判定されるリスクが上がる
2. **httpx の設計**: `AsyncClient` はセッション単位でヘッダーを保持する設計であり、リクエストごとの上書きはコードの複雑性が増す
3. **実用上の十分性**: 実行ごとにランダムな 1 つの UA を使用すれば、ボット検出は十分に回避できる

ワークフローの実行間隔（通常 1 日 1 回以上）を考慮すると、セッション単位のローテーションで十分。

---

## 追加改善: 重複チェックのフェーズ前倒し

### 現状の問題

現在のパイプラインでは、重複チェックはフェーズ 4（`Publisher.publish_batch`）内で実行される。つまり、重複記事に対してもフェーズ 2（本文抽出）とフェーズ 3（AI 要約）が実行され、リソースが無駄に消費される。

```
【現状の処理順序】 src/news/orchestrator.py:186-269

収集(504件)
  → ステータスフィルタ / 記事数制限
  → 抽出（504件全てに HTTP リクエスト + trafilatura 処理）
  → 要約（抽出成功分全てに Claude API 呼出）
  → 重複チェック + 公開（ここで初めて重複を除外）
```

重複チェックに使う URL は `CollectedArticle.url` としてフェーズ 1 完了時点で確定しているため、後続フェーズに渡す前に除外できる。

### 改善案

重複チェックをフェーズ 1 直後（フェーズ 2 の前）に移動する。

```
【改善後の処理順序】

収集(504件)
  → ステータスフィルタ / 記事数制限
  → 重複チェック（既存 Issue の URL と照合、重複を除外）
  → 抽出（新規記事のみ）
  → 要約（新規記事のみ）
  → 公開（重複チェック済みのためスキップなし）
```

### 節約できるコスト

重複記事 1 件あたり、以下の処理をスキップできる:

| フェーズ | 1 件あたりのコスト | 節約 |
|---------|-------------------|------|
| 2. 抽出 | HTTP リクエスト 1〜4 回（リトライ含む）+ trafilatura | 節約可 |
| 3. 要約 | Claude API 呼出 1 回（最大 60s × リトライ 3 回） | **最も効果大** |

フェーズ 3 の Claude API 呼出が処理時間・コストともに最も大きいため、ここを削減する効果が高い。

### 変更対象ファイル

| ファイル | 変更内容 |
|----------|----------|
| `src/news/orchestrator.py` | フェーズ 1 後に重複チェックステップを追加 |
| `src/news/publisher.py` | `_get_existing_issues()` と `_is_duplicate()` を外部から呼び出し可能にする |
| `tests/news/unit/test_orchestrator.py` | 重複チェック前倒しの検証テスト追加 |

### 修正内容

#### 1. `src/news/publisher.py` — 重複チェックメソッドの公開

`_get_existing_issues()` を外部から呼び出せるよう公開メソッド化する。`_is_duplicate()` も URL ベースの判定を `CollectedArticle` で使えるよう汎用化する。

```python
# 既存の _get_existing_issues を公開化
async def get_existing_urls(self, days: int | None = None) -> set[str]:
    """直近N日の既存 Issue から記事 URL を取得する。

    Parameters
    ----------
    days : int | None, optional
        取得対象期間。None の場合は config の duplicate_check_days を使用。

    Returns
    -------
    set[str]
        既存 Issue に含まれる記事 URL のセット。
    """
    check_days = days or self._config.github.duplicate_check_days
    return await self._get_existing_issues(days=check_days)
```

```python
# URL ベースの重複判定（CollectedArticle 用）
def is_duplicate_url(self, url: str, existing_urls: set[str]) -> bool:
    """URL が既存 Issue に含まれるか判定する。"""
    return url in existing_urls
```

#### 2. `src/news/orchestrator.py` — フェーズ 1 後に重複チェックを挿入

`run()` メソッドのフェーズ 1（収集）直後、フェーズ 2（抽出）の前に重複チェックステップを追加する。

**変更箇所**: `run()` メソッド内、ステータスフィルタ/記事数制限の後（202行目付近）

```python
# Apply max_articles limit
if max_articles and len(collected) > max_articles:
    collected = collected[:max_articles]
    print(f"  記事数制限適用: {len(collected)}件")

# ---- 追加: 重複チェック（フェーズ2の前に実行） ----
existing_urls = await self._publisher.get_existing_urls()
before_dedup = len(collected)
collected = [
    a for a in collected
    if not self._publisher.is_duplicate_url(str(a.url), existing_urls)
]
dedup_count = before_dedup - len(collected)
if dedup_count > 0:
    print(f"  重複除外: {before_dedup} -> {len(collected)}件 (重複: {dedup_count}件)")

if not collected:
    print("  -> 処理対象の記事がありません")
    # ... 既存の早期リターン処理
```

#### 3. `Publisher.publish_batch()` — 重複チェックの二重実行を防止

重複チェックがフェーズ 1 後で完了しているため、`publish_batch()` 内の重複チェックは冗長になる。ただし安全策として残し、ログレベルを下げる。

```python
# publish_batch() 内の既存重複チェック（変更なし、安全策として維持）
if self._is_duplicate(article, existing_urls):
    duplicate_count += 1
    logger.debug(  # info → debug に変更（通常到達しないため）
        "Duplicate detected in publish_batch (safety check)",
        article_url=str(article.extracted.collected.url),
    )
    # ... 既存の DUPLICATE 処理
```

### WorkflowResult への影響

重複チェックの前倒しにより `total_duplicates` の計上位置が変わる。現状は `PublishedArticle` の `DUPLICATE` ステータスから計上しているが、改善後はフェーズ 1 の段階で除外されるため `published` リストに含まれなくなる。

対応方法: `_build_result()` に `total_duplicates_early` パラメータを追加するか、`run()` 内で直接カウントして `WorkflowResult` に反映する。

```python
result = self._build_result(
    collected=collected,
    extracted=extracted,
    summarized=summarized,
    published=published,
    started_at=started_at,
    finished_at=finished_at,
    early_duplicates=dedup_count,  # 追加
)
```

### テスト追加

| テスト名 | 検証内容 |
|---------|---------|
| `test_正常系_重複記事がフェーズ2前に除外される` | 既存 URL と一致する記事が抽出対象から除外されることを検証 |
| `test_正常系_重複除外後に記事が0件で早期リターン` | 全記事が重複の場合に空の `WorkflowResult` が返ることを検証 |
| `test_正常系_重複件数がWorkflowResultに反映される` | `total_duplicates` に前倒しチェックの除外数が含まれることを検証 |

### 実装チェックリスト

- [ ] `src/news/publisher.py`: `get_existing_urls()` 公開メソッド追加
- [ ] `src/news/publisher.py`: `is_duplicate_url()` 公開メソッド追加
- [ ] `src/news/orchestrator.py`: フェーズ 1 後に重複チェックステップを挿入
- [ ] `src/news/orchestrator.py`: `_build_result()` に `early_duplicates` 対応追加
- [ ] `src/news/publisher.py`: `publish_batch()` 内の重複チェックログレベルを `debug` に変更
- [ ] `tests/news/unit/test_orchestrator.py`: 重複チェック前倒しのテスト追加
- [ ] `make check-all` が成功することを確認

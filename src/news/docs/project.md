# news プロジェクト

**GitHub Project**: [#24](https://github.com/users/YH-05/projects/24)

## 概要

**汎用ニュース収集パッケージ** - 複数のデータソースからニュースを取得し、様々な出力先に保存する。

### 解決する課題

- 複数のニュースソースを統一的に扱いたい
  - python yfinance Tickerクラスで取得できる個別銘柄・指数・セクターETF・コモディティのニュース
  - python yfinance Searchクラスで取得できるキーワード検索によるマクロ経済・テーマ別ニュース
  - webスクレイピングで取得した記事など
- 出力先（ファイル、GitHub Issue、レポート用データ）を柔軟に切り替えたい
  - GitHub ProjectにIssueとしてニュースを投稿したい
  - 日次のニュース収集や週次のレポート作成、将来の詳細レポート作成に役立てたい
- 対象カテゴリ（金融、テクノロジー等）を設定可能にしたい
  - 情報ソースとカテゴリごとに取得方法を定める
- 収集したニュースをAIに翻訳・要約・タグ付けなどをしてもらいたい
  - 情報収集まではpythonの自動化スクリプトで行い、ニュースの解釈をAIに任せる
  - 情報収集をpythonで自動化することにより、AIの無駄なコンテキスト消費を抑える狙い
- 将来的にはスクリプトを定期実行してニュース収集作業を自動化する

### MCPサーバーやスキルとの使い分け
- tavily mcpサーバーやgemini searchスキル、web searchを使用した検索は、AIが動的にweb検索を行うためのツール
- それに対し、newsパッケージが提供するものは、あらかじめ定めたニュースソースからの情報収集自動化機能(AIに情報を渡すところまで)である
- またrss mcpサーバー(financeプロジェクトで作成しているsrc/rssのこと)はRSSフィード取得に特化しているが、newsパッケージはRSSフィードを取り扱わない

### 既存エージェントとの関係

本パッケージは2つの利用パターンを想定：

**パターンA: 対話的利用**
- ユーザー → Claude Code → newsパッケージ呼び出し
- `.claude/agents/` 配下の `finance-news-*` エージェント群がnewsパッケージを呼び出す
- 取得したデータをJSON形式で受け取り、エージェント側でGitHub Issue投稿等を実行

**パターンB: 自動実行ワークフロー**
- cron等 → Pythonスクリプト → newsパッケージでニュース収集
- → Claude Agent SDK経由でエージェント起動
- → エージェントが要約・分類・GitHub投稿を実行
- 定期的なニュース収集の完全自動化を実現

### webスクレイピングの方針
- bot対策: コード実行にインターバルを設けてレート制限を回避
- スクレイピング手法: BeautifulSoup、Playwrightなど
- 開発方法: サイトによって対処方法が変わるため、ユーザーから開発要請を受けたらそのサイトのスクレイピングモジュールを開発する

### 設計方針

- **yfinance 最優先**: Phase 2 で yfinance ニュース取得を実装
  - **Ticker クラス**: 個別銘柄・指数・セクターETF・コモディティなど、特定ティッカーに関連するニュース
  - **Search クラス**: マクロ経済・テーマ別など、キーワード検索によるニュース
- **プラグイン方式**: データソースを抽象化し、新しいソースを容易に追加可能
  - yfinance Ticker: 株式・指数・セクター・コモディティニュース
  - yfinance Search: マクロ経済・テーマ別ニュース（キーワード検索）
  - scraper: 将来的なWebスクレイピング対応（サイト別に開発）
- **AI処理統合**: Claude Code エージェントと連携し、要約・分類を自動化
  - Claude Codeには収集したニュース情報を**json形式**で渡す(ニュースソースのURLやサマリー、日付などのメタ情報も含めて)
  - 収集情報の集約場所は一か所に定める: `finance/data/news/` フォルダに`{ニュースソース名}_{YYYYMMDD}.json`の命名規則でjson出力
    - YYYYMMDDの日時はファイル出力時の日時
  - jsonのフォーマットを作成する必要がある
- **rss パッケージと独立**: RSS 以外のソース（API、スクレイピング）に対応

## 主要機能

### Phase 0: yfinance 調査 ✅ 完了

- [x] yfinance.Ticker.news の仕様確認
- [x] yfinance.Search.news の仕様確認
- [x] 取得可能なニュースの種類・形式・フィールド
- [x] レート制限の有無
- [x] ユニークキー（重複判定に使える項目）の特定
- [x] 既存 market パッケージとの重複確認

#### 調査結果（2026-01-28）

##### yfinance.Ticker（個別銘柄・指数用）

**API仕様**:
- `ticker.news` プロパティ: デフォルト10件のニュースを取得
- `ticker.get_news(count=N, tab='news')` メソッド: 件数とタブ指定可能
  - `tab` オプション: `"news"`, `"all"`, `"press releases"`
- **制約**: 指定したティッカー（銘柄・指数・ETF等）に関連するニュースのみ取得可能
- **用途**: 個別銘柄、株価指数、セクターETF、コモディティのニュース取得

##### yfinance.Search（キーワード検索用）

**API仕様**:
- `yf.Search(query, news_count=N)` でキーワード検索によるニュース取得
- パラメータ:
  - `query`: 検索キーワード（例: "Federal Reserve", "inflation", "AI technology"）
  - `news_count`: 取得するニュース件数
  - `max_results`: クォート結果の最大件数
  - `include_research`: リサーチデータを含めるかどうか
- **制約なし**: 任意のキーワードでニュース検索が可能
- **用途**: テーマ別ニュース収集（マクロ経済、テクノロジートレンド等）

**使用例**:
```python
import yfinance as yf

# Searchクラスでキーワード検索
news = yf.Search("Federal Reserve interest rate", news_count=10).news
news = yf.Search("inflation economy", news_count=10).news
news = yf.Search("AI technology stocks", news_count=10).news
```

##### TickerとSearchの使い分け

| ユースケース | 推奨クラス | 理由 |
|-------------|-----------|------|
| 個別銘柄ニュース（AAPL, GOOGL等） | Ticker | ティッカー指定で関連ニュースを取得 |
| 株価指数ニュース（^GSPC, ^DJI等） | Ticker | 指数ティッカーで関連ニュースを取得 |
| セクターETFニュース（XLF, XLK等） | Ticker | ETFティッカーで関連ニュースを取得 |
| コモディティニュース（GC=F, CL=F等） | Ticker | コモディティティッカーで取得 |
| マクロ経済ニュース | **Search** | "Federal Reserve", "inflation"等のキーワードで検索 |
| テーマ別ニュース | **Search** | 任意のテーマキーワードで検索 |
| 業界動向ニュース | **Search** | "semiconductor industry"等で検索 |

**Ticker.news データ構造**:
```python
# 返り値: list[dict]
# 各要素の構造:
{
    "id": "UUID形式の記事ID",  # ユニークキー
    "content": {
        "id": "UUID形式の記事ID",
        "contentType": "STORY" | "VIDEO",
        "title": "記事タイトル",
        "summary": "記事要約",
        "description": "詳細説明（空の場合あり）",
        "pubDate": "2026-01-27T23:33:53Z",  # ISO8601形式
        "displayTime": "2026-01-28T06:27:34Z",
        "provider": {
            "displayName": "Yahoo Finance",
            "url": "http://finance.yahoo.com/"
        },
        "canonicalUrl": {
            "url": "https://finance.yahoo.com/news/...",
            "site": "finance",
            "region": "US",
            "lang": "en-US"
        },
        "thumbnail": {
            "originalUrl": "https://...",
            "originalWidth": 5971,
            "originalHeight": 3980,
            "resolutions": [...]
        },
        "metadata": {"editorsPick": true/false},
        "finance": {"premiumFinance": {...}},
        "storyline": {"storylineItems": [...]}  # 関連記事
    }
}
```

**Search.news データ構造**:
```python
# 返り値: list[dict]
# Ticker.newsと同様の構造（content配下にニュース情報）
# ただし related_tickers は検索クエリからは自動付与されない
{
    "id": "UUID形式の記事ID",
    "content": {
        "id": "UUID形式の記事ID",
        "contentType": "STORY" | "VIDEO",
        "title": "記事タイトル",
        "summary": "記事要約",
        "pubDate": "2026-01-27T23:33:53Z",
        "canonicalUrl": {"url": "https://..."},
        "provider": {"displayName": "...", "url": "..."},
        "thumbnail": {...}
    }
}
```

**レート制限**:
- 10件連続リクエストで問題なし（平均0.3秒/リクエスト）
- Yahoo Finance のレート制限は緩い（ただし大量リクエスト時は curl_cffi でブラウザ偽装推奨）

**ユニークキー（重複チェック用）**:
- **採用**: `canonicalUrl.url`（記事URL）を主キーとして使用
- **理由**: URL はどのソースでも必ず存在し、記事を一意に特定できる

**対応ティッカータイプ**:
| タイプ | 例 | ニュース取得 |
|--------|-----|-------------|
| 個別銘柄 | AAPL, GOOGL | ✅ 10件/リクエスト |
| 株価指数 | ^GSPC, ^DJI | ✅ 10件/リクエスト |
| セクターETF | XLF, XLK | ✅ 10件/リクエスト |
| コモディティ | GC=F, CL=F | ✅ 10件/リクエスト |

**既存 market パッケージとの関係**:
- `src/market/yfinance/` は **OHLCV価格データの取得のみ** を担当
- ニュース機能は実装されていない → **重複なし**
- news パッケージで独自に実装可能

**エラーパターン調査結果**:
| ケース | 挙動 | 対応方針 |
|--------|------|----------|
| 無効なティッカー | 空リスト `[]` を返す | 警告ログを出力、継続 |
| 空文字ティッカー | `ValueError` 例外 | 事前バリデーションで防止 |
| 上場廃止銘柄 | 空リスト `[]` を返す | 警告ログを出力、継続 |
| 特殊文字 | 空リスト `[]` を返す | 事前バリデーションで防止 |
| ネットワークエラー | 各種例外 | リトライ + 指数バックオフ |
| レート制限 | HTTPエラー / 空応答 | リトライ + 長めの待機 |

---

## 詳細設計

### エラーハンドリング戦略

#### リトライ設定

```python
@dataclass(frozen=True)
class RetryConfig:
    """リトライ設定"""
    max_attempts: int = 3          # 最大リトライ回数
    initial_delay: float = 1.0     # 初回待機時間（秒）
    max_delay: float = 60.0        # 最大待機時間（秒）
    exponential_base: float = 2.0  # 指数バックオフの基数
    jitter: bool = True            # ランダムなゆらぎを追加

    # リトライ対象の例外
    retryable_exceptions: tuple[type[Exception], ...] = (
        ConnectionError,
        TimeoutError,
        # HTTPError (429 Too Many Requests, 5xx)
    )
```

#### リトライフロー

```
1回目失敗 → 1秒待機 → 2回目失敗 → 2秒待機 → 3回目失敗 → エラーログ出力 → 次のティッカーへ継続
                       (jitterで ±50%)
```

**重要**: リトライ失敗時は例外を握りつぶし（try-except）、エラーをログに記録して次の処理に進む。
バッチ処理全体が1件の失敗で停止しないようにする。

#### エラー分類と対応

| エラー種別 | 例 | リトライ | 対応 |
|-----------|-----|---------|------|
| 一時的エラー | 接続タイムアウト, 429, 5xx | ✅ する | 指数バックオフでリトライ、最終失敗時はスキップ |
| 永続的エラー | 無効ティッカー, 認証エラー | ❌ しない | 即座にスキップ、ログ出力 |
| データなし | 空リスト返却 | ❌ しない | 警告ログ、空結果を返す |

#### エラー回避の実装パターン

```python
# === Ticker ベース（個別銘柄・指数用） ===
def fetch_all_by_ticker(tickers: list[str]) -> list[FetchResult]:
    """複数ティッカーのニュースを取得（エラー時も継続）"""
    results: list[FetchResult] = []

    for ticker in tickers:
        try:
            articles = fetch_ticker_with_retry(ticker)
            results.append(FetchResult(
                ticker=ticker,
                articles=articles,
                success=True,
            ))
        except Exception as e:
            logger.error(
                "Failed to fetch news",
                ticker=ticker,
                error=str(e),
                error_type=type(e).__name__,
            )
            results.append(FetchResult(
                ticker=ticker,
                articles=[],
                success=False,
                error=SourceError(str(e), source="yfinance", ticker=ticker),
            ))

    return results


# === Search ベース（キーワード検索用） ===
def fetch_all_by_query(queries: list[str], news_count: int = 10) -> list[FetchResult]:
    """複数キーワードでニュースを検索（エラー時も継続）"""
    results: list[FetchResult] = []

    for query in queries:
        try:
            articles = fetch_search_with_retry(query, news_count)
            results.append(FetchResult(
                query=query,
                articles=articles,
                success=True,
            ))
        except Exception as e:
            logger.error(
                "Failed to search news",
                query=query,
                error=str(e),
                error_type=type(e).__name__,
            )
            results.append(FetchResult(
                query=query,
                articles=[],
                success=False,
                error=SourceError(str(e), source="yfinance-search", ticker=None),
            ))

    return results
```

#### カスタム例外クラス

```python
class NewsError(Exception):
    """news パッケージの基底例外"""
    pass

class SourceError(NewsError):
    """データソースからの取得エラー"""
    def __init__(
        self,
        message: str,
        source: str,
        ticker: str | None = None,
        cause: Exception | None = None,
        retryable: bool = False,
    ) -> None:
        super().__init__(message)
        self.source = source
        self.ticker = ticker
        self.cause = cause
        self.retryable = retryable

class ValidationError(NewsError):
    """入力バリデーションエラー"""
    def __init__(self, message: str, field: str, value: object) -> None:
        super().__init__(message)
        self.field = field
        self.value = value

class RateLimitError(SourceError):
    """レート制限エラー（リトライ可能）"""
    def __init__(self, source: str, retry_after: float | None = None) -> None:
        super().__init__(
            f"Rate limit exceeded for {source}",
            source=source,
            retryable=True,
        )
        self.retry_after = retry_after
```

#### 取得結果の型

```python
@dataclass
class FetchResult:
    """ニュース取得結果（Ticker/Search両対応）"""
    articles: list[Article]
    success: bool
    # Ticker ベースの場合
    ticker: str | None = None
    # Search ベースの場合
    query: str | None = None
    error: SourceError | None = None
    fetched_at: datetime = field(default_factory=datetime.now)
    retry_count: int = 0

    @property
    def article_count(self) -> int:
        return len(self.articles)

    @property
    def is_empty(self) -> bool:
        return len(self.articles) == 0

    @property
    def source_identifier(self) -> str:
        """取得元の識別子（ticker または query）"""
        return self.ticker or self.query or "unknown"
```

---

### Article モデル詳細設計

#### 設計方針

- **ソース非依存**: yfinance 固有のフィールドに依存しない汎用モデル
- **必須フィールド最小化**: どのソースでも取得可能なフィールドのみ必須
- **URL を主キーとして使用**: 重複チェックは `url` フィールドで行う（`id` は不要）
- **拡張性**: `metadata` フィールドでソース固有の情報を保持

#### Article モデル定義

```python
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, HttpUrl

class ContentType(str, Enum):
    """コンテンツ種別"""
    ARTICLE = "article"    # 通常の記事
    VIDEO = "video"        # 動画コンテンツ
    PRESS_RELEASE = "press_release"  # プレスリリース
    UNKNOWN = "unknown"

class ArticleSource(str, Enum):
    """記事ソース"""
    YFINANCE_TICKER = "yfinance_ticker"  # Ticker.news 経由
    YFINANCE_SEARCH = "yfinance_search"  # Search.news 経由
    SCRAPER = "scraper"
    RSS = "rss"  # 将来的な連携用

class Provider(BaseModel):
    """配信元情報"""
    name: str                      # 配信元名（例: "Yahoo Finance"）
    url: HttpUrl | None = None     # 配信元URL

class Thumbnail(BaseModel):
    """サムネイル画像"""
    url: HttpUrl
    width: int | None = None
    height: int | None = None

class Article(BaseModel):
    """ニュース記事の共通モデル

    yfinance, スクレイパー等、複数のソースから取得した記事を
    統一的に扱うためのデータモデル。

    Attributes
    ----------
    url : HttpUrl
        記事の元URL（重複チェックの主キー）
    title : str
        記事タイトル
    published_at : datetime
        公開日時（UTC）
    source : ArticleSource
        取得元ソース

    Notes
    -----
    - **重複チェックは `url` で行う**（`id` はソースによって存在しない場合がある）
    - `summary` が空の場合は `title` を使用することを推奨
    """

    # === 必須フィールド（どのソースでも必ず取得可能） ===
    url: HttpUrl = Field(..., description="記事の元URL（重複チェックの主キー）")
    title: str = Field(..., min_length=1, description="記事タイトル")
    published_at: datetime = Field(..., description="公開日時（UTC）")
    source: ArticleSource = Field(..., description="取得元ソース")

    # === オプションフィールド ===
    summary: str | None = Field(None, description="記事要約")
    content_type: ContentType = Field(
        default=ContentType.ARTICLE,
        description="コンテンツ種別"
    )
    provider: Provider | None = Field(None, description="配信元情報")
    thumbnail: Thumbnail | None = Field(None, description="サムネイル画像")

    # === 関連情報 ===
    related_tickers: list[str] = Field(
        default_factory=list,
        description="関連ティッカーシンボル"
    )
    tags: list[str] = Field(
        default_factory=list,
        description="タグ（カテゴリ、キーワード等）"
    )

    # === メタデータ ===
    fetched_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="取得日時（UTC）"
    )
    metadata: dict[str, object] = Field(
        default_factory=dict,
        description="ソース固有のメタデータ"
    )

    # === AI処理結果（後から追加） ===
    summary_ja: str | None = Field(None, description="日本語要約（AI生成）")
    category: str | None = Field(None, description="カテゴリ（AI分類）")
    sentiment: float | None = Field(
        None,
        ge=-1.0,
        le=1.0,
        description="センチメントスコア（-1.0〜1.0）"
    )

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }
```

#### yfinance → Article 変換

```python
# === Ticker.news → Article 変換 ===
def ticker_news_to_article(raw: dict, ticker: str) -> Article:
    """yfinance Ticker.news のデータを Article モデルに変換

    Parameters
    ----------
    raw : dict
        yfinance Ticker.news から取得した生データ
    ticker : str
        取得元のティッカーシンボル

    Returns
    -------
    Article
        変換後の Article インスタンス
    """
    content = raw.get("content", {})

    content_type_map = {
        "STORY": ContentType.ARTICLE,
        "VIDEO": ContentType.VIDEO,
    }

    return Article(
        url=content.get("canonicalUrl", {}).get("url"),
        title=content.get("title", ""),
        published_at=datetime.fromisoformat(
            content.get("pubDate", "").replace("Z", "+00:00")
        ),
        source=ArticleSource.YFINANCE_TICKER,
        summary=content.get("summary"),
        content_type=content_type_map.get(
            content.get("contentType"),
            ContentType.UNKNOWN
        ),
        provider=Provider(
            name=content.get("provider", {}).get("displayName", "Unknown"),
            url=content.get("provider", {}).get("url"),
        ) if content.get("provider") else None,
        thumbnail=Thumbnail(
            url=content.get("thumbnail", {}).get("originalUrl"),
            width=content.get("thumbnail", {}).get("originalWidth"),
            height=content.get("thumbnail", {}).get("originalHeight"),
        ) if content.get("thumbnail", {}).get("originalUrl") else None,
        related_tickers=[ticker],  # ティッカーを関連銘柄として設定
        metadata={
            "yfinance_content_type": content.get("contentType"),
            "editors_pick": content.get("metadata", {}).get("editorsPick", False),
            "is_premium": content.get("finance", {}).get("premiumFinance", {}).get("isPremiumNews", False),
            "region": content.get("canonicalUrl", {}).get("region"),
            "lang": content.get("canonicalUrl", {}).get("lang"),
        },
    )


# === Search.news → Article 変換 ===
def search_news_to_article(raw: dict, query: str) -> Article:
    """yfinance Search.news のデータを Article モデルに変換

    Parameters
    ----------
    raw : dict
        yfinance Search.news から取得した生データ
    query : str
        検索に使用したキーワード

    Returns
    -------
    Article
        変換後の Article インスタンス
    """
    content = raw.get("content", {})

    content_type_map = {
        "STORY": ContentType.ARTICLE,
        "VIDEO": ContentType.VIDEO,
    }

    return Article(
        url=content.get("canonicalUrl", {}).get("url"),
        title=content.get("title", ""),
        published_at=datetime.fromisoformat(
            content.get("pubDate", "").replace("Z", "+00:00")
        ),
        source=ArticleSource.YFINANCE_SEARCH,
        summary=content.get("summary"),
        content_type=content_type_map.get(
            content.get("contentType"),
            ContentType.UNKNOWN
        ),
        provider=Provider(
            name=content.get("provider", {}).get("displayName", "Unknown"),
            url=content.get("provider", {}).get("url"),
        ) if content.get("provider") else None,
        thumbnail=Thumbnail(
            url=content.get("thumbnail", {}).get("originalUrl"),
            width=content.get("thumbnail", {}).get("originalWidth"),
            height=content.get("thumbnail", {}).get("originalHeight"),
        ) if content.get("thumbnail", {}).get("originalUrl") else None,
        related_tickers=[],  # Search では自動付与されない
        tags=[query],  # 検索キーワードをタグとして設定
        metadata={
            "yfinance_content_type": content.get("contentType"),
            "search_query": query,  # 検索クエリを保存
            "region": content.get("canonicalUrl", {}).get("region"),
            "lang": content.get("canonicalUrl", {}).get("lang"),
        },
    )
```

#### JSON 出力フォーマット

**Ticker ベース（個別銘柄・指数）**:
```json
{
  "meta": {
    "source": "yfinance_ticker",
    "ticker": "AAPL",
    "fetched_at": "2026-01-28T12:00:00Z",
    "article_count": 10,
    "version": "1.0"
  },
  "articles": [
    {
      "url": "https://finance.yahoo.com/news/...",
      "title": "Apple Reports Q1 2026 Earnings",
      "published_at": "2026-01-27T23:33:53Z",
      "source": "yfinance_ticker",
      "summary": "Apple announced...",
      "content_type": "article",
      "provider": {
        "name": "Yahoo Finance",
        "url": "http://finance.yahoo.com/"
      },
      "thumbnail": {
        "url": "https://s.yimg.com/...",
        "width": 5971,
        "height": 3980
      },
      "related_tickers": ["AAPL"],
      "tags": [],
      "fetched_at": "2026-01-28T12:00:00Z",
      "metadata": {
        "yfinance_content_type": "STORY",
        "editors_pick": true,
        "is_premium": false
      },
      "summary_ja": null,
      "category": null,
      "sentiment": null
    }
  ]
}
```

**Search ベース（キーワード検索）**:
```json
{
  "meta": {
    "source": "yfinance_search",
    "query": "Federal Reserve interest rate",
    "fetched_at": "2026-01-28T12:00:00Z",
    "article_count": 10,
    "version": "1.0"
  },
  "articles": [
    {
      "url": "https://finance.yahoo.com/news/...",
      "title": "Fed Signals Rate Cut in 2026",
      "published_at": "2026-01-27T20:15:00Z",
      "source": "yfinance_search",
      "summary": "The Federal Reserve indicated...",
      "content_type": "article",
      "provider": {
        "name": "Reuters",
        "url": "https://www.reuters.com/"
      },
      "thumbnail": {
        "url": "https://s.yimg.com/...",
        "width": 1200,
        "height": 800
      },
      "related_tickers": [],
      "tags": ["Federal Reserve interest rate"],
      "fetched_at": "2026-01-28T12:00:00Z",
      "metadata": {
        "yfinance_content_type": "STORY",
        "search_query": "Federal Reserve interest rate"
      },
      "summary_ja": null,
      "category": null,
      "sentiment": null
    }
  ]
}
```

---

### Phase 1: 基盤構築

- [ ] データソース抽象化（SourceProtocol）
- [ ] 出力先抽象化（SinkProtocol）
- [ ] 設定管理（SourceConfig, SinkConfig, ProcessorConfig）
- [ ] 基本的なニュース記事モデル（Article）
- [ ] メインコレクター基盤（Collector）

### Phase 2: yfinance ニュースソース実装

- [ ] yfinance ニュース取得基盤
  - [ ] 共通基盤（base.py）- Ticker/Search両対応
  - [ ] **Ticker ベース**（特定銘柄・指数に関連するニュース）
    - [ ] 株価指数ニュース（index.py）- ^GSPC, ^DJI 等のティッカー指定
    - [ ] セクター別ニュース（sector.py）- XLF, XLK 等のセクターETF指定
    - [ ] 個別銘柄ニュース（stock.py）- AAPL, GOOGL 等のティッカー指定
    - [ ] コモディティニュース（commodity.py）- GC=F, CL=F 等のティッカー指定
  - [ ] **Search ベース**（キーワード検索によるニュース）
    - [ ] マクロ経済ニュース（macro.py）- "Federal Reserve", "inflation" 等のキーワード検索
    - [ ] テーマ別ニュース（search.py）- 任意キーワードでの汎用検索
- [ ] ソース設定ファイル（YAML/JSON）
  - [ ] Ticker用設定（ティッカーリスト）
  - [ ] Search用設定（キーワードリスト）

### Phase 3: Web スクレイピングソース実装（将来拡張）

- [ ] 汎用スクレイパー基盤（Playwright/BeautifulSoup/lxml）
- [ ] サイト別パーサー設定（CSS セレクタ、XPath）
- [ ] ページネーション対応
- [ ] レート制限・礼儀正しいクローリング

### Phase 4: 出力先実装

- [ ] ファイル出力（JSON必須, ParquetやMarkdownはオプションとして）
  - [ ] 出力フォーマット作成
- [ ] GitHub Issue/Project 出力
- [ ] 週次レポート用データ出力（`aggregated_data.json` 形式）

### Phase 5: 運用機能

- [ ] 重複チェック機構
- [ ] 取得履歴管理
- [ ] エラーハンドリング・リトライ

### Phase 6: AIエージェント連携（Claude Agent SDK）

- [ ] ProcessorProtocol（AI処理の抽象化）
- [ ] Claude Agent SDK 統合
  - [ ] エージェント呼び出し基盤
  - [ ] 記事データのJSON受け渡し
- [ ] 要約生成プロセッサ
  - [ ] 要約エージェント呼び出し
  - [ ] 日本語要約の生成・保存
- [ ] 分類・タグ付けプロセッサ
  - [ ] 分類エージェント呼び出し
  - [ ] カテゴリ自動分類（金融、テクノロジー等）
  - [ ] キーワード・エンティティ抽出
- [ ] パイプライン実行
  - [ ] 収集 → 処理 → 出力の一連のフロー
  - [ ] バッチ処理・並列実行対応
- [ ] 自動実行ワークフロー
  - [ ] cron/スケジューラ連携
  - [ ] 定期実行スクリプト

## アーキテクチャ

```
news/
├── core/
│   ├── article.py      # Article モデル（共通データ構造）
│   ├── source.py       # SourceProtocol（データソース抽象化）
│   ├── sink.py         # SinkProtocol（出力先抽象化）
│   └── processor.py    # ProcessorProtocol（AI処理抽象化）
├── sources/
│   ├── yfinance/       # python yfinanceライブラリを使った実装
│   │   ├── __init__.py
│   │   ├── base.py     # yfinance共通基盤（Ticker/Search両対応）
│   │   │
│   │   │  # === Ticker ベース（特定銘柄・指数に関連するニュース） ===
│   │   ├── index.py    # 株価指数ニュース（^GSPC, ^DJI等のティッカー指定）
│   │   ├── sector.py   # セクターETFニュース（XLF, XLK等のティッカー指定）
│   │   ├── stock.py    # 個別銘柄ニュース（AAPL, GOOGL等のティッカー指定）
│   │   ├── commodity.py # コモディティニュース（GC=F, CL=F等のティッカー指定）
│   │   │
│   │   │  # === Search ベース（キーワード検索によるニュース） ===
│   │   ├── macro.py    # マクロ経済ニュース（"Federal Reserve"等のキーワード検索）
│   │   └── search.py   # テーマ別ニュース（任意キーワードでの汎用検索）
│   │
│   └── scraper/        # スクレイピングソース実装（将来拡張）
│       ├── base.py     # 汎用スクレイパー基盤
│       ├── parser.py   # サイト別パーサー設定
│       └── sites/      # サイト固有の実装
├── processors/         # AI処理実装（Claude Agent SDK経由）
│   ├── summarizer.py   # 要約生成エージェント呼び出し
│   ├── classifier.py   # 分類・タグ付けエージェント呼び出し
│   └── pipeline.py     # 収集→処理→出力のパイプライン管理
├── sinks/
│   ├── file.py         # ファイル出力（JSON, Parquet）
│   ├── github.py       # GitHub Issue/Project 出力
│   └── report.py       # 週次レポート用出力（aggregated_data.json 形式）
├── config/
│   └── loader.py       # 設定ファイル読み込み（data/config/ から読込）
└── collector.py        # メインコレクター（オーケストレーション）
```

**設定ファイル配置**:
- 設定ファイル: `data/config/news_sources.yaml`
- 設定読み込み: `news/config/loader.py` が `data/config/` を参照

## 技術的考慮事項

### GitHub API レート制限対策

GitHub CLI (`gh`) を使用する際のレート制限対策。3つのレベルから選択。

#### レート制限の概要

| API種別 | 制限 | 消費ポイント |
|--------|------|-------------|
| REST API | 5,000 リクエスト/時間 | 1 リクエスト = 1 ポイント |
| GraphQL API | 5,000 ポイント/時間 | クエリの複雑さで変動（1-100+ポイント） |

**現状の問題点**:
- `gh issue view`, `gh project item-list` などはGraphQL APIを使用
- Issue 1件あたり複数のAPIコール（view, item-add, item-edit）
- 100件のIssue処理で500+ポイント消費の可能性

---

#### レベル1: 簡易対策（スリープ追加）

**実装工数**: 低（1-2時間）

**内容**:
```python
import time

for issue_number in issues:
    process_issue(issue_number)
    time.sleep(1.0)  # 1秒待機
```

**メリット**:
- 実装が非常に簡単
- 既存コードへの影響最小
- すぐに導入可能

**デメリット**:
- 処理時間が大幅に増加（100件で100秒追加）
- レート制限に達すると対処できない
- 非効率（レート制限に余裕があっても遅い）

**推奨ケース**:
- 少量のIssue処理（10件以下/回）
- 開発・テスト環境
- 緊急の暫定対応

---

#### レベル2: 中級対策（バッチ+リトライ）

**実装工数**: 中（4-8時間）

**内容**:
1. **一括取得**: 個別APIコールを減らす
2. **指数バックオフ**: レート制限時に適応的に待機
3. **レート制限監視**: 残りポイントを確認して調整

```python
import subprocess
import json
import time

def get_rate_limit() -> dict:
    """現在のレート制限状況を取得"""
    result = subprocess.run(
        ["gh", "api", "rate_limit"],
        capture_output=True, text=True, check=True
    )
    return json.loads(result.stdout)

def execute_with_backoff(func, max_retries=3):
    """指数バックオフでリトライ"""
    for attempt in range(max_retries):
        try:
            return func()
        except subprocess.CalledProcessError as e:
            if "rate limit" in str(e.stderr).lower():
                wait_time = 2 ** attempt * 30  # 30s, 60s, 120s
                time.sleep(wait_time)
            else:
                raise
    raise Exception("Max retries exceeded")

# 一括取得の例
def get_issues_batch(limit=100):
    """一括でIssue情報を取得（個別取得を避ける）"""
    result = subprocess.run(
        ["gh", "issue", "list", "--repo", "owner/repo",
         "--limit", str(limit), "--json", "number,title,body,projectItems"],
        capture_output=True, text=True, check=True
    )
    return json.loads(result.stdout)
```

**メリット**:
- APIコール数を大幅に削減（10分の1程度）
- レート制限に達しても自動復旧
- 処理速度と安定性のバランスが良い

**デメリット**:
- 実装がやや複雑
- レート制限リセットまで待機が必要な場合がある
- キャッシュがないため再実行時に再取得

**推奨ケース**:
- 中規模のIssue処理（10-100件/回）
- 定期実行ワークフロー
- 本番環境での日次処理

---

#### レベル3: 本格対策（キャッシュ+最適化）

**実装工数**: 高（1-2日）

**内容**:
1. **ローカルキャッシュ**: 取得済みデータを永続化
2. **差分取得**: 前回からの差分のみ取得
3. **バッチリクエスト**: GraphQL mutationをまとめる
4. **TTL管理**: キャッシュの有効期限管理

```python
import json
from pathlib import Path
from datetime import datetime, timedelta

class GitHubCache:
    """GitHub API結果のローカルキャッシュ"""

    def __init__(self, cache_dir: Path = Path("data/cache/github")):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def get_existing_issues(self, max_age_hours: int = 24) -> dict[int, dict]:
        """キャッシュからIssue情報を取得"""
        cache_file = self.cache_dir / "issues.json"
        if not cache_file.exists():
            return {}

        data = json.loads(cache_file.read_text())
        cached_at = datetime.fromisoformat(data["cached_at"])

        # キャッシュの有効期限チェック
        if datetime.now() - cached_at > timedelta(hours=max_age_hours):
            return {}

        return {issue["number"]: issue for issue in data["issues"]}

    def update_cache(self, issues: list[dict]) -> None:
        """Issue情報をキャッシュに保存"""
        cache_file = self.cache_dir / "issues.json"
        data = {
            "cached_at": datetime.now().isoformat(),
            "issues": issues
        }
        cache_file.write_text(json.dumps(data, ensure_ascii=False, indent=2))

    def get_project_items(self, project_number: int) -> dict[str, dict]:
        """Project item情報をキャッシュから取得"""
        cache_file = self.cache_dir / f"project_{project_number}_items.json"
        if not cache_file.exists():
            return {}

        data = json.loads(cache_file.read_text())
        return {item["id"]: item for item in data.get("items", [])}

class OptimizedPublisher:
    """最適化されたGitHub Publisher"""

    def __init__(self, cache: GitHubCache):
        self.cache = cache
        self._project_items_cache: dict[str, str] = {}

    def publish_batch(self, articles: list, dry_run: bool = False):
        # 1. キャッシュから既存Issue情報を取得
        existing_issues = self.cache.get_existing_issues()

        # 2. キャッシュにないものだけAPIで取得
        missing_numbers = [a.issue_number for a in articles
                          if a.issue_number not in existing_issues]
        if missing_numbers:
            new_issues = self._fetch_issues(missing_numbers)
            existing_issues.update(new_issues)
            self.cache.update_cache(list(existing_issues.values()))

        # 3. Project item情報もキャッシュ優先
        project_items = self.cache.get_project_items(15)

        # 4. 処理実行
        for article in articles:
            # キャッシュされたitem_idを使用
            issue_url = f"https://github.com/owner/repo/issues/{article.issue_number}"
            if issue_url in project_items:
                item_id = project_items[issue_url]["id"]
            else:
                # 新規追加が必要な場合のみAPIコール
                item_id = self._add_to_project(issue_url)

            self._set_status(item_id, article.status)
```

**メリット**:
- APIコール数を最小化（キャッシュヒット時は0）
- 再実行時に高速（差分のみ処理）
- 大量処理でも安定
- レート制限に達するリスクが極めて低い

**デメリット**:
- 実装が複雑
- キャッシュの整合性管理が必要
- ディスク容量を消費
- キャッシュ無効化のロジックが必要

**推奨ケース**:
- 大規模のIssue処理（100件以上/回）
- 頻繁な再実行が必要な場合
- 本番環境での信頼性重視

---

#### 対策レベル比較表

| 項目 | レベル1 (簡易) | レベル2 (中級) | レベル3 (本格) |
|------|---------------|---------------|---------------|
| 実装工数 | 1-2時間 | 4-8時間 | 1-2日 |
| APIコール削減 | なし | 50-90% | 90-99% |
| レート制限回避 | 低 | 中 | 高 |
| 処理速度 | 遅い | 中 | 速い |
| 再実行耐性 | なし | 低 | 高 |
| 保守コスト | 低 | 中 | 高 |
| 推奨Issue数/回 | 〜10件 | 10-100件 | 100件以上 |

---

#### 現在の実装状況

| 対策 | 状態 | 備考 |
|------|------|------|
| APIコール間のスリープ | ❌ 未実装 | レベル1対策 |
| 指数バックオフリトライ | ✅ 実装済み | TrafilaturaExtractorで使用 |
| 一括取得 | ⚠️ 部分的 | `gh issue list` は使用、`gh project item-list` は未最適化 |
| レート制限監視 | ❌ 未実装 | レベル2対策 |
| ローカルキャッシュ | ❌ 未実装 | レベル3対策 |
| 差分取得 | ❌ 未実装 | レベル3対策 |

---

### 依存関係

| パッケージ | 用途 | Phase |
|-----------|------|-------|
| `pydantic` | 設定・モデル定義 | Phase 1 |
| `yfinance` | 株式・指数ニュース取得 | Phase 2 |
| `httpx` | HTTP クライアント（スクレイピング用） | Phase 3 |
| `beautifulsoup4` | Web スクレイピング | Phase 3 |
| `playwright` | 動的サイトスクレイピング | Phase 3 |
| `lxml` | 高速 HTML/XML パーサー | Phase 3 |
| `claude-code-sdk` | Claude Agent SDK（エージェント呼び出し） | Phase 6 |

### 既存パッケージとの関係

| パッケージ | 関係 |
|-----------|------|
| `rss` | **独立** - RSS フィードは rss パッケージが担当 |
| `analyze` | **連携可能** - 収集後の分析処理を委譲 |
| `utils` | **利用** - ロギング、ユーティリティを利用 |

## 成功基準

1. **拡張性**: 新しいデータソースを 1 ファイル追加で対応可能
2. **設定駆動**: コード変更なしで取得対象・出力先を変更可能
3. **信頼性**: 重複なし、エラー時のリトライ、取得履歴管理
4. **テスト**: 各コンポーネントのカバレッジ 80% 以上

## 要検討事項

### 高優先度（設計前に決定必須）

| 項目 | 問題点 | 対応案 | 状態 |
|------|--------|--------|------|
| yfinance API仕様の事前調査 | ニュース取得の制限、レート制限、取得可能なデータ形式が不明 | Phase 0として調査フェーズを追加 | ✅ 完了 |
| yfinance Search クラス調査 | Tickerクラス以外のニュース取得手段が不明 | Phase 0で追加調査 | ✅ 完了（キーワード検索対応確認） |
| JSON出力フォーマット定義 | 「フォーマット作成が必要」とあるが具体的スキーマが未定義 | Phase 1でArticleモデルと共に定義 | 未着手 |
| market パッケージとの関係 | 既存の `src/market/` にもyfinance関連実装がある | 重複回避・連携方針を明記 | ✅ 完了（重複なし確認済み） |
| 具体的なティッカー/キーワード定義 | Ticker用（index, sector, stock, commodity）とSearch用（macro等）で何を取得するか未定義 | 設定ファイルで定義、デフォルト値も用意 | 未着手 |

### 中優先度（Phase 1-2 開始前に決定）

| 項目 | 問題点 | 対応案 | 状態 |
|------|--------|--------|------|
| 重複チェックの具体的方法 | URLハッシュ？タイトル類似度？yfinanceニュースのユニークキーは何か | Phase 0調査で特定 | ✅ 完了（`id`フィールド使用） |
| 設定ファイルスキーマ | `news_sources.yaml` の具体的な形式が未定義 | Phase 1で定義 | 未着手 |
| テストのモック方針 | yfinance APIをどうモックするか | vcr.py または responses を検討 | 未着手 |
| GitHub投稿先Project番号 | どのProjectに投稿するか | 設定ファイルで指定可能に | 未着手 |

### 低優先度（実装時に決定可能）

| 項目 | 問題点 | 対応案 |
|------|--------|--------|
| リトライ戦略の詳細 | 回数、バックオフ間隔が未定義 | Phase 5で実装時に決定 |
| Phase間の並列可能性 | Phase 4と5は並列可能では？ | 依存関係を整理して判断 |

## 非スコープ

- センチメント分析（→ analyze パッケージ）
- RSS フィード対応（→ rss パッケージ）
- リアルタイム配信（バッチ処理のみ）

---

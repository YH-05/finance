# 開発ガイドライン (Development Guidelines)

rssライブラリの開発における実装規約・開発プロセス・品質基準を定義します。

## 技術スタック

### 言語・ランタイム

| 技術 | バージョン | 用途 |
|------|-----------|------|
| Python | 3.12+ | PEP 695型ヒント対応、パターンマッチング、改善されたエラーメッセージ |
| uv | latest | Rustベースの高速パッケージマネージャー |

### 主要ライブラリ

| ライブラリ | バージョン | 用途 |
|-----------|-----------|------|
| httpx | 0.27.0+ | 非同期HTTP/HTTPSクライアント、リトライ制御 |
| feedparser | 6.0.0+ | RSS 2.0/Atomパーサー |
| filelock | 3.20.0+ | クロスプラットフォーム対応ファイルロック |
| structlog | 25.4.0+ | 構造化ロギング（financeパッケージから継承） |
| click | 8.1.0+ | CLIフレームワーク（P1機能） |
| mcp | 0.9.0+ | MCPプロトコル実装（P1機能） |
| APScheduler | 3.10.0+ | スケジューラー（P1機能） |

### 開発ツール

| ツール | 用途 |
|--------|------|
| Ruff | リント・フォーマット（Rustベース、高速） |
| pyright | 型チェック（厳密な型チェック） |
| pytest | テストフレームワーク |
| Hypothesis | プロパティベーステスト（不正入力検証） |
| pytest-cov | カバレッジ測定（目標80%） |
| pytest-benchmark | ベンチマーク測定 |
| memory_profiler | メモリプロファイリング |

## コーディング規約

### 型ヒント（PEP 695準拠）

**Python 3.12+の新構文を使用**:

```python
# ✅ 良い例: 組み込み型を直接使用
def fetch_feeds(category: str | None = None) -> list[Feed]:
    """指定カテゴリのフィードを取得する。"""
    ...

# ✅ 良い例: PEP 695のジェネリック構文
def first[T](items: list[T]) -> T | None:
    """リストの最初の要素を返す。"""
    return items[0] if items else None

# ❌ 悪い例: 従来のtyping.List/Dict/Optional
from typing import List, Optional
def fetch_feeds(category: Optional[str] = None) -> List[Feed]: ...
```

**型エイリアス（PEP 695）**:

```python
# rss/types.py
from typing import Literal

# ✅ 良い例: type文による型エイリアス
type FeedID = str
type TaskStatus = Literal["todo", "in_progress", "completed"]
type Nullable[T] = T | None

# ❌ 悪い例: TypeAliasを使用
from typing import TypeAlias
FeedID: TypeAlias = str
```

### 命名規則

#### ディレクトリ・ファイル

```
# ディレクトリ: snake_case、複数形（レイヤー）または単数形（機能）
src/rss/
├── core/                   # データ処理層（単数形）
├── services/               # サービス層（複数形）
├── storage/                # データ永続化層（単数形）
└── validators/             # 入力検証層（複数形）

# ファイル: snake_case、サフィックス推奨
http_client.py              # OK
feed_manager.py             # OK
json_storage.py             # OK
url_validator.py            # OK
```

#### クラス・関数・変数

```python
# クラス: PascalCase、サフィックス必須
class FeedManager: ...           # サービス層: Manager/Fetcher/Reader
class HTTPClient: ...            # データ処理層: Client/Parser/Detector
class JSONStorage: ...           # データ永続化層: Storage/Manager
class URLValidator: ...          # 入力検証層: Validator

# 関数: snake_case、動詞で始める
def add_feed(url: str, title: str) -> str: ...
def fetch_feed(feed_id: str) -> FetchResult: ...
def search_items(query: str) -> list[FeedItem]: ...

# 変数: snake_case、名詞
feed_id = "550e8400-e29b-41d4-a716-446655440000"
fetch_interval = FetchInterval.DAILY
is_enabled = True

# Boolean変数: is_/has_/should_/can_で始める
is_valid = True
has_error = False
should_retry = True
can_fetch = False

# 定数: UPPER_SNAKE_CASE
MAX_RETRY_COUNT = 3
DEFAULT_TIMEOUT = 10
FEEDS_FILE_NAME = "feeds.json"
```

### データモデル定義

**dataclassを使用**:

```python
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

# Enum: PascalCase、単数形
class FetchInterval(str, Enum):
    """フィード取得間隔"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MANUAL = "manual"

class FetchStatus(str, Enum):
    """フィード取得ステータス"""
    SUCCESS = "success"
    FAILURE = "failure"
    PENDING = "pending"

# dataclass: PascalCase、単数形
@dataclass
class Feed:
    """フィード情報モデル"""
    feed_id: str                    # UUID v4形式
    url: str                        # HTTP/HTTPSスキーマのみ
    title: str                      # 1-200文字
    category: str                   # 1-50文字
    fetch_interval: FetchInterval
    created_at: datetime
    updated_at: datetime
    last_fetched: datetime | None
    last_status: FetchStatus
    enabled: bool
```

### コメント規約

**Docstring（NumPy形式）**:

```python
def fetch_feed(
    feed_id: str,
    timeout: int = 10,
    max_retries: int = 3,
) -> FetchResult:
    """フィードを取得し、差分を検出して保存する。

    Parameters
    ----------
    feed_id : str
        取得するフィードのID（UUID v4形式）
    timeout : int, default=10
        HTTP取得のタイムアウト（秒）
    max_retries : int, default=3
        リトライ最大回数

    Returns
    -------
    FetchResult
        取得結果（成功/失敗、新規アイテム数等）

    Raises
    ------
    FeedNotFoundError
        指定されたフィードIDが存在しない場合
    FeedFetchError
        フィード取得に失敗した場合（max_retries回リトライ後）
    FeedParseError
        フィードのパースに失敗した場合

    Examples
    --------
    >>> result = fetcher.fetch_feed("550e8400-e29b-41d4-a716-446655440000")
    >>> print(result.success)
    True
    >>> print(result.new_items)
    5
    """
    ...
```

**インラインコメント**:

```python
# ✅ 良い例: なぜそうするかを説明
# キャッシュを無効化して、最新のフィードデータを取得
cache.clear()

# feedparserは不正なXMLでもパースを試みるため、追加でバリデーション実施
if not parsed.get("feed"):
    raise FeedParseError(f"フィードの構造が不正です: {url}")

# ❌ 悪い例: 何をしているか（コードを見れば分かる）
# キャッシュをクリアする
cache.clear()
```

### エラーハンドリング

**カスタム例外クラス（exceptions.py）**:

```python
class RSSError(Exception):
    """RSSパッケージの基底例外"""
    pass

class FeedNotFoundError(RSSError):
    """フィードが見つからない"""
    pass

class FeedAlreadyExistsError(RSSError):
    """フィードが既に存在する"""
    pass

class FeedFetchError(RSSError):
    """フィード取得に失敗"""
    pass

class FeedParseError(RSSError):
    """フィードのパースに失敗"""
    pass

class InvalidURLError(RSSError):
    """無効なURL形式"""
    pass

class FileLockError(RSSError):
    """ファイルロック取得に失敗"""
    pass
```

**エラーハンドリングパターン**:

```python
from rss.exceptions import FeedNotFoundError, FeedFetchError
from finance.utils.logging_config import get_logger

logger = get_logger(__name__)

# ✅ 良い例: 適切なエラーハンドリング
async def fetch_feed(feed_id: str) -> FetchResult:
    """フィードを取得する。"""
    try:
        # フィード情報取得
        feed = self.manager.get_feed(feed_id)
        if feed is None:
            raise FeedNotFoundError(f"フィードが見つかりません (ID: {feed_id})")

        # HTTP取得（リトライ機構内蔵）
        response = await self.http_client.fetch(
            feed.url,
            timeout=10,
            max_retries=3,
        )

        # パース
        parsed = self.parser.parse(response.content)

        logger.info("フィード取得成功", feed_id=feed_id, url=feed.url, items_count=len(parsed))
        return FetchResult(success=True, new_items=len(parsed))

    except FeedNotFoundError:
        logger.error("フィード取得失敗: フィードが見つかりません", feed_id=feed_id)
        raise
    except FeedFetchError as e:
        logger.error("フィード取得失敗: HTTPエラー", feed_id=feed_id, error=str(e), exc_info=True)
        raise
    except FeedParseError as e:
        logger.error("フィード取得失敗: パースエラー", feed_id=feed_id, error=str(e), exc_info=True)
        raise
    except Exception as e:
        logger.error("フィード取得失敗: 予期しないエラー", feed_id=feed_id, error=str(e), exc_info=True)
        raise FeedFetchError(f"フィード取得に失敗しました: {e}") from e

# ❌ 悪い例: エラーを無視
async def fetch_feed(feed_id: str) -> FetchResult | None:
    try:
        return await self._fetch_feed_internal(feed_id)
    except Exception:
        return None  # エラー情報が失われる
```

**エラーメッセージの書き方**:

```python
# ✅ 良い例: 具体的で解決策を示す
raise InvalidURLError(f"HTTP/HTTPSスキーマのみ許可されます: {url}")
raise ValidationError(
    f"タイトルは1-200文字で入力してください。現在の文字数: {len(title)}",
    field="title",
    value=title,
)

# ❌ 悪い例: 曖昧で役に立たない
raise ValueError("Invalid input")
raise Exception("Error occurred")
```

### ロギング

**構造化ロギング（structlog使用）**:

```python
from finance.utils.logging_config import get_logger

logger = get_logger(__name__)

# ✅ 良い例: 構造化ログ
logger.info(
    "フィード取得成功",
    feed_id=feed_id,
    url=url,
    items_count=10,
    new_items=5,
    duration_ms=1234,
)

logger.warning(
    "リトライ実行中",
    feed_id=feed_id,
    url=url,
    attempt=2,
    max_retries=3,
    error=str(e),
)

logger.error(
    "フィード取得失敗",
    feed_id=feed_id,
    url=url,
    error=str(e),
    exc_info=True,  # スタックトレースを記録
)

# ❌ 悪い例: 文字列補間のみ
logger.info(f"Feed fetched: {feed_id}")
logger.error(f"Error: {e}")
```

**ログレベル**:

| レベル | 用途 | 例 |
|--------|------|-----|
| DEBUG | HTTP取得開始、パース開始、内部処理の詳細 | "Fetching feed started", "Parsing feed content" |
| INFO | フィード取得成功、アイテム保存完了、バッチ実行開始/終了 | "Feed fetched successfully", "Batch execution started" |
| WARNING | リトライ実行、URL重複検出、設定不備 | "Retrying feed fetch", "Duplicate URL detected" |
| ERROR | 取得失敗、パースエラー、ファイルロックエラー | "Failed to fetch feed", "Parse error occurred" |

### 非同期処理

**async/awaitの使用**:

```python
import asyncio
import httpx

# ✅ 良い例: 並列フィード取得
class FeedFetcher:
    async def fetch_all_async(
        self,
        category: str | None = None,
        max_concurrent: int = 5,
    ) -> list[FetchResult]:
        """複数フィードを並列取得する。

        Parameters
        ----------
        category : str | None, optional
            カテゴリフィルタ（Noneの場合は全カテゴリ）
        max_concurrent : int, default=5
            同時実行数の上限（デフォルト5、最大10）

        Returns
        -------
        list[FetchResult]
            取得結果のリスト
        """
        feeds = self.manager.list_feeds(category=category, enabled_only=True)
        semaphore = asyncio.Semaphore(max_concurrent)

        async def fetch_with_semaphore(feed_id: str) -> FetchResult:
            async with semaphore:
                return await self._fetch_feed_async(feed_id)

        tasks = [fetch_with_semaphore(feed.feed_id) for feed in feeds]
        return await asyncio.gather(*tasks, return_exceptions=False)

# ❌ 悪い例: 逐次実行
async def fetch_all(self, feeds: list[Feed]) -> list[FetchResult]:
    results = []
    for feed in feeds:
        result = await self._fetch_feed_async(feed.feed_id)  # 遅い
        results.append(result)
    return results
```

## アーキテクチャ規約

### レイヤードアーキテクチャの遵守

```
UIレイヤー (cli/, mcp/)
    ↓ (OK)
サービスレイヤー (services/)
    ↓ (OK)
データ処理レイヤー (core/)
データ永続化レイヤー (storage/)
入力検証レイヤー (validators/)
    ↓ (OK)
共通モジュール (types.py, exceptions.py)
```

**依存関係のルール**:

```python
# ✅ 良い例: 上位レイヤーから下位レイヤーへの依存
# services/feed_manager.py
from rss.storage.json_storage import JSONStorage
from rss.validators.url_validator import URLValidator
from rss.types import Feed, FeedsData
from rss.exceptions import FeedAlreadyExistsError

class FeedManager:
    def __init__(self, storage: JSONStorage, validator: URLValidator) -> None:
        self.storage = storage
        self.validator = validator

# ❌ 悪い例: 下位レイヤーから上位レイヤーへの依存
# storage/json_storage.py
from rss.services.feed_manager import FeedManager  # 禁止！

class JSONStorage:
    def __init__(self, manager: FeedManager) -> None:  # 禁止！
        self.manager = manager
```

**循環依存の防止（Protocol使用）**:

```python
# ✅ 良い例: Protocolで型定義を抽出
# types.py
from typing import Protocol

class FeedManagerProtocol(Protocol):
    """FeedManagerのインターフェース"""
    def get_feed(self, feed_id: str) -> Feed | None: ...
    def list_feeds(self, category: str | None = None) -> list[Feed]: ...

# services/feed_fetcher.py
from rss.types import FeedManagerProtocol

class FeedFetcher:
    def __init__(self, manager: FeedManagerProtocol) -> None:
        self.manager = manager  # インターフェースに依存
```

### ファイル配置規則

| ファイル種別 | 配置先 | 命名規則 | 例 |
|------------|--------|---------|-----|
| HTTP通信 | core/ | snake_case | http_client.py |
| パーサー | core/ | snake_case | parser.py |
| 差分検出 | core/ | snake_case | diff_detector.py |
| サービス | services/ | snake_case + サフィックス | feed_manager.py, feed_fetcher.py |
| ストレージ | storage/ | snake_case + サフィックス | json_storage.py, lock_manager.py |
| バリデーター | validators/ | snake_case + サフィックス | url_validator.py |
| CLIコマンド | cli/ | snake_case | main.py |
| MCPサーバー | mcp/ | snake_case | server.py |
| 型定義 | パッケージルート | types.py | types.py |
| 例外クラス | パッケージルート | exceptions.py | exceptions.py |

## Git運用ルール

### ブランチ戦略（Git Flow）

```
main (本番環境)
└── develop (開発・統合環境)
    ├── feature/rss-feed-fetcher      # 新機能開発
    ├── fix/feed-parse-error          # バグ修正
    ├── refactor/storage-layer        # リファクタリング
    ├── docs/api-documentation        # ドキュメント
    └── test/feed-workflow            # テスト追加
```

**運用ルール**:

- **main**: 本番リリース済みの安定版コードのみ。タグでバージョン管理
- **develop**: 次期リリースに向けた最新の開発コードを統合。CIで自動テスト実施
- **feature/fix/refactor/docs/test**: developから分岐し、作業完了後にPRでdevelopへマージ
- **直接コミット禁止**: すべてのブランチでPRレビューを必須とし、コード品質を担保
- **マージ方針**: feature→developはsquash merge、develop→mainはmerge commit

### コミットメッセージ規約

**フォーマット（Conventional Commits）**:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Type一覧**:

```
feat: 新機能
fix: バグ修正
docs: ドキュメント
style: フォーマット
refactor: リファクタリング
test: テスト追加・修正
chore: その他（依存関係更新等）
```

**例**:

```
feat(fetcher): 並列フィード取得機能を追加

複数フィードを効率的に取得するため、並列取得機能を実装しました。

実装内容:
- asyncio.gatherによる並列実行
- セマフォによる同時実行数制御（デフォルト5、最大10）
- タイムアウト・リトライ機構の統合

パフォーマンス:
- 5フィードの取得時間: 25秒 → 7秒（71%改善）

Closes #42
```

### プルリクエストプロセス

**作成前のチェック**:

- [ ] 全てのテストがパス（make test）
- [ ] Lintエラーがない（make lint）
- [ ] 型チェックがパス（make typecheck）
- [ ] 競合が解決されている

**PRテンプレート**:

```markdown
## 変更の種類

- [ ] 新機能 (feat)
- [ ] バグ修正 (fix)
- [ ] リファクタリング (refactor)
- [ ] ドキュメント (docs)
- [ ] その他 (chore)

## 変更内容

### 何を変更したか

[簡潔な説明]

### なぜ変更したか

[背景・理由]

### どのように変更したか

- [変更点1]
- [変更点2]

## テスト

### 実施したテスト

- [ ] ユニットテスト追加（カバレッジ80%以上）
- [ ] 統合テスト追加（フルフロー確認）
- [ ] 手動テスト実施

### テスト結果

[テスト結果の説明]

## 関連Issue

Closes #[番号]

## レビューポイント

[レビュアーに特に見てほしい点]
```

## テスト戦略

### テストの種類とカバレッジ目標

| テスト種別 | 対象 | カバレッジ目標 |
|----------|------|--------------|
| ユニットテスト | 個別の関数・クラス | 80%以上 |
| 統合テスト | 複数コンポーネントの連携 | 主要フロー100% |
| プロパティテスト | 不正入力への対処 | 重要な検証ロジック |
| E2Eテスト | ユーザーシナリオ全体 | 主要シナリオ100% |

### ユニットテスト

**対象**:

- URLValidator: URL形式検証、文字列長検証
- DiffDetector: 差分検出ロジック
- FeedParser: RSS 2.0/Atomパース処理
- LockManager: ファイルロック取得・解放
- JSONStorage: JSON読み書き

**テストケース例**:

```python
import pytest
from rss.validators.url_validator import URLValidator
from rss.exceptions import InvalidURLError

class TestURLValidator:
    class TestValidateURL:
        def test_HTTPS_URLは検証を通過する(self):
            """HTTPS URLは検証を通過する"""
            validator = URLValidator()
            assert validator.validate_url("https://example.com/feed.xml") is True

        def test_HTTP_URLは検証を通過する(self):
            """HTTP URLは検証を通過する"""
            validator = URLValidator()
            assert validator.validate_url("http://example.com/feed.xml") is True

        def test_HTTP_HTTPS以外はInvalidURLErrorを発生させる(self):
            """HTTP/HTTPS以外はInvalidURLErrorを発生させる"""
            validator = URLValidator()
            with pytest.raises(InvalidURLError):
                validator.validate_url("ftp://example.com/feed.xml")

        def test_空文字列はInvalidURLErrorを発生させる(self):
            """空文字列はInvalidURLErrorを発生させる"""
            validator = URLValidator()
            with pytest.raises(InvalidURLError):
                validator.validate_url("")
```

### 統合テスト

**対象**:

- フィード登録 → 取得 → アイテム保存 → 検索のフルフロー
- 並列フィード取得
- ファイルロック競合のシミュレーション

**テストケース例**:

```python
import pytest
from pathlib import Path
from rss.services.feed_manager import FeedManager
from rss.services.feed_fetcher import FeedFetcher
from rss.services.feed_reader import FeedReader

class TestFeedWorkflow:
    def test_フィード登録から検索までのフルフローが動作する(self, tmp_path: Path, mock_rss_server):
        """フィード登録 → 取得 → 検索のフルフローが動作する"""
        # Given: モックHTTPサーバーでRSSフィードを提供
        server_url = mock_rss_server.url_for("/feed.xml")

        manager = FeedManager(data_dir=tmp_path)
        fetcher = FeedFetcher(manager)
        reader = FeedReader(data_dir=tmp_path)

        # When: フィード登録
        feed_id = manager.add_feed(
            url=server_url,
            title="Test Feed",
            category="finance",
        )

        # When: フィード取得
        result = fetcher.fetch_feed(feed_id)

        # When: アイテム検索
        items = reader.search_items(query="金利", category="finance")

        # Then: 検証
        assert result.success is True
        assert result.new_items == 10
        assert len(items) > 0
```

### プロパティベーステスト（Hypothesis）

**対象**:

- FeedParser: 不正なXML/HTMLへの対処
- DiffDetector: 任意のアイテムリストで差分検出が正常動作

**テストケース例**:

```python
from hypothesis import given, strategies as st
from rss.validators.url_validator import URLValidator

class TestURLValidatorProperty:
    @given(st.text(min_size=1, max_size=200))
    def test_任意の1_200文字文字列は検証を通過する(self, title: str):
        """任意の1-200文字文字列は検証を通過する"""
        validator = URLValidator()
        assert validator.validate_title(title) is True

    @given(st.text(min_size=201))
    def test_201文字以上の文字列はValueErrorを発生させる(self, title: str):
        """201文字以上の文字列はValueErrorを発生させる"""
        validator = URLValidator()
        with pytest.raises(ValueError):
            validator.validate_title(title)
```

### テスト命名規則

**パターン**: `test_[対象]_[条件]_[期待結果]` または日本語

```python
# ✅ 良い例（日本語）
def test_正常なデータでタスクを作成できる(): ...
def test_タイトルが空の場合ValidationErrorを送出する(): ...
def test_存在しないIDの場合Noneを返す(): ...

# ✅ 良い例（英語）
def test_create_with_valid_data_returns_task(): ...
def test_create_with_empty_title_raises_validation_error(): ...

# ❌ 悪い例
def test1(): ...
def test_works(): ...
```

## コードレビュー基準

### レビューポイント

**機能性**:
- [ ] 要件を満たしているか
- [ ] エッジケースが考慮されているか
- [ ] エラーハンドリングが適切か

**可読性**:
- [ ] 命名が明確か（snake_case統一）
- [ ] コメントが適切か（NumPy形式Docstring）
- [ ] 複雑なロジックが説明されているか

**保守性**:
- [ ] 重複コードがないか
- [ ] 責務が明確に分離されているか（レイヤードアーキテクチャ遵守）
- [ ] 変更の影響範囲が限定的か

**パフォーマンス**:
- [ ] 不要な計算がないか
- [ ] メモリ使用量が100MB以内か
- [ ] データベースクエリが最適化されているか（該当する場合）

**セキュリティ**:
- [ ] 入力検証が適切か（URLValidator使用）
- [ ] 機密情報がハードコードされていないか
- [ ] HTTPS証明書検証が有効か

### レビューコメントの書き方

**建設的なフィードバック**:

```markdown
## ✅ 良い例
この実装だと、フィード数が増えた時にパフォーマンスが劣化する可能性があります。
dictを使った検索を検討してはどうでしょうか？

```python
feed_map = {f.feed_id: f for f in feeds}
result = feed_map.get(feed_id)
```

## ❌ 悪い例
この書き方は良くないです。
```

**優先度の明示**:

- `[必須]`: 修正必須（セキュリティ、バグ等）
- `[推奨]`: 修正推奨（パフォーマンス、可読性等）
- `[提案]`: 検討してほしい（アーキテクチャ、設計等）
- `[質問]`: 理解のための質問

## 開発環境セットアップ

### 必要なツール

| ツール | バージョン | インストール方法 |
|--------|-----------|-----------------|
| Python | 3.12+ | pyenv install 3.12 または uv python pin 3.12 |
| uv | latest | curl -LsSf https://astral.sh/uv/install.sh \| sh |

### セットアップ手順

```bash
# 1. リポジトリのクローン
git clone [URL]
cd finance

# 2. 依存関係のインストール
uv sync --all-extras

# 3. 環境変数の設定（必要に応じて）
export RSS_DATA_DIR="./data/raw/rss"  # データディレクトリ（デフォルト）
export LOG_LEVEL="INFO"                # ログレベル
export LOG_FORMAT="text"               # ログフォーマット（json/text）

# 4. 開発サーバーの起動（P1機能）
uv run rss-cli --help
uv run rss-mcp
```

### 推奨開発ツール

- **VS Code + Pylance**: 型チェック、オートコンプリート
- **Ruff**: リント・フォーマット（自動修正機能）
- **pytest**: テスト実行

## 品質チェックコマンド

```bash
# 全チェック
make check-all          # format, lint, typecheck, test

# 個別チェック
make format             # コードフォーマット（Ruff）
make lint               # リント（Ruff）
make typecheck          # 型チェック（pyright）
make test               # テスト実行（pytest）
make test-cov           # カバレッジ付きテスト

# 依存関係
uv add package_name     # 通常パッケージ追加
uv add --dev pkg        # 開発用パッケージ追加
uv sync --all-extras    # 全依存関係を同期
```

## パフォーマンス要件

### レスポンスタイム

| 操作 | 目標時間 | 測定環境 |
|------|---------|---------|
| フィード取得（単一） | 5秒以内 | ネットワーク遅延除く |
| JSON保存・読込（100アイテム） | 100ms以内 | 標準的なPC環境 |
| キーワード検索（1000アイテム） | 1秒以内 | 標準的なPC環境 |
| 並列フィード取得（5フィード） | 10秒以内 | ネットワーク遅延除く |

### リソース使用量

| リソース | 上限 | 測定方法 |
|---------|------|---------|
| メモリ | 100MB | memory_profilerで測定（1000アイテム処理時） |
| CPU | 制限なし | 並列取得時は複数コアを活用 |
| ディスク | 制限なし | ユーザーがフィード数・アイテム数を制御 |

## セキュリティ基準

### 入力検証

- URLバリデーション: HTTP/HTTPSスキーマのみ許可
- 文字列長検証: タイトル1-200文字、カテゴリ1-50文字
- エラーメッセージ: スタックトレースは開発環境のみ

### HTTPS通信

- 証明書検証: `verify=True`で証明書検証を有効化
- User-Agent設定: `rss-feed-collector/0.1.0`
- タイムアウト設定: デフォルト10秒（DoS攻撃対策）

### ファイルパーミッション

- デフォルト: OS標準（ユーザー権限で読み書き可能）
- 推奨: `chmod 600 data/raw/rss/*.json`（所有者のみ読み書き）

## チェックリスト

実装完了前に確認:

### コード品質
- [ ] 命名が明確で一貫している（snake_case統一）
- [ ] 関数が単一の責務を持っている
- [ ] マジックナンバーがない（定数化されている）
- [ ] 型ヒントが適切に記載されている（PEP 695準拠）
- [ ] エラーハンドリングが実装されている
- [ ] ロギングが実装されている（structlog使用）

### アーキテクチャ
- [ ] レイヤードアーキテクチャを遵守している
- [ ] 循環依存がない（Protocolで解決）
- [ ] ファイル配置規則に従っている

### セキュリティ
- [ ] 入力検証が実装されている（URLValidator使用）
- [ ] 機密情報がハードコードされていない
- [ ] HTTPS証明書検証が有効である

### パフォーマンス
- [ ] 適切なデータ構造を使用している（dict, set）
- [ ] 不要な計算を避けている
- [ ] 並列処理が適切に実装されている（asyncio.gather使用）
- [ ] メモリ使用量が100MB以内である

### テスト
- [ ] ユニットテストが書かれている（pytest）
- [ ] テストがパスする（make test）
- [ ] カバレッジが80%以上である（make test-cov）
- [ ] エッジケースがカバーされている

### ドキュメント
- [ ] 関数・クラスにNumPy形式のdocstringがある
- [ ] 複雑なロジックにコメントがある
- [ ] AIDEV-TODO/FIXMEが記載されている（該当する場合）

### ツール
- [ ] Ruffエラーがない（make lint）
- [ ] 型チェックがパスする（make typecheck）
- [ ] フォーマットが統一されている（make format）

# market.fraser

FRASER（Federal Reserve Archival System for Economic Research）REST API を使用して連邦準備制度のアーカイブ文書（FOMC Minutes、Beige Book、Federal Reserve Board Speeches など）を取得するモジュール。

## Features

- **30 req/min レート制限を尊重する `DualWindowRateLimiter`**: 1分窓・1時間窓の両方を監視し、`market.alphavantage.rate_limiter` の実装を再利用。
- **SQLite キャッシュ統合**: `market.cache.SQLiteCache` を共有し、エンドポイント別に最適化された TTL（アイテムメタデータ 24h、マスターリスト 7d など）でキャッシュ。
- **SSRF / CWE-209 / CWE-532 対策**: ホスト名ホワイトリスト（`ALLOWED_HOSTS`）、レスポンスログ切り詰め（`MAX_RESPONSE_BODY_LOG`）、`FraserConfig.api_key` の `repr=False`。
- **Pydantic V2 ドメインモデル**: `FraserItem` / `FOMCMeeting` / `BeigeBookReport` などを `populate_by_name=True` + `extra='ignore'` で前方互換に設計。
- **アトミックファイルダウンロード**: `tempfile.NamedTemporaryFile` + `Path.replace()` で部分ファイルが残らない。`item_id` 単位のロックで同一アイテムの重複ダウンロードを防止。

## インストール

このモジュールは `market` パッケージの一部です。

```bash
# リポジトリ全体の依存関係をインストール
uv sync --all-extras
```

## 設定

### API キーの取得

FRASER API キーは `POST /api/api_key` で発行します（無料・即時）。

```bash
# 1. 申請者の email を含めてリクエスト
curl -X POST "https://fraser.stlouisfed.org/api/api_key" \
  -H "Content-Type: application/json" \
  -d '{"email": "your@example.com"}'
# レスポンスに API キーが含まれます。
```

### API キーの設定

**方法1: `.env` ファイル（推奨）**

```bash
# .env に追加（リポジトリ直下）
FRASER_API_KEY=your_api_key_here
```

**方法2: 環境変数**

```bash
export FRASER_API_KEY="your_api_key_here"
```

**方法3: 直接指定**

```python
from market.fraser import FraserClient, FraserConfig

client = FraserClient(config=FraserConfig(api_key="your_api_key_here"))
```

## Quick Start

### ユースケース 1: 2024 年の FOMC Minutes 一覧取得

```python
from market.fraser import FOMCMinutesFetcher

# 1. FOMCMinutesFetcher を作成（.env から API キー自動読込）
fetcher = FOMCMinutesFetcher()

# 2. 2024 年の FOMC Minutes を取得
meetings = fetcher.list_minutes(year_range=(2024, 2024))

# 3. 結果を確認
print(f"取得件数: {len(meetings)}")
for meeting in meetings:
    print(f"  - {meeting.date.isoformat()}: itemId={meeting.item_id} | {meeting.title}")
```

**出力例:**

```
取得件数: 8
  - 2024-01-31: itemId=634123 | Minutes of the FOMC Meeting, January 30-31, 2024
  - 2024-03-20: itemId=634124 | Minutes of the FOMC Meeting, March 19-20, 2024
  - 2024-05-01: itemId=634125 | Minutes of the FOMC Meeting, April 30-May 1, 2024
  ...
```

### ユースケース 2: 特定 Minutes の TXT ダウンロード + メタデータ保存

```python
from market.fraser import FOMCMinutesFetcher

fetcher = FOMCMinutesFetcher()

# item_id を指定して TXT を取得（PDF にフォールバック可能）
path, meeting = fetcher.fetch_text(item_id=634123, prefer="txt")

print(f"保存先: {path}")
print(f"ファイルサイズ: {path.stat().st_size} bytes")
print(f"メタデータ: {path.with_suffix('.meta.json')}")
print(f"meeting_date: {meeting.meeting_date}")
```

**出力例:**

```
保存先: data/raw/fraser/fomc/minutes/2024-01-31_634123.txt
ファイルサイズ: 87543 bytes
メタデータ: data/raw/fraser/fomc/minutes/2024-01-31_634123.meta.json
meeting_date: 2024-01-31
```

## 公開サーフェス（HF1 確定: 8 シンボル）

`from market.fraser import ...` で利用可能なシンボルは以下の 8 つに限定されています。
内部ユーティリティ（`FraserSession`, `FraserDownloader`, `parser.*` など）は
サブモジュールから直接インポートしてください。

| シンボル | 種別 | 用途 |
|---------|------|------|
| `FraserClient` | クラス | REST API クライアント本体 |
| `FOMCMinutesFetcher` | クラス | FOMC Minutes 取得（PR3 で追加） |
| `FraserConfig` | dataclass | 設定（認証・タイムアウト・レート制限） |
| `FOMCMeeting` | Pydantic V2 model | FOMC ミーティングのドメインモデル |
| `FraserError` | 例外基底 | 全 FRASER 例外の catch-all |
| `FraserAuthError` | 例外 | 認証失敗（401/403） |
| `FraserParseError` | 例外 | レスポンスパース失敗 |
| `FraserRateLimitError` | 例外 | レート制限超過（429） |

## API Reference

### `FraserClient`

```python
class FraserClient:
    def __init__(
        self,
        config: FraserConfig | None = None,
        session: FraserSession | None = None,
        cache: SQLiteCache | None = None,
    ) -> None: ...

    def list_items(self, title_id: int, limit: int = 50, page: int = 1, *, use_cache: bool = True) -> list[FraserItem]: ...
    def get_item(self, item_id: int, *, use_cache: bool = True) -> FraserItem: ...
    def get_title(self, title_id: int, *, use_cache: bool = True) -> FraserTitle: ...
    def get_toc(self, item_id: int, *, use_cache: bool = True) -> list[FraserTocEntry]: ...
    def get_authors(self, *, use_cache: bool = True) -> list[FraserAuthor]: ...
    def get_subjects(self, *, use_cache: bool = True) -> list[FraserSubject]: ...
    def get_themes(self, *, use_cache: bool = True) -> list[FraserTheme]: ...
    def get_timeline(self, title_id: int, *, use_cache: bool = True) -> list[FraserTimelineEvent]: ...
```

### `FOMCMinutesFetcher`

```python
class FOMCMinutesFetcher(BaseFraserFetcher):
    doc_type: DocType  # = DocType.FOMC_MINUTES

    def __init__(
        self,
        client: FraserClient | None = None,
        downloader: FraserDownloader | None = None,
        base_dir: Path = Path("data/raw/fraser"),
    ) -> None: ...

    def list_minutes(
        self,
        year_range: tuple[int, int],
        *,
        limit: int = 100,
    ) -> list[FOMCMeeting]: ...

    def fetch_text(
        self,
        item_id: int,
        *,
        prefer: str = "txt",
    ) -> tuple[Path, FOMCMeeting]: ...

    def fetch_pdf(self, item_id: int) -> tuple[Path, FOMCMeeting]: ...
```

| 引数 | 型 | デフォルト | 説明 |
|------|----|-----------|------|
| `year_range` | `tuple[int, int]` | 必須 | `(start_year, end_year)` 両端含む |
| `limit` | `int` | 100 | 1 ページあたりの取得件数 |
| `item_id` | `int` | 必須 | FRASER アイテム ID |
| `prefer` | `'txt' \| 'pdf'` | `'txt'` | 優先フォーマット（フォールバック自動） |

### `FraserConfig`

```python
@dataclass(frozen=True)
class FraserConfig:
    api_key: str = ""           # 空なら FRASER_API_KEY 環境変数を参照
    base_url: str = "https://fraser.stlouisfed.org/api"
    timeout: float = 30.0        # > 0 必須
    requests_per_minute: int = 30  # >= 1 必須
    requests_per_hour: int = 1800
    retry_config: RetryConfig = field(default_factory=RetryConfig)
```

### `FOMCMeeting`

`FraserItem` を継承し、FOMC 固有フィールドを追加した Pydantic V2 モデル。

| フィールド | 型 | 説明 |
|-----------|----|------|
| `item_id` | `int` | FRASER アイテム ID |
| `title` | `str` | タイトル |
| `date` | `date` | 公開日（`YYYY-MM-DD` / `YYYY-MM` / `YYYY` 自動正規化） |
| `meeting_date` | `date \| None` | 会議日（FOMC メタデータが含まれる場合のみ） |
| `meeting_type` | `str \| None` | 会議種別（`regular` / `intermeeting` など） |
| `location` | `FraserLocation \| None` | PDF/TXT URL |
| `description` | `str \| None` | 概要 |

### エラー階層

```
FraserError
├── FraserAuthError          (401/403)
├── FraserRateLimitError     (429, retry_after 保持)
├── FraserNotFoundError      (404)
├── FraserAPIError           (その他 4xx/5xx)
├── FraserParseError         (Pydantic ValidationError ラップ)
├── FraserDownloadError      (ファイル DL 失敗)
└── FraserValidationError    (設定値違反)
```

公開サーフェスには `FraserError` / `FraserAuthError` / `FraserParseError` / `FraserRateLimitError` の
4 つのみが含まれます。それ以外は `market.fraser.errors` から直接インポートしてください。

## Examples

実動作例は `notebook/FRASER/fraser_demo.ipynb` に追加予定（PR5 で整備）。

それまでは [Quick Start](#quick-start) のスニペットを Python REPL や
スクリプトに貼り付けて実行することで動作確認できます。

## Troubleshooting

### 1. `FraserAuthError: FRASER API key not provided.`

`FRASER_API_KEY` 環境変数が未設定です。`.env` ファイルに以下を追加してください。

```bash
FRASER_API_KEY=your_api_key_here
```

API キーをまだ発行していない場合は [API キーの取得](#api-キーの取得) を参照。

### 2. `FraserRateLimitError: Rate limit exceeded (HTTP 429)`

FRASER API は **30 リクエスト/分** を超えると 429 を返します。

- `FraserConfig.requests_per_minute` はデフォルトで 30 に設定済みなので、通常は自動で待機します。
- スロットルを超えた場合は `retry_after` 属性（秒数）を確認して再試行までスリープしてください。

```python
from market.fraser import FraserRateLimitError

try:
    items = client.list_items(title_id=677)
except FraserRateLimitError as e:
    print(f"Retry after {e.retry_after} seconds")
```

### 3. `FraserValidationError: title_id for 'beige_book' is not configured.`

`market.fraser.constants.KNOWN_TITLE_IDS` で `None` のままになっている文書タイプの `title_id` を
発見・登録する必要があります。以下の CLI を実行してください。

```bash
uv run python -m market.fraser.scripts.discover_titles \
    --output data/config/fraser_titles.json \
    --interactive
```

確認した `title_id` を `KNOWN_TITLE_IDS` にハードコードするか、出力された JSON ファイルを
`data/config/fraser_titles.json` に配置すると `BaseFraserFetcher._resolve_title_id()` が自動でフォールバック解決します。

### 4. API キーを失効・再発行したい

漏洩が疑われる場合は以下の手順で revoke + 再発行します。

```bash
# 1. 旧 API キーを revoke
curl -X DELETE "https://fraser.stlouisfed.org/api/api_key" \
  -H "X-Api-Key: <old_key>"

# 2. 新規 API キーを再発行
curl -X POST "https://fraser.stlouisfed.org/api/api_key" \
  -H "Content-Type: application/json" \
  -d '{"email": "your@example.com"}'

# 3. .env を更新
sed -i '' 's/FRASER_API_KEY=.*/FRASER_API_KEY=<new_key>/' .env
```

詳細な運用手順は PR5（`notebook/FRASER/fraser_demo.ipynb`）で整備予定。

### 5. ダウンロードファイルが `.tmp` のまま残る

通常は `tempfile.NamedTemporaryFile` + `finally` ブロックで自動削除されますが、
プロセスが異常終了した場合に残骸が残る可能性があります。以下のコマンドで安全に削除できます。

```bash
find data/raw/fraser/ -name "*.tmp" -delete
```

## 関連モジュール

- `market.fred` - FRED API（経済指標時系列データ）
- `market.alphavantage` - Alpha Vantage API（株価・ファンダメンタル）
- `market.cache` - SQLite キャッシュ層（FRASER でも共有）

## ライセンス

このモジュールは quants リポジトリのライセンスに従います。
FRASER API の利用にあたっては [FRASER 利用規約](https://fraser.stlouisfed.org/) を遵守してください。

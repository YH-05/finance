# FRASER REST API サブパッケージ実装プラン (`src/market/fraser/`)

> 📝 推奨リネーム先: `docs/plan/2026-05-25_market-fraser-library.md`（実装着手前に `/plan-docs-rename` で変換）

## Context

FRB/FOMC 関連の一次テキスト資料（FOMC 議事録・声明文・記者会見、Beige Book、各種金融政策報告、Powell/Volcker 等の歴史的スピーチ）をマクロクオンツ分析・レジーム判定 (`notebook/REGIME_SWITCHING/`) や NLP パイプライン (`notebook/FILING_NLP/`) に応用したい。これらの一次資料は **St. Louis Fed の FRASER API** から構造化メタデータ + フルテキスト(TXT) + PDF として取得可能。

現状、`notebook/FRASER/fraser_test.ipynb` でユーザーが API key 取得・`title_id=677`（FOMC Minutes）の `/items` 動作確認まで完了済みだが、`requests` 直叩きで再利用性なし。一方 `src/market/` 配下には `fred/`・`alphavantage/` 等の成熟した API クライアント実装パターンが既にある。

**ゴール**: `src/market/fraser/` として FRASER API クライアントを実装し、テキスト取得 + 構造化メタデータまでをライブラリ責務とする（NLP は notebook 側で `src/embedding/` や FinBERT パイプラインに委譲）。これにより SEC Filings (`src/edgar/`) と並ぶ「政策テキスト」一次データ層が確立する。

## Scope（ユーザー確認済み）

- **対象ドキュメント**: FOMC Minutes / FOMC Statements + Press Conferences / Beige Book / FRB Speeches + Monetary Policy Reports + 歴史アーカイブ（全 4 種）
- **責務範囲**: API クライアント + キャッシュ + PDF/TXT ダウンロード + 構造化メタデータ抽出まで。NLP・エンベディング・factor 統合は **本ライブラリの責務外**
- **保存戦略**: API JSON は SQLite キャッシュ、PDF/TXT 実体は `data/raw/fraser/<doc_type>/<date>_<itemId>.<ext>` に永続化
- **API key**: `.env` に `FRASER_API_KEY` を追加、`notebook/FRASER/fraser_test.ipynb` 内のハードコード値を移行

## FRASER API 仕様サマリ（調査結果）

- **Base URL**: `https://fraser.stlouisfed.org/api`
- **認証**: `X-API-Key` ヘッダー（`POST /api/api_key` で発行）
- **レート制限**: **30 req/min**（API key 単位で自動エンフォース、要強アグレッシブ・キャッシング）
- **データモデル 3 階層**: `title`（書誌・刊行物）→ `item`（個別ファイル、`location.pdfUrl[]` / `location.textUrl[]` を含む）→ `toc`（ページ範囲セクション）
- **発見系**: `theme` / `subject` / `author` / `timeline` の各エンドポイント（全フルテキスト検索エンドポイントは**ない**ため、title_id 経由がメイン）
- **共通クエリパラメータ**: `limit`, `page`, `format`, `fields`（`!` 区切り）
- **レスポンス**: MODS XML 由来の深くネストした JSON、`format=json` 既定

## ディレクトリ構成

```
src/market/fraser/
├── __init__.py          # 公開 API（FraserClient, fetchers, models, errors）
├── README.md            # 使い方とクイックスタート（fred/README.md に倣う）
├── constants.py         # BASE_URL, ALLOWED_HOSTS, env 名, レート定数, KNOWN_TITLE_IDS
├── types.py             # FraserConfig / FetchOptions / RetryConfig / CacheTTL 定数
├── errors.py            # FraserError 階層
├── rate_limiter.py      # 30 req/min token bucket
├── session.py           # FraserSession: httpx Client + X-API-Key + RateLimiter + tenacity retry + SSRF guard
├── client.py            # FraserClient: 全エンドポイント wrap
├── cache.py             # FraserCache: market.cache.SQLiteCache 派生（prefix="fraser:"）
├── models.py            # Pydantic V2: FraserTitle / FraserItem / FraserTocEntry / FraserLocation / FOMCMeeting / BeigeBookReport / FRBSpeech
├── parser.py            # API JSON → Pydantic 変換（部分パース寛容）
├── downloader.py        # PDF/TXT 実体 DL（streaming + ETag + atomic rename）
├── fetchers/
│   ├── __init__.py
│   ├── base.py          # BaseFraserFetcher（client + cache + downloader 集約）
│   ├── fomc.py          # FOMCMinutesFetcher / FOMCStatementsFetcher
│   ├── beige_book.py    # BeigeBookFetcher
│   ├── speeches.py      # FRBSpeechFetcher（記者会見含む）
│   └── monetary_policy.py  # MonetaryPolicyReportFetcher + 歴史アーカイブ
└── scripts/
    └── discover_titles.py  # subject/theme から FRB 関連 title_id を発見する CLI
```

設計原則は `src/market/fred/` の 3 層構成を発展させ、`src/market/alphavantage/` の **session 分離 + models + parser + rate_limiter** パターンを取り込む。

## 主要設計判断

### HTTP クライアント: **httpx**
`alphavantage/session.py` で実績あり。`timeout` / `limits` / `verify` の一括管理、将来 async 拡張容易。`fred/` の `requests` ベースは採用しない（FRASER 用は新規）。

### データモデル: **Pydantic V2**
FRASER の JSON は MODS XML 由来で深くネスト、optional 多発、`pdfUrl[]` のような配列ラップ多用。`Field(alias=...)` で camelCase → snake_case 変換、`model_validate()` の部分寛容性で堅牢化。`dataclass` は不向き。

### title_id レジストリ: **ハイブリッド**
30 req/min 制約下で全 subject/theme を毎回走査するのは非現実的。`constants.KNOWN_TITLE_IDS`（ハードコード）+ `data/config/fraser_titles.json`（永続化）+ `scripts/discover_titles.py`（CLI 更新）の 3 層構成。

```python
KNOWN_TITLE_IDS: Final[dict[str, int]] = {
    "fomc_minutes": 677,                    # ユーザー確認済み
    "fomc_statements": <discover で確定>,
    "fomc_press_conferences": <discover で確定>,
    "beige_book": <discover で確定>,
    "monetary_policy_report": <discover で確定>,
    "frb_speeches": <discover で確定>,
}
```

PR1 着手時に `discover_titles.py` で残り 5 件を確定させ、`KNOWN_TITLE_IDS` を埋める。

### キャッシュ階層（TTL）
| データ種別 | TTL | 理由 |
|---|---|---|
| title metadata | 30 日 | 書誌情報はほぼ不変 |
| items list (per title) | 7 日 | 新 item 追加検知 |
| item metadata | 30 日 | 個別 item は変更稀 |
| author/subject/theme | 30 日 | 静的 |
| timeline events | 7 日 | 更新頻度低 |

共通 `market_data.db` に `fraser:` プレフィクスで同居（`src/market/cache/cache.py` の `SQLiteCache` を再利用）。

### ファイル保存パス規約
`data/raw/fraser/<doc_subdir>/<YYYY-MM-DD>_<itemId>.{pdf,txt,meta.json}`

例: `data/raw/fraser/fomc/minutes/2024-01-31_12345.txt`

冪等性: ファイル存在チェック → `ETag` / `Last-Modified` 比較 → 必要時のみ再 DL。並行 DL は `.tmp` → atomic rename。

### レート制限 + リトライ
- `market.alphavantage.rate_limiter.DualWindowRateLimiter` を流用（`requests_per_minute=30`）
- `news_scraper.retry.create_retry_decorator` パターン（tenacity 指数バックオフ、jitter、`max_attempts=5`）
- 429 は `Retry-After` ヘッダ尊重（`max(retry_after, exponential_delay)`）

### エラー階層（`src/market/errors.py:MarketError` 継承）
`FraserError` → `FraserAuthError` (401/403) / `FraserRateLimitError` (429, `retry_after` 属性) / `FraserNotFoundError` (404) / `FraserAPIError` (5xx, RetryableError 派生) / `FraserParseError` / `FraserDownloadError`

## 典型ユースケース（公開 API）

```python
from market.fraser import FOMCMinutesFetcher, BeigeBookFetcher

# Case 1: FOMC Minutes 一覧 → 個別議事録テキスト
fetcher = FOMCMinutesFetcher()                       # FRASER_API_KEY を .env から自動読込
meetings = fetcher.list_minutes(year_range=(2020, 2024))  # list[FOMCMeeting]
text_path, meeting = fetcher.fetch_text(meetings[0].item_id, prefer="txt")
text = text_path.read_text()

# Case 2: Beige Book 年単位の一括取得（PDF/TXT 両方並列 DL）
reports = BeigeBookFetcher().fetch_all(year_range=(2023, 2024))
```

## 既存パターン参照（再利用元）

| 再利用先 | パス | 用途 |
|---|---|---|
| 3 層構成テンプレ | `src/market/fred/{base_fetcher,fetcher,cache,types,constants}.py` | サブパッケージ全体構成 |
| httpx Session 層 | `src/market/alphavantage/session.py` | `FraserSession` のテンプレ |
| rate limiter | `src/market/alphavantage/rate_limiter.py:DualWindowRateLimiter` | 30 req/min 制約用 |
| 共通 SQLite キャッシュ | `src/market/cache/cache.py:SQLiteCache` + `_resolve_cache_db_path` | `FraserCache` の親 |
| tenacity リトライ | `src/news_scraper/retry.py:create_retry_decorator` | バックオフ実装 |
| Retryable/Permanent 階層 | `src/news_scraper/exceptions.py` | エラー分類設計 |
| テキスト抽出パターン | `src/edgar/extractors/text.py` | ライブラリ範囲の境界線参照 |
| env 読込 | `src/utils_core/settings.py:load_project_env` | `FRASER_API_KEY` 取得 |
| ロガー | `utils_core.logging.get_logger` | 全モジュール標準 |
| テスト構成 | `tests/market/fred/` の unit/property/integration 分割 | `tests/market/fraser/` のテンプレ |
| データ保存規約 | `data/raw/edgar/` の `<entity>/<date>_<id>` 構造 | `data/raw/fraser/<doc_type>/<date>_<itemId>` |

## 実装ロードマップ（5 PR）

| PR | スコープ | 主要ファイル | 受け入れ条件 |
|---|---|---|---|
| **PR1: 基盤** | constants / types / errors / models / rate_limiter / session + `scripts/discover_titles.py` で `KNOWN_TITLE_IDS` 確定 | `constants.py, types.py, errors.py, models.py, rate_limiter.py, session.py, scripts/discover_titles.py` | session で `title_id=677` を実 API 取得、5 ドキュメント種別の title_id が `KNOWN_TITLE_IDS` に埋まる |
| **PR2: Client + Cache + Downloader** | 全エンドポイント wrap、SQLite キャッシュ、PDF/TXT DL | `client.py, cache.py, downloader.py, parser.py` | unit カバレッジ 80%+、integration で実 PDF/TXT 1 件 DL |
| **PR3: FOMC Minutes MVP** | `fetchers/fomc.py`（Minutes のみ）、`__init__.py` 公開 | `fetchers/base.py, fetchers/fomc.py, __init__.py, README.md` | E2E: `list_minutes((2024,2024))` で 6 件以上取得、1 件 TXT DL（>1KB） |
| **PR4: 他ドキュメント拡張** | Statements / Press Conferences / Beige Book / Speeches / MPR | `fetchers/{beige_book,speeches,monetary_policy}.py`, `fomc.py` 拡張 | 各 fetcher で unit + integration 1 件 |
| **PR5: 検証ノートブック + アーカイブ** | thin demo notebook 作成、`fraser_test.ipynb` 退避 | `notebook/FRASER/fraser_demo.ipynb`, `notebook/FRASER/archive/fraser_test.ipynb` | 全セル成功実行、`research idea.md` 参照リンク追加 |

各 PR で `make check-all` (ruff + pyright + pytest unit) が pass する単位に分割。

## テスト計画

```
tests/market/fraser/
├── conftest.py            # pytest-httpx fixtures、sample JSON、tmp data dir
├── unit/                  # session / rate_limiter / client / cache / models / parser / downloader / errors / fetchers
├── property/              # Hypothesis: 任意 JSON でも parse 失敗で FraserParseError
└── integration/           # @pytest.mark.integration、title_id=677、FRASER_API_KEY 未設定なら skip
```

- HTTP モック: `pytest-httpx`（`alphavantage` 既存）
- レート制限テスト: `monkeypatch.setattr(time, "monotonic", ...)` で時間制御
- CI では `integration` マーカーをデフォルト除外（手動 `pytest -m integration` で実行）

## 既存 `notebook/FRASER/fraser_test.ipynb` の扱い

PR5 で `notebook/FRASER/archive/` へ退避し、`notebook/FRASER/fraser_demo.ipynb`（thin demo、3-4 行 API 紹介 + `notebook/FILING_NLP/research idea.md` への次ステップリンク）に置き換える。

**重要**: `fraser_test.ipynb` Cell 1 に **API key がハードコード**されている（`6da0308c620b2308091cb2c902a0f5db`）。PR1 着手時に:
1. `.env` に `FRASER_API_KEY=6da0308c620b2308091cb2c902a0f5db` を追加（手動）
2. `.env.example` に `FRASER_API_KEY=your_api_key_here` 行を追加
3. `fraser_test.ipynb` の該当行を `os.getenv("FRASER_API_KEY")` に書き換え（archive 前のクリーニング）

## 検証方法

### 自動チェック
- `make check-all` 通過（ruff lint + format、pyright、pytest unit + property）
- カバレッジ: `src/market/fraser/` 全体 **85% 以上**
- 統合テスト: `FRASER_API_KEY=... pytest tests/market/fraser/integration -m integration`

### E2E スモーク（PR3 完了時）

```bash
uv run python -c "
from market.fraser import FOMCMinutesFetcher
f = FOMCMinutesFetcher()
ms = f.list_minutes(year_range=(2024, 2024))
assert len(ms) >= 6, f'Expected >=6 minutes, got {len(ms)}'
path, m = f.fetch_text(ms[0].item_id)
assert path.exists() and path.stat().st_size > 1000
print(f'OK: {len(ms)} minutes, sample: {path}')
"
```

### 手動チェック
- `.env.example` に `FRASER_API_KEY=...` の例示行があるか
- `data/raw/fraser/fomc/minutes/` に 3 件以上 PDF/TXT が存在するか
- `market_data.db` に `fraser:` プレフィクスのキャッシュエントリがあるか
- `data/config/fraser_titles.json` に 6 種類の title_id が埋まっているか

## Critical Files for Implementation

- `/Users/yukihata/Desktop/quants/src/market/fraser/session.py`
- `/Users/yukihata/Desktop/quants/src/market/fraser/client.py`
- `/Users/yukihata/Desktop/quants/src/market/fraser/models.py`
- `/Users/yukihata/Desktop/quants/src/market/fraser/fetchers/fomc.py`
- `/Users/yukihata/Desktop/quants/src/market/fraser/__init__.py`
- `/Users/yukihata/Desktop/quants/src/market/fraser/constants.py`（`KNOWN_TITLE_IDS`）
- `/Users/yukihata/Desktop/quants/scripts/discover_titles.py`（PR1 で title_id 確定用 CLI）
- `/Users/yukihata/Desktop/quants/.env.example`（`FRASER_API_KEY` 追記）

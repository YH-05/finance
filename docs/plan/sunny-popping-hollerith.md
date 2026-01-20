# Yahoo Finance Earnings Calendar スクレイピング実装計画

## 概要

Yahoo Finance の Earnings Calendar ページ（https://finance.yahoo.com/calendar/earnings/）をスクレイピングし、今後の決算発表予定企業の情報を取得する機能を実装する。

## 既存実装との比較

### 既存: `EarningsCalendar` クラス（yfinance ベース）

**ファイル**: `src/market_analysis/analysis/earnings.py`

- **方式**: yfinance の `get_earnings_dates()` を使用
- **入力**: 銘柄リスト（デフォルト: Mag7 + セクター代表約30銘柄）
- **処理**: 各銘柄を個別にAPIコール
- **制限**: 指定した銘柄以外は取得不可

### 新規: Web スクレイピング

- **方式**: Yahoo Finance Earnings Calendar ページをスクレイピング
- **入力**: 日付範囲
- **処理**: 指定期間の全決算予定を一括取得
- **利点**:
    - 銘柄を事前に知らなくても、その日に決算がある全企業を発見可能
    - 時価総額、決算発表時間（AMC/BMO）などの追加情報を取得
    - 小型株・新規上場株も漏れなく取得

### ユースケースの違い

| ユースケース         | 既存（yfinance） | 新規（スクレイピング） |
| -------------------- | ---------------- | ---------------------- |
| 特定銘柄の決算日確認 | ✅ 適切          | △ オーバーキル         |
| 今週の全決算一覧取得 | △ 銘柄指定が必要 | ✅ 適切                |
| 決算シーズンの俯瞰   | ✗ 不向き         | ✅ 適切                |
| 時価総額順での表示   | ✗ 不可           | ✅ 可能                |

## ページ構造分析

### URL パターン

- ベースURL: `https://finance.yahoo.com/calendar/earnings/`
- 日付指定: `/calendar/earnings?from=2026-01-18&to=2026-01-24&day=2026-01-20`

### テーブル構造（取得可能データ）

| カラム             | 説明                   | 例                                                 |
| ------------------ | ---------------------- | -------------------------------------------------- |
| Symbol             | ティッカーシンボル     | NFLX, AAPL                                         |
| Company            | 会社名                 | Netflix, Inc.                                      |
| Event Name         | イベント名             | Q4 2025 Earnings Announcement                      |
| Earnings Call Time | 発表時間               | AMC (After Market Close), BMO (Before Market Open) |
| EPS Estimate       | 予想EPS                | 0.55                                               |
| Reported EPS       | 実績EPS（発表後）      | -                                                  |
| Surprise (%)       | サプライズ率（発表後） | -                                                  |
| Market Cap         | 時価総額               | 372.88B                                            |

### 週間カレンダー構造

- 1週間単位で表示（日曜〜土曜）
- 各日に決算予定数が表示（例: "30 Earnings"）
- 日付クリックでその日の詳細一覧を表示

## 実装方針

### 決定事項

- **実装場所**: 既存の `src/market_analysis/analysis/earnings.py` に追加
- **スクレイピング方式**: Playwright（JavaScript レンダリング対応）
- **API スタイル**: 非同期（async/await）

### ファイル構成（変更後）

```
src/market_analysis/
├── analysis/
│   └── earnings.py              # 既存 + 新規クラス追加
│       ├── EarningsCalendar     # 既存（yfinance ベース）
│       ├── EarningsData         # 既存
│       ├── EarningsCalendarScraper  # 新規（Playwright ベース）
│       └── EarningsScrapedEvent     # 新規（スクレイピング用データ型）
├── types.py                      # 既存（Enum追加）
└── errors.py                     # 既存
```

## 詳細設計

### 1. 型定義の追加

#### types.py に追加

```python
class EarningsCallTime(str, Enum):
    """決算発表時間"""
    BMO = "BMO"  # Before Market Open
    AMC = "AMC"  # After Market Close
    TAS = "TAS"  # Time Not Supplied
    UNKNOWN = "UNKNOWN"
```

#### earnings.py に追加

```python
@dataclass
class EarningsScrapedEvent:
    """Webスクレイピングで取得した決算イベント情報"""
    symbol: str
    company_name: str
    event_name: str
    earnings_date: date
    call_time: EarningsCallTime
    eps_estimate: float | None
    reported_eps: float | None
    surprise_percent: float | None
    market_cap_str: str | None  # "372.88B" 形式

    @property
    def market_cap_value(self) -> float | None:
        """時価総額を数値（ドル）に変換"""
        if not self.market_cap_str:
            return None
        # 372.88B → 372880000000
        ...

@dataclass
class EarningsCalendarScraperResult:
    """スクレイピング結果"""
    events: list[EarningsScrapedEvent]
    target_date: date
    fetched_at: datetime
    from_cache: bool = False
```

### 2. EarningsCalendarScraper クラス

```python
class EarningsCalendarScraper:
    """Yahoo Finance Earnings Calendar ページのスクレイパー（非同期）"""

    BASE_URL = "https://finance.yahoo.com/calendar/earnings"

    def __init__(
        self,
        headless: bool = True,
        timeout: int = 30000,
    ) -> None:
        self._headless = headless
        self._timeout = timeout

    async def fetch_by_date(
        self,
        target_date: date,
    ) -> EarningsCalendarScraperResult:
        """指定日の決算一覧を取得"""
        ...

    async def fetch_date_range(
        self,
        start_date: date,
        end_date: date,
    ) -> list[EarningsCalendarScraperResult]:
        """指定期間の決算一覧を取得（日付ごとに並列取得）"""
        ...

    async def _scrape_page(
        self,
        target_date: date,
    ) -> list[EarningsScrapedEvent]:
        """Playwrightでページをスクレイピング"""
        ...

    def _parse_table_row(
        self,
        cells: list[str],
        target_date: date,
    ) -> EarningsScrapedEvent:
        """テーブル行をパース"""
        ...

    @staticmethod
    def _parse_market_cap(value: str) -> str | None:
        """時価総額文字列をパース（"372.88B" → "372.88B"）"""
        ...

    @staticmethod
    def _parse_eps(value: str) -> float | None:
        """EPS文字列をパース（"0.55" → 0.55, "-" → None）"""
        ...
```

### 3. スクレイピング実装詳細

```python
async def _scrape_page(self, target_date: date) -> list[EarningsScrapedEvent]:
    from playwright.async_api import async_playwright

    url = f"{self.BASE_URL}?day={target_date.isoformat()}"

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=self._headless)
        page = await browser.new_page()

        try:
            await page.goto(url, wait_until="networkidle", timeout=self._timeout)

            # テーブルが表示されるまで待機
            await page.wait_for_selector("table tbody tr", timeout=self._timeout)

            # テーブル行を取得
            rows = await page.query_selector_all("table tbody tr")

            events = []
            for row in rows:
                cells = await row.query_selector_all("td")
                if len(cells) >= 8:
                    cell_texts = [await cell.inner_text() for cell in cells]
                    event = self._parse_table_row(cell_texts, target_date)
                    events.append(event)

            return events
        finally:
            await browser.close()
```

### 4. エラーハンドリング

既存の `errors.py` の `DataFetchError` を活用：

- ネットワークエラー: `ErrorCode.NETWORK_ERROR`
- パースエラー: `ErrorCode.DATA_NOT_FOUND`
- レート制限: `ErrorCode.RATE_LIMIT`

### 5. キャッシュ戦略

- キャッシュキー: `earnings_calendar:{start_date}:{end_date}`
- TTL: 1時間（決算カレンダーは頻繁に更新されないため）
- 既存の `SQLiteCache` を活用

## ファイル変更一覧

| ファイル                                                       | 変更内容                                                                                |
| -------------------------------------------------------------- | --------------------------------------------------------------------------------------- |
| `src/market_analysis/types.py`                                 | `EarningsCallTime` Enum 追加                                                            |
| `src/market_analysis/analysis/earnings.py`                     | `EarningsScrapedEvent`, `EarningsCalendarScraperResult`, `EarningsCalendarScraper` 追加 |
| `src/market_analysis/analysis/__init__.py`                     | エクスポート追加                                                                        |
| `tests/market_analysis/unit/analysis/test_earnings_scraper.py` | 新規テスト作成                                                                          |
| `pyproject.toml`                                               | playwright 依存関係追加（必要な場合）                                                   |

## 実装ステップ

### Step 1: 依存関係確認

- `playwright` がインストールされているか確認
- 必要なら `uv add playwright` で追加
- `playwright install chromium` でブラウザをインストール

### Step 2: 型定義の追加

- `types.py` に `EarningsCallTime` Enum を追加

### Step 3: データクラス追加

- `earnings.py` に `EarningsScrapedEvent`, `EarningsCalendarScraperResult` を追加

### Step 4: スクレイパークラス実装

- `EarningsCalendarScraper` クラスの骨格作成
- `fetch_by_date()` メソッド実装
- `_scrape_page()` メソッド実装（Playwright）
- `_parse_table_row()` メソッド実装

### Step 5: 日付範囲取得の実装

- `fetch_date_range()` メソッド実装
- asyncio.gather による並列取得

### Step 6: エラーハンドリング・ログ

- タイムアウト、ネットワークエラー対応
- 構造化ログ出力

### Step 7: テスト作成

- 単体テスト（パース処理のテスト）
- 統合テスト（実際のページアクセス、`@pytest.mark.integration`）

### Step 8: エクスポート更新

- `__init__.py` に新規クラスを追加

## 検証方法

### 動作確認

```python
import asyncio
from datetime import date
from market_analysis.analysis.earnings import EarningsCalendarScraper

async def main():
    scraper = EarningsCalendarScraper()

    # 特定日の決算一覧を取得
    result = await scraper.fetch_by_date(date(2026, 1, 21))

    print(f"取得件数: {len(result.events)}")
    for event in result.events[:5]:  # 上位5件
        print(f"{event.symbol}: {event.company_name}")
        print(f"  発表時間: {event.call_time.value}")
        print(f"  EPS予想: {event.eps_estimate}")
        print(f"  時価総額: {event.market_cap_str}")

asyncio.run(main())
```

### テスト実行

```bash
# 単体テスト
uv run pytest tests/market_analysis/unit/analysis/test_earnings_scraper.py -v

# 統合テスト（実際のページアクセス）
uv run pytest tests/market_analysis/integration/test_earnings_scraper.py -v -m integration

# 全テスト
make test
```

### 品質チェック

```bash
make check-all  # format, lint, typecheck, test
```

## 注意事項

1. **利用規約**: Yahoo Finance の利用規約を確認（個人利用・非商用目的）
2. **レート制限**: 短時間での大量リクエストを避ける（1秒以上の間隔推奨）
3. **ページ構造変更**: Yahoo Finance のUI変更に備え、堅牢なパーサー実装とテスト
4. **ヘッドレスモード**: 本番では `headless=True` を使用
5. **タイムアウト**: ネットワーク状況に応じてタイムアウト値を調整

## 既存機能との使い分け

| 目的                           | 使用するクラス                    |
| ------------------------------ | --------------------------------- |
| 特定銘柄（AAPL等）の決算日確認 | `EarningsCalendar`（既存）        |
| 今週の全決算一覧取得           | `EarningsCalendarScraper`（新規） |
| 決算シーズンの俯瞰             | `EarningsCalendarScraper`（新規） |

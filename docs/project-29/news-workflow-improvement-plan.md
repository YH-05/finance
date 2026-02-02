# ニュースワークフロー改善実装計画

## 概要

`docs/news-workflow-analysis-2026-02-02.md` の分析結果に基づき、ニュースワークフローの改善を実施する。

## 現状分析

### カテゴリ分布（rss-presets.json）
| カテゴリ | フィード数 | マップ先Status |
|----------|-----------|----------------|
| tech | 5 | ai |
| market | 5 | index |
| finance | 19 | finance |
| **stock** | **0** | - |
| **sector** | **0** | - |
| **macro** | **0** | - |

### 問題のサマリー

| 問題 | 影響 | 優先度 |
|------|------|--------|
| MarketWatch URL変更（301エラー） | marketフィード1件失敗 | 高 |
| Seeking Alpha ブロックドメイン | marketフィード1件スキップ | 情報 |
| CNBC - Markets フォーマットエラー | marketフィード1件失敗 | 高 |
| stock/sector/macroカテゴリ不在 | 該当Status投稿0件 | 中 |
| RSS収集層にリトライ設定なし | Yahoo Finance 429エラー | 中 |
| CNBCコンテンツ抽出44%失敗 | 抽出成功率低下 | 低 |

---

## Phase 1: 即時対応（優先度: 高）

### 1.1 MarketWatch URL更新

**ファイル**: `data/config/rss-presets.json` (行32-38)

```json
// 変更前
{
  "url": "https://feeds.marketwatch.com/marketwatch/topstories/",
  "title": "MarketWatch Top Stories",
  "category": "market"
}

// 変更後
{
  "url": "https://feeds.content.dowjones.io/public/rss/mw_topstories",
  "title": "MarketWatch Top Stories",
  "category": "market"
}
```

**検証**: `curl -sI "https://feeds.content.dowjones.io/public/rss/mw_topstories" | head -1`

### 1.2 RSS収集層へのリトライ機構追加

**ファイル**: `src/news/collectors/rss.py`

現在の実装では RSS フィード取得失敗時にスキップするのみ。指数バックオフリトライを追加する。

```python
# 既存の RetryConfig を活用
from news.core.result import RetryConfig

class RSSCollector:
    def __init__(self, config: RSSConfig) -> None:
        self._retry_config = RetryConfig(
            max_attempts=3,
            initial_delay=2.0,  # Yahoo Finance対策で2秒に
            exponential_base=2.0,
            jitter=True,
        )
```

### 1.3 news-collection-config.yaml にリトライ設定追加

**ファイル**: `data/config/news-collection-config.yaml` (行40-42の後に追加)

```yaml
# RSS設定
rss:
  presets_file: "data/config/rss-presets.json"
  # 新規追加: リトライ設定
  retry:
    max_attempts: 3
    initial_delay_seconds: 2.0  # Yahoo Finance 429対策で2秒に
    max_delay_seconds: 30.0
    exponential_base: 2.0
    jitter: true
```

**設定モデル追加**: `src/news/config/models.py`

```python
@dataclass
class RSSRetryConfig:
    max_attempts: int = 3
    initial_delay_seconds: float = 2.0
    max_delay_seconds: float = 30.0
    exponential_base: float = 2.0
    jitter: bool = True
```

---

## Phase 2: 構造的改善（優先度: 中）

### 2.1 新規フィード追加（stock/sector/macro対応）

**ファイル**: `data/config/rss-presets.json`

以下のフィードを追加：

| カテゴリ | フィード | URL |
|----------|----------|-----|
| stock | Nasdaq Stock News | `https://www.nasdaq.com/feed/rssoutbound?category=stocks` |
| stock | Investopedia Stock News | `https://www.investopedia.com/feedbuilder/feed/getfeed?feedName=rss_headline` |
| macro | Federal Reserve Press | `https://www.federalreserve.gov/feeds/press_all.xml` |
| macro | CNBC Economy | `https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=20910258` |
| sector | ETF.com News | `https://www.etf.com/rss/news.xml` |

### 2.2 status_mapping 拡張

**ファイル**: `data/config/news-collection-config.yaml`

```yaml
status_mapping:
  # 既存
  tech: "ai"
  market: "index"
  finance: "finance"

  # 新規追加
  stock: "stock"
  sector: "sector"
  macro: "macro"
  economy: "macro"      # economyカテゴリもmacroにマップ
  earnings: "stock"     # 決算ニュースはstockにマップ
```

### 2.3 rss-presets.json の既存フィードカテゴリ再分類

一部のフィードを適切なカテゴリに再分類：

| フィード | 現在 | 変更後 | 行番号 |
|----------|------|--------|--------|
| CNBC - Economy | finance | macro | 96-101 |
| CNBC - Earnings | market | stock | 137-143 |
| CNBC - Energy | finance | sector | 180-185 |
| CNBC - Health Care | finance | sector | 151-157 |

**変更例**（CNBC - Economy）:
```json
{
  "url": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=20910258",
  "title": "CNBC - Economy",
  "category": "macro",  // finance → macro に変更
  "fetch_interval": "daily",
  "enabled": true
}
```

---

## Phase 3: 技術的改善（優先度: 低）

### 3.1 CNBC抽出失敗対策

**オプション A**: CNBC専用抽出ロジック追加
- `src/news/extractors/cnbc.py` を新規作成
- CNBC特有のDOM構造に対応したセレクタ

**オプション B**: Playwright フォールバックの強化
- 現在のPlaywrightフォールバックは実装済みだが、CNBC用の追加セレクタを定義
- `.ArticleBody-articleBody` などのCNBC固有クラスを追加

**推奨**: オプション B（既存実装の拡張で対応可能）

### 3.2 フィード健全性監視

**ファイル**: `src/news/monitoring.py` (新規)

```python
@dataclass
class FeedHealthMetrics:
    feed_url: str
    success_rate: float
    last_success: datetime | None
    consecutive_failures: int
    last_error: str | None
```

- 連続失敗カウントの追跡
- 失敗率の定期レポート
- 自動アラート（連続5回失敗でログ警告）

---

## 変更対象ファイル

| ファイル | 変更内容 |
|----------|----------|
| `data/config/rss-presets.json` | URL更新、新規フィード追加、カテゴリ再分類 |
| `data/config/news-collection-config.yaml` | リトライ設定追加、status_mapping拡張 |
| `src/news/collectors/rss.py` | リトライ機構追加 |
| `src/news/config/models.py` | RSSRetryConfig モデル追加 |
| `src/news/extractors/playwright.py` | CNBC用セレクタ追加（Phase 3） |

---

## 検証方法

### Phase 1 検証

```bash
# 1. MarketWatch フィードのテスト
curl -I "https://feeds.content.dowjones.io/public/rss/mw_topstories"

# 2. ワークフロー実行（dry-run）
python -m news.scripts.finance_news_workflow --dry-run --verbose

# 3. ログでリトライ動作を確認
grep -E "retry|Retrying" logs/news-workflow-*.log
```

### Phase 2 検証

```bash
# 1. 新規フィードの疎通確認
python -c "
import feedparser
feeds = [
    'https://www.nasdaq.com/feed/rssoutbound?category=stocks',
    'https://www.federalreserve.gov/feeds/press_all.xml',
]
for url in feeds:
    d = feedparser.parse(url)
    print(f'{url}: {len(d.entries)} entries')
"

# 2. status_mappingの動作確認
python -m news.scripts.finance_news_workflow --dry-run --status stock,macro

# 3. カテゴリ分布の確認
grep -o '"category": "[^"]*"' data/config/rss-presets.json | sort | uniq -c
```

### 全体検証

```bash
# 品質チェック
make check-all

# 統合テスト
uv run pytest tests/news/integration/ -v
```

---

## 実装順序

1. **Phase 1.1**: MarketWatch URL更新（5分）
2. **Phase 1.2-1.3**: リトライ機構追加（30分）
3. **Phase 2.1**: 新規フィード追加（15分）
4. **Phase 2.2-2.3**: status_mapping拡張 + カテゴリ再分類（15分）
5. **Phase 3**: CNBC対策（オプション、必要に応じて）

---

## リスクと対策

| リスク | 対策 |
|--------|------|
| 新規フィードURLが無効 | 事前にcurlでHTTPステータス確認 |
| リトライによる処理時間増加 | max_attemptsを3に制限、タイムアウト設定 |
| CNBC抽出率が改善しない | ブロックリストへの追加を検討 |

---

## 情報収集結果（実装前調査）

### 既存の監視・統計パターン

`src/news/core/history.py` に既存の統計収集フレームワークがある：

```python
# 使用可能なクラス
- SourceStats: success_count, error_count, article_count, success_rate
- SinkResult: success, error_message, metadata
- CollectionRun: started_at, completed_at, sources, sinks, duration_seconds
- CollectionHistory: runs管理、save/load、get_statistics()
```

**Phase 3.2の実装方針**:
- 新規 `monitoring.py` ではなく、既存の `history.py` パターンを拡張
- `FeedHealthMetrics` を `SourceStats` の拡張として実装検討

### FeedError モデル（既存）

`src/news/models.py:638-692` に既存の `FeedError` モデル：
- `feed_url`, `feed_name`, `error`, `error_type`, `timestamp`
- `WorkflowResult.feed_errors` として集約済み

### Playwright Extractor セレクタ

`src/news/extractors/playwright.py:96-104` の現在のセレクタ：

```python
_selectors: list[str] = [
    "article",
    "main",
    "[role='main']",
    ".article-body",
    ".post-content",
    "#content",
    "body",
]
```

**CNBC用に追加すべきセレクタ（Phase 3.1）**:
- `.ArticleBody-articleBody`
- `.RenderKeyPoints-list`
- `[data-module="ArticleBody"]`

### RSSリトライ機構の実装状況

**実装済み（途中で中断）**:
1. `RssRetryConfig` モデルを `config/models.py` に追加済み
2. `RssConfig.retry` フィールド追加済み
3. `rss.py` に `asyncio`, `random` インポート追加済み

**未実装**:
- `_fetch_feed` メソッドへのリトライロジック追加
- `news-collection-config.yaml` へのリトライ設定追加

### 変更済みファイル（要ロールバック確認）

| ファイル | 変更内容 |
|----------|----------|
| `data/config/rss-presets.json` | MarketWatch URL更新 |
| `src/news/config/models.py` | RssRetryConfig追加、RssConfig.retry追加 |
| `src/news/collectors/rss.py` | import追加（asyncio, random） |

### テストへの影響

**`tests/news/unit/collectors/test_rss.py`**:
- リトライ機構のテストは存在しない → **新規テスト追加が必要**
- 既存のfixtureは `RssConfig(presets_file=...)` のみでデフォルト値使用
- リトライ機能追加後も既存テストは通る（後方互換性あり）
- 追加が必要なテスト:
  - `test_正常系_リトライで成功する`
  - `test_正常系_最大リトライ回数で失敗する`
  - `test_正常系_指数バックオフが適用される`

**`tests/news/unit/config/test_models.py`**:
- `RssRetryConfig` のテストは存在しない → **新規テスト追加が必要**
- 追加が必要なテスト:
  - `test_正常系_デフォルト値で作成できる`
  - `test_正常系_カスタム値で作成できる`
  - `test_異常系_無効値でValidationError`

**`tests/news/unit/extractors/test_playwright.py`**:
- 現在のテストはセレクタ変更に影響なし（モックを使用）
- CNBC用セレクタ追加後もテストは通る

### status_mapping の現状

**`data/config/news-collection-config.yaml` (行9-24)**:

```yaml
status_mapping:
  # 現在のRSSカテゴリマッピング
  tech: "ai"
  market: "index"
  finance: "finance"

  # yfinanceカテゴリ（存在するが直接使用されない）
  yf_index: "index"
  yf_stock: "stock"
  yf_ai_stock: "ai"
  yf_sector_etf: "sector"
  yf_macro: "macro"
```

**問題点**: RSSの `category` フィールドから `stock`, `sector`, `macro` へ直接マップできるエントリがない。

**Phase 2.2で追加が必要**:
```yaml
# RSSカテゴリ追加
stock: "stock"       # 個別銘柄ニュース
sector: "sector"     # セクター分析
macro: "macro"       # マクロ経済
economy: "macro"     # 経済ニュースもmacroへ
earnings: "stock"    # 決算ニュースはstockへ
```

### カテゴリ再分類の詳細（Phase 2.3）

提案された4件の再分類:

| フィード | 現在行 | 変更前 | 変更後 | 理由 |
|----------|--------|--------|--------|------|
| CNBC - Economy | 96-101 | finance | macro | 経済指標・金融政策ニュース |
| CNBC - Earnings | 137-143 | market | stock | 企業決算ニュース |
| CNBC - Energy | 180-185 | finance | sector | エネルギーセクターETF関連 |
| CNBC - Health Care | 151-157 | finance | sector | ヘルスケアセクターETF関連 |

### 新規フィードURL検証状況

| フィード | URL | 検証結果 |
|----------|-----|----------|
| Nasdaq Stock News | `https://www.nasdaq.com/feed/rssoutbound?category=stocks` | **未検証** |
| Investopedia | `https://www.investopedia.com/feedbuilder/feed/getfeed?feedName=rss_headline` | **未検証** |
| Federal Reserve Press | `https://www.federalreserve.gov/feeds/press_all.xml` | ✅ 確認済み |
| CNBC Economy | `https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=20910258` | ✅ 既存利用中 |
| ETF.com News | `https://www.etf.com/rss/news.xml` | **未検証** |

**実装前に検証が必要なURL**: Nasdaq, Investopedia, ETF.com

---

## 期待効果

| Status | 現在 | 改善後（予想） |
|--------|------|---------------|
| index | 3件 | 10-15件 |
| stock | 0件 | 5-10件 |
| sector | 0件 | 3-5件 |
| macro | 0件 | 5-8件 |

---

## 実装時の注意事項

1. **リトライ機構**: `_fetch_feed` メソッド内で `self._config.rss.retry` を参照
2. **テスト追加**: Phase 1 完了後に `RssRetryConfig` と リトライ動作のテストを追加
3. **CNBC セレクタ**: 優先度順にリストに追加（`article` より前か後かで動作が変わる）
4. **status_mapping**: 既存のyfinance用マッピングとの重複に注意

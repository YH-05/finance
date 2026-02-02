# ニュースワークフロー改善実装計画

## 概要

`docs/news-workflow-analysis-2026-02-02.md` の分析結果に基づき、ニュースワークフローの改善を実施する。

## 調査結果サマリー（2026-02-02 追加調査）

### 重要な発見

**curlとPythonライブラリの挙動差異**:

| フィード | curl結果 | feedparser結果 | 結論 |
|----------|----------|---------------|------|
| CNBC（14/15本） | 403 Forbidden | **200 OK, 30件取得** | ✅ 問題なし |
| Yahoo Finance | 429 Too Many Requests | **200 OK, 48件取得** | ✅ 問題なし |
| Financial Times | 301 Redirect | **200 OK, 25件取得**（新URL） | ✅ URL更新で解決 |
| CNBC Markets | 403 | 200だが**0件** | ❌ フィードID無効 |

**結論**: ワークフローはPython（feedparser/trafilatura）で本文取得→Claude Code要約の順序で実装されているため、curlの403/429は問題にならない。

### ワークフロー実装確認

```
RSS Feed (feedparser)
  ↓ [Python]
Tier 1: trafilatura で本文取得
  ↓ [失敗時]
Tier 2: MCP Playwright で本文取得
  ↓ [失敗時]
Tier 3: RSS Summary フォールバック
  ↓ [成功時]
Claude Code: 本文をPromptに含めて要約生成
  ↓
GitHub Issue: 要約を本文に含める
```

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

### 問題のサマリー（優先度再評価）

| 問題 | 影響 | 優先度 | 備考 |
|------|------|--------|------|
| ~~MarketWatch URL変更~~ | ~~marketフィード1件失敗~~ | ~~高~~ | ✅ **解決済み** |
| Seeking Alpha ブロックドメイン | marketフィード1件スキップ | 情報 | 意図的なブロック |
| CNBC - Markets フィードID無効 | marketフィード1件失敗 | **高** | 0件を返す |
| Financial Times URL変更 | financeフィード1件失敗 | **高** | 新URLに更新必要 |
| stock/sector/macroカテゴリ不在 | 該当Status投稿0件 | 中 | 新規フィード追加 |
| ~~RSS収集層にリトライ設定なし~~ | ~~Yahoo Finance 429エラー~~ | ~~中~~ | ✅ **feedparserで動作** |
| CNBCコンテンツ抽出44%失敗 | 抽出成功率低下 | 低 | Playwright強化で対応 |

---

## Phase 1: 即時対応（優先度: 高）

### 1.1 CNBC - Markets フィード無効化

**ファイル**: `data/config/rss-presets.json` (行82-87)

フィードID `20907743` は無効（0件を返す）。無効化する。

```json
// 変更前
{
  "url": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=20907743",
  "title": "CNBC - Markets",
  "category": "market",
  "fetch_interval": "daily",
  "enabled": true
}

// 変更後
{
  "url": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=20907743",
  "title": "CNBC - Markets",
  "category": "market",
  "fetch_interval": "daily",
  "enabled": false  // フィードID無効のため
}
```

### 1.2 Financial Times URL更新

**ファイル**: `data/config/rss-presets.json` (行53-59)

```json
// 変更前
{
  "url": "https://www.ft.com/?format=rss",
  "title": "Financial Times",
  "category": "finance",
  "fetch_interval": "daily",
  "enabled": true
}

// 変更後
{
  "url": "https://www.ft.com/markets?format=rss",
  "title": "Financial Times - Markets",
  "category": "finance",
  "fetch_interval": "daily",
  "enabled": true
}
```

**検証結果**: feedparserで200 OK, 25件取得確認済み

---

## Phase 2: 構造的改善（優先度: 中）

### 2.1 新規フィード追加（stock/sector/macro対応）

**ファイル**: `data/config/rss-presets.json`

以下のフィードを追加（検証済み）：

| カテゴリ | フィード | URL | 検証結果 |
|----------|----------|-----|----------|
| stock | Nasdaq Stock News | `https://www.nasdaq.com/feed/rssoutbound?category=stocks` | ✅ 動作確認 |
| sector | Nasdaq ETFs | `https://www.nasdaq.com/feed/rssoutbound?category=etfs` | ✅ 動作確認 |
| market | Nasdaq Markets | `https://www.nasdaq.com/feed/rssoutbound?category=markets` | ✅ 動作確認 |
| market | Investing.com | `https://www.investing.com/rss/news_25.rss` | ✅ 動作確認 |
| macro | Federal Reserve Press | `https://www.federalreserve.gov/feeds/press_all.xml` | ✅ 動作確認 |

**除外したフィード（検証で失敗）**:
| フィード | URL | 理由 |
|----------|-----|------|
| ~~Investopedia~~ | `investopedia.com/feedbuilder/...` | 404 Not Found |
| ~~ETF.com~~ | `etf.com/rss/news.xml` | 403 Cloudflareブロック |

### 2.2 status_mapping 拡張

**ファイル**: `data/config/news-collection-config.yaml`

```yaml
status_mapping:
  # 既存
  tech: "ai"
  market: "index"
  finance: "finance"

  # 新規追加（RSSカテゴリ用）
  stock: "stock"
  sector: "sector"
  macro: "macro"
  economy: "macro"      # economyカテゴリもmacroにマップ
  earnings: "stock"     # 決算ニュースはstockにマップ
  etfs: "sector"        # ETFニュースはsectorにマップ
```

### 2.3 rss-presets.json の既存フィードカテゴリ再分類

一部のフィードを適切なカテゴリに再分類：

| フィード | 現在 | 変更後 | 行番号 | 理由 |
|----------|------|--------|--------|------|
| CNBC - Economy | finance | macro | 96-101 | 経済指標・金融政策 |
| CNBC - Earnings | market | stock | 137-143 | 企業決算 |
| CNBC - Energy | finance | sector | 180-185 | エネルギーセクター |
| CNBC - Health Care | finance | sector | 151-157 | ヘルスケアセクター |

---

## Phase 3: 技術的改善（優先度: 低）

### 3.1 CNBC抽出失敗対策（Playwrightセレクタ強化）

**ファイル**: `src/news/extractors/playwright.py`

現在のセレクタ（L96-104）に CNBC 用セレクタを追加：

```python
_selectors: list[str] = [
    # CNBC専用（優先度高）
    ".ArticleBody-articleBody",
    ".RenderKeyPoints-list",
    "[data-module='ArticleBody']",
    # 既存
    "article",
    "main",
    "[role='main']",
    ".article-body",
    ".post-content",
    "#content",
    "body",
]
```

### 3.2 リトライ機構追加（オプション）

**状態**: 設定モデルは実装済み、ロジック未実装

feedparser では 429/403 エラーが発生しないため、**優先度を「低」に変更**。
ただし、将来的な安定性向上のため実装を推奨。

**実装済み**:
- `RssRetryConfig` モデル（`config/models.py`）
- `RssConfig.retry` フィールド

**未実装**:
- `_fetch_feed` メソッドへのリトライロジック
- `news-collection-config.yaml` へのリトライ設定

---

## 変更対象ファイル

| ファイル | 変更内容 | Phase |
|----------|----------|-------|
| `data/config/rss-presets.json` | CNBC Markets無効化、FT URL更新、新規フィード追加、カテゴリ再分類 | 1, 2 |
| `data/config/news-collection-config.yaml` | status_mapping拡張 | 2 |
| `src/news/extractors/playwright.py` | CNBC用セレクタ追加 | 3 |

---

## 検証方法

### Phase 1 検証

```bash
# 1. 変更後のフィード動作確認
uv run python -c "
import feedparser

# CNBC Markets（無効化確認）
feed1 = feedparser.parse('https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=20907743')
print(f'CNBC Markets: {len(feed1.entries)} entries (should be 0)')

# Financial Times（新URL）
feed2 = feedparser.parse('https://www.ft.com/markets?format=rss')
print(f'FT Markets: {len(feed2.entries)} entries')
"
```

### Phase 2 検証

```bash
# 1. 新規フィードの疎通確認
uv run python -c "
import feedparser

feeds = [
    ('Nasdaq Stocks', 'https://www.nasdaq.com/feed/rssoutbound?category=stocks'),
    ('Nasdaq ETFs', 'https://www.nasdaq.com/feed/rssoutbound?category=etfs'),
    ('Nasdaq Markets', 'https://www.nasdaq.com/feed/rssoutbound?category=markets'),
    ('Investing.com', 'https://www.investing.com/rss/news_25.rss'),
    ('Federal Reserve', 'https://www.federalreserve.gov/feeds/press_all.xml'),
]
for name, url in feeds:
    d = feedparser.parse(url)
    print(f'{name}: {len(d.entries)} entries')
"

# 2. カテゴリ分布の確認
grep -o '"category": "[^"]*"' data/config/rss-presets.json | sort | uniq -c

# 3. ワークフロー実行（dry-run）
python -m news.scripts.finance_news_workflow --dry-run --verbose
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

1. **Phase 1.1**: CNBC Markets 無効化
2. **Phase 1.2**: Financial Times URL更新
3. **Phase 2.1**: 新規フィード追加（5本）
4. **Phase 2.2**: status_mapping 拡張
5. **Phase 2.3**: 既存フィードカテゴリ再分類
6. **Phase 3.1**: CNBC用Playwrightセレクタ追加（オプション）

---

## リスクと対策

| リスク | 対策 |
|--------|------|
| 新規フィードが将来無効化される | フィード健全性の定期確認（手動） |
| CNBC抽出率が改善しない | ブロックリストへの追加を検討 |
| Nasdaq が User-Agent 制限を強化 | feedparser のデフォルト User-Agent で動作確認済み |

---

## 期待効果

| Status | 現在 | 改善後（予想） |
|--------|------|---------------|
| index | 3件 | 10-15件 |
| stock | 0件 | 5-10件 |
| sector | 0件 | 3-5件 |
| macro | 0件 | 5-8件 |

---

## 補足: 調査で判明した事項

### feedparser vs curl の挙動差異

- **curl**: ブラウザ検出で 403/429 を返すサイトが多い
- **feedparser**: 適切な User-Agent を使用し、正常に取得可能
- **trafilatura**: 同様に適切なヘッダーで本文取得可能

### ワークフロー実装の確認結果

1. **RSS収集**: `src/news/collectors/rss.py` で feedparser 使用 ✅
2. **本文抽出**: `src/news/extractors/trafilatura.py` で3段階フォールバック ✅
3. **要約生成**: `src/news/processors/summarizer.py` で Claude Agent SDK 使用 ✅
4. **Issue作成**: `src/news/publisher.py` で gh CLI 使用 ✅

**結論**: Python本文取得 → Claude Code要約 の順序で正しく実装されている。

### 実装済み項目（変更不要）

| 項目 | 状態 |
|------|------|
| MarketWatch URL | ✅ 更新済み |
| RssRetryConfig モデル | ✅ 実装済み（ロジック未使用） |
| ドメインフィルタリング | ✅ 動作中 |
| Playwright フォールバック | ✅ 動作中 |
| User-Agent ローテーション | ✅ 設定済み |

---

## 実装時の注意事項

1. **feedparser検証**: 新規フィードは必ず feedparser で動作確認（curl不可）
2. **カテゴリ一貫性**: status_mapping と rss-presets.json のカテゴリ名を一致させる
3. **CNBC セレクタ順序**: 優先度の高いセレクタを先頭に配置

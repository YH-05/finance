# ニュースワークフロー分析レポート

**日付**: 2026-02-02
**ログファイル**: `logs/news-workflow-2026-02-02.log`

---

## 全体統計

| 項目 | 値 | 割合 |
|------|-----|------|
| 収集記事数 | 490 | 100% |
| 抽出成功 | 273 | 56% |
| 要約成功 | 169 | 35% |
| Issue作成 | 74 | 15% |
| 重複スキップ | 95 | 19% |

---

## 投稿カテゴリ分布

| カテゴリ | 投稿数 | ステータス |
|----------|--------|------------|
| ai | 34 | 正常 |
| finance | 37 | 正常 |
| **index** | **3** | 極端に少ない |
| **stock** | **0** | 投稿なし |
| **sector** | **0** | 投稿なし |
| **macro** | **0** | 投稿なし |

---

## 失敗パターン分類

### 1. フィード取得エラー (4/29フィード失敗)

| フィード | エラー | 根本原因 | 対策 |
|----------|--------|----------|------|
| MarketWatch Top Stories | `301 Moved Permanently` | URL変更 | `https://feeds.content.dowjones.io/public/rss/mw_topstories` に更新 |
| Yahoo Finance | `429 Too Many Requests` | レート制限 | リトライ間隔の追加 |
| Financial Times | `301 Moved Permanently` | URL変更 | 新URLの調査・更新 |
| CNBC - Markets | `Invalid feed format` | フィード形式変更/アンチボット | フィードURL確認・代替検討 |

### 2. コンテンツ抽出エラー (217件)

| エラー種別 | 件数 | 主な原因 |
|------------|------|----------|
| Body text too short | 216 | CNBC等のアンチスクレイピング |
| Insufficient content | 1 | コンテンツ不足 |
| Paywall検出 | 10 | ペイウォール |

**影響**: 抽出失敗率 44%（217/490）

### 3. ブロックドメイン (意図的スキップ)

`seekingalpha.com` からの約40記事が設定により `Blocked domain article skipped` でスキップ

---

## 根本原因分析: index/stock投稿が少ない理由

### 原因1: RSSカテゴリマッピングの不備

`rss-presets.json` のカテゴリ分布:

| カテゴリ | フィード数 | 対応Status | 備考 |
|----------|------------|------------|------|
| tech | 5 | ai | 正常 |
| market | 5 | index | 3/5が壊れている |
| finance | 19 | finance | 正常 |
| **stock** | **0** | - | カテゴリが存在しない |
| **sector** | **0** | - | カテゴリが存在しない |
| **macro** | **0** | - | カテゴリが存在しない |

### 原因2: marketカテゴリのフィードが壊滅状態

5件中3件が失敗:

| フィード | ステータス | 問題 |
|----------|------------|------|
| MarketWatch | 失敗 | URL変更で301エラー |
| Seeking Alpha | 失敗 | ブロックドメイン |
| CNBC - Markets | 失敗 | フィード形式エラー |
| CNBC - Investing | 動作 | - |
| CNBC - Earnings | 動作 | - |

### 原因3: CNBCコンテンツ抽出の高失敗率

Playwright fallbackを有効にしても、CNBCの記事本文抽出が44%失敗

- 原因: アンチスクレイピング対策
- 症状: `Body text too short or empty`

---

## 推奨改善策

### 即時対応（優先度: 高）

#### 1. MarketWatch URL更新

```json
// data/config/rss-presets.json
{
    "url": "https://feeds.content.dowjones.io/public/rss/mw_topstories",
    "title": "MarketWatch Top Stories",
    "category": "market",
    "fetch_interval": "daily",
    "enabled": true
}
```

#### 2. CNBC - Markets フィードURL確認

現在のURL `https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=20907743` が `Invalid feed format` を返すため、代替URLまたは新しいフィードIDを調査

#### 3. Yahoo Finance対策

`news-collection-config.yaml` にリトライ間隔を追加:

```yaml
rss:
  retry_delay_seconds: 2  # リクエスト間の遅延
  max_retries: 3
```

### 構造的改善（優先度: 中）

#### 1. stock/sector/macroカテゴリの追加

現在のRSSプリセットには個別株、セクター分析、マクロ経済のカテゴリがない。以下のフィード追加を検討:

**個別株 (stock)**:
- CNBC - Stocks to Watch
- Investopedia Stock News

**セクター分析 (sector)**:
- セクター別ETFニュース
- S&P Sector Indices

**マクロ経済 (macro)**:
- Fed RSS
- 経済指標ニュース

#### 2. status_mapping拡張

```yaml
# data/config/news-collection-config.yaml
status_mapping:
  # 既存
  tech: "ai"
  market: "index"
  finance: "finance"

  # 新規追加
  earnings: "stock"      # 決算ニュース → stock
  economy: "macro"       # 経済ニュース → macro
  sector: "sector"       # セクター分析
  stocks: "stock"        # 個別株ニュース
```

#### 3. 代替フィードの検討

| カテゴリ | 候補フィード | URL |
|----------|--------------|-----|
| index | Investopedia Markets | 要調査 |
| stock | Nasdaq Stock News | https://www.nasdaq.com/feed/rssoutbound |
| macro | Federal Reserve | https://www.federalreserve.gov/feeds/press_all.xml |

### 技術的改善（優先度: 低）

#### 1. CNBC抽出改善

- カスタム抽出ロジックの実装
- API経由でのコンテンツ取得検討

#### 2. 監視・アラート

- フィード取得失敗の自動検知
- カテゴリ分布の定期レポート

---

## 次のアクション

1. [ ] MarketWatch URLを新URLに更新
2. [ ] CNBC - MarketsフィードのURL調査
3. [ ] stock/sector/macroカテゴリのフィード追加
4. [ ] status_mapping拡張
5. [ ] Yahoo Financeのレート制限対策

---

## 関連ファイル

| ファイル | 説明 |
|----------|------|
| `data/config/news-collection-config.yaml` | ワークフロー設定 |
| `data/config/rss-presets.json` | RSSフィードプリセット |
| `src/news/publisher.py` | カテゴリ→Status変換ロジック |
| `src/news/collectors/rss.py` | RSS収集ロジック |

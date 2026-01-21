---
summary: "NASDAQ RSS記事の全文取得にはGemini searchを使用する（WebFetch/mcp fetchはブロックされる）"
created: 2026-01-19
tags: [rss, nasdaq, gemini-search, web-scraping]
related: [data/raw/rss/feeds.json]
---

# NASDAQ RSS記事の取得方法

## 問題

NASDAQサイトはボット対策（Cloudflare等のWAF）を実装しており、以下のツールでの記事取得が失敗する：

- `WebFetch` → タイムアウト/キャンセル
- `mcp__fetch__fetch` → `Failed to fetch robots.txt due to a connection issue`

## 解決策

**Gemini search**を使用して記事内容を取得する。

```bash
gemini --prompt 'WebSearch: <記事タイトル> <著者名>'
```

### 例

```bash
gemini --prompt 'WebSearch: NASDAQ Weekly Chartstopper January 16 2026 Michael Normyle'
```

## RSSフィード自体は正常

- RSSフィードの取得（`mcp__rss__rss_fetch_feed`）は成功する
- RSSは機械読み取りを前提として公開されているため、ボット対策の対象外
- `title`, `link`, `published`, `summary`, `author` は取得可能
- `content` フィールドは通常 `null`

## NASDAQフィード一覧

登録済みのNASDAQ RSSフィード（2026-01-19追加）：

| タイトル | カテゴリ |
|---------|---------|
| NASDAQ Original | market |
| NASDAQ ETFs | market |
| NASDAQ Markets | market |
| NASDAQ Options | market |
| NASDAQ Stocks | market |
| NASDAQ AI | tech |
| NASDAQ Financial Advisors | finance |
| NASDAQ FinTech | tech |
| NASDAQ Innovation | tech |
| NASDAQ Technology | tech |

## 注意

- AI/Technology関連の記事（Investing News Network提供）はRSSのsummaryにほぼ全文が含まれる場合がある
- NASDAQ Original等はsummaryが短いため、全文取得にはGemini searchが必要

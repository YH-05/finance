# 既存リサーチ系エージェント調査レポート

**作成日**: 2026-01-14
**Issue**: #47 既存リサーチ系エージェントの調査

## 調査対象

| エージェント | 目的 | Phase |
|-------------|------|-------|
| finance-web | Web検索で金融情報を収集 | 2 |
| finance-wiki | Wikipediaから背景情報を収集 | 2 |
| finance-source | raw-dataから情報源を整理 | 3 |

## 各エージェントの入出力形式

### finance-web

| 項目 | 内容 |
|------|------|
| **入力** | `queries.json` (web_search クエリ) |
| **出力** | `raw-data.json` |
| **依存** | finance-query-generator |
| **ツール** | WebSearch |

**出力スキーマ**:
```json
{
    "article_id": "<記事ID>",
    "collected_at": "ISO8601形式",
    "sources": {
        "web_search": [
            {
                "source_id": "W001",
                "query_id": "Q010",
                "url": "https://...",
                "title": "記事タイトル",
                "snippet": "概要テキスト",
                "source_name": "Bloomberg",
                "published_date": "2025-01-10",
                "reliability": "high | medium | low",
                "relevance": "high | medium | low"
            }
        ]
    }
}
```

### finance-wiki

| 項目 | 内容 |
|------|------|
| **入力** | `queries.json` (wikipedia クエリ) |
| **出力** | `raw-data.json` |
| **依存** | finance-query-generator |
| **ツール** | Wikipedia MCP |

**MCPツール一覧**:
- `mcp__wikipedia__search_wikipedia` - キーワード検索
- `mcp__wikipedia__get_article` - 記事全文取得
- `mcp__wikipedia__get_summary` - 要約取得
- `mcp__wikipedia__get_sections` - セクション構造取得
- `mcp__wikipedia__extract_key_facts` - 重要事実の抽出

**出力スキーマ**:
```json
{
    "article_id": "<記事ID>",
    "collected_at": "ISO8601形式",
    "sources": {
        "wikipedia": [
            {
                "source_id": "WK001",
                "query_id": "Q001",
                "title": "記事タイトル",
                "lang": "ja | en",
                "url": "https://...",
                "summary": "要約テキスト",
                "key_facts": [...],
                "sections": [...],
                "related_topics": [...],
                "reliability": "high"
            }
        ]
    }
}
```

### finance-source

| 項目 | 内容 |
|------|------|
| **入力** | `raw-data.json` |
| **出力** | `sources.json`, `article-meta.json` (tags更新) |
| **依存** | finance-web, finance-wiki, finance-market-data |
| **ツール** | なし（データ変換のみ） |

**出力スキーマ**:
```json
{
    "article_id": "<記事ID>",
    "generated_at": "ISO8601形式",
    "sources": [
        {
            "source_id": "S001",
            "original_id": "W001 | WK001 | MD001",
            "type": "official | news | analysis | data | reference | opinion",
            "title": "...",
            "url": "...",
            "reliability": "high | medium | low",
            "relevance": "high | medium | low",
            "content_summary": "...",
            "key_data": [...]
        }
    ],
    "statistics": {
        "total_sources": 15,
        "by_reliability": {...},
        "by_type": {...}
    }
}
```

## MCPツールの使い方

### Wikipedia MCP

```
# 検索
mcp__wikipedia__search_wikipedia: "検索キーワード"

# 記事取得
mcp__wikipedia__get_article: "記事タイトル"

# 要約取得
mcp__wikipedia__get_summary: "記事タイトル"

# 重要事実抽出
mcp__wikipedia__extract_key_facts: "記事タイトル"
```

### WebSearch

```
# 日本語クエリ
WebSearch: "米国株 週間レビュー 2025年1月"

# 英語クエリ
WebSearch: "S&P 500 weekly analysis January 2025"

# サイト指定クエリ
WebSearch: "site:bloomberg.com US stock market weekly"
```

## 共通パターン

### 1. エージェント定義ファイル構造（YAMLフロントマター）

```yaml
---
name: エージェント名
description: 説明
input: 入力ファイル
output: 出力ファイル
model: inherit
color: カラー
depends_on: [依存エージェント]
phase: フェーズ番号
priority: high | medium | low
---
```

### 2. 処理フロー

全エージェントで共通のフローパターン:

```
1. 入力ファイルの読み込み
2. 並列処理の実行（可能な場合）
3. 結果の整理・構造化
4. 出力ファイルへの書き込み
```

### 3. 信頼度・関連度の判定基準

**信頼度（reliability）**:
| レベル | 条件 |
|--------|------|
| high | 公式IR、大手金融メディア、政府機関、SEC EDGAR、取引所公式 |
| medium | ニュースサイト、アナリストレポート、Yahoo Finance、Wikipedia |
| low | 個人ブログ、SNS、掲示板、不明なソース |

**関連度（relevance）**:
| レベル | 条件 |
|--------|------|
| high | トピックに直接関連、最新情報 |
| medium | 背景情報、関連トピック |
| low | 間接的な関連のみ |

### 4. エラーハンドリングパターン

```
### E00X: エラー名

**発生条件**:
- 条件1
- 条件2

**対処法**:
1. 対処法1
2. 対処法2
```

主なエラーコード:
- **E002**: 入力ファイルエラー（ファイルが存在しない/空）
- **E004**: 外部サービスエラー（検索エラー、MCP接続エラー）

### 5. 重要ルール（共通）

- JSON 以外を一切出力しない
- 並列実行を最大限活用（処理時間削減）
- 信頼性の高いソースを優先
- 重複を除去

## 画像収集エージェントへの適用指針

上記の共通パターンを踏まえ、画像収集エージェントは以下の構造で実装すべき:

### 推奨構造

```yaml
---
name: finance-image
description: 金融記事用の画像を収集するエージェント
input: article-meta.json または queries.json
output: images.json (画像URLリスト)
model: inherit
color: purple
depends_on: [finance-query-generator]
phase: 2
priority: medium
---
```

### 出力スキーマ案

```json
{
    "article_id": "<記事ID>",
    "collected_at": "ISO8601形式",
    "images": [
        {
            "image_id": "IMG001",
            "url": "https://...",
            "alt_text": "画像の説明",
            "source_name": "Unsplash",
            "license": "CC0 | CC-BY | Editorial",
            "dimensions": {"width": 1920, "height": 1080},
            "relevance": "high | medium | low"
        }
    ]
}
```

### 使用可能なツール

- **WebSearch**: 画像検索クエリ
- **WebFetch**: 特定サイトからの画像情報取得
- **MCP**: 必要に応じて追加

---

**調査完了日**: 2026-01-14

# 画像収集エージェント使用ガイド

**エージェント名**: research-image-collector
**最終更新**: 2026-01-14

## 概要

`research-image-collector` は、note記事用の画像を収集し `images.json` を生成するエージェントです。フリー素材サイト（Unsplash、Pexels、Pixabay）を優先的に検索し、ライセンスを自動チェックして安全に使用できる画像を収集します。

### 主な機能

- 記事メタデータからの画像検索クエリ自動生成
- 複数のフリー素材サイトへの並列検索
- ライセンス自動判定（承認/要確認/却下）
- 画像メタデータの構造化出力

## 基本的な使い方

### 1. 前提条件

記事ワークスペースに `article-meta.json` が存在する必要があります。

```
articles/{category}_{id}_{slug}/
└── article-meta.json  # 必須
```

### 2. エージェントの呼び出し

Task ツールを使用してエージェントを起動します：

```
Task tool:
  subagent_type: research-image-collector
  prompt: "articles/mr_001_weekly_review/article-meta.json を読み込み、画像を収集してください"
```

### 3. 出力確認

エージェント実行後、以下のファイルが生成されます：

```
articles/{category}_{id}_{slug}/
└── 01_research/
    └── images/
        ├── images.json          # 収集結果
        ├── collected/           # 収集画像メタデータ
        └── generated/           # 自前生成画像
```

## 入力形式

### article-meta.json の必須フィールド

```json
{
    "article_id": "mr_001_weekly_review",
    "topic": "米国株週間レビュー",
    "keywords": ["S&P500", "NASDAQ", "決算"],
    "category": "market_report"
}
```

| フィールド | 型 | 説明 |
|-----------|------|------|
| article_id | string | 記事の一意識別子 |
| topic | string | 記事のトピック（画像検索キーワード生成に使用） |
| keywords | string[] | キーワードリスト（検索クエリ生成に使用） |
| category | string | 記事カテゴリ |

## 出力形式

### images.json スキーマ

```json
{
    "article_id": "mr_001_weekly_review",
    "collected_at": "2026-01-14T12:00:00Z",
    "images": [
        {
            "image_id": "IMG001",
            "type": "collected",
            "url": "https://unsplash.com/photos/xxx",
            "download_url": "https://images.unsplash.com/xxx",
            "local_path": null,
            "alt_text": "Stock market trading floor",
            "source_name": "Unsplash",
            "photographer": "John Doe",
            "license": {
                "type": "Unsplash License",
                "commercial_use": true,
                "attribution_required": false,
                "url": "https://unsplash.com/license"
            },
            "dimensions": {
                "width": 1920,
                "height": 1080
            },
            "file_format": "JPEG",
            "relevance": "high",
            "usage_status": "approved"
        }
    ],
    "statistics": {
        "total": 5,
        "by_type": {
            "collected": 3,
            "generated": 2
        },
        "by_license": {
            "free": 4,
            "editorial": 1
        },
        "by_status": {
            "approved": 4,
            "pending_review": 1,
            "rejected": 0
        }
    }
}
```

### 画像オブジェクトのフィールド

| フィールド | 型 | 説明 |
|-----------|------|------|
| image_id | string | 画像の一意識別子（IMG001形式） |
| type | string | `collected`（収集）または `generated`（自前生成） |
| url | string | 画像の元URL |
| download_url | string | ダウンロード用URL |
| local_path | string/null | ローカル保存パス（ダウンロード時） |
| alt_text | string | 代替テキスト |
| source_name | string | ソースサイト名 |
| photographer | string | 撮影者名（判明している場合） |
| license | object | ライセンス情報 |
| dimensions | object | 画像サイズ（width, height） |
| file_format | string | ファイル形式（JPEG, PNG, SVG） |
| relevance | string | 関連度（high, medium, low） |
| usage_status | string | 使用可否（approved, pending_review, rejected） |

### usage_status の意味

| ステータス | 説明 | 対応 |
|-----------|------|------|
| approved | 使用可能 | そのまま記事に使用可 |
| pending_review | 手動確認必要 | ライセンスを確認後に判断 |
| rejected | 使用不可 | 使用しない |

## 対象画像ソース

### 優先度: 高（フリー素材）

| サイト | ライセンス | 商用利用 | 帰属表示 |
|--------|-----------|---------|---------|
| Unsplash | Unsplash License | OK | 不要 |
| Pexels | Pexels License | OK | 不要 |
| Pixabay | Pixabay License | OK | 不要 |

### 優先度: 高（自前生成）

| ツール | 用途 |
|--------|------|
| market_analysis.visualization | 株価チャート・分析グラフ |
| matplotlib / plotly | カスタムチャート |

### 優先度: 中（公式ソース）

| サイト | ライセンス | 用途 |
|--------|-----------|------|
| TradingView | 埋め込み許可 | チャート埋め込み |
| SEC EDGAR | Public Domain | IR資料・財務データ |
| FRED | Public Domain | 経済指標チャート |

## MCPツールの使用

エージェントは以下のMCPツールを活用します：

### Fetch MCP

```
mcp__fetch__fetch: Webコンテンツ取得
```

フリー素材サイトから画像情報を取得する際に使用します。

### SEC EDGAR MCP

```
mcp__sec-edgar-mcp__get_company_info    # 企業情報取得
mcp__sec-edgar-mcp__get_recent_filings  # 最新提出書類取得
```

企業のIR資料から公式画像を取得する際に使用します。

### Reddit MCP

```
mcp__reddit__get_subreddit_hot_posts    # 人気投稿取得
mcp__reddit__get_post_content           # 投稿内容取得
```

市場センチメント関連の画像を探す際に使用します。

## 実行例

### 例1: 週間市場レポート用の画像収集

**入力: article-meta.json**

```json
{
    "article_id": "mr_001_weekly_review",
    "topic": "米国株週間レビュー：S&P500が過去最高値更新",
    "keywords": ["S&P500", "NASDAQ", "テック株", "決算"],
    "category": "market_report"
}
```

**実行**

```
Task tool:
  subagent_type: research-image-collector
  prompt: |
    articles/market_report_001_weekly_review/article-meta.json を読み込み、
    記事用の画像を収集してください。
    - フリー素材サイトから3-5枚
    - 株価チャートの自前生成を1-2枚
```

**出力: images.json（抜粋）**

```json
{
    "article_id": "mr_001_weekly_review",
    "collected_at": "2026-01-14T12:00:00Z",
    "images": [
        {
            "image_id": "IMG001",
            "type": "collected",
            "url": "https://unsplash.com/photos/stock-market",
            "alt_text": "Stock market trading floor with digital displays",
            "source_name": "Unsplash",
            "license": {
                "type": "Unsplash License",
                "commercial_use": true,
                "attribution_required": false
            },
            "relevance": "high",
            "usage_status": "approved"
        },
        {
            "image_id": "IMG002",
            "type": "generated",
            "local_path": "generated/chart_sp500_weekly.png",
            "alt_text": "S&P 500 週間チャート（2026年1月第2週）",
            "source_name": "market_analysis",
            "license": {
                "type": "Original",
                "commercial_use": true,
                "attribution_required": false
            },
            "relevance": "high",
            "usage_status": "approved"
        }
    ],
    "statistics": {
        "total": 5,
        "by_type": { "collected": 3, "generated": 2 },
        "by_status": { "approved": 5, "pending_review": 0 }
    }
}
```

### 例2: 個別銘柄分析用の画像収集

**入力: article-meta.json**

```json
{
    "article_id": "sa_001_apple_analysis",
    "topic": "Apple決算分析：AIへの投資拡大",
    "keywords": ["Apple", "AAPL", "iPhone", "AI", "決算"],
    "category": "stock_analysis"
}
```

**実行**

```
Task tool:
  subagent_type: research-image-collector
  prompt: |
    articles/stock_analysis_001_apple/article-meta.json を読み込み、
    Apple決算分析記事用の画像を収集してください。
    SEC EDGARからIR資料の画像も取得してください。
```

### 例3: 経済指標解説用の画像収集

**実行**

```
Task tool:
  subagent_type: research-image-collector
  prompt: |
    articles/economic_indicators_001_cpi/article-meta.json を読み込み、
    CPI解説記事用の画像を収集してください。
    FREDからの経済指標チャートを優先してください。
```

## トラブルシューティング

### E001: 画像検索エラー

**症状**: 画像検索結果が0件、またはネットワークエラー

**原因**:
- ネットワーク接続の問題
- サイトによるアクセスブロック
- 検索クエリが適切でない

**対処法**:
1. ネットワーク接続を確認
2. 別のフリー素材サイトで検索を試行
3. 検索クエリを調整（英語キーワードを使用）
4. 自前生成（market_analysis）を優先使用

### E002: ライセンス不明

**症状**: `usage_status: "pending_review"` の画像が多い

**原因**:
- ライセンス情報がページから取得できない
- 既知のライセンスタイプに一致しない

**対処法**:
1. 手動でライセンスページを確認
2. 確認後、images.json の `usage_status` を更新
3. 不明な場合は使用を避け、フリー素材サイトの画像を使用

### E003: 画像メタデータ取得失敗

**症状**: `dimensions: null` など一部情報が欠損

**原因**:
- 画像ページの構造変更
- JavaScript レンダリングが必要なページ

**対処法**:
1. 可能な範囲のメタデータで進める（必須項目が揃っていれば使用可）
2. 手動で情報を補完
3. 別の画像を選択

### E004: 自前生成の失敗

**症状**: チャート画像が生成されない

**原因**:
- market_analysis パッケージのエラー
- データ取得の失敗

**対処法**:
1. データソース（yfinance等）の接続を確認
2. エラーログを確認して原因特定
3. 手動でチャートを生成

### E005: 著作権リスクのある画像

**症状**: `usage_status: "rejected"` の画像

**原因**:
- Rights Reserved ライセンス
- ウォーターマーク付き画像の検出
- 企業ロゴの無断使用検出

**対処法**:
1. **絶対に使用しない**
2. フリー素材サイトから代替画像を検索
3. 自前でチャートやグラフを生成

## ライセンス確認チェックリスト

画像使用前に以下を確認してください：

- [ ] `usage_status` が `approved` である
- [ ] `attribution_required` が `true` の場合、出典を記載する準備ができている
- [ ] Editorial ライセンスの画像は報道・教育目的での使用に限定している
- [ ] ウォーターマークが付いていない
- [ ] 人物写真の場合、モデルリリースがあることを確認

## 帰属表示テンプレート

`attribution_required: true` の画像を使用する場合：

```markdown
## 画像クレジット

- [画像タイトル](画像URL) by [作者名](作者URL) / [ライセンス](ライセンスURL)
```

**例**:

```markdown
## 画像クレジット

- [Stock Trading Analysis](https://example.com/img) by John Doe / CC-BY 4.0
```

## 関連ドキュメント

- [要件定義書](./project/image-collection-requirements.md)
- [計画書](./project/research-agent.md)
- [エージェント定義](./.claude/agents/research-image-collector.md)

---

**Issue**: #51
**関連Issue**: #49（エージェント定義ファイル作成）

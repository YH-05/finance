# 画像収集要件定義書

**作成日**: 2026-01-14
**Issue**: #48 画像収集の要件定義
**ステータス**: 確定

## 概要

note記事用の画像収集機能について、対象サイト、収集フロー、保存構成、ライセンス確認ルールを定義する。

## 1. 対象サイトリスト

### 1.1 フリー素材サイト（優先度: 高）

| サイト名 | URL | ライセンス | 用途 |
|----------|-----|-----------|------|
| Unsplash | https://unsplash.com | Unsplash License | 写真・背景 |
| Pexels | https://www.pexels.com | Pexels License | 写真・イラスト |
| Pixabay | https://pixabay.com | Pixabay License | 写真・ベクター |

### 1.2 金融データソース（優先度: 高）

| サイト名 | URL | ライセンス | 用途 |
|----------|-----|-----------|------|
| TradingView | https://www.tradingview.com | 埋め込み許可 | チャート埋め込み |
| Yahoo Finance | https://finance.yahoo.com | Editorial | 参考データ |

### 1.3 公式ソース（優先度: 中）

| サイト名 | URL | ライセンス | 用途 |
|----------|-----|-----------|------|
| SEC EDGAR | https://www.sec.gov/edgar | Public Domain | IR資料・財務データ |
| 企業IR | 各社公式サイト | Editorial / 要確認 | ロゴ・IR画像 |
| FRED | https://fred.stlouisfed.org | Public Domain | 経済指標チャート |

### 1.4 自前生成（優先度: 高）

| ツール | 用途 |
|--------|------|
| market_analysis.visualization | 株価チャート・分析グラフ |
| matplotlib / plotly | カスタムチャート |

## 2. 画像収集フロー

### 2.1 フロー図

```
┌─────────────────┐
│  article-meta   │  記事メタデータ
│    .json        │  (トピック、キーワード)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  クエリ生成     │  画像検索用クエリ作成
│  (keywords →    │
│   image query)  │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│         並列画像検索                      │
├──────────┬──────────┬──────────┬─────────┤
│ Unsplash │ Pexels   │ Pixabay  │ 自前   │
│ API/Web  │ API/Web  │ API/Web  │ 生成   │
└──────────┴──────────┴──────────┴─────────┘
         │
         ▼
┌─────────────────┐
│  メタデータ     │  URL, サイズ, ALT,
│  収集           │  ライセンス情報
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  ライセンス     │  利用可否判定
│  チェック       │  (自動 + 手動確認)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  images.json    │  収集結果保存
│  出力           │
└─────────────────┘
```

### 2.2 処理ステップ詳細

#### Step 1: クエリ生成

```
入力: article-meta.json
  - topic: "米国株週間レビュー"
  - keywords: ["S&P500", "NASDAQ", "決算"]

出力: 画像検索クエリ
  - "stock market chart"
  - "S&P 500 trading"
  - "financial analysis graph"
```

#### Step 2: 画像検索

- **WebSearch**: `"stock market" site:unsplash.com`
- **WebFetch**: 検索結果ページから画像URLを抽出
- **自前生成**: market_analysis で株価チャート生成

#### Step 3: メタデータ収集

各画像について以下を取得:
- `url`: 画像URL
- `alt_text`: 代替テキスト
- `source_name`: ソースサイト名
- `license`: ライセンス種別
- `dimensions`: 幅 x 高さ
- `file_format`: PNG / JPEG / SVG

#### Step 4: ライセンスチェック

- 自動判定: ソースサイトごとのデフォルトライセンス適用
- 手動確認: Editorial / 要確認フラグの画像はレビュー必須

## 3. 保存ディレクトリ構成

### 3.1 記事ごとの画像

```
articles/
└── {category}_{id}_{slug}/
    └── 01_research/
        └── images/
            ├── images.json          # 画像メタデータ
            ├── collected/           # 収集画像（参照用URL）
            │   └── IMG001_unsplash.json
            └── generated/           # 自前生成画像
                ├── chart_sp500.png
                └── chart_nasdaq.png
```

### 3.2 images.json スキーマ

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
        },
        {
            "image_id": "IMG002",
            "type": "generated",
            "local_path": "generated/chart_sp500.png",
            "alt_text": "S&P 500 Weekly Chart",
            "source_name": "market_analysis",
            "license": {
                "type": "Original",
                "commercial_use": true,
                "attribution_required": false
            },
            "dimensions": {
                "width": 1200,
                "height": 800
            },
            "file_format": "PNG",
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
            "pending_review": 1
        }
    }
}
```

## 4. ライセンス確認ルール

### 4.1 ライセンス種別と利用可否

| ライセンス | 商用利用 | 帰属表示 | note記事 | 備考 |
|-----------|---------|---------|---------|------|
| CC0 / Public Domain | OK | 不要 | **使用可** | 最も安全 |
| Unsplash License | OK | 不要 | **使用可** | 推奨 |
| Pexels License | OK | 不要 | **使用可** | 推奨 |
| Pixabay License | OK | 不要 | **使用可** | 推奨 |
| CC-BY | OK | **必要** | **使用可** | 出典記載必須 |
| CC-BY-SA | OK | **必要** | **使用可** | 派生作品も同ライセンス |
| CC-BY-NC | NG | **必要** | **要確認** | 非商用のみ |
| Editorial | 限定 | **必要** | **要確認** | 報道・教育目的のみ |
| Rights Reserved | NG | - | **使用不可** | 許諾が必要 |

### 4.2 自動判定ルール

```python
def check_license(image: dict) -> str:
    """
    Returns
    -------
    str
        "approved" | "pending_review" | "rejected"
    """
    license_type = image["license"]["type"].lower()

    # 自動承認
    auto_approved = [
        "cc0", "public domain",
        "unsplash license", "pexels license", "pixabay license",
        "original"  # 自前生成
    ]
    if any(l in license_type for l in auto_approved):
        return "approved"

    # 帰属表示必要（出典記載で承認）
    attribution_required = ["cc-by", "cc-by-sa"]
    if any(l in license_type for l in attribution_required):
        return "approved"  # 出典記載フラグを立てる

    # 手動確認必要
    manual_review = ["editorial", "cc-by-nc", "unknown"]
    if any(l in license_type for l in manual_review):
        return "pending_review"

    # その他は拒否
    return "rejected"
```

### 4.3 帰属表示テンプレート

CC-BY等で帰属表示が必要な場合:

```markdown
<!-- 記事末尾に追加 -->
## 画像クレジット

- [画像タイトル](画像URL) by [作者名](作者URL) / [ライセンス](ライセンスURL)
```

例:
```markdown
- [Stock Trading](https://example.com/img) by John Doe / CC-BY 4.0
```

### 4.4 禁止事項

以下の使用は禁止:

1. **Rights Reserved 画像**: 明示的な許諾なし
2. **ウォーターマーク付き画像**: 有料素材の無断使用
3. **他者の著作物のスクリーンショット**: 著作権侵害リスク
4. **人物写真（Editorial）**: 商用利用での肖像権問題
5. **企業ロゴ（無断）**: 商標権侵害リスク

### 4.5 安全な画像収集チェックリスト

- [ ] フリー素材サイト（Unsplash/Pexels/Pixabay）を優先使用
- [ ] 自前生成チャートを積極活用
- [ ] ライセンス種別を必ず記録
- [ ] Editorial画像は使用前に確認
- [ ] 帰属表示が必要な画像は出典を明記
- [ ] 不明な場合は使用しない

---

## 次のステップ

1. この要件に基づき、`finance-image` エージェントを実装
2. Unsplash/Pexels/Pixabay API の調査（API キー取得方法）
3. market_analysis との連携方法を検討

---

**承認**: 要件定義完了
**最終更新**: 2026-01-14

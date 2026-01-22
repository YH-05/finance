# テーマフィルタリングパターン

特定のテーマに絞ってニュースを収集するパターンです。

## 対応テーマ一覧

| テーマID | 名前 | GitHub Status | 対象内容 |
|---------|------|---------------|----------|
| index | Index | 株価指数 | 日経平均、TOPIX、S&P500、ETF |
| stock | Stock | 個別銘柄 | 決算発表、企業ニュース |
| sector | Sector | 業界動向 | 半導体、自動車、金融 |
| macro | Macro Economics | マクロ経済 | 金融政策、経済指標、中央銀行 |
| ai | AI | AI技術 | AI企業、技術動向 |
| finance | Finance | 企業財務 | M&A、資金調達、金融商品 |

## 単一テーマの収集

### 株価指数ニュースのみ

```bash
/collect-finance-news --themes "index"
```

### 期待される出力

```
================================================================================
                    /collect-finance-news 開始
================================================================================

## 設定確認
- 対象テーマ: index（株価指数）
- 期間: 過去24時間

## Phase 3: テーマ別収集
| テーマ | 取得件数 | 投稿件数 | 重複 |
|--------|---------|---------|------|
| Index | 8 | 6 | 2 |

## Phase 4: 結果報告
- 総投稿数: 6件
- スキップ済みテーマ: Stock, Sector, Macro Economics, AI, Finance

================================================================================
                    /collect-finance-news 完了
================================================================================
```

### マクロ経済ニュースのみ

```bash
/collect-finance-news --themes "macro"
```

FOMC、日銀金融政策決定会合、雇用統計など重要イベント時に有用です。

### AI関連ニュースのみ

```bash
/collect-finance-news --themes "ai"
```

AI企業の決算発表や技術動向を追跡する際に使用します。

## 複数テーマの指定

### 市場全体の動向（指数 + マクロ）

```bash
/collect-finance-news --themes "index,macro"
```

市場全体の方向性を把握する際に有用です。

### 期待される出力

```
## Phase 3: テーマ別収集
| テーマ | 取得件数 | 投稿件数 | 重複 |
|--------|---------|---------|------|
| Index | 8 | 6 | 2 |
| Macro Economics | 10 | 8 | 2 |

## Phase 4: 結果報告
- 総投稿数: 14件
- スキップ済みテーマ: Stock, Sector, AI, Finance
```

### 個別銘柄分析（銘柄 + 業界 + 財務）

```bash
/collect-finance-news --themes "stock,sector,finance"
```

決算シーズンや M&A 動向を追跡する際に有用です。

### テクノロジー関連（AI + 銘柄）

```bash
/collect-finance-news --themes "ai,stock"
```

テクノロジーセクターに注目する際に使用します。

## テーマ一覧の確認方法

### 設定ファイルから確認

```bash
# テーマ設定ファイルの確認
cat data/config/finance-news-themes.json | jq '.themes | keys'
```

出力：
```json
[
  "ai",
  "finance",
  "index",
  "macro",
  "sector",
  "stock"
]
```

### 各テーマの詳細確認

```bash
# 特定テーマの設定を確認
cat data/config/finance-news-themes.json | jq '.themes.index'
```

出力：
```json
{
  "name": "Index",
  "name_ja": "株価指数",
  "github_status_id": "3925acc3",
  "description": "株価指数（日経平均、TOPIX、S&P500等）の動向",
  "feeds": [...]
}
```

## ユースケース別の推奨設定

### 決算シーズン

```bash
# 個別銘柄と財務情報に注力
/collect-finance-news --themes "stock,finance" --since 1d
```

### FOMC / 日銀会合前後

```bash
# マクロ経済と指数に注力
/collect-finance-news --themes "macro,index" --since 1d
```

### セクターローテーション分析

```bash
# 業界動向を重点的に収集
/collect-finance-news --themes "sector" --since 3d
```

### AI・テクノロジートレンド

```bash
# AI関連ニュースを週次で収集
/collect-finance-news --themes "ai" --since 7d --limit 30
```

## 注意事項

### テーマ指定の形式

- カンマ区切りで複数指定可能
- スペースは入れない
- 大文字小文字を区別しない

```bash
# 正しい例
/collect-finance-news --themes "index,macro"
/collect-finance-news --themes "INDEX,MACRO"

# 間違った例
/collect-finance-news --themes "index, macro"  # スペースあり
/collect-finance-news --themes index macro     # カンマなし
```

### 存在しないテーマを指定した場合

```
エラー: 無効なテーマ 'invalid_theme'
有効なテーマ: index, stock, sector, macro, ai, finance
```

## 関連パターン

- [日次収集パターン](./daily-collection.md): 全テーマの標準収集
- [dry-runモードパターン](./dry-run.md): 投稿前の確認

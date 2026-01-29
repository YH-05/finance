# GitHub Project #15 ニュース集約レポート

## 概要

GitHub Project #15（Finance News Collection）から蓄積されたニュース Issue を取得し、週次レポート作成用に構造化データとして出力したもの。

## 集約データ

**ファイル**: `news_from_project.json`

### 基本情報

- **集約期間**: 2026-01-22 ～ 2026-01-29
- **生成日時**: 2026-01-29T14:13:19.714359Z
- **対象プロジェクト**: GitHub Project #15
- **ラベルフィルタ**: `news`

### データ統計

- **総ニュース件数**: 100件

#### カテゴリ別統計

| カテゴリ | 件数 | 比率 |
|---------|------|------|
| AI | 31 | 31.0% |
| Sector | 28 | 28.0% |
| Finance | 18 | 18.0% |
| Macro Economics | 14 | 14.0% |
| Index | 8 | 8.0% |
| Stock | 1 | 1.0% |
| Other | 0 | 0.0% |

## JSON スキーマ

### トップレベル構造

```json
{
  "period": {
    "start": "2026-01-22",
    "end": "2026-01-29"
  },
  "project_number": 15,
  "generated_at": "ISO 8601形式の日時",
  "total_count": 100,
  "news": [/* ニュース配列 */],
  "by_category": {/* カテゴリ別ニュース */},
  "statistics": {/* カテゴリ別統計 */}
}
```

### ニュース アイテム構造

各ニュースアイテムは以下のフィールドを含みます:

| フィールド | 型 | 説明 |
|-----------|------|------|
| `issue_number` | number | GitHub Issue 番号 |
| `title` | string | Issue タイトル（カテゴリ付き） |
| `category` | string | 分類されたカテゴリ |
| `labels` | array | GitHub ラベル配列 |
| `issue_url` | string | GitHub Issue への直リンク |
| `original_url` | string | 元記事の URL（あれば） |
| `created_at` | string | Issue 作成日時（ISO 8601） |
| `date` | string | Issue 作成日（YYYY-MM-DD） |
| `summary` | string | ニュースの要約（最大300字） |

### カテゴリ分類ロジック

1. **タイトルから自動抽出**: `[カテゴリ名]` 形式から抽出
   - 日本語: `株価指数` → `Index`
   - 日本語: `個別銘柄` → `Stock`
   - 日本語: `セクター` → `Sector`
   - 日本語: `マクロ経済` → `Macro Economics`
   - 英語: 対応するカテゴリにマッピング

2. **キーワードマッチング**: タイトルからキーワードでカテゴリ判定

## 使用方法

### 週次レポート生成での使用

```python
import json

with open('news_from_project.json', 'r') as f:
    data = json.load(f)

# 全ニュースを取得
all_news = data['news']

# カテゴリ別にアクセス
index_news = data['by_category']['Index']
macro_news = data['by_category']['Macro Economics']

# 統計情報を参照
stats = data['statistics']
print(f"AI関連ニュース: {stats['AI']}件")
```

### フィルタリング例

```python
# 特定カテゴリのニュースのみ抽出
finance_news = [n for n in data['news'] if n['category'] == 'Finance']

# 最新5件を取得
latest_5 = data['news'][:5]

# 元記事 URL がある記事のみ
with_urls = [n for n in data['news'] if n['original_url']]
```

## ファイル仕様

- **ファイルサイズ**: ~149KB
- **形式**: JSON（UTF-8）
- **構造**: ネストされた JSON オブジェクト
- **検証**: `jq '.' news_from_project.json` で検証可能

## 関連ファイル

このディレクトリ内の他のファイル:

- `metadata.json`: レポート生成メタデータ
- `indices.json`: 指数関連ニュース
- `mag7.json`: MAG7 銘柄ニュース
- `sectors.json`: セクター関連ニュース

## 処理フロー

```
Phase 1: データ取得
  └─ GitHub Issue List API から news ラベル付き Issue を取得（limit: 100）

Phase 2: フィルタリング
  └─ 作成日時が 2026-01-22 ～ 2026-01-29 の Issue のみ抽出

Phase 3: カテゴリ分類
  ├─ Issue タイトルから `[カテゴリ名]` 形式で抽出
  └─ キーワードマッチングで未分類の Issue を分類

Phase 4: 構造化
  ├─ Issue 本文から URL と要約を抽出
  ├─ JSON スキーマに従って構造化
  └─ ファイルに保存

Phase 5: 統計生成
  └─ カテゴリ別件数を集計
```

## 注意事項

1. **URL の扱い**: 一部ニュースは `original_url` が空である場合があります（Issue 本文に URL が含まれていない場合）
2. **要約の長さ**: 要約は最大 300 字に制限されています
3. **カテゴリの精度**: キーワードマッチングに基づくため、一部に分類誤りがある可能性があります
4. **日時形式**: すべての日時は ISO 8601 形式（UTC）です

## 更新履歴

- **2026-01-29**: 初回生成（集約期間: 2026-01-22 ～ 2026-01-29、100件）

---

**生成者**: weekly-report-news-aggregator エージェント
**生成日時**: 2026-01-29T14:13:19.714359Z

# Issue作成テンプレート

GitHub Issue作成時のフォーマット定義。

## Issueタイトル形式

```
[{{theme_ja}}] {{japanese_title}}
```

### テーマ名プレフィックス

| テーマキー | プレフィックス | GitHub Status |
|-----------|--------------|---------------|
| `index` | `[株価指数]` | Index |
| `stock` | `[個別銘柄]` | Stock |
| `sector` | `[セクター]` | Sector |
| `macro` | `[マクロ経済]` | Macro Economics |
| `ai` | `[AI]` | AI |
| `finance` | `[金融]` | Finance |

### タイトル翻訳ルール

- 英語タイトルは日本語に翻訳
- 企業名・固有名詞は原則そのまま（例: Apple, Fed, S&P 500）
- 専門用語は日本語訳を使用（例: earnings → 決算）

## Issue本文テンプレート

```markdown
{{summary}}

### 情報源URL

{{url}}

### 公開日

{{published_date}}

### 収集日時

{{collected_at}}

### カテゴリ

{{category}}

### フィード/情報源名

{{feed_source}}

### 備考・メモ

{{notes}}

---

**自動収集**: このIssueは `/collect-finance-news` コマンドによって自動作成されました。
```

## プレースホルダー一覧

| プレースホルダー | 説明 | 例 | 必須 |
|-----------------|------|-----|------|
| `{{theme_ja}}` | テーマ名（日本語） | `株価指数` | ✅ |
| `{{japanese_title}}` | 記事タイトル（日本語） | `S&P 500が最高値更新` | ✅ |
| `{{summary}}` | 日本語要約（4セクション構成） | - | ✅ |
| `{{url}}` | 元記事のURL | `https://cnbc.com/...` | ✅ |
| `{{published_date}}` | 公開日時（JST形式） | `2026-01-15 10:00(JST)` | ✅ |
| `{{collected_at}}` | 収集日時（JST形式） | `2026-01-15 14:30(JST)` | ✅ |
| `{{category}}` | カテゴリ表記 | `Index（株価指数）` | ✅ |
| `{{feed_source}}` | フィード名 | `CNBC - Markets` | ✅ |
| `{{notes}}` | 備考・メモ | テーマ、AI判定理由 | ❌ |

## 要約フォーマット（4セクション構成）

`{{summary}}` には以下の構造で要約を記載：

```markdown
### 概要
- [主要事実を箇条書きで3行程度]
- [数値データがあれば含める]
- [関連企業があれば含める]

### 背景
[この出来事の背景・経緯を記載。記事に記載がなければ「[記載なし]」]

### 市場への影響
[株式・為替・債券等への影響を記載。記事に記載がなければ「[記載なし]」]

### 今後の見通し
[今後予想される展開・注目点を記載。記事に記載がなければ「[記載なし]」]
```

### 各セクションの記載ルール

| セクション | 内容 | 記載なしの例 |
|-----------|------|-------------|
| 概要 | 主要事実、数値データ | （常に何か記載できるはず） |
| 背景 | 経緯、原因、これまでの流れ | 速報で背景説明がない場合 |
| 市場への影響 | 株価・為替・債券への影響 | 影響の言及がない場合 |
| 今後の見通し | 予想、アナリスト見解 | 将来予測の言及がない場合 |

## ラベル設定

### 必須ラベル

- `news`: 全ニュースIssueに付与

### オプションラベル（将来拡張用）

| ラベル | 条件 |
|--------|------|
| `urgent` | 速報性が高い記事 |
| `earnings` | 決算関連 |
| `fed` | Fed/金融政策関連 |

## URL設定の重要ルール

> **絶対に守ること**: `{{url}}`には**RSSから取得したオリジナルのlink**をそのまま使用すること。
>
> - ✅ 正しい: RSSの`link`フィールドの値をそのまま使用
> - ❌ 間違い: WebFetchのリダイレクト先URL
> - ❌ 間違い: URLを推測・生成する
> - ❌ 間違い: URLを短縮・変換する

## Issue作成手順

```bash
# Step 1: テンプレート読み込み（frontmatter除外）
template=$(cat .github/ISSUE_TEMPLATE/news-article.md | tail -n +7)

# Step 2: 収集日時を取得
collected_at=$(TZ=Asia/Tokyo date '+%Y-%m-%d %H:%M')

# Step 3: プレースホルダーを置換
body="${template//\{\{summary\}\}/$japanese_summary}"
body="${body//\{\{url\}\}/$link}"
body="${body//\{\{published_date\}\}/$published_jst(JST)}"
body="${body//\{\{collected_at\}\}/$collected_at(JST)}"
body="${body//\{\{category\}\}/$category}"
body="${body//\{\{feed_source\}\}/$source}"
body="${body//\{\{notes\}\}/$notes}"

# Step 4: Issue作成
issue_url=$(gh issue create \
    --repo YH-05/finance \
    --title "[${theme_ja}] ${japanese_title}" \
    --body "$body" \
    --label "news")

# Step 5: Issue番号を抽出
issue_number=$(echo "$issue_url" | grep -oE '[0-9]+$')

# Step 6: Issueをclose（ニュースIssueはclosed状態で保存）
gh issue close "$issue_number" --repo YH-05/finance
```

## GitHub Project設定

Issue作成後、以下を設定：

1. **Project追加**: `gh project item-add 15 --owner YH-05 --url {issue_url}`
2. **Status設定**: テーマに対応するStatusを設定
3. **公開日時設定**: `YYYY-MM-DD` 形式で日付を設定

### Status Option ID一覧

| テーマ | Status名 | Option ID |
|--------|----------|-----------|
| index | Index | `3925acc3` |
| stock | Stock | `f762022e` |
| sector | Sector | `48762504` |
| macro | Macro Economics | `730034a5` |
| ai | AI | `6fbb43d0` |
| finance | Finance | `ac4a91b1` |

## 参照

- **GitHub Issueテンプレート**: `.github/ISSUE_TEMPLATE/news-article.md`
- **共通処理ガイド**: `.claude/agents/finance_news_collector/common-processing-guide.md`
- **テーマ設定**: `data/config/finance-news-themes.json`

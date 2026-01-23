---
name: weekly-template-rendering
description: "週次レポートのテンプレートにデータとコメントを埋め込むスキル。aggregated_data.json と comments.json からMarkdown形式のレポートを生成する。"
allowed-tools: Read, Write
---

# Weekly Template Rendering

週次レポートのテンプレートにデータとコメントを埋め込むスキルです。

## 目的

このスキルは以下を提供します：

- **テンプレート埋め込み**: プレースホルダーを実データで置換
- **Markdown生成**: 読みやすいフォーマットで週次レポートを生成
- **JSON出力**: 構造化データとしても出力
- **テーブル生成**: 指数、MAG7、セクターのテーブルを自動生成

## いつ使用するか

### プロアクティブ使用

`weekly-report-writer` エージェントの第3フェーズとして、`weekly-comment-generation` の後に呼び出される。

### 明示的な使用

週次レポート生成ワークフローの一部として呼び出し。

## 入力データ

### 必須ファイル

```
articles/weekly_report/{date}/data/
├── aggregated_data.json   # 集約データ
└── comments.json          # 生成コメント
```

### テンプレートファイル

```
articles/templates/weekly_market_report_template.md
```

## 出力データ

### 出力先

```
articles/weekly_report/{date}/02_edit/
├── weekly_report.md       # Markdownレポート
└── weekly_report.json     # 構造化データ
```

## テンプレート構造

### Markdownテンプレート

```markdown
# 週次マーケットレポート {{report_date}}

- **対象期間**: {{start_date}} 〜 {{end_date}}
- **生成日時**: {{generated_at}}

## 今週のハイライト

{{highlight_comment}}

## 市場概況

### 主要指数パフォーマンス

{{indices_table}}

### スタイル分析

{{style_analysis_comment}}

## Magnificent 7 + 半導体

### パフォーマンス

{{mag7_table}}

### 個別銘柄トピック

{{mag7_comment}}

## セクター分析

### 上位セクター

{{sectors_top_table}}

{{sectors_top_comment}}

### 下位セクター

{{sectors_bottom_table}}

{{sectors_bottom_comment}}

## マクロ経済・政策動向

{{macro_comment}}

## 投資テーマ別動向

{{themes_comment}}

## 来週の注目材料

{{outlook_comment}}

---

**免責事項**: 本レポートは情報提供を目的としており、投資助言ではありません。
投資判断は自己責任で行ってください。

**生成**: weekly-report-writer エージェント
```

## プレースホルダー一覧

### メタデータ

| プレースホルダー | ソース | 説明 |
|-----------------|--------|------|
| `{{report_date}}` | aggregated_data.metadata.report_date | レポート日付 |
| `{{start_date}}` | aggregated_data.metadata.period.start | 対象期間開始 |
| `{{end_date}}` | aggregated_data.metadata.period.end | 対象期間終了 |
| `{{generated_at}}` | 生成時刻 | JST形式 |

### コメント

| プレースホルダー | ソース | 説明 |
|-----------------|--------|------|
| `{{highlight_comment}}` | comments.highlight.content | ハイライト |
| `{{indices_comment}}` | comments.indices.content | 指数コメント |
| `{{style_analysis_comment}}` | aggregated_data.indices.style_analysis | スタイル分析 |
| `{{mag7_comment}}` | comments.mag7.content | MAG7コメント |
| `{{sectors_top_comment}}` | comments.sectors_top.content | 上位セクター |
| `{{sectors_bottom_comment}}` | comments.sectors_bottom.content | 下位セクター |
| `{{macro_comment}}` | comments.macro.content | マクロ経済 |
| `{{themes_comment}}` | comments.themes.content | 投資テーマ |
| `{{outlook_comment}}` | comments.outlook.content | 来週の材料 |

### テーブル

| プレースホルダー | ソース | 説明 |
|-----------------|--------|------|
| `{{indices_table}}` | aggregated_data.indices | 指数テーブル |
| `{{mag7_table}}` | aggregated_data.mag7.stocks | MAG7テーブル |
| `{{sectors_top_table}}` | aggregated_data.sectors.top_3 | 上位セクター |
| `{{sectors_bottom_table}}` | aggregated_data.sectors.bottom_3 | 下位セクター |

## テーブル生成仕様

### 指数テーブル

```markdown
| 指数 | 週間リターン | YTD | 終値 |
|------|-------------|-----|------|
| S&P 500 | +2.50% | +3.20% | 5,850.50 |
| S&P 500 等ウェイト | +1.80% | +2.50% | 178.30 |
| グロース (VUG) | +3.20% | +4.10% | 380.20 |
| バリュー (VTV) | +1.20% | +2.00% | 165.80 |
| NASDAQ | +3.10% | +4.50% | 18,520.30 |
| Russell 2000 | +1.50% | +1.80% | 2,050.40 |
```

### MAG7テーブル

```markdown
| 銘柄 | ティッカー | 週間リターン | YTD | 終値 |
|------|-----------|-------------|-----|------|
| Tesla | TSLA | +3.70% | +5.20% | $245.30 |
| NVIDIA | NVDA | +1.90% | +8.50% | $680.50 |
| Apple | AAPL | +1.50% | +2.30% | $195.80 |
| Microsoft | MSFT | +1.20% | +3.10% | $410.20 |
| Amazon | AMZN | +0.80% | +2.80% | $185.40 |
| Alphabet | GOOGL | -0.80% | +1.50% | $175.30 |
| Meta | META | -1.20% | +0.80% | $520.10 |
```

### セクターテーブル

```markdown
| セクター | ETF | 週間リターン | 構成比 |
|---------|-----|-------------|--------|
| IT | XLK | +2.80% | 29.5% |
| エネルギー | XLE | +2.30% | 4.2% |
| 金融 | XLF | +1.80% | 13.1% |
```

## プロセス

```
Phase 1: データ読み込み
├── aggregated_data.json 読み込み
├── comments.json 読み込み
└── テンプレートファイル読み込み

Phase 2: テーブル生成
├── 指数テーブル生成
│   └── indices データから Markdown テーブル作成
├── MAG7テーブル生成
│   └── mag7 データから Markdown テーブル作成
├── セクターテーブル生成（上位）
│   └── top_3 データから Markdown テーブル作成
└── セクターテーブル生成（下位）
    └── bottom_3 データから Markdown テーブル作成

Phase 3: プレースホルダー置換
├── メタデータプレースホルダー置換
├── コメントプレースホルダー置換
└── テーブルプレースホルダー置換

Phase 4: 出力生成
├── weekly_report.md を保存
└── weekly_report.json を保存
```

## JSON出力形式

### weekly_report.json

```json
{
  "metadata": {
    "report_date": "2026-01-22",
    "period": {
      "start": "2026-01-14",
      "end": "2026-01-21"
    },
    "generated_at": "2026-01-22T09:30:00+09:00",
    "total_characters": 3450,
    "sections": 8
  },
  "summary": {
    "highlight": "S&P 500が週間+2.50%上昇...",
    "market_sentiment": "bullish",
    "key_drivers": ["企業決算", "Fed発言", "AI需要"]
  },
  "indices": {
    "spx": { "return": "+2.50%", "ytd": "+3.20%" },
    "rsp": { "return": "+1.80%", "ytd": "+2.50%" },
    "vug": { "return": "+3.20%", "ytd": "+4.10%" },
    "vtv": { "return": "+1.20%", "ytd": "+2.00%" }
  },
  "mag7": {
    "average_return": "+1.45%",
    "top_performer": { "ticker": "TSLA", "return": "+3.70%" },
    "bottom_performer": { "ticker": "META", "return": "-1.20%" }
  },
  "sectors": {
    "top": ["IT", "エネルギー", "金融"],
    "bottom": ["ヘルスケア", "公益", "素材"],
    "rotation": "グロース回帰"
  },
  "content": {
    "highlight": "...",
    "indices": "...",
    "mag7": "...",
    "sectors_top": "...",
    "sectors_bottom": "...",
    "macro": "...",
    "themes": "...",
    "outlook": "..."
  }
}
```

## 使用例

### 例1: 標準的なレンダリング

**入力**:
```
articles/weekly_report/2026-01-22/data/
├── aggregated_data.json ✓
└── comments.json ✓
```

**出力**:
```
articles/weekly_report/2026-01-22/02_edit/
├── weekly_report.md ✓ (3450字)
└── weekly_report.json ✓
```

### 例2: テンプレートファイルが存在しない場合

**処理**:
- デフォルトテンプレートを使用
- 警告をログに出力

**出力**:
```json
{
  "warning": "テンプレートファイルが見つかりません。デフォルトテンプレートを使用します。"
}
```

## フォーマット規則

### 数値フォーマット

| 種類 | 形式 | 例 |
|------|------|-----|
| リターン（正） | `+X.XX%` | `+2.50%` |
| リターン（負） | `-X.XX%` | `-1.20%` |
| リターン（ゼロ） | `0.00%` | `0.00%` |
| 株価 | `$X,XXX.XX` | `$5,850.50` |
| 時価総額 | `$X.XX T/B` | `$3.80T` |
| 日付 | `YYYY-MM-DD` | `2026-01-22` |
| 日時 | `YYYY-MM-DD HH:MM (JST)` | `2026-01-22 09:30 (JST)` |

### Markdownフォーマット

- 見出し: `#` (H1), `##` (H2), `###` (H3)
- 表: GitHub Flavored Markdown 形式
- 箇条書き: `-` を使用
- 強調: `**太字**`
- リンク: `[テキスト](URL)`

## 品質基準

### 必須（MUST）

- [ ] 全プレースホルダーが置換される
- [ ] Markdownが正しい構文
- [ ] テーブルが正しくレンダリング可能
- [ ] JSONが有効な形式

### 推奨（SHOULD）

- 見出し階層が一貫している
- 数値フォーマットが統一されている
- 文字エンコーディングがUTF-8

## エラーハンドリング

### E001: 入力ファイル不足

```json
{
  "error": "入力ファイルが見つかりません",
  "missing": ["comments.json"],
  "suggestion": "先に weekly-comment-generation を実行してください"
}
```

### E002: プレースホルダー未置換

```json
{
  "warning": "一部のプレースホルダーが置換されませんでした",
  "unresolved": ["{{themes_comment}}"],
  "action": "デフォルト値で置換"
}
```

### E003: 出力ディレクトリエラー

```json
{
  "error": "出力ディレクトリを作成できません",
  "path": "articles/weekly_report/2026-01-22/02_edit/",
  "suggestion": "ディレクトリの権限を確認してください"
}
```

## 完了条件

- [ ] weekly_report.md が生成される
- [ ] weekly_report.json が生成される
- [ ] 全プレースホルダーが置換される
- [ ] テーブルが正しく生成される
- [ ] Markdownフォーマットが有効

## 関連スキル

- **weekly-data-aggregation**: 入力データ（aggregated_data.json）を提供
- **weekly-comment-generation**: 入力データ（comments.json）を提供
- **weekly-report-validation**: 生成レポートの品質検証

## 参考資料

- `docs/project/project-21/project.md`: 週次レポートプロジェクト計画
- `.claude/templates/weekly-report-issue.md`: Issue投稿テンプレート

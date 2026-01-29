# Task 16: 週次レポートテンプレートの更新

**Phase**: 4 - 統合
**依存**: Task 02, Task 07, Task 12
**ファイル**: `template/market_report/weekly_market_report_template.md`

## 概要

週次マーケットレポートのテンプレートに「金利・債券市場」「為替市場」セクションを追加する。

## 現行テンプレート構造

```markdown
# 週次マーケットレポート {report_date}
## 今週のハイライト
## 市場概況
### 主要指数パフォーマンス
### スタイル分析（グロース vs バリュー）
## Magnificent 7 + 半導体
## セクター分析
## マクロ経済・政策動向
## 投資テーマ別動向
## 来週の注目材料
```

## 追加するセクション

### 金利・債券市場セクション

「マクロ経済・政策動向」の前に追加:

```markdown
---

## 金利・債券市場

### 米国債利回り

{interest_rates_table}

{interest_rates_comment}

### イールドカーブ分析

{yield_curve_analysis}

---
```

### 為替市場セクション

「金利・債券市場」の後に追加:

```markdown
## 為替市場

### 円クロス主要通貨

{currencies_table}

{currencies_comment}

---
```

### 来週の注目材料セクションの拡張

既存の `{upcoming_events}` を詳細化:

```markdown
## 来週の注目材料

### 主要企業決算

{earnings_table}

### 経済指標発表

{economic_releases_table}

{upcoming_events_comment}
```

## 変更後のテンプレート構造

```markdown
# 週次マーケットレポート {report_date}

**対象期間**: {period_start}〜{period_end}

---

## 今週のハイライト

{highlights}

---

## 市場概況

### 主要指数パフォーマンス

{indices_table}

{indices_comment}

### スタイル分析（グロース vs バリュー）

{style_analysis}

---

## Magnificent 7 + 半導体

### パフォーマンス

{mag7_table}

### 個別銘柄トピック

{mag7_comment}

---

## セクター分析

### 上位3セクター

{top_sectors_table}

{top_sectors_comment}

### 下位3セクター

{bottom_sectors_table}

{bottom_sectors_comment}

---

## 金利・債券市場                     ← 新規

### 米国債利回り

{interest_rates_table}

{interest_rates_comment}

### イールドカーブ分析

{yield_curve_analysis}

---

## 為替市場                           ← 新規

### 円クロス主要通貨

{currencies_table}

{currencies_comment}

---

## マクロ経済・政策動向

{macro_comment}

---

## 投資テーマ別動向

{theme_comment}

---

## 来週の注目材料                     ← 拡張

### 主要企業決算

{earnings_table}

### 経済指標発表

{economic_releases_table}

{upcoming_events_comment}

---

**免責事項**: ...
```

## プレースホルダー定義

### 新規プレースホルダー

| プレースホルダー | 説明 | 対応データ |
|-----------------|------|-----------|
| `{interest_rates_table}` | 金利一覧テーブル | interest_rates.data |
| `{interest_rates_comment}` | 金利コメント | comments.interest_rates |
| `{yield_curve_analysis}` | イールドカーブ分析 | interest_rates.yield_curve |
| `{currencies_table}` | 為替一覧テーブル | currencies.symbols |
| `{currencies_comment}` | 為替コメント | comments.currencies |
| `{earnings_table}` | 決算予定テーブル | upcoming_events.earnings |
| `{economic_releases_table}` | 経済指標テーブル | upcoming_events.economic_releases |
| `{upcoming_events_comment}` | 注目材料コメント | comments.outlook |

## 受け入れ条件

- [ ] 金利・債券市場セクションが追加されている
- [ ] 為替市場セクションが追加されている
- [ ] 来週の注目材料セクションが拡張されている
- [ ] プレースホルダーが正しく定義されている
- [ ] 既存のプレースホルダーに影響がない
- [ ] Markdownの構文が正しい

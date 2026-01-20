# {report_date_formatted} Weekly Comment

## Indices (AS OF {end_date_formatted})

| 指数 | 週間リターン |
|------|-------------|
| S&P 500 | {spx_return} |
| 等ウェイト (RSP) | {rsp_return} |
| グロース (VUG) | {vug_return} |
| バリュー (VTV) | {vtv_return} |

{indices_comment}

<!--
ニュースコンテキスト:
{indices_news_context}
-->

## Magnificent 7

| 銘柄 | 週間リターン |
|------|-------------|
{mag7_table}

{mag7_comment}

<!--
ニュースコンテキスト:
{mag7_news_context}
-->

## セクター別パフォーマンス

### 上位3セクター

| セクター | ETF | 週間リターン |
|----------|-----|-------------|
{top_sectors_table}

{top_sectors_comment}

### 下位3セクター

| セクター | ETF | 週間リターン |
|----------|-----|-------------|
{bottom_sectors_table}

{bottom_sectors_comment}

<!--
ニュースコンテキスト:
{sectors_news_context}
-->

## 今後の材料

{upcoming_materials}

## 戦略変更

{strategy_changes}

---

**免責事項**: 本コメントは情報提供を目的としており、投資助言ではありません。投資判断は自己責任で行ってください。

**データソース**: Yahoo Finance (yf.download)、期間: {period_start} 〜 {period_end}

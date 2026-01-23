# 週次マーケットレポートテンプレート設計書

**Issue**: #771
**作成日**: 2026-01-23
**ステータス**: 確定

## 概要

note.com 投稿用の週次マーケットレポートの定型フォーマットを定義する。
毎週同じ構成で比較しやすく、読者にとって読みやすいレポートを生成することを目的とする。

## レポート構成（8セクション）

```
1. 今週のハイライト（サマリー）
2. 市場概況（指数、スタイル分析）
3. Magnificent 7 + 半導体
4. セクター分析
5. マクロ経済・政策動向
6. 投資テーマ別動向
7. 来週の注目材料
8. 免責事項
```

## 詳細構成

### 1. 今週のハイライト

**目的**: 読者が最初に全体像を把握できるサマリー

**文字数目標**: 600字程度

**内容**:
- 3〜5個のバレットポイント
- 主要指数の週間パフォーマンス
- 最も重要なイベント/ニュース
- 市場センチメント

**プレースホルダー**:
```markdown
## 今週のハイライト

{highlights_bullets}

> 【市場センチメント】{market_sentiment}
```

---

### 2. 市場概況

**目的**: 主要指数とスタイル分析を表形式で可視化

#### 2.1 主要指数パフォーマンス

**プレースホルダー**:
```markdown
### 主要指数パフォーマンス

| 指数 | 週間リターン | 要因分析 |
|------|-------------|---------|
| S&P 500 | {spx_return} | {spx_factor} |
| NASDAQ | {ndx_return} | {ndx_factor} |
| Russell 2000 | {rut_return} | {rut_factor} |
| VIX | {vix_value} | {vix_factor} |

{indices_commentary}
```

#### 2.2 スタイル分析

**プレースホルダー**:
```markdown
### スタイル分析

| 比較 | 銘柄A | 銘柄B | 差分 | 解釈 |
|------|-------|-------|------|------|
| 大型 vs 中小型 | S&P 500 ({spx_return}) | Russell 2000 ({rut_return}) | {large_vs_small_diff} | {large_vs_small_comment} |
| 時価加重 vs 等ウェイト | SPY ({spy_return}) | RSP ({rsp_return}) | {cap_vs_equal_diff} | {cap_vs_equal_comment} |
| グロース vs バリュー | VUG ({vug_return}) | VTV ({vtv_return}) | {growth_vs_value_diff} | {growth_vs_value_comment} |

{style_analysis_commentary}
```

---

### 3. Magnificent 7 + 半導体

**目的**: 市場牽引銘柄の詳細分析

**文字数目標**: 各銘柄トピック 600字程度

#### 3.1 パフォーマンステーブル

**プレースホルダー**:
```markdown
### パフォーマンス

| 銘柄 | ティッカー | 週間リターン | 注目ニュース |
|------|-----------|-------------|-------------|
| Apple | AAPL | {aapl_return} | {aapl_headline} |
| Microsoft | MSFT | {msft_return} | {msft_headline} |
| Alphabet | GOOGL | {googl_return} | {googl_headline} |
| Amazon | AMZN | {amzn_return} | {amzn_headline} |
| NVIDIA | NVDA | {nvda_return} | {nvda_headline} |
| Meta | META | {meta_return} | {meta_headline} |
| Tesla | TSLA | {tsla_return} | {tsla_headline} |
| **SOX指数** | ^SOX | {sox_return} | {sox_headline} |
```

#### 3.2 個別銘柄トピック

**プレースホルダー**:
```markdown
### 個別銘柄トピック

#### {top_performer_ticker}: {top_performer_name}

{top_performer_analysis}

**関連ニュース**:
- {top_performer_news_1}
- {top_performer_news_2}

#### {notable_mover_ticker}: {notable_mover_name}

{notable_mover_analysis}

**関連ニュース**:
- {notable_mover_news_1}
- {notable_mover_news_2}
```

---

### 4. セクター分析

**目的**: 上位・下位セクターの詳細分析

**文字数目標**: 各セクター 600字程度

#### 4.1 上位3セクター

**プレースホルダー**:
```markdown
### 上位3セクター

| 順位 | セクター | ETF | 週間リターン |
|------|----------|-----|-------------|
| 1 | {top1_sector_name} | {top1_sector_etf} | {top1_sector_return} |
| 2 | {top2_sector_name} | {top2_sector_etf} | {top2_sector_return} |
| 3 | {top3_sector_name} | {top3_sector_etf} | {top3_sector_return} |

#### {top1_sector_name}

{top1_sector_analysis}

**背景ニュース**:
- {top1_news_1}
- {top1_news_2}

#### {top2_sector_name}

{top2_sector_analysis}

#### {top3_sector_name}

{top3_sector_analysis}
```

#### 4.2 下位3セクター

**プレースホルダー**:
```markdown
### 下位3セクター

| 順位 | セクター | ETF | 週間リターン |
|------|----------|-----|-------------|
| 1 | {bottom1_sector_name} | {bottom1_sector_etf} | {bottom1_sector_return} |
| 2 | {bottom2_sector_name} | {bottom2_sector_etf} | {bottom2_sector_return} |
| 3 | {bottom3_sector_name} | {bottom3_sector_etf} | {bottom3_sector_return} |

#### {bottom1_sector_name}

{bottom1_sector_analysis}

#### {bottom2_sector_name}

{bottom2_sector_analysis}

#### {bottom3_sector_name}

{bottom3_sector_analysis}
```

---

### 5. マクロ経済・政策動向

**目的**: 市場に影響を与えるマクロ要因の整理

**プレースホルダー**:
```markdown
## マクロ経済・政策動向

### Fed・金融政策

{fed_policy_commentary}

**注目指標**:
- FF金利: {ff_rate}
- 10年債利回り: {us10y_yield}
- 2年債利回り: {us2y_yield}

### 経済指標

| 指標 | 発表値 | 予想 | 前回 | 市場への影響 |
|------|--------|------|------|-------------|
| {indicator_1_name} | {indicator_1_actual} | {indicator_1_expected} | {indicator_1_previous} | {indicator_1_impact} |
| {indicator_2_name} | {indicator_2_actual} | {indicator_2_expected} | {indicator_2_previous} | {indicator_2_impact} |

{macro_commentary}
```

---

### 6. 投資テーマ別動向

**目的**: 注目テーマの動向をまとめる

**プレースホルダー**:
```markdown
## 投資テーマ別動向

### AI・半導体

{ai_semiconductor_commentary}

**関連銘柄動向**:
{ai_related_stocks}

### {theme_2_name}

{theme_2_commentary}

### {theme_3_name}

{theme_3_commentary}
```

---

### 7. 来週の注目材料

**目的**: 来週のイベントカレンダー

**プレースホルダー**:
```markdown
## 来週の注目材料

### 決算発表

| 日付 | 銘柄 | ティッカー | 注目ポイント |
|------|------|-----------|-------------|
| {earnings_1_date} | {earnings_1_company} | {earnings_1_ticker} | {earnings_1_focus} |
| {earnings_2_date} | {earnings_2_company} | {earnings_2_ticker} | {earnings_2_focus} |
| {earnings_3_date} | {earnings_3_company} | {earnings_3_ticker} | {earnings_3_focus} |

### 経済指標発表

| 日付 | 指標 | 予想 | 前回 |
|------|------|------|------|
| {econ_1_date} | {econ_1_name} | {econ_1_expected} | {econ_1_previous} |
| {econ_2_date} | {econ_2_name} | {econ_2_expected} | {econ_2_previous} |

### その他イベント

{other_events}
```

---

### 8. 免責事項

**プレースホルダー**:
```markdown
---

**免責事項**: 本記事は情報提供を目的としており、特定の金融商品の売買を推奨するものではありません。投資判断は自己責任で行ってください。

**データソース**: Yahoo Finance、FRED (Federal Reserve Economic Data)、各種ニュースソース

**対象期間**: {period_start} 〜 {period_end}

**作成日**: {report_date}
```

---

## プレースホルダー一覧

### 基本情報

| プレースホルダー | 説明 | 形式 | 例 |
|-----------------|------|------|-----|
| `{report_date}` | レポート作成日 | YYYY-MM-DD | 2026-01-22 |
| `{report_date_formatted}` | フォーマット済み日付 | YYYY/M/D(曜日) | 2026/1/22(Wed) |
| `{period_start}` | 対象期間開始日 | YYYY-MM-DD | 2026-01-14 |
| `{period_end}` | 対象期間終了日 | YYYY-MM-DD | 2026-01-21 |

### 指数関連

| プレースホルダー | 説明 | 形式 | 例 |
|-----------------|------|------|-----|
| `{spx_return}` | S&P 500 週間リターン | ±X.XX% | +2.50% |
| `{ndx_return}` | NASDAQ 週間リターン | ±X.XX% | +3.20% |
| `{rut_return}` | Russell 2000 週間リターン | ±X.XX% | +1.80% |
| `{spy_return}` | SPY 週間リターン | ±X.XX% | +2.48% |
| `{rsp_return}` | RSP 等ウェイト週間リターン | ±X.XX% | +1.90% |
| `{vug_return}` | VUG グロース週間リターン | ±X.XX% | +3.10% |
| `{vtv_return}` | VTV バリュー週間リターン | ±X.XX% | +1.50% |
| `{vix_value}` | VIX 終値 | XX.XX | 15.50 |
| `{spx_factor}` | S&P 500 要因分析 | テキスト | AI関連銘柄牽引 |

### MAG7関連

| プレースホルダー | 説明 | 形式 | 例 |
|-----------------|------|------|-----|
| `{aapl_return}` | Apple 週間リターン | ±X.XX% | -2.30% |
| `{msft_return}` | Microsoft 週間リターン | ±X.XX% | +1.50% |
| `{googl_return}` | Alphabet 週間リターン | ±X.XX% | +0.80% |
| `{amzn_return}` | Amazon 週間リターン | ±X.XX% | +2.10% |
| `{nvda_return}` | NVIDIA 週間リターン | ±X.XX% | +4.50% |
| `{meta_return}` | Meta 週間リターン | ±X.XX% | +1.20% |
| `{tsla_return}` | Tesla 週間リターン | ±X.XX% | +3.70% |
| `{sox_return}` | SOX 週間リターン | ±X.XX% | +3.10% |
| `{aapl_headline}` | Apple 注目ニュース | テキスト | AI競争激化懸念 |

### セクター関連

| プレースホルダー | 説明 | 形式 | 例 |
|-----------------|------|------|-----|
| `{top1_sector_name}` | 上位1位セクター名 | テキスト | Information Technology |
| `{top1_sector_etf}` | 上位1位セクターETF | ティッカー | XLK |
| `{top1_sector_return}` | 上位1位セクターリターン | ±X.XX% | +2.50% |
| `{top1_sector_analysis}` | 上位1位セクター分析 | テキスト（600字） | AI需要が... |
| `{bottom1_sector_name}` | 下位1位セクター名 | テキスト | Health Care |
| `{bottom1_sector_etf}` | 下位1位セクターETF | ティッカー | XLV |
| `{bottom1_sector_return}` | 下位1位セクターリターン | ±X.XX% | -2.90% |

### マクロ経済関連

| プレースホルダー | 説明 | 形式 | 例 |
|-----------------|------|------|-----|
| `{ff_rate}` | FF金利 | X.XX% | 4.50% |
| `{us10y_yield}` | 10年債利回り | X.XX% | 4.10% |
| `{us2y_yield}` | 2年債利回り | X.XX% | 4.25% |
| `{fed_policy_commentary}` | Fed政策コメント | テキスト | FOMCは... |

### コメンタリー関連

| プレースホルダー | 説明 | 形式 | 目標文字数 |
|-----------------|------|------|-----------|
| `{highlights_bullets}` | ハイライトバレット | Markdown箇条書き | 600字 |
| `{indices_commentary}` | 指数コメント | テキスト | 400字 |
| `{style_analysis_commentary}` | スタイル分析コメント | テキスト | 300字 |
| `{top_performer_analysis}` | トップ銘柄分析 | テキスト | 600字 |
| `{top1_sector_analysis}` | セクター分析 | テキスト | 600字 |
| `{macro_commentary}` | マクロコメント | テキスト | 400字 |
| `{market_sentiment}` | 市場センチメント | 単語 | Bullish/Neutral/Bearish |

---

## サンプル出力イメージ

```markdown
# 週次マーケットレポート 2026/1/22

**対象期間**: 2026/1/15〜2026/1/22

---

## 今週のハイライト

- S&P 500は週間+2.50%上昇、2026年初来高値を更新
- NVIDIA決算が市場予想を上回り、AI関連株が軒並み上昇
- FRBパウエル議長の発言で年内利下げ期待が後退
- テクノロジーセクターが市場牽引、ヘルスケアは軟調
- VIXは15.50まで低下、リスクオン環境継続

> 【市場センチメント】Bullish（強気）

---

## 市場概況

### 主要指数パフォーマンス

| 指数 | 週間リターン | 要因分析 |
|------|-------------|---------|
| S&P 500 | +2.50% | AI関連銘柄牽引、NVIDIA決算好感 |
| NASDAQ | +3.20% | テック株全般に買い |
| Russell 2000 | +1.80% | 金利低下期待で小型株回復 |
| VIX | 15.50 | リスクオフ後退 |

S&P 500指数は週間+2.50%上昇し、2026年初来高値を更新しました。週前半はFOMC議事要旨の公表を控えて様子見姿勢が強かったものの、NVIDIA決算発表後にAI関連株を中心に買いが加速しました。

### スタイル分析

| 比較 | 銘柄A | 銘柄B | 差分 | 解釈 |
|------|-------|-------|------|------|
| 大型 vs 中小型 | S&P 500 (+2.50%) | Russell 2000 (+1.80%) | +0.70% | 大型株優位 |
| 時価加重 vs 等ウェイト | SPY (+2.48%) | RSP (+1.90%) | +0.58% | メガキャップ主導 |
| グロース vs バリュー | VUG (+3.10%) | VTV (+1.50%) | +1.60% | グロース優位 |

今週は大型グロース株が市場を牽引しました。等ウェイト指数(RSP)が時価加重指数(SPY)を下回ったことから、上昇の恩恵はMAG7を中心とした一部の銘柄に集中していたことがわかります。

---

## Magnificent 7 + 半導体

### パフォーマンス

| 銘柄 | ティッカー | 週間リターン | 注目ニュース |
|------|-----------|-------------|-------------|
| Apple | AAPL | -2.30% | AI競争激化、幹部退職報道 |
| Microsoft | MSFT | +1.50% | Azure成長継続期待 |
| Alphabet | GOOGL | +0.80% | Gemini 2.0発表 |
| Amazon | AMZN | +2.10% | AWS新サービス発表 |
| NVIDIA | NVDA | +4.50% | 決算好感、データセンター需要堅調 |
| Meta | META | +1.20% | 広告事業好調 |
| Tesla | TSLA | +3.70% | 中国販売好調報道 |
| **SOX指数** | ^SOX | +3.10% | AI需要でセクター全般上昇 |

### 個別銘柄トピック

#### NVDA: NVIDIA

NVIDIAは週間+4.50%上昇し、MAG7でトップパフォーマーとなりました。1月21日に発表された2025年Q4決算では、売上高が前年同期比+65%の350億ドル、EPSは市場予想を15%上回る$0.89を記録しました。

特にデータセンター部門は前年同期比+80%の成長を達成し、AI需要の持続性が改めて確認されました。CFOのColette Kress氏は「Blackwellアーキテクチャへの需要は供給を大きく上回っている」とコメントし、2026年も高成長が続く見通しを示しました。

**関連ニュース**:
- [NVIDIA決算: データセンター売上が記録更新](https://example.com/nvidia-earnings)
- [Blackwell生産拡大へ、TSMCと追加契約](https://example.com/nvidia-tsmc)

---

## セクター分析

### 上位3セクター

| 順位 | セクター | ETF | 週間リターン |
|------|----------|-----|-------------|
| 1 | Information Technology | XLK | +2.80% |
| 2 | Consumer Discretionary | XLY | +2.20% |
| 3 | Communication Services | XLC | +1.90% |

#### Information Technology

ITセクターは週間+2.80%上昇し、市場をリードしました。NVIDIA決算を起点にAI関連投資の加速期待が高まり、半導体・ソフトウェア銘柄全般に買いが入りました。特にデータセンター向けインフラ需要が堅調で、AMD、Broadcom、Marvellなども軒並み上昇しています。

また、企業のAI投資動向を示すIT支出調査でも、2026年のAI関連予算が前年比+40%増加する見込みとの報告があり、セクターへの資金流入が続いています。

**背景ニュース**:
- [企業AI投資、2026年は40%増加見込み](https://example.com/ai-spending)
- [データセンター需要、過去最高を更新](https://example.com/datacenter-demand)

### 下位3セクター

| 順位 | セクター | ETF | 週間リターン |
|------|----------|-----|-------------|
| 1 | Health Care | XLV | -2.90% |
| 2 | Utilities | XLU | -2.20% |
| 3 | Real Estate | XLRE | -1.80% |

#### Health Care

ヘルスケアセクターは週間-2.90%下落し、最も軟調なパフォーマンスとなりました。新政権の医薬品価格引き下げ政策への警戒感が続く中、大手製薬各社の2026年ガイダンスが軒並み慎重な見通しを示したことが重しとなりました。

---

## マクロ経済・政策動向

### Fed・金融政策

FOMCは1月の会合で政策金利を据え置きました。パウエル議長は記者会見で「インフレは依然として目標を上回っており、追加利下げには慎重なアプローチが必要」との見解を示しました。市場では年内2回の利下げ予想が後退し、債券利回りは上昇しました。

**注目指標**:
- FF金利: 4.25-4.50%
- 10年債利回り: 4.15%
- 2年債利回り: 4.30%

### 経済指標

| 指標 | 発表値 | 予想 | 前回 | 市場への影響 |
|------|--------|------|------|-------------|
| 小売売上高 (前月比) | +0.8% | +0.5% | +0.3% | 消費堅調で株高 |
| 新規失業保険申請件数 | 21.5万件 | 22.0万件 | 22.3万件 | 雇用市場安定 |

---

## 投資テーマ別動向

### AI・半導体

AI関連銘柄は今週も好調を維持しました。NVIDIA決算を契機に、AI向けGPU需要の持続性が改めて確認され、サプライチェーン全体に恩恵が及んでいます。

**関連銘柄動向**:
- NVIDIA (+4.50%): 決算好感
- AMD (+3.20%): データセンターシェア拡大期待
- SMCI (+5.80%): AIサーバー需要拡大

---

## 来週の注目材料

### 決算発表

| 日付 | 銘柄 | ティッカー | 注目ポイント |
|------|------|-----------|-------------|
| 1/28 | Apple | AAPL | iPhone販売・AI戦略 |
| 1/29 | Microsoft | MSFT | Azure成長率・Copilot収益化 |
| 1/30 | Meta | META | 広告収入・メタバース損失 |

### 経済指標発表

| 日付 | 指標 | 予想 | 前回 |
|------|------|------|------|
| 1/26 | PCE物価指数 (前年比) | +2.6% | +2.6% |
| 1/27 | 消費者信頼感指数 | 110.5 | 109.7 |

---

**免責事項**: 本記事は情報提供を目的としており、特定の金融商品の売買を推奨するものではありません。投資判断は自己責任で行ってください。

**データソース**: Yahoo Finance、FRED (Federal Reserve Economic Data)、各種ニュースソース

**対象期間**: 2026-01-15 〜 2026-01-22

**作成日**: 2026-01-23
```

---

## 出力形式

### Markdown形式

- ファイル名: `weekly_report.md`
- 出力先: `articles/weekly_report/{YYYY-MM-DD}/02_edit/`
- 用途: note.com投稿用

### JSON形式

- ファイル名: `weekly_report.json`
- 出力先: `articles/weekly_report/{YYYY-MM-DD}/data/`
- 用途: 構造化データ、後続処理

**JSON構造**:
```json
{
  "metadata": {
    "report_date": "2026-01-22",
    "period_start": "2026-01-15",
    "period_end": "2026-01-22",
    "generated_at": "2026-01-23T10:00:00+09:00"
  },
  "highlights": {
    "bullets": [...],
    "sentiment": "bullish"
  },
  "indices": {
    "spx": { "return": 0.025, "factor": "..." },
    "ndx": { "return": 0.032, "factor": "..." }
  },
  "mag7": [...],
  "sectors": {
    "top": [...],
    "bottom": [...]
  },
  "macro": {...},
  "themes": [...],
  "upcoming": {
    "earnings": [...],
    "economic_indicators": [...]
  }
}
```

---

## 文字数目標（合計 5,000〜8,000字）

| セクション | 目標文字数 |
|-----------|-----------|
| 今週のハイライト | 600字 |
| 市場概況（指数+スタイル） | 700字 |
| MAG7+半導体（テーブル+トピック） | 1,200字 |
| セクター分析（上位3+下位3） | 1,800字 |
| マクロ経済・政策動向 | 600字 |
| 投資テーマ別動向 | 600字 |
| 来週の注目材料 | 400字 |
| **合計** | **約6,000字** |

---

## 関連ドキュメント

- プロジェクト計画書: `docs/project/project-21/project.md`
- 既存コマンド: `.claude/commands/generate-market-report.md`
- 既存テンプレート: `template/market_report/weekly_comment_template.md`
- サンプル: `template/market_report/sample/20251210_weekly_comment.md`

# dr-stock チャート修正プラン

## Context

dr-stock ワークフローで生成される株価チャート・ピア比較チャートに2つの問題がある：

1. **データ頻度の乖離**: SKILL.md では「株価（日足）5年分 OHLCV」と仕様に記載されているが、実際の `market-data.json` は月次終値（`monthly_closes`）のみ。結果、ローソク足が描けずラインチャート + 月次SMA 3/6ヶ月で代用
2. **チャート仕様の分散**: チャートの種類・期間・インジケーター等が `dr-report-generator.md`, `dr-visualizer.md`, `dr-stock-lead.md` の3箇所にハードコーディングされており管理困難

**目標**:
- 株価チャート・ピア比較を **日次データ・過去3年** に変更
- チャートテンプレートを **1箇所の設定ファイル** に一元管理

---

## 修正ファイル一覧

| # | ファイル | 変更内容 | 新規/修正 |
|---|---------|----------|----------|
| 1 | `.claude/skills/dr-stock/chart-templates.json` | チャートテンプレート設定ファイル | **新規作成** |
| 2 | `.claude/agents/deep-research/dr-stock-lead.md` | T1 タスク記述に日次OHLCV取得を明記 + T8 にテンプレート参照を追加 | 修正 |
| 3 | `.claude/agents/deep-research/dr-report-generator.md` | chart-templates.json の参照指示を追加 | 修正 |
| 4 | `.claude/agents/deep-research/dr-visualizer.md` | ハードコーディングされたチャートコード削除 → chart-templates.json 参照に変更 | 修正 |

---

## Step 1: chart-templates.json 作成

**ファイル**: `.claude/skills/dr-stock/chart-templates.json`

5種類のチャート仕様を一元管理する JSON 設定ファイル。

```json
{
  "version": "1.0",
  "defaults": {
    "width": 1200,
    "height": 600,
    "theme": "light",
    "dpi_scale": 2.0,
    "font_family": "Hiragino Sans, Yu Gothic, Meiryo, sans-serif"
  },
  "charts": {
    "price_chart": {
      "description": "株価チャート（ローソク足 + 移動平均線）",
      "type": "candlestick",
      "data_source": "daily_ohlcv",
      "period": "3y",
      "indicators": [
        {"type": "sma", "window": 20, "name": "SMA 20日"},
        {"type": "sma", "window": 50, "name": "SMA 50日"}
      ],
      "show_volume": true,
      "annotations": ["52w_high", "52w_low"],
      "output_file": "price_chart.png",
      "visualization_class": "CandlestickChart"
    },
    "peer_comparison": {
      "description": "ピア比較（相対パフォーマンス）",
      "type": "cumulative_returns",
      "data_source": "daily_ohlcv",
      "period": "3y",
      "normalize_to_100": true,
      "target_line_width": 3,
      "peer_line_width": 1.5,
      "output_file": "peer_comparison.png",
      "visualization_class": "LineChart"
    },
    "financial_trend": {
      "description": "財務指標トレンド",
      "type": "subplot_bars",
      "data_source": "financial_info",
      "metrics": [
        {"label": "営業利益率 (%)", "key": "operating_margin"},
        {"label": "純利益率 (%)", "key": "profit_margin"},
        {"label": "ROA (%)", "key": "return_on_assets"},
        {"label": "売上成長率 (%)", "key": "revenue_growth"}
      ],
      "layout": {"rows": 2, "cols": 2},
      "output_file": "financial_trend.png"
    },
    "valuation_heatmap": {
      "description": "バリュエーション比較ヒートマップ",
      "type": "heatmap",
      "data_source": "financial_info",
      "metrics": [
        {"label": "Trailing P/E", "key": "trailing_pe"},
        {"label": "Forward P/E", "key": "forward_pe"},
        {"label": "P/B", "key": "price_to_book"},
        {"label": "EV/EBITDA", "key": "ev_to_ebitda"},
        {"label": "P/S", "key": "price_to_sales"}
      ],
      "colorscale": "RdYlGn_r",
      "output_file": "valuation_heatmap.png",
      "visualization_class": "HeatmapChart"
    },
    "sector_performance": {
      "description": "セクターパフォーマンス（期間別リターン比較）",
      "type": "grouped_bars",
      "data_source": "returns",
      "periods": [
        {"label": "1ヶ月", "key": "1m"},
        {"label": "3ヶ月", "key": "3m"},
        {"label": "6ヶ月", "key": "6m"},
        {"label": "1年", "key": "1y"}
      ],
      "output_file": "sector_performance.png"
    }
  }
}
```

---

## Step 2: dr-stock-lead.md 修正

**ファイル**: `.claude/agents/deep-research/dr-stock-lead.md`

### 2a. T1 タスク記述に日次OHLCVデータ取得を明記

T1 TaskCreate の description に出力スキーマを追加:

```yaml
# 変更前（L308-325）
description: |
  yfinance/FRED を使用して市場データを取得する。
  ## 処理内容
  - 株価データ取得（{ticker} + ピアグループ、{analysis_period}分）
  - 財務指標取得（P/E, P/B, EV/EBITDA, ROE, ROA 等）
  - ピア全銘柄の同指標取得
  - 配当履歴取得

# 変更後
description: |
  yfinance/FRED を使用して市場データを取得する。

  ## 入力
  - {research_dir}/00_meta/research-meta.json

  ## 出力ファイル
  {research_dir}/01_data_collection/market-data.json

  ## 処理内容
  - 日次OHLCV取得（{ticker} + ピアグループ全銘柄、過去3年分）
  - 月次終値取得（{ticker} + ピアグループ全銘柄、{analysis_period}分）
  - 財務指標取得（P/E, P/B, EV/EBITDA, ROE, ROA 等）
  - ピア全銘柄の同指標取得
  - 配当履歴取得
  - 期間別リターン計算（1m, 3m, 6m, 1y, 3y, 5y）

  ## 出力スキーマ（必須フィールド）
  ```json
  {
    "metadata": {
      "target": "{ticker}",
      "peers": [...],
      "period": "{analysis_period}"
    },
    "stocks": {
      "{TICKER}": {
        "price_data": {
          "current": {"date": "...", "open": 0, "high": 0, "low": 0, "close": 0, "volume": 0},
          "period_stats": {"high_52w": 0, "low_52w": 0, ...},
          "returns": {"1m": 0, "3m": 0, "6m": 0, "1y": 0},
          "monthly_closes": {"YYYY-MM": 0.0, ...},
          "daily_ohlcv": [
            {"date": "YYYY-MM-DD", "open": 0, "high": 0, "low": 0, "close": 0, "volume": 0}
          ]
        },
        "financial_info": {...}
      }
    }
  }
  ```
```

### 2b. T8 タスク記述にチャートテンプレート参照を追加

T8 TaskCreate の description を修正:

```yaml
# 変更前（L469-491）
description: |
  分析結果からレポートとチャート生成スクリプトを出力する。
  ...
  ## 処理内容
  - {output_format} 形式でのレポート生成
  - 免責事項・出典の明記
  - チャート生成用 Python スクリプトの出力
  - スクリプトは src/analyze/visualization/ のクラスを使用

# 変更後
description: |
  分析結果からレポートとチャート生成スクリプトを出力する。
  ...
  ## 処理内容
  - {output_format} 形式でのレポート生成
  - 免責事項・出典の明記
  - チャート生成用 Python スクリプト（render_charts.py）の出力
  - **チャート仕様は `.claude/skills/dr-stock/chart-templates.json` を参照**
  - 可視化クラスは src/analyze/visualization/ を使用
  - daily_ohlcv データが存在する場合はローソク足チャートを生成
```

---

## Step 3: dr-report-generator.md 修正

**ファイル**: `.claude/agents/deep-research/dr-report-generator.md`

ファイル末尾（L365付近、「関連エージェント」セクションの前）に以下を追加:

```markdown
## チャート生成スクリプト（render_charts.py）の生成ルール

### チャートテンプレート設定

全チャートの仕様は以下の設定ファイルで一元管理されている:

```
.claude/skills/dr-stock/chart-templates.json
```

render_charts.py を生成する際は、**このファイルの仕様に従うこと**。
チャートの種類、データソース、期間、インジケーター等をハードコーディングせず、
chart-templates.json の定義に基づいてコードを生成する。

### データソースの判定

| chart-templates.json の data_source | market-data.json のフィールド | チャートタイプ |
|-------------------------------------|-------------------------------|---------------|
| `daily_ohlcv` | `stocks.{TICKER}.price_data.daily_ohlcv` | ローソク足 or 日次ライン |
| `financial_info` | `stocks.{TICKER}.financial_info` | バー / ヒートマップ |
| `returns` | `stocks.{TICKER}.price_data.returns` | グループバー |

### render_charts.py の実装パターン

1. **株価チャート（`price_chart`）**:
   - `daily_ohlcv` がある場合: `CandlestickChart` + `add_sma()` で日次ローソク足
   - ない場合: `monthly_closes` でラインチャート（フォールバック）

2. **ピア比較（`peer_comparison`）**:
   - `daily_ohlcv` がある場合: 日次終値から累積リターンを計算
   - ない場合: `monthly_closes` から累積リターンを計算

3. **財務トレンド / バリュエーション / セクター**: `financial_info` / `returns` を使用（既存通り）

### 必須インポート

```python
from analyze.visualization import (
    CandlestickChart,
    LineChart,
    PriceChartData,
    ChartConfig,
    ChartTheme,
    HeatmapChart,
    get_theme_colors,
)
```
```

---

## Step 4: dr-visualizer.md 修正

**ファイル**: `.claude/agents/deep-research/dr-visualizer.md`

チャートテンプレートのハードコーディングを削除し、chart-templates.json への参照に置き換える。

### 変更内容

1. L39-218 のチャート関数テンプレートコード（7つの `create_*` 関数）を削除
2. L220-272 のリサーチタイプ別チャートのハードコーディングを削除
3. L289-327 のカラーパレット・フォントサイズ・保存設定のハードコーディングを削除
4. 以下に置き換え:

```markdown
## チャートテンプレート設定

全チャートの仕様は以下の設定ファイルで一元管理されています:

```
.claude/skills/dr-stock/chart-templates.json
```

チャートの種類、データソース、期間、インジケーター等のカスタマイズは
この設定ファイルを編集してください。

## dr-stock での使用

**注意**: このエージェントは dr-stock ワークフローでは直接呼び出されません。
dr-report-generator が chart-templates.json に基づいて render_charts.py を生成し、
dr-stock-lead が Bash で実行します。

## 可視化モジュール参照

チャート生成には `src/analyze/visualization/` のクラスを使用:

| クラス/関数 | 用途 |
|------------|------|
| `CandlestickChart` | ローソク足チャート（日次OHLCV） |
| `LineChart` | ラインチャート（月次フォールバック） |
| `HeatmapChart` | ヒートマップ（バリュエーション比較） |
| `plot_cumulative_returns()` | 累積リターン比較 |

詳細: `src/analyze/visualization/__init__.py`
```

---

## 検証方法

### 1. 設定ファイルの妥当性確認

```bash
python -c "import json; json.load(open('.claude/skills/dr-stock/chart-templates.json'))"
```

### 2. エンドツーエンドテスト

```bash
/dr-stock MCO
```

以下を確認:
- [ ] `market-data.json` に `daily_ohlcv` フィールドが含まれる
- [ ] `daily_ohlcv` のデータポイント数が約750（3年 x 約250営業日）
- [ ] `render_charts.py` が chart-templates.json の仕様に基づいて生成される
- [ ] `price_chart.png` がローソク足で描画される（月次ラインではなく）
- [ ] `peer_comparison.png` が日次データで描画される
- [ ] 財務トレンド・バリュエーション・セクターは既存通り動作する

### 3. フォールバック確認

daily_ohlcv がない過去のデータでもエラーにならないことを確認:
- `research/DR_stock_20260121_NVDA/01_data_collection/market-data.json` のように monthly_closes のみのデータでも render_charts.py が正常にラインチャートを生成する

---

## データサイズへの影響

| 項目 | 現在 | 変更後 |
|------|------|--------|
| monthly_closes | 60ポイント/銘柄 (~2KB) | 変更なし（維持） |
| daily_ohlcv | なし | ~750ポイント/銘柄 (~50KB) |
| 6銘柄合計 | ~12KB | ~312KB（+300KB） |
| market-data.json 全体 | ~64KB | ~364KB |

許容範囲内。

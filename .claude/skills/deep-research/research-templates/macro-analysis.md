# Macro Analysis Template

マクロ経済分析のテンプレート

## 分析フレームワーク

### 1. 経済健全性

```json
{
  "economic_health": {
    "growth": {
      "real_gdp_yoy": null,
      "gdp_nowcast": null,
      "lei_index": null,
      "trend": "expanding | stable | contracting"
    },
    "employment": {
      "nonfarm_payrolls": null,
      "unemployment_rate": null,
      "labor_participation": null,
      "job_openings": null,
      "trend": "strong | moderate | weak"
    },
    "inflation": {
      "cpi_headline": null,
      "cpi_core": null,
      "pce_core": null,
      "wage_growth": null,
      "trend": "accelerating | stable | decelerating"
    }
  }
}
```

### 2. 金融政策

```json
{
  "monetary_policy": {
    "current": {
      "fed_funds_rate": null,
      "policy_stance": "restrictive | neutral | accommodative",
      "real_rate": null
    },
    "fomc": {
      "last_decision": "",
      "statement_tone": "hawkish | neutral | dovish",
      "dot_plot_median": null
    },
    "market_expectations": {
      "next_meeting_prob_cut": null,
      "next_meeting_prob_hold": null,
      "next_meeting_prob_hike": null,
      "year_end_rate_expectation": null
    },
    "quantitative": {
      "balance_sheet_size": null,
      "qt_pace": null
    }
  }
}
```

### 3. 市場影響

```json
{
  "market_implications": {
    "equities": {
      "rate_sensitivity": "high | medium | low",
      "recommended_sectors": [],
      "stance": "overweight | neutral | underweight"
    },
    "fixed_income": {
      "yield_curve_shape": "inverted | flat | normal | steep",
      "credit_spreads": null,
      "duration_recommendation": "long | neutral | short"
    },
    "currencies": {
      "dxy_trend": "strengthening | stable | weakening",
      "key_drivers": []
    }
  }
}
```

### 4. シナリオ分析

```json
{
  "scenarios": {
    "base_case": {
      "name": "",
      "probability": null,
      "gdp_growth": null,
      "year_end_ffr": null,
      "market_impact": ""
    },
    "bull_case": {
      "name": "",
      "probability": null,
      "gdp_growth": null,
      "year_end_ffr": null,
      "market_impact": ""
    },
    "bear_case": {
      "name": "",
      "probability": null,
      "gdp_growth": null,
      "year_end_ffr": null,
      "market_impact": ""
    }
  }
}
```

## 深度別チェックリスト

### Quick

- [ ] GDP、雇用、CPI の最新値
- [ ] 現行金利と次回会合見通し
- [ ] 市場への影響概要

### Standard

- [ ] 全主要経済指標
- [ ] Fed政策詳細 + 市場織り込み
- [ ] アセットクラス別影響
- [ ] 3シナリオ分析

### Comprehensive

- [ ] 全指標 + 地域別比較
- [ ] 詳細なFed分析 + 他中銀
- [ ] 詳細なポジショニング提案
- [ ] 感応度分析
- [ ] イベントカレンダー

## 主要経済指標

### 成長指標

| 指標 | FRED ID | 発表頻度 |
|------|---------|---------|
| 実質GDP | GDPC1 | 四半期 |
| GDPNow | - | 随時 |
| 景気先行指数 | - | 月次 |
| ISM製造業 | - | 月次 |
| ISM非製造業 | - | 月次 |

### 雇用指標

| 指標 | FRED ID | 発表頻度 |
|------|---------|---------|
| 非農業部門雇用者数 | PAYEMS | 月次 |
| 失業率 | UNRATE | 月次 |
| 労働参加率 | CIVPART | 月次 |
| 求人数 | JTSJOL | 月次 |
| ADP雇用 | - | 月次 |

### インフレ指標

| 指標 | FRED ID | 発表頻度 |
|------|---------|---------|
| CPI（総合） | CPIAUCSL | 月次 |
| CPI（コア） | CPILFESL | 月次 |
| PCE（コア） | PCEPILFE | 月次 |
| PPI | PPIACO | 月次 |
| 平均時給 | CES0500000003 | 月次 |

### 金利・金融

| 指標 | FRED ID | 発表頻度 |
|------|---------|---------|
| FFレート | FEDFUNDS | 日次 |
| 2年国債 | DGS2 | 日次 |
| 10年国債 | DGS10 | 日次 |
| 30年国債 | DGS30 | 日次 |
| IG スプレッド | BAMLC0A0CM | 日次 |
| HY スプレッド | BAMLH0A0HYM2 | 日次 |

## データソース

| データ | Tier 1 | Tier 2 | Tier 3 |
|--------|--------|--------|--------|
| 経済指標 | FRED | BLS | ニュース |
| Fed政策 | FOMC | CME FedWatch | アナリスト |
| 市場データ | Yahoo Finance | Bloomberg | - |
| 予測 | Fed | コンセンサス | アナリスト |

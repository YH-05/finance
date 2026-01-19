# Sector Analysis Template

セクター分析のテンプレート

## 分析フレームワーク

### 1. セクター概観

```json
{
  "sector_overview": {
    "sector_name": "",
    "market_cap_total": null,
    "constituent_count": null,
    "concentration": {
      "top_5_weight": null,
      "top_10_weight": null,
      "hhi_index": null
    },
    "sub_sectors": [
      {
        "name": "",
        "weight": null,
        "growth_rate": null
      }
    ]
  }
}
```

### 2. パフォーマンス分析

```json
{
  "performance": {
    "absolute": {
      "ytd": null,
      "1y": null,
      "3y_annualized": null,
      "5y_annualized": null
    },
    "relative": {
      "vs_sp500_ytd": null,
      "vs_sp500_1y": null,
      "rank_among_sectors": null
    },
    "risk_metrics": {
      "volatility_1y": null,
      "sharpe_ratio_1y": null,
      "max_drawdown_1y": null,
      "beta": null
    }
  }
}
```

### 3. バリュエーション

```json
{
  "valuation": {
    "sector_metrics": {
      "pe_median": null,
      "pe_average": null,
      "pb_median": null,
      "ev_ebitda_median": null,
      "dividend_yield_median": null
    },
    "historical": {
      "pe_vs_5y_avg": null,
      "pe_percentile": null,
      "premium_discount_vs_market": null
    },
    "dispersion": {
      "pe_range_low": null,
      "pe_range_high": null,
      "valuation_spread": "narrow | moderate | wide"
    }
  }
}
```

### 4. ローテーション分析

```json
{
  "rotation": {
    "momentum": {
      "fund_flow_3m": null,
      "etf_flow_3m": null,
      "trend": "inflow | outflow | neutral"
    },
    "relative_strength": {
      "vs_market_3m": null,
      "vs_market_6m": null,
      "trend": "strengthening | weakening | neutral"
    },
    "cycle_position": {
      "economic_cycle_correlation": null,
      "current_phase": "early | mid | late | recession",
      "leading_lagging": "leading | neutral | lagging"
    }
  }
}
```

### 5. 銘柄選定

```json
{
  "stock_selection": {
    "leaders": [
      {
        "ticker": "",
        "name": "",
        "weight": null,
        "ytd_return": null,
        "pe": null,
        "reason": ""
      }
    ],
    "laggards": [],
    "value_opportunities": [],
    "high_growth": [],
    "dividend_plays": []
  }
}
```

## 深度別チェックリスト

### Quick

- [ ] セクター基本情報
- [ ] YTD、1年パフォーマンス
- [ ] P/E、配当利回り
- [ ] 上位5銘柄リスト

### Standard

- [ ] セクター概観（構成、集中度）
- [ ] 全期間パフォーマンス + リスク指標
- [ ] 全バリュエーション指標 + ヒストリカル
- [ ] ローテーション分析
- [ ] 上位10銘柄 + バリュー機会

### Comprehensive

- [ ] 詳細なセクター構造分析
- [ ] サブセクター別分析
- [ ] 詳細なリスク分析
- [ ] 機関投資家フロー分析
- [ ] 全銘柄スクリーニング
- [ ] ポジショニング提案

## セクター一覧

| セクター | ETF | 景気感応度 |
|----------|-----|-----------|
| technology | XLK | 高 |
| healthcare | XLV | 低 |
| financials | XLF | 高 |
| consumer_discretionary | XLY | 高 |
| consumer_staples | XLP | 低 |
| industrials | XLI | 高 |
| energy | XLE | 高 |
| materials | XLB | 高 |
| utilities | XLU | 低 |
| real_estate | XLRE | 中 |
| communication_services | XLC | 中 |

## データソース

| データ | Tier 1 | Tier 2 | Tier 3 |
|--------|--------|--------|--------|
| 構成銘柄 | Yahoo Finance | ETF holdings | - |
| パフォーマンス | Yahoo Finance | Bloomberg | - |
| ファンドフロー | ETF.com | ニュース | - |
| 個別銘柄 | SEC EDGAR | Yahoo Finance | ニュース |

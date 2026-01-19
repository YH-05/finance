# Stock Analysis Template

個別銘柄分析のテンプレート

## 分析フレームワーク

### 1. 企業概要

```json
{
  "company_info": {
    "ticker": "",
    "name": "",
    "sector": "",
    "industry": "",
    "market_cap": null,
    "description": ""
  }
}
```

### 2. 財務健全性

```json
{
  "financial_health": {
    "revenue_trend": {
      "cagr_3y": null,
      "cagr_5y": null,
      "latest_yoy": null,
      "trend": "growing | stable | declining"
    },
    "profitability": {
      "gross_margin": null,
      "operating_margin": null,
      "net_margin": null,
      "roe": null,
      "roa": null,
      "roic": null
    },
    "balance_sheet": {
      "debt_to_equity": null,
      "current_ratio": null,
      "quick_ratio": null,
      "interest_coverage": null
    },
    "cash_flow": {
      "fcf_ttm": null,
      "fcf_margin": null,
      "fcf_conversion": null
    }
  }
}
```

### 3. バリュエーション

```json
{
  "valuation": {
    "absolute": {
      "dcf_value": null,
      "assumptions": {}
    },
    "relative": {
      "pe_ratio": null,
      "forward_pe": null,
      "pb_ratio": null,
      "ps_ratio": null,
      "ev_ebitda": null,
      "peg_ratio": null
    },
    "vs_industry": {
      "pe_premium_discount": null,
      "pb_premium_discount": null
    },
    "historical": {
      "pe_5y_avg": null,
      "pe_5y_high": null,
      "pe_5y_low": null,
      "current_percentile": null
    }
  }
}
```

### 4. ビジネス品質

```json
{
  "business_quality": {
    "competitive_advantage": {
      "moat_type": "none | narrow | wide",
      "moat_sources": [],
      "market_share": null
    },
    "management": {
      "ceo_tenure": null,
      "insider_ownership": null,
      "track_record": ""
    },
    "capital_allocation": {
      "dividend_yield": null,
      "buyback_yield": null,
      "rd_intensity": null,
      "capex_intensity": null
    }
  }
}
```

### 5. カタリスト・リスク

```json
{
  "catalysts": [
    {
      "type": "product | financial | regulatory | strategic",
      "description": "",
      "expected_date": "",
      "impact": "high | medium | low",
      "probability": "high | medium | low"
    }
  ],
  "risks": [
    {
      "type": "competitive | regulatory | operational | financial | macro",
      "description": "",
      "source": "10-K | analysis | news",
      "impact": "high | medium | low",
      "probability": "high | medium | low"
    }
  ]
}
```

## 深度別チェックリスト

### Quick

- [ ] 基本的な企業情報
- [ ] 直近2四半期の財務
- [ ] P/E、P/B、配当利回り
- [ ] 主要なカタリスト/リスク（各1-2件）

### Standard

- [ ] 企業概要・ビジネスモデル
- [ ] 3年間の財務トレンド
- [ ] 全主要バリュエーション指標
- [ ] 競争優位性分析
- [ ] カタリスト/リスク（各3-5件）
- [ ] 投資判断フレームワーク

### Comprehensive

- [ ] 詳細な企業分析
- [ ] 5年間の財務トレンド + セグメント分析
- [ ] DCFバリュエーション
- [ ] 詳細な競争分析
- [ ] 経営陣・ガバナンス分析
- [ ] 詳細なカタリスト/リスクマトリックス
- [ ] シナリオ分析（ブル/ベース/ベア）

## データソース

| データ | Tier 1 | Tier 2 | Tier 3 |
|--------|--------|--------|--------|
| 財務データ | SEC EDGAR | Yahoo Finance | ニュース |
| バリュエーション | Yahoo Finance | 分析記事 | - |
| カタリスト | 公式IR | ニュース | ブログ |
| リスク | 10-K | アナリスト | - |

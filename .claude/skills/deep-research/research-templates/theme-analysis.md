# Theme Analysis Template

テーマ投資分析のテンプレート

## 分析フレームワーク

### 1. テーマ定義

```json
{
  "theme_definition": {
    "name": "",
    "name_en": "",
    "description": "",
    "structural_drivers": [
      {
        "driver": "",
        "impact": "high | medium | low",
        "duration": "short | medium | long",
        "evidence": ""
      }
    ],
    "tam": {
      "current_year": null,
      "current_value": null,
      "currency": "USD",
      "cagr_5y": null,
      "forecast": []
    },
    "adoption_curve": {
      "current_penetration": null,
      "growth_phase": "early | growth | maturity | decline",
      "s_curve_position": "innovation | early_adopters | early_majority | late_majority | laggards"
    }
  }
}
```

### 2. バリューチェーン

```json
{
  "value_chain": {
    "layers": [
      {
        "layer": "infrastructure | platform | application | end_user",
        "name": "",
        "description": "",
        "profit_pool_share": null,
        "entry_barrier": "very_high | high | medium | low",
        "key_players": [
          {
            "ticker": "",
            "name": "",
            "role": ""
          }
        ]
      }
    ],
    "dynamics": {
      "power_concentration": "",
      "margin_pressure": "",
      "emerging_opportunity": ""
    }
  }
}
```

### 3. 投資機会

```json
{
  "investment_opportunities": {
    "pure_play": [
      {
        "ticker": "",
        "name": "",
        "theme_exposure": null,
        "revenue_from_theme_pct": null,
        "pe": null,
        "growth_rate": null,
        "risk_reward": "high | medium | low",
        "investment_thesis": "",
        "key_risks": []
      }
    ],
    "diversified": [],
    "etfs": [
      {
        "ticker": "",
        "name": "",
        "expense_ratio": null,
        "aum": null,
        "theme_purity": "high | medium | low"
      }
    ]
  }
}
```

### 4. タイミング分析

```json
{
  "timing": {
    "catalysts": [
      {
        "catalyst": "",
        "expected_date": "",
        "impact": "high | medium | low",
        "beneficiaries": []
      }
    ],
    "entry_point": {
      "current_valuation": "cheap | fair | expensive",
      "recommendation": "buy | accumulate | wait | reduce",
      "rationale": ""
    },
    "risks": [
      {
        "risk": "",
        "probability": "high | medium | low",
        "impact": "high | medium | low",
        "mitigation": ""
      }
    ]
  }
}
```

## 深度別チェックリスト

### Quick

- [ ] テーマ概要・定義
- [ ] TAM推計
- [ ] 主要2-3レイヤー
- [ ] 上位5銘柄 + 主要ETF

### Standard

- [ ] テーマ詳細 + 構造的ドライバー
- [ ] TAM + 普及曲線
- [ ] 全レイヤー + 主要企業
- [ ] 10-15銘柄 + ETF比較
- [ ] カタリスト + リスク

### Comprehensive

- [ ] 詳細なTAM + 地域別 + シナリオ
- [ ] 詳細な競争分析
- [ ] 全関連銘柄スクリーニング
- [ ] 詳細なイベントカレンダー
- [ ] ポートフォリオ構築提案

## 主要投資テーマ例

### テクノロジー

| テーマ | 説明 | 関連セクター |
|--------|------|-------------|
| AI・機械学習 | 人工知能技術の進化 | 半導体、ソフトウェア、クラウド |
| クラウドコンピューティング | オンプレミスからクラウドへの移行 | ソフトウェア、データセンター |
| サイバーセキュリティ | デジタル脅威への対応 | ソフトウェア |
| 5G・通信 | 次世代通信インフラ | 通信機器、半導体 |
| 半導体 | コンピューティングの基盤 | 製造装置、ファウンドリ、設計 |

### サステナビリティ

| テーマ | 説明 | 関連セクター |
|--------|------|-------------|
| クリーンエネルギー | 再生可能エネルギーへの転換 | ソーラー、風力、蓄電池 |
| EV・電動化 | 自動車の電動化 | 自動車、電池、充電インフラ |
| ESG投資 | 持続可能な投資 | 全セクター |
| 水資源 | 水インフラ・処理技術 | 公益、インフラ |

### 人口動態

| テーマ | 説明 | 関連セクター |
|--------|------|-------------|
| 高齢化社会 | 人口高齢化への対応 | ヘルスケア、シニア向けサービス |
| 新興国消費者 | 新興国の中間層拡大 | 消費財、小売 |
| デジタルネイティブ | Z世代・ミレニアル世代 | eコマース、SNS |

### ヘルスケア

| テーマ | 説明 | 関連セクター |
|--------|------|-------------|
| バイオテクノロジー | 遺伝子治療・創薬 | バイオ医薬品 |
| デジタルヘルス | ヘルステック | ソフトウェア、医療機器 |
| 医療機器 | 革新的医療デバイス | 医療機器 |

## データソース

| データ | Tier 1 | Tier 2 | Tier 3 |
|--------|--------|--------|--------|
| 市場規模 | 業界レポート | アナリスト | ニュース |
| 企業情報 | SEC EDGAR | Yahoo Finance | ニュース |
| 普及率 | 業界レポート | 調査機関 | ブログ |
| トレンド | Web検索 | ニュース | SNS |

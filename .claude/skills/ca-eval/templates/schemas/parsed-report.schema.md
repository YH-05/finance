# parsed-report.schema.md スキーマ

> 生成タスク: T2 | 生成エージェント: ca-report-parser
> 読み込み先: T4_claim_extractor（ca_candidates[]を主張抽出の出発点として使用）

## JSONスキーマ

```json
{
  "ticker": "AME",
  "company_name": "AMETEK, Inc.",
  "report_path": "analyst/raw/AME US.md",
  "parsed_at": "2026-02-18T14:54:00Z",
  "report_type": "unknown",
  "sections": [
    {
      "title": "投資判断推移・ESG評価・中長期競争優位・CAGR推定",
      "content": "ESGスコア58%でリスト追加。ニッチトップ戦略の概要、競争優位性、M&A体制、CAGRの推定を含む主要セクション",
      "summary": "2022年10月のリスト追加時の包括的評価。需要優位性（スイッチングコスト）・供給優位性（規模の経済・コストシナジー）の両面から競争優位性を整理。CAGR10%（売上8%+OPレバレッジ1%+自社株買い1%）を推定。"
    },
    {
      "title": "2024年08月09日 四半期決算フォローアップ",
      "content": "2024年Q2決算：売上YoY+5.4%（OG▲2%、M&A+8%、FX▲1%）、OPM25.8%、EPS1.66。ガイダンス引き下げ（通年+5~7%）。オートメーション在庫調整、ヘルスケアParagon関連調整が要因。競争優位性に変化なし、Buy継続。",
      "summary": "2024Q2決算：外部要因によるシクリカル影響を受けたが競争優位性に変化なし。M&A大型化の兆候に注視。"
    },
    {
      "title": "2024年06月21日 AMETEK 1x1面談（IR VP）",
      "content": "Churn Rateはほぼゼロ。医療21%まで拡大。OG/M&A比率が1:1へ変化（4%+4%=8%）。分散型組織体制の詳細。LT Financial Algorithm：EIG・EMGともに8%成長、30bp/年のCore EBIT Margin改善。",
      "summary": "IR面談を踏まえたCAGR微調整（10.5%→10%）。OG比率上昇でトップライン予見性向上。"
    },
    {
      "title": "事業特性・競争優位性詳細",
      "content": "ミッションクリティカルな財、ニッチトップ（市場シェア30~50%）、カスタマイズ製品。EIG（売上高68%、OPM25.5%）、EMG（売上高32%、OPM24.5%）。直販8割体制。R&D売上高5%超。2002年以来M&A件数86件。",
      "summary": "事業の競争優位性の核心：ミッションクリティカル×ニッチトップ×カスタマイズ＝高スイッチングコスト"
    },
    {
      "title": "Capital Allocation・生産体制",
      "content": "2012年以来累計USD10bn投下：M&A74%、配当11%、自社株買15%。Capex売上高比2%。ローコスト拠点（上海、メキシコ、セルビア、マレーシア、チェコ）。中国リスク対応済み（売上高比1割弱）。",
      "summary": "資本配分：M&A中心。ローコスト製造で高CF創出力を維持。"
    }
  ],
  "ca_candidates": [
    {
      "id": 1,
      "text": "ニッチトップ戦略：大手企業の参入リスクや顧客の内製化リスクの低いニッチ領域（市場規模USD150~400M）でシェア30~50%を確保。Mission Critical且つカスタマイズした財に特化することで高いスイッチングコストを有している。",
      "source_section": "投資判断推移・ESG評価・中長期競争優位・CAGR推定",
      "ca_type": "structural",
      "cagr_connected": true,
      "factual_claims": [
        "ニッチ領域の市場規模はUSD150~400M",
        "市場シェア30~50%を確保",
        "USD1bn以上の市場は回避",
        "Tier2サプライヤーとして大手（エマソン、GE、Honeywell等）とは直接競合しない"
      ]
    },
    {
      "id": 2,
      "text": "M&A実行能力と規律ある買収体制：社内11名のM&Aチームを持ち、2002年以来86件（年約4件、平均買収金額USD100M）の買収実績。ROIC20%超（goodwill除き）を維持した規律ある買収。3年後ROIC10%以上、IRR15%、1年目EPS accretiveの基準を満たす案件のみ実施。",
      "source_section": "投資判断推移・ESG評価・中長期競争優位・CAGR推定",
      "ca_type": "operational",
      "cagr_connected": true,
      "factual_claims": [
        "M&Aチーム11名（2024年時点）",
        "2002年以来累計M&A金額USD8.4bn、86件",
        "年平均4件、平均M&A金額USD100M",
        "ROIC20%超（goodwill除き）を維持",
        "買収基準：3年後ROIC10%以上、IRR15%、1年目EPS accretive",
        "売上高の買収ターゲットサイズ：USD50~200M"
      ]
    }
  ],
  "cagr_references": [
    {
      "context": "最新CAGR推定（2024年6月面談後修正）",
      "value": "10%",
      "period": "2024年以降（中長期）",
      "breakdown": {
        "revenue_growth": "8%（OG4%+M&A4%）",
        "op_leverage": "1%（30bp/年のCore EBIT Margin改善）",
        "buyback": "1%（2014-2023平均）"
      }
    },
    {
      "context": "旧CAGR推定（2022年10月時点）",
      "value": "10.5%",
      "period": "2022年以降（中長期）",
      "breakdown": {
        "revenue_growth": "9%（OG3%+M&A6%）",
        "op_leverage": "1~2%",
        "buyback": "0~1%"
      }
    }
  ],
  "key_themes": [
    "ニッチトップM&A戦略",
    "ミッションクリティカル×カスタマイズ→高スイッチングコスト",
    "規律あるM&A実行能力（ROIC維持）",
    "分散型組織・PMIノウハウ蓄積",
    "直販体制によるOPM改善",
    "医療・航空宇宙向けポートフォリオ拡大",
    "OG比率上昇（1:1）による安定成長"
  ],
  "data_limitations": [
    "SEC EDGAR MCPがEDGAR_IDENTITY未設定のため財務数値はレポートから抽出した参照値のみ",
    "レポート種別判定（①期初/②四半期レビュー）はPoC段階のためスキップ"
  ]
}
```

## フィールド説明

| フィールド | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| `ticker` | string | ✅ | 銘柄ティッカーシンボル |
| `company_name` | string | ✅ | 企業正式名称 |
| `report_path` | string | ✅ | 解析対象のアナリストレポートファイルパス |
| `parsed_at` | string (ISO 8601) | ✅ | パース実行時刻 |
| `report_type` | string | ✅ | レポート種別: `"initial"` / `"quarterly_review"` / `"unknown"` |
| `sections` | array[object] | ✅ | レポートのセクション一覧（時系列順） |
| `sections[].title` | string | ✅ | セクションタイトル（日付が含まれる場合は`YYYY年MM月DD日 {内容}`形式） |
| `sections[].content` | string | ✅ | セクション本文の要約（原文から重要箇所を抜粋） |
| `sections[].summary` | string | ✅ | セクションの1〜2文サマリー |
| `ca_candidates` | array[object] | ✅ | 競争優位性候補の一覧。フラット構造（旧 `sections[].advantage_candidates` 形式は廃止） |
| `ca_candidates[].id` | integer | ✅ | 候補ID（1から連番） |
| `ca_candidates[].text` | string | ✅ | 競争優位性の説明テキスト（レポートから抽出・整理） |
| `ca_candidates[].source_section` | string | ✅ | 抽出元のセクションタイトル |
| `ca_candidates[].ca_type` | string | ✅ | 競争優位性の種別: `"structural"` / `"operational"` / `"financial"` |
| `ca_candidates[].cagr_connected` | boolean | ✅ | CAGRとの関連性フラグ |
| `ca_candidates[].factual_claims` | array[string] | ✅ | 検証可能な事実的主張のリスト |
| `cagr_references` | array[object] | ✅ | レポート中のCAGR推定値の一覧（時系列、最新が先頭） |
| `cagr_references[].context` | string | ✅ | CAGR推定の背景・時点 |
| `cagr_references[].value` | string | ✅ | CAGR推定値（例: `"10%"`, `"+HSD"`） |
| `cagr_references[].period` | string | ✅ | 推定対象期間 |
| `cagr_references[].breakdown` | object | ✅ | CAGR内訳（revenue_growth, op_leverage, buyback 等） |
| `key_themes` | array[string] | ✅ | レポートの主要テーマ一覧（3〜10個） |
| `data_limitations` | array[string] | ✅ | データ上の制限事項（SEC EDGAR未取得等） |

## バリデーションルール

- `ca_candidates` はフラット配列として定義すること（旧実装の `sections[].advantage_candidates` ネスト構造は使用しない）
- `ca_candidates[].id` は1から始まる連番であること
- `ca_candidates[].ca_type` は `"structural"` / `"operational"` / `"financial"` のいずれかであること
- `cagr_references` の最初の要素が最新のCAGR推定値であること（時系列降順）
- `cagr_references[].value` は数値を含む文字列形式（`"10%"`, `"+HSD"`, `"+10% EPS CAGR"` 等）
- `report_type` が `"unknown"` の場合は `data_limitations` に理由を記載すること
- `sections` はレポートの時系列順（最新が後）で記載すること

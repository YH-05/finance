# fact-check.schema.md スキーマ

> 生成タスク: T5 | 生成エージェント: ca-fact-checker
> 読み込み先: T6_pattern_verifier（overall_statusを参照）、T7_report_generator（fact_check_status / rule9_applied を使用）、T9_accuracy（contradicted件数を検証）

## JSONスキーマ

```json
{
  "research_id": "CA_eval_20260218-1454_AME",
  "ticker": "AME",
  "verified_at": "2026-02-18T15:20:00Z",
  "verifier": "ca-eval-lead (T5直接実行)",
  "data_sources": {
    "primary": "analyst/raw/AME US.md",
    "sec_edgar_mcp": "unavailable（EDGAR_IDENTITY未設定）",
    "note": "ファクトチェックはアナリストレポートの内部一貫性チェックと記述の明示的矛盾検出に限定。SEC EDGAR直接照合は不可。"
  },
  "fact_checks": [
    {
      "claim_id": 1,
      "claim_title": "ニッチ市場特化型スイッチングコスト",
      "factual_claims_checked": [
        {
          "fact": "ニッチ領域の市場規模はUSD150~400M（USD1bn以上の大規模市場は回避）",
          "status": "verified",
          "evidence": "アナリストレポート（10/21/22）に「市場規模USD150~400Mの領域（大手企業の参入リスク/顧客の内製化リスクのあるUSD1bn以上の市場は回避している模様）」と明示",
          "confidence_impact": "none"
        },
        {
          "fact": "各ニッチ領域での市場シェア30~50%",
          "status": "verified",
          "evidence": "アナリストレポートに「ニッチトップ（市場シェア30~50%）」と明示",
          "confidence_impact": "none"
        },
        {
          "fact": "Tier2サプライヤーとして大手（エマソン、GE、Honeywell、Lockheed Martin等）と直接競合しない",
          "status": "verified",
          "evidence": "アナリストレポートに「プロセス機器：エマソン、GE、日立、ABB等のTier1企業と競合しているわけではなく、これら企業へ納入するTier2の位置づけ」と明示",
          "confidence_impact": "none"
        }
      ],
      "overall_status": "verified",
      "rule9_applied": false,
      "notes": "主要事実主張は全てレポートと整合。SEC EDGAR照合は不可だが内部一貫性は確認。"
    },
    {
      "claim_id": 2,
      "claim_title": "規律あるニッチM&A実行能力",
      "factual_claims_checked": [
        {
          "fact": "M&Aチーム11名（deal sourcing 4名、execution 6名、+1名=11名）",
          "status": "verified",
          "evidence": "アナリストレポート（2024年6月面談）に「M&A体制：11名からなるM&Aチームあり（2022時点から一名追加した模様）」と明示。",
          "confidence_impact": "none"
        },
        {
          "fact": "買収ターゲットサイズ：売上高USD50~200M（現在は大型化傾向：USD1bn超）",
          "status": "verified",
          "evidence": "レポートに「買収企業の規模：売上高USD50-200Mがレンジ」と明示。ただし2024Q2時点で「big business（USD1bn以上）を買うことになるだろう」とCEOコメント。",
          "confidence_impact": "minor_upward",
          "note": "大型化傾向は懸念材料として記録。従来の選定基準から逸脱する可能性。",
          "caveat": "「Bloomberg上に開示されているものに限定」との注記あり。実際の件数・金額はより大きい可能性。"
        }
      ],
      "overall_status": "verified_with_caveat",
      "rule9_applied": false,
      "notes": "主要数値は全てレポートと整合。大型化（USD1bn超）の兆候は投資リスクとしてアノテーション。"
    }
  ],
  "summary": {
    "total_facts_checked": 20,
    "verified": 18,
    "verified_with_caveat": 1,
    "unverifiable": 1,
    "contradicted": 0,
    "rule9_applications": 0
  },
  "overall_assessment": {
    "data_quality": "high_for_report_sourced_data",
    "sec_edgar_verification": "not_possible",
    "major_findings": [
      "全主要事実主張はアナリストレポート内で整合的（事実誤認なし）",
      "M&A大型化（USD1bn超）の兆候：従来のUSD50-200Mレンジから逸脱の可能性（Claim #2の留意点）",
      "Pricing Powerスプレッド：2021-2022の100bpから2024の50bpへ縮小（Claim #6の留意点）",
      "SEC EDGAR直接照合不可のため、財務数値の独立検証はできていない"
    ],
    "no_rule9_triggered": "事実誤認はゼロ。ルール9（事実誤認→confidence 10%）の適用なし。",
    "annotation": "全主張のconfidenceスコアを現状維持。SEC EDGAR照合が可能となった場合、ROIC20%・Capex比率2%・EPS Accretive実績を再検証すべき。"
  }
}
```

## フィールド説明

| フィールド | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| `research_id` | string | ✅ | ワークフロー固有ID |
| `ticker` | string | ✅ | 銘柄ティッカーシンボル |
| `verified_at` | string (ISO 8601) | ✅ | ファクトチェック実行時刻 |
| `verifier` | string | ✅ | 実行エージェント名 |
| `data_sources` | object | ✅ | 照合に使用したデータソースの情報 |
| `data_sources.primary` | string | ✅ | 主要データソースのファイルパス |
| `data_sources.sec_edgar_mcp` | string | ✅ | SEC EDGAR MCPの利用状況と制限説明 |
| `data_sources.note` | string | ✅ | ファクトチェックの実施範囲の説明 |
| `fact_checks` | array[object] | ✅ | 主張別のファクトチェック結果一覧 |
| `fact_checks[].claim_id` | integer | ✅ | 対応する主張ID（claims.jsonのclaim_idと一致） |
| `fact_checks[].claim_title` | string | ✅ | 主張タイトル（claims.jsonのtitleと一致） |
| `fact_checks[].factual_claims_checked` | array[object] | ✅ | 検証した個別事実のネスト配列 |
| `fact_checks[].factual_claims_checked[].fact` | string | ✅ | 検証した事実的主張のテキスト |
| `fact_checks[].factual_claims_checked[].status` | string | ✅ | 検証結果: `"verified"` / `"verified_with_caveat"` / `"unverifiable"` / `"contradicted"` |
| `fact_checks[].factual_claims_checked[].evidence` | string | ✅ | 検証根拠（出典箇所と引用） |
| `fact_checks[].factual_claims_checked[].confidence_impact` | string | ✅ | 確信度への影響: `"none"` / `"minor_upward"` / `"minor_downward"` / `"major_upward"` / `"major_downward"` |
| `fact_checks[].factual_claims_checked[].note` | string | - | 追加の注記（懸念事項、留意点） |
| `fact_checks[].factual_claims_checked[].caveat` | string | - | 検証の限界・条件付き承認の説明 |
| `fact_checks[].overall_status` | string | ✅ | 主張全体の検証ステータス: `"verified"` / `"verified_with_caveat"` / `"unverifiable"` / `"contradicted"` |
| `fact_checks[].rule9_applied` | boolean | ✅ | ルール9（事実誤認→即却下）を適用したかどうか |
| `fact_checks[].notes` | string | ✅ | ファクトチェック結果の総評 |
| `summary` | object | ✅ | ファクトチェック全体のサマリー |
| `summary.total_facts_checked` | integer | ✅ | 検証した事実の総件数 |
| `summary.verified` | integer | ✅ | 検証済みの件数 |
| `summary.verified_with_caveat` | integer | ✅ | 条件付き検証済みの件数 |
| `summary.unverifiable` | integer | ✅ | 検証不能の件数 |
| `summary.contradicted` | integer | ✅ | 矛盾が検出された件数 |
| `summary.rule9_applications` | integer | ✅ | ルール9を適用した主張の件数 |
| `overall_assessment` | object | ✅ | ファクトチェック全体の評価 |
| `overall_assessment.data_quality` | string | ✅ | データ品質評価: `"high_for_report_sourced_data"` / `"medium"` / `"low"` 等 |
| `overall_assessment.sec_edgar_verification` | string | ✅ | SEC EDGAR照合の可否: `"completed"` / `"partial"` / `"not_possible"` |
| `overall_assessment.major_findings` | array[string] | ✅ | 主要な発見事項の一覧 |
| `overall_assessment.no_rule9_triggered` | string | - | ルール9非適用の理由（contradicted = 0の場合） |
| `overall_assessment.annotation` | string | - | 追加のアノテーション・推奨事項 |

## バリデーションルール

- `fact_checks[].factual_claims_checked` は `claims.json` の `factual_claims` と対応していること（すべての事実的主張を検証すること）
- `fact_checks[].factual_claims_checked[].status` が `"contradicted"` の場合、対応する主張に `rule9_applied: true` が設定されていること（ただしT4でルール9の自動適用が行われている場合は除く）
- `summary.total_facts_checked` = `summary.verified` + `summary.verified_with_caveat` + `summary.unverifiable` + `summary.contradicted` であること
- `summary.rule9_applications` は `fact_checks[].rule9_applied: true` の件数と一致すること
- `overall_assessment.sec_edgar_verification` が `"not_possible"` の場合、`data_sources.note` に理由が記載されていること
- `fact_checks` の `claim_id` は `claims.json` に存在する全ての `claim_id` を網羅すること

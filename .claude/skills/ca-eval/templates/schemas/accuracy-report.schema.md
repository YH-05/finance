# accuracy-report.schema.md スキーマ

> 生成タスク: T9 | 生成エージェント: ca-report-generator（精度チェックフェーズ）または ca-eval-lead
> 読み込み先: research-meta.json（T9のtask_results.verdict として記録される）

## JSONスキーマ

```json
{
  "research_id": "CA_eval_20260218-1454_AME",
  "ticker": "AME",
  "mode": "simplified",
  "generated_at": "2026-02-18T16:00:00Z",
  "kb_version": "v1.0.0",
  "mode_determination": {
    "reason": "AMEはPhase 2データ（analyst/phase2_KY/*AME*.md）が存在しないため簡易モードを適用",
    "phase2_data_searched": "analyst/phase2_KY/*AME*",
    "phase2_data_found": false,
    "full_mode_eligible_tickers": ["CHD", "COST", "LLY", "MNST", "ORLY"]
  },
  "full_mode_results": null,
  "simplified_mode_results": {
    "check_id": "S-8",
    "check_description": "contradicted事実に対するルール9自動適用（confidence → 10%）の確認",
    "fact_check_source": "research/CA_eval_20260218-1454_AME/03_verification/fact-check.json",
    "contradicted_claims": [],
    "contradicted_count": 0,
    "rule9_applied_count": 0,
    "overall_verdict": "pass",
    "pass": true,
    "annotation": "contradictedと判定された事実の主張は0件。ルール9（事実誤認→confidence 10%）の適用対象なし。簡易モードのS-8チェックは合格。",
    "caveats": [
      "SEC EDGAR MCPが利用不可のため、ファクトチェックはアナリストレポートの内部一貫性チェックに限定。外部データソースとの照合は実施されていない。",
      "EDGAR_IDENTITYが設定された環境で再実行した場合、contradicted件数が変化する可能性がある。",
      "verified_with_caveat（M&A大型化リスク）: 1件存在するが、これはcontradictedではなく留意事項のアノテーションであるため、S-8チェックの対象外。"
    ]
  },
  "overall_assessment": {
    "accuracy_verdict": "pass",
    "confidence_level": "low",
    "reason": "簡易モードのS-8チェックのみ実施。SEC EDGAR非利用のため、チェックの信頼性は低い。Phase 2データ（Y評価値）との比較による精度検証は未実施。",
    "recommendation": "AMEのPhase 2評価（Y評価値）が蓄積された後、フルモードで再評価することを推奨。特にClaim #2（M&A実行能力）のCAGR confidence（70%条件付き）についてのY評価との比較が有益。"
  }
}
```

## フィールド説明

| フィールド | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| `research_id` | string | ✅ | ワークフロー固有ID |
| `ticker` | string | ✅ | 銘柄ティッカーシンボル |
| `mode` | string | ✅ | 精度チェックモード: `"simplified"` / `"full"` |
| `generated_at` | string (ISO 8601) | ✅ | 精度チェック実行時刻 |
| `kb_version` | string | ✅ | 使用したKBのバージョン（例: `"v1.0.0"`） |
| `mode_determination` | object | ✅ | モード判定の詳細 |
| `mode_determination.reason` | string | ✅ | モード判定の根拠説明 |
| `mode_determination.phase2_data_searched` | string | ✅ | Phase 2データの検索パターン（glob形式） |
| `mode_determination.phase2_data_found` | boolean | ✅ | Phase 2データが見つかったかどうか |
| `mode_determination.full_mode_eligible_tickers` | array[string] | ✅ | フルモード対応可能な銘柄一覧（Phase 2データ保有銘柄） |
| `full_mode_results` | object \| null | ✅ | フルモードの精度チェック結果（`mode: "full"` の場合のみ、`"simplified"` の場合は `null`） |
| `simplified_mode_results` | object \| null | ✅ | 簡易モードの精度チェック結果（`mode: "simplified"` の場合のみ、`"full"` の場合は `null`） |
| `simplified_mode_results.check_id` | string | ✅ | チェックID（例: `"S-8"`） |
| `simplified_mode_results.check_description` | string | ✅ | チェック内容の説明 |
| `simplified_mode_results.fact_check_source` | string | ✅ | 参照したfact-check.jsonのファイルパス |
| `simplified_mode_results.contradicted_claims` | array | ✅ | ルール9が適用された主張の一覧（0件の場合は空配列） |
| `simplified_mode_results.contradicted_count` | integer | ✅ | contradicted事実の件数 |
| `simplified_mode_results.rule9_applied_count` | integer | ✅ | ルール9を適用した主張の件数 |
| `simplified_mode_results.overall_verdict` | string | ✅ | チェック結果: `"pass"` / `"fail"` |
| `simplified_mode_results.pass` | boolean | ✅ | チェック合格フラグ |
| `simplified_mode_results.annotation` | string | ✅ | チェック結果の説明 |
| `simplified_mode_results.caveats` | array[string] | ✅ | チェックの限界・留意事項のリスト |
| `overall_assessment` | object | ✅ | 精度チェック全体の評価 |
| `overall_assessment.accuracy_verdict` | string | ✅ | 総合判定: `"pass"` / `"fail"` / `"conditional_pass"` |
| `overall_assessment.confidence_level` | string | ✅ | 判定の信頼性: `"high"` / `"medium"` / `"low"` |
| `overall_assessment.reason` | string | ✅ | 総合判定の根拠説明 |
| `overall_assessment.recommendation` | string | - | 今後の推奨アクション |

## バリデーションルール

- `mode` は `"simplified"` または `"full"` のいずれかであること
- `mode` が `"simplified"` の場合: `simplified_mode_results` は必須、`full_mode_results` は `null`
- `mode` が `"full"` の場合: `full_mode_results` は必須、`simplified_mode_results` は `null`
- `mode_determination.phase2_data_found` が `false` の場合、`mode` は `"simplified"` であること
- `mode_determination.phase2_data_found` が `true` の場合、`mode` は `"full"` であること
- `simplified_mode_results.contradicted_count` は fact-check.json の `summary.contradicted` と一致すること
- `simplified_mode_results.rule9_applied_count` は fact-check.json の `summary.rule9_applications` と一致すること
- `simplified_mode_results.overall_verdict` と `overall_assessment.accuracy_verdict` は整合すること（`"pass"` / `"fail"` の判定が一致）
- `overall_assessment.accuracy_verdict` は research-meta.json の `task_results.T9_accuracy.verdict` と一致すること
- `simplified_mode_results.contradicted_claims` が1件以上の場合、`simplified_mode_results.pass` は `false` であること

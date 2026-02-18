# pattern-verification.schema.md スキーマ

> 生成タスク: T6 | 生成エージェント: ca-pattern-verifier
> 読み込み先: T7_report_generator（pattern_results[]のfinal_confidenceとpatterns_detectedを使用）

## JSONスキーマ

```json
{
  "research_id": "CA_eval_20260218-1454_AME",
  "ticker": "AME",
  "verified_at": "2026-02-18T15:25:00Z",
  "verifier": "ca-eval-lead (T6直接実行)",
  "kb2_patterns_applied": {
    "rejection_patterns": ["A", "B", "C", "D", "E", "F", "G"],
    "high_eval_patterns": ["I", "II", "III", "IV", "V"]
  },
  "pattern_results": [
    {
      "claim_id": 1,
      "claim_title": "ニッチ市場特化型スイッチングコスト（ミッションクリティカル×カスタマイズ）",
      "rejection_patterns_detected": [],
      "high_eval_patterns_detected": [
        {
          "pattern": "III",
          "name": "能力>結果（プロセスの評価）",
          "match_strength": "strong",
          "reasoning": "スイッチングコスト・ミッションクリティカル性・カスタマイズという構造的属性（能力）として正しく記述。市場シェア30~50%という結果を根拠に使いつつ、その背後の構造が優位性として抽出されている。"
        },
        {
          "pattern": "IV",
          "name": "構造的な市場ポジション",
          "match_strength": "moderate",
          "reasoning": "ニッチ計測・プロセス機器市場（USD150~400M）×Tier2ポジション×ミッションクリティカル性の合致は構造的市場ポジションパターンに合致。ただしORLY（フラグメント市場×密度）ほどの明確な市場構造分析がなく、合致の論理がやや弱い。"
        }
      ],
      "pattern_G_analysis": {
        "detected": true,
        "severity": "moderate",
        "reasoning": "同じニッチTier2計測機器プレイヤー（Roper Technologies、Fortive、MTS Systems等）との具体的比較が欠如。Tier1企業（エマソン、GE）との差別化は示されているが、純粋競合との比較がない（パターンG部分適用）。"
      },
      "confidence_adjustment": {
        "direction": "none",
        "reason": "高評価パターンIII・IVが検出されPatternG（moderate）が確認されるが、claims.jsonの70%評価と整合的。調整不要。"
      },
      "final_confidence": 70,
      "cagr_pattern_assessment": {
        "pattern_II_match": "partial",
        "reasoning": "スイッチングコスト→低Churn→OG4%の接続は1-2ステップで比較的直接的。ただしChurn率の定量開示がなく検証可能性に限界あり（パターンII部分適用）。"
      }
    },
    {
      "claim_id": 2,
      "claim_title": "規律あるニッチM&A実行能力（選定・PMI・ガバナンス体制）",
      "rejection_patterns_detected": [],
      "high_eval_patterns_detected": [
        {
          "pattern": "I",
          "name": "定量的裏付けのある差別化",
          "match_strength": "strong",
          "reasoning": "86件・USD8.4bn・ROIC20%超（goodwill除き）・IRR15%基準・11名チームという複数の定量的裏付けあり。"
        },
        {
          "pattern": "III",
          "name": "能力>結果（プロセスの評価）",
          "match_strength": "strong",
          "reasoning": "M&A実行能力の「選定基準」「チーム構成」「Playbook蓄積」「断念の規律」が能力の証明として機能している。"
        },
        {
          "pattern": "IV",
          "name": "構造的な市場ポジション",
          "match_strength": "moderate",
          "reasoning": "ニッチ計測機器市場のフラグメント性×AMETEKのM&A実行能力はORLY#5（90%）に類似。ただしフラグメント度の定量的論拠が欠如。"
        }
      ],
      "rejection_pattern_analysis": {
        "pattern_A": "not_detected（86件の実績は結果だが、選定基準・Playbookという能力が主張の核心）",
        "pattern_G": "partial（ITW・Roperとの具体的M&A能力比較が欠如。ROICの数値比較があれば解消）"
      },
      "confidence_adjustment": {
        "direction": "none",
        "reason": "高評価パターンI・III・IV（moderate）が揃う。PatternG（partial）が確認されるが70%評価と整合。"
      },
      "final_confidence": 70,
      "cagr_pattern_assessment": {
        "pattern_II_match": "moderate",
        "reasoning": "M&A4%寄与→CAGR10%の40%担当。2002年以来のトラックレコードが検証可能。ただし大型化（USD1bn超）に伴うdownsideリスクで不確実性上昇。"
      }
    }
  ],
  "systematic_pattern_analysis": {
    "most_common_rejection_pattern": "G（純粋競合対比不明）",
    "pattern_G_frequency": "6/7主張で部分的に検出（ほぼ全主張で純粋競合比較が不足）",
    "pattern_B_concerns": "Claim #3（集中購買）で業界共通能力の疑いあり",
    "strongest_high_eval_patterns": "パターンIII（能力>結果）が最も多く検出。パターンI（定量的裏付け）は部分的。パターンIV（構造的市場ポジション）は部分的。",
    "overall_assessment": "主張の構造は概ね良好（パターンA・Fはわずか2件のみ強度高く検出）。最大の課題は純粋競合比較の欠如（パターンG）。"
  },
  "consistency_check": {
    "internal_consistency": "good",
    "cross_claim_consistency": [
      {
        "issue": "Claim #1・#2・#3・#4・#5は相互補完関係にあり整合的",
        "status": "consistent"
      },
      {
        "issue": "Claim #6（Pricing Power）はClaim #1の派生結果として整合",
        "status": "consistent_but_redundant"
      },
      {
        "issue": "Claim #7（ポートフォリオ分散）はClaim #2・#5の結果として整合",
        "status": "consistent_but_result"
      }
    ],
    "cagr_consistency": "CAGR10%（売上8%+OPレバ1%+自社株1%）の各要素にClaim #1-#5が対応しており整合的"
  },
  "summary": {
    "rejection_patterns_detected": {
      "A": 2,
      "B": 1,
      "C": 0,
      "D": 1,
      "E": 0,
      "F": 1,
      "G": 4
    },
    "high_eval_patterns_detected": {
      "I": 3,
      "II": 0,
      "III": 5,
      "IV": 2,
      "V": 0
    },
    "confidence_adjustments_made": 0,
    "overall_pattern_quality": "moderate_to_good"
  }
}
```

## フィールド説明

| フィールド | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| `research_id` | string | ✅ | ワークフロー固有ID |
| `ticker` | string | ✅ | 銘柄ティッカーシンボル |
| `verified_at` | string (ISO 8601) | ✅ | パターン検証実行時刻 |
| `verifier` | string | ✅ | 実行エージェント名 |
| `kb2_patterns_applied` | object | ✅ | 適用したKB2パターンの一覧 |
| `kb2_patterns_applied.rejection_patterns` | array[string] | ✅ | 適用した却下パターンID一覧（A〜G） |
| `kb2_patterns_applied.high_eval_patterns` | array[string] | ✅ | 適用した高評価パターンID一覧（I〜V） |
| `pattern_results` | array[object] | ✅ | 主張別のパターン検証結果一覧 |
| `pattern_results[].claim_id` | integer | ✅ | 対応する主張ID（claims.jsonのclaim_idと一致） |
| `pattern_results[].claim_title` | string | ✅ | 主張タイトル（claims.jsonのtitleと一致） |
| `pattern_results[].rejection_patterns_detected` | array[object] | ✅ | 検出された却下パターンの一覧（未検出の場合は空配列） |
| `pattern_results[].rejection_patterns_detected[].pattern` | string | ✅ | パターンID（A〜G） |
| `pattern_results[].rejection_patterns_detected[].name` | string | ✅ | パターン名称 |
| `pattern_results[].rejection_patterns_detected[].match_strength` | string | ✅ | 一致強度: `"strong"` / `"moderate"` / `"weak"` |
| `pattern_results[].rejection_patterns_detected[].reasoning` | string | ✅ | 検出根拠の説明 |
| `pattern_results[].high_eval_patterns_detected` | array[object] | ✅ | 検出された高評価パターンの一覧（未検出の場合は空配列） |
| `pattern_results[].high_eval_patterns_detected[].pattern` | string | ✅ | パターンID（I〜V） |
| `pattern_results[].high_eval_patterns_detected[].name` | string | ✅ | パターン名称 |
| `pattern_results[].high_eval_patterns_detected[].match_strength` | string | ✅ | 一致強度: `"strong"` / `"moderate"` / `"weak"` / `"partial"` |
| `pattern_results[].high_eval_patterns_detected[].reasoning` | string | ✅ | 検出根拠の説明 |
| `pattern_results[].pattern_G_analysis` | object | - | パターンG（純粋競合比較不足）の詳細分析（検出時） |
| `pattern_results[].pattern_G_analysis.detected` | boolean | ✅ | パターンG検出フラグ |
| `pattern_results[].pattern_G_analysis.severity` | string | ✅ | 深刻度: `"strong"` / `"moderate"` / `"weak"` |
| `pattern_results[].pattern_G_analysis.reasoning` | string | ✅ | 検出根拠 |
| `pattern_results[].rejection_pattern_analysis` | object | - | 各却下パターンの詳細分析（テキスト形式、主要パターンのみ） |
| `pattern_results[].confidence_adjustment` | object | ✅ | 確信度の調整内容 |
| `pattern_results[].confidence_adjustment.direction` | string | ✅ | 調整方向: `"upward"` / `"downward"` / `"slight_downward"` / `"slight_upward"` / `"none"` |
| `pattern_results[].confidence_adjustment.reason` | string | ✅ | 調整の理由 |
| `pattern_results[].final_confidence` | integer | ✅ | 最終確信度スコア（10/30/50/70/90の5段階） |
| `pattern_results[].cagr_pattern_assessment` | object | ✅ | CAGR接続のパターン評価 |
| `pattern_results[].cagr_pattern_assessment.pattern_II_match` | string | ✅ | パターンII（直接的CAGR接続）との一致度: `"strong"` / `"moderate"` / `"partial"` / `"none"` |
| `pattern_results[].cagr_pattern_assessment.reasoning` | string | ✅ | 評価の根拠 |
| `systematic_pattern_analysis` | object | ✅ | 全主張を通じたパターンの傾向分析 |
| `systematic_pattern_analysis.most_common_rejection_pattern` | string | ✅ | 最も多く検出された却下パターン |
| `systematic_pattern_analysis.pattern_G_frequency` | string | ✅ | パターンGの検出頻度（例: `"6/7主張"`) |
| `systematic_pattern_analysis.strongest_high_eval_patterns` | string | ✅ | 最も多く検出された高評価パターン |
| `systematic_pattern_analysis.overall_assessment` | string | ✅ | 全体的なパターン品質の評価 |
| `consistency_check` | object | ✅ | 主張間の整合性チェック結果 |
| `consistency_check.internal_consistency` | string | ✅ | 内部整合性評価: `"good"` / `"moderate"` / `"poor"` |
| `consistency_check.cross_claim_consistency` | array[object] | ✅ | 主張間の整合性分析 |
| `consistency_check.cagr_consistency` | string | ✅ | CAGR推定との整合性評価 |
| `summary` | object | ✅ | パターン検証全体のサマリー |
| `summary.rejection_patterns_detected` | object | ✅ | 各却下パターンの検出件数（A〜G全て記載） |
| `summary.high_eval_patterns_detected` | object | ✅ | 各高評価パターンの検出件数（I〜V全て記載） |
| `summary.confidence_adjustments_made` | integer | ✅ | 確信度を実際に調整した主張の件数 |
| `summary.overall_pattern_quality` | string | ✅ | 全体的なパターン品質評価 |

## バリデーションルール

- `pattern_results` はclaims.jsonの全主張に対応する要素を含むこと（claim_idの網羅性）
- `pattern_results[].final_confidence` は 10/30/50/70/90 の5段階のいずれかであること
- `pattern_results[].confidence_adjustment.direction` が `"none"` 以外の場合、`final_confidence` がclaims.jsonの `confidence.ca_score` と異なること
- `summary.rejection_patterns_detected` と `summary.high_eval_patterns_detected` は全パターンID（A〜GおよびI〜V）のキーを含むこと
- `pattern_results[].rejection_patterns_detected` と `pattern_results[].high_eval_patterns_detected` が共に空配列の場合、`confidence_adjustment.direction` は `"none"` であること
- `cagr_pattern_assessment.pattern_II_match` が `"strong"` の場合、高い `final_confidence`（70以上）が期待されること

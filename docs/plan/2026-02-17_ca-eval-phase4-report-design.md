# CA-Eval Phase 4 レポート生成・検証 詳細設計書

> 作成日: 2026-02-17
> 前提: [CA-Evalワークフロー詳細設計書](../../analyst/claude_code/workflow_design.md)
> 関連: [暗黙知拡充ループ設計書](2026-02-17_ca-eval-phase4-5-knowledge-expansion-loop.md)

---

## Context

CA-Eval Phase 4（T7: レポート生成、T8: 3層検証、T9: 精度検証）は設計レベルで仕様が存在するが、以下が不足している:

- report.md のセクション構成・分量・テンプレートが概要レベル
- T8（3層検証）のチェック項目・重大度・自動修正ロジックが未詳細
- T9（精度検証）の簡易モード（Phase 2の5銘柄以外）が未定義

本設計書で Phase 4 の実装に必要な全仕様を確定する。

**要件**:
- 想定読者: Y + 他のチームメンバー（文脈説明を含む）
- 分量: 5-8ページ相当
- T8: 問題検出時は自動修正 → verified-report.md
- T9: 5銘柄はフル精度検証、それ以外は簡易版を常に実行

---

## 1. report.md テンプレート仕様

### 1.1 セクション構成と分量

```
report.md（全体 5-8ページ相当）
├── 1. ヘッダー情報（~0.3ページ）
├── 2. 評価サマリーテーブル（~0.5ページ）
├── 3. 個別主張セクション x N件（~3-5ページ、各 0.4-0.6ページ）
├── 4. CAGR接続サマリー（~0.5ページ）
├── 5. 警鐘セクション（~0.3ページ）
├── 6. 全体フィードバックセクション（~0.3ページ）
└── 7. メタデータ・技術情報（折りたたみ、~0.1ページ）
```

### 1.2 セクション1: ヘッダー情報

```markdown
# [TICKER] 競争優位性評価レポート

| 項目 | 値 |
|------|-----|
| **対象銘柄** | [TICKER]（[企業名]） |
| **入力レポート** | [report_source]（①期初 / ②四半期 / 混合） |
| **生成日** | [YYYY-MM-DD] |
| **リサーチID** | [research_id] |
| **データソース** | SEC EDGAR (MCP), アナリストレポート, 業界分析 |
| **KBバージョン** | [kb_version] |
| **主張数** | 競争優位性 [N]件 / CAGR接続 [N]件 / 事実 [N]件 |
```

### 1.3 セクション2: 評価サマリーテーブル

Phase 2のYの評価テーブル形式（横型テーブル）に合わせる。

```markdown
## 評価サマリー

| # | 優位性 | AI確信度 | CAGR接続 | CAGR確信度 |
|---|--------|---------|----------|-----------|
| 1 | [主張テキスト（30字以内に要約）] | [X]% | [接続先・寄与内容] | [Y]% |
| 2 | ... | ... | ... | ... |

### 確信度分布

| 確信度 | AI評価 | KY基準値 | 判定 |
|--------|--------|---------|------|
| 90%（かなり納得） | [N]件 ([X]%) | 6% | [OK/要確認] |
| 70%（おおむね納得） | [N]件 ([X]%) | 26% | [OK/要確認] |
| 50%（まあ納得） | [N]件 ([X]%) | 35% | [OK/要確認] |
| 30%（あまり納得しない） | [N]件 ([X]%) | 26% | [OK/要確認] |
| 10%（却下） | [N]件 ([X]%) | 6% | [OK/要確認] |

### ファクトチェック結果サマリー

- verified: [N]件 / contradicted: [N]件 / unverifiable: [N]件 / not_checked: [N]件
```

**判定ロジック**: AI出現率がKY基準値から15%以上乖離 → 「要確認」。

### 1.4 セクション3: 個別主張セクション（テンプレート）

```markdown
---

### #[N]: [主張テキスト]

**分類**: [descriptive_label]
**レポート種別**: ①期初投資仮説レポート / ②四半期継続評価レポート
[②の場合のみ表示:]
> ⚠️ この主張は四半期レビュー（②）から抽出されました。
> 期初レポート（①）での妥当性を再検討してください。

#### AI評価: [ランク名]（[X]%）

[2-3文のコメント。5層評価に基づく。結論→根拠→改善提案の順。]
[重要な指摘は<u>下線</u>で強調]

#### CAGR接続

| パラメータ | AI確信度 | コメント |
|-----------|---------|---------|
| 売上成長寄与 +X% | [Y]% | [1-2文] |
| マージン改善寄与 +X% | [Z]% | [1-2文] |

#### 根拠（アナリストレポートより）

[evidence_from_report]

#### ルール適用結果

| ルール | 判定 | 根拠 |
|--------|------|------|
| ルール[N] | [verdict] | [reasoning（1文）] |

※ 該当ルールのみ記載。

#### 検証結果

- **ファクトチェック**: [verified/contradicted/unverifiable/not_checked]
  - [検証の詳細（1-2文）]
- **パターン照合**:
  - 高評価: [該当パターン名 + 概要] / なし
  - 却下: [該当パターン名 + 概要] / なし

---

**納得度:**  10% / 30% / 50% / 70% / 90%  ← 丸をつける

**該当する質問に一言お願いします（1文で十分です）:**
- 納得しない場合 → 一番引っかかる点は？
- どちらとも言えない場合 → 何があれば納得度が上がる？
- 納得する場合 → 他の企業でも同じことが言えない理由は？

回答:


**この指摘は他の銘柄にも当てはまりますか？（任意）**
□ はい → KB追加候補として記録
□ いいえ → この銘柄固有の判断
□ わからない

**補足（任意）:**


---
```

**設計判断**:
- ルール適用結果は**該当ルールのみ記載**（全ルール列挙は冗長）
- コメントは2-3文（dogma.md「コメント記述ルール」5原則準拠）
- `<u>`下線はYのPhase 2スタイルに合わせて使用
- 「他の銘柄にも当てはまりますか」は暗黙知拡充ループ設計書§3.3と整合

### 1.5 セクション4: CAGR接続サマリー

```markdown
## CAGR接続サマリー

### 構造的 vs 補完的の区分

| # | CAGR接続 | 区分 | 寄与パラメータ | AI確信度 | ソース優位性 |
|---|---------|------|-------------|---------|------------|
| C1 | [接続テキスト] | 構造的 / 補完的 | 売上成長 +X% | [Y]% | #[N] |

### CAGR接続の全体評価

[1-2段落: 因果チェーンの直接性、TAM→シェア→利益率の中間ステップ有無、
ブレークダウン数値の根拠妥当性、①/②由来の区別]
```

### 1.6 セクション5: 警鐘セクション

```markdown
## 警鐘事項

### ①/②区別の確認

| # | 主張 | ソース | 警戒レベル |
|---|------|--------|----------|
| [N] | [主張テキスト] | ②四半期レビュー | ⚠️ 拡大解釈の可能性 |

### 既存判断への警鐘

[1-2段落: 既存判断への無批判的追従、①の前提の現在の合理性、
②の積み重ねからの拡大解釈、銘柄間の推論パターン一貫性]
```

### 1.7 セクション6: 全体フィードバックセクション

```markdown
## 全体フィードバック

**レポート全体として、あなたの考え方に沿った議論ができていますか？**
□ 概ね沿っている  □ 部分的に沿っている  □ 沿っていない

**最も良かった主張の番号:**  #___
**最も問題のある主張の番号:**  #___

**全体的な印象（自由記述）:**


**AIの評価で最も違和感のある点（1文で十分です）:**

```

### 1.8 セクション7: メタデータ

`<details>` タグで折りたたみ。KBバージョン、ロード数、データ利用可否、実行時間。

---

## 2. structured.json スキーマ（追加フィールド）

既存スキーマに `five_layer_evaluation` フィールドを追加:

```json
{
  "claims": [
    {
      "id": 1,
      "claim_type": "competitive_advantage",
      "claim": "主張テキスト",
      "descriptive_label": "ラベル",
      "evidence_from_report": "根拠",
      "report_type_source": "initial | quarterly",
      "supported_by_facts": [3, 4],
      "cagr_connections": [2],
      "rule_evaluation": { "...既存..." },
      "verification": { "...既存..." },
      "five_layer_evaluation": {
        "layer_1_prerequisite": {
          "rule_9_factual_accuracy": "pass | fail",
          "rule_3_relative_advantage": "pass | fail"
        },
        "layer_2_nature": {
          "rule_1_capability_vs_result": "capability | result",
          "rule_2_noun_test": "pass | fail",
          "rule_8_strategy_vs_advantage": "advantage | strategy"
        },
        "layer_3_evidence": {
          "rule_4_quantitative": "present | absent",
          "rule_7_pure_competitor": "present | absent",
          "rule_10_negative_case": "present | absent",
          "rule_11_industry_structure": "strong_fit | weak_fit | absent"
        },
        "layer_4_cagr": {
          "rule_5_directness": "direct | indirect",
          "rule_6_structural_vs_complementary": "structural | complementary",
          "verifiability": "high | medium | low"
        },
        "layer_5_source": {
          "rule_12_source_type": "initial | quarterly",
          "overinterpretation_risk": "low | medium | high"
        }
      },
      "ai_comment": "2-3文のコメント"
    }
  ],
  "summary": {
    "...既存...",
    "warning_flags": {
      "quarterly_derived_claims": 1,
      "overinterpretation_risks": 0,
      "confidence_distribution_anomaly": false
    }
  }
}
```

---

## 3. T8（3層検証）詳細仕様

### 3.1 重大度分類

| 重大度 | 定義 | 対処 |
|--------|------|------|
| **Critical** | Yへの信頼性を損なう問題 | 必ず自動修正 |
| **Warning** | Yの指摘を予測できる問題 | 自動修正 + `[⚠️ T8修正]` 注釈 |
| **Info** | 改善提案レベル | verification-results.json に記録のみ |

### 3.2 検証層A: JSON-レポート整合性（7項目）

| ID | チェック項目 | 重大度 | 自動修正 |
|----|-------------|--------|---------|
| A-1 | 主張の網羅性（JSON全件がMDに記載） | Critical | 欠落主張を追記 |
| A-2 | confidence転記の正確性 | Critical | MD値をJSON値に合わせ修正 |
| A-3 | confidenceとトーンの一致 | Critical | コメント文を書き換え |
| A-4 | ルール適用結果の反映 | Warning | 欠落ルールを追記 |
| A-5 | contradicted事実の明示 | Critical | 事実の記述を追加 |
| A-6 | パターン照合結果の反映 | Warning | パターン情報を追記 |
| A-7 | CAGR接続の対応関係 | Warning | リンク修正 |

**A-3判定ロジック**:
- confidence <= 30% かつ 肯定的表現（「納得感あり」「優位性として妥当」等） → Critical
- confidence >= 70% かつ 否定的表現が主論点 → Critical
- confidence == 50% は中間的表現が適切

### 3.3 検証層B: KYルール準拠（9項目）

| ID | チェック項目 | 重大度 | 自動修正 |
|----|-------------|--------|---------|
| B-1 | ルール1（能力vs結果）の適用 | Warning | ルール1適用結果を追加 |
| B-2 | ルール2（名詞テスト）の適用 | Warning | 名詞形への変換提案を追加 |
| B-3 | ルール3（相対性）の適用 | Warning | 相対性検証コメントを追加 |
| B-4 | ルール4（定量的裏付け）の反映 | Info | 改善提案として記録 |
| B-5 | ルール7（純粋競合比較）の反映 | Warning | 競合比較の不足を指摘 |
| B-6 | ルール8（戦略vs優位性）の適用 | Warning | ルール8適用を追加 |
| B-7 | ルール9（事実誤認 → 10%）の適用 | Critical | confidence を 10% に強制修正 |
| B-8 | **ルール11なしの90%排除** | Critical | 90%→70%に引き下げ |
| B-9 | ルール12（①/②区別）フラグ | Warning | 警戒フラグを追加 |

**B-8は最重要チェック**: KB3実績で90%はORLY#2, #5のみ（全34件中2件）。いずれもパターンIV（構造的市場ポジション）を満たす。業界構造分析なしの90%は許容しない。

### 3.4 検証層C: パターン一貫性（4項目）

| ID | チェック項目 | 重大度 | 自動修正 |
|----|-------------|--------|---------|
| C-1 | 却下パターン検出時のconfidence上限 | Critical | 上限値に引き下げ |
| C-2 | 高評価パターン検出時のconfidence下限 | Warning | 注釈付与 |
| C-3 | 複数パターン該当時の調整 | Warning | 却下優先で再計算 |
| C-4 | 銘柄間一貫性 | Info | 参考情報として記録 |

**C-1: 却下パターンのconfidence上限テーブル**:

| 却下パターン | confidence上限 | KB3根拠 |
|-------------|--------------|---------|
| A: 結果を原因と取り違え | 50% | CHD#4=30%, MNST#1=50% |
| B: 業界共通で差別化にならない | 30% | LLY#6=30% |
| C: 因果関係の飛躍 | 30% | MNST#5=30% |
| D: 定性的で定量的裏付けなし | 30% | COST#2=10% |
| E: 事実誤認 | 10% | 強制（ルール9） |
| F: 戦略を優位性と混同 | 50% | ORLY#2分離後90% |
| G: 純粋競合に対する優位性不明 | 50% | COST#3=50% |

**C-2: 高評価パターンのconfidence下限テーブル**:

| 高評価パターン | confidence下限 | KB3根拠 |
|---------------|--------------|---------|
| I: 定量的裏付けのある差別化 | 50% | COST#1=70% |
| II: 直接的なCAGR接続メカニズム | 50% | CAGR全般50%+ |
| III: 能力 > 結果 | 50% | CHD#1=70% |
| IV: 構造的な市場ポジション | 70% | ORLY#2,#5=90% |
| V: 競合との具体的比較 | 50% | ORLY#1=70% |

**C-3: 複数パターン該当時の解決ルール**:
1. パターンE（事実誤認）は全てに優先 → 強制10%
2. 却下パターン（A-G、E以外）を先に適用
3. 高評価パターン（I-V）を後に適用
4. 上限90%、下限10%

### 3.5 自動修正の優先順位

| 順位 | 修正対象 | 対象ファイル |
|------|---------|------------|
| 1 | confidence値 | structured.json + report.md |
| 2 | コメント文 | report.md |
| 3 | 主張の追記 | report.md |
| 4 | ルール適用の追記 | report.md |
| 5 | 注釈の追加 | report.md |

全修正は verification-results.json の `corrections` 配列に記録。

### 3.6 verification-results.json スキーマ

```json
{
  "research_id": "...",
  "ticker": "ORLY",
  "verification_timestamp": "2026-02-17T10:35:00Z",
  "verification_layers": {
    "layer_a_json_report_consistency": {
      "status": "pass | fail | pass_with_warnings",
      "checks": [
        {
          "check_id": "A-3",
          "name": "confidenceとトーンの一致",
          "status": "fail",
          "severity": "critical",
          "details": "主張#3（confidence 30%）のコメントが肯定的トーン",
          "affected_claims": [3]
        }
      ]
    },
    "layer_b_ky_rule_compliance": { "...同構造..." },
    "layer_c_pattern_consistency": { "...同構造..." }
  },
  "corrections": [
    {
      "correction_id": 1,
      "source_check": "A-3",
      "claim_id": 3,
      "type": "comment_rewrite | confidence_adjustment | claim_addition | annotation",
      "before": "ある程度の優位性として認められる",
      "after": "方向性は認めるが、定量的裏付けが不足しており納得感は限定的",
      "reason": "confidence 30% に対してトーンが肯定的すぎた"
    }
  ],
  "overall_status": "pass | fail | pass_with_corrections",
  "statistics": {
    "total_checks": 20,
    "passed": 18,
    "failed_critical": 1,
    "failed_warning": 1,
    "info": 0,
    "corrections_applied": 2
  }
}
```

---

## 4. T9（精度検証）詳細仕様

### 4.1 モード切り替え

| モード | 対象 | 内容 |
|--------|------|------|
| **フルモード** | Phase 2の5銘柄（CHD, COST, LLY, MNST, ORLY） | AI評価 vs Y評価の主張単位比較 |
| **簡易モード** | 上記以外の全銘柄 | confidence分布+ヒューリスティック検証 |

Phase 2データファイルパターン: `analyst/phase2_KY/*_{TICKER}_phase2.md`

### 4.2 フルモード

#### 主張マッチング
AI主張（competitive_advantage）とY評価の主張テキストを意味的類似性で1:1マッチング。マッチングできないものは unmatched / missing_in_ai として記録。

#### 乖離の定量化

| 乖離幅 | 分類 |
|--------|------|
| 0 | exact_match |
| 1-10% | within_target |
| 11-20% | acceptable |
| 21-30% | significant |
| 31%+ | critical |

#### 合格基準

| メトリクス | 合格基準 |
|----------|---------|
| 平均乖離（優位性） | mean(abs(AI - Y)) <= 10% |
| 平均乖離（CAGR接続） | mean(abs(AI - Y)) <= 10% |
| 最大乖離 | max(abs(AI - Y)) <= 30% |
| 20%超乖離の主張数 | <= 全主張の25% |
| 方向性バイアス | mean(AI - Y)の絶対値 <= 5% |

**不合格時**: accuracy-report.json に不合格理由を記録し報告。レポート自体は出力する（ブロックしない）。

### 4.3 簡易モード（8チェック項目）

| ID | チェック項目 | 重大度 | 判定基準 |
|----|-------------|--------|---------|
| S-1 | 90%の出現率 | Warning | 全主張の15%以下（KY基準: 6%） |
| S-2 | 50%の最頻値確認 | Info | 50%付近が30%以上 |
| S-3 | 10%の希少性 | Info | 全主張の15%以下（contradicted除く） |
| S-4 | CAGR > CA平均スコア | Info | 平均CAGR確信度 >= 平均CA確信度 |
| S-5 | 却下パターンconfidence上限 | Warning | T8 C-1と同一基準 |
| S-6 | ルール11なしの90%排除 | Critical | 業界構造分析なしに90%不可 |
| S-7 | 主張数の妥当性 | Warning | 5-15件の範囲内 |
| S-8 | ルール9自動適用確認 | Critical | contradicted → 10% |

### 4.4 accuracy-report.json スキーマ

```json
{
  "research_id": "...",
  "ticker": "ORLY",
  "mode": "full | simplified",
  "generated_at": "2026-02-17T10:37:00Z",
  "kb_version": "v1.0.0",
  "full_mode_results": {
    "y_data_source": "analyst/phase2_KY/phase1_ORLY_phase2.md",
    "claim_matching": {
      "ai_claims_total": 6,
      "y_evaluations_total": 6,
      "matched": 5,
      "unmatched_ai": 1,
      "missing_in_ai": 1
    },
    "advantage_accuracy": {
      "comparisons": [
        {
          "claim_id": 1,
          "ai_confidence": 70,
          "y_confidence": 70,
          "deviation": 0,
          "severity": "exact_match",
          "deviation_analysis": "一致"
        }
      ],
      "mean_abs_deviation": 8.0,
      "max_abs_deviation": 20,
      "direction_bias": "slight_underestimate"
    },
    "cagr_accuracy": { "...同構造..." },
    "overall_verdict": "pass | fail",
    "pass_criteria": {
      "mean_deviation_within_10": true,
      "max_deviation_within_30": true,
      "over_20_percent_under_25_pct": true,
      "direction_bias_within_5": true
    },
    "improvement_suggestions": ["..."]
  },
  "simplified_mode_results": {
    "checks": [
      {
        "check_id": "S-1",
        "name": "confidence分布の妥当性（90%の出現率）",
        "status": "pass | warning | fail",
        "value": "1件 (16.7%)",
        "threshold": "15%以下"
      }
    ],
    "overall_status": "pass | pass_with_warnings | fail",
    "warning_count": 1,
    "critical_count": 0
  }
}
```

---

## 5. 修正対象ファイル一覧

| # | ファイル | 修正内容 | 優先度 |
|---|---------|---------|--------|
| 1 | `.claude/agents/ca-report-generator.md` | report.md テンプレートの全面書き換え: セクション1-7構成、個別主張テンプレート、structured.json に five_layer_evaluation 追加 | ★★★ |
| 2 | `.claude/agents/deep-research/ca-eval-lead.md` | T8: 3層検証の20チェック項目・重大度・自動修正ロジック追記。T9: フルモード/簡易モード切り替え・accuracy-report.json スキーマ追記 | ★★★ |
| 3 | `analyst/claude_code/workflow_design.md` | Section 4.8-4.10, Section 7 を本設計書の内容で更新 | ★★ |
| 4 | `.claude/skills/ca-eval/SKILL.md` | 出力ファイルの説明更新（新セクション構成、新JSONスキーマ） | ★ |
| 5 | `docs/plan/2026-02-17_ca-eval-phase4-5-knowledge-expansion-loop.md` | §3.3フィードバックテンプレートとの整合確認・更新 | ★ |

---

## 6. 検証方法

1. **テンプレート検証**: report.md テンプレートで ORLY の模擬レポートを生成し、Phase 2の Y 評価データと比較して構造の妥当性を確認
2. **T8検証**: 意図的に問題を含むレポート（confidenceとトーンの不一致、ルール11なしの90%等）を作成し、3層検証が正しく検出・修正することを確認
3. **T9検証**: ORLY のフルモードで AI 評価と Phase 2 の Y 評価を比較し、乖離メトリクスが合格基準を満たすことを確認

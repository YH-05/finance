# CA-Eval ワークフロー詳細設計書

> 作成日: 2026-02-17
> 前提: [Dify詳細設計書](../memo/dify_workflow_design.md) | [Dify比較表](dify_comparison.md)
> 上位文書: [CAGR推定フレームワーク](../memo/cagr_estimation_framework.md)

---

## 1. 概要

本文書は、Difyワークフロー（KYの投資判断を模倣する競争優位性評価）を Claude Code Agent Teams で再実装するための詳細設計書である。

### 目的

アナリストレポートと SEC EDGAR ライブデータを入力として、KYの12ルール＋補足に基づく競争優位性評価レポートを自動生成する。

### 設計原則

| 原則 | 内容 | Difyからの変更 |
|------|------|----------------|
| KYの暗黙知のみ注入 | 外部フレームワーク（Seven Powers等）は導入しない | 変更なし |
| 主張は破棄しない | ファクトチェック失敗でもアノテーション付きで保持 | 変更なし |
| 全KB直接読み込み | RAG不要。25ファイル（~62KB）を全てコンテキストに含める | **新規**（RAG→直接読み込み） |
| SECライブデータ | KB4の手動アップロードを SEC EDGAR MCP に置換 | **新規** |
| 並列実行 | Phase 1: 3並列、Phase 3: 2並列で時間短縮 | **新規** |
| 自動精度検証 | phase2_KYデータとの数値比較を自動実行 | **新規** |

---

## 2. ナレッジベース設計

### 2.1 KB一覧（直接読み込み方式）

| KB | 名称 | ファイルパス | ファイル数 | 合計サイズ | 使用タスク |
|----|------|------------|-----------|-----------|-----------|
| KB1 | ルール集 | `analyst/dify/kb1_rules/*.md` | 8 | ~15KB | T4, T8 |
| KB2 | パターン集 | `analyst/dify/kb2_patterns/*.md` | 12 | ~20KB | T6, T8 |
| KB3 | few-shot集 | `analyst/dify/kb3_fewshot/*.md` | 5 | ~15KB | T4 |
| Dogma | 判断軸 | `analyst/Competitive_Advantage/analyst_YK/dogma.md` | 1 | ~12KB | 全タスク |
| **合計** | | | **26** | **~62KB** | |

### 2.2 KB1: ルール集（8ファイル直接読み込み）

| ファイル | ルール | カテゴリ |
|---------|--------|---------|
| `rule01_capability_not_result.md` | ルール1: 能力・仕組み ≠ 結果・実績 | 優位性の定義 |
| `rule02_noun_attribute.md` | ルール2: 名詞で表現される属性 | 優位性の定義 |
| `rule04_quantitative_evidence.md` | ルール4: 定量的裏付け | 裏付けの質 |
| `rule06_structural_vs_complementary.md` | ルール6: 構造的 vs 補完的を区別 | 優位性の定義 |
| `rule07_pure_competitor_differentiation.md` | ルール7: 純粋競合への差別化 | 裏付けの質 |
| `rule08_strategy_not_advantage.md` | ルール8: 戦略 ≠ 優位性 | 優位性の定義 |
| `rule10_negative_case.md` | ルール10: ネガティブケース（断念例） | 裏付けの質 |
| `rule11_industry_structure_fit.md` | ルール11: 業界構造×企業ポジション合致 | 裏付けの質 |

**Difyとの差異**: RAG検索による取りこぼしゼロ。全8ルールが常にコンテキストに含まれる。

### 2.3 KB2: パターン集（12ファイル直接読み込み）

#### 却下パターン（confidence 低下）

| ファイル | パターン | 名称 | 影響 |
|---------|---------|------|------|
| `pattern_A_result_as_cause.md` | A | 結果を原因と取り違え | -30% 以上 |
| `pattern_B_industry_common.md` | B | 業界共通で差別化にならない | -30% 以上 |
| `pattern_C_causal_leap.md` | C | 因果関係の飛躍 | -20% |
| `pattern_D_qualitative_only.md` | D | 定性的で定量的裏付けなし | -10〜20% |
| `pattern_E_factual_error.md` | E | 事実誤認 | → 10%（ルール9連携） |
| `pattern_F_strategy_confusion.md` | F | 戦略を優位性と混同 | -20% |
| `pattern_G_unclear_vs_pure_competitor.md` | G | 純粋競合に対する優位性不明 | -10〜20% |

#### 高評価パターン（confidence 上昇）

| ファイル | パターン | 名称 | 影響 |
|---------|---------|------|------|
| `pattern_I_quantitative_differentiation.md` | I | 定量的裏付けのある差別化 | +20% |
| `pattern_II_direct_cagr_mechanism.md` | II | 直接的なCAGR接続メカニズム | +20% |
| `pattern_III_capability_over_result.md` | III | 能力 > 結果（プロセスの評価） | +10〜20% |
| `pattern_IV_structural_market_position.md` | IV | 構造的な市場ポジション | +30% |
| `pattern_V_specific_competitor_comparison.md` | V | 競合との具体的比較 | +10〜20% |

**Difyとの差異**: 12パターン全てが同時に参照可能。Difyでは Top-K=4 のため最大4パターンしか検索できなかった。

### 2.4 KB3: few-shot集（5ファイル直接読み込み）

| ファイル | 銘柄 | 平均優位性スコア | 特徴 |
|---------|------|----------------|------|
| `fewshot_ORLY.md` | ORLY | 63% | 市場構造との合致が最高評価要因 |
| `fewshot_COST.md` | COST | 39% | 分散大。一般論を厳しく却下 |
| `fewshot_MNST.md` | MNST | 40% | シェア=結果の原則を厳格適用 |
| `fewshot_CHD.md` | CHD | 50% | 能力vs結果の区別が明確 |
| `fewshot_LLY.md` | LLY | 47% | 業界共通能力を厳しく批判 |

**Difyとの差異**: 5銘柄の全評価例が常に参照可能。KYのスコア分布傾向のキャリブレーションが正確に。

### 2.5 KB4 → SEC EDGAR MCP（完全置換）

Difyの KB4（10-K/10-Q 手動アップロード）を SEC EDGAR MCP ツールで完全に置換。

| Dify | Claude Code | 改善 |
|------|------------|------|
| 銘柄ごとにKB作成 | `mcp__sec-edgar-mcp__get_financials` | 手動作業ゼロ |
| セクション単位でチャンク分割 | `mcp__sec-edgar-mcp__get_filing_sections` | チャンク設計不要 |
| 手動アップロード必要 | ティッカー指定のみ | 常に最新データ |
| 静的データ | ライブ取得 | 更新不要 |
| PoC対象銘柄のみ | 任意の米国上場企業 | 銘柄制限なし |

---

## 3. ワークフロー設計

### 3.1 全体構成: 10タスク・5フェーズ

```
/ca-eval ORLY
    |
    Phase 0: Setup (Lead直接実行)
    |-- [T0] research-meta.json作成 + ディレクトリ作成
    |       [HF0] パラメータ確認
    |
    Phase 1: データ収集 (3並列)
    |-- [T1] sec-collector (finance-sec-filings) ----+
    |-- [T2] report-parser (ca-report-parser) -------+ 並列
    |-- [T3] industry (industry-researcher) ---------+
    |
    Phase 2: 主張抽出 + ルール適用 (直列)
    |-- [T4] extractor (ca-claim-extractor)
    |       blockedBy: [T1, T2, T3]
    |
    Phase 3: ファクトチェック + パターン検証 (2並列)
    |-- [T5] fact-checker (ca-fact-checker) ----------+
    |-- [T6] pattern-verifier (ca-pattern-verifier) --+ 並列
    |       blockedBy: [T4]
    |       [HF1] 中間品質レポート
    |
    Phase 4: レポート生成 + 検証 (直列)
    |-- [T7] reporter (ca-report-generator)
    |       blockedBy: [T5, T6]
    |-- [T8] Lead: レポート3層検証
    |-- [T9] Lead: 精度検証 (phase2_KYデータがある場合)
    |       [HF2] 最終出力
    |
    Phase 5: Cleanup (TeamDelete)
```

### 3.2 Difyステップとの対応

| Dify ステップ | Claude Code タスク | 改善点 |
|-------------|-------------------|--------|
| 知識検索①(KB4) + LLM①(主張抽出) | **T4: ca-claim-extractor** | KB1+KB3も同時読み込み。RAG不要 |
| 知識検索②(KB1+KB3) + LLM②(ルール適用) | **T4に統合** | ステップ分離不要 |
| 知識検索③(KB4) + LLM③(ファクトチェック) | **T5: ca-fact-checker** | SEC EDGAR MCPで追加検証 |
| 知識検索④(KB2) + LLM④(検証/JSON) | **T6: ca-pattern-verifier** | 12パターン全て同時参照 |
| LLM⑤(レポート生成) | **T7: ca-report-generator** | 全検証結果を統合 |
| 知識検索⑤(KB1+KB2) + LLM⑥(レポート検証) | **T8: Lead直接実行** | 3層検証 |
| *(なし)* | **T1: SEC Filings取得** | 新機能: KB4の完全置換 |
| *(なし)* | **T2: Report Parser** | 新機能: ①/②区別 |
| *(なし)* | **T3: Industry Research** | 新機能: 業界データ |
| *(なし)* | **T9: 精度検証** | 新機能: 自動精度比較 |

---

## 4. 各タスクの詳細設計

### 4.1 T0: Setup（Lead直接実行）

**リサーチID生成**: `CA_eval_{YYYYMMDD}_{TICKER}`

**ディレクトリ作成**:
```
research/CA_eval_{YYYYMMDD}_{TICKER}/
├── 00_meta/
│   └── research-meta.json
├── 01_data_collection/
├── 02_claims/
├── 03_verification/
└── 04_output/
```

**レポート検索**:
1. `report_path` が指定されていればそれを使用
2. 未指定の場合は `analyst/raw/` 配下で ticker に一致するファイルを Glob 検索
3. 見つからない場合はエラー

**research-meta.json 出力**:
```json
{
  "research_id": "CA_eval_20260217_ORLY",
  "type": "ca_eval",
  "ticker": "ORLY",
  "created_at": "2026-02-17T10:00:00Z",
  "parameters": {
    "ticker": "ORLY",
    "report_path": "analyst/raw/ORLY_report.md"
  },
  "status": "in_progress",
  "workflow": {
    "phase_0": "done",
    "phase_1": "pending",
    "phase_2": "pending",
    "phase_3": "pending",
    "phase_4": "pending",
    "phase_5": "pending"
  }
}
```

### 4.2 T1: SEC Filings 取得（finance-sec-filings）

**エージェント**: `finance-sec-filings`（既存、stock モード）

**処理内容**:
- 5年分の財務データ（損益/BS/CF）
- 直近2年分の 10-K/10-Q
- 直近1年の 8-K イベント
- インサイダー取引サマリー
- キーメトリクス
- 10-K セクション（Business, Risk Factors, Properties, MD&A）

**出力**: `{research_dir}/01_data_collection/sec-data.json`

**致命度**: Fatal=Yes（SEC データなしでは主張検証が不可能）

### 4.3 T2: Report Parser（ca-report-parser）

**エージェント**: `ca-report-parser`（新規）

**処理内容**:
1. レポート種別の判定（①期初レポート / ②四半期レビュー / 混合）
2. セクション分割（投資テーゼ、事業概要、競争優位性、財務分析等）
3. ①/②の帰属付与
4. 競争優位性の抽出候補、事実の主張、CAGR参照を識別

**出力**: `{research_dir}/01_data_collection/parsed-report.json`

**致命度**: Fatal=Yes（レポート解析なしでは主張抽出が不可能）

### 4.4 T3: Industry Research（industry-researcher）

**エージェント**: `industry-researcher`（既存）

**処理内容**:
- 業界構造・市場規模
- 主要プレイヤー・競争環境
- 参入障壁・モート
- dogma.md 12判断ルールに基づく競争優位性の予備評価

**出力**: `{research_dir}/01_data_collection/industry-context.json`

**致命度**: Fatal=No（業界データなしでも主張抽出・評価は可能。縮小版で続行）

### 4.5 T4: Claim Extraction + Rule Application（ca-claim-extractor）

**エージェント**: `ca-claim-extractor`（新規）

**Difyからの統合**: ステップ1（主張抽出）+ ステップ2（ルール適用）

**入力ファイル**:
- `{research_dir}/01_data_collection/sec-data.json`（T1, 必須）
- `{research_dir}/01_data_collection/parsed-report.json`（T2, 必須）
- `{research_dir}/01_data_collection/industry-context.json`（T3, 任意）
- `analyst/Competitive_Advantage/analyst_YK/dogma.md`
- `analyst/dify/kb1_rules/` 配下 8ファイル
- `analyst/dify/kb3_fewshot/` 配下 5ファイル

**処理内容**:
1. **主張抽出**: parsed-report.json の `advantage_candidates` から 5-15件を抽出
2. **ルール適用**: KB1の8ルール + ゲートキーパー（ルール9, 3）を適用
3. **KB3キャリブレーション**: 5銘柄の評価例を参照し確信度を調整
4. **①/②区別**: ルール12を適用

**出力スキーマ**: Dify設計書§6 に準拠した claims.json

**出力**: `{research_dir}/02_claims/claims.json`

**致命度**: Fatal=Yes（主張抽出が全ての下流タスクの基盤）

### 4.6 T5: Fact Check（ca-fact-checker）

**エージェント**: `ca-fact-checker`（新規）

**Dify対応**: ステップ3

**入力ファイル**:
- `{research_dir}/02_claims/claims.json`（T4, 必須）
- `{research_dir}/01_data_collection/sec-data.json`（T1, 必須）
- SEC EDGAR MCP ツール（追加検証用）

**処理内容**:
1. 各 `factual_claim` を sec-data.json と照合
2. sec-data.json で不足する場合は SEC EDGAR MCP ツールで追加取得
3. `verified` / `contradicted` / `unverifiable` を判定
4. `contradicted` → ルール9自動適用（confidence → 10%）

**出力**: `{research_dir}/03_verification/fact-check.json`

**致命度**: Fatal=No（ファクトチェック失敗時は全件 unverifiable として続行）

### 4.7 T6: Pattern Verification（ca-pattern-verifier）

**エージェント**: `ca-pattern-verifier`（新規）

**Dify対応**: ステップ4

**入力ファイル**:
- `{research_dir}/02_claims/claims.json`（T4, 必須）
- `analyst/dify/kb2_patterns/` 配下 12ファイル
- `analyst/Competitive_Advantage/analyst_YK/dogma.md`

**処理内容**:
1. 各主張を却下パターン A-G と照合（confidence 下方調整）
2. 各主張を高評価パターン I-V と照合（confidence 上方調整）
3. CAGR接続のパターン照合（パターンII特化）
4. 一貫性チェック（同じパターンに同じロジック適用、KY基準との分布比較）

**出力**: `{research_dir}/03_verification/pattern-verification.json`

**致命度**: Fatal=No（パターン検証なしでもレポート生成は可能）

### 4.8 T7: Report Generation（ca-report-generator）

**エージェント**: `ca-report-generator`（新規）

**Dify対応**: ステップ5

**入力ファイル**:
- `{research_dir}/02_claims/claims.json`（T4, 必須）
- `{research_dir}/03_verification/fact-check.json`（T5, 任意）
- `{research_dir}/03_verification/pattern-verification.json`（T6, 任意）
- `analyst/Competitive_Advantage/analyst_YK/dogma.md`

**処理内容**:
1. claims.json にファクトチェック結果とパターン検証結果をマージ
2. 最終 confidence を算出
3. Markdown レポート生成（フィードバックテンプレート埋込）
4. 構造化 JSON（Dify設計書§6準拠）生成

**出力**:
- `{research_dir}/04_output/report.md`
- `{research_dir}/04_output/structured.json`

**致命度**: Fatal=Yes

### 4.9 T8: Report Verification（Lead直接実行）

**Dify対応**: ステップ6

**3層検証**:

| 検証層 | 内容 | 検出する問題 |
|--------|------|-------------|
| 検証A: JSON-レポート整合 | confidence とトーンの一致、主張の網羅性 | レポート生成時の拡大解釈 |
| 検証B: KYルール準拠 | 12ルールに沿った議論か | ルール適用の記述漏れ |
| 検証C: パターン一貫性 | 却下/高評価パターンの表現チェック | confidence 30%が肯定的に書かれている等 |

**出力**:
- `{research_dir}/04_output/verified-report.md`
- `{research_dir}/04_output/verification-results.json`

### 4.10 T9: Accuracy Scoring（Lead直接実行）

**Difyにない新機能**。

**対象銘柄**: CHD, COST, LLY, MNST, ORLY（phase2_KYデータが存在する銘柄のみ）

**処理内容**:
1. `analyst/phase2_KY/phase1_{TICKER}_phase2.md` を読み込み
2. KYの実スコアと AI 予測スコアを比較
3. 乖離分析を出力

**出力**: `{research_dir}/04_output/accuracy-report.json`

**精度目標**:
- 平均乖離: ±10% 以内
- 個別項目: ±20% 以内

---

## 5. 依存関係マトリクス

```yaml
dependency_matrix:
  # Phase 1: 全て独立（依存なし）
  T1: {}  # SEC Filings
  T2: {}  # Report Parser
  T3: {}  # Industry Research

  # Phase 2: T1-T3 に混合依存
  T4:
    T1: required   # SEC データは必須
    T2: required   # パースドレポートは必須
    T3: optional   # 業界データは任意

  # Phase 3: T4 に必須依存
  T5:
    T4: required   # claims.json は必須
  T6:
    T4: required   # claims.json は必須

  # Phase 4: T5, T6 に混合依存
  T7:
    T4: required   # claims.json は必須（ベースデータ）
    T5: optional   # fact-check.json は任意
    T6: optional   # pattern-verification.json は任意

  # T8, T9 は Lead 直接実行
  T8:
    T7: required
  T9:
    T8: required
```

---

## 6. 構造化JSON出力スキーマ

Dify設計書§6 のスキーマを踏襲し、Claude Code 固有フィールドを追加:

```json
{
  "ticker": "ORLY",
  "report_source": "アナリストA",
  "extraction_metadata": {
    "kb1_rules_loaded": 8,
    "kb3_fewshot_loaded": 5,
    "dogma_loaded": true,
    "sec_data_available": true,
    "industry_context_available": true
  },
  "claims": [
    {
      "id": 1,
      "claim_type": "competitive_advantage",
      "claim": "ローカルな規模の経済による配送・在庫の効率化",
      "descriptive_label": "配送密度による原価優位",
      "evidence_from_report": "店舗数5,800超、配送センター30拠点（レポートp.8）",
      "report_type_source": "initial",
      "supported_by_facts": [3, 4],
      "cagr_connections": [2],
      "rule_evaluation": {
        "applied_rules": ["rule_6", "rule_11"],
        "results": [
          {
            "rule": "rule_6",
            "verdict": "structural",
            "reasoning": "配送密度は競合が容易に再現できない構造的優位"
          }
        ],
        "confidence": 90,
        "confidence_adjustments": [],
        "overall_reasoning": "市場構造との合致が明確"
      },
      "verification": {
        "fact_check_status": "verified",
        "pattern_matches": ["IV"],
        "pattern_rejections": [],
        "final_confidence": 90,
        "confidence_delta": 0
      }
    },
    {
      "id": 2,
      "claim_type": "cagr_connection",
      "claim": "店舗密度の拡大 → 配送効率 → マージン改善 → 営業利益CAGR +2pp",
      "descriptive_label": "配送密度→マージン改善経路",
      "source_advantage": 1,
      "rule_evaluation": {
        "applied_rules": ["rule_5", "rule_12"],
        "results": [
          {
            "rule": "rule_5",
            "verdict": "direct",
            "reasoning": "2ステップの因果。検証可能"
          }
        ],
        "confidence": 80,
        "confidence_adjustments": [],
        "overall_reasoning": "因果メカニズムが直接的で検証可能"
      }
    },
    {
      "id": 3,
      "claim_type": "factual_claim",
      "claim": "店舗数5,829",
      "verification_status": "verified",
      "verification_attempted": [
        "2024年10-K Item 2: 'We operated 5,829 stores as of December 31, 2024'"
      ],
      "what_would_verify": null,
      "confidence_impact": "none",
      "affected_claims": [1],
      "verification_source": "sec-data.json + SEC EDGAR MCP"
    }
  ],
  "accuracy_comparison": {
    "ky_data_available": true,
    "ky_data_source": "analyst/phase2_KY/phase1_ORLY_phase2.md",
    "comparisons": [
      {
        "claim_id": 1,
        "ai_confidence": 90,
        "ky_confidence": 90,
        "deviation": 0,
        "deviation_analysis": "一致"
      }
    ],
    "average_deviation": 5.0,
    "max_deviation": 20,
    "within_target": true
  }
}
```

---

## 7. レポート出力フォーマット

### 7.1 Markdownレポート（report.md）

Dify設計書§5.5 のフォーマットを踏襲:

```markdown
# [TICKER] 競争優位性評価レポート

## レポート情報
- 対象銘柄: [TICKER]
- 入力レポート: [アナリスト名]
- 生成日: [日付]
- リサーチID: [research_id]
- データソース: SEC EDGAR (MCP), アナリストレポート, 業界分析

---

## 競争優位性候補

### #1: [主張テキスト]

**分類**: [descriptive_label]
**確信度**: [X]%
**レポート種別**: ①期初レポート / ②四半期レビュー

**根拠**:
[evidence_from_report]

**ルール適用結果**:
- ルール[N]: [verdict] — [reasoning]

**ファクトチェック**:
- [verification_status に応じた記述]

**パターン照合**:
- 高評価: [該当パターン] / 却下: [該当パターン]

**CAGR接続**: [接続先がある場合]

---

**納得度:**  10% / 30% / 50% / 70% / 90%  ← 丸をつける

**該当する質問に一言お願いします（1文で十分です）:**

- 納得しない場合 → 一番引っかかる点は？
- どちらとも言えない場合 → 何があれば納得度が上がる？
- 納得する場合 → 他の企業でも同じことが言えない理由は？

回答:


**補足（任意）:**


---

[以下、#2〜#N まで同様]

---

## 全体フィードバック

**レポート全体として、あなたの考え方に沿った議論ができていますか？**

□ 概ね沿っている  □ 部分的に沿っている  □ 沿っていない

**最も良かった主張の番号:**  #___
**最も問題のある主張の番号:**  #___

**その他コメント（任意）:**

```

### 7.2 検証結果（verification-results.json）

```json
{
  "verification_layers": {
    "layer_a_json_report_consistency": {
      "status": "pass",
      "issues": []
    },
    "layer_b_ky_rule_compliance": {
      "status": "pass",
      "issues": []
    },
    "layer_c_pattern_consistency": {
      "status": "warning",
      "issues": [
        {
          "claim_id": 3,
          "issue": "confidence 30% に対してレポート内の記述がやや肯定的",
          "severity": "minor",
          "suggestion": "トーンを調整"
        }
      ]
    }
  },
  "overall_status": "pass_with_warnings",
  "corrections_applied": 1
}
```

---

## 8. 実行時間見積もり

| フェーズ | タスク | 推定時間 | 備考 |
|---------|--------|---------|------|
| Phase 0 | T0 Setup | ~10秒 | Lead直接実行 |
| Phase 1 | T1+T2+T3 並列 | ~3分 | SEC MCP + レポート解析 + 業界検索 |
| Phase 2 | T4 主張抽出 | ~2分 | KB読み込み + 5-15件評価 |
| Phase 3 | T5+T6 並列 | ~2分 | SEC MCP追加検証 + 12パターン照合 |
| Phase 4 | T7 レポート生成 | ~1.5分 | Markdown + JSON |
| Phase 4 | T8 3層検証 | ~1分 | Lead直接実行 |
| Phase 4 | T9 精度検証 | ~30秒 | 該当銘柄のみ |
| Phase 5 | Cleanup | ~10秒 | TeamDelete |
| **合計** | | **~10分** | 全自動 |

Dify比較: ~6分 + 手動前処理 → Claude Code: ~10分（全自動、追加検証含む）

---

## 9. 関連ファイル

| ファイル | パス |
|---------|------|
| リーダーエージェント | `.claude/agents/deep-research/ca-eval-lead.md` |
| ワーカーエージェント | `.claude/agents/ca-report-parser.md` 他5ファイル |
| コマンド | `.claude/commands/ca-eval.md` |
| スキル | `.claude/skills/ca-eval/SKILL.md` |
| Dify比較表 | `analyst/claude_code/dify_comparison.md` |
| Dify詳細設計書 | `analyst/memo/dify_workflow_design.md` |
| Dogma | `analyst/Competitive_Advantage/analyst_YK/dogma.md` |
| KB1ルール集 | `analyst/dify/kb1_rules/` (8ファイル) |
| KB2パターン集 | `analyst/dify/kb2_patterns/` (12ファイル) |
| KB3 few-shot集 | `analyst/dify/kb3_fewshot/` (5ファイル) |
| Phase 2検証データ | `analyst/phase2_KY/` (5銘柄) |

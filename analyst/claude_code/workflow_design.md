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

**✅ 実体確認済み**: `analyst/claude_code/kb1_rules/` (2026-02-17)

| ファイル | ルール | カテゴリ | サイズ | 重要度 |
|---------|--------|---------|--------|--------|
| `rule01_capability_not_result.md` | ルール1: 能力・仕組み ≠ 結果・実績 | 優位性の定義 | 3.0KB | ★★★ |
| `rule02_noun_attribute.md` | ルール2: 名詞で表現される属性 | 優位性の定義 | 1.9KB | ★★★ |
| `rule04_quantitative_evidence.md` | ルール4: 定量的裏付け | 裏付けの質 | 2.2KB | ★★ |
| `rule06_structural_vs_complementary.md` | ルール6: 構造的 vs 補完的を区別 | 優位性の定義 | 2.0KB | ★★★ |
| `rule07_pure_competitor_differentiation.md` | ルール7: 純粋競合への差別化 | 裏付けの質 | 2.2KB | ★★ |
| `rule08_strategy_not_advantage.md` | ルール8: 戦略 ≠ 優位性 | 優位性の定義 | 2.5KB | ★★★ |
| `rule10_negative_case.md` | ルール10: ネガティブケース（断念例） | 裏付けの質 | 2.3KB | ★ |
| `rule11_industry_structure_fit.md` | ルール11: 業界構造×企業ポジション合致 | 裏付けの質 | 2.6KB | ★★★ |

**ファイル構造**（全ルール共通）:
- **ルール定義**: 明確な基準
- **良い例**: KYが高評価したケース（実銘柄・実スコア付き）
- **悪い例**: KYが低評価したケース（実銘柄・実スコア付き）
- **KYの原文**: feedback.md からの直接引用

**重要な発見**:
- **ルール2の教訓**: REASONING段階での批判的推論を最終出力まで反映すべき → **T8検証の核心**
- **ルール11の厳格性**: 90%評価は業界構造×企業ポジション合致のみ（全34件中2件 = 6%）

**Difyとの差異**: RAG検索による取りこぼしゼロ。全8ルールが常にコンテキストに含まれる。

### 2.3 KB2: パターン集（12ファイル直接読み込み）

**✅ 実体確認済み**: `analyst/claude_code/kb2_patterns/` (2026-02-17)

#### 却下パターン（confidence 低下）

| ファイル | パターン | 名称 | サイズ | 影響 | 確信度 |
|---------|---------|------|--------|------|--------|
| `pattern_A_result_as_cause.md` | A | 結果を原因と取り違え | 1.8KB | -30%以上 | 30%以下 |
| `pattern_B_industry_common.md` | B | 業界共通で差別化にならない | 2.1KB | -30%以上 | 20-30% |
| `pattern_C_causal_leap.md` | C | 因果関係の飛躍 | 2.0KB | -20% | 30% |
| `pattern_D_qualitative_only.md` | D | 定性的で定量的裏付けなし | 1.9KB | -10〜20% | 10-20% |
| `pattern_E_factual_error.md` | E | 事実誤認 | 1.7KB | → 10% | 10% |
| `pattern_F_strategy_confusion.md` | F | 戦略を優位性と混同 | 2.0KB | -20% | 30% |
| `pattern_G_unclear_vs_pure_competitor.md` | G | 純粋競合に対する優位性不明 | 1.9KB | -10〜20% | 30-50% |

#### 高評価パターン（confidence 上昇）

| ファイル | パターン | 名称 | サイズ | 影響 | 確信度 |
|---------|---------|------|--------|------|--------|
| `pattern_I_quantitative_differentiation.md` | I | 定量的裏付けのある差別化 | 1.9KB | +20% | 70-90% |
| `pattern_II_direct_cagr_mechanism.md` | II | 直接的なCAGR接続メカニズム | 2.3KB | +20% | 90% |
| `pattern_III_capability_over_result.md` | III | 能力 > 結果（プロセスの評価） | 1.9KB | +10〜20% | 70% |
| `pattern_IV_structural_market_position.md` | IV | 構造的な市場ポジション | 2.2KB | +30% | 90% |
| `pattern_V_specific_competitor_comparison.md` | V | 競合との具体的比較 | 2.2KB | +10〜20% | 70% |

**ファイル構造**（全パターン共通）:
- **パターン定義**: 明確な検出基準
- **具体例**: 実銘柄での適用例（ORLY, COST, MNST等）
- **KYのルール**: 原則の直接引用
- **検出のチェックポイント**: 実装時の判定基準

**適用順序の重要性**:
1. **却下パターン（A-G）を先に適用** → confidence 下方調整
2. **高評価パターン（I-V）を後で適用** → confidence 上方調整

**Difyとの差異**: 12パターン全てが同時に参照可能。Difyでは Top-K=4 のため最大4パターンしか検索できなかった。

### 2.4 KB3: few-shot集（5ファイル直接読み込み）

**✅ 実体確認済み**: `analyst/claude_code/kb3_fewshot/` (2026-02-17)

| ファイル | 銘柄 | サイズ | 平均優位性スコア | 特徴 | KYが重視した視点 |
|---------|------|--------|----------------|------|----------------|
| `fewshot_ORLY.md` | ORLY | 3.5KB | 63%（最高） | 90%評価×2件 | 市場構造（フラグメント）×企業ポジション（規模・密度）の合致 |
| `fewshot_COST.md` | COST | 3.3KB | 39%（最低） | 分散大（10%〜90%） | 数値裏付けの有無、純粋競合（SAMS CLUB）との差別化 |
| `fewshot_MNST.md` | MNST | 2.9KB | 40% | 事実誤認は即却下 | シェア=結果の原則、ブランド力の背後要因 |
| `fewshot_CHD.md` | CHD | 3.5KB | 50% | 能力vs結果の区別 | ポート管理運営力（能力）vs ポートシフト（結果） |
| `fewshot_LLY.md` | LLY | 3.7KB | 47% | 業界共通能力を厳しく批判 | メガファーマ共通能力は30%、Novo対比で70% |

**ファイル構造**（全銘柄共通）:
- **銘柄概要**: 平均スコア、特徴、KYの全体印象
- **主張一覧と評価**: 各主張のスコア、KYの理由、KYの指摘、該当ルール/パターン
- **KYが重視した視点**: 銘柄ごとの判断基準のポイント

**確信度スケールの実分布**（全34件）:

| 確信度 | 件数 | 割合 | 特徴 |
|--------|------|------|------|
| 90% | 2 | 6% | **極めて稀**。業界構造×企業ポジション合致のみ（ORLY#2, #5） |
| 70% | 8 | 26% | 定量的裏付け、競合との具体的比較 |
| **50%** | **11** | **35%** | **最頻値**。方向性は認めるが裏付け不十分 |
| 20-30% | 8 | 26% | 業界共通、因果関係の飛躍 |
| 10% | 2 | 6% | 事実誤認（MNST#6）、定性的で評価不可能（COST#2） |

**重要な発見**:
- **50%がデフォルト**: KYは多くの仮説を「まあ納得」と評価する傾向
- **90%は極めて厳格**: 業界構造分析なしに90%を付与してはならない
- **数値裏付けの影響**: COST#1（退職率9% vs 20%+）→ 70%、COST#2（劇場的価値）→ 10%

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
1. レポート種別の判定（**期初投資仮説レポート** / **四半期継続評価レポート** / 混合）
2. セクション分割（投資テーゼ、事業概要、競争優位性、財務分析等）
3. レポート種別の帰属付与
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
**レポート種別**: 期初投資仮説レポート / 四半期継続評価レポート

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

---

## 10. KB分析結果と設計上の洞察

> **調査日**: 2026-02-17
> **調査範囲**: KB1（8ファイル）、KB2（12ファイル）、KB3（5ファイル）、dogma.md の全量確認

### 10.1 確信度計算の2段階方式

KB分析から、確信度計算は以下の2段階で行うべきことが判明：

```python
# Phase 1: ルール適用（KB1 + KB3キャリブレーション）
base_confidence = apply_rules(
    claim=claim,
    kb1_rules=load_all_8_rules(),  # ルール1,2,4,6,7,8,10,11
    kb3_calibration=load_5_fewshots()  # スコア分布の参照
)

# Phase 2: パターン照合（KB2）
adjusted_confidence = apply_patterns(
    base_confidence=base_confidence,
    reject_patterns=load_patterns_A_to_G(),  # 先に適用（-30%〜-10%）
    approve_patterns=load_patterns_I_to_V()   # 後で調整（+10%〜+30%）
)
```

**重要**: 却下パターン（A-G）を先に適用し、その後に高評価パターン（I-V）で調整する順序を守ること。

### 10.2 90%評価の厳格化

**KB3の重要な発見**:
- 90%評価は全34件中わずか2件（6%）
- いずれも「業界構造×企業ポジション合致」（ORLY#2, #5）
- 50%が最頻値（35%）→ KYは多くの仮説を「まあ納得」と評価

**実装への影響**:

```python
def is_90_percent_qualified(claim: dict) -> bool:
    """90%評価の条件チェック（KB3の実績に基づく厳格な基準）"""
    return (
        has_industry_structure_analysis(claim) and  # 業界構造の分析が明確
        has_company_position_analysis(claim) and    # 企業ポジションが構造的
        has_clear_fit_explanation(claim) and        # 両者の合致が説明されている
        base_confidence >= 85                       # 厳格な閾値
    )

# デフォルトバイアス: 50%
# 業界構造分析なしに90%を付与してはならない
```

### 10.3 REASONING保持の仕組み（T8検証の核心）

**KB1ルール2の教訓**:
```markdown
> AIのREASONING段階での示唆
> LLYの評価では、REASONING段階（最終出力の前段階）で以下のような有益な指摘がなされた
> **教訓**: REASONING段階での批判的推論は、最終出力まで反映されるべき。
```

**T8: 3層検証の具体化**:

| 検証層 | 内容 | 実装方法 |
|--------|------|----------|
| **検証A: JSON-レポート整合** | REASONING段階の批判が最終レポートに反映されているか | LLM判定（KB1ルール2の教訓を指示に含める） |
| **検証B: KYルール準拠** | KB1の8ルール全てに言及しているか | ルールベース（ルール11の有無を特に確認） |
| **検証C: パターン一貫性** | KB2の12パターンとconfidenceの一貫性 | confidence 30%なのに肯定的トーンになっていないか確認 |

### 10.4 ①/②区別と警鐘機能

**プロジェクトの最優先事項**（dogma.md §5.2より）:

| 優先度 | 機能 |
|--------|------|
| **最高** | 既存判断への警鐘（FM/ANが既存判断に縛られていることへの指摘） |
| **高** | 推論段階での批判が最終出力で消えないこと |
| **高** | 銘柄間での一貫した推論パターンの適用 |

**実装への影響**:
- **T2（ca-report-parser）**: 期初投資仮説レポート/四半期継続評価レポート/混合の判定アルゴリズム
- **T4（ca-claim-extractor）**: ②から抽出された優位性には警戒フラグを付与
- **T7（ca-report-generator）**: ②由来の主張には注意書き追加
  - 例: 「⚠️ この主張は四半期レビュー（②）から抽出されました。期初レポート（①）での妥当性を再検討してください。」

### 10.5 エラーハンドリング設計（部分障害時の挙動）

| シナリオ | 現在の設計 | 決定事項（KB分析を踏まえて） |
|---------|-----------|---------------------------|
| **T3失敗** (industry-researcher) | 縮小版で続行 | industry-context.json がない場合、T4は「業界構造分析なし」として処理。ルール11を適用できず、90%評価は不可能と明記 |
| **T5失敗** (fact-checker) | 全件 unverifiable | レポート生成時に「ファクトチェック未実施」の警告を追加 |
| **T6失敗** (pattern-verifier) | パターン検証なし | KB2の12パターン照合なしでレポート生成。検証結果に影響範囲を明記 |
| **T1失敗** (SEC Filings) | Fatal | 再試行3回、タイムアウト30秒/回 |

---

## 11. プロジェクトの目的と設計思想

> **出典**: `analyst/Competitive_Advantage/analyst_YK/dogma.md` + `feedback.md`

### 11.1 プロジェクトの核心的な目的

**アナリスト Y（吉沢）の競争優位性判断に関する暗黙知の抽出と体系化**

| 項目 | 内容 |
|------|------|
| **何を抽出するか** | Y の競争優位性評価の判断基準（12ルール + 補足） |
| **どう体系化するか** | Phase 2 全5銘柄のフィードバックから、確信度スケール・評価体系を明文化 |
| **最終アウトプット** | アナリストレポート → Y の判断軸に基づく競争優位性評価レポート自動生成 |
| **外部フレームワーク** | Seven Powers 等は導入しない。Y の暗黙知のみ注入 |

### 11.2 優位性の定義（5原則）

| # | 原則 | 根拠 |
|---|------|------|
| 1 | **優位性は「能力・仕組み」であり、「結果・実績」ではない** | CHD#4「成長加速は結果であって背景となる優位性ではない」 |
| 2 | **優位性は「名詞」で表現される属性である** | LLY feedback「ブランド力、スイッチングコスト、エコシステム、技術力…」 |
| 3 | **優位性は競合に対して「相対的に際立つ」ものでなければならない** | LLY#6「グローバル大手医薬品であればほぼ同等」→ 30% |
| 4 | **優位性は業界構造・競争環境と密接に関係する** | ORLY#2, #5（フラグメント市場 × 規模・密度 → 90%） |
| 5 | **定量的裏付けがあると納得度が上がる** | COST#1（退職率9% vs 業界20%+ → 70%） |

### 11.3 優位性と認めないもの（6却下基準）

| # | 却下基準 | 典型例 |
|---|---------|--------|
| 1 | **結果の優位性への誤帰属** | MNST#1「シェアはあくまで結果」→ 50% |
| 2 | **業界共通の能力** | LLY#6「メガファーマなら誰でも持っている」→ 30% |
| 3 | **戦略の優位性への混同** | ORLY#2「ドミナント出店戦略＝戦略は優位性ではない」 |
| 4 | **定性的で測定不能な主張** | COST#2「劇場的価値」→ 10% |
| 5 | **因果関係の飛躍** | MNST#5「低所得→コンビニ→粘着力 は飛躍」→ 30% |
| 6 | **事実誤認に基づく仮説** | MNST#6「OPMをGPMと誤認」→ 10%（即却下） |

### 11.4 確信度スケール

| ランク | 確信度 | 定義 |
|--------|--------|------|
| かなり納得 | 90% | 構造的優位性 + 明確なCAGR接続 + 定量的裏付け |
| おおむね納得 | 70% | 妥当な仮説 + 一定の裏付け（競合比較または数値あり） |
| まあ納得 | 50% | 方向性は認めるが裏付け不十分（追加情報があれば上がりうる） |
| あまり納得しない | 30% | 飛躍的解釈・因果関係の逆転・差別化根拠不十分 |
| 却下 | 10% | 事実誤認・競争優位性として不成立 |

### 11.5 AI への期待機能（最優先）

| 優先度 | 機能 |
|--------|------|
| **最高** | 既存判断への警鐘（FM/AN が既存判断に縛られていることへの指摘） |
| **高** | 推論段階での批判が最終出力で消えないこと |
| **高** | 銘柄間での一貫した推論パターンの適用 |
| **中** | Few-shot examples の影響を制御した安定的な出力 |

### 11.6 期初投資仮説レポート vs 四半期継続評価レポート

```markdown
優先度: ①（主） > ②（従）

- 期初投資仮説レポート: 投資仮説の根幹。ここで設定された優位性が基準
- 四半期継続評価レポート: ①の妥当性を再検証するための材料

⚠️ ②から新たな優位性を「発見」することへの警戒
⚠️ ①の妥当性を再検討させるような仕組みが必要
```

> 「②の積み重ねから拡大解釈するのでなく、①の妥当性を再検討させるような仕組み考えられないのでしょうか?」（feedback.md より）

---

## 12. 暗黙知拡充ループ

Phase 0-4（評価レポート生成）の上位に、**Yの暗黙知を継続的に拡充するループ**が存在する。

詳細設計: `docs/plan/2026-02-17_ca-eval-phase4-5-knowledge-expansion-loop.md`

### ループ概要

```
[ステップ1] AI評価実行（CA-Eval Phase 0-4）
    ↓
[ステップ2] Yフィードバック収集（構造化テンプレート）
    ↓
[ステップ3] フィードバック分析・KB更新判定
    ↓
[ステップ4] KB更新・回帰テスト
    ↓
[ステップ5] 継続判定（フィードバック量が漸減するまで反復）
```

### 設計原則

| 原則 | 内容 |
|------|------|
| **Yの判断が正** | AI評価とY評価が乖離した場合、Yが正しい前提で分析する |
| **フィードバック駆動** | AIの自動分析は補助。KB更新の根拠はYのフィードバックのみ |
| **汎用性の検証** | 2銘柄以上で再現した指摘のみKB追加候補とする |
| **回帰テスト必須** | KB更新後、Phase 2の5銘柄で精度が劣化しないことを確認する |

---

## 13. 実装前の確認事項

### 13.1 最優先：暗黙知の正確な再現

| タスク | 決めるべき詳細 | KBからの示唆 |
|--------|---------------|------------|
| **T4: ca-claim-extractor** | KB1+KB3の読み込み順序、確信度計算式の詳細 | ルール適用順序（ルール1→2→6→8→11）、KB3のスコア分布でキャリブレーション |
| **T6: ca-pattern-verifier** | 12パターン同時参照の実装、確信度調整ロジック | 却下パターン（A-G）を先に適用 → 高評価パターン（I-V）で調整 |
| **T8: 3層検証** | REASONING段階の批判を保持する仕組み | **ルール2の教訓**：REASONING段階での批判を最終出力まで反映 |
| **T9: 精度検証** | Phase 2 データとの乖離許容範囲（±10%）を超えた場合のアクション | 暗黙知再現の品質保証 |

### 13.2 高優先：レポート種別区別の実装

| タスク | 決めるべき詳細 |
|--------|---------------|
| **T2: ca-report-parser** | 期初投資仮説レポート/四半期継続評価レポート/混合の判定アルゴリズム |
| **T4: ca-claim-extractor** | 四半期継続評価レポートから抽出された優位性への警戒フラグの付与 |
| **T7: ca-report-generator** | 四半期継続評価レポート由来の主張への注意書き追加 |

### 13.3 中優先：検証可能性の確保

| タスク | 決めるべき詳細 |
|--------|---------------|
| **T5: ca-fact-checker** | SEC MCP による追加検証の範囲 |
| **T9: 精度検証** | 乖離分析レポートのフォーマット |

### 13.4 エージェント設計の推奨順序

1. **Phase 0**: T0（Lead直接実行）← 既存パターンで実装可能
2. **Phase 1**: T2（ca-report-parser）← レポート種別区別が全体に影響
3. **Phase 2**: T4（ca-claim-extractor）← 暗黙知再現の核心
4. **Phase 3**: T6（ca-pattern-verifier）← 一貫性保証
5. **Phase 4**: T7（ca-report-generator）、T8（3層検証）、T9（精度検証）
6. **Phase 4-5**: T10-T15（暗黙知拡充ループ）← 詳細設計完了

### 13.5 KB精読の推奨

実装開始前に以下のKBを精読すること：

| KB | ファイル数 | 読了目安 | 優先度 |
|----|-----------|---------|--------|
| **KB1** | 8 | 30分 | ★★★ |
| **KB2** | 12 | 40分 | ★★★ |
| **KB3** | 5 | 30分 | ★★ |
| **Dogma** | 1 | 20分 | ★★★ |

**合計**: ~2時間で全KB精読可能

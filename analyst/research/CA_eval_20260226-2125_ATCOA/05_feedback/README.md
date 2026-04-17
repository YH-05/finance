# CA評価フィードバック → Dogma / KB 反映事項

> **元資料**:
> - [Feedback_ATCOA.md](../Feedback_ATCOA.md)（ATCOA）
> - [Feedback_CPRT.md](../../CA_eval_20260226-2046_CPRT/Feedback_CPRT.md)（CPRT）
> - [Analysis_Erie_direction_error.md](../../CA_eval_20260226-2046_CPRT/Analysis_Erie_direction_error.md)（CPRT workflow事象）
> **対象レポート**:
> - [revised-report-ATCOA.md](../04_output/revised-report-ATCOA.md)
> - [revised-report-CPRT.md](../../CA_eval_20260226-2046_CPRT/04_output/revised-report-CPRT.md)
> **作成日**: 2026-04-17
> **評価者フィードバック**: アナリストY

## 目的

複数銘柄のT8修正後レポートに対するアナリストYのフィードバックから、**Dogmaの見直し候補**および**KBの拡張候補**を抽出し、個別ファイルで整理する。本ディレクトリは銘柄横断のフィードバック集約場所として運用する。

## フィードバック一覧

### Dogma 関連（評価方法論の見直し）

| # | ファイル | 論点 | トリガー | 優先度 |
|---|---------|------|---------|-------|
| D1 | [dogma_ca_cagr_independence.md](dogma_ca_cagr_independence.md) | CA確信度×CAGR確信度の独立評価 vs 掛け算方針 | ATCOA #5 | **高** |
| D2 | [dogma_market_growth_ca_cagr_condition.md](dogma_market_growth_ca_cagr_condition.md) | 掛け算適用条件の精緻化（市場並み成長の扱い） | CPRT #4 | 中 |

### KB 関連（評価パターン・基準の拡張）

| # | ファイル | 論点 | トリガー | 優先度 |
|---|---------|------|---------|-------|
| K1 | [kb_multi_segment_dilution.md](kb_multi_segment_dilution.md) | 多部門企業における事業別優位性希薄化評価 | ATCOA | **高** |
| K2 | [kb_negative_stock_pattern.md](kb_negative_stock_pattern.md) | 保有継続疑問型銘柄の評価パターン新設 | ATCOA | **高** |
| K3 | [kb_industry_specific_kpi.md](kb_industry_specific_kpi.md) | 業界特性を考慮したKPI適用基準（Churn Rate等） | ATCOA #1 | 中 |
| K4 | [kb_nominal_gdp_benchmark.md](kb_nominal_gdp_benchmark.md) | 名目GDP基準による成長率優位性判定 | ATCOA | 中 |
| K5 | [kb_causality_separation.md](kb_causality_separation.md) | 複合因果チェーンの個別検証原則 | ATCOA #4 | 中 |
| K6 | [kb_pricing_time_horizon.md](kb_pricing_time_horizon.md) | 足元サイクル vs サイクルスルーのプライシング評価分離 | ATCOA | 低 |
| K7 | [kb_claim_hierarchy.md](kb_claim_hierarchy.md) | Claim間の階層関係と相互強化クラスタ | CPRT #4/#6, #1-3三位一体 | **高** |
| K8 | [kb_industry_macro_vs_firm_factor.md](kb_industry_macro_vs_firm_factor.md) | 業界マクロと企業固有要因の中間領域（hybrid） | CPRT #5 TLF | **高** |
| K9 | [kb_scale_vs_revenue_effect.md](kb_scale_vs_revenue_effect.md) | スケールメリットと増収効果の識別基準 | CPRT #6 | **高** |
| K10 | [kb_evidence_direction_verification.md](kb_evidence_direction_verification.md) | 証拠の方向性検証プロセス（narrative駆動防止） | CPRT Erie誤記事象 | **高** |
| K11 | [kb_geographic_segmentation.md](kb_geographic_segmentation.md) | 地域別分割評価ルール | CPRT #7 | 中 |

### アナリストYへの追加質問

| # | ファイル | 内容 | トリガー | 優先度 |
|---|---------|------|---------|-------|
| Q-ATCOA | [questions_for_analyst_Y.md](questions_for_analyst_Y.md) | ATCOA情報源・判断根拠を引き出す18問 | ATCOA | **高** |
| Q-CPRT | [questions_for_analyst_Y.md](../../CA_eval_20260226-2046_CPRT/05_feedback/questions_for_analyst_Y.md) | CPRT情報源・判断根拠を引き出す20問 | CPRT | **高** |

## 総括

### ATCOA由来の論点

Yのフィードバックは、**AI評価のロジック自体への反論**よりも、**評価の粒度・時間軸・業界特性の適用方法**に対する指摘が中心。特に D1（CA×CAGR独立性）と K1（多部門企業の希薄化）は、KB3（COST, CHD, ORLY, LLY, MNST）の単一事業支配型銘柄では顕在化しなかった論点で、ATCOAが初めて浮上させた構造的課題。

K2（ネガティブ銘柄パターン）は Y 自身が KB 拡張の必要性を明示的に指摘しており、優先的に取り込むべき。

### CPRT由来の論点

CPRT は複占市場・三位一体構造という **Claim間の相互作用** が顕在化した初の銘柄:

- **K7（階層・クラスタ）**: ATCOAでは現れなかった「下位概念への格下げ」「三位一体相互強化」を構造的に扱う必要
- **K8（hybrid factor）**: TLF上昇のような「業界マクロと個社要因の混合」分類が必要。CPRT #5 の AI 90% vs Y 70% 乖離の解消キー
- **K9（スケール識別）**: AIの「比率改善=スケールメリット」短絡判定への歯止め
- **K10（証拠方向性）**: Erie Insurance 方向誤記事例（Analysis_Erie_direction_error.md）から派生したワークフロー品質管理ルール
- **K11（地域分割）**: COST で深堀りされなかった地域別評価の精緻化
- **D2（掛け算条件）**: ATCOA D1 の補遺として、接続構造だけでなく「CAGR寄与の定量性」も掛け算適用条件に組み込む

### クロスカッティング論点

| 論点 | ATCOA ファイル | CPRT ファイル | 統合の方向 |
|------|-------------|-------------|----------|
| CA×CAGR接続 | D1（独立 vs 掛け算） | D2（寄与定量性で条件分岐） | **直交する2軸で統合運用** |
| 因果分離 | K5（複合チェーン分離） | K8（業界×個社の分離） | **因果分離の2類型として整理** |
| 業界 vs 個社 | K3（KPI適用基準） | K8（hybrid factor分類） | **業界適用の多面性として統合** |

### 次回のCA評価ワークフローへの反映

優先順位:

1. **K10（証拠方向性）+ K7（階層）**: ワークフロー品質に直結、早期実装
2. **D1 + D2（CA×CAGR接続）**: Dogma改訂で評価基盤を確立
3. **K8（hybrid）+ K9（スケール識別）**: 頻出誤判定の歯止め
4. **K1, K2, K11**: 特殊銘柄パターンの蓄積
5. **K3, K4, K5, K6, D2**: 運用細則として段階的導入

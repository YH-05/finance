# [D2] Dogma見直し: CA×CAGR掛け算の適用条件精緻化

> **区分**: Dogma（D1補遺）
> **優先度**: 中
> **トリガー銘柄**: CPRT
> **トリガーClaim**: #4 複占市場構造（CA 50% / CAGR 70%）
> **関連**: [D1] [dogma_ca_cagr_independence.md](dogma_ca_cagr_independence.md)

## 論点

### T8批判の掛け算解釈

critique.json（#4）:
> 「dogma.md §3.1『最終納得度は掛け算で評価すべき』に基づけば、Claim#4単体のCAGR寄与は限定的」
> → CA 50% × CAGR 70% = 実質 35% の注記追加

### Yの掛け算適用条件（Feedback_CPRT.md #4）

> 「CAGRの背景として大きな影響与えるCAであれば CAの納得度を割り引く（掛け算する）ことが妥当。**CPRTの売上CAGRでは市場並みの成長を示唆しており、複占市場であることとの関連性薄く、掛け目の引き下げはしない**」

- 「掛け算する」条件: Claim が CAGR への**主要ドライバー**である場合
- 掛け算しない条件: Claim が CAGR に**直接寄与しない基盤条件**である場合

## ATCOA D1 との差異・補完

### ATCOA D1（独立評価 vs 掛け算）

- 論点: CA 確信度と CAGR 確信度は独立か掛け算か
- Y の立場: 独立評価を基本とするが自信なし
- 提案: 接続構造タイプ別ルール（1対1直接接続なら掛け算、1対多・多対1なら独立）

### CPRT D2（市場成長超過の条件）

- 論点: 接続の**向き**だけでなく、CAGR への**寄与の定量性**も条件
- Y の立場: CAGR が市場並みなら Claim は「基盤条件」にすぎず掛け算しない
- 提案: 掛け算適用を「CAGR が市場並み超過を示し、かつ Claim がそのドライバー」である場合に限定

両者は**対立ではなく直交する条件**:
- D1: 接続構造（1対1 / 1対多 / 多対1）
- D2: 寄与の定量性（市場超過 vs 市場並み）

## 問題の本質

### 複占構造のパラドックス

CPRT #4 は典型的な「基盤条件型 Claim」:

| 論点 | 評価 |
|------|------|
| 複占市場 = 新規参入困難 | CA として妥当（基盤条件としての重要性） |
| 複占 → CPRT の売上CAGR寄与 | 限定的（CPRT単独のシェア成長寄与は小さい） |
| 複占 → 他Claim#1-3 の機能前提 | 機能（K7 階層・クラスタで整理） |

AI の「CA 50% × CAGR 70% = 35%」解釈は、**Claim#4 の価値を過小評価**する。
基盤条件として#1-3を機能させる役割の方が重要。

### KB3銘柄での類似構造

| 銘柄 | 基盤条件型Claim | CAGR寄与の性質 |
|------|--------------|--------------|
| COST #2 バイイングパワー | シェアは結果、コスト優位は仕組み | 市場並み以上を牽引 → 掛け算適用 |
| CPRT #4 複占 | 複占は業界構造の結果 | CAGRは市場並み → 掛け算不適用 |
| CHD #4 (仮) 市場地位 | 個別ブランドNo.1地位 | 市場並み → 掛け算不適用 |

## Dogma改訂案

### Proposal A: 掛け算適用条件の3段階

```yaml
multiplication_rule:
  case_1_full_multiplication:
    condition: "Claim が CAGR主要ドライバーで、定量的に market-beat を説明"
    treatment: "最終納得度 = CA × CAGR"
    example: "COST #1 会員制 → CAGR直接寄与"

  case_2_no_multiplication:
    condition: "Claim が CAGR基盤条件（他Claim機能の前提）、市場並み成長"
    treatment: "CA と CAGR を独立評価。掛け算せず加点要素として扱う"
    example: "CPRT #4 複占構造 → #1-3 機能の前提"

  case_3_conditional_multiplication:
    condition: "Claim が CAGR寄与するが業界要因との混合"
    treatment: "hybrid factor ルール（K8）適用。業界部分は独立、個社部分は掛け算"
    example: "CPRT #5 TLF上昇 → 業界70% + 個社調整"
```

### Proposal B: 判定フローチャート

```
Q1: この Claim は CAGR の主要ドライバーか？
  Yes → Q2: 市場並み超過を定量的に示せるか？
    Yes → case_1（full multiplication）
    No → case_2（no multiplication）
  No → Q3: 他 Claim の機能前提として働いているか？
    Yes → case_2（基盤条件、独立評価）
    No → case_3 または Claim 自体の除外検討
```

### Proposal C: claims.json スキーマへの反映

```json
{
  "claim_id": 4,
  "cagr_connection": {
    "confidence": 70,
    "multiplication_case": "case_2_no_multiplication",
    "rationale": "複占構造は #1-3 の機能前提。CPRT売上CAGRが市場並みのため Claim#4 単独のドライバー寄与は限定的。独立評価。"
  }
}
```

### Proposal D: revised-report §2 サマリー表の修正

現行:
> CA 50% × CAGR 70% = 実質 35%（注記）

改訂後:
> CA 50% / CAGR 70%（基盤条件型、独立評価。掛け算不適用）
> 基盤条件として #1-3 の機能前提として重要性評価。

## ATCOA D1 との統合運用

D1（接続構造）と D2（寄与の定量性）の同時適用:

| 接続構造\寄与定量 | 市場超過説明可 | 市場並みのみ |
|---------------|------------|----------|
| 1対1直接接続 | 掛け算適用 | **独立評価**（D2により格上げ） |
| 1対多接続 | 独立評価（D1） | 独立評価 |
| 多対1接続（基盤条件） | 掛け算適用 | **独立評価**（基盤条件として認定） |

**CPRT #4 の位置**: 多対1接続（複占 → #1-3 機能前提）× 市場並み → **独立評価**で確定。

## AI/Y評価の乖離解消

| 項目 | AI評価 | Y評価 | 乖離原因 | 提案後の整合性 |
|------|--------|-------|---------|--------------|
| CA | 50% | 50% | 一致 | - |
| CAGR | 70% | 50% | AIは独立70%としつつ掛け算注記35%、Yは市場並みで接続弱いと判断しCAGRも50%に | case_2（独立評価＋基盤条件）でCAGR 50-70%レンジ |

## アクション

1. dogma v1.1 に掛け算適用条件の3段階（Proposal A）を追加
2. ca-claim-extractor / ca-report-generator に判定フローチャート（Proposal B）を実装
3. claims.json の `cagr_connection` に `multiplication_case` フィールド追加
4. KB3 既存銘柄の全 Claim に multiplication_case を retrofit
5. D1 との統合運用マトリクスを dogma に記載
6. Y本人に「基盤条件 vs ドライバー」の判別基準を ヒアリング（questions_for_analyst_Y.md Q10, Q11 に対応）

## 関連ファイル

- [Feedback_CPRT.md](../../CA_eval_20260226-2046_CPRT/Feedback_CPRT.md) #4
- [revised-report-CPRT.md](../../CA_eval_20260226-2046_CPRT/04_output/revised-report-CPRT.md) §3 #4
- [critique.json](../../CA_eval_20260226-2046_CPRT/04_output/critique.json) #4 批判
- [questions_for_analyst_Y.md](../../CA_eval_20260226-2046_CPRT/05_feedback/questions_for_analyst_Y.md) Q10, Q11
- [D1] [dogma_ca_cagr_independence.md](dogma_ca_cagr_independence.md) - 接続構造タイプ別ルール（本ファイルと直交）
- [K7] [kb_claim_hierarchy.md](kb_claim_hierarchy.md) - 階層・クラスタ（基盤条件の下位判定）
- [K8] [kb_industry_macro_vs_firm_factor.md](kb_industry_macro_vs_firm_factor.md) - hybrid factor（case_3）

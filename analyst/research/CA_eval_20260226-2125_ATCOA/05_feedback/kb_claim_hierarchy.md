# [K7] KB拡張: Claim間の階層関係と相互強化クラスタ

> **区分**: KB 評価構造
> **優先度**: 高
> **トリガー銘柄**: CPRT
> **トリガーClaim**: #4 複占市場構造 / #6 スケールメリット / #1-3 三位一体

## 論点

### Yの階層判定（Feedback_CPRT.md #6）

> 「あくまで2社寡占に近い状況（#4）に規定された中での「スケール」との考えであり **CA評価は＃６＜＃４**」

- Claim#6（スケールメリット）は Claim#4（複占市場構造）の**下位概念**
- Y評価: #4=50%, #6=30% → 下位は上位を超えない

### Yの相互強化指摘（Feedback_CPRT.md #1, #3）

> 「NIMBYヤードの保有（＃２）や保険会社との間で築かれた関係性（＃３）にも起因する高い市場占有率がCOPART社のネットワーク効果をより強化している」
>
> 「CPRTでは、ネットワーク効果（＃１）やNIMBYヤード保有（＃２）にも支えられ高いスイッチングコストが発生している」

- Claim#1-3 は**互いに強化し合う三位一体クラスタ**
- 単独評価より相互依存を認識した上での評価が適切

## 問題の本質

### AI評価の並列独立処理

現状の claims.json は Claim を並列独立に評価する構造:

```json
{
  "claim_id": 1, "confidence": 70,   // 独立
  "claim_id": 4, "confidence": 50,   // 独立
  "claim_id": 6, "confidence": 50    // 独立 ← Yは30%（下位概念）
}
```

**欠落している構造**:
- Claim間の階層関係（A ⊃ B: AがBの上位）
- Claim間の相互強化関係（A ↔ B: 双方向強化）

### KB3銘柄での類似構造

| 銘柄 | 階層/クラスタ構造 |
|------|-------------------|
| ORLY | #1 サービス密度 と #2 フラグメント市場における規模 が相互強化 |
| COST | #1 会員制ロックイン と #2 バイイングパワー が相互強化（会員基盤→購買量→会員価値） |
| CPRT | #1 ネットワーク効果 ↔ #2 NIMBY Yard ↔ #3 スイッチングコスト（三位一体） |
| CPRT | #4 複占 ⊃ #6 スケールメリット（階層） |

→ **階層と相互強化は KB3 でも頻出するが、AI の評価フレームに組み込まれていない**

## KB改訂案

### Proposal A: Claim間関係の明示化（必須項目化）

claims.json のスキーマに以下を追加:

```json
{
  "claim_id": 6,
  "title": "スケールメリット",
  "confidence": 30,
  "hierarchy": {
    "parent_claim_id": 4,
    "relation": "subordinate",
    "constraint": "CA(6) <= CA(4)"
  },
  "cluster": null
}
```

```json
{
  "claim_id": 1,
  "title": "ネットワーク効果",
  "confidence": 70,
  "hierarchy": null,
  "cluster": {
    "cluster_id": "CPRT_triad",
    "members": [1, 2, 3],
    "relation": "mutual_reinforcement",
    "note": "三位一体の相互強化。1つの崩壊は他2つにも波及"
  }
}
```

### Proposal B: 階層関係の判定ルール

Claim A が Claim B の下位概念となる条件:

| 判定基準 | 説明 |
|---------|------|
| 因果的包含 | A の発生が B の存在を前提とする（例: 複占 → 複占下でのスケール） |
| 範囲的包含 | A が B のサブセット（例: 特定地域 → 全体） |
| 時間的包含 | A が B の一部期間のみ成立 |

**ルール化**: 階層関係が認定された場合、`CA(subordinate) ≤ CA(superordinate)` を制約として課す。

### Proposal C: 相互強化クラスタの評価

クラスタメンバー間の相互強化を認めた場合の取り扱い:

1. **個別評価は独立に実施**（現行通り）
2. 総合評価セクションで「クラスタとしての頑健性」を別途評価
3. **連鎖リスク**（1メンバーの崩壊が他に波及する脆弱性）を systematic_issue として明示

CPRT revised-report は§4で三位一体構造を図示しているが、claims.json レベルでは認識されていない。構造化データ側でも明示すべき。

## 既存KB3との整合性

| 現行AI評価 | 階層/クラスタ認識後 |
|-----------|-------------------|
| ORLY #1: 90% | #1-#2 クラスタ評価（頑健性加算） |
| CHD #1: 70%, #7: 50% | #7 が #1 の下位（買収選定能力 → 個別買収成功） |
| COST #1: 90%, #3: 50% | #1 が #3 を下から支える（会員基盤 → バイイング交渉力） |

## アクション

1. claims.json スキーマに `hierarchy` / `cluster` フィールドを追加
2. ca-claim-extractor に階層・クラスタ関係の抽出を指示
3. ca-report-generator に階層制約（`CA(下位) ≤ CA(上位)`）のチェックを実装
4. KB3 既存銘柄についても事後的に階層・クラスタ関係を追加記述
5. Y本人に「CPRT三位一体の連鎖リスク顕在化シナリオ」をヒアリング（questions_for_analyst_Y.md Q17 に対応）

## 関連ファイル

- [Feedback_CPRT.md](../../CA_eval_20260226-2046_CPRT/Feedback_CPRT.md) #6, 追加FB三位一体連鎖リスク
- [revised-report-CPRT.md](../../CA_eval_20260226-2046_CPRT/04_output/revised-report-CPRT.md) §4 三位一体構造図
- [questions_for_analyst_Y.md](../../CA_eval_20260226-2046_CPRT/05_feedback/questions_for_analyst_Y.md) Q11, Q17
- [D1] [dogma_ca_cagr_independence.md](dogma_ca_cagr_independence.md) - 1対多接続の扱い

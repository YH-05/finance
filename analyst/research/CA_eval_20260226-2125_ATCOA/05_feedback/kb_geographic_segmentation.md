# [K11] KB拡張: 地域別分割評価ルール

> **区分**: KB 評価粒度
> **優先度**: 中
> **トリガー銘柄**: CPRT
> **トリガーClaim**: #7 海外市場での横展開可能なビジネスモデル

## 論点

### AI評価（CA 50% / CAGR 70%）

根拠:
- 英国シェア4割、International +17%超
- 「定性的、大陸系はスクラッチ構築中」と注記しつつも単一スコア

### Yの分離指摘（Feedback_CPRT.md #7）

> 「国内ノウハウの移管面では優位。一方で **NIMBYヤードの確保がされている国内に比べて、これから横展開してゆく海外では優位性が劣る**と考えるため納得度評価は中位、並み」

- 「実績市場」（英国: 既にシェア4割達成）
- 「進出中市場」（大陸欧州: スクラッチ構築中）
- 両者を**単一スコアで評価するのは不正確**

## 問題の本質

### 単一スコア評価の情報損失

現行の claim 構造は1 Claim = 1 confidence:

```json
{
  "claim_id": 7,
  "title": "海外市場での横展開可能なビジネスモデル",
  "confidence": 50,  // 英国成功＋大陸進出中を混合評価
  "source_sections": ["S4"]
}
```

**損失情報**:
- 英国単独では何%か（おそらく70-90%）
- ドイツ等大陸単独では何%か（おそらく30-50%）
- 両者の加重平均で50%としているが、Volume加重なのか単純平均なのかが不透明

### KB3銘柄との比較

| 銘柄 | 地域展開の扱い | 評価粒度 |
|------|-------------|---------|
| COST | 米国/海外を分離せず #5 で単一評価 (20%) | 分離不十分 |
| CPRT | 米75% / 海外17%（International成長率開示あり）を単一評価 | **分離可能** |
| ORLY | 米国中心、Mexico進出中 | 分離の必要性低い |
| CHD | 米国中心、海外比率低 | 分離の必要性低い |

→ CPRT は地域別データが相対的に開示されており、**分離評価の精度向上余地が大きい**

## KB改訂案

### Proposal A: 地域サブClaim への分割

1 Claim を地域別に分割:

```json
{
  "claim_id": 7,
  "title": "海外市場での横展開可能なビジネスモデル",
  "geographic_breakdown": [
    {
      "region": "UK",
      "status": "established",
      "market_share": 0.4,
      "sub_confidence": 70,
      "evidence": "シェア4割、実績あり"
    },
    {
      "region": "Continental Europe (Germany etc.)",
      "status": "entering",
      "market_share": null,
      "sub_confidence": 30,
      "evidence": "スクラッチ構築中、NIMBY未確保"
    },
    {
      "region": "Other International",
      "status": "mixed",
      "market_share": null,
      "sub_confidence": 50,
      "evidence": "Purple Wave等含む"
    }
  ],
  "aggregate_confidence": 50,
  "aggregation_method": "volume_weighted"
}
```

### Proposal B: ステータス別評価テンプレート

地域の成熟ステータスに応じた評価上限:

| ステータス | 定義 | CA confidence 上限 |
|-----------|-----|------------------|
| established | 開示可能なシェア実績あり、黒字化 | 90% |
| entering | 事業進行中、シェア開示なし | 50% |
| exploring | 市場調査・パイロット段階 | 30% |
| not_entered | 未進出 | N/A（評価対象外） |

進出中市場は実績が出るまで 50% 上限。集約評価では volume/revenue 加重。

### Proposal C: 米国モデルの普遍性評価

海外展開の CA を評価する際、**米国モデルの普遍性**を別途評価:

| 米国特有要素 | 海外での成立条件 | 調査項目 |
|-----------|--------------|---------|
| 損保会社集中度（80%） | 各国の損保市場構造 | Motor insurance penetration, top-5 concentration |
| 全損判定率（21.4%） | 修理費 vs 車両価格比 | 各国の修理費水準、車齢分布 |
| 廃車規制・所有権移転 | 各国の法制度 | ELV Directive等の規制 |
| NIMBY立地 | 都市構造・住民反応 | 都市部/郊外配置の違い |

普遍性が低い要素（例: NIMBY立地）が多い地域は、海外展開 confidence を引き下げ。

### Proposal D: 集約評価の透明化

地域別 sub_confidence から aggregate_confidence を計算する方式を明示:

```
aggregate = Σ(sub_confidence_i × weight_i)
  weight_i = revenue_share_i  # 売上比率加重（デフォルト）
  または
  weight_i = opportunity_share_i  # 機会規模加重（forward-looking）
```

CPRT #7 の場合:
- UK: sub 70% × revenue_share ~5% = 3.5pt
- Continental: sub 30% × revenue_share ~10% = 3.0pt
- Other Int'l: sub 50% × revenue_share ~2% = 1.0pt
- 海外全体 weighted avg ≈ 45%

## AI/Y評価の乖離解消

| 項目 | AI評価 | Y評価 | 乖離原因 | 提案後の整合性 |
|------|--------|-------|---------|--------------|
| CA | 50% | 50% | 一致 | 粒度を上げても収斂 |
| CAGR | **70%** | **50%** | AIは過去成長を前提、Yは海外NIMBY未確保を重視 | 地域別 sub-confidence で Continental の低評価を反映 |

## アクション

1. claims.json スキーマに `geographic_breakdown` フィールド追加（Proposal A）
2. dogma v1.1 にステータス別 confidence 上限ルール追加（Proposal B）
3. industry-researcher に「各国損保市場構造」の調査タスクを追加（Proposal C）
4. 集約評価の加重方式を structured.json に明示（Proposal D）
5. Y本人に地域別評価の選好をヒアリング（questions_for_analyst_Y.md Q15, Q16 に対応）

## 関連ファイル

- [Feedback_CPRT.md](../../CA_eval_20260226-2046_CPRT/Feedback_CPRT.md) #7
- [revised-report-CPRT.md](../../CA_eval_20260226-2046_CPRT/04_output/revised-report-CPRT.md) §3 #7
- [questions_for_analyst_Y.md](../../CA_eval_20260226-2046_CPRT/05_feedback/questions_for_analyst_Y.md) Q15, Q16

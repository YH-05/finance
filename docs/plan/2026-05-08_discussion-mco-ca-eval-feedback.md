# 議論メモ: MCO CA評価のAN批判分析と評価フレームワーク改善

**日付**: 2026-05-08
**議論ID**: disc-2026-05-08-mco-ca-eval-feedback
**プロジェクト**: quants-analyst-tacit-knowledge
**前回議論**: disc-2026-04-09-fm-an-perspective（FM目線とAN目線の差異）

---

## 背景・コンテキスト

`analyst/research/CA_eval_20260226-2059_MCO/` で実施した MCO の競争優位性評価に対し、アナリストYから `Feedback_MCO.md` で詳細フィードバックを受領。AI評価とAN評価の乖離を分析し、評価フレームワークの構造的問題を特定する必要が生じた。

旧版（CA_eval_20260220-0931_MCO）と新版（CA_eval_20260226-2059_MCO、T8修正版）の両方で同様の判定バイアスが見られたため、単発の評価ミスではなく**評価パイプライン全体の構造的問題**として診断を実施。

---

## 議論のサマリー

### Phase 1: 乖離マトリクス作成

7主張の AI評価 vs AN評価 を整理:

| # | 主張 | AI評価 | AN評価 | 主な乖離 |
|---|------|-------|--------|---------|
| 1 | 寡占構造 | 90% | 70% | -20pt（事業構成希薄化） |
| 2 | プライシングパワー | 70% | 70% | 一致だがロジック批判 |
| 3 | スイッチングコスト | 70% | 70% | 一致 |
| 4 | MAデータ蓄積 | 50%/70% | 50%/70% | 一致だが評価軸批判 |
| 5 | PC市場成長 | 50% | 30%/50% | CA -20pt |
| 6 | ブランド認知 | 30% | 50% | CA +20pt（逆方向） |
| 7 | 借換え需要 | 30%/70% | 30%/50% | CAGR -20pt |

平均 CA: 56% → 49%（-7pt）、平均 CAGR: 71% → 62%（-9pt）

### Phase 2: 5論点の特定と質問群作成

| 論点 | 内容 | 質問群 |
|------|------|--------|
| A | 保守性≠確度の原則（claim#2） | Q-A1〜A6 |
| B | 定量データ vs 論理整合性（claim#4） | Q-B1〜B5 |
| C | 事業構成ブレンド評価（claim#1） | Q-C1〜C5 |
| D | ブランド認知の独立性（claim#6） | Q-D1〜D5 |
| E | 市場機会と環境要因（claim#5/#7） | Q-E1〜E5 |

すべて `analyst/research/CA_eval_20260226-2059_MCO/Inverview_MCO_20260508.md` に詳細記載。

### Phase 3: 根本原因診断

「なぜAIが定量データで納得度を高める判定を下したか」の原因を6項目で診断:

1. **エージェント定義のルール4 短縮化**: dogma原典「説明力MUST、定量WANT」が agent 側で「定量的裏付け」に縮約
2. **KB2 D/I の非対称構造**: 定量を加点（+20%）、定性を減点（-10〜20%）する設計
3. **パターンD 修正の未反映**: 2026-02-26 の KB 修正が agent 定義に伝播していない
4. **論理整合性独立評価機構の不在**: パターンC（因果飛躍）が定量データ依存判定
5. **KB3 few-shot の偏り**: 90%評価例がすべて定量豊富、LLM のパターンマッチング偏り
6. **T8 批判の比較軸誤り**: COST との比較で「定量データの有無」を主軸化

詳細は `analyst/research/CA_eval_20260226-2059_MCO/memo_eval_logic_diagnosis_20260508.md`。

---

## 決定事項

| ID | 内容 | 確度 |
|----|------|------|
| dec-2026-05-08-003 | claim#4 の評価で「定量データの存在で論理整合性を担保する」運用は誤り。AN原則「論理連鎖の決定要因の妥当性が一次評価軸」を採用 | tentative（要AN確認） |
| dec-2026-05-08-004 | dogma_v1.0.md ルール4 のテキスト自体は AN 原則と整合。問題は運用パイプライン6箇所のバイアス | active |
| dec-2026-05-08-005 | フレームワーク改善は AN 質問回答後に確定。優先回答は Q-A1（confidence 定義）と Q-A2(b)（バイアス調整） | active |

---

## アクションアイテム

| ID | 内容 | 優先度 | 期限 |
|----|------|--------|------|
| act-2026-05-08-002 | アナリストYに質問群を提示し回答取得（Q-A1, Q-A2(b) 優先） | 高 | 2026-05-15 |
| act-2026-05-08-003 | ca-pattern-verifier.md:49 のパターンD を 2026-02-26 修正版に同期 | 中 | - |
| act-2026-05-08-004 | ca-claim-extractor.md / ca-report-generator.md のルール4 表現を原典通りに修正 | 中 | - |
| act-2026-05-08-005 | KB2 に論理整合性パターンを新設、パターンC の判定基準変更（要AN回答） | 中 | - |
| act-2026-05-08-006 | revised-report-MCO.md の v3 作成（AN回答反映版） | 低 | - |

---

## 次回の議論トピック

- AN 回答取得後の論点別深掘り（特に B: 論理整合性、C: 事業構成ブレンド）
- KB3 全体の運用監査の必要性判断（既存の COST/ORLY/MNST 評価が AN 原則で変わるか）
- 業界決定要素マップの整備方針（Q-B5）
- フィードバックループ vs ダブルカウントの判定基準（Q-D5）

---

## 参考情報

### 関連ファイル

- `analyst/research/CA_eval_20260226-2059_MCO/Feedback_MCO.md` - AN フィードバック原文
- `analyst/research/CA_eval_20260226-2059_MCO/04_output/revised-report-MCO.md` - T8修正版レポート
- `analyst/research/CA_eval_20260226-2059_MCO/Inverview_MCO_20260508.md` - AN追加質問
- `analyst/research/CA_eval_20260226-2059_MCO/memo_eval_logic_diagnosis_20260508.md` - 根本原因診断
- `analyst/research/CA_eval_20260220-0931_MCO/04_output/revised-report-MCO.md` - 旧版レポート
- `analyst/Competitive_Advantage/analyst_YK/dogma/dogma_v1.0.md` - 評価ルール原典
- `analyst/Competitive_Advantage/analyst_YK/kb2_patterns/pattern_D_qualitative_only.md` - 2026-02-26 修正
- `.claude/agents/ca-claim-extractor.md`, `ca-pattern-verifier.md`, `ca-report-generator.md`

### Neo4j 保存先

- Project: `quants-analyst-tacit-knowledge`
- Discussion: `disc-2026-05-08-mco-ca-eval-feedback`
- Decisions: `dec-2026-05-08-003`, `dec-2026-05-08-004`, `dec-2026-05-08-005`
- ActionItems: `act-2026-05-08-002` 〜 `act-2026-05-08-006`
- 前回議論との接続: `FOLLOWS → disc-2026-04-09-fm-an-perspective`

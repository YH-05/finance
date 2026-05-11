# 議論メモ: ファンドコンセプト・リサーチ方向性の再構築

**日付**: 2026-05-11
**議論ID**: disc-2026-05-11-fund-research-restructure
**参加**: ユーザー + AI (Opus 4.7)
**親プロジェクト**: quants-analyst-tacit-knowledge

---

## 背景・コンテキスト

既存リサーチメモ `analyst/memo/2026-05-06_AI_augmentation_research_for_fund_concept.md`（8章・25論文以上の整理済み）の内容が「ファンドコンセプト訴求」の観点では不足しているという問題提起から、追加リサーチの方向性を議論。

### 既存リサーチの到達点

- 6軸構造（A-F: Centaur, 暗黙知伝播, ルーチン外, ノイズ削減, 認知拡張, 形式知化）
- KY/Y固有: 12ルール・却下7パターン・高評価5パターン・4ステップワークフロー
- ファンド構想: ハイブリッド構成（システムプロンプト + RAG）、Phase 0-2改善サイクル、PoC 8銘柄完了

### 既存リサーチの弱点（メモ自体が認識）

1. 軸F（形式知化）のエビデンスが薄い
2. 金融特化のRCT実証、資産運用業界事例、規制、Kahneman最終発言、AI増強型アクティブの位置付け

### AIが指摘した追加ギャップ

- マルチエージェント本体の研究（Du, Liang, FinMem等）が空白
- 暗黙知抽出の方法論（インタビュー、think-aloud等）が薄い
- 専門家判断バイアス研究が薄い
- 「優秀なアナリスト」の認知特性研究が皆無
- AI/MLファンドの実トラックレコード
- LP/機関投資家の評価軸
- 日本市場の特殊性

---

## 議論のサマリー

### Q1: リサーチの最終ゴール

→ **LP/投資家への訴求資料**

### Q2: ターゲットLP

→ **国内機関投資家 × シード期**

含意:
- 守り型: コンプライアンス・説明可能性・リスク管理体制が必須
- 慎重: 国内既存 AI/クオンツ機関との差別化を厳しく問われる
- シード期: チーム × コンセプト × プロセス × PoC で実績代替を論証

### Q3: 最大ギャップ

→ **競合カテゴリ + AI増強型アクティブのカテゴリ確立**

戦略: ポジショニング/カテゴリ創出
- 「純粋AIクオンツ」でも「純粋人手アクティブ」でもない第3カテゴリ
- 競合のトラックレコードで「カテゴリ存在/儲かる」を証明
- 自社をリーディングエッジとして位置付け

### Q4: 実行期限

→ **期限なし・継続蓄積**

### Q5: コンセプトの核心 — 重要な発見

ユーザー回答:
> 「アナリストYのような熟練アナリスト/ファンドマネージャーの暗黙知を、マルチエージェントの形でスケールして Information Coefficient の要素2つを同時に高める、というコンセプト」

→ **Fundamental Law of Active Management (Grinold 1989)** の枠組み

$$IR = IC \times \sqrt{BR}$$

| 要素 | 既存アクティブ | 既存クオンツ | Y × MAS |
|---|---|---|---|
| IC（予測の質） | 高 | 中〜低 | **高**（Y型暗黙知） |
| BR（独立予測数） | 低（人手依存） | 高 | **高**（MAS並列） |
| IR | 頭打ち | 限界 | **両方押上** |

### Q6: IC の2要素の定義

→ **IC（予測の質）と Breadth（独立予測の数）** — Fundamental Law の核心解釈

### Q7: 7軸プランの調整

→ **三核心グループ化**: A+B+C を「Fundamental Law 三本柱」、D+E を「業界証拠」としてグループ化

### Q8: 確定方針

→ **確定・保存し、全軸にActionItemを発行**

---

## 決定事項

| ID | 内容 |
|----|------|
| dec-2026-05-11-001 | ファンドコンセプトの理論的バックボーンに Fundamental Law of Active Management (Grinold 1989; IR = IC × √BR) を採用 |
| dec-2026-05-11-002 | リサーチ構造を「三核心 + LP応用」の階層に再整理。継続蓄積方針、全軸並行でActionItem発行 |

---

## 最終リサーチ構造

```
【核心1: Fundamental Law 三本柱】— IR = IC × √BR の論証
├── A. Fundamental Law of Active Management の理論
│   Grinold (1989), Grinold & Kahn (2000), Clarke/de Silva/Thorley (2002:TC拡張),
│   Buckle (2004), Ye (2008), Schmidt et al. (2019), Coqueret & Guida (2022)
├── B. IC × Breadth 同時最適化の経験的研究
│   IC希釈問題、Independent bets定義困難性、ファクター集中の罠
└── C. マルチエージェントによる Breadth 拡大
    Du et al. (2023), Liang et al. (2023), FinMem/FinAgent/FinCon,
    BlackRock AlphaAgents, agent diversity

【核心2: 業界証拠】— カテゴリ確立
├── D. 競合分析を Fundamental Law レンズで分類
│   Quantamental(中IC・中BR) / 純粋クオンツ(低IC・高BR) /
│   純粋アクティブ(高IC・低BR) vs Y×MAS(高IC・高BR)
└── E. 業界IR水準の実証
    SPIVA reports, BlackRock SAE/Acadian/Two Sigma の公開IR、
    AI/MLファンド実績（Eurekahedge AI/ML Index等）

【核心3: 暗黙知証拠】— IC 維持の証拠
└── F. Y型暗黙知のIC安定性
    既存メモ（2026-05-06_AI_augmentation_research_for_fund_concept.md）の
    Augmentation研究をFundamental Law視点で再フレーミング

【応用: LP訴求設計】
└── G. 国内機関投資家のIR評価軸
    GPIF・年金・生損保の運用機関選定基準、IRベース評価の実態、
    AIファンド評価軸
```

---

## アクションアイテム

| ID | 軸 | 内容 | 優先度 |
|----|----|------|--------|
| act-2026-05-11-006 | A | Fundamental Law理論文献の精読 + 新章追加 | 高 |
| act-2026-05-11-007 | B | IC×Breadth経験的研究の文献調査 | 中 |
| act-2026-05-11-008 | C | マルチエージェント文献調査（Du, Liang, FinMem等） | 高 |
| act-2026-05-11-009 | D | 競合の自社紹介資料・IR資料・ピッチデック収集 | 高 |
| act-2026-05-11-010 | E | SPIVA + AI/MLファンドの公開IR・実績収集 | 高 |
| act-2026-05-11-011 | F | 既存メモのFundamental Law視点再フレーミング | 中 |
| act-2026-05-11-012 | G | 国内機関投資家の運用機関選定基準調査 | 中 |

---

## 既存メモとの関係

既存メモ `analyst/memo/2026-05-06_AI_augmentation_research_for_fund_concept.md` の6軸構造は **軸F（Y型暗黙知のIC安定性）** のサブセットとして再配置される。具体的再解釈:

| 既存メモの軸 | Fundamental Law視点での再解釈 |
|---|---|
| A. AI×人間協働 | IC × Breadth の同時押し上げの一般定理 |
| B. 暗黙知伝播 | **IC維持の経験的証拠**（Brynjolfsson QJE 2025）|
| C. ルーチン外でも品質向上 | IC安定性の経験的証拠（Dell'Acqua HBS WP 24-013）|
| D. ノイズ削減 | **IC安定性向上**（Kahneman *Noise*）|
| E. 認知拡張 | IC × Breadth 拡張の一般枠組み |
| F. 形式知化 | 暗黙知の AI 移植可能性（IC伝達の理論的可能性）|

---

## 次回の議論トピック

- 各軸の初期文献調査結果のレビュー（軸ごと/まとめて）
- 軸C のMAS文献調査結果から、自社の MAS アーキテクチャ設計への含意
- 軸D の競合分析結果から、ポジショニング・スライドのドラフト
- 軸E の業界IR水準データから、訴求数字の確定
- 軸F の既存メモ再フレーミング後の新メモのレビュー
- LP訴求資料の構造ドラフト（軸G の評価軸を組み込んだピッチデックスケルトン）

---

## 参考情報

- 既存リサーチ: `analyst/memo/2026-05-06_AI_augmentation_research_for_fund_concept.md`
- 関連プロジェクト: `analyst/memo/phase0_philosophy_injection_design.md`（KY 12ルール体系）
- AN目線形式知化方針: project memory `project_fm_an_perspective_discussion.md`（判断パスカタログ + RAG 方式）
- アナリストユニバース: project memory `project_analyst_universe.md`（300-400銘柄）
- 直前の議論: `docs/plan/2026-05-11_discussion-feedback-loop-recap.md`（MCO/LRCX フィードバックループ）

---

## 保存先

- Neo4j Discussion: `disc-2026-05-11-fund-research-restructure`
- Neo4j Decisions: `dec-2026-05-11-001`, `dec-2026-05-11-002`
- Neo4j ActionItems: `act-2026-05-11-006` 〜 `act-2026-05-11-012`
- Project リンク: `quants-analyst-tacit-knowledge` -[:HAS_DISCUSSION]-> Discussion
- ドキュメント: `docs/plan/2026-05-11_discussion-fund-research-restructure.md`

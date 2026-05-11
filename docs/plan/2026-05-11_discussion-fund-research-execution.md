# 進捗保存: 7軸リサーチ並列実行と統合サマリー作成

**日付**: 2026-05-11
**議論ID**: disc-2026-05-11-fund-research-execution
**親プロジェクト**: quants-analyst-tacit-knowledge
**前段議論**: disc-2026-05-11-fund-research-restructure（構造合意）

---

## 背景・コンテキスト

`disc-2026-05-11-fund-research-restructure` で合意した「三核心 + LP応用」7軸構造に基づき、各軸を並列サブエージェントで実行し、リサーチメモを `analyst/memo/` に保存した。

ファンドコンセプト全体像:
- 目的: 国内機関投資家×シード期 LP 向け訴求
- 理論バックボーン: Fundamental Law of Active Management (IR = IC × √BR)
- 戦術: 「AI増強型アクティブ」のカテゴリ確立
- Y型熟練アナリストの暗黙知でIC維持、マルチエージェントでBreadth_eff拡大

---

## 実行サマリー

### 並列実行した7軸

| 軸 | テーマ | 自己評価 | ファイル文字数 |
|:--:|------|:----:|:----:|
| A | Fundamental Law 理論 | ★★★★★ | 〜7,300 |
| B | IC×BR 経験的研究 | ★★★★☆ | 〜19,300 |
| C | マルチエージェント | ★★★★★ | 〜8,200 |
| D | 競合分析 | ★★★★☆ | 〜24,400 |
| E | 業界IR水準 | ★★★★★ | 〜10,000 |
| F | 暗黙知IC再フレーミング | ★★★★☆ | 〜7,500 |
| G | 国内機関投資家評価軸 | ★★★★★ | 〜16,000 |
| **統合** | 統合サマリー | — | 〜5,000 |
| **合計** | | | **〜97,700** |

### 生成ファイル一覧

`/Users/yukihata/Desktop/quants/analyst/memo/`:
- `2026-05-11_axes-integration-summary.md`
- `2026-05-11_axis-A_fundamental-law-theory.md`
- `2026-05-11_axis-B_ic-breadth-empirical.md`
- `2026-05-11_axis-C_multi-agent-breadth.md`
- `2026-05-11_axis-D_competitive-landscape.md`
- `2026-05-11_axis-E_industry-ir-evidence.md`
- `2026-05-11_axis-F_tacit-knowledge-reframing.md`
- `2026-05-11_axis-G_jp-institutional-ir-criteria.md`

---

## 決定的発見（LP訴求の核 7つ）

| # | 発見 | 軸 | LP訴求での意義 |
|:--:|------|:--:|---|
| 1 | **IR の N→∞ 上限 = μ_IC/σ_IC**（Qian-Hua/Ding-Martin Redux） | A/B | 「σ(IC)抑制」が隠れた優位軸として理論的に存在 |
| 2 | **Buckle Effective Breadth ⇔ Yang Effective Channel** の数理的同型 | B/C | MAS設計と Fundamental Law が直結 |
| 3 | **純AI (AIEQ) 設定来劣後** vs **Acadian 93-94% BM超過** | E/D | カテゴリ二分割の業界実証 |
| 4 | **IC-BR散布図右上の業界空白** | D | Y × MAS が独占可能ポジション |
| 5 | **DE Shaw Cogence Fund $3-5B でクオンツ巨人がディスクレショナリー回帰** | D | 業界トレンドが方向性を肯定 |
| 6 | **AOP補充原則3-4（142機関受入）+ 金商法改正（資本金1000万円・外注可）** | G | シード期に絶好の制度追い風 |
| 7 | **McLean-Pontiff 公開後35%減衰** | B/F | 未公表IC（Y暗黙知）優位の最強論拠 |

---

## 軸間連携の数理的・実証的接続

```
                                ┌──────────────────────────────────────────┐
                                │  Grinold 1989: IR = IC × √BR (軸A)        │
                                │  Ding-Martin Redux: ≤ μ_IC / σ_IC         │
                                └──────────────┬───────────────────────────┘
                                               │
                ┌──────────────────────────────┼───────────────────────────┐
                │ IC側                          │                    BR側   │
                ▼                              │                            ▼
  ┌────────────────────────────┐               │            ┌────────────────────────────┐
  │ 軸F: Y型暗黙知のIC維持/移植 │               │            │ 軸C: MAS で Breadth_eff 拡大│
  │  - Brynjolfsson QJE 2025    │               │            │  - Du/Liang MAD            │
  │  - Dell'Acqua HBS 24-013    │               │            │  - Yang et al effective Ch │
  │  - Kahneman Noise (σ_IC削減)│               │            │  - Miyazaki Oxford fine-gr.│
  │  - Kim/Muhn EPS 60.4%       │               │            │  - BlackRock AlphaAgents   │
  └────────────────────────────┘               │            └────────────────────────────┘
                ▲                              │                            ▲
                │                              │                            │
                │    軸B: IC希釈/Effective Breadth (Buckle 2004 ⇔ Yang 2026)
                │      - McLean-Pontiff: 公開アノマリー35%減衰（未公表IC優位）
                │      - Strongin/Polakow-Gebbie: 相関考慮で BR は急速縮退
                │
                └────── 軸D/E で業界実証 ────────┘

                       軸D: 競合分類（IC-BR散布図、右上空白を明示）
                       軸E: 業界IR水準（純AI劣後 vs Quantamental勝利の実証）
                                  │
                                  ▼
                       軸G: 国内機関LP訴求設計
                       （AOP補充原則3-4、AI評価軸、ピッチ30分構成）
```

---

## アクションアイテム（次の議論候補）

| ID | 内容 | 優先度 |
|----|------|:----:|
| act-2026-05-11-013 | ピッチ資料スケルトン作成（軸G骨子 + 軸D/E数字 + 軸A/B/C/F理論） | 高 |
| act-2026-05-11-014 | Y暗黙知のIC化（既存 KY 12ルール体系の IC 算出フレーム変換） | 高 |
| act-2026-05-11-015 | MAS実装設計レビュー（Yang/Miyazaki/AlphaAgents 知見の取り込み） | 中 |
| act-2026-05-11-016 | PoC 検証計画（軸B/F の理論主張を自社データで実証） | 中 |
| act-2026-05-11-017 | 競合ベンチマーク選定（Acadian/AQR QMNIX/BlackRock SAE 等の絞り込み） | 低 |

---

## 完了済 ActionItem（軸A-G 個別調査）

| ID | 軸 | 状態 |
|----|:--:|:----:|
| act-2026-05-11-006 | A | completed |
| act-2026-05-11-007 | B | completed |
| act-2026-05-11-008 | C | completed |
| act-2026-05-11-009 | D | completed |
| act-2026-05-11-010 | E | completed |
| act-2026-05-11-011 | F | completed |
| act-2026-05-11-012 | G | completed |

---

## リサーチギャップ（継続調査推奨）

| 弱点 | 軸 | 必要なエビデンス |
|---|:--:|---------------|
| Y個人のIC直接測定 | F | 5銘柄×31件評価データから IC 推定 |
| Y×MAS固有のσ(IC)削減効果 | B | MAS構成の独立性指標と σ(IC) 関係性の実証 |
| Schmidt et al. 2019 出典 | A | Buckle 2014 / Boyd 2017 / Gârleanu-Pedersen 2013 が代替候補 |
| Grinold 1989 原典 + G&K 2000 Ch.6 Appendix 6A | A | 物理書籍経由で精読要 |
| Capital Group Multiple Manager System との差別化 | D | 同社の最新公開情報深掘り |
| Bridgewater AIA Labs の詳細 | D | 業界専門レポート要 |

---

## 想定批判への準備（軸G の B1-B12 抜粋）

| 批判 | 反論材料 |
|---|---|
| 「シード期で実績がない」 | AOP補充原則3-4「業歴で排除しない」、ピッチ30分構成にPoC実証データ枠 |
| 「AIブラックボックス」 | 軸C: Miyazaki fine-grained task decomposition → 説明可能性を構造で担保 |
| 「過学習・データマイニング」 | 軸B: McLean-Pontiff 公開後35%減衰 → 未公表IC優位、軸F: Y暗黙知は固有 |
| 「キャパシティ問題」 | 軸B: Buckle Effective Breadth 上限を明示認識、capacity を IR と切り離して訴求 |
| 「Y属人化リスク」 | 軸F: 暗黙知のAI移植可能性（Brynjolfsson, Kim/Muhn）+ MAS で複数AN対応 |
| 「Boosted.ai と何が違う」 | 軸D: ツール提供 vs ファンド組成、Y固有判断パスカタログ |
| 「DE Shaw Cogence と何が違う」 | 軸D: 巨人クオンツのディスクレショナリー回帰は方向性肯定、規模・国内特化で差別化 |

---

## 保存先

- **Neo4j Discussion**: `disc-2026-05-11-fund-research-execution`
- **Neo4j ActionItems**: `act-2026-05-11-013` 〜 `017`（新規、pending）
- **Neo4j ActionItems**: `act-2026-05-11-006` 〜 `012`（completed、軸個別）
- **Neo4j リレーション**: Project→Discussion (HAS_DISCUSSION), Discussion→Discussion (FOLLOWS_UP), Discussion→ActionItem (PRODUCED×5)
- **リサーチメモ**: `analyst/memo/2026-05-11_axis-*.md`（7軸）+ `2026-05-11_axes-integration-summary.md`（統合）
- **本ドキュメント**: `docs/plan/2026-05-11_discussion-fund-research-execution.md`

---

## 次回の議論候補トピック

1. **ピッチ資料スケルトンのドラフトレビュー**（act-013）
2. **Y暗黙知のIC化フレーム設計**（act-014）— 既存12ルールから IC 算出パイプラインへ
3. **MAS実装設計の更新**（act-015）— Stage 2部分完了状態に Yang/Miyazaki 知見を取り込む
4. **PoC 検証計画書**（act-016）— 自社データで軸B/F 理論主張を実証
5. **ベンチマーク選定の合意**（act-017）— Acadian / AQR / BlackRock SAE / Eurekahedge AI/ML Index の優先順位

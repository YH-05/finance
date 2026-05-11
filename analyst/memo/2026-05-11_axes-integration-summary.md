# 7軸統合サマリー — ファンドコンセプト訴求の論証体系

**作成日**: 2026-05-11
**目的**: 軸A〜G の調査結果を統合し、LP訴求の中核ナラティブを構築
**根拠**: `disc-2026-05-11-fund-research-restructure`（Neo4j）+ 7軸個別メモ

---

## 0. 統合ナラティブ（30秒ピッチ）

> **既存アクティブは IC 高くスケール不能、既存クオンツは BR 高くシグナル劣化。** 我々は Y型熟練アナリストの暗黙知でICを高位維持し、マルチエージェントで Breadth_eff を拡大することで、Fundamental Law of Active Management の理論限界 IR = μ_IC / σ_IC（Ding-Martin redux）に最も近づくファンドを構築する。AIEQ ETF が示した「純AIは負ける」結論と、Acadian/AQR Quantamental が示した「人 × 規律の融合は勝つ」結論の、その先のフロンティアに位置する。

---

## 1. 各軸の主要発見（強度評価付き）

| 軸 | テーマ | 強度 | 決定的な発見 |
|----|--------|:----:|:------------|
| **A** | Fundamental Law 理論 | ★★★★★ | Qian-Hua (2004): **IR = mean(IC)/std(IC)** — σ(IC)抑制こそ隠れた優位軸 |
| **B** | IC×BR 経験的研究 | ★★★★☆ | Ding-Martin Redux: **IR の N→∞ 上限 = μ_IC/σ_IC**（無限BR不可、Buckle: ρ=0.1, N=500 → BR_eff≈10 縮退） |
| **C** | マルチエージェント | ★★★★★ | Yang et al. (2026): **2多様 ≧ 16同質** — effective channel K* が上限、N ではない。**Buckle の Effective Breadth と数理的同型** |
| **D** | 競合分析 | ★★★★☆ | **IC-BR 散布図右上（高IC×高BR）が実質空白** + DE Shaw Cogence Fund $3-5B でクオンツ巨人がディスクレショナリー回帰 |
| **E** | 業界 IR 実証 | ★★★★★ | **純AI ETF (AIEQ) 設定来劣後、純AI型11本平均-1.8%** vs Acadian 93-94% BM超過、AQR QMNIX 5年18.7%、RIEF 2024 +22.7% |
| **F** | 暗黙知 IC 再フレーム | ★★★★☆ | Kim/Muhn/Nikolaev (2024): **GPT-4 EPS 予測 60.4% vs 人間 52.7%**、Otis 2024 Kenya RCT 上位+18% / 下位マイナス |
| **G** | 国内機関投資家 | ★★★★★ | **AOP補充原則3-4「新興運用業者を業歴で排除しない」142機関受入表明 + 金商法改正で資本金1000万円・ミドルバック外注可** |

---

## 2. 軸間の数理的・実証的接続

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
  │  - Kahneman Noise (σ_IC削減)│               │            │  - Miyazaki Oxford fine-grain│
  │  - Kim/Muhn EPS 60.4%       │               │            │  - BlackRock AlphaAgents   │
  └────────────────────────────┘               │            └────────────────────────────┘
                ▲                              │                            ▲
                │                              │                            │
                │    軸B: IC希釈/Effective Breadth (Buckle 2004 ⇔ Yang 2026 同型)
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

### 数理的同型の発見（軸B ⇔ 軸C）
- **軸B**: Buckle (2004) "Effective Breadth" — 相関 ρ で BR_eff = N / (1 + (N-1)ρ)
- **軸C**: Yang et al. (2026) "Effective Channel K*" — エージェント多様性で実効通信容量
- → **同じ数式構造**。MAS の多様性確保がそのまま Fundamental Law の BR_eff 拡大に対応

### 実証的連鎖（軸E ⇔ 軸F ⇔ 軸D）
- **軸E**: 純AI (AIEQ) 失敗、Quantamental 成功 → AI単独ではIC足りない
- **軸F**: GPT-4 が人間のEPS予測を上回る (Kim/Muhn) → AIにIC源泉はある
- **軸D**: Boosted.ai "Mirror your thinking" 思想（180+ AM 利用）はツール提供にとどまる → ファンド組成として実装する Y × MAS が空白

---

## 3. LP訴求の論証体系（5本柱）

| 柱 | 主張 | 根拠軸 | 決定的数字/論文 |
|---|------|:----:|---------------|
| **P1** | アクティブ運用の構造的劣勢は確定事項 | E | SPIVA US 2024: 15年全22カテゴリで過半数敗北、世界10ヶ国平均90%劣後 |
| **P2** | 純AIは負ける、Quantamentalは勝つ | E, D | AIEQ 設定来劣後、純AI型11本-1.8% vs Acadian 93-94% BM超過 |
| **P3** | 我々はYの暗黙知でIC高位維持 | F, B | Brynjolfsson QJE 2025、McLean-Pontiff 公開後35%減衰 → 未公表IC優位 |
| **P4** | MASでBreadth_effを拡大、上限 μ_IC/σ_IC に接近 | C, A, B | Yang et al. effective channel、Buckle effective breadth、Ding-Martin redux |
| **P5** | 国内シード期に絶好の制度追い風 | G | AOP補充原則3-4（142機関受入）+ 金商法改正（資本金1000万円・外注可） |

---

## 4. 想定批判への準備（軸G の B1-B12 を抜粋）

| 批判 | 反論材料 |
|---|---|
| 「シード期で実績がない」 | AOP補充原則3-4「業歴で排除しない」、ピッチ30分構成にPoC実証データ枠 |
| 「AIブラックボックス」 | 軸C: Miyazaki fine-grained task decomposition → 説明可能性を構造で担保 |
| 「過学習・データマイニング」 | 軸B: McLean-Pontiff 公開後35%減衰 → 未公表IC優位、軸F: Y暗黙知は固有 |
| 「キャパシティ問題」 | 軸B: Buckle Effective Breadth 上限を明示認識、capacity を IR と切り離して訴求 |
| 「Y属人化リスク」 | 軸F: 暗黙知のAI移植可能性（Brynjolfsson, Kim/Muhn）+ MAS で複数AN対応 |
| 「Boosted.ai と何が違う」 | 軸D: ツール提供 vs ファンド組成、Y固有判断パスカタログ（軸C: Miyazaki が学術支持） |
| 「DE Shaw Cogence と何が違う」 | 軸D: 巨人クオンツのディスクレショナリー回帰は方向性肯定、規模・国内特化で差別化 |

---

## 5. リサーチギャップと次の調査推奨

### 残る論証上の弱点

| 弱点 | 軸 | 必要なエビデンス |
|---|:---:|---------------|
| Y個人のIC直接測定 | F | アナリストYのフィードバックデータからIC推定（既存 KY 12ルール体系を IC 算出ベースに変換） |
| Y×MAS固有のσ(IC)削減効果 | B | MAS構成の独立性指標と σ(IC) 関係性の実証（自社PoCデータで検証） |
| Schmidt et al. 2019 出典 | A | Buckle 2014 / Boyd 2017 / Gârleanu-Pedersen 2013 が代替候補、特定要 |
| Grinold 1989 原典 + Grinold-Kahn 2000 Ch.6 Appendix 6A | A | 物理書籍経由で精読必要 |
| Capital Group Multiple Manager System との差別化 | D | 同社の最新公開情報深掘り |
| Bridgewater AIA Labs の詳細 | D | 公開情報不足、業界専門レポート要 |

### 軸の更新優先度

1. **軸G ピッチ資料骨子案の活用** — 即着手可能、AOP補充原則3-4 を訴求軸に
2. **軸D/E の合体ピッチ図** — IC-BR散布図 + 業界IR数字テーブル → 1スライド化
3. **軸F のY暗黙知を IC スコア化** — 既存KY 12ルール体系を IC 算出フレームに変換
4. **軸C のMAS実装設計** — Yang et al. effective channel + Miyazaki task decomp を実装に落とす
5. **軸B/Aの数理深掘り** — Ding-Martin Redux を社内技術メモ化、ファンドオファリングメモのテクニカル付録に

---

## 6. ファイル一覧

| 軸 | ファイル | 文字数(概算) |
|---|---------|:----:|
| 統合 | `2026-05-11_axes-integration-summary.md`（本ファイル）| 〜5,000 |
| A | `2026-05-11_axis-A_fundamental-law-theory.md` | 〜7,300 |
| B | `2026-05-11_axis-B_ic-breadth-empirical.md` | 〜19,300 |
| C | `2026-05-11_axis-C_multi-agent-breadth.md` | 〜8,200 |
| D | `2026-05-11_axis-D_competitive-landscape.md` | 〜24,400 |
| E | `2026-05-11_axis-E_industry-ir-evidence.md` | 〜10,000 |
| F | `2026-05-11_axis-F_tacit-knowledge-reframing.md` | 〜7,500 |
| G | `2026-05-11_axis-G_jp-institutional-ir-criteria.md` | 〜16,000 |
| **総計** | | **〜97,700** |

---

## 7. Neo4j 保存状況

- Discussion: `disc-2026-05-11-fund-research-restructure`
- Decision: `dec-2026-05-11-001` (Fundamental Law 採用), `dec-2026-05-11-002` (三核心構造)
- ActionItem: `act-2026-05-11-006` 〜 `act-2026-05-11-012`（7軸、全 status: pending → completed 要更新）
- 議論メモ: `docs/plan/2026-05-11_discussion-fund-research-restructure.md`

### 次のNeo4j更新候補
- ActionItem 006-012 を `status: completed` に更新
- 各軸の主要論文を Source ノードとして登録（軸ごとに上位5-10論文）
- 「IC-BR 散布図右上空白」「AIEQ vs Acadian分離」「AOP補充原則3-4」等の発見を Claim ノードとして登録

---

## 8. 次の議論候補トピック

1. **ピッチ資料スケルトン作成** — 軸G の 11.1-11.4 をベースに、軸D/Eの数字、軸A/B/C/Fの理論で肉付け
2. **Y暗黙知のIC化** — 既存 KY 12ルール体系（`analyst/memo/phase0_philosophy_injection_design.md`）を IC 算出可能なフレームに変換
3. **MAS実装設計レビュー** — 軸C の Yang/Miyazaki 知見を既存 MAS ファンド運用システム設計に取り込み
4. **PoC 検証計画** — 軸B/F の理論的主張を自社PoCデータで実証する設計
5. **競合ベンチマーク選定** — 軸D/E からベンチマーク候補（Acadian Global Equity, AQR QMNIX 等）を絞り込み

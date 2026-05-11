# 軸A: Fundamental Law of Active Management — 理論的バックボーン

**作成日**: 2026-05-11
**目的**: ファンドコンセプトの理論的基礎を文献調査し、IR = IC × √BR の系譜と現代的拡張を整理
**位置付け**: 三核心1 — Fundamental Law 三本柱の第1柱
**重複回避**: 本メモは "理論" を扱う。AI による Augmentation 側の証拠は `analyst/memo/2026-05-06_AI_augmentation_research_for_fund_concept.md` を参照

---

## 0. エグゼクティブサマリ

| # | 文献 | 主張（一言） | 本ファンドへの含意 | 確信度 |
|---|------|-------------|--------------------|--------|
| 1 | Grinold (1989), Grinold & Kahn (2000) | **IR = IC × √BR**。スキル × 機会数の平方根で運用価値を分解 | ファンドのスコアカードは IC・BR・TC の三軸で説明する | 強い |
| 2 | Clarke, de Silva, Thorley (2002) | 制約下では **IR = TC × IC × √BR**。long-only 制約だけで TC ≈ 0.6 → IR が 40% 削がれる | Y×MAS は long-only でも、シグナル→ポジションの忠実度 (TC) を最大化する設計が支柱 | 強い |
| 3 | Qian & Hua (2004), Ye (2008) | IC は時変。真の IR ≈ **mean(IC) / std(IC)** — Strategy Risk の存在 | 平均 IC だけでなく IC ボラの抑制が支配的 → アンサンブル / Y のレジーム判定で std(IC) を縮減 | 中〜強 |
| 4 | Buckle (2004; 2014 working paper) | Generalised FLAM。資産間相関・予測相関を陽に扱う。**「専門家を独立に並べた方が、相関を考慮する単一マネージャより IR が高い」** | Y のマルチエージェント分業（事業 / バリュエーション / マクロ……）の理論根拠 | 強い |
| 5 | Sneddon (2020) | Buckle を実証で追認。**「return correlation が高いほどアグレッシブに動け」「forecast correlation も IR を高める」** — 直観に反する設計含意 | レジーム集中（マクロ衝撃）局面ほど判断の集約が効く | 中 |
| 6 | Ding & Martin (2017) "Redux" | classical FLAM は条件付き・無条件分散の混在で誤定式化。新 FLAM は IC_t の分散を陽に組み込み、**N→∞ で IR は有限の上界に収束**（"無限ブレッドス幻想" の否定） | BR を無限に拡大すれば IR が無限に伸びるという naïve 解釈を捨てる。"質×戦略リスク" がボトルネック | 中〜強 |
| 7 | McLean & Pontiff (2016) | アノマリーは論文公開後に約 **32-35% 減衰**。IC は時間と共に消耗する公共財 | 公開された IC ソース（ファクター）への依存はキャパ・劣化リスク。**未公表の暗黙知（Y）由来の IC** に優位性 | 強い |
| 8 | Coqueret & Guida (2020/2023) "ML for Factor Investing" | ML は IC を線形相関から非線形・条件付きへ拡張。**Information Horizon** とラベル設計が新たな自由度 | LLM/ML を組み合わせれば IC の "非線形成分" を取り出せる — 古典 FLAM の "線形 IC" 想定を超える | 中 |

**核心メッセージ**: IR = IC × √BR は強固だが「測れていないところに勝機がある」。本ファンドは①TC（暗黙知→ポジション忠実度）、②mean(IC)/std(IC) の安定化、③公開ファクターに依存しない IC ソース（Y の暗黙知＋LLM 抽出）の三点で従来クオンツを上回る設計が可能。

---

## 1. 起源: Grinold (1989) と Grinold & Kahn (2000)

### 1.1 Grinold (1989) — 起源論文

- **書誌**: Grinold, R. C. (1989). "The Fundamental Law of Active Management." *Journal of Portfolio Management*, 15(3), Spring, pp. 30–37.
- **DOI / URL**: 出版元ペイウォール。URL は https://www.pm-research.com/content/iijpormgmt/15/3/30（CFA Institute / PMR 経由、要購読）
- **主張（導出）**:
  - 二次効用最大化のもとで、未制約最適アクティブポートフォリオの情報比 (IR) は
    $$IR^{*} = IC \cdot \sqrt{BR}$$
  - IC（Information Coefficient）= 予測 αと実現リターンのクロスセクション相関（スキル）
  - BR（Breadth）= 年間の独立予測機会数
  - 期待付加価値（リスク調整後）: $E(R_A)^{*} = IC \cdot \sqrt{BR} \cdot \sigma_A$
- **想定**:
  - 全予測の IC が等しい（identical IC）
  - 全予測が独立（independent）
  - 取引コストなし、制約なし
  - リターンと予測が結合正規分布
- **限界**:
  - "独立"の定義が運用上曖昧（年率化の根拠が脆い）
  - IC が時変であることを扱わない（後に Qian-Hua, Ye, Ding-Martin が指摘）
  - 取引コスト・キャパシティを無視
- **本ファンドへの含意**:
  - **スコアカードの3軸**：人間 Y の判断と AI のマルチエージェントが、(a) IC（質）、(b) BR（数）、後述の (c) TC（実装）を同時に押し上げる設計が可能
  - スキルと機会数は **掛け算ではなく IC × √BR** — IC を2倍にする方が、機会を4倍にするのと同等。よって "Y の判断品質" を増幅させる方が筋がよい

### 1.2 Grinold & Kahn (2000) — 教科書化

- **書誌**: Grinold, R. C., & Kahn, R. N. (2000). *Active Portfolio Management: A Quantitative Approach for Producing Superior Returns and Controlling Risk* (2nd ed.). New York: McGraw-Hill.
- **ISBN**: 0-07-024882-6
- **重要章**:
  - **Ch. 4 "The Fundamental Law of Active Management"** — FLAM の直観
  - **Ch. 6 "Information Analysis"** — IC 推定の実務、Appendix 6A に FLAM の正式導出
  - **Ch. 5 "Residual Risk and Return: The Information Ratio"** — IR の定義と "good IR" 基準（IR=0.5 = "good"、0.75 = "very good"、1.0 = "exceptional"）
- **追加された含意**:
  - "Alpha is Volatility × IC × Score" (Grinold 1994) を介して、α 推定値 = $\sigma \cdot IC \cdot z$ の分解が確立される
- **論争点**:
  - Appendix 6A の (6A.20) 式 "$\zeta_b^2 = \rho^2 = IC^2$" の導出が不明瞭との指摘あり（Quantitative Finance Stack Exchange [Q&A](https://quant.stackexchange.com/questions/73655) — Ding-Martin が後に "the Grinold-Kahn fundamental law is basically flawed" と踏み込む（後述 §6）
- **本ファンドへの含意**:
  - 教科書水準の "IR=1.0 = 例外的" を、現代のファンドで本気で狙うなら、IC の質と BR の数を**同時に**設計工学として上げる必要 — 個人の判断だけ・モデルだけでは到達困難。**Centaur 型運用 (Y × MAS) の必然性**

---

## 2. Transfer Coefficient 拡張: Clarke, de Silva, Thorley (2002, 2006)

### 2.1 Clarke, de Silva, Thorley (2002) — Transfer Coefficient の導入

- **書誌**: Clarke, R., de Silva, H., & Thorley, S. (2002). "Portfolio Constraints and the Fundamental Law of Active Management." *Financial Analysts Journal*, 58(5), September/October, pp. 48–66.
- **URL（要約・著者ページ）**: https://www.tandfonline.com/doi/abs/10.2469/faj.v58.n5.2468 ／ https://rpc.cfainstitute.org/research/financial-analysts-journal/2002/portfolio-constraints-and-the-fundamental-law-of-active-management
- **受賞**: Graham and Dodd Award of Excellence (2002)
- **主張（拡張式）**:
  $$IR = TC \cdot IC \cdot \sqrt{BR}$$
  - TC（Transfer Coefficient）= 制約下のアクティブウェイトと無制約最適アクティブウェイトの相関 ∈ [0, 1]
- **重要な定量結果**:
  - **典型的な long-only equity ポートフォリオでは TC ≈ 0.6** → 予想 IR が **40% 削減**される
  - 制約には：no short sales、turnover、market-cap / value-growth neutrality、sector constraint など
  - 興味深い知見: long-only 下では **active risk (TE) を上げるほど TC が下がる** — long-only 制約が銘柄を多く binding し、より多くのシグナルが反映できなくなるため
- **ex-post 分解**:
  - 実現アクティブリターン = E[α | IC_realized] + Noise（制約由来）
  - TC=1.0 の無制約ポートフォリオでは、ex-post 分散はすべて IC の実現値で説明可能
- **本ファンドへの含意**:
  - **TC は "暗黙知→ポジション" の忠実度メーター**。Y の判断や MAS のアウトプットを portfolio construction で歪めず実装できるか
  - long-only であってもユニバースを広げ（small/mid cap を含む）、TC を最大化することで Y の IC を活かせる
  - **訴求ポイント**: "我々の IC は Y の暗黙知由来で他社模倣困難。さらに TC を上げる実装設計（low-turnover, smart constraint design）も含めて IR を上乗せ"

### 2.2 Clarke, de Silva, Thorley (2005, 2006) — 拡張・パフォーマンス帰属

- **書誌**:
  - Clarke, R., de Silva, H., & Thorley, S. (2005). "Performance Attribution and the Fundamental Law." *Financial Analysts Journal*, 61(5), pp. 70–83. ← Graham & Dodd Scroll Award
    - URL: https://www.jstor.org/stable/4480702
  - Clarke, R., de Silva, H., & Thorley, S. (2006). "The Fundamental Law of Active Management." *Journal of Investment Management*, 4(3), pp. 54–72.
- **追加貢献**: FLAM パラメータを **factor-based regression attribution** に落とし込み、運用パフォーマンスを IC × TC × BR の枠で診断可能に
- **本ファンドへの含意**: LP 向け月次/四半期レポートで、IR を IC・TC・BR・Noise に分解した attribution を提供できれば**説明責任の差別化**になる

### 2.3 日本での実証 — Sodeyama & Yano (Sumitomo Trust)

- **書誌**: 袖山祐治 & 矢野邦昭, "Active Management and Portfolio Constraints"（証券アナリストジャーナル賞論文の英訳版）
- **URL**: https://www.saa.or.jp/english/professional/pdf/sodeyamayano.pdf ／日本語版 https://www.saa.or.jp/journal/prize/pdf/sodeyamayano.pdf
- **主張**: 日本株 (TOPIX 等) で non-negative 制約 (long-only) を課すと TC が低下、特に **目標アクティブリターン t=5.0% でも TC ≈ 0.800**（無制約比で **約 13% の構築能力低下**）
- **本ファンドへの含意**: 国内市場では小型株を含めユニバースを広げて TC を上げる戦術が機能する余地（特に Y のカバレッジ＝中小型・テーマ株なら有利）

---

## 3. 実装上の課題: Buckle (2004, 2014) と Sneddon (2020)

### 3.1 Buckle (2004) — Generalised FLAM

- **書誌**: Buckle, D. (2004). "How to Calculate Breadth: An Evolution of the Fundamental Law of Active Portfolio Management." *Journal of Asset Management*, 4(6), pp. 393–405.
  - DOI: 10.1057/palgrave.jam.2240117
- **続編 (working paper, 2014)**: Buckle, D. "Modern Portfolio Theory: Should Active Managers Be Using It?"（Cambridge CFR で講演）
  - URL: https://www.statslab.cam.ac.uk/~mrt31/CFR/events/content/20023/Modern_Active_Portfolio_Theory_-_David_J_Buckle.pdf
- **主張（数式）**: Buckle は資産間相関 (W) を陽に組み込み、平均/分散最適アクティブポジションの IR を
  $$IR = \frac{\mathrm{tr}(W^{-1})}{\left[\mathrm{tr}(W^{-1} W^{-1}) + \mathrm{tr}((W^{-1})^2)\right]^{1/2}}$$
  と一般化（"Generalised Fundamental Law of Active Management"）。Grinold-Kahn の独立同分布 IC 仮定は特殊ケース
- **驚きの含意**:
  - **「相関のある資産には、独立な専門マネージャを並列に並べた方が IR が高い」**：Buckle は "the use of independent active manager specialists is better than one general active manager who can account for asset correlations" と明言
  - **「定額サイズ（constant size）のアクティブポジションは、mean-variance 最適より IR が高い場合がある」**：ナイーブな MPT 最適化は IR 最大化しない（最大化するのは別の関数）
  - **多期間問題**：「各期に FLAM を適用しても多期間 IR は最大化されない。別の運用アプローチが必要」
- **本ファンドへの含意**:
  - **マルチエージェント分業の理論的正当化**：MAS（事業エージェント / 競争優位エージェント / マクロエージェント……）を独立に走らせ、最後に statistical aggregation する設計 ＞ 単一巨大モデル
  - **multi-period 設計**：単期 IR 最大化のリバランスは中期 IR を最大化しない → 中期 horizon を意識したリバランス間隔と turnover 設計

### 3.2 Ye (2008) — Signal Quality の変動

- **書誌**: Ye, J. (2008). "How Variation in Signal Quality Affects Performance." *Financial Analysts Journal*, 64(4), July/August, pp. 48–61.
  - URL: https://www.tandfonline.com/doi/abs/10.2469/faj.v64.n4.5
- **主張**: 「IC が時変であることはアクティブリスクに新たな成分を加える」。古典 FLAM は IC を定数扱いし、結果として IR を過大評価する
- **重要な貢献**: signal quality（IC）の時系列分散は **strategy risk** として真のアクティブリスクに上乗せされる（Qian-Hua 2004 を継承）
- **本ファンドへの含意**: Y の判断・MAS の出力に対し、レジーム別 IC 推定と分散の縮減（アンサンブル、stop-loss-by-regime）を組み込むべき

### 3.3 Qian & Hua (2004) — Active Risk and Information Ratio

- **書誌**: Qian, E., & Hua, R. (2004). "Active Risk and Information Ratio." *Journal of Investment Management*, 2(3), pp. 20–34.
  - URL: https://www.panagora.com/assets/JOIM-Active-Risk-and-Information-Ratio.pdf
- **核心式**: $\displaystyle IR = \frac{\mathrm{mean}(IC)}{\mathrm{std}(IC)}$ ← FLAM とは独立に、IR を IC の **mean/std** として直接表現
  - "IR measures the ratio of average excess return to the standard deviation of excess return, if IC were the sole determinant of excess return, then IR would be the ratio of average IC to the standard deviation of IC"
- **主張**: tracking error model の TE は **strategy risk**（IC の時変）を見落としており、真のアクティブリスクは大きい
- **本ファンドへの含意**:
  - LP 向け IR 予想値はナイーブな IC×√BR ではなく、**mean(IC)/std(IC) ベースのコンサバ推定**で示せば説明力が高い
  - Y の暗黙知が "std(IC) を下げる"（判断の安定性）を主張できれば、IR は単純な IC アップ以上にレバレッジが効く

### 3.4 Sneddon (2020) — Fallacies of Breadth

- **書誌**: Sneddon, L. (2020). "Strategy Design and the Fallacies of Breadth." *Journal of Asset Management*, 21(7), December, pp. 626–635.
  - DOI: 10.1057/s41260-020-00193-y
- **主張（直観に反する3つの結論）**:
  1. リターン相関が高い局面ほど、**アクティブマネージャはアグレッシブに動くべき**（Buckle に合致）
  2. 予測の相関 (forecast correlation) が高いほど **IR は向上する** — "正しい予測が複数モデルで一致" は強気サイン
  3. 単純な "BR を増やす" 戦略は performance を改善しない場合がある — *correlations matter more than count*
- **本ファンドへの含意**:
  - 危機・レジーム転換時こそ Y × MAS のアグレッシブ運用が効く（Buffett の "Be greedy when others are fearful" の定量的根拠）
  - 複数エージェントの合意度（forecast correlation）を意思決定の確信度シグナルに使う設計が支持される

---

## 4. 多期間・動的拡張: Ding & Martin (2017) Redux と関連研究

### 4.1 Ding & Martin (2017) — "The Fundamental Law of Active Management: Redux"

- **書誌**: Ding, Z., & Martin, R. D. (2017). "The Fundamental Law of Active Management: Redux." *Journal of Empirical Finance*, 43, pp. 91–114.
  - URL: https://ideas.repec.org/a/eee/empfin/v43y2017icp91-114.html ／ https://www.sciencedirect.com/science/article/pii/S0927539817300592 (要購読)
- **主張**:
  - 古典 FLAM は条件付き分散 (conditional) と無条件分散 (unconditional) を混在させており、IR を過大評価する
  - cross-section factor model を出発点に再導出すると、最適 IR は
    - **mean(IC_t)** に正比例
    - **std(IC_t)** に反比例
    - 資産数 N に正比例（ただし N→∞ で**有限の上限に収束**）
  - "There is no such thing as breadth, period" — IC_mean / IC_stdev のみが本質
- **想定**:
  - 残差リターンの無条件平均 = 0、ファクターエクスポージャの平均 = 0、分散 = 1（標準化）
  - quadratic utility 最適化を用いるマネージャ
- **実証**: 著者らのファクターモデルは、業界標準ファクターモデルより**著しく高い IR** を実現
- **本ファンドへの含意**:
  - "BR を増やせば IR が無限に伸びる" という naïve サイズ訴求を採らない
  - **質 (IC mean) と安定性 (1/IC std) が本質** → Y の判断品質と MAS のロバスト性が支配的
  - LP 向けには「我々は **mean/std-of-IC** 基準で IR を構成」と説明できれば、定量的説得力が高まる

### 4.2 Ding, Martin, Yang (2020) — Time-Varying IC とターンオーバー

- **書誌**: Ding, Z., Martin, R. D., & Yang, C. (2020). "Portfolio Turnover when IC is Time-Varying." *Journal of Asset Management*, 21, pp. 609–622.
  - DOI: 10.1057/s41260-020-00188-9 (近接) ／ https://www.researchgate.net/publication/338954198
- **主張**: stock-specific risk (ε)、factor risk (W)、strategy risk (IC std) の3層分解。ターンオーバーは IC の時変構造で大きく変動
- **本ファンドへの含意**: 月次リバランスの最適性は IC の自己相関に依存。Y の見通しが長期 (12ヶ月+) なら turnover を抑え、TC を最大化する設計が合理

### 4.3 多期間拡張に関する注意

> **重要な訂正**: 軸 A の指示にあった "Schmidt et al. (2019) Multi-period extensions of the Fundamental Law" について、Tavily / arXiv で網羅検索を行ったが**該当論文を特定できなかった**。

近接する多期間拡張は以下のいずれかが想定されていた可能性が高い:

- **Buckle (2014) の Section 3**: "applying [FLAM] to each period of the multi-period problem does not maximise information ratio" と明示
- **Boyd et al. (2017) "Multi-Period Trading via Convex Optimization"**: Stanford / Convex 多期間最適化、IR を含む。URL: https://web.stanford.edu/~boyd/papers/pdf/cvx_portfolio.pdf
- **Gârleanu & Pedersen (2013) "Dynamic Trading with Predictable Returns and Transaction Costs"**: *Journal of Finance* 68(6), 2309–2340 — 動的 αとコストの最適 trade-off
- **Cochrane** の "Portfolios for Long-Term Investors"（夢のような未公刊 review）: 動的ポートフォリオ理論を payoff stream で再定式化

**確信度**: 中（指示の "Schmidt et al. 2019" は出典未確認のため、軸 A 完成稿では出典のはっきりした Buckle 2014 / Gârleanu-Pedersen / Ding-Martin 系列を主軸にすべき）

### 4.4 IC 自体の劣化: McLean & Pontiff (2016)

- **書誌**: McLean, R. D., & Pontiff, J. (2016). "Does Academic Research Destroy Stock Return Predictability?" *Journal of Finance*, 71(1), pp. 5–32.
  - DOI: 10.1111/jofi.12365
  - URL: https://www.hec.ca/finance/Fichier/McLean.pdf (preprint)
- **主張**: 97 のクロスセクション予測指標のうち、**論文公開後にリターンが平均 32–35% 減衰**。アノマリーは消滅はしないが大幅劣化
- **本ファンドへの含意 — 本ファンドの最強の理論的訴求**:
  - "Y の暗黙知" は **公開されていない IC ソース** → ファクターのクラウディング・劣化リスクから免れる
  - 公開ファクター (Value, Momentum, Quality...) を機械的に積むだけのクオンツは IC が経年劣化する
  - LLM/MAS による Y の暗黙知抽出は、**新しい IC ソースを継続的に生成する仕組み** — McLean-Pontiff の枠組みで論理的優位

---

## 5. ML 時代の再解釈: Coqueret & Guida (2020, 2023)

### 5.1 書誌

- **R Version**: Coqueret, G., & Guida, T. (2020). *Machine Learning for Factor Investing: R Version*. Chapman and Hall / CRC. ISBN 9781003034858 (eBook). 342 pages.
- **Python Version**: Coqueret, G., & Guida, T. (2023). *Machine Learning for Factor Investing: Python Version*. CRC Press. ISBN 9780367639747.
- **オンライン無料版**: https://www.mlfactor.com/ ／ サンプルデータ https://github.com/shokru/mlfactor.github.io

### 5.2 主要章と FLAM 関連トピック

| 章 | 主題 | FLAM への含意 |
|---|------|---------------|
| Ch. 3 | Factor investing and asset pricing anomalies | 古典 IC の経済的根拠 |
| Ch. 4 | Data preprocessing | IC を強化する label engineering（極値ラベルが情報を持つ） |
| Ch. 5–9 | Penalized regression, Tree, NN, SVM, Bayesian | IC の **非線形成分** を抽出する手段 |
| Ch. 10 | Validating and tuning | out-of-sample IC の robust 推定 |
| Ch. 11 | Ensemble | Strategy risk (std IC) を下げるアプローチ |
| Ch. 12 | Portfolio backtesting | IC → portfolio へ落とす実務的注意（TC を上げる方法と等価） |

### 5.3 ML 時代の IC の再解釈

- **線形 IC の限界**: 古典 IC は Spearman / Pearson 相関 — 線形・単調関係のみ捕捉
- **ML による拡張**:
  - 木モデル・NN は非線形・条件付き関係を学習
  - "Predictability" は **特定のレジーム / セクター / horizon に局所化**されている（IC 自体が conditional 量）
  - Coqueret-Guida (2020) は extreme labels が情報を集中して持つことを実証 — IC は分布の尾で計測すべきという主張
- **本ファンドへの含意**:
  - Y の暗黙知は **conditional IC**（特定の状況でのみ高 IC）と整合 — ML との相性が良い
  - MAS の各エージェントは特定 conditional IC に特化させ、メタエージェントが組み合わせる設計が支持される
  - **古典 FLAM の "constant IC" 想定はもはや過小評価** — 非線形・条件付き IC を取り込めば実効 IR は上方修正される余地

---

## 6. ファンドコンセプトへの含意（統合）

### 6.1 三本柱の理論サポート

| 柱 | 根拠論文 | 主張 |
|----|---------|------|
| **IC を未公表ソースから持続供給** | McLean-Pontiff (2016), Coqueret-Guida (2020) | 公開ファクターは劣化する。Y の暗黙知 × LLM 抽出による未公表 IC が長期優位 |
| **TC を最大化する実装** | Clarke-de Silva-Thorley (2002, 2005), Sodeyama-Yano | long-only でも TC=1.0 に近づける smart constraint design で IR を 40% アップサイド |
| **BR の質を上げる（単純拡大ではなく相関込みで設計）** | Buckle (2004, 2014), Sneddon (2020), Ding-Martin (2017) | "独立な専門エージェントを並列" の MAS は単一巨大モデルより理論的に IR が高い |

### 6.2 Information Ratio の分解で見える優位

古典：$IR = IC \cdot \sqrt{BR}$
拡張：$IR \approx TC \cdot \frac{\mathrm{mean}(IC)}{\mathrm{std}(IC)} \cdot f(\text{correlations})$

**Y × MAS の各要素がどこを押し上げるか**:

| 要素 | Y の暗黙知 | MAS（マルチエージェント） | LLM 抽出 |
|------|-----------|--------------------------|---------|
| mean(IC) ↑ | ◎ (高品質判断) | ○ (専門化) | ○ (非線形 IC) |
| std(IC) ↓ | ○ (経験で安定) | ◎ (アンサンブル) | ○ (regime detection) |
| TC ↑ | △ | ◎ (機械的に最適化) | ○ |
| BR (effective) ↑ | △ | ◎ (24/7 並列) | ◎ (universe expansion) |

→ **三層が補完関係**にあり、単独ではどこか弱い軸を別の層が埋める。これが Centaur 型運用が古典クオンツ・古典ファンダの双方を上回る理論根拠

### 6.3 LP 訴求での使い方（理論面）

1. **冒頭スライド**: IR = IC × √BR を提示 → "業界の言語" を共有
2. **拡張式**: IR = TC × IC × √BR で説明責任の枠を設定
3. **差別化**: mean(IC)/std(IC) 表現で「我々の優位は std を下げるところにある」
4. **未公表 IC**: McLean-Pontiff を引用し "我々の IC は劣化しない理由" を説明
5. **MAS の必然**: Buckle/Sneddon を引用し "並列専門家設計" を理論的に正当化

---

## 7. 未調査・継続調査推奨

### 7.1 直接フォローアップすべき論文

- **Grinold (1989) PDF 全文** — 出典の正式入手（CFA Institute / PMR 課金）
- **Grinold & Kahn (2000) Ch. 4, 6, Appendix 6A** — 物理書籍からの精読
- **Clarke-de Silva-Thorley (2006)** "The Fundamental Law of Active Management" *JOIM* 4(3) — 2002 論文の完成版
- **Ding & Martin (2017)** 全文 — 数式の再検証
- **Schmidt et al. 2019 (?)**: 出典が確認できなかった。原典文献を再確認のうえ、該当論文を特定する必要あり

### 7.2 まだ調べられていない領域

- **Information Horizon と alpha decay**: Qian, Sorensen, Hua (2007) "Information Horizon, Portfolio Turnover, and Optimal Alpha Models" *JPM*
- **Hedge fund / multi-strategy 文脈での FLAM**: Hedge Fund Research 系資料
- **HFT / 高頻度の FLAM**: BR が極大化された世界での IR 上限（Renaissance Technologies の運用が示唆）
- **行動ファイナンス系**:
  - Kahneman, Sibony, Sunstein (2021) *Noise* — std(IC) との関連
  - Polanyi (1966) "The Tacit Dimension" — 暗黙知が IC ソースになりうる哲学的基礎
- **Treynor-Black (1973)** "How to Use Security Analysis to Improve Portfolio Selection" — FLAM の前史。本軸の冒頭ストーリーに使える
- **Sorensen, Hua, Qian, Schoen (2004)** "Multiple Alpha Sources and Active Management" *JPM* — MAS 設計の論理的源流の1つ

### 7.3 批判的視点

- **Black-Litterman vs FLAM**: ベイズ枠組みでの相補性
- **FLAM のキャパシティ問題**: BR を上げると一銘柄あたりの sizing が落ち、取引コスト・市場インパクトが効く。Kahn & Shaffer (2005) "The Surprisingly Small Impact of Asset Growth on Expected Alpha"
- **Sharpe (1991) "The Arithmetic of Active Management"** — アクティブ運用ゼロサム性の補強
- **Asness, Frazzini, Pedersen (2014, 2017)** "Fact, Fiction, and Factor Investing" — IC ソース論で AQR 系の対立論点を確認

---

## 8. 引用候補リスト（S / A / B 級）

### S級（必ず引用、原典）

| # | 文献 | URL/DOI | 確信度 |
|---|------|---------|--------|
| S1 | Grinold (1989) "The Fundamental Law of Active Management" *JPM* 15(3), 30–37 | https://www.pm-research.com/content/iijpormgmt/15/3/30（要購読） | 強い |
| S2 | Grinold & Kahn (2000) *Active Portfolio Management* 2nd ed., McGraw-Hill | ISBN 0-07-024882-6 | 強い |
| S3 | Clarke, de Silva, Thorley (2002) "Portfolio Constraints and the FLAM" *FAJ* 58(5), 48–66 | https://www.tandfonline.com/doi/abs/10.2469/faj.v58.n5.2468 | 強い |
| S4 | McLean & Pontiff (2016) "Does Academic Research Destroy Stock Return Predictability?" *JoF* 71(1), 5–32 | DOI: 10.1111/jofi.12365 / preprint: https://www.hec.ca/finance/Fichier/McLean.pdf | 強い |

### A級（理論深化 / 拡張、強く推奨）

| # | 文献 | URL/DOI | 確信度 |
|---|------|---------|--------|
| A1 | Qian & Hua (2004) "Active Risk and Information Ratio" *JOIM* 2(3), 20–34 | https://www.panagora.com/assets/JOIM-Active-Risk-and-Information-Ratio.pdf | 強い |
| A2 | Buckle (2004) "How to Calculate Breadth: An Evolution of the FLAM" *JoAM* 4(6), 393–405 | DOI: 10.1057/palgrave.jam.2240117 | 強い |
| A3 | Buckle (2014 WP) "Modern Portfolio Theory: Should Active Managers Be Using It?" | https://www.statslab.cam.ac.uk/~mrt31/CFR/events/content/20023/Modern_Active_Portfolio_Theory_-_David_J_Buckle.pdf | 中 |
| A4 | Ye (2008) "How Variation in Signal Quality Affects Performance" *FAJ* 64(4), 48–61 | https://www.tandfonline.com/doi/abs/10.2469/faj.v64.n4.5 | 強い |
| A5 | Ding & Martin (2017) "The FLAM: Redux" *J. Empirical Finance* 43, 91–114 | https://ideas.repec.org/a/eee/empfin/v43y2017icp91-114.html | 強い |
| A6 | Clarke, de Silva, Thorley (2005) "Performance Attribution and the Fundamental Law" *FAJ* 61(5), 70–83 | https://www.jstor.org/stable/4480702 | 中 |
| A7 | Clarke, de Silva, Thorley (2006) "The Fundamental Law of Active Management" *JOIM* 4(3), 54–72 | URL未確認（JOIM サイト） | 中 |
| A8 | Sneddon (2020) "Strategy Design and the Fallacies of Breadth" *JoAM* 21(7), 626–635 | DOI: 10.1057/s41260-020-00193-y | 中 |
| A9 | Coqueret & Guida (2020/2023) *Machine Learning for Factor Investing* Chapman & Hall | https://www.mlfactor.com/ (無料 online) ／ ISBN 9781003034858 | 強い |

### B級（補助・補強）

| # | 文献 | URL/DOI | 確信度 |
|---|------|---------|--------|
| B1 | Grinold (1994) "Alpha is Volatility Times IC Times Score" *JPM* 20(4), 9–16 | 出版元ペイウォール | 強い |
| B2 | Grinold & Kahn (1992) "Information Analysis" *JPM* 18(3), 14–21 | 出版元ペイウォール | 中 |
| B3 | Sorensen, Hua, Qian, Schoen (2004) "Multiple Alpha Sources and Active Management" *JPM* 30(2), 39–45 | 出版元ペイウォール | 中 |
| B4 | Ding, Martin, Yang (2020) "Portfolio Turnover when IC is Time-Varying" *JoAM* 21(7), 609–622 | DOI: 10.1057/s41260-020-00193-y 近接 | 中 |
| B5 | 袖山祐治・矢野邦昭 "Active Management and Portfolio Constraints"（証券アナリストジャーナル賞） | https://www.saa.or.jp/english/professional/pdf/sodeyamayano.pdf | 中 |
| B6 | Treynor & Black (1973) "How to Use Security Analysis to Improve Portfolio Selection" *J. Business* 46(1), 66–86 | 出版元ペイウォール | 強い |
| B7 | Sharpe (1991) "The Arithmetic of Active Management" *FAJ* 47(1), 7–9 | https://web.stanford.edu/~wfsharpe/art/active/active.htm | 強い |
| B8 | Kahneman, Sibony, Sunstein (2021) *Noise: A Flaw in Human Judgment* HarperCollins | ISBN 9780316451406 | 強い |
| B9 | Boyd et al. (2017) "Multi-Period Trading via Convex Optimization" *Foundations and Trends in Optimization* 3(1), 1–76 | https://web.stanford.edu/~boyd/papers/pdf/cvx_portfolio.pdf | 強い |
| B10 | Gârleanu & Pedersen (2013) "Dynamic Trading with Predictable Returns and Transaction Costs" *JoF* 68(6), 2309–2340 | DOI: 10.1111/jofi.12080 | 強い |

---

**作成完了**: 2026-05-11 / 軸 A 第1版

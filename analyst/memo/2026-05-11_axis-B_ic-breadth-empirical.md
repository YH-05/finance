# 軸B: IC × Breadth 同時最適化の経験的研究

**作成日**: 2026-05-11
**目的**: IR = IC × √BR の「同時押し上げ」主張に対する典型的批判への反論材料を整理
**位置付け**: 三核心1 — Fundamental Law 三本柱の第2柱（軸A=理論的基盤、軸C=実装制約・拡張）

---

## エグゼクティブサマリ

Grinold (1989) の Fundamental Law of Active Management (FLAM) は IR = IC × √BR という単純な分解を提示したが、その後 35 年の経験的研究は **「IC と BR は独立に押し上げられない」** という事実を一貫して確認している。主な発見:

1. **IC dilution (IC 希釈)**: 投資対象を機械的に拡大すると、限界銘柄の予測精度が低下し IC は単調に減衰する (Buckle 2004, Sneddon 2020)。
2. **Independent bets の幻想**: PCA で測定すると、S&P500 ですら有効次元は 5-10 程度、新興市場では 1-3 に過ぎず、「N=500」は実効的には大幅に過大計上 (Polakow & Gebbie 2008)。
3. **Effective Breadth (BR_eff)**: Buckle (2004) の半一般化公式 BR_eff = N / [1 + (N-1)ρ] により、相関 ρ=0.1 で N=500 が BR_eff ≈ 10 に縮退することが定量化された。
4. **Ding & Martin (2017) Redux**: 経験的に強い形は IR = μ_IC / σ_IC （IC の平均/標準偏差）であり、N に上限が存在する。**「ブレッドスを無制限に拡大すれば IR が無限に上がる」は誤り**。
5. **Active Share の論争**: Cremers & Petajisto (2009) は Active Share と超過リターンの正相関を示したが、Frazzini, Friedman, Pomorski (2016, AQR) はベンチマーク選択効果が支配的と反論。両者は両立しうる ("patient + high AS" → 持続的アウトパフォーム; Cremers & Pareek 2016)。
6. **Crowding と alpha decay**: McLean & Pontiff (2016) は公開アノマリーが平均 32-35% 減衰、Pastor-Stambaugh-Taylor (2015, 2021) は業界規模拡大とともに IR が低下する規模の不経済を頑健に確認。

**結論**: ファンドコンセプト「Y × MAS」が「IC × BR を同時押し上げ」と主張するには、(a) 「IC 源泉が他社と異なる暗黙知である」(crowding 回避)、(b) 「BR は機械的銘柄数ではなく独立判断パスの数」(effective breadth)、(c) 「σ_IC が小さい安定スキル」 (Ding-Martin Redux) の3点を実証する必要がある。本資料はその論拠材料を提供する。

---

## 1. IC 希釈問題 (IC dilution)

### 1.1 基礎概念

IC (Information Coefficient) は予測リターンと実現リターンの cross-sectional 相関であり、典型的に -0.05 〜 +0.15 の範囲をとる。**IC=0.05 以上が「強いシグナル」**、0.10 以上は overfitting の疑いとされる (fe.training 2026)。

### 1.2 BR 拡大に伴う IC 減衰の実証

- **Michaud & Michaud (2005)** "Equity Optimization Issues IV: The Fundamental Law of Mismanagement": Grinold 公式は情報の不確実性と実務制約を無視。BR を機械的に増やすと「情報の質」が低下し、最適化は質と量のトレードオフを考慮すべき。
- **Fulcrum Asset Management (2024)** "Don't Bet the Ranch: Hit Ratios, Asymmetry and Breadth": Hit ratio 55%, asymmetry 1.5 の仮定で、平均相関が **ρ=0.1 に上昇すると BR>15 の追加価値はほぼゼロ**、ρ=0.2 では BR>10 で価値消失。Extreme breadth 戦略は高レバレッジ・相関リスクで破綻リスクが高い。
- **Sneddon (2020)** "Strategy design and the fallacies of breadth" (Journal of Asset Management 21/7): リターン相関の負の影響を確認し、**ブレッドスを機械的に増やすことは IR を必ずしも改善しない**ことを定式化。

### 1.3 メカニズム

1. **限界銘柄効果**: アナリストカバレッジを 50 → 500 銘柄に拡大すると、深く理解できる銘柄数が制約されるため、限界銘柄の IC は低下。
2. **シグナル相関**: 同じファクター（PER、モメンタム等）でドライブされる銘柄群は、独立予測ではなく1つの予測の繰り返しに過ぎない。
3. **エラー相関**: 予測モデルが捉えきれない共通要因（マクロショック等）が銘柄間で誤差を相関させる。

### 1.4 回避策の文献

- **Heinrich, Shivarova, Zurek (2021)** "Factor investing: alpha concentration versus diversification" (J Asset Manag 22): Alpha-Concentration アプローチが情報含有量の高いファクターに傾斜することを示し、純粋な分散より優位。
- **Mickens (2026)** ブログ実証: concentrated long/short value/momentum はアルファを維持するが、profitability/investment ファクターでは消失。

**確信度**: 高 (複数論文で一致)

---

## 2. Independent bets の定義困難性

### 2.1 「N」の問題

Grinold 公式の N は「独立な予測の数」だが、実務で N を定義する標準的手法はない。**Stack Exchange (quant.stackexchange Q73655) で示された痛烈な批判**: 「Ding-Martin Redux を読めば、Grinold-Kahn の Fundamental Law は基本的に欠陥があると分かる。本当の公式は IR = IC_mean / IC_stdev であり、breadth は存在しない」。

### 2.2 ファクターによる「真の独立性」消失

- **InvestResolve (Tactical Alpha Pt.1)**: S&P 100 や S&P 500 を universe としても、PCA で第一主成分が分散の大部分を吸収し、有効ブレッドスは公称 N より遥かに小さい。Staub & Singer 系の手法で asset allocation 由来 vs security selection 由来のブレッドスを分解可能。
- **Polakow & Gebbie (2008)** "How many independent bets are there?" (J Asset Manag 9/4, arXiv:physics/0601166): SVD + Kaiser-Guttman 停止基準で南アフリカ市場の有効次元 (ED) を測定。**Top5銘柄ですら1次元、市場全体でも数次元に過ぎない**。新興市場の concentration リスクの実証的根拠。

### 2.3 Forecast/Error correlation の二重問題

- **Buckle (2004)** "How to calculate breadth: An evolution of the fundamental law of active portfolio management" (J Asset Manag 4/6, 393-405): 予測値の相関 ρ_f だけでなく、**予測誤差の相関 ρ_e も BR を侵食**することを定式化。実務では真の誤差相関を知り得ないため、簡略形を提案: BR_eff = function of (ρ_f, ρ_e, N)。
- **Chincarini & Kim (2007)** "Another look at the information ratio" (J Asset Manag 8/5): IC の定義そのものが Grinold-Kahn と Clarke-Buckle で異なることを指摘 — 1銘柄1IC か、1ファクター1IC か。**この定義差により BR の解釈が根本的に変わる**。

**確信度**: 高 (PCA・SVD ベースの実証は再現性が高い)

---

## 3. Effective Breadth (BR_eff)

### 3.1 Buckle (2004) の半一般化公式

Buckle は Grinold-Kahn の前提を緩めた "generalized fundamental law" を導出し、相関を考慮した実効ブレッドス:

```
BR_eff = N · (1 + Forecast_correlation · ρ_e) / [1 + (N-1) · ρ_e]
```

(ijbms.net 2021 の Risk-Adjusted Breadth in Active Portfolio Management で引用された Buckle 2004 p.399 の式)

**数値例** (Patev et al. 2021): Dispersion=0.15, Forecast correlation=0.10, Error correlation=0.02 のとき、N=500 でも実効ブレッドスは 50-100 程度。**N=500 の universe で IR √500 = IR × 22 倍を期待するのは誤り、実効的には √70 ≈ 8 倍程度**。

### 3.2 Effective Number of Bets (ENB) 系統

- **Meucci (2009)** "Managing Diversification" (Risk magazine): Principal portfolios のエントロピーを用いた ENB。最小ねじれ変換 (Minimum Torsion) を用いる Meucci, Santangelo & Deguest (2014) も実務で広く使用。
- **Portfolio Optimizer (2024)** 等の実装: ENB = exp(H(p̃)) where p̃ は principal component diversification distribution。

### 3.3 典型値

| Universe | 公称 N | 推定 BR_eff (PCA / Kaiser-Guttman) |
|----------|--------|-----------------------------------|
| S&P 500 | 500 | 5-15 (市場ベータが支配的) |
| 米国全銘柄 + ファクター慎重 | ~3000 | 30-50 |
| 南アフリカ Top40 | 40 | 1-3 (Polakow & Gebbie 2008) |
| グローバルマクロ (10資産) | 10 | 3-5 |

### 3.4 Strongin et al. (Goldman Sachs) 系

InvestResolve, Tom Capital, Northfield 等の機関の文献では、Strongin の「discretionary vs systematic」での breadth 差を引用。**Discretionary は breadth が低いが IC が高く、Systematic は逆**という構造的二項対立 (Tom Capital AG, Medium 2023)。

**確信度**: 中-高 (理論は確立、数値は universe 依存)

---

## 4. IC の時系列安定性とレジーム依存性

### 4.1 Qian & Hua (2004) の Strategy Risk

**Qian & Hua (2004)** "Active Risk and Information Ratio" (Journal of Investment Management 2/3): IC は時系列で変動し、**この変動 (σ_IC) は Tracking Error とは別の「Strategy Risk」を生む**。彼らの導いた形式:

```
IR = μ_IC / σ_IC
```

これは Grinold 公式と矛盾せず、N が十分大きいときの極限。実例: GP2EV ファクターで IC stdev = 2.7%, E2P で 3.4% → ex post TE はそれぞれ 6.9%, 8.7% (本来の risk model TE より大幅に高い)。

### 4.2 Ding & Martin (2017) の統合形式

**Ding & Martin (2017)** "The fundamental law of active management: Redux" (J Empirical Finance 43, 91-114): 完全な公式:

```
IR = μ_IC / √[σ_IC² + (1 - μ_IC² - σ_IC²)/N]
```

**N → ∞ で IR → μ_IC / σ_IC が absolute upper bound**。つまり**「ブレッドスをいくら拡大しても、IC の安定性が悪ければ IR は IC_mean/IC_stdev で頭打ち**」。

### 4.3 IC の時系列的不安定性の実証

- **Ding, Martin, Yang (2020)** "Portfolio Turnover when IC is Time Varying" (J Asset Manag 21): IC が時変であることを前提に最適 turnover を導出。
- **Ye (2008)** "How Variation in Signal Quality Affects Performance" (FAJ 64/4): シグナル品質の時系列変動が IR を侵食。
- **fe.training (2026) "Information Coefficient (IC)"**: 月次 IC の rolling 6-month 平均で見ると、レジーム転換期に大きく変動 (リーマンショック、コロナ等)。

### 4.4 レジーム依存性

- **Amundi Research Center**: 高ボラ期に資産間相関が上昇し、active management の potential IR は低下する。
- **Stock market correlations during 2008-2009** (Finance Research Letters): 50 株式市場でクライシス期に相関がジャンプ。**「ストレス期には effective breadth が崩壊する」**という観察。

**確信度**: 高 (Ding-Martin Redux は学術的定説化)

---

## 5. Active Share と Fundamental Law

### 5.1 Cremers & Petajisto (2009) の核心主張

**Cremers, K.J.M. & Petajisto, A. (2009)** "How Active Is Your Fund Manager? A New Measure That Predicts Performance" (Review of Financial Studies 22/9, 3329-3365):

- Active Share (AS) = 0.5 × Σ|w_fund - w_index|
- 米株式 MF (1980-2003) で AS 上位は benchmark を有意にアウトパフォーム (年率 +1.13〜+1.39%、費用控除後)
- AS と Tracking Error の 2×2 グリッドで、「高AS・低TE」(stock pickers) が最良、「低AS・高TE」 (factor bets) が最悪。

### 5.2 Petajisto (2013) 単独研究の追試

**Petajisto (2013)** "Active Share and Mutual Fund Performance" (FAJ 69/4): サンプル 1990-2009 で「最もアクティブな stock pickers が年率+1.26%、closet indexer/factor bets は劣後」。AS<60%のファンドは avoid 推奨。

### 5.3 AQR からの反論

**Frazzini, Friedman, Pomorski (2016)** "Deactivating Active Share" (FAJ 72/2, 14-21):

- AS と fund returns の関係は、**ベンチマーク選択効果が支配的**。同一ベンチマーク内で AS をソートしても、performance との相関は -0.75 (負相関!)。
- 「sorting funds on active share is equivalent to sorting on benchmark type」。
- AS は AQR から見ると **manager selection tool として無効**。

### 5.4 Cremers (2017) "AQR in Wonderland" 再反論

- 「AQR-WP の結論は典型的 academic standards で評価すべきではなく "Wonderland Genre"」と痛烈批判。
- **AQR の small cap fund 比率の説明は誇張** (small cap funds は 2000 年以降 24% 程度で安定; AS の variation は依然有意)。

### 5.5 Patient Capital との交互作用

**Cremers & Pareek (2016)** "Patient Capital Outperformance" (Journal of Financial Economics 122): **高AS かつ低 turnover (patient) の組み合わせ**でアウトパフォームが顕著。これは「真の stock pickers」を識別する条件。

### 5.6 FLAM への含意

Active Share は IR = IC × √BR の **TC (Transfer Coefficient) と関連**するが、AS だけでは IC や BR の質は分からない。AS は「ベンチマークから乖離する勇気」の代理変数だが、その乖離が正しい IC に基づくかは別問題。**Active Share 単独では fundamental law の代替にはならない**が、低 AS (closet indexer) は明らかに IR を諦めている。

**確信度**: 中 (Cremers vs AQR の論争は決着していないが、両者の主張は両立しうる)

---

## 6. Capacity と Crowding

### 6.1 McLean & Pontiff (2016) の post-publication decay

**McLean & Pontiff (2016)** "Does Academic Research Destroy Stock Return Predictability?" (Journal of Finance 71/1, 5-32):

- 82 アノマリーを調査。**平均 35% の post-publication decay** (in-sample alpha 5% → post-publication 3.25%)。
- Out-of-sample で 26%、publication 後で +9% 追加減衰。Lower bound estimate of publication effect = 25%。
- Trading activity (turnover, dollar volume, short interest) が post-publication に増加 → 套利者が殺到する証拠。
- **idiosyncratic risk が高いアノマリー (套利コスト高) は decay が小さい** → mispricing 説と整合。

### 6.2 Pastor-Stambaugh-Taylor (2015, 2021) の規模の不経済

- **PST (2015)** "Scale and Skill in Active Management" (JFE 116): **業界規模拡大に伴い、ファンドの IR が低下**。fund-level diseconomies of scale。
- **PST + Zhu (2021)** "Diseconomies of Scale in Active Management: Robust Evidence" (Critical Finance Review 11): robust regression でも結論不変。データエラー、ベンチマーク選択を変えても結果は維持。
- **示唆**: アクティブ運用業界全体の AUM が拡大すると、平均的なファンドのアルファ生成能力は構造的に低下。「自分が儲かるなら他人も気づく」効果。

### 6.3 Factor Crowding の実証

- **arXiv 2512.11913 (2025)** "Not All Factors Crowd Equally": 8つの Fama-French ファクター (1963-2024) で:
  - Momentum は **hyperbolic decay α(t) = K/(1+λt)** に fit (R²=0.65)、linear/exponential を上回る。
  - Mechanical factors (momentum, reversal) は crowd しやすい; judgment-based (value, quality) は crowd しにくい (Hua-Sun の「signal ambiguity barrier」と整合)。
  - 2015 以降 crowding が加速。
- **Kang, Rouwenhorst, Tang (2021)** "Crowding and Factor Returns" (Alpha Architect 引用): 商品先物市場で carry/momentum/value の crowding を CFTC データから測定。**crowded factor は subsequent drawdown が深い**。
- **Cho (2020)** "Turning alphas into betas" (JFE): 套利活動が alpha を beta に変換する。crowded アセットは discount-rate ベータが上昇し、capital shock に脆弱。

### 6.4 Capacity 推定の文献

- **Kahn & Shaffer (2005)** "The Surprisingly Small Impact of Asset Growth on Expected Alpha" (JPM 32/1): 楽観的見解—規模拡大の影響は驚くほど小さい (Pastor 系と対立)。
- **Novy-Marx & Velikov (2015)** "A taxonomy of anomalies and their trading costs": 多くのアノマリーは trading cost 控除後にネット alpha が消失。
- **Frazzini, Israel, Moskowitz (2014)** "Trading Costs of Asset Pricing Anomalies": AQR 実取引データで、規模拡大時の trading cost を推定。

**確信度**: 高 (Pastor-Stambaugh-Taylor は方法論的論争を経て頑健性を確立)

---

## 7. ファンドコンセプトへの含意

### 7.1 「Y × MAS」モデルが押し上げる軸

| FLAM 要素 | Y単独 | MAS単独 | Y×MAS |
|-----------|-------|---------|-------|
| **IC** | 高 (深い暗黙知) | 中 (体系的) | **高 (Y の IC を MAS が安定化)** |
| **BR** | 低 (300-400銘柄) | 高 (機械的拡張可能) | **中-高 (実効的に独立な判断パス)** |
| **σ_IC** | 中 (人間の調子) | 低 (ルール化) | **低 (MAS が IC stability を担保)** |
| **TC** | 中 (制約あり) | 高 (執行効率) | **高** |
| **Crowding 耐性** | 高 (公開されない判断) | 低 (公開シグナル) | **高 (Y の暗黙知が moat)** |

### 7.2 典型的批判への反論材料

**批判A: 「BR を増やせば IC が希釈される」 (Buckle, Sneddon)**
→ 反論: Y の暗黙知を MAS で **「異なる判断パス」として展開**することで、機械的銘柄拡大ではなく**実効ブレッドス (BR_eff) を増やす**。判断パス間の相関 (ρ_e) は Y の "judgment heterogeneity" により低く保たれる。

**批判B: 「Independent bets は PCA で見れば数次元しかない」 (Polakow-Gebbie)**
→ 反論: ファクター・銘柄レベルの相関とは別に、**「判断軸」レベルでの独立性**を測定すべき。アナリスト Y が CA (競争優位)、財務、マネジメント、マクロ感応度を独立軸で評価していれば、判断パス数は universe ベースの ED より大きい。

**批判C: 「IR = μ_IC/σ_IC が absolute upper bound」 (Ding-Martin)**
→ 反論: MAS が Y の判断を **「人間の調子の悪さ」から保護**することで σ_IC を引き下げる。具体的には:
- MAS による「忘却防止」(過去の判断軸の一貫性)
- MAS による「感情バイアス検知」(下げ相場でのパニック売り抑制)
- これにより μ_IC を維持しつつ σ_IC を下げる → upper bound 自体を引き上げる

**批判D: 「Active Share だけでは無意味」 (Frazzini-AQR)**
→ 反論: Y × MAS は単純な high-AS ではなく、**"high AS + patient + 一貫した IC 源泉"** (Cremers-Pareek 2016 の patient capital と整合)。

**批判E: 「Crowding でアルファは消える」 (McLean-Pontiff, factor crowding)**
→ 反論: Y の暗黙知は **「公開シグナルではない」** ため McLean-Pontiff の 35% decay は適用されない。MAS は公開ファクターの組み合わせではなく、Y 固有のパターン認識を学習・展開するため、模倣困難。

### 7.3 必要な実証

LP 訴求のためには以下の実証データが必要:

1. **Y 単独の歴史的 IC 分布**: μ_IC, σ_IC の推定 (4年分のトラックレコードから)
2. **判断パスの独立性測定**: Y の判断を CA/財務/マネジメント等の軸で分解し、軸間の predictive相関を ρ_e として推定
3. **MAS 介入の effect size**: σ_IC を実際にどれだけ下げるか (シミュレーション or 過去判断のリプレイ)
4. **Capacity 上限の試算**: Y のカバレッジ拡大時の限界 IC 減衰曲線

---

## 8. 未調査・継続調査推奨

### 8.1 直接的に深掘りすべき論文

- **Sneddon (2020)** 本文 (現状アクセスできず要約のみ確認) — fallacies of breadth の具体的反例
- **Ding, Martin, Yang (2020)** "Portfolio Turnover when IC is Time Varying" — 時変 IC 下での最適 turnover
- **Buckle (2003, 2004)** 本文 — generalized FLAM の数式詳細
- **Cremers (2017)** "AQR in Wonderland" 全文 — Active Share 論争の最新版
- **Zurek & Heinrich (2021)** "Bottom-up versus top-down factor investing" — alpha 予測精度の階層構造

### 8.2 関連分野で未カバー

- **Berk & Green (2004)** の equilibrium モデル — 「投資家が学習する」前提での scale & alpha
- **AQR Patient Capital シリーズ** (Cremers & Pareek 2016 系) — patient vs impatient の境界条件
- **Behavioral biases と IC σ** — Kahneman-Tversky 系のバイアスが σ_IC をどう増幅するか
- **AI/ML による IC stability の改善** — 2020 年代のクオンツファンドが ML で σ_IC を下げた実証 (Kaniel et al. 2023, JFE 150)
- **Multi-agent system と効率的アンサンブル** — MAS 文献からの「判断の独立性最大化」設計原則

### 8.3 Y×MAS 固有のオープン質問

1. アナリストの暗黙知を MAS が「忠実に展開」する精度はどれだけか? (HF Phase 0 で議論済の "philosophy injection" 課題)
2. MAS の判断パス間の真の独立性をどう測定するか? (Ablation study が必要)
3. crowding 耐性をどう実証するか? (proprietary IC vs benchmark IC の長期追跡)

---

## 9. 引用候補リスト (S/A/B 級)

### S 級 (LP 訴求資料で中核的に引用)

| 著者・年 | タイトル | ジャーナル | 役割 |
|---------|---------|-----------|------|
| **Grinold, R.C. (1989)** | "The Fundamental Law of Active Management" | J Portfolio Management 15/3, 30-37 | 公式の出典 |
| **Grinold & Kahn (2000)** | Active Portfolio Management (2nd ed.) | McGraw-Hill | 教科書的標準 |
| **Clarke, de Silva, Thorley (2002)** | "Portfolio Constraints and the Fundamental Law of Active Management" | FAJ 58/5, 48-66 | TC 拡張 |
| **Buckle, D. (2004)** | "How to calculate breadth" | J Asset Manag 4/6, 393-405 | Effective Breadth の核心 |
| **Qian & Hua (2004)** | "Active Risk and Information Ratio" | J Investment Management 2/3, 1-15 | Strategy Risk (σ_IC) |
| **Cremers & Petajisto (2009)** | "How Active Is Your Fund Manager?" | RFS 22/9, 3329-3365 | Active Share |
| **McLean & Pontiff (2016)** | "Does Academic Research Destroy Stock Return Predictability?" | J Finance 71/1, 5-32 | Crowding 35% decay |
| **Ding & Martin (2017)** | "The fundamental law of active management: Redux" | J Empirical Finance 43, 91-114 | IR upper bound |
| **Pastor, Stambaugh, Taylor (2015)** | "Scale and Skill in Active Management" | JFE 116, 23-45 | 規模の不経済 |

### A 級 (補強引用)

| 著者・年 | タイトル | ジャーナル |
|---------|---------|-----------|
| Petajisto (2013) | "Active Share and Mutual Fund Performance" | FAJ 69/4 |
| Frazzini, Friedman, Pomorski (2016) | "Deactivating Active Share" | FAJ 72/2, 14-21 |
| Cremers & Pareek (2016) | "Patient Capital Outperformance" | JFE 122, 288-306 |
| Polakow & Gebbie (2008) | "How many independent bets are there?" | J Asset Manag 9/4, 278-288 (arXiv:physics/0601166) |
| Sneddon (2020) | "Strategy design and the fallacies of breadth" | J Asset Manag 21/7, 626-635 |
| Ye, J. (2008) | "How Variation in Signal Quality Affects Performance" | FAJ 64/4, 48-61 |
| Pastor, Stambaugh, Taylor, Zhu (2021) | "Diseconomies of Scale in Active Management: Robust Evidence" | Critical Finance Review 11, 593-611 |
| Heinrich, Shivarova, Zurek (2021) | "Factor investing: alpha concentration versus diversification" | J Asset Manag 22, 464-487 |

### B 級 (背景・補助)

| 著者・年 | タイトル |
|---------|---------|
| Michaud & Michaud (2005) | "The Fundamental Law of Mismanagement" (New Frontier Newsletter) |
| Sorensen, Qian, Hua, Schoen (2004) | "Multiple Alpha Sources and Active Management" (JPM 30/2) |
| Ding, Martin, Yang (2020) | "Portfolio Turnover when IC is Time Varying" (J Asset Manag 21) |
| Chincarini & Kim (2007) | "Another look at the information ratio" (J Asset Manag 8/5) |
| Cho, T. (2020) | "Turning alphas into betas: Arbitrage and endogenous risk" (JFE) |
| Kang, Rouwenhorst, Tang (2021) | "Crowding and Factor Returns" (working paper) |
| Berk & Green (2004) | "Mutual Fund Flows and Performance in Rational Markets" (JPE 112/6) |
| Meucci, Santangelo, Deguest (2014) | "Measuring Portfolio Diversification Based on Optimized Uncorrelated Factors" (Risk) |
| Kahn & Shaffer (2005) | "The Surprisingly Small Impact of Asset Growth on Expected Alpha" (JPM 32/1) |
| diBartolomeo (2008) | "Measuring Investment Skill Using the Effective Information Coefficient" (J Performance Measurement) |
| Kaniel, Lin, Pelger, Van Nieuwerburgh (2023) | "Machine-learning the skill of mutual fund managers" (JFE 150) |

### URL/DOI 確認済み主要論文 (一次資料)

- Ding & Martin (2017): https://ideas.repec.org/a/eee/empfin/v43y2017icp91-114.html
- Buckle (2004): https://link.springer.com/article/10.1057/palgrave.jam.2240118 (DOI:10.1057/palgrave.jam.2240118)
- Qian & Hua (2004) PDF: https://www.panagora.com/assets/JOIM-Active-Risk-and-Information-Ratio.pdf
- Cremers & Petajisto (2009): https://depot.som.yale.edu/icf/papers/fileuploads/2370/original/06-14.pdf
- Petajisto (2013) PDF: http://www.petajisto.net/media/20090831h.pdf
- Frazzini, Friedman, Pomorski (2015 working / 2016 FAJ): http://www.petajisto.net/papers/ffp_original.pdf
- McLean & Pontiff (2016) working: https://www.hec.ca/finance/Fichier/McLean.pdf
- Pastor, Stambaugh, Taylor (2015): https://www.nber.org/system/files/working_papers/w19891/w19891.pdf
- Pastor, Stambaugh, Taylor, Zhu (2021): https://cfr.ivo-welch.info/published/papers/pastor2021diseconomies.pdf
- Polakow & Gebbie (2008): https://arxiv.org/abs/physics/0601166
- Clarke-de Silva-Thorley (2002): https://rpc.cfainstitute.org/research/financial-analysts-journal/2002/portfolio-constraints-and-the-fundamental-law-of-active-management
- Not All Factors Crowd Equally (2025): https://arxiv.org/abs/2512.11913 (※ 著者が major revision 申請中、現時点では withdraw 表示)

---

## 10. 軸A・C との連携ポイント

### 軸A (Fundamental Law の理論基盤) との連携
- 軸 A で扱う Grinold (1989) 元論文の数学的導出を前提に、本軸 B では「経験的に IC・BR がどう振る舞うか」を補完
- TC (Transfer Coefficient, Clarke-de Silva-Thorley 2002) は軸 A の枠内、本軸では捕捉のみ

### 軸C (実装制約・MAS 設計) との連携
- 本軸の「σ_IC を下げる」「BR_eff を上げる」の具体的工学的手法は軸 C で扱う
- MAS が判断パスの独立性を保つ機構 (例: 異なるシステムプロンプト、異なる情報セット) は軸 C
- Capacity 制約下での銘柄選択・サイジングは軸 C の Risk Parity / Portfolio Construction

### LP 訴求資料への組み込み順序 (推奨)

1. **Hook**: Grinold (1989) の式を提示 → 単純さの魅力
2. **理論基盤** (軸A): 数学的厳密性を確認
3. **経験的厚み** (本軸 B): 「naive な IR=IC×√BR は通用しない」批判をすべて列挙し、それぞれに Y×MAS で反論
4. **実装** (軸C): MAS のアーキテクチャが (3) の反論を具体的に実現する仕組み
5. **トラックレコード**: Y の実績 + simulated MAS の追加効果

---

## 確信度総合評価

| セクション | 確信度 | 根拠 |
|-----------|--------|------|
| 1. IC dilution | 高 | 4論文以上で一致 |
| 2. Independent bets | 高 | PCA 実証は再現性高 |
| 3. Effective Breadth | 中-高 | 理論は確立、数値は universe 依存 |
| 4. IC stability | 高 | Ding-Martin Redux は学術的定説 |
| 5. Active Share | 中 | Cremers vs AQR 論争未決着、両立可能 |
| 6. Capacity & Crowding | 高 | PST 系は方法論的検証済 |
| 7. ファンドコンセプト含意 | 中 | 反論材料は揃ったが、実証データ不足 |

**IC × BR 同時押上の論証強度**: **B+ (中-高)**。論理的・理論的には反論可能、ただし Y×MAS 固有の実証データ(σ_IC 削減効果、判断パス独立性)がまだ不足。実証データを得れば A 級論証へ昇格可能。

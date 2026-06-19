# 軸F: Y型暗黙知の IC 安定性 — Fundamental Law 視点による再フレーミング

**作成日**: 2026-05-11
**目的**: 既存メモ (2026-05-06 `AI_augmentation_research_for_fund_concept.md`) で整理した Augmentation 研究群を、Fundamental Law of Active Management (IR = IC × √BR) の **IC 観点** で再配置する
**位置付け**: ファンドコンセプト三核心 (3) — 「Y型暗黙知が IC の源泉である」という主張の経験的・理論的証拠軸
**前提**: 軸 A (IC × √BR 押し上げの一般定理) と軸 B (MAS による BR 拡張) と並行。本軸は IC 側の安定性と移植可能性を担う

---

## エグゼクティブサマリ

### 既存 6 軸 → Fundamental Law レンズへの再配置

| 既存メモの章 / テーマ | Fundamental Law レンズでの再解釈 | 役割 |
|---|---|---|
| **§1 AI×人間協働 (Centaur, Cyborg)** Kasparov / Dell'Acqua / Boudreau | IC × √BR を **同時に** 押し上げる一般定理 → 主軸 A に再配置 | 理論起源 |
| **§1.2 / §3.4 Brynjolfsson, Li, Raymond (QJE 2025) "AI が熟練者の暗黙知を拡散"** | **IC 伝達の経験的証拠** — Y の暗黙知を別人格 (LLM) へ移植可能との直接実証 | 本軸の中核 |
| **§1.1 Dell'Acqua HBS WP 24-013 "Jagged Frontier"（品質 +40%）** | **IC 安定性の証拠** — フロンティア内では IC 純度+安定性が向上、ただし境界外では IC が劣化する制約条件 | 本軸の中核 |
| **§1.7 Kahneman *Noise* (2021)** | **IC 純度向上の機序** — 同条件下の判断変動 (occasion noise) を抑え、IC の母集団分散を縮小 | IC 安定性の機序 |
| **§2.1 / §1.5 認知拡張・専門家補強 (Boudreau, UW/Adobe)** | IC × BR の両面押し上げ → 軸 A 補強 | 理論補強 |
| **§3 暗黙知形式知化 (Polanyi, Nonaka SECI, GenAI-SECI)** | **IC 移植可能性の理論的枠組み** — どこまで形式化すれば IC が損なわれないかの設計原理 | 本軸の理論 |
| **§4 Alpha-GPT / FinArena / Black-Litterman / AlphaAgents** | **金融特化での IC 移植の参照アーキテクチャ** | 実装含意 |

### 本軸キーメッセージ

1. **Y の IC は移植可能である** — Brynjolfsson et al. (QJE 2025) は、AI モデルが熟練者の暗黙知を他者に拡散することを大規模実証。これは Y の暗黙知を LLM ベース MAS に「シード」することで IR = IC × √BR の IC を保持/伝播できる経験的根拠となる。
2. **IC は AI で純化できる (Noise の削減)** — Kahneman *Noise* と Brynjolfsson の顧客満足度/解決率向上の事実は、AI が判断のオケージョン・ノイズを抑えることで **同じ IC でも実効的な IR が改善する**ことを示す。
3. **IC は境界条件付きで成立する (Jagged Frontier)** — Dell'Acqua の +40% は「フロンティア内」のみ。Otis Berkeley/HBS の Kenya RCT は **上位起業家でのみ +18%**、下位はマイナス。Y の判断を AI に移植する際は **Y が既に高 IC を実証している領域** に絞る設計原理が支持される。
4. **IC 移植には設計が必要 (SECI × RAG)** — Polanyi の不可知論と Brynjolfsson の楽観論は **「完全形式知化は不要、十分なパターン抽出で IC は伝達される」** という現代的調停で解決可能。既プロジェクト `project_fm_an_perspective_discussion.md` の「判断パスカタログ + RAG 方式」と一致。

---

## 1. IC 移植可能性の理論的基礎

### 1.1 Fundamental Law における IC の定義

Grinold (1989) / Grinold & Kahn (1995) の Fundamental Law of Active Management:

$$IR = IC \cdot \sqrt{BR}$$

- **IR** (Information Ratio) = 超過リターン / アクティブリスク
- **IC** (Information Coefficient) = 予測値と実現値の相関（マネージャーのスキル）
- **BR** (Breadth) = 独立予測の本数（年あたり）

IC は **「マネージャーの予測が実現リターンとどれだけ相関するか」** を測る。Buffett 型のように年に少数だが高 IC、Simons 型のように日に数万件で低 IC、いずれも IR を上げられる（Corporate Finance Institute; OMSCS Notes 2025）。

> 注: Ding & Martin (2017) "The fundamental law of active management: Redux" は Grinold-Kahn 公式の breadth の仮定を厳密化し、$IR = IC_{mean} / IC_{stdev}$ と再表現できることを示している (Quant Stack Exchange 2024)。この **IC の時系列安定性 (= IC の標準偏差を抑えること)** が IR を直接決めるという見方は、本軸の「IC 安定性」議論と整合する。

### 1.2 Y の暗黙知 = IC の源泉

Y 型熟練アナリストの「暗黙知」(Polanyi 1966, *The Tacit Dimension*) は、

- 銘柄選択（cross-sectional な相対判断）
- タイミング（時系列上の確信度）
- 規律（実行段階での認知バイアス制御）

の各段階で **「予測値と実現値の相関を平均より高くする」** 能力として現れる。これは Fundamental Law の IC そのものである。

ただし、Polanyi 流の暗黙知は **完全な形式知化ができない (tacit knowing は明示知の前提)** ため、伝統的なクオンツファクター（バリュー、モメンタム等）では捕捉不可能と長らく見なされてきた。

### 1.3 暗黙知 → 形式知の SECI スパイラル (Nonaka & Takeuchi 1995)

| ステップ | 内容 |
|---|---|
| Socialization | 暗黙 → 暗黙（弟子入り型） |
| Externalization | 暗黙 → 明示（言語化・モデル化） |
| Combination | 明示 → 明示（ファクター統合等） |
| Internalization | 明示 → 暗黙（実践による内面化） |

**GenAI-SECI 拡張** (arXiv 2603.21866, 2026) は LLM が Externalization と Internalization を仲介する設計を提案。Y の暗黙知を Externalization → Combination → AI が再生する形にできれば、Y の IC が AI に移植される。

---

## 2. IC 伝達の経験的証拠: Brynjolfsson, Li, Raymond (QJE 2025) の深掘り

### 2.1 研究設計と核心結果

- 発行: *Quarterly Journal of Economics* 140(2), 889–942（NBER WP 31161, arXiv 2304.11771）
- 設計: Fortune 500 のカスタマーサポート **5,179 名** × 生成 AI 対話アシスタント staggered rollout
- 核心一文 (Abstract, arXiv 2304.11771 p.1):
  > "We provide suggestive evidence that the **AI model disseminates the potentially tacit knowledge of more able workers** and helps newer workers move down the experience curve."

### 2.2 IC 伝達の機序: 経験曲線の劇的圧縮

NBER WP 31161 の Figure 9 / Appendix A.4 から（researchgate 抜粋, nber.org pdf 確認）:

| 群 | 2 ヶ月時点の生産性 | 5 ヶ月時点 | 8-10 ヶ月時点 |
|---|---|---|---|
| Never Treated (AI なし) | 約 1.5 resolutions/hour | 約 2.0 | **2.5 (到達)** |
| Always Treated (AI あり初日から) | **2.5 (即時到達)** | 3.0+ | 継続上昇 |
| Late Treated (5 ヶ月目から AI) | 1.5（AI なし軌道） | 2.0 → 急上昇 | Always Treated 軌道に合流 |

**IC 観点での解釈**:
- 「2 ヶ月で 8-10 ヶ月相当の経験曲線位置に到達」= **AI が熟練者のパターン認識（= IC の構成要素）を新人に即時伝達した**
- これは「IC は経験年数で増える」という従来モデルに対して、**「IC は外部 (AI) からシード可能」** との反証
- Y の判断パターンを LLM に Externalize → 他のエージェント (新人 OR AI) が即座に Y 級 IC を発揮できる構造

### 2.3 IC 純度の同時改善: 顧客満足度 / 解決率 / 離職

Abstract より:
- 顧客満足度 (NPS) **+** （Figure A.5 Panel D）
- Resolution rate **+** （Figure A.5 Panel C）
- Managerial intervention 要請 **減**
- 離職率 **改善**

これらは **「同じスループットでも質が向上した」** = IC 純度向上を示唆する。Fundamental Law では BR が一定で IC が上がれば IR が直接改善する。

### 2.4 熟練者本人への効果が小さい点の再解釈

「最高スキル層は AI の効果が小さい」「ボトム層は +34%」というスキルレベリング効果は、**Y 本人を AI で増強する話ではなく、Y の暗黙知を AI 経由で別エージェントに分配する話と読むべき**。Y の IC は所与とし、AI は **Y の IC を 24/7 並列稼働させる伝達装置** として機能する。これがファンドコンセプトの中核論理と一致する。

### 2.5 IC 移植の論証強度（自己評価）

- **論証強度: 強 (★★★★☆)**
- 5,179 名 × staggered rollout × 経験曲線の劇的圧縮 + 質的指標同時改善は、ランダム化と規模の両面で十分な統計力を持つ
- 残る弱点: 金融特化ではない、IC を直接測定したわけではない（生産性で代替）
- 補完が必要: §6 で金融特化の IC 直接測定研究 (Kim/Muhn/Nikolaev 2024) を投入

---

## 3. IC 安定性の経験的証拠: Dell'Acqua HBS WP 24-013

### 3.1 核心数値（既存メモ §1.1 を IC 視点で再解釈）

| 指標 | 効果 | IC 観点の解釈 |
|---|---|---|
| タスク完遂数 +12.2% | BR 上昇 | 軸 A 寄り |
| 完遂時間 -25.1% | 単位時間 BR 上昇 | 軸 A 寄り |
| **品質 +40%** | **IC 上昇** | **本軸の核心** |
| 平均以下 +43% / 平均以上 +17% | スキルレベリング | IC ばらつき縮小 |

「品質 +40%」は専門評価者による盲検評価。これは **同じ意思決定空間でアウトプット品質が上がった = 予測の質 (IC) が上がった** と解釈できる。

### 2.2 Jagged Frontier の含意 — IC は境界条件付き

> "フロンティア外（人間の文脈判断が必要）タスクでは AI 利用群は **-19 ポイント**"

**IC 観点での解釈**: AI 補強が IC を改善するのは **「Y が既に高 IC を実証している領域」のみ**。フロンティア外では IC が劣化する。これは設計原理として:

- ファンドコンセプトの適用ユニバースを Y が知見を持つ 300–400 銘柄 (`project_analyst_universe.md` 既決定) に限定する
- 新規セクター・新興市場へ拡張する際は、Y が事前に基準点を作るまで AI 単独で IC を主張しない

という運用ルールを支持する。

### 3.3 スキルレベリング → IC 分散の縮小

「平均以下 +43%、平均以上 +17%」は **チーム全体の IC 分散が縮小し、平均 IC が向上する**ことを意味する。Fundamental Law の Ding-Martin Redux 版 ($IR = IC_{mean} / IC_{std}$) の枠組みで、IC の標準偏差が縮むことは IR の直接的押し上げとなる。

---

## 4. IC 純度向上: Kahneman, Sibony, Sunstein *Noise* (2021)

### 4.1 Noise の定義と IC への影響

Kahneman et al. (2021) は人間判断のばらつきを 3 種類に分解:

| Noise 種別 | IC への影響 |
|---|---|
| Level noise (人ごとの平均判断のずれ) | IC の系統的バイアス |
| Pattern noise (人ごとの判断パターンの違い) | IC のクロスセクション分散 |
| Occasion noise (同一人物の機会変動) | **IC の時系列分散 → Ding-Martin 公式の分母** |

特に Occasion noise（疲労・気分・順序効果）は、Y 本人が同じ局面で日によって異なる判断をする現象であり、これが IC の時系列安定性を直接損なう。

### 4.2 アルゴリズムの一貫性 = IC 安定性

Kahneman らは **「単純な線形ルールでも熟練者の判断より一貫性で勝る」** ことを多数の領域 (臨床診断、保険査定、雇用判断) で示した。AI に Y の判断パターンを移植すれば、Y の signal を保持しつつ Occasion noise を消去できる。これは Fundamental Law の IC 安定性を直接改善する設計原理である。

### 4.3 Brynjolfsson 結果との整合

Brynjolfsson et al. (2023) で示された顧客満足度向上・managerial intervention 要請の減少は、まさに **AI が現場判断の Occasion noise を抑制した結果** と読める。Kahneman の理論予測と Brynjolfsson の実証が一致する点は、IC 純度向上の論証強度を高める。

---

## 5. SECI モデルと IC 移植の設計原理

### 5.1 完全形式知化が不要であるという調停

Polanyi (1966) の「暗黙知は完全に形式知化できない」立場と Brynjolfsson et al. (2025) の「AI は暗黙知を拡散する」観察は一見矛盾するが、**現代的調停**は以下:

- 暗黙知の **完全な意味理解** は不可能 (Polanyi)
- 暗黙知の **実用上十分なパターン抽出** は LLM で可能 (Brynjolfsson)
- → 「**IC を保持するに足るレベルの形式化** は可能」というのが本軸の主張

### 5.2 GenAI-SECI とパターンカタログ + RAG 方式

既プロジェクトメモ (`project_fm_an_perspective_discussion.md`) で決定済の「判断パスカタログ + RAG 方式」は、

| SECI ステップ | 実装 |
|---|---|
| Externalization (暗黙 → 明示) | Y への構造化 Q&A、判断パスカタログ生成 |
| Combination (明示 → 明示) | カタログ → ベクトル DB / Neo4j KG |
| Internalization (明示 → 暗黙) | LLM エージェントが RAG で再生、Y 級判断を発揮 |

という対応が成立し、GenAI-SECI モデル (arXiv 2603.21866) の枠組みと一致する。

### 5.3 SECI 移植の失敗条件

完全には移植できない要素として:

- **Relational tacit knowledge** (Collins 2010): Y の人脈・現場感覚 — 言語化困難
- **Somatic tacit knowledge**: 反射的な相場勘 — 量的なシグナルへの分解で部分代替

これらは MAS 設計時に **「Y が常時カバー」とする領域** として明示し、AI 移植を試みない部分を残す必要がある。

---

## 6. 補充論文（既存メモに無い IC 関連）

### 6.1 Kim, Muhn, Nikolaev (2024) "Financial Statement Analysis with Large Language Models"

- **発行**: BFI WP 2024-65 / SUERF Policy Brief 1008 / Chicago Booth Fama-Miller / arXiv 2407.17866
- **設計**: 15,401 社 × 1968–2021 の財務諸表を匿名化 → GPT-4 Turbo に Chain-of-Thought プロンプトで翌期 EPS 方向予測
- **核心結果（IC 観点）**:
  - GPT-4 の予測精度 **60.4%** vs 人間アナリスト **52.7%** (1 ヶ月後), 56.7% (1–2 四半期後)
  - GPT は **アナリストが苦戦する状況（小型株、損失計上、ボラタイル earnings）で相対優位**
  - 取引戦略の Sharpe ratio / alpha が GPT 予測ベースで人間/ML ベースより高い
- **本軸への含意**: **金融特化での IC 直接測定**。LLM 単独でも Y 級アナリストに匹敵/凌駕する IC を発揮可能 → Y の判断パターンを RAG/Prompt で移植すれば更に IC が伸びる余地

### 6.2 Otis, Clarke, Delecourt, Holtz, Koning (2024) "The Uneven Impact of Generative AI on Entrepreneurial Performance"

- **発行**: HBS WP 24-042 / Columbia Business School / Berkeley Haas
- **設計**: ケニア 640 名 SMB 起業家 × GPT-4 ベース AI メンター (WhatsApp) × 5 ヶ月 RCT
- **核心結果（IC 観点）**:
  - 平均処理効果: ゼロ（帰無仮説棄却不可）
  - **事前登録の異質性**: 上位起業家 +0.27 SD、下位起業家マイナス
  - Mollick (2024) Stanford GSB 引用: **上位起業家 +18% 利益増、下位はマイナス**
- **本軸への含意**: Jagged Frontier 論の補強。**「既に高 IC を実証している主体に対してのみ AI 増強が機能する」** という Y 型ファンドの大前提を直接的に裏付ける独立 RCT 証拠

### 6.3 (補充) "When LLMs Go Abroad: Foreign Bias in AI Financial Predictions" (HBS WP 26-013, 2026)

- **設計**: ChatGPT vs DeepSeek の国別バイアス比較
- **結果**: ChatGPT は **13.3% 大きな絶対価格予測誤差、7% 高い方向性予測誤差**（DeepSeek 比）
- **IC 観点**: LLM 単独の IC は学習データのバイアスに依存 → **Y の判断による校正 (再校正) が IC 純度確保に必要**

### 6.4 (補充) "Large Language Models and Return Prediction in China" (ABFER 2024)

- **設計**: BERT/FinBERT/RoBERTa/Baichuan/ChatGLM/InternLM/Ensemble × 中国市場ニュース
- **結果**: out-of-sample 方向予測精度 **約 52.6–52.8%**（accuracy）、cross-sectional correlation **1.5–2.0%**
- **IC 観点**: **LLM 単独の IC は約 0.015–0.020 にとどまる**。Y による解釈・選別を加えることで IC を一桁伸ばす設計余地が大きい

### 6.5 (補充) "What Does ChatGPT Make of Historical Stock Returns?" (AEA 2026)

- **結果**: LLM 単独予測は **「過剰外挿 (over-extrapolation)」のバイアス**、平均予測 2.0% vs 実現 1.12%
- **IC 観点**: LLM 単独の IC を毀損する系統的バイアスを Y の判断で校正する必要性を強調

### 6.6 補充論文の総合的含意

| 論文 | Y の IC を…？ |
|---|---|
| Kim/Muhn/Nikolaev 2024 | **代替**できる程度に LLM 単独で IC 高い → Y との合成で更に伸ばせる |
| Otis 2024 | **上位主体でのみ AI 増強が効く** → Y 型に AI を載せる戦略の妥当性裏付け |
| HBS 26-013 | **LLM 単独は地域バイアスがある** → Y による再校正が IC 純度に必要 |
| ABFER 2024 (中国) | LLM 単独 IC ≈ 0.02 → Y 級アナリスト IC (経験的に 0.05–0.15) との合成で IR 押し上げ余地大 |
| AEA 2026 | LLM 過剰外挿バイアス → Y による Noise 削減 + 再校正 |

---

## 7. ファンドコンセプトへの含意（IC 設計原理）

### 7.1 IC 移植の必要要素

| 要素 | 出典 | 実装 |
|---|---|---|
| **Externalization** (Y 暗黙知 → 明示) | Nonaka SECI / GenAI-SECI | 構造化 Q&A、判断パスカタログ |
| **Combination** (明示知の構造化) | 同上 | Neo4j KG, ベクトル DB |
| **Internalization** (LLM が Y 級判断を再生) | Brynjolfsson QJE 2025 | RAG-augmented MAS |
| **Noise 除去** (Occasion noise) | Kahneman *Noise* | 一貫したプロンプト・温度 0 / モデル固定 |
| **Frontier 制御** (Jagged Frontier) | Dell'Acqua HBS 24-013, Otis HBS 24-042 | Y 既知ユニバース 300–400 銘柄に限定 |
| **再校正** (LLM バイアス除去) | HBS 26-013, AEA 2026 | Y による定期 review、二段階チェック |

### 7.2 設計上の禁則事項

- Y が未経験のセクター・市場での AI 自律判断 → IC 不明
- 単一 LLM への依存（Lopez-Lira 系の単純な GPT 予測） → Foreign bias リスク
- 形式化なしで Y の判断を「丸投げで真似させる」 → SECI Externalization なしでは IC 移植不可

### 7.3 軸 A・軸 B との連携ポイント

| 軸 | 連携内容 |
|---|---|
| **軸 A (IR = IC × √BR)** | 本軸 F は IC 側を保持・移植する条件を提供。軸 A はその意義を定式化 |
| **軸 B (MAS による BR 拡張)** | 本軸 F が移植した IC を、軸 B が複数エージェント × 銘柄 × 時点で並列稼働させ √BR を最大化 |
| **軸 C/D (実装基盤)** | 本軸の SECI 設計原理を、軸 C/D の MAS 実装で具体化 |

---

## 8. 既存メモとの対応表（全 25 論文 + 補充 5 本）

### S 級（IC 観点での最重要）

| # | 論文 | 既存メモでの位置 | IC 観点での再配置 |
|---|---|---|---|
| 1 | **Brynjolfsson, Li, Raymond (QJE 2025)** | §1.2, §3.4 | **本軸 §2 中核** — IC 伝達の経験的証拠 |
| 2 | **Dell'Acqua et al. (HBS 24-013)** | §1.1 | **本軸 §3 中核** — IC 安定性 + Jagged Frontier |
| 3 | **Kahneman, Sibony, Sunstein *Noise* (2021)** | §1.7 | **本軸 §4 中核** — IC 純度向上の機序 |
| 4 | Polanyi *Tacit Dimension* (1966) | §3.1 | 本軸 §1.3, §5 — 移植可能性の境界条件 |
| 5 | Nonaka & Takeuchi (1995) SECI | §3.1 | 本軸 §5 — 移植の設計原理 |

### A 級（IC 観点でも重要）

| # | 論文 | 既存メモ位置 | IC 観点 |
|---|---|---|---|
| 6 | Noy & Zhang (Science 2023) | §1.3 | スキルレベリング → IC 分散縮小 |
| 7 | Peng et al. (Copilot 2023) | §1.4 | コーディング領域での IC 移植実証 |
| 8 | Boudreau et al. (Centaur 2024) | §1.5 | IC × BR 同時押し上げの理論化 |
| 9 | Daugherty & Wilson Missing Middle | §1.6 | IC 移植の組織設計 |
| 10 | GenAI-SECI (arXiv 2603.21866) | §3.2 | 本軸 §5.2 — 設計枠組み |
| 11 | Augmenting Expert Cognition (UW/Adobe) | §2.2, §3.2 | 認知拡張 = IC 保持と拡張の両立 |
| 12 | Tacit Knowledge Discovery (UFMG/USP) | §3.2 | LLM による暗黙知発見 = Externalization 自動化 |

### B 級（金融特化）

| # | 論文 | 既存メモ位置 | IC 観点 |
|---|---|---|---|
| 13 | Alpha-GPT | §4.1 | アイデア → ファクター = SECI Externalization の金融実装 |
| 14 | Toward Expert Investment Teams (Oxford-Man) | §4.2 | MAS 内での IC 役割分担 |
| 15 | AlphaAgents (BlackRock) | §4.3 | 機関投資家での IC 移植実装例 |
| 16 | FinArena (arXiv 2503.02692) | §4.4 | Mixture of Experts = IC 集約 |
| 17 | Decision-informed NN with LLM (Oxford/UNIST) | §4.5 | IC → 意思決定変換 |
| 18 | LLM-Enhanced Black-Litterman (2504.14345) | §4.6 | **Y のビュー (暗黙知 IC) を BL に投入する直接実装** |
| 19 | Are LLMs Rational Investors (2402.12713) | §4.7 | LLM バイアス除去 = IC 純度確保 |

### C 級（ドメイン拡張）

| # | 論文 | 既存メモ位置 | IC 観点 |
|---|---|---|---|
| 20 | Sepsis Diagnosis (2309.12368) | §2.1 | 医療での IC 安定性 |
| 21 | CopilotCAD (2404.07424) | §2.1 | 専門家補助 = IC 維持 |
| 22 | 2-Factor Retrieval Radiology (2412.00372) | §2.1 | AI 予測の信頼度 = IC 校正 |
| 23 | AI-Assisted Prostate Cancer MRI (2502.03482) | §2.1 | 専門家での IC 補強 |
| 24 | Tool or Tutor Cancer (2502.16411) | §2.1 | IC 保持 (ツール) vs 学習 (チューター) |
| 25 | Future of Work with AI Agents (Stanford 2506.06576) | §5.5 | 経済全体の IC 移植監査 |

### 補充（既存メモに無い IC 関連）

| # | 論文 | 出典 | IC 観点 |
|---|---|---|---|
| **26** | **Kim, Muhn, Nikolaev (2024) Financial Statement Analysis with LLMs** | BFI WP 2024-65 / arXiv 2407.17866 | **金融特化 IC 直接測定** — GPT-4 60.4% vs 人間 52.7% |
| **27** | **Otis et al. (2024) Uneven Impact on Kenyan Entrepreneurs** | HBS WP 24-042 | **Jagged Frontier の独立追試** — 上位 +18%、下位マイナス |
| **28** | **When LLMs Go Abroad: Foreign Bias (HBS 26-013)** | HBS WP 26-013 | LLM 単独 IC のバイアス → Y 校正の必要性 |
| **29** | **LLMs and Return Prediction in China (ABFER 2024)** | ABFER 2024 conference | **LLM 単独 IC ≈ 0.02** の基準点 |
| **30** | **What Does ChatGPT Make of Historical Stock Returns? (AEA 2026)** | AEA Conference 2026 | LLM 過剰外挿 → Y による Noise 削減必要 |

### 引用不可（再掲）

- Toner-Rodgers (2024) arXiv 2412.17866 — **MIT 撤回要請、データ捏造の疑い**

---

## 9. 未調査・継続調査推奨

1. **Y 級アナリストの IC 実証ベンチマーク**: 経験的に IC は 0.05–0.15 と言われるが、Y 個人の IC を直接測定する設計を別タスクで詰める必要
2. **IC 時系列安定性のフィールド実証**: Brynjolfsson の経験曲線は生産性指標、IC そのものの時系列は未測定。金融分野での fortified RCT が必要
3. **Ding & Martin (2017) Redux** の理論精読 — $IR = IC_{mean} / IC_{std}$ への完全移行で、本軸の論理を更に厳密化可能
4. **EU AI Act / SEC Marketing Rule** 下でのアナリスト判断 AI 移植の合法性 — 開示要件次第で SECI Externalization の粒度に制約あり
5. **Mollick / Otis フォローアップ**: 上位 + 18% の持続性、AI 利用が Y 自身の IC を毀損しないか（cognitive offloading リスク）

---

**参考プロジェクト Memory**:
- `project_fm_an_perspective_discussion.md` — AN 目線形式知化（判断パスカタログ + RAG）と一致
- `project_analyst_universe.md` — Y チームのスクリーニング済みユニバース（300–400 銘柄）= Jagged Frontier の運用上の境界

**情報源**: 既存メモ `2026-05-06_AI_augmentation_research_for_fund_concept.md`, alphaXiv MCP (Brynjolfsson 2304.11771 一次取得), Tavily 検索 (Kim/Muhn/Nikolaev, Otis Kenya, HBS 26-013, ABFER, AEA), CFI / OMSCS Notes (Grinold-Kahn 公式), Quant Stack Exchange (Ding-Martin Redux)

**作成者**: Claude (Opus 4.7) via /quants

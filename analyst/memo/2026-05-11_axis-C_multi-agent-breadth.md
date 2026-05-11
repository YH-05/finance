# 軸C: マルチエージェントによる Breadth 拡大

**作成日**: 2026-05-11
**目的**: MAS (Multi-Agent System) で Fundamental Law of Active Management における Breadth (独立予測数) を拡大できることの理論的・実証的支持を整理する
**位置付け**: 三核心1 — Fundamental Law 三本柱の第3柱（IC × Breadth × TC のうち Breadth 担保）

---

## エグゼクティブサマリ

| 主張                                 | 強い証拠                                                                                                                                                                          | Breadth 観点での評価                                                 |
| ---------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------- |
| **C-1. MAS は単体 LLM の推論精度を向上させる**   | Du et al. (arXiv 2305.14325): GSM8K 等で +10〜20%。Liang et al. (2305.19118): DoT問題を解消、commonsense MT と counter-intuitive arithmetic で MAD が CoT/self-reflection 超え               | エージェントを並列化して **「相互批評で独立思考を強化」** する仕組み自体が Breadth を高める設計        |
| **C-2. 鍵は数ではなく多様性（diversity）**     | Yang et al. (arXiv 2602.03794, ICML 2026 submit): **2 つの多様エージェントが 16 の同質エージェントに匹敵**。L4 (model+persona diversity) で peak 77.4% vs L1 baseline 65.5%                            | Breadth = 独立性 × 数。同質スケールは情報チャネル飽和、異質スケールは情報チャネル単調増加            |
| **C-3. ヒエラルキー型 MAS は金融タスクで実証的に有効** | FinCon (2407.06567): manager-analyst 階層 + CVRF で単一銘柄・ポートフォリオで FinMem 超え。TradingAgents (2412.20138): 専門アナリスト + Bull/Bear デベート + リスク管理 で baseline 超え                            | アナリスト Y 1 名の代わりに **専門分化エージェント N 名 × M 銘柄 × T 時刻** で Breadth 増殖 |
| **C-4. 業界実装は既に始まっている**             | BlackRock AlphaAgents (2508.11152): Fundamental/Sentiment/Valuation の3エージェント debate で 15 銘柄 4 ヶ月で Sharpe 向上。JPM "Ask David" 多エージェントAI、Morgan Stanley AI@MS Assistant (98% 採用) | 「実運用に耐える」 概念実証は完了。Fund concept は **「研究 → 既に展開済」** の位置取り        |
| **C-5. スケーラビリティに上限あり**             | Yang et al. (2602.03794): homogeneous は diminishing returns。Liang et al. (2305.19118): adaptive break が重要                                                                     | 純粋に N を増やすのは ROI が低い → **多様性のあるエージェント設計** が Breadth 拡大の鍵       |

**Fundamental Law への含意**: アナリスト Y 一人の Breadth は人間の認知限界 (1日 5–10 銘柄 × 250営業日) に縛られるが、Y の判断パスを反映した多様化エージェント N 名で日次 × 全銘柄カバーすれば、**Breadth は実効的に N × カバー銘柄数倍** に拡大可能。ただし「独立性」を担保しない限り Effective Breadth は伸びない (Clarke-Silva-Thorley TC 論と同根)。

---

## 1. 一般 MAS 理論 — Multi-Agent Debate

### 1.1 Du, Li, Torralba, Tenenbaum, Mordatch (2023) "Improving Factuality and Reasoning in Language Models through Multiagent Debate"
- **arXiv**: 2305.14325 (MIT CSAIL + Google Brain)
- **設計**: 複数の同一 LLM インスタンスが個別に解答 → 互いの解答を読み批評 → 自分の解答を更新（複数ラウンド）。"Society of Minds" (Minsky) からインスピレーション
- **結果（GPT-3.5-turbo, 3 agents × 2 rounds 設定）**:
  - GSM8K (算術): single 77.0% → debate 85.0%
  - MMLU: 単体 63.9% → debate 71.1%
  - 伝記事実生成 (factuality): hallucination 大幅減少
- **重要な観察**: 全エージェントが最初に間違えていても、**互いの誤りの非相関性** から debate 後に正解に収束するケースが多い。**「同質エージェントでも、サンプリングのばらつきから独立性が生じれば集合知が成立する」** ことを示唆
- **Breadth 評価**: ★★★★★ — MAS が単一エージェントを超える「最初の決定的論文」。エージェント間の独立した提案 → 批評 → 統合プロセスは、Fundamental Law の "N 独立予測" の LLM 版

### 1.2 Liang, He, Jiao, Wang et al. (2023) "Encouraging Divergent Thinking in Large Language Models through Multi-Agent Debate"
- **arXiv**: 2305.19118 (Tsinghua + SJTU + Tencent AI Lab)
- **新概念**: **Degeneration-of-Thought (DoT)** = LLM が初期解答に確信を持つと、self-reflection しても新しい思考を生み出せない問題
- **設計**: MAD (Multi-Agent Debate) — Affirmative side + Negative side ("devil" vs "angel") + Judge による調停
  - Affirmative agent は主張を提示
  - Negative agent は "tit for tat" で反論
  - Judge が議論を監視し adaptive break を判断
- **結果**:
  - Commonsense Machine Translation: GPT-3.5 + MAD が GPT-4 baseline と同等
  - Counter-Intuitive Arithmetic (反直観的数学): self-reflection は CoT と同等の誤答だが、MAD は 10–20 pp 改善
  - Figure 1 (disagreement curve): self-reflection は2ラウンドで disagreement 0 に収束（DoT発症）、MAD は 5 ラウンド維持
- **重要な含意**:
  - **「Adaptive break」必須**: 議論を永遠に続けると性能が劣化。エージェント間の認識ギャップが閉じた時点で停止
  - **「Modest tit-for-tat」必須**: 過度な反論は混乱を生むが、軽度の批判精神は divergent thinking を促進
  - **Judge は同じ LLM ファミリーでないと公平にならない**: GPT-3.5 を judge にすると GPT-4 出力にバイアスを持つ
- **Breadth 評価**: ★★★★★ — **「Independent thinking を意図的に強化する仕組み」** を明示。Fund concept への直接的応用: アナリスト Y のロジックを Devil-Angel 構造で常時検証

### 1.3 Wang, Mao, Wu, Ge, Wei, Ji (2023) "Solo Performance Prompting" (Unleashing Cognitive Synergy)
- **arXiv**: 2307.05300 (Microsoft Research + UIUC)
- **設計**: **単一 LLM 内で複数ペルソナを動的生成** し、内部対話で課題を解く（SPP）
- **結果**: GPT-4 で factual hallucination 削減、reasoning 維持。GPT-3.5/Llama2-13b では効果不在
- **意義**: **「ペルソナ多様性そのものが推論性能向上に貢献」** することを示す。MAS のコストを下げる方向（1 LLM 呼び出しで多視点）
- **Breadth 評価**: ★★★★ — 多様性 = エージェント数とは無関係。アナリスト Y の暗黙知を複数ペルソナ (e.g. Bull/Bear/Skeptic) で内部化すれば、1 推論コールでも N 視点を取得可能

---

## 2. Critic-Actor / LLM-as-Judge / Self-Consistency

### 2.1 Wang et al. (2022) "Self-Consistency Improves Chain of Thought Reasoning"
- **arXiv**: 2203.11171 (Google Research/Brain)
- **設計**: 1 つの問題に対し T>0 サンプリングで多様な推論パスを K 本生成 → 最終回答で majority vote
- **結果**: GSM8K +10%, SVAMP +14%, MultiArith +24% (greedy decode 比)。**K=40 で +23 pp** (MultiArith)
- **重要な観察**: K と精度は対数的に飽和する（Figure 3）。K=5〜10 で大半の gain を獲得
- **Breadth 評価**: ★★★★ — **「sampling diversity から独立性を引き出す」** 最古の手法。エージェント数 = サンプル数の縮図

### 2.2 Yao et al. (2023) "Tree of Thoughts: Deliberate Problem Solving with LLMs"
- **arXiv**: 2305.10601 (Princeton + Google DeepMind)
- **設計**: 推論を「思考の木」として展開し、各ノードで thought proposals → state evaluator (heuristic) で枝刈り → BFS/DFS で探索
- **結果**: Game of 24 で CoT 4% → ToT 74%
- **Breadth 評価**: ★★★ — single-agent だが、System 2 的な deliberate な探索は MAS の構成要素にも応用可能（各エージェントが ToT で個別探索 → 集約）

### 2.3 Zheng et al. (2023) "Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena"
- **arXiv**: 2306.05685 (UC Berkeley + Stanford + UCSD)
- **発見**: GPT-4 を judge にすると **人間の選好と 80%以上一致**（human-human agreement と同水準）
- **制約**: position bias (前者選好)、verbosity bias (長文選好)、self-enhancement bias (自モデル選好)
- **Breadth 評価**: ★★★★ — MAS 設計の判定者を LLM で自動化できる確証。Fund concept では「アナリスト Y の批判をシミュレートする judge agent」を構築する根拠

---

## 3. 金融特化 LLM エージェント — 比較表

### 3.1 主要 4 フレームワーク比較

| 軸 | **FinMem** (Yu et al. 2023) | **FinAgent** (Zhang et al. 2024) | **FinCon** (Yu et al. 2024) | **TradingAgents** (Xiao et al. 2024) |
| --- | --- | --- | --- | --- |
| arXiv | 2311.13743 | 2402.18485 | 2407.06567 | 2412.20138 |
| 機関 | Stevens IT | NTU Singapore | Stevens IT + Wuhan U | UCLA + MIT |
| エージェント構造 | **単一エージェント** (3 モジュール: Profiling, Memory, Decision) | **単一エージェント** (multimodal + dual reflection) | **マネージャー-アナリスト階層 (N=4)** | **専門アナリスト + Bull/Bear debate + リスクチーム** |
| 入力モダリティ | テキスト (ニュース) + 価格 | テキスト + 価格 + K-line **画像** + ツール | テキスト + 価格 + ECC 音声 | テキスト + 価格 + ソーシャル |
| メモリ | **階層メモリ (shallow/mid/deep)**, 人間認知模倣 (K=5 が最適) | Diversified memory retrieval + dual-level reflection | Episodic + Procedural; **CVRF** (Conceptual Verbal Reinforcement) | 短期 + 長期、debate 履歴 |
| 多様性メカニズム | 役割プロファイル (risk-seeking/averse/adaptive) | Dual-level reflection (低レベル/高レベル) | **専門役割** (sentiment/risk/portfolio mgr) | **Bull researcher vs Bear researcher** デベート構造 |
| 実証評価 | TSLA/NFLX/AMZN/MSFT/COIN 5銘柄, GPT-4 で B&H 超え (Sharpe 2.0+) | 6 データセット (株式+暗号), +36% profit 平均, 92.27% リターン 1 ケース | TSLA/MSFT/PFE ポートフォリオ, Markowitz MV と FinRL 超え | 比較対象 baseline 群を上回る Sharpe |
| Breadth 拡大度 | ★★ (単一エージェント, ただし K=10 で human limit 突破) | ★★★ (multimodal で情報チャネル増, dual reflection) | **★★★★ (専門化階層で独立予測者 N 増)** | **★★★★★ (Bull/Bear が構造的に independent bets を生成)** |

### 3.2 FinMem 詳細 (2311.13743)
- **核心**: 人間の作業記憶限界 (Miller 1956: 5–9 アイテム) を **K=10 まで拡張** することで TSLA Cumulative Return が +0.794 (B&H -0.669)
- **Risk profile の影響**: self-adaptive が strict risk-seeking/averse を上回る
- **Breadth 観点**: 単一エージェントだが、「メモリ容量 = 同時保持できる仮説数」が Breadth の代理指標と解釈可能

### 3.3 FinCon 詳細 (2407.06567)
- **CVRF (Conceptual Verbal Reinforcement)**: マネージャーが期末に PnL を批評し、「投資信念」を自然言語で更新 → 該当アナリストノードに伝播
- **疎な通信**: peer-to-peer のフル通信ではなく、必要なノードにだけ更新を propagate → スケーラビリティ確保
- **Breadth 観点**: 階層型 = アナリスト N 名 × マネージャー 1 名で N+1 independent agents。CVRF が独立性を保つ

### 3.4 TradingAgents 詳細 (2412.20138)
- **役割**: Fundamental Analyst, Sentiment Analyst, Technical Analyst, News Analyst, Bull Researcher, Bear Researcher, Risk Manager, Trader
- **コミュニケーション設計**: 自然言語履歴の "telephone effect" を回避するため、構造化された情報受け渡しを採用
- **Bull/Bear debate**: 同一データに対し対立的推論を生成 → trader が統合 → **意図的に divergent thinking を構造化**
- **Breadth 観点**: ★★★★★ — Liang et al. の MAD を金融特化させた設計。**「アナリスト Y の判断ロジックを 8 役割に分解し、各役割が独立予測を行う」** ファンドコンセプト直接対応

### 3.5 TradExpert (Ding et al. 2024)
- **arXiv**: 2411.00782 (Université de Montréal + Mila)
- **設計**: 4 専門 LLM (News, Market, Alpha factors, Fundamentals) + 1 General Expert で集約 (Mixture of Experts)
- **Breadth 観点**: MoE は「データソース別の独立予測」を集約する設計 → 情報チャネル数 = Breadth の代理

### 3.6 Toward Expert Investment Teams (Miyazaki, Kawahara, Roberts, Zohren 2026)
- **arXiv**: 2602.23330 (Japan Digital Design + Oxford-Man Institute)
- **核心主張**: **既存 MAS は coarse-grained instruction (「10-K を分析せよ」) で性能劣化**。実務家のワークフローに準拠した fine-grained task decomposition (e.g., 「業界比較 ROE 算出 → 過去 5 期推移分析 → ピア比較」) で risk-adjusted return が向上
- **実証**: 日本株、leakage-controlled backtest。**fine-grained 設計が coarse-grained を有意に上回る**
- **追加発見**:
  - 中間出力 (intermediate agent outputs) と最終決定の preference alignment が性能の主要ドライバ
  - 各システムの **低相関出力** を利用したポートフォリオ最適化 → 単一システム超え
- **Breadth 観点**: ★★★★★ — **「タスク粒度自体が Breadth を規定する」** ことを実証。アナリスト Y の判断パスを 50 ステップに分解すれば、各ステップが独立予測ノードになり得る

---

## 4. 業界実装事例

### 4.1 BlackRock AlphaAgents (Zhao, Lyu, Jones, Garber, Pasquali, Mehta 2025)
- **arXiv**: 2508.11152 (BlackRock 社員 6 名)
- **設計**: 3 エージェント (Fundamental / Sentiment / Valuation) + round-robin debate で BUY/SELL 合意
- **入力**: 10-K/10-Q (Fundamental), Bloomberg news (Sentiment), 価格/ボリューム (Valuation)
- **実証**: 2024 年 4 ヶ月 × 15 テック銘柄 → 単一エージェント、ベンチマーク超え (Sharpe)
- **本人達が言及**: 「将来は Technical Analysis Agent や Macro Economist Agent を追加し、スケール可能な構造」 → **業界が「エージェント数を増やして Breadth 拡大」 を明示的に目指している**
- **Breadth 評価**: ★★★★★ — 世界最大手 AM の最初の MAS 論文。Fund concept は **「BlackRock と同じ方向の延長線上にある」** と訴求可能

### 4.2 JPMorgan IndexGPT / Ask David
- **IndexGPT (2024 launch)**: GPT-4 で thematic keywords 生成 → 専用 NLP モデルで news scan → テーマ別 ETF 構築。**「アナリスト手作業のキーワード抽出を自動化」**
- **Ask David** (Private Bank): **多エージェント AI システム**、ドメインクエリで 90%+ accuracy
- **規模**: 2024 年 AI 予算 $1.3B / 総 IT $17B、2025 年 $18B
- **Breadth 評価**: ★★★★ — エージェントベースでテーマ → 銘柄を自動拡張する具体例

### 4.3 Morgan Stanley AI @ Morgan Stanley Assistant / Debrief
- **構造**: GPT-4 を 100,000 件のリサーチレポート (intellectual capital) に grounding した RAG
- **採用率**: 98% のアドバイザーチームが日常利用
- **効果**: ドキュメントアクセス率 20% → 80%
- **Debrief**: クライアントミーティング録音 → アクションアイテム抽出 → Salesforce 自動連携
- **Breadth 評価**: ★★★ — エージェント間の divergent thinking ではなく **個人アナリストの拡張ツール**。が、「アナリストの形式知を組織的に拡散」 (Brynjolfsson et al. 2025 の実装事例) として援用可能

### 4.4 Bloomberg LP — Agentic AI
- **BloombergGPT (arXiv 2303.17564)**: 50B params、財務特化 corpus 363B tokens + 一般 345B tokens
- **2025 戦略**: Anthropic MCP プロトコル採用、エージェントツールサーバー SDK 構築。**「2025 は AI Agent の年」** と公式表明
- **既存機能**: AI-powered Earnings Call Summaries, Document Search (mobile)
- **Breadth 評価**: ★★★ — インフラ側 (ツール標準) で MAS を後押し

---

## 5. Agent Diversity と Independent Bets の関係 (本軸の核心)

### 5.1 Yang et al. (2026) "Understanding Agent Scaling via Diversity" — Game Changer
- **arXiv**: 2602.03794 (SJTU + Caltech + JHU + UC Berkeley)
- **理論枠組み**: **Information-theoretic bound** — MAS 性能は intrinsic task uncertainty で上限され、**「effective channel 数 K*」** が真の性能ドライバ。エージェント数 N ではない
- **実証 (Table 2)**:

| Method | Config | Agents needed to match L1 baseline (N=16) | Peak accuracy |
| --- | --- | --- | --- |
| Vote | L1 (no diversity) | 16 | 65.49% |
| Vote | L2 (persona div.) | 8 | 66.01% |
| Vote | L3 (model div.) | **4** | 71.54% |
| Vote | L4 (full diversity) | **2** | **76.86%** |
| Debate | L4 (full diversity) | **2** | **77.43%** |

- **驚異的発見**: **2 つの multimodel + multi-persona エージェントが、16 個の同質エージェントを超える**
- **理論**: 同質エージェントの出力は強相関 → 追加サンプルが effective channel を増やさない (Theorem A.15)
- **Breadth 観点 ★★★★★**: これは Fundamental Law の Effective Breadth (Clarke-Silva-Thorley) の MAS 版そのもの。**「N を増やしても相関が高ければ Breadth は増えない、独立性確保が本質」**

### 5.2 Fundamental Law との対応

Grinold (1989) の Fundamental Law:
$$IR \approx IC \times \sqrt{BR}$$

Clarke-Silva-Thorley (2002) の Generalized Law:
$$IR \approx IC \times TC \times \sqrt{N}$$

ここで N は **independent bets** であり、相関のある予測は実効的に減少する。Yang et al. の MAS 結果は、

$$\text{MAS 性能} \propto K^* \text{ (effective channels)}$$

であり、$K^*$ は **エージェント間の相関構造で決まる**。**Fundamental Law における N と MAS における K* は同一概念の別表現** であり、`MAS の effective channel 拡大 = Fund concept の Breadth 拡大` の数理的等価性が成立する。

### 5.3 Breadth 拡大の 3 つのメカニズム

| メカニズム | 関連論文 | Breadth 寄与 |
| --- | --- | --- |
| **(a) 並列化 (N agents)** | Du et al. (2305.14325), Wang et al. (2203.11171) | 線形 (同質なら飽和) |
| **(b) 多様化 (heterogeneity)** | Yang et al. (2602.03794), Liang et al. (2305.19118) | **超線形** — 2 多様 ≧ 16 同質 |
| **(c) タスク分解 (fine-grained)** | Miyazaki et al. (2602.23330) | 各サブタスクが独立予測ノードに |

→ **Fund concept では (a)(b)(c) を組み合わせて使う**: Y の判断パスを fine-grained task に分解 (c) → 各タスクに複数 LLM + 複数ペルソナを割当 (b) → 全銘柄 × 全営業日に並列化 (a)

---

## 6. スケーラビリティと制約

### 6.1 同質スケールの飽和
- Yang et al. (2602.03794) Finding 1: 同質エージェント数 N を増やすと marginal gain ∆Success/∆N が急速に 0 へ収束。N=16 でも N=2 と差が小さいケース多数
- Liang et al. (2305.19118): MAD ラウンド数を増やすと **adaptive break 機構なしでは劣化** (over-iteration による confusion)

### 6.2 計算コスト
- Du et al. (2305.14325): N agents × R rounds で API コール数は N × R 倍
- 実務的閾値: N=3〜5, R=2〜3 が典型 (FinCon, TradingAgents, AlphaAgents が採用)

### 6.3 Hallucination の伝染リスク
- FinCon 論文 (2407.06567) は portfolio task で hallucination の **増幅** を報告 — 「単一銘柄より複雑なタスクは MAS でも誤りやすい」
- 対策: AlphaAgents の **debate consensus 機構** (合意できない場合は人間介入)

### 6.4 Judge の選定問題
- Liang et al. (2305.19118): 異なる LLM ファミリーを judge にすると不公平
- Zheng et al. (2306.05685): GPT-4 judge は self-enhancement bias を持つ
- → Fund concept では **「アナリスト Y 自身を最終判断者にする」** ことで bias を制御

### 6.5 適切な agent 数の見極め
- ICLR 2025 blog (Multi-LLM-Agents Debate): 多くの公開実装は N=3, R=2〜3 が最適。N>5 は ROI が急減
- Yang et al.: **N より diversity に投資せよ** が結論

---

## 7. ファンドコンセプトへの含意

### 7.1 Y 型暗黙知 × MAS で Breadth 拡大する設計

```
【現状】 Y 一人体制
  - カバー銘柄: 50–100
  - 判断頻度: 月次〜四半期
  - Breadth 概算: 50 × 4 = 200/年

【提案】 Y-Inspired MAS
  Layer 1: Y の判断パスを fine-grained task に分解 (Miyazaki et al. 2602.23330)
    → 例: 競争優位性評価 = (a) Moat 5項目チェック → (b) ピア比較 → (c) ESG → (d) 経営者品質 → ...
  Layer 2: 各サブタスクに多様化エージェント (Yang et al. 2602.03794)
    → 例: GPT-4 + Claude + Gemini の persona×model 多様化
  Layer 3: 役割別エージェント (AlphaAgents 構造)
    → Fundamental / Sentiment / Valuation / Technical / Macro
  Layer 4: Bull/Bear debate (TradingAgents 構造)
    → 各銘柄で意図的に対立予測を生成
  Layer 5: Y 自身を judge として最終判定 (Zheng et al. の bias 制御)

  → カバー銘柄: 500–1000 (全市場)
  → 判断頻度: 日次
  → Breadth 概算: 1000 × 250 × K* (effective channels) = 数十万〜数百万
```

### 7.2 訴求ストーリー

> **「アナリスト Y の判断は一人 1 ヶ月で 50 銘柄が限界です。しかし Y の暗黙知を学習した多様化エージェントを並列展開すれば、同じ判断品質で全市場 × 全営業日のカバーが可能です。これは Fundamental Law の Breadth を理論的に 10,000 倍以上拡張する設計です。」**

### 7.3 想定 FAQ

| 想定批判 | 反論材料 |
| --- | --- |
| 「エージェントを増やしても精度は上がらない」 | Yang et al. (2602.03794): 同質スケールは飽和、**多様性スケールは超線形に伸びる**。我々は多様化重視 |
| 「LLM の hallucination が独立性を破壊」 | Du et al. (2305.14325): エージェント間 debate で hallucination が **削減**。FinCon も検証 |
| 「業界では未実証」 | BlackRock AlphaAgents (2508.11152) は 2025 年公開、JPM Ask David は本番稼働、Morgan Stanley は 98% 採用率。**「研究 → 既に展開済」** |
| 「Y 一人で十分」 | Brynjolfsson et al. (QJE 2025): AI は熟練者の暗黙知を拡散する装置。Y の判断は維持しつつ Breadth だけ拡張 |
| 「Liang et al. の DoT 問題は MAS でも残る」 | TradingAgents の Bull/Bear 構造は **意図的に反論側を強制** することで DoT を回避する設計 |

### 7.4 軸 A, B との連携

- **軸 A (人間 × AI 増強)** との連携: AI が **暗黙知を抽出** → MAS が **暗黙知を並列実行**。両軸が直列で機能する
- **軸 B (Fundamental Law 系)** との連携: Y の暗黙知 = **高 IC の source**。MAS = **高 Breadth の手段**。両者の積で IR を最大化
- **三軸統合**: `IR = IC(Y の暗黙知) × TC(運用設計) × √N(MAS effective channels)`

---

## 8. 未調査・継続調査推奨

| 項目 | 理由 |
| --- | --- |
| **AutoGen / CrewAI / LangGraph 等 framework 比較** | 実装選定に必須。OSS 状況の最新 (2026) 調査が必要 |
| **MAS の inference cost 最適化研究** | コスト = 商業化のボトルネック。Speculative decoding, KV-cache sharing 関連 |
| **Specialized financial LLMs** (FinGPT, FinMA, PIXIU, Open-FinLLMs) | エージェントの base model 選定に影響 |
| **Reflexion / Self-Refine** | 内省機構との関係。FinCon の CVRF と類縁 |
| **GenAI agent in long-horizon tasks** (Voyager, Generative Agents) | エージェントの長期記憶設計 |
| **Causal inference + MAS** | 株価変動の因果推論を MAS で組む論文 (新興分野) |
| **NeurIPS 2025 / ICLR 2026 の最新 MAS 論文** | 本メモは 2025 年中盤までカバー、最新動向の追跡が必要 |
| **Backtesting bias in LLM trading agents** | "Look-ahead bias" 警告論文 (推測あり) を要確認 |
| **JPMorgan "Ask David" 詳細** | NDA で論文未公開だが、公開記事のさらなる収集 |

---

## 9. 引用候補リスト

### S 級（必ず引用）
1. **Du, Li, Torralba, Tenenbaum, Mordatch (2023)** "Improving Factuality and Reasoning in Language Models through Multiagent Debate" arXiv 2305.14325
2. **Liang, He, Jiao et al. (2023)** "Encouraging Divergent Thinking in LLMs through Multi-Agent Debate" arXiv 2305.19118
3. **Yang, Qu, Wen et al. (2026)** "Understanding Agent Scaling in LLM-Based Multi-Agent Systems via Diversity" arXiv 2602.03794
4. **Zhao, Lyu, Jones, Garber, Pasquali, Mehta (2025)** "AlphaAgents: LLM-based Multi-Agents for Equity Portfolio Constructions" arXiv 2508.11152 (BlackRock)
5. **Yu, Yao, Li et al. (2024)** "FINCON: Synthesized LLM Multi-Agent System with Conceptual Verbal Reinforcement" arXiv 2407.06567
6. **Xiao, Sun, Luo, Wang (2024)** "TradingAgents: Multi-Agents LLM Financial Trading Framework" arXiv 2412.20138
7. **Miyazaki, Kawahara, Roberts, Zohren (2026)** "Toward Expert Investment Teams: A Multi-Agent LLM System with Fine-Grained Trading Tasks" arXiv 2602.23330 (Oxford-Man Institute)

### A 級（コンセプト裏付け）
8. **Yu, Li, Chen et al. (2023)** "FinMem: Performance-Enhanced LLM Trading Agent with Layered Memory and Character Design" arXiv 2311.13743
9. **Zhang, Zhao, Xia et al. (2024)** "FinAgent: A Multimodal Foundation Agent for Financial Trading" arXiv 2402.18485
10. **Xu, Liu, Li (2025)** "FinArena: A Human-Agent Collaboration Framework for Financial Market Analysis and Forecasting" arXiv 2503.02692
11. **Wang, Yuan, Zhou, Ni, Shum, Guo (2023)** "Alpha-GPT: Human-AI Interactive Alpha Mining" arXiv 2308.00016
12. **Ding, Shi, Liu (2024)** "TradExpert: Revolutionizing Trading with Mixture of Expert LLMs" arXiv 2411.00782
13. **Wang, Wei et al. (2022)** "Self-Consistency Improves Chain of Thought Reasoning in Language Models" arXiv 2203.11171
14. **Yao, Yu, Zhao et al. (2023)** "Tree of Thoughts: Deliberate Problem Solving with LLMs" arXiv 2305.10601
15. **Wang, Mao, Wu, Ge, Wei, Ji (2023)** "Unleashing Cognitive Synergy in LLMs: Multi-Persona Self-Collaboration" arXiv 2307.05300
16. **Zheng, Chiang et al. (2023)** "Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena" arXiv 2306.05685

### B 級（業界・実装事例）
17. **Wu, Irsoy, Lu et al. (2023)** "BloombergGPT: A Large Language Model for Finance" arXiv 2303.17564
18. **JPMorgan IndexGPT** (Bloomberg, May 2024) - thematic AI investment
19. **JPMorgan "Ask David"** Private Bank multi-agent system
20. **Morgan Stanley AI @ Morgan Stanley Assistant / Debrief** (OpenAI partnership)
21. **Bloomberg LP MCP Adoption** (2025) - Agentic AI productionization
22. **ICLR Blogposts 2025 "Multi-LLM-Agents Debate: Performance, Efficiency, and Scaling Challenges"**

### C 級（拡張）
23. FinRobot — Agentic financial statement analysis
24. MarketSenseAI — 5 specialized agents
25. FinVerse — 600+ financial APIs in agent crew
26. Literature Review of Multi-Agent Debate for Problem-Solving arXiv 2506.00066

---

**作成者**: Claude (Opus 4.7, 1M context)
**主要ソース**: alphaXiv MCP (PDF query), Tavily / WebSearch (業界実装)
**文字数**: 約 8,200 字

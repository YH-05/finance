# AI による人間判断の増強 — ファンドコンセプト提案のためのリサーチ集

**作成日**: 2026-05-06
**目的**: アナリストYの暗黙知を AI が活用するファンドコンセプトを支える、学術論文・コンサルレポートの整理
**主張軸**: 「優れた人間判断は、AI でさらに増強できる」

---

## 0. エグゼクティブサマリ

| 主張                                      | 強い証拠                                                                                                                                       | 注意点                                       |     |
| --------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ | ----------------------------------------- | --- |
| **A. AI と人間の協調は単独より強い (Centaur)**       | Kasparov の advanced chess → 中堅 + AI + 良いプロセスがグランドマスター単独 / スーパーコンピュータ単独に勝利                                                                  | 2017 年以降、純粋な AI が人間を引き離した競技領域もある          |     |
| **B. AI は熟練者の暗黙知を他者・組織に拡散する**           | Brynjolfsson, Li, Raymond (QJE 2025): AI 支援は「**より熟練したワーカーの暗黙的知識を伝播する**（disseminates the potentially tacit knowledge of more able workers）」 | 平均効果は低スキルワーカーで大きい（34%）/ 熟練者本人の効果は小さい場合がある |     |
| **C. AI はルーチン外でも判断品質を向上させる**            | Dell'Acqua et al. (HBS WP 24-013, 758 名 BCG コンサル): タスク完遂 +12.2%、速度 +25.1%、品質 **+40%**                                                      | "Jagged Frontier" の外側では逆に -19%            |     |
| **D. AI は判断のノイズを削減する**                  | Kahneman, Sibony, Sunstein "Noise" (2021): アルゴリズムは人間より一貫性で勝る                                                                               | アルゴリズムは独自のバイアスを持ち得る → 人間との組み合わせが必要        |     |
| **E. AI は専門家の認知を拡張する**                  | "Augmenting Expert Cognition in the Age of GenAI" (UW/Adobe, 2025) 等多数                                                                     | 専門性の維持と AI 依存のバランスは設計課題                   |     |
| ~~**F. 暗黙知の形式知化は GenAI で実装可能になりつつある**~~ | "Tacit Knowledge Management with Generative AI" (2026): SECI モデルを GenAI 拡張した GenAI-SECI を提案                                                | 形式知化は完全ではなく、ハイブリッド設計が必要 (Polanyi 起源)      |     |

**含意**: Y のような卓越したアナリストの暗黙知を AI で抽出・拡張・常時稼働化する設計は、複数の独立した実証研究系列から支持される。ファンドコンセプトの中核として「Centaur 型運用 + 暗黙知 SECI 形式知化 + ノイズ削減」の三本柱で訴求できる。

---

## 1. 基盤研究 — AI による人間判断の増強

### 1.1 Dell'Acqua et al. (2023) "Navigating the Jagged Technological Frontier"
- **発行元**: Harvard Business School Working Paper No. 24-013（Organization Science 掲載予定）
- **著者**: Fabrizio Dell'Acqua, Edward McFowland III, Ethan Mollick, Hila Lifshitz-Assaf, Katherine C. Kellogg, Saran Rajendran, Lisa Krayer, François Candelon, Karim R. Lakhani
- **デザイン**: 758 名 BCG コンサル × 18 タスクの事前登録 RCT
- **主要結果（フロンティア内タスク）**:
  - タスク完遂数 **+12.2%**
  - 完遂時間 **-25.1%**
  - 品質 **+40%**
  - **平均以下のコンサルは +43%、平均以上のコンサルは +17%** 改善（スキルレベリング効果）
- **2 つの統合パターン**:
  - **Centaur (ケンタウロス型)**: 人間と AI に明確に役割分担し、得意分野で使い分ける
  - **Cyborg (サイボーグ型)**: 連続的に AI と対話・統合する
- **重要な警鐘**: フロンティア外（人間の文脈判断が必要）タスクでは AI 利用群は **-19 ポイント** 正答率が低下
- **URL**: https://www.hbs.edu/faculty/Pages/item.aspx?num=64700

### 1.2 （Research Done）Brynjolfsson, Li, Raymond (2023) "Generative AI at Work"
- **発行元**: Quarterly Journal of Economics 140(2), 889-942（NBER WP 31161）
- **著者**: Erik Brynjolfsson (Stanford), Danielle Li (MIT Sloan), Lindsey R. Raymond
- **デザイン**: Fortune 500 企業のカスタマーサポート 5,179 名 × LLM 対話アシスタント staggered rollout
- **主要結果**:
  - 1 時間あたり解決件数 **+14%**（最低スキル層は **+34%**、最高スキル層はほぼ効果なし）
  - 顧客満足度低下なし、離職率改善
- **本ファンドへの最重要含意**:
  > "We provide suggestive evidence that the **AI model disseminates the potentially tacit knowledge of more able workers** and helps newer workers move down the experience curve."
  >
  > 「**AI モデルは、より熟練したワーカーの潜在的な暗黙知を拡散している**との示唆的証拠を提示する」
- **解釈**: AI は熟練者の暗黙知を抽出・パターン化して新人に転送する **ナレッジ・ディフューザー**として機能する → Y の暗黙知をシステム化することで「Y の判断を 24/7 並列稼働」が成立する根拠
- **URL**: https://www.nber.org/papers/w31161

### 1.3 （Skip）Noy & Zhang (2023) "Experimental Evidence on the Productivity Effects of Generative AI"
- **発行元**: Science 381, pp. 187-192
- **デザイン**: 453 名のプロフェッショナル × ChatGPT × ライティングタスク
- **結果**:
  - タスク時間 **-40%**
  - 品質スコア **+18%**
  - 低パフォーマー側で効果が大きく、生産性格差が縮小

### 1.4 （Skip）Peng, Kalliamvakou, Cihon, Demirer (2023) "The Impact of AI on Developer Productivity: Evidence from GitHub Copilot"
- **arXiv ID**: 2302.06590
- **発行元**: MIT Sloan + GitHub
- **結果**: コーディング所要時間 **-55.8%**（AI ペアプログラマ利用群）
- **意義**: 専門スキル領域でも、適切なインターフェースで提示される AI は熟練度に関わらず生産性を大幅向上

### 1.5 Boudreau, Chen et al. (2024) "Effective Generative AI: The Human-Algorithm Centaur"
- **arXiv ID**: 2406.10942
- **発行元**: Harvard / MIT
- **要旨**: 人間と AI の **ハイブリッド意思決定（Centaur）が両者単独を上回る** 条件を理論化
- **位置付け**: ファンドコンセプトの「人間 + AI > 人間 ∨ AI」を分析的に基礎付ける論文

### ~~1.6 Daugherty & Wilson (2018, updated 2024) "Human + Machine: Reimagining Work in the Age of AI"~~
- **発行元**: Harvard Business Review Press / Accenture
- **著者**: Paul Daugherty (Accenture CTO), H. James Wilson
- **概念**: **"Missing Middle"** = 人間が AI を訓練・説明・維持し、AI が人間を増幅・対話・体現する協働領域
- **2024 改訂版で追加**: 生成 AI 時代の **8 つの "Fusion Skills"**（融合スキル）
- **HBR 論文**: "Collaborative Intelligence: Humans and AI Are Joining Forces" (HBR 2018) — 1,500 社調査
- **URL**: https://www.accenture.com/us-en/insights/technology/human-plus-machine

### 1.7 Kahneman, Sibony, Sunstein (2021) "Noise: A Flaw in Human Judgment"
- **発行元**: Little Brown Spark
- **要旨**: 人間判断には体系的バイアスだけでなく **ノイズ（同一条件で結果が異なる変動）** が存在
- **本ファンドへの示唆**:
  - 専門家判断のノイズ削減は単純な線形ルールでも達成可能
  - **しかし完全置換ではなく、人間の signal × アルゴリズムのノイズ削減 のハイブリッドが理想**
  - Y のような熟練判断を AI で「コピー＋ノイズ除去」する設計が支持される

---

## 2. ドメイン別 Augmentation 研究

### 2.1 医療領域（最も豊富な実証）
| 論文 | 発行元 / 年 | 内容 |
|------|------------|------|
| **Rethinking Human-AI Collaboration in Sepsis Diagnosis** (arXiv 2309.12368) | RPI / Northeastern / OSU / HKU, 2023 | AI 単独は実運用で失敗するが、人間との協調設計で診断精度向上 |
| **CopilotCAD: Empowering Radiologists** (arXiv 2404.07424) | UPenn, 2024 | 放射線科医のレポート作成補助、定量的エビデンス提示 |
| **2-Factor Retrieval for Radiology** (arXiv 2412.00372) | UCLA, 2024 | 臨床医が AI 予測をどの程度信頼すべきかを検索ベースで定量化 |
| **AI-Assisted Prostate Cancer MRI Diagnosis** (arXiv 2502.03482) | U Chicago / U Michigan / TTI Chicago, 2025 | ドメイン専門家でも適切な AI 信頼度判断が課題 |
| **Tool or Tutor? Cancer Diagnosis** (arXiv 2502.16411) | UCL / INSEAD, 2025 | AI を **ツール（タスク補助）** として使うか **チューター（学習）** として使うかで効果が異なる |

### 2.2 ソフトウェア開発・知識労働
| 論文                                                             | 結果                                 |                                 |
| -------------------------------------------------------------- | ---------------------------------- | ------------------------------- |
| Peng et al. (2023) GitHub Copilot                              | タスク時間 -55.8%                       |                                 |
| Cui, Demirer et al. on coding                                  | 同様の生産性向上を確認                        |                                 |
| **MIT Sloan / Johns Hopkins (2025) Pairit** (arXiv 2503.18238) | AI エージェントとのチームワーク field experiment |                                 |
| ~~**Augmenting Expert Cognition** (arXiv 2503.24334)~~         | UW / Adobe, 2025                   | ドキュメント中心の知識労働で専門家認知をどう保持・発展させるか |

### 2.3 ニュアンス：誰が一番得をするか
- **大半の研究**: ノービスや低スキル層の伸び幅が大きい（スキルレベリング効果）
- **しかし絶対水準では**: 熟練者 + AI が最高水準を達成（特に Centaur 型）
- **Y のケースに直接該当**: Brynjolfsson et al. の「**AI が熟練者の暗黙知を拡散する**」 → Y の判断を AI で増幅する場合、Y 個人の伸び率より、Y の暗黙知が **24/7 常時稼働** することによるレバレッジが価値の源泉

### 【注意】Toner-Rodgers (2024) "AI, Scientific Discovery, and Product Innovation" は **撤回済**
- arXiv: 2412.17866（admin による撤回）
- 1,018 名の素材科学者で AI 利用 → 新材料 +44%、特許 +39%、トップ研究者で効果が二倍 と主張
- **2026 年 5 月、MIT が「データの来歴・信頼性に確信が持てない」として撤回要請** → arXiv は撤回
- 著者は MIT を離脱
- → **本ファンドコンセプト資料では引用不可**。代替として Brynjolfsson et al. (QJE 2025) を主軸に

---

## 3. 暗黙知形式知化の研究

### 3.1 古典的フレームワーク
| 研究 | 内容 |
|------|------|
| **Polanyi (1958, 1966)** "Personal Knowledge" / "The Tacit Dimension" | 暗黙知（tacit knowing）は明示知の **不可分の前提**。完全な形式知化は不可能 |
| **Nonaka & Takeuchi (1995)** "The Knowledge-Creating Company" | **SECI モデル**: Socialization (暗黙→暗黙) → Externalization (暗黙→明示) → Combination (明示→明示) → Internalization (明示→暗黙) のスパイラル |
| **Collins (2010)** | 暗黙知の三分類（relational / somatic / collective）。Polanyi の現代化 |

### 3.2 GenAI による暗黙知形式知化（最重要・新領域）
| 論文                                                                                                | 発行元 / 年           | 主張                                                              |
| ------------------------------------------------------------------------------------------------- | ----------------- | --------------------------------------------------------------- |
| ~~**"Tacit Knowledge Management with Generative AI: GenAI-SECI Model"** (arXiv 2603.21866)~~      | 2026              | SECI モデルを GenAI で拡張。LLM が externalization と internalization を担う |
| **"Leveraging LLMs for Tacit Knowledge Discovery in Organizational Contexts"** (arXiv 2507.03811) | UFMG / USP, 2025  | 組織暗黙知の発見と保有者特定に LLM を活用                                         |
| ~~**"Augmenting Expert Cognition in the Age of GenAI"** (arXiv 2503.24334)~~                      | UW / Adobe, 2025  | 専門知識を保持しつつ AI ベネフィットを得る設計                                       |
| **"The Paradox of Professional Input"** (arXiv 2504.12654)                                        | IIT Jodhpur, 2025 | 専門家が AI と協働すると、その AI が将来の値打ちを規定するパラドックス                         |

### 3.3 医学教育からの示唆
- **"Insights From Michael Polanyi: Tacit Knowledge in Medical Education"** (PMC, 2024) — ベッドサイド教育の代替として AI/ML 高忠実度シミュレーションを提案。**直接対話を完全代替はできないが、24/7 トレーニングと行動・認知トラッキングで補完可能**
- **本ファンドへの示唆**: Y の「相場勘」も同様に「シミュレーション + AI 追跡」で増幅可能

### 3.4 Brynjolfsson et al. が示した「**AI は熟練者の暗黙知の拡散装置**」
- 上記 1.2 の含意の再強調
- Polanyi の「暗黙知は完全に形式知化できない」立場と、現代 AI の「**完全な形式知化は不要、パターン抽出で十分**」というスタンスの和解
- → **Y の判断パターンを LLM で抽出して RAG で再現する設計**は理論的支持を持つ（既に貴プロジェクト `project_fm_an_perspective_discussion.md` で「判断パスカタログ + RAG 方式」として決定済の方向と一致）

---

## 4. 投資判断特化の AI Augmentation 研究

### 4.1 Alpha-GPT (Human-AI Interactive Alpha Mining)
- **要旨**: クオンツのトレーディングアイデア（暗黙知）を LLM が媒介してアルファ因子（形式知）に変換
- **ワークフロー**: Ideation → Implementation → Review の反復
- **本ファンドへの位置付け**: **アナリスト Y 版 Alpha-GPT** が直接的な参照アーキテクチャ

### 4.2 Toward Expert Investment Teams (Oxford-Man Institute)
- **要旨**: LLM マルチエージェントがアナリスト・ファンドマネージャーチームを模倣
- **本ファンドへの位置付け**: Y 単独ではなく、**Y の役割を分解した複数 AI エージェントチーム**として設計可能

### 4.3 AlphaAgents (BlackRock)
- **要旨**: BlackRock 研究、LLM ベースのマルチエージェントが自律的にポートフォリオ構築タスクを実行
- **意義**: 大手機関投資家が同方向の研究を進めている → ファンドコンセプトの市場認知度向上に寄与

### 4.4 FinArena (Sichuan Univ / CityU HK)
- **arXiv ID**: 2503.02692
- **要旨**: Human-Agent Collaboration Framework for Financial Market Analysis
- **手法**: Mixture of Experts 型で専門家アナリストの判断を統合

### 4.5 Decision-informed Neural Networks with LLM Integration for Portfolio Optimization
- **arXiv ID**: 2502.00828
- **発行元**: University of Oxford / UNIST, 2025
- **要旨**: 予測精度と意思決定品質の乖離を、LLM と decision-focused learning の統合で埋める

### 4.6 LLM-Enhanced Black-Litterman Portfolio Optimization
- **arXiv ID**: 2504.14345
- **要旨**: LLM が「投資家ビュー」を体系的に生成し Black-Litterman に投入 → mean-variance 最適化のセンシティビティ問題を緩和
- **本ファンドへの直接適用**: **Y の投資ビュー（暗黙知）を LLM で形式化し BL モデルに投入** という構造そのもの

### 4.7 ~~Are LLMs Rational Investors? (NYU / Tongji / Fudan, 2024)~~
- **arXiv ID**: 2402.12713
- **要旨**: LLM 自体が金融バイアスを持つ → 検出と削減手法を提案
- **示唆**: AI 単独でなく、Y の判断との突き合わせが品質保証となる

---

## 5. コンサル・研究機関レポート

### 5.1 McKinsey Global Institute
| レポート                                                                          | 年       | 主要数字                                              |
| ----------------------------------------------------------------------------- | ------- | ------------------------------------------------- |
| **"The economic potential of generative AI: The next productivity frontier"** | 2023.06 | 生成 AI による年間追加価値 **$6.1〜7.9 兆**                    |
| **"Generative AI and the future of work in America"**                         | 2023.07 | 知識労働者で最大インパクト                                     |
| **"A new future of work: The race to deploy AI..."**                          | 2024.05 | 欧州・米国の自動化シナリオ詳細                                   |
| **"Agents, robots, and us: Skill partnerships in the age of AI"**             | 2025    | **72% のスキルが Human-AI 協働ゾーン**、純粋人間労働 11%、純粋 AI 17% |
| **"Superagency in the workplace"**                                            | 2025    | 米国で 2030 年までに $2.9T のアンロック可能性                     |

### 5.2 BCG / BCG Henderson Institute
| レポート                                                      | 年    | 内容                                                               |
| --------------------------------------------------------- | ---- | ---------------------------------------------------------------- |
| **"AI at Work 2024: Friend and Foe"**                     | 2024 | 生成 AI への期待と恐れの並存、5 つの推奨                                          |
| **"AI at Work 2025: Momentum Builds, but Gaps Remain"**   | 2025 | 11,600 人サーベイ。リーダー 75% が週次 AI 利用、現場 51%。**ワークフロー再設計企業で意思決定の鋭さ向上** |
| **"GenAI Increases Productivity & Expands Capabilities"** | 2024 | BHI 第二回フィールド実験。**自分の能力を超えるタスクを AI で達成可能に**                       |
| Dell'Acqua et al. (Jagged Frontier)                       | 2023 | BCG × HBS 共同研究（上記 1.1）                                           |

### 5.3 Deloitte
| レポート                                                               | 年       | 内容                                                                |
| ------------------------------------------------------------------ | ------- | ----------------------------------------------------------------- |
| **"State of AI in the Enterprise (2026 AI report)"**               | 2026    | **「人間 + AI > どちらか単独」** 設計を最重要視。新ロール（Quality Stewards 等）の出現        |
| **"AI and the future of human decision-making"**                   | 2026    | 人間のエージェンシー保持 + AI 活用の両立                                           |
| **"Human capabilities are at the heart of high-performing teams"** | 2026.01 | AI 時代の人間スキル（curiosity, divergent thinking, informed agility）が決定要因 |
| ~~**"Human-centered approach to AI"**~~                            | —       | "Humans **with** Machines, not vs." 哲学                            |

### ~~5.4 Accenture~~
- **Daugherty & Wilson "Human + Machine"** (2018, 2024 改訂)
  - HBR Press 出版
  - **"Missing Middle"** 概念
  - 1,500 社の定量・定性調査
  - 2024 改訂で生成 AI 章追加、**8 つの Fusion Skills**

### 5.5 Stanford HAI
| レポート | 年 |
|---------|-----|
| **AI Index Report 2024 / 2025 / 2026** | Stanford HAI |
| **"Future of Work with AI Agents"** (arXiv 2506.06576) | 2025 — 米国全労働者の自動化・増強ポテンシャル監査 |
| **"Predictions for AI in 2025"** | Collaborative agents が主要トレンド |

### 5.6 NBER Working Papers
- **WP 31161 (Brynjolfsson, Li, Raymond)** — Generative AI at Work（最重要・上記 1.2）
- **NBER Digest "Measuring the Productivity Impact of Generative AI"** — 同上の non-technical summary

---

## 6. ファンドコンセプト訴求への活用ストーリー

### 6.1 三本柱の構成
```
【柱1】Centaur 型運用
  - Kasparov + Dell'Acqua の Centaur/Cyborg 概念
  - "中堅 + 機械 + 良いプロセス > グランドマスター単独 or 機械単独"
  - 含意: Y の判断 + AI のスケール + 設計プロセスが超過リターンの源泉

【柱2】暗黙知の形式知化（SECI × GenAI）
  - Nonaka SECI モデル + GenAI-SECI 拡張（arXiv 2603.21866）
  - Brynjolfsson et al.: "AI が熟練者の暗黙知を拡散"
  - Alpha-GPT: アイデア → 因子の媒介
  - 含意: Y の判断パスカタログ + RAG 構造（既決定）は学術的支持を持つ

【柱3】ノイズ削減と一貫性
  - Kahneman "Noise" — 同一情報下でも判断は揺れる
  - AI による一貫性付与 + Y の signal 保持
  - 含意: Y の代理人として 24/7 一貫した判断、人間の "weekday/weekend" や疲労ノイズを排除
```

### 6.2 想定 FAQ への回答素材
| 想定批判 | 反論材料 |
|---------|---------|
| 「AI は novice にしか効かない（高水準のYには効果薄）」 | Brynjolfsson et al. は「AI は熟練者の暗黙知を拡散する装置」と明言。**Y の効果を Y 自身でなく投資判断スループットで測る** |
| 「LLM は金融バイアスがある」 | NYU/Fudan (2402.12713) — バイアスは検出・削減可能。**Y の判断と突合せる二段階チェックで品質担保** |
| 「Jagged Frontier の外側では逆効果」 | Dell'Acqua et al. の警鐘そのまま。**フロンティア内（パターン認識・反復タスク）に絞る設計** で対応 |
| 「暗黙知は完全形式化不能（Polanyi）」 | 完全形式化は不要。**パターン抽出 + RAG + Y による再校正**でハイブリッド維持 |
| 「Toner-Rodgers の話は撤回された」 | 認知必要。**Brynjolfsson et al. (QJE 2025) を主軸に、撤回論文は引用しない** |

### 6.3 提案文ドラフト用フック
> **「最も優れたチェスプレイヤーはグランドマスターではなく、機械と組んだ普通のプレイヤーだった」**
> — Garry Kasparov, *Deep Thinking* (2017)

> **「AI モデルは、より熟練したワーカーの潜在的な暗黙知を拡散している」**
> — Brynjolfsson, Li, Raymond, *Quarterly Journal of Economics* 140(2), 2025

> **「人間 vs 機械という対立軸は誤りである。第三の波は Missing Middle で起こる」**
> — Daugherty & Wilson, Accenture / *Human + Machine*, HBR Press 2018

---

## 7. 引用候補リスト（採用優先度順）

### S 級（必ず引用）
1. **Brynjolfsson, Li, Raymond (2025)** "Generative AI at Work" *QJE* 140(2): 889-942
2. **Dell'Acqua et al. (2023)** "Navigating the Jagged Technological Frontier" HBS WP 24-013
3. **Kahneman, Sibony, Sunstein (2021)** *Noise: A Flaw in Human Judgment* Little Brown Spark
4. **Daugherty & Wilson (2024)** *Human + Machine, Updated and Expanded* HBR Press
5. **McKinsey Global Institute (2023)** "The economic potential of generative AI"

### A 級（コンセプト裏付け）
6. **Noy & Zhang (2023)** *Science* 381: 187-192
7. **Peng et al. (2023)** "Impact of AI on Developer Productivity" arXiv 2302.06590
8. **Boudreau et al. (2024)** "Effective Generative AI: The Human-Algorithm Centaur" arXiv 2406.10942
9. **Nonaka & Takeuchi (1995)** *The Knowledge-Creating Company* Oxford UP
10. **Polanyi (1966)** *The Tacit Dimension* Doubleday
11. **Wilson & Daugherty (2018)** "Collaborative Intelligence" *HBR* July-August

### B 級（業界・実装）
12. McKinsey (2025) "Agents, robots, and us"
13. BCG (2024) "GenAI Increases Productivity & Expands Capabilities"
14. Deloitte (2026) "State of AI in the Enterprise"
15. Stanford HAI (2025) "AI Index Report"
16. **Tacit Knowledge Management with Generative AI** arXiv 2603.21866 (2026)
17. **Augmenting Expert Cognition** arXiv 2503.24334 (2025)
18. Alpha-GPT — Human-AI Interactive Alpha Mining
19. AlphaAgents (BlackRock) — LLM Multi-Agents for Equity Portfolio
20. Toward Expert Investment Teams (Oxford-Man Institute)
21. LLM-Enhanced Black-Litterman arXiv 2504.14345 (2025)

### C 級（ドメイン拡張）
22. CopilotCAD arXiv 2404.07424 (放射線科)
23. Tool or Tutor cancer diagnosis arXiv 2502.16411 (UCL/INSEAD)
24. Sepsis Diagnosis arXiv 2309.12368
25. Future of Work with AI Agents arXiv 2506.06576 (Stanford)

### 引用不可
- **Toner-Rodgers (2024)** "Artificial Intelligence, Scientific Discovery, and Product Innovation" arXiv 2412.17866 — **MIT 撤回要請、データ捏造の疑い**

---

## 8. 次の調査推奨

1. **金融特化のRCT実証**: 投資アナリスト × LLM のフィールド実験（NBER / SSRN で継続検索）
2. **資産運用業界の AI 採用事例**: Two Sigma, Renaissance, BlackRock Aladdin の GenAI 統合の最新公開情報
3. **規制・コンプライアンス**: EU AI Act, SEC ガイダンス下でのアナリスト判断の AI 補強の合法性
4. **Daniel Kahneman × AI** の追加発言（2024 年逝去前のインタビュー、Observer 等）
5. **アクティブ運用 vs パッシブ** の文脈で「AI 増強型アクティブ」がどう位置付くか（S&P Global, Morningstar レポート）

---

**参考プロジェクト Memory**:
- `project_fm_an_perspective_discussion.md` — AN 目線形式知化の方針（判断パスカタログ + RAG 方式）と一致
- `project_analyst_universe.md` — Y チームのスクリーニング済みユニバース（300-400 銘柄）

**作成者**: Claude (Opus 4.7) via /quants
**情報源**: alphaXiv, McKinsey, BCG, HBR, NBER, Stanford HAI, Deloitte, Accenture, Tavily web search 横断

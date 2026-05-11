# 軸D: 競合分析 — Fundamental Law レンズで分類

**作成日**: 2026-05-11
**目的**: 既存ファンドを IC × BR 軸で分類し、Y × MAS（マルチエージェントシステム）の中央上位ポジショニングを論証
**位置付け**: 三核心2 — 業界証拠の第1柱（軸E「業界 IR 水準」につなぐ前段）

---

## エグゼクティブサマリ

**Fundamental Law of Active Management (Grinold–Kahn)**:
> IR ≒ IC × √BR

- **IC (Information Coefficient)**: 個々の予測の質。アナリストの「深さ・洞察」
- **BR (Breadth)**: 独立した予測の回数。クオンツの「広さ・銘柄数 × 頻度」
- **IR (Information Ratio)**: 期待される超過収益の安定性

純粋アクティブは IC 偏重で BR が小さく、純粋クオンツは BR 偏重で IC が薄い。Quantamental は両者の中間に位置するが、IC のソースは「ファクター × オルタナデータ」に留まる。**Y × MAS は IC ソースに「卓越したアナリストの判断パス」を投入することで、Quantamental よりさらに右上（高 IC × 高 BR）に位置するポジショニングを訴求する**。

### IC-BR 散布図（俯瞰）

```
                  HIGH IC（深い洞察）
                       ↑
                       |
   Berkshire ●         |         ★ Y × MAS（目標）
                       |       （Yの判断パス × 多銘柄並列）
   Capital Group ●     |
   Contrafund ●        |
                       |   Acadian ●
   T. Rowe ●           |   SAE (BlackRock) ●
                       |   PanAgora ●  AQR ●
   レオス・ひふみ ●    |
                       |   Robeco ●
                       |   Man Numeric ●
   スパークス ●        |
   ─────────────────────┼────────────────────→ HIGH BR（広さ）
                       |   ● Boosted.ai (ツール)
                       |   ● AlphaSense (ツール)
                       |
                       |   ● Numerai
                       |   ● Bridgewater Pure Alpha
                       |   ● 野村 / 大和 / AMOne クオンツ
                       |
                       |   ● Two Sigma  ● DE Shaw
                       |   ● Man AHL  ● WorldQuant
                       |   ● Renaissance Medallion
                       |
                  LOW IC（広く浅く）
```

### 主要発見

1. **Quantamental グループは「データ駆動の量的拡張」に終始**しており、特定アナリストの判断パスをモデル化したファンドは公開情報上ほぼ存在しない。
2. **Centaur/AI 増強型は「ツール提供」と「クラウドソース」の2形態**であり、特定の卓越したアナリストの暗黙知を中核に据えた運用ファンドは未踏領域。
3. **国内は AI / クオンツ単独運用が主流**で、AN 判断との明示的融合事例は乏しい。Y × MAS の差別化余地は大きい。

---

## 1. Quantamental グループ（中IC・中BR）

### 1.1 BlackRock Systematic Active Equity (SAE)

| 項目 | 内容 |
|------|------|
| URL | https://www.blackrock.com/ |
| 設立 | SAE 起源は 1985 年、Andrew Ang による Factor-Based Strategies は 2015 年〜（〜2024 年退任） |
| 運用残高 | Factor-Based Strategies グループ：$125B+（Ang 着任時 2015 年）／ SAE 全体は BlackRock 全体（$11T+）に組み込まれた巨大プラットフォーム |
| IC 源泉 | ファクター（バリュー、モメンタム、クオリティ、low vol）+ オルタナデータ（衛星画像、テキスト分析）+ AI による株式選別 |
| BR 源泉 | グローバル数千銘柄 × 高頻度リバランス |
| 訴求アングル | "Systematic investing combines insights from huge quantities of data, human expertise, and advanced computer modelling"（公式）— **「データ + 人間の専門性 + 高度モデル」の三位一体** |
| Y × MAS への含意 | SAE は "human expertise" を訴求するが、実態は **ファクター + データサイエンス**。卓越したアナリスト個人の判断パスをモデル化しているわけではない |

**重要引用** (BlackRock 公式 BGF Systematic Global Equity High Income Fund):
> "The big question we have been hearing from clients is, 'How can AI help us invest?'... With so many stocks in the global market, it's extremely difficult for human investors to analyze all the information available... That is where the benefit of AI come in"

**含意**: BlackRock は AI を **人間アナリストの「網羅性の壁」を超える道具** として位置付けているが、AN の判断軸そのものを継承する方向ではない。

### 1.2 Acadian Asset Management

| 項目 | 内容 |
|------|------|
| URL | https://www.acadian-asset.com/ |
| 設立 | 1986 年（ボストン、ロンドン・シンガポール・シドニー） |
| 運用残高 | **$196 billion**（2026年3月末） |
| IC 源泉 | 「市場は非効率である」前提のもと、独自データセット、ファンダメンタル + クオンツの融合 |
| BR 源泉 | **65,000銘柄を毎日分析**、120人以上の運用チーム |
| 訴求アングル | "Among the first firms in the world to apply data and technology to the systematic evaluation of global investments"／"Convergence of world-class talent, data-driven insights, and innovative tools" |
| 公開論文 | "Conviction, Concentration, and Quant"、"Machine Learning in Quant Investing: Revolution or Evolution?"（2019年）、"Investing with Big Data"（2017年） |

**Acadian の最大の特徴**: 「Systematic = 規律 × 広さ」を強調し、**集中型「高IC」運用に対する代替**として systematic extension strategies（long/short の活用）を訴求。**Y × MAS が掲げる「Y の深いIC × 銘柄広がり」というアングルとは方向性が逆**（Acadian は深いICよりも「広いがそこそこ深い」）。

### 1.3 AQR Capital Management

| 項目 | 内容 |
|------|------|
| URL | https://www.aqr.com/ |
| 設立 | 1998 年（Cliff Asness、Goldman Sachs Asset Mgmt 出身、Eugene Fama 弟子） |
| 運用残高 | **$189B 総運用**（2025年末、うちヘッジファンド $109.1B）／ AFI Hedge Fund Power List 2026 で世界1位 |
| 戦略 | Apex（multi-strategy, $6.8B, 2025 +19.6%）、Helix（trend, $5.7B）、Delphi（long-short equity, $6.8B, +16.8%）、Quantamental／Hybrid 戦略 |
| IC 源泉 | アカデミック・ファクター（value, momentum, carry, quality）+ テキスト分析 + 一部「ファンダメンタル」と「クオンツ」の融合 |
| BR 源泉 | 株式・債券・通貨・コモディティを横断的にシステマティック運用 |
| 訴求アングル | "Apply academic research to systematic factor investing"／"Quantitative + Discretionary/Hybrid strategies through a combination of quantitative and fundamental techniques"（ADV Brochure） |
| AI への態度 | Asness 公開発言（2026年3月）"We tend to really hate the last year of a bubble"（AI バブル懸念を表明） |

**重要**: AQR は **アカデミック因子 + テキスト分析** が中核で、アナリストの暗黙知の明示的モデル化は訴求していない。

### 1.4 Robeco Conservative Equities / Quant Equities

| 項目 | 内容 |
|------|------|
| URL | https://www.robeco.com/ |
| 設立 | Robeco は 1929 年、Conservative Equities は 2006 年（Pim van Vliet 主導） |
| 運用残高 | Conservative Equities シリーズ **$10B+** USD（公式） |
| IC 源泉 | low-volatility anomaly + 「integrated alpha factors」（高品質・収益安定企業へのファンダメンタル要素を統合） |
| BR 源泉 | グローバル株式 5,000銘柄をスクリーニング |
| 訴求アングル | "Low-volatility effect is perhaps the largest anomaly in finance"／**「下落耐性」と「長期コンパウンディング企業」へのアクセス** |
| 学術的裏付け | van Vliet & Blitz (2007) "The volatility effect", JPM |

**ポイント**: Robeco は「low-vol + integrated alpha」というファクター・アングルが鮮明で、AN の判断パスを取り込むモデルは未公開。

### 1.5 PanAgora Asset Management

| 項目 | 内容 |
|------|------|
| URL | https://www.panagora.com/ |
| 設立 | 1989 年（ボストン、Power Financial Corporation 傘下） |
| 運用残高 | 公開情報未確認（Form ADV の数値は文字化け／**要確認**） |
| IC 源泉 | "Contextual Alpha Modeling"（市場環境に応じて動的にファクターを再ウェイト）、業界レベル独自データ |
| BR 源泉 | Active Equity, Defensive Equity（low-vol risk-balanced）, Multi Asset（risk parity）の3本柱 |
| 訴求アングル | "Evolutionary Quantitative Investing"／"Merges traditional investment theory with quantitative techniques, using investment theory and portfolio manager experience as a foundation, while quantitative techniques verify, refine, and apply those ideas" |

**特筆**: PanAgora は明示的に **「ポートフォリオマネージャーの経験を基盤としてクオンツが検証・洗練・適用する」** と謳っている。Y × MAS のアングルと表面的に近いが、実際には「個人ファクターの設計参加」レベルにとどまる。

---

## 2. 純粋クオンツ（低IC・高BR）

### 2.1 Two Sigma

| 項目 | 内容 |
|------|------|
| URL | https://www.twosigma.com/ |
| 設立 | 2001 年（John Overdeck, David Siegel） |
| 運用残高 | **$110B**（Form ADV 2026-01）／ヘッジファンド AUM は $70B（2025年）から記録更新中 |
| 人員 | 約 1,700 名、250+ PhD、380+ PB のストレージ、世界トップ5級スーパーコンピュータ計算能力 |
| データ | 10,000以上のデータソース、48,000以上のシミュレーション/日 |
| IC 源泉 | 統計学習による短中期予測、アルファ・キャプチャ・システム（センチメント） |
| BR 源泉 | 統計アービトラージ、merger arb、event-driven、relative value、volatility arb、structured credit、sentiment |
| 訴求アングル | "Scientific approach to managing and investing capital across diversified global strategies" |

**2025-26 注目点**: 系統的ファンドが2026年Q1のボラ環境で multi-strategy ピア（Balyasny -4.3%、Citadel Wellington -1.9%）を上回るパフォーマンス。一方で系統的 vs ディスクレショナリーの分断が露呈し、アジア discretionary は -7.3%。

### 2.2 Renaissance Technologies

| 項目 | 内容 |
|------|------|
| URL | https://www.rentec.com/（限定情報） |
| 設立 | 1982 年（Jim Simons） |
| 運用残高 | **$92B**（SEC Form ADV 2025年3月）／約 $46B（AFI 2026 ヘッジファンド）|
| ファミリー | Medallion（社内限定、1988-2018で年率66%グロス、Sharpe>2.0、唯一の負け年は1989年）／ RIEF, RIDA, RIDGE（外部投資家向け、Medallion との乖離 17-19pt） |
| IC 源泉 | 短期統計アービトラージ、ノイズ・トレーディングの逆張り |
| BR 源泉 | 50.75% win rate × 高頻度執行 × 数千ポジション |
| 訴求アングル | "Statistical arbitrage at scale"／**Medallion は capacity 制約があるため外部 RIEF/RIDA/RIDGE はより穏当な戦略** |

**Y × MAS への含意**: Renaissance は **「BR の極致」**。AN 個人の IC は介在せず、純粋に数値パターン。Y のような卓越したファンダメンタル判断をモデル化する方向とは正反対。

### 2.3 D.E. Shaw

| 項目 | 内容 |
|------|------|
| URL | https://www.deshaw.com/ |
| 設立 | 1988 年（David E. Shaw、コロンビア大計算機科学教授） |
| 運用残高 | **$213B**（Form ADV 2026-03-31）／ AFI 2026 で $72B ヘッジファンド AUM（41% YoY 増） |
| 戦略 | systematic / discretionary / hybrid の3つを並列運用 |
| 注目動向 | **2025年9月、systematic を捨てて純ディスクレショナリー運用に振り切る "Cogence Fund" を $3-5B で組成** — クオンツ・キングが人間判断に回帰 |
| IC 源泉 | 計算機・物理アルゴリズム、最近は人間判断も再評価 |
| BR 源泉 | 数千銘柄 × 多戦略 |

**重要含意**: **DE Shaw が "Cogence Fund" で示したように、純クオンツの巨人ですら「人間の深い判断（高IC）」の価値を再評価している**。Y × MAS のテーゼは業界トレンドの方向性に沿う。

### 2.4 Man AHL / Numeric

| 項目 | 内容 |
|------|------|
| URL | https://www.man.com/ |
| Man Group 全体 | **$66.5B**（AUM, AFI 2026） |
| Man AHL | **$168.6B 総資産**（FY2024、レバレッジ込）／ revenue $1.46B／ Trend-following、EWMA crossover が中核（1987年〜） |
| Man Numeric | **$45.4B 総資産**（2023年9月末）／systematic equities、factor + ML |
| IC 源泉 | AHL: 価格・行動シグナル / Numeric: factor models + ML stock selection |
| BR 源泉 | AHL: グローバル先物・通貨・金利・コモディティ／ Numeric: 数千銘柄株式 |
| 訴求アングル | "Behavioral arbitrage at institutional scale"（AHL）／"Alpha first"（Numeric, motto since founding 1989 by Lang Wheeler） |

### 2.5 Bridgewater Pure Alpha

| 項目 | 内容 |
|------|------|
| URL | https://www.bridgewater.com/ |
| 設立 | 1975 年（Ray Dalio） |
| 運用残高 | **$78B**（AFI 2026、-12.9% YoY）／ Pure Alpha は absolute return 戦略 |
| 戦略 | Pure Alpha（1991年〜、年率高一桁% @ 12% vol target、32年間で負け年は4回のみ）／ All Weather（risk parity） |
| IC 源泉 | システマティック・ファンダメンタル・マクロ（経済レジーム × 因果関係） |
| BR 源泉 | 多資産・グローバル × 多レジーム判定 |
| 2026年特徴 | AIA Labs（AI Investment Associate Labs）を新設、AI が discretionary judgment を補完 |

**重要**: Bridgewater 自身が **「AI 資本ブームの理解」を投資テーマ化**しつつ、AI を運用判断の補助に用いる動きを明示している。

---

## 3. 純粋アクティブ（高IC・低BR）

### 3.1 Fidelity Contrafund / Will Danoff

| 項目 | 内容 |
|------|------|
| URL | https://fundresearch.fidelity.com/mutual-funds/summary/316071109 |
| 設立 | 1967 年（Danoff 就任 1990 年） |
| 運用残高 | Contrafund **$166.7B**（2025年6月末）／Contrafund 戦略全体 $248B+ |
| 集中度 | top holdings 10%超（Meta が一時 10%+）、Buffett の助言 "When you have a good idea, bet big" を契機に 2012 年以降コンセントレーションを強化 |
| パフォーマンス | 1990-2026 年率約14%（S&P500、Russell 1000 Growth を継続的に上回る） |
| IC 源泉 | **個人アナリスト判断（Danoff 単独 → 2025年4月以降 Weiner & Anolic 加入）**、Fidelity の業界アナリスト網との連携 |
| BR 源泉 | 数百銘柄（large-cap growth 中心）／高 conviction で集中 |
| 2025-26 動向 | Danoff は2026年末退任予定。**Fidelity 全体で Danoff（Contrafund）+ Wymer（Growth Co.）の2名で$500B+** — 高IC を個人判断に依存することの脆弱性が露呈 |

**Y × MAS への含意**: **Contrafund は「人間 IC の到達点」を示すが、属人性・後継問題が業界共通の課題**。Y × MAS はこの「個人IC の永続化・並列化」を技術的に解決する位置付けで訴求できる。

### 3.2 Capital Group / American Funds

| 項目 | 内容 |
|------|------|
| URL | https://www.capitalgroup.com/ |
| 設立 | 1931 年 |
| 運用残高 | グループ全体 **$3T 超** |
| 特徴 | **Multiple Manager System**（複数 PM が別々にスリーブを運用 → アンサンブル化）／ 個別 PM の判断を分散することで属人リスクを低減 |
| IC 源泉 | "Deep research capabilities and multiple manager system"（公式）／ 「rigorous research, individual accountability since 1931」 |
| BR 源泉 | 1社内多 PM × グローバル × 数百銘柄 |

**含意**: Capital Group は **「複数の人間 PM のアンサンブル」を制度化** している。Y × MAS の「Y の判断パス × MAS による並列化」と概念的に近いが、Capital Group は人間 PM そのものを使うのに対し、**Y × MAS は Y 一人の判断パスを AI でレプリケート・拡張する点で差別化**。

### 3.3 T. Rowe Price / Capital Appreciation

| 項目 | 内容 |
|------|------|
| URL | https://www.troweprice.com/ |
| 設立 | 1937 年 |
| 運用残高 | T. Rowe Price グループ全体 $1.5T 超（公開情報未確認、要再検証） |
| 旗艦 | Capital Appreciation Fund（David Giroux 主導、Morningstar Manager of the Decade 2010s） |
| IC 源泉 | アナリスト・ドリブン、ファンダメンタル深掘り |
| BR 源泉 | 中型ポートフォリオ（30-100銘柄） |

### 3.4 Berkshire Hathaway

| 項目 | 内容 |
|------|------|
| URL | https://www.berkshirehathaway.com/ |
| 運用残高 | 株式ポートフォリオ **$275B**（13F Q4 2025）／キャッシュ $344B（2025Q2） |
| 集中度 | **top 10 が 88%+ ／ Apple 単独 21%** |
| IC 源泉 | Buffett の判断（"Diversification is protection against ignorance. It makes little sense if you know what you're doing"） |
| BR 源泉 | 極めて小さい（保有銘柄は数十）|
| 訴求アングル | 究極の「IC 偏重」モデル — Fundamental Law の極端 |

**Y × MAS への含意**: Berkshire は IC の象徴。**Y × MAS は「Y の Buffett 級 IC × Acadian 級 BR」を目指す中央上位ポジショニングを明示できる**。

---

## 4. Centaur/AI 増強型新興

### 4.1 Numerai

| 項目 | 内容 |
|------|------|
| URL | https://numer.ai/ |
| 設立 | 2015 年（Richard Craib） |
| 運用残高 | **$550M**（2024年）／ 2025 年 Series C $30M（valuation $500M） |
| 仕組み | **クラウドソース**：全世界のデータサイエンティストが暗号化データで予測を提出 → NMR トークンでステーキング → メタモデルがアンサンブル |
| 2024 リターン | **+25.45% net**（市場ボラ環境下） |
| 訴求アングル | "Final Hedge Fund"／decentralized, AI-driven, crowd-sourced |
| IC 源泉 | 数千モデルの集合知（弱IC × 多数） |
| BR 源泉 | 数千モデル × 全銘柄 |

**Y × MAS との対比**: Numerai は **「匿名 crowd の集合知」**。Y × MAS は **「特定の卓越したアナリスト1人の判断パス」**。方向性が真逆。

### 4.2 Boosted.ai

| 項目 | 内容 |
|------|------|
| URL | https://boosted.ai/ |
| 設立 | 2017 年（トロント、Joshua Pantony / Jon Dorando / Nicholas Abe） |
| 利用顧客 | **180+ asset managers 世界最大級** |
| 提供物 | Boosted Insights 3.0（generative AI 投資アシスタント）、Alfa（agentic AI platform）／40時間のアナリスト作業を **20分に短縮** |
| ポジション | **ツール提供** — ファンド運用は行わない |
| 訴求アングル | "AI co-worker that users can train to think like them"／"Mirrors your thinking" |

**重要**: Boosted.ai は **「個別 PM の思考パターンを学習する」** と謳い、Y × MAS と最も近い思想を持つ競合。ただし **ツール提供** であり、特定アナリストの判断パスを基盤に組成されたファンドではない。Y × MAS は「Boosted.ai 的ツールを Y に特化して内製＋ファンドとして運用」というポジショニングが可能。

### 4.3 AlphaSense

| 項目 | 内容 |
|------|------|
| URL | https://www.alpha-sense.com/ |
| 設立 | 2011 年 |
| 利用顧客 | 3,500+ enterprise customers（S&P500 多数） |
| 提供物 | Generative Search、Generative Grid、Deep Research、500M+ premium documents（broker research, expert calls, filings, news, internal docs） |
| ポジション | **リサーチ補助** — ファンド運用は行わない |
| 訴求アングル | "Analyst-level insights at speed"／"Fully automate end-to-end market intelligence workflows" |

**含意**: AlphaSense は **アナリスト作業の効率化**。Y × MAS のテーゼ（Y の判断軸を AI で並列稼働）とは別軸。

### 4.4 WorldQuant

| 項目 | 内容 |
|------|------|
| URL | https://www.worldquant.com/ |
| 設立 | 2007 年（Igor Tulchinsky、Millennium 元 PM） |
| 運用残高 | 公開情報未確認（Millennium 顧客資金中心） |
| 特徴 | "Alpha factory"（多数の researchers が "alphas" を生産・組み合わせ）／ WorldQuant University で世界中から人材確保 |
| IC 源泉 | 多数のリサーチャーが小さなアルファを発見 → 統合 |
| BR 源泉 | 数千〜数万のアルファシグナルを統合 |

**Y × MAS との対比**: WorldQuant は **「リサーチャー大量動員」モデル**。Y × MAS は **「卓越した1人の判断パスを MAS でスケール」モデル**。

### 4.5 Voya Investment Management（旧 ING / VOYA AI）

| 項目 | 内容 |
|------|------|
| URL | https://institutional.voya.com/ |
| 運用残高 | $350B+（公開情報未確認、要再検証） |
| AI 戦略 | Machine Intelligence 部門（Vincent Costa）が AI/ML を 株式運用に統合 |

NN Investment Partners は Voya からスピンオフし、現在は **Goldman Sachs Asset Management** に統合（2022年買収完了）。元 NN IP の "AI Driven Equities" シリーズは Goldman Sachs QIS（Quantitative Investment Strategies）チームに継承。

---

## 5. 国内運用機関

### 5.1 野村アセットマネジメント

| 項目 | 内容 |
|------|------|
| URL | https://www.nomura-am.co.jp/ |
| 設立 | 1959 年 |
| 運用残高 | **108.4兆円**（2025年12月末、業界トップ） |
| AI / クオンツ | 日本初のアクティブ運用型ETFを設定／スマートベータ・AI 銘柄選定ファンドあり |
| ポジション | **総合運用会社** — AI / クオンツは1つのスリーブ |
| 国内 ETF 残高シェア首位、UCITS ファンド 2.1兆円 |

**Y × MAS への含意**: 野村は AI / スマートベータを「商品の1つ」として位置付けており、「AN 暗黙知 × MAS」の中核訴求は未踏。**シード期向け差別化余地大**。

### 5.2 大和アセットマネジメント

| 項目 | 内容 |
|------|------|
| URL | https://www.daiwa-am.co.jp/ |
| クオンツ運用 | ベータ・ソリューション運用部（飯田尚宏チームリーダー、運用経験18年9ヶ月） |
| 戦略 | クオンツアクティブ運用、テーマ型ファンドのアロケーション戦略運用 |
| 主要ファンド | iFree シリーズ、ダイワつみたて、マルチアセット戦略ファンド |
| 大和ファンドコンサルティング | 2024 ファンド評価で「**国内クオンツは3年連続マイナス超過リターン**、バリュー因子有効性低下、オルタナデータ活用に期待」と公式発言 |

**重要発言**:
> 「クオンツ運用とジャッジメンタル運用のどちらが優れているかを単純に比較することは適切ではない。それぞれに長所と短所があることに加えて、両運用のリターン相関は低い傾向が見られることから、ポートフォリオのリスク・リターン特性を向上させるために、両運用を適切に配分することが重要」（大和ファンド・コンサルティング 堀内シニアアナリスト）

**Y × MAS への含意**: **国内大手 FoF/ファンド評価機関は「クオンツ × ジャッジメンタル の組み合わせ」を明示的に推奨**しており、Y × MAS の単一ファンド内融合は需要に合致する。

### 5.3 アセットマネジメントOne

| 項目 | 内容 |
|------|------|
| URL | https://www.am-one.co.jp/ |
| 関連プロダクト | **「AI（人工知能）活用型世界株ファンド（ディープAI）」** を公開／マルチアセット・クオンツ運用部（澤頭寛 共同部長、20年以上の運用経験、NY 時代の2007年からクオンツ） |
| 体制 | CIO 制導入、株式運用部 / 債券運用部 / マルチアセット・クオンツ運用部、サステナブル投資戦略部、フィナンシャルイノベーション部 |
| 特徴 | ジャッジメンタル + クオンツ + マルチアセットの3本柱を統合 |

### 5.4 スパークス・グループ

| 項目 | 内容 |
|------|------|
| URL | https://www.sparx.jp/ |
| 設立 | 1989 年（阿部修平、George Soros 弟子） |
| 運用残高 | **1兆8,720億円**（2025年3月末） |
| パフォーマンス | 営業利益率 **43.0%**（同業 SBI レオス 18.1%、SBIGAM 19.6% を大きく上回る） |
| 戦略 | 日本株アクティブ（ロング・ショート戦略を日本に初導入）、実物資産、プライベートエクイティ |
| 訴求 | 「マクロはミクロの集積である」「徹底した現場主義」 |
| 成功報酬付帯ファンド 35.1% — performance-linked モデル |

**Y × MAS への含意**: スパークスは **国内純粋アクティブの代表格**。AN 暗黙知の体系化は明示していないが、**「現場主義 = 高IC を訴求点とする独立系運用」のカテゴリの先行者**として参照に値する。

### 5.5 レオス・キャピタルワークス（ひふみ）

| 項目 | 内容 |
|------|------|
| URL | https://www.rheos.jp/ |
| 設立 | 2003 年（藤野英人） |
| 運用残高 | **1兆7,000億円**（2026年2月10日、過去最高） |
| 直販残高 | 2,795億円（2026年1月末、112販売パートナー） |
| 戦略 | 「守りながらふやす」アクティブ運用／日本株中心 |
| ブランド戦略 | 「顔の見える運用」「企業との対話」（フィスコレポートより） |

**Y × MAS への含意**: ひふみは **「顔の見える運用」で個人投資家のアクティブ需要を獲得**。Y × MAS は機関投資家×シード期向けで、ターゲット層は被らないが、**「個人 PM のブランド × 集中型運用」が国内で受容される証左**。

---

## 6. IC-BR 散布図（テキスト/ASCII で詳細）

```
                                  HIGH IC
                                     ↑
   3.4 Berkshire ●                   |              ★ ★ ★
   (Buffett, conc.88%)               |          ★ Y × MAS（目標位置） ★
                                     |        「Y の Buffett 級 IC ×
   3.1 Contrafund ●                  |         Quantamental 級 BR」
   (Danoff, $166B, top1=10%)         |        ★ ★ ★
                                     |
   3.2 Capital Group ●               |
   (Multi PM, $3T)                   |               ● 1.2 Acadian
                                     |               ($196B, 65K stocks)
   3.3 T. Rowe Price ●               |
                                     |       ● 1.1 BlackRock SAE
   5.4 スパークス ●                  |       ($125B+)
   (1.87兆、独立系)                  |       ● 1.5 PanAgora
                                     |       ● 1.3 AQR ($189B)
   5.5 ひふみ ●                      |
   (1.7兆、ブランド型)               |               ● 1.4 Robeco
                                     |               (low-vol, $10B+)
                                     |
                                     |       ● 4.2 Boosted.ai (ツール)
                                     |       ● 4.3 AlphaSense (ツール)
                                     |
   ─────────────────────────────────┼──────────────────────────────→ HIGH BR
                                     |
                                     |       ● 5.3 AMOne
                                     |       (ディープAI ファンド)
                                     |       ● 5.1 野村 / 5.2 大和
                                     |       (AI銘柄選定/クオンツアクティブ)
                                     |
                                     |       ● 2.5 Bridgewater Pure Alpha
                                     |       ($78B, AIA Labs)
                                     |
                                     |       ● 4.1 Numerai
                                     |       (crowd-sourced, $550M)
                                     |
                                     |               ● 4.4 WorldQuant
                                     |               (alpha factory)
                                     |
                                     |       ● 2.4 Man AHL ($168B)
                                     |       ● 2.4 Man Numeric ($45B)
                                     |
                                     |       ● 2.1 Two Sigma ($110B)
                                     |       ● 2.3 DE Shaw ($213B)
                                     |       ● 2.2 Renaissance Medallion
                                     |       (社内限定、66% gross)
                                     ↓
                                  LOW IC
```

### 散布図の解釈

1. **右上のスペース（高IC × 高BR）は実質的に空白** — そこに Y × MAS が入る
2. Quantamental グループ（中央右）は **「中IC × 中BR」** に密集
3. 純粋アクティブ（左上）は **集中度が高く、属人リスクを抱える**
4. 純粋クオンツ（右下）は **BR で勝負、IC は薄い**
5. **Centaur ツール（Boosted.ai, AlphaSense）は IC を補助するが、それ自体はファンドではない**

---

## 7. ファンドコンセプトへの含意

### 7.1 差別化ナラティブ（Y × MAS 訴求の核）

| 競合カテゴリ | 競合の強み | Y × MAS の差別化 |
|------------|----------|----------------|
| Berkshire / Contrafund | 高IC、長期実績 | **属人性を克服**：Y の判断パスをモデル化し、後継問題を解消 |
| Capital Group | Multi-Manager System | **AI で「Y を多重化」**：人間 PM ではなく Y の暗黙知 + MAS で並列化 |
| Acadian / BlackRock SAE | データ駆動、$196B 規模 | **IC ソースが違う**：ファクター/オルタナデータではなく「卓越した AN の判断軸」 |
| AQR | アカデミック因子 | **暗黙知の SECI 形式知化**：論文化されていない実務的判断軸を活用 |
| Two Sigma / DE Shaw | 純粋クオンツ、計算機資源 | **DE Shaw が "Cogence" で discretionary に回帰した動向と一致**：純クオンツの限界を Y で補う |
| Bridgewater AIA Labs | AI が discretionary を補完 | Y × MAS は **AN を中核に据え、AI を補助に位置付け**：逆方向 |
| Boosted.ai | 「Mirror your thinking」ツール | **ツール提供ではなくファンド組成**：単一の卓越したアナリスト Y に特化、外販ではなく内製 |
| Numerai | クラウドソース集合知 | **匿名群衆ではなく特定の卓越した個人**：IC の質を妥協しない |
| 国内 AI/クオンツ（野村/大和/AMOne） | 国内営業力 | **AN 判断との明示的融合は国内に存在しない** — シード期向けで先行優位確保可能 |
| ひふみ / スパークス | 顔の見える運用 | **機関投資家×シード期** にターゲット集中、個人マーケ不要 |

### 7.2 競合排除ロジック

**Y × MAS が独占的に主張できるポジション**：

1. **「Y 個人の Buffett 級 IC × Quantamental 級 BR」** — IC-BR 平面の右上スペース
2. **「暗黙知の SECI 形式知化 + マルチエージェント並列稼働」** — Boosted.ai 思想 × ファンド組成
3. **「特定アナリストの判断パスをコア IP として運用」** — Capital Group の Multi-Manager 思想 × AI レプリケーション
4. **「DE Shaw の "Cogence" 動向に呼応する次世代型」** — クオンツ業界自体が discretionary 価値を再評価する中、AN 中核設計を先取り

### 7.3 業界圧力との合致

- **AQR Asness の AI バブル懸念** → 純AI 依存ではなく AN 主導が逆張りで合理的
- **大和ファンドコンサル「クオンツ × ジャッジメンタルの組み合わせ」推奨** → 機関投資家ニーズと合致
- **Contrafund Danoff 退任後の属人性問題** → Y × MAS の「暗黙知の永続化」ナラティブが時流に合う

---

## 8. 未調査・継続調査推奨

| 項目 | 理由 | 次のアクション |
|------|------|--------------|
| PanAgora AUM 詳細 | Form ADV データが取得できず | Form ADV を直接取得 |
| T. Rowe Price 旗艦ファンド AUM | 公開情報の確認 | TROW 10-K と Capital Appreciation Fund のファクトシート |
| Voya Investment / NN IP の AI 戦略 | NN IP → Goldman 統合後の動向不明 | Goldman QIS の最新情報 |
| WorldQuant 顧客資金規模 | 非公開 | Millennium 13F + 関連報道 |
| Acadian の Y 型アングルへの近さ | "Conviction, Concentration, and Quant" 論文の内容深掘り | 該当 PDF を入手・精査 |
| Bridgewater AIA Labs の詳細 | 2026 年立ち上げで情報限定 | Greg Jensen の公開発言追跡 |
| Capital Group の Multi-Manager System の人数・体制 | 不明 | 公式採用ページ・Annual Report |
| 国内アナリストドリブン投信（さわかみ、コモンズ） | 1次調査対象外 | 機関投資家×シード期との関係を再評価 |
| ピクテ Quest AI | クオンツ2.0 と称する点が興味深い | 独立調査・対比 |
| BNP Paribas AM の「ホワイトボックス」訴求 | AI を「銘柄選択ツールではない」と明示 | 立論補強の引用元 |
| Acadian の "Machine Learning in Quant Investing"（2019） | 業界視点の整理に有用 | 学術論文として深読み |

---

## 9. 主要競合の訴求アングル比較表

| ファンド | カテゴリ | 訴求の核 | AN 判断の扱い |
|---------|---------|---------|--------------|
| BlackRock SAE | Quantamental | データ × 人間専門性 × モデル | ファクター設計者として |
| Acadian | Quantamental | 65K銘柄 × 体系的評価 | チーム判断（個人ではない） |
| AQR | Quantamental | アカデミック因子 + Quantamental hybrid | 補助的 |
| Robeco Conservative | Quantamental（low-vol特化） | low-vol anomaly + integrated alpha | 学術モデルベース |
| PanAgora | Quantamental | Contextual Alpha + PM経験 | 「PM経験をクオンツが検証」 |
| Two Sigma | 純クオンツ | Scientific approach + 1700名・48K simulations/日 | 介在せず |
| Renaissance Medallion | 純クオンツ（極致） | Statistical arb at scale | 介在せず |
| DE Shaw | 純クオンツ → discretionary 回帰 | systematic + discretionary + hybrid | **Cogence Fund で discretionary 復権** |
| Man AHL | 純クオンツ trend | Behavioral arbitrage | 介在せず |
| Bridgewater Pure Alpha | systematic-fundamental macro | 経済レジーム × 因果 + AIA Labs | discretionary 主導 |
| Contrafund | 純アクティブ | Will Danoff の判断 × Fidelity リサーチ網 | **中核 IP（属人）** |
| Capital Group | 純アクティブ | Multiple Manager System | **複数人のアンサンブル** |
| T. Rowe Price | 純アクティブ | Analyst-driven, deep research | 中核 |
| Berkshire | 純アクティブ（究極） | Buffett の判断、集中、長期 | **究極の中核** |
| Numerai | Centaur（crowd） | クラウドソース集合知 | 匿名群衆 |
| Boosted.ai | Centaur（ツール） | "Mirror your thinking" agentic AI | ツールとして補助 |
| AlphaSense | Centaur（ツール） | analyst-level insights at speed | ツールとして補助 |
| WorldQuant | Centaur（alpha factory） | 多数リサーチャーの alpha 統合 | リサーチャー大量動員 |
| 野村スマートベータ/AI | 国内 Quantamental | データドリブン銘柄選定 | 介在せず |
| 大和クオンツ | 国内 純クオンツ | ベータソリューション、クオンツアクティブ | チーム運用 |
| AMOne ディープAI | 国内 AI型 | 深層学習で世界株選定 | クオンツチーム |
| スパークス | 国内 純アクティブ | 現場主義、L/S戦略 | 中核（阿部修平の哲学） |
| レオス ひふみ | 国内 純アクティブ | 顔の見える運用、企業対話 | 中核（藤野英人） |
| **★ Y × MAS** | **AI増強型アクティブ** | **Y の暗黙知 × MAS による IC×BR 同時最大化** | **中核 IP として永続化・並列化** |

---

## 10. 軸E（業界IR水準）に渡すデータポイント

軸E（業界 IR水準）の論証で使えるデータ:

1. **Acadian $196B、35年以上の運用実績** — systematic active equity の業界水準 IR ベンチマーク
2. **Renaissance Medallion は66%グロス・Sharpe>2.0** だが capacity 制約で外部不可、RIEF/RIDA は Sharpe 0.57-0.85（ABC Quant データ）
3. **Bridgewater Pure Alpha** 32年で負け年4回のみ、年率高一桁% @ 12% vol target → IR ≒ 0.6-0.8 推定
4. **AQR Apex 2025年 +19.6%、Helix +18.6%、Delphi +16.8%** — 同年の市場環境込みの近年実績
5. **Contrafund 1990-2026 年率14%** vs S&P500 → 長期 IR の純アクティブベンチマーク
6. **Two Sigma 2026Q1**: systematic ファンドが pure long/short discretionary（アジア -7.3%）を上回る
7. **AI による生産性向上の業界水準**: Boosted.ai が40時間→20分（120倍効率）、これを IR=IC×√BR の BR 拡張根拠として活用可能
8. **国内クオンツの3年連続マイナス超過リターン**（大和ファンドコンサル）— 国内純クオンツ単独の限界を示す業界統計
9. **DE Shaw "Cogence Fund" $3-5B 組成**（2025年9月）— クオンツ巨人の discretionary 回帰、IC 価値の業界再評価
10. **AFI Top 20 Power List 2026**: AQR ($189B), Man Group ($66.5B), DE Shaw ($72B HF), Two Sigma ($50.7B HF), Renaissance ($46B), Bridgewater ($78B) — システマティック陣営の業界規模感

---

**作成完了**: 2026-05-11
**次の軸**: 軸E（業界IR水準の数値化）／軸F（シード期 LP の競合資金配分パターン）

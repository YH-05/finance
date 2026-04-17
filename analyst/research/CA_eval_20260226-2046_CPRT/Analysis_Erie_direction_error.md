# Erie Insurance 方向誤記の原因分析

> **対象レポート**: `04_output/revised-report-CPRT.md`（ca-eval_20260226-2046_CPRT）
> **作成日**: 2026-04-17
> **起点**: Yによるフィードバック（`Feedback_CPRT.md` その他セクション）

---

## 1. 事象

revised-report-CPRT.md の主張#3（スイッチングコスト）懸念点に以下の記述がある。

> **懸念点**: RB Global面談（2025/10）で「rebateや接待でシェア奪還」を目指す姿勢が示されている。**Erie InsuranceのRB→CPRT移行**もスイッチが「起きうる」ことの証拠。（line 135）

Yからの指摘:

- 原典では Erie Insurance は **CPRT→RB** の方向でスイッチしている（RB Global面談でRB側が証言した獲得事例）
- AIは面談記録の「当社」を RB ではなく CPRT と誤解しているのではないか
- 仮に "RB→CPRT" が正しかったとしても、CPRTにとって顧客**獲得**イベントであり「懸念点」に置くのは論理的に破綻している

本ドキュメントは、この誤記が発生した経路と根本原因を工程別にトレースした結果をまとめる。

---

## 2. 原典の事実関係

`analyst/research/raw/CPRT US.md` における該当箇所:

- **line 11**: セクション見出し「10/3/25 米国出張@2025/9」
- **line 13**: サブ見出し「**20 RB Global**」
- **line 15**: 面談者「Eric Guerin CFO, Sameer Rathod VP of IR」（RB Global側の人物）
- **line 37**: （シェアをパリティにする力学についてどう考えるのか?）という問いに対するRB側の回答
- **line 38**:

> 事実として、Erie Insurance も競合の 50%シェアを**当社**に移して、**当社独占**の状況になった。

このコンテキストでの主語対応:

| 指示語 | 実体 |
|--------|------|
| 当社 | **RB Global（IAA）** — 面談相手 |
| 競合 | **CPRT** |

したがって原典の事実は **「Erie Insurance は CPRT（競合）→ RB Global（当社）に50%シェア移管」=CPRTからの流出（競合への奪取）** である。

---

## 3. 誤記の伝播経路

### 3.1 各ステージでの Erie 言及回数

| Stage | 担当エージェント | モデル | Erie 登場数 | S3=「RB Global面談」の文脈保持 |
|-------|----------------|--------|-------------|-----|
| 原典 `raw/CPRT US.md` | - | - | 1 | ✅ line 13「20 RB Global」見出し |
| T2 `parsed-report.json` | ca-report-parser | Sonnet | 0 | ✅ S3.title="米国出張@2025/9 RB Global面談メモ" |
| T4 `claims.json` | ca-claim-extractor | Sonnet | 0 | ⚠️ 「rebateで奪還」のみ残存、Erie脱落 |
| T5 `fact-check.json` | ca-fact-checker | Sonnet | 0 | - |
| T6 `pattern-verification.json` | ca-pattern-verifier | Sonnet | 0 | - |
| **T7 `draft-report.md`** | **ca-report-generator** | **Sonnet** | **1（方向反転）← 初出** | **❌ 失われた** |
| T8 `critique.json` | ca-eval-lead (Lead) | Opus | 2（継承） | ❌ 継承 |
| T8 `revised-report-CPRT.md` | ca-eval-lead (Lead) | Opus | 2（継承） | ❌ 継承 |

### 3.2 T7 の入力設計

`.claude/agents/ca-report-generator.md` の入力ファイル仕様:

| 必須入力 | 内容 |
|---------|------|
| claims.json (T4) | 主張 + ルール評価 |
| fact-check.json (T5) | 事実検証 |
| pattern-verification.json (T6) | パターン照合 |
| dogma_v1.0.md, KB1 rules | 判断軸 |

**`parsed-report.json` も `raw/CPRT US.md` も入力に含まれていない**にもかかわらず、T7 の draft-report.md で Erie Insurance（claims.json にも fact-check.json にも存在しない固有名詞）が出現。

---

## 4. エージェント境界での文脈喪失

### 4.1 問題①: T4→T7 間での構造化データの粒度不足（本質的原因）

- T4 ca-claim-extractor は S3（RB面談）から「rebate奪還」しか抽出しておらず、Erie 事例を構造化データに落とさなかった
- T7 ca-report-generator は narrative 肉付け（「懸念点」セクションの具体例）のために**仕様外で raw を直接参照せざるを得ず**、その時点で章見出しという文脈情報（S3=RB Global面談）を失った
- **構造化データに乗らなかった情報は、後段エージェントが raw に降りて拾い直す時点で主語情報が剥落する**

### 4.2 問題②: T7（Sonnet）→ T8（Opus）の非対称な責任分担

- T7（Sonnet）が raw を読んで narrative を生成
- T8（Opus）は draft と structured input のみを批判対象とし、**raw への再突合を行わない**
- モデル能力差（Opus の判断力）が活きる前に、Sonnet 由来の事実誤認が固定化する
- T8 は critique.json の `kb_reference` でむしろ誤った方向を KB 整合性の根拠として**強化**した（「KB1ルール10の双方向性」として誤方向を正当化）

---

## 5. 論理破綻: 懸念点への配置

### 5.1 AIが書こうとした論旨の構造

T8批判の狙いは「スイッチングコストは絶対的ではない」という反例を提示することであり、対比構造は以下のはずだった:

| 方向 | 事例 | 主張への寄与 |
|------|------|-------------|
| **IAA→CPRT**（CPRT獲得） | GEICO | 「スイッチは稀だから優位性の証拠」（KB1ルール10 正方向） |
| **CPRT→RB**（CPRT喪失） | **USAA喪失** | 「スイッチも起きうるから絶対ではない」（KB1ルール10 逆方向＝懸念点） |

CPRTにとっての懸念点は **CPRT→RB方向**の流出事例でなければならない。実際 raw には USAA 喪失（line 40「USAA をロスしたとき」）があり、この方向性は正しく拾われている。

### 5.2 AIが実際に書いた論理破綻

revised-report line 135:

> 懸念点: ... **Erie InsuranceのRB→CPRT移行**もスイッチが「起きうる」ことの証拠

critique.json line 37:

> GEICOのIAA→CPRTスイッチはスイッチの稀少性の裏付けだが、**Erie InsuranceのRB→CPRTスイッチ、USAAの喪失事例**は逆にスイッチが起きうることの証拠

ここには**3つの矛盾**が同居している:

#### 矛盾① 同方向の事例を対極の証拠として扱っている

GEICO「IAA→CPRT」と（誤記の）Erie「RB→CPRT」は**同じ方向**（他社→CPRT）。同方向の事象が「稀少の証拠」と「頻発の証拠」を同時に示すことは論理的に不可能。

#### 矛盾② 異方向の事例を並列列挙している

「Erie RB→CPRT」（CPRTの獲得）と「USAAの喪失」（CPRTの損失）は**真逆の方向**なのに、critique.json では同じセンテンスで並列に「起きうる証拠」として列挙されている。

#### 矛盾③ 獲得事例を懸念点に配置している

**RB→CPRT移行=CPRTの顧客獲得**であり、スイッチングコストの**強さを示す好材料**。これを「懸念点」に置くのは、結論と証拠の符号が逆転。

### 5.3 なぜAIは気付かなかったか

**字面の「スイッチ」をイベント種別として抽象化し、方向性の意味論チェックを省略したため**。推論ステップを分解すると:

1. 「スイッチングコストが絶対的でないことを示す反例が必要」（narrative 要件）
2. raw から「スイッチ」を含む文を検索 → Erie 事例をヒット
3. "RB→CPRT" と "CPRT→RB" の違いを、どちらも「スイッチ」トークンとして等価に扱う
4. GEICO（IAA→CPRT）が既出で「稀少の証拠」扱いなので、Erie は「反対の証拠」として "逆に" の接続詞で貼り付け
5. 「懸念点」セクションに配置するとき、**「その事例がCPRTにとって得か損か」の影響評価を実行していない**

手順5が致命的。LLMは「懸念点＝スイッチが起きる証拠」という**語彙レベルの型**で埋めてしまい、「CPRTが顧客を得るイベントは懸念足り得ない」という**因果の符号検証**を走らせていない。

---

## 6. 根本原因: 3つのレベルの区別

| 現象 | 定義 | Erie事例での現れ方 |
|------|------|--------------------|
| **① 字面（lexical）解釈** | トークン一致で判定、意味論や方向性を見ない | 「スイッチ」という語があれば、RB→CPRTでもCPRT→RBでも同じ「switch event」として抽象化 |
| **② 字面（literal）KB適用** | KBのルール文を表面的に適用、前提条件を検証しない | KB1ルール10「双方向性」を「スイッチ事例が2つあればOK」と解釈し、方向が噛み合っているかを検証しない |
| **③ narrative駆動** | 章構成・テンプレートのスロットを埋めることが目的化し、素材の妥当性検証が後回しになる | 「懸念点」セクションに「何か反例」を入れる必要がある→Erie事例を素材として投入→得失の符号チェックを省略 |

### 6.1 本件での関係性

- **③ narrative駆動** = スロットを埋めにいく生成モード（主犯）
- **② KB字面解釈** = スロットに入れる素材を検証しない運用モード（共犯）
- **① 字面解釈** = 素材の個別解釈段階での誤り（誤読の直接原因）

③の narrative スロット充填と②の KB 機械適用が噛み合って、①で起きた方向誤読を止められなかった。KB の字面適用は本来③の暴走を止める**ガードレール**の役割を持つべきだが、今回はガードレール自体が字面で運用されて機能しなかった。

---

## 7. 改善提案

| 改善案 | 対象 | 内容 |
|-------|------|------|
| **A. T2 parser の粒度強化** | ca-report-parser | S3 の本文を `source_text` に含め、節見出し（speaker=RB Global CFO 等）を明示的にタグ付け |
| **B. T4 extractor の網羅性** | ca-claim-extractor | スイッチングコスト関連で GEICO だけでなく Erie/USAA 等のネガティブ事例も factual_claims として抽出し、方向属性（direction: `gain` / `loss`）を必須フィールド化 |
| **C. T7 の raw 参照禁止** | ca-report-generator | 入力ファイルを構造化データに限定し、raw が必要な記述は T4 に pipe back する |
| **D. T8 critique に出典突合ステップ追加** | ca-eval-lead | 批判対象の事実について、原典 raw の該当行まで遡って主語を確認するチェックリスト |
| **E. 「懸念点」スロット充填時の符号検証** | テンプレート定義 | 各懸念点記述について、その事象が評価対象企業の CA をどの符号で動かすかを明示列挙させるフォーマットを強制 |
| **F. KB1ルール10適用時の方向性明示** | KB仕様 | ルール10適用時に「どちらの方向の事例か」「評価対象企業にとって得か損か」を明示的に出力させる |

**優先度**: E と F が最も直接的なブレーキとなる。A-D は構造的改善だが実装コストが高い。

---

## 8. 要約

- Erie Insurance の方向は原典では **CPRT→RB**（CPRTの喪失）。revised-report は **RB→CPRT** と**反転誤記**している
- 誤記の初出は T7 `draft-report.md`。T2-T6 の構造化データには Erie が存在せず、T7 ca-report-generator が仕様外で raw を再読した際に「当社」の主語特定を誤ったと推定される
- T8 Lead（Opus）は draft を批判対象としつつも、raw 突合を行わないため誤記を検出できず、むしろ KB1ルール10 の双方向性として誤方向を正当化した
- さらに本質的な破綻は、**RB→CPRT という CPRT にとっての獲得イベントを懸念点に配置した**こと。これは narrative 駆動のスロット充填が、事象の符号検証を伴わずに行われた結果
- 改善の要は、**KB適用時の方向性明示**と、**懸念点スロット充填時の符号検証**をフォーマット上で強制すること

---

*本分析は Y のフィードバック（`Feedback_CPRT.md` その他セクション）を起点に、`raw/CPRT US.md` / `parsed-report.json` / `claims.json` / `fact-check.json` / `pattern-verification.json` / `draft-report.md` / `critique.json` / `revised-report-CPRT.md` を全工程トレースして作成。*

# 議論メモ: Step3 サンプル sector 識別性検証 notebook 設計

**日付**: 2026-05-29
**議論ID**: disc-2026-05-29-sector-validation-design
**参加**: ユーザー + AI
**前 Discussion**: [disc-2026-05-29-spx-completion-snapshot](2026-05-29_discussion-spx-completion-snapshot.md)
**関連 pilot**: [disc-2026-05-22-filing-nlp-embedding](2026-05-22_discussion-filing-nlp-embedding.md)

## 背景・コンテキスト

SPX Step2（FILING_NLP_v2 / indices_v1）が 2026-05-28 20:21 JST に 500/500 CIK で完走（20,139 filings / 43,233 sections / 1,530,210 chunks / failed 0）。
次の Step3（embed_indices.py）を全件 1.53M chunks に投入する前に、pilot 9 ticker 段階で確立した embedding 設計（`dec-2026-05-22-emb-001〜008`）が SPX scale で sector 構造を保存できるかを定量検証するフェーズを挿入する。

ユーザー要望:
- 「sector 識別性が大事」
- 「全 GICS セクター × 各 5 銘柄」「2020 年以降」「10-K + 10-Q」「chunks 数のオーダーは気にしない」
- 「コードは notebook で実行できるようにして」「1-2 本」
- 「A（フルセット指標）に加えて FASTopic の実装」

## Phase 1: コンテキスト復元

### 既存資産

| 資産 | 状態 |
|------|------|
| chunks parquet (499 CIK) | NAS `/Volumes/personal_folder/Quants/FILING_NLP_v2/chunks/indices_v1/` |
| chunks スキーマ | 13 列: filing_id, cik, **ticker**, form, filing_date, **fiscal_year**, **section_key**, section_role, subsection_idx, subsection_title, chunk_idx, **text**, token_count |
| SPX universe (503 ticker) | `notebook/FILING_NLP/2026-05-22_SPX Index.json` + GICS_SECTOR_NAME / GICS_INDUSTRY_NAME / CUR_MKT_CAP |
| GICS sector 分布 | 11 sector、最少 Energy 21 ticker（全て 5 抽出可能） |
| pilot 5 ticker 段階 | `dec-2026-05-22-emb-001〜008`（MAX_TOKENS=512, MPS bfloat16, batch=32 random, NaN-marker checkpoint, L2 normalize, table 除外） |
| `notebook/FILING_NLP/pipeline/embed_indices.py` | 798 行で実装済み（HF1 確定設計、per-CIK shard、CLI） |
| `notebook/FILING_NLP/05_embedding.ipynb` | gte-Qwen2 embedding 生成セル群（流用可能） |
| FASTopic | PyPI `fastopic`、NeurIPS 2024 Wu et al.、`preset_doc_embeddings: np.ndarray` を `fit_transform` で受け取れる |

### chunks parquet サンプル（CIK 4962 = AXP）

11,092 chunks / 10-K 3,956 + 10-Q 7,136 / section: item_1, item_1a, item_7, item_2

## 議論のサマリー

### 論点1: 次フェーズの優先順位

候補: Step3 / RAY / 品質統計 / 他指数

→ **Step3 embedding に進む**。ただしユーザー指定で「サンプル数銘柄・数年分の time-series と cross-section 検証」が前提。全件投入は本検証 OK 後。

### 論点2: サンプル設計（銘柄構成 × 年度範囲）

ユーザー回答:
- sector 識別性が主目的
- 全 GICS セクター × 各 5 銘柄
- 2020 年以降
- 10-K + 10-Q
- chunks 数のオーダー制約なし

### 論点3: 5 ticker 選定方法

選択肢 A〜D を提示。

→ **B: 時価総額 + industry 分散**を採用。同 sector 内で GICS_INDUSTRY が異なる 5 銘柄、時価総額順で dedupe。within-sector 多様性も担保し、sector の本質を「足し算で」捉えられるかを検証可能にする。

### 論点4: section 絞り込み

→ **A: 全 section（item_1 + item_1a + item_7 + item_2）**。notebook 側で section 別に sector 識別性を比較する。item_1（Business）が sector 本質に最も近いと予想されるが、item_1a/item_7/item_2 との差を測ることで section 寄与度を可視化。

### 論点5: 検証指標

→ **A: フルセット + FASTopic**。
- (a) L2 norm 分布 + cosine similarity ヒストグラム (within-sector vs between-sector)
- (b) UMAP / PCA 2D 可視化（sector / industry / ticker でカラー）
- (c) sector 識別性: KNN (k=5, leave-one-out) / Linear probe (LR) / Silhouette / Adjusted Mutual Information (KMeans vs GICS)
- (d) time-series 安定性: 同 ticker × 同 section の年度間 cosine 推移、ticker centroid drift
- (e) ベースライン: TF-IDF + LR vs gte-Qwen2
- (f) **FASTopic**: 教師なし topic 発見 + topic_activity_over_time + GICS_SECTOR との AMI

### 論点6: notebook 構成と embedding 実行方法

選択肢 A（CLI + 分析 5 本）/ B（全 notebook 1-2 本）/ C（細分割 6-7 本）/ D（pilot 互換 1 本）。

→ **B: 全 notebook 完結（2 本）**を採用。embedding 生成も notebook 内で実行（pilot 05_embedding.ipynb のロジックを貼る）。中間ファイル経由で n01/n02 を疎結合。

### 論点7: 中間ファイル保存先

→ **NAS**（`/Volumes/personal_folder/Quants/FILING_NLP_v2/embeddings/sector_validation/`）。SPX chunks/embeddings と同階層に統一、他 PC と共有可能。

### FASTopic 統合確認（Web 調査）

- `pip install fastopic` で導入可能
- `model = FASTopic(num_topics=K, doc_embed_model=wrapper)` （wrapper は `.encode(docs, ...)` 実装）
- `top_words, doc_topic_dist = model.fit_transform(docs, preset_doc_embeddings=our_gte_qwen2_embeddings)` で事前計算 embedding を直接注入可能（再 encode 回避）
- `topic_activity_over_time(time_slices)` で年度別 topic prevalence
- device: 'cuda' / 'cpu'（MPS 明示記述なし → 開始は CPU、可能なら MPS 検証）

## 決定事項

| ID | 内容 | コンテキスト |
|----|------|------------|
| dec-2026-05-29-002 | Step3 全件 (SPX 1,530,210 chunks) embedding 着手の前にサンプル sector 識別性検証フェーズを挿入。pilot 設計が SPX scale で sector 構造を保存できるか定量検証してから全件投入を判断 | 全件 embedding は MPS でも数十時間。失敗後の再投入コストが大きいため 150K chunks 程度で品質確認 |
| dec-2026-05-29-003 | 検証サンプル: 11 GICS sector × 5 ticker (時価総額順 + GICS_INDUSTRY 分散 dedupe) = 55 ticker × 2020-01-01 以降 × 10-K + 10-Q × 全 4 section、chunks 数オーダー制約なし | sector 識別性が目的。within-sector 多様性のため industry 分散。section 別比較は notebook で実施 |
| dec-2026-05-29-004 | 検証指標フルセット + FASTopic: (a) norm/cosine 分布 (b) UMAP/PCA (c) KNN/Linear probe/Silhouette/AMI (d) time-series 安定性 (e) TF-IDF ベースライン (f) FASTopic + topic_activity_over_time | 教師あり (KNN/LR) と教師なし (Silhouette/AMI/FASTopic) 両軸で多角的検証 |
| dec-2026-05-29-005 | Notebook 2 本構成 + NAS 中間ファイル。n01_extract_and_embed.ipynb (55 ticker 選定 + chunks 抽出 + embedding 生成) → 中間ファイル NAS 保存 → n02_analyze_and_topics.ipynb (全指標) | embedding 計算は重いため n01/n02 を中間ファイルで疎結合化、n02 の分析イテレーションを高速化 |
| dec-2026-05-29-006 | FASTopic 統合方針: preset_doc_embeddings に gte-Qwen2 注入、num_topics=30 初期値、device='cpu' 開始、time_slices=fiscal_year、chunk-level を doc 単位 | FASTopic は fit_transform(docs, preset_doc_embeddings) で事前計算 embedding を受け取れる。150K × 30 程度なら CPU でも数十分。集約は後段で検討 |

## ActionItem 状態更新

| ID | 旧状態 | 新状態 | 備考 |
|----|--------|--------|------|
| act-2026-05-29-003 (Step3 全件起動計画) | pending / medium | **revised** / pending / **low** | dec-2026-05-29-002 によりサンプル検証完了後に再計画。再活性化判断は act-2026-05-29-008 で |

## 新規アクションアイテム

| ID | 内容 | 優先度 |
|----|------|--------|
| act-2026-05-29-004 | 55 ticker 選定スクリプト作成。SPX universe JSON → GICS_SECTOR ごとに CUR_MKT_CAP 降順 + GICS_INDUSTRY dedupe で 5 抽出。chunks parquet との突合で実在 ticker のみ採用。出力: `data/processed/sector_validation/ticker_list.csv` | high |
| act-2026-05-29-005 | n01_extract_and_embed.ipynb 実装。55 ticker × fiscal_year>=2020 × form in (10-K, 10-Q) で chunks 抽出 → gte-Qwen2-1.5B-instruct MPS bfloat16 batch=32 random で embedding 生成 → NAS の `embeddings/sector_validation/{embeddings.npy, chunks_meta.parquet}` に保存 | high |
| act-2026-05-29-006 | n02_analyze_and_topics.ipynb 実装。中間ファイル読込 → (a)〜(f) 全指標。FASTopic は num_topics=30 で preset_doc_embeddings 注入、time_slices=fiscal_year、AMI vs GICS_SECTOR を計算。section 別の比較も実施 | high |
| act-2026-05-29-007 | FASTopic 依存追加と smoke test。`uv add fastopic topmost` → 最小サンプル (1 ticker 分) で fit_transform + preset_doc_embeddings 動作確認。MPS 動作可否を判定 (NG なら device='cpu' 確定) | medium |
| act-2026-05-29-008 | サンプル検証完了後の全件 Step3 再計画判断。判定基準: sector 識別性 (KNN accuracy / AMI) 許容水準、time-series 安定性、FASTopic で意味ある topic 抽出。OK なら act-2026-05-29-003 を再活性化、NG なら原因分析 → 再検証 | low |

## 次回の議論トピック

1. n01/n02 notebook の初版実装レビュー
2. サンプル検証結果（KNN accuracy / AMI / FASTopic topic 例 / time-series drift）の評価と合格基準の最終化
3. 全件 Step3 再活性化の Go/No-Go 判断
4. （並行）RAY (Russell 3000) Step2 単独起動 (act-2026-05-29-001) の起動タイミング
5. CIK 1137390 zero-chunk 調査 (act-2026-05-29-002) の優先度再評価

## 参考情報

### 銘柄構成プレビュー（時価総額 top 5 ベース、industry dedupe 適用前）

| Sector | 候補上位 5 (要 industry dedupe) |
|--------|--------------------------------|
| Information Technology | NVDA, AAPL, MSFT, AVGO, MU |
| Communication Services | GOOGL, META, NFLX, TMUS, [+1] (GOOG 重複除外) |
| Consumer Discretionary | AMZN, TSLA, HD, MCD, TJX |
| Financials | BRK/B, JPM, V, MA, BAC |
| Health Care | LLY, JNJ, ABBV, UNH, MRK |
| Consumer Staples | WMT, COST, KO, PG, PM |
| Energy | XOM, CVX, COP, WMB, SLB |
| Industrials | CAT, GE, GEV, RTX, BA |
| Materials | LIN, NEM, FCX, SHW, ECL |
| Real Estate | WELL, PLD, EQIX, AMT, DLR |
| Utilities | NEE, SO, CEG, DUK, AEP |

### chunks 数概算

- SPX 平均 76 chunks/filing × 55 ticker × 7 年 × 5 filings/年 ≈ **150,000 chunks**
- gte-Qwen2 MPS bfloat16 batch=32 random → 約 **1 時間**

### FASTopic 参考リンク

- 論文: https://arxiv.org/pdf/2405.17978
- GitHub: https://github.com/BobXWu/FASTopic
- PyPI: https://pypi.org/project/fastopic/
- API: `FASTopic(num_topics, doc_embed_model, normalize_embeddings)`, `fit_transform(docs, preset_doc_embeddings, epochs, learning_rate)`, `topic_activity_over_time(time_slices)`, `visualize_topic_hierarchy()`

### 関連 Decision

- dec-2026-05-22-emb-001〜008 (pilot 段階の embedding 設計)
- dec-2026-05-28-001 (NAS 直接書き込み)
- dec-2026-05-28-002 (per-CIK checkpoint パターン)
- dec-2026-05-28-003 (Step3 embedding は MPS GPU で別物のため再見積もり必要)
- dec-2026-05-29-001 (SPX Step2 完走)

### 保存先

- NAS: `/Volumes/personal_folder/Quants/FILING_NLP_v2/embeddings/sector_validation/`
- ローカル: `notebook/FILING_NLP/sector_validation/n01_extract_and_embed.ipynb`, `n02_analyze_and_topics.ipynb`
- ticker list: `data/processed/sector_validation/ticker_list.csv`

---

## 進捗更新 (2026-05-29 追記)

### act-2026-05-29-004 完了 ✅

`notebook/FILING_NLP/sector_validation/select_tickers.py` を実装・実行し、`data/processed/sector_validation/ticker_list.csv`（55行 = 11 sector × 5）を生成。ユーザー承認済み。関連決定: `dec-2026-05-29-007`。

**選定結果**
- 全 11 GICS sector で 5/5 達成（null 0 / cik 重複 0 / ticker 重複 0）
- chunks 突合カバレッジ: SPX 503 中 499 マッチ

**レビューで確認した論点**
1. **ticker 表記**: chunks parquet も SPX JSON と同じ **Bloomberg 形式**（`BRK/B`, `BF/B`）。正規化（`/` `.` → `-`、大文字化）で両側突合。CSV の ticker は chunks 側実表記なので n01 フィルタにそのまま使用可。
2. **industry 分散の構造的限界**: Energy は GICS industry が 2 種のみ（XOM/CVX/COP/WMB が同一 "Oil, Gas & Consumable Fuels"）、Materials は NEM/FCX が "Metals & Mining" 重複。within-sector 多様性は GICS 構造由来で限定。dedupe を緩め時価総額順補充して各 5 確保。→ 許容。
3. **chunks 非実在で除外（4件）**: GOOGL（GOOG と同一企業、実質問題なし）、FOXA / NWSA / BNY（Step2 500/500 完走にもかかわらず chunks 欠落）。各 sector 5 確保のためサンプル検証には影響なし。ただし FOXA/NWSA/BNY は **zero-chunk 調査（act-2026-05-29-002）と関連する可能性**があり要追跡。

### 次の着手（act-004 完了時点）

- **次**: `act-2026-05-29-005`（n01_extract_and_embed.ipynb）。`ticker_list.csv` を入力に chunks 抽出 + gte-Qwen2 embedding 生成 → NAS 中間ファイル保存。
- **並列可**: `act-2026-05-29-007`（fastopic 依存追加 + MPS/CPU smoke test）。n02 着手までに済ませる。

---

## 進捗更新 (2026-05-29 追記 #2): act-005 コード確定（フル生成は未起動）

### 実施内容

`act-2026-05-29-005`（n01）の**コードを確定**。ユーザー指示によりフル embedding 生成（~41h）は未起動とし、別タスク `act-2026-05-29-009` に分離。

**成果物**
- `notebook/FILING_NLP/sector_validation/n01_extract_and_embed.ipynb`（6セル、構文 compile OK）
- `notebook/FILING_NLP/sector_validation/extract_chunks.py`（抽出 helper、ruff OK）
- `embed_indices.py`（`_load_model` を bidirectional 修正、ruff OK）
- NAS `embeddings/sector_validation/chunks_meta.parquet`（**107,984 行**、15列、GICS 結合済・行順確定）

**抽出統計**: 総 107,984 chunks / 10-K 49,718・10-Q 58,266 / fy2020-2026 / token mean 272・median 144・max 512(trunc) / 55 ticker 全カバー。sector別最大 Financials 26,263、最小 Health Care 5,642。

### 🔴 重大な技術的発見と修正（`dec-2026-05-29-008`）

サブエージェントが当初 `embed_indices._load_model` を `trust_remote_code=False`（標準 `Qwen2Model`=**causal**）に変更していたが、**これは誤り**。HF cache の `modeling_qwen.py` を精読した結果:
- `Qwen2Model.forward` の `is_causal` デフォルトは **`False`**（L968）
- sdpa 経路で `_prepare_4d_attention_mask_for_sdpa`（**bidirectional**）に分岐（L1038）

→ **gte-Qwen2 は bidirectional attention で埋め込むのが GTE 設計**（causal LLM の mask を外す手法）。標準 causal Qwen2Model に置換すると埋め込みが**意味的に別物**になり、pilot（`dec-2026-05-22-emb`）とも乖離 → 検証が無効化される。

**修正**: transformers 5.1.0 で壊れるのは `config.rope_theta` 欠落のみ（必要 import は全残存）と判明。`rope_theta`(=1000000.0) を `rope_parameters` から config に復元注入し `trust_remote_code=True` でカスタム bidirectional encoder をロード。検証結果: load 成功・`module=modeling_qwen`・L2 norm≈1.0・NaN 0・実測 0.729 chunks/sec。tokenizer は標準 slow `Qwen2Tokenizer`（vocab 同一）。**この修正は全件 Step3 本番にも必須**。

### ⏭ フル embedding 生成の起動手順（`act-2026-05-29-009`、deferred）

実測 **0.729 chunks/sec → 107,984 chunks で約 41.2h**。NaN-marker resume 対応で中断耐性あり。

```bash
cd /Users/yuki/Desktop/quants

# pre-flight（~9分、OUT_EMB 未保存の実測のみ）
N01_SMOKE=1 uv run jupyter nbconvert --to notebook --execute \
  --output /tmp/n01_smoke.ipynb --ExecutePreprocessor.timeout=-1 \
  notebook/FILING_NLP/sector_validation/n01_extract_and_embed.ipynb

# フル生成（~41h、detached、resume 対応）
caffeinate -i nohup env N01_SMOKE=0 \
  uv run jupyter nbconvert --to notebook --execute \
  --output /tmp/n01_executed.ipynb --ExecutePreprocessor.timeout=-1 \
  notebook/FILING_NLP/sector_validation/n01_extract_and_embed.ipynb \
  > logs/n01_sector_validation_embed.log 2>&1 &
```

中断時は同コマンド再実行で `embeddings.npy` の NaN 行から resume。

**任意の最適化**: `chunks_meta` を `token_count` 順ソートしてから encode すると `padding=True` の無駄が減り、~25-30h に短縮見込み（要小ベンチで実効率確認）。行順は n02 が metadata join するため影響なし。

### 次の着手（更新）

- `act-2026-05-29-009`（フル embedding 生成、~41h）— ユーザー任意のタイミングで起動
- `act-2026-05-29-006`（n02_analyze_and_topics.ipynb）— embeddings.npy 完成後
- `act-2026-05-29-007`（fastopic smoke）— n02 着手までに並列で（pyproject に fastopic/topmost は追加済みの模様、smoke 未実施）

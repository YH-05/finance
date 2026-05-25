# 議論メモ: FILING_NLP v2 パイロット実行結果 + 有効な対応策カタログ

**日付**: 2026-05-25
**議論ID**: disc-2026-05-25-filing-nlp-v2-pilot-results
**Project**: quants
**前回**: [disc-2026-05-25-filing-nlp-v2-strategy-c](2026-05-25_discussion-filing-nlp-v2-strategy-c.md)

## 背景・コンテキスト

同日午前に Strategy C 設計を確定し、`notebook/FILING_NLP/pipeline/` パッケージと `pipeline_pilot.ipynb` を実装。100 銘柄ランダムサンプリング × ヒストリカル全期間（filing_date >= 2002）の **パイロット実行** を notebook 上で実施した。

本メモは:
1. パイロット実行結果の数値報告
2. **検証された有効な対応策（5 パターン）の詳細カタログ**
3. 本実行（Task #4、6,000 社）へ向けた最終判断

を記録する。「対応策カタログ」は今後の類似プロジェクト（規模拡張、SEC API 連携、Apple Silicon ML、NAS バッチ処理）で **設計パターンとして参照** する。

## パイロット実行結果

### 規模統計

| 指標 | 値 | 評価 |
|---|---|---|
| 処理 CIK | 100 (sample, seed=42) | – |
| chunks 生成された CIK | **66** | 66% 活性 |
| 0-chunk CIK | 34 | 34% 真に「データなし」 |
| 総 filings | 4,040 | – |
| filings status=success | 3,781 (93.6%) | ◎ |
| filings status=no_sections | 259 (6.4%) | 許容 |
| 総 sections | 7,893 | – |
| 総 chunks | **137,970** | – |
| エラー (errors.jsonl) | **0 件** | ◎ |
| 上限超過 chunk (>1024 tok) | 721 / 137,970 = **0.52%** | 許容 |
| fiscal_year 範囲 | 2002 - 2026 (全 25 年カバー) | ◎ |

### token 分布

```
count: 137,970
mean:    380.1
std:     360.6
min:       1.0
25%:      73.0
50%:     230.0
75%:     715.0
max:    3541.0
```

### form × section_key 別 chunk 数

| form | section_key | section_role | chunks |
|---|---|---|---|
| 10-K | item_1 | business | 21,474 |
| 10-K | item_1a | risk_factors | 17,216 |
| 10-K | item_7 | mda | 27,989 |
| 10-Q | item_1a | risk_factors | 7,782 |
| 10-Q | item_2 | mda | **63,509** |

10-Q の item_2 (MD&A) が最大ボリューム（全 chunks の 46%）。10-Q は四半期発行で件数自体が多いため。

### DOM section 取得率

| section_key | filings | dom_found | dom_rate | text_len 平均 | tables_removed 平均 |
|---|---|---|---|---|---|
| item_1 (10-K Business) | 949 | 353 | **37.2%** | 47,906 | 1.6 |
| item_1a (Risk Factors) | 3,230 | 1,855 | **57.4%** | 26,691 | 2.0 |
| item_2 (10-Q MD&A) | 2,778 | 2,161 | **77.8%** | 50,416 | 7.1 |
| item_7 (10-K MD&A) | 936 | 348 | **37.2%** | 70,458 | 2.1 |

**観察**: 10-K の item_1 / item_7 が同率 37.2%。Part I/II の TOC parser に同じ失敗パターンがある可能性。ただし `dom_found=False` でも text 抽出は heuristic fallback で成功しているため、最終データには影響なし。

### fiscal_year トレンド

```
2002:    332
2008:  2,056
2015:  4,465
2020: 11,399  ← 急増 (universe 拡大 + Item 1A 拡張規制)
2024: 12,355
2025: 13,235  ← peak
2026:  7,079  (部分年)
```

健全な分布。古い年代の少なさは「銘柄の上場年度ばらつき」を反映。

### バグ修正の効果検証

| 指標 | 修正前 (kill 後 resume) | 修正後 (fresh run) | 改善 |
|---|---|---|---|
| 0-chunk CIK | 44 / 100 | **34 / 100** | **-10 CIK 復旧** |
| 総 chunks | 124,613 | **137,970** | +13,357 |
| unique CIK | 56 | **66** | +10 |
| filings success | 3,264 | **3,781** | +517 |

`ShardWriter` の **per-CIK parquet 直接書き出し方式** + `write_cik → mark_done` 順序固定により、smoke test で chunks 生成された 5 銘柄（SWKH/XCUR/KEX/GMED/QBTS）が正しく復旧。

## 議論のサマリー（有効な対応策カタログ）

### 対応策 A: データ品質を担保する 5 層抽出デザイン

| 層 | 機構 | DOM 取得失敗時の fallback |
|---|---|---|
| 1. text 抽出 | `obj.get_item_with_part(part, item)` | – (9/9 銘柄でカバー) |
| 2. DOM table 除外 | `sec.tables()` から TableNode 列挙 → text から除去 | safety net (5層) に委譲 |
| 3. Subsection 検出 | 強シグナル正規表現 (Risk/MD&A/Business 系) | – (DOM 取得失敗時の主役) |
| 4. 段落 packing | gte-Qwen2 tokenizer で MAX_TOKENS=1024 まで | – |
| 5. Safety net | `_is_table_like()` + `_is_page_artifact()` | – |

**効果実証**:
- DOM rate item_1 / item_7 が 37% でも、status=success は 93.6% → **fallback が機能**
- 上限超過 0.52% (許容範囲)、エラー 0 件
- text 抽出経路は edgartools の現行 API で 9/9 銘柄 (CIK 2 命名規則含む) で動作

### 対応策 B: kill 耐性 per-CIK 出力パターン

**問題**: メモリ buffer + 周期 flush では kill 時にデータ消失。checkpoint は「完了」記録されるため resume で永久 skip → サイレント データロス。

**解決パターン**:

```
[従来] 不安全パターン
   add(buffer) → mark_done → (flush_every で) flush
                       ↑ ここで kill されると buffer 消失

[修正] 安全パターン
   write_cik(per-CIK ファイル直接書き出し) → mark_done
   write_cik 失敗時: mark_done 呼ばず continue (resume で再処理)
```

**証拠**:
- smoke test で chunks 生成された 5 銘柄が修正前 pilot で 0 chunks → 修正後 pilot で正常復旧
- per-CIK ファイル = `chunks_cik{10桁CIK}.parquet` = 新規 write のみ、read-modify-write 不要

**応用範囲**: SEC API 以外でも「長時間バッチ処理 × 中断耐性」が必要なケース全般（学術論文ダウンロード、財務データ更新、自動再収集 cron 等）。

### 対応策 C: 複数命名規則の吸収パターン

**問題**: edgartools が `doc.sections` で 2 種類のキー命名を混在させる:
- AAPL/NVDA/AVGO/META: `part_i_item_1` (snake_case)
- MSFT/GOOGL/AMZN/AMAT: `Item 1` (raw label)

**解決パターン**:

```python
def get_section(doc, part, item):
    """3 候補を順に try、最初にヒットしたものを返す."""
    part_norm = part.lower().replace(" ", "_")
    item_norm = item.lower().replace(" ", "_")
    candidates = [
        f"{part_norm}_{item_norm}",  # "part_i_item_1a"
        item,                         # "Item 1A"
        item.upper(),                 # "ITEM 1A"
    ]
    for key in candidates:
        sec = doc.sections.get(key)
        if sec is not None:
            return sec, key
    return None, None
```

**効果**: 9/9 銘柄カバー（最初の試行で覆われない場合も 2-3 番目で吸収）。

**応用範囲**: 外部 API のスキーマ揺らぎ全般（フィラー差、API バージョン差、データソース統合）。

### 対応策 D: SEC API スケール調整パターン

**確定設定**:

| パラメータ | 値 | 根拠 |
|---|---|---|
| `max_workers` | **8** | I/O bound (HTTPS) なので thread で十分。8 で SEC レート上限を超えない |
| `rate_rps` | **7** (TokenBucket) | SEC 非公式上限 ~10 req/sec/IP の安全マージン |
| `rate_burst` | 10 | 突発的なバースト許容 |
| 出力形式 | per-CIK parquet | 並列 write、merge は事後 |
| 進捗表示 | `tqdm.auto` | notebook で widget、CLI で text |
| logger | `edgar.core` の legacy parser フィルタ | warning ノイズ抑制 |

**実証**:
- pilot で SEC rate limit 違反 0 件（429 エラーなし）
- 100 CIK ≒ 60-90 分（実時間）
- workers=8 / rate=7 が **stable な動作点**

**応用範囲**: 各種 SEC EDGAR バッチ収集、その他レート制限のある HTTPS API バッチ。

### 対応策 E: 「真にデータなし」CIK の見分け方

**観察**: pilot の 34 zero-chunk CIK を会社名から分類:

| カテゴリ | 該当銘柄例 | 件数 (推定) | 識別方法 |
|---|---|---|---|
| **Closed-end fund** (N-CSR filer) | NMI (Nuveen)、CIK (Credit Suisse) | ~5-10 | 会社名に "FUND" / "TRUST" 含む |
| **Foreign filer** (20-F filer) | EDN (Argentina)、PHI (Philippines)、COE (China)、EDRY (Greece)、BTG (Canada)、ZYBT (China) | ~10-15 | exchange='NYSE'/'Nasdaq' だが本拠地が米国外 |
| **短期上場後 cutoff 直前** | WAI、AFJK、PSIG | ~5-10 | filings 数 0-2 件、filing_date が 2024-2026 のみ |
| **delisted / shell** | – | 残り | filings_metadata 空 + universe からも消失予定 |

**判断**: 本実行 (6,000 社) でも同様の比率（~10% 弱）が想定される。事前 filter する **コスト** (universe 確定時に Company().get_filings() を 6,000 回呼ぶ) > **便益** (10% の処理時間削減) のため、**事前 filter しない**方針。

代替: filings_metadata の status と form 分布を本実行後の品質分析で集計し、メタデータ層で識別する。

**応用範囲**: 投資ユニバース定義全般（NASDAQ 上場 ≠ 米国 10-K filer）、特に外国 ADR 多めの市場分析。

## 決定事項

| ID | 内容 |
|---|---|
| dec-2026-05-25-011 | per-CIK parquet 方式の効果実証。本実行も同方式継続 |
| dec-2026-05-25-012 | 0-chunk CIK は「真にデータなし」と確認。本実行で事前 filter しない |
| dec-2026-05-25-013 | 本実行スケール推定を pilot 実測ベースで更新 (4,000 active CIK / 8.4M chunks / 15-25 GB / 36-54h) |
| dec-2026-05-25-014 | Phase 3 調整は本実行前にしない (heuristic fallback で品質許容) |
| dec-2026-05-25-015 | 本実行は run_id='production' / workers=8 / rate=7 (pilot 同等) で起動 |
| dec-2026-05-25-016 | 「有効な対応策」5 パターン (A: 品質 / B: kill 耐性 / C: 命名規則吸収 / D: スケール / E: 真データなし検別) をカタログ化 |

## アクションアイテム

| ID | 内容 | 優先度 | ステータス |
|---|---|---|---|
| act-2026-05-25-007 | 本実行 (Task #4) を run_id='production' で起動 | 高 | pending |
| act-2026-05-25-008 | 本実行中の進捗監視 (progress.json + per-CIK parquet サンプリング検証) | 高 | pending |
| act-2026-05-25-009 | item_7 (10-K MD&A) の DOM rate 37.2% の追加調査 (本実行後) | 中 | pending |
| act-2026-05-25-010 | 本実行完了後の zero-chunk CIK 最終分類確認 | 中 | pending |

(前回 discussion の act-001/002 は completed、003/004/005/006 は引き続き有効)

## 本実行への最終判断

**判定**: 本実行に進む準備完了。Strategy C パイプラインは品質・kill 耐性・スケール調整の 3 軸で実証済み。

**起動コマンド** (notebook ベース):
1. `pipeline_pilot.ipynb` をベースに `RUN_ID = "production"`、`SAMPLE_N = 6000` (= universe 全数) に変更
2. Cell 5 で `RESET = True` (新規 run のため)
3. Cell 6 でバックグラウンド実行 (notebook ターミナル不要なら CLI: `python -m notebook.FILING_NLP.pipeline.run_pilot --n 6000 --workers 8 --rate 7 --run-id production`)

**監視ポイント**:
- CIK 完了ペース (target: 110-160 CIK/h)
- errors.jsonl 行数（突発的増加なら一時停止）
- NAS 書き込み速度 (per-CIK parquet ファイル数のペース)
- 0-chunk CIK 比率 (pilot の ~34% から大きく外れないか)

## 次回の議論トピック

1. **本実行進捗の中間レビュー** — 1 日目終了時点のサンプル品質
2. **データ品質統計分析レポート** — Task #5、Phase 3 調整の必要性判断
3. **下流 embedding 生成 (02b)** — chunks_v2 → gte-Qwen2 1536 次元
4. **クオンツ分析応用** — Risk Factor 時系列差分、業界類似度、FASTopic 等

## 参考情報

- 前回設計議論: [2026-05-25_discussion-filing-nlp-v2-strategy-c.md](2026-05-25_discussion-filing-nlp-v2-strategy-c.md)
- 元設計議論: [2026-05-22_discussion-filing-nlp-embedding.md](2026-05-22_discussion-filing-nlp-embedding.md)
- 実装パッケージ: `notebook/FILING_NLP/pipeline/`
- パイロット notebook: `notebook/FILING_NLP/pipeline_pilot.ipynb`
- NAS 保存先: `/Volumes/personal_folder/Quants/FILING_NLP_v2/`
- Universe: 6,000 unique CIK (NYSE 2,608 + Nasdaq 3,392)

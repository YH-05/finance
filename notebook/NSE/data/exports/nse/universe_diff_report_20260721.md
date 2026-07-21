# NIFTY 750 Universe 差分レポート (2026-07-21 版)

**比較**: 前回確定版 `nifty750_universe.csv` (855 銘柄、05-12) vs 今回版 `nifty750_universe_20260721.csv` (864 銘柄)
**データ取得時点**: 指数構成CSV は 2026-07-14 (Last-Modified)、`stocks` マスタと株主データは 2026-07-15 取得
**経緯**: 初版は 2026-06-30 を基準日として作成した。以降の改訂で基準日を 2026-07-21 に変更している（末尾の改訂2節を参照）。6月末版の成果物は `archive/` に退避済み

## サマリー

| 項目 | 前回 (05-12) | 今回 (06-30) | 差分 |
|------|------|------|------|
| 総銘柄数 | 855 | 863 | +8 |
| OWNER 銘柄数 | 599 | 598 | -1 |
| NOT_OWNER 銘柄数 | 256 | 265 | +9 |
| NIFTY TOTAL MKT 構成銘柄数 (is_nifty_total_mkt=True) | 744 | 750 | +6 |

**注意**: OWNER 銘柄数の増減だけでは構成の入れ替えが見えない。銘柄単位の差分は「OWNER 構成銘柄の入れ替え」節を参照すること。

## 6月末時点構成の扱い

NSE の指数構成 API（`equity-stockIndices`）は現在時点の構成のみ返し、point-in-time（過去日付指定）取得に対応していない。また DB の `index_members` テーブルも履歴を保持しない単一スナップショット設計のため、「6月末時点」を厳密に再現する手段は存在しない。

一方、NSE 公式の指数方法論により、NIFTY 系指数の定期見直し（reconstitution）は**3月末・9月末に効力発生**（データ基準日は1月末・7月末）と確認できた。したがって 2026年6月末時点の構成は、直近3月の見直し後のまま変わっていないはずであり、次の変更は9月末まで発生しない。この根拠に基づき、**2026-07-15時点で取得した構成を6月末時点の構成として採用**した（ユーザー承認済み）。

取得は動的API不通のため、静的CSV配信（`nsearchives.nseindia.com/content/indices/ind_niftytotalmarket_list.csv`、Last-Modified: 2026-07-14）を新規実装（`IndicesCollector.fetch_index_constituents_archive()`）で使用した。

## NIFTY TOTAL MKT 構成差分（真の指数入れ替え）

前回universeの `is_nifty_total_mkt=True`（744銘柄）と、今回取得した最新構成（751銘柄）を比較。

### 新規採用 10 銘柄

| symbol | 会社名 | is_owner_company | promoter_total_pct | owner_flag_final_hybrid |
|---|---|---|---|---|
| AGL | Allcargo Global Limited | — (universe から除外) | 63.28% | OWNER |
| RATNAMANI | Ratnamani Metals & Tubes Limited | **True** | 59.77% | OWNER |
| JSWDULUX | JSW Dulux Limited | False | 61.20% | OWNER_WEAK |
| SANOFICONR | Sanofi Consumer Healthcare India Limited | False | 71.27% | NOT_OWNER (MNC) |
| INDGN | Indegene Limited | False | 21.42% | OWNER_WEAK |
| IXIGO | Le Travenues Technology Limited | False | 13.35% | OWNER_WEAK |
| SUDARSCHEM | Sudarshan Chemical Industries Limited | False | 8.19% | OWNER (Stage1未達) |
| FIRSTCRY | Brainbees Solutions Limited | False | 5.31% | OWNER_WEAK |
| PINELABS | Pine Labs Limited | False | 2.66% | OWNER_WEAK |
| SAMHI | Samhi Hotels Limited | False | 2.14% | OWNER_WEAK |

INDGN/IXIGOはStage1閾値（10%）を超えているが、`owner_flag_final_hybrid`がyaml未知family・Tier2ハイブリッドルールにより`OWNER_WEAK`に留まり、`is_owner_company`はFalse（後述の既知課題を参照）。

**2026-07-21 訂正**: 当初この節は「OWNER確定は2銘柄（AGL, RATNAMANI）」と記載していたが、2点とも誤りだった。

- **RATNAMANI は新規ではない**。前回版（05-12）に rev1 補完銘柄（`in_rev1=True`）として既に OWNER で収録済みであり、今回新規なのは「NIFTY TOTAL MKT 指数構成への採用」であって universe への追加ではない。
- **AGL は基準日超過のため universe から除外した**（下記「AGL の除外」節）。

結果として、この10銘柄による OWNER の純増は **0 銘柄**である。

### 除外 3 銘柄（NIFTY TOTAL MKT 構成から除外）

| symbol | 状態 |
|---|---|
| AKZOINDIA | 最新EQUITY_L.csv（全上場銘柄マスタ）に存在せず、上場廃止と推定 |
| CIGNITITEC | 同上、上場廃止と推定 |
| GSPL | 同上、上場廃止と推定 |

3銘柄とも `is_owner_company=False` に更新（`is_nifty_total_mkt`等の指数帰属フラグがFalseに反転）。`owner_candidates.csv`は累積型データのためuniverse行自体は削除せず保持する既存設計を踏襲（ユーザー承認済み）。投資戦略側で必要なら `df[df["is_nifty_total_mkt"]]` で現行構成のみに絞り込み可能。

## Promoter 比率の時系列変化（既存855銘柄の再判定トリガー）

既存 `shareholdings` テーブルの四半期時系列（45,283行）から、`detect_promoter_drift(threshold_pct=1.0)` で変化を検出。**36銘柄**が対象となり、うち **HOMEFIRST** が Stage1 閾値（10%）を下方跨ぎ（12.35%→6.99%）と検出された。

ただし実際には、この変化は2026-07-15時点の`owner_candidates.csv`側データに**05-12時点で既に反映済み**であったことが判明した（`shareholdings`テーブルの四半期データ更新タイミングと`owner_candidates.csv`のXBRL detail取得タイミングにずれがあったため）。今回の再判定で `HOMEFIRST` の `is_owner_company` に変化はない（既にFalse）。

## 発見・修正したバグ: promoter_total_pct 算出ロジック

新規銘柄5件（FIRSTCRY, INDGN, IXIGO, PINELABS, SAMHI）で `promoter_total_pct` が誤って 0.0% と算出される不具合を発見・修正した。

**原因**: `aggregate_owner_candidate()` の `promoter_total_pct` 算出が `PromoterAndPromoterGroup` カテゴリの「総合計」行（`sub_category`が空文字/`Indian`/`Foreign`）に依存していたが、一部のXBRL開示（主に新規上場企業）ではこの総合計行自体が省略され、`DirectorsAndDirectorsRelatives`等のsub_category別内訳行のみが存在するケースがあった。

**修正**: `promoter_total_pct`が0.0のままの場合、`natural_pct_sum`（hufi+nri+dir+kmp+relの合計）にフォールバックする処理を追加（`persist_incremental.py`・`persist_rev1_missing.py`両方に適用）。

**影響検証**: 既存845銘柄（rev1由来）のうち25銘柄（HDFCBANK, ICICIBANK, ITC, LT, PAYTM等）が同一パターンの影響を受けていたが、フォールバック後も全て10%未満（最大PAYTM 9.28%）のため`is_owner_company`判定への影響はゼロ。Stage1閾値を跨いだのはINDGN・IXIGOの2件のみ（いずれも新規銘柄）。既存845銘柄側のowner_candidates.csv/owner_review_sheet.csvは今回変更していない（diff 0件で確認済み）。

## 既知の未対応課題（今回スコープ外）

- **SAMMAANCAP の再ラベリング**（2026年6月のIHC出資41.5%取得反映）: 別タスクとして後回し（ユーザー確認済み）
- **INDGN/IXIGOのOWNER_WEAK判定**: Stage1バグ修正によりpromoter比率は正しく反映されたが、`owner_flag_final_hybrid`のTier2ハイブリッドルール（yaml未知family時の据え置き）により`OWNER_WEAK`のまま。director_only ルール厳格化（act-2026-04-17-006、既存フォローアップ）と合わせて次回検討
- **company_name欠損**: `owner_candidates.csv`の92行（うち47行は既存rev1由来、45行は今回追加分）で`company_name`がNaN。`aggregate_owner_candidate()`の`shareholder_name`取得ロジックの既知の制限（今回新規に発生した問題ではない）
- **stocksテーブルの完全最新化は未実施**: 今回はAGLの登録漏れのみ個別対応。EQUITY_L.csv全体（2387銘柄、旧stocksテーブル2796→2928件）の差分反映は`nse_index_20260630.db`のみに適用済みで、本体`nse_index.db`には未反映

## 使用ファイル

### DB（前回版・今回版を分離）
- `notebook/NSE/data/cache/nse/nse_index_20260512.db`（前回版、読み取り専用の基準として保持）
- `notebook/NSE/data/cache/nse/nse_index_20260630.db`（今回作業用、stocks最新化・46銘柄分永続化済み）
- `notebook/NSE/data/cache/nse/nse_index.db`（本体、無変更）
- `notebook/NSE/data/cache/nse/nse_index_backup_20260715.db`（安全バックアップ、無変更）

### 主要成果物
- `notebook/NSE/data/exports/nse/nifty750_universe_20260630.csv`（863銘柄、確定版。2026-07-21 に AGL 除外で 864→863）
- `notebook/NSE/data/exports/nse/post_cutoff_pending_20260630.csv`（基準日超過で除外した AGL、次回版で採用）
- `notebook/NSE/data/exports/nse/nifty750_universe_summary_20260630.md`
- `notebook/NSE/data/exports/nse/owner_review_sheet.csv`（更新、旧版は`owner_review_sheet_20260512.csv`にバックアップ）
- `notebook/NSE/data/exports/nse/owner_candidates.csv`（1183行に拡張、旧版は`owner_candidates_before_promoter_fix.csv`等にバックアップ）
- `notebook/NSE/data/exports/nse/refetch_incremental_log.json`（46銘柄のPhase3/4取得ログ）
- `notebook/NSE/data/exports/nse/persist_incremental_20260630_log.json`（永続化ログ）

### 新規実装スクリプト
- `src/market/nse/analysis/universe_diff.py`（universe差分検出）
- `src/market/nse/analysis/promoter_drift.py`（promoter比率時系列変化検出）
- `src/market/nse/collectors/indices.py::fetch_index_constituents_archive()`（静的CSV経由の指数構成取得、新規メソッド追加）
- `notebook/NSE/scripts/refetch_incremental.py`（差分銘柄のNSEデータ取得、CLI引数化）
- `notebook/NSE/scripts/persist_incremental.py`（永続化・分類、rev1非依存の汎用版）
- `notebook/NSE/scripts/prepare_incremental_db.py`（DB複製）
- `notebook/NSE/scripts/update_stocks_master.py`（stocksテーブル最新化）
- `notebook/NSE/scripts/update_index_members.py`（index_members最新化）
- `notebook/NSE/scripts/build_nifty750_universe.py`（`--db-path`/`--output-*`引数化、`--cutoff-date` 追加）

## NSE接続障害の記録（今回発生・解決済み）

作業中、NSE公式サイトの`equity-stockIndices`動的APIが404エラーを返す障害が発生した（地理的ブロックではなく、このエンドポイント単体の問題と判明）。他の全API（`allIndices`, `corporate-share-holdings-master`, XBRL静的ファイル）は正常動作しており、代替の静的CSV配信（`nsearchives.nseindia.com/content/indices/`）で同等のデータを取得できることを確認し、恒久的な代替手段として実装した。

---

# 2026-07-21 改訂: 銘柄単位の検証で判明した事項

初版のサマリー表は「OWNER 599 → 599、差分 0」と読めるが、実際には構成銘柄が入れ替わっていた。銘柄単位で突合した結果を以下に記録する。

## OWNER 構成銘柄の入れ替え

| 区分 | 銘柄数 | 内訳 |
|---|---|---|
| 継続 | 598 | — |
| 追加 | 0 | AGL は基準日超過で除外（下記） |
| 除外 | 1 | INOXGREEN（下記） |

最終: OWNER **598 銘柄**（前回 599 から -1）。

## AGL の除外（point-in-time 整合性）

`stocks` テーブルの上場日は **2026-07-03**（series `BE`）、株主データの `report_date` も **2026-07-02** であり、**2026-06-30 時点では未上場**の銘柄だった。指数構成を静的CSV（Last-Modified: 2026-07-14）から取得したため、基準日より後の新規上場が混入した。

「NIFTY系の定期見直しは3月末・9月末適用のため6月末時点の構成は現時点と一致する」という初版の根拠は、**定期見直し以外の経路で起きる新規上場銘柄の組み入れを考慮できていなかった**。

対応として `build_nifty750_universe.py` に `--cutoff-date` オプションを追加し、基準日より後に上場した銘柄を universe から除外する処理を実装した（純粋関数 `market.nse.analysis.universe_diff.find_post_cutoff_listings()`、単体テスト6件を追加）。今回の実行では AGL 1銘柄が除外された。

AGL 自体の判定は正しく（Shashi Kiran Shetty 54.26% ほか Shetty 一族で `hufi_pct=60.25%`）、次回版で採用する。データは取得済みで `post_cutoff_pending_20260630.csv` に保存した。

## INOXGREEN の判定反転（未解決・方針決定待ち）

`is_owner_company` が True → False に変化した唯一の銘柄。**promoter比率は56.12%で不変、Stage1も通過**しており、実態の変化ではない。

| | 05-12 | 06-30 |
|---|---|---|
| `owner_flag` | `owner_confirmed_individual_and_director` | `owner_confirmed_director_only` |
| `owner_flag_final_hybrid` | OWNER | OWNER_WEAK |
| `is_owner_company` | True | False |

### 根本原因: 分類ロジックの二重実装

同一の Tier 1 ルールに対して、2つの異なる実装が存在する。

| 実装 | 判定式 | INOXGREEN の結果 |
|---|---|---|
| `nse_owner_analysis.ipynb` Cell 14 `assign_owner_flag()` | **株主数**ベース `hufi_num >= 1` | `individual_and_director` → OWNER |
| `persist_incremental.py` / `persist_rev1_missing.py` / `persist_and_classify.py` `aggregate_owner_candidate()` | **保有比率**ベース `hufi_pct > 0` | `director_only` → OWNER_WEAK |

INOXGREEN の自然人promoter（Devansh Jain, Mukesh Patni, Vivek Kumar Jain）は合計500株（発行済4.01億株）で `hufi_pct` が丸めて **0.00%** となる。今回46銘柄の再取得でスクリプト経路を通ったため判定が反転した。株主構成データ自体は05-12版DBと同一であることを確認済み。

なお同期間に promoter 名簿から Devendra Kumar Jain（100株）が消えているが、`hufi_num` は 4→3 でどちらも1以上のため、**この反転の原因ではない**。

### 影響範囲: universe 内に16銘柄の不整合

`hufi_num >= 1` かつ `hufi_pct == 0.00` かつ `dir_pct` または `kmp_pct` > 0 の銘柄が16件あり、実装経路によって扱いが分かれている。

- ノートブック経路（13件）: ABSLAMC, ADANIENT, ADANIPORTS, AFCONS, DALBHARAT, GODREJPROP, JSWINFRA, JUBLFOOD, SONACOMS, SPLPETRO, TORNTPHARM, WELCORP, WELENT
- スクリプト経路（3件）: INOXGREEN, ADANIENSOL, FINOPB

ADANIENT（`hufi_num=2`, `hufi_pct=0.00`）が OWNER である一方、同条件の INOXGREEN が OWNER_WEAK になっており、universe は自己矛盾した状態にある。

### 付随して判明した差異

`owner_labeling_methodology.md` §296-305 は保有比率ベースで記述されており、ノートブック実装が仕様から外れている。一方、出荷済み universe の大半はノートブック実装の結果である。また今回の `promoter_total_pct` フォールバック修正はスクリプト2本にのみ適用され、**ノートブック（Cell 12・14）には未反映**であるため、次回の全量再実行で INDGN・IXIGO 等の修正が失われる。

### 統一方針の選択肢

| 方針 | INOXGREEN | 他への影響 |
|---|---|---|
| A: 株主数ベースに統一（スクリプト3本を修正） | OWNER 復帰 | 既存13銘柄は現状維持。仕様書の更新が必要 |
| B: 保有比率ベースに統一（ノートブックを修正） | OWNER_WEAK のまま | AFCONS, DALBHARAT, GODREJPROP, JUBLFOOD, SONACOMS, SPLPETRO の6銘柄が OWNER_WEAK に転落し OWNER が純減6 |

判定意図が「自然人promoterが存在するか」なら A、「自然人が実質的な持分を持つか」なら B が整合する。**本項は方針未決のため、現時点の universe は INOXGREEN を除外した状態（OWNER 598）で確定させている。**

関連する既存フォローアップ: `act-2026-04-17-006`（`owner_confirmed_director_only` ルール厳格化）

---

# 2026-07-21 改訂2: 基準日を 07-21 に変更、分類ルールを統一

ユーザー判断により (1) AGL を universe に含める、(2) 分類ルールを株主数ベースに統一する、の2点を実施した。基準日が変わったため成果物を `_20260721` に改名した。

## 最終結果

| 項目 | 前回確定版 (05-12) | 今回 (07-21) | 差分 |
|---|---|---|---|
| 総銘柄数 | 855 | 864 | +9 |
| OWNER 銘柄数 | 599 | **600** | +1 |
| NOT_OWNER 銘柄数 | 256 | 264 | +8 |

**OWNER の増加は AGL 1銘柄のみ。減少はゼロ。継続 599 銘柄。**

つまりこの四半期でオーナー企業の顔ぶれは実質的に変化しておらず、新規上場の AGL が加わっただけである。

## 変更1: 基準日を 2026-07-21 に変更

初版は 2026-06-30 を基準日としたが、AGL (2026-07-03 上場) を含める判断となったため基準日を 2026-07-21 に変更した。`--cutoff-date 2026-07-21` で生成している。

**データの実際の取得時点に注意**: 指数構成CSVは Last-Modified 2026-07-14、`stocks` マスタは 2026-07-15 取得である。基準日 07-21 との間に指数構成の変更がないことは未検証（NSE の定期見直しは3月末・9月末適用のため、通常はこの期間に構成変更は起きないが、新規上場の組み入れは随時発生しうる）。

- 成果物: `nifty750_universe_20260721.csv` (864銘柄) / `nifty750_universe_summary_20260721.md`
- `post_cutoff_pending_20260630.csv` と 06-30 版 universe は `archive/` に退避

## 変更2: 分類ルールを株主数ベースに統一

`owner_flag` の Tier 1 判定を `hufi_pct > 0` から `hufi_num >= 1` に変更した。判定ルールは `src/market/nse/analysis/owner_classification.py` に一元化し、`persist_incremental.py` / `persist_rev1_missing.py` / `persist_and_classify.py` の3スクリプトが同モジュールを import する形にした。単体テスト17件を追加。

### 適用範囲を限定した理由（重要）

**全864銘柄に新ルールを適用すると240銘柄のフラグが変化する**ことが判明したため、今回スクリプト経路で処理した45銘柄のみに適用した。

240件も動く原因は、ノートブック実装とスクリプト実装の差異が `hufi` の判定軸だけではなかったことにある。調査の結果、以下の差異が追加で判明した。

| 差異 | ノートブック | スクリプト |
|---|---|---|
| hufi の判定軸 | 株主数 | 保有比率 → **今回統一** |
| **dir / kmp の判定軸** | **株主数** | **保有比率** → 未統一 |
| **外資ガード** (`MAX_FOREIGN_NON_GOVT_PCT`) | **あり (4箇所)** | **なし** |
| **独自 tier** | `excluded_low_promoter` / `ambiguous_minor_individual` / `owner_via_individual_in_other` | なし |

したがって現状は「hufi の判定軸のみ統一され、他の差異は残っている」状態である。完全統一には dir/kmp の判定軸・外資ガード・独自tierそれぞれについて仕様判断が必要で、240銘柄規模の再判定を伴う。**別タスクとして扱う。**

### 実際に変化した銘柄

| symbol | owner_flag | 結果 |
|---|---|---|
| INOXGREEN | `director_only` → `individual_and_director` | OWNER_WEAK → **OWNER** (05-12 版の判定に復帰) |
| ADANIENSOL | `director_only` → `individual_and_director` | OWNER のまま変化なし |

## 変更3: apply_hybrid に STATE/MNC 否定チェックを追加

`individual_and_director` は従来 yaml チェックを素通りして OWNER になっていた。株主数ベース化により該当銘柄が増えるため、`hufi_pct == 0`（自然人に実質持分なし）かつ yaml が `STATE` / `MNC` の場合に `NOT_OWNER` へ落とすガードを追加した。

自然人 promoter が全員雇われ経営陣で、実体は政府系・外資系という銘柄を弾くのが目的である（想定例: FINOPB は自然人6名が全員KMPで、promoter に Bharat Petroleum (GOI系) を含む。現時点では `director_only` のままなので既存の yaml チェックで NOT_OWNER を維持しているが、再取得時にフラグが変わっても判定が壊れないようにした）。

`PROFESSIONAL` を対象に含めていないのは意図的である。`STATE` / `MNC` は政府保有・外資親会社という構造的事実で誤りにくいが、`PROFESSIONAL` は判断を伴い yaml 辞書の誤りが混入しうるため。実例として TORNTPHARM は promoter が Mehta 一族（SUDHIR / SAMIR MEHTA、MEHTA FAMILY TRUST）でありながら `PROFESSIONAL=[Torrent(Torrent / KKR)]` と誤マッチしている。

## 新たに判明したフォローアップ

- **yaml 辞書の誤り**: TORNTPHARM の `Torrent(Torrent / KKR)` エントリ。現状は実害が出ていないが要修正
- **ノートブックへの未反映**: `promoter_total_pct` のフォールバック修正 (INDGN / IXIGO 等) が `nse_owner_analysis.ipynb` Cell 12・14 に入っていない。全量再実行時に修正が失われる
- **分類ルールの完全統一**: 上記の dir/kmp 判定軸・外資ガード・独自tier（240銘柄規模）

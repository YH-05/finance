# NIFTY 750 Universe 差分レポート (2026-06-30 版)

**比較**: 前回確定版 `nifty750_universe_20260512.csv` (855 銘柄) vs 今回版 `nifty750_universe_20260630.csv` (864 銘柄)
**実行日**: 2026-07-15（取得データは技術的根拠により 2026-06-30 時点相当として採用、詳細は「6月末時点構成の扱い」節を参照）

## サマリー

| 項目 | 前回 (05-12) | 今回 (06-30) | 差分 |
|------|------|------|------|
| 総銘柄数 | 855 | 864 | +9 |
| OWNER 銘柄数 | 599 | 599 | 0 |
| NOT_OWNER 銘柄数 | 256 | 265 | +9 |
| NIFTY TOTAL MKT 構成銘柄数 (is_nifty_total_mkt=True) | 744 | 751 | +7 |

## 6月末時点構成の扱い

NSE の指数構成 API（`equity-stockIndices`）は現在時点の構成のみ返し、point-in-time（過去日付指定）取得に対応していない。また DB の `index_members` テーブルも履歴を保持しない単一スナップショット設計のため、「6月末時点」を厳密に再現する手段は存在しない。

一方、NSE 公式の指数方法論により、NIFTY 系指数の定期見直し（reconstitution）は**3月末・9月末に効力発生**（データ基準日は1月末・7月末）と確認できた。したがって 2026年6月末時点の構成は、直近3月の見直し後のまま変わっていないはずであり、次の変更は9月末まで発生しない。この根拠に基づき、**2026-07-15時点で取得した構成を6月末時点の構成として採用**した（ユーザー承認済み）。

取得は動的API不通のため、静的CSV配信（`nsearchives.nseindia.com/content/indices/ind_niftytotalmarket_list.csv`、Last-Modified: 2026-07-14）を新規実装（`IndicesCollector.fetch_index_constituents_archive()`）で使用した。

## NIFTY TOTAL MKT 構成差分（真の指数入れ替え）

前回universeの `is_nifty_total_mkt=True`（744銘柄）と、今回取得した最新構成（751銘柄）を比較。

### 新規採用 10 銘柄

| symbol | 会社名 | is_owner_company | promoter_total_pct | owner_flag_final_hybrid |
|---|---|---|---|---|
| AGL | Allcargo Global Limited | **True** | 63.28% | OWNER |
| RATNAMANI | Ratnamani Metals & Tubes Limited | **True** | 59.77% | OWNER |
| JSWDULUX | JSW Dulux Limited | False | 61.20% | OWNER_WEAK |
| SANOFICONR | Sanofi Consumer Healthcare India Limited | False | 71.27% | NOT_OWNER (MNC) |
| INDGN | Indegene Limited | False | 21.42% | OWNER_WEAK |
| IXIGO | Le Travenues Technology Limited | False | 13.35% | OWNER_WEAK |
| SUDARSCHEM | Sudarshan Chemical Industries Limited | False | 8.19% | OWNER (Stage1未達) |
| FIRSTCRY | Brainbees Solutions Limited | False | 5.31% | OWNER_WEAK |
| PINELABS | Pine Labs Limited | False | 2.66% | OWNER_WEAK |
| SAMHI | Samhi Hotels Limited | False | 2.14% | OWNER_WEAK |

OWNER確定は2銘柄（AGL, RATNAMANI）。INDGN/IXIGOはStage1閾値（10%）を超えているが、`owner_flag_final_hybrid`がyaml未知family・Tier2ハイブリッドルールにより`OWNER_WEAK`に留まり、`is_owner_company`はFalse（後述の既知課題を参照）。

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
- `notebook/NSE/data/exports/nse/nifty750_universe_20260630.csv`（864銘柄、確定版）
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
- `notebook/NSE/scripts/build_nifty750_universe.py`（`--db-path`/`--output-*`引数化）

## NSE接続障害の記録（今回発生・解決済み）

作業中、NSE公式サイトの`equity-stockIndices`動的APIが404エラーを返す障害が発生した（地理的ブロックではなく、このエンドポイント単体の問題と判明）。他の全API（`allIndices`, `corporate-share-holdings-master`, XBRL静的ファイル）は正常動作しており、代替の静的CSV配信（`nsearchives.nseindia.com/content/indices/`）で同等のデータを取得できることを確認し、恒久的な代替手段として実装した。

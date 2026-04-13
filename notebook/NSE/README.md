# NSE 全上場銘柄 データ取得パイプライン

## 概要

`nse_full_download.ipynb` は National Stock Exchange of India (NSE) の全上場銘柄データ（約 2,263 銘柄）を取得し、SQLite データベース (`data/cache/nse/nse_index.db`) に格納する Jupyter Notebook です。

`src/market/nse/` パッケージの Collector を使用し、4 段階のパイプラインでデータを収集します。

---

## 所要時間

| Phase | 内容 | 所要時間（全銘柄） |
|-------|------|--------------------|
| Phase 1 | 全上場株マスタ（EQUITY_L.csv） | 〜1 分 |
| Phase 2 | インデックス構成 + sector/industry 補完 | 〜5 分 |
| Phase 3 | 株主構成マスタ（2,200+ 銘柄ループ） | 〜20 分 |
| Phase 4 | XBRL 詳細株主データ | 〜10 分 |
| **合計** | | **30〜40 分** |

`LIMIT_SYMBOLS=10` を設定すると 10 銘柄のみで動作確認できます（2〜3 分）。

---

## 出力テーブル定義（DDL）

### `stocks` — 全上場銘柄マスタ

```sql
CREATE TABLE IF NOT EXISTS stocks (
    symbol          TEXT PRIMARY KEY,
    company_name    TEXT NOT NULL,
    isin            TEXT,
    series          TEXT DEFAULT 'EQ',
    listing_date    TEXT,
    face_value      REAL,
    industry        TEXT,
    sector          TEXT,
    basic_industry  TEXT,
    macro           TEXT,
    is_fno          INTEGER,
    last_price      REAL,
    previous_close  REAL,
    year_high       REAL,
    year_low        REAL,
    ffmc            REAL,
    pct_change_30d  REAL,
    pct_change_365d REAL,
    fetched_at      TEXT NOT NULL
)
```

### `index_members` — インデックス構成銘柄

```sql
CREATE TABLE IF NOT EXISTS index_members (
    index_name  TEXT NOT NULL,
    symbol      TEXT NOT NULL,
    priority    INTEGER,
    fetched_at  TEXT NOT NULL,
    PRIMARY KEY (index_name, symbol),
    FOREIGN KEY (symbol) REFERENCES stocks(symbol)
)
```

### `shareholdings` — 四半期別株主構成

```sql
CREATE TABLE IF NOT EXISTS shareholdings (
    symbol              TEXT NOT NULL,
    as_on_date          TEXT NOT NULL,
    promoter_pct        REAL,
    public_pct          REAL,
    employee_trust_pct  REAL DEFAULT 0,
    submission_date     TEXT,
    broadcast_date      TEXT,
    xbrl_url            TEXT,
    fetched_at          TEXT NOT NULL,
    PRIMARY KEY (symbol, as_on_date),
    FOREIGN KEY (symbol) REFERENCES stocks(symbol)
)
```

`promoter_pct` は `CorporateShareHolding.to_float_promoter_group_pct()` で float 変換してから INSERT します（REAL 型互換）。

### `shareholding_detail` — XBRL 詳細株主データ

```sql
CREATE TABLE IF NOT EXISTS shareholding_detail (
    symbol              TEXT NOT NULL,
    report_date         TEXT NOT NULL,
    category            TEXT NOT NULL,
    sub_category        TEXT NOT NULL DEFAULT '',
    shareholder_name    TEXT NOT NULL DEFAULT '',
    pan                 TEXT NOT NULL DEFAULT '',
    num_shareholders    INTEGER,
    num_fully_paid_shares INTEGER,
    num_voting_rights   INTEGER,
    pct_total_shares    REAL,
    pct_fully_diluted   REAL,
    num_shares_demat    INTEGER,
    is_category_total   INTEGER DEFAULT 1,
    fetched_at          TEXT NOT NULL,
    PRIMARY KEY (symbol, report_date, category, sub_category, shareholder_name),
    FOREIGN KEY (symbol) REFERENCES stocks(symbol)
)
```

Phase 4 は `WHERE NOT EXISTS` で冪等 INSERT します。

---

## 使い方

### フル実行（全銘柄）

1. ノートブックを開く
2. Cell 3（Config）で設定を確認し、必要に応じて変更
3. 「Run All」で全セルを実行

### 部分実行（特定 Phase のみ）

Cell 3 の `SKIP_PHASE_*` フラグを `True` に設定することで、特定の Phase をスキップできます。

```python
# Phase 1,2 完了済みの場合
SKIP_PHASE_1: bool = True
SKIP_PHASE_2: bool = True
SKIP_PHASE_3: bool = False  # Phase 3 から再開
SKIP_PHASE_4: bool = False
```

### 動作確認（LIMIT_SYMBOLS=10）

```python
# Cell 3 で設定
LIMIT_SYMBOLS: int = 10  # 10 銘柄のみで全 Phase を確認
```

全 Phase が 2〜3 分で完了します。

---

## データソース API 一覧

| データ | API / エンドポイント | Collector |
|--------|---------------------|-----------|
| 全銘柄マスタ | `https://nsearchives.nseindia.com/content/equities/EQUITY_L.csv` | `StockListCollector.fetch_stock_list()` |
| インデックス一覧 | `https://www.nseindia.com/api/allIndices` | `IndicesCollector.fetch_all_indices()` |
| インデックス構成 | `https://www.nseindia.com/api/equity-stockIndices?index=<name>` | `IndicesCollector.fetch_index()` |
| 株主構成 | `https://www.nseindia.com/api/corporate-share-holdings-master` | `ShareholdingCollector.fetch_shareholding()` |
| XBRL 詳細 | `https://nsearchives.nseindia.com/corporate/xbrl/<symbol>.xml` | `ShareholdingCollector.fetch_xbrl_detail()` |

---

## 既存 `scripts/` との関係

`scripts/` 以下の下記ファイルはスタンドアロン実装であり、非推奨です。
本ノートブックが後継実装として、`src/market/nse/` パッケージを使用します。

| スクリプト | 役割 | 移行先 |
|-----------|------|--------|
| `scripts/nse_index_shareholding.py` | Phase 1-3 相当のスタンドアロン実装 | 本ノートブック |
| `scripts/nse_parse_xbrl.py` | XBRL パーサーのスタンドアロン実装 | `src/market/nse/xbrl.py` |

---

## 関連ファイル

- 実装パッケージ: `src/market/nse/`
  - `collectors/stock_list.py` — `StockListCollector`
  - `collectors/indices.py` — `IndicesCollector`
  - `collectors/share_holding.py` — `ShareholdingCollector`
  - `xbrl.py` — `parse_xbrl`, `ParseResult`, `ShareholderRow`
- 計画書: `docs/project/project-106/project.md`

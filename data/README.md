# Data Directory

金融データの格納ディレクトリ。
- データベースファイル
- ニュース
- 株式市場関連データ
- 個別株データ
- マクロ経済データ
- 投資テーマに関連したデータ
- セルサイドやコンサルのレポート
- 自分の研究メモやレポート

## 構造

```
data/
├── sqlite/              # SQLite データベース（OLTP）
│   ├── market.db       # 市場データ（株価、為替、指標）
│   └── metadata.db     # メタデータ・取得履歴
│
├── duckdb/             # DuckDB データベース（OLAP）
│   └── analytics.duckdb
│
├── raw/                # 生データ（Parquet形式）
│   ├── yfinance/       # yfinance から取得
│   │   ├── stocks/     # 株価
│   │   ├── forex/      # 為替
│   │   └── indices/    # 指標
│   └── fred/           # FRED から取得
│       └── indicators/ # 経済指標
│
├── processed/          # 加工済みデータ
│   ├── daily/          # 日次集計
│   └── aggregated/     # 集約データ
│
├── news/               # 金融・株式市場ニュースデータ
│
├── market/             # マーケットデータ
│
├── stock/              # 個別株データ
│
├── macroeconomics/     # マクロ経済データ
│
├── investment_theme/   # 投資テーマ(AI, Healthcare, Energy, Commodity, Wealth, ...)関連データ
│
└── exports/            # エクスポート用
    ├── csv/
    └── json/
```

## 用途

| ディレクトリ | 用途 | 形式 |
|-------------|------|------|
| sqlite/ | トランザクション、正規化データ保存 | SQLite |
| duckdb/ | 分析クエリ、集計処理 | DuckDB |
| raw/ | 生データアーカイブ | Parquet |
| processed/ | 加工済みデータ | Parquet |
| exports/ | 外部連携用エクスポート | CSV/JSON |

## ファイル命名規則

### Parquet

```
{source}/{category}/{symbol}_{YYYYMMDD}_{YYYYMMDD}.parquet
```

例: `raw/yfinance/stocks/AAPL_20240101_20241231.parquet`

### CSV/JSON

```
{category}_{symbol}_{YYYYMMDD}.{ext}
```

例: `exports/csv/stock_AAPL_20241211.csv`

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
├── config/             # 設定ファイル
│   ├── finance-news-filter.json   # ニュースフィルター設定
│   ├── finance-news-themes.json   # ニューステーマ設定
│   ├── fred_series.json           # FRED系列定義
│   ├── rss-presets.json           # RSSフィードプリセット
│   └── yfinance_tickers.json      # yfinanceティッカー定義
│
├── schemas/            # JSONスキーマ定義
│   ├── raw-data.schema.json       # 生データスキーマ
│   ├── analysis.schema.json       # 分析結果スキーマ
│   ├── claims.schema.json         # 主張抽出スキーマ
│   ├── fact-checks.schema.json    # ファクトチェックスキーマ
│   ├── sentiment.schema.json      # センチメント分析スキーマ
│   ├── sec-filings.schema.json    # SEC提出書類スキーマ
│   └── ...                        # その他スキーマ
│
├── raw/                # 生データ
│   ├── yfinance/       # yfinance から取得（Parquet形式）
│   │   ├── stocks/     # 株価
│   │   ├── forex/      # 為替
│   │   └── indices/    # 指標
│   ├── fred/           # FRED から取得
│   │   └── indicators/ # 経済指標
│   └── rss/            # RSSフィードキャッシュ
│       └── {feed_id}/  # フィードごとのキャッシュ
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
| config/ | 設定ファイル（ティッカー、フィード定義等） | JSON |
| schemas/ | データ構造のJSONスキーマ定義 | JSON Schema |
| raw/ | 生データアーカイブ | Parquet/JSON |
| raw/rss/ | RSSフィードのキャッシュ | JSON |
| processed/ | 加工済みデータ | Parquet |
| news/ | 金融ニュースデータ | JSON |
| market/ | マーケットデータ（週次レポート等） | JSON |
| stock/ | 個別株データ | JSON |
| macroeconomics/ | マクロ経済データ | JSON |
| investment_theme/ | 投資テーマ関連データ | JSON |
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

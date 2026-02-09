# market.export

市場データのマルチフォーマットエクスポートモジュール。

## 概要

`MarketDataResult` および `AnalysisResult` を JSON、CSV、SQLite、AI エージェント向け JSON の4形式でエクスポートします。

**対応フォーマット:**

| フォーマット | メソッド | 用途 |
|-------------|---------|------|
| JSON | `to_json()` | 汎用データ交換 |
| CSV | `to_csv()` | スプレッドシート連携 |
| SQLite | `to_sqlite()` | ローカル DB 永続化（UPSERT 対応） |
| Agent JSON | `to_agent_json()` | AI エージェント向け構造化出力 |

## クイックスタート

### JSON エクスポート

```python
from market.export import DataExporter

exporter = DataExporter(result)

# 文字列として取得
json_str = exporter.to_json()

# ファイルに書き出し
exporter.to_json(output_path="./data/exports/aapl.json")

# メタデータなし
json_str = exporter.to_json(include_metadata=False)
```

### CSV エクスポート

```python
exporter = DataExporter(result)

# 文字列として取得
csv_str = exporter.to_csv()

# ファイルに書き出し
exporter.to_csv(output_path="./data/exports/aapl.csv")

# カスタム日付フォーマット
csv_str = exporter.to_csv(date_format="%Y/%m/%d")
```

### SQLite エクスポート（UPSERT）

```python
exporter = DataExporter(result)

# UPSERT（デフォルト: 既存行は更新、新規行は追加）
rows = exporter.to_sqlite("./data/market.db")
print(f"{rows} 行を書き込み")

# テーブル名を指定
rows = exporter.to_sqlite(
    db_path="./data/market.db",
    table_name="stock_prices",
)

# テーブルを置き換え
rows = exporter.to_sqlite("./data/market.db", if_exists="replace")
```

### AI エージェント向け JSON

```python
exporter = DataExporter(result)

# AgentOutput オブジェクトとして取得
agent_output = exporter.to_agent_json()

print(agent_output.summary)
# → "Market data for AAPL containing 252 data points from 2024-01-01 to 2024-12-31.
#    Price moved up 15.32% over the period."

print(agent_output.recommendations)
# → ["Strong upward trend detected (15.3% gain).", ...]

# ファイルに書き出し
exporter.to_agent_json(output_path="./data/agent/aapl.json")
```

## API リファレンス

### DataExporter

データエクスポーターのメインクラス。

**コンストラクタ:**

```python
DataExporter(
    result: MarketDataResult | AnalysisResult,
    date_format: str = "%Y-%m-%d",
)
```

| パラメータ | 型 | 説明 |
|-----------|-----|------|
| `result` | `MarketDataResult \| AnalysisResult` | エクスポート対象データ |
| `date_format` | `str` | 日付フォーマット文字列 |

**メソッド:**

| メソッド | 説明 | 戻り値 |
|---------|------|--------|
| `to_json(output_path, indent, include_metadata)` | JSON エクスポート | `str` |
| `to_csv(output_path, date_format, include_index)` | CSV エクスポート | `str` |
| `to_sqlite(db_path, table_name, if_exists)` | SQLite エクスポート | `int`（行数） |
| `to_agent_json(output_path, source_module, include_recommendations)` | Agent JSON エクスポート | `AgentOutput` |

**プロパティ:**

| プロパティ | 型 | 説明 |
|-----------|-----|------|
| `result` | `MarketDataResult \| AnalysisResult` | 元データ |
| `data` | `pd.DataFrame` | データフレーム |
| `symbol` | `str` | シンボル |

### to_sqlite の if_exists オプション

| 値 | 説明 |
|----|------|
| `"upsert"` | 既存行を更新、新規行を挿入（デフォルト） |
| `"replace"` | テーブルを削除して再作成 |
| `"append"` | 既存テーブルに追加 |
| `"fail"` | テーブルが存在する場合エラー |

### AgentOutput

AI エージェント向けの構造化出力。

| フィールド | 型 | 説明 |
|-----------|-----|------|
| `metadata` | `AgentOutputMetadata` | バージョン、ソース、期間等 |
| `summary` | `str` | 人間が読めるサマリー |
| `data` | `dict[str, Any]` | 構造化データ（最新値、統計、変動率等） |
| `recommendations` | `list[str]` | トレンド・ボラティリティに基づく推奨 |

### 例外

| 例外 | 説明 |
|------|------|
| `ExportError` | エクスポートエラー（format, path, cause 情報付き） |

## モジュール構成

```
market/export/
├── __init__.py    # パッケージエクスポート
├── exporter.py    # DataExporter 実装
└── README.md      # このファイル
```

## 関連モジュール

- [market.yfinance](../yfinance/README.md) - データ取得（エクスポート元）
- [market.fred](../fred/README.md) - データ取得（エクスポート元）
- [market.cache](../cache/README.md) - キャッシュ（SQLite 共通基盤）

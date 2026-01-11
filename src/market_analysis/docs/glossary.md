# プロジェクト用語集 (Glossary)

## 概要

このドキュメントは、market_analysis ライブラリで使用される用語の定義を管理します。
全てのドキュメント、コード、コミュニケーションで統一的に使用してください。

**更新日**: 2026-01-11

---

## ドメイン用語

プロジェクト固有のビジネス概念や金融市場に関する用語。

### OHLCV (Open, High, Low, Close, Volume)

**定義**: 金融市場の価格データの標準形式。一定期間の始値、高値、安値、終値、出来高を含む。

**説明**:
株式や為替等の時系列データの基本構造。本ライブラリでは pandas DataFrame の標準カラム名として使用。

**カラム構成**:

| カラム名 | 型 | 説明 |
|----------|-----|------|
| Date | datetime64[ns] | 日付 (index) |
| Open | float64 | 始値 |
| High | float64 | 高値 |
| Low | float64 | 安値 |
| Close | float64 | 終値 |
| Volume | float64 | 出来高 |
| Adj Close | float64 | 調整後終値 |

**関連用語**: [終値](#終値-close-price)、[調整後終値](#調整後終値-adjusted-close)

**英語表記**: OHLCV (Open, High, Low, Close, Volume)

### 終値 (Close Price)

**定義**: 取引日の最終約定価格。

**説明**:
テクニカル分析において最も重要な価格データ。移動平均、リターン計算等の基準として使用。

**関連用語**: [OHLCV](#ohlcv-open-high-low-close-volume)、[調整後終値](#調整後終値-adjusted-close)

**英語表記**: Close Price

### 調整後終値 (Adjusted Close)

**定義**: 株式分割や配当を反映した終値。

**説明**:
長期の株価分析では、株式分割や配当落ちの影響を除外するために調整後終値を使用。yfinance から取得するデータに含まれる。

**関連用語**: [終値](#終値-close-price)

**英語表記**: Adjusted Close Price

### ティッカーシンボル (Ticker Symbol)

**定義**: 株式や金融商品を識別するための略称コード。

**説明**:
yfinance でデータを取得する際に使用する識別子。市場によって形式が異なる。

**形式の例**:

| 市場 | 形式 | 例 |
|------|------|-----|
| 米国株 | そのまま | AAPL, MSFT, GOOGL |
| 日本株 | .T サフィックス | 7203.T (トヨタ) |
| 為替 | =X サフィックス | USDJPY=X |
| 先物 | =F サフィックス | GC=F (金), CL=F (原油) |
| 主要指数 | ^ プレフィックス | ^GSPC (S&P 500) |

**関連用語**: [通貨ペア](#通貨ペア-currency-pair)

**英語表記**: Ticker Symbol

### 通貨ペア (Currency Pair)

**定義**: 為替取引において、2つの通貨の組み合わせ。

**説明**:
ベース通貨（左側）とクォート通貨（右側）で構成。本ライブラリでは「USDJPY」形式で指定し、内部で「USDJPY=X」に変換。

**例**:
- USD/JPY: 米ドル/日本円
- EUR/USD: ユーロ/米ドル
- GBP/USD: 英ポンド/米ドル

**関連用語**: [ティッカーシンボル](#ティッカーシンボル-ticker-symbol)

**英語表記**: Currency Pair

### 日次リターン (Daily Return)

**定義**: 1日あたりの価格変化率。

**計算式**:
```
Return_t = (Price_t - Price_{t-1}) / Price_{t-1}
```

**説明**:
投資パフォーマンスの基本指標。ボラティリティや相関分析の入力データとして使用。

**関連用語**: [ボラティリティ](#ボラティリティ-volatility)

**英語表記**: Daily Return

### ボラティリティ (Volatility)

**定義**: 価格変動の大きさを表す指標。リターンの標準偏差で計算。

**計算式**:
```
Volatility = std(Returns) * sqrt(252)  # 年率換算
```

**説明**:
リスク指標として使用。年率換算には取引日数（通常252日）の平方根を乗じる。

**関連用語**: [日次リターン](#日次リターン-daily-return)、[相関分析](#相関分析-correlation-analysis)

**英語表記**: Volatility

### 相関分析 (Correlation Analysis)

**定義**: 複数の資産間の価格変動の関連性を分析する手法。

**説明**:
相関係数は -1 から 1 の範囲で、1 に近いほど同じ方向に動き、-1 に近いほど逆方向に動く。ポートフォリオのリスク分散に活用。

**計算方法**:
- Pearson（線形相関）
- Spearman（順位相関）
- Kendall（順序相関）

**関連用語**: [ベータ値](#ベータ値-beta)、[ローリング相関](#ローリング相関-rolling-correlation)

**英語表記**: Correlation Analysis

### ローリング相関 (Rolling Correlation)

**定義**: 一定期間のウィンドウを移動させながら計算する相関係数。

**説明**:
時系列で相関の変化を追跡可能。市場環境の変化を検出するのに有用。

**関連用語**: [相関分析](#相関分析-correlation-analysis)

**英語表記**: Rolling Correlation

### ベータ値 (Beta)

**定義**: ベンチマークに対する個別銘柄の感応度を示す指標。

**計算式**:
```
Beta = Cov(Stock, Benchmark) / Var(Benchmark)
```

**説明**:
- Beta > 1: ベンチマークより変動が大きい
- Beta = 1: ベンチマークと同じ変動
- Beta < 1: ベンチマークより変動が小さい
- Beta < 0: ベンチマークと逆方向に動く

**関連用語**: [相関分析](#相関分析-correlation-analysis)

**英語表記**: Beta

---

## テクニカル指標

テクニカル分析で使用される計算指標。

### 単純移動平均 (SMA: Simple Moving Average)

**定義**: 指定期間の終値の単純平均。

**計算式**:
```
SMA_n = (P_1 + P_2 + ... + P_n) / n
```

**説明**:
トレンドの方向性を判断する基本的な指標。期間が長いほど滑らかな線になり、短いほど価格に追従する。

**カラム名**: `SMA_{期間}`（例: SMA_20, SMA_50）

**関連用語**: [指数移動平均](#指数移動平均-ema-exponential-moving-average)

**英語表記**: Simple Moving Average (SMA)

### 指数移動平均 (EMA: Exponential Moving Average)

**定義**: 直近のデータに重みを置いた移動平均。

**計算式**:
```
EMA_t = Price_t * k + EMA_{t-1} * (1 - k)
k = 2 / (period + 1)
```

**説明**:
SMA より価格変動に敏感に反応。トレンド転換の早期検出に有用。

**カラム名**: `EMA_{期間}`（例: EMA_20, EMA_50）

**関連用語**: [単純移動平均](#単純移動平均-sma-simple-moving-average)

**英語表記**: Exponential Moving Average (EMA)

---

## 技術用語

プロジェクトで使用している技術・フレームワーク・ツールに関する用語。

### yfinance

**定義**: Yahoo Finance API の Python ラッパーライブラリ。

**公式サイト**: https://github.com/ranaroussi/yfinance

**本プロジェクトでの用途**:
株価、為替、コモディティ、指数データの取得に使用。無料で豊富な市場カバレッジを提供。

**バージョン**: >=0.2.0

**シンボル形式**:
- 米国株: `AAPL`
- 日本株: `7203.T`
- 為替: `USDJPY=X`
- コモディティ: `GC=F`
- 指数: `^GSPC`

**関連ドキュメント**: [アーキテクチャ設計書](./architecture.md)

### FRED API

**定義**: Federal Reserve Economic Data の公開 API。

**公式サイト**: https://fred.stlouisfed.org/docs/api/fred/

**本プロジェクトでの用途**:
経済指標データ（金利、GDP、CPI、失業率等）の取得に使用。

**バージョン**: fredapi >=0.5.0

**主要シリーズID**:

| シリーズID | 指標名 |
|-----------|--------|
| DGS10 | 10年国債金利 |
| GDP | 国内総生産 |
| CPIAUCSL | 消費者物価指数 |
| UNRATE | 失業率 |
| FEDFUNDS | フェデラルファンド金利 |

**設定**:
- 環境変数 `FRED_API_KEY` で API キーを設定
- API キー取得: https://fred.stlouisfed.org/docs/api/api_key.html

**関連ドキュメント**: [アーキテクチャ設計書](./architecture.md)

### plotly

**定義**: インタラクティブなチャートを生成する Python ライブラリ。

**公式サイト**: https://plotly.com/python/

**本プロジェクトでの用途**:
価格チャート、相関ヒートマップの生成。marimo ノートブックでのインタラクティブ表示に対応。

**バージョン**: >=5.18.0

**出力形式**: PNG, SVG, HTML

**関連ドキュメント**: [機能設計書](./functional-design.md)

### marimo

**定義**: リアクティブな Python ノートブック環境。

**公式サイト**: https://marimo.io/

**本プロジェクトでの用途**:
分析結果のインタラクティブな可視化とレポート作成。plotly との統合により動的なチャート表示が可能。

**関連ドキュメント**: [機能設計書](./functional-design.md)

### pandas

**定義**: データ分析のための Python ライブラリ。

**公式サイト**: https://pandas.pydata.org/

**本プロジェクトでの用途**:
市場データの格納、変換、分析処理の基盤。DataFrame が主要なデータ構造。

**バージョン**: >=2.0.0

**主要データ構造**:
- DataFrame: 2次元のラベル付きデータ構造
- Series: 1次元のラベル付きデータ構造

**関連ドキュメント**: [アーキテクチャ設計書](./architecture.md)

### structlog

**定義**: 構造化ログを出力する Python ライブラリ。

**公式サイト**: https://www.structlog.org/

**本プロジェクトでの用途**:
全操作のログ出力。JSON 形式でのログ出力をサポートし、運用時のトレーサビリティを確保。

**バージョン**: >=24.0.0

**使用方法**:
```python
from market_analysis.utils.logging_config import get_logger

logger = get_logger(__name__)
logger.info("data_fetched", symbol="AAPL", rows=252)
```

**関連ドキュメント**: [開発ガイドライン](./development-guidelines.md)

### pyright

**定義**: Microsoft が開発した Python の静的型チェッカー。

**公式サイト**: https://github.com/microsoft/pyright

**本プロジェクトでの用途**:
strict モードで全コードの型チェックを実施。型安全性を確保し、実行時エラーを防止。

**バージョン**: latest

**関連ドキュメント**: [開発ガイドライン](./development-guidelines.md)

### Hypothesis

**定義**: プロパティベーステストのための Python ライブラリ。

**公式サイト**: https://hypothesis.readthedocs.io/

**本プロジェクトでの用途**:
テクニカル指標計算の境界値テスト。自動生成されたテストデータで不変条件を検証。

**バージョン**: >=6.0.0

**関連ドキュメント**: [開発ガイドライン](./development-guidelines.md)

---

## 略語・頭字語

### API

**正式名称**: Application Programming Interface

**意味**: アプリケーション間の通信規約。

**本プロジェクトでの使用**:
yfinance API、FRED API でデータを取得。また、MarketData、Analysis、Chart クラスがユーザー向け API を提供。

### TTL

**正式名称**: Time To Live

**意味**: データやキャッシュの有効期限。

**本プロジェクトでの使用**:
SQLite キャッシュのデフォルト TTL は 24 時間。`cache_ttl_hours` パラメータで変更可能。

### TDD

**正式名称**: Test-Driven Development

**意味**: テスト駆動開発。テストを先に書いてから実装を行う開発手法。

**本プロジェクトでの適用**:
全ての新機能開発で TDD を採用。

**手順**:
1. テストを書く
2. テストを実行 → 失敗を確認
3. 実装を書く
4. テストを実行 → 成功を確認
5. リファクタリング

**参考**: [開発ガイドライン](./development-guidelines.md)

### LRD

**正式名称**: Library Requirements Document

**意味**: ライブラリ要求定義書。

**本プロジェクトでの使用**:
market_analysis ライブラリの機能要件、非機能要件を定義したドキュメント。

**参考**: [LRD](./library-requirements.md)

### MVI

**正式名称**: Minimum Viable Implementation

**意味**: 最小実行可能実装。最初にリリースする最小限の機能セット。

**本プロジェクトでの使用**:
LRD の P0 優先度の機能が MVI スコープ。

---

## アーキテクチャ用語

システム設計・アーキテクチャに関する用語。

### レイヤードアーキテクチャ (Layered Architecture)

**定義**: システムを役割ごとに複数の層に分割し、上位層から下位層への一方向の依存関係を持たせる設計パターン。

**本プロジェクトでの適用**:
3層アーキテクチャを採用。

```
┌─────────────────────────────────────────────────────────────┐
│                    インターフェース層 (api/)                  │
│  MarketData  │  Analysis  │  Chart                          │
│  - 入力バリデーション                                        │
│  - 戻り値の型保証                                            │
├─────────────────────────────────────────────────────────────┤
│                    コアロジック層 (core/)                     │
│  DataFetcher  │  Analyzer  │  Visualizer  │  Exporter       │
│  - ビジネスロジック                                          │
│  - データ変換                                                │
├─────────────────────────────────────────────────────────────┤
│                    インフラ層 (utils/)                        │
│  CacheManager  │  RetryHandler  │  Logger  │  Validator     │
│  - 技術的関心事                                              │
│  - 外部サービス接続                                          │
└─────────────────────────────────────────────────────────────┘
```

**メリット**:
- 関心の分離による保守性向上
- テストが容易（各層を独立してテスト可能）
- 変更の影響範囲が限定的

**依存関係のルール**:
- api/ → core/ → utils/ の一方向のみ許可
- 下位層から上位層への依存は禁止

**関連ドキュメント**: [アーキテクチャ設計書](./architecture.md)

### インターフェース層 (Interface Layer)

**定義**: ユーザー向け公開 API を提供するレイヤー。

**本プロジェクトでの適用**:
`api/` ディレクトリに配置。入力バリデーション、戻り値の型保証を担当。

**主要クラス**: MarketData, Analysis, Chart

**関連用語**: [レイヤードアーキテクチャ](#レイヤードアーキテクチャ-layered-architecture)

### コアロジック層 (Core Layer)

**定義**: ビジネスロジックを実装するレイヤー。

**本プロジェクトでの適用**:
`core/` ディレクトリに配置。データ取得、分析計算、可視化、エクスポートのロジックを実装。

**主要クラス**: DataFetcher, Analyzer, Visualizer, Exporter

**関連用語**: [レイヤードアーキテクチャ](#レイヤードアーキテクチャ-layered-architecture)

### インフラ層 (Infrastructure Layer)

**定義**: 横断的関心事と技術的詳細を扱うレイヤー。

**本プロジェクトでの適用**:
`utils/` ディレクトリに配置。ログ、キャッシュ、リトライ、バリデーション等を担当。

**主要コンポーネント**: CacheManager, RetryHandler, Logger, Validator

**関連用語**: [レイヤードアーキテクチャ](#レイヤードアーキテクチャ-layered-architecture)

### キャッシュ (Cache)

**定義**: データの再取得を避けるための一時保存機構。

**本プロジェクトでの適用**:
SQLite ベースのローカルキャッシュ。API 呼び出しの削減とオフライン時のフォールバックを提供。

**キャッシュキー形式**:
```
{source}:{symbol}:{start_date}:{end_date}
```

例: `yfinance:AAPL:2024-01-01:2024-12-31`

**デフォルト設定**:
- TTL: 24時間
- パス: `~/.market_analysis/cache.db`

**関連ドキュメント**: [アーキテクチャ設計書](./architecture.md)

---

## エラー・例外

システムで定義されているエラーと例外。

### MarketAnalysisError

**クラス名**: `MarketAnalysisError`

**継承元**: `Exception`

**発生条件**:
market_analysis ライブラリの全エラーの基底クラス。直接送出されることはなく、サブクラスとして使用。

**関連エラー**: DataFetchError, ValidationError, AnalysisError, ExportError

### DataFetchError

**クラス名**: `DataFetchError`

**継承元**: `MarketAnalysisError`

**発生条件**:
外部 API（yfinance, FRED）からのデータ取得に失敗した場合に発生。

**エラーコード**: `DATA_FETCH_ERROR`, `API_CONNECTION_ERROR`, `RATE_LIMIT_ERROR`

**属性**:
- `symbol`: 対象シンボル
- `source`: データソース名
- `retry_count`: リトライ回数

**対処方法**:
- ユーザー: ネットワーク接続を確認、シンボルの妥当性を確認
- 開発者: リトライ設定を調整、キャッシュフォールバックを確認

**実装箇所**: `src/market_analysis/errors.py`

### ValidationError

**クラス名**: `ValidationError`

**継承元**: `MarketAnalysisError`

**発生条件**:
入力パラメータがビジネスルールに違反した場合に発生。

**エラーコード**: `INVALID_SYMBOL`, `INVALID_DATE_RANGE`

**属性**:
- `field`: エラーが発生したフィールド名
- `value`: 入力された値
- `message`: エラーメッセージ

**対処方法**:
- ユーザー: エラーメッセージに従って入力を修正
- 開発者: バリデーションロジックを確認

**実装箇所**: `src/market_analysis/errors.py`

### AnalysisError

**クラス名**: `AnalysisError`

**継承元**: `MarketAnalysisError`

**発生条件**:
分析処理でエラーが発生した場合（データ不足等）。

**属性**:
- `operation`: 失敗した操作名
- `message`: エラーメッセージ

**対処方法**:
- ユーザー: データの期間や件数を確認
- 開発者: 入力データの検証を強化

**実装箇所**: `src/market_analysis/errors.py`

### ExportError

**クラス名**: `ExportError`

**継承元**: `MarketAnalysisError`

**発生条件**:
データのエクスポート（ファイル出力等）に失敗した場合。

**エラーコード**: `EXPORT_ERROR`

**属性**:
- `format`: 出力形式
- `message`: エラーメッセージ

**対処方法**:
- ユーザー: 出力先パスの権限を確認、ディスク容量を確認
- 開発者: ファイル操作のエラーハンドリングを確認

**実装箇所**: `src/market_analysis/errors.py`

---

## データモデル用語

データ構造に関する用語。

### MarketDataResult

**定義**: 市場データ取得結果を表すデータクラス。

**主要フィールド**:
- `data`: pd.DataFrame - OHLCV データ
- `source`: DataSource - データソース情報
- `start_date`: datetime - データ開始日
- `end_date`: datetime - データ終了日
- `symbol`: str - ティッカーシンボル
- `data_type`: Literal - データ種別

**関連用語**: [OHLCV](#ohlcv-open-high-low-close-volume)

### AnalysisResult

**定義**: テクニカル分析結果を表すデータクラス。

**主要フィールド**:
- `data`: pd.DataFrame - 分析済みデータ
- `indicators`: list[str] - 追加された指標名
- `metadata`: dict - メタデータ

**関連用語**: [単純移動平均](#単純移動平均-sma-simple-moving-average)、[指数移動平均](#指数移動平均-ema-exponential-moving-average)

### AgentOutput

**定義**: AI エージェント向けの構造化出力形式。

**主要フィールド**:
- `success`: bool - 成功フラグ
- `data`: list[dict] | None - JSON シリアライズ可能なデータ
- `metadata`: AgentOutputMetadata | None - メタデータ
- `error`: str | None - エラーメッセージ
- `error_code`: str | None - エラーコード

**使用例**:
```json
{
  "success": true,
  "data": [...],
  "metadata": {
    "source": "yfinance",
    "symbol": "AAPL",
    "record_count": 252
  }
}
```

---

## 索引

### あ行
- [インターフェース層](#インターフェース層-interface-layer) - アーキテクチャ用語
- [インフラ層](#インフラ層-infrastructure-layer) - アーキテクチャ用語

### か行
- [キャッシュ](#キャッシュ-cache) - アーキテクチャ用語
- [コアロジック層](#コアロジック層-core-layer) - アーキテクチャ用語

### さ行
- [指数移動平均 (EMA)](#指数移動平均-ema-exponential-moving-average) - テクニカル指標
- [終値 (Close Price)](#終値-close-price) - ドメイン用語
- [相関分析](#相関分析-correlation-analysis) - ドメイン用語

### た行
- [単純移動平均 (SMA)](#単純移動平均-sma-simple-moving-average) - テクニカル指標
- [ティッカーシンボル](#ティッカーシンボル-ticker-symbol) - ドメイン用語
- [調整後終値 (Adjusted Close)](#調整後終値-adjusted-close) - ドメイン用語
- [通貨ペア](#通貨ペア-currency-pair) - ドメイン用語

### な行
- [日次リターン (Daily Return)](#日次リターン-daily-return) - ドメイン用語

### は行
- [ベータ値 (Beta)](#ベータ値-beta) - ドメイン用語
- [ボラティリティ (Volatility)](#ボラティリティ-volatility) - ドメイン用語

### ら行
- [レイヤードアーキテクチャ](#レイヤードアーキテクチャ-layered-architecture) - アーキテクチャ用語
- [ローリング相関](#ローリング相関-rolling-correlation) - ドメイン用語

### A-Z
- [AgentOutput](#agentoutput) - データモデル用語
- [AnalysisError](#analysiserror) - エラー・例外
- [AnalysisResult](#analysisresult) - データモデル用語
- [API](#api) - 略語
- [DataFetchError](#datafetcherror) - エラー・例外
- [ExportError](#exporterror) - エラー・例外
- [FRED API](#fred-api) - 技術用語
- [Hypothesis](#hypothesis) - 技術用語
- [LRD](#lrd) - 略語
- [MarketAnalysisError](#marketanalysiserror) - エラー・例外
- [MarketDataResult](#marketdataresult) - データモデル用語
- [marimo](#marimo) - 技術用語
- [MVI](#mvi) - 略語
- [OHLCV](#ohlcv-open-high-low-close-volume) - ドメイン用語
- [pandas](#pandas) - 技術用語
- [plotly](#plotly) - 技術用語
- [pyright](#pyright) - 技術用語
- [structlog](#structlog) - 技術用語
- [TDD](#tdd) - 略語
- [TTL](#ttl) - 略語
- [ValidationError](#validationerror) - エラー・例外
- [yfinance](#yfinance) - 技術用語

---

## 変更履歴

| 日付 | 変更者 | 変更内容 |
|------|--------|----------|
| 2026-01-11 | 初版作成 | 全カテゴリの用語を定義 |

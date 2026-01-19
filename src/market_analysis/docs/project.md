# market_analysis プロジェクト

**ステータス**: 主要機能完了
**GitHub Project**: [#6](https://github.com/users/YH-05/projects/6)
**作成日**: 2026-01-01
**主要機能完了日**: 2026-01-18

## 概要

金融市場のデータ取得・分析・可視化を行う Python ライブラリ。
グローバル市場（株式、為替、債券、コモディティ）のデータを yfinance と FRED API から取得し、
テクニカル分析指標の計算、相関分析、チャート生成を提供する。

**主な用途:**

- 株価・為替・指数データの取得と分析
- マクロ経済指標（金利、GDP、インフレ率等）の追跡
- 複数資産間の相関分析
- 分析結果の可視化とエクスポート

## 主要機能

### データ取得（Data Fetching）

- [x] yfinance による株価・為替・指数データ取得
- [x] FRED API による経済指標データ取得
- [x] コモディティ（金、原油等）データ取得（yfinance経由）
- [x] SQLite によるローカルキャッシュ
- [x] yfinance のティッカー管理

### 分析機能（Analysis）

- [x] 基本指標: 移動平均、リターン、ボラティリティ - Issue: [#21](https://github.com/YH-05/finance/issues/21), [#22](https://github.com/YH-05/finance/issues/22)
- [x] 相関分析: 複数銘柄間の相関係数、ベータ値 - Issue: [#23](https://github.com/YH-05/finance/issues/23)
- [ ] セクター分析: セクター別パフォーマンス比較

### 可視化（Visualization）

- [x] ChartBuilder 基盤クラス - Issue: [#38](https://github.com/YH-05/finance/issues/38)
- [x] 価格チャート（ローソク足、ライン） - Issue: [#24](https://github.com/YH-05/finance/issues/24)
- [x] テクニカル指標オーバーレイ - Issue: [#24](https://github.com/YH-05/finance/issues/24)
- [x] 相関ヒートマップ - Issue: [#25](https://github.com/YH-05/finance/issues/25)
- [x] PNG/SVG 形式でのエクスポート - Issue: [#24](https://github.com/YH-05/finance/issues/24)

### データ出力（Export）

- [x] pandas DataFrame
- [x] JSON/CSV エクスポート - Issue: [#26](https://github.com/YH-05/finance/issues/26)
- [x] SQLite データベース保存 - Issue: [#26](https://github.com/YH-05/finance/issues/26)
- [x] AI エージェント向け構造化 JSON - Issue: [#26](https://github.com/YH-05/finance/issues/26)

### 運用機能（Operations）

- [ ] 日次バッチ処理対応
- [ ] 定期実行（scheduler）対応

## 技術的考慮事項

### 技術スタック

- **データ取得**: yfinance, fredapi
- **データ処理**: pandas, numpy
- **可視化**: plotly（メイン）, marimo（ノートブック）, matplotlib/seaborn（フォールバック）
- **永続化**: SQLite (sqlite3)
- **スケジューリング**: schedule または APScheduler

### 制約・依存関係

- Python 3.12+
- yfinance の API レート制限に注意
- FRED API キーが必要（環境変数 `FRED_API_KEY`）
- 無料 API のため、リアルタイムデータは非対応

### 対象市場

- **株式**: グローバル主要指数（日経225、S&P500、FTSE等）
- **為替**: 主要通貨ペア（USD/JPY、EUR/USD等）
- **債券**: 米国債金利
- **コモディティ**: 金、原油、天然ガス等

## 成功基準

1. **機能完成度**
    - yfinance/FRED からデータを正常に取得できる
    - 基本指標と相関分析が正確に計算される
    - チャートが正しく生成・エクスポートされる

2. **品質基準**
    - テストカバレッジ 80% 以上
    - 型チェック（pyright）エラーなし
    - ドキュメント完備

3. **運用性**
    - 日次バッチ処理が安定稼働する
    - エラー時の適切なログ出力
    - AI エージェントから利用可能な JSON API

---

## Worktree 並列開発計画

### feature/correlation ブランチ

相関分析機能の実装

| Issue                                             | タイトル                                          | 優先度 | 見積もり |
| ------------------------------------------------- | ------------------------------------------------- | ------ | -------- |
| [#23](https://github.com/YH-05/finance/issues/23) | CorrelationAnalyzer の実装（相関係数 + ベータ値） | P0     | 4h       |

**依存関係**: #21 (完了) -> #23 -> #28

### feature/visualize ブランチ

チャート生成機能の実装

| Issue                                             | タイトル                                                  | 優先度 | 見積もり |
| ------------------------------------------------- | --------------------------------------------------------- | ------ | -------- |
| [#38](https://github.com/YH-05/finance/issues/38) | ChartBuilder 基盤クラス                                   | P0     | 2h       |
| [#24](https://github.com/YH-05/finance/issues/24) | PlotlyChart（価格チャート + オーバーレイ + エクスポート） | P0     | 6h       |
| [#25](https://github.com/YH-05/finance/issues/25) | HeatmapChart                                              | P0     | 1.5h     |

**依存関係**: #38 -> #24, #25 -> #29

### feature/export ブランチ

データエクスポート機能の実装

| Issue                                             | タイトル                                      | 優先度 | 見積もり |
| ------------------------------------------------- | --------------------------------------------- | ------ | -------- |
| [#26](https://github.com/YH-05/finance/issues/26) | Exporter（基盤 + JSON/CSV + SQLite + AI向け） | P0     | 6h       |

**依存関係**: #11, #12 (完了) -> #26 -> #27

---

> このファイルは `/new-project @src/market_analysis/docs/project.md` で詳細化されました

---

## GitHub Project #6 Issue一覧

| # | タイトル | ステータス |
|---|---------|----------|
| [#5](https://github.com/YH-05/finance/issues/5) | プロジェクト基盤の初期化 | Done |
| [#11](https://github.com/YH-05/finance/issues/11) | 型定義の作成 | Done |
| [#12](https://github.com/YH-05/finance/issues/12) | エラー型の定義 | Done |
| [#13](https://github.com/YH-05/finance/issues/13) | ロギング設定の実装 | Done |
| [#14](https://github.com/YH-05/finance/issues/14) | バリデーション機能の実装 | Done |
| [#15](https://github.com/YH-05/finance/issues/15) | リトライ機能の実装 | Done |
| [#16](https://github.com/YH-05/finance/issues/16) | キャッシュ機能の実装 | Done |
| [#17](https://github.com/YH-05/finance/issues/17) | BaseDataFetcher 抽象クラスの実装 | Done |
| [#18](https://github.com/YH-05/finance/issues/18) | YFinanceFetcher の実装 | Done |
| [#19](https://github.com/YH-05/finance/issues/19) | FREDFetcher の実装 | Done |
| [#20](https://github.com/YH-05/finance/issues/20) | DataFetcherFactory の実装 | Done |
| [#21](https://github.com/YH-05/finance/issues/21) | IndicatorCalculator の実装 | Done |
| [#22](https://github.com/YH-05/finance/issues/22) | Analyzer クラスの実装 | Done |
| [#23](https://github.com/YH-05/finance/issues/23) | CorrelationAnalyzer の実装 | Done |
| [#24](https://github.com/YH-05/finance/issues/24) | PlotlyChart クラスの実装 | Done |
| [#25](https://github.com/YH-05/finance/issues/25) | HeatmapChart クラスの実装 | Done |
| [#26](https://github.com/YH-05/finance/issues/26) | Exporter クラスの実装 | Done |
| [#27](https://github.com/YH-05/finance/issues/27) | MarketData API の実装 | Done |
| [#28](https://github.com/YH-05/finance/issues/28) | Analysis API の実装 | Done |
| [#29](https://github.com/YH-05/finance/issues/29) | Chart API の実装 | Done |
| [#30](https://github.com/YH-05/finance/issues/30) | パッケージエクスポートの設定 | Done |
| [#33](https://github.com/YH-05/finance/issues/33) | yfinance のティッカー管理 | Done |
| [#38](https://github.com/YH-05/finance/issues/38) | ChartBuilder 基盤クラスの実装 | Done |
| [#316](https://github.com/YH-05/finance/issues/316) | Chart.price_chart で Close カラムが見つからない ValueError を修正 | Done |
| [#324](https://github.com/YH-05/finance/issues/324) | fetch_stock で複数銘柄の株価データを一括取得できるようにする | Done |
| [#325](https://github.com/YH-05/finance/issues/325) | fetch_fred で複数 series_id の一括取得と統一データフレーム形式への変更 | Todo |
| [#374](https://github.com/YH-05/finance/issues/374) | [refactor]: print を logger.error に置き換え（analysis.py） | Todo |
| [#375](https://github.com/YH-05/finance/issues/375) | [refactor]: _find_column の再利用によるコード重複削減 | Todo |
| [#376](https://github.com/YH-05/finance/issues/376) | [refactor]: 未使用変数・パラメータの整理（analysis.py） | Todo |
| [#377](https://github.com/YH-05/finance/issues/377) | [refactor]: コメントアウトされたコード（TICKERS_WORLD）と対応メソッドの整理 | Todo |
| [#378](https://github.com/YH-05/finance/issues/378) | [refactor]: MarketPerformanceAnalyzer の責務分離 | Todo |
| [#379](https://github.com/YH-05/finance/issues/379) | [refactor]: Analysis クラスから静的メソッドを CorrelationApi クラスに分離 | Todo |
| [#380](https://github.com/YH-05/finance/issues/380) | [refactor]: パラメータ検証ロジックの共通化（デコレータ/バリデータ） | Todo |
| [#381](https://github.com/YH-05/finance/issues/381) | [refactor]: MarketPerformanceAnalyzer の遅延読み込み（Lazy Loading）化 | Todo |
| [#382](https://github.com/YH-05/finance/issues/382) | [refactor]: MarketPerformanceAnalyzer への依存性注入（DI）パターン導入 | Todo |
| [#383](https://github.com/YH-05/finance/issues/383) | [refactor]: 非同期データ取得の導入 | Todo |

**25件完了 / 36件中** (2026-01-19)

---

**最終更新**: 2026-01-19
**更新内容**: コード分析レポート（analysis.py）の要対処事項をIssue化（#374-#383）、GitHub Project #6に追加

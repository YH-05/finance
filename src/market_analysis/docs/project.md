# market_analysis プロジェクト

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
- [ ] 相関分析: 複数銘柄間の相関係数、ベータ値 - Issue: [#23](https://github.com/YH-05/finance/issues/23)
- [ ] セクター分析: セクター別パフォーマンス比較

### 可視化（Visualization）
- [ ] ChartBuilder 基盤クラス - Issue: [#38](https://github.com/YH-05/finance/issues/38)
- [ ] 価格チャート（ローソク足、ライン） - Issue: [#24](https://github.com/YH-05/finance/issues/24)
- [ ] テクニカル指標オーバーレイ - Issue: [#24](https://github.com/YH-05/finance/issues/24)
- [ ] 相関ヒートマップ - Issue: [#25](https://github.com/YH-05/finance/issues/25)
- [ ] PNG/SVG 形式でのエクスポート - Issue: [#24](https://github.com/YH-05/finance/issues/24)

### データ出力（Export）
- [ ] pandas DataFrame
- [ ] JSON/CSV エクスポート - Issue: [#26](https://github.com/YH-05/finance/issues/26)
- [ ] SQLite データベース保存 - Issue: [#26](https://github.com/YH-05/finance/issues/26)
- [ ] AI エージェント向け構造化 JSON - Issue: [#26](https://github.com/YH-05/finance/issues/26)

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

| Issue | タイトル | 優先度 | 見積もり |
|-------|---------|--------|---------|
| [#23](https://github.com/YH-05/finance/issues/23) | CorrelationAnalyzer の実装（相関係数 + ベータ値） | P0 | 4h |

**依存関係**: #21 (完了) -> #23 -> #28

### feature/visualize ブランチ
チャート生成機能の実装

| Issue | タイトル | 優先度 | 見積もり |
|-------|---------|--------|---------|
| [#38](https://github.com/YH-05/finance/issues/38) | ChartBuilder 基盤クラス | P0 | 2h |
| [#24](https://github.com/YH-05/finance/issues/24) | PlotlyChart（価格チャート + オーバーレイ + エクスポート） | P0 | 6h |
| [#25](https://github.com/YH-05/finance/issues/25) | HeatmapChart | P0 | 1.5h |

**依存関係**: #38 -> #24, #25 -> #29

### feature/export ブランチ
データエクスポート機能の実装

| Issue | タイトル | 優先度 | 見積もり |
|-------|---------|--------|---------|
| [#26](https://github.com/YH-05/finance/issues/26) | Exporter（基盤 + JSON/CSV + SQLite + AI向け） | P0 | 6h |

**依存関係**: #11, #12 (完了) -> #26 -> #27

---

> このファイルは `/new-project @src/market_analysis/docs/project.md` で詳細化されました

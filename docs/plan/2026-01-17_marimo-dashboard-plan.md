# marimo マーケットダッシュボード実装計画

## 概要

`notebook_sample/Market-Report2.py` を参考に、株式市場・マクロ経済データ確認用のインタラクティブダッシュボードを marimo で実装する。

## プロジェクト管理

### 作成するリソース

1. **docs/project/project-17/** - プロジェクトドキュメント
2. **GitHub Project #17** - タスク管理
3. **GitHub Issues** - 実装タスク

### プロジェクト名

「marimo Market Dashboard」

## 参考実装の機能

Market-Report2.py は以下の機能を持つが、外部モジュール（`QUANTS_DIR` の `fred_database_utils`, `market_report_utils`）に依存しており再利用不可：

- S&P500、Magnificent 7、SOX指数のパフォーマンス
- セクターETF（XL系）のパフォーマンス
- 貴金属パフォーマンス
- セクターETFのローリングベータ（vs S&P500）
- 米国金利・イールドスプレッド
- VIX・ハイイールドスプレッド
- 経済不確実性指数
- ドルインデックス vs 貴金属相関
- 週次リターン分布

## 実装方針

既存の `src/market_analysis/` ライブラリを活用し、marimo のインタラクティブ UI を追加。

### 使用する既存API

| API | 用途 |
|-----|------|
| `MarketData.fetch_stock()` | 株価・指数データ取得 |
| `MarketData.fetch_fred()` | FRED経済指標取得 |
| `MarketData.fetch_commodity()` | 貴金属データ取得 |
| `PRESET_GROUPS` | ティッカーグループ（MAGNIFICENT_7, ALL_SECTORS等） |
| `CorrelationAnalyzer.calculate_rolling_beta()` | ローリングベータ |
| `CorrelationAnalyzer.calculate_rolling_correlation()` | ローリング相関 |

### marimo UI要素

| UI | 用途 |
|----|------|
| `mo.ui.dropdown` | 期間選択（1M, 3M, 6M, 1Y, 2Y, 5Y） |
| `mo.ui.date` | カスタム開始/終了日 |
| `mo.ui.multiselect` | ティッカー選択 |
| `mo.ui.slider` | ローリング窓サイズ |
| `mo.ui.tabs` | セクション切替 |

## ダッシュボード構成

```
┌─────────────────────────────────────────────────────────────┐
│ Market Dashboard - マーケットレポート                        │
├─────────────────────────────────────────────────────────────┤
│ [期間選択ドロップダウン]                                      │
├─────────────────────────────────────────────────────────────┤
│ Tab 1: パフォーマンス概要                                     │
│   - S&P500 & 主要指数                                        │
│   - Magnificent 7 & SOX                                     │
│   - セクターETF                                              │
│   - 貴金属                                                   │
├─────────────────────────────────────────────────────────────┤
│ Tab 2: マクロ指標                                            │
│   - 米国金利（10Y, 2Y, FF）                                  │
│   - イールドスプレッド                                        │
│   - VIX & ハイイールドスプレッド                              │
├─────────────────────────────────────────────────────────────┤
│ Tab 3: 相関・ベータ分析                                       │
│   - セクターETFローリングベータ                               │
│   - ドルインデックス vs 貴金属                                │
│   - 相関ヒートマップ                                         │
├─────────────────────────────────────────────────────────────┤
│ Tab 4: リターン分布                                          │
│   - 週次リターンヒストグラム                                  │
│   - 統計サマリー                                             │
└─────────────────────────────────────────────────────────────┘
```

## 実装ファイル

```
notebook/
└── market_dashboard.py    # メインダッシュボード（約600-800行）
```

## 実装ステップ（GitHub Issues）

### Phase 0: プロジェクト準備
- [ ] docs/project/project-17/ フォルダ作成
- [ ] GitHub Project #17 作成
- [ ] README.md 作成

### Phase 1: 基本骨格（Issue #1）
- [ ] marimo app 初期化
- [ ] 共通UI要素（期間選択）配置
- [ ] タブ構造作成

### Phase 2: Tab 1 - パフォーマンス概要（Issue #2）
- [ ] パフォーマンス計算関数（期間別リターン: 1D, 1W, 1M, YTD）
- [ ] S&P500/Mag7/SOX データ取得・テーブル表示
- [ ] セクターETFパフォーマンステーブル
- [ ] 貴金属パフォーマンステーブル
- [ ] ヒートマップスタイリング

### Phase 3: Tab 2 - マクロ指標（Issue #3）
- [ ] FRED データ取得（DGS10, DGS2, DFF）
- [ ] 金利チャート（Plotly）
- [ ] イールドスプレッド計算・表示
- [ ] VIX/ハイイールドスプレッドチャート

### Phase 4: Tab 3 - 相関・ベータ（Issue #4）
- [ ] ローリングベータ計算（CorrelationAnalyzer）
- [ ] ベータチャート
- [ ] ドルvs貴金属相関計算・チャート
- [ ] 相関ヒートマップ

### Phase 5: Tab 4 - リターン分布（Issue #5）
- [ ] 週次リターン計算
- [ ] ヒストグラム生成（Plotly）
- [ ] 統計サマリーテーブル

### Phase 6: 統合・検証（Issue #6）
- [ ] 全タブ動作確認
- [ ] エラーハンドリング追加
- [ ] キャッシュ最適化

## FRED シリーズID

| 指標 | シリーズID |
|-----|-----------|
| 10年国債 | DGS10 |
| 2年国債 | DGS2 |
| FF金利 | DFF |
| ハイイールドスプレッド | BAMLH0A0HYM2 |
| 経済不確実性指数 | USEPUINDXD |
| ドルインデックス | DTWEXAFEGS |

## 重要ファイル

- `src/market_analysis/api/market_data.py` - データ取得
- `src/market_analysis/analysis/correlation.py` - 相関・ベータ計算
- `src/market_analysis/utils/ticker_registry.py` - PRESET_GROUPS
- `notebook_sample/Market-Report2.py` - 参考実装

## 環境要件

- `FRED_API_KEY` 環境変数（FRED データ取得に必要）
- marimo >= 0.19.2（導入済み）

## 検証方法

```bash
# marimoで起動して動作確認
marimo edit notebook/market_dashboard.py
```

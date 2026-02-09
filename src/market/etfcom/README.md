# market.etfcom

ETF.com からの ETF データスクレイピングおよび REST API 連携モジュール。

## 概要

ETF.com のスクリーナー、プロフィールページ、ファンドフローページ、REST API から ETF 関連データを取得します。curl_cffi によるボットブロッキング対策と Playwright によるブラウザ自動化に対応。

**取得可能なデータ:**

- **ティッカーリスト**: ETF.com スクリーナーからの全 ETF ティッカー
- **ファンダメンタルズ**: 個別 ETF プロフィールページの Key-Value データ
- **ファンドフロー**: 日次ファンドフローデータ
- **ヒストリカルファンドフロー**: REST API 経由の過去ファンドフローデータ

## クイックスタート

### ティッカー一覧の取得

```python
from market.etfcom import TickerCollector

collector = TickerCollector()
df = collector.fetch()
print(f"ETF数: {len(df)}")
print(df.head())
```

### ファンダメンタルズの取得

```python
from market.etfcom import FundamentalsCollector

collector = FundamentalsCollector()
df = collector.fetch(tickers=["SPY", "VOO", "IVV"])
print(df)
```

### ファンドフローの取得

```python
from market.etfcom import FundFlowsCollector

collector = FundFlowsCollector()
df = collector.fetch()
print(df.head())
```

### ヒストリカルファンドフローの取得（REST API）

```python
from market.etfcom import HistoricalFundFlowsCollector

collector = HistoricalFundFlowsCollector()
records = collector.fetch(
    ticker="SPY",
    start_date="2024-01-01",
    end_date="2024-12-31",
)
for record in records:
    print(f"{record.date}: {record.flow:,.0f}")
```

### ETFComSession の直接使用

```python
from market.etfcom import ETFComSession

with ETFComSession() as session:
    response = session.get_with_retry("https://www.etf.com/SPY")
    print(response.status_code)
```

## API リファレンス

### コレクタークラス

| クラス | 説明 | 継承元 |
|--------|------|--------|
| `TickerCollector` | ETF.com スクリーナーからティッカーリストを取得 | `DataCollector` |
| `FundamentalsCollector` | 個別 ETF プロフィールから Key-Value データを取得 | `DataCollector` |
| `FundFlowsCollector` | ファンドフローページから日次フローデータを取得 | `DataCollector` |
| `HistoricalFundFlowsCollector` | REST API 経由で過去ファンドフローデータを取得 | - |

### ETFComSession

curl_cffi ベースの HTTP セッション。ボットブロッキング対策を内蔵。

| メソッド | 説明 |
|---------|------|
| `get_with_retry(url)` | リトライ付き GET リクエスト |

**特徴:**
- 403/429 レスポンスの自動ハンドリング
- 指数バックオフによるリトライ
- プロキシローテーション対応
- コンテキストマネージャー対応

### データ型

| 型 | 説明 |
|----|------|
| `ETFRecord` | ETF メタデータレコード（フィールド正規化済み） |
| `FundFlowRecord` | 日次ファンドフローレコード |
| `FundamentalsRecord` | ETF ファンダメンタルズレコード |
| `HistoricalFundFlowRecord` | REST API からのヒストリカルフローレコード |
| `RetryConfig` | リトライ設定（指数バックオフ） |
| `ScrapingConfig` | スクレイピング設定 |
| `TickerInfo` | ティッカー情報 |

### 例外クラス

| 例外 | 説明 |
|------|------|
| `ETFComError` | ETF.com 操作の基底例外 |
| `ETFComAPIError` | REST API エラー |
| `ETFComBlockedError` | ボットブロッキング検出時 |
| `ETFComScrapingError` | HTML パース / データ抽出失敗時 |
| `ETFComTimeoutError` | ページ読み込みタイムアウト時 |

## トラブルシューティング

### ボットブロッキング

```
ETFComBlockedError: Bot detection triggered
```

**解決方法:**
- `RetryConfig` でリトライ間隔を長めに設定
- プロキシの利用を検討
- リクエスト頻度を下げる

### タイムアウト

```
ETFComTimeoutError: Page load timed out
```

**解決方法:**
- `ScrapingConfig` でタイムアウト値を延長
- ネットワーク接続を確認

## モジュール構成

```
market/etfcom/
├── __init__.py      # パッケージエクスポート
├── collectors.py    # 4つのコレクタークラス
├── session.py       # ETFComSession（HTTP セッション）
├── errors.py        # 例外クラス
├── types.py         # データ型定義
├── constants.py     # URL、パターン等の定数
├── browser.py       # Playwright ブラウザ自動化
└── README.md        # このファイル
```

## 依存ライブラリ

| ライブラリ | 用途 |
|-----------|------|
| curl_cffi | ボットブロッキング対策付き HTTP |
| beautifulsoup4 | HTML パース |
| playwright | ブラウザ自動化（動的ページ対応） |
| requests | 標準 HTTP クライアント |

## 関連モジュール

- [market.yfinance](../yfinance/README.md) - Yahoo Finance データ取得
- [market.cache](../cache/README.md) - キャッシュ機能
- [market.export](../export/README.md) - データエクスポート

# market.bloomberg

Bloomberg Terminal と連携して金融データを取得するモジュール。

## 概要

Bloomberg Professional サービス（blpapi）を使用して、機関投資家向けの高品質な金融データを取得します。

**取得可能なデータ:**

- **ヒストリカルデータ**: 株価、指数、為替、債券の時系列データ
- **リファレンスデータ**: 企業情報、財務データ、アナリスト予想
- **フィールド情報**: Bloomberg フィールドの定義・メタデータ
- **識別子変換**: TICKER ↔ ISIN ↔ CUSIP の相互変換
- **インデックス構成銘柄**: S&P 500、日経225 等の構成銘柄取得
- **ニュース**: Bloomberg ニュースストーリーの取得

## 前提条件

- Bloomberg Terminal のライセンスとアクセス権
- Bloomberg API SDK（`blpapi`）のインストール
- Bloomberg のバックエンドサービスへのネットワーク接続

```bash
# blpapi のインストール（Bloomberg から SDK を取得後）
pip install blpapi
```

## クイックスタート

```python
from market.bloomberg import BloombergFetcher, BloombergFetchOptions

# 1. フェッチャーを作成
fetcher = BloombergFetcher()

# 2. ヒストリカルデータを取得
options = BloombergFetchOptions(
    securities=["AAPL US Equity"],
    fields=["PX_LAST", "PX_VOLUME"],
    start_date="2024-01-01",
    end_date="2024-12-31",
)
results = fetcher.get_historical_data(options)

# 3. 結果を確認
for result in results:
    print(f"{result.security}: {len(result.data)} 件")
    print(result.data.tail())
```

### 複数銘柄の取得

```python
options = BloombergFetchOptions(
    securities=[
        "AAPL US Equity",
        "MSFT US Equity",
        "7203 JP Equity",  # トヨタ
    ],
    fields=["PX_LAST", "PX_VOLUME", "CUR_MKT_CAP"],
    start_date="2024-01-01",
    end_date="2024-12-31",
    periodicity=Periodicity.DAILY,
)
results = fetcher.get_historical_data(options)
```

### 識別子の変換

```python
# ISIN から Bloomberg Ticker へ変換
ticker = fetcher.convert_identifier(
    identifier="US0378331005",
    from_type=IDType.ISIN,
    to_type=IDType.TICKER,
)
# → "AAPL US Equity"
```

## API リファレンス

### BloombergFetcher

Bloomberg データ取得のメインクラス。

**メソッド:**

| メソッド | 説明 | 戻り値 |
|---------|------|--------|
| `get_historical_data(options)` | ヒストリカルデータを取得 | `list[BloombergDataResult]` |
| `get_reference_data(securities, fields)` | リファレンスデータを取得 | `dict` |
| `get_field_info(fields)` | フィールド定義を取得 | `list[FieldInfo]` |
| `convert_identifier(identifier, from_type, to_type)` | 識別子を変換 | `str` |
| `get_index_members(index)` | インデックス構成銘柄を取得 | `list[str]` |

### BloombergFetchOptions

| フィールド | 型 | 説明 |
|-----------|-----|------|
| `securities` | `list[str]` | Bloomberg 銘柄識別子のリスト |
| `fields` | `list[str]` | Bloomberg フィールド名のリスト |
| `start_date` | `str` | 取得開始日（YYYY-MM-DD） |
| `end_date` | `str` | 取得終了日（YYYY-MM-DD） |
| `periodicity` | `Periodicity` | データ頻度 |
| `overrides` | `list[OverrideOption]` | フィールドオーバーライド |

### 型定義

| 型 | 説明 |
|----|------|
| `BloombergDataResult` | データ取得結果 |
| `FieldInfo` | フィールドのメタデータ |
| `IDType` | 識別子タイプ（TICKER, ISIN, CUSIP） |
| `NewsStory` | ニュースストーリー |
| `Periodicity` | データ頻度（DAILY, WEEKLY, MONTHLY 等） |
| `OverrideOption` | フィールドオーバーライド設定 |

### 例外クラス

| 例外 | 説明 |
|------|------|
| `BloombergError` | Bloomberg 操作の基底例外 |
| `BloombergConnectionError` | 接続エラー（host/port 情報付き） |
| `BloombergSessionError` | セッションエラー（サービス情報付き） |
| `BloombergDataError` | データ取得エラー（security/fields 情報付き） |
| `BloombergValidationError` | バリデーションエラー（field/value 情報付き） |

## よく使う Bloomberg フィールド

### 株価

| フィールド | 説明 |
|-----------|------|
| `PX_LAST` | 最終価格 |
| `PX_OPEN` | 始値 |
| `PX_HIGH` | 高値 |
| `PX_LOW` | 安値 |
| `PX_VOLUME` | 出来高 |
| `PX_BID` | 買い気配値 |
| `PX_ASK` | 売り気配値 |

### 財務データ

| フィールド | 説明 |
|-----------|------|
| `CUR_MKT_CAP` | 時価総額 |
| `PE_RATIO` | PER（株価収益率） |
| `BEST_EPS` | コンセンサス EPS |
| `DVD_INDICATED_YIELD` | 配当利回り |
| `RETURN_ON_EQUITY` | ROE |

## モジュール構成

```
market/bloomberg/
├── __init__.py      # パッケージエクスポート
├── fetcher.py       # BloombergFetcher 実装
├── types.py         # 型定義（BloombergFetchOptions 等）
├── constants.py     # フィールド定数
├── sample/          # サンプルデータ・ユーティリティ
│   ├── data_blpapi.py   # Bloomberg API サンプル
│   └── data_local.py    # ローカルファイル処理
└── README.md        # このファイル
```

## 関連ファイル

- `market/bloomberg_processor.py` - Bloomberg Excel ファイルの処理（DataCollector 継承）

## 関連モジュール

- [market.yfinance](../yfinance/README.md) - Yahoo Finance データ取得（無料代替）
- [market.factset](../factset/README.md) - FactSet データ取得（計画中）
- [market.export](../export/README.md) - データエクスポート

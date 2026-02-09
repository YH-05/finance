# analyze.sector

セクター分析モジュール。

## 概要

GICS 11 セクターの ETF パフォーマンス分析を提供します。セクター ETF のリターン取得、セクターランキング（上位/下位）、セクター内の貢献銘柄の特定に対応。

**対応セクター（11 セクター）:**

| セクター | ETF | キー |
|---------|------|------|
| Technology | XLK | `technology` |
| Financial | XLF | `financial` |
| Health Care | XLV | `health_care` |
| Energy | XLE | `energy` |
| Industrial | XLI | `industrial` |
| Consumer Discretionary | XLY | `consumer_discretionary` |
| Consumer Staples | XLP | `consumer_staples` |
| Materials | XLB | `materials` |
| Utilities | XLU | `utilities` |
| Real Estate | XLRE | `real_estate` |
| Communication Services | XLC | `communication_services` |

## クイックスタート

### セクターパフォーマンス分析

```python
from analyze.sector import analyze_sector_performance

result = analyze_sector_performance(period="1mo", top_n=5)

for sector in result.sectors:
    print(f"{sector.name}: {sector.return_1w:.2%}")
    for contrib in sector.top_contributors:
        print(f"  {contrib.ticker} ({contrib.name}): {contrib.return_1w:.2%}")
```

### セクター ETF リターン取得

```python
from analyze.sector import fetch_sector_etf_returns

returns = fetch_sector_etf_returns(period="1mo")
# → {'technology': 0.045, 'financial': 0.032, ...}
```

### 上位/下位セクター

```python
from analyze.sector import get_top_bottom_sectors

top, bottom = get_top_bottom_sectors(returns, n=3)
# top: [('technology', 0.045), ('financial', 0.032), ...]
# bottom: [('utilities', -0.012), ...]
```

## API リファレンス

### 関数

| 関数 | 説明 | 戻り値 |
|------|------|--------|
| `analyze_sector_performance(period, top_n=5)` | セクターパフォーマンス分析（貢献銘柄付き） | `SectorAnalysisResult` |
| `fetch_sector_etf_returns(period)` | セクター ETF のリターン取得 | `dict[str, float]` |
| `get_top_bottom_sectors(returns, n=3)` | 上位/下位セクター取得 | `tuple[list, list]` |
| `fetch_top_companies(etf, limit=10)` | ETF 内の上位銘柄取得 | `list[dict[str, Any]]` |

### データクラス

| クラス | フィールド | 説明 |
|--------|-----------|------|
| `SectorAnalysisResult` | sectors, generated_at, period | 分析結果全体 |
| `SectorInfo` | name, key, etf, return_1w, top_contributors | セクター情報 |
| `SectorContributor` | ticker, name, return_1w, weight | 貢献銘柄情報 |

### 定数

| 定数 | 型 | 説明 |
|------|-----|------|
| `SECTOR_KEYS` | `list[str]` | 11 セクターキーのリスト |
| `SECTOR_ETF_MAP` | `dict[str, str]` | セクターキー → ETF ティッカーのマッピング |
| `SECTOR_NAMES` | `dict[str, str]` | セクターキー → 表示名のマッピング |

## モジュール構成

```
analyze/sector/
├── __init__.py   # パッケージエクスポート（4関数 + 3クラス + 3定数）
├── sector.py     # セクター分析関数・データクラス
└── README.md     # このファイル
```

## 依存ライブラリ

| ライブラリ | 用途 |
|-----------|------|
| yfinance | セクター ETF 価格データ取得 |

## 関連モジュール

- [analyze.config](../config/README.md) - セクター ETF シンボル定義
- [analyze.returns](../returns/README.md) - リターン計算（`TICKERS_SECTORS` 定数）
- [analyze.reporting](../reporting/README.md) - パフォーマンスレポートでのセクター分析

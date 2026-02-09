# analyze.config

シンボルグループと期間設定の管理モジュール。

## 概要

`symbols.yaml` からシンボルグループ定義（指数、MAG7、セクター、コモディティ、通貨ペア）とリターン計算期間を読み込み、Pydantic モデルで型安全にアクセスする設定管理モジュールです。`@lru_cache` によるキャッシュで、設定ファイルの読み込みは 1 回のみ。

**設定階層:**

```
SymbolsConfig（ルート）
├── indices: IndicesConfig
│   ├── us: list[IndexSymbol]        # 米国指数（^GSPC, ^DJI 等）
│   └── global_: list[IndexSymbol]   # 海外指数（^N225, ^FTSE 等）
├── mag7: list[Mag7Symbol]           # Magnificent 7
├── commodities: list[CommoditySymbol]  # コモディティ先物
├── currencies: dict[str, list[CurrencyPairSymbol]]  # 通貨ペア
├── sectors: list[SectorSymbol]      # セクター ETF
├── sector_stocks: SectorStocksConfig  # セクター代表銘柄（11セクター）
└── return_periods: ReturnPeriodsConfig  # リターン計算期間（11期間）
```

## クイックスタート

### シンボルグループの取得

```python
from analyze.config import get_symbols, get_symbol_group, get_return_periods

# MAG7 のティッカーリスト
mag7 = get_symbols("mag7")
# → ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA']

# 米国指数のティッカーリスト
us_indices = get_symbols("indices", "us")
# → ['^GSPC', '^DJI', '^IXIC', ...]

# 通貨ペア（名前付き）
jpy_crosses = get_symbol_group("currencies", "jpy_crosses")
# → [{'symbol': 'USDJPY=X', 'name': '米ドル/円'}, ...]

# リターン計算期間
periods = get_return_periods()
# → {'1D': 1, 'WoW': 'prev_tue', '1W': 5, 'MTD': 'mtd', '1M': 21, ...}
```

### Pydantic モデルでの利用

```python
from analyze.config import SymbolsConfig, IndexSymbol, IndicesConfig

config = SymbolsConfig(
    indices=IndicesConfig(
        us=[IndexSymbol(symbol="^GSPC", name="S&P 500")],
        global_=[IndexSymbol(symbol="^N225", name="日経225")],
    ),
    ...
)
symbols = config.get_symbols("indices", "us")
```

## API リファレンス

### ローダー関数

| 関数 | 説明 | 戻り値 |
|------|------|--------|
| `load_symbols_config()` | YAML を dict で読み込み（`@lru_cache`） | `dict[str, Any]` |
| `get_symbols(group, subgroup)` | ティッカーシンボルのリスト取得 | `list[str]` |
| `get_symbol_group(group, subgroup)` | シンボル＋名前の辞書リスト取得 | `list[dict[str, str]]` |
| `get_return_periods()` | リターン計算期間定義を取得 | `dict[str, int \| str]` |

### シンボルモデル

| クラス | フィールド | 説明 |
|--------|-----------|------|
| `IndexSymbol` | symbol, name | 株価指数（`^GSPC`, `^DJI` 等） |
| `Mag7Symbol` | symbol, name | Magnificent 7 銘柄 |
| `SectorSymbol` | symbol, name | セクター ETF（`XLF`, `XLK` 等） |
| `CommoditySymbol` | symbol, name | コモディティ先物（`GC=F`, `CL=F` 等） |
| `CurrencyPairSymbol` | symbol, name | 通貨ペア（`USDJPY=X` 等） |
| `SectorStockSymbol` | symbol, name, sector | セクター内個別銘柄 |

### 設定モデル

| クラス | 説明 |
|--------|------|
| `SymbolsConfig` | ルート設定（`get_symbols()`, `get_symbol_group()`, `get_return_periods_dict()` メソッド） |
| `IndicesConfig` | 指数設定（us, global_ の 2 グループ） |
| `SectorStocksConfig` | セクター代表銘柄（XLF〜XLC の 11 セクター） |
| `ReturnPeriodsConfig` | リターン期間（1D, WoW, 1W, MTD, 1M, 3M, 6M, YTD, 1Y, 3Y, 5Y） |

### グループ名一覧

| group | subgroup | 説明 |
|-------|----------|------|
| `"indices"` | `"us"`, `"global"`, `None`（全件） | 株価指数 |
| `"mag7"` | — | Magnificent 7 |
| `"commodities"` | — | コモディティ先物 |
| `"currencies"` | `"jpy_crosses"` 等, `None`（全件） | 通貨ペア |
| `"sectors"` | — | セクター ETF |
| `"sector_stocks"` | `"XLF"`, `"XLK"` 等, `None`（全件） | セクター代表銘柄 |

## モジュール構成

```
analyze/config/
├── __init__.py     # パッケージエクスポート（10モデル + 4関数）
├── loader.py       # 設定ローダー（YAML読み込み、@lru_cache）
├── models.py       # Pydantic モデル定義（10クラス）
├── symbols.yaml    # シンボルグループ定義ファイル
└── README.md       # このファイル
```

## 依存ライブラリ

| ライブラリ | 用途 |
|-----------|------|
| pydantic | 設定モデルのバリデーション |
| PyYAML | YAML ファイルの読み込み |

## 関連モジュール

- [analyze.returns](../returns/README.md) - リターン計算（定数 `RETURN_PERIODS` を使用）
- [analyze.sector](../sector/README.md) - セクター分析（セクター ETF 設定を使用）
- [analyze.reporting](../reporting/README.md) - レポート生成（シンボルグループを使用）

# ASEAN + India カバレッジ統合設計書

**作成日**: 2026-04-10
**Issue**: #3900 [Wave3] ASEAN カバレッジ統合設計
**ステータス**: 実装済み（PR作成済み）

---

## 1. 概要

NSE（National Stock Exchange of India）/BSE（Bombay Stock Exchange）を ASEAN カバレッジの India データソースとして位置づけ、既存の ASEAN フレームワーク（`asean_common`）を `market_common` へリネームし、`MarketExchange` enum に NSE/BSE メンバーを追加した設計について記述する。

---

## 2. enum 戦略: `AseanMarket` → `MarketExchange`

### 2.1 リネーム理由

| 旧名称 | 新名称 | 理由 |
|--------|--------|------|
| `AseanMarket` | `MarketExchange` | India (NSE/BSE) を追加するにあたり、ASEAN 固有の名前から汎用名に変更。将来の US/EU 拡張にも対応可能 |
| `market.asean_common` | `market.market_common` | enum 名との命名統一 |

### 2.2 MarketExchange enum メンバー

```python
class MarketExchange(str, Enum):
    # ASEAN 6取引所
    SGX   = "SGX"   # Singapore Exchange
    BURSA = "BURSA" # Bursa Malaysia
    SET   = "SET"   # Stock Exchange of Thailand
    IDX   = "IDX"   # Indonesia Stock Exchange
    HOSE  = "HOSE"  # Ho Chi Minh Stock Exchange (Vietnam)
    PSE   = "PSE"   # Philippine Stock Exchange
    # India
    NSE   = "NSE"   # National Stock Exchange of India（主要データソース）
    BSE   = "BSE"   # Bombay Stock Exchange（当面実装対象外）
```

### 2.3 BSE の位置づけ

BSE は `MarketExchange` enum メンバーとして含めるが、以下の理由から実装は当面対象外:

1. **geo-block 問題**: BSE の Web API は日本/海外 IP からのアクセスをブロックする
2. **NSE で十分**: NSE 上場銘柄は BSE とほぼ重複しており、NSE データで India カバレッジは充足可能

---

## 3. ディレクトリリネーム

| 変更前 | 変更後 |
|--------|--------|
| `src/market/asean_common/` | `src/market/market_common/` |
| `tests/market/asean_common/` | `tests/market/market_common/` |

旧 `asean_common` は後方互換性のためにシムとして残し、`market_common` の全シンボルを再エクスポートする。

### 3.1 移行ガイド

```python
# 旧（引き続き動作するが非推奨）
from market.asean_common import AseanMarket

# 新（推奨）
from market.market_common import MarketExchange
```

---

## 4. 型マッピング表: NSE `StockQuote` → `TickerRecord`

NSE quote API (`/api/quote-equity?symbol=RELIANCE`) の `industryInfo` フィールドから `TickerRecord` の `sector`/`industry` を取得する。

### 4.1 industryInfo 4階層構造

```json
{
  "industryInfo": {
    "macro": "FINANCIAL SERVICES",
    "sector": "FINANCIAL SERVICES",
    "industry": "Finance",
    "basicIndustry": "Diversified Financials"
  }
}
```

### 4.2 マッピング仕様

| NSE `industryInfo` フィールド | `TickerRecord` フィールド | 説明 |
|-------------------------------|---------------------------|------|
| `industryInfo.macro` | `sector` | GICS セクター相当（大分類） |
| `industryInfo.industry` | `industry` | 業種（中分類） |

### 4.3 変換例

| NSE symbol | `industryInfo.macro` → `sector` | `industryInfo.industry` → `industry` |
|------------|----------------------------------|---------------------------------------|
| RELIANCE   | OIL GAS & CONSUMABLE FUELS       | Refineries/ Petro-Products            |
| INFY       | INFORMATION TECHNOLOGY           | Computers - Software & Consulting     |
| HDFCBANK   | FINANCIAL SERVICES               | Banks                                 |

---

## 5. yfinance サフィックスマッピング

`YFINANCE_SUFFIX_MAP` に NSE と BSE のサフィックスを追加した。

```python
YFINANCE_SUFFIX_MAP: Final[dict[MarketExchange, str]] = {
    MarketExchange.SGX:   ".SI",
    MarketExchange.BURSA: ".KL",
    MarketExchange.SET:   ".BK",
    MarketExchange.IDX:   ".JK",
    MarketExchange.HOSE:  ".VN",
    MarketExchange.PSE:   ".PS",
    MarketExchange.NSE:   ".NS",  # 追加: NSE India
    MarketExchange.BSE:   ".BO",  # 追加: BSE India
}
```

### 使用例

```python
# NSE 上場株 Reliance Industries の yfinance ティッカー
symbol = "RELIANCE"
suffix = YFINANCE_SUFFIX_MAP[MarketExchange.NSE]  # → ".NS"
yf_ticker = f"{symbol}{suffix}"  # → "RELIANCE.NS"
```

---

## 6. tradingview-screener 統合: screener 重複排除

### 6.1 問題

NSE と BSE の両方が tradingview-screener の `market="india"` にマッピングされているため、`Query.set_markets("india")` でそのまま取得すると両取引所の銘柄が重複して返される。

### 6.2 解決策: NSE 優先フィルタ

```python
# screener.py の _query_screener() 内
if market == MarketExchange.NSE:
    nse_exchange = SCREENER_EXCHANGE_MAP[MarketExchange.NSE]  # "NSE"
    query = (
        Query()
        .set_markets("india")
        .select(*_SCREENER_COLUMNS)
        .where(Column("type") == "stock", Column("exchange") == nse_exchange)
        .limit(_MAX_RESULTS)
    )
```

### 6.3 SCREENER_MARKET_MAP への NSE 追加

```python
SCREENER_MARKET_MAP: Final[dict[MarketExchange, str]] = {
    MarketExchange.SGX:   "singapore",
    MarketExchange.BURSA: "malaysia",
    MarketExchange.SET:   "thailand",
    MarketExchange.IDX:   "indonesia",
    MarketExchange.HOSE:  "vietnam",
    MarketExchange.PSE:   "philippines",
    MarketExchange.NSE:   "india",   # 追加: NSE → india
    # BSE は意図的に除外（重複排除設計のため NSE のみ "india" にマップ）
}
```

---

## 7. 移行計画

### 7.1 変更の影響範囲

| 変更内容 | ファイル数 | 出現回数 |
|----------|-----------|---------|
| `AseanMarket` → `MarketExchange` | ~20 | ~203 |
| `asean_common` → `market_common` | ~48 | ~233 |
| **合計** | **~48** | **~436** |

### 7.2 後方互換性

`src/market/asean_common/__init__.py` をシムとして残す:

```python
# asean_common/__init__.py（シム）
from market.market_common import MarketExchange, ...
AseanMarket = MarketExchange  # compat alias
```

これにより既存の `from market.asean_common import AseanMarket` 形式のインポートは引き続き動作する。

### 7.3 非推奨タイムライン

| フェーズ | 内容 |
|----------|------|
| Wave3（本PR） | `market_common` 追加、`asean_common` シム化 |
| 次回 Wave | 内部利用箇所を `market_common` に移行 |
| 将来 | `asean_common` 削除（DeprecationWarning 追加後） |

---

## 8. 関連情報

- **議論メモ**: `docs/plan/2026-04-08_discussion-asean-integration-design.md`
- **MarketExchange enum**: `src/market/market_common/constants.py`
- **TickerRecord**: `src/market/market_common/types.py`
- **NSE StockQuote**: `src/market/nse/types.py`
- **NSE industryInfo**: `src/market/nse/parsers.py`
- **screener 重複排除実装**: `src/market/market_common/screener.py`

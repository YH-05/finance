# Task 06: CurrencyAnalyzer クラス作成

**Phase**: 2 - 為替データ
**依存**: Task 05
**ファイル**: `src/analyze/reporting/currency.py`

## 概要

yfinance を使用して円クロス為替レートを取得し、複数期間の騰落率を計算する `CurrencyAnalyzer` クラスを作成する。

## 対象通貨ペア

| ティッカー | 通貨ペア | 説明 |
|-----------|---------|------|
| USDJPY=X | USD/JPY | 米ドル/円 |
| EURJPY=X | EUR/JPY | ユーロ/円 |
| GBPJPY=X | GBP/JPY | 英ポンド/円 |
| AUDJPY=X | AUD/JPY | 豪ドル/円 |
| CADJPY=X | CAD/JPY | カナダドル/円 |
| CHFJPY=X | CHF/JPY | スイスフラン/円 |

## 実装仕様

### クラス設計

```python
class CurrencyAnalyzer:
    """yfinance から為替データを取得し分析するクラス.

    PerformanceAnalyzer と同様のパターンで、
    円クロス為替レートの取得と期間別騰落率計算を行う。
    """

    def __init__(self) -> None: ...

    def get_currency_data(self, subgroup: str = "jpy_crosses") -> DataFrame:
        """指定サブグループの為替データを取得.

        Parameters
        ----------
        subgroup : str
            サブグループ名（デフォルト: "jpy_crosses"）

        Returns
        -------
        DataFrame
            為替データ（Date, symbol, variable, value）
        """
        ...

    def calculate_returns(
        self,
        data: DataFrame,
        periods: dict[str, int | str],
    ) -> DataFrame:
        """期間別の騰落率を計算.

        株価と同様に pct_change で騰落率を計算する。
        """
        ...

    def get_currency_performance(
        self,
        subgroup: str = "jpy_crosses",
    ) -> DataFrame:
        """為替パフォーマンス（騰落率）を計算."""
        ...
```

### 期間定義

既存の `return_periods` を使用:

```python
# analyze/config/symbols.yaml から取得
return_periods = get_return_periods()
# {"1D": 1, "WoW": "prev_tue", "1W": 5, "MTD": "mtd", ...}
```

### 計算方法

- 為替は**騰落率**で計算（株価と同様）
- 例: USD/JPY が 150.00 → 155.00 の場合、騰落率は +3.33%
- 円安 = 騰落率プラス、円高 = 騰落率マイナス

## 参照パターン

- `src/analyze/reporting/performance.py`: PerformanceAnalyzer
- `src/market/yfinance/fetcher.py`: YFinanceFetcher

## 受け入れ条件

- [ ] symbols.yaml から通貨ペアを取得できる
- [ ] YFinanceFetcher を使用して為替データを取得できる
- [ ] 期間別の騰落率を正しく計算できる
- [ ] ロギングが実装されている
- [ ] NumPy形式のDocstringがある

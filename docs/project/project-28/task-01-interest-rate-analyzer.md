# Task 01: InterestRateAnalyzer クラス作成

**Phase**: 1 - 金利データ
**依存**: なし
**ファイル**: `src/analyze/reporting/interest_rate.py`

## 概要

FRED API を使用して米国債利回りとFF金利を取得し、複数期間の変化率を計算する `InterestRateAnalyzer` クラスを作成する。

## 対象シリーズ

| シリーズID | 名称 | 用途 |
|-----------|------|------|
| DGS2 | 2年国債利回り | 短期金利 |
| DGS10 | 10年国債利回り | 長期金利 |
| DGS30 | 30年国債利回り | 超長期金利 |
| FEDFUNDS | FF金利 | 政策金利 |
| T10Y2Y | 10年-2年スプレッド | イールドカーブ |

## 実装仕様

### クラス設計

```python
class InterestRateAnalyzer:
    """FRED から金利データを取得し分析するクラス.

    PerformanceAnalyzer と同様のパターンで、
    金利データの取得と期間別変化率計算を行う。
    """

    # 対象シリーズの定義
    SERIES_CONFIG: dict[str, dict[str, str]] = {
        "DGS2": {"name_ja": "2年国債利回り", "category": "treasury"},
        "DGS10": {"name_ja": "10年国債利回り", "category": "treasury"},
        "DGS30": {"name_ja": "30年国債利回り", "category": "treasury"},
        "FEDFUNDS": {"name_ja": "FF金利", "category": "policy"},
        "T10Y2Y": {"name_ja": "10年-2年スプレッド", "category": "spread"},
    }

    def __init__(self) -> None: ...

    def get_interest_rate_data(self) -> DataFrame:
        """全シリーズの金利データを取得."""
        ...

    def calculate_changes(
        self,
        data: DataFrame,
        periods: dict[str, int | str],
    ) -> DataFrame:
        """期間別の変化量を計算（騰落率ではなく差分）."""
        ...

    def get_yield_curve_analysis(self) -> dict[str, Any]:
        """イールドカーブ分析（スプレッド、逆イールド判定）."""
        ...
```

### 期間定義

```python
INTEREST_RATE_PERIODS = {
    "1D": 1,       # 前日比
    "1W": 5,       # 1週間前比
    "MTD": "mtd",  # 月初来
    "YTD": "ytd",  # 年初来
}
```

### 計算方法

- 金利は**差分**で計算（株価と異なり騰落率ではない）
- 例: 10年債が 4.50% → 4.55% の場合、変化は +0.05 (5bp)

## 参照パターン

- `src/analyze/reporting/performance.py`: PerformanceAnalyzer
- `src/market/fred/fetcher.py`: FREDFetcher

## 受け入れ条件

- [ ] FREDFetcher を使用して5シリーズのデータを取得できる
- [ ] 期間別の変化量（差分）を正しく計算できる
- [ ] イールドカーブ分析（逆イールド判定）ができる
- [ ] ロギングが実装されている
- [ ] NumPy形式のDocstringがある

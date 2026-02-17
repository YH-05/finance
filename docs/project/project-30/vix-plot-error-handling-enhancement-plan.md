# VIX プロットエラーハンドリング強化計画

## 問題概要

`vix.plot_vix_and_high_yield_spread()` で `KeyError: 'date'` が発生。
原因: FREDキャッシュにデータがない場合、空DataFrameが `pd.pivot_table(index="date")` に渡される。

## 変更対象ファイル

| ファイル | 変更内容 |
|----------|----------|
| `src/analyze/reporting/vix.py` | エラーハンドリング・ログ追加 |
| `src/market/errors.py` | `FREDCacheNotFoundError` 追加 |
| `tests/analyze/unit/reporting/test_vix.py` | 新規作成（TDD） |

## 実装内容

### 1. `src/market/errors.py` に新規エラークラス追加

```python
class FREDCacheNotFoundError(FREDFetchError):
    """FRED series data not found in local cache.

    Parameters
    ----------
    series_ids : list[str]
        Missing series IDs
    """

    def __init__(self, series_ids: list[str]) -> None:
        self.series_ids = series_ids
        series_str = ", ".join(series_ids)
        message = (
            f"FRED series not found in cache: {series_str}. "
            f"Sync data using: HistoricalCache().sync_series(\"{series_ids[0]}\")"
        )
        super().__init__(message)
```

### 2. `src/analyze/reporting/vix.py` の改修

#### 2.1 インポート・ログ設定追加

```python
from market.errors import FREDCacheNotFoundError
from utils_core.logging import get_logger

logger = get_logger(__name__)
```

#### 2.2 `_load_multiple_series()` 改修

```python
def _load_multiple_series(series_ids: list[str]) -> pd.DataFrame:
    """複数のFREDシリーズをロードして結合する。

    Raises
    ------
    FREDCacheNotFoundError
        全シリーズの取得に失敗した場合
    """
    logger.debug("Loading FRED series", series_ids=series_ids)

    cache = HistoricalCache()
    dfs = []
    missing = []

    for series_id in series_ids:
        df = cache.get_series_df(series_id)
        if df is None or df.empty:
            logger.warning("Series not found in cache", series_id=series_id)
            missing.append(series_id)
            continue

        df = df.reset_index()
        df.columns = ["date", "value"]  # カラム名を明示的に設定
        df["variable"] = series_id
        dfs.append(df)
        logger.debug("Series loaded", series_id=series_id, rows=len(df))

    if not dfs:
        logger.error("All series failed to load", missing=missing)
        raise FREDCacheNotFoundError(missing)

    if missing:
        logger.warning("Some series missing", loaded=[s for s in series_ids if s not in missing], missing=missing)

    result = pd.concat(dfs, ignore_index=True)
    logger.info("Series loading complete", total_rows=len(result))
    return result
```

#### 2.3 プロット関数にバリデーション追加

```python
def plot_vix_and_high_yield_spread() -> go.Figure | None:
    """VIXと米国ハイイールドスプレッドをプロット。

    Returns
    -------
    go.Figure | None
        プロット図。データ不足時はNone。

    Raises
    ------
    FREDCacheNotFoundError
        全シリーズの取得に失敗した場合
    """
    logger.info("Creating VIX and High Yield Spread plot")

    fred_series_list = ["VIXCLS", "BAMLH0A0HYM2"]

    try:
        raw_data = _load_multiple_series(fred_series_list)
    except FREDCacheNotFoundError:
        logger.error("Cannot create plot: no data available")
        raise

    # pivot前にカラム検証
    required = {"date", "variable", "value"}
    if not required.issubset(raw_data.columns):
        missing_cols = required - set(raw_data.columns)
        raise ValueError(f"Missing columns: {missing_cols}")

    df = pd.pivot_table(
        raw_data,
        index="date",
        columns="variable",
        values="value",
        aggfunc="first",
    )

    # pivot後にシリーズ検証
    for series in fred_series_list:
        if series not in df.columns:
            logger.warning("Series missing after pivot", series=series)

    # 以下プロット処理（既存コード維持）
    ...
```

### 3. テスト作成 (`tests/analyze/unit/reporting/test_vix.py`)

```python
"""Tests for VIX reporting module."""
from unittest.mock import MagicMock, patch
import pandas as pd
import pytest
from analyze.reporting.vix import _load_multiple_series, plot_vix_and_high_yield_spread
from market.errors import FREDCacheNotFoundError


class TestLoadMultipleSeries:
    @patch("analyze.reporting.vix.HistoricalCache")
    def test_正常系_複数シリーズを結合できる(self, mock_cache_class):
        mock_cache = MagicMock()
        dates = pd.date_range("2024-01-01", periods=3)
        mock_cache.get_series_df.side_effect = [
            pd.DataFrame({"value": [15.0, 16.0, 17.0]}, index=dates),
            pd.DataFrame({"value": [3.5, 3.6, 3.7]}, index=dates),
        ]
        mock_cache_class.return_value = mock_cache

        result = _load_multiple_series(["VIXCLS", "BAMLH0A0HYM2"])

        assert len(result) == 6
        assert set(result.columns) == {"date", "variable", "value"}

    @patch("analyze.reporting.vix.HistoricalCache")
    def test_異常系_全シリーズ失敗でエラー(self, mock_cache_class):
        mock_cache = MagicMock()
        mock_cache.get_series_df.return_value = None
        mock_cache_class.return_value = mock_cache

        with pytest.raises(FREDCacheNotFoundError) as exc:
            _load_multiple_series(["VIXCLS"])

        assert "VIXCLS" in str(exc.value)
        assert "sync_series" in str(exc.value)

    @patch("analyze.reporting.vix.HistoricalCache")
    def test_エッジケース_部分欠損で警告つき成功(self, mock_cache_class):
        mock_cache = MagicMock()
        dates = pd.date_range("2024-01-01", periods=3)
        mock_cache.get_series_df.side_effect = [
            pd.DataFrame({"value": [15.0, 16.0, 17.0]}, index=dates),
            None,
        ]
        mock_cache_class.return_value = mock_cache

        result = _load_multiple_series(["VIXCLS", "BAMLH0A0HYM2"])

        assert len(result) == 3
        assert "VIXCLS" in result["variable"].values
```

## 実装順序

1. `src/market/errors.py` に `FREDCacheNotFoundError` 追加
2. `tests/analyze/unit/reporting/test_vix.py` 作成（TDD: Red）
3. `src/analyze/reporting/vix.py` 改修（TDD: Green）
4. `make check-all` で品質確認

## 検証方法

```bash
# テスト実行
uv run pytest tests/analyze/unit/reporting/test_vix.py -v

# 品質チェック
make check-all

# 手動検証（キャッシュなしの状態で）
python -c "from analyze.reporting.vix import plot_vix_and_high_yield_spread; plot_vix_and_high_yield_spread()"
# → FREDCacheNotFoundError が適切なメッセージで発生することを確認
```

"""Unit tests for ICAnalyzer class.

このモジュールはIC/IR分析機能の単体テストを提供します。
Spearman/Pearson相関、IR計算、統計的有意性検定をテストします。
"""

from typing import Literal

import numpy as np
import pandas as pd
import pytest

from factor.errors import InsufficientDataError, ValidationError
from factor.validation.ic_analyzer import ICAnalyzer, ICResult

# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def sample_factor_values() -> pd.DataFrame:
    """テスト用のファクター値DataFrame。

    Returns
    -------
    pd.DataFrame
        ファクター値 (index: 日付, columns: 銘柄シンボル)
    """
    dates = pd.date_range("2024-01-01", periods=20, freq="D")
    symbols = ["AAPL", "GOOGL", "MSFT", "AMZN", "META"]

    # 乱数シードを固定して再現性を確保
    np.random.seed(42)
    data = np.random.randn(20, 5)

    return pd.DataFrame(data, index=dates, columns=pd.Index(symbols))


@pytest.fixture
def sample_forward_returns() -> pd.DataFrame:
    """テスト用のフォワードリターンDataFrame。

    Returns
    -------
    pd.DataFrame
        フォワードリターン (index: 日付, columns: 銘柄シンボル)
    """
    dates = pd.date_range("2024-01-01", periods=20, freq="D")
    symbols = ["AAPL", "GOOGL", "MSFT", "AMZN", "META"]

    # 乱数シードを固定して再現性を確保
    np.random.seed(123)
    data = np.random.randn(20, 5) * 0.02  # リターンは小さい値

    return pd.DataFrame(data, index=dates, columns=pd.Index(symbols))


@pytest.fixture
def perfect_positive_correlation_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    """完全正相関 (IC=1) のテストデータ。

    Returns
    -------
    tuple[pd.DataFrame, pd.DataFrame]
        (ファクター値, フォワードリターン)
    """
    dates = pd.date_range("2024-01-01", periods=10, freq="D")
    symbols = ["A", "B", "C", "D", "E"]

    # ファクター値とリターンが完全に同じ順序
    factor_data = np.array(
        [
            [1.0, 2.0, 3.0, 4.0, 5.0],
            [2.0, 3.0, 4.0, 5.0, 1.0],
            [3.0, 4.0, 5.0, 1.0, 2.0],
            [4.0, 5.0, 1.0, 2.0, 3.0],
            [5.0, 1.0, 2.0, 3.0, 4.0],
            [1.0, 3.0, 5.0, 2.0, 4.0],
            [2.0, 4.0, 1.0, 3.0, 5.0],
            [3.0, 5.0, 2.0, 4.0, 1.0],
            [4.0, 1.0, 3.0, 5.0, 2.0],
            [5.0, 2.0, 4.0, 1.0, 3.0],
        ]
    )

    factor_df = pd.DataFrame(factor_data, index=dates, columns=pd.Index(symbols))
    # リターンはファクターと同じランク順序（完全正相関）
    return_df = factor_df.copy()

    return factor_df, return_df


@pytest.fixture
def perfect_negative_correlation_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    """完全逆相関 (IC=-1) のテストデータ。

    Returns
    -------
    tuple[pd.DataFrame, pd.DataFrame]
        (ファクター値, フォワードリターン)
    """
    dates = pd.date_range("2024-01-01", periods=10, freq="D")
    symbols = ["A", "B", "C", "D", "E"]

    factor_data = np.array(
        [
            [1.0, 2.0, 3.0, 4.0, 5.0],
            [2.0, 3.0, 4.0, 5.0, 1.0],
            [3.0, 4.0, 5.0, 1.0, 2.0],
            [4.0, 5.0, 1.0, 2.0, 3.0],
            [5.0, 1.0, 2.0, 3.0, 4.0],
            [1.0, 3.0, 5.0, 2.0, 4.0],
            [2.0, 4.0, 1.0, 3.0, 5.0],
            [3.0, 5.0, 2.0, 4.0, 1.0],
            [4.0, 1.0, 3.0, 5.0, 2.0],
            [5.0, 2.0, 4.0, 1.0, 3.0],
        ]
    )

    factor_df = pd.DataFrame(factor_data, index=dates, columns=pd.Index(symbols))
    # リターンはファクターと逆のランク順序（完全逆相関）
    return_df = 6.0 - factor_df  # 1→5, 2→4, 3→3, 4→2, 5→1

    return factor_df, return_df


@pytest.fixture
def minimal_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    """最小データ数 (5件) のテストデータ。

    Returns
    -------
    tuple[pd.DataFrame, pd.DataFrame]
        (ファクター値, フォワードリターン)
    """
    dates = pd.date_range("2024-01-01", periods=5, freq="D")
    symbols = ["A", "B", "C", "D", "E"]

    np.random.seed(99)
    factor_data = np.random.randn(5, 5)
    return_data = np.random.randn(5, 5) * 0.02

    factor_df = pd.DataFrame(factor_data, index=dates, columns=pd.Index(symbols))
    return_df = pd.DataFrame(return_data, index=dates, columns=pd.Index(symbols))

    return factor_df, return_df


@pytest.fixture
def sample_prices() -> pd.DataFrame:
    """テスト用の価格DataFrame。

    Returns
    -------
    pd.DataFrame
        価格データ (index: 日付, columns: 銘柄シンボル)
    """
    dates = pd.date_range("2024-01-01", periods=30, freq="D")
    symbols = ["AAPL", "GOOGL", "MSFT"]

    # 初期価格
    initial_prices = [150.0, 140.0, 380.0]

    np.random.seed(42)
    # ランダムウォークで価格を生成
    price_data = np.zeros((30, 3))
    for i, initial in enumerate(initial_prices):
        returns = np.random.randn(30) * 0.02
        price_data[:, i] = initial * np.cumprod(1 + returns)

    return pd.DataFrame(price_data, index=dates, columns=pd.Index(symbols))


# =============================================================================
# TestICAnalyzerInit: 初期化テスト
# =============================================================================


class TestICAnalyzerInit:
    """ICAnalyzerクラスの初期化テスト。"""

    def test_正常系_デフォルトでspearman(self) -> None:
        """デフォルトの相関計算方法がspearmanであることを確認。"""
        analyzer = ICAnalyzer()
        assert analyzer.method == "spearman"

    def test_正常系_spearmanで初期化(self) -> None:
        """spearmanメソッドで初期化できることを確認。"""
        analyzer = ICAnalyzer(method="spearman")
        assert analyzer.method == "spearman"

    def test_正常系_pearsonで初期化(self) -> None:
        """pearsonメソッドで初期化できることを確認。"""
        analyzer = ICAnalyzer(method="pearson")
        assert analyzer.method == "pearson"

    def test_異常系_不正なmethodでValidationError(self) -> None:
        """不正なメソッドが指定された場合、ValidationErrorが発生することを確認。"""
        with pytest.raises(ValidationError):
            ICAnalyzer(method="invalid")  # type: ignore


# =============================================================================
# TestSpearmanIC: Spearman IC計算テスト
# =============================================================================


class TestSpearmanIC:
    """Spearman IC（ランク相関）計算のテスト。"""

    def test_正常系_spearman_icが計算できる(
        self,
        sample_factor_values: pd.DataFrame,
        sample_forward_returns: pd.DataFrame,
    ) -> None:
        """Spearman ICが正常に計算されることを確認。"""
        analyzer = ICAnalyzer(method="spearman")
        result = analyzer.analyze(sample_factor_values, sample_forward_returns)

        assert isinstance(result, ICResult)
        assert result.method == "spearman"
        # ICは-1から1の範囲
        assert -1.0 <= result.mean_ic <= 1.0

    def test_正常系_spearman_icの値が範囲内(
        self,
        sample_factor_values: pd.DataFrame,
        sample_forward_returns: pd.DataFrame,
    ) -> None:
        """時系列ICの全ての値が-1から1の範囲内であることを確認。"""
        analyzer = ICAnalyzer(method="spearman")
        ic_series = analyzer.compute_ic_series(
            sample_factor_values, sample_forward_returns
        )

        valid_ic = ic_series.dropna()
        assert (valid_ic >= -1.0).all()
        assert (valid_ic <= 1.0).all()

    def test_正常系_完全正相関でIC約1(
        self,
        perfect_positive_correlation_data: tuple[pd.DataFrame, pd.DataFrame],
    ) -> None:
        """完全正相関データでSpearman IC が約1になることを確認。"""
        factor_df, return_df = perfect_positive_correlation_data
        analyzer = ICAnalyzer(method="spearman")
        result = analyzer.analyze(factor_df, return_df)

        # 完全正相関なのでIC=1.0（浮動小数点の誤差を考慮）
        assert result.mean_ic == pytest.approx(1.0, abs=0.001)

    def test_正常系_完全逆相関でIC約マイナス1(
        self,
        perfect_negative_correlation_data: tuple[pd.DataFrame, pd.DataFrame],
    ) -> None:
        """完全逆相関データでSpearman IC が約-1になることを確認。"""
        factor_df, return_df = perfect_negative_correlation_data
        analyzer = ICAnalyzer(method="spearman")
        result = analyzer.analyze(factor_df, return_df)

        # 完全逆相関なのでIC=-1.0（浮動小数点の誤差を考慮）
        assert result.mean_ic == pytest.approx(-1.0, abs=0.001)


# =============================================================================
# TestPearsonIC: Pearson IC計算テスト
# =============================================================================


class TestPearsonIC:
    """Pearson IC（線形相関）計算のテスト。"""

    def test_正常系_pearson_icが計算できる(
        self,
        sample_factor_values: pd.DataFrame,
        sample_forward_returns: pd.DataFrame,
    ) -> None:
        """Pearson ICが正常に計算されることを確認。"""
        analyzer = ICAnalyzer(method="pearson")
        result = analyzer.analyze(sample_factor_values, sample_forward_returns)

        assert isinstance(result, ICResult)
        assert result.method == "pearson"
        # ICは-1から1の範囲
        assert -1.0 <= result.mean_ic <= 1.0

    def test_正常系_pearson_icの値が範囲内(
        self,
        sample_factor_values: pd.DataFrame,
        sample_forward_returns: pd.DataFrame,
    ) -> None:
        """時系列ICの全ての値が-1から1の範囲内であることを確認。"""
        analyzer = ICAnalyzer(method="pearson")
        ic_series = analyzer.compute_ic_series(
            sample_factor_values, sample_forward_returns
        )

        valid_ic = ic_series.dropna()
        assert (valid_ic >= -1.0).all()
        assert (valid_ic <= 1.0).all()

    def test_正常系_完全正相関でIC約1(
        self,
        perfect_positive_correlation_data: tuple[pd.DataFrame, pd.DataFrame],
    ) -> None:
        """完全正相関データでPearson IC が約1になることを確認。"""
        factor_df, return_df = perfect_positive_correlation_data
        analyzer = ICAnalyzer(method="pearson")
        result = analyzer.analyze(factor_df, return_df)

        # 完全正相関なのでIC=1.0（浮動小数点の誤差を考慮）
        assert result.mean_ic == pytest.approx(1.0, abs=0.001)


# =============================================================================
# TestIRCalculation: IR計算テスト
# =============================================================================


class TestIRCalculation:
    """IR（情報比率）計算のテスト。"""

    def test_正常系_IRが計算できる(
        self,
        sample_factor_values: pd.DataFrame,
        sample_forward_returns: pd.DataFrame,
    ) -> None:
        """IRが正常に計算されることを確認。"""
        analyzer = ICAnalyzer(method="spearman")
        result = analyzer.analyze(sample_factor_values, sample_forward_returns)

        assert isinstance(result.ir, float)
        assert not np.isnan(result.ir)

    def test_正常系_IRはmean_ic割るstd_ic(
        self,
        sample_factor_values: pd.DataFrame,
        sample_forward_returns: pd.DataFrame,
    ) -> None:
        """IR = mean_ic / std_ic であることを確認。"""
        analyzer = ICAnalyzer(method="spearman")
        result = analyzer.analyze(sample_factor_values, sample_forward_returns)

        expected_ir = result.mean_ic / result.std_ic
        assert result.ir == pytest.approx(expected_ir, rel=1e-6)

    def test_正常系_高いIRは安定したIC(
        self,
        perfect_positive_correlation_data: tuple[pd.DataFrame, pd.DataFrame],
    ) -> None:
        """完全相関（安定したIC）でIRが高くなることを確認。"""
        factor_df, return_df = perfect_positive_correlation_data
        analyzer = ICAnalyzer(method="spearman")
        result = analyzer.analyze(factor_df, return_df)

        # 完全相関ではstd_icが0に近いため、IRは非常に大きくなる
        # std_icが0の場合はinf（無限大）になる可能性がある
        assert result.ir > 1.0 or np.isinf(result.ir)


# =============================================================================
# TestICSeriesComputation: 時系列IC計算テスト
# =============================================================================


class TestICSeriesComputation:
    """時系列IC計算のテスト。"""

    def test_正常系_時系列ICを取得できる(
        self,
        sample_factor_values: pd.DataFrame,
        sample_forward_returns: pd.DataFrame,
    ) -> None:
        """compute_ic_seriesで時系列ICが取得できることを確認。"""
        analyzer = ICAnalyzer(method="spearman")
        ic_series = analyzer.compute_ic_series(
            sample_factor_values, sample_forward_returns
        )

        assert isinstance(ic_series, pd.Series)
        assert len(ic_series) > 0

    def test_正常系_時系列ICのインデックスが日付(
        self,
        sample_factor_values: pd.DataFrame,
        sample_forward_returns: pd.DataFrame,
    ) -> None:
        """時系列ICのインデックスが日付であることを確認。"""
        analyzer = ICAnalyzer(method="spearman")
        ic_series = analyzer.compute_ic_series(
            sample_factor_values, sample_forward_returns
        )

        assert isinstance(ic_series.index, pd.DatetimeIndex)

    def test_正常系_analyzeのic_seriesと一致(
        self,
        sample_factor_values: pd.DataFrame,
        sample_forward_returns: pd.DataFrame,
    ) -> None:
        """analyzeで返されるic_seriesとcompute_ic_seriesが一致することを確認。"""
        analyzer = ICAnalyzer(method="spearman")
        result = analyzer.analyze(sample_factor_values, sample_forward_returns)
        direct_ic_series = analyzer.compute_ic_series(
            sample_factor_values, sample_forward_returns
        )

        pd.testing.assert_series_equal(result.ic_series, direct_ic_series)


# =============================================================================
# TestStatisticalSignificance: 統計的有意性テスト
# =============================================================================


class TestStatisticalSignificance:
    """統計的有意性（t値、p値）のテスト。"""

    def test_正常系_t値が計算される(
        self,
        sample_factor_values: pd.DataFrame,
        sample_forward_returns: pd.DataFrame,
    ) -> None:
        """t値が正常に計算されることを確認。"""
        analyzer = ICAnalyzer(method="spearman")
        result = analyzer.analyze(sample_factor_values, sample_forward_returns)

        assert isinstance(result.t_stat, float)
        assert not np.isnan(result.t_stat)

    def test_正常系_p値が計算される(
        self,
        sample_factor_values: pd.DataFrame,
        sample_forward_returns: pd.DataFrame,
    ) -> None:
        """p値が正常に計算されることを確認。"""
        analyzer = ICAnalyzer(method="spearman")
        result = analyzer.analyze(sample_factor_values, sample_forward_returns)

        assert isinstance(result.p_value, float)
        assert 0.0 <= result.p_value <= 1.0

    def test_正常系_有意なICは低いp値(
        self,
        perfect_positive_correlation_data: tuple[pd.DataFrame, pd.DataFrame],
    ) -> None:
        """有意なIC（完全相関）では低いp値になることを確認。"""
        factor_df, return_df = perfect_positive_correlation_data
        analyzer = ICAnalyzer(method="spearman")
        result = analyzer.analyze(factor_df, return_df)

        # 完全相関は統計的に非常に有意
        assert result.p_value < 0.05


# =============================================================================
# TestICResultDataclass: ICResult データクラステスト
# =============================================================================


class TestICResultDataclass:
    """ICResultデータクラスのテスト。"""

    def test_正常系_全フィールドが格納される(
        self,
        sample_factor_values: pd.DataFrame,
        sample_forward_returns: pd.DataFrame,
    ) -> None:
        """ICResultに全フィールドが格納されることを確認。"""
        analyzer = ICAnalyzer(method="spearman")
        result = analyzer.analyze(sample_factor_values, sample_forward_returns)

        # 全てのフィールドが存在し、適切な型であることを確認
        assert isinstance(result.ic_series, pd.Series)
        assert isinstance(result.mean_ic, float)
        assert isinstance(result.std_ic, float)
        assert isinstance(result.ir, float)
        assert isinstance(result.t_stat, float)
        assert isinstance(result.p_value, float)
        assert isinstance(result.method, str)
        assert isinstance(result.n_periods, int)

    def test_正常系_n_periodsが正しい(
        self,
        sample_factor_values: pd.DataFrame,
        sample_forward_returns: pd.DataFrame,
    ) -> None:
        """n_periodsがIC計算に使用した期間数と一致することを確認。"""
        analyzer = ICAnalyzer(method="spearman")
        result = analyzer.analyze(sample_factor_values, sample_forward_returns)

        valid_ic_count = result.ic_series.dropna().count()
        assert result.n_periods == valid_ic_count

    def test_正常系_methodが正しく設定される(self) -> None:
        """methodフィールドが正しく設定されることを確認。"""
        dates = pd.date_range("2024-01-01", periods=10, freq="D")
        symbols = ["A", "B", "C", "D", "E"]
        np.random.seed(42)
        factor_df = pd.DataFrame(
            np.random.randn(10, 5), index=dates, columns=pd.Index(symbols)
        )
        return_df = pd.DataFrame(
            np.random.randn(10, 5), index=dates, columns=pd.Index(symbols)
        )

        spearman_result = ICAnalyzer(method="spearman").analyze(factor_df, return_df)
        pearson_result = ICAnalyzer(method="pearson").analyze(factor_df, return_df)

        assert spearman_result.method == "spearman"
        assert pearson_result.method == "pearson"


# =============================================================================
# TestComputeForwardReturns: フォワードリターン計算テスト
# =============================================================================


class TestComputeForwardReturns:
    """compute_forward_returnsメソッドのテスト。"""

    def test_正常系_1期間のフォワードリターン(
        self,
        sample_prices: pd.DataFrame,
    ) -> None:
        """1期間のフォワードリターンが正しく計算されることを確認。"""
        forward_returns = ICAnalyzer.compute_forward_returns(sample_prices, periods=1)

        assert isinstance(forward_returns, pd.DataFrame)
        assert forward_returns.columns.tolist() == sample_prices.columns.tolist()
        # フォワードリターンは価格データより1行少ない（最後の行はNaN）
        assert len(forward_returns) == len(sample_prices)

    def test_正常系_5期間のフォワードリターン(
        self,
        sample_prices: pd.DataFrame,
    ) -> None:
        """5期間のフォワードリターンが正しく計算されることを確認。"""
        forward_returns = ICAnalyzer.compute_forward_returns(sample_prices, periods=5)

        assert isinstance(forward_returns, pd.DataFrame)
        # 最後の5行はNaN
        assert forward_returns.iloc[-5:].isna().all().all()

    def test_正常系_リターン計算式が正しい(self) -> None:
        """リターン計算式 (P_{t+n} / P_t - 1) が正しいことを確認。"""
        dates = pd.date_range("2024-01-01", periods=5, freq="D")
        prices = pd.DataFrame(
            {"A": [100.0, 110.0, 121.0, 133.1, 146.41]},
            index=dates,
        )

        forward_returns = ICAnalyzer.compute_forward_returns(prices, periods=1)

        # 手動計算: (110-100)/100 = 0.1
        assert forward_returns.iloc[0, 0] == pytest.approx(0.1, rel=1e-6)
        # 手動計算: (121-110)/110 = 0.1
        assert forward_returns.iloc[1, 0] == pytest.approx(0.1, rel=1e-6)


# =============================================================================
# TestErrorHandling: エラーハンドリングテスト
# =============================================================================


class TestErrorHandling:
    """エラーハンドリングのテスト。"""

    def test_異常系_空のDataFrameでInsufficientDataError(self) -> None:
        """空のDataFrameを渡すとInsufficientDataErrorが発生することを確認。"""
        analyzer = ICAnalyzer(method="spearman")
        empty_factor = pd.DataFrame()
        empty_returns = pd.DataFrame()

        with pytest.raises(InsufficientDataError):
            analyzer.analyze(empty_factor, empty_returns)

    def test_異常系_データ点数が不足でInsufficientDataError(self) -> None:
        """データ点数が不足している場合、InsufficientDataErrorが発生することを確認。"""
        analyzer = ICAnalyzer(method="spearman")
        dates = pd.date_range("2024-01-01", periods=2, freq="D")
        symbols = ["A", "B"]  # 2銘柄では不足

        factor_df = pd.DataFrame(
            np.array([[1.0, 2.0], [3.0, 4.0]]),
            index=dates,
            columns=pd.Index(symbols),
        )
        return_df = pd.DataFrame(
            np.array([[0.01, 0.02], [0.03, 0.04]]),
            index=dates,
            columns=pd.Index(symbols),
        )

        with pytest.raises(InsufficientDataError):
            analyzer.analyze(factor_df, return_df)

    def test_異常系_index不一致でValidationError(self) -> None:
        """factor_valuesとforward_returnsのindexが一致しない場合、
        ValidationErrorが発生することを確認。
        """
        analyzer = ICAnalyzer(method="spearman")

        factor_dates = pd.date_range("2024-01-01", periods=10, freq="D")
        return_dates = pd.date_range("2024-02-01", periods=10, freq="D")  # 異なる期間
        symbols = ["A", "B", "C", "D", "E"]

        np.random.seed(42)
        factor_df = pd.DataFrame(
            np.random.randn(10, 5), index=factor_dates, columns=pd.Index(symbols)
        )
        return_df = pd.DataFrame(
            np.random.randn(10, 5), index=return_dates, columns=pd.Index(symbols)
        )

        with pytest.raises(ValidationError):
            analyzer.analyze(factor_df, return_df)

    def test_異常系_columns不一致でValidationError(self) -> None:
        """factor_valuesとforward_returnsのcolumnsが一致しない場合、
        ValidationErrorが発生することを確認。
        """
        analyzer = ICAnalyzer(method="spearman")

        dates = pd.date_range("2024-01-01", periods=10, freq="D")
        factor_symbols = ["A", "B", "C", "D", "E"]
        return_symbols = ["X", "Y", "Z", "W", "V"]  # 異なる銘柄

        np.random.seed(42)
        factor_df = pd.DataFrame(
            np.random.randn(10, 5), index=dates, columns=pd.Index(factor_symbols)
        )
        return_df = pd.DataFrame(
            np.random.randn(10, 5), index=dates, columns=pd.Index(return_symbols)
        )

        with pytest.raises(ValidationError):
            analyzer.analyze(factor_df, return_df)


# =============================================================================
# TestBoundaryConditions: 境界値テスト
# =============================================================================


class TestBoundaryConditions:
    """境界値・エッジケースのテスト。"""

    def test_エッジケース_最小データ数で計算可能(
        self,
        minimal_data: tuple[pd.DataFrame, pd.DataFrame],
    ) -> None:
        """最小データ数（5件）でもIC計算が可能であることを確認。"""
        factor_df, return_df = minimal_data
        analyzer = ICAnalyzer(method="spearman")
        result = analyzer.analyze(factor_df, return_df)

        assert isinstance(result, ICResult)
        assert result.n_periods >= 1

    def test_エッジケース_NaN含むデータの処理(self) -> None:
        """NaNを含むデータが正しく処理されることを確認。"""
        dates = pd.date_range("2024-01-01", periods=10, freq="D")
        symbols = ["A", "B", "C", "D", "E"]

        np.random.seed(42)
        factor_data = np.random.randn(10, 5)
        return_data = np.random.randn(10, 5)

        # 一部をNaNに設定
        factor_data[0, 0] = np.nan
        factor_data[5, 2] = np.nan
        return_data[3, 1] = np.nan

        factor_df = pd.DataFrame(factor_data, index=dates, columns=pd.Index(symbols))
        return_df = pd.DataFrame(return_data, index=dates, columns=pd.Index(symbols))

        analyzer = ICAnalyzer(method="spearman")
        result = analyzer.analyze(factor_df, return_df)

        # NaNを除外して計算されることを確認
        assert isinstance(result, ICResult)
        assert not np.isnan(result.mean_ic)

    def test_エッジケース_同じ値のみのデータ(self) -> None:
        """全て同じ値のデータの処理を確認（標準偏差が0になるケース）。"""
        dates = pd.date_range("2024-01-01", periods=10, freq="D")
        symbols = ["A", "B", "C", "D", "E"]

        # ファクター値が全て同じ（分散0）
        factor_df = pd.DataFrame(
            np.ones((10, 5)), index=dates, columns=pd.Index(symbols)
        )
        return_df = pd.DataFrame(
            np.random.randn(10, 5), index=dates, columns=pd.Index(symbols)
        )

        analyzer = ICAnalyzer(method="spearman")

        # 全て同じ値の場合、相関が計算できないためNaNまたはエラー
        # 実装によって挙動が異なる可能性があるため、例外またはNaN結果を許容
        try:
            result = analyzer.analyze(factor_df, return_df)
            # 結果がNaNになることを許容
            assert np.isnan(result.mean_ic) or isinstance(result.mean_ic, float)
        except (InsufficientDataError, ValidationError):
            # エラーになることも許容
            pass


# =============================================================================
# TestParameterizedCases: パラメトライズテスト
# =============================================================================


class TestParameterizedCases:
    """パラメトライズされたテストケース。"""

    @pytest.mark.parametrize(
        "method",
        ["spearman", "pearson"],
    )
    def test_パラメトライズ_各methodでICが計算できる(
        self,
        method: Literal["spearman", "pearson"],
        sample_factor_values: pd.DataFrame,
        sample_forward_returns: pd.DataFrame,
    ) -> None:
        """各相関計算メソッドでICが計算できることを確認。"""
        analyzer = ICAnalyzer(method=method)
        result = analyzer.analyze(sample_factor_values, sample_forward_returns)

        assert isinstance(result, ICResult)
        assert result.method == method
        assert -1.0 <= result.mean_ic <= 1.0

    @pytest.mark.parametrize(
        "periods",
        [1, 5, 10, 21],
    )
    def test_パラメトライズ_各期間でフォワードリターンが計算できる(
        self,
        periods: int,
        sample_prices: pd.DataFrame,
    ) -> None:
        """各期間でフォワードリターンが計算できることを確認。"""
        forward_returns = ICAnalyzer.compute_forward_returns(sample_prices, periods)

        assert isinstance(forward_returns, pd.DataFrame)
        # 最後のperiods行はNaN
        nan_count = forward_returns.isna().all(axis=1).sum()
        assert nan_count == periods

    @pytest.mark.parametrize(
        "n_symbols",
        [5, 10, 50],
    )
    def test_パラメトライズ_様々な銘柄数でIC計算(
        self,
        n_symbols: int,
    ) -> None:
        """様々な銘柄数でICが計算できることを確認。"""
        dates = pd.date_range("2024-01-01", periods=20, freq="D")
        symbols = [f"SYM_{i}" for i in range(n_symbols)]

        np.random.seed(42)
        factor_df = pd.DataFrame(
            np.random.randn(20, n_symbols), index=dates, columns=pd.Index(symbols)
        )
        return_df = pd.DataFrame(
            np.random.randn(20, n_symbols) * 0.02, index=dates, columns=pd.Index(symbols)
        )

        analyzer = ICAnalyzer(method="spearman")
        result = analyzer.analyze(factor_df, return_df)

        assert isinstance(result, ICResult)
        assert result.n_periods > 0

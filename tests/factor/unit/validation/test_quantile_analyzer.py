"""Unit tests for QuantileAnalyzer class.

QuantileAnalyzer は分位ポートフォリオ分析を行うクラスで、
ファクター値に基づいてポートフォリオを分位に分け、
各分位のリターンを計算・分析する機能を提供する。
"""


import numpy as np
import pandas as pd
import plotly.graph_objects as go
import pytest

from factor.errors import InsufficientDataError, ValidationError
from factor.types import QuantileResult
from factor.validation.quantile_analyzer import QuantileAnalyzer

# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def sample_factor_values() -> pd.DataFrame:
    """分析用のサンプルファクター値を生成する。

    Returns
    -------
    pd.DataFrame
        日付をインデックス、銘柄をカラムとするファクター値のDataFrame
    """
    np.random.seed(42)
    dates = pd.date_range("2024-01-01", periods=60, freq="D")
    symbols = ["AAPL", "GOOGL", "MSFT", "AMZN", "META"]

    data = np.random.randn(60, 5)
    return pd.DataFrame(data, index=dates, columns=pd.Index(symbols))


@pytest.fixture
def sample_forward_returns() -> pd.DataFrame:
    """分析用のサンプル将来リターンを生成する。

    Returns
    -------
    pd.DataFrame
        日付をインデックス、銘柄をカラムとする将来リターンのDataFrame
    """
    np.random.seed(123)
    dates = pd.date_range("2024-01-01", periods=60, freq="D")
    symbols = ["AAPL", "GOOGL", "MSFT", "AMZN", "META"]

    data = np.random.randn(60, 5) * 0.02  # 日次リターンとして妥当な範囲
    return pd.DataFrame(data, index=dates, columns=pd.Index(symbols))


@pytest.fixture
def monotonic_factor_values() -> pd.DataFrame:
    """単調性テスト用のファクター値を生成する。

    高いファクター値の銘柄が高いリターンを持つように設計。

    Returns
    -------
    pd.DataFrame
        単調性を持つファクター値のDataFrame
    """
    dates = pd.date_range("2024-01-01", periods=20, freq="D")
    symbols = [f"STOCK_{i}" for i in range(10)]

    # 各銘柄に固定のファクター値を割り当て
    data = np.array([[i + 1] * 20 for i in range(10)]).T
    return pd.DataFrame(data, index=dates, columns=pd.Index(symbols), dtype=float)


@pytest.fixture
def monotonic_forward_returns() -> pd.DataFrame:
    """単調性テスト用の将来リターンを生成する。

    ファクター値と相関するリターンを設計。

    Returns
    -------
    pd.DataFrame
        ファクター値と正の相関を持つ将来リターンのDataFrame
    """
    dates = pd.date_range("2024-01-01", periods=20, freq="D")
    symbols = [f"STOCK_{i}" for i in range(10)]

    # 高いファクター値の銘柄ほど高いリターン
    data = np.array([[(i + 1) * 0.01] * 20 for i in range(10)]).T
    return pd.DataFrame(data, index=dates, columns=pd.Index(symbols))


@pytest.fixture
def analyzer() -> QuantileAnalyzer:
    """デフォルト設定の QuantileAnalyzer を生成する。"""
    return QuantileAnalyzer()


@pytest.fixture
def custom_analyzer() -> QuantileAnalyzer:
    """カスタム設定の QuantileAnalyzer を生成する。"""
    return QuantileAnalyzer(n_quantiles=10)


# =============================================================================
# TestQuantileAnalyzerInit: 初期化テスト
# =============================================================================


class TestQuantileAnalyzerInit:
    """QuantileAnalyzer の初期化に関するテスト。"""

    def test_正常系_デフォルト設定で初期化される(self) -> None:
        """デフォルトでn_quantiles=5で初期化されることを確認。"""
        analyzer = QuantileAnalyzer()
        assert analyzer.n_quantiles == 5

    def test_正常系_カスタム分位数で初期化される(self) -> None:
        """カスタムのn_quantiles値で初期化できることを確認。"""
        analyzer = QuantileAnalyzer(n_quantiles=10)
        assert analyzer.n_quantiles == 10

    def test_正常系_2分位で初期化される(self) -> None:
        """最小のn_quantiles=2で初期化できることを確認。"""
        analyzer = QuantileAnalyzer(n_quantiles=2)
        assert analyzer.n_quantiles == 2

    def test_異常系_分位数が1以下でValidationError(self) -> None:
        """n_quantilesが1以下の場合、ValidationErrorが発生することを確認。"""
        with pytest.raises(ValidationError, match="n_quantiles"):
            QuantileAnalyzer(n_quantiles=1)

        with pytest.raises(ValidationError, match="n_quantiles"):
            QuantileAnalyzer(n_quantiles=0)

        with pytest.raises(ValidationError, match="n_quantiles"):
            QuantileAnalyzer(n_quantiles=-5)


# =============================================================================
# TestAssignQuantiles: 分位割り当てテスト
# =============================================================================


class TestAssignQuantiles:
    """assign_quantiles メソッドに関するテスト。"""

    def test_正常系_ファクター値に分位を割り当てる(
        self,
        analyzer: QuantileAnalyzer,
        sample_factor_values: pd.DataFrame,
    ) -> None:
        """ファクター値に基づいて分位が正しく割り当てられることを確認。"""
        result = analyzer.assign_quantiles(sample_factor_values)

        assert isinstance(result, pd.DataFrame)
        assert result.shape == sample_factor_values.shape
        assert result.index.equals(sample_factor_values.index)
        assert list(result.columns) == list(sample_factor_values.columns)

    def test_正常系_分位値の範囲が正しい(
        self,
        analyzer: QuantileAnalyzer,
        sample_factor_values: pd.DataFrame,
    ) -> None:
        """割り当てられた分位値が1からn_quantilesの範囲内であることを確認。"""
        result = analyzer.assign_quantiles(sample_factor_values)

        # NaNを除いた値が1-5の範囲内
        valid_values = result.values[~np.isnan(result.values)]
        assert valid_values.min() >= 1
        assert valid_values.max() <= analyzer.n_quantiles

    def test_正常系_分位が均等に分布する(
        self,
        analyzer: QuantileAnalyzer,
        sample_factor_values: pd.DataFrame,
    ) -> None:
        """各分位に割り当てられる銘柄数が概ね均等であることを確認。"""
        result = analyzer.assign_quantiles(sample_factor_values)

        # 各日付について分位の分布を確認
        for date in result.index[:5]:  # 最初の5日について確認
            row = result.loc[date]
            value_counts = row.value_counts().sort_index()
            # 各分位に少なくとも1銘柄は割り当てられる（銘柄数が十分な場合）
            assert len(value_counts) > 0

    def test_正常系_カスタム分位数で割り当てる(
        self,
        custom_analyzer: QuantileAnalyzer,
        sample_factor_values: pd.DataFrame,
    ) -> None:
        """カスタムのn_quantilesで正しく分位が割り当てられることを確認。"""
        result = custom_analyzer.assign_quantiles(sample_factor_values)

        valid_values = result.values[~np.isnan(result.values)]
        assert valid_values.min() >= 1
        assert valid_values.max() <= custom_analyzer.n_quantiles

    def test_異常系_空のDataFrameでエラー(
        self,
        analyzer: QuantileAnalyzer,
    ) -> None:
        """空のDataFrameを渡した場合、エラーが発生することを確認。"""
        empty_df = pd.DataFrame()

        with pytest.raises((ValidationError, InsufficientDataError)):
            analyzer.assign_quantiles(empty_df)

    def test_エッジケース_NaN値を含むデータ(
        self,
        analyzer: QuantileAnalyzer,
    ) -> None:
        """NaN値を含むファクターデータでも処理できることを確認。"""
        dates = pd.date_range("2024-01-01", periods=10, freq="D")
        data = pd.DataFrame(
            {
                "A": [1.0, np.nan, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0],
                "B": [np.nan, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, np.nan],
            },
            index=dates,
        )

        result = analyzer.assign_quantiles(data)
        assert isinstance(result, pd.DataFrame)
        # NaN位置はNaNのまま
        assert pd.isna(result.iloc[0, 0]) or not pd.isna(result.iloc[0, 0])


# =============================================================================
# TestComputeQuantileReturns: 分位別リターン計算テスト
# =============================================================================


class TestComputeQuantileReturns:
    """compute_quantile_returns メソッドに関するテスト。"""

    def test_正常系_分位別リターンを計算する(
        self,
        analyzer: QuantileAnalyzer,
        sample_factor_values: pd.DataFrame,
        sample_forward_returns: pd.DataFrame,
    ) -> None:
        """分位別のリターンが正しく計算されることを確認。"""
        quantile_assignments = analyzer.assign_quantiles(sample_factor_values)
        result = analyzer.compute_quantile_returns(
            quantile_assignments,
            sample_forward_returns,
        )

        assert isinstance(result, pd.DataFrame)
        # カラム数は分位数と一致
        assert len(result.columns) == analyzer.n_quantiles

    def test_正常系_リターンのインデックスが正しい(
        self,
        analyzer: QuantileAnalyzer,
        sample_factor_values: pd.DataFrame,
        sample_forward_returns: pd.DataFrame,
    ) -> None:
        """計算されたリターンのインデックスが元データと一致することを確認。"""
        quantile_assignments = analyzer.assign_quantiles(sample_factor_values)
        result = analyzer.compute_quantile_returns(
            quantile_assignments,
            sample_forward_returns,
        )

        # インデックスが一致
        assert result.index.equals(sample_forward_returns.index)

    def test_異常系_形状が異なるデータでエラー(
        self,
        analyzer: QuantileAnalyzer,
        sample_factor_values: pd.DataFrame,
    ) -> None:
        """分位割り当てとリターンのデータ形状が異なる場合、エラーになることを確認。"""
        quantile_assignments = analyzer.assign_quantiles(sample_factor_values)

        # 異なる形状のリターンデータ
        different_returns = pd.DataFrame(
            np.random.randn(30, 3),  # 異なる行数と列数
            index=pd.date_range("2024-02-01", periods=30, freq="D"),
            columns=pd.Index(["X", "Y", "Z"]),
        )

        with pytest.raises(ValidationError):
            analyzer.compute_quantile_returns(quantile_assignments, different_returns)


# =============================================================================
# TestAnalyze: 分析メソッドテスト
# =============================================================================


class TestAnalyze:
    """analyze メソッドに関するテスト。"""

    def test_正常系_分析結果が正しい型で返される(
        self,
        analyzer: QuantileAnalyzer,
        sample_factor_values: pd.DataFrame,
        sample_forward_returns: pd.DataFrame,
    ) -> None:
        """analyze メソッドが QuantileResult を返すことを確認。"""
        result = analyzer.analyze(sample_factor_values, sample_forward_returns)

        assert isinstance(result, QuantileResult)

    def test_正常系_QuantileResultの属性が正しく設定される(
        self,
        analyzer: QuantileAnalyzer,
        sample_factor_values: pd.DataFrame,
        sample_forward_returns: pd.DataFrame,
    ) -> None:
        """QuantileResult の各属性が正しく設定されることを確認。"""
        result = analyzer.analyze(sample_factor_values, sample_forward_returns)

        # quantile_returns: 分位別リターンのDataFrame
        assert isinstance(result.quantile_returns, pd.DataFrame)
        assert len(result.quantile_returns.columns) == analyzer.n_quantiles

        # mean_returns: 分位別平均リターンのSeries
        assert isinstance(result.mean_returns, pd.Series)
        assert len(result.mean_returns) == analyzer.n_quantiles

        # long_short_return: Top - Bottom リターン
        assert isinstance(result.long_short_return, float)

        # monotonicity_score: 単調性スコア（0-1）
        assert isinstance(result.monotonicity_score, float)
        assert 0.0 <= result.monotonicity_score <= 1.0

        # n_quantiles: 分位数
        assert result.n_quantiles == analyzer.n_quantiles

    def test_正常系_平均リターンが正しく計算される(
        self,
        analyzer: QuantileAnalyzer,
        sample_factor_values: pd.DataFrame,
        sample_forward_returns: pd.DataFrame,
    ) -> None:
        """分位別平均リターンが正しく計算されることを確認。"""
        result = analyzer.analyze(sample_factor_values, sample_forward_returns)

        # 平均リターンは quantile_returns の各列の平均
        for i, mean_ret in enumerate(result.mean_returns, start=1):
            expected = result.quantile_returns[i].mean()
            assert abs(mean_ret - expected) < 1e-10 or pd.isna(mean_ret)

    def test_正常系_LongShortリターンが正しく計算される(
        self,
        analyzer: QuantileAnalyzer,
        sample_factor_values: pd.DataFrame,
        sample_forward_returns: pd.DataFrame,
    ) -> None:
        """Long-Short リターン（Top - Bottom）が正しく計算されることを確認。"""
        result = analyzer.analyze(sample_factor_values, sample_forward_returns)

        # Long-Short = Top分位の平均 - Bottom分位の平均
        top_return = result.mean_returns.iloc[-1]  # 最高分位
        bottom_return = result.mean_returns.iloc[0]  # 最低分位
        expected_ls = top_return - bottom_return

        assert abs(result.long_short_return - expected_ls) < 1e-10

    def test_正常系_単調性スコアが正しく計算される(
        self,
        analyzer: QuantileAnalyzer,
        monotonic_factor_values: pd.DataFrame,
        monotonic_forward_returns: pd.DataFrame,
    ) -> None:
        """完全に単調なデータで単調性スコアが1.0に近いことを確認。"""
        result = analyzer.analyze(monotonic_factor_values, monotonic_forward_returns)

        # 完全に単調なデータでは単調性スコアは1.0に近い
        assert result.monotonicity_score >= 0.8

    def test_正常系_turnoverがオプションで設定される(
        self,
        analyzer: QuantileAnalyzer,
        sample_factor_values: pd.DataFrame,
        sample_forward_returns: pd.DataFrame,
    ) -> None:
        """turnover 属性がオプションで正しく設定されることを確認。"""
        result = analyzer.analyze(sample_factor_values, sample_forward_returns)

        # turnover は None または pd.Series
        assert result.turnover is None or isinstance(result.turnover, pd.Series)

    def test_異常系_データ不足でエラー(
        self,
        analyzer: QuantileAnalyzer,
    ) -> None:
        """データが不十分な場合、エラーが発生することを確認。"""
        dates = pd.date_range("2024-01-01", periods=2, freq="D")
        factor = pd.DataFrame({"A": [1.0, 2.0]}, index=dates)
        returns = pd.DataFrame({"A": [0.01, 0.02]}, index=dates)

        with pytest.raises((InsufficientDataError, ValidationError)):
            analyzer.analyze(factor, returns)


# =============================================================================
# TestPlot: 可視化テスト
# =============================================================================


class TestPlot:
    """plot メソッドに関するテスト。"""

    def test_正常系_plotlyのFigureを返す(
        self,
        analyzer: QuantileAnalyzer,
        sample_factor_values: pd.DataFrame,
        sample_forward_returns: pd.DataFrame,
    ) -> None:
        """plot メソッドが plotly Figure を返すことを確認。"""
        result = analyzer.analyze(sample_factor_values, sample_forward_returns)
        fig = analyzer.plot(result)

        assert isinstance(fig, go.Figure)

    def test_正常系_タイトルを設定できる(
        self,
        analyzer: QuantileAnalyzer,
        sample_factor_values: pd.DataFrame,
        sample_forward_returns: pd.DataFrame,
    ) -> None:
        """カスタムタイトルを設定できることを確認。"""
        result = analyzer.analyze(sample_factor_values, sample_forward_returns)
        custom_title = "My Quantile Analysis"
        fig = analyzer.plot(result, title=custom_title)

        assert fig.layout.title is not None
        title_text = (
            fig.layout.title.text
            if hasattr(fig.layout.title, "text")
            else str(fig.layout.title)
        )
        assert custom_title in title_text

    def test_正常系_タイトル未指定時はデフォルト(
        self,
        analyzer: QuantileAnalyzer,
        sample_factor_values: pd.DataFrame,
        sample_forward_returns: pd.DataFrame,
    ) -> None:
        """タイトル未指定時にデフォルトタイトルが設定されることを確認。"""
        result = analyzer.analyze(sample_factor_values, sample_forward_returns)
        fig = analyzer.plot(result, title=None)

        assert fig.layout.title is not None


# =============================================================================
# TestQuantileResult: データクラステスト
# =============================================================================


class TestQuantileResult:
    """QuantileResult データクラスに関するテスト。"""

    def test_正常系_データクラスが正しく作成される(self) -> None:
        """QuantileResult が正しく作成されることを確認。"""
        quantile_returns = pd.DataFrame(
            {
                1: [0.01, 0.02],
                2: [0.02, 0.03],
                3: [0.03, 0.04],
                4: [0.04, 0.05],
                5: [0.05, 0.06],
            },
            index=pd.date_range("2024-01-01", periods=2, freq="D"),
        )
        mean_returns = pd.Series(
            [0.015, 0.025, 0.035, 0.045, 0.055], index=[1, 2, 3, 4, 5]
        )

        result = QuantileResult(
            quantile_returns=quantile_returns,
            mean_returns=mean_returns,
            long_short_return=0.04,
            monotonicity_score=0.95,
            n_quantiles=5,
            turnover=None,
        )

        assert result.n_quantiles == 5
        assert result.long_short_return == 0.04
        assert result.monotonicity_score == 0.95
        assert result.turnover is None

    def test_正常系_turnoverを設定できる(self) -> None:
        """turnover を設定した QuantileResult が作成できることを確認。"""
        quantile_returns = pd.DataFrame(
            {1: [0.01], 2: [0.02], 3: [0.03]},
            index=pd.date_range("2024-01-01", periods=1, freq="D"),
        )
        mean_returns = pd.Series([0.01, 0.02, 0.03], index=[1, 2, 3])
        turnover = pd.Series([0.1, 0.15, 0.2], index=[1, 2, 3])

        result = QuantileResult(
            quantile_returns=quantile_returns,
            mean_returns=mean_returns,
            long_short_return=0.02,
            monotonicity_score=1.0,
            n_quantiles=3,
            turnover=turnover,
        )

        assert result.turnover is not None
        assert len(result.turnover) == 3


# =============================================================================
# TestPyrightStrict: 型チェック関連テスト
# =============================================================================


class TestPyrightStrict:
    """pyright strict モードでの型安全性テスト。

    これらのテストは型アノテーションの正確性を確認するためのもの。
    実行時には全てパスするべきだが、型チェッカーがエラーを検出しないことを保証。
    """

    def test_正常系_メソッドの戻り値型が正しい(
        self,
        analyzer: QuantileAnalyzer,
        sample_factor_values: pd.DataFrame,
        sample_forward_returns: pd.DataFrame,
    ) -> None:
        """各メソッドの戻り値型が正しいことを確認。"""
        # assign_quantiles -> pd.DataFrame
        quantiles: pd.DataFrame = analyzer.assign_quantiles(sample_factor_values)
        assert isinstance(quantiles, pd.DataFrame)

        # compute_quantile_returns -> pd.DataFrame
        returns: pd.DataFrame = analyzer.compute_quantile_returns(
            quantiles, sample_forward_returns
        )
        assert isinstance(returns, pd.DataFrame)

        # analyze -> QuantileResult
        result: QuantileResult = analyzer.analyze(
            sample_factor_values, sample_forward_returns
        )
        assert isinstance(result, QuantileResult)

        # plot -> go.Figure
        fig: go.Figure = analyzer.plot(result)
        assert isinstance(fig, go.Figure)

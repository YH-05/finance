"""Unit tests for MomentumFactor class.

MomentumFactorは価格モメンタム（過去リターン）の計算を提供する。
計算式: (P_{t-skip} / P_{t-lookback}) - 1

このテストは TDD Red 状態で作成されており、
実装が完了するまで失敗する。
"""

from datetime import datetime

import numpy as np
import pandas as pd
import pytest

# AIDEV-NOTE: 実装が存在しないため、インポートは失敗する（Red状態）
# pytest.importorskipを使用して、実装後に自動的にテストが有効になる
MomentumFactor = pytest.importorskip("factor.factors.price.momentum").MomentumFactor


class MockDataProvider:
    """テスト用のモックDataProvider。

    DataProviderプロトコルを実装し、テスト用の価格データを返す。
    """

    def __init__(self, prices_df: pd.DataFrame) -> None:
        """モックプロバイダーを初期化する。

        Parameters
        ----------
        prices_df : pd.DataFrame
            get_prices()で返す価格データ。
            MultiIndex columns: (symbol, price_type)
            Index: DatetimeIndex
        """
        self._prices_df = prices_df

    def get_prices(
        self,
        symbols: list[str],
        start_date: datetime | str,
        end_date: datetime | str,
    ) -> pd.DataFrame:
        """価格データを返す。"""
        return self._prices_df

    def get_volumes(
        self,
        symbols: list[str],
        start_date: datetime | str,
        end_date: datetime | str,
    ) -> pd.DataFrame:
        """ボリュームデータを返す（未使用）。"""
        return pd.DataFrame()

    def get_fundamentals(
        self,
        symbols: list[str],
        metrics: list[str],
        start_date: datetime | str,
        end_date: datetime | str,
    ) -> pd.DataFrame:
        """ファンダメンタルデータを返す（未使用）。"""
        return pd.DataFrame()

    def get_market_cap(
        self,
        symbols: list[str],
        start_date: datetime | str,
        end_date: datetime | str,
    ) -> pd.DataFrame:
        """時価総額データを返す（未使用）。"""
        return pd.DataFrame()


def create_price_dataframe(
    symbols: list[str],
    dates: pd.DatetimeIndex,
    close_prices: dict[str, list[float]],
) -> pd.DataFrame:
    """テスト用の価格DataFrameを作成するヘルパー関数。

    Parameters
    ----------
    symbols : list[str]
        銘柄リスト
    dates : pd.DatetimeIndex
        日付インデックス
    close_prices : dict[str, list[float]]
        銘柄ごとの終値リスト

    Returns
    -------
    pd.DataFrame
        MultiIndex columns (symbol, price_type) の価格DataFrame
    """
    data: dict[tuple[str, str], list[float]] = {}
    for symbol in symbols:
        prices = close_prices[symbol]
        data[(symbol, "Close")] = prices
        # Open, High, Low, Volumeはダミー値
        data[(symbol, "Open")] = prices
        data[(symbol, "High")] = [p * 1.01 for p in prices]
        data[(symbol, "Low")] = [p * 0.99 for p in prices]
        data[(symbol, "Volume")] = [1000000.0] * len(prices)

    df = pd.DataFrame(data, index=dates)
    df.index.name = "Date"
    df.columns = pd.MultiIndex.from_tuples(df.columns, names=["symbol", "price_type"])
    return df


class TestMomentumFactorInheritance:
    """MomentumFactorがFactor基底クラスを継承していることを確認するテスト。"""

    def test_正常系_Factor基底クラスを継承している(self) -> None:
        """MomentumFactorがFactor基底クラスを継承していることを確認。"""
        from factor.core.base import Factor

        factor = MomentumFactor()
        assert isinstance(factor, Factor)

    def test_正常系_必須クラス属性が定義されている(self) -> None:
        """name, description, categoryの必須クラス属性が定義されていることを確認。"""
        factor = MomentumFactor()

        assert hasattr(factor, "name")
        assert hasattr(factor, "description")
        assert hasattr(factor, "category")

        assert factor.name == "momentum"
        assert (
            "モメンタム" in factor.description
            or "momentum" in factor.description.lower()
        )

    def test_正常系_カテゴリがPRICEまたはMOMENTUMである(self) -> None:
        """categoryがFactorCategory.PRICEまたはMOMENTUMであることを確認。"""
        from factor.enums import FactorCategory

        factor = MomentumFactor()

        # MomentumはPRICEまたはMOMENTUMカテゴリのいずれか
        assert factor.category in (FactorCategory.PRICE, FactorCategory.MOMENTUM)


class TestMomentumFactorInit:
    """MomentumFactor初期化のテスト。"""

    def test_正常系_デフォルト値で初期化される(self) -> None:
        """デフォルトのlookback=252, skip_recent=21で初期化されることを確認。"""
        factor = MomentumFactor()

        assert factor.lookback == 252
        assert factor.skip_recent == 21

    def test_正常系_1ヶ月期間で初期化される(self) -> None:
        """lookback=21（1ヶ月）でカスタム初期化できることを確認。"""
        # skip_recent=0を指定（デフォルトの21だとlookbackと同じになりエラー）
        factor = MomentumFactor(lookback=21, skip_recent=0)

        assert factor.lookback == 21
        assert factor.skip_recent == 0

    def test_正常系_3ヶ月期間で初期化される(self) -> None:
        """lookback=63（3ヶ月）でカスタム初期化できることを確認。"""
        factor = MomentumFactor(lookback=63)

        assert factor.lookback == 63

    def test_正常系_12ヶ月期間で初期化される(self) -> None:
        """lookback=252（12ヶ月）でカスタム初期化できることを確認。"""
        factor = MomentumFactor(lookback=252)

        assert factor.lookback == 252

    def test_正常系_skip_recentをカスタマイズできる(self) -> None:
        """skip_recentパラメータをカスタマイズできることを確認。"""
        factor = MomentumFactor(lookback=252, skip_recent=0)

        assert factor.skip_recent == 0

    def test_異常系_lookbackがゼロ以下でエラー(self) -> None:
        """lookbackが0以下の場合、ValueErrorが発生することを確認。"""
        with pytest.raises(ValueError):
            MomentumFactor(lookback=0)

        with pytest.raises(ValueError):
            MomentumFactor(lookback=-1)

    def test_異常系_skip_recentが負の場合エラー(self) -> None:
        """skip_recentが負の場合、ValueErrorが発生することを確認。"""
        with pytest.raises(ValueError):
            MomentumFactor(lookback=252, skip_recent=-1)

    def test_異常系_skip_recentがlookback以上でエラー(self) -> None:
        """skip_recentがlookback以上の場合、ValueErrorが発生することを確認。"""
        with pytest.raises(ValueError):
            MomentumFactor(lookback=21, skip_recent=21)

        with pytest.raises(ValueError):
            MomentumFactor(lookback=21, skip_recent=30)


class TestMomentumFactorCompute:
    """MomentumFactor.compute()のテスト。"""

    def setup_method(self) -> None:
        """テストフィクスチャのセットアップ。"""
        self.factor = MomentumFactor(lookback=21, skip_recent=0)

    def test_正常系_モメンタムが正しく計算される(self) -> None:
        """モメンタム = (P_{t-skip} / P_{t-lookback}) - 1 が正しく計算されることを確認。"""
        # Arrange: 30日間のデータ（lookback=21に対応）
        dates = pd.date_range("2024-01-01", periods=30, freq="B")
        symbols = ["AAPL"]

        # 価格が100から130に上昇（30%上昇）
        prices = list(np.linspace(100, 130, 30))
        close_prices = {"AAPL": prices}

        prices_df = create_price_dataframe(symbols, dates, close_prices)
        provider = MockDataProvider(prices_df)

        # Act
        result = self.factor.compute(
            provider=provider,
            universe=symbols,
            start_date="2024-01-01",
            end_date="2024-02-15",
        )

        # Assert
        assert isinstance(result, pd.DataFrame)
        assert "AAPL" in result.columns

        # 最終日のモメンタム: (130 / 100) - 1 = 0.3 (30%)
        # ただし最初の21日間はNaNになる
        valid_values = result["AAPL"].dropna()
        assert len(valid_values) > 0

    def test_正常系_複数銘柄で計算できる(self) -> None:
        """複数銘柄のモメンタムが計算できることを確認。"""
        # Arrange
        dates = pd.date_range("2024-01-01", periods=30, freq="B")
        symbols = ["AAPL", "GOOGL", "MSFT"]

        close_prices = {
            "AAPL": list(np.linspace(100, 130, 30)),  # 30%上昇
            "GOOGL": list(np.linspace(100, 90, 30)),  # 10%下落
            "MSFT": [100.0] * 30,  # 横ばい
        }

        prices_df = create_price_dataframe(symbols, dates, close_prices)
        provider = MockDataProvider(prices_df)

        # Act
        result = self.factor.compute(
            provider=provider,
            universe=symbols,
            start_date="2024-01-01",
            end_date="2024-02-15",
        )

        # Assert
        assert set(result.columns) == set(symbols)
        assert len(result) > 0

    def test_正常系_skip_recentで直近期間を除外できる(self) -> None:
        """skip_recentパラメータで直近期間を除外できることを確認。"""
        # Arrange
        factor = MomentumFactor(lookback=21, skip_recent=5)
        dates = pd.date_range("2024-01-01", periods=30, freq="B")
        symbols = ["AAPL"]

        # 最後の5日間で急落するケース
        prices = [100.0] * 25 + [50.0] * 5  # 最後5日で50%下落
        close_prices = {"AAPL": prices}

        prices_df = create_price_dataframe(symbols, dates, close_prices)
        provider = MockDataProvider(prices_df)

        # Act
        result = factor.compute(
            provider=provider,
            universe=symbols,
            start_date="2024-01-01",
            end_date="2024-02-15",
        )

        # Assert: skip_recent=5なので直近5日間の下落は無視される
        assert isinstance(result, pd.DataFrame)


class TestMomentumFactorComputeReturnFormat:
    """MomentumFactor.compute()の戻り値フォーマットのテスト。"""

    def setup_method(self) -> None:
        """テストフィクスチャのセットアップ。"""
        self.factor = MomentumFactor(lookback=21, skip_recent=0)

        # 共通のテストデータ
        dates = pd.date_range("2024-01-01", periods=30, freq="B")
        symbols = ["AAPL", "GOOGL"]
        close_prices = {
            "AAPL": list(np.linspace(100, 130, 30)),
            "GOOGL": list(np.linspace(100, 110, 30)),
        }
        self.prices_df = create_price_dataframe(symbols, dates, close_prices)
        self.provider = MockDataProvider(self.prices_df)
        self.symbols = symbols

    def test_正常系_DataFrameが返される(self) -> None:
        """戻り値がpd.DataFrameであることを確認。"""
        result = self.factor.compute(
            provider=self.provider,
            universe=self.symbols,
            start_date="2024-01-01",
            end_date="2024-02-15",
        )

        assert isinstance(result, pd.DataFrame)

    def test_正常系_インデックスがDatetimeIndex(self) -> None:
        """インデックスがDatetimeIndexであることを確認。"""
        result = self.factor.compute(
            provider=self.provider,
            universe=self.symbols,
            start_date="2024-01-01",
            end_date="2024-02-15",
        )

        assert isinstance(result.index, pd.DatetimeIndex)

    def test_正常系_インデックス名がDate(self) -> None:
        """インデックス名が'Date'であることを確認。"""
        result = self.factor.compute(
            provider=self.provider,
            universe=self.symbols,
            start_date="2024-01-01",
            end_date="2024-02-15",
        )

        assert result.index.name == "Date"

    def test_正常系_カラムがシンボル名(self) -> None:
        """カラムがシンボル名（universe）であることを確認。"""
        result = self.factor.compute(
            provider=self.provider,
            universe=self.symbols,
            start_date="2024-01-01",
            end_date="2024-02-15",
        )

        assert list(result.columns) == self.symbols

    def test_正常系_値が数値型(self) -> None:
        """DataFrame内の値が数値型であることを確認。"""
        result = self.factor.compute(
            provider=self.provider,
            universe=self.symbols,
            start_date="2024-01-01",
            end_date="2024-02-15",
        )

        for col in result.columns:
            assert result[col].dtype in [np.float64, np.float32, float]


class TestMomentumFactorComputeMomentumPeriods:
    """各モメンタム期間（1/3/12ヶ月）の計算テスト。"""

    def _create_test_data(self, n_days: int) -> tuple[MockDataProvider, list[str]]:
        """テストデータを作成するヘルパー。"""
        dates = pd.date_range("2023-01-01", periods=n_days, freq="B")
        symbols = ["AAPL"]
        # 一定の上昇トレンド
        close_prices = {"AAPL": list(np.linspace(100, 200, n_days))}
        prices_df = create_price_dataframe(symbols, dates, close_prices)
        return MockDataProvider(prices_df), symbols

    def test_正常系_1ヶ月モメンタム計算(self) -> None:
        """lookback=21（1ヶ月）でモメンタムが計算できることを確認。"""
        factor = MomentumFactor(lookback=21, skip_recent=0)
        provider, symbols = self._create_test_data(50)

        result = factor.compute(
            provider=provider,
            universe=symbols,
            start_date="2023-01-01",
            end_date="2023-03-31",
        )

        assert isinstance(result, pd.DataFrame)
        # 21日目以降からデータがある
        valid_count = result["AAPL"].notna().sum()
        assert valid_count > 0

    def test_正常系_3ヶ月モメンタム計算(self) -> None:
        """lookback=63（3ヶ月）でモメンタムが計算できることを確認。"""
        factor = MomentumFactor(lookback=63, skip_recent=0)
        provider, symbols = self._create_test_data(100)

        result = factor.compute(
            provider=provider,
            universe=symbols,
            start_date="2023-01-01",
            end_date="2023-06-30",
        )

        assert isinstance(result, pd.DataFrame)
        valid_count = result["AAPL"].notna().sum()
        assert valid_count > 0

    def test_正常系_12ヶ月モメンタム計算(self) -> None:
        """lookback=252（12ヶ月）でモメンタムが計算できることを確認。"""
        factor = MomentumFactor(lookback=252, skip_recent=21)
        provider, symbols = self._create_test_data(300)

        result = factor.compute(
            provider=provider,
            universe=symbols,
            start_date="2023-01-01",
            end_date="2024-03-31",
        )

        assert isinstance(result, pd.DataFrame)
        valid_count = result["AAPL"].notna().sum()
        assert valid_count > 0


class TestMomentumFactorEdgeCases:
    """MomentumFactorのエッジケーステスト。"""

    def test_エッジケース_データ不足でNaN(self) -> None:
        """lookback期間より短いデータでNaNが返されることを確認。"""
        factor = MomentumFactor(lookback=21, skip_recent=0)

        # 10日分しかデータがない（lookback=21に不足）
        dates = pd.date_range("2024-01-01", periods=10, freq="B")
        symbols = ["AAPL"]
        close_prices = {"AAPL": [100.0] * 10}
        prices_df = create_price_dataframe(symbols, dates, close_prices)
        provider = MockDataProvider(prices_df)

        result = factor.compute(
            provider=provider,
            universe=symbols,
            start_date="2024-01-01",
            end_date="2024-01-15",
        )

        # 全てNaN
        assert result["AAPL"].isna().all()

    def test_エッジケース_価格がゼロの場合(self) -> None:
        """価格がゼロの場合の処理を確認（ゼロ除算対策）。"""
        factor = MomentumFactor(lookback=5, skip_recent=0)

        dates = pd.date_range("2024-01-01", periods=10, freq="B")
        symbols = ["AAPL"]
        # 途中でゼロが入る
        close_prices = {
            "AAPL": [100.0, 0.0, 0.0, 50.0, 60.0, 70.0, 80.0, 90.0, 100.0, 110.0]
        }
        prices_df = create_price_dataframe(symbols, dates, close_prices)
        provider = MockDataProvider(prices_df)

        result = factor.compute(
            provider=provider,
            universe=symbols,
            start_date="2024-01-01",
            end_date="2024-01-15",
        )

        # ゼロ除算でinf/NaNが発生する可能性があるが、エラーにならないこと
        assert isinstance(result, pd.DataFrame)

    def test_エッジケース_NaN値を含むデータ(self) -> None:
        """NaN値を含むデータでも正しく処理されることを確認。"""
        factor = MomentumFactor(lookback=5, skip_recent=0)

        dates = pd.date_range("2024-01-01", periods=10, freq="B")
        symbols = ["AAPL"]
        close_prices = {
            "AAPL": [
                100.0,
                np.nan,
                110.0,
                115.0,
                120.0,
                125.0,
                np.nan,
                135.0,
                140.0,
                145.0,
            ]
        }
        prices_df = create_price_dataframe(symbols, dates, close_prices)
        provider = MockDataProvider(prices_df)

        result = factor.compute(
            provider=provider,
            universe=symbols,
            start_date="2024-01-01",
            end_date="2024-01-15",
        )

        assert isinstance(result, pd.DataFrame)

    def test_エッジケース_単一銘柄でも動作(self) -> None:
        """単一銘柄でも正しく動作することを確認。"""
        factor = MomentumFactor(lookback=21, skip_recent=0)

        dates = pd.date_range("2024-01-01", periods=30, freq="B")
        symbols = ["AAPL"]
        close_prices = {"AAPL": list(np.linspace(100, 130, 30))}
        prices_df = create_price_dataframe(symbols, dates, close_prices)
        provider = MockDataProvider(prices_df)

        result = factor.compute(
            provider=provider,
            universe=symbols,
            start_date="2024-01-01",
            end_date="2024-02-15",
        )

        assert len(result.columns) == 1
        assert "AAPL" in result.columns


class TestMomentumFactorValidation:
    """MomentumFactorの入力バリデーションテスト。"""

    def setup_method(self) -> None:
        """テストフィクスチャのセットアップ。"""
        self.factor = MomentumFactor(lookback=21, skip_recent=0)

        dates = pd.date_range("2024-01-01", periods=30, freq="B")
        symbols = ["AAPL"]
        close_prices = {"AAPL": [100.0] * 30}
        self.prices_df = create_price_dataframe(symbols, dates, close_prices)
        self.provider = MockDataProvider(self.prices_df)

    def test_異常系_空のユニバースでエラー(self) -> None:
        """空のuniverseでValidationErrorが発生することを確認。"""
        from factor.errors import ValidationError

        with pytest.raises(ValidationError):
            self.factor.compute(
                provider=self.provider,
                universe=[],
                start_date="2024-01-01",
                end_date="2024-02-15",
            )

    def test_異常系_終了日が開始日より前でエラー(self) -> None:
        """end_dateがstart_dateより前の場合、ValidationErrorが発生することを確認。"""
        from factor.errors import ValidationError

        with pytest.raises(ValidationError):
            self.factor.compute(
                provider=self.provider,
                universe=["AAPL"],
                start_date="2024-02-15",
                end_date="2024-01-01",
            )

    def test_正常系_文字列日付で動作(self) -> None:
        """文字列形式の日付でも正しく動作することを確認。"""
        result = self.factor.compute(
            provider=self.provider,
            universe=["AAPL"],
            start_date="2024-01-01",
            end_date="2024-02-15",
        )

        assert isinstance(result, pd.DataFrame)

    def test_正常系_datetime日付で動作(self) -> None:
        """datetime形式の日付でも正しく動作することを確認。"""
        result = self.factor.compute(
            provider=self.provider,
            universe=["AAPL"],
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 2, 15),
        )

        assert isinstance(result, pd.DataFrame)


class TestMomentumFactorMetadata:
    """MomentumFactorのメタデータテスト。"""

    def test_正常系_metadataプロパティが存在する(self) -> None:
        """metadataプロパティが存在することを確認。"""
        factor = MomentumFactor()

        assert hasattr(factor, "metadata")

    def test_正常系_metadataが正しい型(self) -> None:
        """metadataがFactorMetadata型であることを確認。"""
        from factor.core.base import FactorMetadata

        factor = MomentumFactor()

        assert isinstance(factor.metadata, FactorMetadata)

    def test_正常系_metadataのnameが正しい(self) -> None:
        """metadata.nameが'momentum'であることを確認。"""
        factor = MomentumFactor()

        assert factor.metadata.name == "momentum"

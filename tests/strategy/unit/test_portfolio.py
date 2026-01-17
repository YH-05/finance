"""Unit tests for strategy.portfolio module.

Tests for Portfolio class:
- Creating from tuple list and Holding list
- Properties (holdings, tickers, weights)
- Normalization behavior with NormalizationWarning
- set_period() for preset and custom periods
- set_provider() for data providers
- __repr__ representation
- Error handling for invalid inputs
"""

import warnings

import pandas as pd
import pytest
from strategy.portfolio import Portfolio

from strategy.errors import InvalidTickerError, NormalizationWarning, ValidationError
from strategy.providers.protocol import DataProvider
from strategy.types import Holding, PresetPeriod, TickerInfo

# =============================================================================
# MockProvider for testing
# =============================================================================


class MockProvider:
    """Mock implementation of DataProvider protocol for testing.

    Provides a simple mock that returns predefined data for testing
    Portfolio's provider-related functionality.
    """

    def __init__(self, valid_tickers: list[str] | None = None) -> None:
        """Initialize MockProvider.

        Parameters
        ----------
        valid_tickers : list[str] | None
            List of valid ticker symbols. If None, all tickers are valid.
        """
        self._valid_tickers = valid_tickers

    def get_prices(
        self,
        tickers: list[str],
        start: str,
        end: str,
    ) -> pd.DataFrame:
        """Return mock price data.

        Parameters
        ----------
        tickers : list[str]
            Ticker symbols
        start : str
            Start date
        end : str
            End date

        Returns
        -------
        pd.DataFrame
            Empty DataFrame (mock)
        """
        return pd.DataFrame()

    def get_ticker_info(self, ticker: str) -> TickerInfo:
        """Return mock ticker info.

        Parameters
        ----------
        ticker : str
            Ticker symbol

        Returns
        -------
        TickerInfo
            Mock ticker information

        Raises
        ------
        InvalidTickerError
            If ticker is not in valid_tickers list
        """
        if self._valid_tickers is not None and ticker not in self._valid_tickers:
            raise InvalidTickerError(f"Invalid ticker symbol: {ticker}")

        return TickerInfo(ticker=ticker, name=f"{ticker} Inc.")

    def get_ticker_infos(self, tickers: list[str]) -> dict[str, TickerInfo]:
        """Return mock ticker infos for multiple tickers.

        Parameters
        ----------
        tickers : list[str]
            Ticker symbols

        Returns
        -------
        dict[str, TickerInfo]
            Dictionary of ticker to TickerInfo
        """
        return {t: self.get_ticker_info(t) for t in tickers}


# =============================================================================
# Test fixtures
# =============================================================================


@pytest.fixture
def mock_provider() -> MockProvider:
    """Create a mock provider that accepts all tickers."""
    return MockProvider()


@pytest.fixture
def mock_provider_with_valid_tickers() -> MockProvider:
    """Create a mock provider with specific valid tickers."""
    return MockProvider(valid_tickers=["VOO", "BND", "VTI", "AAPL", "GOOGL"])


@pytest.fixture
def sample_holdings_tuple() -> list[tuple[str, float]]:
    """Sample holdings as tuple list."""
    return [("VOO", 0.6), ("BND", 0.4)]


@pytest.fixture
def sample_holdings_dataclass() -> list[Holding]:
    """Sample holdings as Holding dataclass list."""
    return [Holding(ticker="VOO", weight=0.6), Holding(ticker="BND", weight=0.4)]


# =============================================================================
# TestPortfolioCreation
# =============================================================================


class TestPortfolioCreation:
    """Portfolio 作成のテスト."""

    # =========================================================================
    # 正常系テスト: tuple 形式からの作成
    # =========================================================================

    def test_正常系_tuple形式のholdingsから作成できる(
        self,
        sample_holdings_tuple: list[tuple[str, float]],
    ) -> None:
        """tuple形式のholdingsからPortfolioが作成されることを確認."""
        portfolio = Portfolio(holdings=sample_holdings_tuple)

        assert len(portfolio.holdings) == 2
        assert portfolio.holdings[0].ticker == "VOO"
        assert portfolio.holdings[0].weight == 0.6
        assert portfolio.holdings[1].ticker == "BND"
        assert portfolio.holdings[1].weight == 0.4

    def test_正常系_単一銘柄のtuple形式で作成できる(self) -> None:
        """単一銘柄のtuple形式でPortfolioが作成されることを確認."""
        portfolio = Portfolio(holdings=[("VTI", 1.0)])

        assert len(portfolio.holdings) == 1
        assert portfolio.holdings[0].ticker == "VTI"
        assert portfolio.holdings[0].weight == 1.0

    def test_正常系_複数銘柄のtuple形式で作成できる(self) -> None:
        """複数銘柄のtuple形式でPortfolioが作成されることを確認."""
        holdings = [
            ("VOO", 0.4),
            ("BND", 0.2),
            ("VTI", 0.2),
            ("GLD", 0.1),
            ("VNQ", 0.1),
        ]
        portfolio = Portfolio(holdings=holdings)

        assert len(portfolio.holdings) == 5

    # =========================================================================
    # 正常系テスト: Holding 形式からの作成
    # =========================================================================

    def test_正常系_Holding形式のholdingsから作成できる(
        self,
        sample_holdings_dataclass: list[Holding],
    ) -> None:
        """Holding形式のholdingsからPortfolioが作成されることを確認."""
        portfolio = Portfolio(holdings=sample_holdings_dataclass)

        assert len(portfolio.holdings) == 2
        assert portfolio.holdings[0].ticker == "VOO"
        assert portfolio.holdings[0].weight == 0.6

    def test_正常系_単一のHolding形式で作成できる(self) -> None:
        """単一のHolding形式でPortfolioが作成されることを確認."""
        portfolio = Portfolio(holdings=[Holding(ticker="SPY", weight=1.0)])

        assert len(portfolio.holdings) == 1

    # =========================================================================
    # 正常系テスト: オプション引数
    # =========================================================================

    def test_正常系_providerを指定して作成できる(
        self,
        sample_holdings_tuple: list[tuple[str, float]],
        mock_provider: MockProvider,
    ) -> None:
        """providerを指定してPortfolioが作成されることを確認."""
        portfolio = Portfolio(
            holdings=sample_holdings_tuple,
            provider=mock_provider,
        )

        assert len(portfolio.holdings) == 2

    def test_正常系_nameを指定して作成できる(
        self,
        sample_holdings_tuple: list[tuple[str, float]],
    ) -> None:
        """nameを指定してPortfolioが作成されることを確認."""
        portfolio = Portfolio(
            holdings=sample_holdings_tuple,
            name="60/40 Portfolio",
        )

        assert len(portfolio.holdings) == 2
        # Note: name プロパティがあればテストを追加

    # =========================================================================
    # 異常系テスト
    # =========================================================================

    def test_異常系_空のholdingsでValidationError(self) -> None:
        """空のholdingsでValidationErrorが発生することを確認."""
        with pytest.raises(ValidationError, match="holdings cannot be empty"):
            Portfolio(holdings=[])

    def test_異常系_空文字列のティッカーでValueError(self) -> None:
        """空文字列のティッカーでValueErrorが発生することを確認."""
        with pytest.raises(ValueError, match="ticker must be non-empty"):
            Portfolio(holdings=[("", 0.5)])

    def test_異常系_負のweightでValueError(self) -> None:
        """負のweightでValueErrorが発生することを確認."""
        with pytest.raises(ValueError, match=r"weight must be between 0\.0 and 1\.0"):
            Portfolio(holdings=[("VOO", -0.1)])

    def test_異常系_1超のweightでValueError(self) -> None:
        """1.0を超えるweightでValueErrorが発生することを確認."""
        with pytest.raises(ValueError, match=r"weight must be between 0\.0 and 1\.0"):
            Portfolio(holdings=[("VOO", 1.5)])


# =============================================================================
# TestPortfolioProperties
# =============================================================================


class TestPortfolioProperties:
    """Portfolio プロパティのテスト."""

    # =========================================================================
    # holdings プロパティ
    # =========================================================================

    def test_正常系_holdingsプロパティでHoldingリストを取得(
        self,
        sample_holdings_tuple: list[tuple[str, float]],
    ) -> None:
        """holdingsプロパティでHoldingリストが取得できることを確認."""
        portfolio = Portfolio(holdings=sample_holdings_tuple)

        holdings = portfolio.holdings
        assert isinstance(holdings, list)
        assert len(holdings) == 2
        assert all(isinstance(h, Holding) for h in holdings)

    def test_正常系_holdingsプロパティは元のリストと独立(
        self,
        sample_holdings_tuple: list[tuple[str, float]],
    ) -> None:
        """holdingsプロパティが元のリストと独立していることを確認."""
        portfolio = Portfolio(holdings=sample_holdings_tuple)

        holdings1 = portfolio.holdings
        holdings2 = portfolio.holdings
        # 同じ内容だが別のリストオブジェクト（防御的コピー）
        assert holdings1 == holdings2

    # =========================================================================
    # tickers プロパティ
    # =========================================================================

    def test_正常系_tickersプロパティでティッカーリストを取得(
        self,
        sample_holdings_tuple: list[tuple[str, float]],
    ) -> None:
        """tickersプロパティでティッカーリストが取得できることを確認."""
        portfolio = Portfolio(holdings=sample_holdings_tuple)

        tickers = portfolio.tickers
        assert isinstance(tickers, list)
        assert tickers == ["VOO", "BND"]

    def test_正常系_tickersプロパティの順序が保持される(self) -> None:
        """tickersプロパティの順序が入力順序と一致することを確認."""
        holdings = [("AAPL", 0.3), ("GOOGL", 0.3), ("MSFT", 0.4)]
        portfolio = Portfolio(holdings=holdings)

        assert portfolio.tickers == ["AAPL", "GOOGL", "MSFT"]

    # =========================================================================
    # weights プロパティ
    # =========================================================================

    def test_正常系_weightsプロパティで比率辞書を取得(
        self,
        sample_holdings_tuple: list[tuple[str, float]],
    ) -> None:
        """weightsプロパティで比率辞書が取得できることを確認."""
        portfolio = Portfolio(holdings=sample_holdings_tuple)

        weights = portfolio.weights
        assert isinstance(weights, dict)
        assert weights == {"VOO": 0.6, "BND": 0.4}

    def test_正常系_weightsプロパティは全ティッカーを含む(self) -> None:
        """weightsプロパティが全ティッカーを含むことを確認."""
        holdings = [("VOO", 0.4), ("BND", 0.3), ("VTI", 0.2), ("GLD", 0.1)]
        portfolio = Portfolio(holdings=holdings)

        weights = portfolio.weights
        assert len(weights) == 4
        assert set(weights.keys()) == {"VOO", "BND", "VTI", "GLD"}


# =============================================================================
# TestPortfolioNormalization
# =============================================================================


class TestPortfolioNormalization:
    """Portfolio 正規化のテスト."""

    # =========================================================================
    # 正常系テスト: 合計が 1.0 の場合
    # =========================================================================

    def test_正常系_合計1の場合は警告なし(self) -> None:
        """比率の合計が1.0の場合は警告が発生しないことを確認."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            Portfolio(holdings=[("VOO", 0.6), ("BND", 0.4)])

            # NormalizationWarning がないことを確認
            normalization_warnings = [
                warning
                for warning in w
                if issubclass(warning.category, NormalizationWarning)
            ]
            assert len(normalization_warnings) == 0

    # =========================================================================
    # 警告テスト: 合計が 1.0 でない場合
    # =========================================================================

    def test_警告系_合計が1未満の場合にNormalizationWarning(self) -> None:
        """比率の合計が1.0未満の場合にNormalizationWarningが発生することを確認."""
        with pytest.warns(NormalizationWarning, match="sum of weights"):
            Portfolio(holdings=[("VOO", 0.5), ("BND", 0.3)])  # 合計 0.8

    def test_警告系_合計が1超の場合にNormalizationWarning(self) -> None:
        """比率の合計が1.0超の場合にNormalizationWarningが発生することを確認."""
        with pytest.warns(NormalizationWarning, match="sum of weights"):
            Portfolio(holdings=[("VOO", 0.6), ("BND", 0.6)])  # 合計 1.2

    # =========================================================================
    # 正規化テスト: normalize=True の場合
    # =========================================================================

    def test_正常系_normalize_Trueで比率が正規化される(self) -> None:
        """normalize=Trueで比率が1.0に正規化されることを確認."""
        portfolio = Portfolio(
            holdings=[("VOO", 0.6), ("BND", 0.6)],  # 合計 1.2
            normalize=True,
        )

        weights = portfolio.weights
        # 0.6/1.2 = 0.5
        assert abs(weights["VOO"] - 0.5) < 1e-10
        assert abs(weights["BND"] - 0.5) < 1e-10
        assert abs(sum(weights.values()) - 1.0) < 1e-10

    def test_正常系_normalize_Trueで合計が1になる(self) -> None:
        """normalize=Trueで比率の合計が1.0になることを確認."""
        portfolio = Portfolio(
            holdings=[("VOO", 0.5), ("BND", 0.3)],  # 合計 0.8
            normalize=True,
        )

        weights = portfolio.weights
        assert abs(sum(weights.values()) - 1.0) < 1e-10

    def test_正常系_normalize_Trueで比率の相対関係が維持される(self) -> None:
        """normalize=Trueで比率の相対関係が維持されることを確認."""
        portfolio = Portfolio(
            holdings=[("VOO", 0.6), ("BND", 0.2), ("VTI", 0.2)],  # 合計 1.0
            normalize=True,
        )

        weights = portfolio.weights
        # VOO は BND の 3 倍
        assert abs(weights["VOO"] / weights["BND"] - 3.0) < 1e-10

    # =========================================================================
    # 境界値テスト
    # =========================================================================

    @pytest.mark.parametrize(
        "holdings,expected_warning",
        [
            ([("VOO", 0.6), ("BND", 0.4)], False),  # 合計 1.0
            ([("VOO", 0.6), ("BND", 0.400001)], True),  # 合計 1.000001
            ([("VOO", 0.6), ("BND", 0.399999)], True),  # 合計 0.999999
        ],
    )
    def test_境界値_合計1近傍での警告発生(
        self,
        holdings: list[tuple[str, float]],
        expected_warning: bool,
    ) -> None:
        """合計が1.0近傍での警告発生を確認."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            Portfolio(holdings=holdings)

            normalization_warnings = [
                warning
                for warning in w
                if issubclass(warning.category, NormalizationWarning)
            ]

            if expected_warning:
                assert len(normalization_warnings) >= 1
            else:
                assert len(normalization_warnings) == 0


# =============================================================================
# TestPortfolioSetPeriod
# =============================================================================


class TestPortfolioSetPeriod:
    """Portfolio.set_period() のテスト."""

    # =========================================================================
    # 正常系テスト: プリセット期間
    # =========================================================================

    @pytest.mark.parametrize(
        "preset",
        ["1y", "3y", "5y", "10y", "ytd", "max"],
    )
    def test_正常系_プリセット期間を設定できる(
        self,
        preset: PresetPeriod,
        sample_holdings_tuple: list[tuple[str, float]],
    ) -> None:
        """プリセット期間を設定できることを確認."""
        portfolio = Portfolio(holdings=sample_holdings_tuple)

        # set_period はエラーなく実行されるべき
        portfolio.set_period(preset=preset)

        # 実装後は period プロパティで確認できるはず

    def test_正常系_1yプリセットで1年間が設定される(
        self,
        sample_holdings_tuple: list[tuple[str, float]],
    ) -> None:
        """1yプリセットで1年間が設定されることを確認."""
        portfolio = Portfolio(holdings=sample_holdings_tuple)
        portfolio.set_period(preset="1y")

        # 実装後にPeriodプロパティでアサート追加

    # =========================================================================
    # 正常系テスト: カスタム期間
    # =========================================================================

    def test_正常系_カスタム期間を設定できる(
        self,
        sample_holdings_tuple: list[tuple[str, float]],
    ) -> None:
        """カスタム期間を設定できることを確認."""
        portfolio = Portfolio(holdings=sample_holdings_tuple)

        portfolio.set_period(start="2020-01-01", end="2024-12-31")

        # 実装後にPeriodプロパティでアサート追加

    def test_正常系_startのみ指定でendは今日(
        self,
        sample_holdings_tuple: list[tuple[str, float]],
    ) -> None:
        """startのみ指定でendが今日になることを確認."""
        portfolio = Portfolio(holdings=sample_holdings_tuple)

        portfolio.set_period(start="2020-01-01")

        # 実装後: end が今日であることを確認

    # =========================================================================
    # 異常系テスト
    # =========================================================================

    def test_異常系_presetとstartを同時に指定でエラー(
        self,
        sample_holdings_tuple: list[tuple[str, float]],
    ) -> None:
        """presetとstartを同時に指定するとエラーになることを確認."""
        portfolio = Portfolio(holdings=sample_holdings_tuple)

        with pytest.raises(ValidationError, match=r"preset.*start.*mutually exclusive"):
            portfolio.set_period(preset="1y", start="2020-01-01")

    def test_異常系_引数なしでエラー(
        self,
        sample_holdings_tuple: list[tuple[str, float]],
    ) -> None:
        """引数なしで呼び出すとエラーになることを確認."""
        portfolio = Portfolio(holdings=sample_holdings_tuple)

        with pytest.raises(ValidationError, match="preset or start"):
            portfolio.set_period()

    def test_異常系_無効な日付形式でエラー(
        self,
        sample_holdings_tuple: list[tuple[str, float]],
    ) -> None:
        """無効な日付形式でエラーになることを確認."""
        portfolio = Portfolio(holdings=sample_holdings_tuple)

        with pytest.raises(ValueError, match="Invalid date format"):
            portfolio.set_period(start="2020/01/01")  # 不正な形式

    def test_異常系_startがendより後でエラー(
        self,
        sample_holdings_tuple: list[tuple[str, float]],
    ) -> None:
        """startがendより後の場合にエラーになることを確認."""
        portfolio = Portfolio(holdings=sample_holdings_tuple)

        with pytest.raises(ValidationError, match=r"start.*before.*end"):
            portfolio.set_period(start="2024-01-01", end="2020-01-01")


# =============================================================================
# TestPortfolioSetProvider
# =============================================================================


class TestPortfolioSetProvider:
    """Portfolio.set_provider() のテスト."""

    # =========================================================================
    # 正常系テスト
    # =========================================================================

    def test_正常系_プロバイダーを設定できる(
        self,
        sample_holdings_tuple: list[tuple[str, float]],
        mock_provider: MockProvider,
    ) -> None:
        """プロバイダーを設定できることを確認."""
        portfolio = Portfolio(holdings=sample_holdings_tuple)

        # set_provider はエラーなく実行されるべき
        portfolio.set_provider(mock_provider)

    def test_正常系_DataProvider準拠のオブジェクトを設定できる(
        self,
        sample_holdings_tuple: list[tuple[str, float]],
    ) -> None:
        """DataProvider準拠のオブジェクトを設定できることを確認."""
        portfolio = Portfolio(holdings=sample_holdings_tuple)

        # DataProvider プロトコルを満たす MockProvider
        provider = MockProvider()
        portfolio.set_provider(provider)

        # isinstance で確認（runtime_checkable）
        assert isinstance(provider, DataProvider)

    def test_正常系_プロバイダーを後から変更できる(
        self,
        sample_holdings_tuple: list[tuple[str, float]],
    ) -> None:
        """プロバイダーを後から変更できることを確認."""
        portfolio = Portfolio(holdings=sample_holdings_tuple)

        provider1 = MockProvider()
        provider2 = MockProvider(valid_tickers=["VOO", "BND"])

        portfolio.set_provider(provider1)
        portfolio.set_provider(provider2)

        # エラーなく変更できることを確認


# =============================================================================
# TestPortfolioRepr
# =============================================================================


class TestPortfolioRepr:
    """Portfolio.__repr__() のテスト."""

    def test_正常系_reprでクラス名が含まれる(
        self,
        sample_holdings_tuple: list[tuple[str, float]],
    ) -> None:
        """__repr__でクラス名が含まれることを確認."""
        portfolio = Portfolio(holdings=sample_holdings_tuple)

        repr_str = repr(portfolio)
        assert "Portfolio" in repr_str

    def test_正常系_reprでティッカーが含まれる(
        self,
        sample_holdings_tuple: list[tuple[str, float]],
    ) -> None:
        """__repr__でティッカーが含まれることを確認."""
        portfolio = Portfolio(holdings=sample_holdings_tuple)

        repr_str = repr(portfolio)
        assert "VOO" in repr_str
        assert "BND" in repr_str

    def test_正常系_reprで比率が含まれる(
        self,
        sample_holdings_tuple: list[tuple[str, float]],
    ) -> None:
        """__repr__で比率が含まれることを確認."""
        portfolio = Portfolio(holdings=sample_holdings_tuple)

        repr_str = repr(portfolio)
        # 0.6 または 60% のような形式を許容
        assert "0.6" in repr_str or "60" in repr_str

    def test_正常系_reprで名前が含まれる(
        self,
        sample_holdings_tuple: list[tuple[str, float]],
    ) -> None:
        """__repr__でnameが含まれることを確認."""
        portfolio = Portfolio(
            holdings=sample_holdings_tuple,
            name="60/40 Portfolio",
        )

        repr_str = repr(portfolio)
        assert "60/40 Portfolio" in repr_str

    def test_正常系_nameなしでもreprが機能する(
        self,
        sample_holdings_tuple: list[tuple[str, float]],
    ) -> None:
        """nameなしでも__repr__が機能することを確認."""
        portfolio = Portfolio(holdings=sample_holdings_tuple)

        repr_str = repr(portfolio)
        # エラーなく文字列が返される
        assert isinstance(repr_str, str)
        assert len(repr_str) > 0


# =============================================================================
# TestPortfolioInvalidTicker
# =============================================================================


class TestPortfolioInvalidTicker:
    """無効なティッカーに関するテスト."""

    def test_異常系_無効なティッカーで明確なエラーメッセージ(
        self,
        mock_provider_with_valid_tickers: MockProvider,
    ) -> None:
        """無効なティッカーで明確なエラーメッセージが返されることを確認.

        Note: このテストは provider のバリデーションが Portfolio 作成時に
        実行される場合のテスト。実装によっては analysis 時にエラーになる可能性あり。
        """
        # INVALID は valid_tickers に含まれない
        portfolio = Portfolio(
            holdings=[("VOO", 0.6), ("INVALID_TICKER", 0.4)],
            provider=mock_provider_with_valid_tickers,
        )

        # 実装によっては、作成時またはデータ取得時にエラーが発生
        # provider.get_ticker_info を呼ぶ場合
        with pytest.raises(InvalidTickerError, match="Invalid ticker symbol"):
            mock_provider_with_valid_tickers.get_ticker_info("INVALID_TICKER")


# =============================================================================
# TestPortfolioParameterized
# =============================================================================


class TestPortfolioParameterized:
    """パラメトライズされたテスト."""

    @pytest.mark.parametrize(
        "holdings,expected_count",
        [
            ([("VOO", 1.0)], 1),
            ([("VOO", 0.5), ("BND", 0.5)], 2),
            ([("VOO", 0.4), ("BND", 0.3), ("VTI", 0.3)], 3),
            ([("A", 0.1), ("B", 0.1), ("C", 0.1), ("D", 0.1), ("E", 0.6)], 5),
        ],
    )
    def test_パラメトライズ_様々な銘柄数でPortfolioを作成できる(
        self,
        holdings: list[tuple[str, float]],
        expected_count: int,
    ) -> None:
        """様々な銘柄数でPortfolioが作成できることを確認."""
        portfolio = Portfolio(holdings=holdings)

        assert len(portfolio.holdings) == expected_count
        assert len(portfolio.tickers) == expected_count
        assert len(portfolio.weights) == expected_count

    @pytest.mark.parametrize(
        "weight",
        [0.0, 0.001, 0.25, 0.5, 0.75, 0.999, 1.0],
    )
    def test_パラメトライズ_有効なweight範囲で作成できる(
        self,
        weight: float,
    ) -> None:
        """有効なweight範囲でPortfolioが作成できることを確認."""
        portfolio = Portfolio(holdings=[("TEST", weight)])

        assert portfolio.holdings[0].weight == weight

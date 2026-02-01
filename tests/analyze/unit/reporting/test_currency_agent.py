"""CurrencyAnalyzer4Agent のテスト."""

import pandas as pd
import pytest
from analyze.reporting.currency_agent import (
    CurrencyAnalyzer4Agent,
    CurrencyResult,
)
from pandas import DataFrame


class TestCurrencyResult:
    """CurrencyResult のテスト."""

    def test_正常系_to_dictで全フィールドが辞書に変換される(self) -> None:
        result = CurrencyResult(
            group="currencies",
            subgroup="jpy_crosses",
            base_currency="JPY",
            generated_at="2026-01-26T12:00:00",
            periods=["1D", "1W", "1M"],
            symbols={
                "USDJPY=X": {"1D": 0.16, "1W": 0.5, "1M": 1.2},
                "EURJPY=X": {"1D": 0.25, "1W": 0.8, "1M": 1.5},
            },
            summary={
                "strongest_currency": {
                    "symbol": "EURJPY=X",
                    "period": "1M",
                    "return_pct": 1.5,
                },
                "weakest_currency": {
                    "symbol": "USDJPY=X",
                    "period": "1D",
                    "return_pct": 0.16,
                },
            },
            latest_dates={"USDJPY=X": "2026-01-24", "EURJPY=X": "2026-01-24"},
            data_freshness={
                "newest_date": "2026-01-24",
                "oldest_date": "2026-01-24",
                "has_date_gap": False,
            },
        )

        dict_result = result.to_dict()

        assert dict_result["group"] == "currencies"
        assert dict_result["subgroup"] == "jpy_crosses"
        assert dict_result["base_currency"] == "JPY"
        assert dict_result["generated_at"] == "2026-01-26T12:00:00"
        assert dict_result["periods"] == ["1D", "1W", "1M"]
        assert dict_result["symbols"]["USDJPY=X"]["1D"] == 0.16
        assert dict_result["summary"]["strongest_currency"]["symbol"] == "EURJPY=X"
        assert dict_result["latest_dates"]["USDJPY=X"] == "2026-01-24"
        assert dict_result["data_freshness"]["has_date_gap"] is False


class TestCurrencyAnalyzer4Agent:
    """CurrencyAnalyzer4Agent のテスト."""

    @pytest.fixture
    def sample_currency_data(self) -> dict[str, DataFrame]:
        """テスト用の為替データ."""
        dates = pd.date_range("2026-01-20", periods=10, freq="D")
        return {
            "USDJPY=X": DataFrame(
                {
                    "open": [155.0 + i * 0.1 for i in range(10)],
                    "high": [155.5 + i * 0.1 for i in range(10)],
                    "low": [154.5 + i * 0.1 for i in range(10)],
                    "close": [155.0 + i * 0.1 for i in range(10)],
                    "volume": [0] * 10,
                },
                index=dates,
            ),
            "EURJPY=X": DataFrame(
                {
                    "open": [168.0 + i * 0.2 for i in range(10)],
                    "high": [168.5 + i * 0.2 for i in range(10)],
                    "low": [167.5 + i * 0.2 for i in range(10)],
                    "close": [168.0 + i * 0.2 for i in range(10)],
                    "volume": [0] * 10,
                },
                index=dates,
            ),
        }

    @pytest.fixture
    def sample_returns(self) -> dict[str, dict[str, float | None]]:
        """テスト用の騰落率データ."""
        return {
            "USDJPY=X": {"1D": 0.065, "1W": 0.328, "1M": None},
            "EURJPY=X": {"1D": 0.119, "1W": 0.597, "1M": None},
        }

    def test_正常系_convert_to_resultで為替データがCurrencyResultに変換される(
        self,
        sample_currency_data: dict[str, DataFrame],
        sample_returns: dict[str, dict[str, float | None]],
    ) -> None:
        analyzer = CurrencyAnalyzer4Agent()

        result = analyzer._convert_to_result(
            currency_data=sample_currency_data,
            returns=sample_returns,
        )

        assert result.group == "currencies"
        assert result.subgroup == "jpy_crosses"
        assert result.base_currency == "JPY"
        assert "1D" in result.periods
        assert "1W" in result.periods
        assert result.symbols["USDJPY=X"]["1D"] == 0.065
        assert result.symbols["EURJPY=X"]["1W"] == 0.597

    def test_正常系_summaryに最強最弱通貨が含まれる(
        self,
        sample_currency_data: dict[str, DataFrame],
        sample_returns: dict[str, dict[str, float | None]],
    ) -> None:
        analyzer = CurrencyAnalyzer4Agent()

        result = analyzer._convert_to_result(
            currency_data=sample_currency_data,
            returns=sample_returns,
        )

        # EURJPY=Xの方が騰落率が高い（円に対してより強い）
        assert result.summary["strongest_currency"]["symbol"] == "EURJPY=X"
        assert result.summary["strongest_currency"]["period"] == "1W"
        assert result.summary["strongest_currency"]["return_pct"] == 0.597

        # USDJPY=Xの方が騰落率が低い（円に対してより弱い）
        assert result.summary["weakest_currency"]["symbol"] == "USDJPY=X"
        assert result.summary["weakest_currency"]["period"] == "1D"
        assert result.summary["weakest_currency"]["return_pct"] == 0.065

    def test_正常系_period_averagesが正しく計算される(
        self,
        sample_currency_data: dict[str, DataFrame],
        sample_returns: dict[str, dict[str, float | None]],
    ) -> None:
        analyzer = CurrencyAnalyzer4Agent()

        result = analyzer._convert_to_result(
            currency_data=sample_currency_data,
            returns=sample_returns,
        )

        # 1D: (0.065 + 0.119) / 2 = 0.092
        # 1W: (0.328 + 0.597) / 2 = 0.4625
        assert abs(result.summary["period_averages"]["1D"] - 0.09) < 0.01
        assert abs(result.summary["period_averages"]["1W"] - 0.46) < 0.01

    def test_正常系_latest_datesが正しく設定される(
        self,
        sample_currency_data: dict[str, DataFrame],
        sample_returns: dict[str, dict[str, float | None]],
    ) -> None:
        analyzer = CurrencyAnalyzer4Agent()

        result = analyzer._convert_to_result(
            currency_data=sample_currency_data,
            returns=sample_returns,
        )

        assert "USDJPY=X" in result.latest_dates
        assert "EURJPY=X" in result.latest_dates
        # 最新日付は 2026-01-29（10日間のデータの最終日）
        assert result.latest_dates["USDJPY=X"] == "2026-01-29"
        assert result.latest_dates["EURJPY=X"] == "2026-01-29"

    def test_正常系_data_freshnessで日付ズレが検出される(self) -> None:
        analyzer = CurrencyAnalyzer4Agent()

        # 日付が異なるデータ
        dates_usd = pd.date_range("2026-01-20", periods=10, freq="D")
        dates_eur = pd.date_range("2026-01-19", periods=10, freq="D")

        currency_data = {
            "USDJPY=X": DataFrame(
                {
                    "open": [155.0] * 10,
                    "high": [155.5] * 10,
                    "low": [154.5] * 10,
                    "close": [155.0] * 10,
                    "volume": [0] * 10,
                },
                index=dates_usd,
            ),
            "EURJPY=X": DataFrame(
                {
                    "open": [168.0] * 10,
                    "high": [168.5] * 10,
                    "low": [167.5] * 10,
                    "close": [168.0] * 10,
                    "volume": [0] * 10,
                },
                index=dates_eur,
            ),
        }
        returns: dict[str, dict[str, float | None]] = {
            "USDJPY=X": {"1D": 0.065},
            "EURJPY=X": {"1D": 0.119},
        }

        result = analyzer._convert_to_result(
            currency_data=currency_data,
            returns=returns,
        )

        assert result.data_freshness["has_date_gap"] is True
        assert result.data_freshness["newest_date"] == "2026-01-29"
        assert result.data_freshness["oldest_date"] == "2026-01-28"

    def test_エッジケース_空のデータで空のCurrencyResultが返される(self) -> None:
        analyzer = CurrencyAnalyzer4Agent()

        result = analyzer._convert_to_result(
            currency_data={},
            returns={},
        )

        assert result.group == "currencies"
        assert result.periods == []
        assert result.symbols == {}
        assert result.summary == {}
        assert result.latest_dates == {}
        assert result.data_freshness == {}

    def test_正常系_periodsが正しい順序で並ぶ(self) -> None:
        analyzer = CurrencyAnalyzer4Agent()

        dates = pd.date_range("2026-01-20", periods=30, freq="D")
        currency_data = {
            "USDJPY=X": DataFrame(
                {
                    "open": [155.0] * 30,
                    "high": [155.5] * 30,
                    "low": [154.5] * 30,
                    "close": [155.0] * 30,
                    "volume": [0] * 30,
                },
                index=dates,
            ),
        }
        # 順番をバラバラに（None を含めて型を合わせる）
        returns: dict[str, dict[str, float | None]] = {
            "USDJPY=X": {"1M": 1.0, "1D": 0.1, "1W": 0.5},
        }

        result = analyzer._convert_to_result(
            currency_data=currency_data,
            returns=returns,
        )

        # 期待される順序: 1D, 1W, 1M
        assert result.periods == ["1D", "1W", "1M"]

    def test_正常系_Noneの騰落率が適切にフィルタリングされる(
        self,
        sample_currency_data: dict[str, DataFrame],
    ) -> None:
        analyzer = CurrencyAnalyzer4Agent()

        returns_with_none = {
            "USDJPY=X": {"1D": 0.065, "1W": None, "1M": None},
            "EURJPY=X": {"1D": None, "1W": 0.597, "1M": None},
        }

        result = analyzer._convert_to_result(
            currency_data=sample_currency_data,
            returns=returns_with_none,
        )

        # Noneは除外される
        assert result.symbols["USDJPY=X"] == {"1D": 0.065}
        assert result.symbols["EURJPY=X"] == {"1W": 0.597}
        # 期間はNone以外の値がある期間のみ
        assert set(result.periods) == {"1D", "1W"}

    def test_正常系_period_bestとperiod_worstが正しく計算される(
        self,
        sample_currency_data: dict[str, DataFrame],
        sample_returns: dict[str, dict[str, float | None]],
    ) -> None:
        analyzer = CurrencyAnalyzer4Agent()

        result = analyzer._convert_to_result(
            currency_data=sample_currency_data,
            returns=sample_returns,
        )

        # 1Dでの最強/最弱
        assert result.summary["period_best"]["1D"]["symbol"] == "EURJPY=X"
        assert result.summary["period_best"]["1D"]["return_pct"] == 0.119
        assert result.summary["period_worst"]["1D"]["symbol"] == "USDJPY=X"
        assert result.summary["period_worst"]["1D"]["return_pct"] == 0.065

        # 1Wでの最強/最弱
        assert result.summary["period_best"]["1W"]["symbol"] == "EURJPY=X"
        assert result.summary["period_best"]["1W"]["return_pct"] == 0.597
        assert result.summary["period_worst"]["1W"]["symbol"] == "USDJPY=X"
        assert result.summary["period_worst"]["1W"]["return_pct"] == 0.328

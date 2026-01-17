"""Unit tests for ROICFactor class.

ROICFactorはROIC（投下資本利益率）の5分位ランク計算と
過去/将来値のシフト機能を提供する。
"""

import numpy as np
import pandas as pd
import pytest

# AIDEV-NOTE: 実装が存在しないため、インポートは失敗する（Red状態）
# pytest.importorskipを使用して、実装後に自動的にテストが有効になる
ROICFactor = pytest.importorskip("factor.factors.quality.roic").ROICFactor


class TestROICFactorInit:
    """ROICFactor初期化のテスト。"""

    def test_正常系_デフォルト値で初期化される(self) -> None:
        """デフォルトのmin_samplesで初期化されることを確認。"""
        factor = ROICFactor()
        assert factor.min_samples == 5

    def test_正常系_カスタム値で初期化される(self) -> None:
        """カスタムのmin_samplesで初期化されることを確認。"""
        factor = ROICFactor(min_samples=10)
        assert factor.min_samples == 10

    def test_異常系_min_samplesがゼロ以下でエラー(self) -> None:
        """min_samplesが0以下の場合、エラーが発生することを確認。"""
        with pytest.raises(ValueError):
            ROICFactor(min_samples=0)

        with pytest.raises(ValueError):
            ROICFactor(min_samples=-1)


class TestROICFactorCalculateRanks:
    """ROICFactor.calculate_ranks()のテスト。"""

    def setup_method(self) -> None:
        """テストフィクスチャのセットアップ。"""
        self.factor = ROICFactor(min_samples=5)

    def test_正常系_十分なデータで5分位ランクが計算される(self) -> None:
        """十分なデータがある場合、5分位ランクが正しく計算されることを確認。"""
        # Arrange: 10銘柄のデータを作成
        df = pd.DataFrame(
            {
                "date": ["2024-01-01"] * 10,
                "ticker": [f"STOCK{i}" for i in range(10)],
                "ROIC": [0.05, 0.08, 0.10, 0.12, 0.15, 0.18, 0.20, 0.22, 0.25, 0.30],
            }
        )

        # Act
        result = self.factor.calculate_ranks(df, roic_column="ROIC", date_column="date")

        # Assert: ROIC_Rankカラムが追加される
        assert "ROIC_Rank" in result.columns

        # ランク値は rank1～rank5 のいずれか
        unique_ranks = result["ROIC_Rank"].dropna().unique()
        assert set(unique_ranks).issubset({"rank1", "rank2", "rank3", "rank4", "rank5"})

    def test_正常系_最高ROIC銘柄がrank1になる(self) -> None:
        """ROIC値が最も高い銘柄がrank1（最高ランク）になることを確認。"""
        df = pd.DataFrame(
            {
                "date": ["2024-01-01"] * 10,
                "ticker": [f"STOCK{i}" for i in range(10)],
                "ROIC": [0.05, 0.08, 0.10, 0.12, 0.15, 0.18, 0.20, 0.22, 0.25, 0.30],
            }
        )

        result = self.factor.calculate_ranks(df, roic_column="ROIC", date_column="date")

        # ROIC=0.30（最高値）の銘柄がrank1
        max_roic_rank = result.loc[result["ROIC"] == 0.30, "ROIC_Rank"].iloc[0]
        assert max_roic_rank == "rank1"

    def test_正常系_最低ROIC銘柄がrank5になる(self) -> None:
        """ROIC値が最も低い銘柄がrank5（最低ランク）になることを確認。"""
        df = pd.DataFrame(
            {
                "date": ["2024-01-01"] * 10,
                "ticker": [f"STOCK{i}" for i in range(10)],
                "ROIC": [0.05, 0.08, 0.10, 0.12, 0.15, 0.18, 0.20, 0.22, 0.25, 0.30],
            }
        )

        result = self.factor.calculate_ranks(df, roic_column="ROIC", date_column="date")

        # ROIC=0.05（最低値）の銘柄がrank5
        min_roic_rank = result.loc[result["ROIC"] == 0.05, "ROIC_Rank"].iloc[0]
        assert min_roic_rank == "rank5"

    def test_正常系_複数日付でそれぞれ独立にランク付けされる(self) -> None:
        """各日付ごとに独立してランク付けされることを確認。"""
        # Arrange: 2日間、各5銘柄のデータ
        df = pd.DataFrame(
            {
                "date": ["2024-01-01"] * 5 + ["2024-01-02"] * 5,
                "ticker": [f"STOCK{i}" for i in range(5)] * 2,
                # 1日目と2日目で順位が逆転
                "ROIC": [0.10, 0.20, 0.30, 0.40, 0.50, 0.50, 0.40, 0.30, 0.20, 0.10],
            }
        )

        result = self.factor.calculate_ranks(df, roic_column="ROIC", date_column="date")

        # 1日目: STOCK4 (ROIC=0.50) がrank1
        day1 = result[result["date"] == "2024-01-01"]
        assert day1.loc[day1["ticker"] == "STOCK4", "ROIC_Rank"].iloc[0] == "rank1"

        # 2日目: STOCK0 (ROIC=0.50) がrank1
        day2 = result[result["date"] == "2024-01-02"]
        assert day2.loc[day2["ticker"] == "STOCK0", "ROIC_Rank"].iloc[0] == "rank1"

    def test_異常系_データが5件未満でNaN(self) -> None:
        """データが5件未満の場合、NaNが返されることを確認。"""
        df = pd.DataFrame(
            {
                "date": ["2024-01-01"] * 4,
                "ticker": ["STOCK0", "STOCK1", "STOCK2", "STOCK3"],
                "ROIC": [0.10, 0.20, 0.30, 0.40],
            }
        )

        result = self.factor.calculate_ranks(df, roic_column="ROIC", date_column="date")

        # 全てNaN
        assert result["ROIC_Rank"].isna().all()

    def test_異常系_全て同じ値の場合の処理(self) -> None:
        """全ての値が同じ場合、NaNが返されることを確認。"""
        df = pd.DataFrame(
            {
                "date": ["2024-01-01"] * 10,
                "ticker": [f"STOCK{i}" for i in range(10)],
                "ROIC": [0.15] * 10,  # 全て同じ値
            }
        )

        result = self.factor.calculate_ranks(df, roic_column="ROIC", date_column="date")

        # 5分位に分割できないためNaN
        assert result["ROIC_Rank"].isna().all()

    def test_正常系_NaN値を含むデータの処理(self) -> None:
        """NaN値を含むデータでも正しく処理されることを確認。"""
        df = pd.DataFrame(
            {
                "date": ["2024-01-01"] * 12,
                "ticker": [f"STOCK{i}" for i in range(12)],
                "ROIC": [
                    0.05,
                    0.08,
                    np.nan,
                    0.12,
                    0.15,
                    np.nan,
                    0.20,
                    0.22,
                    0.25,
                    0.30,
                    0.32,
                    0.35,
                ],
            }
        )

        result = self.factor.calculate_ranks(df, roic_column="ROIC", date_column="date")

        # NaN以外の値にはランクが付く
        valid_ranks = result[result["ROIC"].notna()]["ROIC_Rank"]
        assert not valid_ranks.isna().all()

        # 元々NaNだった行はNaNのまま
        nan_rows = result[result["ROIC"].isna()]
        assert nan_rows["ROIC_Rank"].isna().all()

    def test_正常系_カスタムROICカラム名を使用できる(self) -> None:
        """ROICカラム名をカスタマイズできることを確認。"""
        df = pd.DataFrame(
            {
                "date": ["2024-01-01"] * 10,
                "ticker": [f"STOCK{i}" for i in range(10)],
                "custom_roic": [
                    0.05,
                    0.08,
                    0.10,
                    0.12,
                    0.15,
                    0.18,
                    0.20,
                    0.22,
                    0.25,
                    0.30,
                ],
            }
        )

        result = self.factor.calculate_ranks(
            df, roic_column="custom_roic", date_column="date"
        )

        assert "custom_roic_Rank" in result.columns


class TestROICFactorAddShiftedValues:
    """ROICFactor.add_shifted_values()のテスト。"""

    def setup_method(self) -> None:
        """テストフィクスチャのセットアップ。"""
        self.factor = ROICFactor(min_samples=5)

    def _create_time_series_data(self) -> pd.DataFrame:
        """時系列データを作成するヘルパーメソッド。"""
        dates = pd.date_range("2020-01-01", periods=20, freq="QE")
        tickers = ["STOCK0", "STOCK1"]

        data = []
        for ticker in tickers:
            for i, date in enumerate(dates):
                data.append(
                    {
                        "date": date,
                        "ticker": ticker,
                        "ROIC": 0.10 + 0.01 * i
                        if ticker == "STOCK0"
                        else 0.20 - 0.01 * i,
                    }
                )

        return pd.DataFrame(data)

    def test_正常系_過去値カラムが追加される(self) -> None:
        """ROIC_1QAgo, ROIC_2QAgoなどの過去値カラムが追加されることを確認。"""
        df = self._create_time_series_data()

        result = self.factor.add_shifted_values(
            df,
            roic_column="ROIC",
            ticker_column="ticker",
            date_column="date",
            past_periods=[1, 2, 4],
            future_periods=[],
        )

        assert "ROIC_1QAgo" in result.columns
        assert "ROIC_2QAgo" in result.columns
        assert "ROIC_4QAgo" in result.columns

    def test_正常系_将来値カラムが追加される(self) -> None:
        """ROIC_1QForward, ROIC_2QForwardなどの将来値カラムが追加されることを確認。"""
        df = self._create_time_series_data()

        result = self.factor.add_shifted_values(
            df,
            roic_column="ROIC",
            ticker_column="ticker",
            date_column="date",
            past_periods=[],
            future_periods=[1, 2, 4],
        )

        assert "ROIC_1QForward" in result.columns
        assert "ROIC_2QForward" in result.columns
        assert "ROIC_4QForward" in result.columns

    def test_正常系_過去値が正しくシフトされる(self) -> None:
        """過去値が正しい期間だけシフトされることを確認。"""
        df = self._create_time_series_data()

        result = self.factor.add_shifted_values(
            df,
            roic_column="ROIC",
            ticker_column="ticker",
            date_column="date",
            past_periods=[1],
            future_periods=[],
        )

        # STOCK0の2四半期目のROIC_1QAgoは1四半期目のROICと同じ
        stock0_data = result[result["ticker"] == "STOCK0"].sort_values("date")
        second_row = stock0_data.iloc[1]
        first_row = stock0_data.iloc[0]

        assert second_row["ROIC_1QAgo"] == first_row["ROIC"]

    def test_正常系_将来値が正しくシフトされる(self) -> None:
        """将来値が正しい期間だけシフトされることを確認。"""
        df = self._create_time_series_data()

        result = self.factor.add_shifted_values(
            df,
            roic_column="ROIC",
            ticker_column="ticker",
            date_column="date",
            past_periods=[],
            future_periods=[1],
        )

        # STOCK0の1四半期目のROIC_1QForwardは2四半期目のROICと同じ
        stock0_data = result[result["ticker"] == "STOCK0"].sort_values("date")
        first_row = stock0_data.iloc[0]
        second_row = stock0_data.iloc[1]

        assert first_row["ROIC_1QForward"] == second_row["ROIC"]

    def test_正常系_銘柄ごとに独立してシフトされる(self) -> None:
        """各銘柄ごとに独立してシフトされることを確認。"""
        df = self._create_time_series_data()

        result = self.factor.add_shifted_values(
            df,
            roic_column="ROIC",
            ticker_column="ticker",
            date_column="date",
            past_periods=[1],
            future_periods=[],
        )

        # 異なる銘柄間でシフトが混ざらない
        stock0_data = result[result["ticker"] == "STOCK0"].sort_values("date")
        stock1_data = result[result["ticker"] == "STOCK1"].sort_values("date")

        # STOCK0の2四半期目のROIC_1QAgoはSTOCK0の1四半期目のROIC
        assert stock0_data.iloc[1]["ROIC_1QAgo"] == stock0_data.iloc[0]["ROIC"]

        # STOCK1の2四半期目のROIC_1QAgoはSTOCK1の1四半期目のROIC（STOCK0ではない）
        assert stock1_data.iloc[1]["ROIC_1QAgo"] == stock1_data.iloc[0]["ROIC"]

    def test_境界条件_シフト期間がデータ範囲を超える場合NaN(self) -> None:
        """シフト期間がデータ範囲を超える場合、NaNになることを確認。"""
        df = self._create_time_series_data()

        result = self.factor.add_shifted_values(
            df,
            roic_column="ROIC",
            ticker_column="ticker",
            date_column="date",
            past_periods=[1, 2],
            future_periods=[1, 2],
        )

        stock0_data = result[result["ticker"] == "STOCK0"].sort_values("date")

        # 最初の行は1期前のデータがない
        assert pd.isna(stock0_data.iloc[0]["ROIC_1QAgo"])

        # 最初の2行は2期前のデータがない
        assert pd.isna(stock0_data.iloc[0]["ROIC_2QAgo"])
        assert pd.isna(stock0_data.iloc[1]["ROIC_2QAgo"])

        # 最後の行は1期先のデータがない
        assert pd.isna(stock0_data.iloc[-1]["ROIC_1QForward"])

        # 最後の2行は2期先のデータがない
        assert pd.isna(stock0_data.iloc[-1]["ROIC_2QForward"])
        assert pd.isna(stock0_data.iloc[-2]["ROIC_2QForward"])

    def test_正常系_月次サフィックスを使用できる(self) -> None:
        """月次データ用のサフィックス(M)を使用できることを確認。"""
        dates = pd.date_range("2020-01-01", periods=24, freq="ME")
        df = pd.DataFrame(
            {
                "date": dates,
                "ticker": ["STOCK0"] * 24,
                "ROIC": [0.10 + 0.001 * i for i in range(24)],
            }
        )

        result = self.factor.add_shifted_values(
            df,
            roic_column="ROIC",
            ticker_column="ticker",
            date_column="date",
            past_periods=[1, 12],
            future_periods=[1, 12],
            freq_suffix="M",  # 月次
        )

        assert "ROIC_1MAgo" in result.columns
        assert "ROIC_12MAgo" in result.columns
        assert "ROIC_1MForward" in result.columns
        assert "ROIC_12MForward" in result.columns

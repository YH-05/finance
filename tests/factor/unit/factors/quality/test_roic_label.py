"""Unit tests for ROICTransitionLabeler class.

ROICTransitionLabelerはROIC5分位ランクの推移に基づいて
遷移ラベル（remain high, remain low, move to high, drop to low, others）を生成する。
"""

import numpy as np
import pandas as pd
import pytest

# AIDEV-NOTE: 実装が存在しないため、インポートは失敗する（Red状態）
# pytest.importorskipを使用して、実装後に自動的にテストが有効になる
ROICTransitionLabeler = pytest.importorskip(
    "factor.factors.quality.roic_label"
).ROICTransitionLabeler


class TestROICTransitionLabelerInit:
    """ROICTransitionLabeler初期化のテスト。"""

    def test_正常系_デフォルト値で初期化される(self) -> None:
        """デフォルト値で初期化されることを確認。"""
        labeler = ROICTransitionLabeler()
        assert labeler is not None

    def test_正常系_カスタムパラメータで初期化される(self) -> None:
        """カスタムパラメータで初期化できることを確認。"""
        labeler = ROICTransitionLabeler(
            high_ranks=["rank1", "rank2"],
            low_ranks=["rank4", "rank5"],
        )
        assert labeler.high_ranks == ["rank1", "rank2"]
        assert labeler.low_ranks == ["rank4", "rank5"]


class TestROICTransitionLabelerLabelTransition:
    """ROICTransitionLabeler.label_transition()のテスト。"""

    def setup_method(self) -> None:
        """テストフィクスチャのセットアップ。"""
        self.labeler = ROICTransitionLabeler()

    def test_正常系_remain_high_全期間rank1(self) -> None:
        """期間中の全ランクがrank1の場合、'remain high'を返すことを確認。"""
        # Arrange: 5期間分のランクデータ（全てrank1）
        ranks = ["rank1", "rank1", "rank1", "rank1", "rank1"]

        # Act
        result = self.labeler.label_transition(ranks)

        # Assert
        assert result == "remain high"

    def test_正常系_remain_high_全期間rank2(self) -> None:
        """期間中の全ランクがrank2の場合、'remain high'を返すことを確認。"""
        ranks = ["rank2", "rank2", "rank2", "rank2", "rank2"]

        result = self.labeler.label_transition(ranks)

        assert result == "remain high"

    def test_正常系_remain_high_rank1とrank2の混合(self) -> None:
        """期間中の全ランクがrank1またはrank2の場合、'remain high'を返すことを確認。"""
        ranks = ["rank1", "rank2", "rank1", "rank2", "rank1"]

        result = self.labeler.label_transition(ranks)

        assert result == "remain high"

    def test_正常系_remain_low_全期間rank5(self) -> None:
        """期間中の全ランクがrank5の場合、'remain low'を返すことを確認。"""
        ranks = ["rank5", "rank5", "rank5", "rank5", "rank5"]

        result = self.labeler.label_transition(ranks)

        assert result == "remain low"

    def test_正常系_remain_low_全期間rank4(self) -> None:
        """期間中の全ランクがrank4の場合、'remain low'を返すことを確認。"""
        ranks = ["rank4", "rank4", "rank4", "rank4", "rank4"]

        result = self.labeler.label_transition(ranks)

        assert result == "remain low"

    def test_正常系_remain_low_rank4とrank5の混合(self) -> None:
        """期間中の全ランクがrank4またはrank5の場合、'remain low'を返すことを確認。"""
        ranks = ["rank4", "rank5", "rank4", "rank5", "rank4"]

        result = self.labeler.label_transition(ranks)

        assert result == "remain low"

    def test_正常系_move_to_high_rank5からrank1へ(self) -> None:
        """低ランク(rank5)から高ランク(rank1)への遷移で'move to high'を返すことを確認。"""
        ranks = ["rank5", "rank4", "rank3", "rank2", "rank1"]

        result = self.labeler.label_transition(ranks)

        assert result == "move to high"

    def test_正常系_move_to_high_rank3からrank2へ(self) -> None:
        """低ランク(rank3)から高ランク(rank2)への遷移で'move to high'を返すことを確認。"""
        ranks = ["rank3", "rank3", "rank3", "rank2", "rank2"]

        result = self.labeler.label_transition(ranks)

        assert result == "move to high"

    def test_正常系_drop_to_low_rank1からrank5へ(self) -> None:
        """高ランク(rank1)から低ランク(rank5)への遷移で'drop to low'を返すことを確認。"""
        ranks = ["rank1", "rank2", "rank3", "rank4", "rank5"]

        result = self.labeler.label_transition(ranks)

        assert result == "drop to low"

    def test_正常系_drop_to_low_rank3からrank4へ(self) -> None:
        """高ランク(rank3)から低ランク(rank4)への遷移で'drop to low'を返すことを確認。"""
        ranks = ["rank3", "rank3", "rank3", "rank4", "rank4"]

        result = self.labeler.label_transition(ranks)

        assert result == "drop to low"

    def test_正常系_others_中間ランクで推移(self) -> None:
        """中間ランクのみで推移する場合、'others'を返すことを確認。"""
        ranks = ["rank3", "rank3", "rank3", "rank3", "rank3"]

        result = self.labeler.label_transition(ranks)

        assert result == "others"

    def test_正常系_others_高から低へ戻る(self) -> None:
        """高ランクから低ランクに下がり、また高ランクに戻る場合、'others'を返すことを確認。"""
        # remain highでもdrop to lowでもないパターン
        ranks = ["rank1", "rank3", "rank5", "rank3", "rank1"]

        result = self.labeler.label_transition(ranks)

        assert result == "others"

    def test_正常系_others_低から高へ戻る(self) -> None:
        """低ランクから高ランクに上がり、また低ランクに戻る場合、'others'を返すことを確認。"""
        ranks = ["rank5", "rank3", "rank1", "rank3", "rank5"]

        result = self.labeler.label_transition(ranks)

        assert result == "others"

    def test_異常系_NaNを含む場合NaNを返す(self) -> None:
        """期間中にNaNが1つでも含まれる場合、NaNを返すことを確認。"""
        ranks = ["rank1", "rank1", np.nan, "rank1", "rank1"]

        result = self.labeler.label_transition(ranks)

        assert pd.isna(result)

    def test_異常系_全てNaNの場合NaNを返す(self) -> None:
        """期間中の全てがNaNの場合、NaNを返すことを確認。"""
        ranks = [np.nan, np.nan, np.nan, np.nan, np.nan]

        result = self.labeler.label_transition(ranks)

        assert pd.isna(result)

    def test_異常系_空リストの場合NaNを返す(self) -> None:
        """空のリストが渡された場合、NaNを返すことを確認。"""
        ranks: list[str] = []

        result = self.labeler.label_transition(ranks)

        assert pd.isna(result)


class TestROICTransitionLabelerLabelDataFrame:
    """ROICTransitionLabeler.label_dataframe()のテスト。"""

    def setup_method(self) -> None:
        """テストフィクスチャのセットアップ。"""
        self.labeler = ROICTransitionLabeler()

    def _create_sample_dataframe(self) -> pd.DataFrame:
        """サンプルDataFrameを作成するヘルパーメソッド。"""
        # 5期間分のランクカラムを持つDataFrame
        return pd.DataFrame(
            {
                "ticker": ["STOCK0", "STOCK1", "STOCK2", "STOCK3", "STOCK4"],
                "ROIC_Rank": ["rank1", "rank5", "rank3", "rank1", "rank4"],
                "ROIC_Rank_1QForward": ["rank1", "rank4", "rank3", "rank2", "rank4"],
                "ROIC_Rank_2QForward": ["rank1", "rank3", "rank3", "rank3", "rank5"],
                "ROIC_Rank_3QForward": ["rank2", "rank2", "rank3", "rank4", "rank5"],
                "ROIC_Rank_4QForward": ["rank2", "rank1", "rank3", "rank5", "rank5"],
            }
        )

    def test_正常系_DataFrameにラベルカラムが追加される(self) -> None:
        """DataFrameにROIC_Labelカラムが追加されることを確認。"""
        df = self._create_sample_dataframe()
        rank_columns = [
            "ROIC_Rank",
            "ROIC_Rank_1QForward",
            "ROIC_Rank_2QForward",
            "ROIC_Rank_3QForward",
            "ROIC_Rank_4QForward",
        ]

        result = self.labeler.label_dataframe(df, rank_columns=rank_columns)

        assert "ROIC_Label" in result.columns

    def test_正常系_各行に正しいラベルが付与される(self) -> None:
        """各行に正しいラベルが付与されることを確認。"""
        df = self._create_sample_dataframe()
        rank_columns = [
            "ROIC_Rank",
            "ROIC_Rank_1QForward",
            "ROIC_Rank_2QForward",
            "ROIC_Rank_3QForward",
            "ROIC_Rank_4QForward",
        ]

        result = self.labeler.label_dataframe(df, rank_columns=rank_columns)

        # STOCK0: rank1 → rank1 → rank1 → rank2 → rank2 = remain high
        assert (
            result.loc[result["ticker"] == "STOCK0", "ROIC_Label"].iloc[0]
            == "remain high"
        )

        # STOCK1: rank5 → rank4 → rank3 → rank2 → rank1 = move to high
        assert (
            result.loc[result["ticker"] == "STOCK1", "ROIC_Label"].iloc[0]
            == "move to high"
        )

        # STOCK2: rank3 → rank3 → rank3 → rank3 → rank3 = others
        assert (
            result.loc[result["ticker"] == "STOCK2", "ROIC_Label"].iloc[0] == "others"
        )

        # STOCK3: rank1 → rank2 → rank3 → rank4 → rank5 = drop to low
        assert (
            result.loc[result["ticker"] == "STOCK3", "ROIC_Label"].iloc[0]
            == "drop to low"
        )

        # STOCK4: rank4 → rank4 → rank5 → rank5 → rank5 = remain low
        assert (
            result.loc[result["ticker"] == "STOCK4", "ROIC_Label"].iloc[0]
            == "remain low"
        )

    def test_正常系_カスタムラベルカラム名を使用できる(self) -> None:
        """カスタムラベルカラム名を使用できることを確認。"""
        df = self._create_sample_dataframe()
        rank_columns = [
            "ROIC_Rank",
            "ROIC_Rank_1QForward",
            "ROIC_Rank_2QForward",
            "ROIC_Rank_3QForward",
            "ROIC_Rank_4QForward",
        ]

        result = self.labeler.label_dataframe(
            df, rank_columns=rank_columns, label_column="CustomLabel"
        )

        assert "CustomLabel" in result.columns
        assert "ROIC_Label" not in result.columns

    def test_正常系_欠損カラムがある場合NaNが付与される(self) -> None:
        """ランクカラムに欠損値がある行にはNaNが付与されることを確認。"""
        df = pd.DataFrame(
            {
                "ticker": ["STOCK0", "STOCK1"],
                "ROIC_Rank": ["rank1", np.nan],
                "ROIC_Rank_1QForward": ["rank1", "rank2"],
                "ROIC_Rank_2QForward": ["rank1", "rank3"],
                "ROIC_Rank_3QForward": ["rank2", "rank4"],
                "ROIC_Rank_4QForward": ["rank2", "rank5"],
            }
        )
        rank_columns = [
            "ROIC_Rank",
            "ROIC_Rank_1QForward",
            "ROIC_Rank_2QForward",
            "ROIC_Rank_3QForward",
            "ROIC_Rank_4QForward",
        ]

        result = self.labeler.label_dataframe(df, rank_columns=rank_columns)

        # STOCK0は正常にラベル付け
        assert (
            result.loc[result["ticker"] == "STOCK0", "ROIC_Label"].iloc[0]
            == "remain high"
        )

        # STOCK1はNaNを含むのでNaN
        assert pd.isna(result.loc[result["ticker"] == "STOCK1", "ROIC_Label"].iloc[0])


class TestROICTransitionLabelerEdgeCases:
    """ROICTransitionLabelerのエッジケーステスト。"""

    def setup_method(self) -> None:
        """テストフィクスチャのセットアップ。"""
        self.labeler = ROICTransitionLabeler()

    def test_正常系_2期間のみのデータでもラベル付け可能(self) -> None:
        """2期間のみのデータでも正しくラベル付けされることを確認。"""
        # remain high: rank1 → rank2
        ranks = ["rank1", "rank2"]
        result = self.labeler.label_transition(ranks)
        assert result == "remain high"

        # move to high: rank5 → rank1
        ranks = ["rank5", "rank1"]
        result = self.labeler.label_transition(ranks)
        assert result == "move to high"

    def test_正常系_1期間のみのデータでもラベル付け可能(self) -> None:
        """1期間のみのデータでも正しくラベル付けされることを確認。"""
        # 1期間のみの場合、そのランクに基づいてラベル付け
        # rank1のみ → remain high
        result = self.labeler.label_transition(["rank1"])
        assert result == "remain high"

        # rank5のみ → remain low
        result = self.labeler.label_transition(["rank5"])
        assert result == "remain low"

        # rank3のみ → others
        result = self.labeler.label_transition(["rank3"])
        assert result == "others"

    def test_正常系_境界条件_move_to_high判定の始点(self) -> None:
        """move to high判定で始点がrank3（低ランク境界）の場合を確認。"""
        # rank3は低ランクに含まれる（rank3, rank4, rank5）
        ranks = ["rank3", "rank2"]
        result = self.labeler.label_transition(ranks)
        assert result == "move to high"

    def test_正常系_境界条件_drop_to_low判定の始点(self) -> None:
        """drop to low判定で始点がrank3（高ランク境界）の場合を確認。"""
        # rank3は高ランクに含まれる（rank1, rank2, rank3）
        ranks = ["rank3", "rank4"]
        result = self.labeler.label_transition(ranks)
        assert result == "drop to low"

    def test_正常系_カスタムランク定義を使用できる(self) -> None:
        """カスタムの高/低ランク定義を使用できることを確認。"""
        # カスタム定義: rank1のみが高ランク、rank5のみが低ランク
        labeler = ROICTransitionLabeler(
            high_ranks=["rank1"],
            low_ranks=["rank5"],
        )

        # rank2は高ランクではないのでremain highにならない
        ranks = ["rank2", "rank2", "rank2"]
        result = labeler.label_transition(ranks)
        assert result != "remain high"

        # rank1のみならremain high
        ranks = ["rank1", "rank1", "rank1"]
        result = labeler.label_transition(ranks)
        assert result == "remain high"

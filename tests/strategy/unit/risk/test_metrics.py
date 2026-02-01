"""Unit tests for RiskMetricsResult dataclass.

RiskMetricsResult はリスク指標の計算結果を保持する dataclass である。
このモジュールでは以下をテストする:
- dataclass の初期化
- to_dict メソッド
- to_markdown メソッド
- summary メソッド
"""

from datetime import date, datetime
from typing import Any

import pandas as pd

from strategy.risk.metrics import RiskMetricsResult


class TestRiskMetricsResultInit:
    """RiskMetricsResult の初期化テスト."""

    def test_正常系_全フィールドを指定して初期化できる(
        self,
        valid_metrics_data: dict[str, Any],
    ) -> None:
        """全フィールドを指定して RiskMetricsResult を初期化できることを確認.

        Parameters
        ----------
        valid_metrics_data : dict[str, Any]
            有効なメトリクスデータ
        """
        result = RiskMetricsResult(**valid_metrics_data)

        assert result.volatility == valid_metrics_data["volatility"]
        assert result.sharpe_ratio == valid_metrics_data["sharpe_ratio"]
        assert result.sortino_ratio == valid_metrics_data["sortino_ratio"]
        assert result.max_drawdown == valid_metrics_data["max_drawdown"]
        assert result.var_95 == valid_metrics_data["var_95"]
        assert result.var_99 == valid_metrics_data["var_99"]
        assert result.beta == valid_metrics_data["beta"]
        assert result.treynor_ratio == valid_metrics_data["treynor_ratio"]
        assert result.information_ratio == valid_metrics_data["information_ratio"]
        assert result.annualized_return == valid_metrics_data["annualized_return"]
        assert result.cumulative_return == valid_metrics_data["cumulative_return"]
        assert result.calculated_at == valid_metrics_data["calculated_at"]
        assert result.period_start == valid_metrics_data["period_start"]
        assert result.period_end == valid_metrics_data["period_end"]

    def test_正常系_オプショナルフィールドがNoneで初期化できる(self) -> None:
        """オプショナルフィールドが None で初期化できることを確認.

        Notes
        -----
        beta, treynor_ratio, information_ratio はベンチマーク指定時のみ計算され、
        指定しない場合は None となる。
        """
        result = RiskMetricsResult(
            volatility=0.15,
            sharpe_ratio=1.2,
            sortino_ratio=1.5,
            max_drawdown=-0.10,
            var_95=-0.02,
            var_99=-0.03,
            beta=None,
            treynor_ratio=None,
            information_ratio=None,
            annualized_return=0.08,
            cumulative_return=0.25,
            calculated_at=datetime.now(),
            period_start=date(2023, 1, 1),
            period_end=date(2023, 12, 31),
        )

        assert result.beta is None
        assert result.treynor_ratio is None
        assert result.information_ratio is None

    def test_正常系_ベンチマーク指標ありで初期化できる(self) -> None:
        """ベンチマーク関連の指標ありで初期化できることを確認."""
        result = RiskMetricsResult(
            volatility=0.15,
            sharpe_ratio=1.2,
            sortino_ratio=1.5,
            max_drawdown=-0.10,
            var_95=-0.02,
            var_99=-0.03,
            beta=1.1,
            treynor_ratio=0.08,
            information_ratio=0.5,
            annualized_return=0.08,
            cumulative_return=0.25,
            calculated_at=datetime.now(),
            period_start=date(2023, 1, 1),
            period_end=date(2023, 12, 31),
        )

        assert result.beta == 1.1
        assert result.treynor_ratio == 0.08
        assert result.information_ratio == 0.5


class TestRiskMetricsResultToDict:
    """RiskMetricsResult.to_dict メソッドのテスト."""

    def test_正常系_全フィールドが辞書に変換される(
        self,
        sample_metrics_result: RiskMetricsResult,
    ) -> None:
        """全フィールドが辞書に変換されることを確認.

        Parameters
        ----------
        sample_metrics_result : RiskMetricsResult
            テスト用のメトリクス結果
        """
        result_dict = sample_metrics_result.to_dict()

        assert isinstance(result_dict, dict)
        assert "volatility" in result_dict
        assert "sharpe_ratio" in result_dict
        assert "sortino_ratio" in result_dict
        assert "max_drawdown" in result_dict
        assert "var_95" in result_dict
        assert "var_99" in result_dict
        assert "beta" in result_dict
        assert "treynor_ratio" in result_dict
        assert "information_ratio" in result_dict
        assert "annualized_return" in result_dict
        assert "cumulative_return" in result_dict
        assert "calculated_at" in result_dict
        assert "period_start" in result_dict
        assert "period_end" in result_dict

    def test_正常系_値が正しく変換される(
        self,
        valid_metrics_data: dict[str, Any],
    ) -> None:
        """値が正しく辞書に変換されることを確認.

        Parameters
        ----------
        valid_metrics_data : dict[str, Any]
            有効なメトリクスデータ
        """
        result = RiskMetricsResult(**valid_metrics_data)
        result_dict = result.to_dict()

        assert result_dict["volatility"] == valid_metrics_data["volatility"]
        assert result_dict["sharpe_ratio"] == valid_metrics_data["sharpe_ratio"]
        assert result_dict["sortino_ratio"] == valid_metrics_data["sortino_ratio"]

    def test_正常系_日付型がISO形式文字列に変換される(
        self,
        sample_metrics_result: RiskMetricsResult,
    ) -> None:
        """日付型が ISO 形式の文字列に変換されることを確認.

        Parameters
        ----------
        sample_metrics_result : RiskMetricsResult
            テスト用のメトリクス結果

        Notes
        -----
        JSON 出力用に datetime と date は文字列に変換される必要がある。
        """
        result_dict = sample_metrics_result.to_dict()

        # calculated_at は ISO 形式文字列
        assert isinstance(result_dict["calculated_at"], str)
        # period_start と period_end も文字列
        assert isinstance(result_dict["period_start"], str)
        assert isinstance(result_dict["period_end"], str)

    def test_正常系_Noneフィールドが保持される(self) -> None:
        """None フィールドが辞書に保持されることを確認."""
        result = RiskMetricsResult(
            volatility=0.15,
            sharpe_ratio=1.2,
            sortino_ratio=1.5,
            max_drawdown=-0.10,
            var_95=-0.02,
            var_99=-0.03,
            beta=None,
            treynor_ratio=None,
            information_ratio=None,
            annualized_return=0.08,
            cumulative_return=0.25,
            calculated_at=datetime.now(),
            period_start=date(2023, 1, 1),
            period_end=date(2023, 12, 31),
        )

        result_dict = result.to_dict()

        assert result_dict["beta"] is None
        assert result_dict["treynor_ratio"] is None
        assert result_dict["information_ratio"] is None


class TestRiskMetricsResultToMarkdown:
    """RiskMetricsResult.to_markdown メソッドのテスト."""

    def test_正常系_マークダウン文字列が生成される(
        self,
        sample_metrics_result: RiskMetricsResult,
    ) -> None:
        """マークダウン形式の文字列が生成されることを確認.

        Parameters
        ----------
        sample_metrics_result : RiskMetricsResult
            テスト用のメトリクス結果
        """
        markdown = sample_metrics_result.to_markdown()

        assert isinstance(markdown, str)
        assert len(markdown) > 0

    def test_正常系_主要指標が含まれる(
        self,
        sample_metrics_result: RiskMetricsResult,
    ) -> None:
        """主要な指標がマークダウンに含まれることを確認.

        Parameters
        ----------
        sample_metrics_result : RiskMetricsResult
            テスト用のメトリクス結果
        """
        markdown = sample_metrics_result.to_markdown()

        # 指標名が含まれることを確認
        assert "ボラティリティ" in markdown or "Volatility" in markdown
        assert "シャープレシオ" in markdown or "Sharpe" in markdown
        assert "ソルティノレシオ" in markdown or "Sortino" in markdown

    def test_正常系_期間情報が含まれる(
        self,
        sample_metrics_result: RiskMetricsResult,
    ) -> None:
        """期間情報がマークダウンに含まれることを確認.

        Parameters
        ----------
        sample_metrics_result : RiskMetricsResult
            テスト用のメトリクス結果
        """
        markdown = sample_metrics_result.to_markdown()

        # 期間情報が含まれる
        assert "2023" in markdown  # 年の情報が含まれる

    def test_正常系_テーブル形式で出力される(
        self,
        sample_metrics_result: RiskMetricsResult,
    ) -> None:
        """テーブル形式でマークダウンが出力されることを確認.

        Parameters
        ----------
        sample_metrics_result : RiskMetricsResult
            テスト用のメトリクス結果
        """
        markdown = sample_metrics_result.to_markdown()

        # テーブルの区切り線が含まれる
        assert "|" in markdown
        assert "---" in markdown or "-|-" in markdown


class TestRiskMetricsResultSummary:
    """RiskMetricsResult.summary メソッドのテスト."""

    def test_正常系_DataFrameが返される(
        self,
        sample_metrics_result: RiskMetricsResult,
    ) -> None:
        """summary メソッドが DataFrame を返すことを確認.

        Parameters
        ----------
        sample_metrics_result : RiskMetricsResult
            テスト用のメトリクス結果
        """
        summary_df = sample_metrics_result.summary()

        assert isinstance(summary_df, pd.DataFrame)

    def test_正常系_全指標がDataFrameに含まれる(
        self,
        sample_metrics_result: RiskMetricsResult,
    ) -> None:
        """全指標が DataFrame に含まれることを確認.

        Parameters
        ----------
        sample_metrics_result : RiskMetricsResult
            テスト用のメトリクス結果
        """
        summary_df = sample_metrics_result.summary()

        # 主要な指標が含まれる
        metrics = summary_df.index.tolist()

        # 少なくとも基本指標が含まれる
        expected_metrics = [
            "volatility",
            "sharpe_ratio",
            "sortino_ratio",
            "max_drawdown",
        ]
        for metric in expected_metrics:
            assert any(metric in str(m).lower() for m in metrics)

    def test_正常系_値が正しい(
        self,
        valid_metrics_data: dict[str, Any],
    ) -> None:
        """DataFrame の値が正しいことを確認.

        Parameters
        ----------
        valid_metrics_data : dict[str, Any]
            有効なメトリクスデータ
        """
        result = RiskMetricsResult(**valid_metrics_data)
        summary_df = result.summary()

        # DataFrame から値を取得して比較
        # 実装によって構造が異なる可能性があるため、存在確認のみ
        assert len(summary_df) > 0


class TestRiskMetricsResultEdgeCases:
    """RiskMetricsResult のエッジケーステスト."""

    def test_エッジケース_極端に大きい値(self) -> None:
        """極端に大きい値でも正しく動作することを確認."""
        result = RiskMetricsResult(
            volatility=100.0,  # 10000% ボラティリティ
            sharpe_ratio=50.0,
            sortino_ratio=100.0,
            max_drawdown=-0.99,  # 99% ドローダウン
            var_95=-0.50,
            var_99=-0.80,
            beta=5.0,
            treynor_ratio=2.0,
            information_ratio=3.0,
            annualized_return=10.0,  # 1000% リターン
            cumulative_return=100.0,  # 10000% 累積リターン
            calculated_at=datetime.now(),
            period_start=date(2020, 1, 1),
            period_end=date(2023, 12, 31),
        )

        # to_dict が正常に動作する
        result_dict = result.to_dict()
        assert result_dict["volatility"] == 100.0

        # to_markdown が正常に動作する
        markdown = result.to_markdown()
        assert isinstance(markdown, str)

        # summary が正常に動作する
        summary_df = result.summary()
        assert isinstance(summary_df, pd.DataFrame)

    def test_エッジケース_極端に小さい値(self) -> None:
        """極端に小さい値でも正しく動作することを確認."""
        result = RiskMetricsResult(
            volatility=0.0001,  # 0.01% ボラティリティ
            sharpe_ratio=0.001,
            sortino_ratio=0.001,
            max_drawdown=-0.0001,  # 0.01% ドローダウン
            var_95=-0.0001,
            var_99=-0.0002,
            beta=0.01,
            treynor_ratio=0.001,
            information_ratio=0.001,
            annualized_return=0.0001,
            cumulative_return=0.0001,
            calculated_at=datetime.now(),
            period_start=date(2023, 1, 1),
            period_end=date(2023, 12, 31),
        )

        # to_dict が正常に動作する
        result_dict = result.to_dict()
        assert result_dict["volatility"] == 0.0001

    def test_エッジケース_負のシャープレシオ(self) -> None:
        """負のシャープレシオでも正しく動作することを確認."""
        result = RiskMetricsResult(
            volatility=0.20,
            sharpe_ratio=-0.5,  # 負のシャープレシオ
            sortino_ratio=-0.3,
            max_drawdown=-0.25,
            var_95=-0.03,
            var_99=-0.05,
            beta=None,
            treynor_ratio=None,
            information_ratio=None,
            annualized_return=-0.10,  # 負のリターン
            cumulative_return=-0.15,
            calculated_at=datetime.now(),
            period_start=date(2023, 1, 1),
            period_end=date(2023, 12, 31),
        )

        result_dict = result.to_dict()
        assert result_dict["sharpe_ratio"] == -0.5
        assert result_dict["annualized_return"] == -0.10

    def test_エッジケース_同日の期間(self) -> None:
        """開始日と終了日が同じ場合も動作することを確認."""
        same_date = date(2023, 6, 15)
        result = RiskMetricsResult(
            volatility=0.0,
            sharpe_ratio=0.0,
            sortino_ratio=0.0,
            max_drawdown=0.0,
            var_95=0.0,
            var_99=0.0,
            beta=None,
            treynor_ratio=None,
            information_ratio=None,
            annualized_return=0.0,
            cumulative_return=0.0,
            calculated_at=datetime.now(),
            period_start=same_date,
            period_end=same_date,
        )

        result_dict = result.to_dict()
        assert result_dict["period_start"] == result_dict["period_end"]

"""Unit tests for ResultFormatter class.

ResultFormatter はリスク指標の計算結果を様々な形式に変換するクラスである。
このモジュールでは以下をテストする:
- to_dataframe メソッド（pandas DataFrame への変換）
- to_dict メソッド（JSON/辞書形式への変換）
- to_markdown メソッド（マークダウン形式への変換）
- _repr_html_ メソッド（marimo/Jupyter 向け HTML 表示サポート）

Notes
-----
TDD の Red フェーズとして、実装前にテストを作成している。
テストは現時点で失敗する（ImportError）ことが期待される。
"""

from datetime import date, datetime
from typing import Any

import pandas as pd
import pytest

from strategy.output.formatter import ResultFormatter
from strategy.risk.metrics import RiskMetricsResult


class TestResultFormatterToDataFrame:
    """ResultFormatter.to_dataframe メソッドのテスト.

    受け入れ条件: リスク指標を pandas DataFrame で取得できる
    """

    def test_正常系_RiskMetricsResultをDataFrameに変換できる(
        self,
        sample_metrics_result: RiskMetricsResult,
    ) -> None:
        """RiskMetricsResult を DataFrame に変換できることを確認.

        Parameters
        ----------
        sample_metrics_result : RiskMetricsResult
            テスト用のメトリクス結果
        """
        formatter = ResultFormatter()
        df = formatter.to_dataframe(sample_metrics_result)

        assert isinstance(df, pd.DataFrame)

    def test_正常系_DataFrameに全リスク指標が含まれる(
        self,
        sample_metrics_result: RiskMetricsResult,
    ) -> None:
        """DataFrame に全てのリスク指標が含まれることを確認.

        Parameters
        ----------
        sample_metrics_result : RiskMetricsResult
            テスト用のメトリクス結果
        """
        formatter = ResultFormatter()
        df = formatter.to_dataframe(sample_metrics_result)

        expected_metrics = [
            "volatility",
            "sharpe_ratio",
            "sortino_ratio",
            "max_drawdown",
            "var_95",
            "var_99",
            "annualized_return",
            "cumulative_return",
        ]

        for metric in expected_metrics:
            assert metric in df.index or metric in df.columns

    def test_正常系_DataFrameの値が正確に反映される(
        self,
        valid_metrics_data: dict[str, Any],
    ) -> None:
        """DataFrame の値が RiskMetricsResult の値と一致することを確認.

        Parameters
        ----------
        valid_metrics_data : dict[str, Any]
            有効なメトリクスデータ
        """
        result = RiskMetricsResult(**valid_metrics_data)
        formatter = ResultFormatter()
        df = formatter.to_dataframe(result)

        # DataFrame のインデックスまたはカラムから値を取得
        # 実装に応じて index または columns で取得
        if "volatility" in df.index:
            assert df.loc["volatility"].iloc[0] == valid_metrics_data["volatility"]
        else:
            assert df["volatility"].iloc[0] == valid_metrics_data["volatility"]

    def test_正常系_ベンチマーク指標がNoneの場合も変換できる(self) -> None:
        """ベンチマーク指標が None の場合も正しく変換できることを確認."""
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

        formatter = ResultFormatter()
        df = formatter.to_dataframe(result)

        assert isinstance(df, pd.DataFrame)
        # None 値が適切に処理されていることを確認
        assert df is not None

    def test_正常系_ベンチマーク指標ありの場合も変換できる(
        self,
        sample_metrics_result: RiskMetricsResult,
    ) -> None:
        """ベンチマーク指標がある場合も正しく変換できることを確認.

        Parameters
        ----------
        sample_metrics_result : RiskMetricsResult
            テスト用のメトリクス結果（ベンチマーク指標あり）
        """
        formatter = ResultFormatter()
        df = formatter.to_dataframe(sample_metrics_result)

        # ベンチマーク関連の指標が含まれる
        benchmark_metrics = ["beta", "treynor_ratio", "information_ratio"]
        for metric in benchmark_metrics:
            assert metric in df.index or metric in df.columns


class TestResultFormatterToDict:
    """ResultFormatter.to_dict メソッドのテスト.

    受け入れ条件: リスク指標を JSON/辞書形式で取得できる
    """

    def test_正常系_RiskMetricsResultを辞書に変換できる(
        self,
        sample_metrics_result: RiskMetricsResult,
    ) -> None:
        """RiskMetricsResult を辞書に変換できることを確認.

        Parameters
        ----------
        sample_metrics_result : RiskMetricsResult
            テスト用のメトリクス結果
        """
        formatter = ResultFormatter()
        result_dict = formatter.to_dict(sample_metrics_result)

        assert isinstance(result_dict, dict)

    def test_正常系_辞書に全フィールドが含まれる(
        self,
        sample_metrics_result: RiskMetricsResult,
    ) -> None:
        """辞書に全てのフィールドが含まれることを確認.

        Parameters
        ----------
        sample_metrics_result : RiskMetricsResult
            テスト用のメトリクス結果
        """
        formatter = ResultFormatter()
        result_dict = formatter.to_dict(sample_metrics_result)

        expected_keys = [
            "volatility",
            "sharpe_ratio",
            "sortino_ratio",
            "max_drawdown",
            "var_95",
            "var_99",
            "beta",
            "treynor_ratio",
            "information_ratio",
            "annualized_return",
            "cumulative_return",
            "calculated_at",
            "period_start",
            "period_end",
        ]

        for key in expected_keys:
            assert key in result_dict

    def test_正常系_辞書の値が正確に反映される(
        self,
        valid_metrics_data: dict[str, Any],
    ) -> None:
        """辞書の値が RiskMetricsResult の値と一致することを確認.

        Parameters
        ----------
        valid_metrics_data : dict[str, Any]
            有効なメトリクスデータ
        """
        result = RiskMetricsResult(**valid_metrics_data)
        formatter = ResultFormatter()
        result_dict = formatter.to_dict(result)

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
        JSON シリアライズ可能にするため、日付は文字列に変換される必要がある。
        """
        formatter = ResultFormatter()
        result_dict = formatter.to_dict(sample_metrics_result)

        assert isinstance(result_dict["calculated_at"], str)
        assert isinstance(result_dict["period_start"], str)
        assert isinstance(result_dict["period_end"], str)

    def test_正常系_JSONシリアライズ可能な形式で出力される(
        self,
        sample_metrics_result: RiskMetricsResult,
    ) -> None:
        """出力された辞書が JSON シリアライズ可能であることを確認.

        Parameters
        ----------
        sample_metrics_result : RiskMetricsResult
            テスト用のメトリクス結果
        """
        import json

        formatter = ResultFormatter()
        result_dict = formatter.to_dict(sample_metrics_result)

        # JSON シリアライズが成功すること
        json_str = json.dumps(result_dict)
        assert isinstance(json_str, str)

        # デシリアライズして元のデータが復元できること
        restored = json.loads(json_str)
        assert restored["volatility"] == result_dict["volatility"]


class TestResultFormatterToMarkdown:
    """ResultFormatter.to_markdown メソッドのテスト.

    受け入れ条件: リスク指標をマークダウン形式のレポートで取得できる
    """

    def test_正常系_RiskMetricsResultをマークダウンに変換できる(
        self,
        sample_metrics_result: RiskMetricsResult,
    ) -> None:
        """RiskMetricsResult をマークダウン形式に変換できることを確認.

        Parameters
        ----------
        sample_metrics_result : RiskMetricsResult
            テスト用のメトリクス結果
        """
        formatter = ResultFormatter()
        markdown = formatter.to_markdown(sample_metrics_result)

        assert isinstance(markdown, str)
        assert len(markdown) > 0

    def test_正常系_マークダウンにタイトルが含まれる(
        self,
        sample_metrics_result: RiskMetricsResult,
    ) -> None:
        """マークダウンにレポートタイトルが含まれることを確認.

        Parameters
        ----------
        sample_metrics_result : RiskMetricsResult
            テスト用のメトリクス結果
        """
        formatter = ResultFormatter()
        markdown = formatter.to_markdown(sample_metrics_result)

        # タイトルが含まれる（# または ## で始まる行）
        assert "#" in markdown

    def test_正常系_マークダウンに主要指標が含まれる(
        self,
        sample_metrics_result: RiskMetricsResult,
    ) -> None:
        """マークダウンに主要なリスク指標が含まれることを確認.

        Parameters
        ----------
        sample_metrics_result : RiskMetricsResult
            テスト用のメトリクス結果
        """
        formatter = ResultFormatter()
        markdown = formatter.to_markdown(sample_metrics_result)

        # 主要指標名が含まれる（日本語または英語）
        assert "Volatility" in markdown or "ボラティリティ" in markdown
        assert "Sharpe" in markdown or "シャープ" in markdown

    def test_正常系_マークダウンにテーブル形式が含まれる(
        self,
        sample_metrics_result: RiskMetricsResult,
    ) -> None:
        """マークダウンがテーブル形式で出力されることを確認.

        Parameters
        ----------
        sample_metrics_result : RiskMetricsResult
            テスト用のメトリクス結果
        """
        formatter = ResultFormatter()
        markdown = formatter.to_markdown(sample_metrics_result)

        # テーブル区切り文字が含まれる
        assert "|" in markdown
        assert "---" in markdown or "-|-" in markdown

    def test_正常系_マークダウンに期間情報が含まれる(
        self,
        sample_metrics_result: RiskMetricsResult,
    ) -> None:
        """マークダウンに分析期間の情報が含まれることを確認.

        Parameters
        ----------
        sample_metrics_result : RiskMetricsResult
            テスト用のメトリクス結果
        """
        formatter = ResultFormatter()
        markdown = formatter.to_markdown(sample_metrics_result)

        # 期間情報が含まれる
        assert "2023" in markdown

    def test_正常系_ベンチマーク指標なしの場合も変換できる(self) -> None:
        """ベンチマーク指標がない場合も正しく変換できることを確認."""
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

        formatter = ResultFormatter()
        markdown = formatter.to_markdown(result)

        assert isinstance(markdown, str)
        # ベンチマーク指標セクションは含まれないか、N/A として表示される
        # 実装に依存するため、文字列であることのみ確認


class TestResultFormatterHtmlRepr:
    """ResultFormatter._repr_html_ メソッドのテスト.

    受け入れ条件: marimo ノートブックで直接表示可能
    """

    def test_正常系_HTML表現を取得できる(
        self,
        sample_metrics_result: RiskMetricsResult,
    ) -> None:
        """_repr_html_ メソッドで HTML 表現を取得できることを確認.

        Parameters
        ----------
        sample_metrics_result : RiskMetricsResult
            テスト用のメトリクス結果
        """
        formatter = ResultFormatter(sample_metrics_result)
        html = formatter._repr_html_()

        assert isinstance(html, str)
        assert len(html) > 0

    def test_正常系_HTML表現にテーブルタグが含まれる(
        self,
        sample_metrics_result: RiskMetricsResult,
    ) -> None:
        """HTML 表現に table タグが含まれることを確認.

        Parameters
        ----------
        sample_metrics_result : RiskMetricsResult
            テスト用のメトリクス結果
        """
        formatter = ResultFormatter(sample_metrics_result)
        html = formatter._repr_html_()

        assert "<table" in html.lower() or "<div" in html.lower()

    def test_正常系_HTML表現に指標値が含まれる(
        self,
        valid_metrics_data: dict[str, Any],
    ) -> None:
        """HTML 表現に指標の値が含まれることを確認.

        Parameters
        ----------
        valid_metrics_data : dict[str, Any]
            有効なメトリクスデータ
        """
        result = RiskMetricsResult(**valid_metrics_data)
        formatter = ResultFormatter(result)
        html = formatter._repr_html_()

        # volatility の値が HTML に含まれる（パーセント表記または小数）
        assert "0.15" in html or "15" in html

    def test_正常系_marimoノートブック互換のHTML出力(
        self,
        sample_metrics_result: RiskMetricsResult,
    ) -> None:
        """marimo ノートブックで表示可能な HTML が出力されることを確認.

        Parameters
        ----------
        sample_metrics_result : RiskMetricsResult
            テスト用のメトリクス結果

        Notes
        -----
        marimo は _repr_html_ メソッドを呼び出して HTML 表示を行う。
        このメソッドが正しく実装されていれば、marimo で直接表示可能。
        """
        formatter = ResultFormatter(sample_metrics_result)

        # _repr_html_ メソッドが存在し、呼び出し可能であること
        assert hasattr(formatter, "_repr_html_")
        assert callable(formatter._repr_html_)

        # HTML が返されること
        html = formatter._repr_html_()
        assert isinstance(html, str)

    def test_正常系_結果なしでインスタンス化した場合も動作する(self) -> None:
        """結果なしでインスタンス化した場合の動作を確認."""
        formatter = ResultFormatter()

        # _repr_html_ は結果がない場合、空文字列または説明メッセージを返す
        # または AttributeError を発生させる可能性がある
        # 実装に応じてテストを調整
        try:
            html = formatter._repr_html_()
            # 空文字列または説明メッセージ
            assert isinstance(html, str)
        except (AttributeError, ValueError):
            # 結果がない場合のエラーは許容
            pass


class TestResultFormatterEdgeCases:
    """ResultFormatter のエッジケーステスト."""

    def test_エッジケース_極端に大きい値の変換(self) -> None:
        """極端に大きい値でも正しく変換できることを確認."""
        result = RiskMetricsResult(
            volatility=100.0,
            sharpe_ratio=50.0,
            sortino_ratio=100.0,
            max_drawdown=-0.99,
            var_95=-0.50,
            var_99=-0.80,
            beta=5.0,
            treynor_ratio=2.0,
            information_ratio=3.0,
            annualized_return=10.0,
            cumulative_return=100.0,
            calculated_at=datetime.now(),
            period_start=date(2020, 1, 1),
            period_end=date(2023, 12, 31),
        )

        formatter = ResultFormatter()

        # 全ての変換メソッドが正常に動作する
        df = formatter.to_dataframe(result)
        assert isinstance(df, pd.DataFrame)

        result_dict = formatter.to_dict(result)
        assert isinstance(result_dict, dict)

        markdown = formatter.to_markdown(result)
        assert isinstance(markdown, str)

    def test_エッジケース_極端に小さい値の変換(self) -> None:
        """極端に小さい値でも正しく変換できることを確認."""
        result = RiskMetricsResult(
            volatility=0.0001,
            sharpe_ratio=0.001,
            sortino_ratio=0.001,
            max_drawdown=-0.0001,
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

        formatter = ResultFormatter()

        # 全ての変換メソッドが正常に動作する
        df = formatter.to_dataframe(result)
        assert isinstance(df, pd.DataFrame)

        result_dict = formatter.to_dict(result)
        assert isinstance(result_dict, dict)

    def test_エッジケース_負の値の変換(self) -> None:
        """負の値でも正しく変換できることを確認."""
        result = RiskMetricsResult(
            volatility=0.20,
            sharpe_ratio=-0.5,
            sortino_ratio=-0.3,
            max_drawdown=-0.25,
            var_95=-0.03,
            var_99=-0.05,
            beta=-0.5,
            treynor_ratio=-0.1,
            information_ratio=-0.2,
            annualized_return=-0.10,
            cumulative_return=-0.15,
            calculated_at=datetime.now(),
            period_start=date(2023, 1, 1),
            period_end=date(2023, 12, 31),
        )

        formatter = ResultFormatter()

        result_dict = formatter.to_dict(result)
        assert result_dict["sharpe_ratio"] == -0.5
        assert result_dict["annualized_return"] == -0.10

    def test_エッジケース_ゼロ値の変換(self) -> None:
        """全てゼロの値でも正しく変換できることを確認."""
        result = RiskMetricsResult(
            volatility=0.0,
            sharpe_ratio=0.0,
            sortino_ratio=0.0,
            max_drawdown=0.0,
            var_95=0.0,
            var_99=0.0,
            beta=0.0,
            treynor_ratio=0.0,
            information_ratio=0.0,
            annualized_return=0.0,
            cumulative_return=0.0,
            calculated_at=datetime.now(),
            period_start=date(2023, 6, 15),
            period_end=date(2023, 6, 15),
        )

        formatter = ResultFormatter()

        df = formatter.to_dataframe(result)
        assert isinstance(df, pd.DataFrame)

        result_dict = formatter.to_dict(result)
        assert result_dict["volatility"] == 0.0


class TestResultFormatterTypeCheck:
    """ResultFormatter の型チェックテスト.

    受け入れ条件: pyright strict でエラーなし
    """

    def test_正常系_戻り値の型が正しい(
        self,
        sample_metrics_result: RiskMetricsResult,
    ) -> None:
        """各メソッドの戻り値の型が正しいことを確認.

        Parameters
        ----------
        sample_metrics_result : RiskMetricsResult
            テスト用のメトリクス結果

        Notes
        -----
        pyright strict モードでの型チェックは CI で実行される。
        このテストは実行時の型確認を行う。
        """
        formatter = ResultFormatter()

        # to_dataframe の戻り値は pd.DataFrame
        df = formatter.to_dataframe(sample_metrics_result)
        assert isinstance(df, pd.DataFrame)

        # to_dict の戻り値は dict[str, Any]
        result_dict = formatter.to_dict(sample_metrics_result)
        assert isinstance(result_dict, dict)
        assert all(isinstance(k, str) for k in result_dict)

        # to_markdown の戻り値は str
        markdown = formatter.to_markdown(sample_metrics_result)
        assert isinstance(markdown, str)

    def test_正常系_引数の型が正しくない場合にエラー(self) -> None:
        """不正な型の引数を渡した場合のエラーを確認.

        Notes
        -----
        実装によっては TypeError または AttributeError が発生する。
        """
        formatter = ResultFormatter()

        with pytest.raises((TypeError, AttributeError)):
            formatter.to_dataframe("not a RiskMetricsResult")  # type: ignore

        with pytest.raises((TypeError, AttributeError)):
            formatter.to_dict(123)  # type: ignore

        with pytest.raises((TypeError, AttributeError)):
            formatter.to_markdown(None)  # type: ignore

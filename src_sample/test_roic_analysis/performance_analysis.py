from typing import Dict, Optional

import numpy as np
import pandas as pd


class PerformanceAnalyzer:
    """ROIC戦略のパフォーマンス分析を行います。

    リターン、リスク指標、およびインデックスに対する相対パフォーマンスを計算します。
    """

    def __init__(self, risk_free_rate: float = 0.00):
        """PerformanceAnalyzerのインスタンスを初期化します。

        Parameters
        ----------
        risk_free_rate : float, optional
            パフォーマンス指標の計算に使用するリスクフリーレート, by default 0.00
        """
        self.risk_free_rate = risk_free_rate

    def calculate_metrics(
        self,
        df: pd.DataFrame,
        return_col: str,
        benchmark_col: Optional[str] = None,
        freq: str = "monthly",
    ) -> Dict[str, float]:
        """包括的なパフォーマンス指標を計算します。

        年率リターン、ボラティリティ、シャープレシオ、最大ドローダウンなどを計算します。
        ベンチマークが指定された場合は、アクティブリターンやインフォメーションレシオなどの
        相対的な指標も計算します。

        Parameters
        ----------
        df : pd.DataFrame
            リターンデータを含むDataFrame。
        return_col : str
            戦略またはポートフォリオのリターンが格納されている列名。
        benchmark_col : Optional[str], optional
            ベンチマークのリターンが格納されている列名（任意）, by default None
        freq : str, optional
            データの頻度 ('monthly' または 'daily'), by default 'monthly'

        Returns
        -------
        Dict[str, float]
            計算されたパフォーマンス指標を格納した辞書。
            例: {'Annualized_Return': 0.1, 'Volatility': 0.15, ...}

        Raises
        ------
        ValueError
            `freq`引数が 'monthly' または 'daily' 以外の場合に発生します。
        """
        metrics = {}

        # Determine annualization factor
        if freq == "monthly":
            ann_factor = 12
        elif freq == "daily":
            ann_factor = 252
        else:
            raise ValueError("freq must be 'monthly' or 'daily'")

        returns = df[return_col].dropna()

        if len(returns) < 2:
            return {
                k: np.nan for k in ["Annualized_Return", "Volatility", "Sharpe_Ratio"]
            }

        # 1. Return Metrics
        # Geometric mean for annualized return
        # (1 + r_total)^(1/N) - 1  or  (1 + r_mean)^12 - 1 ?
        # Standard convention: (1 + mean_return)^12 - 1 for arithmetic annualization
        # Or CAGR: (End/Start)^(1/Years) - 1
        # Let's use arithmetic mean annualization for simplicity and consistency with common practice in finance libs
        metrics["Annualized_Return"] = (1 + returns.mean()) ** ann_factor - 1

        # Cumulative Return
        metrics["Cumulative_Return"] = (1 + returns).cumprod().iloc[-1] - 1

        # 2. Risk Metrics
        metrics["Volatility"] = returns.std() * np.sqrt(ann_factor)

        # Max Drawdown
        cumulative_return = (1 + returns).cumprod()
        running_max = cumulative_return.expanding().max()
        drawdown = (cumulative_return - running_max) / running_max
        metrics["Max_Drawdown"] = drawdown.min()

        # 3. Risk-Adjusted Return
        metrics["Sharpe_Ratio"] = (
            metrics["Annualized_Return"] - self.risk_free_rate
        ) / metrics["Volatility"]

        # Sortino Ratio
        downside_returns = returns[returns < 0]
        downside_deviation = downside_returns.std() * np.sqrt(ann_factor)
        if downside_deviation > 0:
            metrics["Sortino_Ratio"] = (
                metrics["Annualized_Return"] - self.risk_free_rate
            ) / downside_deviation
        else:
            metrics["Sortino_Ratio"] = np.nan

        # 4. Relative Metrics (if benchmark provided)
        if benchmark_col and benchmark_col in df.columns:
            benchmark_returns = df[benchmark_col].dropna()
            # Align indices
            aligned_data = pd.concat([returns, benchmark_returns], axis=1, join="inner")
            r_strat = aligned_data[return_col]
            r_bench = aligned_data[benchmark_col]

            active_returns = r_strat - r_bench
            metrics["Active_Return"] = active_returns.mean() * ann_factor  # Annualized

            tracking_error = active_returns.std() * np.sqrt(ann_factor)
            if tracking_error > 0:
                metrics["Information_Ratio"] = metrics["Active_Return"] / tracking_error
            else:
                metrics["Information_Ratio"] = np.nan

            metrics["Win_Rate"] = (r_strat > r_bench).mean()

        return metrics

    def calculate_cumulative_returns(
        self, df: pd.DataFrame, return_col: str
    ) -> pd.Series:
        """累積リターンの時系列を計算します。

        Parameters
        ----------
        df : pd.DataFrame
            リターンデータを含むDataFrame。
        return_col : str
            リターンが格納されている列名。

        Returns
        -------
        pd.Series
            累積リターンの時系列データ。
        """
        return (1 + df[return_col].fillna(0)).cumprod() - 1

    def calculate_drawdown_series(self, df: pd.DataFrame, return_col: str) -> pd.Series:
        """ドローダウン（資産の下落率）の時系列を計算します。

        過去の最高資産からの下落率を時系列で計算します。

        Parameters
        ----------
        df : pd.DataFrame
            リターンデータを含むDataFrame。
        return_col : str
            リターンが格納されている列名。

        Returns
        -------
        pd.Series
            ドローダウンの時系列データ。
        """
        cum_ret = (1 + df[return_col].fillna(0)).cumprod()
        running_max = cum_ret.expanding().max()
        drawdown = (cum_ret - running_max) / running_max
        return drawdown

import sqlite3
from pathlib import Path
from typing import List

import numpy as np
import pandas as pd


class MacroAnalyzer:
    """ROIC戦略のためのマクロ経済分析を行います。

    インフレ、金利、VIXなどの異なるマクロレジーム下でのパフォーマンスを分析します。
    """

    def __init__(self, fred_db_path: str):
        """MacroAnalyzerのインスタンスを初期化します。

        Parameters
        ----------
        fred_db_path : str
            マクロ経済データが格納されているFREDのSQLiteデータベースへのパス。
        """
        self.fred_db_path = Path(fred_db_path)

    def load_macro_data(self, series_ids: List[str]) -> pd.DataFrame:
        """FREDデータベースからマクロ経済指標の時系列データを読み込みます。

        Parameters
        ----------
        series_ids : List[str]
            読み込む対象のFREDシリーズIDのリスト (例: ['CPIAUCSL', 'DGS10'])。

        Returns
        -------
        pd.DataFrame
            日付をインデックスとし、各シリーズIDを列名とするマクロ経済指標のDataFrame。

        Raises
        ------
        FileNotFoundError
            指定された`fred_db_path`にデータベースファイルが存在しない場合に発生します。
        """
        if not self.fred_db_path.exists():
            raise FileNotFoundError(f"FRED database not found at {self.fred_db_path}")

        dfs = []
        with sqlite3.connect(self.fred_db_path) as conn:
            for series_id in series_ids:
                try:
                    query = f"SELECT date, value FROM {series_id}"
                    df = pd.read_sql(query, con=conn, parse_dates=["date"])
                    df = df.set_index("date").rename(columns={"value": series_id})
                    dfs.append(df)
                except Exception as e:
                    print(f"Error loading {series_id}: {e}")

        if not dfs:
            return pd.DataFrame()

        # Merge all series
        macro_df = pd.concat(dfs, axis=1).sort_index()
        return macro_df

    def define_regimes(
        self, df: pd.DataFrame, series_id: str, method: str = "median"
    ) -> pd.DataFrame:
        """指定された時系列データに基づいてマクロレジームを定義します。

        Parameters
        ----------
        df : pd.DataFrame
            レジームを定義するための時系列データを含むDataFrame。
        series_id : str
            レジーム定義の基準とするデータ系列の列名。
        method : str, optional
            レジームの定義方法。以下のいずれかを指定します, by default 'median'
            - 'median': 中央値を基準に 'High'/'Low' の2レジームを定義。
            - 'trend': 12ヶ月移動平均を基準に 'Rising'/'Falling' の2レジームを定義。
            - 'level_change': 水準（中央値）と変化（前年比）を組み合わせて
              'High & Rising', 'High & Falling', 'Low & Rising', 'Low & Falling' の
              4レジームを定義。

        Returns
        -------
        pd.DataFrame
            レジーム情報を示す新しい列が追加されたDataFrame。
        """
        col_name = f"{series_id}_Regime"

        if method == "median":
            median_val = df[series_id].median()
            df[col_name] = np.where(df[series_id] > median_val, "High", "Low")

        elif method == "trend":
            # Simple trend: Current vs Moving Average (e.g., 12M)
            ma = df[series_id].rolling(12).mean()
            df[col_name] = np.where(df[series_id] > ma, "Rising", "Falling")

        elif method == "level_change":
            # Level and Change (e.g., High & Rising, Low & Falling)
            median_val = df[series_id].median()
            change = df[series_id].diff(12)  # YoY change

            conditions = [
                (df[series_id] > median_val) & (change > 0),
                (df[series_id] > median_val) & (change <= 0),
                (df[series_id] <= median_val) & (change > 0),
                (df[series_id] <= median_val) & (change <= 0),
            ]
            choices = [
                "High & Rising",
                "High & Falling",
                "Low & Rising",
                "Low & Falling",
            ]
            df[col_name] = np.select(conditions, choices, default="Unknown")

        return df

    def analyze_conditional_performance(
        self, strategy_returns: pd.DataFrame, macro_df: pd.DataFrame, regime_col: str
    ) -> pd.DataFrame:
        """マクロレジーム条件下での戦略パフォーマンスを分析します。

        戦略リターンとマクロレジームをマージし、各レジーム下での
        年率リターン、ボラティリティ、シャープレシオなどのパフォーマンス指標を計算します。

        Parameters
        ----------
        strategy_returns : pd.DataFrame
            'date'とリターン列('Return')を含む戦略リターンのDataFrame。
        macro_df : pd.DataFrame
            'date'とレジーム列を含むマクロデータのDataFrame。
        regime_col : str
            `macro_df`内のレジーム情報が含まれる列名。

        Returns
        -------
        pd.DataFrame
            レジームごと（行）のパフォーマンス指標（列）を格納したDataFrame。
        """
        # Merge strategy returns with macro regimes
        # Ensure dates align (e.g., month end)

        # Resample macro to month end if needed
        macro_monthly = macro_df.resample("M").last()

        merged = pd.merge(
            strategy_returns,
            macro_monthly[[regime_col]],
            left_on="date",
            right_index=True,
            how="inner",
        )

        # Calculate metrics per regime
        results = []
        for regime in merged[regime_col].unique():
            regime_data = merged[merged[regime_col] == regime]

            # Simple metrics: Mean Return, Volatility
            # Assuming 'Return' column exists
            if "Return" in regime_data.columns:
                mean_ret = regime_data["Return"].mean() * 12
                vol = regime_data["Return"].std() * np.sqrt(12)
                sharpe = mean_ret / vol if vol > 0 else np.nan
                count = len(regime_data)

                results.append(
                    {
                        "Regime": regime,
                        "Annualized Return": mean_ret,
                        "Volatility": vol,
                        "Sharpe Ratio": sharpe,
                        "Count": count,
                    }
                )

        return pd.DataFrame(results).set_index("Regime")

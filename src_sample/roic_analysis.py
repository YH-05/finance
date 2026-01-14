"""
roic_analysis.py
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import src.ROIC_make_data_files_ver2 as roic_utils

from src import factset_utils


# ==========================================================
class PerformanceAnalyzer:
    def __init__(
        self,
        factset_index_db_path: Path,
        financials_db_path: Path,
        UNIVERSE_CODE: str,
        return_names: list[str] | None = None,
        required_cols: list[str] | None = None,
        factor_list: list[str] | None = None,
    ):
        self.factset_index_db_path = factset_index_db_path
        self.financials_db_path = financials_db_path
        self.UNIVERSE_CODE = UNIVERSE_CODE

        if return_names is None:
            self.return_names = [
                "Return_12M_annlzd",
                "Forward_Return_12M_annlzd",
                "Active_Return_12M_annlzd",
                "Forward_Active_Return_12M_annlzd",
                "Return_3Y_annlzd",
                "Forward_Return_3Y_annlzd",
                "Active_Return_3Y_annlzd",
                "Forward_Active_Return_3Y_annlzd",
                "Return_5Y_annlzd",
                "Forward_Return_5Y_annlzd",
                "Active_Return_5Y_annlzd",
                "Forward_Active_Return_5Y_annlzd",
            ]
        else:
            self.return_names = return_names

        if required_cols is None:
            self.required_cols = [
                "year",
                "P_SYMBOL",
                "SEDOL",
                "GICS Sector",
                "GICS Industry Group",
                "Weight (%)",
            ]
        else:
            self.required_cols = required_cols

        if factor_list is None:
            self.factor_list = [
                "ROIC_label_Past3Y",
                "ROIC_label_Past5Y",
                "Factor_Composite_Growth_Score",
                "Factor_Composite_Growth_Score_Rank",
                "Factor_Size_Score",
                "Factor_Size_Score_Rank",
                "Factor_Leverage_Score",
                "Factor_Leverage_Score_Rank",
                # "Return_2YAgo_to_1YAgo",
                # "Return_2YAgo_to_1YAgo_PctRank",
                # "Return_2YAgo_to_1YAgo_PctRank_Sector_Neutral",
                # "Return_3YAgo_to_2YAgo",
                # "Return_3YAgo_to_2YAgo_PctRank",
                # "Return_3YAgo_to_2YAgo_PctRank_Sector_Neutral",
                # "Return_3YAgo_to_1YAgo",
                # "Return_3YAgo_to_1YAgo_PctRank",
                # "Return_3YAgo_to_1YAgo_Inv_PctRank",
                # "Return_3YAgo_to_1YAgo_PctRank_Sector_Neutral",
                # "Return_3YAgo_to_1YAgo_Inv_PctRank_Sector_Neutral",
            ]
        else:
            self.factor_list = factor_list

    # ------------------------------------------------------
    def data_loader(self) -> pd.DataFrame:
        # 構成銘柄
        df_weight = factset_utils.load_index_constituents(
            factset_index_db_path=self.factset_index_db_path,
            UNIVERSE_CODE=self.UNIVERSE_CODE,
        )
        # ファクター
        df_factor = factset_utils.load_financial_data(
            financials_db_path=self.financials_db_path,
            factor_list=self.factor_list + self.return_names,
        ).fillna(np.nan)

        df = factset_utils.merge_idx_constituents_and_financials(
            df_weight=df_weight, df_factor=df_factor
        ).assign(year=lambda x: x["date"].dt.year)

        return df

    # ------------------------------------------------------
    def calculate_mean_returns_for_roic_label(
        self,
        df: pd.DataFrame,
        factor_col: str,
        return_col: str,
    ) -> pd.DataFrame:
        use_cols = self.required_cols + [factor_col] + [return_col]
        df_performance = df.copy()
        df_performance = df_performance[use_cols].dropna(subset=[factor_col], how="any")
        g = (
            df.groupby(["year"] + [factor_col])[return_col]
            .apply(roic_utils.clipped_mean)
            .reset_index()
        ).dropna(subset=return_col, ignore_index=True)

        return g

    # ------------------------------------------------------
    def calculate_mean_returns_for_ranked_factor(
        self,
        df: pd.DataFrame,
        roic_factor: str,
        roic_label: str,
        factor_name: str,
        return_col: str,
    ) -> pd.DataFrame:
        factor_cols = [roic_factor, factor_name]
        use_cols = self.required_cols + factor_cols + [return_col]

        df_performance = df.copy()
        df_performance = df_performance[use_cols].dropna(subset=factor_cols, how="any")
        df_performance = df_performance.loc[df_performance[roic_factor] == roic_label]

        g = (
            df_performance.groupby(["year"] + factor_cols)[return_col]
            .apply(roic_utils.clipped_mean)
            .reset_index()
        ).dropna(subset=return_col, ignore_index=True)

        return g

    # ------------------------------------------------------
    def calculate_mean_returns_double_factors(
        self,
        df: pd.DataFrame,
        factor1: str,
        factor2: str,
        return_col: str,
        factor1_rank: str | None = None,
        factor2_rank: str | None = None,
    ) -> pd.DataFrame:
        factor_cols = [factor1, factor2]
        use_cols = self.required_cols + factor_cols + [return_col]

        df_performance = df.copy()
        df_performance = df_performance[use_cols].dropna(subset=factor_cols, how="any")
        if factor1_rank:
            df_performance = df_performance.loc[df_performance[factor1] == factor1_rank]
        if factor2_rank:
            df_performance = df_performance.loc[df_performance[factor2] == factor2_rank]

        g = (
            df_performance.groupby(["year"] + factor_cols)[return_col]
            .apply(roic_utils.clipped_mean)
            .reset_index()
        ).dropna(subset=return_col, ignore_index=True)

        return g

    # ------------------------------------------------------
    def plot_roic_label_performance(
        self,
        df_to_plot: pd.DataFrame,
        roic_factor_name: str,
        return_col: str,
    ):
        hue_order = [
            "remain high",
            "move to high",
            "drop to low",
            "remain low",
            "others",
        ]
        palette = ["limegreen", "blue", "orange", "red", "gray"]

        fig, ax = plt.subplots(figsize=(12, 3), tight_layout=True)
        fig.suptitle(f"{roic_factor_name} / {return_col}")
        sns.barplot(
            df_to_plot,
            x="year",
            y=return_col,
            hue=roic_factor_name,
            hue_order=hue_order,
            palette=palette,
            ax=ax,
            alpha=0.75,
        )
        # 凡例のラベルをソート
        handles, labels = ax.get_legend_handles_labels()
        sorted_pairs = sorted(zip(labels, handles, strict=False))
        sorted_labels, sorted_handles = zip(*sorted_pairs, strict=False)
        ax.legend(
            sorted_handles, sorted_labels, loc="lower left", title=roic_factor_name
        )
        fig.show()

    # ------------------------------------------------------
    def plot_factor_performance(
        self,
        df_to_plot: pd.DataFrame,
        factor_name: str,
        return_col: str,
        roic_label_name: str | None = None,
    ):
        hue_order = ["rank1", "rank2", "rank3", "rank4", "rank5"]
        palette = sns.color_palette("Blues_r", n_colors=5)

        fig, ax = plt.subplots(figsize=(12, 3), tight_layout=True)
        if roic_label_name:
            figure_title = f"ROIC label: {roic_label_name} / Ranked by: {factor_name} \n {return_col}"
        else:
            figure_title = f"Ranked by: {factor_name} \n {return_col}"
        fig.suptitle(figure_title)
        sns.barplot(
            df_to_plot,
            x="year",
            y=return_col,
            hue=factor_name,
            hue_order=hue_order,
            palette=palette,
            ax=ax,
            errorbar=None,
        )
        # 凡例のラベルをソート
        handles, labels = ax.get_legend_handles_labels()
        sorted_pairs = sorted(zip(labels, handles, strict=False))
        sorted_labels, sorted_handles = zip(*sorted_pairs, strict=False)
        ax.legend(sorted_handles, sorted_labels, loc="lower left", title=factor_name)
        fig.show()

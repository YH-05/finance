import pandas as pd


class FactorAnalyzer:
    """ROIC戦略のためのファクター分析を行います。

    ダブルソート、条件付きソート、ファクター結合分析などを実行します。
    """

    def __init__(self):
        """FactorAnalyzerのインスタンスを初期化します。"""
        pass

    def perform_double_sort(
        self,
        df: pd.DataFrame,
        factor1: str,
        factor2: str,
        return_col: str,
        n_quantiles: int = 5,
        method: str = "independent",
    ) -> pd.DataFrame:
        """2つのファクターに基づいたダブルソート分析を実行します。

        指定された2つのファクターでポートフォリオを分類し、各ポートフォリオの
        平均リターンを計算します。分類方法には 'independent' と 'conditional' があります。

        Parameters
        ----------
        df : pd.DataFrame
            ファクター値とリターンデータを含むDataFrame。'date'列が必要です。
        factor1 : str
            1つ目のファクターの列名。
        factor2 : str
            2つ目のファクターの列名。
        return_col : str
            リターンデータの列名。
        n_quantiles : int, optional
            分類に使用する分位数（例: 5は五分位数）, by default 5
        method : str, optional
            ソート方法。'independent'（独立ソート）または 'conditional'（依存ソート）を
            指定します, by default 'independent'

        Returns
        -------
        pd.DataFrame
            各ポートフォリオの平均リターンを行列形式で格納したDataFrame。
            行インデックスは factor1 のランク、列インデックスは factor2 のランクに対応します。

        Raises
        ------
        ValueError
            `method`引数が 'independent' または 'conditional' 以外の場合に発生します。
        """
        df = df.copy()

        if method == "independent":
            # Independent Sort: Rank both factors independently across the whole universe (or group)
            # Usually done per date
            df["Factor1_Rank"] = df.groupby("date")[factor1].transform(
                lambda x: pd.qcut(x, n_quantiles, labels=False, duplicates="drop")
            )
            df["Factor2_Rank"] = df.groupby("date")[factor2].transform(
                lambda x: pd.qcut(x, n_quantiles, labels=False, duplicates="drop")
            )

        elif method == "conditional":
            # Conditional Sort: First sort by Factor1, then within each Factor1 bucket, sort by Factor2
            df["Factor1_Rank"] = df.groupby("date")[factor1].transform(
                lambda x: pd.qcut(x, n_quantiles, labels=False, duplicates="drop")
            )

            df["Factor2_Rank"] = df.groupby(["date", "Factor1_Rank"])[
                factor2
            ].transform(
                lambda x: pd.qcut(x, n_quantiles, labels=False, duplicates="drop")
            )

        else:
            raise ValueError("method must be 'independent' or 'conditional'")

        # Calculate average return for each portfolio
        # We group by ranks and calculate mean return
        # Note: Ranks are 0-indexed (0 to n-1)

        portfolio_returns = (
            df.groupby(["Factor1_Rank", "Factor2_Rank"])[return_col].mean().unstack()
        )

        # Rename index/columns for clarity
        portfolio_returns.index.name = f"{factor1} Rank"
        portfolio_returns.columns.name = f"{factor2} Rank"

        # Adjust labels to be 1-indexed (Low to High usually, depends on factor direction)
        # pd.qcut assigns 0 to lowest values.
        # If factor is "Higher is Better" (like ROIC), 0 is Low ROIC.
        # If factor is "Lower is Better" (like Valuation), 0 is Low Valuation (Cheap).

        return portfolio_returns

    def calculate_factor_spread(
        self, df: pd.DataFrame, factor_col: str, return_col: str, n_quantiles: int = 5
    ) -> pd.Series:
        """ファクターのロング・ショートスプレッドリターンを計算します。

        指定されたファクターで銘柄を分位数に分類し、最高分位数のポートフォリオをロング、
        最低分位数のポートフォリオをショートした場合のスプレッドリターンを時系列で算出します。

        Parameters
        ----------
        df : pd.DataFrame
            ファクター値とリターンデータを含むDataFrame。'date'列が必要です。
        factor_col : str
            分析対象のファクターの列名。
        return_col : str
            リターンデータの列名。
        n_quantiles : int, optional
            分類に使用する分位数, by default 5

        Returns
        -------
        pd.Series
            日付をインデックスとし、スプレッドリターンを値として持つ時系列シリーズ。
        """
        df["Rank"] = df.groupby("date")[factor_col].transform(
            lambda x: pd.qcut(x, n_quantiles, labels=False, duplicates="drop")
        )

        # Long Top (n-1), Short Bottom (0)
        # Assuming Higher Factor = Long
        long_ret = df[df["Rank"] == n_quantiles - 1].groupby("date")[return_col].mean()
        short_ret = df[df["Rank"] == 0].groupby("date")[return_col].mean()

        spread = long_ret - short_ret
        return spread

    def analyze_factor_persistence(
        self, df: pd.DataFrame, factor_col: str, horizon_months: int = 12
    ) -> float:
        """ファクターの持続性（ランク自己相関）を分析します。

        指定されたファクターのランクが、特定の期間（`horizon_months`）にわたって
        どれだけ維持されるかを、ランクの自己相関係数によって評価します。

        Parameters
        ----------
        df : pd.DataFrame
            ファクター値を含むDataFrame。'date'列と'P_SYMBOL'列が必要です。
        factor_col : str
            分析対象のファクターの列名。
        horizon_months : int, optional
            相関を計算する期間（月単位）, by default 12

        Returns
        -------
        float
            現在のランクと`horizon_months`ヶ月後のランクとの間の自己相関係数。
        """
        # Rank autocorrelation
        df["Rank"] = df.groupby("date")[factor_col].rank(pct=True)

        # Shift rank by horizon
        # Need to handle panel data structure properly
        # Assuming df has 'P_SYMBOL' and 'date'

        df_sorted = df.sort_values(["P_SYMBOL", "date"])
        df_sorted["Future_Rank"] = df_sorted.groupby("P_SYMBOL")["Rank"].shift(
            -horizon_months
        )

        correlation = df_sorted[["Rank", "Future_Rank"]].corr().iloc[0, 1]
        return correlation

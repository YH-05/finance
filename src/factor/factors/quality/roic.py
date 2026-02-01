"""ROIC (Return on Invested Capital) factor calculations.

This module provides ROIC factor calculations including:
- Quintile ranking of ROIC values
- Past/future ROIC value shifting for time-series analysis

Reference: src_sample/ROIC_make_data_files_ver2.py:1113-1151
"""

import numpy as np
import pandas as pd

from utils_core.logging import get_logger

logger = get_logger(__name__)

# Default rank labels (rank1 = highest ROIC, rank5 = lowest ROIC)
_DEFAULT_RANK_LABELS = ["rank5", "rank4", "rank3", "rank2", "rank1"]


class ROICFactor:
    """ROIC factor calculator for cross-sectional analysis.

    Provides methods to calculate quintile ranks of ROIC values
    and create shifted (past/future) ROIC columns for time-series analysis.

    Parameters
    ----------
    min_samples : int, default=5
        Minimum number of valid samples required for rank calculation.
        If fewer samples exist, NaN is returned.

    Attributes
    ----------
    min_samples : int
        Minimum samples required for calculations

    Examples
    --------
    >>> factor = ROICFactor(min_samples=10)
    >>> df = pd.DataFrame({
    ...     "date": ["2024-01-01"] * 10,
    ...     "ticker": [f"STOCK{i}" for i in range(10)],
    ...     "ROIC": [0.05, 0.08, 0.10, 0.12, 0.15, 0.18, 0.20, 0.22, 0.25, 0.30],
    ... })
    >>> result = factor.calculate_ranks(df)
    >>> "ROIC_Rank" in result.columns
    True
    """

    def __init__(self, min_samples: int = 5) -> None:
        """Initialize ROICFactor.

        Parameters
        ----------
        min_samples : int, default=5
            Minimum number of valid samples required for calculations

        Raises
        ------
        ValueError
            If min_samples is not positive
        """
        if min_samples <= 0:
            raise ValueError(f"min_samples must be positive, got {min_samples}")

        self.min_samples = min_samples
        logger.debug("ROICFactor initialized", min_samples=min_samples)

    def calculate_ranks(
        self,
        df: pd.DataFrame,
        roic_column: str = "ROIC",
        date_column: str = "date",
    ) -> pd.DataFrame:
        """Calculate quintile ranks of ROIC values by date.

        Transforms ROIC values to 5 quintile ranks for each date independently.
        Rank1 represents the highest ROIC values, rank5 the lowest.

        Parameters
        ----------
        df : pd.DataFrame
            Input DataFrame containing ROIC and date columns
        roic_column : str, default="ROIC"
            Name of the column containing ROIC values
        date_column : str, default="date"
            Name of the column containing date values

        Returns
        -------
        pd.DataFrame
            DataFrame with additional rank column named "{roic_column}_Rank"

        Notes
        -----
        The rank transformation uses pd.qcut with 5 bins. If fewer than
        min_samples valid values exist for a date, NaN is assigned.
        If all values are identical (no variance), NaN is assigned.

        Reference: src_sample/ROIC_make_data_files_ver2.py:1113-1151

        Examples
        --------
        >>> factor = ROICFactor()
        >>> df = pd.DataFrame({
        ...     "date": ["2024-01-01"] * 10,
        ...     "ticker": [f"STOCK{i}" for i in range(10)],
        ...     "ROIC": [0.05, 0.08, 0.10, 0.12, 0.15, 0.18, 0.20, 0.22, 0.25, 0.30],
        ... })
        >>> result = factor.calculate_ranks(df)
        >>> result.loc[result["ROIC"] == 0.30, "ROIC_Rank"].iloc[0]
        'rank1'
        """
        logger.debug(
            "Calculating ROIC ranks",
            roic_column=roic_column,
            date_column=date_column,
            rows=len(df),
        )

        result = df.copy()
        rank_column = f"{roic_column}_Rank"

        def _calculate_quintile(group: pd.Series) -> pd.Series:
            """Calculate quintile rank for a group."""
            valid_count = group.notna().sum()

            if valid_count < self.min_samples:
                logger.warning(
                    "Insufficient data for quintile rank",
                    valid_count=valid_count,
                    min_samples=self.min_samples,
                )
                return pd.Series(np.nan, index=group.index)

            try:
                # pd.qcut assigns 0-4 (5 bins), we add 1 to get 1-5
                qcut_result = pd.qcut(group, q=5, labels=False, duplicates="drop")
                quintile_numeric = pd.Series(qcut_result, index=group.index) + 1

                # Map numeric values to rank labels
                # Note: qcut assigns lower numbers to lower values
                # So quintile 1 (lowest values) -> rank5
                # And quintile 5 (highest values) -> rank1
                label_map = {
                    1.0: "rank5",
                    2.0: "rank4",
                    3.0: "rank3",
                    4.0: "rank2",
                    5.0: "rank1",
                }
                return quintile_numeric.map(label_map)

            except ValueError as e:
                # Handle case where there are too few unique values
                logger.warning(
                    "Could not create 5 quintiles",
                    error=str(e),
                    unique_values=group.nunique(),
                )
                return pd.Series(np.nan, index=group.index)

        result[rank_column] = df.groupby(date_column)[roic_column].transform(
            _calculate_quintile
        )

        logger.info(
            "ROIC ranks calculated",
            output_column=rank_column,
            unique_ranks=result[rank_column].nunique(),
        )

        return result

    def add_shifted_values(
        self,
        df: pd.DataFrame,
        roic_column: str = "ROIC",
        ticker_column: str = "ticker",
        date_column: str = "date",
        past_periods: list[int] | None = None,
        future_periods: list[int] | None = None,
        freq_suffix: str = "Q",
    ) -> pd.DataFrame:
        """Add past and future ROIC value columns.

        Creates new columns with shifted ROIC values for each ticker.
        For past values, shift forward (current row gets past value).
        For future values, shift backward (current row gets future value).

        Parameters
        ----------
        df : pd.DataFrame
            Input DataFrame containing ROIC, ticker, and date columns
        roic_column : str, default="ROIC"
            Name of the column containing ROIC values
        ticker_column : str, default="ticker"
            Name of the column containing ticker/symbol values
        date_column : str, default="date"
            Name of the column containing date values
        past_periods : list[int] | None, default=None
            List of periods to shift for past values.
            E.g., [1, 2, 4] creates columns for 1, 2, and 4 periods ago.
        future_periods : list[int] | None, default=None
            List of periods to shift for future values.
            E.g., [1, 2, 4] creates columns for 1, 2, and 4 periods forward.
        freq_suffix : str, default="Q"
            Suffix for column names indicating frequency.
            "Q" for quarterly, "M" for monthly.

        Returns
        -------
        pd.DataFrame
            DataFrame with additional shifted value columns

        Notes
        -----
        Column naming convention:
        - Past: "{roic_column}_{n}{freq_suffix}Ago" (e.g., "ROIC_1QAgo")
        - Future: "{roic_column}_{n}{freq_suffix}Forward" (e.g., "ROIC_1QForward")

        Examples
        --------
        >>> factor = ROICFactor()
        >>> result = factor.add_shifted_values(
        ...     df,
        ...     past_periods=[1, 2],
        ...     future_periods=[1, 2],
        ...     freq_suffix="Q",
        ... )
        >>> "ROIC_1QAgo" in result.columns
        True
        """
        past_periods = past_periods or []
        future_periods = future_periods or []

        logger.debug(
            "Adding shifted ROIC values",
            roic_column=roic_column,
            ticker_column=ticker_column,
            past_periods=past_periods,
            future_periods=future_periods,
            freq_suffix=freq_suffix,
        )

        result = df.copy()

        # Ensure data is sorted by ticker and date for proper shifting
        result = result.sort_values([ticker_column, date_column])

        # Add past value columns
        for period in past_periods:
            col_name = f"{roic_column}_{period}{freq_suffix}Ago"
            result[col_name] = result.groupby(ticker_column)[roic_column].shift(period)
            logger.debug("Added past column", column=col_name, shift=period)

        # Add future value columns
        for period in future_periods:
            col_name = f"{roic_column}_{period}{freq_suffix}Forward"
            result[col_name] = result.groupby(ticker_column)[roic_column].shift(-period)
            logger.debug("Added future column", column=col_name, shift=-period)

        # Restore original order
        result = result.loc[df.index]

        logger.info(
            "Shifted ROIC values added",
            past_columns=len(past_periods),
            future_columns=len(future_periods),
        )

        return result


__all__ = ["ROICFactor"]

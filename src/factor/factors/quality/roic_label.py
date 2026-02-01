"""ROIC transition labeling for factor analysis.

This module provides functionality to label ROIC rank transitions
over time periods, categorizing stocks based on their ROIC trajectory.

Reference: src_sample/ROIC_make_data_files_ver2.py:1246-1386
"""

from collections.abc import Sequence
from typing import Any

import numpy as np
import pandas as pd
from utils_core.logging import get_logger

logger = get_logger(__name__)


class ROICTransitionLabeler:
    """ROIC transition labeler for categorizing rank trajectories.

    Labels stock ROIC trajectories based on rank transitions over time.
    Categories include: remain high, remain low, move to high, drop to low, others.

    Parameters
    ----------
    high_ranks : list[str] | None, default=None
        Ranks considered as "high" ROIC. Defaults to ["rank1", "rank2"].
    low_ranks : list[str] | None, default=None
        Ranks considered as "low" ROIC. Defaults to ["rank4", "rank5"].

    Attributes
    ----------
    high_ranks : list[str]
        Ranks considered high
    low_ranks : list[str]
        Ranks considered low

    Examples
    --------
    >>> labeler = ROICTransitionLabeler()
    >>> ranks = ["rank1", "rank1", "rank2", "rank1", "rank2"]
    >>> labeler.label_transition(ranks)
    'remain high'
    """

    def __init__(
        self,
        high_ranks: list[str] | None = None,
        low_ranks: list[str] | None = None,
    ) -> None:
        """Initialize ROICTransitionLabeler.

        Parameters
        ----------
        high_ranks : list[str] | None, default=None
            Ranks considered as "high" ROIC. Defaults to ["rank1", "rank2"].
        low_ranks : list[str] | None, default=None
            Ranks considered as "low" ROIC. Defaults to ["rank4", "rank5"].
        """
        self.high_ranks = high_ranks or ["rank1", "rank2"]
        self.low_ranks = low_ranks or ["rank4", "rank5"]

        logger.debug(
            "ROICTransitionLabeler initialized",
            high_ranks=self.high_ranks,
            low_ranks=self.low_ranks,
        )

    def label_transition(self, ranks: Sequence[Any]) -> str | float:
        """Generate transition label from a list of ranks.

        Analyzes the trajectory of ROIC ranks over time and assigns
        a descriptive label based on the observed pattern.

        Parameters
        ----------
        ranks : Sequence[Any]
            Sequence of rank values (e.g., ["rank1", "rank2", "rank3"]).
            Can contain np.nan for missing values.

        Returns
        -------
        str | float
            One of:
            - "remain high": All ranks are in high_ranks
            - "remain low": All ranks are in low_ranks
            - "move to high": Starts low/mid, ends high
            - "drop to low": Starts high/mid, ends low
            - "others": Other patterns
            - np.nan: Missing data

        Notes
        -----
        The logic follows src_sample/ROIC_make_data_files_ver2.py:1246-1386

        Examples
        --------
        >>> labeler = ROICTransitionLabeler()
        >>> labeler.label_transition(["rank5", "rank3", "rank2", "rank1"])
        'move to high'
        """
        # Handle empty list
        if not ranks:
            return np.nan

        # Check for any NaN values
        if any(pd.isna(r) for r in ranks):
            return np.nan

        first_rank = ranks[0]
        last_rank = ranks[-1]

        # Check "remain high" - all ranks in high_ranks
        if all(r in self.high_ranks for r in ranks):
            return "remain high"

        # Check "remain low" - all ranks in low_ranks
        if all(r in self.low_ranks for r in ranks):
            return "remain low"

        # Check "move to high" - starts low/mid, ends high
        # Low/mid: not in high_ranks (includes rank3, rank4, rank5)
        # High: in high_ranks (rank1, rank2)
        starts_not_high = first_rank not in self.high_ranks
        ends_high = last_rank in self.high_ranks
        if starts_not_high and ends_high:
            return "move to high"

        # Check "drop to low" - starts high/mid, ends low
        # High/mid: not in low_ranks (includes rank1, rank2, rank3)
        # Low: in low_ranks (rank4, rank5)
        starts_not_low = first_rank not in self.low_ranks
        ends_low = last_rank in self.low_ranks
        if starts_not_low and ends_low:
            return "drop to low"

        # All other patterns
        return "others"

    def label_dataframe(
        self,
        df: pd.DataFrame,
        rank_columns: list[str],
        label_column: str = "ROIC_Label",
    ) -> pd.DataFrame:
        """Add transition labels to a DataFrame.

        Applies label_transition to each row using the specified rank columns.

        Parameters
        ----------
        df : pd.DataFrame
            Input DataFrame containing rank columns
        rank_columns : list[str]
            List of column names containing ranks in chronological order
        label_column : str, default="ROIC_Label"
            Name of the output label column

        Returns
        -------
        pd.DataFrame
            DataFrame with additional label column

        Examples
        --------
        >>> labeler = ROICTransitionLabeler()
        >>> df = pd.DataFrame({
        ...     "ticker": ["A", "B"],
        ...     "ROIC_Rank": ["rank1", "rank5"],
        ...     "ROIC_Rank_1QForward": ["rank1", "rank1"],
        ... })
        >>> result = labeler.label_dataframe(df, ["ROIC_Rank", "ROIC_Rank_1QForward"])
        >>> result["ROIC_Label"].tolist()
        ['remain high', 'move to high']
        """
        logger.debug(
            "Labeling DataFrame",
            rank_columns=rank_columns,
            label_column=label_column,
            rows=len(df),
        )

        result = df.copy()

        def _apply_label(row: pd.Series) -> str | float:
            """Extract ranks and apply labeling."""
            ranks: list[Any] = [row[col] for col in rank_columns]
            return self.label_transition(ranks)

        result[label_column] = df.apply(_apply_label, axis=1)

        logger.info(
            "DataFrame labeled",
            label_column=label_column,
            unique_labels=result[label_column].nunique(),
        )

        return result


__all__ = ["ROICTransitionLabeler"]

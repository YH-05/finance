"""Sector-neutral normalization for the CA Strategy pipeline.

Thin wrapper around :class:`factor.core.normalizer.Normalizer` that
maps universe sector information, applies robust Z-score normalization
within each (as_of_date, gics_sector) group, and adds sector ranking.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pandas as pd

from factor.core.normalizer import Normalizer
from utils_core.logging import get_logger

if TYPE_CHECKING:
    from .types import UniverseConfig

logger = get_logger(__name__)


class SectorNeutralizer:
    """Apply sector-neutral Z-score normalization to stock scores.

    Wraps :class:`Normalizer.normalize_by_group` to compute robust
    Z-scores within (as_of_date, gics_sector) groups and adds
    ``sector_zscore`` and ``sector_rank`` columns to the result.

    Parameters
    ----------
    min_samples : int, default=5
        Minimum number of stocks in a sector group for Z-score
        calculation.  Groups with fewer samples get NaN Z-scores.

    Examples
    --------
    >>> neutralizer = SectorNeutralizer(min_samples=3)
    >>> ranked_df = neutralizer.neutralize(scores_df, universe)
    >>> ranked_df[["ticker", "sector_zscore", "sector_rank"]]
    """

    def __init__(self, min_samples: int = 5) -> None:
        self._normalizer = Normalizer(min_samples=min_samples)
        self._min_samples = min_samples
        logger.debug(
            "SectorNeutralizer initialized",
            min_samples=min_samples,
        )

    def neutralize(
        self,
        scores_df: pd.DataFrame,
        universe: UniverseConfig,
    ) -> pd.DataFrame:
        """Apply sector-neutral Z-score normalization and ranking.

        Parameters
        ----------
        scores_df : pd.DataFrame
            DataFrame with at least ``ticker``, ``aggregate_score``,
            and ``as_of_date`` columns.
        universe : UniverseConfig
            Universe configuration providing ticker-to-sector mapping.

        Returns
        -------
        pd.DataFrame
            Input DataFrame augmented with ``gics_sector``,
            ``sector_zscore``, and ``sector_rank`` columns.
            Tickers not in the universe are excluded.
        """
        if scores_df.empty:
            logger.info("Empty scores DataFrame, returning empty result")
            cols = [
                *scores_df.columns.tolist(),
                "gics_sector",
                "sector_zscore",
                "sector_rank",
            ]
            return pd.DataFrame(columns=pd.Index(cols))

        # Build ticker -> sector mapping from universe
        sector_map = {t.ticker: t.gics_sector for t in universe.tickers}
        logger.debug(
            "Universe sector mapping built",
            universe_size=len(sector_map),
        )

        # Add sector column via mapping
        result = scores_df.copy()
        result["gics_sector"] = result["ticker"].map(sector_map)  # type: ignore[arg-type]

        # Filter out tickers not in universe
        before_count = len(result)
        result = result.dropna(subset=["gics_sector"]).reset_index(drop=True)
        dropped = before_count - len(result)
        if dropped > 0:
            logger.warning(
                "Tickers not in universe excluded",
                dropped_count=dropped,
            )

        if result.empty:
            logger.info("No tickers matched universe")
            result["sector_zscore"] = pd.Series(dtype=float)
            result["sector_rank"] = pd.Series(dtype=float)
            return result

        # Apply robust Z-score normalization by (as_of_date, gics_sector)
        result = self._normalizer.normalize_by_group(
            data=result,
            value_column="aggregate_score",
            group_columns=["as_of_date", "gics_sector"],
            method="zscore",
            robust=True,
        )

        # Rename the output column from Normalizer's convention
        zscore_col = "aggregate_score_zscore"
        if zscore_col in result.columns:
            result = result.rename(columns={zscore_col: "sector_zscore"})

        # Compute sector rank (1 = highest score within sector/date group)
        result["sector_rank"] = (
            result.groupby(["as_of_date", "gics_sector"])["aggregate_score"]
            .rank(ascending=False, method="min")
            .astype(int)
        )

        logger.info(
            "Sector neutralization completed",
            total_stocks=len(result),
            sectors=result["gics_sector"].nunique(),
        )

        return result


__all__ = ["SectorNeutralizer"]

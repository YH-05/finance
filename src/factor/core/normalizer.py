"""Normalization algorithms for factor analysis.

This module provides various normalization methods for factor values including:
- Z-score normalization (standard and robust)
- Percentile rank transformation
- Quintile rank transformation
- Winsorization (outlier clipping)
- Group-based (sector-neutral) normalization
"""

from typing import Any

import numpy as np
import pandas as pd

from utils_core.logging import get_logger

from ..errors import ValidationError

logger = get_logger(__name__)


# Constants
_MAD_SCALE_FACTOR = 1.4826  # Scale factor to convert MAD to standard deviation


class Normalizer:
    """Factor normalization algorithms.

    Provides various normalization methods for cross-sectional factor data.
    All methods support both Series and DataFrame inputs, and can operate
    on groups for sector-neutral normalization.

    Parameters
    ----------
    min_samples : int, default=5
        Minimum number of valid samples required for calculations

    Examples
    --------
    >>> normalizer = Normalizer(min_samples=10)
    >>> zscore_data = normalizer.zscore(factor_series)
    >>> rank_data = normalizer.percentile_rank(factor_series)
    """

    def __init__(self, min_samples: int = 5) -> None:
        """Initialize Normalizer.

        Parameters
        ----------
        min_samples : int, default=5
            Minimum number of valid samples required for calculations

        Raises
        ------
        ValidationError
            If min_samples is not positive
        """
        if min_samples <= 0:
            raise ValidationError(
                f"min_samples must be positive, got {min_samples}",
                field="min_samples",
                value=min_samples,
            )
        self.min_samples = min_samples
        logger.debug("Normalizer initialized", min_samples=min_samples)

    def zscore(
        self,
        data: pd.Series | pd.DataFrame,
        *,
        robust: bool = True,
    ) -> pd.Series | pd.DataFrame:
        """Calculate Z-score normalization.

        Parameters
        ----------
        data : pd.Series | pd.DataFrame
            Input data to normalize
        robust : bool, default=True
            If True, use median and MAD (robust to outliers).
            If False, use mean and standard deviation.

        Returns
        -------
        pd.Series | pd.DataFrame
            Z-score normalized data with same shape as input

        Raises
        ------
        InsufficientDataError
            If fewer than min_samples valid values exist
        NormalizationError
            If standard deviation or MAD is zero

        Examples
        --------
        >>> normalizer = Normalizer()
        >>> zscore = normalizer.zscore(pd.Series([1, 2, 3, 4, 5]))
        >>> zscore.mean()  # Approximately 0
        0.0
        """
        logger.debug(
            "Calculating zscore",
            robust=robust,
            data_shape=data.shape if hasattr(data, "shape") else len(data),
        )

        if isinstance(data, pd.DataFrame):
            return data.apply(lambda x: self._zscore_series(x, robust=robust))
        return self._zscore_series(data, robust=robust)

    def _zscore_series(self, series: pd.Series, *, robust: bool) -> pd.Series:
        """Calculate Z-score for a single series."""
        valid_count = series.notna().sum()

        if valid_count < self.min_samples:
            logger.warning(
                "Insufficient data for zscore",
                valid_count=valid_count,
                min_samples=self.min_samples,
            )
            return pd.Series(np.nan, index=series.index)

        if robust:
            center = series.median()
            mad = (series - center).abs().median()
            scale = mad * _MAD_SCALE_FACTOR
        else:
            center = series.mean()
            scale = series.std()

        if scale == 0 or bool(pd.isna(scale)):
            logger.warning(
                "Zero or NaN scale in zscore calculation",
                robust=robust,
                center=center,
                scale=scale,
            )
            return pd.Series(np.nan, index=series.index)

        zscore = (series - center) / scale
        logger.debug(
            "Zscore calculated",
            center=float(center),
            scale=float(scale),
            valid_count=valid_count,
        )
        return zscore

    def percentile_rank(
        self,
        data: pd.Series | pd.DataFrame,
    ) -> pd.Series | pd.DataFrame:
        """Calculate percentile rank transformation (0-1 scale).

        Parameters
        ----------
        data : pd.Series | pd.DataFrame
            Input data to transform

        Returns
        -------
        pd.Series | pd.DataFrame
            Percentile ranks (0 to 1) with same shape as input

        Examples
        --------
        >>> normalizer = Normalizer()
        >>> ranks = normalizer.percentile_rank(pd.Series([10, 30, 20, 40, 50]))
        >>> ranks.tolist()
        [0.2, 0.6, 0.4, 0.8, 1.0]
        """
        logger.debug(
            "Calculating percentile rank",
            data_shape=data.shape if hasattr(data, "shape") else len(data),
        )

        if isinstance(data, pd.DataFrame):
            return data.apply(self._percentile_rank_series)
        return self._percentile_rank_series(data)

    def _percentile_rank_series(self, series: pd.Series) -> pd.Series:
        """Calculate percentile rank for a single series."""
        valid_count = series.notna().sum()

        if valid_count < self.min_samples:
            logger.warning(
                "Insufficient data for percentile rank",
                valid_count=valid_count,
                min_samples=self.min_samples,
            )
            return pd.Series(np.nan, index=series.index)

        return series.rank(pct=True)

    def quintile_rank(
        self,
        data: pd.Series | pd.DataFrame,
        *,
        labels: list[str] | None = None,
    ) -> pd.Series | pd.DataFrame:
        """Calculate quintile rank transformation (5 groups).

        Parameters
        ----------
        data : pd.Series | pd.DataFrame
            Input data to transform
        labels : list[str] | None, default=None
            Labels for quintile groups (1-5). If None, uses numeric values 1-5.
            Must have exactly 5 elements if provided.

        Returns
        -------
        pd.Series | pd.DataFrame
            Quintile ranks (1-5 or custom labels) with same shape as input

        Raises
        ------
        ValidationError
            If labels is provided but does not have exactly 5 elements

        Examples
        --------
        >>> normalizer = Normalizer()
        >>> quintiles = normalizer.quintile_rank(
        ...     pd.Series([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        ... )
        >>> quintiles.unique()
        array([1, 2, 3, 4, 5])
        """
        if labels is not None and len(labels) != 5:
            raise ValidationError(
                f"labels must have exactly 5 elements, got {len(labels)}",
                field="labels",
                value=labels,
            )

        logger.debug(
            "Calculating quintile rank",
            data_shape=data.shape if hasattr(data, "shape") else len(data),
            custom_labels=labels is not None,
        )

        if isinstance(data, pd.DataFrame):
            return data.apply(lambda x: self._quintile_rank_series(x, labels=labels))
        return self._quintile_rank_series(data, labels=labels)

    def _quintile_rank_series(
        self, series: pd.Series, *, labels: list[str] | None
    ) -> pd.Series:
        """Calculate quintile rank for a single series."""
        valid_count = series.notna().sum()

        if valid_count < self.min_samples:
            logger.warning(
                "Insufficient data for quintile rank",
                valid_count=valid_count,
                min_samples=self.min_samples,
            )
            return pd.Series(np.nan, index=series.index)

        try:
            # Use pd.qcut with labels=False to get numeric bins, then add 1
            qcut_result = pd.qcut(series, q=5, labels=False, duplicates="drop")
            quintile_numeric = pd.Series(qcut_result, index=series.index) + 1

            if labels is not None:
                # Map numeric values to custom labels
                label_map = {i: labels[i - 1] for i in range(1, 6)}
                return quintile_numeric.map(label_map)

            return quintile_numeric

        except ValueError as e:
            # Handle case where there are too few unique values for 5 bins
            logger.warning(
                "Could not create 5 quintiles",
                error=str(e),
                unique_values=series.nunique(),
            )
            return pd.Series(np.nan, index=series.index)

    def winsorize(
        self,
        data: pd.Series | pd.DataFrame,
        *,
        limits: tuple[float, float] = (0.01, 0.01),
    ) -> pd.Series | pd.DataFrame:
        """Winsorize data by clipping extreme values.

        Parameters
        ----------
        data : pd.Series | pd.DataFrame
            Input data to winsorize
        limits : tuple[float, float], default=(0.01, 0.01)
            Lower and upper percentile limits for clipping.
            (0.01, 0.01) means clip at 1st and 99th percentiles.
            (0.05, 0.05) means clip at 5th and 95th percentiles.

        Returns
        -------
        pd.Series | pd.DataFrame
            Winsorized data with same shape as input

        Raises
        ------
        ValidationError
            If limits are not valid percentiles (0-0.5)

        Examples
        --------
        >>> normalizer = Normalizer()
        >>> data = pd.Series([1, 2, 3, 100, 5])  # 100 is an outlier
        >>> winsorized = normalizer.winsorize(data, limits=(0.1, 0.1))
        """
        lower_limit, upper_limit = limits

        if not (0 <= lower_limit <= 0.5 and 0 <= upper_limit <= 0.5):
            raise ValidationError(
                f"limits must be in range [0, 0.5], got ({lower_limit}, {upper_limit})",
                field="limits",
                value=limits,
            )

        logger.debug(
            "Winsorizing data",
            data_shape=data.shape if hasattr(data, "shape") else len(data),
            limits=limits,
        )

        if isinstance(data, pd.DataFrame):
            return data.apply(lambda x: self._winsorize_series(x, limits=limits))
        return self._winsorize_series(data, limits=limits)

    def _winsorize_series(
        self, series: pd.Series, *, limits: tuple[float, float]
    ) -> pd.Series:
        """Winsorize a single series."""
        lower_limit, upper_limit = limits

        lower_quantile = series.quantile(lower_limit)
        upper_quantile = series.quantile(1 - upper_limit)

        return series.clip(lower=lower_quantile, upper=upper_quantile)

    def normalize_by_group(
        self,
        data: pd.DataFrame,
        value_column: str,
        group_columns: list[str],
        *,
        method: str = "zscore",
        **kwargs: Any,
    ) -> pd.DataFrame:
        """Normalize data within groups (e.g., sector-neutral normalization).

        Parameters
        ----------
        data : pd.DataFrame
            Input DataFrame containing value and group columns
        value_column : str
            Name of the column to normalize
        group_columns : list[str]
            Columns to group by (e.g., ["date", "sector"])
        method : str, default="zscore"
            Normalization method to apply. One of:
            - "zscore": Z-score normalization
            - "percentile_rank": Percentile rank (0-1)
            - "quintile_rank": Quintile rank (1-5)
            - "winsorize": Winsorization
        **kwargs : Any
            Additional arguments passed to the normalization method

        Returns
        -------
        pd.DataFrame
            DataFrame with additional normalized column

        Raises
        ------
        ValidationError
            If method is not recognized or required columns are missing

        Examples
        --------
        >>> normalizer = Normalizer()
        >>> df = pd.DataFrame({
        ...     "date": ["2024-01-01"] * 6,
        ...     "sector": ["Tech", "Tech", "Finance", "Finance", "Tech", "Finance"],
        ...     "value": [1, 2, 3, 4, 5, 6]
        ... })
        >>> result = normalizer.normalize_by_group(
        ...     df, "value", ["date", "sector"], method="zscore"
        ... )
        """
        # Validate columns exist
        missing_cols = [
            c for c in [value_column, *group_columns] if c not in data.columns
        ]
        if missing_cols:
            raise ValidationError(
                f"Missing columns in DataFrame: {missing_cols}",
                field="columns",
                value=missing_cols,
            )

        valid_methods = {"zscore", "percentile_rank", "quintile_rank", "winsorize"}
        if method not in valid_methods:
            raise ValidationError(
                f"Unknown method '{method}'. Must be one of: {valid_methods}",
                field="method",
                value=method,
            )

        logger.debug(
            "Normalizing by group",
            value_column=value_column,
            group_columns=group_columns,
            method=method,
        )

        result = data.copy()
        output_column = f"{value_column}_{method}"

        # Define normalization function based on method
        def normalize_func(group: pd.Series) -> pd.Series:
            if method == "zscore":
                return self._zscore_series(group, robust=kwargs.get("robust", True))
            elif method == "percentile_rank":
                return self._percentile_rank_series(group)
            elif method == "quintile_rank":
                return self._quintile_rank_series(group, labels=kwargs.get("labels"))
            else:  # winsorize
                return self._winsorize_series(
                    group, limits=kwargs.get("limits", (0.01, 0.01))
                )

        result[output_column] = data.groupby(group_columns)[value_column].transform(
            normalize_func
        )

        logger.info(
            "Group normalization completed",
            method=method,
            output_column=output_column,
            groups=len(data.groupby(group_columns)),
        )

        return result


__all__ = ["Normalizer"]

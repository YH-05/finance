"""PCA analysis for yield curve and factor decomposition.

This module provides PCA analysis with economically meaningful
sign adjustments, particularly for yield curve analysis.
"""

from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd
from utils_core.logging import get_logger

from ..errors import InsufficientDataError, ValidationError

logger = get_logger(__name__)

# Lazy import for sklearn to avoid heavy import cost
_PCA: Any = None


def _get_pca_class() -> Any:
    """Lazy import of sklearn PCA."""
    global _PCA
    if _PCA is None:
        from sklearn.decomposition import PCA

        _PCA = PCA
    return _PCA


@dataclass
class PCAResult:
    """Result of PCA analysis.

    Parameters
    ----------
    scores : pd.DataFrame
        Principal component scores (transformed data)
    components : np.ndarray
        Principal component loadings
    explained_variance_ratio : np.ndarray
        Proportion of variance explained by each component
    column_names : list[str]
        Names for the principal components
    pca_model : Any
        The fitted sklearn PCA object
    """

    scores: pd.DataFrame
    components: np.ndarray
    explained_variance_ratio: np.ndarray
    column_names: list[str]
    pca_model: Any = field(repr=False)

    @property
    def cumulative_variance(self) -> np.ndarray:
        """Get cumulative variance explained."""
        return np.cumsum(self.explained_variance_ratio)

    @property
    def total_variance_explained(self) -> float:
        """Get total variance explained by all components."""
        return float(np.sum(self.explained_variance_ratio))


class YieldCurvePCA:
    """PCA analysis for yield curves with economic interpretation.

    Performs PCA on yield curve data and aligns signs of components
    to ensure consistent economic interpretation:
    - PC1 (Level): Positive when all rates increase
    - PC2 (Slope): Positive when curve steepens (long > short)
    - PC3 (Curvature): Positive when middle rates rise relative to ends

    Parameters
    ----------
    n_components : int, default=3
        Number of principal components to extract

    Examples
    --------
    >>> pca = YieldCurvePCA(n_components=3)
    >>> result = pca.fit_transform(yield_data)
    >>> level_factor = result.scores["Level"]
    """

    def __init__(self, n_components: int = 3) -> None:
        """Initialize YieldCurvePCA.

        Parameters
        ----------
        n_components : int, default=3
            Number of principal components to extract
        """
        if n_components <= 0:
            raise ValidationError(
                f"n_components must be positive, got {n_components}",
                field="n_components",
                value=n_components,
            )
        self.n_components = n_components
        self._pca_model: Any = None
        logger.debug("YieldCurvePCA initialized", n_components=n_components)

    def fit_transform(
        self,
        data: pd.DataFrame,
        *,
        use_changes: bool = True,
        align_signs: bool = True,
    ) -> PCAResult:
        """Fit PCA and transform yield curve data.

        Parameters
        ----------
        data : pd.DataFrame
            Yield curve data with maturities as columns and dates as index.
            Should be sorted from shortest to longest maturity.
        use_changes : bool, default=True
            If True, perform PCA on yield changes (diff).
            If False, perform PCA on yield levels.
        align_signs : bool, default=True
            If True, align component signs for economic interpretation.

        Returns
        -------
        PCAResult
            Result containing scores, components, and explained variance

        Raises
        ------
        InsufficientDataError
            If data has fewer rows than n_components after removing NaN
        """
        PCA = _get_pca_class()

        logger.debug(
            "Fitting yield curve PCA",
            data_shape=data.shape,
            use_changes=use_changes,
            align_signs=align_signs,
        )

        # Prepare data
        if use_changes:
            pca_data = data.diff().dropna()
        else:
            pca_data = data.dropna()

        if len(pca_data) < self.n_components:
            raise InsufficientDataError(
                f"Insufficient data for PCA: {len(pca_data)} < {self.n_components}",
                required=self.n_components,
                available=len(pca_data),
            )

        # Fit PCA
        self._pca_model = PCA(n_components=self.n_components)
        scores_raw = self._pca_model.fit_transform(pca_data)
        components = self._pca_model.components_.copy()

        # Align signs if requested
        if align_signs:
            scores_aligned = self.align_signs(components, scores_raw)
        else:
            scores_aligned = scores_raw

        # Create column names
        column_names = self._get_component_names()

        # Create scores DataFrame
        scores_df = pd.DataFrame(
            scores_aligned,
            index=pca_data.index,
            columns=pd.Index(column_names),
        )

        result = PCAResult(
            scores=scores_df,
            components=components,
            explained_variance_ratio=self._pca_model.explained_variance_ratio_.copy(),
            column_names=column_names,
            pca_model=self._pca_model,
        )

        logger.info(
            "PCA fit completed",
            total_variance_explained=f"{result.total_variance_explained:.4f}",
            observations=len(pca_data),
        )

        return result

    def align_signs(
        self,
        components: np.ndarray,
        scores: np.ndarray,
    ) -> np.ndarray:
        """Align PCA component signs for economic interpretation.

        Adjusts signs based on economic interpretation of yield curve factors:
        - PC1 (Level): All loadings positive (rates up = factor up)
        - PC2 (Slope): Long end positive, short end negative (steepening positive)
        - PC3 (Curvature): Middle positive (hump = positive)

        Parameters
        ----------
        components : np.ndarray
            PCA loadings (n_components x n_features)
        scores : np.ndarray
            PCA scores (n_samples x n_components)

        Returns
        -------
        np.ndarray
            Sign-aligned scores (n_samples x n_components)

        Notes
        -----
        This method modifies the components array in-place and returns
        the aligned scores array.
        """
        aligned_scores = scores.copy()
        n_components = min(3, components.shape[0])

        # PC1 (Level): Sum of loadings should be positive
        if n_components >= 1 and np.sum(components[0]) < 0:
            components[0] = -components[0]
            aligned_scores[:, 0] = -aligned_scores[:, 0]
            logger.debug("PC1 (Level) sign flipped")

        # PC2 (Slope): Last loading (longest maturity) should be positive
        if n_components >= 2 and components[1, -1] < 0:
            components[1] = -components[1]
            aligned_scores[:, 1] = -aligned_scores[:, 1]
            logger.debug("PC2 (Slope) sign flipped")

        # PC3 (Curvature): Middle loading should be positive
        if n_components >= 3:
            mid_index = len(components[2]) // 2
            if components[2, mid_index] < 0:
                components[2] = -components[2]
                aligned_scores[:, 2] = -aligned_scores[:, 2]
                logger.debug("PC3 (Curvature) sign flipped")

        return aligned_scores

    def transform(
        self, data: pd.DataFrame, *, use_changes: bool = True
    ) -> pd.DataFrame:
        """Transform new data using the fitted PCA model.

        Parameters
        ----------
        data : pd.DataFrame
            Yield curve data to transform
        use_changes : bool, default=True
            If True, transform yield changes (diff)

        Returns
        -------
        pd.DataFrame
            Transformed scores

        Raises
        ------
        RuntimeError
            If called before fit_transform
        """
        if self._pca_model is None:
            raise RuntimeError("Must call fit_transform before transform")

        if use_changes:
            transform_data = data.diff().dropna()
        else:
            transform_data = data.dropna()

        scores = self._pca_model.transform(transform_data)

        # Apply sign alignment consistent with fitted model
        aligned_scores = self.align_signs(self._pca_model.components_, scores)

        return pd.DataFrame(
            aligned_scores,
            index=transform_data.index,
            columns=pd.Index(self._get_component_names()),
        )

    def get_loadings(self) -> pd.DataFrame:
        """Get PCA loadings as a DataFrame.

        Returns
        -------
        pd.DataFrame
            Loadings with components as rows and features as columns

        Raises
        ------
        RuntimeError
            If called before fit_transform
        """
        if self._pca_model is None:
            raise RuntimeError("Must call fit_transform before get_loadings")

        return pd.DataFrame(
            self._pca_model.components_,
            index=pd.Index(self._get_component_names()),
        )

    def _get_component_names(self) -> list[str]:
        """Generate component names based on n_components."""
        standard_names = ["Level", "Slope", "Curvature"]
        if self.n_components <= 3:
            return standard_names[: self.n_components]
        # For additional components beyond 3
        extra_names = [f"PC{i + 1}" for i in range(3, self.n_components)]
        return standard_names + extra_names


__all__ = ["PCAResult", "YieldCurvePCA"]

"""Abstract base class for macro factors.

This module provides the BaseMacroFactor abstract base class that defines
the common interface for all macroeconomic factor implementations.
"""

from abc import ABC, abstractmethod

import pandas as pd

from utils_core.logging import get_logger

logger = get_logger(__name__)


class BaseMacroFactor(ABC):
    """Abstract base class for macroeconomic factors.

    This class defines the common interface that all macro factor
    implementations must follow. It provides:
    - name: Factor identifier
    - required_series: List of required FRED series IDs
    - calculate: Method to compute factor values from input data

    Subclasses must implement all abstract properties and methods.

    Examples
    --------
    >>> class MyFactor(BaseMacroFactor):
    ...     @property
    ...     def name(self) -> str:
    ...         return "MyFactor"
    ...
    ...     @property
    ...     def required_series(self) -> list[str]:
    ...         return ["SERIES1", "SERIES2"]
    ...
    ...     def calculate(self, data: pd.DataFrame) -> pd.DataFrame:
    ...         return data.copy()
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the factor name.

        Returns
        -------
        str
            The unique identifier for this factor.
        """
        ...

    @property
    @abstractmethod
    def required_series(self) -> list[str]:
        """Return the list of required FRED series IDs.

        Returns
        -------
        list[str]
            List of FRED series identifiers required for calculation.
            Each series ID should be unique and valid for FRED API.
        """
        ...

    @abstractmethod
    def calculate(
        self,
        data: pd.DataFrame,
        **kwargs: pd.Series | pd.DataFrame | None,
    ) -> pd.DataFrame:
        """Calculate factor values from input data.

        Parameters
        ----------
        data : pd.DataFrame
            Input data containing the required series as columns.
            Index should be DatetimeIndex.
        **kwargs : pd.Series | pd.DataFrame | None
            Additional optional arguments for factor calculation.
            Common kwargs include:
            - market_factor: Market factor for orthogonalization
            - control_factors: Control factors for orthogonalization

        Returns
        -------
        pd.DataFrame
            DataFrame containing the calculated factor values.
            Index should be DatetimeIndex matching the input data.
            Columns are the factor names (e.g., "Level", "Slope", "Curvature").

        Raises
        ------
        KeyError
            If required series are missing from input data.
        InsufficientDataError
            If there are not enough data points for calculation.
        """
        ...

    def __repr__(self) -> str:
        """Return string representation of the factor."""
        return f"{self.__class__.__name__}(name={self.name!r})"


__all__ = ["BaseMacroFactor"]

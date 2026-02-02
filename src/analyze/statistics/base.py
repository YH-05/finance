"""Base statistical analyzer abstract class.

This module provides the abstract base class for all statistical analyzers,
defining the common interface for performing statistical calculations
on financial data.

Examples
--------
>>> from analyze.statistics.base import StatisticalAnalyzer
>>> class MyAnalyzer(StatisticalAnalyzer):
...     def calculate(self, df: pd.DataFrame, **kwargs) -> pd.DataFrame:
...         return df.describe()
...     def validate_input(self, df: pd.DataFrame) -> bool:
...         return not df.empty
"""

from abc import ABC, abstractmethod
from typing import Any

import pandas as pd

from utils_core.logging import get_logger

logger = get_logger(__name__)


class StatisticalAnalyzer(ABC):
    """Abstract base class for statistical analyzers.

    This class defines the common interface for all statistical analyzers,
    providing a standardized way to perform calculations and validate input
    data for various statistical analyses.

    Subclasses must implement:
    - calculate(): Perform the statistical calculation
    - validate_input(): Validate the input data

    Attributes
    ----------
    name : str
        The name of the analyzer (defaults to class name)

    Examples
    --------
    >>> class RollingMeanAnalyzer(StatisticalAnalyzer):
    ...     def calculate(self, df: pd.DataFrame, window: int = 20) -> pd.DataFrame:
    ...         return df.rolling(window).mean()
    ...
    ...     def validate_input(self, df: pd.DataFrame) -> bool:
    ...         return not df.empty and df.select_dtypes(include=['number']).shape[1] > 0
    ...
    >>> analyzer = RollingMeanAnalyzer()
    >>> result = analyzer.analyze(price_df, window=30)
    """

    @property
    def name(self) -> str:
        """Return the name of this statistical analyzer.

        Returns
        -------
        str
            The analyzer name (defaults to class name)

        Examples
        --------
        >>> analyzer = MyAnalyzer()
        >>> analyzer.name
        'MyAnalyzer'
        """
        return self.__class__.__name__

    @abstractmethod
    def calculate(self, df: pd.DataFrame, **kwargs: Any) -> pd.DataFrame:
        """Perform the statistical calculation.

        This method should implement the core statistical calculation logic.
        The implementation should handle the specific analysis requirements
        and return the results as a DataFrame.

        Parameters
        ----------
        df : pd.DataFrame
            The input data for the calculation. The expected format
            depends on the specific analyzer implementation.
        **kwargs : Any
            Additional keyword arguments specific to the calculation.
            Common arguments include:
            - window: Rolling window size
            - periods: Number of periods for calculations
            - target: Target column name for comparison

        Returns
        -------
        pd.DataFrame
            The calculation results. The structure depends on the
            specific analyzer implementation.

        Raises
        ------
        ValueError
            If the input data is invalid or missing required columns.
        CalculationError
            If the calculation fails.

        Examples
        --------
        >>> analyzer = RollingCorrelationAnalyzer()
        >>> result = analyzer.calculate(price_df, window=60, target="SPY")
        >>> result.head()
                      AAPL      MSFT
        2024-01-01   0.85      0.90
        2024-01-02   0.86      0.89
        """
        ...

    @abstractmethod
    def validate_input(self, df: pd.DataFrame) -> bool:
        """Validate the input data for calculation.

        This method should verify that the input DataFrame meets the
        requirements for the specific statistical calculation, including
        checking for required columns, data types, and sufficient data points.

        Parameters
        ----------
        df : pd.DataFrame
            The DataFrame to validate.

        Returns
        -------
        bool
            True if the data is valid for calculation, False otherwise.

        Examples
        --------
        >>> analyzer = RollingCorrelationAnalyzer()
        >>> df = pd.DataFrame({"AAPL": [100, 101, 102], "SPY": [400, 401, 402]})
        >>> analyzer.validate_input(df)
        True
        >>> analyzer.validate_input(pd.DataFrame())
        False
        """
        ...

    def analyze(self, df: pd.DataFrame, **kwargs: Any) -> pd.DataFrame:
        """Validate input and perform calculation in a single operation.

        This convenience method combines validate_input() and calculate()
        to provide a simple interface for statistical analysis. It logs
        the analysis process and raises an error if validation fails.

        Parameters
        ----------
        df : pd.DataFrame
            The input data for analysis.
        **kwargs : Any
            Additional keyword arguments passed to calculate().

        Returns
        -------
        pd.DataFrame
            The validated calculation results.

        Raises
        ------
        ValueError
            If the input data fails validation.

        Examples
        --------
        >>> analyzer = RollingBetaAnalyzer()
        >>> result = analyzer.analyze(price_df, window=60, benchmark="SPY")
        >>> print(f"Calculated beta for {len(result)} periods")
        Calculated beta for 252 periods
        """
        logger.info(
            "Starting statistical analysis",
            analyzer=self.name,
            input_rows=len(df),
            kwargs=str(kwargs) if kwargs else "none",
        )

        if not self.validate_input(df):
            logger.error(
                "Input validation failed",
                analyzer=self.name,
                input_rows=len(df),
                input_columns=list(df.columns) if not df.empty else [],
            )
            msg = f"Input validation failed for {self.name}"
            raise ValueError(msg)

        logger.debug(
            "Input validation passed",
            analyzer=self.name,
        )

        result = self.calculate(df, **kwargs)

        logger.info(
            "Statistical analysis completed",
            analyzer=self.name,
            output_rows=len(result),
            output_columns=list(result.columns) if not result.empty else [],
        )

        return result


__all__ = ["StatisticalAnalyzer"]

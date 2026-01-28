"""Integrated strategy builder combining market, analyze, and factor packages.

This module provides the main integration point that combines all three
packages (market, analyze, factor) for unified strategy construction.

Classes
-------
IntegratedStrategyBuilder
    Unified builder for portfolio strategies using all integrated packages

Functions
---------
create_integrated_builder
    Factory function to create an IntegratedStrategyBuilder

Examples
--------
>>> from strategy.integration import create_integrated_builder
>>> builder = create_integrated_builder()
>>> strategy = builder.build_strategy(symbols, start_date, end_date)
"""

from datetime import datetime
from typing import Any

import pandas as pd

from utils_core.logging import get_logger

from .analyze_integration import TechnicalSignalProvider, create_signal_provider
from .factor_integration import FactorBasedRiskCalculator, create_factor_risk_calculator
from .market_integration import (
    StrategyMarketDataProvider,
    create_strategy_market_provider,
)

logger = get_logger(__name__)


class IntegratedStrategyBuilder:
    """Builder for portfolio strategies using market, analyze, and factor packages.

    This class provides a unified interface for constructing portfolio
    strategies by integrating data from the market package, signals from
    the analyze package, and risk analysis from the factor package.

    Parameters
    ----------
    market_provider : StrategyMarketDataProvider | None
        Custom market data provider. If None, creates a default one.
    signal_provider : TechnicalSignalProvider | None
        Custom signal provider. If None, creates a default one.
    risk_calculator : FactorBasedRiskCalculator | None
        Custom risk calculator. If None, creates a default one.

    Attributes
    ----------
    market_provider : StrategyMarketDataProvider
        The market data provider
    signal_provider : TechnicalSignalProvider
        The technical signal provider
    risk_calculator : FactorBasedRiskCalculator
        The factor-based risk calculator

    Examples
    --------
    >>> builder = IntegratedStrategyBuilder()
    >>> strategy = builder.build_strategy(
    ...     symbols=["AAPL", "GOOGL"],
    ...     start_date="2024-01-01",
    ...     end_date="2024-12-31",
    ... )
    """

    def __init__(
        self,
        market_provider: StrategyMarketDataProvider | None = None,
        signal_provider: TechnicalSignalProvider | None = None,
        risk_calculator: FactorBasedRiskCalculator | None = None,
    ) -> None:
        """Initialize IntegratedStrategyBuilder.

        Parameters
        ----------
        market_provider : StrategyMarketDataProvider | None
            Custom market data provider
        signal_provider : TechnicalSignalProvider | None
            Custom signal provider
        risk_calculator : FactorBasedRiskCalculator | None
            Custom risk calculator
        """
        logger.debug("Initializing IntegratedStrategyBuilder")

        self._market_provider = market_provider or create_strategy_market_provider()
        self._signal_provider = signal_provider or create_signal_provider()
        self._risk_calculator = risk_calculator or create_factor_risk_calculator()

        logger.info("IntegratedStrategyBuilder initialized")

    @property
    def market_provider(self) -> StrategyMarketDataProvider:
        """Get the market data provider.

        Returns
        -------
        StrategyMarketDataProvider
            The market data provider
        """
        return self._market_provider

    @property
    def signal_provider(self) -> TechnicalSignalProvider:
        """Get the technical signal provider.

        Returns
        -------
        TechnicalSignalProvider
            The signal provider
        """
        return self._signal_provider

    @property
    def risk_calculator(self) -> FactorBasedRiskCalculator:
        """Get the factor-based risk calculator.

        Returns
        -------
        FactorBasedRiskCalculator
            The risk calculator
        """
        return self._risk_calculator

    def build_strategy(
        self,
        symbols: list[str],
        start_date: datetime | str,
        end_date: datetime | str,
        include_signals: bool = True,
        include_risk: bool = True,
    ) -> dict[str, Any]:
        """Build a comprehensive portfolio strategy.

        This method combines data from all three integrated packages:
        1. Market package: Fetch price data
        2. Analyze package: Compute technical signals
        3. Factor package: Calculate risk metrics

        Parameters
        ----------
        symbols : list[str]
            List of ticker symbols
        start_date : datetime | str
            Start date for analysis
        end_date : datetime | str
            End date for analysis
        include_signals : bool
            Whether to include technical signals (default: True)
        include_risk : bool
            Whether to include risk analysis (default: True)

        Returns
        -------
        dict[str, Any]
            Strategy results containing:
            - prices: Price data DataFrame
            - returns: Returns DataFrame
            - signals: Dict of technical signals per symbol (if include_signals)
            - risk: Dict of risk metrics per symbol (if include_risk)
            - summary: Strategy summary

        Raises
        ------
        ValueError
            If symbols list is empty

        Examples
        --------
        >>> builder = IntegratedStrategyBuilder()
        >>> result = builder.build_strategy(["AAPL"], "2024-01-01", "2024-12-31")
        >>> "prices" in result
        True
        """
        logger.info(
            "Building integrated strategy",
            symbols=symbols,
            start_date=str(start_date),
            end_date=str(end_date),
        )

        if not symbols:
            logger.error("Empty symbols list provided")
            raise ValueError("symbols list cannot be empty")

        result: dict[str, Any] = {
            "symbols": symbols,
            "start_date": str(start_date),
            "end_date": str(end_date),
        }

        # Step 1: Fetch price data from market package
        logger.debug("Step 1: Fetching price data")
        try:
            prices = self._market_provider.get_prices(symbols, start_date, end_date)
            result["prices"] = prices

            # Calculate returns
            returns = self._market_provider.get_returns(symbols, start_date, end_date)
            result["returns"] = returns
        except Exception as e:
            logger.error("Failed to fetch market data", error=str(e))
            result["prices"] = pd.DataFrame()
            result["returns"] = pd.DataFrame()

        # Step 2: Compute technical signals from analyze package
        if include_signals:
            logger.debug("Step 2: Computing technical signals")
            signals: dict[str, dict[str, Any]] = {}

            for symbol in symbols:
                close_key = (symbol, "Close")
                if not result["prices"].empty and close_key in result["prices"].columns:
                    close_data = result["prices"][close_key]
                    if isinstance(close_data, pd.Series):
                        signals[symbol] = self._signal_provider.compute_signals(
                            close_data
                        )
                    else:
                        signals[symbol] = {}
                else:
                    signals[symbol] = {}

            result["signals"] = signals

        # Step 3: Calculate risk metrics from factor package
        if include_risk:
            logger.debug("Step 3: Calculating risk metrics")
            risk: dict[str, dict[str, Any]] = {}

            for symbol in symbols:
                if not result["returns"].empty and symbol in result["returns"].columns:
                    symbol_data = result["returns"][symbol].dropna()
                    symbol_returns = pd.Series(symbol_data)
                    if len(symbol_returns) > 0:
                        risk[symbol] = self._risk_calculator.calculate_risk(
                            symbol_returns
                        )
                    else:
                        risk[symbol] = {}
                else:
                    risk[symbol] = {}

            result["risk"] = risk

        # Generate summary
        result["summary"] = self._generate_summary(result)

        logger.info(
            "Strategy built successfully",
            symbols_count=len(symbols),
            has_prices=not result["prices"].empty,
            has_returns=not result["returns"].empty,
        )

        return result

    def _generate_summary(self, result: dict[str, Any]) -> dict[str, Any]:
        """Generate strategy summary.

        Parameters
        ----------
        result : dict[str, Any]
            Strategy results

        Returns
        -------
        dict[str, Any]
            Summary statistics
        """
        summary: dict[str, Any] = {
            "symbols": result.get("symbols", []),
            "start_date": result.get("start_date"),
            "end_date": result.get("end_date"),
        }

        # Price data summary
        prices = result.get("prices")
        if prices is not None and not prices.empty:
            summary["data_points"] = len(prices)
            summary["date_range"] = {
                "first": str(prices.index.min()),
                "last": str(prices.index.max()),
            }
        else:
            summary["data_points"] = 0
            summary["date_range"] = None

        # Risk summary
        risk = result.get("risk", {})
        if risk:
            volatilities = [
                r.get("volatility")
                for r in risk.values()
                if r.get("volatility") is not None
            ]
            if volatilities:
                summary["avg_volatility"] = sum(volatilities) / len(volatilities)

        # Signal summary
        signals = result.get("signals", {})
        if signals:
            summary["signals_computed"] = list(
                set(
                    key for symbol_signals in signals.values() for key in symbol_signals
                )
            )

        return summary

    def analyze_correlations(
        self,
        symbols: list[str],
        start_date: datetime | str,
        end_date: datetime | str,
    ) -> pd.DataFrame:
        """Analyze return correlations between symbols.

        Parameters
        ----------
        symbols : list[str]
            List of ticker symbols
        start_date : datetime | str
            Start date
        end_date : datetime | str
            End date

        Returns
        -------
        pd.DataFrame
            Correlation matrix

        Examples
        --------
        >>> builder = IntegratedStrategyBuilder()
        >>> corr = builder.analyze_correlations(["AAPL", "GOOGL"], "2024-01-01", "2024-12-31")
        """
        logger.debug("Analyzing correlations", symbols=symbols)

        returns = self._market_provider.get_returns(symbols, start_date, end_date)

        if returns.empty:
            return pd.DataFrame()

        correlation = returns.corr()

        logger.info("Correlations analyzed", shape=correlation.shape)

        return correlation


def create_integrated_builder(
    market_provider: StrategyMarketDataProvider | None = None,
    signal_provider: TechnicalSignalProvider | None = None,
    risk_calculator: FactorBasedRiskCalculator | None = None,
) -> IntegratedStrategyBuilder:
    """Factory function to create an IntegratedStrategyBuilder.

    Parameters
    ----------
    market_provider : StrategyMarketDataProvider | None
        Custom market data provider
    signal_provider : TechnicalSignalProvider | None
        Custom signal provider
    risk_calculator : FactorBasedRiskCalculator | None
        Custom risk calculator

    Returns
    -------
    IntegratedStrategyBuilder
        A new IntegratedStrategyBuilder instance

    Examples
    --------
    >>> builder = create_integrated_builder()
    >>> isinstance(builder, IntegratedStrategyBuilder)
    True
    """
    logger.debug("Creating IntegratedStrategyBuilder via factory function")
    return IntegratedStrategyBuilder(
        market_provider=market_provider,
        signal_provider=signal_provider,
        risk_calculator=risk_calculator,
    )


__all__ = [
    "IntegratedStrategyBuilder",
    "create_integrated_builder",
]

"""Portfolio management module for the strategy package.

This module provides the Portfolio class for managing portfolio holdings,
asset allocations, and period settings for analysis.
"""

from __future__ import annotations

import warnings
from datetime import date
from typing import TYPE_CHECKING, overload

from .errors import NormalizationWarning, ValidationError
from .types import Holding, Period, PresetPeriod
from .utils.logging_config import get_logger

if TYPE_CHECKING:
    from .providers.protocol import DataProvider

logger = get_logger(__name__, module="portfolio")


class Portfolio:
    """ポートフォリオ管理クラス.

    保有銘柄と比率を管理し、資産配分分析やリスク指標計算を提供する。

    Parameters
    ----------
    holdings : list[tuple[str, float]] | list[Holding]
        保有銘柄のリスト。(ticker, weight) タプルまたは Holding オブジェクト
    provider : DataProvider | None
        データプロバイダー。None の場合は後から set_provider で設定
    name : str | None
        ポートフォリオ名（任意）
    normalize : bool
        比率の合計が1.0でない場合に自動正規化するか（デフォルト: False）

    Raises
    ------
    ValidationError
        holdings が空の場合
    ValueError
        ティッカーが空文字列または比率が無効な範囲の場合

    Examples
    --------
    >>> portfolio = Portfolio([("VOO", 0.6), ("BND", 0.4)])
    >>> portfolio.tickers
    ['VOO', 'BND']
    >>> portfolio.weights
    {'VOO': 0.6, 'BND': 0.4}

    >>> # Holding オブジェクトを使用
    >>> holdings = [Holding("VOO", 0.6), Holding("BND", 0.4)]
    >>> portfolio = Portfolio(holdings, name="60/40 Portfolio")
    """

    # AIDEV-NOTE: 正規化チェックの許容誤差
    _WEIGHT_TOLERANCE = 1e-9

    def __init__(
        self,
        holdings: list[tuple[str, float]] | list[Holding],
        provider: DataProvider | None = None,
        name: str | None = None,
        normalize: bool = False,
    ) -> None:
        """Initialize Portfolio with holdings and optional parameters.

        Parameters
        ----------
        holdings : list[tuple[str, float]] | list[Holding]
            保有銘柄のリスト。(ticker, weight) タプルまたは Holding オブジェクト
        provider : DataProvider | None
            データプロバイダー。None の場合は後から set_provider で設定
        name : str | None
            ポートフォリオ名（任意）
        normalize : bool
            比率の合計が1.0でない場合に自動正規化するか（デフォルト: False）
        """
        logger.debug(
            "Creating Portfolio",
            holdings_count=len(holdings),
            name=name,
            normalize=normalize,
            has_provider=provider is not None,
        )

        # Validate holdings is not empty
        if not holdings:
            logger.error("Portfolio creation failed", reason="empty holdings")
            msg = "holdings cannot be empty"
            raise ValidationError(msg, code="PORTFOLIO_001")

        # Convert to Holding objects
        self._holdings = self._convert_to_holdings(holdings)

        # Store other attributes
        self._provider = provider
        self._name = name
        self._period: Period | None = None

        # Handle normalization
        self._handle_normalization(normalize)

        logger.info(
            "Portfolio created",
            holdings_count=len(self._holdings),
            tickers=[h.ticker for h in self._holdings],
            name=name,
            total_weight=sum(h.weight for h in self._holdings),
        )

    def _convert_to_holdings(
        self,
        holdings: list[tuple[str, float]] | list[Holding],
    ) -> list[Holding]:
        """Convert holdings input to list of Holding objects.

        Parameters
        ----------
        holdings : list[tuple[str, float]] | list[Holding]
            Input holdings in either tuple or Holding format

        Returns
        -------
        list[Holding]
            List of Holding objects

        Raises
        ------
        ValueError
            If ticker is empty or weight is out of range
        """
        result: list[Holding] = []

        for item in holdings:
            if isinstance(item, Holding):
                result.append(item)
            else:
                # Tuple format (ticker, weight)
                ticker, weight = item
                # Holding's __post_init__ will validate
                result.append(Holding(ticker=ticker, weight=weight))

        return result

    def _handle_normalization(self, normalize: bool) -> None:
        """Handle weight normalization.

        Parameters
        ----------
        normalize : bool
            Whether to normalize weights to sum to 1.0
        """
        total_weight = sum(h.weight for h in self._holdings)

        if abs(total_weight - 1.0) < self._WEIGHT_TOLERANCE:
            # Weights already sum to 1.0
            logger.debug("Weights already normalized", total_weight=total_weight)
            return

        if normalize:
            # Normalize weights
            logger.debug(
                "Normalizing weights",
                original_total=total_weight,
                target_total=1.0,
            )
            self._holdings = [
                Holding(ticker=h.ticker, weight=h.weight / total_weight)
                for h in self._holdings
            ]
            logger.info(
                "Weights normalized",
                original_total=total_weight,
                new_total=sum(h.weight for h in self._holdings),
            )
        else:
            # Issue warning
            logger.warning(
                "Weights do not sum to 1.0",
                total_weight=total_weight,
                expected=1.0,
                difference=total_weight - 1.0,
            )
            warnings.warn(
                f"sum of weights ({total_weight:.6f}) does not equal 1.0, "
                "consider using normalize=True",
                NormalizationWarning,
                stacklevel=3,
            )

    @property
    def holdings(self) -> list[Holding]:
        """保有銘柄のリストを返す.

        Returns
        -------
        list[Holding]
            保有銘柄のリスト（防御的コピー）
        """
        return list(self._holdings)

    @property
    def tickers(self) -> list[str]:
        """ティッカーシンボルのリストを返す.

        Returns
        -------
        list[str]
            ティッカーシンボルのリスト（入力順序を保持）
        """
        return [h.ticker for h in self._holdings]

    @property
    def weights(self) -> dict[str, float]:
        """ティッカーと比率の辞書を返す.

        Returns
        -------
        dict[str, float]
            ティッカーをキー、比率を値とする辞書
        """
        return {h.ticker: h.weight for h in self._holdings}

    @property
    def name(self) -> str | None:
        """ポートフォリオ名を返す.

        Returns
        -------
        str | None
            ポートフォリオ名。設定されていない場合は None
        """
        return self._name

    def set_provider(self, provider: DataProvider) -> None:
        """データプロバイダーを設定.

        Parameters
        ----------
        provider : DataProvider
            設定するデータプロバイダー
        """
        logger.debug(
            "Setting provider",
            provider_type=type(provider).__name__,
        )
        self._provider = provider
        logger.info("Provider set", provider_type=type(provider).__name__)

    @overload
    def set_period(self, preset: PresetPeriod) -> None: ...

    @overload
    def set_period(self, *, start: str, end: str | None = None) -> None: ...

    def set_period(
        self,
        preset: PresetPeriod | None = None,
        *,
        start: str | None = None,
        end: str | None = None,
    ) -> None:
        """分析期間を設定.

        Parameters
        ----------
        preset : PresetPeriod | None
            プリセット期間（"1y", "3y", "5y", "10y", "ytd", "max"）
        start : str | None
            開始日（YYYY-MM-DD形式）
        end : str | None
            終了日（YYYY-MM-DD形式）。None の場合は今日

        Raises
        ------
        ValidationError
            preset と start/end を同時に指定した場合
            preset も start/end も指定しなかった場合
            start が end より後の場合
        ValueError
            日付形式が無効な場合
        """
        logger.debug(
            "Setting period",
            preset=preset,
            start=start,
            end=end,
        )

        # Validate mutually exclusive parameters
        if preset is not None and start is not None:
            logger.error(
                "Invalid period parameters",
                reason="preset and start are mutually exclusive",
            )
            msg = "preset and start/end are mutually exclusive"
            raise ValidationError(msg, code="PORTFOLIO_002")

        if preset is None and start is None:
            logger.error(
                "Invalid period parameters",
                reason="neither preset nor start specified",
            )
            msg = "Either preset or start must be specified"
            raise ValidationError(msg, code="PORTFOLIO_003")

        if preset is not None:
            # Use preset period
            self._period = Period.from_preset(preset)
            logger.info("Period set from preset", preset=preset)
        else:
            # Use custom period
            assert start is not None  # For type checker
            start_date = self._parse_date(start)
            end_date = self._parse_date(end) if end else date.today()

            if start_date > end_date:
                logger.error(
                    "Invalid period",
                    reason="start is after end",
                    start=start,
                    end=end or "today",
                )
                msg = "start must be before end"
                raise ValidationError(msg, code="PORTFOLIO_004")

            self._period = Period(start=start_date, end=end_date)
            logger.info(
                "Period set from custom range",
                start=start_date.isoformat(),
                end=end_date.isoformat(),
            )

    def _parse_date(self, date_str: str) -> date:
        """Parse date string in YYYY-MM-DD format.

        Parameters
        ----------
        date_str : str
            Date string in YYYY-MM-DD format

        Returns
        -------
        date
            Parsed date object

        Raises
        ------
        ValueError
            If date format is invalid
        """
        try:
            parts = date_str.split("-")
            if len(parts) != 3:
                raise ValueError("Expected YYYY-MM-DD format")

            year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
            return date(year, month, day)
        except (ValueError, AttributeError) as e:
            logger.error(
                "Invalid date format",
                date_str=date_str,
                error=str(e),
            )
            msg = f"Invalid date format: {date_str!r}, expected YYYY-MM-DD"
            raise ValueError(msg) from e

    def __repr__(self) -> str:
        """ポートフォリオの文字列表現.

        Returns
        -------
        str
            ポートフォリオの構成を示す文字列
        """
        holdings_str = ", ".join(f"{h.ticker}={h.weight:.2%}" for h in self._holdings)

        if self._name:
            return f"Portfolio(name={self._name!r}, holdings=[{holdings_str}])"
        return f"Portfolio(holdings=[{holdings_str}])"

    def __len__(self) -> int:
        """保有銘柄数を返す.

        Returns
        -------
        int
            保有銘柄数
        """
        return len(self._holdings)

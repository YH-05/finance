"""Analysis API for technical analysis and correlation.

This module provides a unified interface for technical analysis operations
including moving averages, returns, volatility, and correlation analysis.
"""

import datetime
from typing import Literal, Self, cast

import curl_cffi
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import yfinance as yf

from ..analysis import Analyzer, CorrelationAnalyzer
from ..errors import AnalysisError, ErrorCode, ValidationError
from ..types import AnalysisResult
from ..utils.logging_config import get_logger

logger = get_logger(__name__, module="analysis_api")

type CorrelationMethod = Literal["pearson", "spearman", "kendall"]


def _find_column(df: pd.DataFrame, col_name: str, operation: str) -> pd.Series:
    """Find column in DataFrame (case-insensitive).

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame to search in
    col_name : str
        Column name to find
    operation : str
        Operation name for error message

    Returns
    -------
    pd.Series
        The found column

    Raises
    ------
    AnalysisError
        If column is not found
    """
    col_lower = col_name.lower()
    for c in df.columns:
        if c.lower() == col_lower:
            return cast("pd.Series", df[c])
    raise AnalysisError(
        f"Column '{col_name}' not found in DataFrame",
        operation=operation,
        code=ErrorCode.INVALID_PARAMETER,
    )


class Analysis:
    """Technical analysis class with method chaining support.

    Provides methods to add technical indicators to price data and
    perform correlation analysis between multiple instruments.

    Parameters
    ----------
    data : pd.DataFrame
        OHLCV DataFrame with at least a 'close' column
    symbol : str
        Symbol identifier for the data

    Examples
    --------
    >>> import pandas as pd
    >>> df = pd.DataFrame({"close": [100, 102, 101, 103, 105, 104, 106]})
    >>> analysis = Analysis(df)
    >>> result = (
    ...     analysis
    ...     .add_sma(period=3)
    ...     .add_ema(period=3)
    ...     .add_returns()
    ...     .add_volatility(period=3)
    ... )
    >>> result.data.columns.tolist()
    ['close', 'sma_3', 'ema_3', 'returns', 'volatility']
    """

    def __init__(
        self,
        data: pd.DataFrame | None,
        symbol: str = "",
    ) -> None:
        """Initialize the Analysis instance.

        Parameters
        ----------
        data : pd.DataFrame | None
            OHLCV DataFrame with at least a 'close' column
        symbol : str, default=""
            Symbol identifier for the data

        Raises
        ------
        ValidationError
            If data is empty or missing required columns
        """
        logger.debug(
            "Initializing Analysis",
            symbol=symbol,
            rows=len(data) if data is not None else 0,
        )

        if data is None or data.empty:
            logger.error("Empty data provided")
            raise ValidationError(
                "Data cannot be empty",
                field="data",
                value="empty DataFrame",
                code=ErrorCode.INVALID_PARAMETER,
            )

        self._analyzer = Analyzer(data, symbol=symbol)
        self._symbol = symbol

        logger.info(
            "Analysis initialized",
            symbol=symbol,
            rows=len(data),
        )

    @property
    def data(self) -> pd.DataFrame:
        """Get the DataFrame with all added indicators.

        Returns
        -------
        pd.DataFrame
            Copy of the data with indicators added as columns
        """
        return self._analyzer.data

    @property
    def indicators(self) -> list[str]:
        """Get list of added indicator names.

        Returns
        -------
        list[str]
            List of indicator column names that have been added
        """
        return list(self._analyzer.indicators.keys())

    def add_sma(
        self,
        period: int = 20,
        column: str = "close",
    ) -> Self:
        """Add Simple Moving Average indicator.

        Parameters
        ----------
        period : int, default=20
            Window size for SMA calculation
        column : str, default="close"
            Column to calculate SMA on

        Returns
        -------
        Self
            Returns self for method chaining

        Raises
        ------
        ValidationError
            If period is invalid

        Examples
        --------
        >>> analysis.add_sma(period=20).add_sma(period=50).add_sma(period=200)
        """
        logger.debug("Adding SMA", period=period, column=column)

        if period < 1:
            logger.error("Invalid period", period=period)
            raise ValidationError(
                f"Period must be positive, got {period}",
                field="period",
                value=str(period),
                code=ErrorCode.INVALID_PARAMETER,
            )

        self._analyzer.add_sma(window=period)
        return self

    def add_ema(
        self,
        period: int = 20,
        column: str = "close",
    ) -> Self:
        """Add Exponential Moving Average indicator.

        Parameters
        ----------
        period : int, default=20
            Span for EMA calculation
        column : str, default="close"
            Column to calculate EMA on

        Returns
        -------
        Self
            Returns self for method chaining

        Raises
        ------
        ValidationError
            If period is invalid

        Examples
        --------
        >>> analysis.add_ema(period=12).add_ema(period=26)
        """
        logger.debug("Adding EMA", period=period, column=column)

        if period < 1:
            logger.error("Invalid period", period=period)
            raise ValidationError(
                f"Period must be positive, got {period}",
                field="period",
                value=str(period),
                code=ErrorCode.INVALID_PARAMETER,
            )

        self._analyzer.add_ema(window=period)
        return self

    def add_returns(
        self,
        column: str = "close",
    ) -> Self:
        """Add daily returns indicator.

        Parameters
        ----------
        column : str, default="close"
            Column to calculate returns on

        Returns
        -------
        Self
            Returns self for method chaining

        Examples
        --------
        >>> analysis.add_returns()
        """
        logger.debug("Adding returns", column=column)

        self._analyzer.add_returns()
        return self

    def add_volatility(
        self,
        period: int = 20,
        column: str = "close",
        annualize: bool = True,
    ) -> Self:
        """Add volatility indicator.

        Parameters
        ----------
        period : int, default=20
            Rolling window size for volatility calculation
        column : str, default="close"
            Column to calculate volatility on
        annualize : bool, default=True
            Whether to annualize volatility (multiply by sqrt(252))

        Returns
        -------
        Self
            Returns self for method chaining

        Raises
        ------
        ValidationError
            If period is invalid

        Examples
        --------
        >>> analysis.add_volatility(period=20)
        """
        logger.debug(
            "Adding volatility", period=period, column=column, annualize=annualize
        )

        if period < 2:
            logger.error("Invalid period", period=period)
            raise ValidationError(
                f"Period must be at least 2, got {period}",
                field="period",
                value=str(period),
                code=ErrorCode.INVALID_PARAMETER,
            )

        self._analyzer.add_volatility(window=period, annualize=annualize)
        return self

    def result(self) -> AnalysisResult:
        """Get the analysis result.

        Returns
        -------
        AnalysisResult
            Result object containing data, indicators, and statistics

        Examples
        --------
        >>> result = analysis.add_sma(20).add_returns().result()
        >>> result.symbol
        'AAPL'
        """
        return self._analyzer.result()

    @staticmethod
    def correlation(
        dataframes: list[pd.DataFrame],
        symbols: list[str] | None = None,
        column: str = "close",
        method: CorrelationMethod = "pearson",
    ) -> pd.DataFrame:
        """Calculate correlation matrix for multiple instruments.

        Parameters
        ----------
        dataframes : list[pd.DataFrame]
            List of DataFrames, one per instrument
        symbols : list[str] | None
            List of symbol names for column labels.
            If None, uses default labels (Symbol_0, Symbol_1, etc.)
        column : str, default="close"
            Column to use for correlation calculation
        method : {"pearson", "spearman", "kendall"}, default="pearson"
            Correlation method to use

        Returns
        -------
        pd.DataFrame
            Symmetric correlation matrix

        Raises
        ------
        ValidationError
            If fewer than 2 DataFrames provided
        AnalysisError
            If correlation calculation fails

        Examples
        --------
        >>> corr = Analysis.correlation(
        ...     [df_aapl, df_googl, df_msft],
        ...     symbols=["AAPL", "GOOGL", "MSFT"]
        ... )
        >>> corr.loc["AAPL", "GOOGL"]
        0.85
        """
        logger.info(
            "Calculating correlation matrix",
            num_dataframes=len(dataframes),
            symbols=symbols,
            method=method,
        )

        if len(dataframes) < 2:
            logger.error("Insufficient DataFrames", count=len(dataframes))
            raise ValidationError(
                f"At least 2 DataFrames required, got {len(dataframes)}",
                field="dataframes",
                value=str(len(dataframes)),
                code=ErrorCode.INVALID_PARAMETER,
            )

        if symbols is None:
            symbols = [f"Symbol_{i}" for i in range(len(dataframes))]
        elif len(symbols) != len(dataframes):
            logger.error(
                "Symbol count mismatch",
                symbols_count=len(symbols),
                df_count=len(dataframes),
            )
            raise ValidationError(
                f"Number of symbols ({len(symbols)}) must match "
                f"number of DataFrames ({len(dataframes)})",
                field="symbols",
                value=str(len(symbols)),
                code=ErrorCode.INVALID_PARAMETER,
            )

        # Extract the specified column from each DataFrame
        try:
            price_data: dict[str, pd.Series] = {}
            for i, df in enumerate(dataframes):
                col = column.lower()
                # Try to find the column (case-insensitive)
                actual_col = None
                for c in df.columns:
                    if c.lower() == col:
                        actual_col = c
                        break

                if actual_col is None:
                    logger.error(
                        "Column not found",
                        column=column,
                        available=list(df.columns),
                        symbol=symbols[i],
                    )
                    raise AnalysisError(
                        f"Column '{column}' not found in DataFrame for {symbols[i]}",
                        operation="correlation",
                        code=ErrorCode.INVALID_PARAMETER,
                    )

                price_data[symbols[i]] = cast("pd.Series", df[actual_col])

            # Create combined DataFrame
            combined = pd.DataFrame(price_data)

            # Calculate correlation matrix
            correlation_matrix = CorrelationAnalyzer.calculate_correlation_matrix(
                combined, method=method
            )

            logger.info(
                "Correlation matrix calculated",
                shape=correlation_matrix.shape,
                method=method,
            )

            return correlation_matrix

        except (ValidationError, AnalysisError):
            raise
        except Exception as e:
            logger.error(
                "Correlation calculation failed",
                error=str(e),
                error_type=type(e).__name__,
            )
            raise AnalysisError(
                f"Failed to calculate correlation: {e}",
                operation="correlation",
                code=ErrorCode.CALCULATION_ERROR,
                cause=e,
            ) from e

    @staticmethod
    def rolling_correlation(
        df1: pd.DataFrame,
        df2: pd.DataFrame,
        period: int = 20,
        column: str = "close",
    ) -> pd.Series:
        """Calculate rolling correlation between two instruments.

        Parameters
        ----------
        df1 : pd.DataFrame
            First instrument's DataFrame
        df2 : pd.DataFrame
            Second instrument's DataFrame
        period : int, default=20
            Rolling window size
        column : str, default="close"
            Column to use for correlation calculation

        Returns
        -------
        pd.Series
            Rolling correlation values

        Raises
        ------
        ValidationError
            If period is invalid
        AnalysisError
            If calculation fails

        Examples
        --------
        >>> rolling_corr = Analysis.rolling_correlation(df_aapl, df_spy, period=20)
        >>> rolling_corr.iloc[-1]
        0.92
        """
        logger.info(
            "Calculating rolling correlation",
            period=period,
            column=column,
        )

        if period < 2:
            logger.error("Invalid period", period=period)
            raise ValidationError(
                f"Period must be at least 2, got {period}",
                field="period",
                value=str(period),
                code=ErrorCode.INVALID_PARAMETER,
            )

        try:
            series1 = _find_column(df1, column, "rolling_correlation")
            series2 = _find_column(df2, column, "rolling_correlation")

            # Align series by index
            aligned = pd.concat([series1, series2], axis=1).dropna()
            if len(aligned) < period:
                logger.warning(
                    "Insufficient overlapping data",
                    available=len(aligned),
                    required=period,
                )

            result = CorrelationAnalyzer.calculate_rolling_correlation(
                aligned.iloc[:, 0],
                aligned.iloc[:, 1],
                window=period,
            )

            logger.info(
                "Rolling correlation calculated",
                period=period,
                valid_values=result.notna().sum(),
            )

            return result

        except (ValidationError, AnalysisError):
            raise
        except Exception as e:
            logger.error(
                "Rolling correlation calculation failed",
                error=str(e),
                error_type=type(e).__name__,
            )
            raise AnalysisError(
                f"Failed to calculate rolling correlation: {e}",
                operation="rolling_correlation",
                code=ErrorCode.CALCULATION_ERROR,
                cause=e,
            ) from e

    @staticmethod
    def beta(
        stock: pd.DataFrame,
        benchmark: pd.DataFrame,
        column: str = "close",
    ) -> float:
        """Calculate beta coefficient against a benchmark.

        Beta measures the sensitivity of an asset's returns to benchmark returns.
        - Beta > 1: Higher volatility than benchmark
        - Beta < 1: Lower volatility than benchmark
        - Beta = 1: Same volatility as benchmark

        Parameters
        ----------
        stock : pd.DataFrame
            Stock DataFrame
        benchmark : pd.DataFrame
            Benchmark DataFrame (e.g., S&P 500)
        column : str, default="close"
            Column to use for calculation

        Returns
        -------
        float
            Beta coefficient

        Raises
        ------
        AnalysisError
            If calculation fails

        Examples
        --------
        >>> beta = Analysis.beta(df_aapl, df_spy)
        >>> beta
        1.15
        """
        logger.info("Calculating beta", column=column)

        try:
            stock_prices = _find_column(stock, column, "beta")
            benchmark_prices = _find_column(benchmark, column, "beta")

            # Calculate returns
            stock_returns = stock_prices.pct_change().dropna()
            benchmark_returns = benchmark_prices.pct_change().dropna()

            # Align returns by index
            aligned = pd.concat([stock_returns, benchmark_returns], axis=1).dropna()

            if len(aligned) < 2:
                logger.warning(
                    "Insufficient overlapping data for beta calculation",
                    available=len(aligned),
                )
                return float("nan")

            beta_value = CorrelationAnalyzer.calculate_beta(
                aligned.iloc[:, 0],
                aligned.iloc[:, 1],
            )

            logger.info("Beta calculated", beta=beta_value)

            return beta_value

        except AnalysisError:
            raise
        except Exception as e:
            logger.error(
                "Beta calculation failed",
                error=str(e),
                error_type=type(e).__name__,
            )
            raise AnalysisError(
                f"Failed to calculate beta: {e}",
                operation="beta",
                code=ErrorCode.CALCULATION_ERROR,
                cause=e,
            ) from e


class MarketPerformanceAnalyzer:
    """
    株価データの取得、リターン計算、および累積リターンプロットを一元的に管理するクラス。
    主要なインデックス、セクター、個別株のパフォーマンスを分析・可視化する機能を提供する。
    データソースはyfinanceを使用し、curl_cffiでHTTPリクエストを行う。
    """

    def __init__(self):
        """
        MarketPerformanceAnalyzerクラスを初期化する。
        データの取得と基本リターンの計算を行う。
        """
        self.today = datetime.date.today()

        # --- 1. 定数（クラス属性）の定義 ---

        self.TICKERS_US_AND_SP500 = [
            # "^SPX",
            "^GSPC",
            "^SPXEW",
            "VUG",
            "VTV",
            "SPHQ",
            "^DJI",
            "^IXIC",
        ]
        # self.TICKERS_WORLD = [
        #     "^GDAXI",
        #     "^FTSE",
        #     "^FCHI",
        #     "^STOXX50E",
        #     "^AEX",
        #     "^N225",
        #     "^HSI",
        #     "000001.SS",
        #     "399001.SZ",
        # ]
        self.TICKERS_MAG7_AND_SOX = [
            "^SOX",
            "AAPL",
            "MSFT",
            "NVDA",
            "GOOGL",
            "AMZN",
            "TSLA",
            "META",
        ]
        self.SECTOR_MAP_EN = {
            "XLY": "Consumer Discretionary",
            "XLP": "Consumer Staples",
            "XLE": "Energy",
            "XLF": "Financials",
            "XLV": "Health Care",
            "XLI": "Industrials",
            "XLK": "Information Technology",
            "XLB": "Materials",
            "XLU": "Utilities",
            "XLC": "Communication Services",
            "XLRE": "Real Estate",
        }
        # 金属
        self.TICKERS_METAL = ["GLD", "SLV", "PPLT", "CPER", "PALL", "DBB"]
        # WTI原油（先物）
        self.TICKERS_OIL = ["CL=F"]
        # 市場センチメント
        self.TICKERS_MARKET = [
            "^VIX",  # VIX
            "DX-Y.NYB",  # ドル指数（DXY Futures）
        ]

        # 全てのティッカーを結合
        self.ALL_TICKERS = list(
            self.TICKERS_US_AND_SP500
            # + self.TICKERS_WORLD
            + self.TICKERS_MAG7_AND_SOX
            + list(self.SECTOR_MAP_EN.keys())
            + self.TICKERS_METAL
            + self.TICKERS_OIL
            + self.TICKERS_MARKET
        )

        # データ取得と前処理
        raw_df = self.yf_download_with_curl(self.ALL_TICKERS)
        self.price_data = (
            raw_df.loc[raw_df["variable"] == "Adj Close"]
            .pivot(index="Date", columns="Ticker", values="value")
            .astype(float)
        ).dropna(subset=list(self.SECTOR_MAP_EN.keys()))

        # 対数リターンの計算とセクター名へのリネーム
        self.log_return = np.log(self.price_data / self.price_data.shift(1))
        self.log_return.rename(columns=self.SECTOR_MAP_EN, inplace=True)

        # 累積リターンの推移を計算（プロット用）
        self.cum_return_plot = np.exp(self.log_return.cumsum()).fillna(1)

        # パフォーマンステーブルの事前計算
        self.performance_table = self._calculate_period_returns()

    # -------------------------------------------------------------------------------------
    def get_eps_historical_data(self, tickers_to_download: list[str]) -> pd.DataFrame:
        """
        指定された複数の銘柄の実績EPS（Reported EPS）のヒストリカルデータを取得する。
        年次（annual）と四半期（quarterly）のデータが含まれます。

        Parameters
        ----------
        tickers_to_download : list[str]
            ティッカーシンボルのリスト（例: ["AAPL", "MSFT"]）

        Returns
        -------
        pd.DataFrame
            全銘柄のEPSデータを結合したDataFrame。
            データ取得に失敗した銘柄は結果に含まれません。
        """
        all_eps_data: list[pd.DataFrame] = []

        for ticker in tickers_to_download:
            try:
                # yf.Tickerオブジェクトをセッション付きで取得
                session = curl_cffi.Session(impersonate="safari15_5")
                t = yf.Ticker(ticker, session=session)

                # --- 決算情報（earnings）を取得 ---
                # .earnings属性は、実績EPS（Reported EPS）と収益（Revenue）のデータフレームを保持
                earnings_data = t.earnings_history.assign(Ticker=ticker)
                earnings_data.index = pd.to_datetime(earnings_data.index)
                all_eps_data.append(earnings_data)

            except Exception as e:
                print(
                    f"エラー: 銘柄 {ticker} のEPSデータ取得中に例外が発生しました: {e}"
                )

        return pd.concat(all_eps_data)

    # -------------------------------------------------------------------------------------
    def yf_download_with_curl(
        self,
        tickers_to_download: list[str],
        period: str = "2y",
        interval: str = "1d",
    ) -> pd.DataFrame:
        """
        yfinanceのダウンロードをcurl_cffiで代替する関数。

        Parameters
        ----------
        tickers_to_download : list[str]
            ダウンロードするティッカーのリスト。
        period : str, default "2y"
            データ取得期間。
        interval : str, default "1d"
            データの間隔。

        Returns
        -------
        pd.DataFrame
            取得したデータフレーム。
        """
        session = curl_cffi.Session(impersonate="safari15_5")
        intra_day_intervals = ["1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h"]
        if not tickers_to_download:
            tickers_to_download = self.ALL_TICKERS
        if interval in intra_day_intervals:
            datetime_col_name = "Datetime"
            raw_df = yf.download(
                tickers=tickers_to_download,
                period=period,
                interval=interval,
                prepost=False,
                group_by="ticker",
            )
            return pd.DataFrame(raw_df)
        else:
            datetime_col_name = "Date"
            raw_df = yf.download(
                tickers=tickers_to_download,
                period=period,
                interval=interval,
                session=session,
                auto_adjust=False,
            )
            df = pd.DataFrame(raw_df).stack(future_stack=True).reset_index()
            df = pd.melt(
                df,
                id_vars=[datetime_col_name, "Ticker"],
                value_vars=df.columns.tolist()[2:],
                value_name="value",
                var_name="variable",
            )
            return df

    # -------------------------------------------------------------------------------------
    ## 期間リターン計算
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    def get_data_since_period_start(
        self, df: pd.DataFrame, date_column: str, period_type: str = "yearly"
    ) -> pd.DataFrame:
        """
        データフレームから、前年の最終日（YTD基準）または前月の最終日（MTD基準）以降のデータを取得する。

        Parameters
        ----------
        df : pd.DataFrame
            日付カラムを持つデータフレーム。
        date_column : str
            日付データが格納されているカラム名（datetime型を想定）。
        period_type : str, default "yearly"
            基準とする期間タイプ。'yearly' (YTD) または 'monthly' (MTD)。

        Returns
        -------
        pd.DataFrame
            基準日以降のデータ。
        """

        # 1. 日付カラムをインデックスに設定し、datetime型に変換
        if date_column not in df.index.names:
            df = df.set_index(date_column)

        # インデックスがdatetime型であることを確認
        df.index = pd.to_datetime(df.index)
        # 2. 基準日を決定するロジック
        start_date = None

        if period_type == "yearly":
            # --- YTD基準日（前年の最終日）の特定 ---

            previous_year = self.today.year - 1

            try:
                # 前年のデータに絞り込み、その中の最大の日付（最終営業日）を特定
                start_date = df.loc[str(previous_year)].index.max()
            except KeyError:
                print(
                    f"警告: {previous_year}年のデータが見つかりませんでした。全データを返します。"
                )
                return df

        elif period_type == "monthly":
            # --- MTD基準日（前月の最終日）の特定 ---

            # 現在の月から1日を引き、前月の任意の日付を取得
            # 例: 9/30 -> 9/29 (前月ではない)
            # 確実に前月の日付を取得するため、現在の月の初日 (self.today.replace(day=1)) から1日を引く
            last_day_of_previous_month = self.today.replace(day=1) - datetime.timedelta(
                days=1
            )

            # 前月の最終日データを探すために、前月のデータを取得
            previous_month_year = last_day_of_previous_month.year
            previous_month = last_day_of_previous_month.month

            try:
                # locで前月・前年のデータを抽出
                # 例: 2025年9月に実行した場合、2025-08のデータに絞り込み
                start_date = df.loc[
                    str(previous_month_year) + "-" + str(previous_month).zfill(2)
                ].index.max()
            except KeyError:
                # データが存在しない場合、直近のデータセットを返却（MTDの場合、現在月全体）
                return pd.DataFrame(
                    df.loc[str(self.today.year) + "-" + str(self.today.month).zfill(2)]
                )

        else:
            raise ValueError(
                "period_type は 'yearly' または 'monthly' のいずれかを指定してください。"
            )

        # 3. 基準日以降のデータを抽出
        if start_date is not None:
            # 抽出範囲は、「基準日」の行から「データフレームの終端」まで
            data_since_period_start = df.loc[start_date:]
            return data_since_period_start

        return df  # 念のため、何か問題があった場合は元のDFを返す

    # -------------------------------------------------------------------------------------
    def _get_last_tuesday_date(self) -> datetime.date:
        """
        先週火曜日の日付を datetime.date 型で取得する。

        Returns
        -------
        datetime.date
            先週火曜日の日付。
        """
        current_weekday = self.today.weekday()
        days_to_subtract = (current_weekday + 7) - 1  # (火曜日の曜日番号)
        return self.today - datetime.timedelta(days=days_to_subtract)

    # -------------------------------------------------------------------------------------
    def get_final_period_return(
        self, df_price: pd.DataFrame, return_type: str, period_name: str
    ) -> pd.DataFrame:
        """
        プライスのDataFrameを受け取り、最終的な累積リターン（%）を計算し整形する。

        Parameters
        ----------
        df_price : pd.DataFrame
            価格データフレーム。
        return_type : str
            リターンの種類 ("simple" または "log")。
        period_name : str
            期間の名前（カラム名に使用）。

        Returns
        -------
        pd.DataFrame
            計算されたリターンを含むデータフレーム。
        """
        result: pd.DataFrame
        if return_type == "simple":
            result = df_price.div(df_price.iloc[0]).sub(1).mul(100).iloc[-1].to_frame()
            result.columns = [period_name]
            result = result.rename(index=self.SECTOR_MAP_EN)
        elif return_type == "log":
            df_log_returns: pd.DataFrame = np.log(df_price / df_price.shift(1)).dropna()
            result = pd.DataFrame(
                np.exp(df_log_returns.sum())
                .sub(1)
                .mul(100)
                .rename(period_name)
                .to_frame()
            )
            result = result.rename(index=self.SECTOR_MAP_EN)
        else:
            raise ValueError(f"Unknown return_type: {return_type}")

        return result

    # -------------------------------------------------------------------------------------
    def _calculate_period_returns(self, return_type: str = "simple") -> pd.DataFrame:
        """
        YTD, MTD, Last Tuesday以降, 前日比のリターンを計算し、統合する。

        Parameters
        ----------
        return_type : str, default "simple"
            リターンの種類 ("simple" または "log")。

        Returns
        -------
        pd.DataFrame
            各期間のリターンを含むデータフレーム。
        """
        # Previous Day (前日比)
        # 最後の2日間の価格データをスライス
        price_prev_day = self.price_data.iloc[-2:]
        # 既存の計算メソッドを再利用してリターンを算出
        cum_return_prev_day = self.get_final_period_return(
            df_price=price_prev_day, return_type=return_type, period_name="prev_day"
        )

        # MTD
        price_mtd = self.get_data_since_period_start(
            self.price_data, date_column="Date", period_type="monthly"
        )
        cum_return_mtd = self.get_final_period_return(
            df_price=price_mtd, return_type=return_type, period_name="mtd"
        )

        # YTD
        price_ytd = self.get_data_since_period_start(
            self.price_data, date_column="Date", period_type="yearly"
        )
        cum_return_ytd = self.get_final_period_return(
            df_price=price_ytd, return_type=return_type, period_name="ytd"
        )

        # Last Tuesday
        last_tuesday_date = self._get_last_tuesday_date()
        price_last_tuesday = self.price_data.loc[
            self.price_data.index.date >= last_tuesday_date
        ]
        cum_return_last_Tuesday = self.get_final_period_return(
            df_price=price_last_tuesday,
            return_type=return_type,
            period_name="last_Tuesday",
        )

        # 統合、整形、ソート
        cum_return: pd.DataFrame = (
            cum_return_ytd.join(cum_return_mtd)
            .join(cum_return_last_Tuesday)
            .join(cum_return_prev_day)
            .round(2)
        )

        # カラムの順序を直感的な順（短期 -> 長期）に入れ替え
        cum_return = pd.DataFrame(
            cum_return[["prev_day", "last_Tuesday", "mtd", "ytd"]]
        )

        # ソートキーを週次リターン（last_Tuesday）に設定
        cum_return.sort_values("last_Tuesday", ascending=False, inplace=True)

        return pd.DataFrame(cum_return)

    # -------------------------------------------------------------------------------------
    def get_performance_groups(self) -> dict:
        """
        セクターやグループごとのパフォーマンスを辞書形式で返す。

        Returns
        -------
        dict
            各グループのパフォーマンスデータフレームを含む辞書。
        """
        cum_return = self.performance_table

        # 辞書値はセクター名（英語）のリストに変換
        sector_names = list(self.SECTOR_MAP_EN.values())

        return {
            "Mag7_SOX": cum_return.loc[
                cum_return.index.isin(self.TICKERS_MAG7_AND_SOX)
            ],
            # "World": cum_return.loc[cum_return.index.isin(self.TICKERS_WORLD)],
            "US_and_SP500_Indices": cum_return.loc[
                cum_return.index.isin(self.TICKERS_US_AND_SP500)
            ],
            "Sector": cum_return.loc[cum_return.index.isin(sector_names)],
            "Metals": cum_return.loc[cum_return.index.isin(self.TICKERS_METAL)],
            "Oil": cum_return.loc[cum_return.index.isin(self.TICKERS_OIL)],
            "Market_Sentiment": cum_return.loc[
                cum_return.index.isin(self.TICKERS_MARKET)
            ],
        }

    # -------------------------------------------------------------------------------------
    ## プロット関数
    # -------------------------------------------------------------------------------------

    def _plot_lines(self, tickers_or_sectors: list[str], title: str):
        """
        汎用の累積リターン折れ線グラフ描画メソッド。

        Parameters
        ----------
        tickers_or_sectors : list[str]
            プロットするティッカーまたはセクターのリスト。
        title : str
            グラフのタイトル。
        """

        # cum_return_plot の列名が、引数のリストに含まれているものに絞り込まれる
        plot_df = self.price_data[tickers_or_sectors]
        plot_df = plot_df.loc[f"{datetime.date.today().year}-01-01" :]
        # 累積リターン
        plot_df = plot_df.div(plot_df.iloc[0]).dropna(how="all")

        fig = go.Figure()
        for ticker in plot_df.columns:
            fig.add_trace(
                go.Scatter(
                    x=plot_df.index,
                    y=plot_df[ticker],
                    mode="lines",
                    name=(
                        self.SECTOR_MAP_EN[ticker]
                        if ticker.startswith("XL")
                        else ticker
                    ),
                    line=dict(width=0.8),
                ),
            )
        fig.update_layout(
            width=850,
            height=450,
            template="plotly_dark",
            title=title,
            hovermode="x",
            legend=dict(
                yanchor="top", y=-0.1, xanchor="center", x=0.5, orientation="h"
            ),
            margin=dict(l=30, r=30, t=50, b=30),
        )
        fig.show()

    # -------------------------------------------------------------------------------------
    def plot_sp500_indices(self):
        """
        S&P 500 インデックスのYTDパフォーマンスをプロットする。
        """
        self._plot_lines(self.TICKERS_US_AND_SP500, "S&P 500 Indices Performance YTD")

    # -------------------------------------------------------------------------------------
    def plot_world_indices(self):
        """
        全世界インデックスのYTDパフォーマンスをプロットする。
        """
        self._plot_lines(self.TICKERS_WORLD, "World Indices Performance YTD")

    # -------------------------------------------------------------------------------------
    def plot_mag7_sox(self):
        """
        Mag7とSOX指数のYTDパフォーマンスをプロットする。
        """
        self._plot_lines(
            self.TICKERS_MAG7_AND_SOX, "Mag7 and SOX Index Performance YTD"
        )

    # -------------------------------------------------------------------------------------
    def plot_sector_performance(self):
        """
        S&P 500 セクターのYTDパフォーマンスをプロットする。
        """
        # セクター名（英語名）をリストとして渡す
        sector_names = list(self.SECTOR_MAP_EN)
        self._plot_lines(sector_names, "S&P 500 Sector Performance YTD")

    # -------------------------------------------------------------------------------------
    def plot_metal(self):
        """
        金属のYTDパフォーマンスをプロットする。
        """
        self._plot_lines(self.TICKERS_METAL, "Metals Performance YTD")

    # -------------------------------------------------------------------------------------
    def plot_oil(self):
        """
        WTIのYTDパフォーマンスをプロットする。
        """
        self._plot_lines(self.TICKERS_OIL, "Oil Performance YTD")

    # -------------------------------------------------------------------------------------
    def plot_market_sentiment(self):
        """
        市場センチメントのYTDパフォーマンスをプロットする。
        """
        self._plot_lines(self.TICKERS_MARKET, "Market Sentiment Performance YTD")

    # -------------------------------------------------------------------------------------


__all__ = ["Analysis", "MarketPerformanceAnalyzer"]

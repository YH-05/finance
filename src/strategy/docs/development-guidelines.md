# 開発ガイドライン (Development Guidelines)

## 概要

strategy パッケージの開発に必要なコーディング規約、開発プロセス、拡張方法を定義します。

**技術スタック**:
- Python 3.12+（PEP 695 型ヒント）
- pandas/numpy/scipy（数値計算・統計）
- Plotly（可視化）
- pytest + Hypothesis（テスト）
- market_analysis パッケージ（データ取得）

## コーディング規約

### 命名規則

#### 変数・関数

```python
# ✅ 良い例
portfolio_returns = calculate_portfolio_returns(holdings, prices)
def calculate_sharpe_ratio(returns: pd.Series, risk_free_rate: float) -> float: ...

# ❌ 悪い例
ret = calc(h, p)
def sr(r: pd.Series, rf: float) -> float: ...
```

**原則**:
- 変数: snake_case、名詞または名詞句
- 関数: snake_case、動詞で始める
- 定数: UPPER_SNAKE_CASE
- Boolean: `is_`, `has_`, `should_` で始める

#### クラス・型

```python
# クラス: PascalCase、名詞
class RiskCalculator: ...
class MarketAnalysisProvider: ...

# Protocol: PascalCase
from typing import Protocol

class DataProvider(Protocol):
    def get_prices(self, tickers: list[str], start: str, end: str) -> pd.DataFrame: ...
    def get_ticker_info(self, ticker: str) -> TickerInfo: ...

# 型エイリアス: PascalCase（PEP 695）
type AssetClass = Literal["equity", "bond", "commodity", "real_estate", "cash", "other"]
type PresetPeriod = Literal["1y", "3y", "5y", "10y", "ytd", "max"]

# 結果型: PascalCase + Result サフィックス
class RiskMetricsResult: ...
class DriftResult: ...

# エラー: PascalCase + Error サフィックス
class StrategyError: ...
class DataProviderError: ...
```

#### ファイル名

| カテゴリ | 規則 | 例 |
|---------|------|-----|
| モジュール | snake_case | `portfolio.py`, `calculator.py` |
| テスト | `test_` + 対象 | `test_calculator.py` |
| プロバイダー | データソース名 | `market_analysis.py`, `mock.py` |

### コードフォーマット

**インデント**: 4スペース

**行の長さ**: 最大88文字（Ruff/Black標準）

**例**:
```python
def calculate_risk_metrics(
    returns: pd.Series,
    risk_free_rate: float = 0.0,
    benchmark_returns: pd.Series | None = None,
    confidence_levels: list[float] | None = None,
) -> RiskMetricsResult:
    """リスク指標を計算する."""
    ...
```

### コメント規約（NumPy形式）

```python
def calculate_sharpe_ratio(
    returns: pd.Series,
    risk_free_rate: float = 0.0,
    annualization_factor: int = 252,
) -> float:
    """シャープレシオを計算する.

    Parameters
    ----------
    returns : pd.Series
        日次リターンの時系列データ
    risk_free_rate : float, default=0.0
        年率リスクフリーレート
    annualization_factor : int, default=252
        年率換算係数（日次データの場合252）

    Returns
    -------
    float
        年率シャープレシオ

    Raises
    ------
    ValueError
        リターンデータが空の場合

    Examples
    --------
    >>> returns = pd.Series([0.01, -0.005, 0.02, -0.01, 0.015])
    >>> sharpe = calculate_sharpe_ratio(returns, risk_free_rate=0.02)
    >>> print(f"Sharpe Ratio: {sharpe:.2f}")
    Sharpe Ratio: 1.23
    """
    ...
```

### エラーハンドリング

**strategy パッケージのエラー階層**:

```python
from strategy.errors import (
    StrategyError,       # 基底エラー
    DataProviderError,   # データプロバイダーエラー
    InvalidTickerError,  # 無効なティッカー
    InsufficientDataError,  # データ不足
    ConfigurationError,  # 設定エラー
    ValidationError,     # 入力バリデーションエラー
)

# エラーハンドリングの例
try:
    prices = provider.get_prices(tickers, start, end)
except DataProviderError as e:
    logger.error(f"データ取得に失敗: {e.source} - {e}")
    raise
except InvalidTickerError as e:
    logger.warning(f"無効なティッカー: {e.ticker}")
    raise ValidationError(
        field="ticker",
        value=e.ticker,
        message=f"Invalid ticker symbol: '{e.ticker}'. Please check the symbol format.",
    ) from e
```

**エラーメッセージの原則**:

```python
# ✅ 良い例: 具体的で解決策を示す
raise ValidationError(
    field="weight",
    value=str(weight),
    message=f"Weight for '{ticker}' must be between 0.0 and 1.0, got {weight}",
)

# ❌ 悪い例: 曖昧
raise ValueError("Invalid weight")
```

### ロギング（必須）

```python
from finance.utils.logging_config import get_logger

logger = get_logger(__name__)

def calculate_portfolio_returns(
    holdings: list[Holding],
    prices: pd.DataFrame,
) -> pd.Series:
    logger.debug("ポートフォリオリターン計算開始", holdings_count=len(holdings))
    try:
        # ... 計算処理
        logger.info("ポートフォリオリターン計算完了", days=len(result))
        return result
    except Exception as e:
        logger.error("ポートフォリオリターン計算失敗", error=str(e), exc_info=True)
        raise
```

### 型ヒント（PEP 695）

```python
# ✅ 良い例: Python 3.12+ スタイル
def normalize_weights[T: (int, float)](weights: list[T]) -> list[float]:
    total = sum(weights)
    return [w / total for w in weights]

# ✅ 良い例: Protocol で抽象化
class DataProvider(Protocol):
    def get_prices(
        self,
        tickers: list[str],
        start: str,
        end: str,
    ) -> pd.DataFrame:
        ...

# ❌ 悪い例: 従来の TypeVar（Python 3.11以前）
from typing import TypeVar
T = TypeVar("T", int, float)
```

## 開発プロセス

### TDD 必須（Red-Green-Refactor）

strategy パッケージの開発は **TDD（テスト駆動開発）必須**です。

**TDD サイクル**:

```
Red → Green → Refactor → Red → ...
```

1. **Red**: 失敗するテストを先に書く
2. **Green**: テストが通る最小限の実装
3. **Refactor**: コードの品質を改善

**例: シャープレシオ計算の TDD**:

```python
# Step 1: Red - 失敗するテストを書く
# tests/strategy/unit/risk/test_calculator.py

class TestRiskCalculator:
    class TestSharpeRatio:
        def test_正のリターンで正のシャープレシオを返す(self):
            returns = pd.Series([0.01, 0.02, 0.01, 0.03, 0.01])
            calculator = RiskCalculator(returns, risk_free_rate=0.0)

            result = calculator.sharpe_ratio()

            assert result > 0

        def test_リスクフリーレートより低いリターンで負のシャープレシオを返す(self):
            returns = pd.Series([0.0001, 0.0002, 0.0001])
            calculator = RiskCalculator(returns, risk_free_rate=0.05)

            result = calculator.sharpe_ratio()

            assert result < 0

# Step 2: Green - テストが通る最小限の実装
# src/strategy/risk/calculator.py

class RiskCalculator:
    def __init__(
        self,
        returns: pd.Series,
        risk_free_rate: float = 0.0,
        annualization_factor: int = 252,
    ) -> None:
        self._returns = returns
        self._risk_free_rate = risk_free_rate
        self._annualization_factor = annualization_factor

    def sharpe_ratio(self) -> float:
        excess_returns = self._returns - self._risk_free_rate / self._annualization_factor
        volatility = excess_returns.std() * np.sqrt(self._annualization_factor)
        mean_return = excess_returns.mean() * self._annualization_factor
        return mean_return / volatility if volatility > 0 else 0.0

# Step 3: Refactor - コードの品質を改善
# - 共通計算をプライベートメソッドに抽出
# - ドキュメントを追加
# - エラーハンドリングを追加
```

### プロパティベーステスト（Hypothesis）

**リスク指標の不変条件をテスト**:

```python
# tests/strategy/property/test_risk_calculator.py
from hypothesis import given, strategies as st

@given(st.lists(st.floats(min_value=-0.1, max_value=0.1), min_size=10))
def test_max_drawdown_bounds(returns):
    """最大ドローダウンが -1.0 から 0.0 の範囲内であることを確認."""
    returns_series = pd.Series(returns)
    calculator = RiskCalculator(returns_series)

    mdd = calculator.max_drawdown()

    assert -1.0 <= mdd <= 0.0

@given(st.lists(st.floats(min_value=0.01, max_value=1.0), min_size=2, max_size=10))
def test_weights_normalize_to_one(weights):
    """正規化後の比率合計が1.0になることを確認."""
    normalized = normalize_weights(weights)
    assert abs(sum(normalized) - 1.0) < 1e-10

@given(st.floats(min_value=0.8, max_value=0.99))
def test_var_95_less_than_var_99(confidence):
    """高い信頼水準ほど VaR の絶対値が大きいことを確認."""
    returns = pd.Series(np.random.normal(0, 0.01, 1000))
    calculator = RiskCalculator(returns)

    var_low = calculator.var(confidence)
    var_high = calculator.var(min(confidence + 0.04, 0.99))

    # より高い信頼水準の VaR はより負の値
    assert var_high <= var_low
```

### ブランチ戦略

```
main
  └─ develop
      ├─ feature/portfolio-class
      ├─ feature/risk-calculator
      ├─ feature/drift-detector
      ├─ fix/sharpe-ratio-calculation
      └─ refactor/provider-interface
```

**ブランチ命名**:
- `feature/[機能名]`: 新機能開発
- `fix/[修正内容]`: バグ修正
- `refactor/[対象]`: リファクタリング
- `docs/[対象]`: ドキュメント
- `test/[対象]`: テスト追加

### コミットメッセージ規約

**フォーマット**:
```
<type>(<scope>): <subject>

<body>

<footer>
```

**Type**:
- `feat`: 新機能
- `fix`: バグ修正
- `docs`: ドキュメント
- `style`: コードフォーマット
- `refactor`: リファクタリング
- `test`: テスト追加・修正
- `chore`: ビルド、補助ツール等

**例**:
```
feat(risk): シャープレシオ計算機能を追加

RiskCalculatorクラスにシャープレシオ計算メソッドを実装しました。
- 年率換算係数をパラメータ化
- リスクフリーレートを考慮
- ゼロボラティリティ時のエッジケース対応

Closes #45
```

### PRプロセス

**作成前のチェック**:
- [ ] 全てのテストがパス（`make test`）
- [ ] Lintエラーがない（`make lint`）
- [ ] 型チェックがパス（`make typecheck`）
- [ ] カバレッジが80%以上

**PRテンプレート**:
```markdown
## 概要
- <変更点1>
- <変更点2>

## テストプラン
- [ ] make check-all が成功することを確認
- [ ] 新規テストケースを追加
- [ ] プロパティテストで境界値を検証
```

## 拡張ガイドライン

### DataProvider プロトコルに準拠したプロバイダーの追加方法

新しいデータプロバイダー（例: Factset）を追加する手順:

**Step 1: Protocol の確認**

```python
# src/strategy/providers/protocol.py
class DataProvider(Protocol):
    """データプロバイダーの抽象インターフェース."""

    def get_prices(
        self,
        tickers: list[str],
        start: str,
        end: str,
    ) -> pd.DataFrame:
        """指定期間の価格データ（OHLCV）を取得.

        Returns
        -------
        pd.DataFrame
            MultiIndex DataFrame（columns: ticker, rows: date）
            各ティッカーに対して open, high, low, close, volume を含む
        """
        ...

    def get_ticker_info(self, ticker: str) -> TickerInfo:
        """ティッカーの情報（セクター、資産クラス等）を取得."""
        ...

    def get_ticker_infos(self, tickers: list[str]) -> dict[str, TickerInfo]:
        """複数ティッカーの情報を一括取得."""
        ...
```

**Step 2: テストを先に書く（TDD）**

```python
# tests/strategy/unit/providers/test_factset.py
import pytest
from strategy.providers.factset import FactsetProvider
from strategy.types import TickerInfo

class TestFactsetProvider:
    class TestGetPrices:
        def test_正常なティッカーで価格データを取得できる(self, mock_factset_api):
            provider = FactsetProvider(api_key="test_key")
            provider._client = mock_factset_api

            result = provider.get_prices(["AAPL", "GOOGL"], "2024-01-01", "2024-12-31")

            assert isinstance(result, pd.DataFrame)
            assert "AAPL" in result.columns.get_level_values(0)
            assert "close" in result.columns.get_level_values(1)

        def test_無効なティッカーでInvalidTickerErrorを送出する(self, mock_factset_api):
            provider = FactsetProvider(api_key="test_key")
            mock_factset_api.get_prices.side_effect = InvalidTickerError("INVALID")

            with pytest.raises(InvalidTickerError):
                provider.get_prices(["INVALID"], "2024-01-01", "2024-12-31")

    class TestGetTickerInfo:
        def test_ティッカー情報を正しく変換する(self, mock_factset_api):
            provider = FactsetProvider(api_key="test_key")

            result = provider.get_ticker_info("AAPL")

            assert isinstance(result, TickerInfo)
            assert result.ticker == "AAPL"
            assert result.asset_class in ["equity", "bond", "commodity"]
```

**Step 3: プロバイダーを実装**

```python
# src/strategy/providers/factset.py
"""Factset API 経由のデータプロバイダー."""

import pandas as pd
from finance.utils.logging_config import get_logger
from strategy.errors import DataProviderError, InvalidTickerError
from strategy.types import TickerInfo

logger = get_logger(__name__)


class FactsetProvider:
    """Factset API 経由のデータプロバイダー.

    Parameters
    ----------
    api_key : str
        Factset API キー
    endpoint : str | None, optional
        API エンドポイント（デフォルト: 公式エンドポイント）

    Examples
    --------
    >>> provider = FactsetProvider(api_key="your_api_key")
    >>> prices = provider.get_prices(["AAPL", "GOOGL"], "2024-01-01", "2024-12-31")
    >>> print(prices.columns)
    MultiIndex([('AAPL', 'open'), ('AAPL', 'high'), ...])
    """

    def __init__(
        self,
        api_key: str,
        endpoint: str | None = None,
    ) -> None:
        self._api_key = api_key
        self._endpoint = endpoint or "https://api.factset.com"
        logger.debug("FactsetProvider 初期化", endpoint=self._endpoint)

    def get_prices(
        self,
        tickers: list[str],
        start: str,
        end: str,
    ) -> pd.DataFrame:
        """DataProvider プロトコルに準拠した価格データ取得."""
        logger.debug("価格データ取得開始", tickers=tickers, start=start, end=end)
        try:
            # Factset API 呼び出し
            raw_data = self._fetch_prices(tickers, start, end)
            result = self._transform_to_dataframe(raw_data)
            logger.info("価格データ取得完了", tickers_count=len(tickers))
            return result
        except Exception as e:
            logger.error("価格データ取得失敗", error=str(e))
            raise DataProviderError(source="Factset", message=str(e)) from e

    def get_ticker_info(self, ticker: str) -> TickerInfo:
        """DataProvider プロトコルに準拠したティッカー情報取得."""
        logger.debug("ティッカー情報取得", ticker=ticker)
        # 実装...

    def get_ticker_infos(self, tickers: list[str]) -> dict[str, TickerInfo]:
        """複数ティッカーの情報を一括取得."""
        return {ticker: self.get_ticker_info(ticker) for ticker in tickers}

    def _fetch_prices(self, tickers: list[str], start: str, end: str) -> dict:
        """Factset API から価格データを取得（内部メソッド）."""
        # API 呼び出しの実装
        ...

    def _transform_to_dataframe(self, raw_data: dict) -> pd.DataFrame:
        """生データを DataFrame に変換（内部メソッド）."""
        # 変換ロジックの実装
        ...
```

**Step 4: エクスポートを追加**

```python
# src/strategy/providers/__init__.py
from strategy.providers.protocol import DataProvider
from strategy.providers.market_analysis import MarketAnalysisProvider
from strategy.providers.mock import MockProvider
from strategy.providers.factset import FactsetProvider  # 追加

__all__ = [
    "DataProvider",
    "MarketAnalysisProvider",
    "MockProvider",
    "FactsetProvider",  # 追加
]

# src/strategy/__init__.py の __all__ にも追加
```

### リスク指標の追加方法

新しいリスク指標（例: カルマーレシオ）を追加する手順:

**Step 1: テストを先に書く（TDD）**

```python
# tests/strategy/unit/risk/test_calculator.py

class TestRiskCalculator:
    class TestCalmarRatio:
        def test_正のリターンと負のドローダウンで正のカルマーレシオを返す(self):
            # 上昇トレンドのリターン
            returns = pd.Series([0.02, 0.01, 0.03, -0.01, 0.02, 0.01])
            calculator = RiskCalculator(returns)

            result = calculator.calmar_ratio()

            assert result > 0

        def test_ゼロドローダウンで無限大を返す(self):
            # 常に正のリターン（ドローダウンなし）
            returns = pd.Series([0.01, 0.01, 0.01, 0.01])
            calculator = RiskCalculator(returns)

            result = calculator.calmar_ratio()

            assert result == float('inf')

        def test_負のリターンとドローダウンで負のカルマーレシオを返す(self):
            returns = pd.Series([-0.02, -0.01, -0.03, -0.01])
            calculator = RiskCalculator(returns)

            result = calculator.calmar_ratio()

            assert result < 0
```

**Step 2: プロパティテストを追加**

```python
# tests/strategy/property/test_risk_calculator.py

@given(st.lists(st.floats(min_value=-0.1, max_value=0.1), min_size=10))
def test_calmar_ratio_sign_consistency(returns):
    """年率リターンと同じ符号を持つことを確認（ゼロドローダウン除く）."""
    returns_series = pd.Series(returns)
    calculator = RiskCalculator(returns_series)

    calmar = calculator.calmar_ratio()
    annualized_return = returns_series.mean() * 252

    # ゼロドローダウンの場合は符号一致を検証しない
    mdd = calculator.max_drawdown()
    if mdd != 0:
        assert (calmar >= 0) == (annualized_return >= 0) or calmar == 0
```

**Step 3: 実装**

```python
# src/strategy/risk/calculator.py

class RiskCalculator:
    # ... 既存のメソッド

    def calmar_ratio(self) -> float:
        """カルマーレシオを計算する.

        年率リターンを最大ドローダウンで割った比率。
        リスク調整後のリターンを評価するための指標。

        Returns
        -------
        float
            カルマーレシオ
            - 正: リスクに見合うリターンがある
            - 負: リスクに見合うリターンがない
            - inf: ドローダウンがゼロ（常に上昇）

        Examples
        --------
        >>> returns = pd.Series([0.02, 0.01, -0.01, 0.03])
        >>> calculator = RiskCalculator(returns)
        >>> calmar = calculator.calmar_ratio()
        >>> print(f"Calmar Ratio: {calmar:.2f}")
        Calmar Ratio: 2.15
        """
        annualized_return = self._calculate_annualized_return()
        mdd = self.max_drawdown()

        if mdd == 0:
            return float('inf') if annualized_return > 0 else 0.0

        return annualized_return / abs(mdd)

    def _calculate_annualized_return(self) -> float:
        """年率リターンを計算（内部メソッド）."""
        return self._returns.mean() * self._annualization_factor
```

**Step 4: RiskMetricsResult に追加**

```python
# src/strategy/risk/metrics.py

@dataclass
class RiskMetricsResult:
    """リスク指標の計算結果."""
    volatility: float
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    var_95: float
    var_99: float
    beta: float | None
    treynor_ratio: float | None
    information_ratio: float | None
    calmar_ratio: float  # 追加
    annualized_return: float
    cumulative_return: float
    calculated_at: datetime
    period_start: date
    period_end: date
```

### market_analysis パッケージとの連携ガイドライン

**連携の原則**:

1. **MarketAnalysisProvider を介してアクセス**: 直接 market_analysis を呼ばない
2. **キャッシュを活用**: market_analysis の SQLiteCache を利用
3. **エラーを適切に変換**: market_analysis のエラーを strategy のエラーにマッピング

```python
# src/strategy/providers/market_analysis.py
"""market_analysis パッケージを使用するデータプロバイダー."""

import pandas as pd
from market_analysis.core import YFinanceFetcher
from market_analysis.utils import CacheConfig
from finance.utils.logging_config import get_logger
from strategy.errors import DataProviderError, InvalidTickerError
from strategy.types import TickerInfo

logger = get_logger(__name__)


class MarketAnalysisProvider:
    """market_analysis パッケージを使用するデータプロバイダー.

    Parameters
    ----------
    cache_config : CacheConfig | None, optional
        キャッシュ設定（デフォルト: 標準設定）
    use_cache : bool, default=True
        キャッシュを使用するかどうか

    Examples
    --------
    >>> provider = MarketAnalysisProvider()
    >>> prices = provider.get_prices(["VOO", "BND"], "2024-01-01", "2024-12-31")
    >>> print(prices.head())
    """

    def __init__(
        self,
        cache_config: CacheConfig | None = None,
        use_cache: bool = True,
    ) -> None:
        self._cache_config = cache_config or CacheConfig()
        self._use_cache = use_cache
        self._yfinance_fetcher = YFinanceFetcher(
            cache_config=self._cache_config,
        )
        logger.debug("MarketAnalysisProvider 初期化", use_cache=use_cache)

    def get_prices(
        self,
        tickers: list[str],
        start: str,
        end: str,
    ) -> pd.DataFrame:
        """DataProvider プロトコルに準拠した価格データ取得.

        Parameters
        ----------
        tickers : list[str]
            取得するティッカーシンボルのリスト
        start : str
            開始日（YYYY-MM-DD形式）
        end : str
            終了日（YYYY-MM-DD形式）

        Returns
        -------
        pd.DataFrame
            MultiIndex DataFrame（columns: ticker, rows: date）

        Raises
        ------
        DataProviderError
            データ取得に失敗した場合
        InvalidTickerError
            無効なティッカーの場合
        """
        logger.debug("価格データ取得開始", tickers=tickers, start=start, end=end)
        try:
            results = self._yfinance_fetcher.fetch_multiple(
                tickers=tickers,
                start=start,
                end=end,
                use_cache=self._use_cache,
            )
            df = self._results_to_dataframe(results)
            logger.info("価格データ取得完了", tickers_count=len(tickers), days=len(df))
            return df
        except Exception as e:
            logger.error("価格データ取得失敗", error=str(e), tickers=tickers)
            if "Invalid ticker" in str(e):
                raise InvalidTickerError(ticker=str(tickers)) from e
            raise DataProviderError(
                source="market_analysis",
                message=f"Failed to fetch prices: {e}",
            ) from e

    def get_ticker_info(self, ticker: str) -> TickerInfo:
        """ティッカーの情報を取得.

        Parameters
        ----------
        ticker : str
            ティッカーシンボル

        Returns
        -------
        TickerInfo
            ティッカーの詳細情報
        """
        logger.debug("ティッカー情報取得", ticker=ticker)
        try:
            info = self._yfinance_fetcher.fetch_ticker_info(ticker)
            return self._convert_to_ticker_info(ticker, info)
        except Exception as e:
            logger.error("ティッカー情報取得失敗", ticker=ticker, error=str(e))
            raise InvalidTickerError(ticker=ticker) from e

    def get_ticker_infos(self, tickers: list[str]) -> dict[str, TickerInfo]:
        """複数ティッカーの情報を一括取得."""
        return {ticker: self.get_ticker_info(ticker) for ticker in tickers}

    def _results_to_dataframe(self, results: list) -> pd.DataFrame:
        """取得結果を MultiIndex DataFrame に変換."""
        # 変換ロジック
        ...

    def _convert_to_ticker_info(self, ticker: str, info: dict) -> TickerInfo:
        """API レスポンスを TickerInfo に変換."""
        return TickerInfo(
            ticker=ticker,
            name=info.get("shortName", ticker),
            sector=info.get("sector"),
            industry=info.get("industry"),
            asset_class=self._determine_asset_class(info),
        )

    def _determine_asset_class(self, info: dict) -> str:
        """ティッカー情報から資産クラスを判定."""
        quote_type = info.get("quoteType", "").lower()
        if quote_type == "equity":
            return "equity"
        elif quote_type == "etf":
            return info.get("category", "equity").lower()
        # ... その他の判定
        return "other"
```

## テスト戦略

### テストの種類と配置

| テスト種別 | 配置先 | 対象 | カバレッジ目標 |
|-----------|--------|------|--------------|
| ユニットテスト | `tests/strategy/unit/` | 個別関数・クラス | 80% |
| プロパティテスト | `tests/strategy/property/` | 不変条件・境界値 | 主要関数 |
| 統合テスト | `tests/strategy/integration/` | 複数コンポーネント連携 | 主要シナリオ |

### テスト命名規則

```python
# ✅ 良い例（日本語）
def test_正のリターンで正のシャープレシオを返す(): ...
def test_無効なティッカーでInvalidTickerErrorを送出する(): ...
def test_キャッシュヒット時に高速に取得できる(): ...

# ✅ 良い例（英語）
def test_sharpe_ratio_positive_with_positive_returns(): ...
def test_raises_invalid_ticker_error_for_invalid_symbol(): ...

# ❌ 悪い例
def test1(): ...
def test_works(): ...
```

### モック・フィクスチャの使用

```python
# tests/strategy/conftest.py
import pytest
import pandas as pd
from unittest.mock import Mock
from strategy.providers.protocol import DataProvider
from strategy.types import TickerInfo

@pytest.fixture
def sample_prices() -> pd.DataFrame:
    """テスト用の価格データ."""
    dates = pd.date_range("2024-01-01", periods=100, freq="D")
    return pd.DataFrame(
        {
            ("VOO", "close"): 400 + np.random.randn(100).cumsum(),
            ("BND", "close"): 80 + np.random.randn(100).cumsum() * 0.1,
        },
        index=dates,
    )

@pytest.fixture
def sample_ticker_infos() -> dict[str, TickerInfo]:
    """テスト用のティッカー情報."""
    return {
        "VOO": TickerInfo(
            ticker="VOO",
            name="Vanguard S&P 500 ETF",
            sector="Financial Services",
            asset_class="equity",
        ),
        "BND": TickerInfo(
            ticker="BND",
            name="Vanguard Total Bond Market ETF",
            sector="Fixed Income",
            asset_class="bond",
        ),
    }

@pytest.fixture
def mock_provider(sample_prices, sample_ticker_infos) -> Mock:
    """テスト用のモックプロバイダー."""
    provider = Mock(spec=DataProvider)
    provider.get_prices.return_value = sample_prices
    provider.get_ticker_infos.return_value = sample_ticker_infos
    return provider
```

## コードレビュー基準

### strategy パッケージ固有のチェックポイント

**リスク計算の正確性**:
- [ ] 年率換算係数が正しく使用されているか
- [ ] エッジケース（ゼロボラティリティ、空データ）が処理されているか
- [ ] 数値精度の問題がないか（浮動小数点エラー）

**パフォーマンス**:
- [ ] ベクトル化計算が使用されているか（ループ禁止）
- [ ] 不要なデータコピーがないか
- [ ] キャッシュが適切に活用されているか

**データプロバイダー連携**:
- [ ] DataProvider プロトコルに準拠しているか
- [ ] エラーが適切に変換されているか
- [ ] ロギングが実装されているか

### ベクトル化計算の確認

```python
# ✅ 良い例: ベクトル化
def calculate_portfolio_returns(
    prices: pd.DataFrame,
    weights: dict[str, float],
) -> pd.Series:
    returns = prices.pct_change()
    weight_series = pd.Series(weights)
    return (returns * weight_series).sum(axis=1)

# ❌ 悪い例: ループ
def calculate_portfolio_returns(
    prices: pd.DataFrame,
    weights: dict[str, float],
) -> pd.Series:
    result = pd.Series(0.0, index=prices.index)
    for ticker, weight in weights.items():
        for i in range(1, len(prices)):
            result.iloc[i] += weight * (
                prices[ticker].iloc[i] / prices[ticker].iloc[i-1] - 1
            )
    return result
```

## 開発環境セットアップ

### 必要なツール

| ツール | バージョン | 用途 |
|--------|-----------|------|
| Python | 3.12+ | ランタイム |
| uv | latest | パッケージ管理 |
| Ruff | latest | リント・フォーマット |
| pyright | latest | 型チェック |

### セットアップ手順

```bash
# 1. リポジトリのクローン
git clone [URL]
cd finance

# 2. 依存関係のインストール
uv sync --all-extras

# 3. 品質チェック
make check-all

# 4. テスト実行
make test

# 5. 特定のテストを実行
uv run pytest tests/strategy/unit/ -v
```

### 推奨開発ツール

- **VS Code + Pylance**: 型チェック、オートコンプリート
- **Ruff**: リント・フォーマット（`make format && make lint`）
- **pytest**: テスト実行（`make test`）

## チェックリスト

### 新機能追加時

- [ ] TDD サイクルに従っている（テスト先行）
- [ ] プロパティテストで境界値を検証
- [ ] NumPy 形式の Docstring を記述
- [ ] ロギングを実装
- [ ] エラーハンドリングを実装
- [ ] `make check-all` が成功

### プロバイダー追加時

- [ ] DataProvider プロトコルに準拠
- [ ] テストを先に作成（TDD）
- [ ] エラーを strategy のエラーに変換
- [ ] キャッシュ戦略を検討
- [ ] `providers/__init__.py` にエクスポートを追加

### リスク指標追加時

- [ ] テストを先に作成（TDD）
- [ ] プロパティテストで不変条件を検証
- [ ] RiskMetricsResult に追加
- [ ] Docstring に Examples を含める
- [ ] ベクトル化計算を使用

### コードレビュー提出時

- [ ] `make check-all` が成功
- [ ] テストカバレッジ 80% 以上
- [ ] ベクトル化計算を使用（ループ禁止）
- [ ] ログメッセージが適切
- [ ] エラーメッセージが具体的

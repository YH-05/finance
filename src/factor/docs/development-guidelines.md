# 開発ガイドライン (Development Guidelines)

## 概要

factor パッケージの開発における統一されたコーディング規約と開発プロセスを定義します。
このガイドラインはアーキテクチャ設計書とリポジトリ構造定義書に基づいています。

## コーディング規約

### 命名規則

#### 変数・関数

```python
# 変数: snake_case、名詞または名詞句
factor_values = compute_momentum(prices)
ic_series = analyzer.compute_ic_series(factor_values, returns)
normalized_data = normalizer.zscore(raw_values)

# 関数: snake_case、動詞で始める
def compute_factor_values(prices: pd.DataFrame, lookback: int) -> pd.DataFrame: ...
def validate_inputs(universe: list[str], start_date: datetime) -> None: ...
def fetch_price_data(symbols: list[str]) -> pd.DataFrame: ...

# Boolean: is_, has_, should_, can_ で始める
is_valid = True
has_cache = cache.is_valid(key)
should_normalize = True
```

#### クラス・型

```python
# クラス: PascalCase
# ファクター: XXXFactor
class MomentumFactor(Factor): ...
class ReversalFactor(Factor): ...
class CompositeValueFactor(Factor): ...

# プロバイダー: XXXProvider
class YFinanceProvider: ...
class FREDProvider: ...  # Post-MVI

# アナライザー: XXXAnalyzer
class ICAnalyzer: ...
class QuantileAnalyzer: ...

# 結果型: XXXResult
class ICResult: ...
class QuantileResult: ...

# エラー: XXXError
class FactorError(Exception): ...
class DataFetchError(FactorError): ...
class ValidationError(FactorError): ...

# Protocol: XXXProtocol または XXX（Protocol継承）
from typing import Protocol

class DataProvider(Protocol):
    def get_prices(self, symbols: list[str], ...) -> pd.DataFrame: ...
```

#### 定数

```python
# UPPER_SNAKE_CASE
DEFAULT_LOOKBACK_PERIOD = 252  # 営業日1年
MAX_RETRY_COUNT = 3
CACHE_TTL_HOURS = 24

# ファクターカテゴリ Enum
from enum import Enum

class FactorCategory(Enum):
    PRICE = "price"
    VALUE = "value"
    QUALITY = "quality"
    SIZE = "size"
    MACRO = "macro"  # Post-MVI
```

#### ファイル名

| カテゴリ | 規則 | 例 |
|---------|------|-----|
| ファクター | snake_case | `momentum.py`, `volatility.py`, `value.py` |
| プロバイダー | snake_case (データソース名) | `yfinance.py`, `fred.py` |
| アナライザー | snake_case + `_analyzer` | `ic_analyzer.py`, `quantile_analyzer.py` |
| テスト | `test_` + 対象ファイル名 | `test_momentum.py`, `test_ic_analyzer.py` |

### コードフォーマット

**インデント**: 4スペース

**行の長さ**: 最大88文字（Ruff/Black標準）

**例**:
```python
def compute_momentum(
    prices: pd.DataFrame,
    lookback: int = 252,
    skip_recent: int = 21,
) -> pd.DataFrame:
    """モメンタムファクターを計算する。"""
    return prices / prices.shift(lookback + skip_recent) - 1
```

### コメント規約（NumPy形式）

```python
def compute_ic_series(
    factor_values: pd.DataFrame,
    forward_returns: pd.DataFrame,
    method: str = "spearman",
) -> pd.Series:
    """ファクター値とフォワードリターンのICを時系列で計算する。

    Parameters
    ----------
    factor_values : pd.DataFrame
        ファクター値 (index: Date, columns: symbols)
    forward_returns : pd.DataFrame
        フォワードリターン (index: Date, columns: symbols)
    method : str, default="spearman"
        相関係数の計算方法 ("spearman" | "pearson")

    Returns
    -------
    pd.Series
        時系列IC (index: Date)

    Raises
    ------
    ValidationError
        factor_valuesとforward_returnsの形状が一致しない場合
    ComputationError
        IC計算に失敗した場合

    Examples
    --------
    >>> ic_series = compute_ic_series(factor_values, forward_returns)
    >>> print(f"Mean IC: {ic_series.mean():.4f}")
    Mean IC: 0.0523
    """
    ...
```

### 型ヒント

**Python 3.12+ スタイル（PEP 695）**:

```python
# 組み込み型を直接使用
def get_prices(
    symbols: list[str],
    start_date: datetime | str,
    end_date: datetime | str,
) -> pd.DataFrame: ...

# ジェネリック型（PEP 695）
def first[T](items: list[T]) -> T | None:
    return items[0] if items else None

# dataclass
from dataclasses import dataclass

@dataclass
class FactorValue:
    data: pd.DataFrame
    factor_name: str
    computed_at: datetime
    universe: list[str]
    parameters: dict[str, Any]

# 型エイリアス
type FactorMatrix = pd.DataFrame  # index: Date, columns: symbols
type ReturnSeries = pd.Series     # index: Date
```

### エラーハンドリング

#### エラー階層

```python
# 基底エラー
class FactorError(Exception):
    """factor パッケージの基底エラー"""

# データ取得エラー
class DataFetchError(FactorError):
    """データ取得に失敗した場合のエラー"""

    def __init__(self, symbols: list[str], message: str) -> None:
        super().__init__(message)
        self.symbols = symbols
        self.message = message

# バリデーションエラー
class ValidationError(FactorError):
    """入力バリデーションエラー"""

    def __init__(self, field: str, value: object, message: str) -> None:
        super().__init__(message)
        self.field = field
        self.value = value

# 計算エラー
class ComputationError(FactorError):
    """ファクター計算エラー"""

    def __init__(self, factor_name: str, message: str) -> None:
        super().__init__(message)
        self.factor_name = factor_name

# データ不足エラー
class InsufficientDataError(FactorError):
    """データ不足エラー"""

    def __init__(self, required: int, available: int, message: str) -> None:
        super().__init__(message)
        self.required = required
        self.available = available
```

#### エラーメッセージの書き方

```python
# 具体的で解決策を示す
raise ValidationError(
    field="lookback",
    value=lookback,
    message=f"lookback must be positive, got {lookback}",
)

raise InsufficientDataError(
    required=252,
    available=100,
    message=f"Momentum calculation requires {252} data points, but only {100} available",
)

raise DataFetchError(
    symbols=["INVALID"],
    message="Failed to fetch data for ['INVALID']: Symbol not found",
)

# 悪い例: 曖昧
raise ValueError("Invalid input")  # 何が不正かわからない
```

#### エラーハンドリングパターン

```python
async def compute_factor(
    self,
    provider: DataProvider,
    universe: list[str],
    start_date: datetime,
    end_date: datetime,
) -> pd.DataFrame:
    try:
        # 入力検証
        self.validate_inputs(universe, start_date, end_date)

        # データ取得
        prices = await provider.get_prices(universe, start_date, end_date)

        # 計算
        return self._compute_impl(prices)

    except ValidationError:
        # 予期されるエラー: そのまま再送出
        raise
    except DataFetchError as e:
        # データ取得エラー: ログ記録して再送出
        logger.error(f"Data fetch failed: {e.message}", symbols=e.symbols)
        raise
    except Exception as e:
        # 予期しないエラー: ラップして再送出
        raise ComputationError(
            factor_name=self.name,
            message=f"Unexpected error: {e}",
        ) from e
```

## Factor クラスの実装パターン

### 基底クラスの構造

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime

import pandas as pd

from factor.providers.base import DataProvider
from factor.types import FactorCategory, FactorMetadata


class Factor(ABC):
    """ファクター計算の基底クラス"""

    @property
    @abstractmethod
    def name(self) -> str:
        """ファクター名"""
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        """ファクターの説明"""
        ...

    @property
    @abstractmethod
    def category(self) -> FactorCategory:
        """ファクターカテゴリ"""
        ...

    @property
    def metadata(self) -> FactorMetadata:
        """ファクターのメタデータ"""
        return FactorMetadata(
            name=self.name,
            description=self.description,
            category=self.category,
            required_data=self._required_data,
            lookback_period=self._lookback_period,
            higher_is_better=self._higher_is_better,
        )

    def compute(
        self,
        provider: DataProvider,
        universe: list[str],
        start_date: datetime | str,
        end_date: datetime | str,
    ) -> pd.DataFrame:
        """ファクター値を計算する

        Parameters
        ----------
        provider : DataProvider
            データプロバイダー
        universe : list[str]
            対象銘柄リスト
        start_date : datetime | str
            開始日
        end_date : datetime | str
            終了日

        Returns
        -------
        pd.DataFrame
            ファクター値 (index: Date, columns: symbols)
        """
        self.validate_inputs(universe, start_date, end_date)
        data = self._fetch_required_data(provider, universe, start_date, end_date)
        return self._compute_impl(data)

    def validate_inputs(
        self,
        universe: list[str],
        start_date: datetime | str,
        end_date: datetime | str,
    ) -> None:
        """入力パラメータを検証する"""
        if not universe:
            raise ValidationError("universe", "[]", "Universe cannot be empty")

        if len(universe) > 1000:
            raise ValidationError(
                "universe",
                f"len={len(universe)}",
                "Universe size exceeds limit of 1000",
            )

        start = pd.to_datetime(start_date)
        end = pd.to_datetime(end_date)
        if start >= end:
            raise ValidationError(
                "date_range",
                f"{start} to {end}",
                "Start date must be before end date",
            )

    @abstractmethod
    def _compute_impl(self, data: pd.DataFrame) -> pd.DataFrame:
        """ファクター計算の実装（サブクラスで実装）"""
        ...

    @abstractmethod
    def _fetch_required_data(
        self,
        provider: DataProvider,
        universe: list[str],
        start_date: datetime | str,
        end_date: datetime | str,
    ) -> pd.DataFrame:
        """必要なデータを取得（サブクラスで実装）"""
        ...
```

### 新規ファクターの実装例

```python
class MomentumFactor(Factor):
    """モメンタムファクター

    過去のリターンに基づいてトレンドフォローするファクター。
    """

    def __init__(
        self,
        lookback: int = 252,
        skip_recent: int = 21,
    ) -> None:
        """
        Parameters
        ----------
        lookback : int, default=252
            モメンタム計算のルックバック期間（営業日）
        skip_recent : int, default=21
            直近の除外期間（リバーサル効果を避けるため）
        """
        if lookback <= 0:
            raise ValidationError("lookback", lookback, "lookback must be positive")
        if skip_recent < 0:
            raise ValidationError("skip_recent", skip_recent, "skip_recent cannot be negative")

        self._lookback = lookback
        self._skip_recent = skip_recent

    @property
    def name(self) -> str:
        return f"momentum_{self._lookback}d"

    @property
    def description(self) -> str:
        return f"{self._lookback}日モメンタム（直近{self._skip_recent}日除外）"

    @property
    def category(self) -> FactorCategory:
        return FactorCategory.PRICE

    @property
    def _required_data(self) -> list[str]:
        return ["close"]

    @property
    def _lookback_period(self) -> int:
        return self._lookback + self._skip_recent

    @property
    def _higher_is_better(self) -> bool:
        return True  # 高いモメンタム = 良いシグナル

    def _fetch_required_data(
        self,
        provider: DataProvider,
        universe: list[str],
        start_date: datetime | str,
        end_date: datetime | str,
    ) -> pd.DataFrame:
        # ルックバック期間分のデータを余分に取得
        extended_start = pd.to_datetime(start_date) - pd.Timedelta(days=self._lookback_period * 2)
        return provider.get_prices(universe, extended_start, end_date)

    def _compute_impl(self, data: pd.DataFrame) -> pd.DataFrame:
        """ベクトル化計算でモメンタムを算出"""
        # ベクトル化: ループを使わず pandas 操作で計算
        momentum = data / data.shift(self._lookback + self._skip_recent) - 1
        return momentum.dropna()
```

## DataProvider の実装パターン

### Protocol 定義

```python
from typing import Protocol
from datetime import datetime

import pandas as pd


class DataProvider(Protocol):
    """データプロバイダーの抽象インターフェース"""

    def get_prices(
        self,
        symbols: list[str],
        start_date: datetime | str,
        end_date: datetime | str,
    ) -> pd.DataFrame:
        """終値を取得

        Returns
        -------
        pd.DataFrame
            index: DatetimeIndex, columns: symbols, values: float64
        """
        ...

    def get_volumes(
        self,
        symbols: list[str],
        start_date: datetime | str,
        end_date: datetime | str,
    ) -> pd.DataFrame:
        """出来高を取得"""
        ...

    def get_fundamentals(
        self,
        symbols: list[str],
        metrics: list[str],
        start_date: datetime | str,
        end_date: datetime | str,
    ) -> pd.DataFrame:
        """ファンダメンタルデータを取得

        Parameters
        ----------
        metrics : list[str]
            取得する指標 (e.g., ["per", "pbr", "roe"])
        """
        ...

    def get_market_cap(
        self,
        symbols: list[str],
        start_date: datetime | str,
        end_date: datetime | str,
    ) -> pd.DataFrame:
        """時価総額を取得"""
        ...
```

### 新規プロバイダーの実装例

```python
import yfinance as yf
import pandas as pd

from factor.providers.base import DataProvider
from factor.providers.cache import Cache
from factor.errors import DataFetchError


class YFinanceProvider:
    """yfinance を使用したデータプロバイダー"""

    def __init__(
        self,
        cache_path: str = "~/.cache/factor",
        cache_ttl_hours: int = 24,
    ) -> None:
        self._cache = Cache(cache_path, cache_ttl_hours)

    def get_prices(
        self,
        symbols: list[str],
        start_date: datetime | str,
        end_date: datetime | str,
    ) -> pd.DataFrame:
        """終値を取得"""
        cache_key = self._make_cache_key("prices", symbols, start_date, end_date)

        # キャッシュチェック
        if self._cache.is_valid(cache_key):
            logger.debug("Cache hit", key=cache_key)
            return self._cache.get(cache_key)

        # データ取得（リトライ付き）
        try:
            data = self._fetch_with_retry(symbols, start_date, end_date, "Close")
            self._cache.set(cache_key, data)
            return data
        except Exception as e:
            raise DataFetchError(symbols, f"Failed to fetch prices: {e}") from e

    def _fetch_with_retry(
        self,
        symbols: list[str],
        start_date: datetime | str,
        end_date: datetime | str,
        column: str,
        max_retries: int = 3,
    ) -> pd.DataFrame:
        """リトライ付きデータ取得"""
        last_error: Exception | None = None

        for attempt in range(max_retries):
            try:
                logger.debug(f"Fetch attempt {attempt + 1}/{max_retries}", symbols=symbols)
                data = yf.download(
                    symbols,
                    start=start_date,
                    end=end_date,
                    progress=False,
                )
                return data[column] if len(symbols) > 1 else data[[column]].rename(columns={column: symbols[0]})
            except Exception as e:
                last_error = e
                if attempt < max_retries - 1:
                    delay = 2 ** attempt  # 指数バックオフ
                    logger.warning(f"Retry after {delay}s", error=str(e))
                    time.sleep(delay)

        raise DataFetchError(symbols, f"Max retries exceeded: {last_error}")

    def _make_cache_key(
        self,
        data_type: str,
        symbols: list[str],
        start_date: datetime | str,
        end_date: datetime | str,
    ) -> str:
        """キャッシュキーを生成"""
        import hashlib
        symbols_hash = hashlib.md5(str(sorted(symbols)).encode()).hexdigest()[:8]
        return f"{data_type}_{symbols_hash}_{start_date}_{end_date}"
```

## 検証機能の追加方法

### 新規アナライザーの実装

```python
from dataclasses import dataclass
from scipy import stats
import pandas as pd
import numpy as np

from factor.types import ICResult
from factor.errors import ValidationError, ComputationError


@dataclass
class ICResult:
    """IC/IR分析結果"""
    ic_series: pd.Series       # 時系列IC
    mean_ic: float             # 平均IC
    std_ic: float              # IC標準偏差
    ir: float                  # 情報比率 (IC / std)
    t_stat: float              # t値
    p_value: float             # p値
    method: str                # 計算方法
    n_periods: int             # 分析期間数


class ICAnalyzer:
    """IC/IR分析を行うアナライザー"""

    def __init__(self, method: str = "spearman") -> None:
        """
        Parameters
        ----------
        method : str, default="spearman"
            相関係数の計算方法 ("spearman" | "pearson")
        """
        if method not in ("spearman", "pearson"):
            raise ValidationError(
                "method",
                method,
                f"method must be 'spearman' or 'pearson', got '{method}'",
            )
        self._method = method

    def analyze(
        self,
        factor_values: pd.DataFrame,
        forward_returns: pd.DataFrame,
    ) -> ICResult:
        """IC/IR分析を実行

        Parameters
        ----------
        factor_values : pd.DataFrame
            ファクター値 (index: Date, columns: symbols)
        forward_returns : pd.DataFrame
            フォワードリターン (index: Date, columns: symbols)

        Returns
        -------
        ICResult
            分析結果
        """
        # 入力検証
        self._validate_inputs(factor_values, forward_returns)

        # IC時系列を計算
        ic_series = self.compute_ic_series(factor_values, forward_returns)

        # 統計量を計算
        mean_ic = ic_series.mean()
        std_ic = ic_series.std()
        ir = mean_ic / std_ic if std_ic > 0 else 0.0

        # t検定
        t_stat, p_value = stats.ttest_1samp(ic_series.dropna(), 0)

        return ICResult(
            ic_series=ic_series,
            mean_ic=mean_ic,
            std_ic=std_ic,
            ir=ir,
            t_stat=t_stat,
            p_value=p_value,
            method=self._method,
            n_periods=len(ic_series.dropna()),
        )

    def compute_ic_series(
        self,
        factor_values: pd.DataFrame,
        forward_returns: pd.DataFrame,
    ) -> pd.Series:
        """IC時系列を計算"""
        common_dates = factor_values.index.intersection(forward_returns.index)
        ic_values = []

        for date in common_dates:
            f_vals = factor_values.loc[date].dropna()
            r_vals = forward_returns.loc[date].dropna()
            common = f_vals.index.intersection(r_vals.index)

            if len(common) < 5:  # 最低5銘柄必要
                ic_values.append(np.nan)
                continue

            if self._method == "spearman":
                ic, _ = stats.spearmanr(f_vals[common], r_vals[common])
            else:
                ic, _ = stats.pearsonr(f_vals[common], r_vals[common])

            ic_values.append(ic)

        return pd.Series(ic_values, index=common_dates, name="IC")

    def _validate_inputs(
        self,
        factor_values: pd.DataFrame,
        forward_returns: pd.DataFrame,
    ) -> None:
        """入力を検証"""
        if factor_values.empty:
            raise ValidationError("factor_values", "empty", "factor_values cannot be empty")
        if forward_returns.empty:
            raise ValidationError("forward_returns", "empty", "forward_returns cannot be empty")
```

## テスト戦略

### テストの種類と役割

| テスト種別 | 対象 | ツール | カバレッジ目標 |
|-----------|------|--------|--------------|
| ユニットテスト | 個別関数・クラス | pytest | 80% |
| プロパティテスト | 不変条件・境界値 | Hypothesis | 主要関数 |
| 統合テスト | API全体フロー | pytest + モック | 主要シナリオ |
| 回帰テスト | 既知値との比較 | pytest | 全ビルトインファクター |

### ユニットテストの例

```python
# tests/factor/unit/factors/price/test_momentum.py
import pytest
import pandas as pd
import numpy as np
from datetime import datetime

from factor.factors.price.momentum import MomentumFactor
from factor.errors import ValidationError


class TestMomentumFactor:
    """MomentumFactorのテスト"""

    class TestInit:
        """初期化のテスト"""

        def test_正常なパラメータで初期化できる(self):
            factor = MomentumFactor(lookback=252, skip_recent=21)

            assert factor.name == "momentum_252d"
            assert factor._lookback == 252
            assert factor._skip_recent == 21

        def test_lookbackが0以下の場合ValidationErrorを送出する(self):
            with pytest.raises(ValidationError) as exc_info:
                MomentumFactor(lookback=0)

            assert exc_info.value.field == "lookback"
            assert "positive" in exc_info.value.message

        def test_skip_recentが負の場合ValidationErrorを送出する(self):
            with pytest.raises(ValidationError) as exc_info:
                MomentumFactor(skip_recent=-1)

            assert exc_info.value.field == "skip_recent"

    class TestCompute:
        """compute メソッドのテスト"""

        @pytest.fixture
        def sample_prices(self) -> pd.DataFrame:
            """テスト用の価格データ"""
            dates = pd.date_range("2020-01-01", periods=300, freq="B")
            np.random.seed(42)
            return pd.DataFrame(
                {
                    "AAPL": 100 * (1 + np.random.randn(300).cumsum() * 0.01),
                    "GOOGL": 200 * (1 + np.random.randn(300).cumsum() * 0.01),
                },
                index=dates,
            )

        @pytest.fixture
        def mock_provider(self, sample_prices, mocker):
            """モックプロバイダー"""
            provider = mocker.Mock()
            provider.get_prices.return_value = sample_prices
            return provider

        def test_正常にファクター値を計算できる(self, mock_provider):
            factor = MomentumFactor(lookback=20, skip_recent=5)

            result = factor.compute(
                provider=mock_provider,
                universe=["AAPL", "GOOGL"],
                start_date="2020-06-01",
                end_date="2020-12-31",
            )

            assert isinstance(result, pd.DataFrame)
            assert list(result.columns) == ["AAPL", "GOOGL"]
            assert not result.empty

        def test_空のuniverseでValidationErrorを送出する(self, mock_provider):
            factor = MomentumFactor()

            with pytest.raises(ValidationError) as exc_info:
                factor.compute(
                    provider=mock_provider,
                    universe=[],
                    start_date="2020-01-01",
                    end_date="2020-12-31",
                )

            assert exc_info.value.field == "universe"
```

### プロパティテストの例

```python
# tests/factor/property/test_normalizer.py
from hypothesis import given, strategies as st, assume
import numpy as np
import pandas as pd

from factor.core.normalizer import Normalizer


class TestNormalizerProperties:
    """Normalizerの不変条件テスト"""

    @given(
        n_rows=st.integers(min_value=10, max_value=100),
        n_cols=st.integers(min_value=2, max_value=20),
    )
    def test_zscore正規化後の平均は0に近い(self, n_rows: int, n_cols: int):
        """z-score正規化後の各行の平均は0に近い"""
        # Given: ランダムなDataFrame
        np.random.seed(42)
        data = pd.DataFrame(
            np.random.randn(n_rows, n_cols),
            columns=[f"col_{i}" for i in range(n_cols)],
        )

        # When: z-score正規化
        normalizer = Normalizer()
        normalized = normalizer.zscore(data, axis=1)

        # Then: 各行の平均は0に近い
        row_means = normalized.mean(axis=1)
        assert np.allclose(row_means, 0, atol=1e-10)

    @given(
        n_rows=st.integers(min_value=10, max_value=100),
        n_cols=st.integers(min_value=2, max_value=20),
    )
    def test_rank正規化後の値は0から1の範囲(self, n_rows: int, n_cols: int):
        """ランク正規化後の値は[0, 1]の範囲内"""
        # Given: ランダムなDataFrame
        np.random.seed(42)
        data = pd.DataFrame(
            np.random.randn(n_rows, n_cols),
            columns=[f"col_{i}" for i in range(n_cols)],
        )

        # When: ランク正規化
        normalizer = Normalizer()
        ranked = normalizer.rank(data, pct=True)

        # Then: 全ての値が0-1の範囲
        assert (ranked >= 0).all().all()
        assert (ranked <= 1).all().all()

    @given(
        lower=st.floats(min_value=0.01, max_value=0.1),
        upper=st.floats(min_value=0.9, max_value=0.99),
    )
    def test_winsorize後の値は指定範囲内(self, lower: float, upper: float):
        """ウィンソライズ後の値は指定したパーセンタイル範囲内"""
        assume(lower < upper)

        # Given: 外れ値を含むデータ
        np.random.seed(42)
        data = pd.DataFrame({
            "col1": [1, 2, 3, 100, 5, 6, 7, 8, 9, 10],  # 100 は外れ値
        })

        # When: ウィンソライズ
        normalizer = Normalizer()
        winsorized = normalizer.winsorize(data, limits=(lower, 1 - upper))

        # Then: 極端な外れ値が除去されている
        assert winsorized["col1"].max() < 100
```

### 統合テストの例

```python
# tests/factor/integration/test_end_to_end.py
import pytest
import pandas as pd

from factor import (
    MomentumFactor,
    YFinanceProvider,
    ICAnalyzer,
    QuantileAnalyzer,
    Normalizer,
)


class TestEndToEndFlow:
    """エンドツーエンドの統合テスト"""

    @pytest.fixture
    def mock_provider(self, mocker):
        """モックプロバイダー（外部API呼び出しを避ける）"""
        provider = mocker.Mock(spec=YFinanceProvider)
        # テストデータを設定
        dates = pd.date_range("2020-01-01", periods=500, freq="B")
        provider.get_prices.return_value = pd.DataFrame(
            {
                "AAPL": 100 * (1 + np.random.randn(500).cumsum() * 0.01),
                "GOOGL": 200 * (1 + np.random.randn(500).cumsum() * 0.01),
                "MSFT": 150 * (1 + np.random.randn(500).cumsum() * 0.01),
            },
            index=dates,
        )
        return provider

    def test_モメンタムファクターの計算から検証までの全フロー(self, mock_provider):
        """
        1. ファクター計算
        2. 正規化
        3. IC分析
        4. 分位分析
        の全フローをテスト
        """
        universe = ["AAPL", "GOOGL", "MSFT"]
        start_date = "2020-06-01"
        end_date = "2021-12-31"

        # 1. ファクター計算
        factor = MomentumFactor(lookback=60, skip_recent=5)
        factor_values = factor.compute(mock_provider, universe, start_date, end_date)

        assert isinstance(factor_values, pd.DataFrame)
        assert not factor_values.empty

        # 2. 正規化
        normalizer = Normalizer()
        normalized = normalizer.zscore(factor_values, axis=1)

        assert normalized.shape == factor_values.shape

        # 3. フォワードリターン計算
        prices = mock_provider.get_prices(universe, start_date, end_date)
        forward_returns = prices.pct_change(21).shift(-21)  # 21日後リターン

        # 4. IC分析
        ic_analyzer = ICAnalyzer(method="spearman")
        ic_result = ic_analyzer.analyze(normalized, forward_returns)

        assert ic_result.n_periods > 0
        assert -1 <= ic_result.mean_ic <= 1

        # 5. 分位分析
        quantile_analyzer = QuantileAnalyzer(n_quantiles=5)
        quantile_result = quantile_analyzer.analyze(normalized, forward_returns)

        assert quantile_result.n_quantiles == 5
        assert len(quantile_result.mean_returns) == 5
```

### 回帰テストの例

```python
# tests/factor/regression/test_known_values.py
import pytest
import pandas as pd
import numpy as np

from factor.factors.price.momentum import MomentumFactor


class TestKnownValues:
    """既知の入力に対する期待出力を検証"""

    def test_モメンタム計算の既知値との比較(self):
        """
        手計算で検証した既知の値との比較
        """
        # Given: 既知のテストケース
        # 日付: D0, D1, D2, D3, D4, D5
        # 価格: 100, 110, 121, 133.1, 146.41, 161.05
        # 5日モメンタム (skip=0): D5/D0 - 1 = 161.05/100 - 1 = 0.6105
        dates = pd.date_range("2020-01-01", periods=6, freq="D")
        prices = pd.DataFrame(
            {"STOCK": [100, 110, 121, 133.1, 146.41, 161.05]},
            index=dates,
        )

        # 直接計算
        expected_momentum = 161.05 / 100 - 1  # = 0.6105

        # When: ファクター計算
        factor = MomentumFactor(lookback=5, skip_recent=0)
        # _compute_impl を直接テスト
        result = factor._compute_impl(prices)

        # Then: 既知の値と一致
        actual_momentum = result.iloc[-1, 0]  # 最後の行、最初の列
        assert np.isclose(actual_momentum, expected_momentum, rtol=1e-4)
```

### テスト命名規則

```python
# 日本語（推奨）
def test_正常なデータでファクターを計算できる(): ...
def test_lookbackが負の場合ValidationErrorを送出する(): ...
def test_空のuniverseでエラーになる(): ...

# 英語
def test_compute_with_valid_data_returns_dataframe(): ...
def test_compute_with_negative_lookback_raises_validation_error(): ...
```

## パフォーマンス考慮事項

### ベクトル化計算の原則

```python
# OK: ベクトル化（pandas/numpy操作）
def compute_momentum(prices: pd.DataFrame, lookback: int) -> pd.DataFrame:
    """ベクトル化計算: 高速"""
    return prices / prices.shift(lookback) - 1  # 全銘柄を一括計算

# NG: ループ処理（極めて遅い）
def compute_momentum_slow(prices: pd.DataFrame, lookback: int) -> pd.DataFrame:
    """ループ処理: 低速"""
    result = pd.DataFrame(index=prices.index, columns=prices.columns)
    for i in range(lookback, len(prices)):
        for col in prices.columns:
            result.iloc[i, prices.columns.get_loc(col)] = (
                prices.iloc[i, prices.columns.get_loc(col)]
                / prices.iloc[i - lookback, prices.columns.get_loc(col)]
                - 1
            )
    return result
```

### パフォーマンス目標

| 操作 | データ規模 | 目標時間 |
|------|-----------|---------|
| ファクター計算 | 100銘柄 x 5年日次 | 1秒以内 |
| IC計算 | 100銘柄 x 1,000日 | 500ms以内 |
| 分位分析 | 100銘柄 x 1,000日 x 5分位 | 500ms以内 |
| データ取得（キャッシュヒット） | 100銘柄 x 5年 | 100ms以内 |

### メモリ効率

```python
# メモリ効率の良いパターン
def process_large_data(data: pd.DataFrame) -> pd.DataFrame:
    # チャンク処理
    chunk_size = 1000
    results = []
    for start in range(0, len(data), chunk_size):
        chunk = data.iloc[start:start + chunk_size]
        results.append(process_chunk(chunk))
    return pd.concat(results)

# float32 オプション（メモリ50%削減）
def to_float32(data: pd.DataFrame) -> pd.DataFrame:
    return data.astype(np.float32)
```

### プロファイリング

```python
from factor.utils.profiling import profile, timeit, profile_context

# デコレータで詳細プロファイリング
@profile
def heavy_computation():
    ...

# 実行時間計測
@timeit
def timed_function():
    ...

# コンテキストマネージャで部分計測
with profile_context("IC計算"):
    ic_result = analyzer.analyze(factor_values, returns)
```

## Git 運用ルール

### ブランチ戦略

```
main (本番リリース)
└── develop (開発統合)
    ├── feature/momentum-factor
    ├── feature/fred-provider
    ├── fix/ic-calculation
    └── refactor/cache-layer
```

### コミットメッセージ規約

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Type**:
- `feat`: 新機能（新ファクター、新プロバイダー）
- `fix`: バグ修正
- `refactor`: リファクタリング
- `test`: テスト追加・修正
- `docs`: ドキュメント
- `perf`: パフォーマンス改善

**例**:
```
feat(factors): MomentumFactor を追加

- 価格ベースのモメンタムファクターを実装
- ルックバック期間と直近除外期間をパラメータ化
- ベクトル化計算で高速処理を実現

Closes #45

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
```

### PRプロセス

**作成前のチェック**:
- [ ] `make format` でフォーマット統一
- [ ] `make lint` でリントエラーなし
- [ ] `make typecheck` で型チェックパス
- [ ] `make test` で全テストパス
- [ ] カバレッジ目標を達成

## コードレビュー基準

### 必須チェック項目

**機能性**:
- [ ] ファクター計算ロジックが正しい
- [ ] エッジケース（空データ、欠損値、外れ値）が処理されている
- [ ] エラーハンドリングが適切

**パフォーマンス**:
- [ ] ベクトル化計算が使用されている（ループを避ける）
- [ ] 不要なデータコピーがない
- [ ] メモリ使用量が適切

**テスト**:
- [ ] ユニットテストが追加されている
- [ ] エッジケースがテストされている
- [ ] 回帰テスト（既知値との比較）がある

### レビューコメントの優先度

```markdown
[必須] IC計算で NaN を適切に処理していません。dropna() を追加してください。
[推奨] このループはベクトル化できます。pandas.rolling() を使うと10倍高速化できます。
[提案] ファクター名に計算パラメータを含めると、複数インスタンスの区別がしやすくなります。
[質問] skip_recent のデフォルト値を21日にした理由を教えてください。
```

## 開発環境セットアップ

```bash
# 1. リポジトリのクローン
git clone [URL]
cd finance

# 2. 依存関係のインストール
uv sync --all-extras

# 3. 開発サーバーの起動（必要に応じて）
uv run python -m factor

# 4. テスト実行
make test

# 5. 品質チェック
make check-all  # format + lint + typecheck + test
```

## チェックリスト

### 新規ファクター追加時

- [ ] `Factor` 基底クラスを継承している
- [ ] `name`, `description`, `category` プロパティを実装
- [ ] `_compute_impl`, `_fetch_required_data` を実装
- [ ] 入力バリデーションが適切
- [ ] ベクトル化計算を使用
- [ ] NumPy形式のDocstringがある
- [ ] ユニットテストを追加
- [ ] プロパティテストを追加（不変条件）
- [ ] 回帰テスト（既知値）を追加
- [ ] `src/factor/__init__.py` の `__all__` に追加

### 新規プロバイダー追加時

- [ ] `DataProvider` Protocol を実装
- [ ] 必要なメソッドをすべて実装
- [ ] キャッシュ機能を実装
- [ ] リトライ機能を実装
- [ ] エラーハンドリングが適切
- [ ] ユニットテストを追加
- [ ] 統合テストを追加
- [ ] `providers/__init__.py` でエクスポート

### 検証機能追加時

- [ ] 結果データクラスを定義
- [ ] `_validate_inputs` を実装
- [ ] 統計計算が正しい
- [ ] ユニットテストを追加
- [ ] プロパティテストを追加
- [ ] `validation/__init__.py` でエクスポート

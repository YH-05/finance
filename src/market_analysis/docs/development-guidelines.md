# 開発ガイドライン (Development Guidelines)

## 概要

本ドキュメントは market_analysis ライブラリの開発におけるコーディング規約と開発プロセスを定義します。

### 技術スタック

| 項目 | 技術 | バージョン |
|------|------|-----------|
| 言語 | Python | 3.12+ |
| パッケージ管理 | uv | latest |
| リント・フォーマット | Ruff | latest |
| 型チェック | pyright | latest (strict) |
| テスト | pytest + Hypothesis | >=8.0.0 |
| ログ | structlog | >=24.0.0 |
| リトライ | tenacity | >=8.2.0 |
| バリデーション | pydantic | >=2.5.0 |

## コーディング規約

### 命名規則

#### 変数・関数

```python
# ✅ 良い例: 金融ドメインの命名
stock_data = fetcher.fetch("AAPL", start, end)
def calculate_moving_average(prices: pd.Series, period: int = 20) -> pd.Series: ...
def fetch_forex_data(pair: str) -> pd.DataFrame: ...

# ❌ 悪い例: 曖昧な命名
data = fetch("AAPL")
def calc(prices, n): ...
```

**原則**:

- 変数: snake_case、名詞または名詞句
- 関数: snake_case、動詞で始める
- 定数: UPPER_SNAKE_CASE
- Boolean: `is_`, `has_`, `should_`, `can_` で始める

**金融ドメイン固有の命名**:

```python
# 価格データ
open_price, high_price, low_price, close_price = ohlc
adjusted_close = adj_close

# 指標
sma_20 = calculate_sma(prices, period=20)
ema_50 = calculate_ema(prices, period=50)
daily_returns = calculate_returns(prices)
annualized_volatility = calculate_volatility(returns, annualize=True)

# 相関
correlation_matrix = calculate_correlation(dataframes)
rolling_corr = calculate_rolling_correlation(series1, series2, period=60)
```

#### クラス・型

```python
# クラス: PascalCase、役割を示すサフィックス
class YFinanceFetcher(BaseDataFetcher): ...
class CorrelationAnalyzer: ...
class PlotlyChart(BaseChart): ...
class CacheManager: ...

# Protocol: 抽象的なインターフェース
from typing import Protocol

class DataFetcherProtocol(Protocol):
    def fetch(self, symbol: str, start: datetime, end: datetime) -> pd.DataFrame: ...
    def validate_symbol(self, symbol: str) -> bool: ...

# 型エイリアス (PEP 695): PascalCase
type DataSource = Literal["yfinance", "fred"]
type TickerSymbol = str
type DateRange = tuple[datetime, datetime]
```

#### ファイル命名

| ファイル種別 | 命名規則 | 例 |
|-------------|---------|-----|
| モジュール | snake_case.py | `market_data.py`, `fetcher.py` |
| テスト | test_[対象].py | `test_fetcher.py`, `test_market_data.py` |
| 型定義 | types.py | `types.py` |
| エラー定義 | errors.py | `errors.py` |

### 型ヒント (PEP 695)

**Python 3.12+ スタイルを使用**:

```python
# ✅ 良い例: 組み込み型を直接使用
def fetch_multiple_stocks(
    symbols: list[str],
    start: datetime,
    end: datetime,
) -> dict[str, pd.DataFrame]:
    """複数銘柄のデータを取得する。"""
    return {symbol: fetch_stock(symbol, start, end) for symbol in symbols}

# ❌ 悪い例: typing からインポート（Python 3.9以降は不要）
from typing import List, Dict
def fetch_multiple_stocks(
    symbols: List[str], start: datetime, end: datetime
) -> Dict[str, pd.DataFrame]: ...
```

**ジェネリック関数・クラス（PEP 695）**:

```python
# ✅ 良い例: PEP 695 の新構文
def first[T](items: list[T]) -> T | None:
    return items[0] if items else None

class DataCache[T]:
    def __init__(self) -> None:
        self._cache: dict[str, T] = {}

    def get(self, key: str) -> T | None:
        return self._cache.get(key)

    def set(self, key: str, value: T) -> None:
        self._cache[key] = value
```

**dataclass と TypedDict の使い分け**:

```python
from dataclasses import dataclass
from typing import TypedDict

# dataclass: メソッドを持つオブジェクト型
@dataclass(frozen=True)
class RetryConfig:
    """リトライ設定"""
    max_retries: int = 3
    initial_delay: float = 1.0
    exponential_base: float = 2.0
    max_delay: float = 30.0

# TypedDict: 辞書型のスキーマ定義（JSON出力など）
class AgentOutput(TypedDict):
    symbol: str
    period: str
    summary: dict[str, float]
    analysis: str
```

### コードフォーマット

**インデント**: 4スペース

**行の長さ**: 最大88文字（Ruff/Black標準）

**引数の改行**:

```python
def fetch_stock(
    symbol: str,
    start: datetime | str | None = None,
    end: datetime | str | None = None,
    *,
    use_cache: bool = True,
    cache_ttl_hours: int = 24,
) -> pd.DataFrame:
    """株価データを取得する。"""
    ...
```

### Docstring規約 (NumPy形式)

**関数・メソッド**:

```python
def calculate_sma(
    data: pd.Series,
    period: int = 20,
) -> pd.Series:
    """単純移動平均（SMA）を計算する。

    Parameters
    ----------
    data : pd.Series
        価格データ（終値など）
    period : int, default=20
        移動平均の期間

    Returns
    -------
    pd.Series
        移動平均値。期間未満のデータはNaN

    Raises
    ------
    ValueError
        期間が1未満の場合

    Examples
    --------
    >>> prices = pd.Series([100, 102, 104, 103, 105])
    >>> sma = calculate_sma(prices, period=3)
    >>> sma.iloc[2]
    102.0
    """
    if period < 1:
        raise ValueError(f"Period must be >= 1, got {period}")
    return data.rolling(window=period).mean()
```

**クラス**:

```python
class MarketData:
    """市場データ取得の統一インターフェース。

    複数のデータソース（yfinance、FRED）からデータを取得し、
    統一されたフォーマットで返します。

    Parameters
    ----------
    cache_enabled : bool, default=True
        キャッシュを有効にするかどうか
    cache_ttl_hours : int, default=24
        キャッシュの有効期限（時間）

    Attributes
    ----------
    fetcher : DataFetcher
        データ取得インスタンス
    cache : CacheManager
        キャッシュ管理インスタンス

    Examples
    --------
    >>> market = MarketData()
    >>> df = market.fetch_stock("AAPL", start="2024-01-01", end="2024-12-31")
    >>> df.columns
    Index(['Open', 'High', 'Low', 'Close', 'Volume', 'Adj Close'], dtype='object')
    """

    def __init__(
        self,
        cache_enabled: bool = True,
        cache_ttl_hours: int = 24,
    ) -> None:
        ...
```

### インラインコメント

```python
# ✅ 良い例: なぜそうするかを説明
# yfinanceは為替ペアに「=X」サフィックスが必要
symbol = f"{pair}=X" if self._is_forex_pair(pair) else pair

# キャッシュミス時のみAPIを呼び出し、レート制限を回避
if cached_data is None:
    data = self._fetch_from_api(symbol)

# AIDEV-NOTE: pickleを使用するのはpandasのDataFrame保存に最適なため
# JSON形式だと日付インデックスや型情報が失われる

# ❌ 悪い例: 何をしているか（コードを見れば分かる）
# シンボルに=Xを追加
symbol = f"{pair}=X"
```

### アンカーコメント

```python
# AIDEV-NOTE: リトライ設定はtenacityを使用。指数バックオフで外部API負荷を軽減
# AIDEV-TODO: 非同期対応を検討 (Issue #XXX)
# AIDEV-QUESTION: FREDのAPI制限は1日何回？確認が必要
```

## エラーハンドリング

### カスタム例外クラス

```python
# errors.py に定義
class MarketAnalysisError(Exception):
    """market_analysis ライブラリの基底エラー"""
    pass


class DataFetchError(MarketAnalysisError):
    """データ取得エラー"""

    def __init__(
        self,
        message: str,
        symbol: str,
        source: str,
        retry_count: int = 0,
    ) -> None:
        super().__init__(message)
        self.symbol = symbol
        self.source = source
        self.retry_count = retry_count


class ValidationError(MarketAnalysisError):
    """入力バリデーションエラー"""

    def __init__(
        self,
        message: str,
        field: str,
        value: object,
    ) -> None:
        super().__init__(message)
        self.field = field
        self.value = value
```

### エラーハンドリングパターン

```python
from market_analysis.utils.logging_config import get_logger

logger = get_logger(__name__)

def fetch_stock_data(symbol: str, start: datetime, end: datetime) -> pd.DataFrame:
    """株価データを取得する。"""
    try:
        # バリデーション
        validated_symbol = validator.validate_symbol(symbol)

        # キャッシュ確認
        cached = cache.get(cache_key)
        if cached is not None:
            logger.debug("cache_hit", symbol=symbol)
            return cached

        # データ取得（リトライ付き）
        data = retry_handler.execute(
            lambda: yfinance.download(validated_symbol, start, end)
        )

        # キャッシュ保存
        cache.set(cache_key, data)
        return data

    except ValidationError:
        # バリデーションエラーはそのまま伝播
        raise
    except ConnectionError as e:
        # 接続エラーはラップして詳細情報を付与
        logger.error("connection_error", symbol=symbol, error=str(e))
        raise DataFetchError(
            f"Failed to connect to yfinance for {symbol}",
            symbol=symbol,
            source="yfinance",
        ) from e
    except Exception as e:
        # 予期しないエラーはログ出力して再送出
        logger.error("unexpected_error", symbol=symbol, error=str(e), exc_info=True)
        raise
```

### エラーメッセージの書き方

```python
# ✅ 良い例: 具体的で解決策を示す
raise ValidationError(
    f"Symbol must be 1-20 alphanumeric characters, got '{symbol}' ({len(symbol)} chars)",
    field="symbol",
    value=symbol,
)

raise DataFetchError(
    f"Failed to fetch {symbol} after {max_retries} retries. "
    f"Check network connection or symbol validity.",
    symbol=symbol,
    source="yfinance",
    retry_count=max_retries,
)

raise ValueError(
    f"Start date ({start}) must be before end date ({end})"
)

# FRED APIキー未設定
raise RuntimeError(
    "FRED API key not set. Set FRED_API_KEY environment variable. "
    "Get your key at: https://fred.stlouisfed.org/docs/api/api_key.html"
)

# ❌ 悪い例: 曖昧で役に立たない
raise ValueError("Invalid input")
raise RuntimeError("API error")
```

## ロギング規約

### 基本パターン

```python
from market_analysis.utils.logging_config import get_logger

logger = get_logger(__name__)

class DataFetcher:
    def fetch(self, symbol: str, start: datetime, end: datetime) -> pd.DataFrame:
        logger.debug("fetch_started", symbol=symbol, start=str(start), end=str(end))

        try:
            data = self._fetch_from_api(symbol, start, end)
            logger.info(
                "fetch_completed",
                symbol=symbol,
                rows=len(data),
                columns=list(data.columns),
            )
            return data
        except Exception as e:
            logger.error(
                "fetch_failed",
                symbol=symbol,
                error=str(e),
                exc_info=True,
            )
            raise
```

### ログレベルの使い分け

| レベル | 用途 | 例 |
|--------|------|-----|
| DEBUG | 開発時のデバッグ情報 | キャッシュキー、中間値 |
| INFO | 正常な処理の完了 | データ取得成功、分析完了 |
| WARNING | 注意すべき状態 | キャッシュミス、リトライ発生 |
| ERROR | エラー発生 | API接続失敗、バリデーションエラー |

### 構造化ログの出力例

```python
# コード
logger.info("analysis_completed", symbol="AAPL", indicators=["SMA", "EMA"], duration_ms=150)

# 出力（JSON形式、LOG_FORMAT=json の場合）
{
    "event": "analysis_completed",
    "symbol": "AAPL",
    "indicators": ["SMA", "EMA"],
    "duration_ms": 150,
    "timestamp": "2024-01-15T10:30:00Z",
    "logger": "market_analysis.core.analyzer"
}
```

## テスト規約

### テストの種類とカバレッジ目標

| テスト種別 | 対象 | カバレッジ目標 | 配置先 |
|-----------|------|--------------|--------|
| ユニットテスト | 個別関数・クラス | 80%以上 | `tests/market_analysis/unit/` |
| プロパティテスト | 境界値・不変条件 | 主要関数 | `tests/market_analysis/property/` |
| 統合テスト | API全体のフロー | 主要ユースケース | `tests/market_analysis/integration/` |
| E2Eテスト | 実際のAPI呼び出し | CI外で実行 | `tests/market_analysis/e2e/` |

### テスト命名規則

```python
# ✅ 良い例（日本語）- 意図が明確
def test_正常なシンボルでデータを取得できる(): ...
def test_無効なシンボルでValidationErrorを送出する(): ...
def test_キャッシュヒット時はAPIを呼び出さない(): ...

# ✅ 良い例（英語）
def test_fetch_with_valid_symbol_returns_dataframe(): ...
def test_fetch_with_invalid_symbol_raises_validation_error(): ...
def test_fetch_uses_cache_when_available(): ...

# ❌ 悪い例
def test1(): ...
def test_fetch(): ...
def test_should_work(): ...
```

### ユニットテストの例

```python
import pytest
import pandas as pd
from datetime import datetime
from unittest.mock import Mock, patch

from market_analysis.core.fetcher import YFinanceFetcher
from market_analysis.errors import ValidationError, DataFetchError


class TestYFinanceFetcher:
    """YFinanceFetcherのテスト"""

    class TestFetch:
        """fetchメソッドのテスト"""

        def test_正常なシンボルでDataFrameを返す(self, mock_yfinance_data: pd.DataFrame):
            # Given
            fetcher = YFinanceFetcher()
            with patch("yfinance.download", return_value=mock_yfinance_data):
                # When
                result = fetcher.fetch(
                    symbol="AAPL",
                    start=datetime(2024, 1, 1),
                    end=datetime(2024, 12, 31),
                )

            # Then
            assert isinstance(result, pd.DataFrame)
            assert "Close" in result.columns
            assert len(result) > 0

        def test_無効なシンボルでValidationErrorを送出する(self):
            # Given
            fetcher = YFinanceFetcher()

            # When/Then
            with pytest.raises(ValidationError) as exc_info:
                fetcher.fetch(
                    symbol="INVALID@SYMBOL",
                    start=datetime(2024, 1, 1),
                    end=datetime(2024, 12, 31),
                )

            assert exc_info.value.field == "symbol"

    class TestValidateSymbol:
        """validate_symbolメソッドのテスト"""

        @pytest.mark.parametrize("symbol", ["AAPL", "MSFT", "USDJPY=X", "GC=F"])
        def test_有効なシンボルでTrueを返す(self, symbol: str):
            fetcher = YFinanceFetcher()
            assert fetcher.validate_symbol(symbol) is True

        @pytest.mark.parametrize("symbol", ["", "A" * 25, "INVALID@", "123"])
        def test_無効なシンボルでFalseを返す(self, symbol: str):
            fetcher = YFinanceFetcher()
            assert fetcher.validate_symbol(symbol) is False
```

### プロパティテストの例

```python
from hypothesis import given, strategies as st, assume
import pandas as pd
import numpy as np

from market_analysis.core.analyzer import IndicatorCalculator


class TestIndicatorCalculatorProperty:
    """IndicatorCalculatorのプロパティテスト"""

    @given(st.lists(
        st.floats(min_value=0.01, max_value=10000, allow_nan=False, allow_infinity=False),
        min_size=30,
        max_size=1000,
    ))
    def test_SMAは入力データの最小値と最大値の間に収まる(self, prices: list[float]):
        # Given
        data = pd.Series(prices)

        # When
        sma = IndicatorCalculator.calculate_sma(data, period=20)

        # Then: NaN以外の値は入力の範囲内
        valid_sma = sma.dropna()
        assert valid_sma.min() >= min(prices)
        assert valid_sma.max() <= max(prices)

    @given(st.lists(
        st.floats(min_value=0.01, max_value=10000, allow_nan=False, allow_infinity=False),
        min_size=30,
        max_size=1000,
    ))
    def test_相関係数は負の1から1の範囲内(self, prices: list[float]):
        # Given
        series1 = pd.Series(prices)
        series2 = pd.Series(prices[::-1])  # 逆順

        # When
        corr = series1.corr(series2)

        # Then
        assert -1.0 <= corr <= 1.0
```

### 統合テストの例

```python
import pytest
import pandas as pd

from market_analysis.api.market_data import MarketData
from market_analysis.api.analysis import Analysis


class TestFetchAndAnalyzeFlow:
    """データ取得から分析までのフロー"""

    @pytest.fixture
    def market_data(self, mock_yfinance) -> MarketData:
        """モック化されたMarketDataインスタンス"""
        return MarketData(cache_enabled=False)

    def test_株価取得から移動平均計算まで(self, market_data: MarketData, mock_ohlcv_data: pd.DataFrame):
        # Given: データ取得
        df = market_data.fetch_stock("AAPL", start="2024-01-01", end="2024-12-31")

        # When: 分析実行
        analysis = Analysis(df)
        result = analysis.add_sma(20).add_ema(50).add_returns().data

        # Then: 期待するカラムが追加されている
        assert "SMA_20" in result.columns
        assert "EMA_50" in result.columns
        assert "Returns" in result.columns
        assert len(result) == len(df)
```

### モック・フィクスチャの定義

```python
# tests/market_analysis/conftest.py
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import Mock, patch


@pytest.fixture
def mock_ohlcv_data() -> pd.DataFrame:
    """OHLCVサンプルデータ"""
    dates = pd.date_range(start="2024-01-01", periods=252, freq="B")
    np.random.seed(42)

    close = 100 + np.cumsum(np.random.randn(252) * 2)

    return pd.DataFrame({
        "Open": close * (1 + np.random.randn(252) * 0.01),
        "High": close * (1 + np.abs(np.random.randn(252)) * 0.02),
        "Low": close * (1 - np.abs(np.random.randn(252)) * 0.02),
        "Close": close,
        "Adj Close": close,
        "Volume": np.random.randint(1000000, 10000000, 252),
    }, index=dates)


@pytest.fixture
def mock_yfinance(mock_ohlcv_data: pd.DataFrame):
    """yfinanceモック"""
    with patch("yfinance.download", return_value=mock_ohlcv_data) as mock:
        yield mock


@pytest.fixture
def temp_cache_db(tmp_path):
    """一時キャッシュDB"""
    db_path = tmp_path / "test_cache.db"
    return str(db_path)
```

## Git運用ルール

### ブランチ戦略

```
main (本番リリース)
  └─ develop (開発統合)
      ├─ feature/market-data-api
      ├─ feature/correlation-analysis
      ├─ fix/cache-expiry-bug
      ├─ refactor/fetcher-interface
      ├─ docs/api-documentation
      └─ test/property-tests
```

**ブランチ種別**:

| プレフィックス | 用途 | ラベル |
|---------------|------|--------|
| `feature/` | 新機能開発 | enhancement |
| `fix/` | バグ修正 | bug |
| `refactor/` | リファクタリング | refactor |
| `docs/` | ドキュメント | documentation |
| `test/` | テスト追加 | test |
| `release/` | リリース準備 | release |

### コミットメッセージ規約

**Conventional Commits形式**:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Type一覧**:

| Type | 用途 | セマンティックバージョン |
|------|------|------------------------|
| feat | 新機能 | minor |
| fix | バグ修正 | patch |
| docs | ドキュメント | - |
| style | コードフォーマット | - |
| refactor | リファクタリング | - |
| perf | パフォーマンス改善 | patch |
| test | テスト追加・修正 | - |
| chore | ビルド、依存関係 | - |

**良いコミットメッセージの例**:

```
feat(fetcher): FRED経済指標データの取得機能を追加

FREDから経済指標データ（金利、GDP等）を取得できるようになりました。

実装内容:
- FREDFetcherクラスの追加
- FRED_API_KEY環境変数のサポート
- リトライ処理の組み込み
- キャッシュ対応

Closes #45
```

```
fix(cache): キャッシュ有効期限の計算エラーを修正

キャッシュのTTL計算がUTCではなくローカル時刻で行われていた問題を修正。
タイムゾーンに関係なく正確にキャッシュが期限切れになります。

Fixes #52
```

### プルリクエストプロセス

**作成前のチェック**:

- [ ] 全てのテストがパス（`make test`）
- [ ] Lintエラーがない（`make lint`）
- [ ] 型チェックがパス（`make typecheck`）
- [ ] フォーマット済み（`make format`）
- [ ] 競合が解決されている

**PRテンプレート**:

```markdown
## 概要
[変更内容の簡潔な説明]

## 変更理由
[なぜこの変更が必要か]

## 変更内容
- [変更点1]
- [変更点2]

## テスト
- [ ] ユニットテスト追加
- [ ] 統合テスト追加（該当する場合）
- [ ] 手動テスト実施

## チェックリスト
- [ ] `make check-all` がパス
- [ ] Docstringが記載されている
- [ ] 型ヒントが適切に記載されている

## 関連Issue
Closes #[Issue番号]
```

## コードレビュー基準

### レビューポイント

**機能性**:

- [ ] LRD要件を満たしているか
- [ ] エッジケースが考慮されているか（空データ、NULL値、境界値）
- [ ] エラーハンドリングが適切か

**可読性**:

- [ ] 命名が明確で金融ドメインに適しているか
- [ ] NumPy形式のDocstringが記載されているか
- [ ] 複雑なロジック（指標計算等）にコメントがあるか

**保守性**:

- [ ] レイヤードアーキテクチャに従っているか
- [ ] 依存関係の方向が正しいか（api→core→utils）
- [ ] 責務が明確に分離されているか

**パフォーマンス**:

- [ ] pandasのベクトル化操作を使用しているか
- [ ] 不要なAPIコールを避けているか（キャッシュ活用）
- [ ] 大量データ処理時のメモリ使用量を考慮しているか

**セキュリティ**:

- [ ] APIキーが環境変数で管理されているか
- [ ] SQLインジェクション対策がされているか（キャッシュDB）
- [ ] 入力検証が実装されているか

### レビューコメントの書き方

**優先度の明示**:

```markdown
[必須] セキュリティ: FRED_API_KEYがログに出力されています
[推奨] パフォーマンス: このループはpandasのapplyで置き換えられます
[提案] 可読性: このメソッド名をcalculate_returns()にした方が明確では？
[質問] この期間のデフォルト値（20日）の根拠を教えてください
```

**建設的なフィードバック**:

```markdown
## ✅ 良い例
この実装だとデータポイントが多い場合にO(n^2)の計算量になります。
pandas.Seriesのrolling()を使うとO(n)で計算できます:

```python
sma = data.rolling(window=period).mean()
```

## ❌ 悪い例
このコードは遅いです。
```

## 開発環境セットアップ

### 必要なツール

| ツール | バージョン | 用途 |
|--------|-----------|------|
| Python | 3.12+ | ランタイム |
| uv | latest | パッケージ管理 |
| make | - | タスクランナー |

### セットアップ手順

```bash
# 1. リポジトリのクローン
git clone <repository-url>
cd finance

# 2. 依存関係のインストール
uv sync --all-extras

# 3. 環境変数の設定
cp .env.example .env
# FRED_API_KEY を設定（FRED使用時のみ）

# 4. 開発ツールの確認
make check-all
```

### 主要コマンド

```bash
# 品質チェック
make check-all    # 全チェック（format, lint, typecheck, test）
make format       # コードフォーマット
make lint         # リント
make typecheck    # 型チェック
make test         # テスト実行
make test-cov     # カバレッジ付きテスト

# 依存関係
uv add <package>      # パッケージ追加
uv add --dev <pkg>    # 開発用パッケージ追加
uv sync --all-extras  # 依存関係の同期
```

### 推奨開発ツール

- **VS Code + Pylance**: 型チェック、オートコンプリート
- **Ruff拡張機能**: リアルタイムリント
- **Python Test Explorer**: テスト実行・デバッグ

## チェックリスト

### 実装時

- [ ] 命名規則に従っている（snake_case、PascalCase）
- [ ] 型ヒントが適切に記載されている（PEP 695準拠）
- [ ] NumPy形式のDocstringがある
- [ ] エラーハンドリングが実装されている
- [ ] ロギングが適切に実装されている
- [ ] レイヤードアーキテクチャに従っている

### テスト時

- [ ] ユニットテストが書かれている
- [ ] カバレッジが80%以上
- [ ] エッジケースがカバーされている
- [ ] モックが適切に使用されている

### コミット時

- [ ] `make check-all` がパス
- [ ] Conventional Commitsに従っている
- [ ] 関連Issueがリンクされている

### PR作成時

- [ ] セルフレビュー完了
- [ ] PRテンプレートが記入されている
- [ ] CIがパスしている

## 参照ドキュメント

| ドキュメント | パス | 内容 |
|-------------|------|------|
| アーキテクチャ設計 | `src/market_analysis/docs/architecture.md` | システム構成、レイヤー設計 |
| リポジトリ構造 | `src/market_analysis/docs/repository-structure.md` | ディレクトリ構成、依存関係 |
| LRD | `src/market_analysis/docs/library-requirements.md` | 要件定義 |
| コーディング規約（共通） | `docs/coding-standards.md` | リポジトリ共通規約 |
| 開発プロセス（共通） | `docs/development-process.md` | リポジトリ共通プロセス |
| テンプレート | `template/` | 実装参照用（変更禁止） |

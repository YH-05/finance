# レジームスイッチングモデル Notebook Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** FRED 7 系列を用いて米国経済の 3 レジームを多変量 HMM で抽出し、S&P500 週次リターンを Markov-Switching Regression で説明する notebook 一式（4 分割）を構築する。

**Architecture:** `notebook/REGIME_SWITCHING/` に `_helpers.py`（データ取得・前処理・可視化ヘルパー）と 4 個の Jupyter notebook を配置。データレイヤーは `market.fred.HistoricalCache`（経済指標）と `market.yfinance.YFinanceFetcher`（S&P500）を経由。経済レジーム抽出には `hmmlearn.GaussianHMM`、市場レジーム回帰には `statsmodels.tsa.regime_switching.MarkovRegression` を使用。

**Tech Stack:** Python 3.12+, pandas, numpy, matplotlib, seaborn, hmmlearn (新規追加), statsmodels >= 0.14.6, scikit-learn >= 1.8.0, yfinance, pytest

**Spec:** `docs/superpowers/specs/2026-05-23-regime-switching-notebook-design.md`

---

## File Structure

### 新規作成
- `notebook/REGIME_SWITCHING/_helpers.py` — データ取得・前処理・可視化の共通関数
- `notebook/REGIME_SWITCHING/01_data_preparation.ipynb` — データ取得・変換・EDA
- `notebook/REGIME_SWITCHING/02_economic_regime_hmm.ipynb` — モデル①: HMM
- `notebook/REGIME_SWITCHING/03_market_regime_ms.ipynb` — モデル②: Markov-Switching Regression
- `notebook/REGIME_SWITCHING/04_comparison.ipynb` — モデル①②の対応分析
- `notebook/REGIME_SWITCHING/README.md` — 実行手順と前提条件
- `notebook/REGIME_SWITCHING/data/` — 中間データ出力ディレクトリ（`.gitkeep`）
- `tests/notebook/regime_switching/test_helpers.py` — `_helpers.py` の単体テスト
- `tests/notebook/regime_switching/__init__.py`
- `tests/notebook/__init__.py`

### 修正
- `pyproject.toml` — `hmmlearn` 依存追加
- `data/config/fred_series.json` — `INDPRO`, `BAA10Y` プリセット追加

---

## Task 0: 環境セットアップ（依存追加・プリセット追加・フォルダ作成）

**Files:**
- Modify: `pyproject.toml`
- Modify: `data/config/fred_series.json`
- Create: `notebook/REGIME_SWITCHING/data/.gitkeep`

- [ ] **Step 1: `hmmlearn` を依存に追加**

Run:
```bash
uv add hmmlearn
```

Expected: `pyproject.toml` の `dependencies` に `"hmmlearn>=0.3.0"` 相当の行が追加され、`uv.lock` が更新される。

- [ ] **Step 2: 追加が成功したことを確認**

Run:
```bash
uv run python -c "import hmmlearn; print(hmmlearn.__version__)"
```

Expected: バージョン文字列（例: `0.3.2`）が出力される。

- [ ] **Step 3: FRED presets に INDPRO と BAA10Y を追加**

`data/config/fred_series.json` の構造はカテゴリ → 系列 ID → メタデータの 2 階層 dict。
各系列エントリのキーは `name_ja`, `name_en`, `frequency`, `units`, `description` の 5 つ。

**INDPRO** を `"Business & Economic Activity"` カテゴリ（既存）に追加する。
そのカテゴリ内の最後の系列エントリの後に `,` 区切りで以下を挿入:

```json
"INDPRO": {
    "name_ja": "鉱工業生産指数",
    "name_en": "Industrial Production: Total Index",
    "frequency": "Monthly",
    "units": "Index 2017=100",
    "description": "鉱工業セクターの生産活動を示す代表的指標。景気サイクルの実体経済側を捉える。"
}
```

**BAA10Y** を `"Corporate Bond Yield Spread"` カテゴリ（既存）に追加する。
そのカテゴリ内の最後の系列エントリの後に `,` 区切りで以下を挿入:

```json
"BAA10Y": {
    "name_ja": "Baa社債-10年国債スプレッド",
    "name_en": "Moody's Seasoned Baa Corporate Bond Yield Relative to Yield on 10-Year Treasury Constant Maturity",
    "frequency": "Daily",
    "units": "Percent",
    "description": "Baa格社債利回りと10年国債利回りのスプレッド。信用リスクの代表的なバロメーター。"
}
```

JSON ファイル全体が valid であること（最終的なフォーマットは Task 0 Step 4 で検証）。

- [ ] **Step 4: presets 追加を検証**

Run:
```bash
uv run python -c "from market.fred import FREDFetcher; FREDFetcher.load_presets(); s = FREDFetcher.get_preset_symbols(); print('INDPRO in:', 'INDPRO' in s, '/ BAA10Y in:', 'BAA10Y' in s)"
```

Expected: 出力が `INDPRO in: True / BAA10Y in: True`。
JSON パースエラーが出る場合は `data/config/fred_series.json` のカンマ・ブラケット位置を再確認。

- [ ] **Step 5: notebook フォルダと data ディレクトリ作成**

Run:
```bash
mkdir -p notebook/REGIME_SWITCHING/data
touch notebook/REGIME_SWITCHING/data/.gitkeep
```

- [ ] **Step 6: コミット**

```bash
git add pyproject.toml uv.lock data/config/fred_series.json notebook/REGIME_SWITCHING/data/.gitkeep
git commit -m "chore(regime-switching): hmmlearn 依存と FRED presets を追加"
```

---

## Task 1: `_helpers.py` のパス定数とモジュール骨格

**Files:**
- Create: `notebook/REGIME_SWITCHING/_helpers.py`
- Create: `tests/notebook/__init__.py`
- Create: `tests/notebook/regime_switching/__init__.py`
- Create: `tests/notebook/regime_switching/test_helpers.py`

- [ ] **Step 1: 失敗するテストを書く**

`tests/notebook/regime_switching/test_helpers.py`:

```python
"""REGIME_SWITCHING/_helpers.py の単体テスト."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


def _load_helpers():
    """notebook/REGIME_SWITCHING/_helpers.py をモジュールとしてロード."""
    here = Path(__file__).resolve()
    repo_root = here.parent.parent.parent.parent  # tests/notebook/regime_switching/ → repo
    helpers_path = repo_root / "notebook" / "REGIME_SWITCHING" / "_helpers.py"
    spec = importlib.util.spec_from_file_location("regime_helpers", helpers_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestModuleConstants:
    def test_PKG_DIR_は_REGIME_SWITCHING_ディレクトリを指す(self) -> None:
        helpers = _load_helpers()
        assert helpers.PKG_DIR.name == "REGIME_SWITCHING"
        assert helpers.PKG_DIR.is_dir()

    def test_DATA_DIR_は_PKG_DIR_配下の_data(self) -> None:
        helpers = _load_helpers()
        assert helpers.DATA_DIR == helpers.PKG_DIR / "data"

    def test_FRED_SERIES_IDS_は7系列を含む(self) -> None:
        helpers = _load_helpers()
        expected = {
            "INDPRO",
            "ICSA",
            "T10YIE",
            "CPIAUCSL",
            "STLFSI4",
            "BAA10Y",
            "T10Y2Y",
        }
        assert set(helpers.FRED_SERIES_IDS) == expected
```

`tests/notebook/__init__.py` と `tests/notebook/regime_switching/__init__.py` は空ファイルで作成。

- [ ] **Step 2: テストを実行して失敗を確認**

Run:
```bash
uv run pytest tests/notebook/regime_switching/test_helpers.py -v
```

Expected: `FileNotFoundError` または `AttributeError` でテスト失敗。

- [ ] **Step 3: 最小実装で通す**

`notebook/REGIME_SWITCHING/_helpers.py`:

```python
"""REGIME_SWITCHING 実験用の共通ユーティリティ.

データ取得・前処理・可視化の関数を提供する。notebook からは
``from _helpers import ...`` で参照する。
"""

from __future__ import annotations

from pathlib import Path

# ---------------------------------------------------------------------------
# パス定数
# ---------------------------------------------------------------------------

PKG_DIR: Path = Path(__file__).resolve().parent
REPO_ROOT: Path = PKG_DIR.parent.parent
DATA_DIR: Path = PKG_DIR / "data"

FRED_WEEKLY_RAW_PARQUET: Path = DATA_DIR / "fred_weekly_raw.parquet"
FEATURES_WEEKLY_PARQUET: Path = DATA_DIR / "features_weekly.parquet"
SP500_WEEKLY_PARQUET: Path = DATA_DIR / "sp500_weekly.parquet"

# ---------------------------------------------------------------------------
# FRED 系列定義
# ---------------------------------------------------------------------------

FRED_SERIES_IDS: list[str] = [
    "INDPRO",
    "ICSA",
    "T10YIE",
    "CPIAUCSL",
    "STLFSI4",
    "BAA10Y",
    "T10Y2Y",
]

# 分析開始日（STLFSI4 と T10YIE が両方揃う時点）
DEFAULT_START_DATE: str = "2003-12-01"
```

- [ ] **Step 4: テストを実行して成功を確認**

Run:
```bash
uv run pytest tests/notebook/regime_switching/test_helpers.py -v
```

Expected: 3 件 PASS。

- [ ] **Step 5: コミット**

```bash
git add notebook/REGIME_SWITCHING/_helpers.py tests/notebook/
git commit -m "feat(regime-switching): _helpers.py の骨格とパス定数を追加"
```

---

## Task 2: `load_fred_weekly()` — FRED 7 系列を W-FRI に揃えて取得

**Files:**
- Modify: `notebook/REGIME_SWITCHING/_helpers.py`
- Modify: `tests/notebook/regime_switching/test_helpers.py`

- [ ] **Step 1: 失敗するテストを書く（モック使用）**

`tests/notebook/regime_switching/test_helpers.py` の末尾に追加:

```python
from unittest.mock import patch
import pandas as pd


class TestLoadFredWeekly:
    def _make_mock_df(self, dates: list[str], values: list[float]) -> pd.DataFrame:
        idx = pd.to_datetime(dates)
        return pd.DataFrame({"value": values}, index=idx)

    def test_全7系列を結合してW_FRI週次DataFrameを返す(self) -> None:
        helpers = _load_helpers()

        def fake_get_series_df(self, series_id: str) -> pd.DataFrame:
            # 2024年1月の数日分の架空データ
            return pd.DataFrame(
                {"value": [1.0, 2.0, 3.0]},
                index=pd.to_datetime(["2024-01-05", "2024-01-12", "2024-01-19"]),
            )

        with patch(
            "market.fred.HistoricalCache.sync_series", return_value={"success": True}
        ), patch(
            "market.fred.HistoricalCache.get_series_df", fake_get_series_df
        ):
            df = helpers.load_fred_weekly(start="2024-01-01")

        # 列がFRED_SERIES_IDSの全てを含む
        assert set(df.columns) == set(helpers.FRED_SERIES_IDS)
        # インデックスはDatetimeIndex
        assert isinstance(df.index, pd.DatetimeIndex)
        # 全インデックスが金曜日（W-FRI）
        assert all(d.dayofweek == 4 for d in df.index)

    def test_start引数より前のデータは除外される(self) -> None:
        helpers = _load_helpers()

        def fake_get_series_df(self, series_id: str) -> pd.DataFrame:
            return pd.DataFrame(
                {"value": [1.0, 2.0, 3.0, 4.0]},
                index=pd.to_datetime(
                    ["2023-12-01", "2024-01-05", "2024-01-12", "2024-01-19"]
                ),
            )

        with patch(
            "market.fred.HistoricalCache.sync_series", return_value={"success": True}
        ), patch(
            "market.fred.HistoricalCache.get_series_df", fake_get_series_df
        ):
            df = helpers.load_fred_weekly(start="2024-01-01")

        assert df.index.min() >= pd.Timestamp("2024-01-01")
```

- [ ] **Step 2: テスト失敗を確認**

Run:
```bash
uv run pytest tests/notebook/regime_switching/test_helpers.py::TestLoadFredWeekly -v
```

Expected: `AttributeError: module 'regime_helpers' has no attribute 'load_fred_weekly'` で失敗。

- [ ] **Step 3: 実装を追加**

`notebook/REGIME_SWITCHING/_helpers.py` の末尾に追加:

```python
import pandas as pd

from market.fred import HistoricalCache
from utils_core.logging import get_logger

logger = get_logger(__name__, module="regime_switching.helpers")


def load_fred_weekly(
    start: str = DEFAULT_START_DATE,
    series_ids: list[str] | None = None,
    cache: HistoricalCache | None = None,
) -> pd.DataFrame:
    """FRED の指定系列を取得し W-FRI 週次に揃えた DataFrame を返す.

    Parameters
    ----------
    start : str
        分析開始日 (YYYY-MM-DD).
    series_ids : list[str] | None
        取得する FRED series ID のリスト. None なら ``FRED_SERIES_IDS`` 全件.
    cache : HistoricalCache | None
        テスト時に差し替え可能. None なら新規生成.

    Returns
    -------
    pd.DataFrame
        インデックスが週末金曜の DatetimeIndex、各列が FRED 系列値.
    """
    ids = list(series_ids) if series_ids is not None else list(FRED_SERIES_IDS)
    cache = cache if cache is not None else HistoricalCache()

    series_frames: dict[str, pd.DataFrame] = {}
    for sid in ids:
        logger.info("Loading FRED series", series_id=sid)
        cache.sync_series(sid)
        df = cache.get_series_df(sid)
        if df is None:
            raise RuntimeError(f"FRED series {sid} could not be loaded from cache")
        series_frames[sid] = df

    # 全系列を W-FRI に揃える: 日次/週次は .last(), 月次は ffill
    aligned: dict[str, pd.Series] = {}
    for sid, df in series_frames.items():
        weekly = df["value"].resample("W-FRI").last().ffill()
        aligned[sid] = weekly

    combined = pd.concat(aligned, axis=1)
    combined.columns = list(aligned.keys())
    combined = combined.loc[combined.index >= pd.Timestamp(start)]
    combined = combined.dropna(how="any")  # 全系列が揃う週のみ残す

    logger.info(
        "FRED weekly data loaded",
        n_rows=len(combined),
        date_range=[str(combined.index.min().date()), str(combined.index.max().date())],
    )
    return combined
```

- [ ] **Step 4: テスト実行して成功を確認**

Run:
```bash
uv run pytest tests/notebook/regime_switching/test_helpers.py::TestLoadFredWeekly -v
```

Expected: 2 件 PASS。

- [ ] **Step 5: コミット**

```bash
git add notebook/REGIME_SWITCHING/_helpers.py tests/notebook/regime_switching/test_helpers.py
git commit -m "feat(regime-switching): load_fred_weekly を追加"
```

---

## Task 3: `transform_features()` — YoY 変換と Z-score 標準化

**Files:**
- Modify: `notebook/REGIME_SWITCHING/_helpers.py`
- Modify: `tests/notebook/regime_switching/test_helpers.py`

- [ ] **Step 1: 失敗するテストを書く**

`tests/notebook/regime_switching/test_helpers.py` の末尾に追加:

```python
import numpy as np


class TestTransformFeatures:
    def _make_input(self) -> pd.DataFrame:
        """週次52週分の架空7系列データを返す."""
        n = 200  # YoY計算に十分な52週超
        idx = pd.date_range("2020-01-03", periods=n, freq="W-FRI")
        rng = np.random.default_rng(0)
        data = {
            "INDPRO": 100 + np.cumsum(rng.normal(0, 0.5, n)),
            "ICSA": 200_000 + np.cumsum(rng.normal(0, 1000, n)),
            "T10YIE": 2.0 + rng.normal(0, 0.1, n),
            "CPIAUCSL": 260 + np.cumsum(rng.normal(0.05, 0.2, n)),
            "STLFSI4": rng.normal(0, 0.5, n),
            "BAA10Y": 2.0 + rng.normal(0, 0.2, n),
            "T10Y2Y": 1.0 + rng.normal(0, 0.3, n),
        }
        return pd.DataFrame(data, index=idx)

    def test_出力は7列のDataFrameで標準化されている(self) -> None:
        helpers = _load_helpers()
        df_in = self._make_input()
        df_out = helpers.transform_features(df_in)

        assert set(df_out.columns) == set(helpers.FRED_SERIES_IDS)
        # 各列の平均はおよそ0、標準偏差はおよそ1
        for col in df_out.columns:
            assert abs(df_out[col].mean()) < 1e-6
            assert abs(df_out[col].std(ddof=0) - 1.0) < 1e-6

    def test_INDPRO_と_CPIAUCSL_はYoY変換後に標準化(self) -> None:
        helpers = _load_helpers()
        df_in = self._make_input()
        df_out = helpers.transform_features(df_in)

        # YoY計算で最初の52週はNaN→dropされる
        assert len(df_out) == len(df_in) - 52

    def test_ICSAは4週移動平均のYoY(self) -> None:
        helpers = _load_helpers()
        df_in = self._make_input()
        df_out = helpers.transform_features(df_in)

        # 出力にICSAが含まれ、ICSAの値は標準化されているはず
        assert "ICSA" in df_out.columns
        assert df_out["ICSA"].isna().sum() == 0
```

- [ ] **Step 2: テスト失敗を確認**

Run:
```bash
uv run pytest tests/notebook/regime_switching/test_helpers.py::TestTransformFeatures -v
```

Expected: `AttributeError: ... no attribute 'transform_features'` で失敗。

- [ ] **Step 3: 実装を追加**

`notebook/REGIME_SWITCHING/_helpers.py` の末尾に追加:

```python
def transform_features(df_raw: pd.DataFrame) -> pd.DataFrame:
    """7 系列を変換し Z-score 標準化した DataFrame を返す.

    変換ルール:
    - INDPRO, CPIAUCSL: 前年同期比 % (52 週前比)
    - ICSA: 4 週移動平均の前年同期比 %
    - T10YIE, STLFSI4, BAA10Y, T10Y2Y: レベルそのまま

    Parameters
    ----------
    df_raw : pd.DataFrame
        ``load_fred_weekly`` の出力 (W-FRI, 列が FRED 系列値).

    Returns
    -------
    pd.DataFrame
        Z-score 標準化後の特徴量。先頭 52 週は YoY 計算により欠損するので除去。
    """
    df = df_raw.copy()

    # YoY% (52週前比)
    yoy_cols = ["INDPRO", "CPIAUCSL"]
    for col in yoy_cols:
        df[col] = (df[col] / df[col].shift(52) - 1.0) * 100.0

    # ICSA: 4週移動平均のYoY%
    ma4 = df["ICSA"].rolling(window=4, min_periods=4).mean()
    df["ICSA"] = (ma4 / ma4.shift(52) - 1.0) * 100.0

    # 先頭の欠損週を除去
    df = df.dropna(how="any")

    # Z-score 標準化 (population std, ddof=0)
    standardized = (df - df.mean()) / df.std(ddof=0)

    return standardized[FRED_SERIES_IDS]
```

- [ ] **Step 4: テスト実行して成功を確認**

Run:
```bash
uv run pytest tests/notebook/regime_switching/test_helpers.py::TestTransformFeatures -v
```

Expected: 3 件 PASS。

- [ ] **Step 5: コミット**

```bash
git add notebook/REGIME_SWITCHING/_helpers.py tests/notebook/regime_switching/test_helpers.py
git commit -m "feat(regime-switching): transform_features (YoY+Zscore) を追加"
```

---

## Task 4: `fetch_sp500_weekly_returns()` — yfinance で ^GSPC を週次リターンに

**Files:**
- Modify: `notebook/REGIME_SWITCHING/_helpers.py`
- Modify: `tests/notebook/regime_switching/test_helpers.py`

- [ ] **Step 1: 失敗するテストを書く（yfinance はモック）**

`tests/notebook/regime_switching/test_helpers.py` の末尾に追加:

```python
class TestFetchSP500WeeklyReturns:
    def test_週次対数リターンSeriesを返す(self) -> None:
        helpers = _load_helpers()

        # 100日分の架空日次データ
        idx = pd.date_range("2024-01-01", periods=100, freq="B")
        fake_daily = pd.DataFrame(
            {"close": 4000 + np.cumsum(np.random.default_rng(0).normal(0, 5, 100))},
            index=idx,
        )

        from market.yfinance.types import MarketDataResult, DataSource
        from datetime import datetime

        fake_result = MarketDataResult(
            data=fake_daily,
            source=DataSource.YFINANCE,
            symbol="^GSPC",
            fetched_at=datetime.now(),
            from_cache=False,
        )

        with patch(
            "market.yfinance.fetcher.YFinanceFetcher.fetch",
            return_value=[fake_result],
        ):
            ret = helpers.fetch_sp500_weekly_returns(start="2024-01-01")

        assert isinstance(ret, pd.Series)
        assert ret.name == "sp500_logret"
        # インデックスは金曜
        assert all(d.dayofweek == 4 for d in ret.index)
        # 最初の値はNaN除去済み
        assert not ret.isna().any()
```

- [ ] **Step 2: テスト失敗を確認**

Run:
```bash
uv run pytest tests/notebook/regime_switching/test_helpers.py::TestFetchSP500WeeklyReturns -v
```

Expected: `AttributeError` で失敗。

- [ ] **Step 3: 実装を追加**

`notebook/REGIME_SWITCHING/_helpers.py` の末尾に追加:

```python
import numpy as np

from datetime import datetime, timezone

from market.yfinance.fetcher import YFinanceFetcher
from market.yfinance.types import FetchOptions


def fetch_sp500_weekly_returns(
    start: str = DEFAULT_START_DATE,
    end: str | None = None,
    fetcher: YFinanceFetcher | None = None,
) -> pd.Series:
    """yfinance で ^GSPC を取得し W-FRI 週次対数リターンを返す.

    Parameters
    ----------
    start : str
        開始日 (YYYY-MM-DD).
    end : str | None
        終了日。None なら今日。
    fetcher : YFinanceFetcher | None
        テスト時に差し替え可能。

    Returns
    -------
    pd.Series
        ``sp500_logret`` という名前の週次対数リターン Series.
    """
    fetcher = fetcher if fetcher is not None else YFinanceFetcher()
    end_date = end if end is not None else datetime.now(timezone.utc).strftime("%Y-%m-%d")

    options = FetchOptions(
        symbols=["^GSPC"],
        start_date=start,
        end_date=end_date,
    )
    results = fetcher.fetch(options)
    if not results:
        raise RuntimeError("^GSPC fetch returned empty result")

    daily = results[0].data
    # 列名は yfinance フォーマット (lower-case 想定); 念のため小文字化
    daily.columns = [c.lower() if isinstance(c, str) else c for c in daily.columns]
    if "close" not in daily.columns:
        raise RuntimeError(
            f"^GSPC data missing 'close' column. columns={list(daily.columns)}"
        )

    weekly_close = daily["close"].resample("W-FRI").last().dropna()
    log_ret = np.log(weekly_close / weekly_close.shift(1)).dropna()
    log_ret.name = "sp500_logret"

    logger.info(
        "S&P500 weekly returns loaded",
        n_weeks=len(log_ret),
        date_range=[str(log_ret.index.min().date()), str(log_ret.index.max().date())],
    )
    return log_ret
```

- [ ] **Step 4: テスト実行して成功を確認**

Run:
```bash
uv run pytest tests/notebook/regime_switching/test_helpers.py::TestFetchSP500WeeklyReturns -v
```

Expected: 1 件 PASS。

- [ ] **Step 5: コミット**

```bash
git add notebook/REGIME_SWITCHING/_helpers.py tests/notebook/regime_switching/test_helpers.py
git commit -m "feat(regime-switching): fetch_sp500_weekly_returns を追加"
```

---

## Task 5: `label_hmm_states()` — INDPRO YoY 平均で HMM 状態をラベル割当

**Files:**
- Modify: `notebook/REGIME_SWITCHING/_helpers.py`
- Modify: `tests/notebook/regime_switching/test_helpers.py`

- [ ] **Step 1: 失敗するテストを書く**

`tests/notebook/regime_switching/test_helpers.py` の末尾に追加:

```python
class TestLabelHmmStates:
    def test_INDPRO_YoY平均の降順で拡大_減速_後退をラベル付け(self) -> None:
        helpers = _load_helpers()

        # 30週分の状態ラベルと INDPRO YoY 値
        states = pd.Series(
            [0] * 10 + [1] * 10 + [2] * 10,
            index=pd.date_range("2024-01-05", periods=30, freq="W-FRI"),
        )
        # state=0 のINDPRO YoY平均が最小、state=2が最大になるようなデータ
        indpro = pd.Series(
            [-2.0] * 10 + [1.0] * 10 + [5.0] * 10,
            index=states.index,
        )

        mapping = helpers.label_hmm_states(states, indpro)

        assert mapping[2] == "拡大"
        assert mapping[1] == "減速"
        assert mapping[0] == "後退・ストレス"

    def test_2状態の場合は拡大_後退ストレスのみ(self) -> None:
        helpers = _load_helpers()
        states = pd.Series(
            [0] * 10 + [1] * 10,
            index=pd.date_range("2024-01-05", periods=20, freq="W-FRI"),
        )
        indpro = pd.Series(
            [-2.0] * 10 + [5.0] * 10,
            index=states.index,
        )
        mapping = helpers.label_hmm_states(states, indpro)
        assert mapping[1] == "拡大"
        assert mapping[0] == "後退・ストレス"
```

- [ ] **Step 2: テスト失敗を確認**

Run:
```bash
uv run pytest tests/notebook/regime_switching/test_helpers.py::TestLabelHmmStates -v
```

Expected: 失敗。

- [ ] **Step 3: 実装を追加**

`notebook/REGIME_SWITCHING/_helpers.py` の末尾に追加:

```python
def label_hmm_states(
    states: pd.Series,
    indpro_yoy: pd.Series,
) -> dict[int, str]:
    """HMM 状態 ID を INDPRO YoY 平均でランク付けし、解釈ラベルを割り当てる.

    Parameters
    ----------
    states : pd.Series
        状態 ID 系列 (int).
    indpro_yoy : pd.Series
        INDPRO の YoY (transform_features の出力でも生のYoYでも可).
        ``states`` と同じインデックスである必要がある.

    Returns
    -------
    dict[int, str]
        state_id -> ラベル文字列 のマッピング.
        ラベルは状態数に応じて以下:
        - 2 状態: 拡大 / 後退・ストレス
        - 3 状態: 拡大 / 減速 / 後退・ストレス
        - 4 状態以上: 拡大1, 拡大2, ..., 後退・ストレス (連番)
    """
    common_idx = states.index.intersection(indpro_yoy.index)
    aligned_states = states.loc[common_idx]
    aligned_indpro = indpro_yoy.loc[common_idx]

    mean_by_state = (
        pd.DataFrame({"state": aligned_states, "indpro": aligned_indpro})
        .groupby("state")["indpro"]
        .mean()
        .sort_values(ascending=False)
    )

    state_ids = mean_by_state.index.tolist()
    n = len(state_ids)
    if n == 2:
        labels = ["拡大", "後退・ストレス"]
    elif n == 3:
        labels = ["拡大", "減速", "後退・ストレス"]
    else:
        labels = [f"拡大{i + 1}" for i in range(n - 1)] + ["後退・ストレス"]

    return {int(sid): label for sid, label in zip(state_ids, labels)}
```

- [ ] **Step 4: テスト成功確認**

Run:
```bash
uv run pytest tests/notebook/regime_switching/test_helpers.py::TestLabelHmmStates -v
```

Expected: 2 件 PASS。

- [ ] **Step 5: コミット**

```bash
git add notebook/REGIME_SWITCHING/_helpers.py tests/notebook/regime_switching/test_helpers.py
git commit -m "feat(regime-switching): label_hmm_states を追加"
```

---

## Task 6: `plot_regime_overlay()` — レジーム背景塗りつぶし時系列プロット

**Files:**
- Modify: `notebook/REGIME_SWITCHING/_helpers.py`
- Modify: `tests/notebook/regime_switching/test_helpers.py`

- [ ] **Step 1: 失敗するテストを書く**

`tests/notebook/regime_switching/test_helpers.py` の末尾に追加:

```python
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


class TestPlotRegimeOverlay:
    def test_axesに塗りつぶしパッチと線が追加される(self) -> None:
        helpers = _load_helpers()

        idx = pd.date_range("2024-01-05", periods=30, freq="W-FRI")
        series = pd.Series(np.arange(30, dtype=float), index=idx, name="value")
        regimes = pd.Series(
            [0] * 10 + [1] * 10 + [2] * 10, index=idx, name="regime"
        )
        palette = {0: "#cccccc", 1: "#aaaaaa", 2: "#888888"}
        labels = {0: "拡大", 1: "減速", 2: "後退・ストレス"}

        fig, ax = plt.subplots()
        helpers.plot_regime_overlay(
            ax=ax, series=series, regimes=regimes, palette=palette, labels=labels
        )

        # ラインが1本以上引かれている
        assert len(ax.lines) >= 1
        # 背景塗りつぶし(axvspanはpatch)が状態数以上存在する
        assert len(ax.patches) >= 3
        plt.close(fig)
```

- [ ] **Step 2: テスト失敗を確認**

Run:
```bash
uv run pytest tests/notebook/regime_switching/test_helpers.py::TestPlotRegimeOverlay -v
```

Expected: 失敗。

- [ ] **Step 3: 実装を追加**

`notebook/REGIME_SWITCHING/_helpers.py` の末尾に追加:

```python
from matplotlib.axes import Axes


def plot_regime_overlay(
    ax: Axes,
    series: pd.Series,
    regimes: pd.Series,
    palette: dict[int, str],
    labels: dict[int, str] | None = None,
    line_color: str = "black",
    line_width: float = 1.2,
) -> Axes:
    """レジーム背景を塗りつぶした時系列プロットを描画.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        描画先 Axes.
    series : pd.Series
        プロットする時系列 (インデックスが日付).
    regimes : pd.Series
        各時点のレジーム ID. ``series`` と同じインデックス長を想定.
    palette : dict[int, str]
        state_id -> 色のマッピング.
    labels : dict[int, str] | None
        state_id -> 凡例ラベルのマッピング. None なら凡例なし.
    line_color : str
        メインラインの色.
    line_width : float
        メインラインの太さ.

    Returns
    -------
    matplotlib.axes.Axes
        受け取った Axes (チェーン用).
    """
    common_idx = series.index.intersection(regimes.index)
    s = series.loc[common_idx]
    r = regimes.loc[common_idx]

    # 連続する同一状態のセグメント区間に対して axvspan で塗りつぶし
    state_arr = r.to_numpy()
    times = r.index.to_numpy()
    if len(state_arr) > 0:
        seg_start = 0
        current_state = int(state_arr[0])
        legend_drawn: set[int] = set()
        for i in range(1, len(state_arr)):
            if int(state_arr[i]) != current_state:
                label = (
                    labels.get(current_state, str(current_state))
                    if labels is not None and current_state not in legend_drawn
                    else None
                )
                ax.axvspan(
                    times[seg_start],
                    times[i],
                    color=palette.get(current_state, "#dddddd"),
                    alpha=0.3,
                    label=label,
                )
                if labels is not None:
                    legend_drawn.add(current_state)
                seg_start = i
                current_state = int(state_arr[i])
        # 最後のセグメント
        label = (
            labels.get(current_state, str(current_state))
            if labels is not None and current_state not in legend_drawn
            else None
        )
        ax.axvspan(
            times[seg_start],
            times[-1],
            color=palette.get(current_state, "#dddddd"),
            alpha=0.3,
            label=label,
        )

    ax.plot(s.index, s.values, color=line_color, linewidth=line_width)
    return ax
```

- [ ] **Step 4: テスト成功確認**

Run:
```bash
uv run pytest tests/notebook/regime_switching/test_helpers.py::TestPlotRegimeOverlay -v
```

Expected: 1 件 PASS。

- [ ] **Step 5: 全 helpers テストを一括実行**

Run:
```bash
uv run pytest tests/notebook/regime_switching/ -v
```

Expected: 全件 PASS (Task 1〜6 のテスト計 12 件程度)。

- [ ] **Step 6: 品質チェック**

Run:
```bash
uv run ruff format notebook/REGIME_SWITCHING/_helpers.py tests/notebook/
uv run ruff check notebook/REGIME_SWITCHING/_helpers.py tests/notebook/
```

Expected: フォーマット適用、lint エラー 0。エラーがあれば修正してから次へ。

- [ ] **Step 7: コミット**

```bash
git add notebook/REGIME_SWITCHING/_helpers.py tests/notebook/regime_switching/test_helpers.py
git commit -m "feat(regime-switching): plot_regime_overlay を追加し helpers 完成"
```

---

## Task 7: `01_data_preparation.ipynb` — データ取得と EDA

**Files:**
- Create: `notebook/REGIME_SWITCHING/01_data_preparation.ipynb`

- [ ] **Step 1: notebook を JSON 形式で作成**

`notebook/REGIME_SWITCHING/01_data_preparation.ipynb` を以下のセル構成で作成（jupyter nbformat v4）。各セルは独立して実行可能であること。

セル構成:

1. **Markdown**: `# 01 Data Preparation\n\nFRED 7 系列と S&P500 を取得し、週次 W-FRI に揃えて変換・標準化する。`

2. **Code** (imports):
```python
from __future__ import annotations
import sys
from pathlib import Path

# このnotebookと同じディレクトリを sys.path に追加して _helpers を import
NOTEBOOK_DIR = Path.cwd()
if str(NOTEBOOK_DIR) not in sys.path:
    sys.path.insert(0, str(NOTEBOOK_DIR))

import _helpers as h
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

sns.set_theme(style="whitegrid")
```

3. **Markdown**: `## FRED 7 系列を取得`

4. **Code**:
```python
df_raw = h.load_fred_weekly(start=h.DEFAULT_START_DATE)
df_raw.to_parquet(h.FRED_WEEKLY_RAW_PARQUET)
print(f"Shape: {df_raw.shape}")
print(f"Date range: {df_raw.index.min().date()} 〜 {df_raw.index.max().date()}")
df_raw.head()
```

5. **Markdown**: `## 生値の可視化`

6. **Code**:
```python
fig, axes = plt.subplots(4, 2, figsize=(14, 12))
for ax, col in zip(axes.flatten(), h.FRED_SERIES_IDS):
    ax.plot(df_raw.index, df_raw[col], linewidth=0.8)
    ax.set_title(col)
    ax.tick_params(axis="x", rotation=45)
axes.flatten()[-1].axis("off")  # 8番目は空
plt.tight_layout()
plt.show()
```

7. **Markdown**: `## 変換と標準化`

8. **Code**:
```python
features = h.transform_features(df_raw)
features.to_parquet(h.FEATURES_WEEKLY_PARQUET)
print(f"Features shape: {features.shape}")
features.describe().round(3)
```

9. **Markdown**: `## 標準化後の可視化`

10. **Code**:
```python
fig, axes = plt.subplots(4, 2, figsize=(14, 12))
for ax, col in zip(axes.flatten(), h.FRED_SERIES_IDS):
    ax.plot(features.index, features[col], linewidth=0.8)
    ax.set_title(f"{col} (z-score)")
    ax.axhline(0, color="grey", linewidth=0.5)
    ax.tick_params(axis="x", rotation=45)
axes.flatten()[-1].axis("off")
plt.tight_layout()
plt.show()
```

11. **Markdown**: `## 相関ヒートマップ`

12. **Code**:
```python
fig, ax = plt.subplots(figsize=(8, 6))
sns.heatmap(
    features.corr(),
    annot=True,
    fmt=".2f",
    cmap="RdBu_r",
    center=0,
    vmin=-1, vmax=1,
    ax=ax,
)
ax.set_title("特徴量相関行列")
plt.tight_layout()
plt.show()
```

13. **Markdown**: `## S&P500 週次対数リターン取得`

14. **Code**:
```python
sp500_ret = h.fetch_sp500_weekly_returns(start=h.DEFAULT_START_DATE)
sp500_ret.to_frame().to_parquet(h.SP500_WEEKLY_PARQUET)
print(f"S&P500 returns shape: {sp500_ret.shape}")
print(f"Annualized vol: {sp500_ret.std() * np.sqrt(52):.3%}")
sp500_ret.head()
```

15. **Markdown**: `## 出力ファイル確認`

16. **Code**:
```python
for path in [h.FRED_WEEKLY_RAW_PARQUET, h.FEATURES_WEEKLY_PARQUET, h.SP500_WEEKLY_PARQUET]:
    size_kb = path.stat().st_size / 1024
    print(f"{path.name}: {size_kb:.1f} KB")
```

- [ ] **Step 2: notebook 形式の整合性を確認**

Run:
```bash
uv run python -c "import nbformat; nb = nbformat.read('notebook/REGIME_SWITCHING/01_data_preparation.ipynb', as_version=4); nbformat.validate(nb); print(f'cells: {len(nb.cells)}')"
```

Expected: `cells: 16` 程度（セル数）が表示され、エラーなし。

- [ ] **Step 3: notebook を実行して動作確認**

Run:
```bash
uv run jupyter nbconvert --to notebook --execute notebook/REGIME_SWITCHING/01_data_preparation.ipynb --output 01_data_preparation.ipynb --ExecutePreprocessor.timeout=300
```

Expected: 実行成功。`notebook/REGIME_SWITCHING/data/` に 3 つの parquet ファイルが生成される。
失敗した場合は出力されたトレースバックを確認し、原因を特定して修正（典型原因: FRED API キー未設定、yfinance ネットワーク問題）。

- [ ] **Step 4: 出力ファイルを確認**

Run:
```bash
ls -la notebook/REGIME_SWITCHING/data/
```

Expected: `fred_weekly_raw.parquet`, `features_weekly.parquet`, `sp500_weekly.parquet`, `.gitkeep` が存在。

- [ ] **Step 5: コミット（生成された parquet は data/ で gitignore 対象なので含めない）**

```bash
git add notebook/REGIME_SWITCHING/01_data_preparation.ipynb
git commit -m "feat(regime-switching): 01_data_preparation notebook を追加"
```

---

## Task 8: `02_economic_regime_hmm.ipynb` — モデル①: 多変量 HMM

**Files:**
- Create: `notebook/REGIME_SWITCHING/02_economic_regime_hmm.ipynb`

- [ ] **Step 1: notebook を作成**

セル構成:

1. **Markdown**: `# 02 Economic Regime: 多変量 Gaussian HMM\n\n7 系列を観測として 3 状態 HMM でレジームを抽出する。`

2. **Code** (imports):
```python
from __future__ import annotations
import sys
from pathlib import Path

NOTEBOOK_DIR = Path.cwd()
if str(NOTEBOOK_DIR) not in sys.path:
    sys.path.insert(0, str(NOTEBOOK_DIR))

import _helpers as h
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from hmmlearn.hmm import GaussianHMM

sns.set_theme(style="whitegrid")
np.random.seed(42)
```

3. **Markdown**: `## 特徴量読み込み`

4. **Code**:
```python
features = pd.read_parquet(h.FEATURES_WEEKLY_PARQUET)
df_raw = pd.read_parquet(h.FRED_WEEKLY_RAW_PARQUET)
print(f"Features: {features.shape}")
features.head()
```

5. **Markdown**: `## HMM 学習\n\n3 状態 Gaussian HMM、full 共分散、200 iter。`

6. **Code**:
```python
X = features.values
model = GaussianHMM(
    n_components=3,
    covariance_type="full",
    n_iter=200,
    random_state=42,
)
model.fit(X)
print(f"Converged: {model.monitor_.converged}")
print(f"Log-likelihood: {model.score(X):.2f}")
```

7. **Markdown**: `## 状態予測とラベル割当`

8. **Code**:
```python
states = pd.Series(model.predict(X), index=features.index, name="state")
proba = pd.DataFrame(
    model.predict_proba(X),
    index=features.index,
    columns=[f"P(state={i})" for i in range(3)],
)

# INDPRO YoYで状態ラベル割当 (生YoYを再計算)
indpro_yoy = (df_raw["INDPRO"] / df_raw["INDPRO"].shift(52) - 1.0) * 100.0
indpro_yoy = indpro_yoy.dropna()

state_labels = h.label_hmm_states(states, indpro_yoy)
print("State labels:", state_labels)
states_labeled = states.map(state_labels)
states_labeled.value_counts()
```

9. **Markdown**: `## 遷移確率行列`

10. **Code**:
```python
trans_df = pd.DataFrame(
    model.transmat_,
    index=[state_labels[i] for i in range(3)],
    columns=[state_labels[i] for i in range(3)],
)
fig, ax = plt.subplots(figsize=(6, 5))
sns.heatmap(trans_df, annot=True, fmt=".3f", cmap="Blues", ax=ax)
ax.set_title("HMM 遷移確率行列")
ax.set_xlabel("To")
ax.set_ylabel("From")
plt.tight_layout()
plt.show()
```

11. **Markdown**: `## レジーム背景塗りつぶし + INDPRO YoY 重ね描き`

12. **Code**:
```python
palette = {
    [k for k, v in state_labels.items() if v == "拡大"][0]: "#aec7e8",
    [k for k, v in state_labels.items() if v == "減速"][0]: "#ffbb78",
    [k for k, v in state_labels.items() if v == "後退・ストレス"][0]: "#ff9896",
}

fig, ax = plt.subplots(figsize=(14, 5))
# INDPRO YoY を共通インデックスに揃え
indpro_aligned = indpro_yoy.reindex(states.index).ffill()
h.plot_regime_overlay(
    ax=ax,
    series=indpro_aligned,
    regimes=states,
    palette=palette,
    labels=state_labels,
)
ax.set_title("経済レジーム (HMM) + INDPRO YoY %")
ax.set_ylabel("INDPRO YoY %")
ax.legend(loc="upper right")
ax.axhline(0, color="grey", linewidth=0.5)
plt.tight_layout()
plt.show()
```

13. **Markdown**: `## レジーム別の特徴量平均`

14. **Code**:
```python
features_with_regime = features.copy()
features_with_regime["regime"] = states_labeled.values
regime_mean = features_with_regime.groupby("regime").mean().round(2)
regime_mean
```

15. **Markdown**: `## 状態事前確率の積み上げチャート`

16. **Code**:
```python
proba_renamed = proba.copy()
proba_renamed.columns = [state_labels[i] for i in range(3)]
fig, ax = plt.subplots(figsize=(14, 4))
ax.stackplot(
    proba_renamed.index,
    proba_renamed.T.values,
    labels=proba_renamed.columns,
    colors=[palette[i] for i in range(3)],
    alpha=0.8,
)
ax.set_title("HMM 状態事前確率")
ax.set_ylabel("P(state)")
ax.set_ylim(0, 1)
ax.legend(loc="upper right")
plt.tight_layout()
plt.show()
```

17. **Markdown**: `## 結果の保存`

18. **Code**:
```python
output = pd.DataFrame({
    "state_id": states,
    "regime": states_labeled,
})
output = output.join(proba_renamed)
output.to_parquet(h.DATA_DIR / "economic_regime_hmm.parquet")
print(f"Saved: {h.DATA_DIR / 'economic_regime_hmm.parquet'}")
```

- [ ] **Step 2: nbformat 検証**

Run:
```bash
uv run python -c "import nbformat; nb = nbformat.read('notebook/REGIME_SWITCHING/02_economic_regime_hmm.ipynb', as_version=4); nbformat.validate(nb); print(f'cells: {len(nb.cells)}')"
```

Expected: エラーなし、`cells: 18` 程度。

- [ ] **Step 3: notebook を実行**

Run:
```bash
uv run jupyter nbconvert --to notebook --execute notebook/REGIME_SWITCHING/02_economic_regime_hmm.ipynb --output 02_economic_regime_hmm.ipynb --ExecutePreprocessor.timeout=600
```

Expected: 実行成功。`Converged: True` と表示され、`economic_regime_hmm.parquet` が生成される。

- [ ] **Step 4: コミット**

```bash
git add notebook/REGIME_SWITCHING/02_economic_regime_hmm.ipynb
git commit -m "feat(regime-switching): 02 経済レジーム HMM notebook を追加"
```

---

## Task 9: `03_market_regime_ms.ipynb` — モデル②: Markov-Switching Regression (パターン A/B)

**Files:**
- Create: `notebook/REGIME_SWITCHING/03_market_regime_ms.ipynb`

- [ ] **Step 1: notebook を作成**

セル構成:

1. **Markdown**: `# 03 Market Regime: Markov-Switching Regression\n\nS&P500 週次対数リターンを 7 系列で説明する 3 状態 MS 回帰を、生 7 系列 (A) と PCA 削減版 (B) の 2 パターンで実行する。`

2. **Code** (imports):
```python
from __future__ import annotations
import sys
from pathlib import Path

NOTEBOOK_DIR = Path.cwd()
if str(NOTEBOOK_DIR) not in sys.path:
    sys.path.insert(0, str(NOTEBOOK_DIR))

import _helpers as h
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.decomposition import PCA
import statsmodels.api as sm
from statsmodels.tsa.regime_switching.markov_regression import MarkovRegression

sns.set_theme(style="whitegrid")
np.random.seed(42)
```

3. **Markdown**: `## データ読み込み`

4. **Code**:
```python
features = pd.read_parquet(h.FEATURES_WEEKLY_PARQUET)
sp500_ret = pd.read_parquet(h.SP500_WEEKLY_PARQUET)["sp500_logret"]

# 共通インデックスに揃える
common_idx = features.index.intersection(sp500_ret.index)
X_full = features.loc[common_idx]
y = sp500_ret.loc[common_idx]
print(f"X shape: {X_full.shape}, y shape: {y.shape}")
```

5. **Markdown**: `## パターン A: 生 7 系列を説明変数`

6. **Code**:
```python
model_a = MarkovRegression(
    endog=y.values,
    k_regimes=3,
    exog=X_full.values,
    switching_variance=True,
    switching_trend=True,
)
res_a = model_a.fit(search_reps=10, disp=False)
print(f"Pattern A: AIC={res_a.aic:.2f}, BIC={res_a.bic:.2f}, LL={res_a.llf:.2f}")
```

7. **Markdown**: `## パターン B: PCA 累積寄与率 80% まで削減`

8. **Code**:
```python
pca = PCA(n_components=0.80, random_state=42)
X_pca = pca.fit_transform(X_full.values)
n_components = X_pca.shape[1]
print(f"PCA components: {n_components} (explained variance: {pca.explained_variance_ratio_.sum():.3%})")

# 寄与率のバープロット
fig, ax = plt.subplots(figsize=(8, 4))
ax.bar(
    range(1, n_components + 1),
    pca.explained_variance_ratio_,
)
ax.set_xlabel("Component")
ax.set_ylabel("Explained Variance Ratio")
ax.set_title("PCA Explained Variance")
plt.tight_layout()
plt.show()
```

9. **Code**:
```python
model_b = MarkovRegression(
    endog=y.values,
    k_regimes=3,
    exog=X_pca,
    switching_variance=True,
    switching_trend=True,
)
res_b = model_b.fit(search_reps=10, disp=False)
print(f"Pattern B: AIC={res_b.aic:.2f}, BIC={res_b.bic:.2f}, LL={res_b.llf:.2f}")
```

10. **Markdown**: `## BIC/AIC 比較表`

11. **Code**:
```python
comparison = pd.DataFrame({
    "Pattern": ["A (raw 7)", f"B (PCA {n_components})"],
    "AIC": [res_a.aic, res_b.aic],
    "BIC": [res_a.bic, res_b.bic],
    "LogLik": [res_a.llf, res_b.llf],
    "k_params": [res_a.params.size, res_b.params.size],
})
comparison
```

12. **Markdown**: `## スムーズ確率の比較（パターン A）`

13. **Code**:
```python
smooth_a = pd.DataFrame(
    res_a.smoothed_marginal_probabilities,
    index=y.index,
    columns=[f"regime_{i}" for i in range(3)],
)
# 平均リターンで状態ラベル: 最大→上昇、最小→下落、中→中立
state_means_a = []
for i in range(3):
    weights = smooth_a[f"regime_{i}"].values
    weighted_mean = (y.values * weights).sum() / weights.sum()
    state_means_a.append((i, weighted_mean))
state_means_a.sort(key=lambda x: x[1], reverse=True)
label_map_a = {state_means_a[0][0]: "上昇", state_means_a[1][0]: "中立", state_means_a[2][0]: "下落"}
print("Pattern A labels:", label_map_a)

smooth_a_labeled = smooth_a.copy()
smooth_a_labeled.columns = [label_map_a[i] for i in range(3)]

fig, ax = plt.subplots(figsize=(14, 4))
palette_market = {"上昇": "#aec7e8", "中立": "#ffbb78", "下落": "#ff9896"}
ax.stackplot(
    smooth_a_labeled.index,
    smooth_a_labeled[["上昇", "中立", "下落"]].T.values,
    labels=["上昇", "中立", "下落"],
    colors=[palette_market[l] for l in ["上昇", "中立", "下落"]],
    alpha=0.8,
)
ax.set_title("Pattern A: スムーズ確率")
ax.set_ylim(0, 1)
ax.legend(loc="upper right")
plt.tight_layout()
plt.show()
```

14. **Markdown**: `## レジーム背景 + S&P500 重ね描き（パターン A）`

15. **Code**:
```python
# argmax で各週のレジームを決定
regime_a = pd.Series(
    smooth_a.values.argmax(axis=1),
    index=smooth_a.index,
)
regime_a_labeled = regime_a.map(label_map_a)

# S&P500 累積リターン
cum_ret = (y.cumsum())

palette_a = {sid: palette_market[label_map_a[sid]] for sid in range(3)}
labels_a = {sid: label_map_a[sid] for sid in range(3)}

fig, ax = plt.subplots(figsize=(14, 5))
h.plot_regime_overlay(
    ax=ax,
    series=cum_ret,
    regimes=regime_a,
    palette=palette_a,
    labels=labels_a,
)
ax.set_title("Pattern A: S&P500 累積対数リターン + 市場レジーム")
ax.set_ylabel("Cumulative log return")
ax.legend(loc="upper left")
plt.tight_layout()
plt.show()
```

16. **Markdown**: `## レジーム別の平均リターン・年率ボラ（パターン A）`

17. **Code**:
```python
stats_a = []
for i in range(3):
    mask = (regime_a == i)
    mean_ret = y[mask].mean() * 52  # 年率
    vol = y[mask].std() * np.sqrt(52)
    stats_a.append({
        "regime": label_map_a[i],
        "weeks": mask.sum(),
        "annualized_mean": mean_ret,
        "annualized_vol": vol,
        "sharpe": mean_ret / vol if vol > 0 else np.nan,
    })
pd.DataFrame(stats_a).round(3)
```

18. **Markdown**: `## パターン B: スムーズ確率と可視化`

19. **Code**:
```python
smooth_b = pd.DataFrame(
    res_b.smoothed_marginal_probabilities,
    index=y.index,
    columns=[f"regime_{i}" for i in range(3)],
)
state_means_b = []
for i in range(3):
    weights = smooth_b[f"regime_{i}"].values
    weighted_mean = (y.values * weights).sum() / weights.sum()
    state_means_b.append((i, weighted_mean))
state_means_b.sort(key=lambda x: x[1], reverse=True)
label_map_b = {state_means_b[0][0]: "上昇", state_means_b[1][0]: "中立", state_means_b[2][0]: "下落"}
print("Pattern B labels:", label_map_b)

regime_b = pd.Series(smooth_b.values.argmax(axis=1), index=smooth_b.index)
palette_b = {sid: palette_market[label_map_b[sid]] for sid in range(3)}
labels_b = {sid: label_map_b[sid] for sid in range(3)}

fig, ax = plt.subplots(figsize=(14, 5))
h.plot_regime_overlay(
    ax=ax,
    series=cum_ret,
    regimes=regime_b,
    palette=palette_b,
    labels=labels_b,
)
ax.set_title("Pattern B (PCA): S&P500 累積対数リターン + 市場レジーム")
ax.set_ylabel("Cumulative log return")
ax.legend(loc="upper left")
plt.tight_layout()
plt.show()
```

20. **Markdown**: `## 結果の保存`

21. **Code**:
```python
out_a = pd.DataFrame({
    "regime_id": regime_a,
    "regime": regime_a_labeled,
}).join(smooth_a_labeled)
out_b = pd.DataFrame({
    "regime_id": regime_b,
    "regime": regime_b.map(label_map_b),
}).join(
    smooth_b.rename(columns={f"regime_{i}": label_map_b[i] for i in range(3)})
)
out_a.to_parquet(h.DATA_DIR / "market_regime_ms_pattern_a.parquet")
out_b.to_parquet(h.DATA_DIR / "market_regime_ms_pattern_b.parquet")
print("Saved both patterns.")
```

- [ ] **Step 2: nbformat 検証**

Run:
```bash
uv run python -c "import nbformat; nb = nbformat.read('notebook/REGIME_SWITCHING/03_market_regime_ms.ipynb', as_version=4); nbformat.validate(nb); print(f'cells: {len(nb.cells)}')"
```

Expected: エラーなし。

- [ ] **Step 3: notebook を実行**

Run:
```bash
uv run jupyter nbconvert --to notebook --execute notebook/REGIME_SWITCHING/03_market_regime_ms.ipynb --output 03_market_regime_ms.ipynb --ExecutePreprocessor.timeout=900
```

Expected: 実行成功（収束に時間がかかる場合あり）。両パターンで BIC が表示され、両 parquet が出力される。
収束失敗時は `search_reps=20` に増やして再実行。

- [ ] **Step 4: コミット**

```bash
git add notebook/REGIME_SWITCHING/03_market_regime_ms.ipynb
git commit -m "feat(regime-switching): 03 市場レジーム MS 回帰 (パターンA/B) notebook を追加"
```

---

## Task 10: `04_comparison.ipynb` — モデル①②の対応分析

**Files:**
- Create: `notebook/REGIME_SWITCHING/04_comparison.ipynb`

- [ ] **Step 1: notebook を作成**

セル構成:

1. **Markdown**: `# 04 Comparison: 経済レジーム vs 市場レジーム\n\nモデル① (HMM) とモデル② パターン B (MS+PCA) のレジーム対応を分析する。`

2. **Code** (imports):
```python
from __future__ import annotations
import sys
from pathlib import Path

NOTEBOOK_DIR = Path.cwd()
if str(NOTEBOOK_DIR) not in sys.path:
    sys.path.insert(0, str(NOTEBOOK_DIR))

import _helpers as h
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

sns.set_theme(style="whitegrid")
```

3. **Markdown**: `## 各モデルの結果を読み込み`

4. **Code**:
```python
econ = pd.read_parquet(h.DATA_DIR / "economic_regime_hmm.parquet")
market_b = pd.read_parquet(h.DATA_DIR / "market_regime_ms_pattern_b.parquet")
print(f"Economic: {econ.shape}, Market(B): {market_b.shape}")

# 共通インデックスに揃える
common_idx = econ.index.intersection(market_b.index)
econ = econ.loc[common_idx]
market_b = market_b.loc[common_idx]
print(f"Common range: {common_idx.min().date()} 〜 {common_idx.max().date()}, n={len(common_idx)}")
```

5. **Markdown**: `## クロス集計表（経済 × 市場レジーム）`

6. **Code**:
```python
cross = pd.crosstab(
    econ["regime"],
    market_b["regime"],
    normalize="index",  # 経済レジーム行で正規化
)
fig, ax = plt.subplots(figsize=(7, 5))
sns.heatmap(cross, annot=True, fmt=".2%", cmap="Blues", ax=ax)
ax.set_title("経済レジーム別の市場レジーム分布")
ax.set_xlabel("市場レジーム (MS+PCA)")
ax.set_ylabel("経済レジーム (HMM)")
plt.tight_layout()
plt.show()
```

7. **Markdown**: `## 同一時間軸での並列表示`

8. **Code**:
```python
econ_palette = {"拡大": "#aec7e8", "減速": "#ffbb78", "後退・ストレス": "#ff9896"}
market_palette = {"上昇": "#aec7e8", "中立": "#ffbb78", "下落": "#ff9896"}

# 各週のレジームを縦に並べた帯チャート
fig, axes = plt.subplots(2, 1, figsize=(14, 4), sharex=True)

# 経済レジーム
for label, color in econ_palette.items():
    mask = (econ["regime"] == label)
    axes[0].fill_between(
        econ.index,
        0, 1,
        where=mask,
        color=color,
        alpha=0.6,
        label=label,
    )
axes[0].set_title("経済レジーム (HMM)")
axes[0].set_yticks([])
axes[0].legend(loc="upper right", ncol=3)

# 市場レジーム
for label, color in market_palette.items():
    mask = (market_b["regime"] == label)
    axes[1].fill_between(
        market_b.index,
        0, 1,
        where=mask,
        color=color,
        alpha=0.6,
        label=label,
    )
axes[1].set_title("市場レジーム (MS+PCA)")
axes[1].set_yticks([])
axes[1].legend(loc="upper right", ncol=3)

plt.tight_layout()
plt.show()
```

9. **Markdown**: `## NBER 景気後退期との比較`

10. **Code**:
```python
from market.fred import HistoricalCache

cache = HistoricalCache()
try:
    cache.sync_series("USREC")
    nber = cache.get_series_df("USREC")["value"]
    # 週次に揃える
    nber_weekly = nber.resample("W-FRI").last().ffill()
    nber_aligned = nber_weekly.reindex(common_idx).fillna(0)
    has_nber = True
except Exception as e:
    print(f"NBER series unavailable: {e}")
    has_nber = False
```

11. **Code**:
```python
if has_nber:
    fig, axes = plt.subplots(3, 1, figsize=(14, 6), sharex=True)

    for label, color in econ_palette.items():
        mask = (econ["regime"] == label)
        axes[0].fill_between(econ.index, 0, 1, where=mask, color=color, alpha=0.6, label=label)
    axes[0].set_title("経済レジーム (HMM)")
    axes[0].set_yticks([])
    axes[0].legend(loc="upper right", ncol=3)

    for label, color in market_palette.items():
        mask = (market_b["regime"] == label)
        axes[1].fill_between(market_b.index, 0, 1, where=mask, color=color, alpha=0.6, label=label)
    axes[1].set_title("市場レジーム (MS+PCA)")
    axes[1].set_yticks([])
    axes[1].legend(loc="upper right", ncol=3)

    axes[2].fill_between(nber_aligned.index, 0, 1, where=(nber_aligned > 0), color="#999999", alpha=0.6)
    axes[2].set_title("NBER 景気後退期")
    axes[2].set_yticks([])

    plt.tight_layout()
    plt.show()
else:
    print("NBER plot skipped.")
```

12. **Markdown**: `## サマリ\n\n- 経済レジームと市場レジームの一致度（同名ラベルでの一致率）\n- NBER 後退期に各モデルがどのレジームを割り当てたか`

13. **Code**:
```python
# 経済 vs 市場の名前マッピング（直感的対応）
econ_to_market = {"拡大": "上昇", "減速": "中立", "後退・ストレス": "下落"}
match = (
    econ["regime"].map(econ_to_market) == market_b["regime"]
).mean()
print(f"経済レジーム → 期待される市場レジームへの一致率: {match:.2%}")

if has_nber:
    nber_weeks = (nber_aligned > 0)
    print(f"\nNBER 後退期 ({nber_weeks.sum()} 週) における分布:")
    print("経済レジーム:")
    print(econ.loc[nber_weeks, "regime"].value_counts(normalize=True).round(3))
    print("\n市場レジーム:")
    print(market_b.loc[nber_weeks, "regime"].value_counts(normalize=True).round(3))
```

- [ ] **Step 2: nbformat 検証**

Run:
```bash
uv run python -c "import nbformat; nb = nbformat.read('notebook/REGIME_SWITCHING/04_comparison.ipynb', as_version=4); nbformat.validate(nb); print(f'cells: {len(nb.cells)}')"
```

Expected: エラーなし。

- [ ] **Step 3: notebook を実行**

Run:
```bash
uv run jupyter nbconvert --to notebook --execute notebook/REGIME_SWITCHING/04_comparison.ipynb --output 04_comparison.ipynb --ExecutePreprocessor.timeout=300
```

Expected: 実行成功、クロス集計と一致率が出力される。

- [ ] **Step 4: コミット**

```bash
git add notebook/REGIME_SWITCHING/04_comparison.ipynb
git commit -m "feat(regime-switching): 04 モデル①②比較 notebook を追加"
```

---

## Task 11: README.md と最終品質チェック

**Files:**
- Create: `notebook/REGIME_SWITCHING/README.md`

- [ ] **Step 1: README.md を作成**

`notebook/REGIME_SWITCHING/README.md`:

```markdown
# REGIME_SWITCHING — レジームスイッチングモデル検証

FRED 7 系列を用いた米国経済レジーム抽出（HMM）と、S&P500 週次リターンの市場レジーム回帰（Markov-Switching Regression）を比較する notebook 一式。

## 前提条件

- `FRED_API_KEY` 環境変数が `.env` に設定されていること
- インターネット接続（yfinance 経由で `^GSPC` を取得）
- `hmmlearn`、`statsmodels`、`scikit-learn` が `uv sync` でインストール済み

## 実行手順

```bash
# 1. データ準備（FRED 取得・週次変換・標準化・S&P500 取得）
uv run jupyter nbconvert --to notebook --execute --inplace 01_data_preparation.ipynb

# 2. 経済レジーム抽出（多変量 Gaussian HMM, 3 状態）
uv run jupyter nbconvert --to notebook --execute --inplace 02_economic_regime_hmm.ipynb

# 3. 市場レジーム回帰（パターン A: 生 7 系列, パターン B: PCA 削減）
uv run jupyter nbconvert --to notebook --execute --inplace 03_market_regime_ms.ipynb

# 4. モデル①②の比較
uv run jupyter nbconvert --to notebook --execute --inplace 04_comparison.ipynb
```

Jupyter 上で対話的に実行する場合も同じ順序。

## ファイル構成

| ファイル | 役割 |
|---|---|
| `_helpers.py` | データ取得・前処理・可視化の共通関数 |
| `01_data_preparation.ipynb` | FRED 7 系列と S&P500 を取得・週次変換・標準化 |
| `02_economic_regime_hmm.ipynb` | 多変量 Gaussian HMM (3 状態) で経済レジーム抽出 |
| `03_market_regime_ms.ipynb` | MS 回帰 (パターン A / B) で市場レジーム抽出 |
| `04_comparison.ipynb` | モデル①②の対応分析と NBER 比較 |
| `data/` | 中間 parquet ファイル（gitignore 対象） |

## 設計と意思決定

- 仕様書: `docs/superpowers/specs/2026-05-23-regime-switching-notebook-design.md`
- 実装プラン: `docs/superpowers/plans/2026-05-23-regime-switching-notebook.md`

## 使用 FRED 系列

| ID | 名称 | 変換 |
|---|---|---|
| INDPRO | 鉱工業生産指数 | YoY % |
| ICSA | 新規失業保険申請件数 | 4 週 MA の YoY % |
| T10YIE | 10 年 BEI | レベル |
| CPIAUCSL | CPI | YoY % |
| STLFSI4 | セントルイス連銀金融ストレス指数 | レベル |
| BAA10Y | Baa - 10Y スプレッド | レベル |
| T10Y2Y | 10Y - 2Y スプレッド | レベル |
```

- [ ] **Step 2: 全体 quality check**

Run:
```bash
uv run ruff format notebook/REGIME_SWITCHING/_helpers.py tests/notebook/
uv run ruff check notebook/REGIME_SWITCHING/_helpers.py tests/notebook/
uv run pyright notebook/REGIME_SWITCHING/_helpers.py
uv run pytest tests/notebook/regime_switching/ -v
```

Expected:
- ruff: フォーマット適用、lint エラー 0
- pyright: 型エラー 0 (notebook と sys.path import の都合で warning が出る可能性はあるが、helpers.py 単体ではエラーなしを目指す)
- pytest: 全件 PASS

エラーがあれば修正してから次へ。

- [ ] **Step 3: 全 notebook の再実行確認（Restart → Run All 相当）**

Run:
```bash
for nb in 01_data_preparation 02_economic_regime_hmm 03_market_regime_ms 04_comparison; do
    echo "=== Running ${nb} ==="
    uv run jupyter nbconvert --to notebook --execute --inplace notebook/REGIME_SWITCHING/${nb}.ipynb --ExecutePreprocessor.timeout=900 || exit 1
done
echo "All notebooks executed successfully."
```

Expected: 全 notebook が連続実行成功し、最後に `All notebooks executed successfully.` が表示される。

- [ ] **Step 4: 最終コミット**

```bash
git add notebook/REGIME_SWITCHING/README.md notebook/REGIME_SWITCHING/*.ipynb
git commit -m "docs(regime-switching): README と最終実行済み notebook を追加"
```

---

## 完了基準

- [ ] `pyproject.toml` に `hmmlearn` が追加され、`uv sync` 成功
- [ ] `data/config/fred_series.json` に `INDPRO`, `BAA10Y` が追加されている
- [ ] `notebook/REGIME_SWITCHING/` に `_helpers.py` + 4 notebook + `README.md` + `data/.gitkeep` が存在
- [ ] `tests/notebook/regime_switching/test_helpers.py` の全テストが PASS
- [ ] 全 4 notebook が `Restart Kernel → Run All` 相当で再実行成功
- [ ] `uv run ruff check`, `uv run pyright` が `_helpers.py` でエラー 0
- [ ] 中間 parquet ファイル 5 個（fred_weekly_raw, features_weekly, sp500_weekly, economic_regime_hmm, market_regime_ms_pattern_a, market_regime_ms_pattern_b）が `notebook/REGIME_SWITCHING/data/` に生成される

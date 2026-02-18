"""単体テスト: ConfigRepository。

対象モジュール: src/dev/ca_strategy/_config.py

universe.json と benchmark_weights.json をロードし、UniverseConfig と
BenchmarkWeight のリストを返す ConfigRepository クラスを検証する。
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest

from dev.ca_strategy._config import ConfigRepository

if TYPE_CHECKING:
    from pathlib import Path


# =============================================================================
# Fixtures
# =============================================================================
@pytest.fixture
def valid_config_dir(tmp_path: Path) -> Path:
    """universe.json と benchmark_weights.json を含む有効なディレクトリを作成する。"""
    universe_data = {
        "tickers": [
            {"ticker": "AAPL", "gics_sector": "Information Technology"},
            {"ticker": "MSFT", "gics_sector": "Information Technology"},
            {"ticker": "JPM", "gics_sector": "Financials"},
        ]
    }
    benchmark_data = {
        "weights": {
            "Information Technology": 0.28,
            "Financials": 0.13,
            "Health Care": 0.12,
        }
    }
    (tmp_path / "universe.json").write_text(
        json.dumps(universe_data, ensure_ascii=False), encoding="utf-8"
    )
    (tmp_path / "benchmark_weights.json").write_text(
        json.dumps(benchmark_data, ensure_ascii=False), encoding="utf-8"
    )
    return tmp_path


@pytest.fixture
def universe_only_dir(tmp_path: Path) -> Path:
    """universe.json のみを含むディレクトリを作成する（benchmark_weights.json なし）。"""
    universe_data = {
        "tickers": [
            {"ticker": "AAPL", "gics_sector": "Information Technology"},
        ]
    }
    (tmp_path / "universe.json").write_text(
        json.dumps(universe_data, ensure_ascii=False), encoding="utf-8"
    )
    return tmp_path


@pytest.fixture
def benchmark_only_dir(tmp_path: Path) -> Path:
    """benchmark_weights.json のみを含むディレクトリを作成する（universe.json なし）。"""
    benchmark_data = {
        "weights": {
            "Information Technology": 0.28,
        }
    }
    (tmp_path / "benchmark_weights.json").write_text(
        json.dumps(benchmark_data, ensure_ascii=False), encoding="utf-8"
    )
    return tmp_path


# =============================================================================
# ConfigRepository.__init__
# =============================================================================
class TestConfigRepositoryInit:
    """ConfigRepository 初期化テスト。"""

    def test_正常系_有効なパスで初期化できる(self, valid_config_dir: Path) -> None:
        """有効な config_path で ConfigRepository が初期化されることを確認。"""
        repo = ConfigRepository(valid_config_dir)

        assert repo._config_path == valid_config_dir

    def test_正常系_ファイルを持たない空ディレクトリでも初期化できる(
        self, tmp_path: Path
    ) -> None:
        """空ディレクトリでも FileNotFoundError なしに初期化できることを確認。"""
        repo = ConfigRepository(tmp_path)

        assert repo._config_path == tmp_path

    def test_異常系_存在しないパスでFileNotFoundError(self, tmp_path: Path) -> None:
        """存在しないパスで FileNotFoundError が発生することを確認。"""
        non_existent = tmp_path / "non_existent_directory"

        with pytest.raises(FileNotFoundError, match="config_path does not exist"):
            ConfigRepository(non_existent)


# =============================================================================
# ConfigRepository.universe
# =============================================================================
class TestConfigRepositoryUniverse:
    """ConfigRepository.universe プロパティテスト。"""

    def test_正常系_有効なuniverse_jsonからUniverseConfigが返される(
        self, valid_config_dir: Path
    ) -> None:
        """有効な universe.json から UniverseConfig が返されることを確認。"""
        repo = ConfigRepository(valid_config_dir)

        universe = repo.universe

        assert universe is not None
        assert len(universe.tickers) == 3

    def test_正常系_tickersのtickerフィールドが正しく読み込まれる(
        self, valid_config_dir: Path
    ) -> None:
        """tickers の ticker フィールドが正しく読み込まれることを確認。"""
        repo = ConfigRepository(valid_config_dir)

        universe = repo.universe
        tickers = [t.ticker for t in universe.tickers]

        assert "AAPL" in tickers
        assert "MSFT" in tickers
        assert "JPM" in tickers

    def test_正常系_tickersのgics_sectorフィールドが正しく読み込まれる(
        self, valid_config_dir: Path
    ) -> None:
        """tickers の gics_sector フィールドが正しく読み込まれることを確認。"""
        repo = ConfigRepository(valid_config_dir)

        universe = repo.universe
        aapl = next(t for t in universe.tickers if t.ticker == "AAPL")

        assert aapl.gics_sector == "Information Technology"

    def test_正常系_universeは2回目の呼び出しでキャッシュされる(
        self, valid_config_dir: Path
    ) -> None:
        """universe プロパティが cached_property によりキャッシュされることを確認。"""
        repo = ConfigRepository(valid_config_dir)

        universe1 = repo.universe
        universe2 = repo.universe

        assert universe1 is universe2

    def test_異常系_universe_jsonが存在しない場合FileNotFoundError(
        self, benchmark_only_dir: Path
    ) -> None:
        """universe.json が存在しない場合に FileNotFoundError が発生することを確認。"""
        repo = ConfigRepository(benchmark_only_dir)

        with pytest.raises(FileNotFoundError, match=r"universe\.json not found"):
            _ = repo.universe

    def test_エッジケース_1ティッカーのみのuniverse_jsonが正しく読み込まれる(
        self, universe_only_dir: Path
    ) -> None:
        """1 ティッカーのみの universe.json が正しく読み込まれることを確認。"""
        repo = ConfigRepository(universe_only_dir)

        universe = repo.universe

        assert len(universe.tickers) == 1
        assert universe.tickers[0].ticker == "AAPL"


# =============================================================================
# ConfigRepository.benchmark
# =============================================================================
class TestConfigRepositoryBenchmark:
    """ConfigRepository.benchmark プロパティテスト。"""

    def test_正常系_有効なbenchmark_weights_jsonからリストが返される(
        self, valid_config_dir: Path
    ) -> None:
        """有効な benchmark_weights.json から BenchmarkWeight のリストが返されることを確認。"""
        repo = ConfigRepository(valid_config_dir)

        benchmark = repo.benchmark

        assert benchmark is not None
        assert len(benchmark) == 3

    def test_正常系_benchmarkのsectorフィールドが正しく読み込まれる(
        self, valid_config_dir: Path
    ) -> None:
        """benchmark の sector フィールドが正しく読み込まれることを確認。"""
        repo = ConfigRepository(valid_config_dir)

        benchmark = repo.benchmark
        sectors = [b.sector for b in benchmark]

        assert "Information Technology" in sectors
        assert "Financials" in sectors
        assert "Health Care" in sectors

    def test_正常系_benchmarkのweightフィールドが正しく読み込まれる(
        self, valid_config_dir: Path
    ) -> None:
        """benchmark の weight フィールドが正しく読み込まれることを確認。"""
        repo = ConfigRepository(valid_config_dir)

        benchmark = repo.benchmark
        it_weight = next(b for b in benchmark if b.sector == "Information Technology")

        assert it_weight.weight == pytest.approx(0.28)

    def test_正常系_benchmarkは2回目の呼び出しでキャッシュされる(
        self, valid_config_dir: Path
    ) -> None:
        """benchmark プロパティが cached_property によりキャッシュされることを確認。"""
        repo = ConfigRepository(valid_config_dir)

        benchmark1 = repo.benchmark
        benchmark2 = repo.benchmark

        assert benchmark1 is benchmark2

    def test_異常系_benchmark_weights_jsonが存在しない場合FileNotFoundError(
        self, universe_only_dir: Path
    ) -> None:
        """benchmark_weights.json が存在しない場合に FileNotFoundError が発生することを確認。"""
        repo = ConfigRepository(universe_only_dir)

        with pytest.raises(
            FileNotFoundError, match=r"benchmark_weights\.json not found"
        ):
            _ = repo.benchmark

    def test_エッジケース_1セクターのみのbenchmark_weights_jsonが正しく読み込まれる(
        self, benchmark_only_dir: Path
    ) -> None:
        """1 セクターのみの benchmark_weights.json が正しく読み込まれることを確認。"""
        repo = ConfigRepository(benchmark_only_dir)

        benchmark = repo.benchmark

        assert len(benchmark) == 1
        assert benchmark[0].sector == "Information Technology"
        assert benchmark[0].weight == pytest.approx(0.28)

    def test_エッジケース_複数セクターの順序が保たれる(
        self, valid_config_dir: Path
    ) -> None:
        """BenchmarkWeight のリストが JSON の順序を保つことを確認。"""
        repo = ConfigRepository(valid_config_dir)

        benchmark = repo.benchmark

        assert benchmark[0].sector == "Information Technology"
        assert benchmark[1].sector == "Financials"
        assert benchmark[2].sector == "Health Care"


# =============================================================================
# ConfigRepository 統合テスト（両プロパティの同時利用）
# =============================================================================
class TestConfigRepositoryIntegration:
    """ConfigRepository の universe と benchmark を同時に使用するテスト。"""

    def test_正常系_universeとbenchmarkを同時に読み込める(
        self, valid_config_dir: Path
    ) -> None:
        """universe と benchmark を同時に読み込めることを確認。"""
        repo = ConfigRepository(valid_config_dir)

        universe = repo.universe
        benchmark = repo.benchmark

        assert len(universe.tickers) > 0
        assert len(benchmark) > 0

    def test_正常系_別インスタンスは独立したキャッシュを持つ(
        self, valid_config_dir: Path
    ) -> None:
        """別のインスタンスはそれぞれ独立したキャッシュを持つことを確認。"""
        repo1 = ConfigRepository(valid_config_dir)
        repo2 = ConfigRepository(valid_config_dir)

        universe1 = repo1.universe
        universe2 = repo2.universe

        assert universe1 is not universe2
        assert len(universe1.tickers) == len(universe2.tickers)

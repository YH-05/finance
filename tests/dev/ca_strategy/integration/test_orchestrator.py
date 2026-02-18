"""Integration tests for ca_strategy orchestrator module.

Tests the Orchestrator with real file I/O but mocked LLM calls.
Verifies end-to-end flow including config loading, checkpoint
persistence, and execution log management.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest

from dev.ca_strategy.orchestrator import Orchestrator

if TYPE_CHECKING:
    from pathlib import Path


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture()
def full_config_dir(tmp_path: Path) -> Path:
    """Create config dir with universe and benchmark data."""
    config = tmp_path / "config"
    config.mkdir()

    universe_data = {
        "tickers": [
            {"ticker": "AAPL", "gics_sector": "Information Technology"},
            {"ticker": "MSFT", "gics_sector": "Information Technology"},
            {"ticker": "JPM", "gics_sector": "Financials"},
        ]
    }
    (config / "universe.json").write_text(
        json.dumps(universe_data, ensure_ascii=False, indent=2)
    )

    benchmark_data = {
        "weights": {
            "Information Technology": 0.60,
            "Financials": 0.40,
        }
    }
    (config / "benchmark_weights.json").write_text(
        json.dumps(benchmark_data, ensure_ascii=False, indent=2)
    )

    return config


@pytest.fixture()
def full_kb_dir(tmp_path: Path) -> Path:
    """Create KB directory structure."""
    kb = tmp_path / "kb"
    kb.mkdir()
    (kb / "kb1_rules_transcript").mkdir()
    (kb / "kb2_patterns_transcript").mkdir()
    (kb / "kb3_fewshot_transcript").mkdir()
    (kb / "system_prompt_transcript.md").write_text("system prompt")
    (kb / "dogma.md").write_text("dogma content")
    return kb


@pytest.fixture()
def full_workspace_dir(tmp_path: Path) -> Path:
    """Create workspace directory."""
    ws = tmp_path / "workspace"
    ws.mkdir()
    return ws


# ===========================================================================
# Config loading integration
# ===========================================================================
class TestConfigLoadingIntegration:
    """Config loading from real JSON files via ConfigRepository."""

    def test_正常系_configファイルからuniverseとbenchmarkを読み込める(
        self,
        full_config_dir: Path,
        full_kb_dir: Path,
        full_workspace_dir: Path,
    ) -> None:
        orch = Orchestrator(
            config_path=full_config_dir,
            kb_base_dir=full_kb_dir,
            workspace_dir=full_workspace_dir,
        )

        universe = orch._config.universe
        benchmark = orch._config.benchmark

        assert len(universe.tickers) == 3
        assert len(benchmark) == 2

        tickers = {t.ticker for t in universe.tickers}
        assert "AAPL" in tickers
        assert "JPM" in tickers

        sectors = {bw.sector for bw in benchmark}
        assert "Information Technology" in sectors
        assert "Financials" in sectors


# ===========================================================================
# Execution log integration
# ===========================================================================
class TestExecutionLogIntegration:
    """Execution log file I/O integration."""

    def test_正常系_execution_logが正しいJSON形式で保存される(
        self,
        full_config_dir: Path,
        full_kb_dir: Path,
        full_workspace_dir: Path,
    ) -> None:
        orch = Orchestrator(
            config_path=full_config_dir,
            kb_base_dir=full_kb_dir,
            workspace_dir=full_workspace_dir,
        )

        orch._save_execution_log("phase1", "completed", None)
        orch._save_execution_log("phase2", "failed", "API error")

        log_path = full_workspace_dir / "execution_log.json"
        assert log_path.exists()

        data = json.loads(log_path.read_text())
        assert "phases" in data
        assert len(data["phases"]) == 2

        p1 = data["phases"][0]
        assert p1["phase"] == "phase1"
        assert p1["status"] == "completed"
        assert p1["error"] is None

        p2 = data["phases"][1]
        assert p2["phase"] == "phase2"
        assert p2["status"] == "failed"
        assert p2["error"] == "API error"

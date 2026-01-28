"""Unit tests for CollectionHistory and related models.

TDD Red phase: These tests will fail until the implementation is complete.
Issue #1720: 収集履歴の記録と統計機能

Tests cover:
- SourceStats model (success_count, error_count, article_count)
- SinkResult model (success, additional metadata)
- CollectionRun model (run_id, started_at, completed_at, sources, sinks)
- CollectionHistory class (add_run, get_latest_runs, get_statistics, save/load)
"""

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from uuid import UUID

import pytest

# These imports will fail until the implementation is created
from news.core.history import (
    CollectionHistory,
    CollectionRun,
    SinkResult,
    SourceStats,
)


class TestSourceStatsModel:
    """Test SourceStats model for tracking source-level statistics."""

    def test_正常系_全フィールドで作成できる(self) -> None:
        """SourceStatsを全フィールドで作成できることを確認。"""
        stats = SourceStats(
            success_count=50,
            error_count=2,
            article_count=480,
        )

        assert stats.success_count == 50
        assert stats.error_count == 2
        assert stats.article_count == 480

    def test_正常系_デフォルト値で作成できる(self) -> None:
        """SourceStatsをデフォルト値で作成できることを確認。"""
        stats = SourceStats()

        assert stats.success_count == 0
        assert stats.error_count == 0
        assert stats.article_count == 0

    def test_正常系_total_countプロパティが正しい(self) -> None:
        """total_countがsuccess_count + error_countを返すことを確認。"""
        stats = SourceStats(
            success_count=50,
            error_count=2,
            article_count=480,
        )

        assert stats.total_count == 52

    def test_正常系_success_rateプロパティが正しい(self) -> None:
        """success_rateが正しい比率を返すことを確認。"""
        stats = SourceStats(
            success_count=50,
            error_count=50,
            article_count=480,
        )

        assert stats.success_rate == 0.5

    def test_エッジケース_全て0の場合のsuccess_rate(self) -> None:
        """total_countが0の場合、success_rateが1.0を返すことを確認。"""
        stats = SourceStats()

        # ゼロ除算を避けるため、total_count=0の場合は1.0を返す
        assert stats.success_rate == 1.0

    def test_異常系_負の値でValidationError(self) -> None:
        """負の値でSourceStatsを作成するとValidationErrorが発生することを確認。"""
        with pytest.raises(ValueError, match="success_count"):
            SourceStats(success_count=-1, error_count=0, article_count=0)

        with pytest.raises(ValueError, match="error_count"):
            SourceStats(success_count=0, error_count=-1, article_count=0)

        with pytest.raises(ValueError, match="article_count"):
            SourceStats(success_count=0, error_count=0, article_count=-1)

    def test_正常系_JSONシリアライズできる(self) -> None:
        """SourceStatsをJSONにシリアライズできることを確認。"""
        stats = SourceStats(
            success_count=50,
            error_count=2,
            article_count=480,
        )
        json_str = stats.model_dump_json()

        assert "50" in json_str
        assert "2" in json_str
        assert "480" in json_str

    def test_正常系_JSONからデシリアライズできる(self) -> None:
        """JSONからSourceStatsをデシリアライズできることを確認。"""
        json_data = '{"success_count": 100, "error_count": 5, "article_count": 950}'
        stats = SourceStats.model_validate_json(json_data)

        assert stats.success_count == 100
        assert stats.error_count == 5
        assert stats.article_count == 950


class TestSinkResultModel:
    """Test SinkResult model for tracking sink operation results."""

    def test_正常系_成功結果を作成できる(self) -> None:
        """成功したSinkResultを作成できることを確認。"""
        result = SinkResult(success=True)

        assert result.success is True
        assert result.metadata == {}

    def test_正常系_失敗結果を作成できる(self) -> None:
        """失敗したSinkResultを作成できることを確認。"""
        result = SinkResult(success=False, error_message="Connection timeout")

        assert result.success is False
        assert result.error_message == "Connection timeout"

    def test_正常系_メタデータ付きで作成できる(self) -> None:
        """メタデータ付きでSinkResultを作成できることを確認。"""
        result = SinkResult(
            success=True,
            metadata={"issues_created": 10, "pr_created": True},
        )

        assert result.success is True
        assert result.metadata["issues_created"] == 10
        assert result.metadata["pr_created"] is True

    def test_正常系_GitHub結果の典型例(self) -> None:
        """GitHub Sink の典型的な結果を作成できることを確認。"""
        result = SinkResult(
            success=True,
            metadata={
                "issues_created": 10,
                "issues_updated": 5,
                "project_items_added": 15,
            },
        )

        assert result.success is True
        assert result.metadata["issues_created"] == 10

    def test_正常系_File結果の典型例(self) -> None:
        """File Sink の典型的な結果を作成できることを確認。"""
        result = SinkResult(
            success=True,
            metadata={
                "file_path": "/data/articles/2026-01-28.json",
                "articles_written": 100,
                "file_size_bytes": 102400,
            },
        )

        assert result.success is True
        assert result.metadata["articles_written"] == 100

    def test_正常系_JSONシリアライズできる(self) -> None:
        """SinkResultをJSONにシリアライズできることを確認。"""
        result = SinkResult(
            success=True,
            metadata={"issues_created": 10},
        )
        json_str = result.model_dump_json()

        assert "true" in json_str.lower()
        assert "issues_created" in json_str

    def test_正常系_JSONからデシリアライズできる(self) -> None:
        """JSONからSinkResultをデシリアライズできることを確認。"""
        json_data = (
            '{"success": false, "error_message": "API rate limit", "metadata": {}}'
        )
        result = SinkResult.model_validate_json(json_data)

        assert result.success is False
        assert result.error_message == "API rate limit"


class TestCollectionRunModel:
    """Test CollectionRun model for tracking a single collection execution."""

    @pytest.fixture
    def sample_sources(self) -> dict[str, SourceStats]:
        """サンプルのソース統計を提供するフィクスチャ。"""
        return {
            "yfinance_ticker": SourceStats(
                success_count=50,
                error_count=2,
                article_count=480,
            ),
            "rss": SourceStats(
                success_count=10,
                error_count=0,
                article_count=100,
            ),
        }

    @pytest.fixture
    def sample_sinks(self) -> dict[str, SinkResult]:
        """サンプルのシンク結果を提供するフィクスチャ。"""
        return {
            "file": SinkResult(success=True),
            "github": SinkResult(
                success=True,
                metadata={"issues_created": 10},
            ),
        }

    def test_正常系_全フィールドで作成できる(
        self,
        sample_sources: dict[str, SourceStats],
        sample_sinks: dict[str, SinkResult],
    ) -> None:
        """CollectionRunを全フィールドで作成できることを確認。"""
        started_at = datetime(2026, 1, 28, 12, 0, 0, tzinfo=timezone.utc)
        completed_at = datetime(2026, 1, 28, 12, 5, 0, tzinfo=timezone.utc)

        run = CollectionRun(
            run_id="550e8400-e29b-41d4-a716-446655440000",
            started_at=started_at,
            completed_at=completed_at,
            sources=sample_sources,
            sinks=sample_sinks,
        )

        assert run.run_id == "550e8400-e29b-41d4-a716-446655440000"
        assert run.started_at == started_at
        assert run.completed_at == completed_at
        assert len(run.sources) == 2
        assert len(run.sinks) == 2

    def test_正常系_run_idが自動生成される(
        self,
        sample_sources: dict[str, SourceStats],
        sample_sinks: dict[str, SinkResult],
    ) -> None:
        """run_idを指定しない場合、自動生成されることを確認。"""
        run = CollectionRun(
            started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
            sources=sample_sources,
            sinks=sample_sinks,
        )

        # UUIDとして有効であることを確認
        assert run.run_id is not None
        UUID(run.run_id)  # 無効なUUIDの場合は例外発生

    def test_正常系_durationプロパティが正しい(
        self,
        sample_sources: dict[str, SourceStats],
        sample_sinks: dict[str, SinkResult],
    ) -> None:
        """durationが正しい実行時間を返すことを確認。"""
        started_at = datetime(2026, 1, 28, 12, 0, 0, tzinfo=timezone.utc)
        completed_at = datetime(2026, 1, 28, 12, 5, 0, tzinfo=timezone.utc)

        run = CollectionRun(
            started_at=started_at,
            completed_at=completed_at,
            sources=sample_sources,
            sinks=sample_sinks,
        )

        assert run.duration == timedelta(minutes=5)
        assert run.duration_seconds == 300

    def test_正常系_total_article_countプロパティが正しい(
        self,
        sample_sources: dict[str, SourceStats],
        sample_sinks: dict[str, SinkResult],
    ) -> None:
        """total_article_countが全ソースの記事数合計を返すことを確認。"""
        run = CollectionRun(
            started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
            sources=sample_sources,
            sinks=sample_sinks,
        )

        # yfinance_ticker: 480 + rss: 100 = 580
        assert run.total_article_count == 580

    def test_正常系_total_error_countプロパティが正しい(
        self,
        sample_sources: dict[str, SourceStats],
        sample_sinks: dict[str, SinkResult],
    ) -> None:
        """total_error_countが全ソースのエラー数合計を返すことを確認。"""
        run = CollectionRun(
            started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
            sources=sample_sources,
            sinks=sample_sinks,
        )

        # yfinance_ticker: 2 + rss: 0 = 2
        assert run.total_error_count == 2

    def test_正常系_is_successfulプロパティが正しい(
        self,
        sample_sources: dict[str, SourceStats],
    ) -> None:
        """is_successfulが全Sinkの成功状態を反映することを確認。"""
        # 全Sink成功
        run_success = CollectionRun(
            started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
            sources=sample_sources,
            sinks={
                "file": SinkResult(success=True),
                "github": SinkResult(success=True),
            },
        )
        assert run_success.is_successful is True

        # 一部Sink失敗
        run_partial = CollectionRun(
            started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
            sources=sample_sources,
            sinks={
                "file": SinkResult(success=True),
                "github": SinkResult(success=False, error_message="Rate limit"),
            },
        )
        assert run_partial.is_successful is False

    def test_エッジケース_空のsourcesとsinks(self) -> None:
        """sourcesとsinksが空でも作成できることを確認。"""
        run = CollectionRun(
            started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
            sources={},
            sinks={},
        )

        assert run.total_article_count == 0
        assert run.total_error_count == 0
        assert run.is_successful is True  # 空の場合は成功とみなす

    def test_正常系_JSONシリアライズできる(
        self,
        sample_sources: dict[str, SourceStats],
        sample_sinks: dict[str, SinkResult],
    ) -> None:
        """CollectionRunをJSONにシリアライズできることを確認。"""
        run = CollectionRun(
            run_id="550e8400-e29b-41d4-a716-446655440000",
            started_at=datetime(2026, 1, 28, 12, 0, 0, tzinfo=timezone.utc),
            completed_at=datetime(2026, 1, 28, 12, 5, 0, tzinfo=timezone.utc),
            sources=sample_sources,
            sinks=sample_sinks,
        )
        json_str = run.model_dump_json()

        assert "550e8400-e29b-41d4-a716-446655440000" in json_str
        assert "yfinance_ticker" in json_str
        assert "github" in json_str

    def test_正常系_JSONからデシリアライズできる(self) -> None:
        """JSONからCollectionRunをデシリアライズできることを確認。"""
        json_data = """
        {
            "run_id": "550e8400-e29b-41d4-a716-446655440000",
            "started_at": "2026-01-28T12:00:00Z",
            "completed_at": "2026-01-28T12:05:00Z",
            "sources": {
                "yfinance_ticker": {
                    "success_count": 50,
                    "error_count": 2,
                    "article_count": 480
                }
            },
            "sinks": {
                "file": {"success": true, "metadata": {}},
                "github": {"success": true, "metadata": {"issues_created": 10}}
            }
        }
        """
        run = CollectionRun.model_validate_json(json_data)

        assert run.run_id == "550e8400-e29b-41d4-a716-446655440000"
        assert run.sources["yfinance_ticker"].article_count == 480
        assert run.sinks["github"].metadata["issues_created"] == 10


class TestCollectionHistoryClass:
    """Test CollectionHistory class for managing collection run history."""

    @pytest.fixture
    def sample_run(self) -> CollectionRun:
        """サンプルのCollectionRunを提供するフィクスチャ。"""
        return CollectionRun(
            run_id="run-001",
            started_at=datetime(2026, 1, 28, 12, 0, 0, tzinfo=timezone.utc),
            completed_at=datetime(2026, 1, 28, 12, 5, 0, tzinfo=timezone.utc),
            sources={
                "yfinance_ticker": SourceStats(
                    success_count=50,
                    error_count=2,
                    article_count=480,
                ),
            },
            sinks={
                "file": SinkResult(success=True),
            },
        )

    @pytest.fixture
    def multiple_runs(self) -> list[CollectionRun]:
        """複数のCollectionRunを提供するフィクスチャ。"""
        base_time = datetime(2026, 1, 28, 12, 0, 0, tzinfo=timezone.utc)
        runs = []
        for i in range(5):
            runs.append(
                CollectionRun(
                    run_id=f"run-{i:03d}",
                    started_at=base_time + timedelta(hours=i),
                    completed_at=base_time + timedelta(hours=i, minutes=5),
                    sources={
                        "yfinance_ticker": SourceStats(
                            success_count=50 + i * 10,
                            error_count=i,
                            article_count=480 + i * 100,
                        ),
                    },
                    sinks={
                        "file": SinkResult(success=True),
                    },
                )
            )
        return runs

    def test_正常系_空のHistoryを作成できる(self) -> None:
        """空のCollectionHistoryを作成できることを確認。"""
        history = CollectionHistory()

        assert len(history) == 0
        assert history.runs == []

    def test_正常系_add_runでRunを追加できる(self, sample_run: CollectionRun) -> None:
        """add_runでCollectionRunを追加できることを確認。"""
        history = CollectionHistory()
        history.add_run(sample_run)

        assert len(history) == 1
        assert history.runs[0].run_id == "run-001"

    def test_正常系_複数のRunを追加できる(
        self, multiple_runs: list[CollectionRun]
    ) -> None:
        """複数のCollectionRunを追加できることを確認。"""
        history = CollectionHistory()
        for run in multiple_runs:
            history.add_run(run)

        assert len(history) == 5

    def test_正常系_get_latest_runsで最新のRunを取得できる(
        self, multiple_runs: list[CollectionRun]
    ) -> None:
        """get_latest_runsで指定数の最新Runを取得できることを確認。"""
        history = CollectionHistory()
        for run in multiple_runs:
            history.add_run(run)

        latest = history.get_latest_runs(3)

        assert len(latest) == 3
        # 最新（started_atが新しい順）でソートされていることを確認
        assert latest[0].run_id == "run-004"
        assert latest[1].run_id == "run-003"
        assert latest[2].run_id == "run-002"

    def test_正常系_get_latest_runsで全件取得(
        self, multiple_runs: list[CollectionRun]
    ) -> None:
        """get_latest_runsで件数以上を指定すると全件取得されることを確認。"""
        history = CollectionHistory()
        for run in multiple_runs:
            history.add_run(run)

        latest = history.get_latest_runs(100)

        assert len(latest) == 5

    def test_エッジケース_空のHistoryでget_latest_runs(self) -> None:
        """空のHistoryでget_latest_runsが空リストを返すことを確認。"""
        history = CollectionHistory()

        latest = history.get_latest_runs(10)

        assert latest == []

    def test_正常系_get_run_by_idでRunを取得できる(
        self, multiple_runs: list[CollectionRun]
    ) -> None:
        """get_run_by_idで特定のRunを取得できることを確認。"""
        history = CollectionHistory()
        for run in multiple_runs:
            history.add_run(run)

        run = history.get_run_by_id("run-002")

        assert run is not None
        assert run.run_id == "run-002"

    def test_エッジケース_存在しないrun_idでget_run_by_id(
        self, sample_run: CollectionRun
    ) -> None:
        """存在しないrun_idでget_run_by_idがNoneを返すことを確認。"""
        history = CollectionHistory()
        history.add_run(sample_run)

        run = history.get_run_by_id("non-existent")

        assert run is None


class TestCollectionHistoryStatistics:
    """Test CollectionHistory statistics calculation."""

    @pytest.fixture
    def history_with_runs(self) -> CollectionHistory:
        """統計計算用のHistoryを提供するフィクスチャ。"""
        history = CollectionHistory()
        base_time = datetime(2026, 1, 28, 12, 0, 0, tzinfo=timezone.utc)

        # Run 1: 成功
        history.add_run(
            CollectionRun(
                run_id="run-001",
                started_at=base_time,
                completed_at=base_time + timedelta(minutes=5),
                sources={
                    "yfinance_ticker": SourceStats(
                        success_count=50,
                        error_count=2,
                        article_count=480,
                    ),
                    "rss": SourceStats(
                        success_count=10,
                        error_count=0,
                        article_count=100,
                    ),
                },
                sinks={
                    "file": SinkResult(success=True),
                    "github": SinkResult(success=True, metadata={"issues_created": 10}),
                },
            )
        )

        # Run 2: 部分失敗
        history.add_run(
            CollectionRun(
                run_id="run-002",
                started_at=base_time + timedelta(hours=1),
                completed_at=base_time + timedelta(hours=1, minutes=3),
                sources={
                    "yfinance_ticker": SourceStats(
                        success_count=40,
                        error_count=10,
                        article_count=380,
                    ),
                },
                sinks={
                    "file": SinkResult(success=True),
                    "github": SinkResult(success=False, error_message="Rate limit"),
                },
            )
        )

        # Run 3: 成功
        history.add_run(
            CollectionRun(
                run_id="run-003",
                started_at=base_time + timedelta(hours=2),
                completed_at=base_time + timedelta(hours=2, minutes=4),
                sources={
                    "yfinance_ticker": SourceStats(
                        success_count=55,
                        error_count=1,
                        article_count=520,
                    ),
                },
                sinks={
                    "file": SinkResult(success=True),
                    "github": SinkResult(success=True, metadata={"issues_created": 15}),
                },
            )
        )

        return history

    def test_正常系_get_statisticsで統計を取得できる(
        self, history_with_runs: CollectionHistory
    ) -> None:
        """get_statisticsで統計情報を取得できることを確認。"""
        stats = history_with_runs.get_statistics()

        assert "total_runs" in stats
        assert "successful_runs" in stats
        assert "failed_runs" in stats
        assert "total_articles" in stats
        assert "total_errors" in stats
        assert "average_duration_seconds" in stats
        assert "success_rate" in stats

    def test_正常系_total_runsが正しい(
        self, history_with_runs: CollectionHistory
    ) -> None:
        """total_runsが正しい値を返すことを確認。"""
        stats = history_with_runs.get_statistics()

        assert stats["total_runs"] == 3

    def test_正常系_successful_runsが正しい(
        self, history_with_runs: CollectionHistory
    ) -> None:
        """successful_runsが正しい値を返すことを確認。"""
        stats = history_with_runs.get_statistics()

        # run-001とrun-003が成功（全Sinkが成功）
        assert stats["successful_runs"] == 2

    def test_正常系_failed_runsが正しい(
        self, history_with_runs: CollectionHistory
    ) -> None:
        """failed_runsが正しい値を返すことを確認。"""
        stats = history_with_runs.get_statistics()

        # run-002は失敗（GitHub Sinkが失敗）
        assert stats["failed_runs"] == 1

    def test_正常系_total_articlesが正しい(
        self, history_with_runs: CollectionHistory
    ) -> None:
        """total_articlesが正しい値を返すことを確認。"""
        stats = history_with_runs.get_statistics()

        # run-001: 480+100=580, run-002: 380, run-003: 520
        # total = 1480
        assert stats["total_articles"] == 1480

    def test_正常系_total_errorsが正しい(
        self, history_with_runs: CollectionHistory
    ) -> None:
        """total_errorsが正しい値を返すことを確認。"""
        stats = history_with_runs.get_statistics()

        # run-001: 2+0=2, run-002: 10, run-003: 1
        # total = 13
        assert stats["total_errors"] == 13

    def test_正常系_average_duration_secondsが正しい(
        self, history_with_runs: CollectionHistory
    ) -> None:
        """average_duration_secondsが正しい値を返すことを確認。"""
        stats = history_with_runs.get_statistics()

        # run-001: 5分=300秒, run-002: 3分=180秒, run-003: 4分=240秒
        # average = (300+180+240)/3 = 240秒
        assert stats["average_duration_seconds"] == 240.0

    def test_正常系_success_rateが正しい(
        self, history_with_runs: CollectionHistory
    ) -> None:
        """success_rateが正しい値を返すことを確認。"""
        stats = history_with_runs.get_statistics()

        # 2/3 ≈ 0.667
        assert abs(stats["success_rate"] - 2 / 3) < 0.001

    def test_エッジケース_空のHistoryの統計(self) -> None:
        """空のHistoryでget_statisticsが適切な値を返すことを確認。"""
        history = CollectionHistory()
        stats = history.get_statistics()

        assert stats["total_runs"] == 0
        assert stats["successful_runs"] == 0
        assert stats["failed_runs"] == 0
        assert stats["total_articles"] == 0
        assert stats["total_errors"] == 0
        assert stats["average_duration_seconds"] == 0.0
        assert stats["success_rate"] == 1.0  # 実行なしは100%成功扱い

    def test_正常系_get_statistics_by_sourceでソース別統計(
        self, history_with_runs: CollectionHistory
    ) -> None:
        """get_statistics_by_sourceでソース別の統計を取得できることを確認。"""
        stats = history_with_runs.get_statistics_by_source()

        assert "yfinance_ticker" in stats
        # yfinance_ticker: 50+40+55=145 success, 2+10+1=13 errors, 480+380+520=1380 articles
        assert stats["yfinance_ticker"]["total_success"] == 145
        assert stats["yfinance_ticker"]["total_errors"] == 13
        assert stats["yfinance_ticker"]["total_articles"] == 1380


class TestCollectionHistoryPersistence:
    """Test CollectionHistory file persistence (save/load)."""

    @pytest.fixture
    def history_with_data(self) -> CollectionHistory:
        """データ入りのHistoryを提供するフィクスチャ。"""
        history = CollectionHistory()
        base_time = datetime(2026, 1, 28, 12, 0, 0, tzinfo=timezone.utc)

        history.add_run(
            CollectionRun(
                run_id="run-001",
                started_at=base_time,
                completed_at=base_time + timedelta(minutes=5),
                sources={
                    "yfinance_ticker": SourceStats(
                        success_count=50,
                        error_count=2,
                        article_count=480,
                    ),
                },
                sinks={
                    "file": SinkResult(success=True),
                },
            )
        )

        history.add_run(
            CollectionRun(
                run_id="run-002",
                started_at=base_time + timedelta(hours=1),
                completed_at=base_time + timedelta(hours=1, minutes=3),
                sources={
                    "rss": SourceStats(
                        success_count=10,
                        error_count=0,
                        article_count=100,
                    ),
                },
                sinks={
                    "github": SinkResult(success=True, metadata={"issues_created": 5}),
                },
            )
        )

        return history

    def test_正常系_JSONファイルに保存できる(
        self, history_with_data: CollectionHistory, temp_dir: Path
    ) -> None:
        """CollectionHistoryをJSONファイルに保存できることを確認。"""
        file_path = temp_dir / "history.json"

        history_with_data.save(file_path)

        assert file_path.exists()
        content = file_path.read_text(encoding="utf-8")
        assert "run-001" in content
        assert "run-002" in content

    def test_正常系_JSONファイルから読み込める(
        self, history_with_data: CollectionHistory, temp_dir: Path
    ) -> None:
        """JSONファイルからCollectionHistoryを読み込めることを確認。"""
        file_path = temp_dir / "history.json"
        history_with_data.save(file_path)

        loaded = CollectionHistory.load(file_path)

        assert len(loaded) == 2
        assert loaded.runs[0].run_id in ["run-001", "run-002"]
        assert loaded.runs[1].run_id in ["run-001", "run-002"]

    def test_正常系_save_loadの往復(
        self, history_with_data: CollectionHistory, temp_dir: Path
    ) -> None:
        """save/loadを往復しても同じデータが保持されることを確認。"""
        file_path = temp_dir / "history.json"
        history_with_data.save(file_path)
        loaded = CollectionHistory.load(file_path)

        original_stats = history_with_data.get_statistics()
        loaded_stats = loaded.get_statistics()

        assert original_stats["total_runs"] == loaded_stats["total_runs"]
        assert original_stats["total_articles"] == loaded_stats["total_articles"]
        assert original_stats["total_errors"] == loaded_stats["total_errors"]

    def test_正常系_存在しないファイルから空のHistoryを作成(
        self, temp_dir: Path
    ) -> None:
        """存在しないファイルパスでloadすると空のHistoryが返ることを確認。"""
        file_path = temp_dir / "non_existent.json"

        loaded = CollectionHistory.load(file_path)

        assert len(loaded) == 0

    def test_正常系_ディレクトリが存在しない場合も保存できる(
        self, history_with_data: CollectionHistory, temp_dir: Path
    ) -> None:
        """親ディレクトリが存在しない場合も保存できることを確認。"""
        file_path = temp_dir / "subdir" / "deep" / "history.json"

        history_with_data.save(file_path)

        assert file_path.exists()

    def test_異常系_不正なJSONファイルでValueError(self, temp_dir: Path) -> None:
        """不正なJSONファイルを読み込むとValueErrorが発生することを確認。"""
        file_path = temp_dir / "invalid.json"
        file_path.write_text("{ invalid json }", encoding="utf-8")

        with pytest.raises(ValueError, match="Invalid JSON"):
            CollectionHistory.load(file_path)

    def test_正常系_空のHistoryを保存できる(self, temp_dir: Path) -> None:
        """空のCollectionHistoryを保存できることを確認。"""
        history = CollectionHistory()
        file_path = temp_dir / "empty_history.json"

        history.save(file_path)

        assert file_path.exists()
        loaded = CollectionHistory.load(file_path)
        assert len(loaded) == 0


class TestCollectionHistoryMaxRuns:
    """Test CollectionHistory max_runs limit."""

    def test_正常系_max_runsを超えると古いRunが削除される(self) -> None:
        """max_runsを超えると古いRunが削除されることを確認。"""
        history = CollectionHistory(max_runs=3)
        base_time = datetime(2026, 1, 28, 12, 0, 0, tzinfo=timezone.utc)

        for i in range(5):
            history.add_run(
                CollectionRun(
                    run_id=f"run-{i:03d}",
                    started_at=base_time + timedelta(hours=i),
                    completed_at=base_time + timedelta(hours=i, minutes=5),
                    sources={},
                    sinks={},
                )
            )

        assert len(history) == 3
        # 最新3件が保持される
        run_ids = [run.run_id for run in history.runs]
        assert "run-002" in run_ids
        assert "run-003" in run_ids
        assert "run-004" in run_ids
        assert "run-000" not in run_ids
        assert "run-001" not in run_ids

    def test_正常系_max_runsを指定しない場合は無制限(self) -> None:
        """max_runsを指定しない場合は無制限に保持されることを確認。"""
        history = CollectionHistory()
        base_time = datetime(2026, 1, 28, 12, 0, 0, tzinfo=timezone.utc)

        for i in range(100):
            history.add_run(
                CollectionRun(
                    run_id=f"run-{i:03d}",
                    started_at=base_time + timedelta(hours=i),
                    completed_at=base_time + timedelta(hours=i, minutes=5),
                    sources={},
                    sinks={},
                )
            )

        assert len(history) == 100


class TestCollectionHistoryJSON:
    """Test CollectionHistory JSON serialization."""

    def test_正常系_model_dump_jsonでJSONにシリアライズできる(self) -> None:
        """CollectionHistoryをmodel_dump_jsonでJSONにシリアライズできることを確認。"""
        history = CollectionHistory()
        base_time = datetime(2026, 1, 28, 12, 0, 0, tzinfo=timezone.utc)

        history.add_run(
            CollectionRun(
                run_id="run-001",
                started_at=base_time,
                completed_at=base_time + timedelta(minutes=5),
                sources={
                    "yfinance_ticker": SourceStats(
                        success_count=50,
                        error_count=2,
                        article_count=480,
                    ),
                },
                sinks={
                    "file": SinkResult(success=True),
                },
            )
        )

        json_str = history.model_dump_json()

        assert "run-001" in json_str
        assert "yfinance_ticker" in json_str
        assert "480" in json_str

    def test_正常系_model_validate_jsonでJSONからデシリアライズできる(self) -> None:
        """JSONからCollectionHistoryをmodel_validate_jsonでデシリアライズできることを確認。"""
        json_data = """
        {
            "runs": [
                {
                    "run_id": "run-001",
                    "started_at": "2026-01-28T12:00:00Z",
                    "completed_at": "2026-01-28T12:05:00Z",
                    "sources": {
                        "yfinance_ticker": {
                            "success_count": 50,
                            "error_count": 2,
                            "article_count": 480
                        }
                    },
                    "sinks": {
                        "file": {"success": true, "metadata": {}}
                    }
                }
            ],
            "max_runs": null
        }
        """
        history = CollectionHistory.model_validate_json(json_data)

        assert len(history) == 1
        assert history.runs[0].run_id == "run-001"
        assert history.runs[0].sources["yfinance_ticker"].article_count == 480

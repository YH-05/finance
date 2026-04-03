"""Unit tests for market.pipeline.errors."""

import pytest

from market.pipeline.errors import (
    CollectorError,
    PhaseError,
    PipelineError,
    QueueError,
    StorageError,
    TickerNormalizationError,
)


class TestPipelineError:
    def test_正常系_メッセージのみでインスタンス化できる(self) -> None:
        err = PipelineError("test error")
        assert str(err) == "test error"
        assert err.message == "test error"
        assert err.context == {}

    def test_正常系_コンテキスト付きでインスタンス化できる(self) -> None:
        err = PipelineError("test", {"key": "value"})
        assert err.context == {"key": "value"}

    def test_正常系_Noneコンテキストは空辞書になる(self) -> None:
        err = PipelineError("test", None)
        assert err.context == {}

    def test_正常系_Exceptionのサブクラスである(self) -> None:
        err = PipelineError("test")
        assert isinstance(err, Exception)

    def test_エッジケース_空文字メッセージで生成できる(self) -> None:
        err = PipelineError("")
        assert err.message == ""


class TestSubclassHierarchy:
    @pytest.mark.parametrize(
        "error_class",
        [PhaseError, StorageError, CollectorError, QueueError, TickerNormalizationError],
    )
    def test_正常系_全サブクラスがPipelineErrorを継承する(
        self, error_class: type[PipelineError]
    ) -> None:
        err = error_class("test")
        assert isinstance(err, PipelineError)
        assert isinstance(err, Exception)

    @pytest.mark.parametrize(
        "error_class",
        [PhaseError, StorageError, CollectorError, QueueError, TickerNormalizationError],
    )
    def test_正常系_全サブクラスがコンテキスト付きで生成できる(
        self, error_class: type[PipelineError]
    ) -> None:
        ctx = {"symbol": "AAPL", "phase": 1}
        err = error_class("test", ctx)
        assert err.context == ctx


class TestPhaseError:
    def test_正常系_フェーズエラーをraiseできる(self) -> None:
        with pytest.raises(PhaseError, match="Phase 2 failed"):
            raise PhaseError("Phase 2 failed", {"phase": 2})


class TestStorageError:
    def test_正常系_ストレージエラーをraiseできる(self) -> None:
        with pytest.raises(StorageError):
            raise StorageError("DB write failed", {"table": "nc_earnings_calendar"})


class TestCollectorError:
    def test_正常系_コレクターエラーをraiseできる(self) -> None:
        with pytest.raises(CollectorError):
            raise CollectorError("API 429", {"status_code": 429})


class TestQueueError:
    def test_正常系_キューエラーをraiseできる(self) -> None:
        with pytest.raises(QueueError):
            raise QueueError("Invalid state", {"from_state": "pending"})


class TestTickerNormalizationError:
    def test_正常系_ノーマライズエラーをraiseできる(self) -> None:
        with pytest.raises(TickerNormalizationError):
            raise TickerNormalizationError(
                "Unknown target", {"symbol": "AAPL", "target": "bad"}
            )

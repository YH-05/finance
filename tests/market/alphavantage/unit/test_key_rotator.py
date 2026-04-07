"""Tests for market.alphavantage.key_rotator module.

Unit tests for the KeyRotator class including:
- Initialization from explicit key list and environment variables
- next_key() rotation based on usage count
- mark_rate_limited() immediate key switching
- Properties: key_count, total_budget, remaining_budget
- Budget exhaustion raises AlphaVantageRateLimitError
- Key values are not leaked in logs (only key_index)
- Session + KeyRotator integration (real instances, HTTP transport patched only)

Test TODO List:
- [x] 環境変数 ALPHA_VANTAGE_API_KEYS からカンマ区切りで複数キー読み取り
- [x] ALPHA_VANTAGE_API_KEY へのシングルキーフォールバック
- [x] キーなし時に ValueError
- [x] 25回使用後に次のキーへ自動切替
- [x] key_count プロパティが正しい値を返す
- [x] total_budget プロパティが正しい値を返す
- [x] remaining_budget プロパティが正しい値を返す（初期状態）
- [x] remaining_budget がリクエストごとに減少する
- [x] mark_rate_limited() で即座に次キーへ切替
- [x] 全キー使い切り時に AlphaVantageRateLimitError
- [x] Session + KeyRotator 統合: 実インスタンスでキーがリクエストに注入される
- [x] Session + KeyRotator 統合: 429応答でmark_rate_limitedが呼ばれ次のキーへ切替
- [x] Session + KeyRotator 統合: 全キー枯渇時にAlphaVantageRateLimitErrorが伝播
- [x] Session + KeyRotator 統合: キーローテーション後のremaining_budget反映
"""

import os
from typing import Any
from unittest.mock import MagicMock, patch

import httpx
import pytest

from market.alphavantage.errors import AlphaVantageRateLimitError
from market.alphavantage.key_rotator import KeyRotator
from market.alphavantage.session import AlphaVantageSession
from market.alphavantage.types import AlphaVantageConfig, RetryConfig

# =============================================================================
# KeyRotator initialization tests
# =============================================================================


class TestKeyRotatorInit:
    """Tests for KeyRotator initialization."""

    def test_正常系_明示的キーリストで初期化(self) -> None:
        rotator = KeyRotator(keys=["fake-api-key1", "fake-api-key2", "fake-api-key3"])
        assert rotator.key_count == 3

    def test_正常系_daily_limit_per_keyのデフォルト値が25(self) -> None:
        rotator = KeyRotator(keys=["fake-api-key1"])
        assert rotator.total_budget == 25

    def test_正常系_カスタムdaily_limitで初期化(self) -> None:
        rotator = KeyRotator(
            keys=["fake-api-key1", "fake-api-key2"], daily_limit_per_key=10
        )
        assert rotator.total_budget == 20

    def test_正常系_環境変数ALPHA_VANTAGE_API_KEYSからカンマ区切りで読み取り(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv(
            "ALPHA_VANTAGE_API_KEYS", "fake-api-keyA,fake-api-keyB,fake-api-keyC"
        )
        monkeypatch.delenv("ALPHA_VANTAGE_API_KEY", raising=False)
        rotator = KeyRotator()
        assert rotator.key_count == 3

    def test_正常系_単一キー環境変数ALPHA_VANTAGE_API_KEYへのフォールバック(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("ALPHA_VANTAGE_API_KEYS", raising=False)
        monkeypatch.setenv("ALPHA_VANTAGE_API_KEY", "single_key")
        rotator = KeyRotator()
        assert rotator.key_count == 1

    def test_異常系_キーなし時にValueError(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("ALPHA_VANTAGE_API_KEYS", raising=False)
        monkeypatch.delenv("ALPHA_VANTAGE_API_KEY", raising=False)
        with pytest.raises(ValueError, match="No Alpha Vantage API keys"):
            KeyRotator()

    def test_異常系_空のキーリストでValueError(self) -> None:
        with pytest.raises(ValueError, match="No Alpha Vantage API keys"):
            KeyRotator(keys=[])

    def test_異常系_すべて空白のキーリストでValueError(self) -> None:
        with pytest.raises(ValueError, match="No Alpha Vantage API keys"):
            KeyRotator(keys=["", "  ", "\t"])

    def test_正常系_空白を含む環境変数キーをトリム(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("ALPHA_VANTAGE_API_KEYS", " fake-api-keyA , fake-api-keyB ")
        monkeypatch.delenv("ALPHA_VANTAGE_API_KEY", raising=False)
        rotator = KeyRotator()
        assert rotator.key_count == 2


# =============================================================================
# KeyRotator.next_key() tests
# =============================================================================


class TestKeyRotatorNextKey:
    """Tests for KeyRotator.next_key() method."""

    def test_正常系_初回呼び出しで最初のキーを返す(self) -> None:
        rotator = KeyRotator(
            keys=["fake-api-key1", "fake-api-key2"], daily_limit_per_key=25
        )
        key = rotator.next_key()
        assert key == "fake-api-key1"

    def test_正常系_25回使用後に次のキーへ自動切替(self) -> None:
        rotator = KeyRotator(
            keys=["fake-api-key1", "fake-api-key2"], daily_limit_per_key=25
        )
        # 25回目まで key1 を取得
        for _ in range(25):
            key = rotator.next_key()
        assert key == "fake-api-key1"
        # 26回目は key2 へ切替
        key = rotator.next_key()
        assert key == "fake-api-key2"

    def test_正常系_カスタムlimitで切替(self) -> None:
        rotator = KeyRotator(
            keys=["fake-api-key1", "fake-api-key2"], daily_limit_per_key=3
        )
        keys_used = [rotator.next_key() for _ in range(4)]
        assert keys_used[:3] == ["fake-api-key1", "fake-api-key1", "fake-api-key1"]
        assert keys_used[3] == "fake-api-key2"

    def test_異常系_全キー消費時にAlphaVantageRateLimitError(self) -> None:
        rotator = KeyRotator(keys=["fake-api-key1"], daily_limit_per_key=2)
        rotator.next_key()
        rotator.next_key()
        with pytest.raises(AlphaVantageRateLimitError):
            rotator.next_key()

    def test_異常系_全キー消費後のエラーメッセージに予算情報を含む(self) -> None:
        rotator = KeyRotator(keys=["fake-api-key1"], daily_limit_per_key=1)
        rotator.next_key()
        with pytest.raises(AlphaVantageRateLimitError, match="budget"):
            rotator.next_key()


# =============================================================================
# KeyRotator.mark_rate_limited() tests
# =============================================================================


class TestKeyRotatorMarkRateLimited:
    """Tests for KeyRotator.mark_rate_limited() method."""

    def test_正常系_mark_rate_limitedで即座に次キーへ切替(self) -> None:
        rotator = KeyRotator(
            keys=["fake-api-key1", "fake-api-key2"], daily_limit_per_key=25
        )
        # 1回だけ使った後でレートリミット
        rotator.next_key()
        rotator.mark_rate_limited()
        key = rotator.next_key()
        assert key == "fake-api-key2"

    def test_異常系_全キーレートリミット時にAlphaVantageRateLimitError(self) -> None:
        rotator = KeyRotator(keys=["fake-api-key1"], daily_limit_per_key=25)
        rotator.next_key()
        rotator.mark_rate_limited()
        with pytest.raises(AlphaVantageRateLimitError):
            rotator.next_key()


# =============================================================================
# KeyRotator properties tests
# =============================================================================


class TestKeyRotatorProperties:
    """Tests for KeyRotator properties."""

    def test_正常系_key_countがキー数を返す(self) -> None:
        rotator = KeyRotator(keys=["fake-key-k1x", "fake-key-k2x", "fake-key-k3x"])
        assert rotator.key_count == 3

    def test_正常系_total_budgetが全キー合計リクエスト数を返す(self) -> None:
        rotator = KeyRotator(
            keys=["fake-key-k1x", "fake-key-k2x"], daily_limit_per_key=25
        )
        assert rotator.total_budget == 50

    def test_正常系_remaining_budgetが初期状態でtotal_budgetと等しい(self) -> None:
        rotator = KeyRotator(
            keys=["fake-key-k1x", "fake-key-k2x"], daily_limit_per_key=25
        )
        assert rotator.remaining_budget == 50

    def test_正常系_remaining_budgetがリクエストごとに減少する(self) -> None:
        rotator = KeyRotator(
            keys=["fake-key-k1x", "fake-key-k2x"], daily_limit_per_key=25
        )
        rotator.next_key()
        assert rotator.remaining_budget == 49
        rotator.next_key()
        assert rotator.remaining_budget == 48

    def test_正常系_remaining_budgetがmark_rate_limited後に更新される(self) -> None:
        rotator = KeyRotator(
            keys=["fake-key-k1x", "fake-key-k2x"], daily_limit_per_key=25
        )
        rotator.next_key()  # k1 count=1
        rotator.mark_rate_limited()  # k1 exhausted (count set to limit)
        # remaining = total - k1_exhausted - 0 used on k2
        # k1 used = 25 (exhausted), k2 used = 0
        assert rotator.remaining_budget == 25


# =============================================================================
# KeyRotator + AlphaVantageSession integration tests (mock なし)
# =============================================================================

_AV_URL = "https://www.alphavantage.co/query"


def _make_mock_response(
    status_code: int = 200,
    json_data: dict[str, Any] | None = None,
    text: str = "",
    headers: dict[str, str] | None = None,
) -> MagicMock:
    """Create a mock httpx.Response for session-level tests."""
    resp = MagicMock(spec=httpx.Response)
    resp.status_code = status_code
    resp.json.return_value = json_data or {}
    resp.text = text or str(json_data or {})
    resp.headers = headers or {"Content-Type": "application/json"}
    return resp


def _zero_delay_config(api_key: str = "") -> AlphaVantageConfig:
    """Return an AlphaVantageConfig with zero delays for fast tests."""
    return AlphaVantageConfig(
        api_key=api_key,
        polite_delay=0.0,
        delay_jitter=0.0,
        timeout=5.0,
    )


def _zero_retry_config(max_attempts: int = 3) -> RetryConfig:
    """Return a RetryConfig with zero delays for fast tests."""
    return RetryConfig(
        max_attempts=max_attempts,
        initial_delay=0.0,
        max_delay=0.0,
        exponential_base=2.0,
        jitter=False,
    )


class TestKeyRotatorSessionIntegration:
    """Session + KeyRotator integration tests using real instances.

    These tests instantiate both ``AlphaVantageSession`` and ``KeyRotator``
    as real objects.  Only the underlying ``httpx.Client.get`` transport
    is patched so that no actual network calls are made.
    """

    def test_正常系_実KeyRotatorのキーがリクエストに注入される(self) -> None:
        """Real KeyRotator injects its first key into the HTTP request params."""
        rotator = KeyRotator(keys=["real-key-1", "real-key-2"], daily_limit_per_key=25)
        ok_response = _make_mock_response(
            json_data={"Meta Data": {}, "Time Series (Daily)": {}}
        )

        with (
            AlphaVantageSession(
                config=_zero_delay_config(), key_rotator=rotator
            ) as session,
            patch.object(session._client, "get", return_value=ok_response) as mock_get,
        ):
            session.get(_AV_URL, params={"function": "TIME_SERIES_DAILY"})

            call_kwargs = mock_get.call_args
            actual_params = call_kwargs.kwargs.get("params") or call_kwargs[1].get(
                "params"
            )
            assert actual_params["apikey"] == "real-key-1"

    def test_正常系_HTTP429後に実KeyRotatorが次のキーへ切替(self) -> None:
        """After HTTP 429, real KeyRotator rotates to the next key.

        Verifies the end-to-end flow:
        1. First request returns 429 → mark_rate_limited() called on real rotator
        2. Second request uses the next key from the rotator
        """
        rotator = KeyRotator(
            keys=["fake-key-aaa1", "fake-key-bbb1"], daily_limit_per_key=25
        )
        rate_limit_response = _make_mock_response(
            status_code=429,
            text="Rate limited",
            headers={"Retry-After": "0"},
        )
        ok_response = _make_mock_response(
            json_data={"Meta Data": {}, "Time Series (Daily)": {}}
        )

        with (
            AlphaVantageSession(
                config=_zero_delay_config(),
                retry_config=_zero_retry_config(max_attempts=2),
                key_rotator=rotator,
            ) as session,
            patch.object(
                session._client,
                "get",
                side_effect=[rate_limit_response, ok_response],
            ) as mock_get,
        ):
            session.get_with_retry(_AV_URL)

            # Second call must use key-b (rotated after 429)
            second_call_params = mock_get.call_args_list[1].kwargs.get(
                "params"
            ) or mock_get.call_args_list[1][1].get("params")
            assert second_call_params["apikey"] == "fake-key-bbb1"

        # Rotator's k1 should be exhausted; remaining budget is k2's budget
        assert rotator.remaining_budget == 24  # k2 used 1 (the successful request)

    def test_異常系_全キー枯渇時にAlphaVantageRateLimitErrorが伝播(self) -> None:
        """When all KeyRotator keys are exhausted, AlphaVantageRateLimitError propagates."""
        rotator = KeyRotator(keys=["only-api-key1"], daily_limit_per_key=1)

        ok_response = _make_mock_response(
            json_data={"Meta Data": {}, "Time Series (Daily)": {}}
        )
        rate_limit_response = _make_mock_response(
            status_code=429,
            text="Rate limited",
            headers={"Retry-After": "0"},
        )

        with AlphaVantageSession(
            config=_zero_delay_config(),
            retry_config=_zero_retry_config(max_attempts=2),
            key_rotator=rotator,
        ) as session:
            # First request succeeds (uses the 1 allowed request)
            with patch.object(session._client, "get", return_value=ok_response):
                session.get(_AV_URL)

            # Second request: HTTP 429 → mark_rate_limited() exhausts the only key
            # → next_key() raises AlphaVantageRateLimitError
            with (
                patch.object(
                    session._client,
                    "get",
                    return_value=rate_limit_response,
                ),
                pytest.raises(AlphaVantageRateLimitError),
            ):
                session.get_with_retry(_AV_URL)

    def test_正常系_キーローテーション後のremaining_budgetが正確(self) -> None:
        """remaining_budget decreases correctly as keys rotate during session requests."""
        rotator = KeyRotator(
            keys=["fake-key-k1x", "fake-key-k2x"], daily_limit_per_key=3
        )
        ok_response = _make_mock_response(
            json_data={"Meta Data": {}, "Time Series (Daily)": {}}
        )

        with (
            AlphaVantageSession(
                config=_zero_delay_config(), key_rotator=rotator
            ) as session,
            patch.object(session._client, "get", return_value=ok_response),
        ):
            # 3 requests exhaust k1
            for _ in range(3):
                session.get(_AV_URL)
            assert rotator.remaining_budget == 3  # k2 intact

            # 4th request rotates to k2
            session.get(_AV_URL)
            assert rotator.remaining_budget == 2  # k2 used 1

    def test_エッジケース_daily_limit_1でrotatorが即座に次キーへ切替(self) -> None:
        """With daily_limit_per_key=1, each request rotates to the next key."""
        rotator = KeyRotator(
            keys=["fake-api-key1", "fake-api-key2", "fake-api-key3"],
            daily_limit_per_key=1,
        )
        ok_response = _make_mock_response(json_data={"Meta Data": {}})

        with (
            AlphaVantageSession(
                config=_zero_delay_config(), key_rotator=rotator
            ) as session,
            patch.object(session._client, "get", return_value=ok_response) as mock_get,
        ):
            session.get(_AV_URL)
            session.get(_AV_URL)
            session.get(_AV_URL)

            # Verify each request used a different key
            keys_used = [
                (call.kwargs.get("params") or call[1].get("params", {}))["apikey"]
                for call in mock_get.call_args_list
            ]
            assert keys_used == ["fake-api-key1", "fake-api-key2", "fake-api-key3"]
            assert rotator.remaining_budget == 0

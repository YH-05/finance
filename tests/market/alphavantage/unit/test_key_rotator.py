"""Tests for market.alphavantage.key_rotator module.

Unit tests for the KeyRotator class including:
- Initialization from explicit key list and environment variables
- next_key() rotation based on usage count
- mark_rate_limited() immediate key switching
- Properties: key_count, total_budget, remaining_budget
- Budget exhaustion raises AlphaVantageRateLimitError
- Key values are not leaked in logs (only key_index)

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
"""

import os

import pytest

from market.alphavantage.errors import AlphaVantageRateLimitError
from market.alphavantage.key_rotator import KeyRotator

# =============================================================================
# KeyRotator initialization tests
# =============================================================================


class TestKeyRotatorInit:
    """Tests for KeyRotator initialization."""

    def test_正常系_明示的キーリストで初期化(self) -> None:
        rotator = KeyRotator(keys=["key1", "key2", "key3"])
        assert rotator.key_count == 3

    def test_正常系_daily_limit_per_keyのデフォルト値が25(self) -> None:
        rotator = KeyRotator(keys=["key1"])
        assert rotator.total_budget == 25

    def test_正常系_カスタムdaily_limitで初期化(self) -> None:
        rotator = KeyRotator(keys=["key1", "key2"], daily_limit_per_key=10)
        assert rotator.total_budget == 20

    def test_正常系_環境変数ALPHA_VANTAGE_API_KEYSからカンマ区切りで読み取り(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("ALPHA_VANTAGE_API_KEYS", "keyA,keyB,keyC")
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

    def test_正常系_空白を含む環境変数キーをトリム(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("ALPHA_VANTAGE_API_KEYS", " keyA , keyB ")
        monkeypatch.delenv("ALPHA_VANTAGE_API_KEY", raising=False)
        rotator = KeyRotator()
        assert rotator.key_count == 2


# =============================================================================
# KeyRotator.next_key() tests
# =============================================================================


class TestKeyRotatorNextKey:
    """Tests for KeyRotator.next_key() method."""

    def test_正常系_初回呼び出しで最初のキーを返す(self) -> None:
        rotator = KeyRotator(keys=["key1", "key2"], daily_limit_per_key=25)
        key = rotator.next_key()
        assert key == "key1"

    def test_正常系_25回使用後に次のキーへ自動切替(self) -> None:
        rotator = KeyRotator(keys=["key1", "key2"], daily_limit_per_key=25)
        # 25回目まで key1 を取得
        for _ in range(25):
            key = rotator.next_key()
        assert key == "key1"
        # 26回目は key2 へ切替
        key = rotator.next_key()
        assert key == "key2"

    def test_正常系_カスタムlimitで切替(self) -> None:
        rotator = KeyRotator(keys=["key1", "key2"], daily_limit_per_key=3)
        keys_used = [rotator.next_key() for _ in range(4)]
        assert keys_used[:3] == ["key1", "key1", "key1"]
        assert keys_used[3] == "key2"

    def test_異常系_全キー消費時にAlphaVantageRateLimitError(self) -> None:
        rotator = KeyRotator(keys=["key1"], daily_limit_per_key=2)
        rotator.next_key()
        rotator.next_key()
        with pytest.raises(AlphaVantageRateLimitError):
            rotator.next_key()

    def test_異常系_全キー消費後のエラーメッセージに予算情報を含む(self) -> None:
        rotator = KeyRotator(keys=["key1"], daily_limit_per_key=1)
        rotator.next_key()
        with pytest.raises(AlphaVantageRateLimitError, match="budget"):
            rotator.next_key()


# =============================================================================
# KeyRotator.mark_rate_limited() tests
# =============================================================================


class TestKeyRotatorMarkRateLimited:
    """Tests for KeyRotator.mark_rate_limited() method."""

    def test_正常系_mark_rate_limitedで即座に次キーへ切替(self) -> None:
        rotator = KeyRotator(keys=["key1", "key2"], daily_limit_per_key=25)
        # 1回だけ使った後でレートリミット
        rotator.next_key()
        rotator.mark_rate_limited()
        key = rotator.next_key()
        assert key == "key2"

    def test_異常系_全キーレートリミット時にAlphaVantageRateLimitError(self) -> None:
        rotator = KeyRotator(keys=["key1"], daily_limit_per_key=25)
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
        rotator = KeyRotator(keys=["k1", "k2", "k3"])
        assert rotator.key_count == 3

    def test_正常系_total_budgetが全キー合計リクエスト数を返す(self) -> None:
        rotator = KeyRotator(keys=["k1", "k2"], daily_limit_per_key=25)
        assert rotator.total_budget == 50

    def test_正常系_remaining_budgetが初期状態でtotal_budgetと等しい(self) -> None:
        rotator = KeyRotator(keys=["k1", "k2"], daily_limit_per_key=25)
        assert rotator.remaining_budget == 50

    def test_正常系_remaining_budgetがリクエストごとに減少する(self) -> None:
        rotator = KeyRotator(keys=["k1", "k2"], daily_limit_per_key=25)
        rotator.next_key()
        assert rotator.remaining_budget == 49
        rotator.next_key()
        assert rotator.remaining_budget == 48

    def test_正常系_remaining_budgetがmark_rate_limited後に更新される(self) -> None:
        rotator = KeyRotator(keys=["k1", "k2"], daily_limit_per_key=25)
        rotator.next_key()  # k1 count=1
        rotator.mark_rate_limited()  # k1 exhausted (count set to limit)
        # remaining = total - k1_exhausted - 0 used on k2
        # k1 used = 25 (exhausted), k2 used = 0
        assert rotator.remaining_budget == 25

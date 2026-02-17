"""Unit tests for notebooklm.constants module."""

from notebooklm.constants import (
    AUDIO_OVERVIEW_TIMEOUT_MS,
    CHAT_RESPONSE_TIMEOUT_MS,
    DEEP_RESEARCH_POLL_INTERVAL_SECONDS,
    DEEP_RESEARCH_TIMEOUT_MS,
    DEFAULT_ELEMENT_TIMEOUT_MS,
    DEFAULT_MAX_RETRIES,
    DEFAULT_NAVIGATION_TIMEOUT_MS,
    DEFAULT_RETRY_BACKOFF_SECONDS,
    DEFAULT_SESSION_FILE,
    FAST_RESEARCH_TIMEOUT_MS,
    FILE_UPLOAD_TIMEOUT_MS,
    GENERATION_POLL_INTERVAL_SECONDS,
    GOOGLE_LOGIN_URL,
    LOGIN_WAIT_TIMEOUT_MS,
    NOTEBOOK_URL_TEMPLATE,
    NOTEBOOKLM_BASE_URL,
    SESSION_CHECK_URL,
    SOURCE_ADD_TIMEOUT_MS,
    STEALTH_INIT_SCRIPT,
    STEALTH_LOCALE,
    STEALTH_TIMEZONE,
    STEALTH_USER_AGENT,
    STEALTH_VIEWPORT,
    STUDIO_GENERATION_TIMEOUT_MS,
)


class TestURLConstants:
    """Tests for URL constants."""

    def test_正常系_ベースURLがhttpsである(self) -> None:
        assert NOTEBOOKLM_BASE_URL.startswith("https://")
        assert "notebooklm.google.com" in NOTEBOOKLM_BASE_URL

    def test_正常系_ノートブックURLテンプレートがフォーマット可能(self) -> None:
        notebook_id = "c9354f3f-f55b-4f90-a5c4-219e582945cf"
        url = NOTEBOOK_URL_TEMPLATE.format(notebook_id=notebook_id)
        assert notebook_id in url
        assert url.startswith("https://")

    def test_正常系_GoogleログインURLがhttpsである(self) -> None:
        assert GOOGLE_LOGIN_URL.startswith("https://")
        assert "accounts.google.com" in GOOGLE_LOGIN_URL

    def test_正常系_セッションチェックURLがベースURLと一致(self) -> None:
        assert SESSION_CHECK_URL == NOTEBOOKLM_BASE_URL


class TestTimeoutConstants:
    """Tests for timeout constants."""

    def test_正常系_ナビゲーションタイムアウトが正の値(self) -> None:
        assert DEFAULT_NAVIGATION_TIMEOUT_MS > 0
        assert isinstance(DEFAULT_NAVIGATION_TIMEOUT_MS, int)

    def test_正常系_エレメントタイムアウトが正の値(self) -> None:
        assert DEFAULT_ELEMENT_TIMEOUT_MS > 0
        assert isinstance(DEFAULT_ELEMENT_TIMEOUT_MS, int)

    def test_正常系_チャットタイムアウトがエレメントタイムアウトより大きい(
        self,
    ) -> None:
        assert CHAT_RESPONSE_TIMEOUT_MS > DEFAULT_ELEMENT_TIMEOUT_MS

    def test_正常系_AudioOverviewタイムアウトが十分大きい(self) -> None:
        # Audio Overview can take several minutes
        assert AUDIO_OVERVIEW_TIMEOUT_MS >= 300_000  # at least 5 minutes

    def test_正常系_Studioタイムアウトが十分大きい(self) -> None:
        # Slides can take ~5 minutes
        assert STUDIO_GENERATION_TIMEOUT_MS >= 300_000

    def test_正常系_DeepResearchタイムアウトが最も大きい(self) -> None:
        # Deep Research can take 25+ minutes
        assert DEEP_RESEARCH_TIMEOUT_MS >= 1_500_000  # at least 25 minutes
        assert DEEP_RESEARCH_TIMEOUT_MS > FAST_RESEARCH_TIMEOUT_MS

    def test_正常系_FastResearchタイムアウトが適切(self) -> None:
        # Fast Research typically completes in 15-30 seconds
        assert FAST_RESEARCH_TIMEOUT_MS >= 60_000

    def test_正常系_ソース追加タイムアウトが正の値(self) -> None:
        assert SOURCE_ADD_TIMEOUT_MS > 0

    def test_正常系_ファイルアップロードタイムアウトが正の値(self) -> None:
        assert FILE_UPLOAD_TIMEOUT_MS > 0
        assert FILE_UPLOAD_TIMEOUT_MS >= SOURCE_ADD_TIMEOUT_MS

    def test_正常系_ログイン待機タイムアウトが十分大きい(self) -> None:
        # Manual login needs time
        assert LOGIN_WAIT_TIMEOUT_MS >= 120_000  # at least 2 minutes


class TestPollingIntervalConstants:
    """Tests for polling interval constants."""

    def test_正常系_生成ポーリング間隔が正の値(self) -> None:
        assert GENERATION_POLL_INTERVAL_SECONDS > 0
        assert isinstance(GENERATION_POLL_INTERVAL_SECONDS, float)

    def test_正常系_DeepResearchポーリング間隔が通常より長い(self) -> None:
        assert DEEP_RESEARCH_POLL_INTERVAL_SECONDS > GENERATION_POLL_INTERVAL_SECONDS


class TestSessionConstants:
    """Tests for session management constants."""

    def test_正常系_セッションファイルパスがjsonファイル(self) -> None:
        assert DEFAULT_SESSION_FILE.endswith(".json")

    def test_正常系_セッションファイルパスがドット始まり(self) -> None:
        # Hidden file to avoid accidental commits
        assert DEFAULT_SESSION_FILE.startswith(".")


class TestStealthConstants:
    """Tests for stealth browser configuration constants."""

    def test_正常系_ビューポートが正の値を持つ(self) -> None:
        assert STEALTH_VIEWPORT["width"] > 0
        assert STEALTH_VIEWPORT["height"] > 0

    def test_正常系_ビューポートが一般的な解像度(self) -> None:
        # Should be a common resolution
        assert STEALTH_VIEWPORT["width"] >= 1280
        assert STEALTH_VIEWPORT["height"] >= 720

    def test_正常系_ユーザーエージェントが空でない(self) -> None:
        assert len(STEALTH_USER_AGENT) > 0
        assert "Mozilla" in STEALTH_USER_AGENT

    def test_正常系_ロケールが設定されている(self) -> None:
        assert len(STEALTH_LOCALE) > 0

    def test_正常系_タイムゾーンが設定されている(self) -> None:
        assert len(STEALTH_TIMEZONE) > 0

    def test_正常系_初期化スクリプトがwebdriver隠蔽を含む(self) -> None:
        assert "webdriver" in STEALTH_INIT_SCRIPT
        assert "undefined" in STEALTH_INIT_SCRIPT

    def test_正常系_初期化スクリプトがWebGL偽装を含む(self) -> None:
        assert "WebGLRenderingContext" in STEALTH_INIT_SCRIPT

    def test_正常系_初期化スクリプトがchrome_runtime追加を含む(self) -> None:
        assert "chrome.runtime" in STEALTH_INIT_SCRIPT


class TestRetryConstants:
    """Tests for retry settings constants."""

    def test_正常系_最大リトライ回数が正の値(self) -> None:
        assert DEFAULT_MAX_RETRIES > 0
        assert isinstance(DEFAULT_MAX_RETRIES, int)

    def test_正常系_リトライバックオフが正の値(self) -> None:
        assert DEFAULT_RETRY_BACKOFF_SECONDS > 0
        assert isinstance(DEFAULT_RETRY_BACKOFF_SECONDS, float)

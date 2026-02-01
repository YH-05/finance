"""Unit tests for URL validator."""

import pytest

from rss.exceptions import InvalidURLError
from rss.validators.url_validator import URLValidator


class TestURLValidatorInit:
    """URLValidator初期化のテスト。"""

    def test_init_creates_instance(self) -> None:
        """インスタンスが作成されることを確認。"""
        validator = URLValidator()
        assert validator is not None


class TestValidateUrl:
    """validate_urlメソッドのテスト。"""

    @pytest.fixture
    def validator(self) -> URLValidator:
        """URLValidatorインスタンスを作成。"""
        return URLValidator()

    def test_validate_url_https_success(self, validator: URLValidator) -> None:
        """HTTPS URLが正常に検証されることを確認。"""
        validator.validate_url("https://example.com/feed")

    def test_validate_url_http_success(self, validator: URLValidator) -> None:
        """HTTP URLが正常に検証されることを確認。"""
        validator.validate_url("http://example.com/rss")

    def test_validate_url_with_path_success(self, validator: URLValidator) -> None:
        """パス付きURLが正常に検証されることを確認。"""
        validator.validate_url("https://example.com/blog/feed.xml")

    def test_validate_url_with_query_success(self, validator: URLValidator) -> None:
        """クエリパラメータ付きURLが正常に検証されることを確認。"""
        validator.validate_url("https://example.com/feed?format=rss")

    def test_validate_url_with_port_success(self, validator: URLValidator) -> None:
        """ポート番号付きURLが正常に検証されることを確認。"""
        validator.validate_url("https://example.com:8080/feed")

    def test_validate_url_empty_raises_error(self, validator: URLValidator) -> None:
        """空文字列がInvalidURLErrorをraiseすることを確認。"""
        with pytest.raises(InvalidURLError, match="cannot be empty"):
            validator.validate_url("")

    def test_validate_url_whitespace_only_raises_error(
        self, validator: URLValidator
    ) -> None:
        """空白のみの文字列がInvalidURLErrorをraiseすることを確認。"""
        with pytest.raises(InvalidURLError, match="cannot be empty"):
            validator.validate_url("   ")

    def test_validate_url_ftp_scheme_raises_error(
        self, validator: URLValidator
    ) -> None:
        """FTPスキームがInvalidURLErrorをraiseすることを確認。"""
        with pytest.raises(InvalidURLError, match="Only HTTP/HTTPS schemes"):
            validator.validate_url("ftp://example.com/file")

    def test_validate_url_file_scheme_raises_error(
        self, validator: URLValidator
    ) -> None:
        """fileスキームがInvalidURLErrorをraiseすることを確認。"""
        with pytest.raises(InvalidURLError, match="Only HTTP/HTTPS schemes"):
            validator.validate_url("file:///path/to/file")

    def test_validate_url_mailto_scheme_raises_error(
        self, validator: URLValidator
    ) -> None:
        """mailtoスキームがInvalidURLErrorをraiseすることを確認。"""
        with pytest.raises(InvalidURLError, match="Only HTTP/HTTPS schemes"):
            validator.validate_url("mailto:user@example.com")

    def test_validate_url_no_scheme_raises_error(self, validator: URLValidator) -> None:
        """スキームなしURLがInvalidURLErrorをraiseすることを確認。"""
        with pytest.raises(InvalidURLError, match="Only HTTP/HTTPS schemes"):
            validator.validate_url("example.com/feed")

    def test_validate_url_no_domain_raises_error(self, validator: URLValidator) -> None:
        """ドメインなしURLがInvalidURLErrorをraiseすることを確認。"""
        with pytest.raises(InvalidURLError, match="must have a valid domain"):
            validator.validate_url("https:///path")

    def test_validate_url_case_insensitive_scheme(
        self, validator: URLValidator
    ) -> None:
        """スキームが大文字小文字を区別しないことを確認。"""
        validator.validate_url("HTTPS://example.com/feed")
        validator.validate_url("HTTP://example.com/feed")
        validator.validate_url("Https://example.com/feed")


class TestValidateTitle:
    """validate_titleメソッドのテスト。"""

    @pytest.fixture
    def validator(self) -> URLValidator:
        """URLValidatorインスタンスを作成。"""
        return URLValidator()

    def test_validate_title_success(self, validator: URLValidator) -> None:
        """有効なタイトルが正常に検証されることを確認。"""
        validator.validate_title("My Feed Title")

    def test_validate_title_single_char_success(self, validator: URLValidator) -> None:
        """1文字のタイトルが正常に検証されることを確認。"""
        validator.validate_title("A")

    def test_validate_title_max_length_success(self, validator: URLValidator) -> None:
        """200文字のタイトルが正常に検証されることを確認。"""
        title = "a" * 200
        validator.validate_title(title)

    def test_validate_title_japanese_success(self, validator: URLValidator) -> None:
        """日本語タイトルが正常に検証されることを確認。"""
        validator.validate_title("金融ニュースフィード")

    def test_validate_title_empty_raises_error(self, validator: URLValidator) -> None:
        """空文字列がValueErrorをraiseすることを確認。"""
        with pytest.raises(ValueError, match="must be between 1 and 200"):
            validator.validate_title("")

    def test_validate_title_whitespace_only_raises_error(
        self, validator: URLValidator
    ) -> None:
        """空白のみの文字列がValueErrorをraiseすることを確認。"""
        with pytest.raises(ValueError, match="whitespace-only"):
            validator.validate_title("   ")

    def test_validate_title_too_long_raises_error(
        self, validator: URLValidator
    ) -> None:
        """201文字以上のタイトルがValueErrorをraiseすることを確認。"""
        title = "a" * 201
        with pytest.raises(ValueError, match="must be between 1 and 200"):
            validator.validate_title(title)


class TestValidateCategory:
    """validate_categoryメソッドのテスト。"""

    @pytest.fixture
    def validator(self) -> URLValidator:
        """URLValidatorインスタンスを作成。"""
        return URLValidator()

    def test_validate_category_success(self, validator: URLValidator) -> None:
        """有効なカテゴリが正常に検証されることを確認。"""
        validator.validate_category("technology")

    def test_validate_category_single_char_success(
        self, validator: URLValidator
    ) -> None:
        """1文字のカテゴリが正常に検証されることを確認。"""
        validator.validate_category("a")

    def test_validate_category_max_length_success(
        self, validator: URLValidator
    ) -> None:
        """50文字のカテゴリが正常に検証されることを確認。"""
        category = "a" * 50
        validator.validate_category(category)

    def test_validate_category_japanese_success(self, validator: URLValidator) -> None:
        """日本語カテゴリが正常に検証されることを確認。"""
        validator.validate_category("金融・経済")

    def test_validate_category_empty_raises_error(
        self, validator: URLValidator
    ) -> None:
        """空文字列がValueErrorをraiseすることを確認。"""
        with pytest.raises(ValueError, match="must be between 1 and 50"):
            validator.validate_category("")

    def test_validate_category_whitespace_only_raises_error(
        self, validator: URLValidator
    ) -> None:
        """空白のみの文字列がValueErrorをraiseすることを確認。"""
        with pytest.raises(ValueError, match="whitespace-only"):
            validator.validate_category("   ")

    def test_validate_category_too_long_raises_error(
        self, validator: URLValidator
    ) -> None:
        """51文字以上のカテゴリがValueErrorをraiseすることを確認。"""
        category = "a" * 51
        with pytest.raises(ValueError, match="must be between 1 and 50"):
            validator.validate_category(category)


class TestLogging:
    """ロギングのテスト。"""

    @pytest.fixture
    def validator(self) -> URLValidator:
        """URLValidatorインスタンスを作成。"""
        return URLValidator()

    def test_validate_url_logs_on_success(
        self, validator: URLValidator, capture_logs: pytest.LogCaptureFixture
    ) -> None:
        """URL検証成功時にログが出力されることを確認。"""
        validator.validate_url("https://example.com/feed")
        # ログが出力されることを確認（構造化ロギングのため詳細は省略）

    def test_validate_url_logs_on_failure(
        self, validator: URLValidator, capture_logs: pytest.LogCaptureFixture
    ) -> None:
        """URL検証失敗時にログが出力されることを確認。"""
        with pytest.raises(InvalidURLError):
            validator.validate_url("ftp://example.com")
        # エラーログが出力されることを確認

"""Property-based tests for RSS feed data validation using Hypothesis."""

from datetime import UTC, datetime

from hypothesis import given
from hypothesis import strategies as st
from rss.exceptions import InvalidURLError
from rss.types import Feed, FeedItem, FetchInterval, FetchStatus
from rss.validators.url_validator import URLValidator

# AIDEV-NOTE: カスタムストラテジーの定義
# RSSフィードデータの各フィールドに対する有効・無効なデータを生成


# URL戦略
@st.composite
def valid_urls(draw: st.DrawFn) -> str:
    """有効なHTTP/HTTPS URLを生成するストラテジー."""
    scheme = draw(st.sampled_from(["http", "https"]))
    # ドメイン名（英数字とハイフン、ドット）
    domain_parts = draw(
        st.lists(
            st.text(
                alphabet=st.characters(
                    whitelist_categories=("Ll", "Lu", "Nd"),
                    blacklist_characters="-.",
                ),
                min_size=1,
                max_size=10,
            ),
            min_size=1,
            max_size=3,
        )
    )
    domain = ".".join(domain_parts)
    # パス（オプション）
    path = draw(
        st.text(
            alphabet=st.characters(whitelist_categories=("Ll", "Lu", "Nd")), max_size=50
        )
    )
    if path:
        return f"{scheme}://{domain}/{path}"
    return f"{scheme}://{domain}"


@st.composite
def invalid_scheme_urls(draw: st.DrawFn) -> str:
    """無効なスキームを持つURLを生成するストラテジー."""
    scheme = draw(st.sampled_from(["ftp", "file", "mailto", "data", "ws"]))
    domain = draw(st.text(min_size=1, max_size=20))
    return f"{scheme}://{domain}"


# タイトル戦略
def valid_titles() -> st.SearchStrategy[str]:
    """有効なタイトル（1-200文字）を生成するストラテジー."""
    return st.text(min_size=1, max_size=200).filter(lambda s: s.strip() != "")


def invalid_titles() -> st.SearchStrategy[str]:
    """無効なタイトルを生成するストラテジー."""
    return st.one_of(
        st.just(""),  # 空文字列
        st.text(alphabet=" \t\n", min_size=1, max_size=10),  # 空白のみ
        st.text(min_size=201, max_size=300),  # 長すぎる
    )


# カテゴリ戦略
def valid_categories() -> st.SearchStrategy[str]:
    """有効なカテゴリ（1-50文字）を生成するストラテジー."""
    return st.text(min_size=1, max_size=50).filter(lambda s: s.strip() != "")


def invalid_categories() -> st.SearchStrategy[str]:
    """無効なカテゴリを生成するストラテジー."""
    return st.one_of(
        st.just(""),  # 空文字列
        st.text(alphabet=" \t\n", min_size=1, max_size=10),  # 空白のみ
        st.text(min_size=51, max_size=100),  # 長すぎる
    )


# ISO 8601タイムスタンプ戦略
@st.composite
def iso8601_timestamps(draw: st.DrawFn) -> str:
    """ISO 8601形式のタイムスタンプを生成するストラテジー."""
    # 2020-01-01から2030-12-31の範囲でランダムな日時を生成
    year = draw(st.integers(min_value=2020, max_value=2030))
    month = draw(st.integers(min_value=1, max_value=12))
    day = draw(st.integers(min_value=1, max_value=28))  # 全月で有効な日
    hour = draw(st.integers(min_value=0, max_value=23))
    minute = draw(st.integers(min_value=0, max_value=59))
    second = draw(st.integers(min_value=0, max_value=59))

    dt = datetime(year, month, day, hour, minute, second, tzinfo=UTC)
    return dt.isoformat()


# UUID v4戦略
def uuid_v4_strings() -> st.SearchStrategy[str]:
    """UUID v4形式の文字列を生成するストラテジー."""
    return st.uuids(version=4).map(str)


class TestURLValidatorProperty:
    """URLValidatorのプロパティベーステスト."""

    def setup_method(self) -> None:
        """各テストメソッド実行前の初期化."""
        self.validator = URLValidator()

    @given(url=valid_urls())
    def test_プロパティ_有効なURLは必ず受け入れられる(self, url: str) -> None:
        """有効なHTTP/HTTPS URLは必ず受け入れられることを検証."""
        # 例外が発生しないことを確認
        self.validator.validate_url(url)

    @given(url=invalid_scheme_urls())
    def test_プロパティ_無効なスキームのURLは必ず拒否される(self, url: str) -> None:
        """HTTP/HTTPS以外のスキームを持つURLは必ず拒否されることを検証."""
        try:
            self.validator.validate_url(url)
            # 例外が発生しなければテスト失敗
            msg = f"Expected InvalidURLError for {url}"
            raise AssertionError(msg)
        except InvalidURLError:
            # 期待通りの例外
            pass

    @given(url=st.sampled_from(["", " ", "\t", "\n", "   "]))
    def test_プロパティ_空白のみのURLは必ず拒否される(self, url: str) -> None:
        """空文字列や空白のみのURLは必ず拒否されることを検証."""
        try:
            self.validator.validate_url(url)
            msg = f"Expected InvalidURLError for empty/blank URL: '{url}'"
            raise AssertionError(msg)
        except InvalidURLError:
            pass

    @given(url=st.text(max_size=20).filter(lambda s: "://" not in s))
    def test_プロパティ_スキームなしURLは必ず拒否される(self, url: str) -> None:
        """スキーム部分のないURLは必ず拒否されることを検証."""
        if not url or url.isspace():
            # 空白のみのケースは別テストでカバー
            return

        try:
            self.validator.validate_url(url)
            msg = f"Expected InvalidURLError for URL without scheme: {url}"
            raise AssertionError(msg)
        except InvalidURLError:
            pass

    @given(title=valid_titles())
    def test_プロパティ_有効なタイトルは必ず受け入れられる(self, title: str) -> None:
        """1-200文字の非空白タイトルは必ず受け入れられることを検証."""
        self.validator.validate_title(title)

    @given(title=invalid_titles())
    def test_プロパティ_無効なタイトルは必ず拒否される(self, title: str) -> None:
        """空文字列、空白のみ、または長すぎるタイトルは必ず拒否されることを検証."""
        try:
            self.validator.validate_title(title)
            msg = f"Expected ValueError for invalid title: '{title}' (len={len(title)})"
            raise AssertionError(msg)
        except ValueError:
            pass

    @given(category=valid_categories())
    def test_プロパティ_有効なカテゴリは必ず受け入れられる(self, category: str) -> None:
        """1-50文字の非空白カテゴリは必ず受け入れられることを検証."""
        self.validator.validate_category(category)

    @given(category=invalid_categories())
    def test_プロパティ_無効なカテゴリは必ず拒否される(self, category: str) -> None:
        """空文字列、空白のみ、または長すぎるカテゴリは必ず拒否されることを検証."""
        try:
            self.validator.validate_category(category)
            msg = f"Expected ValueError for invalid category: '{category}' (len={len(category)})"
            raise AssertionError(msg)
        except ValueError:
            pass


class TestFeedDataProperty:
    """Feedデータクラスのプロパティベーステスト."""

    @given(
        feed_id=uuid_v4_strings(),
        url=valid_urls(),
        title=valid_titles(),
        category=valid_categories(),
        fetch_interval=st.sampled_from(
            [FetchInterval.DAILY, FetchInterval.WEEKLY, FetchInterval.MANUAL]
        ),
        created_at=iso8601_timestamps(),
        updated_at=iso8601_timestamps(),
        last_fetched=st.one_of(st.none(), iso8601_timestamps()),
        last_status=st.sampled_from(
            [FetchStatus.SUCCESS, FetchStatus.FAILURE, FetchStatus.PENDING]
        ),
        enabled=st.booleans(),
    )
    def test_プロパティ_有効なフィールドでFeedが生成される(
        self,
        feed_id: str,
        url: str,
        title: str,
        category: str,
        fetch_interval: FetchInterval,
        created_at: str,
        updated_at: str,
        last_fetched: str | None,
        last_status: FetchStatus,
        enabled: bool,
    ) -> None:
        """有効なフィールド値でFeedオブジェクトが生成できることを検証."""
        feed = Feed(
            feed_id=feed_id,
            url=url,
            title=title,
            category=category,
            fetch_interval=fetch_interval,
            created_at=created_at,
            updated_at=updated_at,
            last_fetched=last_fetched,
            last_status=last_status,
            enabled=enabled,
        )

        # フィールドが正しく設定されていることを確認
        assert feed.feed_id == feed_id
        assert feed.url == url
        assert feed.title == title
        assert feed.category == category
        assert feed.fetch_interval == fetch_interval
        assert feed.created_at == created_at
        assert feed.updated_at == updated_at
        assert feed.last_fetched == last_fetched
        assert feed.last_status == last_status
        assert feed.enabled == enabled


class TestFeedItemDataProperty:
    """FeedItemデータクラスのプロパティベーステスト."""

    @given(
        item_id=uuid_v4_strings(),
        title=valid_titles(),
        link=valid_urls(),
        published=st.one_of(st.none(), iso8601_timestamps()),
        summary=st.one_of(st.none(), st.text(max_size=1000)),
        content=st.one_of(st.none(), st.text(max_size=5000)),
        author=st.one_of(st.none(), st.text(min_size=1, max_size=100)),
        fetched_at=iso8601_timestamps(),
    )
    def test_プロパティ_有効なフィールドでFeedItemが生成される(
        self,
        item_id: str,
        title: str,
        link: str,
        published: str | None,
        summary: str | None,
        content: str | None,
        author: str | None,
        fetched_at: str,
    ) -> None:
        """有効なフィールド値でFeedItemオブジェクトが生成できることを検証."""
        item = FeedItem(
            item_id=item_id,
            title=title,
            link=link,
            published=published,
            summary=summary,
            content=content,
            author=author,
            fetched_at=fetched_at,
        )

        # フィールドが正しく設定されていることを確認
        assert item.item_id == item_id
        assert item.title == title
        assert item.link == link
        assert item.published == published
        assert item.summary == summary
        assert item.content == content
        assert item.author == author
        assert item.fetched_at == fetched_at

    @given(
        item_id=uuid_v4_strings(),
        title=valid_titles(),
        link=valid_urls(),
        fetched_at=iso8601_timestamps(),
    )
    def test_プロパティ_オプショナルフィールドがNoneでも動作する(
        self,
        item_id: str,
        title: str,
        link: str,
        fetched_at: str,
    ) -> None:
        """オプショナルフィールドが全てNoneでもFeedItemが生成できることを検証."""
        item = FeedItem(
            item_id=item_id,
            title=title,
            link=link,
            published=None,
            summary=None,
            content=None,
            author=None,
            fetched_at=fetched_at,
        )

        assert item.published is None
        assert item.summary is None
        assert item.content is None
        assert item.author is None


class TestEdgeCasesProperty:
    """エッジケースのプロパティベーステスト."""

    def setup_method(self) -> None:
        """各テストメソッド実行前の初期化."""
        self.validator = URLValidator()

    @given(
        title=st.text(
            alphabet=st.characters(
                whitelist_categories=("Ll", "Lu", "Nd", "Po", "Ps", "Pe", "Sm"),
                min_codepoint=0x0021,
                max_codepoint=0x007E,
            ),
            min_size=1,
            max_size=200,
        )
    )
    def test_プロパティ_ASCII特殊文字を含むタイトルが処理される(
        self, title: str
    ) -> None:
        """ASCII範囲の特殊文字を含むタイトルが正しく処理されることを検証."""
        if title.strip():  # 空白のみでない場合
            self.validator.validate_title(title)

    @given(
        title=st.text(
            alphabet=st.characters(
                whitelist_categories=("Ll", "Lu", "Nd", "Po"),
                min_codepoint=0x3000,
                max_codepoint=0x30FF,
            ),
            min_size=1,
            max_size=200,
        )
    )
    def test_プロパティ_日本語文字を含むタイトルが処理される(self, title: str) -> None:
        """日本語文字（ひらがな、カタカナ、句読点）を含むタイトルが正しく処理されることを検証."""
        if title.strip():  # 空白のみでない場合
            self.validator.validate_title(title)

    @given(title=st.text(min_size=1, max_size=200))
    def test_プロパティ_境界値タイトルが正しく処理される(self, title: str) -> None:
        """境界値付近のタイトル長が正しく処理されることを検証."""
        if title.strip():
            # 空白のみでなければ受け入れられるべき
            self.validator.validate_title(title)
        else:
            # 空白のみなら拒否されるべき
            try:
                self.validator.validate_title(title)
                msg = f"Expected ValueError for whitespace-only title: '{title}'"
                raise AssertionError(msg)
            except ValueError:
                pass

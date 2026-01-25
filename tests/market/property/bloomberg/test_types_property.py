"""Property-based tests for market.bloomberg.types module.

TDD Red Phase: These tests are designed to fail initially.
Uses Hypothesis for property-based testing to verify invariants.

Test Properties:
- [x] BloombergFetchOptions: securities list is never empty after validation
- [x] BloombergFetchOptions: fields list is never empty after validation
- [x] BloombergDataResult: row_count equals len(data)
- [x] BloombergDataResult: is_empty is consistent with row_count
- [x] OverrideOption: field and value are always preserved
"""

from datetime import datetime
from typing import Any

import pandas as pd
from hypothesis import assume, given
from hypothesis import strategies as st


class TestBloombergFetchOptionsProperties:
    """Property-based tests for BloombergFetchOptions."""

    @given(
        securities=st.lists(
            st.text(
                alphabet=st.sampled_from("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 "),
                min_size=1,
                max_size=30,
            ),
            min_size=1,
            max_size=10,
        ),
        fields=st.lists(
            st.text(
                alphabet=st.sampled_from("ABCDEFGHIJKLMNOPQRSTUVWXYZ_"),
                min_size=1,
                max_size=30,
            ),
            min_size=1,
            max_size=10,
        ),
    )
    def test_プロパティ_securitiesとfieldsが保持される(
        self,
        securities: list[str],
        fields: list[str],
    ) -> None:
        """BloombergFetchOptions が securities と fields を正確に保持することを確認。"""
        from market.bloomberg.types import BloombergFetchOptions

        # Filter out empty strings
        securities = [s for s in securities if s.strip()]
        fields = [f for f in fields if f.strip()]
        assume(len(securities) > 0)
        assume(len(fields) > 0)

        options = BloombergFetchOptions(
            securities=securities,
            fields=fields,
        )

        assert options.securities == securities
        assert options.fields == fields

    @given(
        start_date=st.dates(
            min_value=datetime(2000, 1, 1).date(),
            max_value=datetime(2030, 12, 31).date(),
        ),
        end_date=st.dates(
            min_value=datetime(2000, 1, 1).date(),
            max_value=datetime(2030, 12, 31).date(),
        ),
    )
    def test_プロパティ_日付が正しく保存される(
        self,
        start_date,
        end_date,
    ) -> None:
        """BloombergFetchOptions が日付を正しく保存することを確認。"""
        from market.bloomberg.types import BloombergFetchOptions

        options = BloombergFetchOptions(
            securities=["AAPL US Equity"],
            fields=["PX_LAST"],
            start_date=str(start_date),
            end_date=str(end_date),
        )

        assert options.start_date == str(start_date)
        assert options.end_date == str(end_date)


class TestBloombergDataResultProperties:
    """Property-based tests for BloombergDataResult."""

    @given(
        row_count=st.integers(min_value=0, max_value=1000),
    )
    def test_プロパティ_row_countがDataFrameの長さと一致(
        self,
        row_count: int,
    ) -> None:
        """row_count プロパティが DataFrame の実際の長さと一致することを確認。"""
        from market.bloomberg.types import BloombergDataResult, DataSource

        # Create DataFrame with specified row count
        df = pd.DataFrame({"PX_LAST": [100.0] * row_count})

        result = BloombergDataResult(
            security="AAPL US Equity",
            data=df,
            source=DataSource.BLOOMBERG,
            fetched_at=datetime.now(),
        )

        assert result.row_count == row_count
        assert result.row_count == len(df)

    @given(
        row_count=st.integers(min_value=0, max_value=100),
    )
    def test_プロパティ_is_emptyがrow_countと整合(
        self,
        row_count: int,
    ) -> None:
        """is_empty プロパティが row_count と整合することを確認。"""
        from market.bloomberg.types import BloombergDataResult, DataSource

        df = pd.DataFrame({"PX_LAST": [100.0] * row_count})

        result = BloombergDataResult(
            security="AAPL US Equity",
            data=df,
            source=DataSource.BLOOMBERG,
            fetched_at=datetime.now(),
        )

        # is_empty should be True only when row_count is 0
        assert result.is_empty == (row_count == 0)
        assert result.is_empty == (result.row_count == 0)


class TestOverrideOptionProperties:
    """Property-based tests for OverrideOption."""

    @given(
        field=st.text(
            alphabet=st.sampled_from("ABCDEFGHIJKLMNOPQRSTUVWXYZ_"),
            min_size=1,
            max_size=50,
        ),
        value=st.one_of(
            st.text(min_size=0, max_size=50),
            st.integers(),
            st.floats(allow_nan=False, allow_infinity=False),
        ),
    )
    def test_プロパティ_fieldとvalueが保持される(
        self,
        field: str,
        value: Any,
    ) -> None:
        """OverrideOption が field と value を正確に保持することを確認。"""
        from market.bloomberg.types import OverrideOption

        assume(len(field.strip()) > 0)

        override = OverrideOption(field=field, value=value)

        assert override.field == field
        assert override.value == value


class TestNewsStoryProperties:
    """Property-based tests for NewsStory."""

    @given(
        story_id=st.text(
            alphabet=st.sampled_from("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"),
            min_size=5,
            max_size=20,
        ),
        headline=st.text(min_size=1, max_size=200),
    )
    def test_プロパティ_story_idとheadlineが保持される(
        self,
        story_id: str,
        headline: str,
    ) -> None:
        """NewsStory が story_id と headline を正確に保持することを確認。"""
        from market.bloomberg.types import NewsStory

        assume(len(story_id.strip()) > 0)
        assume(len(headline.strip()) > 0)

        story = NewsStory(
            story_id=story_id,
            headline=headline,
            datetime=datetime.now(),
        )

        assert story.story_id == story_id
        assert story.headline == headline


class TestIDTypeProperties:
    """Property-based tests for IDType enum."""

    def test_プロパティ_全てのIDタイプが小文字の値を持つ(self) -> None:
        """全ての IDType の値が小文字であることを確認。"""
        from market.bloomberg.types import IDType

        for id_type in IDType:
            assert id_type.value == id_type.value.lower()
            assert id_type.value.isalpha()


class TestPeriodicityProperties:
    """Property-based tests for Periodicity enum."""

    def test_プロパティ_全ての周期が大文字の値を持つ(self) -> None:
        """全ての Periodicity の値が大文字であることを確認。"""
        from market.bloomberg.types import Periodicity

        for periodicity in Periodicity:
            assert periodicity.value == periodicity.value.upper()
            assert periodicity.value.isalpha()

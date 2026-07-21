"""Unit tests for market.nse.analysis.universe_diff module.

NIFTY 750 universe の前回スナップショットと最新の指数構成 DataFrame を比較し、
新規採用・除外・維持銘柄を検出する ``diff_universe`` のテストスイート。

Test TODO List:
- [x] diff_universe(): 新規採用・除外・維持を正しく検出
- [x] diff_universe(): 完全一致（全銘柄 unchanged）
- [x] diff_universe(): previous が空（全銘柄 added）
- [x] diff_universe(): current が空（全銘柄 removed）
- [x] diff_universe(): symbol の大文字小文字・前後空白を正規化して比較
- [x] diff_universe(): previous に symbol 列がない場合 KeyError
- [x] diff_universe(): current に symbol 列がない場合 KeyError
- [x] diff_universe(): 戻り値が UniverseDiff 型でソート済みリストを持つ
- [x] UniverseDiff: frozen dataclass であること
- [x] find_post_cutoff_listings(): 基準日より後に上場した銘柄を検出
- [x] find_post_cutoff_listings(): 基準日ちょうどの上場は除外対象外
- [x] find_post_cutoff_listings(): listing_date 欠損・不正値は除外対象外
- [x] find_post_cutoff_listings(): 該当なしで空リスト
- [x] find_post_cutoff_listings(): 必須列がない場合 KeyError
"""

from dataclasses import FrozenInstanceError

import pandas as pd
import pytest

from market.nse.analysis.universe_diff import (
    UniverseDiff,
    diff_universe,
    find_post_cutoff_listings,
)


class TestDiffUniverse:
    """diff_universe() 関数のテスト。"""

    def test_正常系_新規採用と除外と維持を正しく検出する(self) -> None:
        """previous と current の差分から added/removed/unchanged を検出できること。"""
        previous = pd.DataFrame({"symbol": ["RELIANCE", "INFY", "TCS"]})
        current = pd.DataFrame({"symbol": ["INFY", "TCS", "WIPRO"]})

        diff = diff_universe(previous, current)

        assert diff.added == ["WIPRO"]
        assert diff.removed == ["RELIANCE"]
        assert diff.unchanged == ["INFY", "TCS"]

    def test_エッジケース_完全一致で全銘柄がunchangedになる(self) -> None:
        """previous と current が完全一致する場合、added/removed は空になること。"""
        previous = pd.DataFrame({"symbol": ["RELIANCE", "INFY"]})
        current = pd.DataFrame({"symbol": ["INFY", "RELIANCE"]})

        diff = diff_universe(previous, current)

        assert diff.added == []
        assert diff.removed == []
        assert diff.unchanged == ["INFY", "RELIANCE"]

    def test_エッジケース_previousが空で全銘柄がaddedになる(self) -> None:
        """previous が空 DataFrame の場合、current の全銘柄が added になること。"""
        previous = pd.DataFrame({"symbol": []})
        current = pd.DataFrame({"symbol": ["RELIANCE", "INFY"]})

        diff = diff_universe(previous, current)

        assert diff.added == ["INFY", "RELIANCE"]
        assert diff.removed == []
        assert diff.unchanged == []

    def test_エッジケース_currentが空で全銘柄がremovedになる(self) -> None:
        """current が空 DataFrame の場合、previous の全銘柄が removed になること。"""
        previous = pd.DataFrame({"symbol": ["RELIANCE", "INFY"]})
        current = pd.DataFrame({"symbol": []})

        diff = diff_universe(previous, current)

        assert diff.added == []
        assert diff.removed == ["INFY", "RELIANCE"]
        assert diff.unchanged == []

    def test_正常系_symbolの大文字小文字と空白揺れを正規化して比較する(self) -> None:
        """symbol の大文字小文字・前後空白の揺れを正規化してから比較すること。"""
        previous = pd.DataFrame({"symbol": [" reliance ", "Infy"]})
        current = pd.DataFrame({"symbol": ["RELIANCE", " infy"]})

        diff = diff_universe(previous, current)

        assert diff.added == []
        assert diff.removed == []
        assert diff.unchanged == ["INFY", "RELIANCE"]

    def test_異常系_previousにsymbol列がない場合KeyError(self) -> None:
        """previous DataFrame に symbol 列がない場合 KeyError を送出すること。"""
        previous = pd.DataFrame({"ticker": ["RELIANCE"]})
        current = pd.DataFrame({"symbol": ["RELIANCE"]})

        with pytest.raises(KeyError, match="symbol"):
            diff_universe(previous, current)

    def test_異常系_currentにsymbol列がない場合KeyError(self) -> None:
        """current DataFrame に symbol 列がない場合 KeyError を送出すること。"""
        previous = pd.DataFrame({"symbol": ["RELIANCE"]})
        current = pd.DataFrame({"ticker": ["RELIANCE"]})

        with pytest.raises(KeyError, match="symbol"):
            diff_universe(previous, current)

    def test_正常系_戻り値がソート済みリストを持つUniverseDiffである(self) -> None:
        """戻り値が UniverseDiff 型であり、各リストがアルファベット順であること。"""
        previous = pd.DataFrame({"symbol": ["ZOMATO", "ADANIENT"]})
        current = pd.DataFrame({"symbol": ["ADANIENT", "WIPRO", "BAJAJ"]})

        diff = diff_universe(previous, current)

        assert isinstance(diff, UniverseDiff)
        assert diff.added == sorted(diff.added)
        assert diff.removed == sorted(diff.removed)
        assert diff.unchanged == sorted(diff.unchanged)


class TestUniverseDiff:
    """UniverseDiff frozen dataclass のテスト。"""

    def test_正常系_frozenである(self) -> None:
        """UniverseDiff が frozen dataclass であること。"""
        diff = UniverseDiff(added=["A"], removed=["B"], unchanged=["C"])

        with pytest.raises(FrozenInstanceError):
            diff.added = ["D"]  # type: ignore[misc]


class TestFindPostCutoffListings:
    """find_post_cutoff_listings() 関数のテスト。

    point-in-time 整合性の担保用。指数構成 CSV を基準日より後に取得した場合、
    基準日時点で未上場の銘柄が混入する（実例: AGL は 2026-07-03 上場だが
    2026-07-14 取得の構成 CSV 経由で 2026-06-30 版 universe に混入した）。
    """

    def test_正常系_基準日より後に上場した銘柄を検出する(self) -> None:
        """listing_date が cutoff より後の銘柄のみ返すこと。"""
        stocks = pd.DataFrame(
            {
                "symbol": ["AGL", "RELIANCE", "PINELABS"],
                "listing_date": ["03-JUL-2026", "29-NOV-1995", "14-NOV-2025"],
            }
        )

        assert find_post_cutoff_listings(stocks, "2026-06-30") == ["AGL"]

    def test_エッジケース_基準日ちょうどの上場は除外対象にしない(self) -> None:
        """cutoff 当日に上場した銘柄は基準日時点で上場済みとして扱うこと。"""
        stocks = pd.DataFrame({"symbol": ["SAMEDAY"], "listing_date": ["30-JUN-2026"]})

        assert find_post_cutoff_listings(stocks, "2026-06-30") == []

    def test_エッジケース_listing_dateが欠損や不正値でも除外対象にしない(self) -> None:
        """日付を解釈できない銘柄は保守的に universe へ残すこと。"""
        stocks = pd.DataFrame(
            {
                "symbol": ["NODATE", "BROKEN", "AGL"],
                "listing_date": [None, "not-a-date", "03-JUL-2026"],
            }
        )

        assert find_post_cutoff_listings(stocks, "2026-06-30") == ["AGL"]

    def test_エッジケース_該当銘柄なしで空リストを返す(self) -> None:
        """全銘柄が基準日以前の上場なら空リストになること。"""
        stocks = pd.DataFrame(
            {
                "symbol": ["RELIANCE", "INFY"],
                "listing_date": ["29-NOV-1995", "08-FEB-1995"],
            }
        )

        assert find_post_cutoff_listings(stocks, "2026-06-30") == []

    def test_正常系_複数銘柄をソート済みで返す(self) -> None:
        """検出結果が symbol の昇順で返ること。"""
        stocks = pd.DataFrame(
            {
                "symbol": ["ZETA", "AGL"],
                "listing_date": ["10-JUL-2026", "03-JUL-2026"],
            }
        )

        assert find_post_cutoff_listings(stocks, "2026-06-30") == ["AGL", "ZETA"]

    def test_異常系_必須列がない場合KeyError(self) -> None:
        """listing_date 列がない DataFrame は KeyError を送出すること。"""
        stocks = pd.DataFrame({"symbol": ["AGL"]})

        with pytest.raises(KeyError, match="listing_date"):
            find_post_cutoff_listings(stocks, "2026-06-30")

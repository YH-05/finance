"""Unit tests for ``market.fraser.scripts.discover_titles``.

Covers argument parsing, subject / title traversal, interactive vs
non-interactive selection, and the merge-and-write JSON output logic.

The tests deliberately avoid network access by stubbing
``FraserSession`` with ``MagicMock`` and feeding canned response bodies
through ``mock_httpx_response_factory``-style helpers. This mirrors the
HF1 pattern adopted across the FRASER unit suite.
"""

from __future__ import annotations

import argparse
import json
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from market.fraser.errors import FraserError
from market.fraser.scripts import discover_titles


def _make_response(payload: dict[str, Any]) -> MagicMock:
    """Return a MagicMock that mimics ``httpx.Response.json()``."""
    response = MagicMock()
    response.json.return_value = payload
    return response


def _make_session(responses: list[dict[str, Any]]) -> MagicMock:
    """Return a MagicMock FraserSession that returns ``responses`` in order."""
    session = MagicMock()
    session.get_with_retry.side_effect = [_make_response(p) for p in responses]
    return session


class TestParseArgs:
    """Argument parsing surface."""

    def test_正常系_デフォルト引数(self) -> None:
        args = discover_titles.parse_args([])

        assert args.output == discover_titles.DEFAULT_OUTPUT_PATH
        assert args.interactive is False
        assert args.keywords == discover_titles.DEFAULT_KEYWORDS

    def test_正常系_interactiveフラグ(self) -> None:
        args = discover_titles.parse_args(["--interactive"])

        assert args.interactive is True

    def test_正常系_outputパス上書き(self, tmp_path: Any) -> None:
        custom_path = tmp_path / "fraser_titles.json"
        args = discover_titles.parse_args(["--output", str(custom_path)])

        assert args.output == custom_path

    def test_正常系_keywords差し替え(self) -> None:
        args = discover_titles.parse_args(
            ["--keywords", "Beige Book", "Monetary Policy Report"]
        )

        assert args.keywords == ["Beige Book", "Monetary Policy Report"]


class TestFetchSubjects:
    """``fetch_subjects`` payload handling."""

    def test_正常系_subjects配列を返す(self) -> None:
        subjects = [{"id": 1, "name": "FOMC"}, {"id": 2, "name": "Beige Book"}]
        session = _make_session([{"subjects": subjects}])

        result = discover_titles.fetch_subjects(session)

        assert result == subjects

    def test_エッジケース_dict以外のレスポンスで空リスト(self) -> None:
        session = _make_session([{"subjects": "not-a-list"}])

        result = discover_titles.fetch_subjects(session)

        assert result == []

    def test_エッジケース_subjectsキーなしで空リスト(self) -> None:
        session = _make_session([{"items": []}])

        result = discover_titles.fetch_subjects(session)

        assert result == []

    def test_エッジケース_リストレスポンスで空リスト(self) -> None:
        session = MagicMock()
        session.get_with_retry.return_value = _make_response([])  # type: ignore[arg-type]

        result = discover_titles.fetch_subjects(session)

        assert result == []


class TestFindMatchingSubjects:
    """``find_matching_subjects`` filter."""

    def test_正常系_部分一致でフィルタ(self) -> None:
        subjects = [
            {"id": 1, "name": "Federal Open Market Committee"},
            {"id": 2, "name": "Beige Book"},
            {"id": 3, "name": "FOMC Press"},
        ]

        matched = discover_titles.find_matching_subjects(subjects, "FOMC")

        assert len(matched) == 1
        assert matched[0]["id"] == 3

    def test_正常系_大文字小文字非依存(self) -> None:
        subjects = [{"id": 1, "name": "Federal Open Market Committee"}]

        matched = discover_titles.find_matching_subjects(
            subjects, "federal open market"
        )

        assert len(matched) == 1

    def test_エッジケース_nameフィールドなしで除外(self) -> None:
        subjects = [{"id": 1}, {"id": 2, "name": "Beige Book"}]

        matched = discover_titles.find_matching_subjects(subjects, "Beige")

        assert len(matched) == 1
        assert matched[0]["id"] == 2


class TestFetchTitlesForSubject:
    """``fetch_titles_for_subject`` payload handling."""

    def test_正常系_titles配列を返す(self) -> None:
        titles = [{"id": 100, "name": "Title A"}, {"id": 200, "name": "Title B"}]
        session = _make_session([{"titles": titles}])

        result = discover_titles.fetch_titles_for_subject(session, subject_id=99)

        assert result == titles
        session.get_with_retry.assert_called_once()

    def test_エッジケース_titlesなしで空リスト(self) -> None:
        session = _make_session([{}])

        result = discover_titles.fetch_titles_for_subject(session, subject_id=99)

        assert result == []


class TestSelectTitle:
    """``_select_title`` interactive / auto selection."""

    def test_エッジケース_空候補でNone(self) -> None:
        chosen = discover_titles._select_title([], "Keyword", interactive=False)

        assert chosen is None

    def test_正常系_非対話モードで先頭候補(self) -> None:
        titles = [{"id": 42, "name": "First"}, {"id": 99, "name": "Second"}]

        chosen = discover_titles._select_title(titles, "X", interactive=False)

        assert chosen == 42

    def test_エッジケース_非対話モード_id無しでNone(self) -> None:
        titles = [{"name": "Missing id"}]

        chosen = discover_titles._select_title(titles, "X", interactive=False)

        assert chosen is None

    def test_正常系_対話モードで数値選択(self) -> None:
        titles = [{"id": 10, "name": "A"}, {"id": 20, "name": "B"}]

        with patch("builtins.input", side_effect=["2"]):
            chosen = discover_titles._select_title(titles, "X", interactive=True)

        assert chosen == 20

    def test_正常系_対話モードでskip(self) -> None:
        titles = [{"id": 10, "name": "A"}]

        with patch("builtins.input", side_effect=["s"]):
            chosen = discover_titles._select_title(titles, "X", interactive=True)

        assert chosen is None

    def test_異常系_対話モード_範囲外でリトライ(self) -> None:
        titles = [{"id": 10, "name": "A"}]

        with patch("builtins.input", side_effect=["999", "abc", "1"]):
            chosen = discover_titles._select_title(titles, "X", interactive=True)

        assert chosen == 10


class TestDiscoverTitleIds:
    """``discover_title_ids`` end-to-end orchestration."""

    def test_エッジケース_subjects空で即空dict(self) -> None:
        session = _make_session([{"subjects": []}])

        result = discover_titles.discover_title_ids(
            session, keywords=["Beige Book"], interactive=False
        )

        assert result == {}

    def test_正常系_keywordsからdiscovery(self) -> None:
        subjects_payload = {
            "subjects": [
                {"id": 1, "name": "Beige Book"},
            ]
        }
        titles_payload = {
            "titles": [{"id": 555, "name": "Beige Book Reports"}],
        }
        session = MagicMock()
        session.get_with_retry.side_effect = [
            _make_response(subjects_payload),
            _make_response(titles_payload),
        ]

        result = discover_titles.discover_title_ids(
            session, keywords=["Beige Book"], interactive=False
        )

        assert result == {"beige_book": 555}

    def test_エッジケース_未マップキーワードはスキップ(self) -> None:
        session = _make_session([{"subjects": [{"id": 1, "name": "Anything"}]}])

        result = discover_titles.discover_title_ids(
            session, keywords=["Not A Real Category"], interactive=False
        )

        assert result == {}

    def test_異常系_titlesフェッチエラーは継続(self) -> None:
        subjects_payload = {
            "subjects": [
                {"id": 1, "name": "Beige Book"},
                {"id": 2, "name": "Beige Book Archive"},
            ]
        }
        titles_payload = {"titles": [{"id": 700, "name": "Reports"}]}
        session = MagicMock()
        session.get_with_retry.side_effect = [
            _make_response(subjects_payload),
            FraserError("simulated failure"),
            _make_response(titles_payload),
        ]

        result = discover_titles.discover_title_ids(
            session, keywords=["Beige Book"], interactive=False
        )

        assert result == {"beige_book": 700}


class TestWriteTitlesJson:
    """``write_titles_json`` merge + backfill behaviour."""

    def test_正常系_新規ファイル作成_KNOWN_TITLE_IDSバックフィル(
        self, tmp_path: Any
    ) -> None:
        output_path = tmp_path / "fraser_titles.json"

        discover_titles.write_titles_json(output_path, discovered={"beige_book": 700})

        loaded = json.loads(output_path.read_text(encoding="utf-8"))
        # KNOWN_TITLE_IDS の fomc_minutes (677) がバックフィルされる
        assert loaded["fomc_minutes"] == 677
        # discovered の値が含まれる
        assert loaded["beige_book"] == 700

    def test_正常系_既存値を保持しつつ上書き(self, tmp_path: Any) -> None:
        output_path = tmp_path / "fraser_titles.json"
        output_path.write_text(
            json.dumps({"fomc_minutes": 999, "preserved": 123}), encoding="utf-8"
        )

        discover_titles.write_titles_json(output_path, discovered={"fomc_minutes": 677})

        loaded = json.loads(output_path.read_text(encoding="utf-8"))
        assert loaded["fomc_minutes"] == 677
        assert loaded["preserved"] == 123

    def test_異常系_不正なJSON既存ファイルでフォールバック(self, tmp_path: Any) -> None:
        output_path = tmp_path / "fraser_titles.json"
        output_path.write_text("{ not valid json", encoding="utf-8")

        # 例外を投げず、既存={} として処理続行する
        discover_titles.write_titles_json(output_path, discovered={"beige_book": 700})

        loaded = json.loads(output_path.read_text(encoding="utf-8"))
        assert loaded["beige_book"] == 700

    def test_エッジケース_親ディレクトリ自動作成(self, tmp_path: Any) -> None:
        output_path = tmp_path / "nested" / "dir" / "fraser_titles.json"

        discover_titles.write_titles_json(output_path, discovered={"beige_book": 1})

        assert output_path.exists()


class TestRun:
    """``run`` driver function smoke tests."""

    def test_正常系_全工程実行(self, tmp_path: Any) -> None:
        output_path = tmp_path / "fraser_titles.json"
        args = argparse.Namespace(
            output=output_path, interactive=False, keywords=["Beige Book"]
        )

        subjects_payload = {"subjects": [{"id": 1, "name": "Beige Book"}]}
        titles_payload = {"titles": [{"id": 555, "name": "Beige Book Reports"}]}

        session_mock = MagicMock()
        session_mock.__enter__ = MagicMock(return_value=session_mock)
        session_mock.__exit__ = MagicMock(return_value=False)
        session_mock.get_with_retry.side_effect = [
            _make_response(subjects_payload),
            _make_response(titles_payload),
        ]

        with patch.object(discover_titles, "FraserSession", return_value=session_mock):
            exit_code = discover_titles.run(args)

        assert exit_code == 0
        assert output_path.exists()
        loaded = json.loads(output_path.read_text(encoding="utf-8"))
        assert loaded["beige_book"] == 555


# Ensure unused pytest import shows up under coverage tools.
pytestmark = pytest.mark.unit

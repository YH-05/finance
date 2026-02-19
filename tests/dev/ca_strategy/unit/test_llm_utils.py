"""単体テスト: LLM共通ユーティリティ関数群。

対象モジュール: src/dev/ca_strategy/_llm_utils.py

load_directory, load_file, extract_text_from_response, strip_code_block,
call_llm の5関数を検証する。外部 API コール（anthropic）はモック化する。
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest

from dev.ca_strategy._llm_utils import (
    build_kb_section,
    call_llm,
    extract_text_from_response,
    load_directory,
    load_file,
    strip_code_block,
)

if TYPE_CHECKING:
    from pathlib import Path


# =============================================================================
# load_directory
# =============================================================================
class TestLoadDirectory:
    """load_directory 関数のテスト。"""

    def test_正常系_mdファイルが全て読み込まれる(self, tmp_path: Path) -> None:
        """ディレクトリ内の .md ファイルが全て読み込まれることを確認。"""
        (tmp_path / "rule01.md").write_text("# Rule 1", encoding="utf-8")
        (tmp_path / "rule02.md").write_text("# Rule 2", encoding="utf-8")
        (tmp_path / "rule03.md").write_text("# Rule 3", encoding="utf-8")

        result = load_directory(tmp_path)

        assert len(result) == 3
        assert "rule01" in result
        assert "rule02" in result
        assert "rule03" in result

    def test_正常系_ファイルステムが拡張子なしでキーになる(
        self, tmp_path: Path
    ) -> None:
        """ファイルのステム（拡張子を除いた名前）がキーになることを確認。"""
        (tmp_path / "kb1_rule.md").write_text("content", encoding="utf-8")

        result = load_directory(tmp_path)

        assert "kb1_rule" in result
        assert ".md" not in next(iter(result.keys()))

    def test_正常系_ファイルの内容が正しく読み込まれる(self, tmp_path: Path) -> None:
        """ファイルの内容が正しく読み込まれることを確認。"""
        content = "# テストルール\n競争優位性の評価基準"
        (tmp_path / "rule.md").write_text(content, encoding="utf-8")

        result = load_directory(tmp_path)

        assert result["rule"] == content

    def test_正常系_ファイルがアルファベット順にソートされる(
        self, tmp_path: Path
    ) -> None:
        """ファイルがアルファベット順に処理されることを確認。"""
        (tmp_path / "c_rule.md").write_text("C", encoding="utf-8")
        (tmp_path / "a_rule.md").write_text("A", encoding="utf-8")
        (tmp_path / "b_rule.md").write_text("B", encoding="utf-8")

        result = load_directory(tmp_path)

        keys = list(result.keys())
        assert keys == sorted(keys)

    def test_正常系_md以外のファイルは無視される(self, tmp_path: Path) -> None:
        """txt や json などの非 .md ファイルが無視されることを確認。"""
        (tmp_path / "rule.md").write_text("# Rule", encoding="utf-8")
        (tmp_path / "data.json").write_text('{"key": "value"}', encoding="utf-8")
        (tmp_path / "notes.txt").write_text("notes", encoding="utf-8")

        result = load_directory(tmp_path)

        assert len(result) == 1
        assert "rule" in result

    def test_エッジケース_存在しないディレクトリで空dictが返される(
        self, tmp_path: Path
    ) -> None:
        """存在しないディレクトリで空の dict が返されることを確認。"""
        non_existent = tmp_path / "non_existent"

        result = load_directory(non_existent)

        assert result == {}

    def test_エッジケース_空ディレクトリで空dictが返される(
        self, tmp_path: Path
    ) -> None:
        """空のディレクトリで空の dict が返されることを確認。"""
        result = load_directory(tmp_path)

        assert result == {}

    def test_エッジケース_UTF8マルチバイト文字を含むファイルが正しく読める(
        self, tmp_path: Path
    ) -> None:
        """日本語などのマルチバイト文字が正しく読み込まれることを確認。"""
        content = "競争優位性の評価基準：持続的な競争優位"
        (tmp_path / "japanese.md").write_text(content, encoding="utf-8")

        result = load_directory(tmp_path)

        assert result["japanese"] == content

    def test_異常系_OSErrorが発生したファイルはスキップされる(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """OSError が発生したファイルをスキップし他のファイルは正常読み込みされることを確認。"""
        (tmp_path / "rule01.md").write_text("OK", encoding="utf-8")
        (tmp_path / "rule02.md").write_text("OK", encoding="utf-8")

        call_count: list[int] = [0]

        def _raise_on_first(*args: object, **kwargs: object) -> str:
            call_count[0] += 1
            if call_count[0] == 1:
                raise OSError("Permission denied")
            return "OK"

        monkeypatch.setattr("pathlib.Path.read_text", _raise_on_first)

        result = load_directory(tmp_path)

        # rule02 should still be loaded even though rule01 raised OSError
        assert isinstance(result, dict)
        assert len(result) == 1


# =============================================================================
# load_file
# =============================================================================
class TestLoadFile:
    """load_file 関数のテスト。"""

    def test_正常系_存在するファイルの内容が返される(self, tmp_path: Path) -> None:
        """存在するファイルの内容が返されることを確認。"""
        content = "# システムプロンプト\nYou are an analyst."
        filepath = tmp_path / "prompt.md"
        filepath.write_text(content, encoding="utf-8")

        result = load_file(filepath)

        assert result == content

    def test_正常系_UTF8マルチバイト文字を含むファイルが正しく読める(
        self, tmp_path: Path
    ) -> None:
        """日本語などのマルチバイト文字が正しく読み込まれることを確認。"""
        content = "競争優位性の評価基準"
        filepath = tmp_path / "japanese.md"
        filepath.write_text(content, encoding="utf-8")

        result = load_file(filepath)

        assert result == content

    def test_エッジケース_存在しないファイルで空文字が返される(
        self, tmp_path: Path
    ) -> None:
        """存在しないファイルで空文字列が返されることを確認。"""
        non_existent = tmp_path / "non_existent.md"

        result = load_file(non_existent)

        assert result == ""

    def test_エッジケース_空のファイルで空文字が返される(self, tmp_path: Path) -> None:
        """空のファイルで空文字列が返されることを確認。"""
        filepath = tmp_path / "empty.md"
        filepath.write_text("", encoding="utf-8")

        result = load_file(filepath)

        assert result == ""

    def test_異常系_OSErrorが発生した場合空文字が返される(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """存在するファイルで OSError が発生した場合に空文字が返されることを確認。"""
        filepath = tmp_path / "prompt.md"
        filepath.write_text("content", encoding="utf-8")

        def _raise_oserror(*args: object, **kwargs: object) -> str:
            raise OSError("Permission denied")

        monkeypatch.setattr("pathlib.Path.read_text", _raise_oserror)

        result = load_file(filepath)

        assert result == ""

    def test_エッジケース_複数行のファイルが正しく読み込まれる(
        self, tmp_path: Path
    ) -> None:
        """複数行のファイルが改行を保持して読み込まれることを確認。"""
        content = "line1\nline2\nline3"
        filepath = tmp_path / "multiline.md"
        filepath.write_text(content, encoding="utf-8")

        result = load_file(filepath)

        assert result == content
        assert result.count("\n") == 2


# =============================================================================
# extract_text_from_response
# =============================================================================
class TestExtractTextFromResponse:
    """extract_text_from_response 関数のテスト。"""

    def test_正常系_単一TextBlockからテキストが抽出される(self) -> None:
        """単一の TextBlock を含むレスポンスからテキストが抽出されることを確認。"""
        mock_message = MagicMock()
        mock_block = MagicMock()
        mock_block.text = "Hello, world!"
        mock_message.content = [mock_block]

        result = extract_text_from_response(mock_message)

        assert result == "Hello, world!"

    def test_正常系_複数TextBlockが改行で結合される(self) -> None:
        """複数の TextBlock が改行で結合されることを確認。"""
        mock_message = MagicMock()
        block1 = MagicMock()
        block1.text = "First block"
        block2 = MagicMock()
        block2.text = "Second block"
        mock_message.content = [block1, block2]

        result = extract_text_from_response(mock_message)

        assert result == "First block\nSecond block"

    def test_正常系_text属性を持たないブロックは無視される(self) -> None:
        """text 属性を持たないブロック（ToolUseBlock 等）が無視されることを確認。"""
        mock_message = MagicMock()
        text_block = MagicMock(spec=["text"])
        text_block.text = "text content"
        tool_block = MagicMock(spec=[])  # text 属性なし
        mock_message.content = [text_block, tool_block]

        result = extract_text_from_response(mock_message)

        assert result == "text content"

    def test_エッジケース_空のcontentリストで空文字が返される(self) -> None:
        """content が空リストの場合に空文字列が返されることを確認。"""
        mock_message = MagicMock()
        mock_message.content = []

        result = extract_text_from_response(mock_message)

        assert result == ""

    def test_エッジケース_空のテキストブロックで空文字が返される(self) -> None:
        """text が空文字の TextBlock のみの場合に空文字列が返されることを確認。"""
        mock_message = MagicMock()
        block = MagicMock()
        block.text = ""
        mock_message.content = [block]

        result = extract_text_from_response(mock_message)

        assert result == ""

    def test_正常系_JSON文字列を含むテキストが正しく抽出される(self) -> None:
        """JSON 文字列を含むテキストが正しく抽出されることを確認。"""
        json_content = '{"claims": [{"id": "CA-001", "claim": "test"}]}'
        mock_message = MagicMock()
        block = MagicMock()
        block.text = json_content
        mock_message.content = [block]

        result = extract_text_from_response(mock_message)

        assert result == json_content


# =============================================================================
# strip_code_block
# =============================================================================
class TestStripCodeBlock:
    """strip_code_block 関数のテスト。"""

    def test_正常系_jsonコードブロックが取り除かれる(self) -> None:
        """```json ... ``` 形式のコードブロックが取り除かれることを確認。"""
        text = '```json\n{"key": "value"}\n```'

        result = strip_code_block(text)

        assert result == '{"key": "value"}'

    def test_正常系_言語指定なしコードブロックが取り除かれる(self) -> None:
        """``` ... ``` 形式（言語指定なし）のコードブロックが取り除かれることを確認。"""
        text = "```\nsome content\n```"

        result = strip_code_block(text)

        assert result == "some content"

    def test_正常系_コードブロックなしのテキストはそのまま返される(self) -> None:
        """コードブロックで囲まれていないテキストがそのまま返されることを確認。"""
        text = '{"key": "value"}'

        result = strip_code_block(text)

        assert result == '{"key": "value"}'

    def test_正常系_前後の空白が除去される(self) -> None:
        """コードブロック内のテキストの前後の空白が除去されることを確認。"""
        text = "```json\n  content  \n```"

        result = strip_code_block(text)

        assert result == "content"

    def test_正常系_複数行のJSONが正しく抽出される(self) -> None:
        """複数行の JSON がコードブロックから正しく抽出されることを確認。"""
        json_lines = '{\n  "claims": [\n    {"id": "CA-001"}\n  ]\n}'
        text = f"```json\n{json_lines}\n```"

        result = strip_code_block(text)

        assert result == json_lines

    def test_エッジケース_空文字入力で空文字が返される(self) -> None:
        """空文字列の入力で空文字列が返されることを確認。"""
        result = strip_code_block("")

        assert result == ""

    def test_エッジケース_コードブロックのみで空文字が返される(self) -> None:
        """コードブロック記号のみの入力で空文字列が返されることを確認。"""
        result = strip_code_block("```json\n\n```")

        assert result == ""

    def test_正常系_プレーンテキストの前後空白が除去される(self) -> None:
        """コードブロックなしのプレーンテキストで前後の空白が除去されることを確認。"""
        result = strip_code_block("  plain text  ")

        assert result == "plain text"

    @pytest.mark.parametrize(
        "input_text,expected",
        [
            ('```json\n{"a": 1}\n```', '{"a": 1}'),
            ('```\n{"a": 1}\n```', '{"a": 1}'),
            ('{"a": 1}', '{"a": 1}'),
            ("  bare text  ", "bare text"),
        ],
    )
    def test_パラメータ化_様々な入力形式で正しく処理される(
        self, input_text: str, expected: str
    ) -> None:
        """様々な入力形式で strip_code_block が正しく処理することを確認。"""
        result = strip_code_block(input_text)

        assert result == expected


# =============================================================================
# call_llm
# =============================================================================
class TestCallLlm:
    """call_llm 関数のテスト。"""

    @pytest.fixture
    def mock_client(self) -> MagicMock:
        """Anthropic クライアントのモックを作成する。"""
        client = MagicMock()
        return client

    @pytest.fixture
    def mock_cost_tracker(self) -> MagicMock:
        """CostTracker のモックを作成する。"""
        return MagicMock()

    @pytest.fixture
    def mock_message(self) -> MagicMock:
        """成功した API レスポンスのモックを作成する。"""
        message = MagicMock()
        block = MagicMock()
        block.text = "LLM response text"
        message.content = [block]
        message.usage.input_tokens = 1000
        message.usage.output_tokens = 500
        return message

    def test_正常系_LLMからテキストが返される(
        self,
        mock_client: MagicMock,
        mock_cost_tracker: MagicMock,
        mock_message: MagicMock,
    ) -> None:
        """call_llm が LLM レスポンスからテキストを返すことを確認。"""
        mock_client.messages.create.return_value = mock_message

        result = call_llm(
            mock_client,
            model="claude-sonnet-4-20250514",
            system="You are an analyst.",
            user_content="Analyze this transcript.",
            max_tokens=4096,
            temperature=0.0,
            cost_tracker=mock_cost_tracker,
            phase="phase1",
        )

        assert result == "LLM response text"

    def test_正常系_messages_createが正しいパラメータで呼ばれる(
        self,
        mock_client: MagicMock,
        mock_cost_tracker: MagicMock,
        mock_message: MagicMock,
    ) -> None:
        """client.messages.create が正しいパラメータで呼ばれることを確認。"""
        mock_client.messages.create.return_value = mock_message
        system_prompt = "You are an analyst."
        user_content = "Analyze this transcript."

        call_llm(
            mock_client,
            model="claude-sonnet-4-20250514",
            system=system_prompt,
            user_content=user_content,
            max_tokens=4096,
            temperature=0.0,
            cost_tracker=mock_cost_tracker,
            phase="phase1",
        )

        mock_client.messages.create.assert_called_once()
        call_kwargs = mock_client.messages.create.call_args.kwargs
        assert call_kwargs["model"] == "claude-sonnet-4-20250514"
        assert call_kwargs["system"] == system_prompt
        assert call_kwargs["max_tokens"] == 4096
        assert call_kwargs["temperature"] == 0.0

    def test_正常系_usercontentがmessagesに渡される(
        self,
        mock_client: MagicMock,
        mock_cost_tracker: MagicMock,
        mock_message: MagicMock,
    ) -> None:
        """user_content が messages パラメータに渡されることを確認。"""
        mock_client.messages.create.return_value = mock_message
        user_content = "Analyze this transcript."

        call_llm(
            mock_client,
            model="claude-sonnet-4-20250514",
            system="System",
            user_content=user_content,
            max_tokens=4096,
            temperature=0.0,
            cost_tracker=mock_cost_tracker,
            phase="phase1",
        )

        call_kwargs = mock_client.messages.create.call_args.kwargs
        messages = call_kwargs["messages"]
        assert len(messages) == 1
        assert messages[0]["role"] == "user"
        assert messages[0]["content"] == user_content

    def test_正常系_CostTrackerのrecordが呼ばれる(
        self,
        mock_client: MagicMock,
        mock_cost_tracker: MagicMock,
        mock_message: MagicMock,
    ) -> None:
        """cost_tracker.record が正しいパラメータで呼ばれることを確認。"""
        mock_client.messages.create.return_value = mock_message

        call_llm(
            mock_client,
            model="claude-sonnet-4-20250514",
            system="System",
            user_content="Content",
            max_tokens=4096,
            temperature=0.0,
            cost_tracker=mock_cost_tracker,
            phase="phase1",
        )

        mock_cost_tracker.record.assert_called_once_with(
            phase="phase1",
            tokens_input=1000,
            tokens_output=500,
        )

    def test_正常系_phaseが正しくCostTrackerに渡される(
        self,
        mock_client: MagicMock,
        mock_cost_tracker: MagicMock,
        mock_message: MagicMock,
    ) -> None:
        """phase 引数が cost_tracker.record に正しく渡されることを確認。"""
        mock_client.messages.create.return_value = mock_message

        call_llm(
            mock_client,
            model="claude-sonnet-4-20250514",
            system="System",
            user_content="Content",
            max_tokens=4096,
            temperature=0.0,
            cost_tracker=mock_cost_tracker,
            phase="phase2",
        )

        call_kwargs = mock_cost_tracker.record.call_args.kwargs
        assert call_kwargs["phase"] == "phase2"

    def test_正常系_複数TextBlockを含むレスポンスが正しく処理される(
        self,
        mock_client: MagicMock,
        mock_cost_tracker: MagicMock,
    ) -> None:
        """複数の TextBlock を含むレスポンスが改行で結合されることを確認。"""
        message = MagicMock()
        block1 = MagicMock()
        block1.text = "First part"
        block2 = MagicMock()
        block2.text = "Second part"
        message.content = [block1, block2]
        message.usage.input_tokens = 500
        message.usage.output_tokens = 200
        mock_client.messages.create.return_value = message

        result = call_llm(
            mock_client,
            model="claude-sonnet-4-20250514",
            system="System",
            user_content="Content",
            max_tokens=4096,
            temperature=0.0,
            cost_tracker=mock_cost_tracker,
            phase="phase1",
        )

        assert result == "First part\nSecond part"

    def test_エッジケース_temperature_0で呼び出される(
        self,
        mock_client: MagicMock,
        mock_cost_tracker: MagicMock,
        mock_message: MagicMock,
    ) -> None:
        """temperature=0 で正しく呼び出されることを確認。"""
        mock_client.messages.create.return_value = mock_message

        call_llm(
            mock_client,
            model="claude-sonnet-4-20250514",
            system="System",
            user_content="Content",
            max_tokens=4096,
            temperature=0,
            cost_tracker=mock_cost_tracker,
            phase="phase1",
        )

        call_kwargs = mock_client.messages.create.call_args.kwargs
        assert call_kwargs["temperature"] == 0


# =============================================================================
# build_kb_section
# =============================================================================
class TestBuildKbSection:
    """build_kb_section 関数のテスト。

    ヘッダーとアイテムリストからナレッジベースセクションを構築する。
    """

    def test_正常系_ヘッダーとアイテムで正しく構築される(self) -> None:
        result = build_kb_section(
            header="## KB1 Rules",
            items=[
                ("Rule 1", "Content of rule 1"),
                ("Rule 2", "Content of rule 2"),
            ],
        )

        assert isinstance(result, list)
        assert len(result) == 3
        assert result[0] == "## KB1 Rules\n"
        assert result[1] == "### Rule 1\n\nContent of rule 1\n"
        assert result[2] == "### Rule 2\n\nContent of rule 2\n"

    def test_正常系_アイテムが空の場合はヘッダーのみ返す(self) -> None:
        result = build_kb_section(
            header="## Empty Section",
            items=[],
        )

        assert len(result) == 1
        assert result[0] == "## Empty Section\n"

    def test_正常系_単一アイテムで正しく構築される(self) -> None:
        result = build_kb_section(
            header="## Single Item",
            items=[("Only Item", "Only content")],
        )

        assert len(result) == 2
        assert result[0] == "## Single Item\n"
        assert result[1] == "### Only Item\n\nOnly content\n"

    def test_正常系_返り値の型がlist_of_str(self) -> None:
        result = build_kb_section(
            header="## Test",
            items=[("A", "content A")],
        )

        assert all(isinstance(item, str) for item in result)

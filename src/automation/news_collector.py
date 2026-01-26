"""finance-news-workflow を Claude Agent SDK で実行するスクリプト。

金融ニュースをRSSフィードから収集し、GitHub Project #15 に投稿する
ワークフローを自動実行します。

Examples
--------
CLI から実行:
    $ uv run python -m automation.news_collector
    $ uv run python -m automation.news_collector --days 3 --dry-run

Python から実行:
    >>> from automation.news_collector import run_news_collection
    >>> await run_news_collection(days=7, themes=["index", "macro"])
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Sequence

# AIDEV-NOTE: database パッケージのロガーを使用
# インポートエラー時は標準ロギングにフォールバック
try:
    from database import get_logger

    logger = get_logger(__name__)
except ImportError:
    import logging

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)


@dataclass
class NewsCollectorConfig:
    """ニュース収集の設定。

    Attributes
    ----------
    days
        過去何日分のニュースを対象とするか
    project
        GitHub Project 番号
    themes
        対象テーマのリスト（空の場合は全テーマ）
    dry_run
        True の場合、GitHub 投稿せずに結果確認のみ
    """

    days: int = 7
    project: int = 15
    themes: list[str] = field(default_factory=list)
    dry_run: bool = False

    def to_command_args(self) -> str:
        """コマンド引数文字列を生成する。

        Returns
        -------
        str
            /finance-news-workflow コマンドに渡す引数文字列
        """
        args_parts: list[str] = []

        if self.days != 7:
            args_parts.append(f"--days {self.days}")

        if self.project != 15:
            args_parts.append(f"--project {self.project}")

        if self.themes:
            themes_str = ",".join(self.themes)
            args_parts.append(f'--themes "{themes_str}"')

        if self.dry_run:
            args_parts.append("--dry-run")

        return " ".join(args_parts)


class NewsCollector:
    """金融ニュース収集の実行管理クラス。

    Claude Agent SDK を使用して finance-news-workflow スキルを実行します。

    Parameters
    ----------
    config
        ニュース収集の設定

    Examples
    --------
    >>> config = NewsCollectorConfig(days=3, dry_run=True)
    >>> collector = NewsCollector(config)
    >>> await collector.run()
    """

    def __init__(self, config: NewsCollectorConfig | None = None) -> None:
        self.config = config or NewsCollectorConfig()
        self._project_root = self._find_project_root()

    def _find_project_root(self) -> Path:
        """プロジェクトルートディレクトリを検索する。

        Returns
        -------
        Path
            プロジェクトルートのパス

        Raises
        ------
        FileNotFoundError
            プロジェクトルートが見つからない場合
        """
        current = Path(__file__).resolve().parent
        for parent in [current, *current.parents]:
            if (parent / "pyproject.toml").exists():
                return parent
        msg = "Project root not found (pyproject.toml not found in parent directories)"
        raise FileNotFoundError(msg)

    def _load_mcp_config(self) -> dict[str, Any]:
        """MCP設定ファイルを読み込む。

        Returns
        -------
        dict[str, Any]
            MCP設定（mcpServers部分）

        Notes
        -----
        .mcp.json が存在しない場合は空の辞書を返す。
        """
        mcp_config_path = self._project_root / ".mcp.json"
        if not mcp_config_path.exists():
            logger.warning("MCP config not found", path=str(mcp_config_path))
            return {}

        try:
            with mcp_config_path.open() as f:
                config = json.load(f)
            return config.get("mcpServers", {})
        except json.JSONDecodeError as e:
            logger.error("Invalid MCP config JSON", error=str(e))
            return {}

    async def run(self) -> bool:
        """ニュース収集ワークフローを実行する。

        Returns
        -------
        bool
            成功した場合 True

        Raises
        ------
        RuntimeError
            Claude Agent SDK が利用できない場合
        """
        try:
            from claude_agent_sdk import ClaudeAgentOptions, query
        except ImportError as e:
            logger.error(
                "Claude Agent SDK not installed",
                error=str(e),
                hint="Run: uv add claude-agent-sdk",
            )
            raise RuntimeError("claude-agent-sdk is not installed") from e

        command_args = self.config.to_command_args()
        prompt = f"/finance-news-workflow {command_args}".strip()

        logger.info(
            "Starting news collection",
            prompt=prompt,
            days=self.config.days,
            themes=self.config.themes or "all",
            dry_run=self.config.dry_run,
        )

        # MCP設定を読み込み
        mcp_servers = self._load_mcp_config()

        # AIDEV-NOTE: MCPサーバー設定は辞書形式または.mcp.jsonパスで渡す
        options_kwargs: dict[str, Any] = {
            "cwd": str(self._project_root),
            # AIDEV-NOTE: 自動承認を有効化（非対話実行のため）
            "allowed_tools": ["Read", "Write", "Edit", "Bash", "Glob", "Grep", "Task"],
            # AIDEV-NOTE: ファイル編集を自動承認
            "permission_mode": "acceptEdits",
        }

        # MCP サーバー設定がある場合のみ追加
        if mcp_servers:
            options_kwargs["mcp_servers"] = mcp_servers

        options = ClaudeAgentOptions(**options_kwargs)

        try:
            # AIDEV-NOTE: ストリーミング実行で進捗を確認可能
            async for message in query(prompt=prompt, options=options):
                # メッセージを処理（デバッグログ）
                if hasattr(message, "type"):
                    logger.debug("Claude message", message_type=message.type)
                # テキスト出力があれば表示
                if hasattr(message, "content") and message.content:
                    print(message.content, flush=True)
        except Exception as e:
            logger.error("News collection failed", error=str(e), exc_info=True)
            return False

        logger.info("News collection completed")
        return True


async def run_news_collection(
    *,
    days: int = 7,
    project: int = 15,
    themes: Sequence[str] | None = None,
    dry_run: bool = False,
) -> bool:
    """ニュース収集を実行するメインエントリポイント。

    Parameters
    ----------
    days
        過去何日分のニュースを対象とするか
    project
        GitHub Project 番号
    themes
        対象テーマのリスト（None の場合は全テーマ）
    dry_run
        True の場合、GitHub 投稿せずに結果確認のみ

    Returns
    -------
    bool
        成功した場合 True

    Examples
    --------
    >>> await run_news_collection(days=3, themes=["index", "macro"])
    True
    """
    config = NewsCollectorConfig(
        days=days,
        project=project,
        themes=list(themes) if themes else [],
        dry_run=dry_run,
    )
    collector = NewsCollector(config)
    return await collector.run()


def parse_args(argv: Sequence[str] | None = None) -> NewsCollectorConfig:
    """コマンドライン引数をパースする。

    Parameters
    ----------
    argv
        引数リスト（None の場合は sys.argv を使用）

    Returns
    -------
    NewsCollectorConfig
        パースされた設定
    """
    parser = argparse.ArgumentParser(
        description="金融ニュース収集ワークフローを実行",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # デフォルト設定で実行
  uv run python -m automation.news_collector

  # 過去3日分を対象
  uv run python -m automation.news_collector --days 3

  # 特定テーマのみ
  uv run python -m automation.news_collector --themes index,macro

  # ドライラン（投稿なし）
  uv run python -m automation.news_collector --dry-run
        """,
    )

    parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="過去何日分のニュースを対象とするか（デフォルト: 7）",
    )

    parser.add_argument(
        "--project",
        type=int,
        default=15,
        help="GitHub Project 番号（デフォルト: 15）",
    )

    parser.add_argument(
        "--themes",
        type=str,
        default="",
        help="対象テーマ（カンマ区切り、例: index,macro,stock）",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="GitHub 投稿せずに結果確認のみ",
    )

    args = parser.parse_args(argv)

    themes = [t.strip() for t in args.themes.split(",") if t.strip()]

    return NewsCollectorConfig(
        days=args.days,
        project=args.project,
        themes=themes,
        dry_run=args.dry_run,
    )


def main() -> int:
    """CLI エントリポイント。

    Returns
    -------
    int
        終了コード（0: 成功, 1: 失敗）
    """
    config = parse_args()
    collector = NewsCollector(config)

    try:
        success = asyncio.run(collector.run())
        return 0 if success else 1
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        return 130
    except Exception as e:
        logger.error("Unexpected error", error=str(e), exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())

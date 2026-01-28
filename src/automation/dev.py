import asyncio

from claude_agent_sdk import ClaudeAgentOptions, query  # type: ignore[import-not-found]
from claude_agent_sdk.types import ResultMessage  # type: ignore[import-not-found]
from rich.console import Console


async def main():
    console = Console()
    async for message in query(
        prompt="このプロジェクトの概要を教えて",
        options=ClaudeAgentOptions(allowed_tools=["Read", "Bash"]),
    ):
        console.print(type(message))
        result = message.result if isinstance(message, ResultMessage) else message
        console.print(result)


asyncio.run(main())

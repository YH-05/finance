import asyncio

from claude_agent_sdk import ClaudeAgentOptions, query
from rich.console import Console


async def main():
    console = Console()
    async for message in query(
        prompt="このプロジェクトの概要を教えて",
        options=ClaudeAgentOptions(allowed_tools=["Read", "Bash"]),
    ):
        console.print(type(message))
        console.print(message)


asyncio.run(main())

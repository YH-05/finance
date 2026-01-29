import marimo

__generated_with = "0.19.6"
app = marimo.App()


@app.cell
def _():
    import json
    from pathlib import Path

    import feedparser
    import pandas as pd
    import trafilatura
    from claude_agent_sdk import ClaudeAgentOptions, query
    from IPython.display import Markdown, display

    root_dir = Path(__name__).cwd().parent
    json_path = root_dir / "config/fred_series.json"

    def load_rss_json(json_path: Path = json_path) -> dict:
        with open(Path("../data/config/rss-presets.json"), mode="r") as f:
            rss_json = json.load(f)["presets"]

        return rss_json

    def extract_body(url: str) -> str:
        downloaded = trafilatura.fetch_url(url)
        try:
            body_str = trafilatura.extract(downloaded, include_formatting=True)
            if not body_str:
                body_str = ""
        except Exception as e:
            print(f"An error occured: {e}")
            body_str = ""
        return body_str

    def get_entries(url: str) -> list[dict]:
        feed = feedparser.parse(url)
        entries: list[dict] = feed["entries"]

        return entries

    def filter_and_add_content_to_entry(entries: list[dict]) -> list[dict]:
        filtered_entries = []
        for entry in entries:
            filtered_entry: dict = {
                k: entry[k]
                for k in entry
                if k in ["link", "title", "summary", "published"]
            }
            filtered_entry["content"] = extract_body(url=filtered_entry["link"])
            filtered_entries.append(filtered_entry)

        return filtered_entries

    async def summarize_content(
        content: str, prompt_template: str | None = None
    ) -> str:
        """
        Claude Agent SDKを使ってコンテンツを要約する

        Parameters
        ----------
        content : str
            要約対象のテキスト
        prompt_template : str | None
            カスタムプロンプト。{content}がコンテンツに置換される。

        Returns
        -------
        str
            要約テキスト
        """
        if prompt_template is None:
            prompt_template = (
                "以下のテキストを日本語で簡潔に要約してください:\n\n{content}"
            )

        prompt = prompt_template.format(content=content)
        options = ClaudeAgentOptions()

        response_parts: list[str] = []
        async for message in query(prompt=prompt, options=options):
            if hasattr(message, "content") and message.content:
                # contentはリスト構造。各ブロックからtextを取り出す
                for block in message.content:
                    if hasattr(block, "text"):
                        response_parts.append(block.text)
                    elif isinstance(block, str):
                        response_parts.append(block)

        return "".join(response_parts)

    async def fetch_and_summarize(url: str) -> str:
        """URLから本文を取得し、要約を返す"""
        body = extract_body(url)
        if not body:
            return "コンテンツを取得できませんでした"

        summary = await summarize_content(body)
        return summary

    return (
        ClaudeAgentOptions,
        Markdown,
        display,
        filter_and_add_content_to_entry,
        get_entries,
        load_rss_json,
        query,
        summarize_content,
    )


@app.cell
def _(display, filter_and_add_content_to_entry, get_entries, load_rss_json):
    cnbc_rss = [s for s in load_rss_json() if s["title"].startswith("CNBC")]
    entries = get_entries(cnbc_rss[0]["url"])
    filtered_entries = filter_and_add_content_to_entry(entries)
    display(filtered_entries)
    return (filtered_entries,)


@app.cell
def _(Markdown, display, filtered_entries):
    print(len(filtered_entries))
    result = filtered_entries[0]["content"]
    display(Markdown(result))


@app.cell
async def _(Markdown, display, filtered_entries, summarize_content):
    # 既存のコンテンツを要約
    content = filtered_entries[0]["content"]
    summary = await summarize_content(content)
    display(Markdown(f"## 要約\n\n{summary}"))


@app.cell
async def _(ClaudeAgentOptions, filtered_entries, query):
    # デバッグ: message構造を確認
    async def debug_message_structure(content: str) -> None:
        prompt = f"以下のテキストを1行で要約してください:\n\n{content[:500]}"
        options = ClaudeAgentOptions()

        async for message in query(prompt=prompt, options=options):
            print(f"message type: {type(message)}")
            print(f"message dir: {[a for a in dir(message) if not a.startswith('_')]}")
            if hasattr(message, "content"):
                print(f"content type: {type(message.content)}")
                print(f"content: {message.content}")
                if isinstance(message.content, list) and len(message.content) > 0:
                    first = message.content[0]
                    print(f"first block type: {type(first)}")
                    print(
                        f"first block dir: {[a for a in dir(first) if not a.startswith('_')]}"
                    )
            print("---")
            break  # 最初のメッセージだけ確認

    await debug_message_structure(filtered_entries[0]["content"])


if __name__ == "__main__":
    app.run()

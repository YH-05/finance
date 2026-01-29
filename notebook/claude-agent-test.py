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
    from claude_agent_sdk import ClaudeAgentOptions
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

    return (
        Markdown,
        display,
        filter_and_add_content_to_entry,
        get_entries,
        load_rss_json,
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


if __name__ == "__main__":
    app.run()

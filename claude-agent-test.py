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

    return Markdown, Path, display, extract_body, feedparser, json


@app.cell
def _(Path, display, json):
    with open(Path("../data/config/rss-presets.json"), mode="r") as f:
        rss_json = json.load(f)["presets"]
        cnbc_rss = [s for s in rss_json if s["title"].startswith("CNBC")]

    display(cnbc_rss[0])
    return (cnbc_rss,)


@app.cell
def _(cnbc_rss, display, extract_body, feedparser):
    feed = feedparser.parse(cnbc_rss[0]["url"])
    entries = feed["entries"]
    # display(entries)

    filtered_entries = []
    for entry in entries:
        filtered_entry = {
            k: entry[k] for k in entry if k in ["link", "title", "summary", "published"]
        }
        filtered_entry["content"] = extract_body(url=filtered_entry["link"])
        filtered_entries.append(filtered_entry)
    display(filtered_entries)
    return (filtered_entries,)


@app.cell
def _(filtered_entries):
    print(len(filtered_entries))


@app.cell
def _(Markdown, display, extract_body, filtered_entries):
    result = extract_body(filtered_entries[0]["link"])

    display(Markdown(result))


@app.cell
def _(display, result_json):
    display(result_json)


if __name__ == "__main__":
    app.run()

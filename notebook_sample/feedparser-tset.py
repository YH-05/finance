import marimo

__generated_with = "0.19.2"
app = marimo.App()


@app.cell
def _():
    import feedparser

    return (feedparser,)


@app.cell
def _(feedparser):
    url = "https://feeds.a.dj.com/rss/RSSMarketsMain.xml"
    url = "https://www.ft.com/markets?format=rss"
    url = "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&type=atom"
    url = "https://www.sec.gov/news/pressreleases.xml"
    url = "https://www.sec.gov/corpfin/whatsnew.xml"
    feed = feedparser.parse(url)

    print(len(feed.entries))

    for entry in feed.entries[:5]:
        print(entry.title)
        print(entry.link)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    うまく取得できず...

    RSS フィードが更新されていない可能性がある。
    """)


@app.cell
def _():
    import marimo as mo

    return (mo,)


if __name__ == "__main__":
    app.run()

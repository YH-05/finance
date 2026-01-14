import marimo

__generated_with = "0.19.2"
app = marimo.App()


@app.cell
def _():
    from tavily import TavilyClient


    tavily_client = TavilyClient(api_key="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")
    response = tavily_client.search("Who is Leo Messi?")

    print(response)
    return (response,)


@app.cell
def _(display, response):
    display(response)
    return


if __name__ == "__main__":
    app.run()

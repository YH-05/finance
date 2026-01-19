import marimo

__generated_with = "0.19.4"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import pandas as pd
    import yfinance as yf
    return (yf,)


@app.cell
def _():
    sector_list =  [
        "basic-materials",
        "communication-services",
        "consumer-cyclical",
        "consumer-defensive",
        "energy",
        "financial-services",
        "healthcare",
        "industrials",
        "real-estate",
        "technology",
        "utilities"
      ]

    return (sector_list,)


@app.cell
def _(sector_list, yf):
    for sector in sector_list:
        symbols_sector = yf.Sector(sector).top_companies
        print(f"===== {sector} =====")
        print(symbols_sector)
    return


@app.cell
def _(yf):
    msft = yf.Ticker("MSFT")
    forward_pe = msft.info.get("forwardPE")
    trailing_pe = msft.info.get("trailingPE")
    print(forward_pe, trailing_pe)

    print(msft.earnings_dates)
    return


@app.cell
def _(yf):
    # 1. スクリーナーオブジェクトを作成
    s = yf.screen("day_gainers")
    quote_list = s['quotes']
    ticker_list = [q['symbol'] for q in quote_list]
    ticker_list
    # # 2. テクノロジーセクターの定義をセット
    # # 'ms_technology' は Yahoo Finance のスクリーナーで使用される ID です
    # s.set_predefined_body('ms_technology')

    # # 3. 実行してティッカーを抽出
    # tickers = [quotedata['symbol'] for quotedata in s.response['quotes']]

    # print(f"取得件数: {len(tickers)}")
    # print(tickers[:10]) # 冒頭10件を表示
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()

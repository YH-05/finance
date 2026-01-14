import marimo

__generated_with = "0.19.2"
app = marimo.App()


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    [参考リンク](https://kiseno-log.com/2020/08/23/python%E3%81%A7%E8%B2%A1%E5%8B%99%E5%88%86%E6%9E%90edinet%E3%81%8B%E3%82%89%E5%9B%9B%E5%8D%8A%E6%9C%9F%E6%B1%BA%E7%AE%97%E3%82%92%E5%8F%96%E5%BE%97%E3%81%99%E3%82%8B/)
    """)
    return


@app.cell
def _():
    from google.colab import drive
    drive.mount('/content/drive')
    return


@app.cell
def _():
    import requests
    import json
    import zipfile
    import glob
    from bs4 import BeautifulSoup

    import os
    return (os,)


@app.cell
def _(os):
    working_dir = '/content/drive/My Drive/05_決算書/'
    os.chdir(working_dir)
    data_dir = os.path.join(working_dir, 'python')   # 生データ用のフォルダ名を入れる
    os.makedirs(data_dir, exist_ok=True)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ##EDINETから任意の書類のコードリストを入手
    """)
    return


@app.cell
def _():
    # データ抽出時に使用する、有価証券報告書および四半期報告書のコードの設定
    ordinance_code = '010'
    form_code_quart = '043000'  # 四半期報告書のコード
    form_code_securities = '030000' # 有価証券報告書のコード
    return


@app.cell
def _():
    import marimo as mo
    return (mo,)


if __name__ == "__main__":
    app.run()

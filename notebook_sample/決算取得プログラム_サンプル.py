# /// script
# dependencies = ["arelle", "isodate"]
# ///

import marimo

__generated_with = "0.19.2"
app = marimo.App()


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    #企業の決算情報をEDINET APIで取得する
    """)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    https://non-dimension.com/get-xbrldata/
    """)


@app.cell
def _():
    from google.colab import drive

    drive.mount("/content/drive")


@app.cell
def _():
    import glob
    import json
    import os
    import zipfile

    import requests

    # packages added via marimo's package management: arelle !pip install arelle
    # packages added via marimo's package management: isodate !pip install isodate
    from arelle import Cntlr, ModelManager
    from arelle.ModelValue import qname
    from bs4 import BeautifulSoup

    return (
        BeautifulSoup,
        Cntlr,
        ModelManager,
        glob,
        json,
        os,
        qname,
        requests,
        zipfile,
    )


@app.cell
def _(os):
    working_dir = "/content/drive/My Drive/05_決算書/"
    os.chdir(working_dir)
    data_dir = os.path.join(working_dir, "python")  # 生データ用のフォルダ名を入れる
    os.makedirs(data_dir, exist_ok=True)
    return (data_dir,)


@app.cell
def _(requests):
    # 書類一覧APIのエンドポイント
    url = "https://disclosure.edinet-fsa.go.jp/api/v1/documents.json"
    # 書類一覧APIのリクエストパラメータ
    params = {"date": "2022-04-25", "type": 2}

    # 書類一覧APIの呼び出し
    res = requests.get(url, params=params, verify=False)

    # レスポンス(JSON)の表示
    print(res.text)
    return (res,)


@app.cell
def _(json, res):
    # APIの結果をjson形式に変換
    res_text = json.loads(res.text)

    # res_text内のresultsの内容を取得
    results = res_text["results"]

    # resultsの中身(docID, docDescription, filerName)を表示
    for result in results:
        print(result["docID"], result["docDescription"], result["filerName"])
    return (results,)


@app.cell
def _(results):
    kessan = []
    for result_1 in results:
        if result_1["docDescription"] is not None:
            if "半期" in result_1["docDescription"]:
                print(
                    result_1["docID"], result_1["docDescription"], result_1["filerName"]
                )
                kessan.append(result_1)
    return (kessan,)


@app.cell
def _(kessan):
    # 0番目のdocumentのdocIDを取得
    docid = kessan[0]["docID"]
    print(docid)
    return (docid,)


@app.cell
def _(data_dir, docid, os, requests):
    # 書類所得APIのエンドポイント
    url_1 = "https://disclosure.edinet-fsa.go.jp/api/v1/documents/" + docid
    os.chdir(data_dir)
    params_1 = {"type": 1}
    filename = docid + ".zip"
    # 書類取得APIのリクエストパラメータ
    res_1 = requests.get(url_1, params=params_1, verify=False)
    if res_1.status_code == 200:
        with open(filename, "wb") as f:
            for chunk in res_1.iter_content(chunk_size=1024):
                # 出力ファイル名
                # 書類取得APIの呼び出し
                # ファイルへの出力
                f.write(chunk)
    return (filename,)


@app.cell
def _(docid, filename, zipfile):
    with zipfile.ZipFile(filename) as existing_zip:
        existing_zip.extractall(docid)


@app.cell
def _(docid, glob):
    filepath = docid + "/XBRL/PublicDoc/"
    files = glob.glob(filepath + "*.htm")  # htmファイルの取得
    files = sorted(files)
    target_file = files[1]
    print(target_file)
    return (target_file,)


@app.cell
def _(target_file):
    with open(target_file, encoding="utf-8") as f_1:
        html = f_1.read()
    return (html,)


@app.cell
def _(BeautifulSoup, html):
    soup = BeautifulSoup(html, "html.parser")
    tag_p = soup.find_all("p")  # pタグの要素を取得

    # pタグのテキストを表示
    for p in tag_p:
        print(p.text)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    #ArelleでXBRL解析
    """)


@app.cell
def _(Cntlr, ModelManager, ctlr):
    # 初期化・インスタンス文章読み込み
    ctrl = Cntlr.Cntlr()
    model_manager = ModelManager.initialize(ctlr)
    model_xbrl = model_manager.load()

    # 文章情報を解放
    model_manager.close()
    return (model_xbrl,)


@app.cell
def _(model_xbrl, qname):
    # プレフィックスをキーとして名前空間URIが格納されている辞書
    ns = model_xbrl.prefixedNamespaces[""]

    # QName文字列からQName型に変更
    qn = qname(ns, name="")

    # QNameをキーとしてfactが格納されている辞書
    # 値はfactのset（同じQNameのfactは複数ありうる）
    facts = model_xbrl.factsByQname[qn]


@app.cell
def _():
    import marimo as mo

    return (mo,)


if __name__ == "__main__":
    app.run()

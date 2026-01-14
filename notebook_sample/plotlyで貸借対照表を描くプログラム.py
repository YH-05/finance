import marimo

__generated_with = "0.19.2"
app = marimo.App()


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    https://qiita.com/Fortinbras/items/d8f546d628168ddef48f
    """)


@app.cell
def _():
    from google.colab import drive

    drive.mount("/content/drive")


@app.cell
def _():
    from plotly import graph_objects as go

    return (go,)


@app.cell
def _(go):
    # 朝日新聞社のBSの数値をサンプルのデータとして利用
    # (子会社の朝日放送HDもしくはテレビ朝日HDが適時開示に「親会社の決算」を発表している)
    data = {
        "総資産": [594628, 605226, 611502, 607605, 614114, 599162, 554408],
        "負債": [256320, 288806, 278072, 234054, 231745, 223782, 217897],
        "純資産": [338307, 316419, 333429, 373551, 382368, 375380, 336511],
        "labels": [
            "2015/03本",
            "2016/03本",
            "2017/03本",
            "2018/03本",
            "2019/03本",
            "2020/03本",
            "2020/09中",
        ],
    }

    # グラフ描画
    fig1 = go.Figure(
        # データの指定
        data=[
            go.Bar(
                name="総資産",
                x=data["labels"],
                y=data["総資産"],
                offsetgroup=0,
            ),
            go.Bar(
                name="負債",
                x=data["labels"],
                y=data["負債"],
                offsetgroup=1,
                base=data["純資産"],
            ),
            go.Bar(
                name="純資産",
                x=data["labels"],
                y=data["純資産"],
                offsetgroup=1,
            ),
        ],
        # レイアウトの指定
        layout=go.Layout(
            title="朝日新聞社_貸借対照表(BS)",
            xaxis_title="決算期",
            yaxis_title="JPY(単位:百万円)",
        ),
    )
    fig1.show()


@app.cell
def _():
    import marimo as mo

    return (mo,)


if __name__ == "__main__":
    app.run()

import marimo

__generated_with = "0.19.2"
app = marimo.App()


@app.cell
def _():
    from google.colab import drive

    drive.mount("/content/drive")


@app.cell
def _():
    # !pip install selenium
    # !pip install webdriver_manager
    # 日本語の混じったcsvファイルをデータフレームに読み込むときに生じるエラーを抑える
    import glob
    import os
    import time
    import zipfile

    import pandas as pd
    from selenium import webdriver
    from webdriver_manager.chrome import ChromeDriverManager

    # import csv
    return ChromeDriverManager, glob, os, pd, time, webdriver, zipfile


@app.cell
def _(os):
    working_dir = "/content/drive/My Drive/05_決算書/"
    os.chdir(working_dir)
    data_dir = os.path.join(working_dir, "python")  # 生データ用のフォルダ名を入れる
    os.makedirs(data_dir, exist_ok=True)
    os.chdir(data_dir)
    return (data_dir,)


@app.cell
def _(ChromeDriverManager, data_dir, time, webdriver):
    def edinet_code_dl():
        # seleniumでchromeからzipファイルをダウンロード
        chromeOptions = webdriver.ChromeOptions()
        chromeOptions.add_experimental_option(
            "prefs",
            {"download.default_directory": data_dir},  # 保存先のディレクトリを指定
        )

        # ブラウザを非表示にする
        chromeOptions.add_argument("--headless")
        url = "https://disclosure.edinet-fsa.go.jp/E01EW/BLMainController.jsp"
        url += "?uji.bean=ee.bean.W1E62071.EEW1E62071Bean&uji.verb"
        url += "=W1E62071InitDisplay&TID=W1E62071&"
        url += "PID=W0EZ0001&SESSIONKEY=&lgKbn=2&dflg=0&iflg=0"

        driver = webdriver.Chrome(
            ChromeDriverManager().install(),
            options=chromeOptions,
        )
        driver.maximize_window()

        # EDINETコードリストにアクセス
        driver.get(url)
        driver.execute_script(
            "EEW1E62071EdinetCodeListDownloadAction('lgKbn=2&dflg=0&iflg=0&dispKbn=1');"
        )
        time.sleep(2)
        driver.quit()

    edinet_code_dl()


@app.cell
def _(glob, pd, zipfile):
    def unzip_to_csv():
        edinet_zip = glob.glob("Edinetcode*.zip")[0]
        zip_file = zipfile.ZipFile(edinet_zip)
        zip_file.extractall("./")
        zip_file.close()

        # os.remove(edinet_zip)
        csv_path = glob.glob("EdinetcodeDlInfo.csv")[0]
        with open(csv_path, encoding="cp932") as f_read:
            new_path = "EdinetcodeDlIinfo_utf8.csv"
            with open(new_path, "w", encoding="utf-8") as f_out:
                f_out.write(f_read.read())

        csv_path = "EdinetcodeDlIinfo_utf8.csv"
        return csv_path

    edinet_csv = unzip_to_csv()
    df = pd.read_csv(edinet_csv, header=1)
    df.drop(columns=["提出者名（英字）", "提出者名（ヨミ）", "所在地"], inplace=True)


if __name__ == "__main__":
    app.run()

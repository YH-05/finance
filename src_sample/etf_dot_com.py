"""
etf_dot_com.py
"""

import datetime
import io
import sqlite3
import time
from pathlib import Path

import numpy as np
import pandas as pd
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager


# =============================================================================
def download_all_tickers(browser_display: bool = False) -> pd.DataFrame:
    """
    etf.comのスクリーナーから全ETFのティッカーと基本情報をダウンロードする。

    Parameters
    ----------
    browser_display : bool, default False
        ブラウザを表示して実行するかどうか。Trueの場合はブラウザが表示される。

    Returns
    -------
    pd.DataFrame
        取得したETFデータを含むDataFrame。
    """
    driver = None
    final_df = pd.DataFrame()

    url = "https://www.etf.com/etfanalytics/etf-screener"
    service = Service(ChromeDriverManager().install())
    options = webdriver.ChromeOptions()

    if not browser_display:
        options.add_argument("--headless")
        # 1. ウィンドウサイズを明示的に指定
        options.add_argument("--window-size=1920,1080")
        # 2. ユーザーエージェントを設定
        options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
        # 3. その他の安定化オプション
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

    try:
        driver = webdriver.Chrome(service=service, options=options)
        wait = WebDriverWait(driver, 30)
        driver.get(url)

        # 1. クッキー同意ボタンの処理
        try:
            accept_button = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[text()='ACCEPT ALL']"))
            )
            accept_button.click()
            print("クッキー同意ボタンをクリックしました。")
        except TimeoutException:
            print("クッキー同意ボタンが見つからなかったため、処理を続行します。")

        # 2. 表示件数を「100」にするボタンをクリック
        try:
            # JavaScriptでクリックする前に、要素がビューポート内に入るようにスクロールさせる
            hundred_button = wait.until(
                EC.presence_of_element_located((By.XPATH, "//button[text()='100']"))
            )
            driver.execute_script("arguments[0].scrollIntoView(true);", hundred_button)
            # 少し待機を追加して、クリックの安定性を高める
            wait.until(EC.element_to_be_clickable((By.XPATH, "//button[text()='100']")))
            driver.execute_script("arguments[0].click();", hundred_button)

            print("表示件数を「100」に変更しました。")
            # 100行になるのを待つ
            wait.until(
                lambda d: len(d.find_elements(By.CSS_SELECTOR, "tbody tr"))
                >= 99  # 99以上などで柔軟に待つ
            )
            print("テーブルの行数が100になったことを確認しました。")
        except TimeoutException:
            print("表示件数を「100」にする処理でタイムアウトしました。")
            # デバッグ用にスクリーンショットを保存
            driver.save_screenshot("error_screenshot.png")
            print(
                "エラー時のスクリーンショットを 'error_screenshot.png' として保存しました。"
            )
            # 失敗した場合はここで処理を終了させる
            raise

        # --- ページネーションループ ---
        all_dfs = []
        page_number = 1

        while True:
            print(f"\n--- {page_number}ページ目のデータを取得しています... ---")

            # テーブル本体が表示されるのを待つ
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "tbody")))

            # 現在のページのテーブルをスクレイピング
            html_source = driver.page_source
            tables = pd.read_html(io.StringIO(html_source))
            if tables:
                all_dfs.append(tables[0])
                print(
                    f"{page_number}ページ目のテーブルを取得しました。（{len(tables[0])}行）"
                )

            # --- 新しい待機ロジック ---
            try:
                # 1. クリックする前に、現在のページの最初のティッカーのテキストを記憶
                first_ticker_before_click = wait.until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, "tbody tr:first-child td:first-child")
                    )
                ).text

                # 2. 「Next」ボタンを見つけてクリック
                next_button = driver.find_element(
                    By.XPATH, "//button[.//span[text()='Next']]"
                )
                if not next_button.is_enabled():
                    print("「Next」ボタンが無効です。最終ページに到達しました。")
                    break

                driver.execute_script("arguments[0].click();", next_button)
                print("「Next」ボタンをクリックしました。")

                # 3. 最初のティッカーの中身が変わることで、ページの更新を検知
                print("ページコンテンツの更新を待っています...")
                wait.until(
                    lambda driver: driver.find_element(
                        By.CSS_SELECTOR, "tbody tr:first-child td:first-child"
                    ).text
                    != first_ticker_before_click
                )
                print("ページの更新を確認しました。")

                page_number += 1

            except (NoSuchElementException, TimeoutException):
                print(
                    "「Next」ボタンが見つからないか、ページが更新されませんでした。最終ページに到達しました。"
                )
                break
        # --- ループ終了 ---

        # 全てのDataFrameを結合
        if all_dfs:
            final_df = (
                pd.concat(all_dfs, ignore_index=True)
                .replace("-", np.nan)
                .dropna()  # dropna()は列に一つでもNaNがあると行ごと削除するので注意
                .assign(datetime_stored=datetime.datetime.now())
            )
            print("\n--- 全ページのデータ取得完了 ---")
            return final_df
        else:
            print("データを取得できませんでした。")
            return final_df

    finally:
        if driver:
            driver.quit()


# =============================================================================
def get_tickers_from_db(db_path: Path) -> list:
    """
    データベースから本日のティッカーリストを取得する。

    Parameters
    ----------
    db_path : Path
        データベースファイルのパス。

    Returns
    -------
    list
        取得したティッカーのリスト。
    """
    print(
        f"データベース '{db_path.name}' から本日のティッカーリストを取得しています..."
    )
    # SQLiteで日付(DATE)関数を使うと、タイムゾーンを考慮せずに日付部分のみで比較できる
    query = f"""
        SELECT DISTINCT
            Ticker
        FROM
            Ticker
        WHERE
            DATE(datetime_stored) = '{datetime.date.today()}'
    """

    conn = None
    try:
        conn = sqlite3.connect(db_path)
        ticker_list = pd.read_sql(query, con=conn)["Ticker"].tolist()
        print(f"{len(ticker_list)}件のティッカーを取得しました。")
        return ticker_list
    except Exception as e:
        print(f"!! データベースからのティッカー取得中にエラー: {e}")
        return []
    finally:
        if conn:
            conn.close()


# =============================================================================
def save_data_to_db(
    df: pd.DataFrame, db_path: Path, table_name: str, if_exists="append"
):
    """
    取得したデータをデータベースに保存する。

    Parameters
    ----------
    df : pd.DataFrame
        保存するデータフレーム。
    db_path : Path
        データベースファイルのパス。
    table_name : str
        保存先のテーブル名。
    if_exists : str, default "append"
        テーブルが存在する場合の挙動 ("fail", "replace", "append")。

    Returns
    -------
    None
    """
    if df.empty:
        print("\n取得データが空のため、データベースへの保存はスキップされました。")
        return

    print(
        f"\nデータベース '{db_path.name}' のテーブル '{table_name}' にデータを保存しています..."
    )
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        df["datetime_created"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        df.to_sql(table_name, conn, index=False, if_exists=if_exists)
        print(f"データベースへの保存が完了しました。（{len(df)}行）")
    except Exception as e:
        print(f"!! データベースへの保存中にエラー: {e}")
    finally:
        if conn:
            conn.close()


# =============================================================================
def scrape_key_value_data(
    driver: webdriver.Chrome,
    wait: WebDriverWait,
    container_id: str,
    retries: int = 5,
    stability_wait: float = 1.0,
) -> dict:
    """
    データが「loading...」を含まず、かつ安定状態になるまで待機して取得する。

    Parameters
    ----------
    driver : webdriver.Chrome
        SeleniumのWebDriverインスタンス。
    wait : WebDriverWait
        SeleniumのWebDriverWaitインスタンス。
    container_id : str
        データを取得する要素のID。
    retries : int, default 5
        リトライ回数。
    stability_wait : float, default 1.0
        安定性を確認するための待機時間（秒）。

    Returns
    -------
    dict
        取得したキー・バリュー形式のデータ。
    """
    # print(f"ID='{container_id}' のデータ取得を開始（ハイブリッド待機モード）...")

    previous_data = {}

    for i in range(retries):
        current_data = {}
        try:
            container_div = wait.until(
                EC.presence_of_element_located((By.ID, container_id))
            )
            # 簡潔にするため、データ行が最低1つ現れるのを待つ
            wait.until(
                lambda d: len(
                    d.find_elements(By.CSS_SELECTOR, f"#{container_id} .inline-flex")
                )
                > 0
            )

            data_rows = container_div.find_elements(By.CLASS_NAME, "inline-flex")
            for row in data_rows:
                children = row.find_elements(By.TAG_NAME, "div")
                if len(children) == 2:
                    key = children[0].text.strip()
                    value = children[1].text.strip()
                    if key and value:
                        current_data[key] = value

            # --- ▼▼▼ 判定ロジックを強化 ▼▼▼ ---

            # 1. まず、取得データに 'loading...' が含まれているかチェック
            is_still_loading = any(
                "loading..." in str(v).lower() for v in current_data.values()
            )

            if is_still_loading:
                # 'loading...'が一つでもあれば、まだ読み込み中と判断して次のリトライへ
                # print(
                #     f"-> ID='{container_id}' に 'loading...' を検出。リトライします... ({i + 1}/{retries}回目)"
                # )
                previous_data = current_data.copy()
                time.sleep(stability_wait)
                continue

            # 2. 'loading...' がない場合、次にデータの安定性をチェック
            if previous_data and current_data and current_data == previous_data:
                # print(f"-> ID='{container_id}' のデータが安定しました。取得完了。")
                return current_data

            # --- ▲▲▲ 判定ロジックここまで ▲▲▲ ---

            previous_data = current_data.copy()
            # print(
            #     f"-> ID='{container_id}' のデータを取得。安定性を確認するため待機します... ({i + 1}/{retries}回目)"
            # )
            time.sleep(stability_wait)

        except Exception as e:
            # print(
            #     f"!! ID='{container_id}' のデータ取得中にエラーが発生: {e}。リトライします..."
            # )
            time.sleep(stability_wait)

    # print(
    #     f"!! リトライ上限に達しました。ID='{container_id}' のデータは安定しませんでした。"
    # )
    return previous_data


# =============================================================================


def get_etf_fundamentals(ticker: str, browser_display: bool = False) -> pd.DataFrame:
    """
    指定されたETFティッカーのファンダメンタルデータをetf.comからスクレイピングする。

    Parameters
    ----------
    ticker : str
        ETFのティッカーシンボル (例: "VOO")
    browser_display : bool, default False
        Trueにするとブラウザを表示して動作を確認できる

    Returns
    -------
    pd.DataFrame
        スクレイピングしたデータを含むDataFrame
    """
    url = f"https://www.etf.com/{ticker}"
    # print(f"\n--- ティッカー: {ticker} のデータ取得を開始します ---")
    # print(f"URL: {url}")

    # --- WebDriverのセットアップ ---
    options = Options()
    if not browser_display:
        # print("ヘッドレスモードで実行します。")
        options.add_argument("--headless")
        options.add_argument("--window-size=1920,1080")
        options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

    service = Service(ChromeDriverManager().install())
    driver = None  # finallyブロックで参照できるよう、外で初期化

    try:
        driver = webdriver.Chrome(service=service, options=options)
        wait = WebDriverWait(driver, 15)  # 待機時間を15秒に設定

        driver.get(url)

        # --- データ取得 ---
        # 2つのセクションからそれぞれデータを取得
        summary_data = scrape_key_value_data(driver, wait, "summary-data")
        classification_data = scrape_key_value_data(
            driver, wait, "classification-index-data"
        )

        # 取得した2つの辞書を結合
        combined_data = {**summary_data, **classification_data}

        if not combined_data:
            # print(f"!! ティッカー: {ticker} のデータを取得できませんでした。")
            return pd.DataFrame()  # 空のDataFrameを返す

        # --- DataFrameの作成 ---
        df = pd.DataFrame([combined_data])
        df = df.assign(Ticker=ticker.upper())

        # カラムの順序を整える
        cols = ["Ticker"] + [col for col in df.columns if col not in ["Ticker"]]
        df = df[cols]

        # print(f"--- ティッカー: {ticker} のデータ取得が完了しました ---")
        return df

    except Exception as e:
        # print(f"!! 処理全体で予期せぬエラーが発生しました: {e}")
        # エラー発生時にスクリーンショットを保存してデバッグに役立てる
        if driver and not browser_display:
            screenshot_path = (
                f"error_{ticker}_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.png"
            )
            driver.save_screenshot(screenshot_path)
            # print(
            #     f"エラー発生時のスクリーンショットを '{screenshot_path}' に保存しました。"
            # )
        return pd.DataFrame()  # エラー時も空のDataFrameを返す

    finally:
        if driver:
            driver.quit()
            # print("ブラウザを終了しました。")


# =============================================================================

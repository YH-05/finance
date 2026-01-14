import marimo

__generated_with = "0.19.2"
app = marimo.App()


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # etf-dot-com.ipynb

    ETF.com からティッカーと基本情報、ファンドフローをスクレイピングするコードを実験するノートブック。

    -   Ticker 取得: OK
    -   ETF Fundamentals 取得: 一部で loading...や--となっているデータを取得してしまい、欠損扱いになってしまうので、改善必要、。
    -   Fund Flow 取得: ticker ひとつについて、取得ロジックを関数化完了。あとは並列処理できるようにする。
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    [ETF.com](https://www.etf.com/etfanalytics/etf-screener?utm_medium=nav)
    """)
    return


@app.cell
def _():
    # magic command not supported in marimo; please file an issue to add support
    # %load_ext autoreload
    # '%autoreload 2' command supported automatically in marimo

    import pandas as pd
    import numpy as np
    import io
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from webdriver_manager.chrome import ChromeDriverManager
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, NoSuchElementException
    import datetime
    from dateutil import relativedelta
    import time
    from concurrent.futures import ProcessPoolExecutor, as_completed
    import sqlite3
    from pathlib import Path
    from etf_dot_com import get_etf_fundamentals, get_tickers_from_db, save_data_to_db
    from tqdm import tqdm

    ROOT_DIR = Path().cwd().parent
    ETF_DIR = ROOT_DIR / "data/ETF"
    return (
        By,
        ChromeDriverManager,
        EC,
        ETF_DIR,
        NoSuchElementException,
        ProcessPoolExecutor,
        Service,
        TimeoutException,
        WebDriverWait,
        as_completed,
        datetime,
        get_etf_fundamentals,
        get_tickers_from_db,
        pd,
        save_data_to_db,
        sqlite3,
        time,
        tqdm,
        webdriver,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Ticker & ETF Fundamentals download
    """)
    return


@app.cell
def _(
    ETF_DIR,
    ProcessPoolExecutor,
    as_completed,
    display,
    get_etf_fundamentals,
    get_tickers_from_db,
    pd,
    save_data_to_db,
    time,
    tqdm,
):
    # --- Ticker download ---
    db_path = ETF_DIR / 'ETFDotCom.db'
    # try:
    #     final_df = download_all_tickers(browser_display=False)
    #     if not final_df.empty:
    #         db_path = ETF_DIR / "ETFDotCom.db"
    #         conn = sqlite3.connect(db_path)
    #         final_df.to_sql("Ticker", conn, index=False, if_exists="append")
    #         conn.close()
    #         print(f"\nデータベース{db_path.name}への保存が完了しました。")
    #     else:
    #         print("\n取得データが空のため、データベースへの保存はスキップされました。")
    _ticker_list = get_tickers_from_db(db_path=db_path)
    # except Exception as e:
    #     print("\n処理中にエラーが発生しました。")
    _MAX_WORKERS = 5
    # --- ETF Fundamentals download ---
    print(f'\n--- 並列処理を開始します（MAX_WORKERS= {_MAX_WORKERS}） ---')
    _start_time = time.time()
    _all_data_list = []
    with ProcessPoolExecutor(max_workers=_MAX_WORKERS) as _executor:
        _futures = {_executor.submit(get_etf_fundamentals, _ticker): _ticker for _ticker in _ticker_list}
        for _future in tqdm(as_completed(_futures), total=len(_ticker_list), desc='スクレイピング進捗'):
            try:
                df = _future.result()
                if not df.empty:
                    _all_data_list.append(df)
            except Exception as e:
                _ticker = _futures[_future]
                print(f'!! ティッカー {_ticker} の処理で予期せぬエラー: {e}')
    if not _all_data_list:
        print('\n\n--- データを一件も取得できませんでした ---')  # tqdmを使って進捗を表示
    _final_df = pd.concat(_all_data_list, ignore_index=True)
    print('\n\n--- 全てのティッカーのデータ取得が完了しました ---')
    display(_final_df)
    save_data_to_db(_final_df, db_path, 'ETF Fundamentals')
    _end_time = time.time()
    print(f'\n--- 全処理完了 ---')
    # 3. 結果を結合し、表示
    # 4. 結合したデータをデータベースに保存
    print(f'実行時間: {_end_time - _start_time:.2f} 秒')
    return


@app.cell
def _(ETF_DIR, pd, sqlite3):
    db_path_1 = ETF_DIR / 'ETFDotCom.db'
    _conn = sqlite3.connect(db_path_1)
    df_1 = pd.read_sql("SELECT * FROM 'ETF Fundamentals'", con=_conn)
    return db_path_1, df_1


@app.cell
def _(
    ProcessPoolExecutor,
    as_completed,
    db_path_1,
    df_1,
    display,
    get_etf_fundamentals,
    pd,
    save_data_to_db,
    time,
    tqdm,
):
    _missing_ticker_list = df_1[df_1.eq('loading...').any(axis=1)]['Ticker'].tolist()
    _MAX_WORKERS = 5
    print(f'\n--- 並列処理を開始します（MAX_WORKERS= {_MAX_WORKERS}） ---')
    _start_time = time.time()
    _all_data_list = []
    with ProcessPoolExecutor(max_workers=_MAX_WORKERS) as _executor:
        _futures = {_executor.submit(get_etf_fundamentals, _ticker): _ticker for _ticker in _missing_ticker_list}
        for _future in tqdm(as_completed(_futures), total=len(_missing_ticker_list), desc='スクレイピング進捗'):
            try:
                df_2 = _future.result()
                if not df_2.empty:
                    _all_data_list.append(df_2)
            except Exception as e:
                _ticker = _futures[_future]
                print(f'!! ティッカー {_ticker} の処理で予期せぬエラー: {e}')
    if not _all_data_list:
        print('\n\n--- データを一件も取得できませんでした ---')
    final_df_missing = pd.concat(_all_data_list, ignore_index=True)
    print('\n\n--- 全てのティッカーのデータ取得が完了しました ---')
    display(final_df_missing)
    save_data_to_db(final_df_missing, db_path_1, 'ETF Fundamentals')
    _end_time = time.time()
    print(f'\n--- 全処理完了 ---')
    print(f'実行時間: {_end_time - _start_time:.2f} 秒')
    return (final_df_missing,)


@app.cell
def _(
    ProcessPoolExecutor,
    as_completed,
    db_path_1,
    display,
    final_df_missing,
    get_etf_fundamentals,
    pd,
    save_data_to_db,
    time,
    tqdm,
):
    display(final_df_missing[final_df_missing.eq('loading...').any(axis=1)])
    df_3 = final_df_missing[final_df_missing.eq('loading...').any(axis=1)]
    _missing_ticker_list = df_3[df_3.eq('loading...').any(axis=1)]['Ticker'].tolist()
    _MAX_WORKERS = 5
    print(f'\n--- 並列処理を開始します（MAX_WORKERS= {_MAX_WORKERS}） ---')
    _start_time = time.time()
    _all_data_list = []
    with ProcessPoolExecutor(max_workers=_MAX_WORKERS) as _executor:
        _futures = {_executor.submit(get_etf_fundamentals, _ticker): _ticker for _ticker in _missing_ticker_list}
        for _future in tqdm(as_completed(_futures), total=len(_missing_ticker_list), desc='スクレイピング進捗'):
            try:
                df_3 = _future.result()
                if not df_3.empty:
                    _all_data_list.append(df_3)
            except Exception as e:
                _ticker = _futures[_future]
                print(f'!! ティッカー {_ticker} の処理で予期せぬエラー: {e}')
    if not _all_data_list:
        print('\n\n--- データを一件も取得できませんでした ---')
    final_df_missing_1 = pd.concat(_all_data_list, ignore_index=True)
    print('\n\n--- 全てのティッカーのデータ取得が完了しました ---')
    display(final_df_missing_1)
    save_data_to_db(final_df_missing_1, db_path_1, 'ETF Fundamentals')
    _end_time = time.time()
    print(f'\n--- 全処理完了 ---')
    print(f'実行時間: {_end_time - _start_time:.2f} 秒')
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### コメント

    '--'がついている行がある？
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Experimental Codes
    """)
    return


@app.cell
def _(
    By,
    ChromeDriverManager,
    EC,
    Service,
    WebDriverWait,
    datetime,
    display,
    pd,
    webdriver,
):
    def _scrape_key_value_data(driver, wait, container_id: str) -> dict:
        """
        指定されたコンテナID内のキーと値のペアをスクレイピングして辞書として返す関数
        """
        data_dict = {}
        print(f"ID='{container_id}'のデータを待機しています...")
        _wait.until(lambda d: len(d.find_elements(By.CSS_SELECTOR, f'#{container_id} .inline-flex')) > 0)
        try:
            _wait.until(EC.invisibility_of_element_located((By.XPATH, f"//*[@id='{container_id}']//*[contains(text(), 'loading...')]")))
        except:
            pass
        print(f"ID='{container_id}'のデータを検出しました。")
        container_div = _driver.find_element(By.ID, container_id)
        data_rows = container_div.find_elements(By.CLASS_NAME, 'inline-flex')
        for row in data_rows:
            children = row.find_elements(By.TAG_NAME, 'div')
            if len(children) == 2:
                key = children[0].text
                value = children[1].text
                data_dict[key] = value
        return data_dict
    _ticker = 'VOO'
    _url = f'https://www.etf.com/{_ticker}'
    _service = Service(ChromeDriverManager().install())
    _driver = webdriver.Chrome(service=_service)
    _wait = WebDriverWait(_driver, 10)
    try:
        _driver.get(_url)
        _summary_data = _scrape_key_value_data(_driver, _wait, 'summary-data')
        _classification_data = _scrape_key_value_data(_driver, _wait, 'classification-index-data')
        _combined_data = {**_summary_data, **_classification_data}
        df_4 = pd.DataFrame([_combined_data])
        df_4 = df_4.assign(datetime_created=datetime.datetime.now(), Ticker=_ticker)
        print('\n--- データフレームの作成に成功しました ---')
        display(df_4)
    except Exception as e:
        print(f'処理中にエラーが発生しました: {e}')
    finally:
        _driver.quit()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### タブ切り替えテスト
    """)
    return


@app.cell
def _(
    By,
    ChromeDriverManager,
    EC,
    Service,
    TimeoutException,
    WebDriverWait,
    time,
    webdriver,
):
    # --- メインの処理 ---
    _ticker = 'VOO'
    _url = f'https://www.etf.com/{_ticker}'
    _service = Service(ChromeDriverManager().install())
    _driver = webdriver.Chrome(service=_service)
    _wait = WebDriverWait(_driver, 10)  # 待機時間を10秒に設定
    try:
        print(f'{_url} にアクセスします...')
        _driver.get(_url)  # サイトにアクセス
        try:
            _cookie_button_xpath = "//button[contains(text(), 'Accept All')]"
            print('クッキー同意ボタンを探しています...')
            _accept_button = _wait.until(EC.element_to_be_clickable((By.XPATH, _cookie_button_xpath)))  # --- 【ステップ1】 クッキー同意ボタンが表示されたらクリックする ---
            print('同意ボタンをクリックします。')  # ポップアップは常に表示されるとは限らないため、try...exceptで囲みます
            _accept_button.click()
            time.sleep(1)  # このXPathは一例です。実際のボタンのテキストや構造に合わせて変更してください。
        except TimeoutException:  # 一般的な「すべて同意する」ボタンを想定しています。
            print('クッキー同意ボタンは見つかりませんでした。処理を続行します。')
        print('「Fund Flows」タブをクリックします...')
        fund_flows_tab = _wait.until(EC.presence_of_element_located((By.ID, 'fp-menu-fund-flows')))
        _driver.execute_script('arguments[0].click();', fund_flows_tab)
        print('「Fund Flows」のコンテンツが表示されるのを待ちます...')
        _wait.until(EC.visibility_of_element_located((By.ID, 'fund-page-fund-flows')))
        print('コンテンツが表示されました。')
        time.sleep(2)
        print('「Overview」タブをクリックします...')
        _overview_tab = _wait.until(EC.presence_of_element_located((By.ID, 'fp-menu-overview')))
        _driver.execute_script('arguments[0].click();', _overview_tab)  # ポップアップが消えるのを少し待ちます
        print('「Overview」のコンテンツが表示されるのを待ちます...')
        _wait.until(EC.visibility_of_element_located((By.ID, 'fund-page-overview')))
        print('コンテンツが表示されました。')
        print('タブの切り替えが完了しました。')  # 10秒待ってもボタンが見つからなければ、表示されていないと判断して次に進みます
    except Exception as e:
        print(f'エラーが発生しました: {e}')
    finally:  # --- 【ステップ2】 目的のタブをJavaScriptでクリックする ---
        print('処理が終了しました。5秒後にブラウザを閉じます。')  # 1. "Fund Flows" タブをクリック
        time.sleep(5)
        _driver.quit()  # 要素がDOM上に読み込まれるのを待機  # JavaScript を使ってクリックを実行  # Fund Flowsタブのメインコンテンツが表示されるまで待機  # ---------  # Fund Flowsタブでの操作  # ---------  # 2. "Overview" タブをクリック  # 要素がDOM上に読み込まれるのを待機  # JavaScript を使ってクリックを実行  # Overviewタブのメインコンテンツが表示されるまで待機  # ---------  # Overviewタブでの操作  # ---------  # 処理が終わったらブラウザを閉じる（必要に応じてコメントを外してください）
    return


@app.cell
def _(
    By,
    ChromeDriverManager,
    EC,
    Service,
    TimeoutException,
    WebDriverWait,
    datetime,
    display,
    pd,
    time,
    webdriver,
):
    def _scrape_key_value_data(driver, wait, container_id: str) -> dict:
        """
        指定されたコンテナID内のキーと値のペアをスクレイピングして辞書として返す関数
        """
        data_dict = {}
        print(f"ID='{container_id}'のデータを待機しています...")
        _wait.until(lambda d: len(d.find_elements(By.CSS_SELECTOR, f'#{container_id} .inline-flex')) > 0)
        try:
            _wait.until(EC.invisibility_of_element_located((By.XPATH, f"//*[@id='{container_id}']//*[contains(text(), 'loading...')]")))
        except:
            pass
        print(f"ID='{container_id}'のデータを検出しました。")
        container_div = _driver.find_element(By.ID, container_id)
        data_rows = container_div.find_elements(By.CLASS_NAME, 'inline-flex')
        for row in data_rows:
            children = row.find_elements(By.TAG_NAME, 'div')
            if len(children) == 2:
                key = children[0].text
                value = children[1].text
                data_dict[key] = value
        return data_dict
    _ticker = 'VOO'
    _url = f'https://www.etf.com/{_ticker}'
    _service = Service(ChromeDriverManager().install())
    _driver = webdriver.Chrome(service=_service)
    _wait = WebDriverWait(_driver, 10)
    try:
        print(f'{_url} にアクセスします...')
        _driver.get(_url)
        try:
            _cookie_button_xpath = "//button[contains(text(), 'Accept All')]"
            print('クッキー同意ボタンを探しています...')
            _accept_button = _wait.until(EC.element_to_be_clickable((By.XPATH, _cookie_button_xpath)))
            print('同意ボタンをクリックします。')
            _accept_button.click()
            time.sleep(1)
        except TimeoutException:
            print('クッキー同意ボタンは見つかりませんでした。処理を続行します。')
        _overview_tab = _wait.until(EC.presence_of_element_located((By.ID, 'fp-menu-overview')))
        _driver.execute_script('arguments[0].click();', _overview_tab)
        _wait.until(EC.visibility_of_element_located((By.ID, 'fund-page-overview')))
        _summary_data = _scrape_key_value_data(_driver, _wait, 'summary-data')
        _classification_data = _scrape_key_value_data(_driver, _wait, 'classification-index-data')
        _combined_data = {**_summary_data, **_classification_data}
        df_5 = pd.DataFrame([_combined_data])
        df_5 = df_5.assign(datetime_created=datetime.datetime.now(), Ticker=_ticker)
        print('\n--- データフレームの作成に成功しました ---')
        display(df_5)
    except Exception as e:
        print(f'処理中にエラーが発生しました: {e}')
    finally:
        print('処理が終了しました。5秒後にブラウザを閉じます。')
        time.sleep(5)
        _driver.quit()
    return


@app.cell
def _(
    By,
    ChromeDriverManager,
    EC,
    ETF_DIR,
    Service,
    TimeoutException,
    WebDriverWait,
    datetime,
    display,
    pd,
    sqlite3,
    time,
    webdriver,
):
    def _scrape_key_value_data(driver, wait, container_id: str) -> dict:
        """
        指定されたコンテナID内のキーと値のペアをスクレイピングして辞書として返す関数
        """
        data_dict = {}
        try:
            print(f"  ID='{container_id}'のデータを待機しています...")
            _wait.until(lambda d: len(d.find_elements(By.CSS_SELECTOR, f'#{container_id} .inline-flex')) > 0)
            _wait.until(EC.invisibility_of_element_located((By.XPATH, f"//*[@id='{container_id}']//*[contains(text(), 'loading...')]")))
            print(f"  ID='{container_id}'のデータを検出しました。")
            container_div = _driver.find_element(By.ID, container_id)
            data_rows = container_div.find_elements(By.CLASS_NAME, 'inline-flex')
            for row in data_rows:
                children = row.find_elements(By.TAG_NAME, 'div')
                if len(children) == 2:
                    key = children[0].text
                    value = children[1].text
                    if key and value:
                        data_dict[key] = value
        except TimeoutException:
            print(f"  警告: ID='{container_id}'のデータが見つからなかったか、タイムアウトしました。")
        except Exception as e:
            print(f"  エラー: ID='{container_id}'のデータ取得中にエラーが発生しました: {e}")
        return data_dict

    def scrape_all_tickers(tickers: list) -> pd.DataFrame:
        """
        tickerのリストを受け取り、ループ処理でデータをスクレイピングして
        1つのDataFrameに結合して返すメイン関数。
        """
        _service = Service(ChromeDriverManager().install())
        _driver = webdriver.Chrome(service=_service)
        _wait = WebDriverWait(_driver, 10)
        all_tickers_data = []
        try:
            initial_url = f'https://www.etf.com/{tickers[0]}'
            print(f'最初のURLにアクセスしてクッキー処理を行います: {initial_url}')
            _driver.get(initial_url)
            cookie_wait = WebDriverWait(_driver, 3)
            try:
                _accept_button = cookie_wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Accept All')]")))
                print('クッキー同意ボタンをクリックします。')
                _accept_button.click()
                time.sleep(1)
            except TimeoutException:
                print('クッキー同意ボタンは見つかりませんでした。')
            for _ticker in tickers:
                print(f"\n--- ticker '{_ticker}' の処理を開始します ---")
                try:
                    _url = f'https://www.etf.com/{_ticker}'
                    print(f'{_url} にアクセスします...')
                    _driver.get(_url)
                    print('  「Overview」のコンテンツが表示されるのを待ちます...')
                    _wait.until(EC.visibility_of_element_located((By.ID, 'fund-page-overview')))
                    print('  コンテンツが表示されました。')
                    _summary_data = _scrape_key_value_data(_driver, _wait, 'summary-data')
                    _classification_data = _scrape_key_value_data(_driver, _wait, 'classification-index-data')
                    if not _summary_data and (not _classification_data):
                        print(f"'{_ticker}' のデータが取得できなかったため、スキップします。")
                        continue
                    _combined_data = {**_summary_data, **_classification_data}
                    _combined_data['Ticker'] = _ticker
                    _combined_data['datetime_created'] = datetime.datetime.now()
                    all_tickers_data.append(_combined_data)
                    print(f"--- ticker '{_ticker}' の処理が正常に完了しました ---")
                except Exception as e:
                    print(f"--- ticker '{_ticker}' の処理中にエラーが発生しました: {e} ---")
                    continue
        finally:
            print('\n全ての処理が終了しました。ブラウザを閉じます。')
            _driver.quit()
        if not all_tickers_data:
            return pd.DataFrame()
        return pd.DataFrame(all_tickers_data)
    db_path_2 = ETF_DIR / 'ETFDotCom.db'
    _conn = sqlite3.connect(db_path_2)
    _ticker_list = pd.read_sql('SELECT * FROM Ticker', con=_conn)['Ticker'].unique().tolist()
    _conn.close()
    display(_ticker_list[:10])
    _final_df = scrape_all_tickers(_ticker_list)
    if not _final_df.empty:
        print('\n--- 最終的な統合データフレーム ---')
        display(_final_df)
    else:
        print('\n有効なデータを取得できませんでした。')
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Fund flow download
    """)
    return


@app.cell
def _(
    By,
    ChromeDriverManager,
    EC,
    NoSuchElementException,
    Service,
    TimeoutException,
    WebDriverWait,
    datetime,
    display,
    pd,
    time,
    webdriver,
):
    def get_fund_flows_data(ticker: str) -> pd.DataFrame:
        """
        指定されたティッカーのFund Flowsデータを専用URLから取得し、DataFrameとして返す関数。
        """
        start_date = '1990-01-01'
        end_date = datetime.date.today().strftime('%Y-%m-%d')
        _url = f'https://www.etf.com/etfanalytics/etf-fund-flows-tool-result?tickers={_ticker},&startDate={start_date}&endDate={end_date}&frequency=DAILY'
        _service = Service(ChromeDriverManager().install())
        _driver = webdriver.Chrome(service=_service)
        _wait = WebDriverWait(_driver, 10)
        all_rows_data = []
        try:
            print(f'{_url} にアクセスします...')
            _driver.get(_url)
            cookie_wait = WebDriverWait(_driver, 3)
            try:
                cookie_button = cookie_wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Accept All')]")))
                print('クッキー同意ボタンをクリックします。')
                cookie_button.click()
                time.sleep(1)
            except TimeoutException:
                print('クッキー同意ボタンは見つかりませんでした。')
            print('データテーブルが表示されるのを待ちます...')
            _wait.until(EC.visibility_of_element_located((By.ID, 'flow-detail')))
            print('表示件数を100件に設定します...')
            display_100_button = _wait.until(EC.presence_of_element_located((By.XPATH, "//button/span[text()='100']")))
            _driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", display_100_button)
            time.sleep(1)
            _driver.execute_script('arguments[0].click();', display_100_button)
            print('テーブルが100件表示に更新されるのを待ちます...')
            time.sleep(3)
            page_num = 1
            while True:
                print(f'{page_num}ページ目のデータを取得中...')
                table = _wait.until(EC.visibility_of_element_located((By.ID, 'fund-flow-result-output-table')))
                rows = table.find_elements(By.XPATH, './/tbody/tr')
                if not rows:
                    print('テーブルに行が見つかりませんでした。')
                    break
                for row in rows:
                    cols = row.find_elements(By.TAG_NAME, 'td')
                    if len(cols) == 2:
                        date = cols[0].text
                        net_flows = cols[1].text
                        all_rows_data.append({'Date': date, f'{_ticker} Net Flows': net_flows})
                try:
                    next_button = _driver.find_element(By.XPATH, "//li[not(contains(@class, 'disabled'))]/a[text()='Next']")
                    _driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_button)
                    time.sleep(1)
                    _driver.execute_script('arguments[0].click();', next_button)
                    print('Nextボタンをクリックしました。')
                    page_num = page_num + 1
                    time.sleep(3)
                except NoSuchElementException:
                    print('最終ページに到達しました。')
                    break
        except Exception as e:
            print(f'処理中にエラーが発生しました: {e}')
        finally:
            _driver.quit()
        if not all_rows_data:
            print('データが取得できませんでした。')
            return pd.DataFrame()
        df = pd.DataFrame(all_rows_data)
        df['Date'] = pd.to_datetime(df['Date'])
        df[f'{_ticker} Net Flows'] = df[f'{_ticker} Net Flows'].str.replace(',', '').astype(float)
        df = df.rename(columns={'Date': 'date', f'{_ticker} Net Flows': 'ETF Net Flows'}).assign(Ticker=_ticker).sort_values('date', ignore_index=True)
        return df
    ticker_symbol = 'VOO'
    fund_flows_df = get_fund_flows_data(ticker_symbol)
    if not fund_flows_df.empty:
        print(f'\n--- {ticker_symbol} のファンドフローデータ取得に成功しました ---')
        print(f'取得したデータ件数: {len(fund_flows_df)}')
        display(fund_flows_df.head())
        display(fund_flows_df.tail())
    return


@app.cell
def _():
    import marimo as mo
    return (mo,)


if __name__ == "__main__":
    app.run()

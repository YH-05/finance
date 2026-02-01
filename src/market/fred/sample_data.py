"""
fetch_data.py
"""

import json
import logging
import os
import re
import sqlite3
from pathlib import Path

import pandas as pd
import requests
from fredapi import Fred
from pandas import DataFrame

from configuration.file_path import Config


def load_fred_series_id_json(github_url: str | None = None) -> dict:
    github_url = github_url if github_url else Config.from_env().fred_series_id_json
    data = requests.get(url=github_url, verify=False).json()
    return data


# ==================================================================================
class FredDataLoader:
    def __init__(self):
        self.config = Config.from_env()
        self.data_dir = self.config.fred_dir
        self.fred_series_json = self.config.fred_series_id_json
        self.db_path = self.data_dir / "FRED.db"
        self.FRED_API = self.config.fred_api_key

    # --------------------------------------------------------------------------------
    def get_fred_ids_from_file(self, github_url: str | None = None) -> list[str]:
        """
        JSONファイルからFREDのシリーズIDを抽出する。

        Parameters
        ----------
        github_url : str | None
            読み込むFRED series id JSONファイルのパス。Github URL。

        Returns
        -------
        list[str]
            FREDのシリーズIDのリスト。
        """
        if github_url is None:
            github_url = self.fred_series_json
        try:
            # ローカルのJSONファイルを読み込む場合
            # with open(str(github_url), encoding="utf-8") as f:
            #     data = json.load(f)

            # data = requests.get(github_url, verify=False).json()
            data = load_fred_series_id_json()
            series_ids = []
            # JSONのトップレベルのキー（"Prices", "Interest Rates"など）でループ
            for category in data.values():
                # 各カテゴリ内のキー（シリーズID）をリストに追加
                series_ids.extend(category.keys())

            return series_ids
        except FileNotFoundError:
            logging.error(f"エラー: ファイル '{github_url}' が見つかりません。")
            return []
        except json.JSONDecodeError:
            logging.error(
                f"エラー: ファイル '{github_url}' は有効なJSON形式ではありません。"
            )
            return []

    # --------------------------------------------------------------------------------
    def delete_table_from_db(self, db_path: Path, table_name: str):
        """
        指定されたSQLiteデータベースから特定のテーブルを削除する。

        Parameters
        ----------
        db_path : Path
            SQLiteデータベースファイルへのパス (pathlib.Path オブジェクト)。
        table_name : str
            削除するテーブル名。
        """

        # 1. テーブル名の簡易検証 (SQLインジェクション対策)
        # 英数字とアンダースコアのみを許可
        if not re.match(r"^[a-zA-Z0-9_]+$", table_name):
            logging.error(
                f"エラー: '{table_name}' は無効なテーブル名です。処理を中止しました。"
            )
            return

        # 2. SQLコマンドの準備
        # テーブル名のような識別子はパラメータ化(?)できないため、f-stringを使用
        # "IF EXISTS" を付けることで、テーブルが存在しなくてもエラーにならない
        # 識別子をダブルクォートで囲み、安全性を高める
        sql_command = f'DROP TABLE IF EXISTS "{table_name}"'

        try:
            # 3. 'with' ステートメントでデータベースに接続
            # ブロック終了時に自動的にコミット(正常時)またはロールバック(異常時)され、
            # 接続がクローズされます。
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()

                # 4. SQLの実行
                cursor.execute(sql_command)

            logging.info(
                f"テーブル '{table_name}' をデータベース ({db_path.name}) から正常に削除しました。"
            )

        except sqlite3.Error as e:
            logging.error(f"データベースエラーが発生しました: {e}")
        except Exception as e:
            logging.error(f"予期せぬエラーが発生しました: {e}")

    # --------------------------------------------------------------------------------
    def store_fred_database(
        self, db_path=None, series_id_list=None, FRED_API=None
    ) -> None:
        """
        FREDの経済指標データをSQLite3データベースに差分更新で保存する。

        データベースやテーブルが存在しない場合は新規作成する。
        既にデータが存在する場合は、最新の日付以降のデータのみを取得して追記する。

        Parameters
        ----------
        db_path : Path, optional
            保存先のSQLiteデータベースファイルへのパス。
        series_id_list : List[str], optional
            取得したいFREDのシリーズIDのリスト。
        FRED_API : str, optional
            FRED APIキー。

        Returns
        -------
        None
        """

        if db_path is None:
            db_path = self.db_path
        if series_id_list is None:
            series_id_list = self.get_fred_ids_from_file()

        logging.info(
            f"--- FREDデータの差分更新を開始 (データベース: '{db_path.name}') ---"
        )
        conn = None

        try:
            # データベースに接続（ファイルがなければ新規作成）
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # 書き込み高速化のための設定
            conn.execute("PRAGMA page_size = 65536;")
            conn.execute("PRAGMA journal_mode = WAL;")
            conn.execute("PRAGMA synchronous = OFF;")

            # FRED APIクライアントの初期化
            if FRED_API is None:
                FRED_API = os.getenv("FRED_API_KEY")
            fred = Fred(api_key=FRED_API)

            # 既存のテーブル一覧を先に取得しておくと効率的
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            existing_tables = {row[0] for row in cursor.fetchall()}

            for series_id in series_id_list:
                start_date = None
                write_mode = "replace"

                # テーブルが既に存在する場合、最終日を取得して差分更新の準備
                if series_id in existing_tables:
                    # f-stringでテーブル名を指定する際は、SQLインジェクション対策として
                    # テーブル名が信頼できるソース（この場合はseries_id_list）由来であることを確認してください。
                    cursor.execute(f'SELECT MAX(date) FROM "{series_id}"')
                    latest_date_str = cursor.fetchone()[0]

                    if latest_date_str:
                        # 最終日の翌日を開始日として設定
                        latest_date = pd.to_datetime(latest_date_str)
                        start_date = (latest_date + pd.Timedelta(days=1)).strftime(
                            "%Y-%m-%d"
                        )
                        write_mode = "append"
                        logging.info(
                            f"テーブル '{series_id}' の最終日: {latest_date_str}。これ以降のデータを取得します。"
                        )
                    else:
                        # テーブルは存在するが空の場合
                        logging.info(
                            f"テーブル '{series_id}' は空です。全期間のデータを取得します。"
                        )
                else:
                    logging.info(
                        f"テーブル '{series_id}' は存在しません。新規に作成します。"
                    )

                # FREDからデータを取得 (start_dateがNoneなら全期間取得)
                logging.info(
                    f"\tFREDシリーズ '{series_id}' を取得中 (開始日: {start_date or '全期間'})..."
                )
                series = fred.get_series(series_id, observation_start=start_date)

                # 新規データが存在する場合のみ処理を実行
                if not series.empty:
                    df = pd.DataFrame(
                        series, columns=["value"]  # type: ignore[arg-type]
                    ).reset_index()
                    df.columns = ["date", series_id]
                    df["date"] = pd.to_datetime(df["date"])

                    # データベースにテーブルとして保存（新規作成 or 追記）
                    df.to_sql(series_id, conn, if_exists=write_mode, index=False)

                    if write_mode == "append":
                        logging.info(
                            f"\tシリーズ '{series_id}' に {len(df)} 件の新規データを追加しました。"
                        )
                    else:
                        logging.info(
                            f"\tシリーズ '{series_id}' をテーブルとして新規保存しました ({len(df)} 件)。"
                        )
                else:
                    logging.info(
                        f"\tシリーズ '{series_id}' に更新データはありませんでした。"
                    )

            logging.info(
                f"--- 全てのFREDデータの差分更新が完了しました (データベース: '{db_path.name}') ---"
            )

        except sqlite3.Error as e:
            logging.error(f"データベースエラー: {e}")
        except Exception as e:
            logging.error(f"エラーが発生しました: {e}")
        finally:
            if conn:
                # WALモードでは、コネクションを閉じる前にコミットが推奨される
                conn.commit()
                conn.close()

    # --------------------------------------------------------------------------------
    def load_data_from_database(self, db_path=None, series_id_list=None) -> DataFrame:
        """SQLiteデータベースから複数の時系列データを読み込む関数である。

        指定されたSQLiteデータベースに接続し、series_id_listに含まれるIDと
        対応するテーブルからデータを読み込む。読み込まれたデータは、
        「date」「value」「variable」の列を持つ単一の縦長形式の
        pandas DataFrameに結合されて返される。

        Parameters
        ----------
        db_path : Path
            読み込み対象のSQLiteデータベースファイルへのパス。
        series_id_list : list of str
            データベースから読み込むシリーズIDのリスト。
            各IDはデータベース内のテーブル名と一致する必要がある。

        Returns
        -------
        pd.DataFrame
            全てのシリーズのデータを結合した縦長形式のDataFrame。
            以下の列を含む:
            - 'date' : 観測日 (datetime型)
            - 'value' : 経済指標の数値
            - 'variable' : データの元となったシリーズID
        """

        if db_path is None:
            db_path = self.db_path
        if series_id_list is None:
            series_id_list = self.get_fred_ids_from_file()

        dfs = []
        conn = sqlite3.connect(db_path)
        for series_id in series_id_list:
            df = (
                pd.read_sql(
                    f"SELECT * FROM '{series_id}' ORDER BY date",
                    con=conn,
                    parse_dates=["date"],
                )
                .rename(columns={series_id: "value"})
                .assign(variable=series_id)
            )

            dfs.append(df)
        df = pd.concat(dfs, ignore_index=True).drop_duplicates(ignore_index=True)

        return df

import os
from pathlib import Path
import re
import sqlite3

from dotenv import load_dotenv
import numpy as np
import pandas as pd
import yaml

from src.configuration import Config


class BloombergTickers:
    """
    既定のBloomberg Tickersをダウンロードするクラス
    """

    def __init__(self):
        self.config = Config.from_env()
        self.bloomberg_root_dir = self.config.bloomberg_root_dir
        self.bloomberg_ticker_yaml = self.bloomberg_root_dir / "ticker-description.yaml"

    def get_all_tickers_description(self):
        with open(self.bloomberg_ticker_yaml, encoding="utf-8") as f:
            ticker_descriptions = yaml.safe_load(f)

        return ticker_descriptions

    def get_msci_kokusai_tickers(self) -> list[str]:
        EQUITY_TYPES = {"equity_index", "equity_sector_index", "equity_industry_index"}
        tickers_kokusai = [
            ticker["bloomberg_ticker"]
            for ticker in self.get_all_tickers_description()
            if (ticker.get("type") in EQUITY_TYPES)
            & (ticker.get("bloomberg_ticker").startswith("MXKO"))
        ]

        return tickers_kokusai


class BloombergDataProcessor:
    def __init__(self):
        """
        BloombergDataProcessorクラスを初期化する。
        環境変数からディレクトリパスを読み込み、必要なファイルやデータベースの存在を確認する。
        """
        load_dotenv()
        self.config = Config.from_env()
        self.data_dir = self.config.bloomberg_root_dir
        self.sp_price_excel = self.data_dir / "SP500-Indices.xlsx"
        # sp_price_excelが見つからない場合
        if not self.sp_price_excel.exists():
            print(f"ファイル '{self.sp_price_excel}' が見つかりません。")
        self.sp_price_db = self.data_dir / "SP_Indices_Price.db"
        if not self.sp_price_db.exists():
            print(f"データベースファイル '{self.sp_price_db}' が見つかりません。")
            print("新しくデータベースを作成します。")
            self.store_sp_indices_price_to_database()
        self.sp_members_excel = self.data_dir / "SP500-Constituents.xlsx"
        if not self.sp_members_excel.exists():
            print(f"ファイル '{self.sp_members_excel}' が見つかりません。")
        else:
            self._store_sp500_members()

    # -------------------------------------------------------------------------------------
    def store_sp_indices_price_to_database(self, excel_path=None, db_path=None) -> None:
        """
        BQLでダウンロードしたS&P500のセクターインデックスとインダストリーインデックスの
        priceデータをsqlite3データベースに保存する関数
        """

        TABLE_NAME = "sp_indices_price"
        if excel_path is None:
            excel_path = self.sp_price_excel
        if db_path is None:
            db_path = self.sp_price_db

        try:
            # 1. Excelファイルの読み込みと前処理
            # BQLの出力形式を想定し、1行目をヘッダー、最初の列を日付として読み込む
            print(f"Reading data from '{excel_path.name}'...")
            df = pd.melt(
                pd.read_excel(excel_path, sheet_name="Price")
                .rename(columns={"Unnamed: 0": "Date"})
                .sort_values("Date"),
                id_vars=["Date"],
                var_name="Ticker",
                value_name="value",
            ).assign(variable="Price")
            df["Date"] = pd.to_datetime(df["Date"])
            df["value"] = df["value"].astype(float)

            print(f"Successfully loaded and reshaped {len(df)} rows from Excel.")

            # 2. データベース接続
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # 3. 差分更新ロジック
            # テーブルが存在するか確認
            cursor.execute(
                f"SELECT name FROM sqlite_master WHERE type='table' AND name='{TABLE_NAME}'"
            )
            table_exists = cursor.fetchone()

            df_to_add = pd.DataFrame()

            if table_exists:
                # テーブルが存在する場合、最新の日付を取得
                latest_date_str = pd.read_sql(
                    f"SELECT MAX(Date) FROM {TABLE_NAME}", conn
                ).iloc[0, 0]

                if latest_date_str:
                    latest_date = pd.to_datetime(latest_date_str)
                    # Excelデータから最新日より後のデータを抽出
                    df_to_add = df[df["Date"] > latest_date].copy()
                    print(
                        f"Database latest date: {latest_date.date()}. Found {len(df_to_add)} new rows to add."
                    )
                else:
                    # テーブルは存在するが空の場合
                    df_to_add = df.copy()
            else:
                # テーブルが存在しない場合、全てのデータを追加対象とする
                df_to_add = df.copy()
                print(
                    f"Table '{TABLE_NAME}' not found. Creating a new table with {len(df_to_add)} rows."
                )

            # 4. 差分データをデータベースに書き込み
            if not df_to_add.empty:
                df_to_add.to_sql(TABLE_NAME, conn, if_exists="append", index=False)
                print(
                    f"Successfully wrote {len(df_to_add)} rows to '{TABLE_NAME}' in '{db_path.name}'."
                )

        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            if "conn" in locals() and conn:
                conn.close()

    # -------------------------------------------------------------------------------------
    def load_sp_indices_price_from_database(
        self, db_path: Path | None = None, tickers: list[str] | None = None
    ) -> pd.DataFrame:
        """
        SQLiteデータベースからS&Pインデックスの価格データを読み込み、DataFrameとして返す。

        Args:
            db_path (Path, optional): データベースファイルのパス。指定しない場合はインスタンスのデフォルトパスを使用。
            tickers (List[str], optional): 読み込むティッカーのリスト。指定しない場合は全ティッカーを読み込む。

        Returns:
            pd.DataFrame: 読み込んだ価格データ。データが存在しない場合は空のDataFrameを返す。
        """
        TABLE_NAME = "sp_indices_price"
        if db_path is None:
            db_path = self.sp_price_db

        if not db_path.exists():
            print(f"データベースファイル '{db_path}' が見つかりません。")
            return pd.DataFrame()

        conn = None
        try:
            conn = sqlite3.connect(db_path)

            query = f"SELECT * FROM {TABLE_NAME}"
            params: list[str] | None = None

            if tickers:
                placeholders = ", ".join("?" for _ in tickers)
                query += f" WHERE Ticker IN ({placeholders})"
                params = tickers

            df = pd.read_sql_query(query, conn, params=params)
            df["Date"] = pd.to_datetime(df["Date"])
            print(f"Successfully loaded {len(df)} rows from '{db_path.name}'.")
            return df

        except Exception as e:
            print(f"An error occurred while reading from the database: {e}")
            return pd.DataFrame()
        finally:
            if conn:
                conn.close()

    # -------------------------------------------------------------------------------------
    def get_current_sp_members(self) -> list[str]:
        """
        BloombergでダウンロードしたSP500構成銘柄のティッカーをlistで返す関数
        """

        tickers = []
        df = pd.read_excel(self.sp_members_excel, sheet_name="current members")
        tickers = df["ID"].unique().tolist()
        return tickers

    # -------------------------------------------------------------------------------------
    def _store_sp500_members(self):
        """
        ExcelファイルからS&P 500構成銘柄データを読み込み、SQLiteデータベースに保存する内部メソッド。
        """
        TABLE_NAME = "Members"

        df = (
            pd.melt(
                pd.read_excel(self.sp_members_excel, sheet_name="current members")[
                    [
                        "ID",
                        "DATES",
                        "market_cap",
                        "gics_sector_name",
                        "gics_industry_group_name",
                        "gics_industry_name",
                        "gics_sub_industry_name",
                    ]
                ],
                id_vars=["ID"],
                var_name="variable",
                value_name="values",
            )
            .dropna(subset=["values"], ignore_index=True)
            .rename(columns={"ID": "Ticker"})
            .assign(
                Ticker=lambda x: x["Ticker"]
                .str.replace("/", "-")
                .str.split(" ", expand=True)[0],
            )
        ).sort_values("Ticker", ignore_index=True)
        df = (
            pd.pivot(df, index="Ticker", columns="variable", values="values")
            .reset_index()
            .rename(columns={"DATES": "date"})
            .assign(date=lambda x: pd.to_datetime(x["date"]))
        ).reindex(
            columns=[
                "date",
                "Ticker",
                "gics_sector_name",
                "gics_industry_group_name",
                "gics_industry_name",
                "gics_sub_industry_name",
                "market_cap",
            ]
        )

        try:
            # 2. データベース接続
            conn = sqlite3.connect(self.sp_price_db)
            cursor = conn.cursor()

            # 3. 差分更新ロジック
            # テーブルが存在するか確認
            cursor.execute(
                f"SELECT name FROM sqlite_master WHERE type='table' AND name='{TABLE_NAME}'"
            )
            table_exists = cursor.fetchone()

            df_to_add = pd.DataFrame()

            if table_exists:
                # テーブルが存在する場合、最新の日付を取得
                latest_date_str = pd.read_sql(
                    f"SELECT MAX(Date) FROM {TABLE_NAME}", conn
                ).iloc[0, 0]

                if latest_date_str:
                    latest_date = pd.to_datetime(latest_date_str)
                    # Excelデータから最新日より後のデータを抽出
                    df_to_add = df[df["Date"] > latest_date].copy()
                    print(
                        f"Database latest date: {latest_date.date()}. Found {len(df_to_add)} new rows to add."
                    )
                else:
                    # テーブルは存在するが空の場合
                    df_to_add = df.copy()
            else:
                # テーブルが存在しない場合、全てのデータを追加対象とする
                df_to_add = df.copy()
                print(
                    f"Table '{TABLE_NAME}' not found. Creating a new table with {len(df_to_add)} rows."
                )

            # 4. 差分データをデータベースに書き込み
            if not df_to_add.empty:
                df_to_add.to_sql(TABLE_NAME, conn, if_exists="append", index=False)
                print(
                    f"Successfully wrote {len(df_to_add)} rows to '{TABLE_NAME}' in '{self.sp_price_db.name}'."
                )

        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            if "conn" in locals() and conn:
                conn.close()

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
            print(
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

            print(
                f"テーブル '{table_name}' をデータベース ({db_path.name}) から正常に削除しました。"
            )

        except sqlite3.Error as e:
            print(f"データベースエラーが発生しました: {e}")
        except Exception as e:
            print(f"予期せぬエラーが発生しました: {e}")

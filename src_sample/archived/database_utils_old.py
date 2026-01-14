"""
database_utils.py
"""

# TODO: 各関数のdocstring整備

import ctypes
import os
from dataclasses import dataclass
from logging import getLogger
from pathlib import Path

import oracledb
import pandas as pd

# os.environ["DPI_DEBUG_LEVEL"] = "64"


# ======================================================================================
logger = getLogger(__name__)


# directory
# def find_bpm_root():
#     current_dir = Path().cwd()
#     if current_dir.name == "BPM":
#         return current_dir
#     else:
#         for ancestor in current_dir.parents:
#             if ancestor.name == "BPM":
#                 return ancestor
#         return None


# ROOT_DIR = find_bpm_root()
# CONFIG_DIR = ROOT_DIR / "config"


# ======================================================================================
@dataclass
class OracleConfigs:
    """
    統合DBへの接続設定を格納するデータクラス

    Attributes:
        HOST: str   DBサーバーのホスト名 or IPアドレス
        HOST_TEST: str   DBサーバーのホスト名 or IPアドレス(テスト環境用)
        PORT: int   DBサーバーのポート番号
        SN: str   DBサーバーのサービス名
        SN_TEST: str   DBサーバーのサービス名(テスト環境用)
        USER: str   DBに接続するユーザー名(read only)
        PASS: str   DBに接続するPASS(read only)
        PERMISSION_USER: str   DBに接続するユーザー名(with a full permission)
        PERMISSION_PASS: str   DBに接続するPASS(with a full permission)
    """

    HOST: str
    HOST_TEST: str
    PORT: int
    SN: str
    SN_TEST: str
    USER: str
    PASS: str
    PERMISSION_USER: str
    PERMISSION_PASS: str


# ======================================================================================
class DBHandler:
    # -----------------------------------------------------------------------------------------
    def __init__(self, user_flg: str, db_environment: str):
        """
        Oracle Databaseへの接続、データの挿入、削除、取得を行うためのクラスです。

        このクラスは、Oracle Databaseの特定のテーブルに対して、
        作成、更新、削除(CRUD操作のR以外)を行う際に特別な権限が必要となる場合に使用します。
        そのため、`PERMISSION_USER` と `PERMISSION_PASS` を使用してデータベースに接続します。

        主な機能:

        - データベースへの接続
        - DataFrameのデータの挿入
        - 条件に合致するレコードの削除
        - SQL文の実行と結果のDataFrameへの変換

        使用方法:

        1. oracle_configsオブジェクトをインスタンス化します。
        2. DBHandlerクラスをインスタンス化し、oracle_configsオブジェクトを引数に渡します。
        3. insert_pandas_into_tableメソッド、delete_dataメソッド、sql_to_pandasメソッドを使用して、
            データベース操作を実行します。

        例:

        ```python
        # oracle_configs オブジェクトをインスタンス化

        handler = DBHandler(oracle_configs)

        # DataFrameのデータをテーブルに挿入
        handler.insert_pandas_into_table(df, "table_name")

        # 条件に合致するレコードを削除
        handler.delete_data("table_name", "where column1 = 'value1'")

        # SQL文を実行し、結果をDataFrameに変換
        result_df = handler.sql_to_pandas("SELECT * FROM table_name")
        ```

        Args:
            oracle_configs (OracleConfigs): Oracle Database への接続情報を含むオブジェクト
                        (HOST, PORT, SN, PERMISSION_USR, PERMISSION_PASS 属性を持つ)
            user_flg (str): "default" | "unyoukanri"
                        userの名前とパスワードを変更する。unyoukanriの場合はUSER=TMA_UKUSER
            db_environment (str): "default" | "test"
                        統合DBの環境を設定する。defaultは本番環境、testはテスト環境
        """

        # python-oracledb Thick Mode 有効化
        oracledb.init_oracle_client()
        self.user_flg = user_flg
        self.db_environment = db_environment
        self.OracleConfigs: OracleConfigs
        self.get_oracle_configs()

    # -----------------------------------------------------------------------------------------
    # def _add_to_path(self, new_path=r"D:\instantclient_12_2"):
    #     """Windowsの環境変数Pathにパスを追加する."""
    #     try:
    #         with winreg.OpenKey(
    #             winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_ALL_ACCESS
    #         ) as key:
    #             value, regtype = winreg.QueryValueEx(key, "Path")
    #             if new_path not in value:
    #                 new_value = value + os.pathsep + new_path
    #                 winreg.SetValueEx(key, "Path", 0, regtype, new_value)
    #                 logger.info(f"パス '{new_path}' を追加しました。")
    #             else:
    #                 logger.info(f"パス '{new_path}' は既に存在します。")
    #     except Exception as e:
    #         logger.error(f"エラーが発生しました: {e}")

    # -----------------------------------------------------------------------------------------
    def get_loaded_oci_path(self):
        """oracledb.init_oracle_client()でロードされたOCIライブラリの絶対パスを返します。

        Returns:
            str: ロードされたOCIライブラリの絶対パス、またはエラーメッセージ。
        """
        try:
            ret = (
                oracledb.init_oracle_client()
            )  # oracledbを初期化することで、ociライブラリをロードします。
            logger.info(f"oracledb.init_oracle_client: {ret}")
            # Windowsの場合
            if os.name == "nt":
                # OCI.DLLのハンドルを取得
                handle = ctypes.windll.kernel32.GetModuleHandleW("oci.dll")
                if not handle:
                    logger.info("oci.dll がロードされていません")
                buf_size = 260
                buf = ctypes.create_unicode_buffer(buf_size)
                ctypes.windll.kernel32.GetModuleFileNameW(handle, buf, buf_size)
                logger.info(f"buf.value = {buf.value}")

        except Exception as e:
            logger.info(f"エラーが発生しました: {e}")

    # -----------------------------------------------------------------------------------------
    # OracleDB 接続情報
    def get_oracle_configs(self):
        # df_configs = pd.read_excel(
        #     CONFIG_DIR / "OracleDB_config.xlsx", sheet_name="config"
        # )
        df_configs = pd.read_excel(
            Path(r"H:\HataY\00_General\04_OracleDB\OracleDB_config.xlsx"),
            sheet_name="config",
        )

        # 必要な列の存在を確認
        required_columns = [
            "HOST",
            "HOST_TEST",
            "PORT",
            "SN",
            "SN_TEST",
            "USER",
            "PASS",
            "PERMISSION_USER",
            "PERMISSION_PASS",
        ]
        for col in required_columns:
            if col not in df_configs["key"].values:
                raise ValueError(f"必要な列 {col} が見つかりません。")

        # df_configs から OracleConfigs を作成
        self.OracleConfigs = OracleConfigs(
            **df_configs.set_index("key")["value"].to_dict()
        )

        # PORT を整数に変換
        self.OracleConfigs.PORT = int(self.OracleConfigs.PORT)
        # logger.debug(self.OracleConfigs)

        del df_configs

    # -----------------------------------------------------------------------------------------
    def _connect(self):
        """
        Oracle Database への接続を確立する

        Returns:
            oracledb.Connection: データベース接続オブジェクト
        """
        if self.user_flg == "default":
            user = self.OracleConfigs.USER
            pw = self.OracleConfigs.PASS
        elif self.user_flg == "unyoukanri":
            user = self.OracleConfigs.PERMISSION_USER
            pw = self.OracleConfigs.PERMISSION_PASS
        else:
            raise Exception

        if self.db_environment == "default":  # 本番環境
            host = self.OracleConfigs.HOST
            service_name = self.OracleConfigs.SN
        elif self.db_environment == "test":  # テスト環境
            host = self.OracleConfigs.HOST_TEST
            service_name = self.OracleConfigs.SN_TEST
        else:
            raise Exception

        dsn = oracledb.makedsn(host, self.OracleConfigs.PORT, service_name=service_name)
        return oracledb.connect(user=user, password=pw, dsn=dsn)

    # -----------------------------------------------------------------------------------------
    def get_table_list(self):
        try:
            # データベースに接続
            with self._connect() as connection:
                with connection.cursor() as cursor:
                    # 登録済みのテーブル一覧を取得する SQL クエリを実行
                    cursor.execute("SELECT table_name FROM all_tables")
                    # # cursor.execute("SELECT MSysObjects.Name FROM MSysObjects")
                    # cursor.execute("SELECT Name FROM MSysObjects WHERE Type='1'")

                    # 結果を取得
                    tables = cursor.fetchall()
                    tables = [s[0] for s in tables]

                    # テーブル一覧を表示
                    # print("登録済みのテーブル一覧:")
                    # for table in tables:
                    #     print(table[0])
                    return tables

        except oracledb.Error as error:
            print(f"Oracle Database Error: {error}")
            return []

        except Exception as error:
            print(f"An error occurred: {error}")
            return []

    # -----------------------------------------------------------------------------------------
    def create_table(self, table_name: str, columns: list):
        """
        create_table
            新しいテーブルを作成するメソッド.

        Args:
            table_name (str): 作成するテーブルの名前
            columns (list): カラム定義のリスト.
                各要素は辞書で、カラム名、データ型、制約などを指定する.
                例: [{'name': 'id', 'type': 'NUMBER', 'constraint': 'PRIMARY KEY'},
                    {'name': 'name', 'type': 'VARCHAR2(255)'}]
        """
        if self.db_environment == "test":
            try:
                with self._connect() as connection:
                    with connection.cursor() as cursor:
                        # カラム定義文字列を作成
                        column_definitions = []
                        primary_key = None

                        for col in columns:
                            if "primary_key" in col:
                                primary_key = col["primary_key"]
                            else:
                                column_definitions.append(
                                    f"{col['name']} {col['type']} {col.get('constraint', '')}"
                                )

                        column_definitions_str = ", ".join(column_definitions)

                        # SQLクエリを作成
                        sql = f"CREATE TABLE {table_name} ({column_definitions_str}"
                        if primary_key:
                            sql += f", CONSTRAINT pk_{table_name} PRIMARY KEY ({', '.join(primary_key)})"
                        sql += ")"

                        # SQL実行
                        cursor.execute(sql)

                        # コミット
                        connection.commit()

                        logger.info(f"テーブル {table_name} が作成されました。")

            except oracledb.Error as error:
                logger.error(f"Oracle Database Error: {error}")
                # ロールバック
                connection.rollback()

            except Exception as error:
                logger.error(f"An error occurred: {error}")
                # ロールバック
                connection.rollback()
        else:
            logger.info(
                "DB Environment must be test version. Switch `db_environment` to `test`."
            )

    # -----------------------------------------------------------------------------------------
    def insert_pandas_by_row_into_table(self, df: pd.DataFrame, table_name: str):
        """
        insert_pandas_into_table
            DataFrame のデータを指定したテーブルに挿入するメソッド

        Args:
            df (pd.DataFrame): 挿入するデータを含む pandas DataFrame
            table_name (str): 挿入先のテーブル名

        """
        try:
            with self._connect() as connection:
                with connection.cursor() as cursor:
                    columns = ", ".join(df.columns)
                    placeholders = ", ".join(
                        [f":{i+1}" for i in range(len(df.columns))]
                    )
                    sql = (
                        f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
                    )
                    # logger.info(sql)

                    # 3. bind variable の値の表示
                    # logger.info("\nbind variable の値:")
                    for _, row in df.iterrows():
                        bind_values = tuple(row)
                        # logger.info(bind_values)  # bind variable の値を表示

                        # 4. 実行前にデータ型をチェック
                        # for i, value in enumerate(bind_values):
                        #     column_name = df.columns[i]
                        #     logger.info(table_name)
                        #     try:
                        #         expected_type = connection.gettype(
                        #             table_name
                        #         )  # テーブルの型を取得
                        #     except Exception as e:
                        #         logger.error(e)
                        #     actual_type = type(value)

                        #     logger.info(
                        #         f"Column: {column_name}, Expected: {expected_type}, Actual: {actual_type}, Value: {value}"
                        #     )
                        #     if pd.isna(value) and expected_type == oracledb.NUMBER:
                        #         logger.info(
                        #             f"Warning: Column {column_name} is NUMBER but inserting a NaN value. This may cause an error."
                        #         )

                        try:
                            cursor.execute(sql, bind_values)
                        except oracledb.Error as e:
                            logger.info(
                                f"Oracle Error details : {e.args}\nBind values: {bind_values}"
                            )
                            raise  # re-raise the exception to be caught later for _, row in df.iterrows():
                        # cursor.execute(sql, tuple(row))
                    connection.commit()
        except Exception as e:
            logger.error(e)

    # -----------------------------------------------------------------------------------------
    def test_insert_pandas_by_row_into_table(
        self, df: pd.DataFrame, schema: str, table_name: str
    ):
        try:
            with self._connect() as connection:
                with connection.cursor() as cursor:
                    columns = ", ".join(df.columns)
                    placeholders = ", ".join(
                        [f":{i+1}" for i in range(len(df.columns))]
                    )
                    sql = f"INSERT INTO {schema}.{table_name} ({columns}) VALUES ({placeholders})"

                    for index, row in df.iterrows():
                        bind_values = tuple(row)
                        try:
                            cursor.execute(sql, bind_values)
                            connection.commit()
                        except oracledb.Error as e:
                            if "ORA-00001" in str(e):  # 既存のデータと重複があった場合
                                pass
                            else:
                                logger.error(f"Error inserting row {index}: {e}")
                                logger.error(f"  SQL: {sql}")
                                logger.error(f"  Bind values: {bind_values}")
                                connection.rollback()
                                raise  # 例外を再発生させて処理を中断

        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")

    # -----------------------------------------------------------------------------------------
    def insert_pandas_into_table(
        self, df: pd.DataFrame, schema: str, table_name: str, unique_key_list: list[str]
    ):
        with self._connect() as connection:
            with connection.cursor() as cursor:
                try:
                    columns = ", ".join(df.columns)
                    placeholders_insert = ", ".join([f"s.{col}" for col in df.columns])
                    merge_conditions = " AND ".join(
                        [f"t.{key} = s.{key}" for key in unique_key_list]
                    )
                    placeholders_merge = ", ".join(
                        [
                            f"t.{col} = s.{col}"
                            for col in df.columns
                            if col not in unique_key_list
                        ]
                    )

                    sql_merge = f"""
                        MERGE INTO {schema}.{table_name} t
                        USING (SELECT {', '.join([f':{i+1} AS {col}' for i, col in enumerate(df.columns)])} FROM dual) s
                        ON ({merge_conditions})
                        WHEN NOT MATCHED THEN
                            INSERT ({columns}) VALUES ({placeholders_insert})
                        WHEN MATCHED THEN
                            UPDATE SET {placeholders_merge}
                    """
                    bind_values = [tuple(row) for _, row in df.iterrows()]
                    cursor.executemany(sql_merge, bind_values)
                    connection.commit()

                except oracledb.Error as e:
                    logger.error(f"Error inserting data: {e}\nSQL={sql_merge}")
                    connection.rollback()
                    raise
                except Exception as e:
                    logger.error(f"An unexpected error occurred: {e}")

    # -----------------------------------------------------------------------------------------
    def delete_data(self, table_name: str, where_clause: str):
        """
        指定したテーブルから条件に合致するレコードを削除するメソッド

        Args:
            table_name: 削除対象のテーブル名
            where_clause: 削除条件を指定する WHERE 句
        """
        with self._connect() as connection:
            with connection.cursor() as cursor:
                sql = f"DELETE FROM {table_name} WHERE {where_clause}"
                cursor.execute(sql)
                connection.commit()

    # -----------------------------------------------------------------------------------------
    def write_to_pandas(self, sql: str) -> pd.DataFrame:
        """
        SQL 文を実行し、結果を pandas DataFrame に変換するメソッド

        Args:
        sql: 実行する SQL 文

        Returns:
        pd.DataFrame: SQL 文の実行結果を含む pandas DataFrame
        """

        # ------------------------------------------
        def _get_columns(cursor):
            """
            列名を取得する関数
            """
            columns = []
            for col in cursor.description:
                columns.append(col.name)
            return columns

        # ------------------------------------------

        try:
            with self._connect() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(sql)

                    columns = _get_columns(cursor)
                    data = cursor.fetchall()
                    df = pd.DataFrame(data, columns=columns)
        except Exception as e:
            logger.error(f"{e}\n\tDB configs: {self.user_flg} | {self.db_environment}")
            df = pd.DataFrame()

        return df


# -----------------------------------------------------------------------------------------

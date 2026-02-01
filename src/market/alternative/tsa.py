import datetime
import re
import sqlite3
from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import pandas as pd
import requests
import seaborn as sns
from bs4 import BeautifulSoup


class TSAPassengerDataCollector:
    """
    ウェブスクレイピングを用いて、TSA Passengerデータを収集するクラス。
    """

    def __init__(self):
        self.url = "https://www.tsa.gov/travel/passenger-volumes"

    def scrape_tsa_passenger_data(
        self,
        year=None,
    ):
        """
        TSAの旅客数データをスクレイピングしてDataFrameを返す関数

        Parameters
        ----------
        year : int, optional
            取得したい特定の年（2019から）。指定しない場合は最新のデータを取得。

        Returns
        -------
        pd.DataFrame or None
            旅客数データを含むデータフレーム。取得に失敗した場合はNone。
        """

        url = self.url
        if year:
            url = f"{self.url}/{year}"

        try:
            # ウェブページを取得
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            response = requests.get(url, headers=headers)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, "html.parser")
            table = soup.find("table")

            if not table:
                print("テーブルが見つかりませんでした")
                return None

            # データを格納するリスト
            dates = []
            numbers = []

            # テーブルの行を処理
            rows = table.find("tbody").find_all("tr")  # pyright: ignore[reportOptionalMemberAccess]

            for row in rows:
                cells = row.find_all("td")
                if len(cells) >= 2:
                    # 日付を取得（テキストをクリーンアップ）
                    date_text = cells[0].get_text(strip=True)

                    # 数値を取得（カンマを除去して整数に変換）
                    number_text = cells[1].get_text(strip=True)
                    number_clean = re.sub(r"[,]", "", number_text)

                    try:
                        # 日付を標準形式に変換
                        date_obj = datetime.datetime.strptime(date_text, "%m/%d/%Y")

                        dates.append(date_obj)
                        numbers.append(int(number_clean))

                    except (ValueError, TypeError) as e:
                        print(f"データ変換エラー: {date_text}, {number_text} - {e}")
                        continue

            # DataFrameを作成
            df = (
                pd.DataFrame({"Date": dates, "Numbers": numbers})
                .assign(Date=lambda x: pd.to_datetime(x["Date"]))
                .sort_values("Date", ascending=False)
                .reset_index(drop=True)
            )

            return df

        except requests.exceptions.RequestException as e:
            print(f"ウェブページの取得に失敗しました: {e}")
            return None
        except Exception as e:
            print(f"予期しないエラーが発生しました: {e}")
            return None

    def display_data_info(self, df: pd.DataFrame):
        """
        データフレームの基本情報を表示する。

        Parameters
        ----------
        df : pd.DataFrame
            情報を表示するデータフレーム。
        """
        if df is not None:
            print("=== TSA旅客数データ ===")
            print(
                f"データ期間: {df['Date'].min().strftime('%Y/%m/%d')} - {df['Date'].max().strftime('%Y/%m/%d')}"
            )
            print(f"データ件数: {len(df)}件")
            print(
                f"最大旅客数: {df['Numbers'].max():,}人 ({df.loc[df['Numbers'].idxmax(), 'Date'].strftime('%Y/%m/%d')})"
            )

            print(
                f"最小旅客数: {df['Numbers'].min():,}人 ({df.loc[df['Numbers'].idxmin(), 'Date'].strftime('%Y/%m/%d')})"
            )
            print(f"平均旅客数: {df['Numbers'].mean():.0f}人")
            print("\n=== 最新10件のデータ ===")
            print(df.head(10).to_string(index=False))

    def save_to_csv(self, df: pd.DataFrame, filename: str = "tsa_passenger_data.csv"):
        """
        DataFrameをCSVファイルに保存する関数

        Parameters
        ----------
        df : pd.DataFrame
            保存するデータフレーム。
        filename : str, default "tsa_passenger_data.csv"
            保存するファイル名。
        """
        try:
            df.to_csv(filename, index=False)
            print(f"\nデータを '{filename}' に保存しました")
        except Exception as e:
            print(f"CSVファイルの保存に失敗しました: {e}")

    def store_to_tsa_database(
        self, df: pd.DataFrame, db_path: str | Path, table_name: str = "tsa_passenger"
    ):
        """
        DataFrameをSQLiteデータベースに保存する関数。
        既存のデータがある場合は、新しい日付のデータのみを追加する。

        Parameters
        ----------
        df : pd.DataFrame
            保存するデータフレーム。
        db_path : str | Path
            データベースファイルのパス。
        table_name : str, default "tsa_passenger"
            保存先のテーブル名。
        """
        conn = None
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # テーブルが存在するか確認
            cursor.execute(
                f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'"
            )
            if cursor.fetchone():
                # 既存の全日付をセットとして取得
                existing_dates = set(
                    pd.read_sql(f"SELECT Date FROM {table_name}", conn)["Date"]
                )
                # 新しいデータのうち、DBに存在しない日付の行のみを抽出
                df["Date_str"] = df["Date"].dt.strftime("%Y-%m-%d %H:%M:%S")
                df_to_add = df[~df["Date_str"].isin(existing_dates)].drop(
                    columns=["Date_str"]
                )
            else:
                # テーブルが存在しない場合は全データを追加対象とする
                df_to_add = df

            print(f"{'-' * 20} + TSA Passenger Data + {'-' * 20}")
            if not df_to_add.empty:
                print(
                    f"{len(df_to_add)}件の新規データをテーブル '{table_name}' に追加します。"
                )
                df_to_add.to_sql(table_name, conn, if_exists="append", index=False)
            else:
                print("追加する新規データはありませんでした。")

        except sqlite3.Error as e:
            print(f"データベースエラーが発生しました: {e}")
        finally:
            if conn:
                conn.close()

    def plot_passenger_trend(self, df_passenger: pd.DataFrame, fig_save_path=None):
        """
        旅客数の推移をプロットする関数
        """
        g_passenger = (
            df_passenger.resample("ME")
            .agg(Numbers=("Numbers", "sum"))
            .assign(Numbers_Change_YOY=lambda df: df["Numbers"].pct_change(12) * 100)
            .dropna()
        )

        # --- plot ---

        fig, ax = plt.subplots(figsize=(10, 5), tight_layout=True)
        ax.set_title(
            f"TSA checkpoint passenger numbers (as of {df_passenger.index.max().strftime('%Y-%m-%d')})"
        )
        ax.bar(
            g_passenger.index,
            g_passenger["Numbers"],
            width=25,
            align="center",
            label="Num. of Passengers",
            alpha=0.5,
            color="blue",
        )
        ax.set_xlabel("Year-Month")
        ax.set_ylabel("Number of Passengers(Millions)")
        ax.yaxis.set_major_formatter(
            mtick.FuncFormatter(lambda x, pos: f"{int(x / 1000000)}")
        )

        ax_sub = ax.twinx()
        sns.lineplot(
            data=g_passenger,
            x=g_passenger.index,
            y="Numbers_Change_YOY",
            ax=ax_sub,
            color="green",
            label="YOY (%)",
            marker="o",
            markersize=4,
        )

        # legend
        handler1, label1 = ax.get_legend_handles_labels()
        handler2, label2 = ax_sub.get_legend_handles_labels()
        ax.legend(handler1 + handler2, label1 + label2, loc="lower right")
        # 服軸に自動で作成された判例を削除
        if ax_sub.get_legend() is not None:
            ax_sub.get_legend().remove()  # ty:ignore[possibly-missing-attribute]

        ax_sub.set_ylim(-100, 100)
        ax_sub.set_ylabel("YOY (%)")
        ax_sub.grid(color="black", linewidth=0.2, linestyle="--")
        ax_sub.yaxis.set_major_formatter(mtick.PercentFormatter())

        # x-axis date format
        ax.xaxis.set_major_locator(mdates.MonthLocator(bymonth=[1, 7]))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
        fig.autofmt_xdate(rotation=90)

        # ax.set_xlim(left=pd.to_datetime("2019-10-31"))

        plt.show()
        if fig_save_path:
            plt.savefig(fig_save_path, dpi=300)
        else:
            return fig

"""
Bloomberg API (BLPAPI) を使用して、ヒストリカルデータ、財務データ、ニュースデータを取得するためのユーティリティクラスを提供します。
Tickerだけでなく、SEDOL, CUSIP, ISIN, FIGIなどの様々な識別子に対応しています。
"""

import datetime
import logging
import sqlite3
from pathlib import Path
from typing import Any

import blpapi
import numpy as np
import pandas as pd
import yaml
from src.configuration import Config

# ロギング設定
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


# ===========================================================================================
class BlpapiFetcher:
    # --------------------------------------------------------------------------
    def __init__(self):
        self.HOST = "localhost"
        self.PORT = 8194
        self.REF_DATA_SERVICE = "//blp/refdata"
        self.NEWS_SERVICE = "//blp/news"

    # --------------------------------------------------------------------------
    def _create_session(self, verbose: bool = True) -> blpapi.Session | None:
        """BLPAPIセッションを開始します。"""
        sessionOptions = blpapi.SessionOptions()
        sessionOptions.setServerHost(self.HOST)
        sessionOptions.setServerPort(self.PORT)

        if verbose:
            print("Bloombergセッションを開始しています...")

        session = blpapi.Session(sessionOptions)
        if not session.start():
            print(
                "セッションの開始に失敗しました。Bloomberg Terminalが実行されているか確認してください。"
            )
            return None

        if verbose:
            print("セッション開始成功。")
        return session

    # --------------------------------------------------------------------------
    def get_historical_data(
        self,
        securities: list[str],
        id_type: str,
        fields: list[str],
        start_date: str,
        end_date: str,
        periodicity: str = "DAILY",
        currency: str | None = None,
        verbose: bool = True,
    ) -> pd.DataFrame:
        """
        BLPAPIを使用してヒストリカルデータを取得し、Pandas DataFrameとして返す
        (get_historical_data_with_overridesのラッパー)

        :param securities: 取得する銘柄識別子リスト (Ticker, SEDOL, CUSIP, ISINなど)
        :param fields: 取得するデータフィールドリスト
        :param start_date: 開始日 (YYYYMMDD形式)
        :param end_date: 終了日 (YYYYMMDD形式)
        :param periodicity: 取得周期 ('DAILY', 'WEEKLY', 'MONTHLY', 'QUARTERLY', 'YEARLY')
        :param currency: データを変換する通貨コード (例: 'JPY', 'USD', 'EUR')
        :param verbose: ログ出力の有効/無効
        """
        # get_historical_data_with_overrides を呼び出し (id_type="ticker" をデフォルトとする)
        df_flat = self.get_historical_data_with_overrides(
            securities=securities,
            fields=fields,
            start_date=start_date,
            end_date=end_date,
            periodicity=periodicity,
            id_type=id_type,
            currency=currency,
            verbose=verbose,
        )

        if df_flat.empty:
            return pd.DataFrame()

        # ピボットして元の出力形式に合わせる
        # Index: Date, Columns: Identifier (Ticker), Values: fields[0]
        if "Identifier" not in df_flat.columns:
            return pd.DataFrame()

        df_pivot = df_flat.pivot_table(
            index="Date",
            columns="Identifier",
            values=fields[0],
        )

        # カラム名をTickerに設定 (元の挙動に合わせる)
        df_pivot.columns.name = "Ticker"

        return df_pivot

    # --------------------------------------------------------------------------
    def get_historical_data_with_overrides(
        self,
        securities: list[str],
        fields: list[str],
        start_date: str,
        end_date: str,
        id_type: str = "ticker",
        periodicity: str = "DAILY",
        currency: str | None = None,
        overrides: dict[str, str] | None = None,
        verbose: bool = True,
    ) -> pd.DataFrame:
        """
        BLPAPIを使用してヒストリカルデータをオーバーライド付きで取得

        様々なセキュリティ識別子に対応し、ForwardおよびTrailing(実績)指標を取得可能

        :param securities: 取得する銘柄識別子リスト
        :param fields: 取得するデータフィールドリスト
        :param start_date: 開始日 (YYYYMMDD形式)
        :param end_date: 終了日 (YYYYMMDD形式)
        :param id_type: 識別子タイプ ('ticker', 'sedol', 'cusip', 'isin', 'figi')
        :param currency: データを変換する通貨コード
        :param periodicity: 取得周期 ('DAILY', 'WEEKLY', 'MONTHLY', 'QUARTERLY', 'YEARLY')
        :param overrides: オーバーライド設定の辞書 (例: {'BEST_FPERIOD_OVERRIDE': '1FY'})
        :param verbose: ログ出力の有効/無効
        :return: DataFrame with historical data

        識別子タイプ:
        - 'ticker': Bloomberg Ticker (例: 'AAPL US Equity')
        - 'sedol': SEDOL (例: '2046251')
        - 'cusip': CUSIP (例: '037833100')
        - 'isin': ISIN (例: 'US0378331005')
        - 'figi': FIGI (例: 'BBG000B9XRY4')

        主要なオーバーライド例:
        - Forward指標: {'BEST_FPERIOD_OVERRIDE': '1FY'}  # 1年先予想
        - Trailing指標: {'BEST_FPERIOD_OVERRIDE': '-0FY'} # 実績
        - NTM指標: {'BEST_FPERIOD_OVERRIDE': '1TY'}      # Next 12M
        """

        # 周期の検証
        valid_periodicities = [
            "DAILY",
            "WEEKLY",
            "MONTHLY",
            "QUARTERLY",
            "SEMI_ANNUALLY",
            "YEARLY",
        ]
        periodicity_upper = periodicity.upper()
        if periodicity_upper not in valid_periodicities:
            print(
                f"❌ 無効な周期: {periodicity}. 有効な値: {', '.join(valid_periodicities)}"
            )
            return pd.DataFrame()

        session = self._create_session(verbose=verbose)
        if not session:
            return pd.DataFrame()

        # 2. サービスへのアクセス
        if not session.openService(self.REF_DATA_SERVICE):
            print(f"❌ サービス '{self.REF_DATA_SERVICE}' のオープンに失敗しました。")
            session.stop()
            return pd.DataFrame()

        ref_data_service = session.getService(self.REF_DATA_SERVICE)
        if verbose:
            print("✅ サービスオープン完了。リクエスト作成中...")

        # 3. 識別子の正規化
        valid_id_types = {
            "ticker": "",
            "sedol": "/sedol/",
            "cusip": "/cusip/",
            "isin": "/isin/",
            "figi": "/figi/",
        }

        id_type_lower = id_type.lower()
        if id_type_lower not in valid_id_types:
            print(
                f"❌ 無効な識別子タイプ: {id_type}. 有効なタイプ: {', '.join(valid_id_types.keys())}"
            )
            session.stop()
            return pd.DataFrame()

        # 識別子のマッピングを作成
        id_mapping = {}
        normalized_securities = []

        for identifier in securities:
            if id_type_lower == "ticker":
                # Tickerの場合はそのまま使用
                normalized_id = identifier
            else:
                # その他の識別子タイプの場合はプレフィックスを追加
                normalized_id = f"{valid_id_types[id_type_lower]}{identifier}"

            normalized_securities.append(normalized_id)
            id_mapping[normalized_id] = identifier

        # 4. リクエストの作成
        request = ref_data_service.createRequest("HistoricalDataRequest")

        for sec in normalized_securities:
            request.append("securities", sec)  # type: ignore

        for field in fields:
            request.append("fields", field)  # type: ignore

        request.set("startDate", start_date)  # type: ignore
        request.set("endDate", end_date)  # type: ignore
        request.set("periodicitySelection", periodicity_upper)  # type: ignore

        # 通貨の指定
        if currency:
            request.set("currency", currency.upper())  # type: ignore

            if currency.upper() == "LOCAL":
                overrides_element = request.getElement("overrides")
                override = overrides_element.appendElement()
                override.setElement("fieldId", "PRICING_CHCE")
                override.setElement("value", "LOCAL")

        # オーバーライドの設定
        if overrides:
            overrides_element = request.getElement("overrides")  # type: ignore
            for field_id, value in overrides.items():
                override = overrides_element.appendElement()
                override.setElement("fieldId", field_id)  # type: ignore
                override.setElement("value", value)  # type: ignore

            if verbose:
                override_info = ", ".join([f"{k}={v}" for k, v in overrides.items()])
                print(f"🔧 オーバーライド設定: {override_info}")

        # 5. リクエストの送信
        if verbose:
            id_type_info = f"[{id_type.upper()}]" if id_type != "ticker" else ""
            currency_info = f" ({currency}建て)" if currency else ""
            periodicity_info = f" [{periodicity_upper}]"  # ✅ 追加
            override_info = " with overrides" if overrides else ""
            print(
                f"📡 リクエストを送信します{id_type_info}{currency_info}{periodicity_info}{override_info}"  # ✅ 変更
            )
            print(
                f"   期間: {datetime.datetime.strptime(start_date, '%Y%m%d').strftime('%Y-%m-%d')} - {datetime.datetime.strptime(end_date, '%Y%m%d').strftime('%Y-%m-%d')}"
            )
        session.sendRequest(request)

        data_store = {}

        # 6. レスポンスの処理
        while True:
            event = session.nextEvent(5000)

            if (
                event.eventType() == blpapi.Event.RESPONSE  # type: ignore
                or event.eventType() == blpapi.Event.PARTIAL_RESPONSE  # type: ignore
            ):
                for msg in event:
                    if msg.hasElement("responseError"):
                        error_info = msg.getElement("responseError")
                        error_message = error_info.getElement("message").getValue()
                        print(
                            f"❌ リクエスト全体のエラーが発生しました: {error_message}"
                        )
                        return pd.DataFrame()

                    if not msg.hasElement("securityData"):
                        continue

                    security_data = msg.getElement("securityData")
                    security_id = security_data.getElement("security").getValue()
                    original_id = id_mapping.get(security_id, security_id)

                    if security_data.hasElement("securityError"):
                        if verbose:
                            print(
                                f"❌ {original_id} ({id_type.upper()}) でエラー: {security_data.getElement('securityError').getElement('message').getValue()}"
                            )
                        continue

                    field_data_array = security_data.getElement("fieldData")

                    for field_data in field_data_array.values():
                        date_str = field_data.getElement("date").getValue()
                        data_point = {"Date": pd.to_datetime(date_str)}

                        for field in fields:
                            if field_data.hasElement(field):
                                data_point[field] = field_data.getElement(
                                    field
                                ).getValue()
                            else:
                                data_point[field] = None

                        if original_id not in data_store:
                            data_store[original_id] = []

                        data_point["Identifier"] = original_id
                        data_point["ID_Type"] = id_type.upper()
                        data_store[original_id].append(data_point)

                if event.eventType() == blpapi.Event.RESPONSE:  # type: ignore
                    break

            elif event.eventType() == blpapi.Event.TIMEOUT:  # type: ignore
                if verbose:
                    print("⏳ タイムアウトしました。")
                break

            elif event.eventType() == blpapi.Event.SESSION_STATUS:  # type: ignore
                for msg in event:
                    if msg.messageType() == blpapi.Name("SessionTerminated"):  # type: ignore
                        print("❌ セッションが終了しました。")
                        return pd.DataFrame()

        # 7. セッションの終了
        session.stop()
        if verbose:
            print("\n✅ データ取得完了。接続を終了しました。")

        # 8. データの整形
        all_data_list = [item for sublist in data_store.values() for item in sublist]

        if not all_data_list:
            if verbose:
                print("取得されたデータがありません。")
            return pd.DataFrame()

        df = pd.DataFrame(all_data_list)

        if verbose:
            print("\n📊 取得データ:")
            print(f"   行数: {len(df):,}行")
            print(f"   日付範囲: {df['Date'].min()} ~ {df['Date'].max()}")
            print(f"   ユニーク日数: {df['Date'].nunique()}日")
            print(f"   識別子数: {df['Identifier'].nunique()}")
            print(f"   識別子タイプ: {id_type.upper()}")
            print(f"   周期: {periodicity_upper}")  # ✅ 追加

        return df

    # --------------------------------------------------------------------------
    def get_financial_data(
        self,
        securities: list[str],
        fields: list[str],
        period: str = "Q",  # Q=Quarterly, A=Annual
        fiscal_period: str | None = None,  # 1FY, 2FY, etc.
        start_date: str | None = None,
        end_date: str | None = None,
        id_type: str = "ticker",
        currency: str | None = None,
        include_announcement_date: bool = False,
        # チャンクサイズのデフォルト設定
        chunk_size: int = 50,
        max_retries: int = 3,
        retry_delay: int = 2,
        verbose: bool = True,
    ) -> pd.DataFrame:
        """
        個別企業の財務データ(損益計算書、貸借対照表、キャッシュフロー等)を取得します。
        大量の銘柄を指定した場合、自動的にチャンク分割して処理します。

        :param securities: 銘柄リスト (例: ['AAPL US Equity'])
        :param fields: フィールドリスト (例: ['SALES_REV_TURN', 'NET_INCOME'])
        :param period: 期間 ('Q' or 'A')
        :param fiscal_period: 会計年度指定 (例: '1FY', '-1FY')
        :param start_date: 開始日 (YYYYMMDD)
        :param end_date: 終了日 (YYYYMMDD)
        :param id_type: 識別子タイプ ('ticker', 'sedol', 'cusip', 'isin', 'figi')
        :param currency: 通貨コード (例: 'USD', 'JPY')
        :param include_announcement_date: 発表日(ANNOUNCEMENT_DT)も同時に取得するかどうか
        :param chunk_size: 1回のリクエストで処理する銘柄数
        :param max_retries: エラー時の最大リトライ回数
        :param retry_delay: リトライ間の待機時間(秒)
        :param verbose: ログ出力
        :return: DataFrame with columns: Ticker, Field, Period_End_Date, Value, Currency, Fiscal_Period, Updated_At, (Announcement_Date)
        """
        session = self._create_session(verbose=verbose)
        if not session:
            return pd.DataFrame()

        if not session.openService(self.REF_DATA_SERVICE):
            print(f"❌ サービス '{self.REF_DATA_SERVICE}' のオープンに失敗しました。")
            session.stop()
            return pd.DataFrame()

        ref_data_service = session.getService(self.REF_DATA_SERVICE)

        # 識別子の正規化
        valid_id_types = {
            "ticker": "",
            "sedol": "/sedol/",
            "cusip": "/cusip/",
            "isin": "/isin/",
            "figi": "/figi/",
        }

        id_type_lower = id_type.lower()
        if id_type_lower not in valid_id_types:
            print(
                f"❌ 無効な識別子タイプ: {id_type}. 有効なタイプ: {', '.join(valid_id_types.keys())}"
            )
            session.stop()
            return pd.DataFrame()

        # 識別子のマッピングを作成
        id_mapping = {}
        normalized_securities = []

        for identifier in securities:
            if id_type_lower == "ticker":
                # Tickerの場合はそのまま使用
                normalized_id = identifier
            else:
                # その他の識別子タイプの場合はプレフィックスを追加
                normalized_id = f"{valid_id_types[id_type_lower]}{identifier}"

            normalized_securities.append(normalized_id)
            id_mapping[normalized_id] = identifier

        # チャンク分割して処理
        all_data_list = []
        total_securities = len(normalized_securities)
        num_chunks = (total_securities + chunk_size - 1) // chunk_size

        if verbose:
            print(
                f"📊 処理対象: {total_securities}銘柄 (チャンク数: {num_chunks}, サイズ: {chunk_size})"
            )

        import time

        for i in range(0, total_securities, chunk_size):
            chunk_securities = normalized_securities[i : i + chunk_size]
            chunk_index = i // chunk_size + 1

            if verbose:
                print(
                    f"🔄 チャンク {chunk_index}/{num_chunks} を処理中 ({len(chunk_securities)}銘柄)..."
                )

            retry_count = 0
            success = False

            while retry_count <= max_retries:
                try:
                    request = ref_data_service.createRequest("HistoricalDataRequest")

                    for sec in chunk_securities:
                        request.append("securities", sec)  # type: ignore

                    request_fields = fields.copy()
                    if (
                        include_announcement_date
                        and "ANNOUNCEMENT_DT" not in request_fields
                    ):
                        request_fields.append("ANNOUNCEMENT_DT")

                    for field in request_fields:
                        request.append("fields", field)  # type: ignore

                    # 期間設定
                    if start_date and end_date:
                        request.set("startDate", start_date)  # type: ignore
                        request.set("endDate", end_date)  # type: ignore
                    else:
                        # デフォルトは過去5年
                        end = datetime.datetime.now()
                        start = end - datetime.timedelta(days=365 * 5)
                        request.set("startDate", start.strftime("%Y%m%d"))  # type: ignore
                        request.set("endDate", end.strftime("%Y%m%d"))  # type: ignore

                    # 周期設定
                    if period.upper() == "A":
                        request.set("periodicitySelection", "YEARLY")  # type: ignore
                    else:
                        request.set("periodicitySelection", "QUARTERLY")  # type: ignore

                    # 通貨設定
                    if currency:
                        request.set("currency", currency.upper())  # type: ignore

                    # オーバーライド (Fiscal Period)
                    if fiscal_period:
                        overrides = request.getElement("overrides")  # type: ignore
                        override = overrides.appendElement()
                        override.setElement("fieldId", "BEST_FPERIOD_OVERRIDE")  # type: ignore
                        override.setElement("value", fiscal_period)  # type: ignore

                    session.sendRequest(request)

                    # 現在時刻 (Updated_At用)
                    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                    chunk_data_list = []

                    while True:
                        event = session.nextEvent(5000)
                        if (
                            event.eventType() == blpapi.Event.RESPONSE
                            or event.eventType() == blpapi.Event.PARTIAL_RESPONSE
                        ):  # type: ignore
                            for msg in event:
                                if msg.hasElement("securityData"):
                                    sec_data = msg.getElement("securityData")
                                    ticker = sec_data.getElement("security").getValue()
                                    # マッピングを使用して元のIDを取得
                                    original_id = id_mapping.get(ticker, ticker)

                                    if sec_data.hasElement("securityError"):
                                        if verbose:
                                            err_msg = (
                                                sec_data.getElement("securityError")
                                                .getElement("message")
                                                .getValue()
                                            )
                                            print(
                                                f"⚠️ {original_id}: Security Error - {err_msg}"
                                            )
                                        continue

                                    field_data_array = sec_data.getElement("fieldData")

                                    for field_data in field_data_array.values():
                                        date_val = field_data.getElement(
                                            "date"
                                        ).getValue()

                                        announcement_date = None
                                        if (
                                            include_announcement_date
                                            and field_data.hasElement("ANNOUNCEMENT_DT")
                                        ):
                                            announcement_date = field_data.getElement(
                                                "ANNOUNCEMENT_DT"
                                            ).getValue()

                                        for field in fields:
                                            if field_data.hasElement(field):
                                                val = field_data.getElement(
                                                    field
                                                ).getValue()

                                                item = {
                                                    "Ticker": original_id,
                                                    "Field": field,
                                                    "Period_End_Date": date_val,
                                                    "Value": val,
                                                    "Currency": (
                                                        currency if currency else None
                                                    ),
                                                    "Fiscal_Period": fiscal_period,
                                                    "Updated_At": current_time,
                                                }

                                                if include_announcement_date:
                                                    item["Announcement_Date"] = (
                                                        announcement_date
                                                    )

                                                chunk_data_list.append(item)

                        if event.eventType() == blpapi.Event.RESPONSE:  # type: ignore
                            break
                        elif event.eventType() == blpapi.Event.TIMEOUT:  # type: ignore
                            raise TimeoutError("Bloomberg API Timeout")

                    all_data_list.extend(chunk_data_list)
                    success = True
                    break  # Retry loop break

                except Exception as e:
                    retry_count += 1
                    if verbose:
                        print(
                            f"⚠️ チャンク {chunk_index} でエラー発生 (試行 {retry_count}/{max_retries + 1}): {e}"
                        )

                    if retry_count <= max_retries:
                        time.sleep(retry_delay)
                        # セッションの再接続を試みる（深刻なエラーの場合）
                        if "Session" in str(e) or "Service" in str(e):
                            print("🔄 セッションを再接続します...")
                            session.stop()
                            session = self._create_session(verbose=False)
                            if not session or not session.openService(
                                self.REF_DATA_SERVICE
                            ):
                                print("❌ 再接続に失敗しました。")
                                break
                            ref_data_service = session.getService(self.REF_DATA_SERVICE)
                    else:
                        print(
                            f"❌ チャンク {chunk_index} の処理に失敗しました。スキップします。"
                        )

        session.stop()

        if not all_data_list:
            if verbose:
                print("⚠️ データなし")
            return pd.DataFrame()

        df = pd.DataFrame(all_data_list)
        if verbose:
            print(f"✅ 合計 {len(df)}件の財務データを取得")

        return df

    # --------------------------------------------------------------------------
    def get_earnings_dates(
        self,
        securities: list[str],
        id_type: str = "ticker",
        verbose: bool = True,
    ) -> pd.DataFrame:
        """
        企業の直近および次回の決算発表日情報を取得します。

        取得フィールド:
        - LATEST_ANNOUNCEMENT_DT: 直近の決算発表日
        - NEXT_ANNOUNCEMENT_DT: 次回の決算発表予定日
        - EARNINGS_ANN_DT_TIME_OF_DAY: 発表時間帯 (Before Market, After Market, etc.)

        :param securities: 銘柄リスト (例: ['AAPL US Equity'])
        :param id_type: 識別子タイプ ('ticker', 'sedol', 'cusip', 'isin', 'figi')
        :param verbose: ログ出力
        :return: DataFrame with columns: Ticker, Latest_Announcement, Next_Announcement, Time_Of_Day
        """
        session = self._create_session(verbose=verbose)
        if not session:
            return pd.DataFrame()

        if not session.openService(self.REF_DATA_SERVICE):
            print(f"❌ サービス '{self.REF_DATA_SERVICE}' のオープンに失敗しました。")
            session.stop()
            return pd.DataFrame()

        ref_data_service = session.getService(self.REF_DATA_SERVICE)

        # 識別子の正規化
        valid_id_types = {
            "ticker": "",
            "sedol": "/sedol/",
            "cusip": "/cusip/",
            "isin": "/isin/",
            "figi": "/figi/",
        }

        id_type_lower = id_type.lower()
        if id_type_lower not in valid_id_types:
            print(
                f"❌ 無効な識別子タイプ: {id_type}. 有効なタイプ: {', '.join(valid_id_types.keys())}"
            )
            session.stop()
            return pd.DataFrame()

        # 識別子のマッピングを作成
        id_mapping = {}
        normalized_securities = []

        for identifier in securities:
            if id_type_lower == "ticker":
                normalized_id = identifier
            else:
                normalized_id = f"{valid_id_types[id_type_lower]}{identifier}"

            normalized_securities.append(normalized_id)
            id_mapping[normalized_id] = identifier

        request = ref_data_service.createRequest("ReferenceDataRequest")

        for sec in normalized_securities:
            request.append("securities", sec)  # type: ignore

        fields = [
            "LATEST_ANNOUNCEMENT_DT",
            "NEXT_ANNOUNCEMENT_DT",
            "EARNINGS_ANN_DT_TIME_OF_DAY",
        ]
        for field in fields:
            request.append("fields", field)  # type: ignore

        if verbose:
            print("📡 決算発表日情報をリクエスト中...")

        session.sendRequest(request)

        data_list = []

        while True:
            event = session.nextEvent(5000)
            if (
                event.eventType() == blpapi.Event.RESPONSE
                or event.eventType() == blpapi.Event.PARTIAL_RESPONSE
            ):  # type: ignore
                for msg in event:
                    if msg.hasElement("securityData"):
                        sec_data_array = msg.getElement("securityData")

                        # ReferenceDataRequest returns array of securityData if multiple securities?
                        # Actually ReferenceDataRequest returns securityData array in response?
                        # Let's check typical structure. Usually it's an array or sequence.
                        # In BLPAPI python, msg.getElement("securityData") returns an array element if it's an array.
                        # But ReferenceDataRequest response structure:
                        # securityData[] -> security, fieldData, sequenceNumber, securityError

                        # If sec_data_array is an array, we iterate.
                        # However, in get_historical_data, it was different.
                        # For ReferenceData, securityData is an array.

                        num_securities = sec_data_array.numValues()

                        for i in range(num_securities):
                            sec_data = sec_data_array.getValue(i)
                            security_id = sec_data.getElement("security").getValue()
                            original_id = id_mapping.get(security_id, security_id)

                            if sec_data.hasElement("securityError"):
                                if verbose:
                                    print(f"❌ {original_id}: Security Error")
                                continue

                            field_data = sec_data.getElement("fieldData")

                            item = {"Ticker": original_id}

                            # LATEST_ANNOUNCEMENT_DT
                            if field_data.hasElement("LATEST_ANNOUNCEMENT_DT"):
                                item["Latest_Announcement"] = field_data.getElement(
                                    "LATEST_ANNOUNCEMENT_DT"
                                ).getValue()
                            else:
                                item["Latest_Announcement"] = None

                            # NEXT_ANNOUNCEMENT_DT
                            if field_data.hasElement("NEXT_ANNOUNCEMENT_DT"):
                                item["Next_Announcement"] = field_data.getElement(
                                    "NEXT_ANNOUNCEMENT_DT"
                                ).getValue()
                            else:
                                item["Next_Announcement"] = None

                            # EARNINGS_ANN_DT_TIME_OF_DAY
                            if field_data.hasElement("EARNINGS_ANN_DT_TIME_OF_DAY"):
                                item["Time_Of_Day"] = field_data.getElement(
                                    "EARNINGS_ANN_DT_TIME_OF_DAY"
                                ).getValue()
                            else:
                                item["Time_Of_Day"] = None

                            data_list.append(item)

            if event.eventType() == blpapi.Event.RESPONSE:  # type: ignore
                break
            elif event.eventType() == blpapi.Event.TIMEOUT:  # type: ignore
                if verbose:
                    print("⏳ タイムアウト")
                break

        session.stop()

        if not data_list:
            if verbose:
                print("⚠️ データなし")
            return pd.DataFrame()

        df = pd.DataFrame(data_list)
        if verbose:
            print(f"✅ {len(df)}件の決算情報を取得")

        return df

    # --------------------------------------------------------------------------
    def analyze_earnings_bfw(
        self,
        ticker: str,
        earnings_date: datetime.datetime,
        days_before: int = 3,
        days_after: int = 3,
        verbose: bool = True,
    ) -> pd.DataFrame:
        """
        決算発表前後のBFWを分析

        :param ticker: 証券コード (例: "AAPL US Equity")
        :param earnings_date: 決算発表日
        :param days_before: 決算前何日から取得するか
        :param days_after: 決算後何日まで取得するか
        :param verbose: ログ出力の有効/無効
        :return: DataFrame with BFW news around earnings
        """
        session = self._create_session(verbose=verbose)
        if not session:
            return pd.DataFrame()

        if not session.openService(self.NEWS_SERVICE):
            print(f"❌ サービス '{self.NEWS_SERVICE}' のオープンに失敗しました。")
            session.stop()
            return pd.DataFrame()

        news_service = session.getService(self.NEWS_SERVICE)
        request = news_service.createRequest("NewsHeadlineRequest")

        request.set("source", "BFW")
        request.append("securities", ticker)

        # 決算日の前後期間
        start_date = earnings_date - datetime.timedelta(days=days_before)
        end_date = earnings_date + datetime.timedelta(days=days_after)

        request.set("startDateTime", start_date)
        request.set("endDateTime", end_date)

        if verbose:
            print(
                f"📡 {ticker} の決算前後BFWを取得中 ({start_date.date()} - {end_date.date()})..."
            )

        session.sendRequest(request)

        headlines = []

        while True:
            event = session.nextEvent(5000)

            if (
                event.eventType() == blpapi.Event.RESPONSE  # type: ignore
                or event.eventType() == blpapi.Event.PARTIAL_RESPONSE  # type: ignore
            ):
                for msg in event:
                    if msg.hasElement("newsHeadlines"):
                        news_headlines = msg.getElement("newsHeadlines")

                        for headline in news_headlines.values():
                            story_dt = headline.getElementAsDatetime("storyDateTime")
                            days_from_earnings = (
                                story_dt.date() - earnings_date.date()
                            ).days

                            headline_data = {
                                "story_datetime": story_dt,
                                "days_from_earnings": days_from_earnings,
                                "headline": headline.getElementAsString("headline"),
                                "story_id": headline.getElementAsString("storyId"),
                            }
                            headlines.append(headline_data)

                if event.eventType() == blpapi.Event.RESPONSE:  # type: ignore
                    break

            elif event.eventType() == blpapi.Event.TIMEOUT:  # type: ignore
                if verbose:
                    print("⏳ タイムアウトしました。")
                break

        session.stop()

        if not headlines:
            if verbose:
                print("取得されたデータがありません。")
            return pd.DataFrame()

        df = pd.DataFrame(headlines)
        df = df.sort_values("story_datetime")

        if verbose:
            print(f"\n✅ {len(df)}件のBFW速報を取得しました。")
            print(f"   決算前: {len(df[df['days_from_earnings'] < 0])}件")
            print(f"   決算当日: {len(df[df['days_from_earnings'] == 0])}件")
            print(f"   決算後: {len(df[df['days_from_earnings'] > 0])}件")

        return df

    # --------------------------------------------------------------------------
    def convert_identifiers(
        self,
        identifiers: list[str],
        id_type: str = "sedol",
        output_fields: list[str] | None = None,
        verbose: bool = True,
    ) -> pd.DataFrame | None:
        """
        様々な識別子(SEDOL, CUSIP, ISIN)からBloomberg TickerとFIGI等を取得

        :param identifiers: 識別子のリスト(例: ['2046251', '0540528'])
        :param id_type: 識別子のタイプ ('sedol', 'cusip', 'isin')
        :param output_fields: 取得したい追加フィールドのリスト(Noneの場合は標準フィールドのみ)
        :param verbose: ログ出力の有効/無効
        :return: DataFrame with columns: Original_ID, Bloomberg_Ticker, FIGI, [追加フィールド], Error
        """
        session = self._create_session(verbose=verbose)
        if not session:
            return None

        # 2. サービスへのアクセス
        if not session.openService(self.REF_DATA_SERVICE):
            print(f"❌ サービス '{self.REF_DATA_SERVICE}' のオープンに失敗しました。")
            session.stop()
            return None

        ref_data_service = session.getService(self.REF_DATA_SERVICE)
        if verbose:
            print("✅ サービスオープン完了。リクエスト作成中...")

        # 3. リクエストの作成
        request = ref_data_service.createRequest("ReferenceDataRequest")

        # 識別子タイプの検証
        valid_id_types = ["sedol", "cusip", "isin"]
        id_type_lower = id_type.lower()

        if id_type_lower not in valid_id_types:
            print(
                f"❌ 無効な識別子タイプ: {id_type}. 有効なタイプ: {', '.join(valid_id_types)}"
            )
            session.stop()
            return None

        # 識別子をBloomberg形式に変換して追加
        id_mapping = {}
        for identifier in identifiers:
            security_id = f"/{id_type_lower}/{identifier}"
            request.append("securities", security_id)  # type: ignore
            id_mapping[security_id] = identifier

        # 標準フィールドを追加
        standard_fields = [
            "PARSEKYABLE_DES",
            "ID_BB_GLOBAL",
        ]

        for field in standard_fields:
            request.append("fields", field)  # type: ignore

        # 追加フィールドがあれば追加
        additional_fields = []
        if output_fields:
            for field in output_fields:
                request.append("fields", field)  # type: ignore
                additional_fields.append(field)

        # 4. リクエストの送信
        if verbose:
            print(
                f"📡 識別子変換リクエストを送信します ({id_type.upper()}数: {len(identifiers)})..."
            )
        session.sendRequest(request)

        # 5. レスポンスの処理
        data_list: list[dict[str, Any]] = []

        while True:
            event = session.nextEvent(5000)

            if (
                event.eventType() == blpapi.Event.RESPONSE  # type: ignore
                or event.eventType() == blpapi.Event.PARTIAL_RESPONSE  # type: ignore
            ):
                for msg in event:
                    security_data_array = msg.getElement("securityData")

                    for security_data in security_data_array.values():
                        security_id = security_data.getElement("security").getValue()
                        original_id = id_mapping.get(security_id, security_id)

                        result: dict[str, Any] = {
                            "Original_ID": original_id,
                            "ID_Type": id_type.upper(),
                            "Bloomberg_Ticker": None,
                            "FIGI": None,
                            "Error": None,
                        }

                        for field in additional_fields:
                            result[field] = None

                        if security_data.hasElement("securityError"):
                            error_msg = (
                                security_data.getElement("securityError")
                                .getElement("message")
                                .getValue()
                            )
                            if verbose:
                                print(
                                    f"❌ {id_type.upper()} {original_id} でエラー: {error_msg}"
                                )
                            result["Error"] = error_msg
                            data_list.append(result)
                            continue

                        field_data = security_data.getElement("fieldData")

                        if field_data.hasElement("PARSEKYABLE_DES"):
                            ticker_element = field_data.getElement("PARSEKYABLE_DES")
                            if not ticker_element.isNull():
                                result["Bloomberg_Ticker"] = ticker_element.getValue()

                        if field_data.hasElement("ID_BB_GLOBAL"):
                            figi_element = field_data.getElement("ID_BB_GLOBAL")
                            if not figi_element.isNull():
                                result["FIGI"] = figi_element.getValue()

                        for field in additional_fields:
                            if field_data.hasElement(field):
                                field_element = field_data.getElement(field)
                                if not field_element.isNull():
                                    result[field] = field_element.getValue()

                        data_list.append(result)

                if event.eventType() == blpapi.Event.RESPONSE:  # type: ignore
                    break

            elif event.eventType() == blpapi.Event.TIMEOUT:  # type: ignore
                if verbose:
                    print("⏳ タイムアウトしました。")
                break

            elif event.eventType() == blpapi.Event.SESSION_STATUS:  # type: ignore
                for msg in event:
                    if msg.messageType() == blpapi.Name("SessionTerminated"):  # type: ignore
                        print("❌ セッションが終了しました。")
                        return None

        # 6. セッションの終了
        session.stop()
        if verbose:
            print("\n✅ 識別子変換完了。接続を終了しました。")

        # 7. データの整形
        if not data_list:
            if verbose:
                print("取得されたデータがありません。")
            return pd.DataFrame()

        df = pd.DataFrame(data_list)

        if verbose:
            success_count = df[df["Error"].isna()].shape[0]
            error_count = df[df["Error"].notna()].shape[0]
            print(f"\n📊 変換結果: 成功 {success_count}件, エラー {error_count}件")

            if len(identifiers) > 0:
                success_rate = (success_count / len(identifiers)) * 100
                print(f"   成功率: {success_rate:.1f}%")

        return df

    # --------------------------------------------------------------------------
    def convert_identifiers_with_date(
        self,
        identifiers: list[str],
        id_type: str = "sedol",
        as_of_date: str | None = None,
        output_fields: list[str] | None = None,
        verbose: bool = True,
    ) -> pd.DataFrame | None:
        """
        特定の時点における識別子からBloomberg Tickerを取得

        :param identifiers: 識別子のリスト(例: ['2046251', '0540528'])
        :param id_type: 識別子のタイプ ('sedol', 'cusip', 'isin')
        :param as_of_date: 基準日 (YYYYMMDD形式、Noneの場合は現在)
        :param output_fields: 取得したい追加フィールドのリスト
        :param verbose: ログ出力の有効/無効
        :return: DataFrame with time-specific identifiers
        """
        session = self._create_session(verbose=verbose)
        if not session:
            return None

        # 2. サービスへのアクセス
        if not session.openService(self.REF_DATA_SERVICE):
            print(f"❌ サービス '{self.REF_DATA_SERVICE}' のオープンに失敗しました。")
            session.stop()
            return None

        ref_data_service = session.getService(self.REF_DATA_SERVICE)
        if verbose:
            print("✅ サービスオープン完了。リクエスト作成中...")

        # 3. リクエストの作成
        request = ref_data_service.createRequest("ReferenceDataRequest")

        valid_id_types = ["sedol", "cusip", "isin"]
        id_type_lower = id_type.lower()

        if id_type_lower not in valid_id_types:
            print(
                f"❌ 無効な識別子タイプ: {id_type}. 有効なタイプ: {', '.join(valid_id_types)}"
            )
            session.stop()
            return None

        id_mapping = {}
        for identifier in identifiers:
            security_id = f"/{id_type_lower}/{identifier}"
            request.append("securities", security_id)  # type: ignore
            id_mapping[security_id] = identifier

        standard_fields = [
            "PARSEKYABLE_DES",
            "ID_BB_GLOBAL",
        ]

        for field in standard_fields:
            request.append("fields", field)  # type: ignore

        additional_fields = []
        if output_fields:
            for field in output_fields:
                request.append("fields", field)  # type: ignore
                additional_fields.append(field)

        # 時点指定のオーバーライド設定
        if as_of_date:
            overrides = request.getElement("overrides")  # type: ignore
            override = overrides.appendElement()
            override.setElement("fieldId", "REFERENCE_DATE")  # type: ignore
            override.setElement("value", as_of_date)  # type: ignore

            if verbose:
                date_str = datetime.datetime.strptime(as_of_date, "%Y%m%d").strftime(
                    "%Y-%m-%d"
                )
                print(f"📅 基準日を設定: {date_str}")

        # 4. リクエストの送信
        if verbose:
            print(
                f"📡 識別子変換リクエストを送信します ({id_type.upper()}数: {len(identifiers)})..."
            )
        session.sendRequest(request)

        # 5. レスポンスの処理
        data_list: list[dict[str, Any]] = []

        while True:
            event = session.nextEvent(5000)

            if (
                event.eventType() == blpapi.Event.RESPONSE  # type: ignore
                or event.eventType() == blpapi.Event.PARTIAL_RESPONSE  # type: ignore
            ):
                for msg in event:
                    security_data_array = msg.getElement("securityData")

                    for security_data in security_data_array.values():
                        security_id = security_data.getElement("security").getValue()
                        original_id = id_mapping.get(security_id, security_id)

                        result: dict[str, Any] = {
                            "Original_ID": original_id,
                            "ID_Type": id_type.upper(),
                            "As_Of_Date": as_of_date if as_of_date else "Current",
                            "Bloomberg_Ticker": None,
                            "FIGI": None,
                            "Error": None,
                        }

                        for field in additional_fields:
                            result[field] = None

                        if security_data.hasElement("securityError"):
                            error_msg = (
                                security_data.getElement("securityError")
                                .getElement("message")
                                .getValue()
                            )
                            if verbose:
                                print(
                                    f"❌ {id_type.upper()} {original_id} でエラー: {error_msg}"
                                )
                            result["Error"] = error_msg
                            data_list.append(result)
                            continue

                        field_data = security_data.getElement("fieldData")

                        if field_data.hasElement("PARSEKYABLE_DES"):
                            ticker_element = field_data.getElement("PARSEKYABLE_DES")
                            if not ticker_element.isNull():
                                result["Bloomberg_Ticker"] = ticker_element.getValue()

                        if field_data.hasElement("ID_BB_GLOBAL"):
                            figi_element = field_data.getElement("ID_BB_GLOBAL")
                            if not figi_element.isNull():
                                result["FIGI"] = figi_element.getValue()

                        for field in additional_fields:
                            if field_data.hasElement(field):
                                field_element = field_data.getElement(field)
                                if not field_element.isNull():
                                    result[field] = field_element.getValue()

                        data_list.append(result)

                if event.eventType() == blpapi.Event.RESPONSE:  # type: ignore
                    break

            elif event.eventType() == blpapi.Event.TIMEOUT:  # type: ignore
                if verbose:
                    print("⏳ タイムアウトしました。")
                break

            elif event.eventType() == blpapi.Event.SESSION_STATUS:  # type: ignore
                for msg in event:
                    if msg.messageType() == blpapi.Name("SessionTerminated"):  # type: ignore
                        print("❌ セッションが終了しました。")
                        return None

        session.stop()
        if verbose:
            print("\n✅ 識別子変換完了。接続を終了しました。")

        if not data_list:
            if verbose:
                print("取得されたデータがありません。")
            return pd.DataFrame()

        df = pd.DataFrame(data_list)

        if verbose:
            success_count = df[df["Error"].isna()].shape[0]
            error_count = df[df["Error"].notna()].shape[0]
            print(f"\n📊 変換結果: 成功 {success_count}件, エラー {error_count}件")

            if len(identifiers) > 0:
                success_rate = (success_count / len(identifiers)) * 100
                print(f"   成功率: {success_rate:.1f}%")

        return df

    # --------------------------------------------------------------------------
    def load_ids_from_blpapi(
        self,
        id_type: str,
        id_list: list[str],
        as_of_date: datetime.datetime,
        verbose: bool = False,
    ) -> pd.DataFrame:
        df = (
            self.convert_identifiers_with_date(
                identifiers=id_list,
                as_of_date=as_of_date.strftime("%Y%m%d"),
                verbose=verbose,
            )
            .drop(columns=["Error", "ID_Type", "As_Of_Date"])
            .assign(
                Original_ID=lambda x: x["Original_ID"].str.replace(" Equity", ""),
                date=as_of_date,
            )
            .rename(
                columns={
                    "Original_ID": id_type,
                    "Bloomberg_Ticker": f"Bloomberg_Ticker_{id_type}",
                    "FIGI": f"FIGI_{id_type}",
                }
            )
            .fillna(np.nan)
        )

        return df

    # --------------------------------------------------------------------------
    def get_reference_data(
        self,
        securities: list[str],
        fields: list[str],
        verbose: bool = True,
    ) -> pd.DataFrame | None:
        """
        BLPAPIを使用して参照データ(GICS分類など)を取得し、Pandas DataFrameとして返す
        :param securities: 取得する銘柄識別子リスト (例: ['AAPL US Equity', 'MSFT US Equity'])
        :param fields: 取得するデータフィールドリスト (例: GICS_SECTOR_NAME)
        :param verbose: ログ出力の有効/無効
        """
        session = self._create_session(verbose=verbose)
        if not session:
            return None

        if not session.openService(self.REF_DATA_SERVICE):
            print(f"❌ サービス '{self.REF_DATA_SERVICE}' のオープンに失敗しました。")
            session.stop()
            return None

        ref_data_service = session.getService(self.REF_DATA_SERVICE)
        if verbose:
            print("✅ サービスオープン完了。リクエスト作成中...")

        request = ref_data_service.createRequest("ReferenceDataRequest")

        for sec in securities:
            request.append("securities", sec)  # type: ignore

        for field in fields:
            request.append("fields", field)  # type: ignore

        if verbose:
            print(f"📡 参照データリクエストを送信します (銘柄数: {len(securities)})...")
        session.sendRequest(request)

        data_list: list[dict[str, Any]] = []

        while True:
            event = session.nextEvent(5000)

            if (
                event.eventType() == blpapi.Event.RESPONSE  # type: ignore
                or event.eventType() == blpapi.Event.PARTIAL_RESPONSE  # type: ignore
            ):
                for msg in event:
                    security_data_array = msg.getElement("securityData")

                    for security_data in security_data_array.values():
                        ticker = security_data.getElement("security").getValue()
                        result: dict[str, Any] = {"Ticker": ticker}

                        if security_data.hasElement("securityError"):
                            error_msg = (
                                security_data.getElement("securityError")
                                .getElement("message")
                                .getValue()
                            )
                            if verbose:
                                print(f"❌ {ticker} でエラー: {error_msg}")
                            for field in fields:
                                result[field] = f"ERROR: {error_msg}"
                            data_list.append(result)
                            continue

                        field_data = security_data.getElement("fieldData")

                        for field in fields:
                            if field_data.hasElement(field):
                                result[field] = field_data.getElement(field).getValue()
                            else:
                                result[field] = None

                        data_list.append(result)

                if event.eventType() == blpapi.Event.RESPONSE:  # type: ignore
                    break

            elif event.eventType() == blpapi.Event.TIMEOUT:  # type: ignore
                if verbose:
                    print("⏳ タイムアウトしました。")
                break

            elif event.eventType() == blpapi.Event.SESSION_STATUS:  # type: ignore
                for msg in event:
                    if msg.messageType() == blpapi.Name("SessionTerminated"):  # type: ignore
                        print("❌ セッションが終了しました。")
                        return None

        session.stop()
        if verbose:
            print("\n✅ データ取得完了。接続を終了しました。")

        if not data_list:
            if verbose:
                print("取得されたデータがありません。")
            return pd.DataFrame()

        df = pd.DataFrame(data_list)
        df = df.set_index("Ticker")

        return df

    # --------------------------------------------------------------------------
    def get_latest_date_from_db(
        self,
        db_path: Path,
        table_name: str,
        tickers: list[str],
    ) -> tuple[datetime.datetime, bool]:
        """
        データベースから最新日付を取得

        Parameters
        ----------
        db_path : Path
            データベースファイルのパス
        table_name : str
            テーブル名
        tickers : List[str]
            対象銘柄のリスト

        Returns
        -------
        Tuple[datetime.datetime, bool]
            (開始日, 増分更新フラグ)
        """
        default_start = datetime.datetime(2000, 1, 1)

        if not db_path.exists():
            return default_start, False

        try:
            with sqlite3.connect(str(db_path)) as conn:
                cursor = conn.cursor()

                # テーブル存在チェック
                cursor.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                    (table_name,),
                )

                if cursor.fetchone() is None:
                    return default_start, False

                # 最新日付取得
                placeholders = ",".join(["?" for _ in tickers])
                query = f"""
                    SELECT MAX(Date) as max_date
                    FROM "{table_name}"
                    WHERE Ticker IN ({placeholders})
                """
                df = pd.read_sql(query, conn, params=tickers)

                max_date_str = df["max_date"].iloc[0]
                if max_date_str is None:
                    return default_start, False

                max_date = pd.to_datetime(max_date_str)
                # 翌日から取得
                start_date = max_date + pd.Timedelta(days=1)

                return start_date, True

        except Exception as e:
            print(f"⚠️ データベース読み取りエラー: {e}")
            return default_start, False

    # --------------------------------------------------------------------------
    def update_historical_data(
        self,
        db_path: Path,
        table_name: str,
        tickers: list[str],
        id_type: str,
        field: str = "PX_LAST",
        default_start_date: datetime.datetime | None = None,
        currency: str | None = None,
        verbose: bool = True,
    ) -> int:
        """
        Bloombergヒストリカルデータの増分更新

        Parameters
        ----------
        db_path : Path
            データベースファイルのパス
        table_name : str
            保存先テーブル名
        tickers : List[str]
            取得する銘柄のリスト
        id_type: str
            識別子タイプ ('ticker', 'sedol', 'cusip', 'isin', 'figi')
        field : str, optional
            取得するフィールド (デフォルト: "PX_LAST")
        default_start_date : datetime.datetime, optional
            デフォルトの開始日 (データがない場合)
        currency : str, optional
            通貨コード (例: 'JPY', 'USD', 'LOCAL')
        verbose : bool, optional
            ログ出力の有効/無効

        Returns
        -------
        int
            保存された行数
        """
        if default_start_date is None:
            default_start_date = datetime.datetime(2000, 1, 1)

        # 既存データの確認
        start_date, is_incremental = self.get_latest_date_from_db(
            db_path, table_name, tickers
        )

        # デフォルト開始日を使用
        if not is_incremental:
            start_date = default_start_date

        end_date = datetime.datetime.today()

        # ステータス表示
        if verbose:
            print("=" * 60)
            if is_incremental:
                print("📊 増分更新モード")
                print(
                    f"   最新データ日付: {(start_date - pd.Timedelta(days=1)).strftime('%Y-%m-%d')}"
                )
            else:
                print("🆕 初期データ取得モード")
                db_path.parent.mkdir(parents=True, exist_ok=True)

            print(
                f"   取得期間: {start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}"
            )
            print(f"   対象銘柄: {len(tickers)}銘柄")
            if currency:
                print(f"   通貨: {currency}")
            print("=" * 60)

        # 取得の必要性チェック
        if start_date >= end_date:
            if verbose:
                print("✅ データは最新です。")
            return 0

        # データ取得
        try:
            df_raw = self.get_historical_data(
                securities=tickers,
                id_type=id_type,
                fields=[field],
                start_date=start_date.strftime("%Y%m%d"),
                end_date=end_date.strftime("%Y%m%d"),
                currency=currency,
                verbose=verbose,
            )

            if df_raw.empty:
                if verbose:
                    print("⚠️ 新規データがありません。")
                return 0

            # データ整形
            df_formatted = (
                pd.melt(
                    df_raw.reset_index(),
                    id_vars=["Date"],
                    var_name="Ticker",
                    value_name="value",
                )
                .assign(
                    variable=field,
                    value=lambda x: pd.to_numeric(x["value"], errors="coerce"),
                )
                .dropna(subset=["value"])
            )  # 欠損値を除外

            if verbose:
                print("\n📈 取得データ:")
                print(f"   行数: {len(df_formatted):,}行")
                print(
                    f"   日付範囲: {df_formatted['Date'].min()} ~ {df_formatted['Date'].max()}"
                )
                print(f"   ユニーク日数: {df_formatted['Date'].nunique()}日")

            # 保存
            rows_saved = self.store_to_database(
                df=df_formatted,
                db_path=db_path,
                table_name=table_name,
                primary_keys=["Date", "Ticker", "variable"],
                verbose=verbose,
            )

            if verbose:
                print(
                    f"\n✅ {'増分更新' if is_incremental else '初期保存'}完了: {rows_saved:,}行"
                )

            return rows_saved

        except Exception as e:
            print(f"\n❌ エラー発生: {e}")
            import traceback

            traceback.print_exc()
            return 0

    # --------------------------------------------------------------------------
    def get_index_members(self, verbose: bool = True) -> list[str]:
        """
        S&P 500 インデックスの構成銘柄を取得
        :param verbose: ログ出力の有効/無効
        :return: 構成銘柄のTickerリスト
        """
        session = self._create_session(verbose=verbose)
        if not session:
            return []

        try:
            # サービスを開く
            if not session.openService(self.REF_DATA_SERVICE):
                print("❌ サービスのオープンに失敗しました。")
                session.stop()
                return []

            refDataService = session.getService(self.REF_DATA_SERVICE)
            request = refDataService.createRequest("ReferenceDataRequest")

            # S&P 500のインデックスティッカー
            request.append("securities", "SPX Index")
            request.append("fields", "INDX_MEMBERS")

            if verbose:
                print("📡 S&P 500構成銘柄をリクエスト中...")
            session.sendRequest(request)

            members = []

            # イベントループ
            while True:
                event = session.nextEvent(5000)

                if (
                    event.eventType() == blpapi.Event.RESPONSE
                    or event.eventType() == blpapi.Event.PARTIAL_RESPONSE
                ):
                    for msg in event:
                        if msg.hasElement("responseError"):
                            print(
                                f"❌ レスポンスエラー: {msg.getElement('responseError')}"
                            )
                            continue

                        securityDataArray = msg.getElement("securityData")

                        for securityData in securityDataArray.values():
                            # セキュリティエラーチェック
                            if securityData.hasElement("securityError"):
                                print(
                                    f"❌ セキュリティエラー: {securityData.getElement('securityError')}"
                                )
                                continue

                            # フィールドデータ取得
                            fieldData = securityData.getElement("fieldData")

                            if fieldData.hasElement("INDX_MEMBERS"):
                                membersElement = fieldData.getElement("INDX_MEMBERS")

                                # 各構成銘柄を取得
                                for i in range(membersElement.numValues()):
                                    memberData = membersElement.getValueAsElement(i)

                                    # ✅ 正しいフィールド名を使用
                                    if memberData.hasElement(
                                        "Member Ticker and Exchange Code"
                                    ):
                                        ticker = memberData.getElementAsString(
                                            "Member Ticker and Exchange Code"
                                        )
                                        members.append(ticker)

                if event.eventType() == blpapi.Event.RESPONSE:
                    break

            session.stop()
            if verbose:
                print(f"✅ {len(members)}銘柄を取得しました。")
            return members

        except Exception as e:
            print(f"❌ エラーが発生しました: {e}")
            import traceback

            traceback.print_exc()
            return []

    # --------------------------------------------------------------------------
    def get_field_info(
        self,
        fields: list[str],
        verbose: bool = True,
    ) -> pd.DataFrame:
        """
        フィールドIDの詳細情報（説明、データ型など）を取得します。

        :param fields: フィールドIDのリスト (例: ['PX_LAST', 'PE_RATIO'])
        :param verbose: ログ出力の有効/無効
        :return: DataFrame with columns: Field, Mnemonic, Description, Datatype
        """
        session = self._create_session(verbose=verbose)
        if not session:
            return pd.DataFrame()

        apiflds_service = "//blp/apiflds"
        if not session.openService(apiflds_service):
            print(f"❌ サービス '{apiflds_service}' のオープンに失敗しました。")
            session.stop()
            return pd.DataFrame()

        field_info_service = session.getService(apiflds_service)
        if verbose:
            print("✅ API Fieldサービスオープン完了。リクエスト作成中...")

        request = field_info_service.createRequest("FieldInfoRequest")
        for field in fields:
            request.append("id", field)

        if verbose:
            print(
                f"📡 フィールド情報リクエストを送信します (フィールド数: {len(fields)})..."
            )
        session.sendRequest(request)

        data_list = []

        while True:
            event = session.nextEvent(5000)
            if (
                event.eventType() == blpapi.Event.RESPONSE
                or event.eventType() == blpapi.Event.PARTIAL_RESPONSE
            ):
                for msg in event:
                    if msg.hasElement("fieldData"):
                        field_data_array = msg.getElement("fieldData")
                        for i in range(field_data_array.numValues()):
                            field_data = field_data_array.getValueAsElement(i)
                            field_info = {
                                "Field": field_data.getElementAsString("id"),
                                "Mnemonic": (
                                    field_data.getElementAsString("mnemonic")
                                    if field_data.hasElement("mnemonic")
                                    else None
                                ),
                                "Description": (
                                    field_data.getElementAsString("description")
                                    if field_data.hasElement("description")
                                    else None
                                ),
                                "Datatype": (
                                    field_data.getElementAsString("datatype")
                                    if field_data.hasElement("datatype")
                                    else None
                                ),
                            }
                            data_list.append(field_info)

                    if msg.hasElement("fieldError"):
                        error_element = msg.getElement("fieldError")
                        # fieldError might be an array or single element depending on request structure
                        # Usually FieldInfoRequest returns fieldData array, and potentially fieldError for specific IDs?
                        # Let's assume fieldError is at message level if request failed entirely,
                        # or inside fieldData if partial.
                        # Actually, for FieldInfoRequest, invalid IDs often result in a fieldData entry with error info or just missing data.
                        # But if there's a top level error:
                        print(f"❌ フィールドエラー: {error_element}")

            if event.eventType() == blpapi.Event.RESPONSE:
                break
            elif event.eventType() == blpapi.Event.TIMEOUT:
                if verbose:
                    print("⏳ タイムアウトしました。")
                break

        session.stop()
        if verbose:
            print(f"✅ {len(data_list)}件のフィールド情報を取得しました。")

        if not data_list:
            return pd.DataFrame()

        return pd.DataFrame(data_list)

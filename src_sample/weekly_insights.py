"""
weekly_insights.py

週次レポートのための定量的インサイト生成モジュール。
- ファクター分析
- マクロ感応度分析 (カルマンフィルタ)
- バリュエーション履歴分析
- 全SEC銘柄のデータ収集・蓄積
"""

import datetime
import sqlite3
import time
from pathlib import Path

import pandas as pd
import requests
import yfinance as yf

# 統計・分析ライブラリ

# pykalmanは標準ではないため、なければ警告を出してスキップするか、簡易実装にする
try:
    from pykalman import KalmanFilter

    HAS_KALMAN = True
except ImportError:
    HAS_KALMAN = False
    print(
        "Warning: pykalman not found. Advanced Beta analysis will be skipped or simplified."
    )

# ローカルモジュール
from database_utils import append_diff_to_sqlite


class WeeklyInsightGenerator:
    def __init__(self):
        self.data_dir = Path(__file__).parent.parent / "data"
        self.market_db_path = self.data_dir / "Market_Data.db"
        self.valuation_db_path = self.data_dir / "Valuation_History.db"
        self.fred_db_path = self.data_dir / "FRED" / "FRED.db"

        # 定数
        self.FACTOR_TICKERS = {
            "Growth": "VUG",
            "Value": "VTV",
            "Quality": "QUAL",
            "Momentum": "MTUM",
            "LowVol": "USMV",
            "SmallCap": "IWM",
            "Market": "SPY",  # ベンチマーク
        }

        self.MACRO_TICKERS = {
            "10Y_Yield": "DGS10",  # FRED
            "USD_Index": "DTWEXBGS",  # FRED
            "Oil": "DCOILWTICO",  # FRED
        }

    # ==================================================================================
    # 1. データ収集・保存 (Data Collection & Storage)
    # ==================================================================================

    def get_sec_tickers(self) -> list[str]:
        """
        SEC公式JSONから全上場企業のティッカーリストを取得する。
        """
        url = "https://www.sec.gov/files/company_tickers.json"
        headers = {
            "User-Agent": "Mozilla/5.0 (Company Name; Contact Information)"
        }  # SEC requires User-Agent

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()

            # dataは辞書形式: {"0": {"cik_str": 320193, "ticker": "AAPL", "title": "Apple Inc."}, ...}
            tickers = [item["ticker"] for item in data.values()]
            print(f"Fetched {len(tickers)} tickers from SEC.")
            return tickers
        except Exception as e:
            print(f"Error fetching SEC tickers: {e}")
            # フォールバック: 主要銘柄のみ返すか、空リスト
            return ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA"]

    def update_databases(self, full_update=False):
        """
        データベースを更新する。
        full_update=Trueの場合、全SEC銘柄のバリュエーション取得を試みる（時間がかかる）。
        Falseの場合、主要銘柄のみ更新。
        """
        print("Updating databases...")

        # 1. ファクター・マクロデータの更新 (Market_Data.db)
        self._update_market_data()

        # 2. バリュエーションデータの更新 (Valuation_History.db)
        if full_update:
            tickers = self.get_sec_tickers()
        else:
            # デフォルトはMag7 + 主要ETF + ダウ
            tickers = list(self.FACTOR_TICKERS.values()) + [
                "AAPL",
                "MSFT",
                "GOOGL",
                "AMZN",
                "NVDA",
                "META",
                "TSLA",
                "^DJI",
            ]

        self._update_valuation_data(tickers)
        print("Database update completed.")

    def _update_market_data(self):
        """ファクターETFの価格データを更新"""
        tickers = list(self.FACTOR_TICKERS.values())
        # yfinanceで一括取得
        data = yf.download(tickers, period="1y", progress=False, auto_adjust=False)

        # Closeデータを整形して保存
        if not data.empty:
            # MultiIndexカラムの場合の処理
            if isinstance(data.columns, pd.MultiIndex):
                close_df = (
                    data["Adj Close"] if "Adj Close" in data.columns else data["Close"]
                )
            else:
                close_df = data

            # 縦持ちに変換 (Date, Ticker, Close)
            melted = close_df.reset_index().melt(
                id_vars="Date", var_name="ticker", value_name="close"
            )
            melted["date"] = melted["Date"].dt.strftime("%Y-%m-%d")
            melted = melted.drop(columns=["Date"]).dropna()

            # 追加保存
            append_diff_to_sqlite(str(self.market_db_path), "price_history", melted)

    def _update_valuation_data(self, tickers: list[str]):
        """
        バリュエーション指標を取得して保存。
        大量のティッカーがある場合、バッチ処理を行う。
        """
        batch_size = 50
        today_str = datetime.date.today().strftime("%Y-%m-%d")

        # 既存データ確認（今日すでに取得済みならスキップするロジックを入れても良い）

        results = []

        # バッチ処理
        for i in range(0, len(tickers), batch_size):
            batch = tickers[i : i + batch_size]
            print(
                f"Fetching valuation data batch {i // batch_size + 1}/{(len(tickers) - 1) // batch_size + 1}..."
            )

            # yfinance.Tickers を使うとマルチスレッドでinfoを取得できるが、不安定なこともある
            # ここではシンプルにループまたはTickerオブジェクトを使用
            # yfinanceのinfo取得は1銘柄ずつAPIを叩くため遅い。
            # 効率化のため、Tickerオブジェクトを一括生成

            # 注意: yf.Tickers(batch).tickers は辞書。
            # infoへのアクセスはネットワークIOが発生する。

            for ticker_symbol in batch:
                try:
                    ticker = yf.Ticker(ticker_symbol)
                    info = ticker.info

                    # 必要なデータを抽出
                    data = {
                        "date": today_str,
                        "ticker": ticker_symbol,
                        "forward_pe": info.get("forwardPE"),
                        "trailing_pe": info.get("trailingPE"),
                        "peg_ratio": info.get("pegRatio"),
                        "price_to_book": info.get("priceToBook"),
                        "enterprise_value": info.get("enterpriseValue"),
                        "enterprise_to_ebitda": info.get("enterpriseToEbitda"),
                        "profit_margins": info.get("profitMargins"),
                    }

                    # 少なくとも1つ有効なデータがあれば追加
                    if any(
                        v is not None
                        for k, v in data.items()
                        if k not in ["date", "ticker"]
                    ):
                        results.append(data)

                except Exception as e:
                    # 個別のエラーは無視して次へ
                    continue

            # レート制限回避のための待機
            time.sleep(1)

            # ある程度たまったらDBに書き込む（メモリ節約）
            if len(results) >= 100:
                df = pd.DataFrame(results)
                append_diff_to_sqlite(
                    str(self.valuation_db_path), "valuation_snapshot", df
                )
                results = []

        # 残りを保存
        if results:
            df = pd.DataFrame(results)
            append_diff_to_sqlite(str(self.valuation_db_path), "valuation_snapshot", df)

    # ==================================================================================
    # 2. 分析ロジック (Analysis Logic)
    # ==================================================================================

    def analyze_factors(self, period_days=5) -> dict:
        """
        ファクターETFのパフォーマンス分析
        """
        conn = sqlite3.connect(self.market_db_path)
        query = "SELECT * FROM price_history ORDER BY date"
        df = pd.read_sql(query, conn)
        conn.close()

        if df.empty:
            return {}

        # ピボット
        pivoted = df.pivot(index="date", columns="ticker", values="close")

        # リターン計算
        if len(pivoted) < period_days + 1:
            return {}

        current = pivoted.iloc[-1]
        prev = pivoted.iloc[-(period_days + 1)]
        returns = ((current / prev) - 1) * 100

        # SPYとのスプレッド
        spy_ret = returns.get(self.FACTOR_TICKERS["Market"], 0)

        result = []
        for name, ticker in self.FACTOR_TICKERS.items():
            if ticker == self.FACTOR_TICKERS["Market"]:
                continue

            ret = returns.get(ticker)
            if ret is not None:
                spread = ret - spy_ret
                result.append(
                    {
                        "factor": name,
                        "ticker": ticker,
                        "return": round(ret, 2),
                        "spread": round(spread, 2),
                    }
                )

        # スプレッド順にソート
        result.sort(key=lambda x: x["spread"], reverse=True)
        return {"factors": result, "market_return": round(spy_ret, 2)}

    def analyze_macro_sensitivity(
        self, target_ticker="XLK", window_short=20, window_long=252
    ) -> dict:
        """
        マクロ感応度分析（相関 + カルマンフィルタベータ）
        デフォルトはテクノロジーセクター(XLK) vs 10年債(DGS10)などを想定
        """
        # データの準備 (Market_Data.dbから取得するか、FRED.dbと結合するか)
        # ここでは簡易的に、Market_Data.dbにマクロデータも入っている前提、または別途取得
        # 実装簡略化のため、yfinanceでオンデマンド取得して計算する形をとる

        # ターゲット（セクター）とマクロ指標（金利）
        tickers = [target_ticker, "^TNX"]  # ^TNX is 10-Year Yield * 10
        data = yf.download(tickers, period="2y", progress=False, auto_adjust=False)[
            "Adj Close"
        ]

        if data.empty or len(data) < window_long:
            return {}

        # 前日比リターン
        returns = data.pct_change().dropna()

        # 相関分析
        corr_short = (
            returns[target_ticker]
            .rolling(window=window_short)
            .corr(returns["^TNX"])
            .iloc[-1]
        )
        corr_long = (
            returns[target_ticker]
            .rolling(window=window_long)
            .corr(returns["^TNX"])
            .iloc[-1]
        )

        result = {
            "correlation": {"short": round(corr_short, 2), "long": round(corr_long, 2)}
        }

        # カルマンフィルタによる時変ベータ
        if HAS_KALMAN:
            # 観測値: セクターリターン, 状態変数: ベータ
            # y_t = beta_t * x_t + epsilon_t
            # beta_t = beta_{t-1} + zeta_t

            y = returns[target_ticker].values
            x = returns["^TNX"].values

            # 状態空間モデルの構築
            # Transition Matrix = 1 (ランダムウォーク)
            # Observation Matrix = x_t

            kf = KalmanFilter(
                transition_matrices=[1],
                observation_matrices=x.reshape(-1, 1, 1),
                initial_state_mean=0,
                initial_state_covariance=1,
                observation_covariance=1,
                transition_covariance=0.01,
            )

            state_means, _ = kf.filter(y)
            current_beta = state_means[-1][0]

            result["beta_kalman"] = round(current_beta, 2)

        return result

    def get_valuation_context(self, tickers: list[str]) -> dict:
        """
        バリュエーション履歴の分析
        """
        conn = sqlite3.connect(self.valuation_db_path)
        placeholders = ",".join(["?"] * len(tickers))
        query = f"SELECT * FROM valuation_snapshot WHERE ticker IN ({placeholders}) ORDER BY date"
        df = pd.read_sql(query, conn, params=tickers)
        conn.close()

        if df.empty:
            return {}

        result = {}
        for ticker in tickers:
            sub_df = df[df["ticker"] == ticker]
            if sub_df.empty:
                continue

            current = sub_df.iloc[-1]

            # 履歴があればパーセンタイル計算
            if len(sub_df) > 10:
                pe_history = sub_df["forward_pe"].dropna()
                if not pe_history.empty:
                    curr_pe = current["forward_pe"]
                    if curr_pe:
                        rank = (pe_history < curr_pe).mean() * 100
                        result[ticker] = {
                            "forward_pe": round(curr_pe, 2),
                            "percentile": round(rank, 1),
                            "samples": len(pe_history),
                        }
            else:
                # データ不足時は現在値のみ
                result[ticker] = {
                    "forward_pe": current["forward_pe"],
                    "percentile": None,
                }

        return result


if __name__ == "__main__":
    # テスト実行
    generator = WeeklyInsightGenerator()
    # generator.update_databases(full_update=False) # 時間がかかるのでコメントアウト
    print(generator.analyze_factors())
    print(generator.analyze_macro_sensitivity())

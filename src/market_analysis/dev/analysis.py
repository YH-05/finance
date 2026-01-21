import datetime

import curl_cffi
import pandas as pd
import yfinance as yf
from pandas import DataFrame
from rich.console import Console

from src.market_analysis.dev import data_fetch


class MagnificentSevenAnalyzer:
    """マグニフィセント7銘柄とSOX Indexを分析するクラス"""

    def __init__(self):
        self.today = datetime.datetime.today()
        self.mag7_tickers: list[str] = [
            "AAPL",
            "MSFT",
            "NVDA",
            "GOOGL",
            "AMZN",
            "TSLA",
            "META",
        ]

    def get_performance(self, performance_period: str = "5d") -> DataFrame:
        yf_fethcer = data_fetch.YfinanceFethcer()
        performance_mag7: DataFrame = yf_fethcer.get_performance(
            tickers=self.mag7_tickers
        ).sort_values(performance_period, ascending=False)

        return performance_mag7


class SectorAnalyzer:
    """S&P500 セクターETFのパフォーマンスを分析するクラス"""

    def __init__(self):
        self.sector_etf_tickers: list[str] = [
            "XLY",  # Consumer Discretionary
            "XLP",  # Consumer Staples
            "XLE",  # Energy
            "XLF",  # Financials
            "XLV",  # Health Care
            "XLI",  # Industrials
            "XLK",  # Information Technology
            "XLB",  # Materials
            "XLU",  # Utilities
            "XLC",  # Communication Services
            "XLRE",  # Real Estate
        ]
        self.sector_map_en = {
            "XLY": "Consumer Discretionary",
            "XLP": "Consumer Staples",
            "XLE": "Energy",
            "XLF": "Financials",
            "XLV": "Health Care",
            "XLI": "Industrials",
            "XLK": "Information Technology",
            "XLB": "Materials",
            "XLU": "Utilities",
            "XLC": "Communication Services",
            "XLRE": "Real Estate",
        }

    def get_top_bottom_sectors(self, performance_period: str = "5d") -> dict:
        """S&P500 セクターETFの1週間パフォーマンスに基づき上位/下位3セクターを抽出する"""
        yf_fethcer = data_fetch.YfinanceFethcer()
        performance_sector = (
            yf_fethcer.get_performance(tickers=self.sector_etf_tickers)
            .sort_values(performance_period, ascending=False)
            .rename(index=self.sector_map_en)
        )
        performance_sector_top_bottom: dict = performance_sector.iloc[
            [0, 1, 2, -3, -2, -1]
        ][performance_period].to_dict()

        return performance_sector_top_bottom


class TopCompaniesAnalyzer:
    """yfinanceで独自定義されているセクターのtop companiesを分析するクラス"""

    def __init__(self):
        self.session = curl_cffi.requests.Session(impersonate="safari15_5")
        self.sectors: list[str] = [
            "basic-materials",
            "industrials",
            "communication-services",
            "healthcare",
            "real-estate",
            "technology",
            "energy",
            "utilities",
            "financial-services",
            "consumer-defensive",
            "consumer-cyclical",
        ]

    def get_sector_top_companies(self, sector: str) -> DataFrame:
        """特定のセクターのtop companiesのDataFrameを取得する"""
        top_companies: DataFrame = yf.Sector(
            sector, session=self.session
        ).top_companies  # ty:ignore[invalid-assignment]
        top_companies["Sector"] = sector
        return top_companies

    def get_all_sectors_top_companies(self) -> DataFrame:
        """すべてのセクターのtop companiesのDataFrameを取得する"""
        top_companies = []
        for sector in self.sectors:
            top_companies.append(self.get_sector_top_companies(sector))
        top_companies = pd.concat(top_companies)
        return top_companies


def main():
    console = Console()
    top_companies_analyzer = TopCompaniesAnalyzer()
    console.print(top_companies_analyzer.get_all_sectors_top_companies())


if __name__ == "__main__":
    main()

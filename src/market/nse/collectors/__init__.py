"""NSE data collector implementations.

This subpackage contains collector classes for various NSE data
endpoints (equity quotes, index constituents, corporate data,
stock list CSV, pre-open session data).

Public API
----------
CorporateCollector
    Collector for NSE corporate data (financial results, event calendar,
    symbol search).  Does not inherit from DataCollector as it returns
    heterogeneous types.
IndicesCollector
    Collector for NSE index constituent data, all-indices summary,
    and market status.
QuoteCollector
    Collector for NSE equity quote data.
StockListCollector
    Collector for NSE equity stock list (EQUITY_L.csv), pre-open
    session data, and market turnover.
"""

from market.nse.collectors.corporate import CorporateCollector
from market.nse.collectors.indices import IndicesCollector
from market.nse.collectors.quote import QuoteCollector
from market.nse.collectors.stock_list import StockListCollector

__all__ = [
    "CorporateCollector",
    "IndicesCollector",
    "QuoteCollector",
    "StockListCollector",
]

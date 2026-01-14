"""
edgar_utils.py
"""

from edgar import *


# ===================================================================
def get_filings_single_ticker(
    ticker: str, form_type: str, start_date: str, end_date: str
):
    """
    指定された企業のEDGARから特定のフォームタイプの提出書類を取得する。

    Parameters
    ----------
    ticker : str
        企業のティッカーシンボル
    form_type : str
        取得するフォームタイプ（例: "10-K", "10-Q", "8-K"）
    start_date : str
        取得開始日（YYYY-MM-DD形式）
    end_date : str
        取得終了日（YYYY-MM-DD形式）

    Returns
    -------
    filings
        取得された提出書類オブジェクト
    """
    company = Company(ticker)
    filings = company.get_filings(form=form_type).filter(
        date=f"{start_date}:{end_date}"
    )
    return filings


# ===================================================================

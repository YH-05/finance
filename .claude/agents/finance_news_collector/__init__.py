"""Finance news collector module.

金融ニュース収集のためのフィルタリングおよびデータ変換機能を提供します。
"""

from .filtering import (
    is_excluded,
    matches_financial_keywords,
)
from .transformation import convert_to_issue_format

__all__ = [
    "convert_to_issue_format",
    "is_excluded",
    "matches_financial_keywords",
]

"""Type definitions for the edgar package.

This module provides type definitions for SEC EDGAR filing data including:
- Filing type classifications (10-K, 10-Q, 13F)
- Section key identifiers for filing sections
- Result dataclass for filing extraction results
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from utils_core.logging import get_logger

logger = get_logger(__name__)


class FilingType(str, Enum):
    """SEC filing form types.

    Attributes
    ----------
    FORM_10K : str
        Annual report (10-K)
    FORM_10Q : str
        Quarterly report (10-Q)
    FORM_13F : str
        Institutional investment manager report (13F)
    """

    FORM_10K = "10-K"
    FORM_10Q = "10-Q"
    FORM_13F = "13F"

    @classmethod
    def from_string(cls, form: str) -> "FilingType":
        """Convert a form type string to FilingType enum.

        Parameters
        ----------
        form : str
            The filing form type string (e.g., "10-K", "10-Q", "13F")

        Returns
        -------
        FilingType
            The corresponding FilingType enum value

        Raises
        ------
        ValueError
            If the form type string is not supported

        Examples
        --------
        >>> FilingType.from_string("10-K")
        <FilingType.FORM_10K: '10-K'>
        >>> FilingType.from_string("10-Q")
        <FilingType.FORM_10Q: '10-Q'>
        """
        for filing_type in cls:
            if filing_type.value == form:
                logger.debug(
                    "Converted form string to FilingType",
                    form=form,
                    filing_type=filing_type.name,
                )
                return filing_type

        supported = [ft.value for ft in cls]
        msg = f"Unsupported filing type: '{form}'. Supported types: {supported}"
        raise ValueError(msg)


class SectionKey(str, Enum):
    """Section identifiers for SEC filing sections.

    Attributes
    ----------
    ITEM_1 : str
        Business description
    ITEM_1A : str
        Risk factors
    ITEM_7 : str
        Management's discussion and analysis (MD&A)
    ITEM_8 : str
        Financial statements and supplementary data
    """

    ITEM_1 = "item_1"
    ITEM_1A = "item_1a"
    ITEM_7 = "item_7"
    ITEM_8 = "item_8"


@dataclass
class EdgarResult:
    """Result of an EDGAR filing extraction operation.

    Parameters
    ----------
    filing_id : str
        The unique filing identifier (accession number)
    text : str
        The full text content of the filing
    sections : dict[SectionKey, str]
        Extracted sections mapped by section key
    metadata : dict[str, Any]
        Additional metadata about the filing

    Examples
    --------
    >>> result = EdgarResult(
    ...     filing_id="0001234567-24-000001",
    ...     text="Full filing text content",
    ...     sections={SectionKey.ITEM_1: "Business section text"},
    ...     metadata={"company": "Example Corp"},
    ... )
    """

    filing_id: str
    text: str
    sections: dict[SectionKey, str] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


__all__ = [
    "EdgarResult",
    "FilingType",
    "SectionKey",
]

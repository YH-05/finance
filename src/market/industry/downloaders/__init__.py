"""PDF download and text extraction subpackage for industry reports.

This package provides tools for downloading PDF reports and extracting
text content from PDF and HTML documents.

Modules
-------
pdf_downloader : PDF download with size limiting and deduplication.
report_parser : PDF/HTML text extraction and metadata extraction.

Public API
----------
PDFDownloader
    Async PDF downloader with size limits and hash-based deduplication.
ReportParser
    Parser for extracting text and metadata from PDF and HTML documents.
"""

from market.industry.downloaders.pdf_downloader import PDFDownloader
from market.industry.downloaders.report_parser import ReportParser

__all__ = ["PDFDownloader", "ReportParser"]

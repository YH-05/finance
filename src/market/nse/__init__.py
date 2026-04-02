"""NSE (National Stock Exchange of India) data retrieval module.

This package provides tools for fetching market data from the
NSE India website (https://www.nseindia.com).

NSE uses a cookie-based session mechanism: a valid session cookie must be
obtained by visiting the home page before any API call is made.

Modules
-------
constants : API URLs, headers, and configuration defaults.
errors : Exception hierarchy for NSE API operations.
types : Configuration dataclasses, Enums, and data record types.

Public API
----------
NseConfig
    Configuration for NSE API HTTP behaviour.
RetryConfig
    Configuration for retry behaviour with exponential backoff.

Enums
-----
NseIndex
    Major NSE index identifiers.

Error Classes
-------------
NseError
    Base exception for all NSE API operations.
NseAPIError
    Exception for HTTP 4xx/5xx error responses.
NseRateLimitError
    Exception for rate limit (HTTP 429) responses.
NseCookieError
    Exception for expired/invalid NSE session cookies.
NseParseError
    Exception for response parsing failures.
NseValidationError
    Exception for data validation failures.
"""

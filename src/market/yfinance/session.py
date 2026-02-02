"""HTTP session abstraction for market.yfinance module.

This module provides the HttpSessionProtocol interface for abstracting
HTTP session objects used by the yfinance module. This enables dependency
injection and testability by allowing mock sessions to be used in tests.

Examples
--------
>>> class RequestsSession:
...     def __init__(self):
...         import requests
...         self._session = requests.Session()
...
...     def get(self, url: str, **kwargs) -> Any:
...         return self._session.get(url, **kwargs)
...
...     def close(self) -> None:
...         self._session.close()
...
>>> session: HttpSessionProtocol = RequestsSession()
>>> response = session.get("https://api.example.com/data")
>>> session.close()
"""

from typing import Any, Protocol

import requests
from curl_cffi import requests as curl_requests
from curl_cffi.requests import BrowserTypeLiteral


class HttpSessionProtocol(Protocol):
    """Protocol defining the interface for HTTP session objects.

    This protocol defines the minimal interface required for HTTP session
    objects used by the yfinance module. Any class that implements the
    `get` and `close` methods with the correct signatures will satisfy
    this protocol.

    The protocol is designed to be compatible with common HTTP libraries
    such as `requests`, `httpx`, and `curl_cffi`.

    Methods
    -------
    get(url: str, **kwargs) -> Any
        Send a GET request to the specified URL.
    close() -> None
        Close the session and release resources.

    Notes
    -----
    This is a structural subtyping protocol (PEP 544). Classes do not need
    to explicitly inherit from this protocol; they only need to implement
    the required methods with compatible signatures.

    Examples
    --------
    Using with requests library:

    >>> import requests
    >>> class RequestsAdapter:
    ...     def __init__(self):
    ...         self._session = requests.Session()
    ...
    ...     def get(self, url: str, **kwargs) -> Any:
    ...         return self._session.get(url, **kwargs)
    ...
    ...     def close(self) -> None:
    ...         self._session.close()
    ...
    >>> session: HttpSessionProtocol = RequestsAdapter()

    Using with curl_cffi library:

    >>> from curl_cffi import requests as curl_requests
    >>> class CurlAdapter:
    ...     def __init__(self):
    ...         self._session = curl_requests.Session()
    ...
    ...     def get(self, url: str, **kwargs) -> Any:
    ...         return self._session.get(url, **kwargs)
    ...
    ...     def close(self) -> None:
    ...         self._session.close()
    ...
    >>> session: HttpSessionProtocol = CurlAdapter()
    """

    def get(self, url: str, **kwargs: Any) -> Any:
        """Send a GET request to the specified URL.

        Parameters
        ----------
        url : str
            The URL to send the GET request to.
        **kwargs : Any
            Additional keyword arguments passed to the underlying HTTP client.
            Common options include:
            - headers: dict[str, str] - HTTP headers
            - params: dict[str, Any] - URL query parameters
            - timeout: float | tuple[float, float] - Request timeout
            - verify: bool - SSL certificate verification

        Returns
        -------
        Any
            The response object from the underlying HTTP client.
            The exact type depends on the implementation.

        Raises
        ------
        Exception
            Implementation-specific exceptions may be raised for network
            errors, timeouts, or other HTTP-related issues.

        Examples
        --------
        >>> response = session.get("https://api.example.com/data")
        >>> response = session.get(
        ...     "https://api.example.com/data",
        ...     headers={"User-Agent": "MyApp/1.0"},
        ...     timeout=30.0,
        ... )
        """
        ...

    def close(self) -> None:
        """Close the session and release resources.

        This method should be called when the session is no longer needed
        to properly release any held resources such as network connections.

        Returns
        -------
        None

        Examples
        --------
        >>> session.close()

        Using as a context manager pattern:

        >>> try:
        ...     response = session.get("https://api.example.com/data")
        ... finally:
        ...     session.close()
        """
        ...


class CurlCffiSession:
    """High-performance HTTP session using curl_cffi with browser impersonation.

    This class wraps curl_cffi.Session to provide a fast HTTP client that
    impersonates real browser TLS fingerprints, helping to bypass rate
    limiting on services like Yahoo Finance.

    Implements HttpSessionProtocol for compatibility with code expecting
    a standard HTTP session interface.

    Parameters
    ----------
    impersonate : BrowserTypeLiteral, optional
        Browser to impersonate for TLS fingerprinting. Options include:
        "chrome", "chrome110", "chrome120", "edge99", "safari15_3".
        Defaults to "chrome".

    Attributes
    ----------
    _session : curl_requests.Session
        The underlying curl_cffi session instance.
    _impersonate : BrowserTypeLiteral
        The browser type being impersonated.

    Examples
    --------
    Basic usage:

    >>> session = CurlCffiSession()
    >>> response = session.get("https://api.example.com/data")
    >>> session.close()

    With custom impersonation:

    >>> session = CurlCffiSession(impersonate="safari15_3")
    >>> response = session.get("https://api.example.com/data")
    >>> session.close()

    Using as a context manager:

    >>> with CurlCffiSession() as session:
    ...     response = session.get("https://api.example.com/data")
    """

    def __init__(self, impersonate: BrowserTypeLiteral = "chrome") -> None:
        """Initialize a new CurlCffiSession.

        Parameters
        ----------
        impersonate : BrowserTypeLiteral, optional
            Browser to impersonate for TLS fingerprinting.
            Defaults to "chrome".
        """
        self._impersonate: BrowserTypeLiteral = impersonate
        self._session: curl_requests.Session = curl_requests.Session(
            impersonate=impersonate
        )

    def get(self, url: str, **kwargs: Any) -> Any:
        """Send a GET request to the specified URL.

        Parameters
        ----------
        url : str
            The URL to send the GET request to.
        **kwargs : Any
            Additional keyword arguments passed to the underlying HTTP client.
            Common options include:
            - headers: dict[str, str] - HTTP headers
            - params: dict[str, Any] - URL query parameters
            - timeout: float | tuple[float, float] - Request timeout
            - verify: bool - SSL certificate verification

        Returns
        -------
        Any
            The response object from curl_cffi.

        Examples
        --------
        >>> response = session.get("https://api.example.com/data")
        >>> response = session.get(
        ...     "https://api.example.com/data",
        ...     headers={"User-Agent": "MyApp/1.0"},
        ...     timeout=30.0,
        ... )
        """
        return self._session.get(url, **kwargs)

    def close(self) -> None:
        """Close the session and release resources.

        This method should be called when the session is no longer needed
        to properly release any held resources such as network connections.

        Examples
        --------
        >>> session.close()
        """
        self._session.close()

    def __enter__(self) -> "CurlCffiSession":
        """Support context manager protocol.

        Returns
        -------
        CurlCffiSession
            Self for use in with statement.
        """
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        """Close session on context exit.

        Parameters
        ----------
        exc_type : type[BaseException] | None
            Exception type if an exception was raised.
        exc_val : BaseException | None
            Exception instance if an exception was raised.
        exc_tb : Any
            Traceback if an exception was raised.
        """
        self.close()


class StandardRequestsSession:
    """Standard HTTP session using the requests library.

    This class wraps requests.Session to provide a standard HTTP client
    for making HTTP requests. It implements HttpSessionProtocol for
    compatibility with code expecting a common HTTP session interface.

    Attributes
    ----------
    _session : requests.Session
        The underlying requests session instance.

    Examples
    --------
    Basic usage:

    >>> session = StandardRequestsSession()
    >>> response = session.get("https://api.example.com/data")
    >>> session.close()

    Using as a context manager:

    >>> with StandardRequestsSession() as session:
    ...     response = session.get("https://api.example.com/data")
    """

    def __init__(self) -> None:
        """Initialize a new StandardRequestsSession.

        Creates a new requests.Session instance for making HTTP requests.
        """
        self._session: requests.Session = requests.Session()

    def get(self, url: str, **kwargs: Any) -> Any:
        """Send a GET request to the specified URL.

        Parameters
        ----------
        url : str
            The URL to send the GET request to.
        **kwargs : Any
            Additional keyword arguments passed to the underlying HTTP client.
            Common options include:
            - headers: dict[str, str] - HTTP headers
            - params: dict[str, Any] - URL query parameters
            - timeout: float | tuple[float, float] - Request timeout
            - verify: bool - SSL certificate verification

        Returns
        -------
        Any
            The response object from requests.

        Examples
        --------
        >>> response = session.get("https://api.example.com/data")
        >>> response = session.get(
        ...     "https://api.example.com/data",
        ...     headers={"User-Agent": "MyApp/1.0"},
        ...     timeout=30.0,
        ... )
        """
        return self._session.get(url, **kwargs)

    def close(self) -> None:
        """Close the session and release resources.

        This method should be called when the session is no longer needed
        to properly release any held resources such as network connections.

        Examples
        --------
        >>> session.close()
        """
        self._session.close()

    def __enter__(self) -> "StandardRequestsSession":
        """Support context manager protocol.

        Returns
        -------
        StandardRequestsSession
            Self for use in with statement.
        """
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        """Close session on context exit.

        Parameters
        ----------
        exc_type : type[BaseException] | None
            Exception type if an exception was raised.
        exc_val : BaseException | None
            Exception instance if an exception was raised.
        exc_tb : Any
            Traceback if an exception was raised.
        """
        self.close()


__all__ = ["CurlCffiSession", "HttpSessionProtocol", "StandardRequestsSession"]

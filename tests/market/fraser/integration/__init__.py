"""Integration tests for the ``market.fraser`` package.

These tests exercise the real FRASER REST API and require the
``FRASER_API_KEY`` environment variable to be set. They are tagged with
``pytest.mark.integration`` so that the default ``make test`` run skips
them.

See Also
--------
tests.market.alphavantage.integration : Reference layout for live API
    integration tests.
"""

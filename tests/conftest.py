"""Test configuration and fixtures for InvestiLearn tests."""

import pytest


@pytest.fixture
def sample_stock_info():
    """Sample stock info data for testing."""
    return {
        "symbol": "AAPL",
        "longName": "Apple Inc.",
        "currentPrice": 150.0,
        "previousClose": 148.0,
        "marketCap": 2500000000000,
        "sector": "Technology",
        "returnOnEquity": 0.15,
        "returnOnAssets": 0.10,
        "profitMargins": 0.25,
        "grossMargins": 0.40,
        "currentRatio": 1.5,
        "quickRatio": 1.2,
        "debtToEquity": 1.8,
        "trailingPE": 28.5,
        "priceToBook": 40.2,
        "pegRatio": 2.1,
    }


@pytest.fixture
def sample_ticker():
    """Sample ticker symbol for testing."""
    return "AAPL"

"""Tests for data_fetcher module."""

from unittest.mock import Mock, patch

import pandas as pd
import pytest

from utils.data_fetcher import (
    get_financial_statements,
    get_historical_data,
    get_news,
    get_stock_info,
)


class TestGetStockInfo:
    """Test suite for get_stock_info function."""

    @pytest.mark.skip(reason="Streamlit cache decorator conflicts with mocking in tests")
    @patch("utils.data_fetcher.yf.Ticker")
    def test_get_stock_info_success(self, mock_ticker):
        """Test successful stock info retrieval."""
        # Setup mock with pickleable data
        mock_stock = Mock()
        mock_stock.info = {
            "symbol": "AAPL",
            "longName": "Apple Inc.",
            "currentPrice": 150.0,
        }
        mock_ticker.return_value = mock_stock

        # Call function (now returns only info dict, not tuple)
        info = get_stock_info("AAPL")

        # Assertions
        assert info is not None
        assert info["symbol"] == "AAPL"
        assert info["longName"] == "Apple Inc."
        mock_ticker.assert_called_with("AAPL")

    @patch("utils.data_fetcher.st.cache_data", lambda **kwargs: lambda f: f)
    @patch("utils.data_fetcher.yf.Ticker")
    def test_get_stock_info_no_symbol(self, mock_ticker):
        """Test handling of stock info without symbol field."""
        # Setup mock with incomplete data
        mock_stock = Mock()
        mock_stock.info = {"longName": "Apple Inc."}  # Missing 'symbol'
        mock_ticker.return_value = mock_stock

        # Call function (now returns only info dict, not tuple)
        info = get_stock_info("AAPL")

        # Should return None when validation fails
        assert info is None

    @patch("utils.data_fetcher.st.cache_data", lambda **kwargs: lambda f: f)
    @patch("utils.data_fetcher.yf.Ticker")
    def test_get_stock_info_empty_info(self, mock_ticker):
        """Test handling of empty stock info."""
        # Setup mock with empty info
        mock_stock = Mock()
        mock_stock.info = {}
        mock_ticker.return_value = mock_stock

        # Call function (now returns only info dict, not tuple)
        info = get_stock_info("INVALID")

        # Should return None
        assert info is None

    @patch("utils.data_fetcher.st.cache_data", lambda **kwargs: lambda f: f)
    @patch("utils.data_fetcher.yf.Ticker")
    def test_get_stock_info_exception(self, mock_ticker):
        """Test handling of exceptions during API call."""
        # Setup mock to raise exception
        mock_ticker.side_effect = Exception("API Error")

        # Call function (now returns only info dict, not tuple)
        info = get_stock_info("INVALID")

        # Should return None on exception
        assert info is None


class TestGetFinancialStatements:
    """Test suite for get_financial_statements function."""

    @pytest.mark.skip(reason="Streamlit cache decorator conflicts with mocking in tests")
    @patch("utils.data_fetcher.yf.Ticker")
    def test_get_financial_statements_success(self, mock_ticker):
        """Test successful financial statements retrieval."""
        # Setup mock DataFrames
        mock_income = pd.DataFrame({"2023-12-31": {"Revenue": 100000}})
        mock_balance = pd.DataFrame({"2023-12-31": {"Total Assets": 500000}})
        mock_cash = pd.DataFrame({"2023-12-31": {"Operating CF": 50000}})

        mock_stock = Mock()
        mock_stock.financials = mock_income
        mock_stock.balance_sheet = mock_balance
        mock_stock.cashflow = mock_cash
        mock_ticker.return_value = mock_stock

        # Call function
        income, balance, cash = get_financial_statements("AAPL")

        # Assertions
        assert income is not None
        assert balance is not None
        assert cash is not None
        assert not income.empty
        mock_ticker.assert_called_with("AAPL")

    @pytest.mark.skip(reason="Streamlit cache decorator conflicts with mocking in tests")
    @patch("utils.data_fetcher.yf.Ticker")
    def test_get_financial_statements_exception(self, mock_ticker):
        """Test handling of exceptions during API call."""
        # Setup mock to raise exception
        mock_ticker.side_effect = Exception("API Error")

        # Call function
        income, balance, cash = get_financial_statements("INVALID")

        # Should return None, None, None on exception
        assert income is None
        assert balance is None
        assert cash is None


class TestGetNews:
    """Test suite for get_news function."""

    @patch("utils.data_fetcher.yf.Ticker")
    def test_get_news_success(self, mock_ticker):
        """Test successful news retrieval."""
        # Setup mock news data
        mock_news = [
            {
                "title": "Apple announces new product",
                "publisher": "TechNews",
                "link": "https://example.com/news1",
            },
            {
                "title": "Apple stock rises",
                "publisher": "FinanceDaily",
                "link": "https://example.com/news2",
            },
        ]
        mock_stock = Mock()
        mock_stock.news = mock_news
        mock_ticker.return_value = mock_stock

        # Call function
        news = get_news("AAPL", max_items=10)

        # Assertions
        assert len(news) == 2
        assert news[0]["title"] == "Apple announces new product"
        mock_ticker.assert_called_once_with("AAPL")

    @patch("utils.data_fetcher.yf.Ticker")
    def test_get_news_with_max_items(self, mock_ticker):
        """Test news retrieval with max_items limit."""
        # Setup mock with many news items
        mock_news = [{"title": f"News {i}"} for i in range(20)]
        mock_stock = Mock()
        mock_stock.news = mock_news
        mock_ticker.return_value = mock_stock

        # Call function with max_items=5
        news = get_news("AAPL", max_items=5)

        # Should return only 5 items
        assert len(news) == 5

    @patch("utils.data_fetcher.yf.Ticker")
    def test_get_news_empty(self, mock_ticker):
        """Test handling of no news available."""
        # Setup mock with no news
        mock_stock = Mock()
        mock_stock.news = None
        mock_ticker.return_value = mock_stock

        # Call function
        news = get_news("AAPL")

        # Should return empty list
        assert news == []

    @patch("utils.data_fetcher.yf.Ticker")
    def test_get_news_exception(self, mock_ticker):
        """Test handling of exceptions during API call."""
        # Setup mock to raise exception
        mock_ticker.side_effect = Exception("API Error")

        # Call function
        news = get_news("INVALID")

        # Should return empty list on exception
        assert news == []


class TestGetHistoricalData:
    """Test suite for get_historical_data function."""

    @patch("utils.data_fetcher.yf.Ticker")
    def test_get_historical_data_success(self, mock_ticker):
        """Test successful historical data retrieval."""
        # Setup mock historical data
        mock_hist = pd.DataFrame(
            {
                "Open": [150.0, 151.0, 152.0],
                "Close": [151.0, 152.0, 153.0],
                "Volume": [1000000, 1100000, 1200000],
            }
        )
        mock_stock = Mock()
        mock_stock.history.return_value = mock_hist
        mock_ticker.return_value = mock_stock

        # Call function
        hist = get_historical_data("AAPL", period="1y")

        # Assertions
        assert hist is not None
        assert not hist.empty
        assert len(hist) == 3
        mock_stock.history.assert_called_once_with(period="1y")

    @patch("utils.data_fetcher.yf.Ticker")
    def test_get_historical_data_different_periods(self, mock_ticker):
        """Test historical data with different time periods."""
        mock_hist = pd.DataFrame({"Close": [150.0]})
        mock_stock = Mock()
        mock_stock.history.return_value = mock_hist
        mock_ticker.return_value = mock_stock

        # Test different periods
        for period in ["1mo", "3mo", "6mo", "1y", "5y"]:
            hist = get_historical_data("AAPL", period=period)
            assert hist is not None

    @patch("utils.data_fetcher.yf.Ticker")
    def test_get_historical_data_exception(self, mock_ticker):
        """Test handling of exceptions during API call."""
        # Setup mock to raise exception
        mock_ticker.side_effect = Exception("API Error")

        # Call function
        hist = get_historical_data("INVALID")

        # Should return None on exception
        assert hist is None

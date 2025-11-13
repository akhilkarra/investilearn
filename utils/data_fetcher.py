"""Data fetching utilities using yfinance"""

import streamlit as st
import yfinance as yf


@st.cache_resource(ttl=3600)  # Cache for 1 hour
def _get_stock_object(ticker):
    """
    Create and cache a yfinance Ticker object

    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL', 'MSFT')

    Returns:
        yf.Ticker object or None on error
    """
    try:
        return yf.Ticker(ticker)
    except Exception as e:
        st.error(f"Error creating ticker object for {ticker}: {str(e)}")
        return None


@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_stock_info(ticker):
    """
    Fetch stock information using yfinance

    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL', 'MSFT')

    Returns:
        dict: Stock info dictionary or None on error
    """
    try:
        stock = _get_stock_object(ticker)
        if stock is None:
            return None

        info = stock.info

        # Validate that we got meaningful data
        if not info or "symbol" not in info:
            st.error(f"No data found for ticker: {ticker}")
            return None

        return info
    except Exception as e:
        st.error(f"Error fetching data for {ticker}: {str(e)}")
        return None


@st.cache_data(ttl=3600)
def get_financial_statements(ticker):
    """
    Fetch financial statements for a given ticker

    Args:
        ticker: Stock ticker symbol

    Returns:
        tuple: (income_statement, balance_sheet, cash_flow) DataFrames
               or (None, None, None) on error
    """
    try:
        stock = _get_stock_object(ticker)
        if stock is None:
            return None, None, None

        # Fetch annual financial statements
        income_stmt = stock.financials
        balance_sheet = stock.balance_sheet
        cash_flow = stock.cashflow

        return income_stmt, balance_sheet, cash_flow
    except Exception as e:
        st.error(f"Error fetching financial statements: {str(e)}")
        return None, None, None


@st.cache_data(ttl=3600)
def get_news(ticker, max_items=10):
    """
    Fetch recent news for a given ticker

    Args:
        ticker: Stock ticker symbol
        max_items: Maximum number of news items to return

    Returns:
        list: List of news dictionaries or empty list on error
    """
    try:
        stock = yf.Ticker(ticker)
        news = stock.news

        if news:
            return news[:max_items]
        return []
    except Exception as e:
        st.warning(f"Error fetching news: {str(e)}")
        return []


@st.cache_data(ttl=3600)
def get_historical_data(ticker, period="1y"):
    """
    Fetch historical price data

    Args:
        ticker: Stock ticker symbol
        period: Time period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)

    Returns:
        DataFrame: Historical price data or None on error
    """
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period)
        return hist
    except Exception as e:
        st.error(f"Error fetching historical data: {str(e)}")
        return None

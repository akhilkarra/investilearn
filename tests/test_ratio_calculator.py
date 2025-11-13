"""Tests for ratio_calculator module."""

from typing import Any

import pandas as pd

from utils.ratio_calculator import calculate_ratios, format_ratio_value, get_ratio_metrics


class TestCalculateRatios:
    """Test suite for calculate_ratios function."""

    def test_calculate_ratios_with_basic_info(self, sample_stock_info):
        """Test ratio calculations with standard stock info."""
        ratios = calculate_ratios(sample_stock_info)

        # Check profitability ratios
        assert ratios["ROE"] == 15.0  # 0.15 * 100
        assert ratios["ROA"] == 10.0  # 0.10 * 100
        assert ratios["Net Profit Margin"] == 25.0  # 0.25 * 100
        assert ratios["Gross Profit Margin"] == 40.0  # 0.40 * 100

        # Check liquidity ratios
        assert ratios["Current Ratio"] == 1.5
        assert ratios["Quick Ratio"] == 1.2

        # Check leverage ratios
        assert ratios["Debt to Equity"] == 1.8

        # Check valuation ratios
        assert ratios["P/E Ratio"] == 28.5
        assert ratios["P/B Ratio"] == 40.2
        assert ratios["PEG Ratio"] == 2.1

    def test_calculate_ratios_with_zero_values(self):
        """Test that zero values are handled correctly (not treated as None)."""
        info = {
            "returnOnEquity": 0.0,  # Zero is valid!
            "returnOnAssets": 0.0,
            "profitMargins": 0.0,
            "grossMargins": 0.0,
        }
        ratios = calculate_ratios(info)

        # Zero should be converted to 0.0%, not None
        assert ratios["ROE"] == 0.0
        assert ratios["ROA"] == 0.0
        assert ratios["Net Profit Margin"] == 0.0
        assert ratios["Gross Profit Margin"] == 0.0

    def test_calculate_ratios_with_missing_values(self):
        """Test that missing values return None."""
        info: dict[str, Any] = {}  # Empty info
        ratios = calculate_ratios(info)

        # All ratios should be None when data is missing
        assert ratios["ROE"] is None
        assert ratios["ROA"] is None
        assert ratios["Net Profit Margin"] is None
        assert ratios["Current Ratio"] is None
        assert ratios["Debt to Equity"] is None

    def test_calculate_ratios_with_income_statement(self):
        """Test Interest Coverage calculation with income statement data."""
        info: dict[str, Any] = {}
        income_stmt = pd.DataFrame(
            {
                "2023-12-31": {
                    "EBIT": 100000000,
                    "Interest Expense": 5000000,
                }
            }
        )

        ratios = calculate_ratios(info, income_stmt=income_stmt)

        # Interest Coverage = EBIT / Interest Expense
        assert ratios["Interest Coverage"] == 20.0  # 100M / 5M

    def test_calculate_ratios_with_negative_interest_expense(self):
        """Test Interest Coverage with negative interest expense (uses absolute value)."""
        info: dict[str, Any] = {}
        income_stmt = pd.DataFrame(
            {
                "2023-12-31": {
                    "EBIT": 100000000,
                    "Interest Expense": -5000000,  # Negative
                }
            }
        )

        ratios = calculate_ratios(info, income_stmt=income_stmt)

        # Should use abs() of interest expense
        assert ratios["Interest Coverage"] == 20.0

    def test_calculate_ratios_with_zero_interest_expense(self):
        """Test Interest Coverage when interest expense is zero."""
        info: dict[str, Any] = {}
        income_stmt = pd.DataFrame(
            {
                "2023-12-31": {
                    "EBIT": 100000000,
                    "Interest Expense": 0,  # Zero - avoid division by zero
                }
            }
        )

        ratios = calculate_ratios(info, income_stmt=income_stmt)

        # Should return None to avoid division by zero
        assert ratios["Interest Coverage"] is None

    def test_calculate_ratios_with_balance_sheet(self):
        """Test Debt Ratio calculation with balance sheet data."""
        info: dict[str, Any] = {}
        balance_sheet = pd.DataFrame(
            {
                "2023-12-31": {
                    "Total Debt": 500000000,
                    "Total Assets": 1000000000,
                }
            }
        )

        ratios = calculate_ratios(info, balance_sheet=balance_sheet)

        # Debt Ratio = Total Debt / Total Assets
        assert ratios["Debt Ratio"] == 0.5

    def test_calculate_ratios_with_zero_total_assets(self):
        """Test Debt Ratio when total assets is zero."""
        info: dict[str, Any] = {}
        balance_sheet = pd.DataFrame(
            {
                "2023-12-31": {
                    "Total Debt": 500000000,
                    "Total Assets": 0,  # Zero - avoid division by zero
                }
            }
        )

        ratios = calculate_ratios(info, balance_sheet=balance_sheet)

        # Should return None to avoid division by zero
        assert ratios["Debt Ratio"] is None

    def test_calculate_ratios_with_missing_financial_data(self):
        """Test calculations when financial statement data is missing."""
        info: dict[str, Any] = {}
        income_stmt = pd.DataFrame({"2023-12-31": {}})  # Empty data

        ratios = calculate_ratios(info, income_stmt=income_stmt)

        # Should return None when required data is missing
        assert ratios["Interest Coverage"] is None

    def test_calculate_ratios_with_empty_dataframe(self):
        """Test calculations with empty DataFrames."""
        info: dict[str, Any] = {}
        empty_df = pd.DataFrame()

        ratios = calculate_ratios(info, income_stmt=empty_df, balance_sheet=empty_df)

        # Should return None for calculated ratios
        assert ratios["Interest Coverage"] is None
        assert ratios["Debt Ratio"] is None


class TestGetRatioMetrics:
    """Test suite for get_ratio_metrics function."""

    def test_get_profitability_metrics(self):
        """Test getting profitability ratio metrics."""
        info_text, metrics = get_ratio_metrics("Profitability")

        assert "Profitability ratios" in info_text
        assert len(metrics) == 4
        assert ("ROE", "ROE (Return on Equity)") in metrics
        assert ("ROA", "ROA (Return on Assets)") in metrics

    def test_get_liquidity_metrics(self):
        """Test getting liquidity ratio metrics."""
        info_text, metrics = get_ratio_metrics("Liquidity")

        assert "Liquidity ratios" in info_text
        assert len(metrics) == 2
        assert ("Current Ratio", "Current Ratio") in metrics
        assert ("Quick Ratio", "Quick Ratio") in metrics
        # Cash Ratio should NOT be in the list (not implemented)
        assert ("Cash Ratio", "Cash Ratio") not in metrics

    def test_get_efficiency_metrics(self):
        """Test getting efficiency ratio metrics."""
        info_text, metrics = get_ratio_metrics("Efficiency")

        assert "Efficiency ratios" in info_text
        assert "calculations pending" in info_text or "pending" in info_text.lower()
        assert len(metrics) == 3
        assert ("Asset Turnover", "Asset Turnover") in metrics

    def test_get_leverage_metrics(self):
        """Test getting leverage ratio metrics."""
        info_text, metrics = get_ratio_metrics("Leverage")

        assert "Leverage ratios" in info_text
        assert len(metrics) == 3
        assert ("Debt to Equity", "Debt-to-Equity") in metrics
        assert ("Interest Coverage", "Interest Coverage") in metrics
        assert ("Debt Ratio", "Debt Ratio") in metrics

    def test_get_valuation_metrics(self):
        """Test getting valuation ratio metrics."""
        info_text, metrics = get_ratio_metrics("Valuation")

        assert "Valuation ratios" in info_text
        assert len(metrics) == 4
        assert ("P/E Ratio", "P/E Ratio") in metrics
        assert ("P/B Ratio", "P/B Ratio") in metrics

    def test_get_invalid_category_returns_default(self):
        """Test that invalid category returns Profitability as default."""
        info_text, metrics = get_ratio_metrics("InvalidCategory")

        # Should default to Profitability
        assert "Profitability ratios" in info_text
        assert ("ROE", "ROE (Return on Equity)") in metrics


class TestFormatRatioValue:
    """Test suite for format_ratio_value function."""

    def test_format_percentage_ratios(self):
        """Test formatting percentage-based ratios."""
        assert format_ratio_value(15.5, "ROE") == "15.50%"
        assert format_ratio_value(10.25, "ROA") == "10.25%"
        assert format_ratio_value(25.0, "Net Profit Margin") == "25.00%"
        assert format_ratio_value(40.123, "Gross Profit Margin") == "40.12%"

    def test_format_regular_ratios(self):
        """Test formatting non-percentage ratios."""
        assert format_ratio_value(1.5, "Current Ratio") == "1.50"
        assert format_ratio_value(28.5, "P/E Ratio") == "28.50"
        assert format_ratio_value(2.123456, "Debt to Equity") == "2.12"

    def test_format_zero_values(self):
        """Test that zero values are formatted correctly (not shown as N/A)."""
        assert format_ratio_value(0.0, "ROE") == "0.00%"
        assert format_ratio_value(0.0, "Current Ratio") == "0.00"

    def test_format_none_values(self):
        """Test that None values return N/A."""
        assert format_ratio_value(None, "ROE") == "N/A"
        assert format_ratio_value(None, "Current Ratio") == "N/A"
        assert format_ratio_value(None, "P/E Ratio") == "N/A"

    def test_format_negative_values(self):
        """Test formatting negative values."""
        assert format_ratio_value(-5.5, "ROE") == "-5.50%"
        assert format_ratio_value(-1.2, "Debt Ratio") == "-1.20"

    def test_format_large_values(self):
        """Test formatting large values."""
        assert format_ratio_value(1234.56, "P/E Ratio") == "1234.56"
        assert format_ratio_value(999.999, "ROA") == "1000.00%"

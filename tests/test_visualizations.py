"""Tests for visualizations module."""

import pandas as pd

from utils.visualizations import (
    create_balance_sankey,
    create_cashflow_sankey,
    create_empty_sankey,
    create_income_sankey,
    create_sankey_diagram,
)


class TestCreateSankeyDiagram:
    """Test suite for create_sankey_diagram function."""

    def test_create_sankey_with_none_data(self):
        """Test handling of None financial data."""
        fig = create_sankey_diagram(None, "income")

        # Should return a figure with "No data available" annotation
        assert fig is not None
        assert len(fig.layout.annotations) > 0
        assert "No data available" in fig.layout.annotations[0].text

    def test_create_sankey_with_empty_dataframe(self):
        """Test handling of empty DataFrame."""
        empty_df = pd.DataFrame()
        fig = create_sankey_diagram(empty_df, "income")

        # Should return empty sankey
        assert fig is not None

    def test_create_sankey_with_income_type(self):
        """Test creating income statement Sankey."""
        data = pd.DataFrame(
            {
                "2023-12-31": {
                    "Total Revenue": 1000000,
                    "Cost Of Revenue": 600000,
                    "Operating Expense": 200000,
                    "Net Income": 150000,
                }
            }
        )

        fig = create_sankey_diagram(data, "income")

        # Should create a Sankey diagram
        assert fig is not None
        assert len(fig.data) > 0
        assert fig.data[0].type == "sankey"

    def test_create_sankey_with_cashflow_type(self):
        """Test creating cash flow Sankey."""
        data = pd.DataFrame(
            {
                "2023-12-31": {
                    "Operating Cash Flow": 500000,
                    "Investing Cash Flow": -200000,
                    "Financing Cash Flow": -100000,
                }
            }
        )

        fig = create_sankey_diagram(data, "cashflow")

        # Should create a Sankey diagram
        assert fig is not None
        assert len(fig.data) > 0

    def test_create_sankey_with_balance_type(self):
        """Test creating balance sheet Sankey."""
        data = pd.DataFrame(
            {
                "2023-12-31": {
                    "Total Assets": 1000000,
                    "Total Liabilities Net Minority Interest": 600000,
                    "Stockholders Equity": 400000,
                }
            }
        )

        fig = create_sankey_diagram(data, "balance")

        # Should create a Sankey diagram
        assert fig is not None
        assert len(fig.data) > 0

    def test_create_sankey_with_invalid_type(self):
        """Test handling of invalid statement type."""
        data = pd.DataFrame({"2023-12-31": {"Revenue": 1000000}})

        fig = create_sankey_diagram(data, "invalid_type")

        # Should return empty sankey
        assert fig is not None


class TestCreateIncomeSankey:
    """Test suite for create_income_sankey function."""

    def test_create_income_sankey_with_valid_data(self):
        """Test income Sankey with complete data."""
        data = pd.Series(
            {
                "Total Revenue": 1000000,
                "Cost Of Revenue": 600000,
                "Operating Expense": 200000,
                "Net Income": 150000,
            }
        )

        fig = create_income_sankey(data)

        # Should create valid Sankey
        assert fig is not None
        assert len(fig.data) > 0
        assert fig.data[0].type == "sankey"
        assert "Income Statement Flow" in fig.layout.title.text

    def test_create_income_sankey_with_zero_revenue(self):
        """Test income Sankey when revenue is zero."""
        data = pd.Series(
            {
                "Total Revenue": 0,
                "Cost Of Revenue": 0,
                "Operating Expense": 0,
                "Net Income": 0,
            }
        )

        fig = create_income_sankey(data)

        # Should return empty sankey when revenue is zero
        assert fig is not None

    def test_create_income_sankey_with_missing_data(self):
        """Test income Sankey with missing fields."""
        data = pd.Series({"Total Revenue": 1000000})  # Missing other fields

        fig = create_income_sankey(data)

        # Should handle gracefully
        assert fig is not None

    def test_create_income_sankey_with_exception(self):
        """Test income Sankey error handling."""
        # Pass invalid data type
        fig = create_income_sankey(None)

        # Should return empty sankey on exception
        assert fig is not None


class TestCreateCashflowSankey:
    """Test suite for create_cashflow_sankey function."""

    def test_create_cashflow_sankey_with_valid_data(self):
        """Test cash flow Sankey with complete data."""
        data = pd.Series(
            {
                "Operating Cash Flow": 500000,
                "Investing Cash Flow": -200000,
                "Financing Cash Flow": -100000,
            }
        )

        fig = create_cashflow_sankey(data)

        # Should create valid Sankey
        assert fig is not None
        assert len(fig.data) > 0
        assert "Cash Flow Movement" in fig.layout.title.text

    def test_create_cashflow_sankey_with_all_zeros(self):
        """Test cash flow Sankey when all values are zero."""
        data = pd.Series(
            {
                "Operating Cash Flow": 0,
                "Investing Cash Flow": 0,
                "Financing Cash Flow": 0,
            }
        )

        fig = create_cashflow_sankey(data)

        # Should return empty sankey
        assert fig is not None

    def test_create_cashflow_sankey_with_missing_data(self):
        """Test cash flow Sankey with missing fields."""
        data = pd.Series({"Operating Cash Flow": 500000})  # Missing other fields

        fig = create_cashflow_sankey(data)

        # Should handle gracefully
        assert fig is not None

    def test_create_cashflow_sankey_with_exception(self):
        """Test cash flow Sankey error handling."""
        # Pass invalid data type
        fig = create_cashflow_sankey(None)

        # Should return empty sankey on exception
        assert fig is not None


class TestCreateBalanceSankey:
    """Test suite for create_balance_sankey function."""

    def test_create_balance_sankey_with_valid_data(self):
        """Test balance sheet Sankey with complete data."""
        data = pd.Series(
            {
                "Total Assets": 1000000,
                "Total Liabilities Net Minority Interest": 600000,
                "Stockholders Equity": 400000,
            }
        )

        fig = create_balance_sankey(data)

        # Should create valid Sankey
        assert fig is not None
        assert len(fig.data) > 0
        assert "Balance Sheet Structure" in fig.layout.title.text

    def test_create_balance_sankey_with_zero_assets(self):
        """Test balance sheet Sankey when assets are zero."""
        data = pd.Series(
            {
                "Total Assets": 0,
                "Total Liabilities Net Minority Interest": 0,
                "Stockholders Equity": 0,
            }
        )

        fig = create_balance_sankey(data)

        # Should return empty sankey
        assert fig is not None

    def test_create_balance_sankey_with_missing_data(self):
        """Test balance sheet Sankey with missing fields."""
        data = pd.Series({"Total Assets": 1000000})  # Missing other fields

        fig = create_balance_sankey(data)

        # Should handle gracefully
        assert fig is not None

    def test_create_balance_sankey_with_exception(self):
        """Test balance sheet Sankey error handling."""
        # Pass invalid data type
        fig = create_balance_sankey(None)

        # Should return empty sankey on exception
        assert fig is not None


class TestCreateEmptySankey:
    """Test suite for create_empty_sankey function."""

    def test_create_empty_sankey_structure(self):
        """Test that empty sankey has correct structure."""
        fig = create_empty_sankey()

        # Should have annotation
        assert fig is not None
        assert len(fig.layout.annotations) > 0
        assert "Insufficient data" in fig.layout.annotations[0].text

    def test_create_empty_sankey_no_data(self):
        """Test that empty sankey has no data traces."""
        fig = create_empty_sankey()

        # Should have no sankey data
        assert len(fig.data) == 0

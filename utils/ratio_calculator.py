"""Financial ratio calculation utilities"""

import streamlit as st


def calculate_ratios(info, income_stmt=None, balance_sheet=None):
    """
    Calculate key financial ratios from stock info and financial statements

    Args:
        info: Stock info dictionary from yfinance
        income_stmt: Income statement DataFrame (optional)
        balance_sheet: Balance sheet DataFrame (optional)

    Returns:
        dict: Dictionary of calculated ratios
    """
    ratios = {}

    try:
        # Profitability ratios
        roe = info.get("returnOnEquity", None)
        ratios["ROE"] = roe * 100 if roe is not None else None

        roa = info.get("returnOnAssets", None)
        ratios["ROA"] = roa * 100 if roa is not None else None

        profit_margin = info.get("profitMargins", None)
        ratios["Net Profit Margin"] = profit_margin * 100 if profit_margin is not None else None

        gross_margin = info.get("grossMargins", None)
        ratios["Gross Profit Margin"] = gross_margin * 100 if gross_margin is not None else None

        # Liquidity ratios
        ratios["Current Ratio"] = info.get("currentRatio", None)
        ratios["Quick Ratio"] = info.get("quickRatio", None)

        # Leverage ratios
        ratios["Debt to Equity"] = info.get("debtToEquity", None)

        # Calculate Interest Coverage if income statement data available
        if income_stmt is not None and not income_stmt.empty:
            try:
                # Get most recent column (latest financial data)
                latest_data = income_stmt.iloc[:, 0]
                ebit = latest_data.get("EBIT", None)
                interest_expense = latest_data.get("Interest Expense", None)

                if ebit is not None and interest_expense is not None and interest_expense != 0:
                    ratios["Interest Coverage"] = ebit / abs(interest_expense)
                else:
                    ratios["Interest Coverage"] = None
            except (KeyError, IndexError, TypeError):
                ratios["Interest Coverage"] = None
        else:
            ratios["Interest Coverage"] = None

        # Calculate Debt Ratio if balance sheet data available
        if balance_sheet is not None and not balance_sheet.empty:
            try:
                latest_data = balance_sheet.iloc[:, 0]
                total_debt = latest_data.get("Total Debt", None)
                total_assets = latest_data.get("Total Assets", None)

                if total_debt is not None and total_assets is not None and total_assets != 0:
                    ratios["Debt Ratio"] = total_debt / total_assets
                else:
                    ratios["Debt Ratio"] = None
            except (KeyError, IndexError, TypeError):
                ratios["Debt Ratio"] = None
        else:
            ratios["Debt Ratio"] = None

        # Valuation ratios
        ratios["P/E Ratio"] = info.get("trailingPE", None)
        ratios["P/B Ratio"] = info.get("priceToBook", None)
        ratios["PEG Ratio"] = info.get("pegRatio", None)
        ratios["Price to Sales"] = info.get("priceToSalesTrailing12Months", None)

    except Exception as e:
        st.warning(f"Error calculating some ratios: {str(e)}")

    return ratios


def get_ratio_metrics(ratio_category):
    """
    Get the list of metrics and descriptions for a ratio category

    Args:
        ratio_category: Category name (Profitability, Liquidity, etc.)

    Returns:
        tuple: (info_text, metrics_list)
    """
    ratio_configs = {
        "Profitability": {
            "info": "💡 **Profitability ratios** measure how efficiently a company generates profit",
            "metrics": [
                ("ROE", "ROE (Return on Equity)"),
                ("ROA", "ROA (Return on Assets)"),
                ("Net Profit Margin", "Net Profit Margin"),
                ("Gross Profit Margin", "Gross Profit Margin"),
            ],
        },
        "Liquidity": {
            "info": "💡 **Liquidity ratios** assess ability to meet short-term obligations",
            "metrics": [
                ("Current Ratio", "Current Ratio"),
                ("Quick Ratio", "Quick Ratio"),
            ],
        },
        "Efficiency": {
            "info": "💡 **Efficiency ratios** show how well assets are being used (calculations pending)",
            "metrics": [
                ("Asset Turnover", "Asset Turnover"),
                ("Inventory Turnover", "Inventory Turnover"),
                ("Days Sales Outstanding", "Days Sales Outstanding"),
            ],
        },
        "Leverage": {
            "info": "💡 **Leverage ratios** indicate financial risk from debt",
            "metrics": [
                ("Debt to Equity", "Debt-to-Equity"),
                ("Interest Coverage", "Interest Coverage"),
                ("Debt Ratio", "Debt Ratio"),
            ],
        },
        "Valuation": {
            "info": "💡 **Valuation ratios** help determine if stock is fairly priced",
            "metrics": [
                ("P/E Ratio", "P/E Ratio"),
                ("P/B Ratio", "P/B Ratio"),
                ("PEG Ratio", "PEG Ratio"),
                ("Price to Sales", "Price-to-Sales"),
            ],
        },
    }

    config = ratio_configs.get(ratio_category, ratio_configs["Profitability"])
    return config["info"], config["metrics"]


def format_ratio_value(value, ratio_name):
    """
    Format a ratio value for display

    Args:
        value: The ratio value
        ratio_name: Name of the ratio

    Returns:
        str: Formatted string for display
    """
    if value is None:
        return "N/A"

    # Percentage ratios
    if any(term in ratio_name for term in ["ROE", "ROA", "Margin"]):
        return f"{value:.2f}%"

    # Regular ratios
    return f"{value:.2f}"

"""Visualization utilities for financial data"""

import logging

import pandas as pd
import plotly.graph_objects as go


def hex_to_rgba(hex_color, alpha=0.4):
    """Convert hex color to rgba format with specified alpha."""
    hex_color = hex_color.lstrip("#")
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


# Set up logger
logger = logging.getLogger(__name__)


def create_sankey_diagram(financial_data, statement_type="income"):
    """
    Create a Sankey diagram for financial statements

    Args:
        financial_data: DataFrame with financial statement data
        statement_type: Type of statement ('income', 'cashflow', 'balance')

    Returns:
        plotly.graph_objects.Figure: Sankey diagram
    """
    if financial_data is None or financial_data.empty:
        # Return empty placeholder figure
        fig = go.Figure()
        fig.add_annotation(
            text="No data available",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
            font={"size": 16, "color": "gray"},
        )
        fig.update_layout(xaxis={"visible": False}, yaxis={"visible": False}, height=400)
        return fig

    # Get the most recent period (first column)
    if len(financial_data.columns) == 0:
        return create_empty_sankey()

    data = financial_data.iloc[:, 0]

    if statement_type == "income":
        return create_income_sankey(data)
    elif statement_type == "cashflow":
        return create_cashflow_sankey(data)
    elif statement_type == "balance":
        return create_balance_sankey(data)
    else:
        return create_empty_sankey()


def create_income_sankey(data):
    """Create dynamic Sankey from actual income statement line items"""
    try:
        # Get all available line items from the income statement
        # data is a Series with financial line items as index

        if data.empty or len(data) == 0:
            return create_empty_sankey()

        # Convert to dict and filter out zero/null values
        items = {k: abs(v) for k, v in data.items() if pd.notna(v) and v != 0}

        if not items:
            return create_empty_sankey()

        # Define the hierarchical structure based on common accounting patterns
        # Revenue flows to various expenses and ultimately to net income
        revenue_keys = ["Total Revenue", "Revenue", "Total Operating Revenue"]
        cogs_keys = ["Cost Of Revenue", "Cost of Revenue", "COGS"]
        gross_profit_keys = ["Gross Profit"]
        operating_income_keys = ["Operating Income", "EBIT"]
        interest_keys = ["Interest Expense"]
        tax_keys = ["Tax Provision", "Income Tax Expense"]
        net_income_keys = ["Net Income", "Net Income Common Stockholders"]

        # Find which keys exist in our data
        def find_key(key_list):
            for key in key_list:
                if key in items:
                    return key, items[key]
            return None, 0

        revenue_key, revenue = find_key(revenue_keys)
        cogs_key, cogs = find_key(cogs_keys)
        gross_profit_key, gross_profit = find_key(gross_profit_keys)
        operating_income_key, operating_income = find_key(operating_income_keys)
        net_income_key, net_income = find_key(net_income_keys)

        if revenue == 0:
            return create_empty_sankey()

        # Build nodes and flows dynamically
        nodes = []
        node_colors = []
        flows = []
        node_map = {}  # Map of key to node index

        # Color palette for accessibility (colorblind-friendly)
        colors = {
            "revenue": "#2E86AB",  # Blue
            "expense": "#A23B72",  # Magenta
            "profit": "#06A77D",  # Teal
            "operating": "#F18F01",  # Orange
            "tax": "#8B5A3C",  # Brown
            "final": "#2D6A4F",  # Dark green
        }

        # Add revenue node
        if revenue_key:
            nodes.append(revenue_key)
            node_colors.append(colors["revenue"])
            node_map[revenue_key] = len(nodes) - 1

        # Add major expense/profit nodes that we found
        if cogs_key and cogs > 0:
            nodes.append(cogs_key)
            node_colors.append(colors["expense"])
            node_map[cogs_key] = len(nodes) - 1
            flows.append((node_map[revenue_key], node_map[cogs_key], cogs))

        if gross_profit_key and gross_profit > 0:
            nodes.append(gross_profit_key)
            node_colors.append(colors["profit"])
            node_map[gross_profit_key] = len(nodes) - 1
            flows.append((node_map[revenue_key], node_map[gross_profit_key], gross_profit))

        # Now add any other operating expenses we can find
        # Look for line items that aren't already included
        excluded_keys = {
            revenue_key,
            cogs_key,
            gross_profit_key,
            operating_income_key,
            net_income_key,
        }

        # Common operating expense patterns
        opex_patterns = [
            "Research And Development",
            "Selling General And Administration",
            "Operating Expense",
            "Depreciation",
            "Amortization",
            "Reconciled Depreciation",
        ]

        source_node = node_map.get(gross_profit_key, node_map.get(revenue_key))

        if source_node is not None:
            for pattern in opex_patterns:
                if pattern in items and pattern not in excluded_keys:
                    value = items[pattern]
                    if value > 0 and value / revenue > 0.02:  # Show if >2% of revenue
                        nodes.append(pattern)
                        node_colors.append(colors["operating"])
                        node_map[pattern] = len(nodes) - 1
                        flows.append((source_node, node_map[pattern], value))

        # Add operating income
        if operating_income_key and operating_income > 0:
            nodes.append(operating_income_key)
            node_colors.append(colors["profit"])
            node_map[operating_income_key] = len(nodes) - 1
            if gross_profit_key:
                flows.append(
                    (node_map[gross_profit_key], node_map[operating_income_key], operating_income)
                )
            else:
                flows.append(
                    (node_map[revenue_key], node_map[operating_income_key], operating_income)
                )

        # Add interest and taxes
        interest_key, interest = find_key(interest_keys)
        tax_key, tax = find_key(tax_keys)

        if operating_income_key:
            op_idx = node_map[operating_income_key]

            if interest_key and interest > 0 and interest / revenue > 0.01:
                nodes.append(interest_key)
                node_colors.append(colors["expense"])
                node_map[interest_key] = len(nodes) - 1
                flows.append((op_idx, node_map[interest_key], interest))

            if tax_key and tax > 0 and tax / revenue > 0.01:
                nodes.append(tax_key)
                node_colors.append(colors["tax"])
                node_map[tax_key] = len(nodes) - 1
                flows.append((op_idx, node_map[tax_key], tax))

            if net_income_key and net_income > 0:
                nodes.append(net_income_key)
                node_colors.append(colors["final"])
                node_map[net_income_key] = len(nodes) - 1
                flows.append((op_idx, node_map[net_income_key], net_income))

        if not flows:
            return create_empty_sankey()

        # Create link colors with transparency using rgba format
        link_colors = [hex_to_rgba(node_colors[source]) for source, _, _ in flows]

        fig = go.Figure(
            data=[
                go.Sankey(
                    node={
                        "pad": 15,
                        "thickness": 20,
                        "line": {"color": "white", "width": 1.5},
                        "label": nodes,
                        "color": node_colors,
                        "customdata": nodes,
                        "hovertemplate": "%{customdata}<br>$%{value:,.0f}<extra></extra>",
                    },
                    link={
                        "source": [f[0] for f in flows],
                        "target": [f[1] for f in flows],
                        "value": [f[2] for f in flows],
                        "color": link_colors,
                        "hovertemplate": "%{source.label} → %{target.label}<br>$%{value:,.0f}<extra></extra>",
                    },
                )
            ]
        )

        fig.update_layout(
            title="Income Statement Flow",
            font={"size": 10},
            height=500,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )

        return fig

    except Exception as e:
        logger.warning("Error creating income statement Sankey: %s", str(e))
        return create_empty_sankey()


def create_cashflow_sankey(data):
    """Create detailed Sankey diagram for cash flow with inflows and outflows"""
    try:
        # Extract cash flow components
        operating_cf = data.get("Operating Cash Flow", 0)
        investing_cf = data.get("Investing Cash Flow", 0)
        financing_cf = data.get("Financing Cash Flow", 0)

        # Operating CF breakdown (if available)
        net_income = data.get("Net Income", 0)
        depreciation = abs(data.get("Depreciation And Amortization", 0))

        # Investing CF breakdown
        capex = abs(data.get("Capital Expenditure", 0))
        investments = abs(data.get("Net Investment Purchase And Sale", 0))

        # Financing CF breakdown
        debt_issued = abs(data.get("Long Term Debt Issuance", 0))
        debt_repayment = abs(data.get("Long Term Debt Payments", 0))
        dividends = abs(data.get("Cash Dividends Paid", 0))
        stock_repurchase = abs(data.get("Repurchase Of Capital Stock", 0))

        # Use absolute values for visualization
        op_abs = abs(operating_cf)
        inv_abs = abs(investing_cf)
        fin_abs = abs(financing_cf)

        if op_abs == 0 and inv_abs == 0 and fin_abs == 0:
            return create_empty_sankey()

        # Build nodes dynamically
        nodes = []
        node_colors = []
        flows = []
        node_idx = 0

        # Starting point
        nodes.append("Beginning Cash")
        node_colors.append("#2E86AB")  # Deep blue
        begin_idx = node_idx
        node_idx += 1

        # Operating activities
        if operating_cf != 0:
            op_idx = node_idx
            nodes.append("Operating CF")
            node_colors.append(
                "#06A77D" if operating_cf > 0 else "#BC4B51"
            )  # Green if positive, red if negative
            flows.append((begin_idx, op_idx, op_abs))
            node_idx += 1

            # Show components if available
            if net_income > 0 and abs(net_income / operating_cf) < 2:  # Reasonable proportion
                ni_idx = node_idx
                nodes.append("Net Income")
                node_colors.append("#52B788")
                flows.append((op_idx, ni_idx, abs(net_income)))
                node_idx += 1

            if depreciation > 0 and depreciation / op_abs > 0.1:
                dep_idx = node_idx
                nodes.append("Depreciation")
                node_colors.append("#74C69D")
                flows.append((op_idx, dep_idx, depreciation))
                node_idx += 1

        # Investing activities
        if investing_cf != 0:
            inv_idx = node_idx
            nodes.append("Investing CF")
            node_colors.append("#F18F01" if investing_cf < 0 else "#90E0EF")  # Orange for cash out
            flows.append((begin_idx, inv_idx, inv_abs))
            node_idx += 1

            if capex > 0 and capex / inv_abs > 0.1:
                capex_idx = node_idx
                nodes.append("CapEx")
                node_colors.append("#C73E1D")
                flows.append((inv_idx, capex_idx, capex))
                node_idx += 1

            if investments > 0 and investments / inv_abs > 0.1:
                invest_idx = node_idx
                nodes.append("Investments")
                node_colors.append("#DC5B21")
                flows.append((inv_idx, invest_idx, investments))
                node_idx += 1

        # Financing activities
        if financing_cf != 0:
            fin_idx = node_idx
            nodes.append("Financing CF")
            node_colors.append("#9B59B6")
            flows.append((begin_idx, fin_idx, fin_abs))
            node_idx += 1

            if debt_issued > 0 and debt_issued / fin_abs > 0.1:
                debt_iss_idx = node_idx
                nodes.append("Debt Issued")
                node_colors.append("#8E44AD")
                flows.append((fin_idx, debt_iss_idx, debt_issued))
                node_idx += 1

            if debt_repayment > 0 and debt_repayment / fin_abs > 0.1:
                debt_pay_idx = node_idx
                nodes.append("Debt Repaid")
                node_colors.append("#6C3483")
                flows.append((fin_idx, debt_pay_idx, debt_repayment))
                node_idx += 1

            if dividends > 0 and dividends / fin_abs > 0.1:
                div_idx = node_idx
                nodes.append("Dividends")
                node_colors.append("#5B2C6F")
                flows.append((fin_idx, div_idx, dividends))
                node_idx += 1

            if stock_repurchase > 0 and stock_repurchase / fin_abs > 0.1:
                buyback_idx = node_idx
                nodes.append("Buybacks")
                node_colors.append("#4A235A")
                flows.append((fin_idx, buyback_idx, stock_repurchase))
                node_idx += 1

        # Ending cash
        net_change = operating_cf + investing_cf + financing_cf
        if net_change != 0:
            end_idx = node_idx
            nodes.append("Ending Cash")
            node_colors.append("#2D6A4F" if net_change > 0 else "#A23B72")
            # Connect from the largest source
            if op_abs >= inv_abs and op_abs >= fin_abs:
                source_idx = 1  # Operating
            elif inv_abs >= fin_abs:
                source_idx = nodes.index("Investing CF") if "Investing CF" in nodes else 1
            else:
                source_idx = nodes.index("Financing CF") if "Financing CF" in nodes else 1
            flows.append((source_idx, end_idx, abs(net_change)))

        if not flows:
            return create_empty_sankey()

        # Create link colors with transparency using rgba format
        link_colors = []
        for source, _, _ in flows:
            base_color = node_colors[source] if source < len(node_colors) else "#999999"
            link_colors.append(hex_to_rgba(base_color))

        fig = go.Figure(
            data=[
                go.Sankey(
                    node={
                        "pad": 15,
                        "thickness": 20,
                        "line": {"color": "white", "width": 1.5},
                        "label": nodes,
                        "color": node_colors,
                        "customdata": nodes,
                        "hovertemplate": "%{customdata}<br>$%{value:,.0f}<extra></extra>",
                    },
                    link={
                        "source": [f[0] for f in flows],
                        "target": [f[1] for f in flows],
                        "value": [f[2] for f in flows],
                        "color": link_colors,
                        "hovertemplate": "%{source.label} → %{target.label}<br>$%{value:,.0f}<extra></extra>",
                    },
                )
            ]
        )

        fig.update_layout(
            title="Cash Flow Movement (Detailed)",
            font={"size": 10},
            height=600,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )

        return fig

    except Exception as e:
        logger.warning("Error creating cash flow Sankey: %s", str(e))
        return create_empty_sankey()


def create_balance_sankey(data):
    """Create detailed Sankey diagram for balance sheet with asset/liability breakdown"""
    try:
        # Extract total assets
        total_assets = abs(data.get("Total Assets", 0))

        if total_assets == 0:
            return create_empty_sankey()

        # Asset breakdown
        current_assets = abs(data.get("Current Assets", 0))
        non_current_assets = abs(
            data.get("Total Non Current Assets", total_assets - current_assets)
        )

        # Further breakdown of current assets
        cash = abs(data.get("Cash And Cash Equivalents", 0))
        receivables = abs(data.get("Accounts Receivable", 0) + data.get("Receivables", 0))
        inventory = abs(data.get("Inventory", 0))

        # Non-current assets breakdown
        ppe = abs(data.get("Net PPE", 0))  # Property, Plant & Equipment
        intangibles = abs(data.get("Goodwill And Other Intangible Assets", 0))

        # Liability breakdown
        current_liabilities = abs(data.get("Current Liabilities", 0))
        non_current_liabilities = abs(
            data.get("Total Non Current Liabilities Net Minority Interest", 0)
        )

        # Equity components
        retained_earnings = abs(data.get("Retained Earnings", 0))
        stockholder_equity = abs(data.get("Stockholders Equity", 0))

        # Build nodes dynamically
        nodes = []
        node_colors = []
        flows = []
        node_idx = 0

        # Assets side (left)
        nodes.append("Total Assets")
        node_colors.append("#2E86AB")  # Deep blue
        assets_idx = node_idx
        node_idx += 1

        # Current Assets
        if current_assets > 0:
            curr_assets_idx = node_idx
            nodes.append("Current Assets")
            node_colors.append("#06A77D")  # Teal
            flows.append((assets_idx, curr_assets_idx, current_assets))
            node_idx += 1

            # Breakdown current assets
            if cash > 0 and cash / current_assets > 0.1:  # Show if >10% of current assets
                cash_idx = node_idx
                nodes.append("Cash")
                node_colors.append("#90E0EF")  # Light blue
                flows.append((curr_assets_idx, cash_idx, cash))
                node_idx += 1

            if receivables > 0 and receivables / current_assets > 0.1:
                recv_idx = node_idx
                nodes.append("Receivables")
                node_colors.append("#00B4D8")  # Cyan
                flows.append((curr_assets_idx, recv_idx, receivables))
                node_idx += 1

            if inventory > 0 and inventory / current_assets > 0.1:
                inv_idx = node_idx
                nodes.append("Inventory")
                node_colors.append("#0077B6")  # Blue
                flows.append((curr_assets_idx, inv_idx, inventory))
                node_idx += 1

        # Non-Current Assets
        if non_current_assets > 0:
            non_curr_idx = node_idx
            nodes.append("Non-Current Assets")
            node_colors.append("#023E8A")  # Dark blue
            flows.append((assets_idx, non_curr_idx, non_current_assets))
            node_idx += 1

            if ppe > 0 and ppe / non_current_assets > 0.1:
                ppe_idx = node_idx
                nodes.append("PP&E")
                node_colors.append("#03045E")  # Navy
                flows.append((non_curr_idx, ppe_idx, ppe))
                node_idx += 1

            if intangibles > 0 and intangibles / non_current_assets > 0.1:
                intang_idx = node_idx
                nodes.append("Intangibles")
                node_colors.append("#5A189A")  # Purple
                flows.append((non_curr_idx, intang_idx, intangibles))
                node_idx += 1

        # Liabilities side (middle/right)
        if current_liabilities > 0:
            curr_liab_idx = node_idx
            nodes.append("Current Liabilities")
            node_colors.append("#F18F01")  # Orange
            flows.append((assets_idx, curr_liab_idx, current_liabilities))
            node_idx += 1

        if non_current_liabilities > 0:
            non_curr_liab_idx = node_idx
            nodes.append("Long-Term Debt")
            node_colors.append("#C73E1D")  # Red-orange
            flows.append((assets_idx, non_curr_liab_idx, non_current_liabilities))
            node_idx += 1

        # Equity side (right)
        if stockholder_equity > 0:
            equity_idx = node_idx
            nodes.append("Shareholders' Equity")
            node_colors.append("#2D6A4F")  # Dark green
            flows.append((assets_idx, equity_idx, stockholder_equity))
            node_idx += 1

            if retained_earnings > 0 and abs(retained_earnings / stockholder_equity) > 0.15:
                ret_earn_idx = node_idx
                nodes.append("Retained Earnings")
                node_colors.append("#52B788")  # Light green
                flows.append((equity_idx, ret_earn_idx, retained_earnings))
                node_idx += 1

        if not flows:
            return create_empty_sankey()

        # Create link colors with transparency using rgba format
        link_colors = []
        for source, _, _ in flows:
            base_color = node_colors[source]
            link_colors.append(hex_to_rgba(base_color))

        fig = go.Figure(
            data=[
                go.Sankey(
                    node={
                        "pad": 15,
                        "thickness": 20,
                        "line": {"color": "white", "width": 1.5},
                        "label": nodes,
                        "color": node_colors,
                        "customdata": nodes,
                        "hovertemplate": "%{customdata}<br>$%{value:,.0f}<extra></extra>",
                    },
                    link={
                        "source": [f[0] for f in flows],
                        "target": [f[1] for f in flows],
                        "value": [f[2] for f in flows],
                        "color": link_colors,
                        "hovertemplate": "%{source.label} → %{target.label}<br>$%{value:,.0f}<extra></extra>",
                    },
                )
            ]
        )

        fig.update_layout(
            title="Balance Sheet Structure (Detailed)",
            font={"size": 10},
            height=600,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )

        return fig

    except Exception as e:
        logger.warning("Error creating balance sheet Sankey: %s", str(e))
        return create_empty_sankey()


def create_empty_sankey():
    """Create an empty placeholder Sankey diagram"""
    fig = go.Figure()
    fig.add_annotation(
        text="Insufficient data for visualization",
        xref="paper",
        yref="paper",
        x=0.5,
        y=0.5,
        showarrow=False,
        font={"size": 14, "color": "gray"},
    )
    fig.update_layout(xaxis={"visible": False}, yaxis={"visible": False}, height=400)
    return fig


def create_ratio_trend_chart(historical_ratios, ratio_name):
    """
    Create a line chart showing ratio trends over time

    Args:
        historical_ratios: DataFrame with ratios over time
        ratio_name: Name of the ratio to plot

    Returns:
        plotly.graph_objects.Figure: Line chart
    """
    fig = go.Figure()

    if historical_ratios is not None and not historical_ratios.empty:
        fig.add_trace(
            go.Scatter(
                x=historical_ratios.index,
                y=historical_ratios[ratio_name],
                mode="lines+markers",
                name=ratio_name,
                line={"color": "#3498db", "width": 2},
                marker={"size": 6},
            )
        )

    fig.update_layout(
        title=f"{ratio_name} Trend",
        xaxis_title="Period",
        yaxis_title=ratio_name,
        height=300,
        hovermode="x unified",
    )

    return fig

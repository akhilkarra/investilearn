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
    """Create dynamic Sankey diagram for cash flow showing all line items"""
    try:
        # Extract all items from the cash flow statement
        items = {k: v for k, v in data.items() if pd.notna(v) and v != 0}

        # Key patterns for cash flow components
        operating_keys = ["Operating Cash Flow", "Cash Flow From Operating Activities"]
        investing_keys = ["Investing Cash Flow", "Cash Flow From Investing Activities"]
        financing_keys = ["Financing Cash Flow", "Cash Flow From Financing Activities"]

        # Find key totals
        def find_key(key_list):
            for key in key_list:
                if key in items:
                    return key, items[key]
            return None, 0

        operating_key, operating_cf = find_key(operating_keys)
        investing_key, investing_cf = find_key(investing_keys)
        financing_key, financing_cf = find_key(financing_keys)

        op_abs = abs(operating_cf)
        inv_abs = abs(investing_cf)
        fin_abs = abs(financing_cf)

        if op_abs == 0 and inv_abs == 0 and fin_abs == 0:
            return create_empty_sankey()

        # Build nodes and flows dynamically
        nodes = []
        node_colors = []
        flows = []
        node_map = {}

        # Color palette for cash flow
        colors = {
            "positive": "#06A77D",  # Teal (inflow)
            "negative": "#BC4B51",  # Red (outflow)
            "operating": "#2E86AB",  # Blue
            "investing": "#F18F01",  # Orange
            "financing": "#9B59B6",  # Purple
            "neutral": "#2D6A4F",  # Dark green
        }

        # Starting node
        nodes.append("Beginning Cash")
        node_colors.append(colors["operating"])
        node_map["Beginning Cash"] = 0

        # Operating Cash Flow
        if operating_key and operating_cf != 0:
            nodes.append(operating_key)
            color = colors["positive"] if operating_cf > 0 else colors["negative"]
            node_colors.append(color)
            node_map[operating_key] = len(nodes) - 1
            flows.append((0, node_map[operating_key], op_abs))

            # Operating CF components
            operating_patterns = {
                "Net Income": "positive",
                "Net Income Common Stockholders": "positive",
                "Depreciation And Amortization": "positive",
                "Depreciation": "positive",
                "Amortization": "positive",
                "Stock Based Compensation": "positive",
                "Deferred Income Tax": "neutral",
                "Change In Working Capital": "neutral",
                "Change In Receivables": "neutral",
                "Change In Inventory": "neutral",
                "Change In Payables And Accrued Expense": "neutral",
                "Change In Prepaid Assets": "neutral",
            }

            excluded = {operating_key, investing_key, financing_key}
            for pattern, color_type in operating_patterns.items():
                if pattern in items and pattern not in excluded:
                    value = abs(items[pattern])
                    if value > 0 and value / op_abs > 0.05:  # >5% threshold
                        nodes.append(pattern)
                        node_colors.append(colors[color_type])
                        node_map[pattern] = len(nodes) - 1
                        flows.append((node_map[operating_key], node_map[pattern], value))
                        excluded.add(pattern)

        # Investing Cash Flow
        if investing_key and investing_cf != 0:
            nodes.append(investing_key)
            color = colors["positive"] if investing_cf > 0 else colors["negative"]
            node_colors.append(color)
            node_map[investing_key] = len(nodes) - 1
            flows.append((0, node_map[investing_key], inv_abs))

            # Investing CF components
            investing_patterns = {
                "Capital Expenditure": "negative",
                "Net PPE Purchase And Sale": "negative",
                "Purchase Of PPE": "negative",
                "Net Investment Purchase And Sale": "neutral",
                "Purchase Of Investment": "negative",
                "Sale Of Investment": "positive",
                "Net Business Purchase And Sale": "neutral",
                "Purchase Of Business": "negative",
            }

            for pattern, color_type in investing_patterns.items():
                if pattern in items and pattern not in excluded:
                    value = abs(items[pattern])
                    if value > 0 and value / inv_abs > 0.1:  # >10% threshold
                        nodes.append(pattern)
                        node_colors.append(colors[color_type])
                        node_map[pattern] = len(nodes) - 1
                        flows.append((node_map[investing_key], node_map[pattern], value))
                        excluded.add(pattern)

        # Financing Cash Flow
        if financing_key and financing_cf != 0:
            nodes.append(financing_key)
            color = colors["positive"] if financing_cf > 0 else colors["negative"]
            node_colors.append(color)
            node_map[financing_key] = len(nodes) - 1
            flows.append((0, node_map[financing_key], fin_abs))

            # Financing CF components
            financing_patterns = {
                "Long Term Debt Issuance": "positive",
                "Long Term Debt Payments": "negative",
                "Net Long Term Debt Issuance": "neutral",
                "Short Long Term Debt Issuance": "positive",
                "Net Short Term Debt Issuance": "neutral",
                "Common Stock Issuance": "positive",
                "Common Stock Payments": "negative",
                "Repurchase Of Capital Stock": "negative",
                "Cash Dividends Paid": "negative",
                "Common Stock Dividend Paid": "negative",
            }

            for pattern, color_type in financing_patterns.items():
                if pattern in items and pattern not in excluded:
                    value = abs(items[pattern])
                    if value > 0 and value / fin_abs > 0.1:  # >10% threshold
                        nodes.append(pattern)
                        node_colors.append(colors[color_type])
                        node_map[pattern] = len(nodes) - 1
                        flows.append((node_map[financing_key], node_map[pattern], value))
                        excluded.add(pattern)

        # Ending cash (net change)
        net_change = operating_cf + investing_cf + financing_cf
        if abs(net_change) > 0:
            nodes.append("Ending Cash")
            color = colors["positive"] if net_change > 0 else colors["negative"]
            node_colors.append(color)
            node_map["Ending Cash"] = len(nodes) - 1

            # Connect from largest component
            if op_abs >= inv_abs and op_abs >= fin_abs and operating_key:
                source_idx = node_map[operating_key]
            elif inv_abs >= fin_abs and investing_key:
                source_idx = node_map[investing_key]
            elif financing_key:
                source_idx = node_map[financing_key]
            else:
                source_idx = 0

            flows.append((source_idx, node_map["Ending Cash"], abs(net_change)))

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
    """Create dynamic Sankey diagram for balance sheet showing all line items"""
    try:
        # Extract all non-zero items from the balance sheet
        items = {k: abs(v) for k, v in data.items() if pd.notna(v) and v != 0}

        # Key patterns for important balance sheet items
        total_assets_keys = ["Total Assets"]
        current_assets_keys = ["Current Assets"]
        non_current_assets_keys = [
            "Total Non Current Assets",
            "Non Current Assets",
            "Net Non Current Assets",
        ]

        # Find key totals
        def find_key(key_list):
            for key in key_list:
                if key in items:
                    return key, items[key]
            return None, 0

        total_assets_key, total_assets = find_key(total_assets_keys)
        current_assets_key, current_assets = find_key(current_assets_keys)
        non_current_assets_key, non_current_assets = find_key(non_current_assets_keys)

        if total_assets == 0:
            return create_empty_sankey()

        # Build nodes and flows dynamically
        nodes = []
        node_colors = []
        flows = []
        node_map = {}

        # Color palette for balance sheet
        colors = {
            "total_assets": "#2E86AB",  # Blue
            "current_assets": "#06A77D",  # Teal
            "non_current_assets": "#023E8A",  # Dark blue
            "current_liabilities": "#F18F01",  # Orange
            "non_current_liabilities": "#C73E1D",  # Red-orange
            "equity": "#2D6A4F",  # Dark green
            "cash": "#90E0EF",  # Light blue
            "receivables": "#00B4D8",  # Cyan
            "inventory": "#0077B6",  # Blue
            "ppe": "#03045E",  # Navy
            "intangibles": "#5A189A",  # Purple
            "other": "#7209B7",  # Magenta
        }

        # Add Total Assets root node
        if total_assets_key:
            nodes.append(total_assets_key)
            node_colors.append(colors["total_assets"])
            node_map[total_assets_key] = len(nodes) - 1

        # Track items we've already added
        excluded = {total_assets_key, current_assets_key, non_current_assets_key}

        # Current Assets breakdown
        if current_assets_key and current_assets > 0:
            nodes.append(current_assets_key)
            node_colors.append(colors["current_assets"])
            node_map[current_assets_key] = len(nodes) - 1
            flows.append((node_map[total_assets_key], node_map[current_assets_key], current_assets))

            # Pattern matching for current asset components
            current_asset_patterns = {
                "Cash And Cash Equivalents": "cash",
                "Cash": "cash",
                "Cash Equivalents": "cash",
                "Accounts Receivable": "receivables",
                "Receivables": "receivables",
                "Net Receivables": "receivables",
                "Inventory": "inventory",
                "Gross Inventory": "inventory",
                "Marketable Securities": "cash",
                "Short Term Investments": "cash",
            }

            for pattern, color_type in current_asset_patterns.items():
                if pattern in items and pattern not in excluded:
                    value = items[pattern]
                    if value > 0 and value / total_assets > 0.03:  # >3% threshold
                        nodes.append(pattern)
                        node_colors.append(colors[color_type])
                        node_map[pattern] = len(nodes) - 1
                        flows.append((node_map[current_assets_key], node_map[pattern], value))
                        excluded.add(pattern)

        # Non-Current Assets breakdown
        if non_current_assets_key and non_current_assets > 0:
            nodes.append(non_current_assets_key)
            node_colors.append(colors["non_current_assets"])
            node_map[non_current_assets_key] = len(nodes) - 1
            flows.append(
                (
                    node_map[total_assets_key],
                    node_map[non_current_assets_key],
                    non_current_assets,
                )
            )

            # Pattern matching for non-current asset components
            non_current_patterns = {
                "Net PPE": "ppe",
                "Gross PPE": "ppe",
                "Properties": "ppe",
                "Plant": "ppe",
                "Equipment": "ppe",
                "Goodwill And Other Intangible Assets": "intangibles",
                "Goodwill": "intangibles",
                "Intangible Assets": "intangibles",
                "Other Intangible Assets": "intangibles",
                "Long Term Investments": "other",
                "Investment In Financial Assets": "other",
            }

            for pattern, color_type in non_current_patterns.items():
                if pattern in items and pattern not in excluded:
                    value = items[pattern]
                    if value > 0 and value / total_assets > 0.03:  # >3% threshold
                        nodes.append(pattern)
                        node_colors.append(colors[color_type])
                        node_map[pattern] = len(nodes) - 1
                        flows.append((node_map[non_current_assets_key], node_map[pattern], value))
                        excluded.add(pattern)

        # Liabilities breakdown
        liability_keys = {
            "Current Liabilities": "current_liabilities",
            "Total Current Liabilities": "current_liabilities",
            "Total Non Current Liabilities Net Minority Interest": "non_current_liabilities",
            "Long Term Debt": "non_current_liabilities",
            "Total Debt": "non_current_liabilities",
        }

        for key, color_type in liability_keys.items():
            if key in items and key not in excluded:
                value = items[key]
                if value > 0 and value / total_assets > 0.05:  # >5% threshold
                    nodes.append(key)
                    node_colors.append(colors[color_type])
                    node_map[key] = len(nodes) - 1
                    flows.append((node_map[total_assets_key], node_map[key], value))
                    excluded.add(key)

        # Equity breakdown
        equity_keys = {
            "Stockholders Equity": "equity",
            "Total Equity Gross Minority Interest": "equity",
            "Common Stock Equity": "equity",
            "Retained Earnings": "equity",
            "Common Stock": "equity",
        }

        for key, color_type in equity_keys.items():
            if key in items and key not in excluded:
                value = items[key]
                if value > 0 and value / total_assets > 0.05:  # >5% threshold
                    nodes.append(key)
                    node_colors.append(colors[color_type])
                    node_map[key] = len(nodes) - 1
                    flows.append((node_map[total_assets_key], node_map[key], value))
                    excluded.add(key)

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

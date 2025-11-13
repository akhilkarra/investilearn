"""Visualization utilities for financial data"""

import logging

import pandas as pd
import plotly.graph_objects as go


def hex_to_rgba(hex_color, alpha=0.4):
    """Convert hex color to rgba format with specified alpha.

    Args:
        hex_color: Hex color string (e.g., '#3498db' or '3498db')
        alpha: Alpha transparency value (0.0 to 1.0), defaults to 0.4

    Returns:
        str: RGBA color string (e.g., 'rgba(52,152,219,0.4)')
    """
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

        # Common operating expense patterns (match GuruFocus detail level)
        opex_patterns = [
            "Selling General And Administration",  # SG&A
            "Research And Development",  # R&D
            "Operating Expense",
            "Depreciation And Amortization",
            "Depreciation",
            "Amortization",
            "Reconciled Depreciation",
        ]

        source_node = node_map.get(gross_profit_key, node_map.get(revenue_key))

        if source_node is not None:
            for pattern in opex_patterns:
                if pattern in items and pattern not in excluded_keys:
                    value = items[pattern]
                    # Lower threshold to 0.5% to match GuruFocus detail
                    if value > 0 and value / revenue > 0.005:
                        # Use shorter labels for clarity
                        label = pattern
                        if pattern == "Selling General And Administration":
                            label = "SG&A"
                        elif pattern == "Research And Development":
                            label = "R&D"
                        elif pattern == "Depreciation And Amortization":
                            label = "DDA"

                        nodes.append(label)
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

        # Check for "Other Income (Expense)" - common in statements
        other_income_keys = [
            "Other Income Expense",
            "Other Non Operating Income Expenses",
            "Net Non Operating Interest Income Expense",
        ]
        other_income_key, other_income = find_key(other_income_keys)

        if operating_income_key:
            op_idx = node_map[operating_income_key]

            # Add "Other Income (Expense)" if present (like GuruFocus)
            if other_income_key and abs(other_income) / revenue > 0.001:  # Even tiny amounts
                nodes.append("Other Income (Expense)")
                # Red for expense, green for income
                other_color = colors["expense"] if other_income < 0 else colors["profit"]
                node_colors.append(other_color)
                node_map["Other Income (Expense)"] = len(nodes) - 1
                flows.append((op_idx, node_map["Other Income (Expense)"], abs(other_income)))

            if interest_key and interest > 0 and interest / revenue > 0.005:
                nodes.append("Interest Expense")
                node_colors.append(colors["expense"])
                node_map["Interest Expense"] = len(nodes) - 1
                flows.append((op_idx, node_map["Interest Expense"], interest))

            if tax_key and tax > 0 and tax / revenue > 0.005:
                nodes.append("Tax")
                node_colors.append(colors["tax"])
                node_map["Tax"] = len(nodes) - 1
                flows.append((op_idx, node_map["Tax"], tax))

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
            annotations=[
                {
                    "text": (
                        "<b>Color Key:</b><br>"
                        f"<span style='color:{colors['revenue']}'>● Revenue</span> | "
                        f"<span style='color:{colors['expense']}'>● Expenses</span> | "
                        f"<span style='color:{colors['profit']}'>● Profit</span><br>"
                        f"<span style='color:{colors['operating']}'>● Operating</span> | "
                        f"<span style='color:{colors['tax']}'>● Tax</span> | "
                        f"<span style='color:{colors['final']}'>● Net Income</span>"
                    ),
                    "xref": "paper",
                    "yref": "paper",
                    "x": 0.5,
                    "y": -0.1,
                    "showarrow": False,
                    "font": {"size": 9},
                    "align": "center",
                }
            ],
        )

        return fig

    except Exception as e:
        logger.warning("Error creating income statement Sankey: %s", str(e))
        return create_empty_sankey()


def create_cashflow_sankey(data):
    """Create dynamic Sankey diagram matching GuruFocus cash flow structure"""
    try:
        # Extract all items from the cash flow statement
        items = {k: v for k, v in data.items() if pd.notna(v) and v != 0}

        # Key patterns for cash flow components (GuruFocus structure)
        net_income_keys = [
            "Net Income From Continuing Operations",
            "Net Income",
            "Net Income Common Stockholders",
        ]
        operating_cf_keys = ["Operating Cash Flow", "Cash Flow From Operating Activities"]
        free_cf_keys = ["Free Cash Flow"]
        investing_cf_keys = ["Investing Cash Flow", "Cash Flow From Investing Activities"]
        financing_cf_keys = ["Financing Cash Flow", "Cash Flow From Financing Activities"]

        # Find key totals
        def find_key(key_list):
            for key in key_list:
                if key in items:
                    return key, items[key]
            return None, 0

        net_income_key, net_income = find_key(net_income_keys)
        operating_cf_key, operating_cf = find_key(operating_cf_keys)
        free_cf_key, free_cf = find_key(free_cf_keys)
        investing_cf_key, investing_cf = find_key(investing_cf_keys)
        financing_cf_key, financing_cf = find_key(financing_cf_keys)

        # Calculate free cash flow if not provided
        capex = abs(items.get("Capital Expenditure", 0))
        if free_cf == 0 and operating_cf != 0:
            free_cf = operating_cf - capex

        if operating_cf == 0 and net_income == 0:
            return create_empty_sankey()

        # Build nodes and flows dynamically (GuruFocus left-to-right flow)
        nodes = []
        node_colors = []
        flows = []
        node_map = {}

        # Color palette for cash flow (GuruFocus style)
        colors = {
            "positive": "#06A77D",  # Teal (inflow)
            "negative": "#BC4B51",  # Red (outflow)
            "operating": "#2E86AB",  # Blue
            "investing": "#F18F01",  # Orange
            "financing": "#9B59B6",  # Purple
            "neutral": "#2D6A4F",  # Dark green
            "beginning": "#90E0EF",  # Light blue
        }

        # Start with Net Income (if available)
        start_idx = None
        if net_income_key and abs(net_income) > 0:
            nodes.append("NI from Cont. Operations")
            node_colors.append(colors["positive"] if net_income > 0 else colors["negative"])
            node_map["NI"] = len(nodes) - 1
            start_idx = node_map["NI"]

        # Operating Inflow node
        if operating_cf > 0:
            nodes.append("Operating Inflow")
            node_colors.append(colors["operating"])
            node_map["Operating Inflow"] = len(nodes) - 1

            if start_idx is not None:
                flows.append((start_idx, node_map["Operating Inflow"], abs(net_income)))

            # Operating Outflow components from Operating Inflow
            # DDA (Depreciation, Depletion, Amortization)
            dda = abs(items.get("Depreciation And Amortization", 0))
            if dda > 0 and dda / abs(operating_cf) > 0.01:
                nodes.append("DDA")
                node_colors.append(colors["neutral"])
                node_map["DDA"] = len(nodes) - 1
                flows.append((node_map["Operating Inflow"], node_map["DDA"], dda))

            # Stock-based compensation
            stock_comp = abs(items.get("Stock Based Compensation", 0))
            if stock_comp > 0 and stock_comp / abs(operating_cf) > 0.01:
                nodes.append("Stock Compensation")
                node_colors.append(colors["neutral"])
                node_map["Stock Compensation"] = len(nodes) - 1
                flows.append(
                    (node_map["Operating Inflow"], node_map["Stock Compensation"], stock_comp)
                )

            # Working capital changes
            wc_change = abs(items.get("Change In Working Capital", 0))
            if wc_change > 0 and wc_change / abs(operating_cf) > 0.02:
                nodes.append("Change in WC")
                node_colors.append(colors["neutral"])
                node_map["Change in WC"] = len(nodes) - 1
                flows.append((node_map["Operating Inflow"], node_map["Change in WC"], wc_change))

        # Operating Outflow node (expenses)
        if operating_cf < 0:
            nodes.append("Operating Outflow")
            node_colors.append(colors["negative"])
            node_map["Operating Outflow"] = len(nodes) - 1

            if start_idx is not None:
                flows.append((start_idx, node_map["Operating Outflow"], abs(operating_cf)))

        # CF from Operations node
        if operating_cf_key and abs(operating_cf) > 0:
            nodes.append("CF from Operations")
            node_colors.append(colors["positive"] if operating_cf > 0 else colors["negative"])
            node_map["CF from Operations"] = len(nodes) - 1

            if "Operating Inflow" in node_map:
                flows.append(
                    (
                        node_map["Operating Inflow"],
                        node_map["CF from Operations"],
                        abs(operating_cf),
                    )
                )
            elif "Operating Outflow" in node_map:
                flows.append(
                    (
                        node_map["Operating Outflow"],
                        node_map["CF from Operations"],
                        abs(operating_cf),
                    )
                )

        # Free Cash Flow node (Operating CF - CapEx)
        if free_cf != 0 and capex > 0:
            # CapEx node
            nodes.append("CapEx")
            node_colors.append(colors["negative"])
            node_map["CapEx"] = len(nodes) - 1

            if "CF from Operations" in node_map:
                flows.append((node_map["CF from Operations"], node_map["CapEx"], capex))

            # Free Cash Flow
            nodes.append("Free Cash Flow")
            node_colors.append(colors["positive"] if free_cf > 0 else colors["negative"])
            node_map["Free Cash Flow"] = len(nodes) - 1

            if "CF from Operations" in node_map:
                flows.append(
                    (node_map["CF from Operations"], node_map["Free Cash Flow"], abs(free_cf))
                )

        # Investing activities (beyond CapEx)
        if investing_cf_key and abs(investing_cf) > 0:
            # Investing Inflow/Outflow
            if investing_cf > 0:
                nodes.append("Investing Inflow")
                node_colors.append(colors["positive"])
                node_map["Investing Inflow"] = len(nodes) - 1
                inv_node_idx = node_map["Investing Inflow"]
            else:
                nodes.append("Investing Outflow")
                node_colors.append(colors["investing"])
                node_map["Investing Outflow"] = len(nodes) - 1
                inv_node_idx = node_map["Investing Outflow"]

            # Net Investment P&S
            net_inv = abs(items.get("Net Investment Purchase And Sale", 0))
            if net_inv > 0 and net_inv / abs(investing_cf) > 0.1:
                nodes.append("Net Investment P&S")
                node_colors.append(colors["neutral"])
                node_map["Net Investment P&S"] = len(nodes) - 1
                flows.append((inv_node_idx, node_map["Net Investment P&S"], net_inv))

            # Other investing activities
            other_inv = abs(items.get("Other Investing Activities", 0))
            if other_inv > 0 and other_inv / abs(investing_cf) > 0.05:
                nodes.append("Other Investing Activities")
                node_colors.append(colors["neutral"])
                node_map["Other Investing Activities"] = len(nodes) - 1
                flows.append((inv_node_idx, node_map["Other Investing Activities"], other_inv))

        # Financing activities
        if financing_cf_key and abs(financing_cf) > 0:
            # Financing Inflow/Outflow
            if financing_cf > 0:
                nodes.append("Financing Inflow")
                node_colors.append(colors["positive"])
                node_map["Financing Inflow"] = len(nodes) - 1
                fin_node_idx = node_map["Financing Inflow"]
            else:
                nodes.append("Financing Outflow")
                node_colors.append(colors["financing"])
                node_map["Financing Outflow"] = len(nodes) - 1
                fin_node_idx = node_map["Financing Outflow"]

            # Net Issuance of Stock
            net_stock = items.get("Net Issuance Of Stock", 0)
            if abs(net_stock) > 0 and abs(net_stock) / abs(financing_cf) > 0.05:
                nodes.append("Net Issuance of Stock")
                node_colors.append(colors["positive"] if net_stock > 0 else colors["negative"])
                node_map["Net Issuance of Stock"] = len(nodes) - 1
                flows.append((fin_node_idx, node_map["Net Issuance of Stock"], abs(net_stock)))

            # Net Issuance of Debt
            net_debt = items.get("Net Issuance Of Debt", 0)
            if abs(net_debt) > 0 and abs(net_debt) / abs(financing_cf) > 0.05:
                nodes.append("Net Issuance of Debt")
                node_colors.append(colors["positive"] if net_debt > 0 else colors["negative"])
                node_map["Net Issuance of Debt"] = len(nodes) - 1
                flows.append((fin_node_idx, node_map["Net Issuance of Debt"], abs(net_debt)))

            # Dividends
            dividends = abs(items.get("Cash Dividends Paid", 0))
            if dividends > 0 and dividends / abs(financing_cf) > 0.05:
                nodes.append("Dividends")
                node_colors.append(colors["negative"])
                node_map["Dividends"] = len(nodes) - 1
                flows.append((fin_node_idx, node_map["Dividends"], dividends))

            # Other Financing Activities
            other_fin = abs(items.get("Other Financing Activities", 0))
            if other_fin > 0 and other_fin / abs(financing_cf) > 0.05:
                nodes.append("Other Financing Activities")
                node_colors.append(colors["neutral"])
                node_map["Other Financing Activities"] = len(nodes) - 1
                flows.append((fin_node_idx, node_map["Other Financing Activities"], other_fin))

        # Net Change in Cash
        net_change = operating_cf + investing_cf + financing_cf
        if abs(net_change) > 0:
            nodes.append("Net Change in Cash")
            node_colors.append(colors["positive"] if net_change > 0 else colors["negative"])
            node_map["Net Change in Cash"] = len(nodes) - 1

            # Connect from Free Cash Flow if available, else CF from Operations
            if "Free Cash Flow" in node_map:
                flows.append(
                    (node_map["Free Cash Flow"], node_map["Net Change in Cash"], abs(net_change))
                )
            elif "CF from Operations" in node_map:
                flows.append(
                    (
                        node_map["CF from Operations"],
                        node_map["Net Change in Cash"],
                        abs(net_change),
                    )
                )

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
            annotations=[
                {
                    "text": (
                        "<b>Color Key:</b><br>"
                        f"<span style='color:{colors['positive']}'>● Inflows</span> | "
                        f"<span style='color:{colors['negative']}'>● Outflows</span> | "
                        f"<span style='color:{colors['operating']}'>● Operating</span><br>"
                        f"<span style='color:{colors['investing']}'>● Investing</span> | "
                        f"<span style='color:{colors['financing']}'>● Financing</span>"
                    ),
                    "xref": "paper",
                    "yref": "paper",
                    "x": 0.5,
                    "y": -0.08,
                    "showarrow": False,
                    "font": {"size": 9},
                    "align": "center",
                }
            ],
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

        # Calculate Total Liabilities (consolidation node)
        total_liabilities = 0
        current_liabilities_val = 0
        non_current_liabilities_val = 0

        # Find liability values
        for key in [
            "Current Liabilities",
            "Total Current Liabilities",
        ]:
            if key in items and key not in excluded:
                current_liabilities_val = items[key]
                excluded.add(key)
                break

        for key in [
            "Total Non Current Liabilities Net Minority Interest",
            "Long Term Debt",
            "Total Debt",
        ]:
            if key in items and key not in excluded:
                non_current_liabilities_val = items[key]
                excluded.add(key)
                break

        total_liabilities = current_liabilities_val + non_current_liabilities_val

        # Add Total Liabilities consolidation node
        if total_liabilities > 0:
            nodes.append("Total Liabilities")
            node_colors.append(colors["current_liabilities"])
            node_map["Total Liabilities"] = len(nodes) - 1
            flows.append(
                (node_map[total_assets_key], node_map["Total Liabilities"], total_liabilities)
            )

            # Add breakdown from Total Liabilities
            if current_liabilities_val > 0:
                nodes.append("Current Liabilities")
                node_colors.append(colors["current_liabilities"])
                node_map["Current Liabilities"] = len(nodes) - 1
                flows.append(
                    (
                        node_map["Total Liabilities"],
                        node_map["Current Liabilities"],
                        current_liabilities_val,
                    )
                )

            if non_current_liabilities_val > 0:
                nodes.append("Long-Term Debt")
                node_colors.append(colors["non_current_liabilities"])
                node_map["Long-Term Debt"] = len(nodes) - 1
                flows.append(
                    (
                        node_map["Total Liabilities"],
                        node_map["Long-Term Debt"],
                        non_current_liabilities_val,
                    )
                )

        # Calculate Total Equity (consolidation node)
        total_equity = 0
        stockholders_equity_val = 0
        retained_earnings_val = 0
        common_stock_val = 0

        # Find equity values
        for key in [
            "Stockholders Equity",
            "Total Equity Gross Minority Interest",
            "Common Stock Equity",
        ]:
            if key in items and key not in excluded:
                stockholders_equity_val = items[key]
                excluded.add(key)
                break

        if "Retained Earnings" in items and "Retained Earnings" not in excluded:
            retained_earnings_val = items["Retained Earnings"]
            excluded.add("Retained Earnings")

        if "Common Stock" in items and "Common Stock" not in excluded:
            common_stock_val = items["Common Stock"]
            excluded.add("Common Stock")

        # Use stockholders equity as total if available, otherwise sum components
        if stockholders_equity_val > 0:
            total_equity = stockholders_equity_val
        else:
            total_equity = retained_earnings_val + common_stock_val

        # Add Total Equity consolidation node
        if total_equity > 0:
            nodes.append("Total Equity")
            node_colors.append(colors["equity"])
            node_map["Total Equity"] = len(nodes) - 1
            flows.append((node_map[total_assets_key], node_map["Total Equity"], total_equity))

            # Add breakdown from Total Equity if components are significant
            if retained_earnings_val > 0 and abs(retained_earnings_val / total_equity) > 0.15:
                nodes.append("Retained Earnings")
                node_colors.append(colors["equity"])
                node_map["Retained Earnings"] = len(nodes) - 1
                flows.append(
                    (
                        node_map["Total Equity"],
                        node_map["Retained Earnings"],
                        retained_earnings_val,
                    )
                )

            if common_stock_val > 0 and common_stock_val / total_equity > 0.15:
                nodes.append("Common Stock")
                node_colors.append(colors["equity"])
                node_map["Common Stock"] = len(nodes) - 1
                flows.append((node_map["Total Equity"], node_map["Common Stock"], common_stock_val))

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
            annotations=[
                {
                    "text": (
                        "<b>Color Key:</b><br>"
                        "<b>Assets:</b> "
                        f"<span style='color:{colors['current_assets']}'>● Current</span> | "
                        f"<span style='color:{colors['non_current_assets']}'>● Non-Current</span><br>"
                        "<b>Liabilities:</b> "
                        f"<span style='color:{colors['current_liabilities']}'>● Current</span> | "
                        f"<span style='color:{colors['non_current_liabilities']}'>● Long-Term</span><br>"
                        "<b>Equity:</b> "
                        f"<span style='color:{colors['equity']}'>● Shareholders' Equity</span>"
                    ),
                    "xref": "paper",
                    "yref": "paper",
                    "x": 0.5,
                    "y": -0.08,
                    "showarrow": False,
                    "font": {"size": 9},
                    "align": "center",
                }
            ],
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
        if ratio_name in historical_ratios.columns:
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
        else:
            logger.warning(
                "Ratio '%s' not found in historical_ratios DataFrame columns.",
                ratio_name,
            )
            fig.add_annotation(
                text=f"Ratio '{ratio_name}' not found in data",
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5,
                showarrow=False,
                font={"size": 14, "color": "gray"},
            )

    fig.update_layout(
        title=f"{ratio_name} Trend",
        xaxis_title="Period",
        yaxis_title=ratio_name,
        height=300,
        hovermode="x unified",
    )

    return fig

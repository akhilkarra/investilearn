"""Visualization utilities for financial data"""

import plotly.graph_objects as go


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
    """Create Sankey diagram for income statement"""
    try:
        # Extract key metrics (handle missing data gracefully)
        revenue = abs(data.get("Total Revenue", 0))
        cogs = abs(data.get("Cost Of Revenue", 0))
        operating_expenses = abs(data.get("Operating Expense", 0))
        net_income = abs(data.get("Net Income", 0))

        if revenue == 0:
            return create_empty_sankey()

        # Calculate gross profit
        gross_profit = revenue - cogs

        # Define nodes
        nodes = [
            "Revenue",
            "Cost of Goods Sold",
            "Gross Profit",
            "Operating Expenses",
            "Net Income",
        ]

        # Define flows (source, target, value)
        flows = []

        if cogs > 0:
            flows.append((0, 1, cogs))  # Revenue -> COGS
            flows.append((0, 2, gross_profit))  # Revenue -> Gross Profit

        if operating_expenses > 0 and gross_profit > 0:
            flows.append((2, 3, operating_expenses))  # Gross Profit -> OpEx
            flows.append((2, 4, net_income))  # Gross Profit -> Net Income

        if not flows:
            return create_empty_sankey()

        # Create Sankey diagram
        fig = go.Figure(
            data=[
                go.Sankey(
                    node={
                        "pad": 15,
                        "thickness": 20,
                        "line": {"color": "black", "width": 0.5},
                        "label": nodes,
                        "color": ["#3498db", "#e74c3c", "#2ecc71", "#e67e22", "#27ae60"],
                    },
                    link={
                        "source": [f[0] for f in flows],
                        "target": [f[1] for f in flows],
                        "value": [f[2] for f in flows],
                        "color": ["rgba(52, 152, 219, 0.3)" for _ in flows],
                    },
                )
            ]
        )

        fig.update_layout(title="Income Statement Flow", font={"size": 10}, height=400)

        return fig

    except Exception:
        return create_empty_sankey()


def create_cashflow_sankey(data):
    """Create Sankey diagram for cash flow statement"""
    try:
        # Extract cash flow components
        operating_cf = data.get("Operating Cash Flow", 0)
        investing_cf = data.get("Investing Cash Flow", 0)
        financing_cf = data.get("Financing Cash Flow", 0)

        # Use absolute values for visualization
        op_abs = abs(operating_cf)
        inv_abs = abs(investing_cf)
        fin_abs = abs(financing_cf)

        if op_abs == 0 and inv_abs == 0 and fin_abs == 0:
            return create_empty_sankey()

        nodes = ["Cash In", "Operating", "Investing", "Financing", "Cash Out"]
        flows = []

        # Simplified flow representation
        if operating_cf > 0:
            flows.append((0, 1, op_abs))
        if investing_cf != 0:
            flows.append((1, 2, inv_abs))
        if financing_cf != 0:
            flows.append((1, 3, fin_abs))

        if not flows:
            return create_empty_sankey()

        fig = go.Figure(
            data=[
                go.Sankey(
                    node={
                        "pad": 15,
                        "thickness": 20,
                        "line": {"color": "black", "width": 0.5},
                        "label": nodes,
                        "color": ["#3498db", "#2ecc71", "#e67e22", "#9b59b6", "#e74c3c"],
                    },
                    link={
                        "source": [f[0] for f in flows],
                        "target": [f[1] for f in flows],
                        "value": [f[2] for f in flows],
                    },
                )
            ]
        )

        fig.update_layout(title="Cash Flow Movement", font={"size": 10}, height=400)

        return fig

    except Exception:
        return create_empty_sankey()


def create_balance_sankey(data):
    """Create Sankey diagram for balance sheet"""
    try:
        # Extract balance sheet components
        total_assets = abs(data.get("Total Assets", 0))
        total_liabilities = abs(data.get("Total Liabilities Net Minority Interest", 0))
        stockholder_equity = abs(data.get("Stockholders Equity", 0))

        if total_assets == 0:
            return create_empty_sankey()

        nodes = ["Total Assets", "Liabilities", "Equity"]
        flows = [(0, 1, total_liabilities), (0, 2, stockholder_equity)]

        fig = go.Figure(
            data=[
                go.Sankey(
                    node={
                        "pad": 15,
                        "thickness": 20,
                        "line": {"color": "black", "width": 0.5},
                        "label": nodes,
                        "color": ["#3498db", "#e74c3c", "#2ecc71"],
                    },
                    link={
                        "source": [f[0] for f in flows],
                        "target": [f[1] for f in flows],
                        "value": [f[2] for f in flows],
                    },
                )
            ]
        )

        fig.update_layout(title="Balance Sheet Structure", font={"size": 10}, height=400)

        return fig

    except Exception:
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

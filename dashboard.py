from datetime import datetime

import streamlit as st

# Import utility functions
from utils.data_fetcher import (
    get_financial_statements,
    get_news,
    get_stock_info,
)
from utils.ratio_calculator import calculate_ratios, format_ratio_value, get_ratio_metrics
from utils.visualizations import create_sankey_diagram

# Page configuration
st.set_page_config(page_title="Fundamental Investment Dashboard", page_icon="📈", layout="wide")

# Title and description
st.title("📊 Fundamental Investment Dashboard")
st.markdown(
    """
Welcome to your long-term investment research tool. Search for companies to analyze their
financial health, key ratios, and stay updated with relevant news.
"""
)

# Search bar
st.markdown("---")
search_query = st.text_input(
    "🔍 Search for a company or ticker symbol",
    placeholder="e.g., Apple, AAPL, Microsoft, etc.",
    help="Enter a company name or stock ticker to begin your analysis",
)

# Filter options
with st.expander("🎯 Advanced Filters (Optional)"):
    col_filter1, col_filter2, col_filter3 = st.columns(3)

    with col_filter1:
        industry = st.selectbox(
            "Industry",
            [
                "All Industries",
                "Technology",
                "Healthcare",
                "Finance",
                "Consumer Goods",
                "Energy",
                "Industrials",
                "Real Estate",
                "Utilities",
            ],
        )

    with col_filter2:
        market_cap = st.selectbox(
            "Market Cap",
            ["All Sizes", "Large Cap (>$10B)", "Mid Cap ($2B-$10B)", "Small Cap (<$2B)"],
        )

    with col_filter3:
        esg_priority = st.checkbox("Prioritize ESG/Low Carbon Emissions")

# Main content area (only show if search query exists)
if search_query:
    # Fetch stock data
    with st.spinner(f"Fetching data for {search_query}..."):
        stock, info = get_stock_info(search_query)

    if stock and info:
        # Display company header
        company_name = info.get("longName", search_query)
        st.markdown("---")

        # Company info header
        col_header1, col_header2, col_header3, col_header4 = st.columns(4)
        with col_header1:
            st.metric("Company", company_name)
        with col_header2:
            price = info.get("currentPrice", info.get("regularMarketPrice", "N/A"))
            prev_close = info.get("previousClose", 0)
            change = (
                ((price - prev_close) / prev_close * 100) if (price != "N/A" and prev_close) else 0
            )
            st.metric("Price", f"${price:.2f}" if price != "N/A" else "N/A", f"{change:+.2f}%")
        with col_header3:
            market_cap = info.get("marketCap", 0)
            st.metric("Market Cap", f"${market_cap / 1e9:.2f}B" if market_cap else "N/A")
        with col_header4:
            sector = info.get("sector", "N/A")
            st.metric("Sector", sector)

        # Get financial statements
        income_stmt, balance_sheet, cash_flow = get_financial_statements(search_query)

        # Calculate ratios
        ratios = calculate_ratios(info, income_stmt, balance_sheet)

        st.markdown("---")

        # Three column layout
        col1, col2, col3 = st.columns([1, 1, 1])

        # Left Column: Financial Statements (Sankey Diagrams)
        with col1:
            st.markdown("### 📊 Financial Statements")
            st.markdown("*Sankey flow diagrams showing money movement*")

            # Tabs for different financial statements
            tab1, tab2, tab3 = st.tabs(["Income Statement", "Cash Flow", "Balance Sheet"])

            with tab1:
                st.info(
                    "💡 **Income Statement** shows how revenue flows through expenses to profit"
                )
                if income_stmt is not None:
                    fig = create_sankey_diagram(income_stmt, "income")
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("No income statement data available")

            with tab2:
                st.info("💡 **Cash Flow** tracks actual cash in and out of the business")
                if cash_flow is not None:
                    fig = create_sankey_diagram(cash_flow, "cashflow")
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("No cash flow data available")

            with tab3:
                st.info("💡 **Balance Sheet** shows what the company owns vs owes")
                if balance_sheet is not None:
                    fig = create_sankey_diagram(balance_sheet, "balance")
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("No balance sheet data available")

        # Middle Column: Key Ratios
        with col2:
            st.markdown("### 📐 Key Financial Ratios")
            st.markdown("*Compare company performance to industry trends*")

            # Ratio categories
            ratio_category = st.selectbox(
                "Select Ratio Category",
                ["Profitability", "Liquidity", "Efficiency", "Leverage", "Valuation"],
            )

            # Get metrics for the selected category
            info_text, metrics_list = get_ratio_metrics(ratio_category)

            st.markdown(f"#### {ratio_category} Ratios")
            st.info(info_text)

            # Display actual ratio values
            for ratio_key, ratio_display in metrics_list:
                value = ratios.get(ratio_key)
                formatted_value = format_ratio_value(value, ratio_key)

                col_m1, col_m2, col_m3 = st.columns(3)
                with col_m1:
                    if value is not None:
                        st.metric(ratio_display, formatted_value)
                    else:
                        st.metric(ratio_display, "N/A")
                with col_m2:
                    st.caption("vs Industry: N/A")
                with col_m3:
                    st.caption("vs 5Y Avg: N/A")

        # Right Column: News and Updates
        with col3:
            st.markdown("### 📰 Relevant News & Updates")
            st.markdown("*Stay informed with latest company developments*")

            # Fetch news
            news_items = get_news(search_query, max_items=10)

            # News filter (for future categorization)
            news_filter = st.radio(
                "News Type",
                ["All News", "Earnings Reports", "Press Releases", "Market Analysis"],
                horizontal=True,
            )

            # Display news items
            st.markdown("#### Recent Headlines")

            if news_items:
                for item in news_items[:5]:  # Show top 5 news items
                    with st.container():
                        title = item.get("title", "No title available")
                        publisher = item.get("publisher", "Unknown source")
                        link = item.get("link", "#")
                        published_time = item.get("providerPublishTime", 0)

                        # Format timestamp
                        if published_time:
                            date_str = datetime.fromtimestamp(published_time).strftime("%B %d, %Y")
                        else:
                            date_str = "Recent"

                        st.markdown(f"**📌 {title}**")
                        st.caption(f"{publisher} • {date_str}")

                        # Show link to article
                        st.markdown(f"[Read more →]({link})")
                        st.markdown("---")
            else:
                st.info("No recent news available for this ticker")

        # Additional sections below the main columns
        st.markdown("---")
        st.markdown("### 📚 Additional Resources")

        col_res1, col_res2, col_res3 = st.columns(3)

        with col_res1:
            st.markdown("#### 📄 SEC Filings")
            st.markdown("- 10-K Annual Report")
            st.markdown("- 10-Q Quarterly Report")
            st.markdown("- 8-K Current Report")
            st.markdown("- Proxy Statements")

        with col_res2:
            st.markdown("#### 📊 Historical Performance")
            st.markdown("- 5-Year Stock Chart")
            st.markdown("- Dividend History")
            st.markdown("- Earnings History")
            st.markdown("- Share Buyback Activity")

        with col_res3:
            st.markdown("#### 🎓 Learn More")
            st.markdown("- What is Fundamental Analysis?")
            st.markdown("- Understanding Financial Ratios")
            st.markdown("- Long-term Investment Strategies")
            st.markdown("- Reading Financial Statements")

    else:
        # If no stock found, show error message
        st.error(
            f"Could not find data for '{search_query}'. Please check the ticker symbol and try again."
        )
        st.info("💡 Tip: Try using the stock ticker symbol (e.g., 'AAPL' for Apple Inc.)")

else:
    # Show helpful information when no search is active
    st.markdown("---")
    st.info("👆 Enter a company name or ticker symbol above to begin your analysis")

    st.markdown("### 🎯 What is Fundamental Investing?")
    st.markdown(
        """
    Fundamental investing is a long-term investment strategy that focuses on analyzing a company's
    financial health, business model, and competitive advantages to identify high-quality companies
    worth holding for decades.

    **Key Principles:**
    - 📊 Analyze financial statements thoroughly
    - 📈 Focus on sustainable competitive advantages
    - ⏳ Think long-term (5-10+ years)
    - 💼 Invest in businesses you understand
    - 📉 Buy quality companies at reasonable prices
    """
    )

    st.markdown("### 🔍 How to Use This Dashboard")
    col_help1, col_help2, col_help3 = st.columns(3)

    with col_help1:
        st.markdown("**1️⃣ Search**")
        st.markdown("Enter a company name or ticker to analyze")

    with col_help2:
        st.markdown("**2️⃣ Analyze**")
        st.markdown("Review financial statements, ratios, and news")

    with col_help3:
        st.markdown("**3️⃣ Decide**")
        st.markdown("Make informed long-term investment decisions")

# Sidebar
with st.sidebar:
    st.markdown("## ⚙️ Settings")

    st.markdown("### Display Preferences")
    show_tooltips = st.checkbox("Show educational tooltips", value=True)
    currency = st.selectbox("Currency", ["USD", "EUR", "GBP", "JPY"])

    st.markdown("---")
    st.markdown("### 📊 Recommender Settings")
    st.markdown("*Coming soon: ML-powered company recommendations*")

    st.markdown("---")
    st.markdown("### 📖 Quick Guide")
    st.markdown(
        """
    **Financial Statements:**
    - Income Statement: Revenue & Profit
    - Cash Flow: Actual cash movement
    - Balance Sheet: Assets & Liabilities

    **Key Ratio Categories:**
    - Profitability: Earnings power
    - Liquidity: Short-term health
    - Efficiency: Asset utilization
    - Leverage: Debt levels
    - Valuation: Price vs value
    """
    )

    st.markdown("---")
    st.caption("Built for long-term fundamental investors 📈")

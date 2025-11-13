from datetime import datetime

import streamlit as st

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
    st.markdown("---")
    st.subheader(f"Analysis for: {search_query}")

    # Three column layout
    col1, col2, col3 = st.columns([1, 1, 1])

    # Left Column: Financial Statements (Sankey Diagrams)
    with col1:
        st.markdown("### 📊 Financial Statements")
        st.markdown("*Sankey flow diagrams showing money movement*")

        # Tabs for different financial statements
        tab1, tab2, tab3 = st.tabs(["Income Statement", "Cash Flow", "Balance Sheet"])

        with tab1:
            st.info("💡 **Income Statement** shows how revenue flows through expenses to profit")
            # Placeholder for Sankey diagram
            st.markdown("```\n📈 Income Statement Sankey\n(To be implemented)\n```")
            st.text("Revenue → Operating Expenses → Net Income")

        with tab2:
            st.info("💡 **Cash Flow** tracks actual cash in and out of the business")
            # Placeholder for Sankey diagram
            st.markdown("```\n💰 Cash Flow Sankey\n(To be implemented)\n```")
            st.text("Operating → Investing → Financing → Net Cash")

        with tab3:
            st.info("💡 **Balance Sheet** shows what the company owns vs owes")
            # Placeholder for Sankey diagram
            st.markdown("```\n⚖️ Balance Sheet Sankey\n(To be implemented)\n```")
            st.text("Assets = Liabilities + Equity")

    # Middle Column: Key Ratios
    with col2:
        st.markdown("### 📐 Key Financial Ratios")
        st.markdown("*Compare company performance to industry and historical trends*")

        # Ratio categories
        ratio_category = st.selectbox(
            "Select Ratio Category",
            ["Profitability", "Liquidity", "Efficiency", "Leverage", "Valuation"],
        )

        # Placeholder for ratio visualizations
        st.markdown(f"#### {ratio_category} Ratios")

        if ratio_category == "Profitability":
            st.info(
                "💡 **Profitability ratios** measure how efficiently a company generates profit"
            )
            metrics = [
                "ROE (Return on Equity)",
                "ROA (Return on Assets)",
                "Net Profit Margin",
                "Gross Profit Margin",
            ]
        elif ratio_category == "Liquidity":
            st.info("💡 **Liquidity ratios** assess ability to meet short-term obligations")
            metrics = ["Current Ratio", "Quick Ratio", "Cash Ratio"]
        elif ratio_category == "Efficiency":
            st.info("💡 **Efficiency ratios** show how well assets are being used")
            metrics = ["Asset Turnover", "Inventory Turnover", "Days Sales Outstanding"]
        elif ratio_category == "Leverage":
            st.info("💡 **Leverage ratios** indicate financial risk from debt")
            metrics = ["Debt-to-Equity", "Interest Coverage", "Debt Ratio"]
        else:  # Valuation
            st.info("💡 **Valuation ratios** help determine if stock is fairly priced")
            metrics = ["P/E Ratio", "P/B Ratio", "PEG Ratio", "Price-to-Sales"]

        # Display placeholder metrics
        for metric in metrics:
            col_m1, col_m2, col_m3 = st.columns(3)
            with col_m1:
                st.metric(metric, "N/A", help=f"{metric} - Data to be loaded")
            with col_m2:
                st.caption("vs Industry: N/A")
            with col_m3:
                st.caption("vs 5Y Avg: N/A")

        # Placeholder for comparison chart
        st.markdown("```\n📊 Historical Trend Chart\n(To be implemented)\n```")

    # Right Column: News and Updates
    with col3:
        st.markdown("### 📰 Relevant News & Updates")
        st.markdown("*Stay informed with latest company developments*")

        # News filter
        news_filter = st.radio(
            "News Type",
            ["All News", "Earnings Reports", "Press Releases", "Market Analysis"],
            horizontal=True,
        )

        # Placeholder for news items
        st.markdown("#### Recent Headlines")

        # Sample news item structure (placeholder)
        for i in range(5):
            with st.container():
                st.markdown(f"**📌 News Headline {i+1}**")
                st.caption(f"Source • {datetime.now().strftime('%B %d, %Y')}")
                st.markdown("Brief summary of the news article will appear here...")
                st.markdown("[Read more →](#)")
                st.markdown("---")

        st.info("💡 News data will be fetched from financial APIs")

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

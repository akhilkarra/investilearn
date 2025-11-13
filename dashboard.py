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


# Helper function to track AI feedback (HAX Guideline G15, G17)
def log_feedback(feedback_type, context, sentiment="neutral"):
    """Track user feedback for AI improvements."""
    if "interaction_log" in st.session_state:
        st.session_state.interaction_log.append(
            {
                "timestamp": datetime.now(),
                "type": feedback_type,
                "context": context,
                "sentiment": sentiment,
            }
        )
    if "feedback_count" in st.session_state:
        st.session_state.feedback_count += 1


# Page configuration
st.set_page_config(page_title="Fundamental Investment Dashboard", page_icon="📈", layout="wide")

# Custom CSS for AI badges and styling
st.markdown(
    """
<style>
.ai-badge {
    background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 2px 8px;
    border-radius: 12px;
    font-size: 11px;
    font-weight: 600;
    display: inline-block;
    margin-left: 8px;
}
.confidence-high { color: #10b981; font-weight: 600; }
.confidence-medium { color: #f59e0b; font-weight: 600; }
.confidence-low { color: #ef4444; font-weight: 600; }
</style>
""",
    unsafe_allow_html=True,
)

# Initialize session state for AI interactions (HAX Guideline G15)
if "feedback_count" not in st.session_state:
    st.session_state.feedback_count = 0
if "interaction_log" not in st.session_state:
    st.session_state.interaction_log = []
if "first_visit" not in st.session_state:
    st.session_state.first_visit = True

# Title and description
st.title("📊 Fundamental Investment Dashboard")
st.markdown(
    """
Welcome to your long-term investment research tool. Search for companies to analyze their
financial health, key ratios, and stay updated with relevant news.
"""
)

# AI Features disclosure (HAX Guideline G1: Make clear what the system can do)
st.info(
    """
🤖 **AI-Powered Features Coming Soon:**
- **Smart News Curation:** ML will recommend articles most relevant to your analysis focus
- **Interactive Learning Guide:** Ask questions about any metric or concept to learn as you explore
- **Context-Aware Hints:** Get explanations based on what you're currently viewing

⚠️ **Important:** This tool provides educational information only and does not constitute investment advice,
financial planning services, or securities recommendations. Always conduct your own due diligence and
consult with a licensed financial advisor before making investment decisions.
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
        info = get_stock_info(search_query)

    if info:
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
            try:
                if price != "N/A" and prev_close != 0:
                    change = (price - prev_close) / prev_close * 100
                else:
                    change = 0
            except (TypeError, ZeroDivisionError):
                change = 0
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

            # Display actual ratio values with contextual help
            for ratio_key, ratio_display in metrics_list:
                value = ratios.get(ratio_key)
                formatted_value = format_ratio_value(value, ratio_key)

                # Create 4 columns: metric, industry, 5Y avg, help button
                col_m1, col_m2, col_m3, col_m4 = st.columns([3, 2, 2, 1])
                with col_m1:
                    if value is not None:
                        st.metric(ratio_display, formatted_value)
                    else:
                        st.metric(ratio_display, "N/A")
                with col_m2:
                    st.caption("vs Industry: N/A")
                with col_m3:
                    st.caption("vs 5Y Avg: N/A")
                with col_m4:
                    # Help button for contextual guide (HAX Guideline G7)
                    help_key = f"help_{ratio_key}_{search_query}"
                    if st.button("❓", key=help_key, help="Ask guide about this"):
                        st.session_state[f"guide_query_{ratio_key}"] = True

                # Show contextual explanation if help was clicked
                if st.session_state.get(f"guide_query_{ratio_key}", False):
                    with st.expander(f"💡 Learn about {ratio_display}", expanded=True):
                        st.markdown(
                            '<span class="ai-badge">AI Guide</span>', unsafe_allow_html=True
                        )

                        # Placeholder explanations (will be replaced with AI)
                        ratio_explanations = {
                            "ROE": f"""
                                **Return on Equity (ROE)** measures how efficiently
                                {company_name} uses shareholder money to generate profit.

                                **Calculation:** Net Income ÷ Shareholder Equity

                                **{company_name}'s ROE:** {formatted_value}

                                **What this means:**
                                - ROE > 15%: Generally considered good
                                - ROE < 10%: May indicate inefficiency
                                - Compare to industry peers for context

                                💡 *This is educational content.
                                AI guide will provide deeper, contextual analysis.*
                            """,
                            "ROA": f"""
                                **Return on Assets (ROA)** shows how profitable
                                {company_name} is relative to its total assets.

                                **Calculation:** Net Income ÷ Total Assets

                                **{company_name}'s ROA:** {formatted_value}

                                💡 *AI guide will provide sector-specific benchmarks.*
                            """,
                        }

                        explanation = ratio_explanations.get(
                            ratio_key,
                            f"""
                            **{ratio_display}** for {company_name}: {formatted_value}

                            💡 *AI guide coming soon with detailed explanations!*
                            """,
                        )

                        st.markdown(explanation)

                        # Feedback buttons (HAX Guideline G9, G17)
                        col_f1, col_f2, col_f3 = st.columns([1, 1, 3])
                        with col_f1:
                            if st.button("👍 Helpful", key=f"helpful_{ratio_key}_{search_query}"):
                                log_feedback(
                                    "guide_explanation",
                                    {"ratio": ratio_key, "ticker": search_query},
                                    "positive",
                                )
                                st.success("Thanks for the feedback!")
                        with col_f2:
                            if st.button(
                                "👎 Not helpful", key=f"not_helpful_{ratio_key}_{search_query}"
                            ):
                                log_feedback(
                                    "guide_explanation",
                                    {"ratio": ratio_key, "ticker": search_query},
                                    "negative",
                                )
                                st.info("We'll improve this explanation!")

                        # Close button
                        if st.button("✕ Close", key=f"close_{ratio_key}_{search_query}"):
                            st.session_state[f"guide_query_{ratio_key}"] = False
                            st.rerun()

        # Right Column: News and Updates
        with col3:
            # AI badge in title (HAX Guideline G1)
            st.markdown(
                '### 📰 Relevant News & Updates <span class="ai-badge">AI Ready</span>',
                unsafe_allow_html=True,
            )
            st.markdown("*Stay informed with latest company developments*")

            # Fetch news
            news_items = get_news(search_query, max_items=10)

            # News filter (for future categorization)
            news_filter = st.radio(
                "News Type",
                ["All News", "Earnings Reports", "Press Releases", "Market Analysis"],
                horizontal=True,
            )

            # Filter news items based on selected filter
            if news_filter != "All News" and news_items:
                filter_keywords = {
                    "Earnings Reports": ["earnings", "results", "quarter", "q1", "q2", "q3", "q4"],
                    "Press Releases": ["press release", "announces", "announcement"],
                    "Market Analysis": ["analysis", "market", "outlook", "forecast", "trend"],
                }
                keywords = filter_keywords.get(news_filter, [])
                filtered_news_items = [
                    item
                    for item in news_items
                    if any(
                        kw.lower()
                        in (item.get("title", "") + " " + item.get("summary", "")).lower()
                        for kw in keywords
                    )
                ]
            else:
                filtered_news_items = news_items

            # Display news items
            st.markdown("#### Recent Headlines")

            if filtered_news_items:
                # Temporary note until ML is implemented
                st.caption(
                    "📊 Currently showing recent news. "
                    "AI curation will prioritize relevance to your analysis."
                )

                for item in filtered_news_items[:5]:  # Show top 5 news items
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

                        # Transparency placeholder (HAX Guideline G11)
                        # Will be replaced with actual ML reasoning
                        with st.expander("🔍 Why is this shown?", expanded=False):
                            st.caption(
                                """
                                **Current:** Showing recent news chronologically

                                **Coming soon - AI will explain:**
                                - Relevance score to your current analysis
                                - Matched keywords and topics
                                - Source credibility rating
                                - Sentiment balance considerations
                                """
                            )

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

    # First-time user guided experience (HAX Guideline G3)
    if st.session_state.first_visit:
        st.success("👋 Welcome to InvestiLearn!")
        st.markdown(
            """
            This dashboard helps you learn fundamental investing by analyzing
            real company data. Let's get started with a quick tour:
            """
        )

        col_tour1, col_tour2, col_tour3 = st.columns(3)

        with col_tour1:
            st.info(
                """
                **1️⃣ Start Simple**

                Search for a company you know
                (like Apple, Microsoft, or Tesla)
                """
            )

        with col_tour2:
            st.info(
                """
                **2️⃣ Explore with AI**

                Click ❓ buttons to learn about
                any metric you don't understand
                """
            )

        with col_tour3:
            st.info(
                """
                **3️⃣ Give Feedback**

                Help improve the AI by rating
                explanations helpful or not
                """
            )

        if st.button("Got it! Let's explore 🚀"):
            st.session_state.first_visit = False
            st.rerun()

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

    # AI Features Toggle (HAX Guideline G18: Convey consequences)
    st.markdown("### 🤖 AI Features")
    ai_enabled = st.checkbox(
        "Enable AI assistance",
        value=True,
        help="Turn on AI-powered news curation and learning guide",
    )

    if ai_enabled:
        st.success("✓ AI features active")
        st.caption(
            "💡 Your interactions help improve recommendations. No personal data is collected."
        )

        # Show AI confidence level preference (HAX Guideline G2)
        confidence_level = st.select_slider(
            "AI confidence threshold",
            options=["Show all", "Medium+", "High only"],
            value="Show all",
            help="Filter AI suggestions by confidence level",
        )

        if confidence_level != "Show all":
            st.caption(f"Only showing {confidence_level} confidence suggestions")
    else:
        st.info("AI features disabled. Showing raw data only.")

    st.markdown("---")
    st.markdown("### Display Preferences")
    show_tooltips = st.checkbox("Show educational tooltips", value=True)
    currency = st.selectbox("Currency", ["USD", "EUR", "GBP", "JPY"])

    # Beginner mode toggle (HAX Guideline G3: Progressive disclosure)
    beginner_mode = st.checkbox(
        "Beginner mode", value=False, help="Simplified view with guided explanations"
    )

    if beginner_mode:
        st.caption("🎓 Showing simplified metrics with learning hints")

    st.markdown("---")

    # AI Guide section with badge
    st.markdown(
        '### � AI Learning Guide <span class="ai-badge">Beta</span>', unsafe_allow_html=True
    )

    if ai_enabled:
        st.markdown(
            """
            **How to use:**
            - Click ❓ next to any metric
            - Get instant explanations
            - Ask follow-up questions (coming soon)

            **Confidence Indicators:**
            - <span class="confidence-high">🟢 High</span>:
              Well-established concepts
            - <span class="confidence-medium">🟡 Medium</span>:
              Context-dependent
            - <span class="confidence-low">🔴 Low</span>:
              Consult an expert
            """,
            unsafe_allow_html=True,
        )

        # Feedback summary (HAX Guideline G15: Learn from behavior)
        if "feedback_count" in st.session_state:
            st.caption(
                f"📊 You've provided {st.session_state.feedback_count} pieces of feedback. Thanks!"
            )
    else:
        st.info("Enable AI features above to use the guide")

    st.markdown("---")

    # Transparency section (HAX Guideline G11)
    with st.expander("🔍 How AI Works Here"):
        st.caption(
            """
            **News Curation:**
            - Analyzes article relevance to your search
            - Balances sentiment and source diversity
            - Updates recommendations as you interact

            **Learning Guide:**
            - Trained on financial education materials
            - Provides context-specific explanations
            - Cites sources when available

            **What we DON'T do:**
            - Make investment recommendations
            - Predict stock prices
            - Guarantee accuracy of third-party data

            **Privacy:**
            - Interactions stored anonymously
            - No personal information collected
            - Data used only to improve experience
            """
        )

    st.markdown("---")

    # Quick reference guide (now contextual)
    st.markdown("### 📖 Quick Reference")
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

    # Legal disclaimer (Required for financial apps)
    with st.expander("⚠️ Important Disclaimers"):
        st.caption(
            """
            **Investment Disclaimer:**
            This tool provides educational information only.
            It does not constitute investment advice, financial
            planning services, or securities recommendations.

            **Data Disclaimer:**
            Financial data is delayed 15-20 minutes and sourced
            from Yahoo Finance. AI-generated content may contain
            errors. Always verify with official SEC filings.

            **Liability:**
            Always conduct your own due diligence and consult
            with a licensed financial advisor before making any
            investment decisions.
            """
        )

    st.markdown("---")
    st.caption("Built for long-term fundamental investors 📈")
    st.caption("v1.0.0-beta | Powered by AI")

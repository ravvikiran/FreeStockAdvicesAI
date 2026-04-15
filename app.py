import os
import sys
import streamlit as st
from datetime import datetime
from typing import Optional, Dict, Any
import base64

from crew import StockAnalysisCrew, get_provider_info


# Page configuration
st.set_page_config(
    page_title="FreeStockAI - Cloud Multi-Agent Stock Analyst",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)


# Initialize session state
if 'history' not in st.session_state:
    st.session_state['history'] = []

if 'current_analysis' not in st.session_state:
    st.session_state['current_analysis'] = None


# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.5rem;
        font-weight: bold;
        color: #2c3e50;
    }
    .success-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
    }
    .warning-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #fff3cd;
        border: 1px solid #ffeeba;
        color: #856404;
    }
    .error-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
    }
    .disclaimer {
        font-size: 0.8rem;
        color: #6c757d;
        font-style: italic;
    }
    .stButton > button {
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)


def format_market_data(data: Dict[str, Any]) -> str:
    """Format market data for display."""
    if 'error' in data:
        return f"Error: {data['error']}"
    
    lines = []
    lines.append(f"**Company:** {data.get('company_name', 'N/A')}")
    lines.append(f"**Current Price:** ${data.get('current_price', 0):.2f}")
    
    change = data.get('change_percent', 0)
    change_emoji = "🟢" if change >= 0 else "🔴"
    lines.append(f"**Change:** {change_emoji} {change:+.2f}%")
    
    lines.append(f"**Volume:** {data.get('volume', 0):,}")
    lines.append(f"**Market Cap:** ${data.get('market_cap', 0):,.0f}" if data.get('market_cap') else "**Market Cap:** N/A")
    lines.append(f"**P/E Ratio:** {data.get('pe_ratio', 'N/A')}")
    lines.append(f"**EPS:** ${data.get('eps', 'N/A')}")
    lines.append(f"**52-Week Range:** ${data.get('fifty_two_week_low', 0):.2f} - ${data.get('fifty_two_week_high', 0):.2f}")
    lines.append(f"**Beta:** {data.get('beta', 'N/A')}")
    lines.append(f"**Sector:** {data.get('sector', 'N/A')}")
    lines.append(f"**Industry:** {data.get('industry', 'N/A')}")
    lines.append(f"**Dividend Yield:** {data.get('dividend_yield', 'N/A')}")
    lines.append(f"**Recommendation:** {data.get('recommendation', 'N/A')}")
    
    return "\n".join(lines)


def display_analysis(result: Dict[str, Any]):
    """Display the analysis results."""
    if not result:
        return
    
    st.markdown("---")
    
    # Header with ticker
    ticker = result.get('ticker', 'UNKNOWN')
    st.markdown(f"## 📊 Stock Analysis: {ticker}")
    
    # Final analysis (with recommendation)
    final_analysis = result.get('final_analysis', '')
    st.markdown(final_analysis)
    
    # Display chart if available
    chart_base64 = result.get('chart_base64')
    if chart_base64:
        st.markdown("### 📈 Technical Chart")
        st.markdown("*6-month candlestick chart with 50 & 200 day moving averages*")
        
        # Display the chart
        st.image(base64.b64decode(chart_base64), caption=f"{ticker} - 6 Month Chart")
    
    # Market data collapsible section
    with st.expander("📋 View Detailed Market Data"):
        market_data = result.get('market_data', {})
        if market_data:
            st.markdown(format_market_data(market_data))
    
    # News collapsible section
    with st.expander("📰 View Recent News"):
        news = result.get('news', '')
        if news:
            st.markdown(news)
        else:
            st.write("No recent news found.")
    
    # Add to history
    st.session_state['history'].append({
        'ticker': ticker,
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'query': st.session_state.get('last_query', '')
    })


def main():
    """Main Streamlit application."""
    
    # Header
    st.markdown('<p class="main-header">📈 FreeStockAI</p>', unsafe_allow_html=True)
    st.markdown("*Cloud Multi-Agent Stock Analyst - AI-Powered Investment Insights*")
    st.markdown("---")
    
    # Sidebar
    with st.sidebar:
        st.markdown("### 🔧 Configuration")
        
        # LLM Provider info
        provider_info = get_provider_info()
        st.markdown(f"**Current LLM:** {provider_info['provider']}")
        st.markdown(f"**Model:** {provider_info['model']}")
        
        st.markdown("---")
        st.markdown("### ℹ️ How It Works")
        st.markdown("""
        1. **Extract Ticker** - Identify the stock from your query
        2. **Fetch Data** - Get real-time market data & fundamentals
        3. **Search News** - Find recent news & hedge fund activity
        4. **Analyze Chart** - Generate chart with technical indicators
        5. **Final Recommendation** - Senior analyst provides Buy/Sell/Hold
        """)
        
        st.markdown("---")
        st.markdown("### ⚠️ Disclaimer")
        st.markdown("""
        This is an AI-generated analysis for educational purposes only.
        
        **It is NOT financial advice.**
        
        Always do your own research before making investment decisions.
        """)
        
        # Clear history button
        if st.button("🗑️ Clear History"):
            st.session_state['history'] = []
            st.rerun()
    
    # Main content area
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Query input
        query = st.text_input(
            "🔍 Enter your stock query:",
            placeholder="e.g., Should I buy Tesla? or What do hedge funds say about Reliance?",
            key="query_input"
        )
    
    with col2:
        # Analyze button
        analyze_button = st.button("🚀 Analyze", type="primary")
    
    # Handle analysis
    if analyze_button and query:
        st.session_state['last_query'] = query
        
        with st.spinner("🔄 Analyzing stock... This may take a minute."):
            try:
                # Create crew and run analysis
                crew = StockAnalysisCrew()
                result = crew.run_with_chart(query)
                
                st.session_state['current_analysis'] = result
                
                # Display results
                display_analysis(result)
                
                st.success("✅ Analysis complete!")
                
            except Exception as e:
                st.error(f"❌ Error during analysis: {str(e)}")
                st.info("Please try again or check your API keys.")
    
    # Display current analysis if exists (after rerun)
    elif st.session_state.get('current_analysis') and not analyze_button:
        display_analysis(st.session_state['current_analysis'])
    
    # Show history
    if st.session_state.get('history'):
        st.markdown("---")
        st.markdown("### 📜 Recent Analyses")
        
        for item in reversed(st.session_state['history'][-5:]):
            with st.container():
                st.markdown(f"**{item['ticker']}** - {item['timestamp']}")
                st.markdown(f"_{item['query']}_")
                st.markdown("---")


if __name__ == "__main__":
    # Handle Railway's dynamic port
    if __name__ == "__main__":
        if "PORT" in os.environ:
            port = os.environ["PORT"]
            sys.argv = ["streamlit", "run", "app.py", "--server.port", port, "--server.address", "0.0.0.0"]
        main()
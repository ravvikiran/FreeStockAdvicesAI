import os
from typing import List, Any

from crewai import Agent
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic


def get_llm():
    """Get the LLM based on environment variables."""
    provider = os.getenv("LLM_PROVIDER", "openai").lower()
    model = os.getenv("LLM_MODEL", "")
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY") or os.getenv("XAI_API_KEY")
    
    if provider == "anthropic":
        api_key = os.getenv("ANTHROPIC_API_KEY")
        model = model or "claude-3-5-sonnet-20241022"
        return ChatAnthropic(
            model=model,
            anthropic_api_key=api_key,
            temperature=0.7
        )
    elif provider == "xai":
        api_key = os.getenv("XAI_API_KEY")
        model = model or "grok-2-1212"
        return ChatOpenAI(
            model=model,
            openai_api_key=api_key,
            base_url="https://api.x.ai/v1",
            temperature=0.7
        )
    else:
        api_key = os.getenv("OPENAI_API_KEY")
        model = model or "gpt-4o"
        return ChatOpenAI(
            model=model,
            openai_api_key=api_key,
            temperature=0.7
        )


def get_vision_llm():
    """Get the vision-capable LLM based on environment variables."""
    provider = os.getenv("LLM_PROVIDER", "openai").lower()
    model = os.getenv("LLM_MODEL", "")
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY") or os.getenv("XAI_API_KEY")
    
    if provider == "anthropic":
        api_key = os.getenv("ANTHROPIC_API_KEY")
        model = model or "claude-3-5-sonnet-20241022"
        return ChatAnthropic(
            model=model,
            anthropic_api_key=api_key,
            temperature=0.7
        )
    elif provider == "xai":
        api_key = os.getenv("XAI_API_KEY")
        model = model or "grok-2-vision-1212"
        return ChatOpenAI(
            model=model,
            openai_api_key=api_key,
            base_url="https://api.x.ai/v1",
            temperature=0.7
        )
    else:
        api_key = os.getenv("OPENAI_API_KEY")
        model = model or "gpt-4o"
        return ChatOpenAI(
            model=model,
            openai_api_key=api_key,
            temperature=0.7
        )


def create_agents(tools: List[Any]):
    """Create all CrewAI agents."""
    llm = get_llm()
    vision_llm = get_vision_llm()
    
    ticker_extractor = Agent(
        role="Ticker Extractor",
        goal="Extract the correct stock ticker symbol from natural language queries",
        backstory="""You are a financial data expert specialized in identifying stock ticker symbols.
        You understand global stock markets and can identify tickers for companies across US, Indian (NSE/BSE), and other markets.
        You know that Indian NSE stocks use .NS suffix (e.g., RELIANCE.NS) and BSE stocks use .BO suffix.
        You always ensure the ticker is in the correct format.""",
        verbose=True,
        allow_delegation=False,
        llm=llm,
        tools=[t for t in tools if t.name == "ticker_extractor"]
    )
    
    market_data_agent = Agent(
        role="Market Data Analyst",
        goal="Fetch comprehensive market data, fundamentals, and key metrics for the stock",
        backstory="""You are an expert at analyzing financial data from yfinance.
        You can extract current price, previous close, volume, market cap, P/E ratio, EPS, 52-week range, beta, sector, and other fundamentals.
        You present data in a clear, structured format.""",
        verbose=True,
        allow_delegation=False,
        llm=llm,
        tools=[t for t in tools if t.name == "market_data"]
    )
    
    news_agent = Agent(
        role="News & Hedge Fund Analyst",
        goal="Search for recent news, analyst recommendations, and hedge fund activity for the stock",
        backstory="""You specialize in finding the latest financial news, analyst upgrades/downgrades, and hedge fund holdings.
        You search for 13F filings, institutional ownership changes, and recent news articles.
        You provide sources and dates for all information found.""",
        verbose=True,
        allow_delegation=False,
        llm=llm,
        tools=[t for t in tools if t.name == "news_search"]
    )
    
    chart_vision_agent = Agent(
        role="Technical Chart Analyst",
        goal="Analyze stock charts and provide technical analysis insights",
        backstory="""You are a technical analysis expert who can interpret candlestick charts, moving averages, and volume patterns.
        You analyze trends, support/resistance levels, and identify bullish/bearish signals.
        You have deep expertise in reading 6-month charts with 50 and 200 day moving averages.""",
        verbose=True,
        allow_delegation=False,
        llm=vision_llm,
        tools=[t for t in tools if t.name == "chart_generator"]
    )
    
    senior_analyst = Agent(
        role="Senior Investment Analyst",
        goal="Synthesize all data and provide a final Buy/Sell/Hold recommendation with pros and cons",
        backstory="""You are a seasoned investment analyst with decades of experience in equity research.
        You combine fundamental analysis, technical analysis, and market sentiment to provide balanced recommendations.
        You always include a strong disclaimer that this is not financial advice.
        Your recommendations come with a confidence level (Low/Medium/High) based on data quality and market conditions.""",
        verbose=True,
        allow_delegation=True,
        llm=llm
    )
    
    return {
        'ticker_extractor': ticker_extractor,
        'market_data_agent': market_data_agent,
        'news_agent': news_agent,
        'chart_vision_agent': chart_vision_agent,
        'senior_analyst': senior_analyst
    }
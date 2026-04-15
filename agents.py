import os
import logging
from typing import List, Any, Optional, Dict

from crewai import Agent
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI

logger = logging.getLogger(__name__)


LLM_PROVIDERS = ["xai", "gemini", "openai", "anthropic", "minimax", "ollama"]


def _validate_api_key(api_key: Optional[str], provider: str) -> None:
    """Validate that API key exists."""
    if not api_key:
        raise ValueError(f"Missing API key for {provider}. Please set the appropriate environment variable.")


def get_llm_from_provider(provider: str, vision: bool = False):
    """Get LLM instance for a specific provider.
    
    Args:
        provider: Provider name (xai, gemini, openai, anthropic, ollama)
        vision: If True, return vision-capable model
    
    Returns:
        LLM instance
    
    Raises:
        ValueError: If API key is missing or provider is invalid
    """
    provider = provider.lower()
    
    if provider == "xai":
        api_key = os.getenv("XAI_API_KEY")
        _validate_api_key(api_key, "xAI")
        model = os.getenv("LLM_MODEL_XAI", "") or ("grok-2-vision-1212" if vision else "grok-2-1212")
        return ChatOpenAI(
            model=model,
            openai_api_key=api_key,
            base_url="https://api.x.ai/v1",
            temperature=0.7
        )
    
    elif provider == "gemini":
        api_key = os.getenv("GOOGLE_API_KEY")
        _validate_api_key(api_key, "Google Gemini")
        model = os.getenv("LLM_MODEL_GEMINI", "") or ("gemini-1.5-pro" if vision else "gemini-1.5-flash")
        return ChatGoogleGenerativeAI(
            model=model,
            google_api_key=api_key,
            temperature=0.7
        )
    
    elif provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        _validate_api_key(api_key, "OpenAI")
        model = os.getenv("LLM_MODEL_OPENAI", "") or "gpt-4o"
        return ChatOpenAI(
            model=model,
            openai_api_key=api_key,
            temperature=0.7
        )
    
    elif provider == "anthropic":
        api_key = os.getenv("ANTHROPIC_API_KEY")
        _validate_api_key(api_key, "Anthropic")
        model = os.getenv("LLM_MODEL_ANTHROPIC", "") or "claude-3-5-sonnet-20241022"
        return ChatAnthropic(
            model=model,
            anthropic_api_key=api_key,
            temperature=0.7
        )
    
    elif provider == "minimax":
        api_key = os.getenv("MINIMAX_API_KEY")
        _validate_api_key(api_key, "MiniMax")
        base_url = os.getenv("MINIMAX_BASE_URL", "https://api.minimax.chat/v1")
        model = os.getenv("LLM_MODEL_MINIMAX", "") or "abab6.5s-chat"
        return ChatOpenAI(
            model=model,
            openai_api_key=api_key,
            base_url=base_url,
            temperature=0.7
        )
    
    elif provider == "ollama":
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        model = os.getenv("LLM_MODEL_OLLAMA", "") or "llama3"
        return ChatOpenAI(
            model=model,
            openai_api_key="dummy",  # Ollama doesn't need API key
            base_url=base_url + "/v1",
            temperature=0.7
        )
    
    else:
        raise ValueError(f"Unknown provider: {provider}. Available: {LLM_PROVIDERS}")


def get_llm_with_fallback(vision: bool = False):
    """Get LLM with automatic fallback to next provider if one fails.
    
    Order: xai -> gemini -> openai -> anthropic -> minimax -> ollama
    
    Args:
        vision: If True, prefer vision-capable models
    
    Returns:
        tuple: (llm_instance, provider_name)
    """
    enabled_providers = []
    
    for provider in LLM_PROVIDERS:
        api_key_env = {
            "xai": "XAI_API_KEY",
            "gemini": "GOOGLE_API_KEY",
            "openai": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "minimax": "MINIMAX_API_KEY",
            "ollama": "OLLAMA_BASE_URL"
        }
        
        api_key = os.getenv(api_key_env.get(provider, ""))
        
        if api_key:
            enabled_providers.append(provider)
            logger.info(f"Found API key for provider: {provider}")
    
    if not enabled_providers:
        raise ValueError(
            f"No LLM providers available. Please set at least one API key:\n"
            f"  - XAI_API_KEY (xAI Grok)\n"
            f"  - GOOGLE_API_KEY (Google Gemini)\n"
            f"  - OPENAI_API_KEY (OpenAI GPT)\n"
            f"  - ANTHROPIC_API_KEY (Anthropic Claude)\n"
            f"  - MINIMAX_API_KEY (MiniMax)\n"
            f"  - OLLAMA_BASE_URL (local Ollama)"
        )
    
    logger.info(f"Enabled providers (in fallback order): {enabled_providers}")
    
    last_error = None
    for provider in enabled_providers:
        try:
            logger.info(f"Attempting to initialize: {provider}")
            llm = get_llm_from_provider(provider, vision=vision)
            
            test_result = llm.invoke("Test")
            logger.info(f"Successfully initialized {provider}")
            return llm, provider
            
        except Exception as e:
            logger.warning(f"Failed to initialize {provider}: {e}")
            last_error = e
            continue
    
    raise RuntimeError(f"All LLM providers failed. Last error: {last_error}")


def get_llm(vision: bool = False):
    """Get the LLM (legacy single-provider function)."""
    llm, provider = get_llm_with_fallback(vision=vision)
    return llm


def get_vision_llm():
    """Get the vision-capable LLM."""
    llm, provider = get_llm_with_fallback(vision=True)
    return llm


def get_provider_info() -> Dict[str, str]:
    """Get information about available LLM providers."""
    available = []
    
    if os.getenv("XAI_API_KEY"):
        available.append("xAI Grok")
    if os.getenv("GOOGLE_API_KEY"):
        available.append("Google Gemini")
    if os.getenv("OPENAI_API_KEY"):
        available.append("OpenAI GPT")
    if os.getenv("ANTHROPIC_API_KEY"):
        available.append("Anthropic Claude")
    if os.getenv("OLLAMA_BASE_URL"):
        available.append("Ollama (local)")
    
    return {
        "available_providers": ", ".join(available) if available else "None",
        "fallback_order": " -> ".join(LLM_PROVIDERS)
    }


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
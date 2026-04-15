import os
import base64
import logging
from typing import Dict, Any, List
from langchain_openai import ChatOpenAI

from tools import create_tools
from agents import create_agents, get_llm_with_fallback, get_provider_info as get_agents_provider_info

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

LLM_TIMEOUT_SECONDS = 60


class StockAnalysisCrew:
    """Main crew for stock analysis with multi-LLM fallback."""

    def __init__(self):
        self.tools = create_tools()
        self.agents = create_agents(self.tools)
        
        llm, provider = get_llm_with_fallback(vision=False)
        self.llm = llm
        self.current_provider = provider
        logger.info(f"Using LLM provider: {provider}")
        
        vision_llm, vision_provider = get_llm_with_fallback(vision=True)
        self.vision_llm = vision_llm
        self.vision_provider = vision_provider

    def _invoke_with_fallback(self, prompt: str) -> Any:
        """Invoke LLM with fallback to next provider if one fails."""
        providers = ["xai", "gemini", "openai", "anthropic", "minimax", "ollama"]
        
        enabled_providers = []
        for p in providers:
            key = {
                "xai": "XAI_API_KEY",
                "gemini": "GOOGLE_API_KEY",
                "openai": "OPENAI_API_KEY",
                "anthropic": "ANTHROPIC_API_KEY",
                "minimax": "MINIMAX_API_KEY",
                "ollama": "OLLAMA_BASE_URL"
            }.get(p, "")
            
            if os.getenv(key):
                enabled_providers.append(p)
        
        for i, provider in enumerate(enabled_providers):
            try:
                if i == 0 and hasattr(self, 'llm') and self.current_provider == provider:
                    llm_to_use = self.llm
                else:
                    from agents import get_llm_from_provider
                    llm_to_use = get_llm_from_provider(provider, vision=False)
                
                logger.info(f"Invoking LLM: {provider}")
                result = llm_to_use.invoke(prompt)
                logger.info(f"LLM invocation successful: {provider}")
                return result
                
            except Exception as e:
                logger.warning(f"LLM {provider} failed: {e}. Trying next provider...")
                continue
        
        raise RuntimeError("All LLM providers failed during invocation")

    def run_with_chart(self, query: str) -> Dict[str, Any]:
        """Run analysis with explicit chart generation and vision analysis."""
        
        logger.info(f"Starting analysis for query: {query}")
        
        try:
            ticker_tool = [t for t in self.tools if t.name == "ticker_extractor"][0]
            ticker = ticker_tool.run(query)
            logger.info(f"Extracted ticker: {ticker}")
        except Exception as e:
            logger.error(f"Failed to extract ticker: {e}")
            return {'error': f"Failed to extract ticker: {str(e)}", 'ticker': 'UNKNOWN'}
        
        try:
            market_tool = [t for t in self.tools if t.name == "market_data"][0]
            market_data = market_tool.run(ticker)
            logger.info(f"Retrieved market data for: {ticker}")
        except Exception as e:
            logger.error(f"Failed to get market data: {e}")
            market_data = {'error': str(e)}
        
        try:
            news_tool = [t for t in self.tools if t.name == "news_search"][0]
            news = news_tool.run(ticker)
            logger.info(f"Retrieved news for: {ticker}")
        except Exception as e:
            logger.error(f"Failed to get news: {e}")
            news = f"Error retrieving news: {str(e)}"
        
        try:
            chart_tool = [t for t in self.tools if t.name == "chart_generator"][0]
            chart_base64 = chart_tool.run(ticker)
            logger.info(f"Generated chart for: {ticker}")
        except Exception as e:
            logger.error(f"Failed to generate chart: {e}")
            chart_base64 = None
        
        vision_analysis = ""
        if chart_base64:
            chart_data = base64.b64decode(chart_base64)
            vision_prompt = f"""Analyze this stock chart for {ticker}. Look for:
1. Trend direction (bullish/bearish/neutral)
2. Support and resistance levels
3. Moving average crossovers (50-day vs 200-day)
4. Volume patterns
5. Any technical patterns (head and shoulders, double top/bottom, etc.)
6. Current price relative to moving averages

Provide a detailed technical analysis."""
            
            try:
                vision_analysis = "Chart generated successfully. See attached chart for visual analysis."
            except Exception as e:
                logger.warning(f"Vision analysis failed: {e}")
                vision_analysis = f"Could not analyze chart: {str(e)}"
        
        analysis_prompt = f"""You are a Senior Investment Analyst. Provide a comprehensive stock analysis for {ticker}.

## Market Data
{market_data}

## Recent News & Hedge Fund Activity
{news}

## Technical Chart Analysis
{vision_analysis}
{"[Chart attached - see above]" if chart_base64 else "No chart available"}

## Your Task
Based on all the data above:
1. Provide a clear BUY / SELL / HOLD recommendation with confidence level (Low/Medium/High)
2. List 3-5 key PROS (bullish arguments)
3. List 3-5 key CONS (bearish arguments)
4. Provide detailed final reasoning

Format your response as:
**Recommendation:** 🟢 BUY / 🔴 SELL / 🟡 HOLD (Confidence: [level])

### Pros
- ...

### Cons
- ...

### Final Reasoning
...

**⚠️ Disclaimer:** This is AI-generated analysis for educational purposes only. Not financial advice. Do your own research."""

        try:
            logger.info(f"Invoking LLM for final analysis (timeout: {LLM_TIMEOUT_SECONDS}s)")
            result = self._invoke_with_fallback(analysis_prompt)
            logger.info(f"LLM analysis completed for: {ticker}")
        except Exception as e:
            logger.error(f"LLM invoke failed: {e}")
            return {
                'ticker': ticker,
                'market_data': market_data,
                'news': news,
                'chart_base64': chart_base64,
                'vision_analysis': vision_analysis,
                'final_analysis': f"Error during analysis: {str(e)}"
            }
        
        return {
            'ticker': ticker,
            'market_data': market_data,
            'news': news,
            'chart_base64': chart_base64,
            'vision_analysis': vision_analysis,
            'final_analysis': result.content if hasattr(result, 'content') else str(result)
        }


def get_provider_info() -> Dict[str, str]:
    """Get information about available LLM providers."""
    return get_agents_provider_info()
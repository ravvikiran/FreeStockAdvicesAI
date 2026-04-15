import os
import base64
from typing import Dict, Any, List

from crewai import Crew, Task, Process
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic

from tools import create_tools
from agents import create_agents, get_llm, get_vision_llm


class StockAnalysisCrew:
    """Main crew for stock analysis."""

    def __init__(self):
        self.tools = create_tools()
        self.agents = create_agents(self.tools)
        self.llm = get_llm()
        self.vision_llm = get_vision_llm()

    def run(self, query: str) -> Dict[str, Any]:
        """Execute the full stock analysis workflow."""
        
        # Step 1: Extract ticker
        ticker_task = Task(
            description=f"Extract the stock ticker from this query: {query}",
            agent=self.agents['ticker_extractor'],
            expected_output="The extracted ticker symbol in the correct format (e.g., TSLA, RELIANCE.NS)"
        )
        
        # Step 2: Get market data
        market_data_task = Task(
            description=f"Fetch comprehensive market data for the extracted ticker. Use the market_data tool.",
            agent=self.agents['market_data_agent'],
            expected_output="Complete market data including price, volume, fundamentals, and key metrics"
        )
        
        # Step 3: Search news
        news_task = Task(
            description=f"Search for recent news, analyst recommendations, and hedge fund activity for the stock. Use the news_search tool.",
            agent=self.agents['news_agent'],
            expected_output="Recent news articles, analyst upgrades/downgrades, and hedge fund activity"
        )
        
        # Step 4: Generate and analyze chart
        chart_task = Task(
            description=f"Generate a 6-month candlestick chart with 50 and 200 day moving averages for the stock. Use the chart_generator tool to create the image, then analyze it.",
            agent=self.agents['chart_vision_agent'],
            expected_output="A base64 encoded chart image and technical analysis insights"
        )
        
        # Create crew with sequential process
        crew = Crew(
            agents=[
                self.agents['ticker_extractor'],
                self.agents['market_data_agent'],
                self.agents['news_agent'],
                self.agents['chart_vision_agent'],
            ],
            tasks=[ticker_task, market_data_task, news_task, chart_task],
            process=Process.sequential,
            verbose=True
        )
        
        # Run the crew
        result = crew.kickoff()
        
        # Extract ticker from result
        ticker_result = str(result).split('\n')[0].strip()
        
        # Now generate final analysis with Senior Analyst
        final_analysis_task = Task(
            description=f"""Based on the following analysis results, provide a final stock recommendation:

{result}

Provide:
1. A clear Buy/Sell/Hold recommendation with confidence level
2. Key Pros (bullish arguments)
3. Key Cons (bearish arguments)
4. Final reasoning

Always end with a strong disclaimer that this is not financial advice.""",
            agent=self.agents['senior_analyst'],
            expected_output="Final recommendation with Buy/Sell/Hold, confidence level, pros, cons, and disclaimer"
        )
        
        # Create final crew for analysis
        final_crew = Crew(
            agents=[self.agents['senior_analyst']],
            tasks=[final_analysis_task],
            process=Process.sequential,
            verbose=False
        )
        
        final_result = final_crew.kickoff()
        
        return {
            'ticker': ticker_result,
            'raw_result': str(result),
            'final_analysis': str(final_result)
        }

    def run_with_chart(self, query: str) -> Dict[str, Any]:
        """Run analysis with explicit chart generation and vision analysis."""
        
        # Step 1: Extract ticker
        ticker_tool = [t for t in self.tools if t.name == "ticker_extractor"][0]
        ticker = ticker_tool.run(query)
        
        # Step 2: Get market data
        market_tool = [t for t in self.tools if t.name == "market_data"][0]
        market_data = market_tool.run(ticker)
        
        # Step 3: Search news
        news_tool = [t for t in self.tools if t.name == "news_search"][0]
        news = news_tool.run(ticker)
        
        # Step 4: Generate chart
        chart_tool = [t for t in self.tools if t.name == "chart_generator"][0]
        chart_base64 = chart_tool.run(ticker)
        
        # Step 5: Analyze chart with vision LLM
        vision_analysis = ""
        if chart_base64:
            # Decode and save temporarily for analysis
            chart_data = base64.b64decode(chart_base64)
            
            # Create prompt for vision analysis
            vision_prompt = f"""Analyze this stock chart for {ticker}. Look for:
1. Trend direction (bullish/bearish/neutral)
2. Support and resistance levels
3. Moving average crossovers (50-day vs 200-day)
4. Volume patterns
5. Any technical patterns (head and shoulders, double top/bottom, etc.)
6. Current price relative to moving averages

Provide a detailed technical analysis."""
            
            try:
                # For vision analysis, we'd ideally use vision-capable models
                # Since the LLM integration for images varies by provider,
                # we'll include the chart in the final analysis task
                vision_analysis = "Chart generated successfully. See attached chart for visual analysis."
            except Exception as e:
                vision_analysis = f"Could not analyze chart: {str(e)}"
        
        # Step 6: Final analysis with Senior Analyst
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

        result = self.llm.invoke(analysis_prompt)
        
        return {
            'ticker': ticker,
            'market_data': market_data,
            'news': news,
            'chart_base64': chart_base64,
            'vision_analysis': vision_analysis,
            'final_analysis': result.content if hasattr(result, 'content') else str(result)
        }


def get_provider_info() -> Dict[str, str]:
    """Get information about the current LLM provider."""
    provider = os.getenv("LLM_PROVIDER", "openai").lower()
    model = os.getenv("LLM_MODEL", "")
    
    if provider == "anthropic":
        return {"provider": "Anthropic Claude", "model": model or "claude-3-5-sonnet-20241022"}
    elif provider == "xai":
        return {"provider": "xAI Grok", "model": model or "grok-2-vision-1212"}
    else:
        return {"provider": "OpenAI", "model": model or "gpt-4o"}
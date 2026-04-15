import os
import io
import base64
import time
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from functools import lru_cache

import yfinance as yf
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from PIL import Image

try:
    from duckduckgo_search import DDGS
except ImportError:
    DDGS = None

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CacheManager:
    """Simple in-memory cache for API calls."""
    
    def __init__(self, ttl_seconds: int = 300):
        self._cache: Dict[str, tuple[Any, float]] = {}
        self._ttl = ttl_seconds
    
    def get(self, key: str) -> Optional[Any]:
        if key in self._cache:
            value, timestamp = self._cache[key]
            if time.time() - timestamp < self._ttl:
                logger.info(f"Cache hit for: {key}")
                return value
            else:
                del self._cache[key]
                logger.info(f"Cache expired for: {key}")
        return None
    
    def set(self, key: str, value: Any) -> None:
        self._cache[key] = (value, time.time())
        logger.info(f"Cache set for: {key}")
    
    def clear(self) -> None:
        self._cache.clear()


market_cache = CacheManager(ttl_seconds=300)
news_cache = CacheManager(ttl_seconds=600)


def retry_with_backoff(max_retries: int = 3, initial_delay: float = 1.0):
    """Decorator to retry functions with exponential backoff."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            delay = initial_delay
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay}s...")
                        time.sleep(delay)
                        delay *= 2
                    else:
                        logger.error(f"All {max_retries} attempts failed: {e}")
            if last_exception:
                raise last_exception
            raise RuntimeError(f"Function {func.__name__} failed after {max_retries} retries")
        return wrapper
    return decorator


class TickerExtractorTool:
    """Tool to extract stock ticker from natural language queries."""

    name = "ticker_extractor"
    description = "Extracts the stock ticker symbol from a natural language query. Supports Indian stocks (.NS, .BO), US stocks, and other international markets."

    def __init__(self, llm=None):
        self.llm = llm

    def run(self, query: str) -> str:
        if self.llm is None:
            return self._fallback_extract(query)
        
        prompt = f"""Extract the stock ticker symbol from the following query. 
Rules:
- For Indian stocks (NSE/BSE), append .NS for NSE or .BO for BSE (e.g., RELIANCE -> RELIANCE.NS)
- For US stocks, use the standard ticker (e.g., Tesla -> TSLA, Apple -> AAPL)
- If no ticker is mentioned but a company name is given, provide the most likely ticker
- Return ONLY the ticker symbol, nothing else

Query: {query}

Return just the ticker symbol:"""

        try:
            result = self.llm.invoke(prompt)
            ticker = result.content.strip().upper()
            return ticker
        except Exception as e:
            return self._fallback_extract(query)

    def _fallback_extract(self, query: str) -> str:
        query_lower = query.lower()
        
        indian_stocks = {
            'reliance': 'RELIANCE.NS',
            'tata': 'TATA.NS',
            'infosys': 'INFY.NS',
            'tcs': 'TCS.NS',
            'hdfc': 'HDFCBANK.NS',
            'icici': 'ICICIBANK.NS',
            'sbi': 'SBIN.NS',
            'itc': 'ITC.NS',
            'sun pharma': 'SUNPHARMA.NS',
            'adani': 'ADANIENT.NS',
        }
        
        us_stocks = {
            'tesla': 'TSLA',
            'apple': 'AAPL',
            'microsoft': 'MSFT',
            'google': 'GOOGL',
            'amazon': 'AMZN',
            'nvidia': 'NVDA',
            'meta': 'META',
            'facebook': 'META',
            'netflix': 'NFLX',
            'amd': 'AMD',
        }
        
        for name, ticker in {**indian_stocks, **us_stocks}.items():
            if name in query_lower:
                return ticker
        
        words = query.upper().split()
        for word in words:
            if len(word) >= 1 and len(word) <= 5 and word.isalpha():
                if '.' not in word:
                    return f"{word}.NS"
        
        return "UNKNOWN"


class MarketDataTool:
    """Tool to fetch market data using yfinance."""

    name = "market_data"
    description = "Fetches comprehensive market data for a given stock ticker including price, volume, fundamentals, and key metrics."

    def __init__(self):
        pass

    @retry_with_backoff(max_retries=3, initial_delay=1.0)
    def run(self, ticker: str) -> Dict[str, Any]:
        cache_key = f"market_data_{ticker}"
        cached = market_cache.get(cache_key)
        if cached:
            return cached
        
        try:
            logger.info(f"Fetching market data for: {ticker}")
            stock = yf.Ticker(ticker)
            info = stock.info
            
            history = stock.history(period="1d")
            current_price = history['Close'].iloc[-1] if not history.empty else 0
            
            previous_close = info.get('previousClose', info.get('regularMarketPreviousClose', 0))
            
            fifty_two_week_low = stock.info.get('fiftyTwoWeekLow', 0)
            fifty_two_week_high = stock.info.get('fiftyTwoWeekHigh', 0)
            
            data = {
                'ticker': ticker,
                'company_name': info.get('longName', info.get('shortName', ticker)),
                'current_price': current_price,
                'previous_close': previous_close,
                'change_percent': ((current_price - previous_close) / previous_close * 100) if previous_close else 0,
                'volume': info.get('volume', 0),
                'avg_volume': info.get('averageVolume', 0),
                'market_cap': info.get('marketCap', 0),
                'pe_ratio': info.get('trailingPE', 0),
                'eps': info.get('trailingEps', 0),
                'beta': info.get('beta', 0),
                'sector': info.get('sector', 'Unknown'),
                'industry': info.get('industry', 'Unknown'),
                'fifty_two_week_low': fifty_two_week_low,
                'fifty_two_week_high': fifty_two_week_high,
                'dividend_yield': info.get('dividendYield', 0),
                'profit_margins': info.get('profitMargins', 0),
                'roe': info.get('returnOnEquity', 0),
                'debt_to_equity': info.get('debtToEquity', 0),
                'target_mean_price': info.get('targetMeanPrice', 0),
                'recommendation': info.get('recommendationKey', 'N/A'),
            }
            
            market_cache.set(cache_key, data)
            logger.info(f"Market data cached for: {ticker}")
            return data
        except Exception as e:
            logger.error(f"Error fetching market data for {ticker}: {e}")
            return {'error': str(e), 'ticker': ticker}


class NewsSearchTool:
    """Tool to search for news and hedge fund recommendations."""

    name = "news_search"
    description = "Searches for recent news, analyst recommendations, hedge fund activity, and 13F filings for a given stock."

    def __init__(self):
        pass

    @retry_with_backoff(max_retries=3, initial_delay=1.0)
    def run(self, ticker: str) -> str:
        cache_key = f"news_{ticker}"
        cached = news_cache.get(cache_key)
        if cached:
            return cached
        
        if DDGS is None:
            return "DuckDuckGo search not available. Please install duckduckgo-search package."
        
        results = []
        
        search_queries = [
            f"{ticker} stock news 2025",
            f"{ticker} analyst recommendation buy sell hold",
            f"hedge fund {ticker} position 2025",
            f"{ticker} 13F filing institutional investors",
        ]
        
        try:
            logger.info(f"Searching news for: {ticker}")
            with DDGS() as ddgs:
                for query in search_queries[:4]:
                    try:
                        ddgs_results = ddgs.text(query, max_results=3)
                        for r in ddgs_results:
                            results.append({
                                'title': r.get('title', ''),
                                'url': r.get('href', ''),
                                'snippet': r.get('body', '')[:200]
                            })
                    except Exception as e:
                        logger.warning(f"Search query failed: {query}, error: {e}")
                        continue
        except Exception as e:
            logger.error(f"Error searching for news for {ticker}: {e}")
            return f"Error searching for news: {str(e)}"
        
        if not results:
            return f"No recent news found for {ticker}."
        
        formatted = f"## Recent News & Analysis for {ticker}\n\n"
        for i, r in enumerate(results[:8], 1):
            formatted += f"**{i}. {r['title']}**\n"
            formatted += f"{r['snippet']}\n"
            formatted += f"Source: {r['url']}\n\n"
        
        news_cache.set(cache_key, formatted)
        logger.info(f"News cached for: {ticker}")
        return formatted


class ChartGeneratorTool:
    """Tool to generate stock charts with technical indicators."""

    name = "chart_generator"
    description = "Generates a 6-month candlestick chart with 50 and 200 day moving averages, volume, and saves as base64 encoded PNG."

    def __init__(self):
        pass

    def run(self, ticker: str) -> Optional[str]:
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="6mo")
            
            if hist.empty:
                return None
            
            fig, axes = plt.subplots(2, 1, figsize=(14, 10), gridspec_kw={'height_ratios': [3, 1]})
            
            ax1 = axes[0]
            ax2 = axes[1]
            
            hist['MA50'] = hist['Close'].rolling(window=50).mean()
            hist['MA200'] = hist['Close'].rolling(window=200).mean()
            
            candle_width = 0.6
            
            up = hist[hist['Close'] >= hist['Open']]
            down = hist[hist['Close'] < hist['Open']]
            
            ax1.bar(up.index, up['Close'] - up['Open'], candle_width, bottom=up['Open'], color='green', edgecolor='green')
            ax1.bar(up.index, up['High'] - up['Close'], 0.2, bottom=up['Close'], color='green')
            ax1.bar(up.index, up['Low'] - up['Open'], 0.2, bottom=up['Open'], color='green')
            
            ax1.bar(down.index, down['Open'] - down['Close'], candle_width, bottom=down['Close'], color='red', edgecolor='red')
            ax1.bar(down.index, down['High'] - down['Open'], 0.2, bottom=down['Open'], color='red')
            ax1.bar(down.index, down['Close'] - down['Low'], 0.2, bottom=down['Low'], color='red')
            
            ax1.plot(hist.index, hist['MA50'], color='blue', linewidth=1.5, label='50-Day MA')
            ax1.plot(hist.index, hist['MA200'], color='orange', linewidth=1.5, label='200-Day MA')
            
            ax1.set_title(f'{ticker} - 6 Month Price Chart', fontsize=14, fontweight='bold')
            ax1.set_ylabel('Price', fontsize=12)
            ax1.legend(loc='upper left')
            ax1.grid(True, alpha=0.3)
            
            ax2.bar(hist.index, hist['Volume'], color=['green' if c >= o else 'red' for c, o in zip(hist['Close'], hist['Open'])], alpha=0.7)
            ax2.set_xlabel('Date', fontsize=12)
            ax2.set_ylabel('Volume', fontsize=12)
            ax2.grid(True, alpha=0.3)
            
            for ax in axes:
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
                ax.xaxis.set_major_locator(mdates.MonthLocator())
                plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
            
            plt.tight_layout()
            
            buf = io.BytesIO()
            plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
            buf.seek(0)
            img_base64 = base64.b64encode(buf.read()).decode('utf-8')
            plt.close()
            
            return img_base64
            
        except Exception as e:
            print(f"Error generating chart: {e}")
            plt.close()
            return None


def create_tools(llm=None) -> List[Any]:
    """Factory function to create all tools."""
    return [
        TickerExtractorTool(llm=llm),
        MarketDataTool(),
        NewsSearchTool(),
        ChartGeneratorTool(),
    ]
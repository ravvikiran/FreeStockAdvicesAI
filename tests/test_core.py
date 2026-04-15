import os
import pytest
from unittest.mock import Mock, patch, MagicMock

os.environ['OPENAI_API_KEY'] = 'test-key'
os.environ['ANTHROPIC_API_KEY'] = 'test-key'


class TestTickerExtractorTool:
    """Tests for TickerExtractorTool."""
    
    def test_fallback_extract_tesla(self):
        from tools import TickerExtractorTool
        tool = TickerExtractorTool(llm=None)
        result = tool.run("Should I buy Tesla?")
        assert result == 'TSLA'
    
    def test_fallback_extract_reliance(self):
        from tools import TickerExtractorTool
        tool = TickerExtractorTool(llm=None)
        result = tool.run("What about Reliance stock?")
        assert result == 'RELIANCE.NS'
    
    def test_fallback_extract_apple(self):
        from tools import TickerExtractorTool
        tool = TickerExtractorTool(llm=None)
        result = tool.run("Apple analysis please")
        assert result == 'AAPL'
    
    def test_fallback_extract_amazon(self):
        from tools import TickerExtractorTool
        tool = TickerExtractorTool(llm=None)
        result = tool.run("Amazon stock")
        assert result == 'AMZN'
    
    def test_fallback_unknown_stock(self):
        from tools import TickerExtractorTool
        tool = TickerExtractorTool(llm=None)
        result = tool.run("random text without stock")
        assert result == 'UNKNOWN'


class TestMarketDataTool:
    """Tests for MarketDataTool."""
    
    @patch('tools.yf.Ticker')
    def test_run_returns_dict(self, mock_ticker):
        from tools import MarketDataTool
        mock_stock = MagicMock()
        mock_stock.info = {
            'longName': 'Test Company',
            'previousClose': 100.0,
            'volume': 1000000,
            'marketCap': 5000000000,
            'trailingPE': 20.0,
            'sector': 'Technology',
        }
        mock_stock.history.return_value = MagicMock()
        mock_stock.history.return_value.__getitem__ = lambda self, key: MagicMock(**{'iloc': MagicMock(**{'__getitem__': lambda s, i: 105.0})})
        mock_ticker.return_value = mock_stock
        
        tool = MarketDataTool()
        result = tool.run("TEST")
        
        assert isinstance(result, dict)
        assert 'ticker' in result


class TestNewsSearchTool:
    """Tests for NewsSearchTool."""
    
    def test_run_no_ddgs(self):
        from tools import NewsSearchTool, DDGS
        original_ddgs = DDGS
        import tools
        tools.DDGS = None
        
        tool = NewsSearchTool()
        result = tool.run("TEST")
        
        tools.DDGS = original_ddgs
        assert "not available" in result.lower()


class TestCacheManager:
    """Tests for CacheManager."""
    
    def test_cache_get_set(self):
        from tools import CacheManager
        cache = CacheManager(ttl_seconds=60)
        
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"
    
    def test_cache_miss(self):
        from tools import CacheManager
        cache = CacheManager(ttl_seconds=60)
        
        assert cache.get("nonexistent") is None
    
    def test_cache_expired(self):
        from tools import CacheManager
        import time
        cache = CacheManager(ttl_seconds=1)
        
        cache.set("key1", "value1")
        time.sleep(1.1)
        assert cache.get("key1") is None
    
    def test_cache_clear(self):
        from tools import CacheManager
        cache = CacheManager(ttl_seconds=60)
        
        cache.set("key1", "value1")
        cache.clear()
        assert cache.get("key1") is None


class TestRetryWithBackoff:
    """Tests for retry decorator."""
    
    def test_succeeds_first_attempt(self):
        from tools import retry_with_backoff
        
        @retry_with_backoff(max_retries=3, initial_delay=0.1)
        def succeed():
            return "success"
        
        assert succeed() == "success"
    
    def test_succeeds_after_retries(self):
        from tools import retry_with_backoff
        
        call_count = 0
        
        @retry_with_backoff(max_retries=3, initial_delay=0.1)
        def fail_twice():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("fail")
            return "success"
        
        assert fail_twice() == "success"
        assert call_count == 3
    
    def test_fails_after_max_retries(self):
        from tools import retry_with_backoff
        
        @retry_with_backoff(max_retries=3, initial_delay=0.1)
        def always_fail():
            raise Exception("always fails")
        
        with pytest.raises(Exception):
            always_fail()


class TestGetLLM:
    """Tests for LLM provider functions."""
    
    @patch.dict(os.environ, {'LLM_PROVIDER': 'openai', 'OPENAI_API_KEY': 'test-key'})
    def test_get_llm_openai(self):
        from agents import get_llm
        llm = get_llm()
        assert llm is not None
    
    @patch.dict(os.environ, {'LLM_PROVIDER': 'anthropic', 'ANTHROPIC_API_KEY': 'test-key'})
    def test_get_llm_anthropic(self):
        from agents import get_llm
        llm = get_llm()
        assert llm is not None
    
    @patch.dict(os.environ, {'LLM_PROVIDER': 'openai'})
    def test_get_llm_missing_key(self):
        from agents import get_llm
        # Remove the key for this test
        original_key = os.environ.pop('OPENAI_API_KEY', None)
        try:
            with pytest.raises(ValueError):
                get_llm()
        finally:
            if original_key:
                os.environ['OPENAI_API_KEY'] = original_key


class TestGetProviderInfo:
    """Tests for provider info function."""
    
    def test_openai_provider(self):
        with patch.dict(os.environ, {'LLM_PROVIDER': 'openai'}):
            from crew import get_provider_info
            info = get_provider_info()
            assert info['provider'] == 'OpenAI'
    
    def test_anthropic_provider(self):
        with patch.dict(os.environ, {'LLM_PROVIDER': 'anthropic'}):
            from crew import get_provider_info
            info = get_provider_info()
            assert info['provider'] == 'Anthropic Claude'
    
    def test_xai_provider(self):
        with patch.dict(os.environ, {'LLM_PROVIDER': 'xai'}):
            from crew import get_provider_info
            info = get_provider_info()
            assert info['provider'] == 'xAI Grok'


class TestFormatMarketData:
    """Tests for market data formatting."""
    
    def test_format_with_complete_data(self):
        from app import format_market_data
        data = {
            'company_name': 'Test Company',
            'current_price': 100.0,
            'change_percent': 2.5,
            'volume': 1000000,
            'market_cap': 5000000000,
            'pe_ratio': 20.0,
            'eps': 5.0,
            'fifty_two_week_low': 80.0,
            'fifty_two_week_high': 120.0,
            'beta': 1.2,
            'sector': 'Technology',
            'industry': 'Software',
            'dividend_yield': 1.5,
            'recommendation': 'buy'
        }
        result = format_market_data(data)
        assert 'Test Company' in result
        assert '$100.00' in result
        assert 'Technology' in result
    
    def test_format_with_error(self):
        from app import format_market_data
        data = {'error': 'Something went wrong', 'ticker': 'TEST'}
        result = format_market_data(data)
        assert 'Error' in result
    
    def test_format_with_none_values(self):
        from app import format_market_data
        data = {
            'company_name': 'Test',
            'current_price': None,
            'change_percent': None,
            'market_cap': None,
            'pe_ratio': None,
            'eps': None,
            'volume': 0,
            'fifty_two_week_low': 0,
            'fifty_two_week_high': 0,
            'beta': None,
            'sector': 'Tech',
            'industry': 'Software',
            'dividend_yield': None,
            'recommendation': 'N/A'
        }
        result = format_market_data(data)
        assert 'Test' in result
        assert 'N/A' in result


class TestCreateTools:
    """Tests for tools factory function."""
    
    def test_create_tools_returns_list(self):
        from tools import create_tools
        tools = create_tools()
        assert isinstance(tools, list)
        assert len(tools) == 4
    
    def test_create_tools_has_correct_names(self):
        from tools import create_tools
        tools = create_tools()
        names = [t.name for t in tools]
        assert 'ticker_extractor' in names
        assert 'market_data' in names
        assert 'news_search' in names
        assert 'chart_generator' in names


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
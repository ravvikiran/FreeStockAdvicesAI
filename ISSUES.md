# Project Issues, Errors, and Improvements Tracker

> **Status**: All issues have been resolved.

## Resolved Issues

### Critical - FIXED

1. ✅ **Amazon ticker typo** (`tools.py:70`)
   - Fixed: `'amazon': 'AMNV'` → `'amazon': 'AMZN'`

2. ✅ **Tuple assignment error** (`tools.py:110`)
   - Fixed: Changed from tuple to separate variables `fifty_two_week_low` and `fifty_two_week_high`

3. ✅ **Duplicate `__name__` check** (`app.py:244-245`)
   - Fixed: Removed redundant nested check

4. ✅ **Unused `run()` method** (`crew.py:22-103`)
   - Fixed: Removed dead code - the method was never called

5. ✅ **Unused CrewAI imports** (`crew.py:5`)
   - Fixed: Removed unused imports (Crew, Task, Process)

### Medium - FIXED

6. ✅ **Memory leak in history** (`app.py:142-146`)
   - Fixed: Added limit of 20 items, older items are removed

7. ✅ **Duplicate LLM functions** (`agents.py:9-72`)
   - Fixed: Refactored `get_llm()` to accept `vision` parameter, `get_vision_llm()` now calls it

8. ✅ **No API key validation** (`agents.py:9-39`)
   - Fixed: Added `_validate_api_key()` function that raises clear error if API key is missing

9. ✅ **Chart not closed on error** (`tools.py:257-259`)
   - Fixed: Added `plt.close()` in exception path

10. ✅ **Missing None checks in formatting** (`app.py:76-100`)
    - Fixed: Added proper None/zero checks before formatting values

## Implemented Improvements

### 1. Caching ✅
- Added `CacheManager` class in `tools.py` with TTL support
- Market data cached for 5 minutes (300s)
- News cached for 10 minutes (600s)
- Cache hit/miss logged for debugging

### 2. Timeout Handling ✅
- Added `LLM_TIMEOUT_SECONDS = 60` constant in `crew.py`
- Individual steps (ticker extraction, market data, news, chart) wrapped in try-except with logging
- Graceful error handling - partial results returned on failure

### 3. Retry Logic ✅
- Added `@retry_with_backoff` decorator in `tools.py`
- 3 retries with exponential backoff (1s → 2s → 4s)
- Applied to `MarketDataTool.run()` and `NewsSearchTool.run()`
- Reduces transient failures from yfinance/DuckDuckGo

### 4. Unit Tests ✅
- Created `tests/test_core.py` with comprehensive tests:
  - `TestTickerExtractorTool` - 5 tests
  - `TestMarketDataTool` - 1 test
  - `TestNewsSearchTool` - 1 test
  - `TestCacheManager` - 4 tests
  - `TestRetryWithBackoff` - 3 tests
  - `TestGetLLM` - 3 tests
  - `TestGetProviderInfo` - 3 tests
  - `TestFormatMarketData` - 3 tests
  - `TestCreateTools` - 2 tests
- Run with: `pytest tests/test_core.py -v`

### 5. Logging ✅
- Added structured logging throughout:
  - `tools.py` - Cache operations, data fetching, errors
  - `crew.py` - Analysis steps, LLM invocations, errors
- Log format: `%(asctime)s - %(name)s - %(levelname)s - %(message)s`
- Configured for INFO level by default

## Optional Future Improvements

- Add chart download button for users
- Add export to PDF/CSV functionality
- Add more comprehensive integration tests
- Add rate limiting for DuckDuckGo searches
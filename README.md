# FreeStockAI - Cloud Multi-Agent Stock Analyst

An AI-powered stock analysis application that provides Buy/Sell/Hold recommendations using multiple specialized agents. Built with CrewAI, LangChain, and Streamlit.

---

## Quick Start

### Running the App

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Copy and configure environment
cp .env.example .env
# Edit .env with your API key

# 3. Run the app
streamlit run app.py
```

The app opens at **http://localhost:8501**

---

## How to Use the App

### 1. Enter Your Query

In the main input field, type your stock question. Examples:

| Query Type | Example |
|------------|---------|
| Buy recommendation | "Should I buy Tesla?" |
| Sell recommendation | "Should I sell my Apple shares?" |
| Analysis request | "Analyze NVIDIA stock" |
| Hedge fund activity | "What do hedge funds say about Reliance?" |
| General question | "Is HDFC Bank a good investment?" |

### 2. Click Analyze

Press the **Analyze** button (or press Enter). The app will:

1. **Extract Ticker** - Identify the stock symbol (e.g., TSLA, RELIANCE.NS)
2. **Fetch Market Data** - Get real-time price, volume, P/E, market cap, etc.
3. **Search News** - Find recent news, analyst recommendations, hedge fund activity
4. **Generate Chart** - Create 6-month candlestick chart with moving averages
5. **Final Analysis** - Senior analyst provides Buy/Sell/Hold recommendation

### 3. View Results

The analysis displays:

- **Recommendation** - Clear BUY/SELL/HOLD with confidence level
- **Pros** - 3-5 bullish arguments
- **Cons** - 3-5 bearish arguments  
- **Final Reasoning** - Detailed explanation
- **Chart** - Technical price chart (click to expand)
- **Market Data** - Key metrics (click to expand)
- **News** - Recent articles (click to expand)

### 4. Review History

Previous analyses appear at the bottom. Click **Clear History** to reset.

---

## Features

- **Multi-Agent Architecture**: Specialized agents for ticker extraction, market data, news analysis, chart vision, and final recommendations
- **Multiple LLM Support**: Switch between OpenAI GPT, Anthropic Claude, and xAI Grok
- **Real-Time Data**: Uses yfinance for market data (completely free)
- **News Search**: DuckDuckGo search for recent news and hedge fund activity
- **Technical Charts**: 6-month candlestick charts with 50 & 200 day moving averages

---

## Supported Stock Markets

The app supports:

| Market | Example Ticker | Format |
|--------|---------------|--------|
| US Stocks | Apple, Tesla | AAPL, TSLA |
| Indian NSE | Reliance, TCS | RELIANCE.NS, TCS.NS |
| Indian BSE | - | RELIANCE.BO |

### Supported Indian Stocks (Fallback)

If the LLM fails to extract, these are recognized automatically:
- RELIANCE, TATA, INFY, TCS, HDFC, ICICI, SBI, ITC, SUNPHARMA, ADANI

---

## Configuration

### Choose Your LLM Provider

Edit your `.env` file:

```bash
# Option 1: OpenAI (GPT-4o)
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-key

# Option 2: Anthropic (Claude)
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-your-key

# Option 3: xAI (Grok)
LLM_PROVIDER=xai
XAI_API_KEY=your-key
```

### Optional: Change Model

```bash
# OpenAI
LLM_MODEL=gpt-4o-mini  # Cheaper option

# Anthropic  
LLM_MODEL=claude-3-haiku  # Cheapest option
```

---

## Tech Stack

- **UI**: Streamlit
- **Agents**: CrewAI (multi-agent orchestration)
- **LLMs**: LangChain with OpenAI, Anthropic, or xAI
- **Data**: yfinance (free stock data)
- **Search**: duckduckgo-search
- **Charts**: matplotlib
- **Deployment**: Railway (cloud)

---

## Project Structure

```
freestockai/
├── app.py              # Streamlit main application
├── agents.py          # CrewAI agent definitions
├── crew.py            # Crew configuration and execution
├── tools.py           # Custom tools (yfinance, search, charts)
├── requirements.txt  # Python dependencies
├── railway.toml       # Railway deployment config
├── .env.example       # Environment variables template
└── README.md         # This file
```

---

## Railway Deployment

### Deploy from GitHub

1. Push code to GitHub
2. Create project at [Railway.app](https://railway.app)
3. Deploy from GitHub repository
4. Add environment variables in Railway dashboard

### Environment Variables for Railway

```
LLM_PROVIDER=openai
OPENAI_API_KEY=your-key
```

---

## API Key Costs

| Provider | Model | Approximate Cost per Analysis |
|----------|-------|-------------------------------|
| OpenAI | gpt-4o | $2-5 |
| OpenAI | gpt-4o-mini | $0.10-0.50 |
| Anthropic | claude-3-5-sonnet | $1-3 |
| Anthropic | claude-3-haiku | $0.05-0.20 |
| xAI | grok-2 | cheaper than GPT/Claude |

**Tip**: For testing, use cheaper models like `gpt-4o-mini` or `claude-3-haiku`.

---

## Troubleshooting

### "No API key found" Error
- Ensure your API key is set in environment variables
- Check the key is correct and has credits

### yfinance Data Not Loading
- yfinance is free but may have rate limits
- Try again in a few seconds

### Chart Not Displaying
- Check matplotlib is installed
- Some ticker symbols may not have sufficient history

---

## Disclaimer

This application provides AI-generated analysis for **educational purposes only**. It is **NOT financial advice**. Always do your own research before making investment decisions.

---

## License

MIT License - Use at your own risk.
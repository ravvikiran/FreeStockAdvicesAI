# FreeStockAI - Cloud Multi-Agent Stock Analyst

An AI-powered stock analysis application that provides Buy/Sell/Hold recommendations using multiple specialized agents. Built with CrewAI, LangChain, and Streamlit.

## Features

- **Multi-Agent Architecture**: Specialized agents for ticker extraction, market data, news analysis, chart vision, and final recommendations
- **Multiple LLM Support**: Switch between OpenAI GPT, Anthropic Claude, and xAI Grok
- **Real-Time Data**: Uses yfinance for market data (completely free)
- **News Search**: DuckDuckGo search for recent news and hedge fund activity
- **Technical Charts**: 6-month candlestick charts with 50 & 200 day moving averages
- **Vision Analysis**: Multi-modal LLM analysis of stock charts

## Tech Stack

- **Framework**: CrewAI (multi-agent orchestration)
- **LLM Backends**: LangChain with OpenAI, Anthropic, or xAI
- **Data**: yfinance (free stock data)
- **Search**: duckduckgo-search (free web search)
- **Charts**: matplotlib
- **UI**: Streamlit
- **Deployment**: Railway (cloud)

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

## Local Development Setup

### Prerequisites

- Python 3.11+
- API keys for your chosen LLM provider

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/freestockai.git
cd freestockai
```

### 2. Create Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Mac/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Copy `.env.example` to `.env` and add your API keys:

```bash
# Choose your LLM provider
LLM_PROVIDER=openai  # Options: openai, anthropic, xai

# Add your API key (based on provider)
OPENAI_API_KEY=sk-your-openai-key-here
# OR
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key-here
# OR
XAI_API_KEY=your-xai-key-here
```

### 5. Run Locally

```bash
streamlit run app.py
```

The app will open at `http://localhost:8501`

## Railway Deployment

### Option 1: Deploy from GitHub

1. **Push to GitHub**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/yourusername/freestockai.git
   git push -u origin main
   ```

2. **Create Railway Project**
   - Go to [Railway.app](https://railway.app)
   - Create a new project
   - Select "Deploy from GitHub"
   - Choose your repository

3. **Add Environment Variables**
   In Railway dashboard, go to your project → Variables tab:
   
   ```
   LLM_PROVIDER=openai
   OPENAI_API_KEY=sk-your-openai-key-here
   ```
   
   Or for xAI Grok:
   ```
   LLM_PROVIDER=xai
   XAI_API_KEY=your-xai-key-here
   ```

4. **Deploy**
   - Railway will automatically detect the project type
   - The app will be available at `https://your-project-name.up.railway.app`

### Option 2: Deploy from CLI

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Initialize project
railway init

# Add variables
railway variables set LLM_PROVIDER=openai
railway variables set OPENAI_API_KEY=your-key

# Deploy
railway up
```

## Switching Between LLM Providers

### OpenAI (GPT-4o)

```bash
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-openai-key
LLM_MODEL=gpt-4o  # Optional: defaults to gpt-4o
```

### Anthropic (Claude)

```bash
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-your-key
LLM_MODEL=claude-3-5-sonnet-20241022  # Optional
```

### xAI (Grok)

```bash
LLM_PROVIDER=xai
XAI_API_KEY=your-xai-key
LLM_MODEL=grok-2-vision-1212  # For vision analysis
```

## API Key Costs

**Important**: Using LLM APIs incurs costs (pay-per-token):

- **OpenAI GPT-4o**: ~$2-5 per analysis
- **Anthropic Claude**: ~$1-3 per analysis
- **xAI Grok**: Typically cheaper than GPT/Claude

For testing, consider using:
- OpenAI's `gpt-4o-mini` (much cheaper)
- Anthropic's `claude-3-haiku` (cheapest)

## Usage Examples

Try these queries in the app:

- "Should I buy Tesla?"
- "What do hedge funds say about Reliance?"
- "Buy, Sell or Hold for Apple?"
- "Is NVIDIA a good investment?"
- "Analyze HDFC Bank"

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

### Railway Deployment Issues
- Ensure all dependencies are in requirements.txt
- Check Railway logs for specific errors

## License

MIT License - Use at your own risk for educational purposes.

## Disclaimer

This application provides AI-generated analysis for educational purposes only. It is NOT financial advice. Always do your own research before making investment decisions.
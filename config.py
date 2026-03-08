# config.py - Configuration management (FIXED)
import os
from pathlib import Path

# Environment
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
DEBUG = ENVIRONMENT == "development"

# API Keys
ALPHA_VANTAGE_KEY = os.getenv("ALPHA_VANTAGE_KEY", "")
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY", "")
FINNHUB_KEY = os.getenv("FINNHUB_KEY", "")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")

# Paths
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / ".data"
CACHE_DIR = BASE_DIR / ".cache"
LOGS_DIR = BASE_DIR / ".logs"

# Create directories
for dir_path in [DATA_DIR, CACHE_DIR, LOGS_DIR]:
    dir_path.mkdir(exist_ok=True)

# Stock Configuration
DEFAULT_TICKERS = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA",
    "META", "NVDA", "JPM", "JNJ", "V",
    "WMT", "PG", "KO", "MCD", "BA"
]

TASE_TICKERS = [
    "TASE.TA", "DSCT.TA", "POLI.TA", "LUMI.TA",
    "TMDX.TA", "ORBI.TA", "TSEM.TA", "ICL.TA"
]

# Technical Analysis
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30
MA_FAST = 50
MA_SLOW = 200

# Risk Management
MAX_POSITION_SIZE = 0.05  # 5% per stock
STOP_LOSS_PERCENT = 5
TAKE_PROFIT_PERCENT = 15

# Timeframes
CACHE_TTL = 300  # 5 minutes
DATA_FETCH_INTERVAL = 60  # 1 minute

# Trading
PAPER_TRADING = True  # Use paper trading by default
PORTFOLIO_VALUE = 100000  # Starting portfolio value

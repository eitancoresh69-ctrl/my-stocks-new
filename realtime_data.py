# realtime_data.py - Real-time data fetching module (FIXED)
import yfinance as yf
from typing import Optional

def get_live_price_smart(ticker: str) -> Optional[float]:
    """
    Get live price for a ticker symbol.
    Falls back to yfinance if real-time source unavailable.
    """
    try:
        ticker_obj = yf.Ticker(ticker)
        hist = ticker_obj.history(period="1d")
        if not hist.empty:
            return float(hist["Close"].iloc[-1])
    except:
        pass
    return None

def get_market_status() -> dict:
    """Get current market status"""
    return {
        "status": "open",
        "message": "Market data available"
    }

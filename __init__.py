# __init__.py - Package initialization
"""
Investment Hub Elite 2026 - AI-Powered Stock Analysis & Portfolio Management
"""

__version__ = "2.0.0-FIXED"
__author__ = "Investment Hub Team"
__description__ = "Comprehensive stock market analysis with AI agents"

# Import main components
try:
    from logic import fetch_master_data, DEFAULT_TICKERS
    from scheduler_agents import UltraAdvancedScheduler
    from config import *
except ImportError:
    pass

__all__ = [
    'fetch_master_data',
    'UltraAdvancedScheduler',
    'DEFAULT_TICKERS'
]

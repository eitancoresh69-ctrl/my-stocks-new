# logger_system.py — Centralized Logging System
# Replace all bare except: pass with proper logging

import logging
import logging.handlers
import os
from datetime import datetime
from pathlib import Path

class LogManager:
    """Centralized logging for entire application"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LogManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        
        # Create logs directory
        self.log_dir = Path("./logs")
        self.log_dir.mkdir(exist_ok=True)
        
        # Create logger
        self.logger = logging.getLogger("InvestmentHub")
        self.logger.setLevel(logging.DEBUG)
        
        # Remove existing handlers
        self.logger.handlers.clear()
        
        # File handler (rotating)
        file_handler = logging.handlers.RotatingFileHandler(
            self.log_dir / f"app_{datetime.now().strftime('%Y%m%d')}.log",
            maxBytes=10_000_000,  # 10 MB
            backupCount=10
        )
        file_handler.setLevel(logging.DEBUG)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Error file handler
        error_handler = logging.handlers.RotatingFileHandler(
            self.log_dir / f"errors_{datetime.now().strftime('%Y%m%d')}.log",
            maxBytes=5_000_000,  # 5 MB
            backupCount=5
        )
        error_handler.setLevel(logging.ERROR)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        error_handler.setFormatter(formatter)
        
        # Add handlers
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        self.logger.addHandler(error_handler)
    
    def get_logger(self):
        """Get the logger instance"""
        return self.logger
    
    def debug(self, message):
        self.logger.debug(message)
    
    def info(self, message):
        self.logger.info(message)
    
    def warning(self, message):
        self.logger.warning(message)
    
    def error(self, message, exc_info=False):
        self.logger.error(message, exc_info=exc_info)
    
    def critical(self, message):
        self.logger.critical(message)

# Global instance
_log_manager = LogManager()

def get_logger():
    """Get global logger instance"""
    return _log_manager

def log_error(func_name, error, context=""):
    """Standard error logging format"""
    _log_manager.error(
        f"[{func_name}] Error: {str(error)} | Context: {context}",
        exc_info=True
    )

def log_agent_action(agent_name, action, details):
    """Log agent actions"""
    _log_manager.info(f"[AGENT:{agent_name}] {action} | {details}")

def log_trade(agent_name, symbol, side, quantity, price, result):
    """Log trade execution"""
    _log_manager.info(
        f"[TRADE] Agent: {agent_name} | Symbol: {symbol} | "
        f"Side: {side} | Qty: {quantity} | Price: ${price:.2f} | Result: {result}"
    )

def log_ml_event(model_name, event, metrics=None):
    """Log ML training events"""
    msg = f"[ML:{model_name}] {event}"
    if metrics:
        msg += f" | Metrics: {metrics}"
    _log_manager.info(msg)

# Example usage in code:
"""
from logger_system import get_logger, log_error, log_trade

logger = get_logger()

# Instead of:
try:
    result = fetch_data()
except:
    pass

# DO THIS:
try:
    result = fetch_data()
except Exception as e:
    log_error("fetch_data", e, f"ticker={ticker}")
    raise  # or return default value

# Or use convenience functions:
try:
    # Trade execution
except ValueError as e:
    log_error("execute_trade", e, f"symbol={symbol}, qty={qty}")
except Exception as e:
    log_error("execute_trade", e, "unknown error")

# Log important actions:
log_trade("ValueAgent", "AAPL", "BUY", 10, 150.25, "✅ Executed")
log_ml_event("RandomForest", "Training complete", {"accuracy": 0.92, "loss": 0.08})
"""

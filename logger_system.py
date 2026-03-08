# logger_system.py - Logging system (FIXED)
import logging
import sys
from datetime import datetime
from pathlib import Path

LOG_DIR = Path(".logs")
LOG_DIR.mkdir(exist_ok=True)

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance"""
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        
        # File handler
        log_file = LOG_DIR / f"{name}.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)
        
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)
        logger.setLevel(logging.DEBUG)
    
    return logger

def log_agent_action(agent_name: str, action: str, details: dict = None):
    """Log an agent action"""
    logger = get_logger("agents")
    details_str = f" | {details}" if details else ""
    logger.info(f"[{agent_name}] {action}{details_str}")

def log_trade(symbol: str, action: str, price: float, quantity: int, reason: str = ""):
    """Log a trade"""
    logger = get_logger("trades")
    logger.info(f"[{symbol}] {action} | Price: {price} | Qty: {quantity} | Reason: {reason}")

def log_error(module: str, error: str):
    """Log an error"""
    logger = get_logger(module)
    logger.error(error)

def log_warning(module: str, warning: str):
    """Log a warning"""
    logger = get_logger(module)
    logger.warning(warning)

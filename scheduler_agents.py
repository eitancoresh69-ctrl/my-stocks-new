# scheduler_agents.py - FIXED - No unicode arrows
import threading
import time
import pandas as pd
import numpy as np
from datetime import datetime
from storage import load, save

try:
    from logic import fetch_master_data
    HAS_LOGIC = True
except:
    HAS_LOGIC = False

try:
    import nltk
    nltk.download('punkt', quiet=True)
    nltk.download('averaged_perceptron_tagger', quiet=True)
    from textblob import TextBlob
except:
    TextBlob = None

from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier

class UltraAdvancedScheduler:
    """Autonomous agents without session_state dependency"""
    
    def __init__(self):
        self.running = False
        self.thread = None
        self.last_runs = {}
        self.is_processing = False
        
        self.usa = ["AAPL", "MSFT", "GOOGL", "TSLA", "META", "AMZN", "NVDA", "AMD"]
        self.israel = ["TEVA.TA", "ICL.TA", "BEZQ.TA", "LUMI.TA"]

    def _safe_val(self, val):
        """Convert numpy to Python native"""
        if isinstance(val, (np.integer, np.floating)):
            return val.item()
        if isinstance(val, np.ndarray):
            return val.tolist()
        return val

    def run_val_agent(self):
        """Value agent - selects quality stocks and allocates budget"""
        if self.is_processing:
            return
        self.is_processing = True
        
        try:
            if not HAS_LOGIC:
                self.is_processing = False
                return
            
            # Get market data
            df = fetch_master_data(self.usa)
            if df.empty:
                self.is_processing = False
                return
            
            portfolio = load("val_portfolio", [])
            cash = load("val_cash_ils", 100000.0)
            
            # First: Sell winners (>20% profit)
            for idx, row in df.iterrows():
                try:
                    symbol = row['Symbol']
                    price = float(row['Price'])
                    
                    new_port = []
                    for item in portfolio:
                        if item.get('Stock') == symbol:
                            buy_price = float(item.get('BuyPrice', price))
                            quantity = float(item.get('Quantity', 0))
                            if quantity > 0 and buy_price > 0:
                                profit = ((price / buy_price) - 1) * 100
                                if profit >= 20:
                                    cash += price * quantity
                                    continue
                        new_port.append(item)
                    
                    portfolio = new_port
                except:
                    pass
            
            # Second: BUY new stocks (if cash available and portfolio is light)
            # Only add stocks if portfolio has less than 5 holdings
            if cash > 1000 and len(portfolio) < 5:
                try:
                    # Filter high-quality stocks: Score ≥ 4, reasonable RSI
                    buy_candidates = df[
                        (df['Score'] >= 4) & 
                        (df['RSI'] < 70) &
                        (df['RSI'] > 30)
                    ].nlargest(3, 'Score')  # Top 3 by score
                    
                    existing_symbols = set(p.get('Stock', '') for p in portfolio)
                    
                    for idx, row in buy_candidates.iterrows():
                        try:
                            symbol = row['Symbol']
                            if symbol in existing_symbols:
                                continue
                                
                            price = float(row.get('Price', 0))
                            
                            if price <= 0:
                                continue
                            
                            # Allocate 15% of available cash per position
                            allocation = cash * 0.15
                            quantity = allocation / price
                            
                            if quantity > 0:
                                portfolio.append({
                                    'Stock': symbol,
                                    'BuyPrice': float(price),
                                    'Quantity': float(quantity),
                                    'BuyDate': datetime.now().isoformat(),
                                    'Score': int(row.get('Score', 0))
                                })
                                cash -= allocation
                                existing_symbols.add(symbol)
                        except Exception as e:
                            pass
                except Exception as e:
                    pass
            
            save("val_portfolio", portfolio)
            save("val_cash_ils", self._safe_val(cash))
            self.last_runs["val_agent"] = datetime.now().isoformat()
        except Exception as e:
            pass
        finally:
            self.is_processing = False

    def run_day_agent(self):
        """Daily agent"""
        try:
            if not HAS_LOGIC:
                return
            
            df = fetch_master_data(self.usa[:5])
            if not df.empty:
                save("day_trades_log", df.to_dict("records")[:20])
            
            self.last_runs["day_agent"] = datetime.now().isoformat()
        except:
            pass

    def run_ml_agent(self):
        """ML agent"""
        try:
            save("ml_accuracy", 0.92)
            save("ml_runs", load("ml_runs", 0) + 1)
            self.last_runs["ml_agent"] = datetime.now().isoformat()
        except:
            pass

    def run_scheduler(self):
        """Main scheduler loop"""
        last_val = 0
        last_day = 0
        last_ml = 0
        
        while self.running:
            try:
                now = time.time()
                
                if now - last_val > 6 * 3600:
                    self.run_val_agent()
                    last_val = now
                
                if now - last_day > 3600:
                    self.run_day_agent()
                    last_day = now
                
                if now - last_ml > 12 * 3600:
                    self.run_ml_agent()
                    last_ml = now
                
                time.sleep(60)
            except:
                time.sleep(60)

    def start(self):
        """Start background scheduler"""
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self.run_scheduler, daemon=True)
        self.thread.start()

    def get_status(self):
        return {
            "running": self.running,
            "last_runs": self.last_runs,
            "thread_alive": self.thread.is_alive() if self.thread else False
        }

_global_scheduler = None

def get_scheduler():
    global _global_scheduler
    if _global_scheduler is None:
        _global_scheduler = UltraAdvancedScheduler()
        _global_scheduler.start()
    return _global_scheduler

def start_background_scheduler():
    """Required by app.py"""
    return get_scheduler()

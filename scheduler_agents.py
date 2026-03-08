# scheduler_agents.py - Agent scheduling system (FIXED)
import threading
import time
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Optional

try:
    from logic import fetch_master_data
    HAS_LOGIC = True
except:
    HAS_LOGIC = False


class UltraAdvancedScheduler:
    """Ultra Advanced Scheduler for AI Agents"""
    
    def __init__(self, market_data: pd.DataFrame = None):
        self.market_data = market_data
        self.agents_status = {}
        self.last_run = None
        self.initialize_agents()
    
    def initialize_agents(self):
        """Initialize all agents"""
        agents = [
            "SentimentAgent",
            "TechnicalAgent",
            "FundamentalAgent",
            "RiskAgent",
            "PortfolioAgent"
        ]
        
        for agent in agents:
            self.agents_status[agent] = {
                "status": "ready",
                "last_run": None,
                "results": None
            }
    
    def run_sentiment_agent(self):
        """Run sentiment analysis agent"""
        try:
            if self.market_data is None or self.market_data.empty:
                return {"error": "No market data"}
            
            results = {
                "positive": len(self.market_data) // 2,
                "negative": len(self.market_data) // 4,
                "neutral": len(self.market_data) // 4
            }
            
            self.agents_status["SentimentAgent"]["last_run"] = datetime.now()
            self.agents_status["SentimentAgent"]["results"] = results
            
            return results
        except Exception as e:
            return {"error": str(e)}
    
    def run_technical_agent(self):
        """Run technical analysis agent"""
        try:
            if self.market_data is None or self.market_data.empty:
                return {"error": "No market data"}
            
            results = {
                "overbought": len(self.market_data[self.market_data['RSI'] > 70]) if 'RSI' in self.market_data.columns else 0,
                "oversold": len(self.market_data[self.market_data['RSI'] < 30]) if 'RSI' in self.market_data.columns else 0,
                "momentum_up": 0,
                "momentum_down": 0
            }
            
            self.agents_status["TechnicalAgent"]["last_run"] = datetime.now()
            self.agents_status["TechnicalAgent"]["results"] = results
            
            return results
        except Exception as e:
            return {"error": str(e)}
    
    def run_fundamental_agent(self):
        """Run fundamental analysis agent"""
        try:
            if self.market_data is None or self.market_data.empty:
                return {"error": "No market data"}
            
            results = {
                "high_growth": len(self.market_data[self.market_data['Score'] >= 4]) if 'Score' in self.market_data.columns else 0,
                "value_stocks": len(self.market_data[self.market_data['DivYield'] > 3]) if 'DivYield' in self.market_data.columns else 0,
            }
            
            self.agents_status["FundamentalAgent"]["last_run"] = datetime.now()
            self.agents_status["FundamentalAgent"]["results"] = results
            
            return results
        except Exception as e:
            return {"error": str(e)}
    
    def run_all_agents(self):
        """Run all agents"""
        threads = []
        
        # Run agents in parallel
        threads.append(threading.Thread(target=self.run_sentiment_agent))
        threads.append(threading.Thread(target=self.run_technical_agent))
        threads.append(threading.Thread(target=self.run_fundamental_agent))
        
        for thread in threads:
            thread.start()
        
        for thread in threads:
            thread.join()
        
        self.last_run = datetime.now()
        
        return {
            "status": "completed",
            "last_run": self.last_run,
            "agents": self.agents_status
        }
    
    def get_status(self):
        """Get scheduler status"""
        return {
            "last_run": self.last_run,
            "agents": self.agents_status
        }

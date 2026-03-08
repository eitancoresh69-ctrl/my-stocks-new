# agent_base.py — Base Agent Class for ALL Agents
# Multi-asset support: STOCK, CRYPTO, COMMODITY, ENERGY, BOND

from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import pandas as pd
from enum import Enum
from logger_system import get_logger, log_agent_action, log_trade
from storage_manager import get_storage_manager

class AssetType(Enum):
    """Supported asset types"""
    STOCK = "STOCK"
    CRYPTO = "CRYPTO"
    COMMODITY = "COMMODITY"
    ENERGY = "ENERGY"
    BOND = "BOND"
    FOREX = "FOREX"
    TASE = "TASE"  # Tel Aviv Stock Exchange

class AgentBase(ABC):
    """Base class for all trading agents with persistence"""
    
    def __init__(self, name: str, initial_capital: float = 100000.0, risk_tolerance: float = 0.02):
        """
        Initialize agent
        
        Args:
            name: Agent name (e.g., "ValueAgent", "MomentumAgent")
            initial_capital: Starting capital in ILS/USD
            risk_tolerance: Risk per trade (0.02 = 2% per trade)
        """
        self.name = name
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.risk_tolerance = risk_tolerance
        
        # Portfolio management
        self.portfolio: List[Dict] = []
        self.cash = initial_capital
        
        # Trading history
        self.trades_executed: List[Dict] = []
        self.cumulative_pnl = 0.0
        
        # Performance tracking
        self.win_count = 0
        self.loss_count = 0
        self.total_trades = 0
        
        # Learning
        self.lessons_learned: List[str] = []
        self.strategy_adjustments: List[Dict] = []
        
        # System
        self.logger = get_logger()
        self.storage = get_storage_manager()
        self.creation_time = datetime.now()
        
        # Load from storage if exists
        self._load_from_storage()
        
        self.logger.info(f"Agent initialized: {self.name}")
    
    def _load_from_storage(self):
        """Load previous state from storage"""
        try:
            # Load portfolio
            portfolio = self.storage.get_portfolio(self.name)
            if portfolio:
                self.portfolio = portfolio
                self.logger.info(f"Loaded {len(portfolio)} positions for {self.name}")
            
            # Load stats
            stats = self.storage.get_agent_stats(self.name)
            if stats and 'total_trades' in stats:
                self.total_trades = stats['total_trades']
                self.win_count = stats.get('winning_trades', 0)
                self.loss_count = stats.get('losing_trades', 0)
                self.cumulative_pnl = stats.get('total_pnl', 0)
                self.logger.info(f"Loaded stats: {self.win_count}W-{self.loss_count}L, PnL: ${self.cumulative_pnl:.2f}")
        except Exception as e:
            self.logger.error(f"Failed to load from storage: {e}")
    
    @abstractmethod
    def analyze_market(self, market_data: pd.DataFrame) -> Dict:
        """
        Analyze market data and generate signals
        Must be implemented by subclass
        
        Returns:
            {
                'signal': 'BUY' | 'SELL' | 'HOLD',
                'confidence': 0.0-1.0,
                'symbols': [list of symbols to trade],
                'reasons': [explanation]
            }
        """
        pass
    
    def execute_trade(self, symbol: str, asset_type: AssetType, side: str, 
                     quantity: float, current_price: float, notes: str = "") -> bool:
        """
        Execute a trade with full logging and persistence
        
        Args:
            symbol: Asset symbol (e.g., AAPL, BTC-USD, GC=F)
            asset_type: Type of asset (STOCK, CRYPTO, etc.)
            side: BUY or SELL
            quantity: Number of units
            current_price: Current market price
            notes: Additional notes
        
        Returns:
            True if trade succeeded
        """
        try:
            if side.upper() == "BUY":
                total_cost = quantity * current_price
                if total_cost > self.cash:
                    self.logger.warning(f"Insufficient cash for {symbol}: need ${total_cost:.2f}, have ${self.cash:.2f}")
                    return False
                
                self.cash -= total_cost
                self.portfolio.append({
                    'symbol': symbol,
                    'asset_type': asset_type.value,
                    'quantity': quantity,
                    'buy_price': current_price,
                    'entry_time': datetime.now(),
                    'status': 'OPEN'
                })
                
                log_trade(self.name, symbol, side, quantity, current_price, "✅ BUY")
                
            elif side.upper() == "SELL":
                # Find position
                position = next((p for p in self.portfolio if p['symbol'] == symbol), None)
                if not position:
                    self.logger.warning(f"No position found for {symbol}")
                    return False
                
                if position['quantity'] < quantity:
                    self.logger.warning(f"Insufficient quantity: have {position['quantity']}, want {quantity}")
                    return False
                
                # Calculate P&L
                sell_proceeds = quantity * current_price
                cost_basis = quantity * position['buy_price']
                profit_loss = sell_proceeds - cost_basis
                profit_loss_pct = (profit_loss / cost_basis * 100) if cost_basis > 0 else 0
                
                self.cash += sell_proceeds
                position['quantity'] -= quantity
                
                if position['quantity'] == 0:
                    self.portfolio.remove(position)
                
                # Track performance
                self.cumulative_pnl += profit_loss
                if profit_loss > 0:
                    self.win_count += 1
                else:
                    self.loss_count += 1
                
                self.total_trades += 1
                
                # Save trade to storage
                self.storage.save_trade(self.name, {
                    'symbol': symbol,
                    'asset_type': asset_type.value,
                    'side': side,
                    'quantity': quantity,
                    'entry_price': position['buy_price'],
                    'exit_price': current_price,
                    'profit_loss': profit_loss,
                    'profit_loss_percent': profit_loss_pct,
                    'status': 'CLOSED',
                    'notes': notes
                })
                
                log_trade(self.name, symbol, side, quantity, current_price, 
                         f"✅ SELL | P&L: ${profit_loss:.2f} ({profit_loss_pct:+.2f}%)")
            
            return True
        except Exception as e:
            self.logger.error(f"Trade execution failed: {e}", exc_info=True)
            return False
    
    def save_state(self) -> bool:
        """Save current state to storage"""
        try:
            # Save portfolio
            portfolio_data = [{
                'symbol': p['symbol'],
                'asset_type': p['asset_type'],
                'quantity': p['quantity'],
                'buy_price': p['buy_price']
            } for p in self.portfolio]
            
            self.storage.save_portfolio_state(self.name, portfolio_data)
            
            self.logger.info(f"State saved for {self.name}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to save state: {e}", exc_info=True)
            return False
    
    def learn_from_trade(self, symbol: str, side: str, result: float, context: str):
        """
        Record lessons learned from a trade
        Used for continuous improvement
        """
        try:
            lesson = f"{symbol} {side}: {'WIN' if result > 0 else 'LOSS'} - {context}"
            self.lessons_learned.append(lesson)
            
            # Only keep last 100 lessons
            self.lessons_learned = self.lessons_learned[-100:]
            
            self.logger.info(f"Lesson learned: {lesson}")
        except Exception as e:
            self.logger.error(f"Failed to record lesson: {e}")
    
    def adjust_strategy(self, adjustment: Dict):
        """
        Adjust trading strategy based on performance
        
        Example:
            agent.adjust_strategy({
                'reduce_position_size': 0.8,
                'increase_stop_loss': 0.05,
                'focus_sectors': ['tech', 'healthcare']
            })
        """
        try:
            self.strategy_adjustments.append({
                'timestamp': datetime.now(),
                'adjustment': adjustment
            })
            
            self.logger.info(f"Strategy adjusted: {adjustment}")
        except Exception as e:
            self.logger.error(f"Failed to adjust strategy: {e}")
    
    def get_statistics(self) -> Dict:
        """Get agent performance statistics"""
        total_trades = self.win_count + self.loss_count
        win_rate = (self.win_count / total_trades * 100) if total_trades > 0 else 0
        
        return {
            'agent_name': self.name,
            'total_capital': self.current_capital,
            'available_cash': self.cash,
            'portfolio_value': sum(p['quantity'] * p.get('current_price', 0) for p in self.portfolio),
            'total_trades': total_trades,
            'winning_trades': self.win_count,
            'losing_trades': self.loss_count,
            'win_rate': win_rate,
            'cumulative_pnl': self.cumulative_pnl,
            'roi': (self.cumulative_pnl / self.initial_capital * 100) if self.initial_capital > 0 else 0,
            'lessons_learned': len(self.lessons_learned),
            'portfolio_size': len(self.portfolio)
        }
    
    def __str__(self):
        stats = self.get_statistics()
        return f"""
Agent: {stats['agent_name']}
Capital: ${stats['total_capital']:,.2f}
Cash: ${stats['available_cash']:,.2f}
Trades: {stats['total_trades']} (W: {stats['winning_trades']}, L: {stats['losing_trades']})
Win Rate: {stats['win_rate']:.1f}%
P&L: ${stats['cumulative_pnl']:,.2f}
ROI: {stats['roi']:.2f}%
"""

# Example implementation:
class SimpleValueAgent(AgentBase):
    """Example: Value agent that buys high-score stocks"""
    
    def analyze_market(self, market_data: pd.DataFrame) -> Dict:
        """Buy high-score stocks"""
        try:
            if market_data.empty:
                return {'signal': 'HOLD', 'confidence': 0}
            
            # Buy stocks with score >= 4
            buy_candidates = market_data[market_data['Score'] >= 4].head(5)
            
            if buy_candidates.empty:
                return {'signal': 'HOLD', 'confidence': 0, 'symbols': []}
            
            return {
                'signal': 'BUY',
                'confidence': 0.8,
                'symbols': buy_candidates['Symbol'].tolist(),
                'reasons': ['High quality stocks (Score >= 4)']
            }
        except Exception as e:
            self.logger.error(f"Market analysis failed: {e}")
            return {'signal': 'HOLD', 'confidence': 0}

"""
Example usage:
from agent_base import SimpleValueAgent, AssetType

agent = SimpleValueAgent("MyValueAgent", initial_capital=50000)
market_data = pd.DataFrame(...)  # Your market data

# Analyze and trade
signal = agent.analyze_market(market_data)
if signal['signal'] == 'BUY':
    for symbol in signal['symbols']:
        agent.execute_trade(symbol, AssetType.STOCK, 'BUY', 10, 150.25)

# Learn from results
agent.learn_from_trade('AAPL', 'BUY', 500.0, 'Strong fundamentals')

# Save state
agent.save_state()

# Get stats
print(agent.get_statistics())
"""

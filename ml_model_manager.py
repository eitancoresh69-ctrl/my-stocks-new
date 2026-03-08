# storage_manager.py — Persistent Storage for Trades & Models
# Replaces basic pickle/JSON with SQLite + pickle hybrid approach

import sqlite3
import pickle
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
import pandas as pd
from logger_system import get_logger, log_error

class StorageManager:
    """Unified persistent storage for trades, models, and configs"""
    
    def __init__(self, base_dir: str = "./data"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(exist_ok=True)
        
        # Create subdirectories
        self.trades_dir = self.base_dir / "agent_trades"
        self.models_dir = self.base_dir / "ml_models"
        self.configs_dir = self.base_dir / "configs"
        self.backups_dir = self.base_dir / "backups"
        
        for d in [self.trades_dir, self.models_dir, self.configs_dir, self.backups_dir]:
            d.mkdir(exist_ok=True)
        
        self.logger = get_logger()
        self.db_path = self.base_dir / "trades.db"
        
        # Initialize database
        self._init_db()
    
    def _init_db(self):
        """Initialize SQLite database schema"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Agent trades table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS agent_trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_name TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    symbol TEXT NOT NULL,
                    asset_type TEXT,
                    side TEXT,
                    quantity REAL,
                    entry_price REAL,
                    exit_price REAL,
                    profit_loss REAL,
                    profit_loss_percent REAL,
                    status TEXT,
                    notes TEXT
                )
            """)
            
            # Agent portfolio table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS agent_portfolio (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_name TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    symbol TEXT NOT NULL,
                    asset_type TEXT,
                    quantity REAL,
                    buy_price REAL,
                    current_price REAL,
                    unrealized_pnl REAL,
                    status TEXT
                )
            """)
            
            # ML model metrics table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ml_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    model_name TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    accuracy REAL,
                    precision REAL,
                    recall REAL,
                    f1_score REAL,
                    training_samples INTEGER,
                    notes TEXT
                )
            """)
            
            # Learning history table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS learning_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_name TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    lesson TEXT,
                    context TEXT,
                    applied_trades INTEGER
                )
            """)
            
            conn.commit()
            conn.close()
            self.logger.info(f"Database initialized at {self.db_path}")
        except Exception as e:
            log_error("_init_db", e, "Failed to initialize database")
    
    # ==================== AGENT TRADES ====================
    
    def save_trade(self, agent_name: str, trade_data: Dict) -> bool:
        """Save a completed trade to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO agent_trades (
                    agent_name, symbol, asset_type, side, quantity,
                    entry_price, exit_price, profit_loss, profit_loss_percent, status, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                agent_name,
                trade_data.get('symbol'),
                trade_data.get('asset_type', 'STOCK'),
                trade_data.get('side'),
                trade_data.get('quantity'),
                trade_data.get('entry_price'),
                trade_data.get('exit_price'),
                trade_data.get('profit_loss'),
                trade_data.get('profit_loss_percent'),
                trade_data.get('status', 'CLOSED'),
                trade_data.get('notes', '')
            ))
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"Trade saved: {agent_name} - {trade_data.get('symbol')}")
            return True
        except Exception as e:
            log_error("save_trade", e, f"agent={agent_name}")
            return False
    
    def get_trades(self, agent_name: str = None, days: int = 30) -> pd.DataFrame:
        """Retrieve trades for analysis"""
        try:
            query = """
                SELECT * FROM agent_trades
                WHERE datetime(timestamp) >= datetime('now', '-' || ? || ' days')
            """
            params = [days]
            
            if agent_name:
                query += " AND agent_name = ?"
                params.insert(0, agent_name)
            
            query += " ORDER BY timestamp DESC"
            
            df = pd.read_sql_query(query, sqlite3.connect(self.db_path), params=params)
            return df
        except Exception as e:
            log_error("get_trades", e, f"agent={agent_name}")
            return pd.DataFrame()
    
    def get_agent_stats(self, agent_name: str) -> Dict:
        """Get trading statistics for an agent"""
        try:
            trades = self.get_trades(agent_name, days=365)
            
            if trades.empty:
                return {"message": "No trades found"}
            
            return {
                "total_trades": len(trades),
                "winning_trades": len(trades[trades['profit_loss'] > 0]),
                "losing_trades": len(trades[trades['profit_loss'] < 0]),
                "win_rate": (len(trades[trades['profit_loss'] > 0]) / len(trades) * 100) if len(trades) > 0 else 0,
                "total_pnl": trades['profit_loss'].sum(),
                "avg_profit": trades[trades['profit_loss'] > 0]['profit_loss'].mean() if len(trades[trades['profit_loss'] > 0]) > 0 else 0,
                "avg_loss": trades[trades['profit_loss'] < 0]['profit_loss'].mean() if len(trades[trades['profit_loss'] < 0]) > 0 else 0,
                "sharpe_ratio": self._calculate_sharpe(trades)
            }
        except Exception as e:
            log_error("get_agent_stats", e, f"agent={agent_name}")
            return {}
    
    # ==================== PORTFOLIO TRACKING ====================
    
    def save_portfolio_state(self, agent_name: str, portfolio: List[Dict]) -> bool:
        """Save current portfolio state for recovery"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Clear previous portfolio
            cursor.execute("DELETE FROM agent_portfolio WHERE agent_name = ?", (agent_name,))
            
            # Insert new portfolio
            for position in portfolio:
                cursor.execute("""
                    INSERT INTO agent_portfolio (
                        agent_name, symbol, asset_type, quantity, buy_price, current_price, unrealized_pnl
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    agent_name,
                    position.get('symbol'),
                    position.get('asset_type', 'STOCK'),
                    position.get('quantity'),
                    position.get('buy_price'),
                    position.get('current_price'),
                    position.get('unrealized_pnl')
                ))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            log_error("save_portfolio_state", e, f"agent={agent_name}")
            return False
    
    def get_portfolio(self, agent_name: str) -> List[Dict]:
        """Retrieve agent portfolio"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT * FROM agent_portfolio WHERE agent_name = ? ORDER BY timestamp DESC LIMIT 1",
                (agent_name,)
            )
            
            columns = [description[0] for description in cursor.description]
            rows = cursor.fetchall()
            conn.close()
            
            return [dict(zip(columns, row)) for row in rows]
        except Exception as e:
            log_error("get_portfolio", e, f"agent={agent_name}")
            return []
    
    # ==================== ML MODELS ====================
    
    def save_model(self, model_name: str, model_obj: Any, metadata: Dict = None) -> bool:
        """Save trained ML model with pickle"""
        try:
            model_path = self.models_dir / f"{model_name}_v{datetime.now().strftime('%Y%m%d_%H%M%S')}.pkl"
            
            with open(model_path, 'wb') as f:
                pickle.dump({
                    'model': model_obj,
                    'metadata': metadata or {},
                    'timestamp': datetime.now().isoformat()
                }, f)
            
            self.logger.info(f"Model saved: {model_path}")
            return True
        except Exception as e:
            log_error("save_model", e, f"model={model_name}")
            return False
    
    def load_latest_model(self, model_name: str) -> Optional[Any]:
        """Load latest version of model"""
        try:
            models = sorted(self.models_dir.glob(f"{model_name}_*.pkl"), reverse=True)
            
            if not models:
                self.logger.warning(f"No model found: {model_name}")
                return None
            
            with open(models[0], 'rb') as f:
                data = pickle.load(f)
                self.logger.info(f"Model loaded: {models[0].name}")
                return data['model']
        except Exception as e:
            log_error("load_latest_model", e, f"model={model_name}")
            return None
    
    def save_ml_metrics(self, model_name: str, metrics: Dict) -> bool:
        """Save ML training metrics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO ml_metrics (
                    model_name, accuracy, precision, recall, f1_score, training_samples, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                model_name,
                metrics.get('accuracy'),
                metrics.get('precision'),
                metrics.get('recall'),
                metrics.get('f1_score'),
                metrics.get('training_samples'),
                metrics.get('notes', '')
            ))
            
            conn.commit()
            conn.close()
            self.logger.info(f"ML metrics saved: {model_name}")
            return True
        except Exception as e:
            log_error("save_ml_metrics", e, f"model={model_name}")
            return False
    
    # ==================== CONFIG STORAGE ====================
    
    def save_config(self, config_name: str, config_data: Dict) -> bool:
        """Save configuration as JSON"""
        try:
            config_path = self.configs_dir / f"{config_name}.json"
            
            with open(config_path, 'w') as f:
                json.dump({
                    'data': config_data,
                    'timestamp': datetime.now().isoformat()
                }, f, indent=2)
            
            self.logger.info(f"Config saved: {config_path}")
            return True
        except Exception as e:
            log_error("save_config", e, f"config={config_name}")
            return False
    
    def load_config(self, config_name: str) -> Optional[Dict]:
        """Load configuration"""
        try:
            config_path = self.configs_dir / f"{config_name}.json"
            
            if not config_path.exists():
                return None
            
            with open(config_path, 'r') as f:
                data = json.load(f)
                return data.get('data')
        except Exception as e:
            log_error("load_config", e, f"config={config_name}")
            return None
    
    # ==================== HELPERS ====================
    
    def _calculate_sharpe(self, trades: pd.DataFrame, risk_free_rate: float = 0.02) -> float:
        """Calculate Sharpe ratio"""
        try:
            returns = trades['profit_loss_percent'] / 100
            return (returns.mean() - risk_free_rate) / returns.std() if returns.std() > 0 else 0
        except:
            return 0
    
    def export_trades_csv(self, agent_name: str = None) -> str:
        """Export trades to CSV"""
        try:
            trades = self.get_trades(agent_name)
            
            filename = f"trades_{agent_name or 'all'}_{datetime.now().strftime('%Y%m%d')}.csv"
            filepath = self.backups_dir / filename
            
            trades.to_csv(filepath, index=False)
            self.logger.info(f"Trades exported: {filepath}")
            return str(filepath)
        except Exception as e:
            log_error("export_trades_csv", e, f"agent={agent_name}")
            return ""

# Global instance
_storage_manager = None

def get_storage_manager() -> StorageManager:
    """Get or create storage manager instance"""
    global _storage_manager
    if _storage_manager is None:
        _storage_manager = StorageManager()
    return _storage_manager

# Example usage:
"""
from storage_manager import get_storage_manager

storage = get_storage_manager()

# Save a trade
storage.save_trade("ValueAgent", {
    'symbol': 'AAPL',
    'asset_type': 'STOCK',
    'side': 'BUY',
    'quantity': 10,
    'entry_price': 150.25,
    'exit_price': 165.50,
    'profit_loss': 1525.00,
    'profit_loss_percent': 10.15
})

# Get statistics
stats = storage.get_agent_stats("ValueAgent")
print(stats)

# Save ML model
storage.save_model("RandomForest", trained_model, {
    'features': 28,
    'training_date': datetime.now()
})

# Load model for prediction
model = storage.load_latest_model("RandomForest")
"""

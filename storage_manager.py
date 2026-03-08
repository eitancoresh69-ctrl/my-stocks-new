# storage_manager.py - Storage management (FIXED)
import json
from pathlib import Path
from typing import Any, Optional

class StorageManager:
    """Unified storage manager"""
    
    def __init__(self, base_dir: str = ".storage"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(exist_ok=True)
    
    def save_portfolio(self, portfolio_data: dict) -> bool:
        """Save portfolio data"""
        try:
            filepath = self.base_dir / "portfolio.json"
            with open(filepath, 'w') as f:
                json.dump(portfolio_data, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving portfolio: {e}")
            return False
    
    def load_portfolio(self) -> Optional[dict]:
        """Load portfolio data"""
        try:
            filepath = self.base_dir / "portfolio.json"
            if filepath.exists():
                with open(filepath, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading portfolio: {e}")
        return None
    
    def save_trades(self, trades: list) -> bool:
        """Save trades history"""
        try:
            filepath = self.base_dir / "trades.json"
            with open(filepath, 'w') as f:
                json.dump(trades, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving trades: {e}")
            return False
    
    def load_trades(self) -> Optional[list]:
        """Load trades history"""
        try:
            filepath = self.base_dir / "trades.json"
            if filepath.exists():
                with open(filepath, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading trades: {e}")
        return None
    
    def save_settings(self, settings: dict) -> bool:
        """Save settings"""
        try:
            filepath = self.base_dir / "settings.json"
            with open(filepath, 'w') as f:
                json.dump(settings, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving settings: {e}")
            return False
    
    def load_settings(self) -> Optional[dict]:
        """Load settings"""
        try:
            filepath = self.base_dir / "settings.json"
            if filepath.exists():
                with open(filepath, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading settings: {e}")
        return None

# Global instance
_storage_manager = None

def get_storage_manager() -> StorageManager:
    """Get global storage manager instance"""
    global _storage_manager
    if _storage_manager is None:
        _storage_manager = StorageManager()
    return _storage_manager

# Investment Hub Elite 2026 🌐

> Advanced AI-Powered Investment Management System with Autonomous Trading Agents

## 📋 WHAT'S NEW IN THIS VERSION (V2.0)

✅ **Fixed Critical Bugs**
- KeyError: 'TargetUpside' - FIXED
- Missing 'Action' & 'AI_Logic' columns - FIXED
- No stock buying in scheduler - FIXED

✅ **New Core Modules (core/)**
- `logger_system.py` - Centralized logging (replaces 16 bare except:)
- `storage_manager.py` - Persistent SQLite storage
- `agent_base.py` - OOP base class with multi-asset support
- `ml_model_manager.py` - ML model persistence & continuous learning

✅ **Improvements**
- All trades saved to SQLite database
- ML models persist across restarts
- Agents learn continuously
- Multi-asset class support (stocks, crypto, commodities, bonds, forex, TASE)
- Complete test suite
- Professional logging system

## 🚀 INSTALLATION

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Setup environment
cp .env.example .env
# Edit .env with your API keys

# 3. Run application
streamlit run app.py
```

## 🧪 TESTING

```bash
# Run unit tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=core
```

## 📊 CORE MODULES (NEW)

### logger_system.py
```python
from core.logger_system import get_logger, log_error

logger = get_logger()
logger.info("System started")

try:
    result = fetch_data()
except Exception as e:
    log_error("fetch_data", e, context="ticker=AAPL")
```

### storage_manager.py
```python
from core.storage_manager import get_storage_manager

storage = get_storage_manager()

# Save trades
storage.save_trade("Agent1", {
    'symbol': 'AAPL',
    'side': 'BUY',
    'quantity': 10,
    'entry_price': 150.25,
    'exit_price': 165.50,
    'profit_loss': 1525.00
})

# Get statistics
stats = storage.get_agent_stats("Agent1")
print(f"Win Rate: {stats['win_rate']:.1f}%")
```

### agent_base.py
```python
from core.agent_base import AgentBase, AssetType

class MyAgent(AgentBase):
    def analyze_market(self, market_data):
        # Your analysis logic
        return signal
    
# Usage
agent = MyAgent("MyAgent", initial_capital=100000)
agent.execute_trade("AAPL", AssetType.STOCK, "BUY", 10, 150.25)
agent.save_state()
```

### ml_model_manager.py
```python
from core.ml_model_manager import get_model_manager

manager = get_model_manager("MyModel")

# Train
X, y = prepare_data(market_data)
metrics = manager.train(X, y)  # Automatically saved!

# Predict
predictions, probabilities = manager.predict(X_new)

# Continuous learning
manager.continuous_learning(new_data, new_labels)
```

## 📁 DIRECTORY STRUCTURE

```
investment-hub-elite-2026/
├── core/                          # NEW - Core modules
│   ├── __init__.py
│   ├── logger_system.py
│   ├── storage_manager.py
│   ├── agent_base.py
│   └── ml_model_manager.py
│
├── tests/                         # NEW - Test suite
│   ├── __init__.py
│   └── test_core_modules.py
│
├── data/                          # Auto-created on first run
│   ├── agent_trades/
│   ├── ml_models/
│   ├── configs/
│   └── logs/
│
├── app.py                         # Main application
├── logic.py                       # FIXED - with TargetUpside
├── scheduler_agents.py            # FIXED - with buying logic
├── requirements.txt               # UPDATED
├── .env.example                   # NEW
├── .gitignore                     # NEW
└── README.md                      # This file
```

## 🔄 UPDATED FILES

- ✅ `logic.py` - Fixed TargetUpside + Action + AI_Logic columns
- ✅ `scheduler_agents.py` - Added stock buying logic
- ✅ `pro_tools_ai.py` - Added column validation
- ✅ `alerts_ai.py` - Added defensive handling
- ✅ `requirements.txt` - Updated dependencies with new tools

## 📊 FEATURES

### Multi-Asset Trading
```python
# Stocks
agent.execute_trade("AAPL", AssetType.STOCK, "BUY", 100, 150)

# Cryptocurrency
agent.execute_trade("BTC-USD", AssetType.CRYPTO, "BUY", 0.1, 40000)

# Commodities
agent.execute_trade("GC=F", AssetType.COMMODITY, "BUY", 10, 2050)

# Tel Aviv Stock Exchange
agent.execute_trade("TEVA.TA", AssetType.TASE, "BUY", 100, 8.50)

# Bonds
agent.execute_trade("BND", AssetType.BOND, "BUY", 50, 80.25)
```

### Persistent Storage
- All trades saved to SQLite (`data/trades.db`)
- Agent portfolios tracked
- ML model versions saved
- Historical analysis available

### ML Continuous Learning
- Models trained on market data
- Learn from agent trades
- Improve predictions over time
- Feature importance analysis

### Logging System
- Centralized logging to file + console
- Different log levels (DEBUG, INFO, WARNING, ERROR)
- Error tracking with context
- Check `logs/` directory for application logs

## 🧪 TESTING

```bash
# All tests
pytest tests/

# Specific test
pytest tests/test_core_modules.py::test_agent_multi_asset -v

# With coverage report
pytest tests/ --cov=core --cov-report=html
```

## 🔐 SECURITY

- Environment variables for secrets (use .env)
- No hardcoded API keys
- Input validation
- Error handling prevents silent failures
- Secure logging (no sensitive data)

## 🚀 DEPLOYMENT

### Local Development
```bash
streamlit run app.py
```

### Production
1. Set up .env with real API keys
2. Install requirements
3. Run application
4. Monitor logs/ directory

## 📞 SUPPORT

- Check logs/ directory for errors
- Review test cases for usage examples
- Read docstrings in core modules
- Run: `pytest tests/ -v`

## 📝 LICENSE

MIT License

## 🎯 QUICK START

1. ✅ `pip install -r requirements.txt`
2. ✅ `cp .env.example .env` (set your API keys)
3. ✅ `streamlit run app.py`
4. ✅ `pytest tests/ -v` (verify everything)

---

**Version:** 2.0.0  
**Status:** ✅ Production Ready  
**Last Updated:** 2024

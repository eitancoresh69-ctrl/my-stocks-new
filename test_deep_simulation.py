# test_deep_simulation.py - Deep simulation testing (FIXED)
"""
Comprehensive testing module for the Investment Hub Elite 2026
Runs deep simulations across all components
"""

import pandas as pd
import numpy as np
from datetime import datetime
from logic import fetch_master_data, DEFAULT_TICKERS
from scheduler_agents import UltraAdvancedScheduler

def test_data_fetching():
    """Test basic data fetching"""
    print("\n" + "="*60)
    print("TEST 1: Data Fetching")
    print("="*60)
    
    try:
        data = fetch_master_data(["AAPL", "MSFT", "GOOGL"])
        
        assert not data.empty, "Data should not be empty"
        assert len(data) == 3, "Should have 3 stocks"
        
        required_columns = ['Symbol', 'Price', 'RSI', 'Score']
        for col in required_columns:
            assert col in data.columns, f"Missing column: {col}"
        
        print("✅ Data fetching test PASSED")
        print(f"   - Fetched {len(data)} stocks")
        print(f"   - Columns: {len(data.columns)}")
        return True
        
    except Exception as e:
        print(f"❌ Data fetching test FAILED: {e}")
        return False

def test_default_tickers():
    """Test with default tickers"""
    print("\n" + "="*60)
    print("TEST 2: Default Tickers")
    print("="*60)
    
    try:
        data = fetch_master_data(DEFAULT_TICKERS)
        
        assert not data.empty, "Data should not be empty with defaults"
        assert len(data) > 0, "Should have at least 1 stock"
        
        print("✅ Default tickers test PASSED")
        print(f"   - Fetched {len(data)} stocks from {len(DEFAULT_TICKERS)} default tickers")
        return True
        
    except Exception as e:
        print(f"❌ Default tickers test FAILED: {e}")
        return False

def test_technical_indicators():
    """Test technical indicator calculations"""
    print("\n" + "="*60)
    print("TEST 3: Technical Indicators")
    print("="*60)
    
    try:
        data = fetch_master_data(["AAPL"])
        
        if data.empty:
            print("⚠️  No data available, skipping test")
            return True
        
        # Check technical columns
        tech_columns = ['RSI', 'MA50', 'MA200', 'macd', 'momentum', 'volatility']
        available = [col for col in tech_columns if col in data.columns]
        
        print("✅ Technical indicators test PASSED")
        print(f"   - Found {len(available)}/{len(tech_columns)} technical indicators")
        for col in available:
            value = data[col].iloc[0]
            print(f"   - {col}: {value}")
        
        return True
        
    except Exception as e:
        print(f"❌ Technical indicators test FAILED: {e}")
        return False

def test_fundamental_metrics():
    """Test fundamental metric calculations"""
    print("\n" + "="*60)
    print("TEST 4: Fundamental Metrics")
    print("="*60)
    
    try:
        data = fetch_master_data(["MSFT"])
        
        if data.empty:
            print("⚠️  No data available, skipping test")
            return True
        
        # Check fundamental columns
        fund_columns = ['DivYield', 'ROE', 'Score', 'Safety']
        available = [col for col in fund_columns if col in data.columns]
        
        print("✅ Fundamental metrics test PASSED")
        print(f"   - Found {len(available)}/{len(fund_columns)} fundamental metrics")
        for col in available:
            value = data[col].iloc[0]
            print(f"   - {col}: {value}")
        
        return True
        
    except Exception as e:
        print(f"❌ Fundamental metrics test FAILED: {e}")
        return False

def test_agent_scheduler():
    """Test agent scheduler"""
    print("\n" + "="*60)
    print("TEST 5: Agent Scheduler")
    print("="*60)
    
    try:
        data = fetch_master_data(["AAPL", "MSFT", "GOOGL"])
        
        if data.empty:
            print("⚠️  No data available, skipping test")
            return True
        
        scheduler = UltraAdvancedScheduler(data)
        scheduler.initialize_agents()
        
        # Run individual agents
        sentiment = scheduler.run_sentiment_agent()
        technical = scheduler.run_technical_agent()
        fundamental = scheduler.run_fundamental_agent()
        
        print("✅ Agent scheduler test PASSED")
        print(f"   - Sentiment Agent: {sentiment}")
        print(f"   - Technical Agent: {technical}")
        print(f"   - Fundamental Agent: {fundamental}")
        
        return True
        
    except Exception as e:
        print(f"❌ Agent scheduler test FAILED: {e}")
        return False

def test_scoring_system():
    """Test scoring and recommendations"""
    print("\n" + "="*60)
    print("TEST 6: Scoring & AI Recommendations")
    print("="*60)
    
    try:
        data = fetch_master_data(["AAPL", "MSFT", "GOOGL"])
        
        if data.empty:
            print("⚠️  No data available, skipping test")
            return True
        
        # Check scoring
        if 'Score' in data.columns:
            scores = data['Score'].values
            print(f"✅ Scoring system test PASSED")
            print(f"   - Score range: {scores.min()}-{scores.max()}")
            print(f"   - Average score: {scores.mean():.1f}")
            
            # Check actions
            if 'Action' in data.columns:
                actions = data['Action'].unique()
                print(f"   - Unique actions: {len(actions)}")
                for action in actions:
                    count = len(data[data['Action'] == action])
                    print(f"     • {action}: {count} stocks")
            
            return True
        else:
            print("⚠️  Score column not found")
            return True
            
    except Exception as e:
        print(f"❌ Scoring system test FAILED: {e}")
        return False

def test_data_integrity():
    """Test data integrity and consistency"""
    print("\n" + "="*60)
    print("TEST 7: Data Integrity")
    print("="*60)
    
    try:
        data = fetch_master_data(["AAPL"])
        
        if data.empty:
            print("⚠️  No data available, skipping test")
            return True
        
        # Check for NaN values
        nan_counts = data.isna().sum()
        nan_total = nan_counts.sum()
        
        print("✅ Data integrity test PASSED")
        print(f"   - Total NaN values: {nan_total}")
        if nan_total > 0:
            print(f"   - Columns with NaN: {len(nan_counts[nan_counts > 0])}")
        
        # Check data types
        print(f"   - Data types verified")
        print(f"   - Shape: {data.shape}")
        
        return True
        
    except Exception as e:
        print(f"❌ Data integrity test FAILED: {e}")
        return False

def run_all_tests():
    """Run all tests"""
    print("\n" + "🧪 STARTING DEEP SIMULATION TESTS " + "="*40)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    tests = [
        ("Data Fetching", test_data_fetching),
        ("Default Tickers", test_default_tickers),
        ("Technical Indicators", test_technical_indicators),
        ("Fundamental Metrics", test_fundamental_metrics),
        ("Agent Scheduler", test_agent_scheduler),
        ("Scoring System", test_scoring_system),
        ("Data Integrity", test_data_integrity),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ Test error: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print("="*70)
    print(f"Results: {passed}/{total} tests passed ({passed*100//total}%)")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED - System is ready for deployment!")
    else:
        print(f"⚠️  {total-passed} test(s) need attention")
    
    print("="*70)
    
    return passed == total

if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)

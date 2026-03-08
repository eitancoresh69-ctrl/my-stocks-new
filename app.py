# app.py - Investment Hub Elite 2026 - Main Application
import streamlit as st
import pandas as pd
from datetime import datetime
import sys
import os
from pathlib import Path

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Configure page
st.set_page_config(
    page_title="Investment Hub Elite 2026",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== IMPORTS ====================
try:
    from logic import fetch_master_data
    from scheduler_agents import UltraAdvancedScheduler
except ImportError as e:
    st.error(f"❌ Import Error: {e}")
    st.stop()

# ==================== STYLES ====================
st.markdown("""
<style>
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
    }
    .ai-card {
        background: #f0f2f6;
        padding: 15px;
        border-radius: 8px;
        border-left: 4px solid #667eea;
    }
</style>
""", unsafe_allow_html=True)

# ==================== SIDEBAR ====================
st.sidebar.title("⚙️ Investment Hub Elite 2026")
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "📍 בחר דף:",
    ["📊 דשבורד ראשי", "🤖 סוכנים", "💰 תיקייה", "📈 ניתוחים", "⚙️ הגדרות"]
)

st.sidebar.markdown("---")
st.sidebar.info("📌 מערכת ניהול השקעות עם סוכנים AI\n\n✅ Real-time data\n✅ Smart agents\n✅ Risk management")

# ==================== MAIN ====================
st.title("📊 Investment Hub Elite 2026")
st.markdown("מערכת ניהול השקעות עם סוכנים אוטונומיים")

# Load data
try:
    @st.cache_data(ttl=300)
    def load_data():
        return fetch_master_data()
    
    market_data = load_data()
    
    if market_data is None or market_data.empty:
        st.error("❌ No data available")
        st.stop()
except Exception as e:
    st.error(f"❌ Error: {e}")
    st.stop()

# ==================== PAGES ====================
if page == "📊 דשבורד ראשי":
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📈 סה״כ מניות", len(market_data))
    with col2:
        high = len(market_data[market_data['Score'] >= 4])
        st.metric("💎 איכותיות", high)
    with col3:
        st.metric("💰 ממוצע מחיר", f"${market_data['Price'].mean():.2f}")
    with col4:
        oversold = len(market_data[market_data['RSI'] < 30])
        st.metric("🟢 Oversold", oversold)
    
    st.divider()
    cols_to_show = ['Symbol', 'Price', 'RSI', 'Score', 'DivYield']
    cols_to_show = [c for c in cols_to_show if c in market_data.columns]
    st.dataframe(market_data[cols_to_show].head(20), use_container_width=True, hide_index=True)

elif page == "🤖 סוכנים":
    st.markdown("### 🤖 Autonomous Agents")
    if st.button("🚀 Run Agents"):
        with st.spinner("⏳ Running..."):
            try:
                scheduler = UltraAdvancedScheduler(market_data)
                st.success("✅ Agents executed")
            except Exception as e:
                st.error(f"❌ Error: {e}")

elif page == "💰 תיקייה":
    st.markdown("### 💰 Portfolio Management")
    buy_candidates = market_data[market_data['Score'] >= 4].head(10)
    if not buy_candidates.empty:
        cols = ['Symbol', 'Price', 'Score', 'RSI']
        cols = [c for c in cols if c in market_data.columns]
        st.dataframe(buy_candidates[cols], use_container_width=True, hide_index=True)

elif page == "📈 ניתוחים":
    st.markdown("### 📈 Analytics")
    try:
        rsi_avg = market_data['RSI'].mean()
        st.metric("RSI Average", f"{rsi_avg:.1f}")
        st.bar_chart(market_data['RSI'].dropna().value_counts().sort_index())
    except Exception as e:
        st.warning(f"⚠️ {e}")

else:  # Settings
    st.markdown("### ⚙️ Settings")
    st.info("✅ API keys loaded from environment")
    if st.button("🗑️ Clear Cache"):
        st.cache_data.clear()
        st.success("✅ Cache cleared")

st.divider()
st.markdown(f"<small>Last update: {datetime.now().strftime('%H:%M:%S')}</small>", unsafe_allow_html=True)

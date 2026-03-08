# simulator.py - FIXED - With all required functions
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from storage import load, save

def render_value_agent(df_all):
    """Value Agent - Long-term investing based on fundamentals"""
    st.markdown("### 💎 Value Agent")
    
    if df_all.empty:
        st.warning("No data available for Value Agent")
        return
    
    try:
        # Filter: Good fundamentals
        value_filter = df_all[
            (df_all.get("LongScore", 0) >= 7) &
            (df_all.get("PayoutRatio", 0) < 60) &
            (df_all.get("CashVsDebt", "") == "OK")
        ]
        
        if not value_filter.empty:
            st.success(f"Found {len(value_filter)} value stocks")
            st.dataframe(
                value_filter[["Symbol", "Price", "LongScore", "DivYield", "ROE", "Action"]],
                hide_index=True
            )
        else:
            st.info("No value stocks found matching criteria")
    except Exception as e:
        st.error(f"Error in Value Agent: {str(e)}")

def render_day_trade_agent(df_all):
    """Day Trade Agent - Short-term technical trading"""
    st.markdown("### ⚡ Day Trade Agent")
    
    if df_all.empty:
        st.warning("No data available for Day Trade Agent")
        return
    
    try:
        # Filter: Technical indicators
        day_filter = df_all[
            (df_all.get("RSI", 50) < 30) |
            (df_all.get("ShortScore", 0) >= 3)
        ]
        
        if not day_filter.empty:
            st.success(f"Found {len(day_filter)} trading opportunities")
            st.dataframe(
                day_filter[["Symbol", "Price", "RSI", "ShortScore", "Change", "Action"]],
                hide_index=True
            )
        else:
            st.info("No trading opportunities found")
    except Exception as e:
        st.error(f"Error in Day Trade Agent: {str(e)}")

def run_simulator():
    """Stock trading simulator"""
    st.markdown("## Trading Simulator")
    
    col1, col2 = st.columns(2)
    
    with col1:
        initial_capital = st.number_input("Initial Capital ($)", value=100000, min_value=1000)
    
    with col2:
        mode = st.selectbox("Mode", ["Buy & Hold", "Active Trading", "Swing Trading"])
    
    if st.button("Start Simulation"):
        st.info("Starting simulation...")
        st.success(f"Portfolio started with ${initial_capital:,}")
        st.metric("Mode", mode)

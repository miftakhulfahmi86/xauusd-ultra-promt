import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime
import pytz

# === SETUP DASHBOARD ===
st.set_page_config(page_title="XAU/USD Ultra Prompt L4", layout="wide")
st.title("🟡 XAU/USD Ultra Prompt Level 4")
st.caption("Multi-strategi: Scalper • Intraday • Swing | Real-time | Intermarket Analysis")

# === TIMEZONE LOCAL DETECTION ===
local_time = datetime.now().astimezone()
hour = local_time.hour
st.sidebar.write(f"🕒 Local Time: {local_time.strftime('%A, %H:%M %Z')}")

active_session = 8 <= hour <= 17
if active_session:
    st.sidebar.success("✅ Active Session: Signals enabled")
else:
    st.sidebar.warning("⚠️ Outside Active Hours")

# === USER CONFIG ===
tf_option = st.sidebar.selectbox("Pilih Timeframe", ["15m", "1h", "4h", "1d"])
tf_mapping = {"15m": "15m", "1h": "60m", "4h": "240m", "1d": "1d"}
interval = tf_mapping[tf_option]

# === LOAD DATA ===
symbol = "XAUUSD=X"
period = "60d" if tf_option != "15m" else "7d"
data = yf.download(symbol, period=period, interval=interval)
data.dropna(inplace=True)

# === INDICATORS ===
data['EMA20'] = data['Close'].ewm(span=20).mean()
data['EMA50'] = data['Close'].ewm(span=50).mean()
data['ATR'] = (data['High'] - data['Low']).rolling(14).mean()

# === ORDER FLOW (BOS/CHOCH) ===
data['BOS/CHOCH'] = np.where(
    (data['Close'] > data['EMA20']) & (data['EMA20'] > data['EMA50']),
    "BOS",
    np.where((data['Close'] < data['EMA20']) & (data['EMA20'] < data['EMA50']), "CHOCH", "Ranging")
)

# === SIGNAL LOGIC ===
last = data.iloc[-1]
signal = "WAIT"
if active_session:
    if last['Close'] > last['EMA20'] > last['EMA50']:
        signal = "BUY"
    elif last['Close'] < last['EMA20'] < last['EMA50']:
        signal = "SELL"

# === ATR-BASED SL/TP ===
sl = round(last['ATR'] * 1.5, 2)
tp = round(last['ATR'] * 2.5, 2)

# === INTERMARKET ===
dxy = yf.download("DX-Y.NYB", period=period, interval=interval)
oil = yf.download("CL=F", period=period, interval=interval)
bond = yf.download("^TNX", period=period, interval=interval)

# === DISPLAY PANEL ===
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("📈 Signal", signal)
    st.write(f"Structure: {last['BOS/CHOCH']}")
with col2:
    st.metric("🎯 Stop Loss", sl)
with col3:
    st.metric("🎯 Take Profit", tp)

st.subheader("📊 Price Chart + EMA")
st.line_chart(data[['Close', 'EMA20', 'EMA50']])

# === INTERMARKET FLOW MATRIX ===
st.subheader("🌐 Intermarket Flow Matrix")
st.write("**DXY (USD Index):**", dxy['Close'].iloc[-1])
st.write("**Crude Oil (CL=F):**", oil['Close'].iloc[-1])
st.write("**US10Y Yield (^TNX):**", bond['Close'].iloc[-1])

# === SIGNAL LOG ===
st.subheader("🗂️ Riwayat Sinyal (Terakhir 10)")
signal_log = data[['Close', 'EMA20', 'EMA50', 'BOS/CHOCH']].copy()
signal_log['Signal'] = np.where(
    (signal_log['Close'] > signal_log['EMA20']) & (signal_log['EMA20'] > signal_log['EMA50']), 'BUY',
    np.where((signal_log['Close'] < signal_log['EMA20']) & (signal_log['EMA20'] < signal_log['EMA50']), 'SELL', 'WAIT')
)
st.dataframe(signal_log.tail(10))

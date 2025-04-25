import streamlit as st
import requests
import pandas as pd
import numpy as np
from datetime import datetime
import time

# === Title === #
st.title("🚀 Crypto Momentum Screener (Test Version - Bitcoin Only)")

# === Timestamp === #
st.write(f"🕓 Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# === Fetch Bitcoin Prices === #
@st.cache_data
def fetch_bitcoin_prices():
    url = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart?vs_currency=usd&days=30&interval=daily"
    response = requests.get(url)
    if response.status_code != 200:
        st.error("❌ Failed to fetch Bitcoin data from CoinGecko API.")
        return None
    data = response.json()
    prices = [price[1] for price in data['prices']]
    return prices

# === Calculate RSI === #
def calculate_rsi(prices, period=14):
    deltas = np.diff(prices)
    seed = deltas[:period]
    up = seed[seed >= 0].sum() / period
    down = -seed[seed < 0].sum() / period
    rs = up / down if down != 0 else 0
    rsi = np.zeros_like(prices)
    rsi[:period] = 100. - 100. / (1. + rs)

    for i in range(period, len(prices)):
        delta = deltas[i - 1]
        upval = max(delta, 0)
        downval = -min(delta, 0)
        up = (up * (period - 1) + upval) / period
        down = (down * (period - 1) + downval) / period
        rs = up / down if down != 0 else 0
        rsi[i] = 100. - 100. / (1. + rs)

    return rsi

# === Main Process === #
prices = fetch_bitcoin_prices()

if prices and len(prices) >= 30:
    prices = np.array(prices)
    
    st.success("✅ Successfully fetched Bitcoin data!")
    
    period_choice = st.selectbox(
        "Select Percentage Change Period:",
        ("7 Days", "14 Days", "30 Days")
    )
    
    period_map = {"7 Days": 7, "14 Days": 14, "30 Days": 30}
    selected_period = period_map[period_choice]
    
    pct_change = (prices[-1] - prices[-(selected_period + 1)]) / prices[-(selected_period + 1)] * 100
    
    rsi = calculate_rsi(prices)
    rsi_current = rsi[-1]
    rsi_ma14 = pd.Series(rsi).rolling(window=14).mean().iloc[-1]
    trend_up = rsi_current > rsi_ma14
    
    result = {
        "Coin": "Bitcoin",
        "Percent Change": pct_change,
        "RSI": rsi_current,
        "RSI_MA14": rsi_ma14,
        "Trend Up (RSI > MA14)": trend_up
    }
    
    df = pd.DataFrame([result])

    # Color coding function
    def color_pct(val):
        color = 'green' if val > 0 else 'red'
        return f'color: {color}'
    
    st.subheader("📈 Bitcoin Momentum Result")
    st.dataframe(df.style.applymap(color_pct, subset=['Percent Change']))

    # Download CSV
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download Data as CSV",
        data=csv,
        file_name='bitcoin_momentum_test.csv',
        mime='text/csv',
    )
else:
    st.error("❌ Could not load Bitcoin prices. Try again later.")


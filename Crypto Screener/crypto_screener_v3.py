import streamlit as st
import requests
import pandas as pd
import numpy as np
import time
from datetime import datetime

# === Title === #
st.title("🚀 Crypto Momentum Screener (Top 50 by Market Cap)")

# === Timestamp === #
st.write(f"🕓 Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# === Functions === #

# Get Top 50 coins by market cap (Safe version)
def get_top_50_coins():
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        'vs_currency': 'usd',
        'order': 'market_cap_desc',
        'per_page': 50,
        'page': 1,
        'sparkline': False
    }
    response = requests.get(url)

    if response.status_code != 200:
        st.error("❌ Failed to fetch top coins from CoinGecko API.")
        return []

    data = response.json()
    if not isinstance(data, list):
        st.error("❌ Invalid data received from CoinGecko API.")
        return []

    coin_ids = [coin['id'] for coin in data]
    return coin_ids

# Fetch historical prices for each coin
def fetch_prices(coin_id):
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart?vs_currency=usd&days=30&interval=daily"
    response = requests.get(url)
    if response.status_code != 200:
        return None
    data = response.json()
    prices = [price[1] for price in data['prices']]
    if len(prices) < 30:
        return None
    return prices

# Calculate RSI
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

# Load all data
@st.cache_data
def load_data():
    top_coins = get_top_50_coins()
    price_data = {}
    failed_coins = []

    for coin in top_coins:
        success = False
        for attempt in range(3):
            prices = fetch_prices(coin)
            if prices:
                price_data[coin] = prices
                success = True
                break
            time.sleep(1.5)
        if not success:
            failed_coins.append(coin)

    return price_data, failed_coins

# === Load Data === #
price_data, failed_coins = load_data()

if failed_coins:
    st.warning(f"⚠️ Failed to load data for {len(failed_coins)} coins:")
    st.write(failed_coins)

# === Sidebar Selections === #
period_choice = st.selectbox(
    "Select Percentage Change Period to Analyze:",
    ("7 Days", "14 Days", "30 Days")
)

period_map = {
    "7 Days": 7,
    "14 Days": 14,
    "30 Days": 30
}
selected_period = period_map[period_choice]

show_only_uptrend = st.checkbox("✅ Show Only Coins in Uptrend (RSI > 14-day RSI MA)")

# === Calculations === #
results = []

for coin, prices in price_data.items():
    prices = np.array(prices)

    # Calculate percent changes
    pct_change = (prices[-1] - prices[-(selected_period + 1)]) / prices[-(selected_period + 1)] * 100

    # Calculate RSI and RSI 14-day moving average
    rsi = calculate_rsi(prices)
    rsi_current = rsi[-1]
    rsi_ma14 = pd.Series(rsi).rolling(window=14).mean().iloc[-1]
    trend_up = rsi_current > rsi_ma14

    results.append({
        'coin': coin,
        'pct_change': pct_change,
        'rsi': rsi_current,
        'rsi_ma14': rsi_ma14,
        'trend_up': trend_up
    })

df = pd.DataFrame(results)

if not df.empty:
    # Calculate Z-score
    df['z_score'] = (df['pct_change'] - df['pct_change'].mean()) / df['pct_change'].std()

    # Apply filter if selected
    df_display = df.copy()
    if show_only_uptrend:
        df_display = df_display[df_display['trend_up']]

    # Sort by Z-score descending
    df_display = df_display.sort_values(by='z_score', ascending=False)

    # === Color Coding Function === #
    def color_z(val):
        color = 'green' if val > 0 else 'red'
        return f'color: {color}'

    # === Display Results === #
    st.subheader(f"📈 Coins Ranked by Z-Score of {period_choice} % Change")
    st.dataframe(df_display.style.applymap(color_z, subset=['z_score']))

    # === Download Button === #
    csv = df_display.to_csv(index=False).encode('utf-8')

    st.download_button(
        label="📥 Download Data as CSV",
        data=csv,
        file_name='crypto_momentum_screen.csv',
        mime='text/csv',
    )
else:
    st.error("❌ No valid data available. Please try again later.")


# Sort by Z-score descending
df_display = df_display.sort_values(by='z_score', ascending=False)

# === Color Coding Function === #
def color_z(val):
    color = 'green' if val > 0 else 'red'
    return f'color: {color}'

# === Display Results === #
st.subheader(f"📈 Coins Ranked by Z-Score of {period_choice} % Change")
st.dataframe(df_display.style.applymap(color_z, subset=['z_score']))

# === Download Button === #
csv = df_display.to_csv(index=False).encode('utf-8')

st.download_button(
    label="📥 Download Data as CSV",
    data=csv,
    file_name='crypto_momentum_screen.csv',
    mime='text/csv',
)

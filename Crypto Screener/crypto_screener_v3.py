# crypto_screen.py
import streamlit as st
import pandas as pd
import requests
from ta.momentum import RSIIndicator
from datetime import datetime, timedelta
import numpy as np

st.set_page_config(page_title="Top Crypto Screener", layout="wide")
st.title("📊 Top 5 Cryptos by Z-Scored % Change (14D) w/ RSI Filter")

# === Settings ===
NUM_COINS = 20
Z_PERIOD = 14
RSI_PERIOD = 14

# === Fetch top 20 crypto coins by market cap ===
@st.cache_data(ttl=3600)
def get_top_20():
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        'vs_currency': 'usd',
        'order': 'market_cap_desc',
        'per_page': NUM_COINS,
        'page': 1,
        'sparkline': False
    }
    response = requests.get(url, params=params)
    data = response.json()
    return [coin['id'] for coin in data]

# === Fetch historical prices and compute metrics ===
@st.cache_data(ttl=3600)
def get_coin_data(coin_id):
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
    params = {
        'vs_currency': 'usd',
        'days': Z_PERIOD + 30,
        'interval': 'daily'
    }
    response = requests.get(url, params=params)
    data = response.json()

    if 'prices' not in data:
        return None

    df = pd.DataFrame(data['prices'], columns=['timestamp', 'price'])
    df['date'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('date', inplace=True)
    df = df[['price']]

    if len(df) < RSI_PERIOD + Z_PERIOD:
        return None

    df['pct_change_14d'] = df['price'].pct_change(Z_PERIOD) * 100
    df['rsi'] = RSIIndicator(df['price'], window=RSI_PERIOD).rsi()
    df['rsi_ma'] = df['rsi'].rolling(RSI_PERIOD).mean()

    latest = df.dropna().iloc[-1]
    return {
        'coin': coin_id,
        '14d_pct_change': latest['pct_change_14d'],
        'zscore_placeholder': 0,
        'rsi': latest['rsi'],
        'rsi_ma': latest['rsi_ma']
    }

# === Run Screener ===
st.write("⏳ Loading data...")
top_coins = get_top_20()

results = []
for coin_id in top_coins:
    metrics = get_coin_data(coin_id)
    if metrics:
        results.append(metrics)

df = pd.DataFrame(results)

# === Filter RSI > RSI MA ===
df = df[df['rsi'] > df['rsi_ma']]

# === Z-score on 14-day % change ===
df['zscore'] = (df['14d_pct_change'] - df['14d_pct_change'].mean()) / df['14d_pct_change'].std()

# === Top 5 by Z-score ===
top5 = df.sort_values(by='zscore', ascending=False).head(5)

st.subheader("🚀 Top 5 Coins (RSI > RSI MA)")
st.dataframe(top5[['coin', '14d_pct_change', 'zscore', 'rsi', 'rsi_ma']].round(2), use_container_width=True)

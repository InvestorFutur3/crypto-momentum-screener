import streamlit as st
import requests
import pandas as pd
import numpy as np
import time

# === 1. Streamlit App Title === #
st.title("🚀 Crypto Momentum Screener (Full List)")

# === 2. List of 50 popular tokens === #
COINS = [
    'bitcoin', 'ethereum', 'binancecoin', 'solana', 'ripple', 'cardano', 'dogecoin', 'polkadot',
    'tron', 'avalanche', 'chainlink', 'uniswap', 'litecoin', 'matic-network', 'internet-computer',
    'stellar', 'filecoin', 'vechain', 'the-graph', 'aptos', 'algorand', 'render-token', 'aave',
    'arbitrum', 'theta-token', 'aave', 'tezos', 'stellar', 'neo', 'optimism', 'eos', 'curve-dao-token',
    'sui', 'sandbox', 'decentraland', 'chiliz', 'flow', 'quant-network', 'iota', 'mina-protocol',
    'loopring', '1inch', 'ocean-protocol', 'kava', 'enjincoin', 'ondo', 'balancer', 'official-trump',
    'zilliqa', 'waves'
]

# === 3. Fetch historical prices === #
def fetch_prices(coin_id):
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart?vs_currency=usd&days=60"
    response = requests.get(url)
    if response.status_code != 200:
        return None
    data = response.json()
    prices = [price[1] for price in data['prices']]
    if len(prices) < 60:
        return None
    return prices

# === 4. Fetch all data === #
@st.cache_data
def load_data():
    price_data = {}
    for coin in COINS:
        prices = fetch_prices(coin)
        if prices:
            price_data[coin] = prices
        time.sleep(1.2)  # Respect API rate limit
    return price_data

price_data = load_data()

# === 5. Calculate percent changes and z-scores === #
results = []
for coin, prices in price_data.items():
    prices = np.array(prices)
    pct_7 = (prices[-1] - prices[-8]) / prices[-8] * 100
    pct_14 = (prices[-1] - prices[-15]) / prices[-15] * 100
    pct_30 = (prices[-1] - prices[-31]) / prices[-31] * 100

    ma10 = np.mean(prices[-10:])
    ma30 = np.mean(prices[-30:])
    trend_up = ma10 > ma30

    results.append({
        'coin': coin,
        'pct_7': pct_7,
        'pct_14': pct_14,
        'pct_30': pct_30,
        'ma10': ma10,
        'ma30': ma30,
        'trend_up': trend_up
    })

df = pd.DataFrame(results)

# Calculate Z-scores
for col in ['pct_7', 'pct_14', 'pct_30']:
    df[f'z_{col}'] = (df[col] - df[col].mean()) / df[col].std()

# Combine Z-scores into one average total score
df['z_total'] = df[['z_pct_7', 'z_pct_14', 'z_pct_30']].mean(axis=1)

# === 6. Display All 50 Coins === #
st.subheader("📈 Full Coin List with Z-scores")

# Choose sort options
sort_column = st.selectbox("Sort by:", options=['z_total', 'z_pct_7', 'z_pct_14', 'z_pct_30'])
ascending = st.checkbox("Sort Ascending?", value=False)

# Filter to only uptrend coins (optional)
show_only_uptrend = st.checkbox("Show only coins in Uptrend (MA10 > MA30)?", value=False)

if show_only_uptrend:
    df = df[df['trend_up']]

# Sort DataFrame
df_sorted = df.sort_values(by=sort_column, ascending=ascending)

# Show nicely in app
st.dataframe(df_sorted[['coin', 'pct_7', 'pct_14', 'pct_30', 'z_pct_7', 'z_pct_14', 'z_pct_30', 'z_total', 'trend_up']])

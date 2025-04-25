import streamlit as st
import requests
import pandas as pd
import numpy as np
import time

# === 1. Streamlit App Title === #
st.title("🚀 Crypto Momentum Screener (All 50 Coins with Z-scores)")

# === 2. List of 50 popular tokens === #
COINS = [
    'bitcoin', 'ethereum', 'binancecoin', 'solana', 'ripple', 'cardano', 'dogecoin', 'polkadot',
    'tron', 'avalanche-2', 'chainlink', 'uniswap', 'litecoin', 'matic-network', 'internet-computer',
    'stellar', 'filecoin', 'vechain', 'the-graph', 'aptos', 'algorand', 'render-token', 'kaspa',
    'arbitrum', 'theta-token', 'aave', 'tezos', 'elrond-erd-2', 'neo', 'optimism', 'eos', 'curve-dao-token',
    'gala', 'sandbox', 'decentraland', 'chiliz', 'flow', 'quant-network', 'iota', 'mina-protocol',
    'loopring', '1inch', 'ocean-protocol', 'kava', 'enjincoin', 'bittorrent', 'balancer', 'convex-finance',
    'zilliqa', 'waves'
]

# === 3. Function to Fetch Historical Prices === #
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

# === 4. Fetch All Data with Retry on Failure === #
@st.cache_data
def load_data():
    price_data = {}
    failed_coins = []

    for coin in COINS:
        success = False
        for attempt in range(3):  # Try up to 3 times
            prices = fetch_prices(coin)
            if prices:
                price_data[coin] = prices
                success = True
                break
            time.sleep(1.5)  # wait before retry
        if not success:
            failed_coins.append(coin)

    return price_data, failed_coins

price_data, failed_coins = load_data()

if failed_coins:
    st.warning(f"⚠️ Failed to load data for {len(failed_coins)} coins:")
    st.write(failed_coins)

# === 5. Calculate % Changes and Z-Scores === #
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

# Combine Z-scores into one "total" score
df['z_total'] = df[['z_pct_7', 'z_pct_14', 'z_pct_30']].mean(axis=1)

# === 6. Streamlit Display === #
st.subheader("📈 Full Coin List with Z-Scores")

# Sort Options
sort_column = st.selectbox("Sort coins by:", options=['z_total', 'z_pct_7', 'z_pct_14', 'z_pct_30'])
ascending = st.checkbox("Sort Ascending?", value=False)

# Filter Option: Only Uptrend Coins
show_only_uptrend = st.checkbox("Show only coins in Uptrend (MA10 > MA30)?", value=False)

# Apply filter
df_display = df.copy()
if show_only_uptrend:
    df_display = df_display[df_display['trend_up']]

# Apply sort
df_display = df_display.sort_values(by=sort_column, ascending=ascending)

# Show full table
st.dataframe(df_display[['coin', 'pct_7', 'pct_14', 'pct_30', 'z_pct_7', 'z_pct_14', 'z_pct_30', 'z_total', 'trend_up']])


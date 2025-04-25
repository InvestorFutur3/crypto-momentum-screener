def get_top_5_coins():
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        'vs_currency': 'usd',
        'order': 'market_cap_desc',
        'per_page': 5,
        'page': 1,
        'sparkline': False
    }
    tries = 0
    while tries < 3:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                coin_ids = [coin['id'] for coin in data]
                return coin_ids
        tries += 1
        time.sleep(2)  # wait 2 seconds before retry
    st.error("❌ Failed to fetch top coins from CoinGecko API after 3 tries.")
    return []



import requests
import pandas as pd
from datetime import datetime

# Replace with your CryptoCompare API key
api_key = 'd9fbcc2400d429a56d763827edfce893853890d5c83cf86c0cf4601872aefb6e'

def fetch_daily_data(symbol):
    url = f'https://min-api.cryptocompare.com/data/v2/histoday?fsym={symbol}&tsym=USD&allData=true&api_key={api_key}'
    response = requests.get(url)
    data = response.json()['Data']['Data']
    df = pd.DataFrame(data)
    df['time'] = [datetime.fromtimestamp(d) for d in df.time]
    return df

df = fetch_daily_data('BTC')

# Filter only necessary columns
df = df[['time', 'open', 'high', 'low', 'close']]

# Rename columns
df.columns = ['Date', 'Open', 'High', 'Low', 'Close']

# Format 'Date' column to 'dd/mm/yyyy'
df['Date'] = df['Date'].dt.strftime('%d/%m/%Y')

# Save to CSV
df.to_csv('BTC_OHLC.csv', index=False)
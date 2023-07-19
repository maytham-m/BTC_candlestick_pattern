import pandas as pd
import requests
import json
import time
from datetime import datetime

def get_binance_bars(symbol, interval):
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}"
    
    # Initialize start_time (unix timestamp for Jan 1, 2010)
    start_time = 1262304000000
    full_df = pd.DataFrame()

    while True:
        url_temp = url + f'&startTime={start_time}'
        data = json.loads(requests.get(url_temp).text)
        df = pd.DataFrame(data)
        if len(df) == 0:
            break
        start_time = df[6][len(df)-1] + 1
        full_df = pd.concat([full_df, df])
        time.sleep(1)  # Control the request frequency to comply with rate limits
    
    full_df.columns = ['open_time', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_asset_volume', 'number_of_trades', 'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore']
    full_df.index = [datetime.fromtimestamp(x/1000.0) for x in full_df.close_time]
    
    return full_df

df = get_binance_bars('BTCUSDT', '1d')
df = df[['open', 'high', 'low', 'close']]

# Rename columns
df.columns = ['Open', 'High', 'Low', 'Close']

# Reset index and rename index column to 'Date'
df = df.reset_index()
df = df.rename(columns={'index':'Date'})

# Format 'Date' column to 'dd/mm/yyyy'
df['Date'] = df['Date'].dt.strftime('%d/%m/%Y')

# Save to CSV
df.to_csv('BTC_OHLC.csv', index=False)
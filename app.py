from flask import Flask, render_template, request
import pandas as pd
import plotly.graph_objs as go
import plotly.io as pio
import numpy as np
from fastdtw import fastdtw
from scipy.spatial.distance import euclidean

app = Flask(__name__)


def euclidean_dist(df1, df2, cols=['Open','High', 'Low', 'Close']):
    # return the euclidean distance between two dataframes, averaged over all columns
    return np.linalg.norm(df1[cols].values - df2[cols].values, axis=1).sum()/4


def normalize(df):
    return (df - df.min()) / (df.max() - df.min())



def compare_patterns(df, days, forecast_days=0):
    # only use numeric columns
    df = df[['Open', 'High', 'Low', 'Close']]
    current_pattern = normalize(df[-days:])
    similarities = []
    df_norm = normalize(df)

    # compare the current pattern with all patterns of the same length
    for i in range(len(df) - days):
        pattern = df[i:i+days]
        # if there's any NaN in the pattern, skip this pattern
        if pattern.isna().any().any():
            continue
        normalized_pattern = normalize(pattern)
        dist = euclidean_dist(current_pattern, normalized_pattern)
        #dist, _ = fastdtw(current_pattern, normalized_pattern, dist=euclidean)
        similarities.append((i, dist))

    similarities.sort(key=lambda x: x[1])

    # keep track of indices that are part of an already-selected pattern
    selected_indices = set(range(len(df) - days, len(df)))
    selected_patterns = []

    # select the top 5 patterns that are not overlapping with each other
    for i, dist in similarities:
        # check if this pattern overlaps with an already-selected pattern
        if any(j in selected_indices for j in range(i, i + days)):
            continue
        selected_indices.update(range(i, i + days))
        selected_patterns.append((i, dist))
        if len(selected_patterns) == 5:
            break

    # Find the average percentage change in price in the next forecast_days days for all patterns within 10% of the most similar pattern, and return this as the forecast price change in addition to the number of patterns within the 10% threshold
    avg_price_change = 0
    count = 0
    # iterate through the patterns in order of similarity (most similar first)
    for i, dist in similarities:
        # if the distance is more than 10% of the distance of the most similar pattern, stop
        if dist > 1.1*selected_patterns[0][1]:
            break
        # pattern represents the next forecast_days days
        # must normalize it before calculating the price change 
        pattern = df_norm[i+days:i+days+forecast_days]
        # price change in the next forecast_days days
        price_change = (pattern['Close'].iloc[-1] - pattern['Close'].iloc[0]) / pattern['Close'].iloc[0] * 100
        avg_price_change += price_change
        count += 1
    avg_price_change /= count

    return selected_patterns, avg_price_change, count



@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        days = int(request.form['days'])
        forecast_days = int(request.form['forecast_days'])

        df = pd.read_csv('BTC_OHLC.csv', parse_dates=['Date'], dayfirst=True)

        # replace '-' with NaN and drop these rows
        df[['Open', 'High', 'Low', 'Close']] = df[['Open', 'High', 'Low', 'Close']].replace('—', np.nan).astype(float)
        df = df.dropna(subset=['Open', 'High', 'Low', 'Close'])
        df = df.sort_values('Date')

        comparisons, avg_price_change, count = compare_patterns(df, days, forecast_days)
        plots = []

        # print the results
        print(f'Average price change: {avg_price_change:.2f}%')
        print(f'Number of patterns within 10% of the most similar pattern: {count}')
        
        # plot the input pattern
        input_pattern = df[-days:]

        # add forecast days to the input pattern to make it the same length as the other patterns
        input_pattern['Date'] = pd.to_datetime(df['Date'])  # make sure the Date column is datetime type

        last_date = input_pattern['Date'].iloc[-1]
        new_dates = pd.date_range(start=last_date + pd.Timedelta(days=1), periods=forecast_days)

        new_data = pd.DataFrame({
            'Date': new_dates,
            'Open': [np.nan]*forecast_days,
            'High': [np.nan]*forecast_days,
            'Low': [np.nan]*forecast_days,
            'Close': [np.nan]*forecast_days
        })
        # add the new data to the input pattern
        input_pattern = pd.concat([input_pattern, new_data])
        
        trace = go.Candlestick(x=input_pattern['Date'],
                               open=input_pattern['Open'],
                               high=input_pattern['High'],
                               low=input_pattern['Low'],
                               close=input_pattern['Close'])
        data = [trace]
        layout = go.Layout(title='Input Pattern')
        fig = go.Figure(data=data, layout=layout)
        div = pio.to_html(fig, full_html=False)
        plots.append(div)

        # plot the comparisons
        for i, dist in comparisons:
            pattern = df[i:i+days+forecast_days]
            trace = go.Candlestick(x=pattern['Date'],
                                   open=pattern['Open'],
                                   high=pattern['High'],
                                   low=pattern['Low'],
                                   close=pattern['Close'])
            data = [trace]


            layout = go.Layout(title=f'Pattern starting at {pattern["Date"].dt.strftime("%d/%m/%Y").values[0]}, avg euclidean distance: {dist:.2f}')
            fig = go.Figure(data=data, layout=layout)
            div = pio.to_html(fig, full_html=False)
            plots.append(div)
        
        print()

        return render_template('compare.html', plots=plots)

    return render_template('index.html')


if __name__ == "__main__":
    app.run(debug=True)

# —

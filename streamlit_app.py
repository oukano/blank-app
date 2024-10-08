import streamlit as st
import yfinance as yf
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
from alpha_vantage.timeseries import TimeSeries
import pytz

# Define available ticker symbols and their names
ticker_options = {
    "QQQ": "Nasdaq",
    "GLD": "XAU",
    "SPY": "S&P"
}

st.title("CTT - Expected Move Calculator")

# Create a dropdown for selecting the ticker symbol
selected_ticker = st.selectbox("Select Ticker Symbol", options=list(ticker_options.keys()), format_func=lambda x: ticker_options[x])

# Fetch the ticker data
ticker = yf.Ticker(selected_ticker)
# Set the U.S. timezone, e.g., New York (Eastern Time)
us_timezone = pytz.timezone('America/New_York')

# Get the current time in the U.S. timezone
us_time = datetime.now(us_timezone)

# Calculate yesterday's date in U.S. timezone
yesterday_date = us_time - timedelta(1)
yesterday_str = yesterday_date.strftime('%Y-%m-%d')
print(ticker.history(start=yesterday_str, end=yesterday_str))
# Get the current price of the selected ticker
current_price = ticker.history(period="2d")['Close'].iloc[-1]

# Fetch the available option expiration dates
option_dates = ticker.options

# If there are available option expiration dates
if option_dates:
    # Create a dropdown for selecting the expiration date
    expiration_date = st.selectbox("Select Expiration Date", options=option_dates)

    # Fetch the option data for the selected expiration date
    option_chain = ticker.option_chain(expiration_date)

    calls = option_chain.calls
    puts = option_chain.puts

    # Merge calls and puts on the strike price
    straddles = calls.merge(puts, on='strike', suffixes=('_call', '_put'))

    # Specify the target strike price (default to current price)
    target_strike = float(current_price)
    # st.write(f"ATM strike: {target_strike:.2f}")
    
    # Find the closest strike price to the target
    available_strikes = straddles['strike'].values
    closest_strike = available_strikes[(abs(available_strikes - target_strike)).argmin()]

    # Filter the straddles for the closest strike price
    closest_straddle = straddles[straddles['strike'] == closest_strike]

    # Display the call and put options for the closest strike price
    if not closest_straddle.empty:
         # Calculate the formula
        calculation = ((closest_straddle['lastPrice_call'].values[0] + closest_straddle['lastPrice_put'].values[0]) / target_strike) * 100
        # Format the calculation result to two decimal places
        formatted_calculation = f"{calculation:.2f}"
        
        # Display the calculation result
        st.write(f"expected move: {formatted_calculation} %")
        st.write(f"Upper band: -")
        st.write(f"lower band: -")
    else:
        st.write(f"No options found for strike price {target_strike} or closest strike price {closest_strike}.")

    
else:
    st.write("No available option expiration dates.")

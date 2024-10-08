import streamlit as st
import yfinance as yf
from datetime import datetime, timedelta
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
st.write(f"Selected Ticker: {selected_ticker}")

# Fetch the ticker data
ticker = yf.Ticker(selected_ticker)

# Get the current date and time in the U.S. timezone
us_timezone = pytz.timezone('America/New_York')
current_time = datetime.now(us_timezone)

# Check if today is a weekend
if current_time.weekday() >= 5:  # Saturday or Sunday
    # Get historical data for yesterday
    yesterday = current_time - timedelta(days=1)
    historical_data = ticker.history(start=yesterday.strftime('%Y-%m-%d'), end=yesterday.strftime('%Y-%m-%d'))

    if historical_data.empty:
        st.write("No historical data available for the selected ticker.")
    else:
        # Get yesterday's closing price
        yesterday_close = historical_data['Close'].iloc[-1]
        st.write(f"Market is closed. Yesterday's Close: {yesterday_close}")
else:
    # Check market hours (9:30 AM to 4 PM EST)
    market_open = datetime.now(us_timezone).replace(hour=9, minute=30, second=0, microsecond=0)
    market_close = datetime.now(us_timezone).replace(hour=16, minute=0, second=0, microsecond=0)

    if current_time < market_open or current_time > market_close:
        # Market is closed, get yesterday's closing price
        yesterday = current_time - timedelta(days=1)
        historical_data = ticker.history(start=yesterday.strftime('%Y-%m-%d'), end=yesterday.strftime('%Y-%m-%d'))

        if historical_data.empty:
            st.write("No historical data available for the selected ticker.")
        else:
            yesterday_close = historical_data['Close'].iloc[-1]
            st.write(f"Market is closed. Yesterday's Close: {yesterday_close}")
    else:
        # Market is open, get the current price
        current_data = ticker.history(period="1d")
        
        if current_data.empty:
            st.write("No historical data available for the selected ticker.")
        else:
            current_price = current_data['Close'].iloc[-1]
            st.write(f"Current Price: {current_price}")

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
    target_strike = float(current_price) if 'current_price' in locals() else yesterday_close

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
        st.write(f"Expected Move: {formatted_calculation} %")
        st.write(f"Upper band: -")
        st.write(f"Lower band: -")
    else:
        st.write(f"No options found for strike price {target_strike} or closest strike price {closest_strike}.")

else:
    st.write("No available option expiration dates.")

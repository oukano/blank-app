import streamlit as st
import yfinance as yf
import numpy as np
import plotly.graph_objects as go

# Define available ticker symbols and their names
ticker_options = {
    "QQQ": "Invesco QQQ Trust",
    "GLD": "SPDR Gold Shares"
}

st.title("CTT volatility calculator")

# Create a dropdown for selecting the ticker symbol
selected_ticker = st.selectbox("Select Ticker Symbol", options=list(ticker_options.keys()), format_func=lambda x: ticker_options[x])

# Fetch the ticker data
ticker = yf.Ticker(selected_ticker)

# Get the current price of the selected ticker
current_price = ticker.history(period="1d")['Close'].iloc[-1]

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
    st.write(f"ATM strike: {target_strike:.2f}")
    
    # Find the closest strike price to the target
    available_strikes = straddles['strike'].values
    closest_strike = available_strikes[(abs(available_strikes - target_strike)).argmin()]

    # Filter the straddles for the closest strike price
    closest_straddle = straddles[straddles['strike'] == closest_strike]

    # Display the call and put options for the closest strike price
    if not closest_straddle.empty:
        st.write(f"Options for closest strike price to {target_strike} (actual strike price {closest_strike}):")
        st.write(closest_straddle[['strike', 'lastPrice_call', 'lastPrice_put', 'bid_call', 'bid_put', 'ask_call', 'ask_put']])
         # Calculate the formula
        calculation = ((closest_straddle['lastPrice_call'].values[0] + closest_straddle['lastPrice_put'].values[0]) / target_strike) * 100
        # Format the calculation result to two decimal places
        formatted_calculation = f"{calculation:.2f}"
        
        # Display the calculation result
        st.write(f"implied Vilatility: {formatted_calculation} %")
    else:
        st.write(f"No options found for strike price {target_strike} or closest strike price {closest_strike}.")

    # Fetch NASDAQ100 data
    nasdaq_ticker = yf.Ticker("QQQ")  # NASDAQ100 ETF
    nasdaq_data = nasdaq_ticker.history(period="1mo")  # 1 month of data

    # Calculate upper and lower bands
    nasdaq_data['Upper Band'] = nasdaq_data['Close'] + (implied_volatility / 100 * nasdaq_data['Close'])
    nasdaq_data['Lower Band'] = nasdaq_data['Close'] - (implied_volatility / 100 * nasdaq_data['Close'])

    # Plot the data
    fig = go.Figure()

    # Add NASDAQ price line
    fig.add_trace(go.Scatter(x=nasdaq_data.index, y=nasdaq_data['Close'], mode='lines', name='NASDAQ Price'))

    # Add Upper Band line
    fig.add_trace(go.Scatter(x=nasdaq_data.index, y=nasdaq_data['Upper Band'], mode='lines', name='Upper Band', line=dict(dash='dash')))

    # Add Lower Band line
    fig.add_trace(go.Scatter(x=nasdaq_data.index, y=nasdaq_data['Lower Band'], mode='lines', name='Lower Band', line=dict(dash='dash')))

    # Update layout
    fig.update_layout(title=f"NASDAQ100 Price and Bands",
                        xaxis_title='Date',
                        yaxis_title='Price',
                        template='plotly_dark')

    # Display the chart
    st.plotly_chart(fig)
else:
    st.write("No available option expiration dates.")

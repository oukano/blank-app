import streamlit as st
import yfinance as yf
from datetime import datetime, timedelta
import pytz
from arch import arch_model
import pandas as pd
import matplotlib.pyplot as plt

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

# Define a default value for yesterday_close
yesterday_close = None


current_data = ticker.history(period="1d")

# Extract the last closing price
yesterday_close = current_data['Close'].iloc[-1]

# Fetch the available option expiration dates
try:
    option_dates = ticker.options
except Exception as e:
    st.write(f"An error occurred while fetching option data: {e}")
    option_dates = []

# If there are available option expiration dates
if option_dates:
    # Create a dropdown for selecting the expiration date
    expiration_date = st.selectbox("Select Expiration Date", options=option_dates)

    # Fetch the option data for the selected expiration date
    try:
        option_chain = ticker.option_chain(expiration_date)

        calls = option_chain.calls
        puts = option_chain.puts

        # Merge calls and puts on the strike price
        straddles = calls.merge(puts, on='strike', suffixes=('_call', '_put'))
        # print(straddles)
        print('yesterday_close')
        print(yesterday_close)
        # Specify the target strike price (default to current price)
        if yesterday_close is not None:
            print('inside yesterday close')
            target_strike = float(current_price) if 'current_price' in locals() else yesterday_close

            # Find the closest strike price to the target
            available_strikes = straddles['strike'].values
            closest_strike = available_strikes[(abs(available_strikes - target_strike)).argmin()]

            # Filter the straddles for the closest strike price
            closest_straddle = straddles[straddles['strike'] == closest_strike]

            # Display the call and put options for the closest strike price
            if not closest_straddle.empty:
                print('inside yesterday close , straddle not empty')

                # Calculate the expected move formula
                expected_move_percentage = ((closest_straddle['lastPrice_call'].values[0] + closest_straddle['lastPrice_put'].values[0]) / target_strike) * 100
                # Format the calculation result to two decimal places
                formatted_expected_move = f"{expected_move_percentage:.2f}"

                # Calculate the upper and lower bands
                upper_band = target_strike * (1 + expected_move_percentage / 100)
                lower_band = target_strike * (1 - expected_move_percentage / 100)

                # Format the bands to two decimal places
                formatted_upper_band = f"{upper_band:.2f}"
                formatted_lower_band = f"{lower_band:.2f}"

                # Display the calculation result
                st.write(f"Expected Move: {formatted_expected_move} %")
                print(f"Expected Move: {formatted_expected_move} %")
                st.write(f"Upper band: {formatted_upper_band}")
                st.write(f"Lower band: {formatted_lower_band}")
            else:
                print('inside yesterday close , straddle empty')
                st.write(f"No options found for strike price {target_strike} or closest strike price {closest_strike}.")
                print(f"No options found for strike price {target_strike} or closest strike price {closest_strike}.")
        else:
            st.write("No closing price available for calculation.")
            print("No closing price available for calculation.")
    except Exception as e:
        st.write(f"An error occurred while fetching option chain data: {e}")
else:
    st.write("No available option expiration dates.")



st.title("📈 GARCH(1,1) 1-Day Volatility Forecast")
st.write("Estimate next-day volatility using the GARCH(1,1) model for S&P 500 or NASDAQ 100.")

# User input
symbol_map = {
    "S&P 500 (SPX)": "^GSPC",
    "NASDAQ 100 (NDX)": "^NDX"
}
index_name = st.selectbox("Select Index", list(symbol_map.keys()))
symbol = symbol_map[index_name]

start_date = st.date_input("Start Date", value=pd.to_datetime("2022-01-01"))

if st.button("Run Forecast and Compare"):
    with st.spinner("Fetching market data and computing..."):
        data = yf.download(symbol, start=start_date)
        iv_data = yf.download(iv_symbol, start=start_date)

        # GARCH Forecast
        returns = 100 * data['Adj Close'].pct_change().dropna()
        model = arch_model(returns, vol='GARCH', p=1, q=1)
        res = model.fit(disp='off')
        forecast = res.forecast(horizon=1)
        garch_vol = forecast.variance.iloc[-1, 0] ** 0.5

        # IV value
        iv_today = iv_data['Close'].dropna().iloc[-1]

        # Display outputs
        st.subheader("🔍 Volatility Summary")
        st.write(f"**GARCH Forecasted 1-Day Volatility** for {index_name}: `{garch_vol:.2f}%`")
        st.write(f"**Implied Volatility (IV)** from {iv_symbol}: `{iv_today:.2f}%`")

        # Volatility premium
        vol_premium = iv_today - garch_vol
        st.write(f"**Volatility Premium (IV - GARCH)**: `{vol_premium:.2f}`")

        # Thresholds (adjustable based on history or your preference)
        iv_threshold = 18 if symbol == "^GSPC" else 22  # typical VIX/VXN average levels
        garch_threshold = returns.std() * 1.5           # rough high-volatility threshold

        # Strategy Bias Logic (4-case matrix)
        st.subheader("🧭 Volatility Regime & CFD Strategy Bias")

        if garch_vol > garch_threshold and iv_today > iv_threshold:
            st.warning("**High GARCH + High IV** 🔥\n\nMarket is volatile and pricing in further risk. Spike potential. Consider fading extremes or reducing exposure.")
        elif garch_vol > garch_threshold and iv_today <= iv_threshold:
            st.warning("**High GARCH + Low IV** ⚠️\n\nRealized risk is high, but market is ignoring it. Beware of underpriced volatility. Consider trading conservatively.")
        elif garch_vol <= garch_threshold and iv_today > iv_threshold:
            st.success("**Low GARCH + High IV** 💡\n\nOptions market expects a move, but realized vol is low. Potential breakout — consider momentum setups.")
        else:
            st.info("**Low GARCH + Low IV** 💤\n\nQuiet regime. Market is calm. Consider mean-reversion or range trading.")

        # Plot GARCH volatility
        fig, ax = plt.subplots()
        res.conditional_volatility.plot(ax=ax, title=f"GARCH Conditional Volatility - {index_name}")
        ax.set_ylabel("Volatility (%)")
        st.pyplot(fig)
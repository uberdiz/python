import numpy as np
import alpaca_trade_api as tradeapi
from tensorflow.keras.models import load_model
import time
import os
import pandas as pd

# Alpaca API credentials
API_KEY = "PK3VQTTVXLHNANOILTYI"
API_SECRET = "nN5QdNFBOeDsaLjAhGNdhcYWgQAahUmUKfO5wfSJ"
BASE_URL = "https://paper-api.alpaca.markets"  # Use paper trading URL for testing

# Alpaca API connection
api = tradeapi.REST(API_KEY, API_SECRET, BASE_URL, api_version='v2')

# List of tickers to trade
tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NVDA", "NFLX", "ADBE", "ORCL",
           "PYPL", "INTC", "AMD", "CSCO", "CRM", "TXN", "QCOM", "IBM", "NOW", "SHOP",
           "UBER", "LYFT", "SQ", "PLTR", "SPOT", "DOCU", "ZM", "SNAP", "PINS",
           "DIS", "CMCSA", "T", "VZ", "NFLX", "TMUS", "KO", "PEP", "MCD", "SBUX",
           "WMT", "COST", "HD", "LOW", "TGT", "DG", "F", "GM", "NKE", "PG"]

# Risk management parameters
RISK_PER_TRADE = 0.01  # Risk 1% of account balance
STOP_LOSS_PERCENT = 0.01  # 1% stop loss
TAKE_PROFIT_PERCENT = 0.02  # 2% take profit
MAX_POSITION_SIZE = 100  # Maximum number of shares to hold per stock

# Function to load model and scaler for a ticker
def load_model_and_scaler(ticker):
    model_path = f"models/{ticker}_model.keras"
    scaler_path = f"models/{ticker}_scaler.npy"
    if os.path.exists(model_path) and os.path.exists(scaler_path):
        model = load_model(model_path)
        scaler = np.load(scaler_path, allow_pickle=True).item()
        return model, scaler
    else:
        return None, None

# Function to calculate position size based on risk and available balance
def calculate_position_size(account_balance, current_price):
    position_size = account_balance * RISK_PER_TRADE / (current_price * STOP_LOSS_PERCENT)
    return min(max(1, int(position_size)), MAX_POSITION_SIZE)  # Ensure at least 1 share and max limit

# Function to fetch recent data from Alpaca API
def fetch_recent_data(ticker):
    try:
        bars = api.get_bars(ticker, "1Min", limit=100)  # Fetch more bars as a buffer
        if len(bars) < 60:
            raise ValueError("Insufficient data returned")
        data = pd.DataFrame({
            'close': [bar.c for bar in bars],
            'high': [bar.h for bar in bars],
            'low': [bar.l for bar in bars]
        })
        data['sma'] = data['close'].rolling(window=10).mean()
        data['ema'] = data['close'].ewm(span=10).mean()
        data = data.dropna()  # Drop rows with NaN values
        return data
    except Exception as e:
        print(f"Error fetching data for {ticker}: {e}")
        return None
# Function to check current portfolio positions
def check_positions():
    positions = api.list_positions()
    return {position.symbol: int(position.qty) for position in positions}
def fetch_recent_data_with_retries(ticker, retries=3):
    for attempt in range(retries):
        data = fetch_recent_data(ticker)
        if data is not None and len(data) >= 60:
            return data
        print(f"Retrying fetch for {ticker} ({attempt + 1}/{retries})...")
        time.sleep(5)
    return None
def is_market_open():
    clock = api.get_clock()
    return clock.is_open

# Optimized trading strategy
# Simplified daily trading function
def daily_trade():
    print("Starting daily trading...")
    try:
        # Fetch account balance and current positions
        account = api.get_account()
        account_balance = float(account.cash)
        current_positions = check_positions()

        # Ensure the market is open before starting
        if not is_market_open():
            print("Market is closed. Exiting...")
            return

        for ticker in tickers:
            try:
                # Load model and scaler
                model, scaler = load_model_and_scaler(ticker)
                if not model or not scaler:
                    print(f"No model or scaler for {ticker}, skipping.")
                    continue

                # Fetch recent data
                data = fetch_recent_data_with_retries(ticker)
                if data is None:
                    print(f"Insufficient data for {ticker}. Skipping...")
                    continue

                # Prepare features for prediction
                features = np.stack([data['close'].values[-60:], data['sma'].values[-60:], data['ema'].values[-60:]], axis=1)
                scaled_features = scaler.transform(features)
                latest_sequence = np.array([scaled_features])

                # Predict percentage change
                predicted_change = model.predict(latest_sequence)[0][0]

                # Determine position size and trade logic
                current_price = data['close'].iloc[-1]
                position_size = calculate_position_size(account_balance, current_price)

                if predicted_change > 0.01:  # Buy signal
                    if ticker not in current_positions:
                        print(f"Buy signal for {ticker}. Buying {position_size} shares.")
                        api.submit_order(
                            symbol=ticker,
                            qty=position_size,
                            side='buy',
                            type='market',
                            time_in_force='gtc'
                        )
                elif predicted_change < -0.01:  # Sell signal
                    if ticker in current_positions:
                        print(f"Sell signal for {ticker}. Selling {current_positions[ticker]} shares.")
                        api.submit_order(
                            symbol=ticker,
                            qty=current_positions[ticker],
                            side='sell',
                            type='market',
                            time_in_force='gtc'
                        )
                else:
                    print(f"No strong signal for {ticker}. Skipping trade.")

            except Exception as e:
                print(f"Error processing {ticker}: {e}")

    except Exception as e:
        print(f"Error in daily trading: {e}")
while True:
    daily_trade()
    time.sleep(60 * 60)  # Sleep for 1 hour before starting again

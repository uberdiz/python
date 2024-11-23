import numpy as np
import yfinance as yf
from tensorflow.keras.models import load_model
import os
import matplotlib.pyplot as plt
# List of tickers to test
tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NVDA", "NFLX", "ADBE", "ORCL",
           "PYPL", "INTC", "AMD", "CSCO", "CRM", "TXN", "QCOM", "IBM", "NOW", "SHOP",
           "UBER", "LYFT", "SQ", "PLTR", "SPOT", "DOCU", "ZM", "SNAP", "PINS",
           "DIS", "CMCSA", "T", "VZ", "NFLX", "TMUS", "KO", "PEP", "MCD", "SBUX",
           "WMT", "COST", "HD", "LOW", "TGT", "DG", "F", "GM", "NKE", "PG"]

# Function to load model and scaler for a ticker
def load_model_and_scaler(ticker):
    model_path = f"models/{ticker}_model.keras"
    scaler_path = f"models/{ticker}_scaler.npy"
    if os.path.exists(model_path) and os.path.exists(scaler_path):
        model = load_model(model_path)
        scaler = np.load(scaler_path, allow_pickle=True).item()
        return model, scaler
    else:
        raise FileNotFoundError(f"Model or scaler not found for {ticker}")

# Test models
for ticker in tickers:
    print(f"Testing model for {ticker}...")
    try:
        # Load model and scaler
        model, scaler = load_model_and_scaler(ticker)

        # Fetch recent historical data
        data = yf.download(ticker, period="5d", interval="1m")
        if data.empty:
            print(f"No data available for {ticker}. Skipping...")
            continue

        # Compute additional features: SMA and EMA
        data['SMA_10'] = data['Close'].rolling(window=10).mean()
        data['EMA_10'] = data['Close'].ewm(span=10, adjust=False).mean()
        data = data.dropna()  # Remove rows with NaN values

        # Prepare feature set
        prices = data['Close'].values.reshape(-1, 1)
        sma = data['SMA_10'].values.reshape(-1, 1)
        ema = data['EMA_10'].values.reshape(-1, 1)

        # Stack features (price, SMA, EMA)
        features = np.hstack([prices, sma, ema])

        # Scale features
        scaled_features = scaler.transform(features)

        # Create sequences for testing
        sequence_length = 60
        X_test = []
        y_actual = []
        for i in range(len(scaled_features) - sequence_length):
            X_test.append(scaled_features[i:i + sequence_length])
            y_actual.append(prices[i + sequence_length][0])  # Actual price for comparison

        X_test = np.array(X_test)
        y_actual = np.array(y_actual)

        # Make predictions
        predictions = model.predict(X_test)

        # Convert percentage change predictions to actual prices
        predictions = y_actual[:len(predictions)] * (1 + predictions.flatten())

        # Plot actual vs predicted prices
        plt.figure(figsize=(10, 6))
        plt.plot(y_actual, label='Actual Prices')
        plt.plot(predictions, label='Predicted Prices')
        plt.title(f"{ticker} Model Test")
        plt.xlabel("Time")
        plt.ylabel("Price")
        plt.legend()
        plt.show()

    except Exception as e:
        print(f"Error testing model for {ticker}: {e}")

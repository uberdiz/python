import yfinance as yf
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, LSTM
from tensorflow.keras import Input
import os

# Ensure models directory exists
os.makedirs("models", exist_ok=True)

# Create LSTM model structure
def create_model(sequence_length, feature_count):
    model = Sequential([
        Input(shape=(sequence_length, feature_count)),
        LSTM(50, return_sequences=True),
        LSTM(50),
        Dense(1, activation='linear')
    ])
    model.compile(optimizer='adam', loss='mean_absolute_percentage_error')
    return model

# Create data sequences for time-series forecasting
def create_sequences(data, targets, sequence_length):
    X, y = [], []
    for i in range(len(data) - sequence_length):
        X.append(data[i:i + sequence_length])
        y.append(targets[i + sequence_length - 1])
    return np.array(X), np.array(y)

# Backtest the model on historical data
def backtest(model, X_test, y_test):
    predictions = model.predict(X_test).flatten()
    correct = np.sum((predictions > 0) == (y_test > 0))
    accuracy = correct / len(y_test) * 100
    print(f"Backtest Accuracy: {accuracy:.2f}%")
    return accuracy

# Training logic
tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NVDA", "NFLX", "ADBE", "ORCL",
           "PYPL", "INTC", "AMD", "CSCO", "CRM", "TXN", "QCOM", "IBM", "NOW", "SHOP",
           "UBER", "LYFT", "SQ", "PLTR", "SPOT", "DOCU", "ZM", "SNAP", "PINS",
           "DIS", "CMCSA", "T", "VZ", "NFLX", "TMUS", "KO", "PEP", "MCD", "SBUX",
           "WMT", "COST", "HD", "LOW", "TGT", "DG", "F", "GM", "NKE", "PG"]
for ticker in tickers:
    try:
        print(f"Training model for {ticker}...")
        data = yf.download(ticker, start="2020-01-01", end="2023-01-01")
        if data.empty:
            print(f"No data for {ticker}. Skipping...")
            continue

        data['sma'] = data['Close'].rolling(window=10).mean()
        data['ema'] = data['Close'].ewm(span=10).mean()
        data = data.dropna()

        prices = data['Close'].values
        sma = data['sma'].values
        ema = data['ema'].values
        pct_change = (prices[1:] - prices[:-1]) / prices[:-1]

        features = np.stack([prices[:-1], sma[:-1], ema[:-1]], axis=1)
        scaler = MinMaxScaler()
        scaled_features = scaler.fit_transform(features)

        X, y = create_sequences(scaled_features, pct_change, 60)
        split = int(0.8 * len(X))
        X_train, X_test = X[:split], X[split:]
        y_train, y_test = y[:split], y[split:]

        model = create_model(60, X_train.shape[2])
        model.fit(X_train, y_train, epochs=100, batch_size=64, verbose=1)

        accuracy = backtest(model, X_test, y_test)

        if accuracy > 50:
            model.save(f"models/{ticker}_model.keras")
            np.save(f"models/{ticker}_scaler.npy", scaler)
            print(f"Model saved for {ticker}.")
        else:
            print(f"Model for {ticker} did not pass backtest.")

    except Exception as e:
        print(f"Error training {ticker}: {e}")

# Indicate that training for all tickers is complete
print("Training complete.")

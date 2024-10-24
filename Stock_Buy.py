import pandas as pd
from alpaca_trade_api.rest import REST, TimeFrame
import os

# Alpaca API credentials (replace with your actual API key and secret)
API_KEY = 'your_api_key'
API_SECRET = 'your_api_secret'
BASE_URL = 'https://paper-api.alpaca.markets'  # Use this for paper trading

# Create Alpaca API instance
api = REST(API_KEY, API_SECRET, BASE_URL, api_version='v2')

def read_stocks_to_buy(file_path):
    """
    Reads the stocks to buy from the CSV file and returns a DataFrame.
    """
    try:
        stocks_df = pd.read_csv(file_path)
        print(f"Loaded {len(stocks_df)} stocks from {file_path}.")
        return stocks_df
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return None

def buy_stock(symbol, price, quantity):
    """
    Places a market order to buy the specified stock symbol at the given price and quantity.
    """
    try:
        # Check if the symbol is tradable
        if api.get_asset(symbol).status == 'ACTIVE':
            # Place the market order (quantity can be defined based on your budget or strategy)
            api.submit_order(
                symbol=symbol,
                qty=quantity,
                side='buy',
                type='market',
                time_in_force='gtc'  # Good till cancelled
            )
            print(f"Placed buy order for {quantity} shares of {symbol} at ${price}")
        else:
            print(f"Stock {symbol} is not active or tradable.")
    except Exception as e:
        print(f"Failed to place order for {symbol}: {e}")

def execute_buying_strategy(stocks_df):
    """
    Iterates over the DataFrame of stocks to buy and executes buy orders based on the provided price and score.
    """
    for index, row in stocks_df.iterrows():
        symbol = row['Stock']
        price = row['Price']
        score = row['Score']  # Can be used to filter or prioritize buying

        # Define the quantity of shares to buy (e.g., based on score or other logic)
        # For simplicity, we're using a fixed quantity (this can be dynamic based on score or account balance)
        quantity = 1  # Set this based on your budget or strategy

        print(f"Preparing to buy {quantity} shares of {symbol} at ${price} with score: {score}")

        # Place the order
        buy_stock(symbol, price, quantity)

def main():
    # Path to your CSV file with the stocks to buy
    file_path = 'stocks_to_buy.csv'
    
    # Read the stocks to buy from the CSV
    stocks_df = read_stocks_to_buy(file_path)
    
    if stocks_df is not None:
        # Execute the buying strategy
        execute_buying_strategy(stocks_df)
    else:
        print("No stocks data to process.")

if __name__ == "__main__":
    main()

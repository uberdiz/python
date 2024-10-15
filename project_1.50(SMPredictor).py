import requests
import pandas as pd
import matplotlib.pyplot as plt
import yfinance as yf

stock = "NVDA"
# Download stock data
tracked_stock = yf.Ticker(stock)
df = tracked_stock.history(start='2020-01-01', end='2024-01-01')

# Function to calculate moving averages
def moving_average(average):
    df[f'{average}_day_MA'] = df['Close'].rolling(window=average).mean()

# Function to calculate RSI
def calculate_rsi(df, period=14):
    # Calculate the daily price change
    df['Price_Change'] = df['Close'].diff()
    
    # Separate gains and losses
    df['Gain'] = df['Price_Change'].apply(lambda x: x if x > 0 else 0)
    df['Loss'] = df['Price_Change'].apply(lambda x: -x if x < 0 else 0)
    
    # Calculate average gains and losses over the defined period (14 days by default)
    df['Avg_Gain'] = df['Gain'].rolling(window=period).mean()
    df['Avg_Loss'] = df['Loss'].rolling(window=period).mean()
    
    # Calculate the Relative Strength (RS)
    df['RS'] = df['Avg_Gain'] / df['Avg_Loss']
    
    # Calculate the RSI
    df['RSI'] = 100 - (100 / (1 + df['RS']))
    
    return df

# Calculate percentage change
df['Pct_change'] = df['Close'].pct_change()

# Calculate moving averages
moving_average(5)
moving_average(10)
moving_average(50)

# Calculate RSI
df = calculate_rsi(df, period=14)

# Display the modified data, including RSI
print(df[['Close', 'Pct_change', '5_day_MA', '10_day_MA', '50_day_MA', 'RSI']].tail())
df[['Close', 'Pct_change', '5_day_MA', '10_day_MA', '50_day_MA', 'RSI']].to_csv('stock_data.csv')
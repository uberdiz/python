import pandas as pd
import os
import numpy as np
import math

# Load data from the provided CSV
df = pd.read_csv("stock_data.csv")

# Lists to store ranked stocks and stocks with incomplete data
complete_data_stocks = []
incomplete_data_stocks = []
reload_stocks = []
interested = ['Market Cap', 'Price', 'Avg Vol (10 day) 3', 'Risk-Free Rate', 'Forward Annual Dividend Yield 4', 'Beta (5Y Monthly)']

# Load existing stocks to be used for comparison or ranking
def load_existing_stocks():
    reload_stocks = pd.read_csv("stocks_to_buy.csv", usecols=['Stock'])['Stock'].tolist() if os.path.exists("stocks_to_buy.csv") else []
    print(reload_stocks)
    
    if os.path.exists("stocks_to_buy.csv"):
        return pd.read_csv("stocks_to_buy.csv", header=None, names=['Type', 'Stock', 'Price', 'Shares', 'Total_Invested'])
    return pd.DataFrame(columns=['Type', 'Stock', 'Price', 'Shares', 'Total_Invested'])

# Function to calculate volatility (as a proxy for BSM's implied volatility)
def calculate_volatility(price_data):
    price_data['Daily Return'] = price_data['Close'].pct_change()
    volatility = price_data['Daily Return'].std() * math.sqrt(252)  # Annualize the volatility
    return volatility

# Function to calculate stock score based on BSM-like ranking
def score_stock_bsm(row):
    try:
        # Assume stock price and strike price are the same for simplicity
        stock_price = float(row['Price'])
        time_to_maturity = 1  # Use 1 year as a default time to maturity
        risk_free_rate = 0.03  # Risk-free rate for BSM
        
        # Get stock-specific data
        volatility = float(row['Beta (5Y Monthly)']) if row['Beta (5Y Monthly)'] != '--' else 0.0
        pe_ratio = float(row['Price']) if row['Price'] != '--' else 0.0
        market_cap = float(row['Market Cap'].replace('T', 'e12').replace('B', 'e9')) if row['Market Cap'] != '--' else 0.0
        dividend_yield = float(row['Forward Annual Dividend Yield 4'].replace('%', '')) / 100 if row['Forward Annual Dividend Yield 4'] != '--' else 0.0

        # Define weights (adjust as needed)
        weights = {
            'Volatility': 0.4,  # Higher volatility favored (for growth-focused stocks)
            'PE Ratio': 0.2,
            'Market Cap': 0.2,
            'Dividend Yield': 0.2
        }

        score = (volatility * weights['Volatility']) + (pe_ratio * weights['PE Ratio']) + (market_cap * weights['Market Cap']) + (dividend_yield * weights['Dividend Yield'])
        
        return score
    except ValueError:
        return None  # Return None if score calculation fails

# Iterate over each row in the DataFrame and calculate BSM-like scores
for index, row in df.iterrows():
    if any(value in ['--', 'Not Found', ''] for value in row):
        incomplete_data_stocks.append({'Stock': row['Stock']})
    else:
        # Calculate the BSM-like stock score
        bsm_score = score_stock_bsm(row)

        if bsm_score is not None:
            complete_data_stocks.append({
                'Stock': row['Stock'],
                'Score': bsm_score,
                'Price': float(row['Price'])
            })

# Sort the stocks by BSM-like score (descending)
sorted_stocks = sorted(complete_data_stocks, key=lambda x: x['Score'], reverse=True)

# Print and save the top stocks to the CSV
top_n = 10  # Select the top N stocks
top_stocks = sorted_stocks[:top_n]

# Write top-ranked stocks to CSV
with open('stocks_to_buy.csv', 'w') as f:
    f.write('Type,Stock,Price,Score\n')
    for stock in top_stocks:
        f.write(f'BSM,{stock["Stock"]},{stock["Price"]},{stock["Score"]:.2f}\n')

print("Top-ranked stocks based on BSM-like scoring have been saved to 'stocks_to_buy.csv'.")

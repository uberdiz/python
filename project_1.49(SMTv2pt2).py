import pandas as pd
import os

# Load data from CSV (replace with actual file path if reading from a file)
df = pd.read_csv("!StockHelper_List.csv")

# Lists to store ranked stocks and stocks with incomplete data
complete_data_stocks = []
incomplete_data_stocks = []

# Function to check if a row has missing or invalid data
def has_missing_data(row):
    return any(value in ['--', 'Not Found', ''] for value in row)

# Function to calculate stock score
def score_stock(row):
    try:
        # Weights for different financial metrics, including beta
        weights = {
            'Return on Equity  (ttm)': 0.25,
            'Quarterly Earnings Growth  (yoy)': 0.2,
            'Operating Cash Flow  (ttm)': 0.2,
            'Current Ratio  (mrq)': 0.1,
            'Price/Sales': 0.1,
            'Price/Book': 0.1,
            'Beta (5Y Monthly)': -0.05  # Assuming lower beta is better, negative weight
        }
        
        # Score calculation using columns
        score = 0
        for metric, weight in weights.items():
            value = row[metric]
            if isinstance(value, str):
                # Handle string inputs
                value = value.strip('%').replace('M', '').replace('B', '').replace('-', '')
                value = float(value) if value else 0.0  # Convert to float or set to 0 if empty
            # If value is already a float, use it directly
            score += value * weight
            
        return score
    except ValueError:
        return None  # Return None if score calculation fails

# Iterate over each row in the DataFrame
for index, row in df.iterrows():
    if has_missing_data(row):
        incomplete_data_stocks.append({'Stock': row['Stock']})
    else:
        score = score_stock(row)
        if score is not None:
            complete_data_stocks.append({
                'Stock': row['Stock'],
                'Score': score,
                'Price': float(row['Price'])
            })

# Sorting complete stocks by score
complete_data_stocks = sorted(complete_data_stocks, key=lambda x: x['Score'], reverse=True)

# Output results
print("Ranked Stocks (Complete Data):")
for stock in complete_data_stocks:
    print(f"Stock: {stock['Stock']}, Score: {stock['Score']}, Price: {stock['Price']}")

# Prepare buyer list based on scores
buyer = [stock['Score'] for stock in complete_data_stocks]

# Total score for calculating proportionate investment
total_score = sum(buyer)
total_spent = 0
top_n = 10
# Print all these stocks, price and number of shares to a csv file
def calculate_stocks(money, total_spent, complete_data_stocks, total_score, top_n=None, action='buy', total_profit=0):
    if action not in ['buy', 'sell']:
        raise ValueError("Action must be 'buy' or 'sell'.")

    if action == 'buy':
        stocks_to_buy = complete_data_stocks[:top_n] if top_n else complete_data_stocks
        buy_details = []  # List to store buying details for CSV
        
        for stock in stocks_to_buy:
            
            weight = stock['Score'] / total_score  # Proportion of total score
            amount_to_invest = int(money * weight)  # Amount to invest in this stock
            
            # Calculate shares to buy
            if stock['Price'] > 0:  # Check to avoid division by zero
                shares_to_buy = int(amount_to_invest / stock['Price'])  # Calculate shares to buy
                total_spent += amount_to_invest
                
                print(f"Buy {shares_to_buy:.2f} stocks of {stock['Stock']} for ${amount_to_invest:.2f}")
                buy_details.append({
                    'Stock': stock['Stock'],
                    'Price': stock['Price'],
                    'Shares to Buy': shares_to_buy,
                    'Amount to Invest': amount_to_invest
                })
            else:
                print(f"Cannot buy {stock['Stock']} due to zero or negative price.")

        print(f"Total spent: ${total_spent:.2f}")

        # Check if the CSV file already exists
        file_exists = os.path.isfile('stocks_to_buy.csv')

        # Create a DataFrame from the buying details
        buy_df = pd.DataFrame(buy_details)
        
        # Append the DataFrame to the CSV file
        buy_df.to_csv('stocks_to_buy.csv', mode='a', header=not file_exists, index=False)
        print("Buying details appended to 'stocks_to_buy.csv'")

    elif action == 'sell':
        # Read the stocks you bought
        bought_stocks_df = pd.read_csv('stocks_to_buy.csv')
        
        # Read current stock prices
        current_stocks_df = pd.read_csv('!StockHelper_List.csv')
        
        # Process each stock that has been bought
        for _, bought_stock in bought_stocks_df.iterrows():
            stock_symbol = bought_stock['Stock']
            bought_price = bought_stock['Price']
            shares_owned = bought_stock['Shares to Buy']
            
            
            # Find the current price of the stock
            current_price_row = current_stocks_df[current_stocks_df['Stock'] == stock_symbol]
            
            if not current_price_row.empty:
                current_price = current_price_row['Price'].values[0]
                print(f"Current price for {stock_symbol} is ${current_price:.2f}")
                
                # Check conditions for selling
                if current_price > bought_price:
                    potential_profit = (current_price - bought_price) * shares_owned
                    total_profit += potential_profit
                    print(f"Consider selling {shares_owned:.2f} shares of {stock_symbol} for a profit of ${potential_profit:.2f}.")
                elif current_price < bought_price:
                    print(f"Holding {shares_owned:.2f} shares of {stock_symbol}, current price is lower than bought price.")
                else:  # current_price == bought_price
                    print(f"Holding {shares_owned:.2f} shares of {stock_symbol}, current price is equal to bought price, no action recommended.")
            else:
                print(f"Current price for {stock_symbol} not found in market data.")
    print(f"Total profit: ${total_profit:.2f}")

# Example usage
total_profit = 0
# To buy stocks:
tobuy = input("Do you want to buy or sell stocks?: (buy / sell): ").lower()
if tobuy == 'buy':
    money = int(input("\nHow much money do you want to spend: "))
    if money <= 0:
        print("Please enter a valid amount of money.")
        exit()
    calculate_stocks(money, total_spent, complete_data_stocks, total_score, top_n, action='buy')
elif tobuy == 'sell':
    calculate_stocks(total_profit, total_spent, complete_data_stocks, total_score, top_n, action='sell')
else:
    while tobuy != 'buy' or tobuy != 'sell':
        print("Invalid input. Please enter 'buy' or 'sell'.\n")
        tobuy = input("Do you want to buy or sell stocks?: (buy / sell): ").lower()
# UPDATE CSV FILE WITH SOLD STOCKS!!!!!!